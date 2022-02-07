 
# 我们如何跟踪一个 Go 微服务中(似乎存在的)内存泄露异常
 2019 年 9 月 5 日

- 原文地址：[How we tracked down (what seemed like) a memory leak in one of our Go microservices](https://blog.detectify.com/2019/09/05/how-we-tracked-down-a-memory-leak-in-one-of-our-go-microservices/)
- 原文作者： Roberto Soares & Christoffer Fjellström
- 本文永久链接：https://github.com/gocn/translator/blob/master/2019/How_we_tracked_down_(what_seemed_like)_a_memory_leak_in_one_of_our_Go_microservices.md
- 译者：[Ryan](https://github.com/ryankwak)
- 校对：[cvley](https://github.com/cvley)

_**来自 Detectify 后端团队的专用博客:**_

**Dectify 的后端开发团队已经使用 Go 多年，这是我们选择的为微服务提供支持的编程语言。** 我们认为 Go 是一种很棒的语言，并且事实证明它在我们的运营中表现地非常出色。 它带有一个很棒的工具集，例如我们稍后将介绍的称为 **pprof** 的工具。

但是，即使 Go 表现如此出色，我们也注意到我们的一个微服务的行为与内存泄漏非常相似。
在这篇文章中，我们将逐步探讨这个问题，决策背后的思考过程以及理解该问题所需的详细信息最后解决这个问题。
## 如何开始

我们在监控系统上可以看到，该微服务的内存使用量会缓慢增长并且永远不会下降，直到达到我们遇到 **OOM（内存不足** 错误，或者我们需要重新启动服务。

尽管 Go 有一些出色的工具，但在调试过程中，我们发现自己想研究完整的内核转储，但是截至撰写本文时，pprof 做不到（或任何其他 Go 工具）不可能）。 它有其局限性，但它提供的功能仍然有助于我们追寻此内存溢出问题的根本原因。

## 用 pprof 优化 Go

pprof 是一个 Go 工具，用于数据可视化和数据分析。 它适用于 CPU 和内存性能分析，但是这里不介绍 CPU 性能分析。

在 Web 服务器中设置 pprof 非常简单。 您可以直接调用 pprof 函数，例如 pprof.WriteHeapProfile，也可以设置 pprof 端点并从那里获取数据，我们发现这种方式更有意思。
对于第二个选项，您只需要导入 pprof 软件包，它将在 `/debug/pprof` 中注册端点。 这样，您可以通过向端点发送 GET 请求来提取数据，这对于抽象化运行容器的环境非常方便。 根据 pprof 文档，可以安全地在生产环境中使用它，因为 pprof 几乎不会增加额外的开销。 但是请记住，`pprof` 端点**不应接受**公开访问，因为它们包含有关您服务的敏感数据。

下面是需要加入到你代码中的内容：

```golang
go
import (
"net/http"
_ "net/http/pprof"
)
```


如此配置之后，您应该可以在 `/debug/pprof` 端点访问不同的 pprof 配置文件。 例如，如果要进行堆优化，则可以执行以下操作：
```curl https://myservice/debug/pprof/heap > heap.out```


该工具有多个内置配置文件，例如：
- `heap`: 堆中活动对象的内存分配采样
- `goroutine`: 堆栈跟踪所有当前 goroutine
- `allocs`: 所有过去的内存分配采样
- `threadcreate`：导致创建新 OS 线程的堆栈跟踪
- `block`: 导致阻塞同步原语的堆栈跟踪
- `mutex`: 竞争互斥量持有者的堆栈跟踪


你可以在[pprof.go](https://golang.org/src/runtime/pprof/pprof.go)文件中找到更多细节信息。

我们将大部分时间都花在堆配置文件上。 如果在堆配置文件中找不到有用的内容，请尝试检查其他内容。 我们还检查了 goroutine 配置文件几次，以确保没有任何 go 例程挂起并泄漏内存。

## 我们在寻找什么

在潜入调试深渊之前，重要的是要退后一步，弄清楚我们到底在寻找什么。 换句话说，Go 中会以什么方式出现内存泄漏（或其他形式的内存压力）？
Go 是一种支持自动垃圾回收语言，它消除了开发人员的许多内存管理职责，但是我们仍然需要谨慎，不要阻塞分配内存被垃圾回收的的过程。
在 Go 中，有几种方法可以做到并导致内存泄漏。 大多数情况下，它们是由以下原因引起的：
- 创建子字符串和子切片
- `defer` 语句错误使用
- 未关闭的 HTTP 响应体（或通常未关闭的资源）
- 孤悬例程
- 全局变量

你可以在[go101](https://go101.org/article/memory-leaking.html)，[vividcortex](https://www.vividcortex.com/blog/2014/01/15/two-go-memory-leaks/)，[hackernoon](https://hackernoon.com/avoiding-memory-leak-in-golang-api-1843ef45fca8)中找到更多案例信息。

现在我们对 Go 中的内存泄漏有了一个想法，这时您可能会想说 _“好吧，我不再需要使用性能分析工具，我看一下我的代码就行了！”_。

实际上，服务有十多行代码和几个结构，因此即使您找到的示例很好地使您了解了内存泄漏的样子，但在没有任何指示符的情况下搜索源代码可能只是 就像在大海捞针一样，我们建议您在查看源代码之前使用 pprof ，这样您就可以找到解决问题一些关键线索。

堆概要文件始终是一个很好的开始，因为堆是内存进行分配的地方。 这是后来由 Go 收集垃圾的内存。 堆不是唯一发生内存分配的地方，有些也发生在堆栈中，但是我们不会在这里讨论内存管理系统的内部工作原理，您可以在本文末尾找到更多资源。

## 搜寻溢出的原因


一切准备就绪，开始调试，我们查看服务的堆配置文件
```curl https://services/domain-service/debug/pprof/heap > heap.out```


现在我们已经通过 pprof 生成了堆解析文件，我们可以开始分析了，运行下面的命令可以有交互式的 pprof 提示。

```go tool pprof heap.out```

提示如图所示：
[![](https://blog.detectify.com/wp-content/uploads/2019/09/prompt.png)](http://blog.detectify.com/wp-content/uploads/2019/09/prompt.png)


`Type: inuse_space` 这部分是说 pprof 在使用的分析模式：
- `inuse_space`: 意味着 `pprof` 分配但是未释放的内存量
- `inuse_objects`: 意味着 `pprof` 分配但是未释放的对象总量
- `alloc_space`: 意味着 `pprof` 分配的内存量，不管是否释放
- `alloc_objects`: 意味着 `pprof` 分配的对象总量，不管是否释放


如果你想要更改模式的话可以运行：
```go tool pprof -<mode> heap.out```


但是现在回到提示，最常见的运行命令是`top`，它显示了最大的内存使用者。 这是我们得到的：
[![](https://blog.detectify.com/wp-content/uploads/2019/09/top-1.png)](http://blog.detectify.com/wp-content/uploads/2019/09/top-1.png)


当我们看到这种情况时，我们的第一个想法是 pprof 或监视系统出现了问题，因为我们稳定地看到了 400 MB 的内存消耗，但是  pprof 报告的内存约为 7 MB。 我们登录计算机检查 docker stats，他们还报告了 400 MB 内存消耗。

## pprof 发生了什么

下面是几个要用到的术语的简单解释：
- `flat`: 代表了一个函数的内存分配量，且依然被该函数所持有
- `cum`: 代表了一个函数或者其他的函数被堆栈调用的内存量

我们也可在 pprof 提示符后运行 `png` 命令生成调用图以及他们的内存消耗情况。

[![graph of stack trace](https://blog.detectify.com/wp-content/uploads/2019/09/graph.png)](http://blog.detectify.com/wp-content/uploads/2019/09/graph.png)

还有一点很重要的是， pprof 还支持 Web UI。 您还可以通过运行以下命令在浏览器中查看所有数据：
```go tool pprof -http=:8080 heap.out```


通过查看该图，我们决定查看 `GetByAPEX` 函数的代码，因为根据 pprof，那里存在比较大内存压力（即使报告的最大内存为 7MB）。 确实，我们发现如果数据量太大那很多代码会导致内存压力，例如使用 `json.Unmarshal` 太多，以及将结构附加到切片上很多，然后使用 pprof 生成的图形可以观察到。 简而言之，`GetByAPEX` 的作用是从我们的 Elastic 集群中获取一些数据，进行一些转换，将它们附加到切片上并返回它们。

**尽管如此，这还不足以引起内存泄漏，**它只会造成内存压力，更不用说 pprof 报告的 7 MB 与我们在监控系统中看到的相比并没有什么。

如果您正在运行 Web UI，则可以转到 _Source_ 选项卡以逐行检查带有内存消耗注释的源代码。 使用 pprof `list` 命令在终端中也可以做到。 它使用正则表达式作为输入，将过滤显示给您的源代码。 例如，您可以在 `top` 返回的内存的主要使用者上使用 `list`。

我们还决定查看分配的对象数量。 这是我们得到的：
[![](https://blog.detectify.com/wp-content/uploads/2019/09/objects-1.png)](http://blog.detectify.com/wp-content/uploads/2019/09/objects-1.png)


看到这之后，我们认为将结构体附加到切片上是罪魁祸首，但是在分析代码之后，我们得出结论，因为没有代码持有对切片或组成切片的内部数组的引用，所以不可能导致内存泄漏。 

这么说我们已经穷尽了能想到的办法来分析这个用 Go 写的 Elastic [库](https://github.com/olivere/elastic)内存泄露的问题，长话短说就是，没发现什么错误。

**pprof 范围以外是否可能有问题？**

我们开始认为我们应该查看完整的核心转储，或者在向 Elastic 集群发出请求时可能存在挂起的连接或执行例程。 因此，我们查看了 pprof 的 goroutine 配置文件：

```golang
curl https://services/domain-service/debug/pprof/goroutine > goroutine.out
go tool pprof goroutine.out
```

[![](https://blog.detectify.com/wp-content/uploads/2019/09/goroutine-1.png)](http://blog.detectify.com/wp-content/uploads/2019/09/goroutine-1.png)


一切看起来也很正常，没有产生异常数量的 Go 例程。 我们还使用了 netstat 来检查与服务容器之间建立的 TCP 连接数量，但是也没有异常，所有 TCP 连接均已正确终止。 我们看到一些空闲的连接，但它们最终被终止了。

在这一点上，我们必须接受一个事实，即这不是内存泄漏。 该功能造成了很多内存压力，并且 Go 垃圾回收器或其运行时正在消耗内存。 我们认为，我们能做的最好的事情就是优化功能以流式传输数据，而不是将结构保留在内存中，但是与此同时，我们对这种奇怪的行为产生了兴趣，因此我们开始研究 Go 内存管理系统。

**关于 Go 运行时我们尝试了两件事：**通过使用`runtime.GC`手动触发垃圾回收并从`runtime/debug`中调用`FreeOSMemory`。

它们都不起作用，但是我们觉得我们越来越接近罪魁祸首，因为我们发现有关 Go 内存模型的一些问题尚未解决，其他人也遇到了运行时无法向操作系统释放可用内存的问题。 `FreeOSMemory` 应该被强制发行，但是对我们来说不起作用。
我们发现 Go 与分配的内存紧密相连，这意味着在将内存释放给操作系统之前，Go 会保留一段时间。 如果您的服务的内存使用量达到峰值，并且至少有 5 分钟的“静默”状态，那么 Go 将开始向操作系统释放内存。 在此之前，它将保留它，以防万一它再次需要该内存以避免请求操作系统重新分配更多内存的开销。
听起来不错，但即使在 5 分钟后，运行时也根本没有释放任何内存。 因此，我们决定做一个小实验来检查问题是否确实在 Go 运行时中。 我们将重新启动服务并运行一个脚本，该脚本会在一段时间内请求大量数据（我们称此为 _x_ 时间量），然后在看到内存消耗达到峰值之后，我们可以让它再运行 5 秒然后停止。 然后，我们将再次运行该脚本达 _x_ 的时间（没有 5 秒的余地），以检查 Go 是否会请求更多的内存或它是否仅使用其保留的内存量。 这是我们得到的结果：
[![](https://blog.detectify.com/wp-content/uploads/2019/09/domain-service-usage-1.png)](http://blog.detectify.com/wp-content/uploads/2019/09/domain-service-usage-1.png)

实际上，Go 并没有要求操作系统提供更多的内存，而是在使用它保留的内容。 问题是 5 分钟规则未得到遵守，运行时从未向操作系统释放内存。

现在，我们终于可以确定这毕竟不是内存泄漏，但是由于我们“浪费”了大量内存，这仍然是一个不良行为。

我们找到了罪魁祸首，但我们对此仍然感到沮丧，因为感觉这是我们无法修复的，这只是 Go 运行时的运行方式。 我们的第一个想法是到此为止，优化我们的业务，但是我们继续深入研究，发现 [Go 仓库](https://github.com/golang/go)在内存管理系统上有了一点小的变更：

[runtime: mechanism for monitoring heap size](https://github.com/golang/go/issues/16843)  
[runtime: scavenging doesn’t reduce reported RSS on darwin, may lead to OOMs on iOS](https://github.com/golang/go/issues/29844)  
[runtime: provide way to disable MADV_FREE](https://github.com/golang/go/issues/28466)  
[runtime: Go routine and writer memory not being released](https://github.com/golang/go/issues/32124) 


事实证明，Go 1.12 中发生了变化，有关运行时如何向操作系统发出信号，表明它可以占用未使用的内存。 在 Go 1.12 之前，运行时会在未使用的内存上发送一个 `MADV_DONTNEED` 信号，并且操作系统会立即回收未使用的内存页面。 从 Go 1.12 开始，该信号已更改为`MADV_FREE`，它告诉操作系统**可以**回收一些未使用的内存页面**如果需要**的话，这意味着除非系统承受着来自不同进程的内存压力。

除非您有其他正在运行的服务而且也很消耗内存，否则**RSS（常驻集大小）**（基本上是该服务正在消耗的表观内存量）不会丢失。

根据 Go 存储库中的问题，这显然仅在 iOS 上是一个问题，在 Linux 上不是，但是我们遇到了同样的问题。 然后我们发现可以使用该标志 `GODEBUG=madvdontneed=1` 来运行 Go 服务，以强制运行时使用 `MADV_DONTNEED` 信号而不是 `MADV_FREE` 信号。 我们决定尝试一下！

首先我们在 `/freememory` 中添加了一个新端点，该端点将仅称为`FreeOSMemory`。 这样，我们可以检查它是否确实适用于新信号。 这是我们得到的结果：
[![](https://blog.detectify.com/wp-content/uploads/2019/09/domain-service-madv-1.png)](http://blog.detectify.com/wp-content/uploads/2019/09/domain-service-madv-1.png)


绿线（services-a）是我们在 14:13 到 14:14 之间称为`/freememory`的线，如您所见，它实际上向操作系统释放了几乎所有内容。 我们没有在 services-b（黄线）上调用`/freememory`，但是显然遵守了 5 分钟规则，并且运行时最终释放了未使用的内存！

## 结论

要对编程语言的运行时如何运行以及它所经历的更改有所了解！ Go 是一门很棒的语言，提供了许多惊人的工具，例如 pprof （一直以来都是正确的，并且没有显示任何内存泄漏的迹象）。 学习如何使用它并读取其输出是我们从此“错误”中学到的最有价值的技能，因此一定要检查一下！

**我们一路找到的所有链接：**
[Jonathan Levison on how he used pprof to debug a memory leak.](https://www.freecodecamp.org/news/how-i-investigated-memory-leaks-in-go-using-pprof-on-a-large-codebase-4bec4325e192/)  
[[VIDEO] Memory leaks in Go and how they look like.](https://www.youtube.com/watch?v=ydWFpcoYraU)  
[ Another memory leak debugging journey!](https://medium.com/dm03514-tech-blog/sre-debugging-simple-memory-leaks-in-go-e0a9e6d63d4d)  
[How to optimize your code if it’s suffering from memory pressure, ](https://syslog.ravelin.com/lemony-scale-its-a-series-of-unfortunate-decisions-b16a59833146)and also general tips on how the Go memory model works.  
[How the Go garbage collector works.](https://blog.golang.org/ismmkeynote)  
[Go’s behavior on not releasing memory to the operating system.](https://utcc.utoronto.ca/~cks/space/blog/programming/GoNoMemoryFreeing)

* * *


作者:
Roberto Soares & Christoffer Fjellström

_ **本文由 Detectify 的后端开发人员团队撰写的。 您是 GO 爱好者吗，想要与 Detectify 开发人员团队一起工作吗？ 在我们的[职业页面]（https://detectify.teamtailor.com/）上申请空缺职位吧。** _