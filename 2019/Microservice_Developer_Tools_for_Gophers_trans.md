
# 给Go开发者准备的微服务开发工具

- 原文地址：[microservice-developer-tools-for-gophers](https://www.bugsnag.com/blog/microservice-developer-tools-for-gophers)
- 原文作者： [Roger Guldbrandsen](https://www.twitter.com/kinbiko)
- 本文永久链接：
- 译者：[Ryan](https://github.com/ryankwak)
- 校对：[cvley](https://github.com/cvley)

你写微服务吗？或许你有在用 Go 写微服务？那么接下来的这些工具有必要了解一下，会让你的开发过程异常流畅。这些工具基本上都定位在帮助 Go 开发者编写微服务程序，但是一些包（例如 `ghz`,`ctop`, 和 `grpcui`）语言和平台并不能识别。许多工具都假设已经有这么一个应用在那了。如果你想要自己尝试一下这些工具请浏览 [该仓库特别为本文设置](https://github.com/kinbiko/microsvcgotools).

## Go 工具链都很好用

Go 是由与开发者有共鸣的资深工程师构建的，最终体现在于 go 命令有一些非常不错的工具。我不想对这些工作做过多的介绍，所以你想要了解的话可以点击我提供的资源链接查看相关工具继续深入。没有其他资料的话可以只查看 go 命令行本身：

* 通过调用  `go test -bench=.`. [对当前包进行性能测试](https://dave.cheney.net/2013/06/30/how-to-write-benchmarks-in-go) 该方法假定你已经在代码包中写了 `BenchmarkFoo` 函数。
* 用一个挺不错的网络接口 `go test -coverprofile=c.out` 后面用 `go tool cover -html=c.out`来生成并[检查测试覆盖率](https://blog.golang.org/cover) 
* 使用 `go tool pprof` [剖析并定位应用瓶颈](https://blog.golang.org/profiling-go-programs)。这种方式可以非常简单的得到你的应用如何使用计算机资源的图形化展示。
* 应用中运行测试来发现并[定位竞态争用](https://blog.golang.org/race-detector)。你可以向 `go test` 函数传递 `-race` 参数。这个工具可以帮助你发现大部分竞争条件，尽管并不能达到 100%。这么说吧，我还没见到它会错误标记某些数据争用的情况。
* 使用 `go doc` 查看任何包的文档,例如 `go doc github.com/bugsnag/bugsnag-go.Configure`。如果你更喜欢网页界面,你可能会青睐[使用 godoc 工具](https://godoc.org/golang.org/x/tools/cmd/godoc)。
* 使用 `go mod why $DEPENDENCY` 可以理解为何你的 go 模块有某些依赖包，例如 `go mod why -m github.com/sirupsen/logrus`。

## panics 会让程序崩溃，但是我们可以使用 panicparse 充分利用 panic

有一个非常棒的工具 [panicparse](https://github.com/maruel/panicparse)。使用这个工具你可以把你的程序导入到这个工具里，如果检测到了 panic 他会自动清晰的打印出来结果，所以你可以快速鉴别出哪里出了问题。

```
go get github.com/maruel/panicparse/cmd/pp
# 取决于你的 $PATH 如何设置，`pp`会被解析
# 作为 Perl 包管理器
alias pp="$GOPATH/bin/pp"
```

运行这个程序，使用 `|&` 管道将标准输出和错误输出 `STDOUT` 和 `STDERR` 到 `pp`,他会持续标准输出直到他辨识出有panic，然后会打印出来。

这里有一个使用以及不使用panicparse进行输出对比的例子：

![Output comparison with and without using panicparse.](https://global-uploads.webflow.com/5c741219fd0819aad790e78b/5d24bb23aab4a50668e0bda0_X_nEh-0w55nohNXwIyeZJJhQIfftKlEbjtv-A0u27uh_iaSXsUG97qWr2HwhNqKzKpkuDpufdX2gXIJ7D0q2CWMTs4ZRbKfap5BWe1ktMl-rF-H0QDbKjusHnQDMRbBRCQduIz_m.png)

### panicparse 非常棒 不过现在把他忘了吧

在 Bugsnag ，我们都是处理 panic 的专家，必须[不时处理panic](https://github.com/bugsnag/bugsnag-go)，这个小工具可以帮上忙。但是 panic 的出现通常是无法预料的。为了确保你能正确地调试 panic,在 `.bashrc`或者 `.zshrc` 文件里创建常用 go 命令的别名,将输出传递给 `pp`。

```
alias gt="go test -timeout 3s ./... 2>&1 | pp"
```

通过这种方式，你发现一个 panic 之后，不需要再运行任何命令。如果 panic 只是偶尔发生那得到的结果就是排序好的。

## 写 gRPC endpoints 程序，但是你没有 Postman? 使用 gRPCurl吧

REST APIs 因为他们的可实验性和测试性的特性，开发者生态中有对应的成熟工具，例如[Postman](https://www.getpostman.com/)。但不幸的是，很多公司发现 REST APIs 不是适用于所有的场景。在 Bugsnag 也是如此。在我们的内部服务里我们使用 gRPC 来做同步通信。如果你想要学习 gRPC，它是如何工作的，我们为何使用他，请参考[我同事的文章](https://www.bugsnag.com/blog/grpc-and-microservices-architecture)。那么也就是说我们不使用类似 Postman 这样的工具。不过这也是一种解决方案。

[gRPCurl](https://github.com/fullstorydev/grpcurl)是一个命令行工具，你可以使用他来与一台 gRPC 服务器使用 json 进行交互，使得读取响应信息非常简单。

在某个相关的仓库里我们有一个`GetFizzBuzzSequence` gRPC 终端节点，其 protobuf 文件位于 `fizzbuzz/fizzbuzz.proto` 中用于计算臭名昭著的 FizzBuzz 的面试问题的答案。你可以关注[指导文档](https://github.com/kinbiko/microsvcgotools#run-and-manually-test-grpc-server-with-grpcurl) 去运行一个试验 gRPC 服务器。我们可以使用 `gRPCurl` 命中此原型文件中定义的终端结点，其命令如下：

```
grpcurl \
-proto fizzbuzz/fizzbuzz.proto \ 
-plaintext \
-d '{"start": 1, "end": 100}' \
localhost:1234 \
fizzbuzz.FizzBuzz/GetFizzBuzzSequence
```

`-proto`参数定义了原型文件，这样 `grpcurl` 知道去请求什么，得到什么样的响应。`-plaintext`参数意思我们可以在本例中发送未加密的数据。-d 参数定义了请求体JSON表示形式将其映射到等效的 gRPC 请求。固定参数是 gRPC 服务器所运行的主机和端口。同时终端节点命名都满足`${包名}.${服务名}/${方法名}`格式。

我发现很难记住并且编辑整个命令，所以相比记住命令，在使用的时候，我给特殊的 gRPC 服务器新建了一个临时的 `grpcall` 别名。因为 `grpcurl` 使用 `@` 来解析标准输入所以下面的别名可以正常运行：

```
alias grpcall="grpcurl -proto fizzbuzz/fizzbuzz.proto -plaintext -d @ localhost:1234 fizzbuzz.FizzBuzz/GetFizzBuzzSequence"

echo '{"start": 1, "end": 100}' | grpcall
```

甚至是：

```
cat my-file.json | grpcall
```

### 我想使用 Postman 但是你给我 curl！输入：gRPCui

`gRPCurl` 很好且足够了但是大多数时候你不想折腾语法，你想要一个更加用户友好的界面，和 `gRPCurl` 一样好用但是更加易用，这个工具就是 `gRPCui`。

![](https://global-uploads.webflow.com/5c741219fd0819aad790e78b/5d24bb23aab4a568f5e0bda1_zd3XW0k__1TUEvSCAHoAOVENUwZqERVUWs2GsiDf2k5jze6qtFW9WBLxWz5zF5NyYA-0s8QI0V7NGMOUPrpaEjyKyFnvcRAg9Eoc6_zD9Cg8BhvBro_MJycZK3I2t1szxauC7ozi.png)

你可以像使用 `gRPCurl` 一样使用 `gRPCui` 但是可以更简单：

```
grpcui -proto fizzbuzz/fizzbuzz.proto -plaintext localhost:1234
```

或者你可以在创建 gRPC 服务器的时候启用[反射功能](https://github.com/grpc/grpc/blob/master/doc/server-reflection.md)，比如：

```
import (
 	//...
 	"google.golang.org/grpc/reflection"
)
// ...
reflection.Register(myGrpcServer)
```

你甚至不需要指明原型文件：

```
grpcui -plaintext localhost:1234
```

注意，如果你想要使用 gRPC 传递流式信息那使用 `gRPCui` 就有点儿别扭了，这样得话你可能会想要退回到 `gRPCurl`。

我也听说[BloomRPC](https://github.com/uw-labs/bloomrpc)，他能像 Postman 一样运行在你的本地电脑上，但是写 BloomRPC 的时候还不支持 gRPC 服务端反射特性，所以你还是需要原型文件。

## 用 ghz 进行载入测试

有好些工具测试 HTTP 终端节点的载入性能，但是测试 gRPC 的就不是很多了。我发现测试 gRPC 的最好的工具是[ghz](https://github.com/bojand/ghz)，该工具受到`hey` 和 `grpcurl`项目启发。支持高度自定义，对于熟悉`grpcurl`的人来说 上手 ghz 不难。

比如：

```
ghz \
--insecure \ # Equivalent of -plaintext for grpcurl
-d '{"start": 1, "end": 600}' \ # Data to send, just like grpcurl
-c 100 \ # Number of concurrent requests to make
-n 5000 \ # Number of total requests to make
--call=fizzbuzz.FizzBuzz/GetFizzBuzzSequence \ # Endpoint to hit, like grpcurl
--connections=5 \ # Number of different gRPC connections to make
localhost:1234 # host:port
```

会给你清晰展现请求耗时是怎样：

```
Summary:
   Count:        5000
   Total:        400.47 ms
   Slowest:      16.16 ms
   Fastest:      0.23 ms
   Average:      7.74 ms
   Requests/sec: 12485.20
```

```
Response time histogram:
   0.234 [1]     |
   1.826 [62]    |∎∎
   3.419 [48]    |∎
   5.011 [264]   |∎∎∎∎∎∎∎
   6.603 [1027]  |∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
   8.196 [1527]  |∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
   9.788 [1322]  |∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
   11.380 [580]  |∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
   12.973 [134]  |∎∎∎∎
   14.565 [29]   |∎
   16.157 [6]    |
```

```
Latency distribution:
   10% in 5.31 ms
   25% in 6.42 ms
   50% in 7.78 ms
   75% in 9.08 ms
   90% in 10.21 ms
   95% in 11.00 ms
   99% in 12.62 ms
```

```
Status code distribution:
   [OK]   5000 responses
```

## 使用 pprof 和 ghz 剖析微服务性能发现瓶颈

我们可以组合 ghz 和[标准库中的 pprof](https://blog.golang.org/profiling-go-programs) 剖析我们的代码，比如可以清晰定位出应用的性能瓶颈。咱们使用这个对比一下 fizzbuzz gRPC 服务器。

```
# 这里的 'main' 是运行在 gRPC 服务器上的二进制程序
go tool pprof -http=":" main http://localhost:4321/debug/pprof/profile
```

默认 pprof 花费三十秒时间来生成剖析文件，目前测试应用至少需要 30 秒才会有最好的结果。最快的方式是在 ghz 命令行更改 `-n` 参数，只要`pprof`服务器生成了剖析文件，`pprof`会打开你的浏览器，生成一个可交互的界面供你查看结果。

 ![Walkthrough of generated profile for the fizzbuzz.](https://global-uploads.webflow.com/5c741219fd0819aad790e78b/5d24c3ca82791f58d317e876_pprof-http-lowres-1.gif)

在本例 fizzbuzz 生成的剖析文件中 你可以看到相当多一部分时间被花费在了日志记录上。
注意：使用`pprof`剖析程序性能适用于所有 Go 程序，不单是 gRPC 服务。你只需要使用其他的工具来查看 ghz 意外的流量。

## 使用`#ctop`管理你的 Docker 容器

如果你在云端开发软件服务，大概率你会使用 Docker. Docker 就像`go`会有很多有用的子命令，但是记住这么多也挺乏味的。[ctop](https://github.com/bcicen/ctop)是一个 docker 状态检查工具。他是一个终端用户界面，你可以看到且与当前运行的 docker 容器交互。它设计的非常的棒即使我只运行了一个 docker 容器。

![Docker stats terminal user interface.](https://global-uploads.webflow.com/5c741219fd0819aad790e78b/5d24bb24489f206f1e2fb419_At5IKwh5al8d-Yf8p0GnV3-tagN1Met7ta-pqBxcPNvbM4278J9o9wQq1qyGA_V6YHHLokUYygfzW5X712-TMHTDQVV5oz3oXeNyjMpeqCjYr8lJWnHwF4KtWZ1u2yJwbjDIiLcz.png)

使用 `ctop` 你可以很方便地：

* 和 `docker stats` 一样查看所有容器的统计信息
* 过滤，搜索指定的容器
* 基于基本属性给容器排序
* 深入单个容器内部，在仪表盘上展示其状态
* 查看容器的日志
* 启动/关闭/重启/中断容器

## 自信开发

我希望你在想学习本文的几个新工具之后开发体验能有提升。Go 最大的优点之一是包容开放的社区。本文上面提到的所有的工具都是社区开发的，而且基本都是开发者用自己的时间开发的。请给你使用的这些工具的开发者们表达一些感谢，比如在 GitHub 上给他们的仓库点亮星星，或者发有关内容的推特。
