# Go 语言的垃圾回收

- 原文地址：https://agrim123.github.io/posts/go-garbage-collector.html
- 原文作者：**Agrim Mittal**
- 本文永久链接：
- 译者：[朱亚光](https://github.com/zhuyaguang)
- 校对：[haoheipi](https://github.com/haoheipi)

> Go \[>= v1.5\]的新垃圾回收器是一种并发的三色标记清除回收器，这个想法最早是由 [Dijkstra 在 1978](https://github.com/rubinius/rubinius-website-archive/blob/cf54187d421275eec7d2db0abd5d4c059755b577/_posts/2013-06-22-concurrent-garbage-collection.markdown) 年提出的。

Go 团队一直在密切关注并改进 Go 语言的垃圾回收器。从每 50 毫秒一次的 10 毫秒 STW 暂停到每次 GC 有两个 500μs 的 STW 暂停，整个改进过程可以在[这里](https://blog.golang.org/ismmkeynote)找到。

长期从事 Go 开发，我一直对其性能感到畏惧，因此我决定深入了解其中的机制，比如 Go 语言为什么如此高效和充满前途，了解它使用的是什么样的垃圾回收器，goroutine 如何在 OS 线程上多路复用，如何对 Go 程序进行性能分析，Go 运行时是如何工作的等等。在这篇文章中，我们将着重探讨 Go 的垃圾回收器是如何工作的。

在浏览互联网时，我发现了很多关于 Go 语言垃圾回收器的赞誉，而我对垃圾回收器的概念和工作原理只有一个抽象的理解，于是我开始阅读和学习，并在[这里](https://agrim123.github.io/posts/garbage-collection.html)记录了一些关于垃圾回收的笔记。

这篇博客仅仅是我在阅读一些关于 Go 的垃圾回收器及其演变历程的博客后整理出的一些想法和结论的随笔。

所以，让我们开始吧。

```plain
紧紧抓住，伙计，这将是一场精彩的旅程。
```

## 一点前置知识

Go 是一种以 C 类系统语言为传统的值传递语言，而不是以大多数托管运行时语言为传统的引用导向语言。值导向还有助于外部函数接口。这可能是 Go 与其他 GC 语言不同的最重要因素。

Go 是一种内存管理语言，这意味着大多数时候你不必担心手动内存管理，因为运行时会为你完成大量工作。然而，动态内存分配并不免费，程序的分配模式可以显著影响其性能：

> Go 二进制文件包含整个运行时且没有[即时编译](https://en.wikipedia.org/wiki/Just-in-time_compilation)。

因为这个原因，最基本的 Go 二进制文件通常[很大](https://golang.org/doc/faq#Why_is_my_trivial_program_such_a_large_binary)。

## 垃圾回收简史

最初的垃圾回收算法是为单处理器机器和堆很小的程序设计的，由于 CPU 和 RAM 是昂贵的，所以用户对可见的 GC 暂停没有问题。当 GC 进来时，你的程序会停止，直到完成堆的全面标记/清除。这种类型的算法在不回收时不会降低你的程序速度，也不会增加内存开销。

简单的 STW 标记/清除的问题在随着你增加核心和扩大你的堆或分配率时会变得非常糟糕。

## Go 的并发收集器

Go 现在的 GC 不是 **“分代”回收** （一种垃圾回收算法）的。它只在后台运行一个普通的标记/清除。这有一些缺点：

- **GC 吞吐量**：程序使用的内存越多，释放已使用内存所需的时间就越多，电脑进行回收的时间与有效工作的时间就越多。
- **整理**：由于没有整理，程序最终可能导致堆的碎片化。
- **程序吞吐量**：由于 GC 需要为每个周期完成大量工作，这会消耗 CPU 时间，从而减慢程序的速度。
- **并发模式故障**：当程序生成的垃圾比 GC 线程清理的快时，会发生这种情况。在这种情况下，运行时没有其他选择，只能停止程序并等待 GC 完成它的工作！[参考文献](https://hellokangning.github.io/en/post/what-is-the-concurrent-mode-failure/)。 要防止这种情况，您需要确保有大量空间，从而增加堆的开销。

## 收集器行为

> Go 的垃圾回收是在程序运行时并发进行的。

等候多时了，让我们看看收集器是如何工作的。

在收集开始时，收集器将经过三个工作阶段。其中两个阶段会导致 Stop The World（STW）延迟，另一个阶段会导致应用程序吞吐量减慢的延迟。

### 标记设置(STW)

当垃圾回收开始时，第一个必须执行的活动是打开写保护（Write Barrier）。这允许在垃圾回收期间在堆上保持数据完整性，因为回收器和应用程序的 goroutine 将同时运行。要打开写保护，必须停止运行的每个应用程序 goroutine。此活动通常非常快，平均每 10 到 30 微秒。这当然前提是应用程序 goroutine 表现正常。

假设在 GC 即将触发之前有 4 个 goroutine 正在运行。回收器必须停止每个 goroutine 以进行工作。唯一的方法是回收器监视并等待每个 goroutine 调用函数。函数调用保证 goroutine 处于安全点以被停止。如果其中一个 goroutine 没有调用函数（比如正在执行[紧密循环操作](https://stackoverflow.com/a/2213001)），那么会发生什么？

例如，第 4 个 goroutine 正在执行以下代码：

```go
func stubbornGoroutine(numbers []int32) int {
    var r int32
    for _, v := range numbers {
        // some operation to r
    }

    return r
}
```

这种情况可能会导致垃圾回收无法开始。因为当收集器等待时，其他处理器不能服务任何其他协程。因此，协程必须在合理的时间内进行函数调用。

> 如果一个 goroutine 没有调用函数，它不会被抢占，并且在任务结束之前它的 P 不会释放。这将迫使 “Stop the World” 等待它。

### 标记阶段 (并发)

在开启写保护器后，回收器开始标记阶段。

首先，回收器为其自身保留了 25% 可用 CPU 容量 。回收器使用 Goroutine 执行回收工作，并需要应用程序 Goroutine 使用的相同的 P 和 M。

标记阶段包括标记堆内存中仍在使用的值。该工作首先通过检查所有现有 Goroutine 的堆栈以找到指向堆内存的根指针。然后，回收器必须从这些根指针遍历堆内存图。

#### Mark assist 

如果收集器确定它需要减缓分配，它将会招募应用程序的 Goroutine 协助 Marking 工作，这称为 Mark Assist。任何应用程序 Goroutine 在 Mark Assist 中的时间量与它对堆内存的数据添加量成比例。

> Mark Assist 可以帮助更快地完成收集。

收集器的一个目标是消除对 Mark Assist 的需求。如果任意一次收集最终需要大量的 Mark Assist，收集器可以更早开始下一次垃圾收集，以减少下一次收集所需的 Mark Assist 数量。

### 标记终止（STW）

一旦标记工作完成，下一阶段是标记终止。这个阶段将关闭写屏障，执行各种清理任务以及计算下一个回收目标的时刻。在标记阶段处于紧密循环的协程也可能导致标记终止 STW 延迟延长。

回收完成后，应用程序协程可以再次使用每个 P，应用程序将回到全速。

### 并发清除

在收集完成后，还有一个活动称为清除。清除是指回收未被标记为正在使用的堆内存中值所关联的内存。 当应用程序 Goroutine 尝试分配堆内存中的新值时，该活动会发生。 清除的延迟时间会被计入堆内存分配的成本中，并与垃圾回收任何相关的延迟无关。

![GC Algorithm Phases](https://agrim123.github.io/images/GC%20Algorithm%20Phases.png)

## 如何让运行时知道什么时候开始回收垃圾？

收集器有一个步伐算法，用于确定何时开始收集。节奏的建模类似于一个控制问题，它试图找到启动 GC 周期的正确时间，以达到目标堆大小目标。Go 的默认步伐控制器将尝试在堆大小加倍时触发 GC 周期。它通过在当前 GC 周期的标记终止阶段设置下一个堆触发大小来实现这一点。因此，在标记所有活动内存后，它可以决定在当前活动集的总堆大小是目前活动集的 2 倍时触发下一个 GC。2 倍的值来自运行时使用的变量`GOGC`，用于设置触发比率。

一种错误的观念是认为减缓收集器的速度是提高性能的方法。这个想法是，如果你可以延迟下一次收集的开始，那么你就是在延迟它造成的延迟。对收集器的同情并不是减缓节奏。

___

Go 1.5 在 2015 年 8 月发布，带有新的低暂停并发垃圾收集器，包括实现了[节奏算法](https://docs.google.com/document/d/1wmjrocXIWTr1JxU-3EQBI6BK6KgtiFArkG47XK73xIQ/edit#heading=h.4801yvqy4taz)。

___

## 采集器延迟成本

有两种类型的延迟会影响运行中的应用程序。

### 窃取 CPU 能力

这种夺走的 CPU 能力的影响意味着在回收过程中，您的应用程序不能全速运行。 应用程序 Goroutines 现在与收集器的 Goroutines 共享 P 或帮助收集（标记辅助）。

### STW 的潜在延迟

第二种被施加的延迟是收集过程中发生的 STW 延迟。 STW 时间是指应用程序协程未执行任何应用工作的时间。应用程序实际上已经停止。每次收集都会发生两次 STW。

___

减少 GC 延迟的方法是识别并删除应用程序中不必要的分配。这样可以从多个方面帮助收集器：

- 保持尽可能小的堆。
- 找到最佳的一致节奏。
- 最小化每次收集的持续时间、STW 和 Mark Assist。

## 有两个控制垃圾回收的开关

正如 Rick Hudson 在[该文](https://blog.golang.org/ismmkeynote)中谈到。

> 我们也不打算增加 GC API 的范围。我们已经运行了近十年，而且有两个开关，感觉已经足够了。没有一个应用程序对我们来说足够重要，以至于我们需要添加一个新的标志。

### GC 百分比

这调整了你想使用的 CPU 的数量以及您想使用的内存的数量。默认值为 100，这意味着堆的一半被用于存活内存，另一半用于分配。这可以向任一方向修改。

### 最大堆内存

MaxHeap 允许程序员设置最大堆大小。Go 对内存不足（OOM）的情况非常敏感；对于内存使用量的临时高峰，应通过增加 CPU 成本来解决，而不是终止。如果 GC 感到内存压力，它会通知应用程序应该释放负载。一旦事情恢复正常，GC 就会通知应用程序可以恢复正常负载。MaxHeap 还提供了更多的调度灵活性。运行时不再对可用内存的多少感到担心，可以将堆的大小调整到 MaxHeap。

___

Go 语言 GC 有一个很详细的说明文档，可以在源代码中[查看](https://github.com/golang/go/blob/master/src/runtime/mgc.go#L5-L127)。

___

这就是 Go 的垃圾回收器的概述。当然，这并不包括所有内容，我可能遗漏了一些要点，但我试图总结我所理解的一切。下面是我所遇到的一些非常好的参考资料，请一定要看一看！

## 参考资料

-   [Getting to Go: The Journey of Go’s Garbage Collector](https://blog.golang.org/ismmkeynote)
-   [The Tail at Scale](https://research.google/pubs/pub40801/)
-   [runtime: tight loops should be preemptible](https://github.com/golang/go/issues/10958#issue-81098230)
-   [Go GC: Prioritizing low latency and simplicity](https://blog.golang.org/go15gc)
-   [Why golang garbage-collector not implement Generational and Compact gc?](https://groups.google.com/forum/m/#!topic/golang-nuts/KJiyv2mV2pU)
-   [Modern garbage collection: A look at the Go GC strategy](https://blog.plan99.net/modern-garbage-collection-911ef4f8bd8e#.674yqu7mr)
-   [Golang’s Real-time GC in Theory and Practice](https://making.pusher.com/golangs-real-time-gc-in-theory-and-practice/)
-   [GopherCon 2018 - Allocator Wrestling](https://about.sourcegraph.com/go/gophercon-2018-allocator-wrestling)