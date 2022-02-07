# 为忙碌开发者准备的 Go 语言性能分析、追踪和可观测性指南

- 原文地址：https://github.com/DataDog/go-profiler-notes/blob/main/guide/README.md
- 原文作者：Felix Geisendörfer
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w36-The_Busy_Developers_Guide_to_Go_Profiling_Tracing_and_Observability.md
- 译者：[cvley](https://github.com/cvley)
- 校对：[朱亚光](https://github.com/zhuyaguang)

- **[简介](#简介):** [本文内容](#read-this) · [Go 语言的心智模型](#mental-model-for-go) · 性能分析与追踪
- **使用场景：** 降低成本 · 降低延迟 · 内存泄露 · 程序挂起（Hanging） · 中断
- **Go 性能分析**： CPU · 内存 · Block · Mutex · Goroutine · ThreadCreate
- **性能分析可视化**： 命令行 · 火焰图 · 浏览器图
- **Go 执行追踪：** 时间线可视化 · 派生分析
- **其他工具：** time · perf · bpftrace
- **高级话题：** 汇编 · 栈追踪
- **Datadog 产品：** 持续性能分析器 · APM （分布式追踪）

🚧 本文还在不断撰写过程中。上面列出的部分会陆续有对应的可点击的地址。关注我的 [twitter](https://twitter.com/felixge) 获取更多进展。

# 简介

## 本文内容

本文是实践指南，目标读者是那些想要通过使用性能分析和追踪技术来提升程序的忙碌 gopher 们。如果你还不熟悉 Go 的内部原理，建议你先阅读整个简介。之后你就可以自由阅读感兴趣的章节。
## Go 的心智模型

在不理解 Go 语言底层运行机制的情况下，成为一个熟练编写 Go 代码的开发者是可能的。但当面对性能分析和调试时，理解内部的心智模型将大有裨益。因此下面我们将展示 Go  的基础模型。这个模型应该足够让你避免绝大多数常见的错误，但是 [所有的模型都是错误的](https://en.wikipedia.org/wiki/All_models_are_wrong)，因此鼓励你探索更深层的资料，以便在将来解决更难的问题。

Go 的首要工作是复用和抽象硬件资源，与操作系统相似。通常使用两个主要的抽象来实现：

1. **Goroutine 调度器：** 管理代码如何在系统的 CPU 上执行。
2. **垃圾回收器：**提供虚拟内存，在需要时自动释放。


### Goroutine 调度器

我们先使用下面的例子来讨论调度器：

```go
func main() {
    res, err := http.Get("https://example.org/")
    if err != nil {
        panic(err)
    }
    fmt.Printf("%d\n", res.StatusCode)
}
```

上面我有一个运行 `main` 函数的 goroutine，称之为 `G1`。下图展示了这个 goroutine 可能在单个 CPU 上执行的简化版的时间线。首先在 CPU 上运行的 `G1` 用于准备 http 请求。接下来在 goroutine 等待网络时， CPU 变成闲置（idle）状态。最后它会再次被调度到 CPU 上并打印出状态码。

<img src="../static/images/w36-The_Busy_Developers_Guide_to_Go_Profiling_Tracing_and_Observability/timeline.png" width=600/>

从调度器的角度看，上面的程序的执行情况如下图所示。首先， `G1`在 `CPU 1` 上 `执行`。接下来 goroutine 在`等待`网络时离开 CPU。一旦发现网络有响应（使用非阻塞 I/O，与 Node.js 相似），调度器将 goroutine 标记为 `可运行`。一旦 CPU 核可用，goroutine 会再次开始 `执行`。在我们的例子中，所有的 CPU 核都可用，所以 `G1` 不需要在`可运行`状态花费时间，就可以立即回到一个 CPU 上`执行` `fmt.Printf()` 函数。

<img src="../static/images/w36-The_Busy_Developers_Guide_to_Go_Profiling_Tracing_and_Observability/scheduler.gif" width=400/>

大多数情况下，Go 程序都运行多个 goroutines，因此会有一些 goroutines 在部分 CPU 核上`执行`，大量的 goroutines 因为各种原因`等待`，理想情况下没有 goroutines 在`可运行`状态，除非程序占用了非常高的 CPU 负载。示例如下图所示。

<img src="../static/images/w36-The_Busy_Developers_Guide_to_Go_Profiling_Tracing_and_Observability/scheduler-complete.png" width=600/>

当然上面的模型忽略了非常多的细节。实际上正相反，Go 调度器运行在操作系统管理的线程之上，甚至 CPU 本身也能够有超线程这样的调度形式。所以如果你感兴趣，可以通过 Ardan 的[Go 调度](https://www.ardanlabs.com/blog/2018/08/scheduling-in-go-part1.html) 这一实验室系列文章或相似的资料，像爱丽丝一样继续在这个兔子洞中继续探索。

然而，上面的模型已足够用于理解本文余下的内容。特别是可以明确一点，对于不同 Go 性能分析器所衡量的时间，本质上应该是 goroutine 在`执行`和`等待`状态上花费的时间，如下图所示。

<img src="../static/images/w36-The_Busy_Developers_Guide_to_Go_Profiling_Tracing_and_Observability/profiler-venn.png" width=800/>

### 垃圾回收器

Go 的另一个主要抽象是垃圾回收期。像 C 语言这样的语言，开发者需要通过`malloc()` 和 `free()`来手动分配和释放内存。这提供了巨大的控制权，但实际上却非常容易出错。垃圾回收器可以减少这个负担，但内存的自动管理很容易成为性能瓶颈。这部分内容将展示 Go 语言 GC 的一个简单模型，对于发现和优化内存管理相关的问题非常有用。

#### 堆栈

我们从基础开始。Go 可以在两个地方分配内存，栈或堆。各个 goroutine 都有各自的栈，它们是内存的一段连续区域。此外还有一大块可以 goroutine 间共享的内存区域，叫做堆。如下图所示。

<img src="../static/images/w36-The_Busy_Developers_Guide_to_Go_Profiling_Tracing_and_Observability/heap-simple.png" width=650/>

当一个函数调用另一个函数时，它会获取自身栈上叫做栈帧的区域，用于存放局部变量。栈指针用于标示帧中下一个可用的位置。当函数返回时，通过将栈指针移回到之前帧的末尾这个简单的方法，将最后帧中的数据丢弃。帧中的数据本身还会存在于栈上，并在下次函数调用时被覆盖。这么做非常简单高效，因为 Go 不需要追踪每个变量。

为了更直观地表述，我们来看下面的例子：

```go
func main() {
	sum := 0
	sum = add(23, 42)
	fmt.Println(sum)
}

func add(a, b int) int {
	return a + b
}
```

其中，我们有个 `main()` 函数，开始时会在栈上为变量 `sum` 预留一些空间。当 `add()` 函数被调用时，它会在自己的帧上保留局部的 `a` 和 `b` 参数。一旦 `add()` 函数返回，栈指针会移回到`main()`函数帧的末尾，这样数据就被丢弃了，而 `sum` 变量会更新为结果的值。同时 `add()` 的旧值在下次函数调用重写覆盖栈指针之前，还会保留。下图是这个过程的可视化图： 

<img src="../static/images/w36-The_Busy_Developers_Guide_to_Go_Profiling_Tracing_and_Observability/stack.gif" width=400/>

上面的例子是对返回值、帧指针、返回地址和函数嵌入等地高度简化，并省略了大量细节。实际上，在 Go 1.17 中，上面的程序可能并不会需要任何栈空间，因为编译器可以使用 CPU 寄存器来管理小量的数据。但这样没问题。这个模型对于重要的 Go 程序分配和丢弃栈上局部变量的方式依旧有意义。

此时你可能想知道的一点是，如果栈上的空间用完了会发生什么。在像 C 这样的语言中，这会导致一个栈溢出的错误。而 Go 可以通过复制出一个 2 倍的栈来自动解决这个问题。这让 goroutines 可以使用非常小，一般 2KiB 的栈空间来启动，而这也是[让 goroutines 比操作系统线程更可扩展](https://golang.org/doc/faq#goroutines)的成功因素。

栈的另一个要素是用于创建栈追踪的方式。这有点过于高级，但如果你感兴趣，可以查阅本项目的[Go 栈追踪](../stack-traces.md) 的文档。
#### 堆

栈分配很棒，但在许多场景下 Go 却无法使用。最常见的一个就是返回一个函数的局部变量的指针。把上面的 `add()` 示例做些修改，就可以看到这个问题：

```go
func main() {
	fmt.Println(*add(23, 42))
}

func add(a, b int) *int {
	sum := a + b
	return &sum
}
```

正常情况下，Go 可以在 `add()` 函数内部的栈上分配 `sum` 变量。但正如我们所知，这个数据在 `add()` 函数返回时会被丢弃。因此为了安全地返回 `&sum` 指针，Go 需要在栈外的内存上为它分配空间。而这就是堆的来源。

堆用于存储那些生命周期长于创建它们的函数的内存，也包括那些使用指针在 goroutine 间共享的数据。然而，这会抛出这块内存如何释放的问题。因为不像栈的分配，堆的分配在创建它们的函数返回时并不会丢弃它们。

Go 使用内建的垃圾回收器解决这个问题。它的实现细节非常复杂，但粗略来看，它会如下图一样追踪内存的使用情况。其中你可以看到，对于堆上的绿色分片空间，有三个 goroutine 有指针指向它们。这些分配的空间，有一些也会通过指针指向其他绿色的分配空间。另外，灰色分配空间可能会指向绿色分片空间，或者互相指向但并不被绿色分配空间所引用。这些分配空间曾经可以访问，但现在被认为是垃圾。当分配栈指针的函数返回时，或值被覆盖重写时，就会发生这种情况。GC 的职责是自动发信并释放这些分配空间。

<img src="../static/images/w36-The_Busy_Developers_Guide_to_Go_Profiling_Tracing_and_Observability/heap-gc.gif" width=650/>

GC 操作包括大量耗时的图遍历和缓存命中。它甚至包括了停止整个程序执行的  stop-the-world 的阶段。幸运的是，Go 的最近版本已经把这个耗时降低毫秒之下，但许多剩余的问题与 GC 有关。事实上，一个 Go 程序 20%

-30% 的执行时间都花在内存管理上，而这非常常见。

一般来说，GC 的花费与程序进行的堆分配空间成正比。因此当优化程序内存相关的情况时，箴言如下：

- **降低**: 尝试将堆内存分配改为栈内存分配，或避免同时发生两种分配的情况。
- **重用:** 重复使用堆分配空间，而不是使用新的空间。
- **循环:** 对于无法避免的堆分配，让 GC 来循环并关注于其他问题。

正如本篇指南中前面的心智模型所说，上面的所有内容都是实际情况的超级简化。但希望它对于剩余部分足够有意义，能启发你阅读更多相关内容的文章。其中一篇你应该阅读的是[了解 Go：Go 垃圾回收器之旅](https://go.dev/blog/ismmkeynote)，它提供了 Go GC 逐年发展的内容和提升规划。

# 免责声明

我是 [felixge](https://github.com/felixge)，就职于 [Datadog](https://www.datadoghq.com/) ，主要工作内容为 Go 的 [持续性能优化](https://www.datadoghq.com/product/code-profiling/)。你应该了解下。我们也在[招聘](https://www.datadoghq.com/jobs-engineering/#all&all_locations) : ).

本页面的信息可认为正确，但不提供任何保证。欢迎反馈！

<!--
注意：

- 堆：这个链接可能是一篇不错的文章：https://medium.com/@ankur_anand/a-visual-guide-to-golang-memory-allocator-from-ground-up-e132258453ed
- GC 开销：对于包含指针的堆内存实时分配的情况下为 O(N)。
- 每个指针的分配都有开销！即使是 nil 指针。
- 降低开销：讨论 CPU、内存和网络。是否有可能在后面的地方提及？

-->
