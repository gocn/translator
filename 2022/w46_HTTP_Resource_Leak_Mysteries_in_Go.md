# Go 中的 HTTP 资源泄漏之谜

- 原文地址：https://coder.com/blog/go-leak-mysteries
- 原文作者：Spike Curtis
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2022/w46_HTTP_Resource_Leak_Mysteries_in_Go.md
- 译者：[Jancd](https://github.com/Jancd)
- 校对：[]()

我喜欢排查泄露的问题。这是一个智力之谜，我总能在这个过程中学到新东西。

这个谜就像你在电视上读到或看的一样：细节是猥琐的，从不令人沮丧，最后，我们总能得到一个很好的合乎逻辑的解释。 这就是计算机的伟大之处：它们最终是可以预测的，所以我可以安全地扮演侦探角色，因为我知道我总是能得到我的罪犯。

如果你讨厌神秘小说或者只想学习参考，你可以[跳到关键要点(剧透警告，废话)](https://coder.com/blog/go-leak-mysteries#key-takeaways)。

## 泄露 Dogfood

![](https://www.datocms-assets.com/19109/1667325071-output-onlinepngtools.png?fit=clip&fm=webp&w=768)

在 Coder，我们构建用于管理公共和私有云中的开发工作区的工具。当然，我们在 Coder 上开发 Coder。 上周，一位工程师在我们的 dogfood[1] 集群的主要编码器服务 coderd（见上图）中发现了一些可疑的地方。

需要重新启动是意料之中的事情了，因为我们非常积极地重新部署以保持接近生产环境，但是同时可以看到每次我们重新启动时，goroutine 数量都会开始缓慢且稳定的增加。

注意，增加的上升角度是恒定的：它以相同的速度上升，无论白天还是晚上。这个服务是我们的主 API 服务器，它的负载肯定不是恒定的。与大多数服务一样，它在工作日的负载最大，而在夜间几乎没有负载。因此，我们猜测泄漏最有可能发生在一些固定的后台任务中，而不是 API 处理程序中。

## 寻找真相

好了，让我们来了解更多关于泄漏的信息!

幸运的是，我们使用[golang 的 pprof HTTP 端点](https://pkg.go.dev/net/http/pprof)运行我们的 dogfood 集群。而且，我们从指标中知道我们有一个 goroutine 泄漏，所以我们可以顺着运行 goroutine 的堆栈跟踪。

在以下信息的行头能看到，一个 writeLoop 有 822 个 goroutines，一个 readLoop 有 820 个 goroutines。

```go
goroutine profile: total 2020
822 @ 0x5ac2b6 0x5bbfd2 0x94e4b5 0x5dce21
#   0x94e4b4    net/http.(*persistConn).writeLoop+0xf4  /usr/local/go/src/net/http/transport.go:2392

820 @ 0x5ac2b6 0x5bbfd2 0x94d3c5 0x5dce21
#   0x94d3c4    net/http.(*persistConn).readLoop+0xda4  /usr/local/go/src/net/http/transport.go:2213
```

接着，我们可以读出涉及 HTTP 的信息。 它是一个 `persistConn`，通过[一些代码阅读](https://github.com/golang/go/blob/8ed0e51b5e5cc50985444f39dc56c55e4fa3bcf9/src/net/http/transport.go#L98)，我们可以看到它用于客户端的连接池。

一般来说性能 HTTP 客户端，不会为每个 HTTP 请求建立一个新连接，而是为每个主机维护一个连接池。 这些连接在空闲时最终超时之前被重复用于多个请求。 这增加了向主机发出许多请求的请求和响应吞吐量，这是非常典型的 HTTP 客户端应用程序。

在我们的代码中，我们似乎泄露了这些连接。但是是怎么泄露的？

让我们看看 [我们挂在 readLoop goroutines 上的那一行](https://github.com/golang/go/blob/8ed0e51b5e5cc50985444f39dc56c55e4fa3bcf9/src/net/http/transport.go#L2213)。 这是一个 `select`，上面有一个很好的有用的评论。

```go
// Before looping back to the top of this function and peeking on
// the bufio.Reader, wait for the caller goroutine to finish
// reading the response body. (or for cancellation or death)
select {
```

因此，某些代码正在发出 HTTP 请求，然后无法取消请求或完成读取响应正文。 通常，当调用者没有调用 [`response.Body.Close()`](https://pkg.go.dev/net/http#Response) 时，就会发生这种情况。 这也解释了 writeLoop goroutines，它们是作为 `readLoop` 的一并创建的，并且[都在等待新的 HTTP 请求](https://github.com/golang/go/blob/8ed0e51b5e5cc50985444f39dc56c55e4fa3bcf9/src/net/http/transport.go#L2392)。

## 深究调用堆栈

如果你以为我们已经结束了，那是可以理解的。我们注意到我们的指标有一个问题，然后使用分析器跟踪挂起的确切代码行。我们还没解开这个谜吗?

嗯，没有。我们发现的 goroutine 正在按设计工作：这些 goroutine 是受害者，而不是肇事者。问题是其他一些 goroutine 发出了 HTTP 请求，但未能取消它或关闭响应正文。而且我们知道其他 goroutine 不会继续那里等待响应，否则我们会在 pprof 输出中看到其中的 820 个。它们会继续执行。

如果能够看到创建泄漏的 goroutine 的调用堆栈不是很好吗？你可以在[go race检测器](https://go.dev/blog/race-detector)中得到这种输出，因此它在技术上必须是可行的。显然，在创建 goroutine 时存储它会增加一些内存开销，但每个 goroutine 可能只需要几 kB。也许有一天我们会得到一个包含它的运行时模式，但不幸的是它在这里没有帮助。实际上很容易找到[开始泄露的goroutines的行](https://github.com/golang/go/blob/8ed0e51b5e5cc50985444f39dc56c55e4fa3bcf9/src/net/http/transport.go#L1750)，因为它在同一个文件中。但是，请记住，这是一个持久连接，它本身是从它所处理的 HTTP 请求异步启动的。

我们需要追踪行为不当的 HTTP 客户端代码。我们知道这个 bug 的基本特征：发出 HTTP 请求，接收 HTTP 响应，忘记调用 `response.Body.Close()`。我们的任务是巨大的，因为简单地说，HTTP 无处不在。它是应用程序开发协议的首选。审计我们代码库中的每个 HTTP 请求/响应将花费数周时间。

## 一切取决于时机

回想一下，我们之前对度量的分析使我们得出结论，它是一个后台任务，现在我们知道它是一个发出 HTTP 请求的任务。但我们可以通过更仔细地观察来找到问题细节。

![](https://www.datocms-assets.com/19109/1667325163-output-onlinepngtools-1.png?fit=clip&fm=webp&w=768)

看似直线稳定的增长实际上是阶梯式的，尽管数据中有一些噪声，但我们似乎看到每 1 小时就有一个很大的增长。

事实证明，我们的 coderd 服务每 1 小时运行 4 个后台作业。我们有四名嫌疑人。会是哪一个呢？会不会不止一个人干的？帮助我们进行侦察的一个快速修复方法是改变作业运行的周期。我可以一次只做一件任务，但如果我能做一点改变，就能留在原地，不是更好吗?

选择 1 小时的间隔是大多数人认为的“一个不错的整数”。但与人不同的是，计算机不关心整数[2]。1 小时并不是我们所关心的确切值，因此可以将其更改为接近的值，而不期望系统范围的行为受到影响。

最好避免整数，事实上，整数越少越好。我选择了其中最不四舍五入的数：质数。这使得从数学上讲，周期不可能是更频繁的任务的倍数，所以它们不断地在同一时间发生。选择一个基本单位，然后让作业的质数乘以这个基本单位。我选择 1 分钟作为基本单位，这样就可以很容易地读出度量图表，因为我们的 Prometheus 度量每 15 秒左右才会被删除一次，所以比 1 分钟更小的度量并不能帮助我们理解度量。所以，1 小时的任务变成了47、53、59、67 分钟。

![](https://www.datocms-assets.com/19109/1667325210-output-onlinepngtools-2.png?fit=clip&fm=webp&w=768)

goroutroutine 的峰值现在大多间隔 47 分钟，尽管仍然有一些噪音。这种额外的噪音使我大吃一惊，并使我怀疑是否不止一个任务要对泄漏负责。但是，选择质数的能力意味着任务的开始是交错的，当将峰值与显示任务开始和停止时间的指标放在一起时，峰值总是与同一任务的开始或停止相关。

因此，我有了我的主要怀疑对象：一个检查所有工作区容器图像标记的任务，以便从它们各自的注册中心获得更新。它的动机是：向容器镜像注册中心发送 HTTP 请求。它是有机会的：我可以一遍又一遍地把它与犯罪时间联系起来。

## 插曲：搜索

上面我已经向你描述了我所做的事情，这些事情实际上在我的调查中取得了进展。在做这些事情的同时，我也在做一件没有进展的事情：读代码。

有了一个好的 IDE，你可以通过调用堆栈向下执行并返回。这很乏味，但我认为我很擅长理解代码，这种深度优先搜索错误代码的方法在过去不止一次地为我找到了错误。

但是，正如前面提到的，HTTP 是非常普遍的，因此有很多地方需要覆盖，并且并不总是清楚何时停止深入执行。另一个 HTTP 请求可能只是另一个层次。可惜的是，这里不能体现。

## Tracking it Down 追踪它

游戏仍在继续！但是，仍然有许多不同的代码路径。与容器镜像注册表交互是[涉及许多 HTTP 请求的复杂交互](https://docs.docker.com/docker-hub/api/latest/)。

我也花了一些时间去了解受害者。乍一看，他们都是无名氏。我们不知道他们死的时候有什么要求。但是，仔细检查传输代码就会发现，泄漏的 readLoop goroutine 有一个 HTTP 请求的引用，它试图返回响应而失败。要是我能读到那个请求就好了！我就知道网址了，这就能让案子有更大的进展。

如果我把它放在调试器里，我就能读取它。

我试图在一些匆忙构建的单元测试中重现泄漏，但没有运气。并不是来自任何注册表的任何容器镜像都会导致泄漏。

然后我明白了：我确切地知道再现错误的容器镜像集。是我们 dogfoog 集群里的那个。我克隆了数据库，这样我的测试就不会中断其他用户或删除任何数据，然后在我自己的工作区中使用调试器针对克隆的数据运行后台作业。

就这么干。

使用调试器逐步检查该任务，我可以看到泄漏的 goroutine。我能从历史信息中读出它的记忆。从请求 URL，我可以知道它是什么图像。僵尸不再是无名氏了！但是，事情已经完成了，goroutine 泄露了。我还是得找到凶手。

有了容器镜像的知识，我再次运行该任务，在顶层添加一些代码，跳过所有内容，但我知道导致泄漏的代码除外。我还在 HTTP 传输 RoundTripper 中添加了一个断点，以便在每个 HTTP 请求上中断。我的断电已经设好，我埋伏着等待行凶者。我知道我接近了真相。

当 HTTP 请求进来时，我点击、点击、点击我的断点，等待我知道的确切的 URL 作为触发器。然后，我有了它：bug 所在的调用堆栈。

正如我们所怀疑的：一个丢失的 `response.Body.Close()`。[修复的PR是一行](https://github.com/google/go-containerregistry/pull/1482)。花了这么多精力，只写一行代码就有点诗意了。

![](https://www.datocms-assets.com/19109/1667325250-output-onlinepngtools-3.png?fit=clip&fm=webp&w=768)

结果不言自明（google/go-containerregistry 仓库的一个 bug）。

## 关键要点

虽然每一个泄漏的代码都以自己的方式泄漏，但许多泄漏探测技术和分析工具都是通用的。

1. 监控你的服务是否存在泄漏。检查每个 Go 软件的关键资源包括： a.内存 b.协程 c.文件描述符（打开的文件）
2. 根据你的应用程序，你可能还需要监视：a.磁盘空间 b.Inodes c.子进程 d.应用程序使用的特殊资源（IP地址?）
3. 看看资源泄漏的速度：a.速率与负载相关吗?可能与你的服务的请求路径相关 b.速率是否与负载无关?可能是一份后台任务
4. 避免在完全相同的时间间隔上运行所有后台作业。使用素数以避免作业运行重叠。
5. 使用监控或日志记录后台作业的开始和结束时间；寻找这些时间和泄漏之间的相关性。
6. 如果可以，可以导出或克隆真实数据，在 IDE 中重现问题。

最后一点，请注意：克隆包含外部客户或用户数据的生产数据时要小心。 如果你完全不确定，请在复制数据之前咨询你的安全团队。 如果你在受监管的行业（金融、医疗保健等）经营或者是爬虫，情况就更是如此。

附注
[1] 使用你自己的产品通俗地称为 dogfooding，如“吃你自己的狗粮”。 [2] 不同人对什么是圆形有不同的看法。

