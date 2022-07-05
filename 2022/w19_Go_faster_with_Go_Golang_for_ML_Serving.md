# 用 Go 跑的更快：使用 Golang 为机器学习服务

因此，我们的要求是用尽可能少的资源完成每秒300万次的预测。值得庆幸的是，这是一种比较简单的推荐系统模型，即多臂老虎机（MAB）。多臂老虎机通常涉及从 [Beta 分布](https://en.wikipedia.org/wiki/Beta_distribution) 等分布中取样。这也是花费时间最多的地方。如果我们能同时做尽可能多的采样，我们就能很好地利用资源。最大限度地提高资源利用率是减少模型所需总体资源的关键。

我们目前的预测服务是用 Python 编写的微服务，它们遵循以下一般结构

> 请求->功能获取->预测->后期处理->返回

一个请求可能需要我们对成千上万的用户、内容对进行评分。带有 GIL 和多进程的 Python 处理性能很鸡肋，我们已经实现了基于 `cython` 和 `C++` 的批量采样方法，绕过了GIL，我们使用了许多基于内核数量的 workers 来并发处理请求。

目前单节点的 Python 服务可以做192个 RPS ，每个大约400对。平均 CPU 利用率只有20%左右。现在的限制因素是语言、服务框架和对存储功能的网络调用。

## 为什么是 Golang?

Golang 是一种静态类型的语言，具有很好的工具性。这意味着错误会被及早发现，而且很容易重构代码。Golang 的并发性是原生的，这对于可以并行运行的机器学习算法和对 Featurestore 的并发网络调用非常重要。它是[这里](https://www.techempower.com/benchmarks/)基准最快的服务语言之一。它也是一种编译语言，所以它在编译时可以进行很好的优化。

## 移植现有的 MAB 到 Golang 上

基本思路，将系统分为3个部分

1.  用于预测和健康的基本 REST API 与存根。
2.  Featurestore 的获取，为此实现一个模块。
3.  使用 [cgo](https://pkg.go.dev/cmd/cgo) 提升和转移 c++ 的采样代码。

第一部分很容易，我选择了 [Fiber](https://gofiber.io/) 框架用于REST API。它似乎是最受欢迎的，有很好的文档，类似 Expressjs 的API。而且它在基准测试中的表现也相当出色。

早期代码

```go
func main() {
    // setup fiber
	app := fiber.New()
    // catch all exception
	app.Use(recover.New())
    // load model struct
	ctx := context.Background()
	md, err := model.NewModel(ctx)
	if err != nil {
		fmt.Println(err)
	}
	defer md.Close()

    // health API
	app.Get("/health", func(c *fiber.Ctx) error {
		if err != nil {
			return fiber.NewError(
                fiber.StatusServiceUnavailable, 
                fmt.Sprintf("Model couldn't load: %v", err))
		}
		return c.JSON(&fiber.Map{
			"status": "ok",
		})
	})
    // predict API
	app.Post("/predict", func(c *fiber.Ctx) error {
		var request map[string]interface{}
		err := json.Unmarshal(c.Body(), &request)
		if err != nil {
			return err
		}

		return c.JSON(md.Predict(request))
	})

```

就这样，任务一完成了。花了不到一个小时。

在第二部分中，需要稍微学习一下如何编写[带方法的结构](https://gobyexample.com/methods)和 [goroutines](https://gobyexample.com/channels)。与 C++ 和 Python 的主要区别之一是，Golang 不支持完全的面向对象编程，主要是不支持继承。它在结构体上的方法的定义方式也与我遇到的其他语言完全不同。

我们使用的 Featurestore 有 [Golang 客户端](https://cloud.google.com/go/docs/reference/cloud.google.com/go/aiplatform/latest/apiv1#cloud_google_com_go_aiplatform_apiv1_FeaturestoreOnlineServingClient)，我所要做的就是在它周围写一个封装器来读取大量并发的实体。

我想要的基本结构是

```go

type VertexFeatureStoreClient struct {
	//client reference to gcp's client
}

func NewVertexFeatureStoreClient(ctx context.Context,) (*VertexFeatureStoreClient, error) {
// client creation code
}

func (vfs *VertexFeatureStoreClient) GetFeaturesByIdsChunk(ctx context.Context, featurestore, entityName string, entityIds []string, featureList []string) (map[string]map[string]interface{}, error) {
	// fetch code for 100 items
}

func (vfs *VertexFeatureStoreClient) GetFeaturesByIds(ctx context.Context, featurestore, entityName string, entityIds []string, featureList []string) (map[string]map[string]interface{}, error) {
	const chunkSize = 100 // limit from GCP
    // code to run each fetch concurrently
	featureChannel := make(chan map[string]map[string]interface{})
	errorChannel := make(chan error)
	var count = 0
	for i := 0; i < len(entityIds); i += chunkSize {
		end := i + chunkSize
		if end > len(entityIds) {
			end = len(entityIds)
		}
		go func(ents []string) {
			features, err := vfs.GetFeaturesByIdsChunk(ctx, featurestore, entityName, ents, featureList)
			if err != nil {
				errorChannel <- err
				return
			}
			featureChannel <- features
		}(entityIds[i:end])
		count++
	}
	results := make(map[string]map[string]interface{}, len(entityIds))
	for {
		select {
		case err := <-errorChannel:
			return nil, err
		case res := <-featureChannel:
			for k, v := range res {
				results[k] = v
			}
		}
		count--
		if count < 1 {
			break
		}
	}

	return results, nil
}
func (vfs *VertexFeatureStoreClient) Close() error {
    //close code
}

```

#### 关于 Goroutine 的提示

尽量多使用通道，有很多教程使用 Goroutine 的 sync workgroups。那些是较低级别的 API，在大多数情况下你都不需要。通道是运行Goroutine 的优雅方式，即使你不需要传递数据，你可以在通道中发送标志来收集。goroutines 是廉价的虚拟线程，你不必担心制造太多的线程并在多个核心上运行。最新的 golang 可以为你跨核心运行。

关于第三部分，这是最难的部分。花了大约一天的时间来调试它。所以，如果你的用例不需要复杂的采样和 `C++`，我建议直接使用 [Gonum](https://www.gonum.org/)，你会为自己节省很多时间。

我没有意识到，从 `cython ` 来的时候，我必须手动编译 `C++` 文件，并将其加载到 cgo include flags 中。

头文件

```c++
#ifndef BETA_DIST_H
#define BETA_DIST_H

#ifdef __cplusplus
extern "C"
{
#endif

    double beta_sample(double, double, long);
#ifdef __cplusplus
}
#endif

#endif

```

注意 `extern C` ，这是 `C++` 代码在 go 中使用的需要，由于[mangling](https://en.wikipedia.org/wiki/Name_mangling)，`C ` 不需要。另一个问题是，我不能在头文件中做任何`#include`语句，在这种情况下 cgo 链接失败（原因不明）。所以我把这些语句移到 `.cpp` 文件中。

编译它

```
g++ -fPIC -I/usr/local/include -L/usr/local/lib  betadist.cpp -shared -o libbetadist.so
```

一旦编译完成，你就可以使用它的 cgo。

cgo 包装文件

```go
/*
#cgo CPPFLAGS: -I${SRCDIR}/cbetadist
#cgo CPPFLAGS: -I/usr/local/include
#cgo LDFLAGS: -Wl,-rpath,${SRCDIR}/cbetadist
#cgo LDFLAGS: -L${SRCDIR}/cbetadist
#cgo LDFLAGS: -L/usr/local/lib
#cgo LDFLAGS: -lstdc++
#cgo LDFLAGS: -lbetadist
#include <betadist.hpp>
*/
import "C"

func Betasample(alpha, beta float64, random int) float64 {
	return float64(C.beta_sample(C.double(alpha), C.double(beta), C.long(random)))
}

```

注意 `LDFLAGS` 中的 `-lbetadist` 是用来链接 `libbetadist.so` 的。你还必须运行 `export DYLD_LIBRARY_PATH=/fullpath_to/folder_containing_so_file/` 。然后我可以运行 `go run .` ，它能够像 go 项目一样工作。

将它们与简单的模型结构和预测方法整合在一起是很简单的，而且相对来说花费的时间更少。

## 结果

![Stress testing result showing 819 QPS](https://ai.ragv.in/images/golang-for-machine-learning-serving/go_mab_qps.png)

| Metric | Python | Go |
| --- | --- | --- |
| Max RPS | 192 | 819 |
| Max latency | 78ms | 110ms |
| Max CPU util. | ~20% | ~55% |

这是对 RPS 的**4.3倍**的提升，这使我们的最低节点数量从80个减少到19个，这是一个巨大的成本优势。最大延迟略高，但这是可以接受的，因为 python 服务在192点时就已经饱和了，如果流量超过这个数字，就会明显下降。

### 我应该把我所有的模型转换为 Golang 吗？

简短的答案：不用。

长答案。Go 在服务方面有很大的优势，但 Python 仍然是实验的王道。我只建议在模型简单且长期运行的基础模型中使用 Go，而不是实验。Go 对于复杂的 ML 用例来说[尚](https://github.com/josephmisiti/awesome-machine-learning#go)不是很成熟。

### 所以房间里的大象，为什么不是 Rust ？

嗯，[希夫做到了](http://shvbsle.in/serving-ml-at-the-speed-of-rust/)。看看吧。它甚至比 Go 还快。