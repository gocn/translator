# Go 高级并发

- 原文地址：https://encore.dev/blog/advanced-go-concurrency
- 原文作者：[André Eriksson](https://encore.dev/blog)
- 译文出处：https://encore.dev/blog
- 本文永久链接：https://github.com/gocn/translator/blob/master/2020/w1_advanced_go_concurrency.md
- 译者：[咔叽咔叽](https://github.com/watermelo)
- 校对者：[fivezh](https://github.com/fivezh)

If you’ve used Go for a while you’re probably aware of some of the basic Go concurrency primitives:
如果你曾经使用过 Go 一段时间，那么你可能了解一些 Go 中的并发原语：

*   `go` 关键字用来生成 goroutines
*   `channel` 用于 goroutines 之间通信
*   `context` 用于传播取消
*   `sync` 和 `sync/atomic` 包用于低级别的原语，例如互斥锁和内存的原子操作

语言特性和包组合在一起，为构建高并发的应用程序提供了丰富的工具集。你可能还没有发现在扩展库 [golang.org/x/sync](https://pkg.go.dev/golang.org/x/sync) 中，提供了一系列更高级别的并发原语。我们将在本文中来谈谈这些内容。

## singleflight 包

正如[文档](https://pkg.go.dev/golang.org/x/sync/singleflight?tab=doc)中所描述，这个包提供了一个重复函数调用抑制的机制。

对于你为了响应用户而开销比较大（例如网络延时）的情况时，这个包就很有用。例如，你的数据库中包含每个城市的天气信息，并且你想将这些数据以 API 的形式提供服务。在某些情况下，可能同时有多个用户想查询同一城市的天气。

在这种场景下，如果你只查询一次数据库然后将结果共享给所有等待的请求，这样不是更好吗？这就是 `singleflight` 提供的功能。

在使用的时候，我们需要要创建一个 `singleflight.Group`。它需要在所有请求中共享才能工作。然后将缓慢或者开销大的操作包装到 `group.Do(key, fn)` 的调用中。对同一个 `key` 的多个并发请求将仅调用 `fn` 一次，并且将 `fn` 的结果返回给所有调用者。  

实际中的使用如下:

```go
package weather

type Info struct {
    TempC, TempF int // temperature in Celsius and Farenheit
    Conditions string // "sunny", "snowing", etc
}

var group singleflight.Group

func City(city string) (*Info, error) {
    results, err, _ := group.Do(city, func() (interface{}, error) {
        info, err := fetchWeatherFromDB(city) // 慢操作
        return info, err
    })
    if err != nil {
        return nil, fmt.Errorf("weather.City %s: %w", city, err)
    }
    return results.(*Info), nil
}
```

需要注意的是，我们传递给 `group.Do` 的闭包必须返回 `(interface{}, error)` 才能和 Go 类型系统一起使用。上面的例子中忽略了 `group.Do` 的第三个返回值，该值是用来表示结果是否在多个调用方之间共享。

如果需要查看更多完整的例子，可以查看 [Encore Playground](https://play.encore.dev/663hvcGbpq-rtw) 中的代码。

## errgroup 包

另一个有用的包是 [errgroup package](https://pkg.go.dev/golang.org/x/sync/errgroup?tab=doc)。它和 `sync.WaitGroup` 比较相似，但是会将任务返回的错误回传给阻塞的调用方。

当你有多个等待的操作，但又想知道它们是否都已经成功完成时，这个包就很有用。还是以上面的天气为例，假如你要一次查询多个城市的天气，并且要确保其中所有的查询都成功返回。

首先定义一个 `errgroup.Group`，然后为每个城市都使用 `group.Go(fn func() error)` 方法。该方法会生成一个 goroutine 来执行这个任务。当生成你想执行的所有任务时，使用 `group.Wait()` 等待它们完成。需要注意和 `sync.WaitGroup` 有一点不同的是，该方法会返回错误。当且仅当所有任务都返回 `nil` 时，才会返回一个 `nil` 错误。

实际中的使用如下:

```go
func Cities(cities ...string) ([]*Info, error) {
    var g errgroup.Group
    var mu sync.Mutex
    res := make([]*Info, len(cities)) // res[i] corresponds to cities[i]

    for i, city := range cities {
        i, city := i, city // 为下面的闭包创建局部变量
        g.Go(func() error {
            info, err := City(city)
            mu.Lock()
            res[i] = info
            mu.Unlock()
            return err
        })
    }
    if err := g.Wait(); err != nil {
        return nil, err
    }
    return res, nil
}
```

这里我们使用一个 `res` 切片来存储每个 goroutine 执行的结果。尽管上面的代码没有使用 `mu` 互斥锁也是线程安全的，但是每个 goroutine 都是在切片中自己的位置写入结果，因此我们不得不使用一个切片，以防代码变化。

## 限制并发

上面的代码将同时查找给定城市的天气信息。如果城市数量比较少，那还不错，但是如果城市数量很多，可能会导致性能问题。在这种情况下，就应该引入限制并发了。

在 Go 中使用 [semaphores](https://www.guru99.com/semaphore-in-operating-system.html) 信号量让实现限制并发变得非常简单。信号量是你学习计算机科学中可能遇到的并发原语，如果没有遇到也不用担心。你可以在多种场景下使用信号量，但是我们使用它来追踪运行中的任务的数量，并阻塞直到有空间可以执行其他任务。

在 Go 中，我们可以使用 `channel` 来实现信号量的功能。如果我们一次需要最多执行 10 个任务，则需要创建一个容量为 10 的 `channel`：`semaphore := make(chan struct{}, 10)`。你可以想象它为一个可以容纳 10 个球的管道。

如果想执行一个新的任务，我们只需要给 `channel` 发送一个值：`semaphore <- struct{}{}`，如果已经有很多任务在运行的话，将会阻塞。这类似于将一个球推入管道，如果管道已满，则需要等待直到有空间为止。

当通过 `<-semaphore` 能从该 `channel` 中取出一个值时，这表示一个任务完成了。这类似于在管道另一端拿出一个球，这将为塞入下一个球提供了空间。

如描述一样，我们修改后的 `Cities` 代码如下：

```go
func Cities(cities ...string) ([]*Info, error) {
    var g errgroup.Group
    var mu sync.Mutex
    res := make([]*Info, len(cities)) // res[i] corresponds to cities[i]
    sem := make(chan struct{}, 10)
    for i, city := range cities {
        i, city := i, city // create locals for closure below
        sem <- struct{}{}
        g.Go(func() error {
            info, err := City(city)
            mu.Lock()
            res[i] = info
            mu.Unlock()
            <-sem
            return err
        })
    }
    if err := g.Wait(); err != nil {
        return nil, err
    }
    return res, nil
}
```

### 加权限制并发

最后，当你想要限制并发的时候，并不是所有任务优先级都一样。在这种情况下，我们消耗的资源将依据低优先级任务和高优先级任务的分布以及它们如何开始运行而变得不同。

在这种场景下使用*加权限制并发*是一种不错的解决方式。它的工作原理很简单：我们不需要为同时运行的任务数量做预估，而是为每个任务提供一个 "cost"，并从信号量中获取和释放它。

我们不再使用 `channel` 来做这件事，因为我们需要立即获取并释放 "cost"。幸运的是，"扩展库" [golang.org/x/sync/sempahore](https://pkg.go.dev/golang.org/x/sync@v0.0.0-20190911185100-cd5d95a43a6e/semaphore?tab=doc) 实现了加权信号量。

`sem <- struct{}{}` 操作叫 "获取"，`<-sem` 操作叫 "释放。你可能会注意到 `semaphore.Acquire` 方法会返回错误，那是因为它可以和 `context` 包一起使用来控制提前结束。在这个例子中，我们将忽略它。

实际上，天气查询的例子比较简单，不适用加权信号量，但是为了简单起见，我们假设 `cost` 变量随城市名称长度而变化。然后，我们修改如下：

```go
func Cities(cities ...string) ([]*Info, error) {
    ctx := context.TODO() // 需要的时候，可以用 context 替换 
    var g errgroup.Group
    var mu sync.Mutex
    res := make([]*Info, len(cities)) // res[i] 对应 cities[i]
    sem := semaphore.NewWeighted(100) // 并发处理 100 个字符
    for i, city := range cities {
        i, city := i, city // 为闭包创建局部变量
        cost := int64(len(city))
        if err := sem.Acquire(ctx, cost); err != nil {
            break
        }
        g.Go(func() error {
            info, err := City(city)
            mu.Lock()
            res[i] = info
            mu.Unlock()
            sem.Release(cost)
            return err
        })
    }
    if err := g.Wait(); err != nil {
        return nil, err
    } else if err := ctx.Err(); err != nil {
        return nil, err
    }
    return res, nil
}
```

## 结论

上面的例子展示了在 Go 中通过微调来实现需要的并发模式是多么简单。