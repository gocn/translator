# 理解Go中的内存分配

- 原文地址：https://medium.com/eureka-engineering/understanding-allocations-in-go-stack-heap-memory-9a2631b5035d
- 原文作者：James Kirk
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[](https://example.com)
***

## 介绍

由于 Go 运行时内置了高效的内存管理，我们通常能够优先考虑程序的正确性和可维护性，而无需过多考虑内存分配的细节。但有时，我们可能会发现代码中的性能瓶颈，并希望深入研究。

当使用 `-benchmem` 标志运行基准测试，就会在输出中看到如下所示的 `allocs/op` 统计。在这篇文章中，我们将了解什么算作分配以及我们可以采取哪些措施来影响这个数字。

```plain
BenchmarkFunc-8  67836464  16.0 ns/op  8 B/op  1 allocs/op
```

## 大家熟知的堆和栈

为了讨论 Go 中的 `allocs/op` 统计，我们将对 Go 程序中的两个内存区域进行探究：堆和栈。

在许多流行的编程语言中，栈通常指线程的调用栈。调用栈是一种 LIFO 的数据结构，用于存储参数、局部变量以及线程执行函数时跟踪的其他数据。每次函数调用都会向栈添加（推入）一个新帧，每次函数返回都会从栈中删除（弹出）。

当最近的栈帧弹出时，我们必须要确保能够安全地释放它的内存。因此，我们不能在堆栈上存储以后需要在其他地方引用的任何内容。

![](https://miro.medium.com/v2/resize:fit:1400/1*t4_KKb6fEkINGsTwbcuk5w.png)

上图为调用 `println` 后某个时间的调用栈视图。

由于线程由操作系统管理，因此线程栈可用的内存量通常是固定的，例如，在许多 Linux 环境中默认为 8MB。这意味着我们还需要注意栈上最终有多少数据，特别是在深度嵌套递归函数的情况下。如果上图中的栈指针超出栈保护界线，程序将因栈溢出错误而崩溃。

_堆_ 是一个更复杂的内存区域，这与数据结构中的堆无关。我们可以按需使用堆来存储程序中需要的数据。此处分配的内存不能在函数返回时简单地释放，需要仔细管理以避免内存泄漏和碎片。堆通常会比任何线程栈大很多倍，大部分优化工作都在研究堆的使用上。

## Go 中的栈和堆

由操作系统管理的线程在 Go 运行时被抽象了出来，使用一个新的抽象：goroutines。Goroutine 在概念上与线程非常相似，但它们存在于用户空间中。这意味着运行时（而不是操作系统）设置了堆栈行为的规则。

![](https://miro.medium.com/v2/resize:fit:1400/1*20Pk1_PXMWm_jMfPpCMfUg.png)



Goroutine 堆栈不再遵循操作系统设置的硬限制，而是以少量内存（当前为 2KB）开始。在执行每个函数调用之前，函数序言中会执行检查以验证不会发生堆栈溢出。在下图中， `convert()` 函数可以在当前堆栈大小的限制内执行（栈指针不会超过 `stackguard0` ）。

![](https://miro.medium.com/v2/resize:fit:1400/1*nP17BbLqFA3LpyLGPDatgg.png)

上图为 Goroutine 的调用堆栈特写

如果会超过 `stackguard0`，运行时将会在执行之前将 `convert()` 当前堆栈复制到新的更大的连续内存空间。这意味着 Go 中的堆栈是动态调整大小的，并且通常只要有足够的内存可以满足它们，就可以不断增长。

Go 堆在概念上再次类似于上述线程模型。所有 goroutine 共享一个公共堆，任何无法存储在栈中的内容都将最终存放在那里。当正在基准测试的函数中发生堆分配时，我们将看到`allocs/ops` 统计数加一。垃圾回收器的工作就是稍后释放掉不再引用的堆变量。

有关 Go 中如何处理内存管理的详细说明，请参阅[Go 内存分配器可视化指南](https://medium.com/@ankur_anand/a-visual-guide-to-golang-memory-allocator-from-ground-up-e132258453ed)。

## 我们如何知道变量何时分配到堆？

这个问题在[官方FAQ](https://golang.org/doc/faq#stack_or_heap)中有解答。

> Go 编译器将在该函数的栈帧中分配该函数的本地变量。但是，如果编译器无法证明函数返回后该变量未被引用，则编译器必须在垃圾回收堆上分配该变量以避免悬空指针错误。此外，如果局部变量非常大，将其存储在堆上而不是栈上可能更有意义
> 
> 如果一个变量已经分配地址，那么该变量就是在堆上分配的候选变量。然而，基本的逃逸分析可以识别某些情况，即此类变量不会在函数返回之后继续存在，就可以驻留在栈上。

由于编译器的实现会随着时间推移而变化，**因此无法仅通过阅读 Go 代码来知道哪些变量将分配到堆中**。但是，可以在编译器的输出中查看上述逃逸分析的结果。`gcflags` 可以通过传递参数给 `go build` 来实现。可以通过 `go tool compile -help` 查看完整的选项列表。

对于逃逸分析结果，可以使用 `-m` 选项 (`打印优化策略`)。让我们用一个简单的程序来测试这一点，该程序为函数 `main1` 和 `stackIt` 创建两个栈帧。

```plain
func main1() {
   _ = stackIt()
}
//go:noinline
func stackIt() int {
   y := 2
   return y * 2
}
```

由于如果编译器删除了函数调用，我们就无法讨论栈行为，因此编译代码时会使用 `noinline` [编译指令](https://dave.cheney.net/2018/01/08/gos-hidden-pragmas)来防止内联。让我们看一下编译器对其优化决策的结果。`-l` 选项用于省略内联。

```plain
$ go build -gcflags '-m -l'
# github.com/Jimeux/go-samples/allocations
```

在这里我们看到没有做出关于逃逸分析的优化策略。换句话说，变量 `y` 会保留在栈上，并且没有触发任何堆分配。我们可以通过基准来验证这一点。

```plain
$ go test -bench . -benchmem
BenchmarkStackIt-8  680439016  1.52 ns/op  0 B/op  0 allocs/op
```

正如预期的那样，`allocs/op` 统计数据为 `0`。从这个结果中我们可以得出的一个重要观察结果是，**复制变量可以让我们将它们保留在栈上并避免分配到堆**。让我们通过修改程序以避免使用指针进行复制来验证这一点。

```plain
func main2() {
   _ = stackIt2()
}
//go:noinline
func stackIt2() *int {
   y := 2
   res := y * 2
   return &res
}
```

让我们看看编译器的输出。

```plain
go build -gcflags '-m -l'
# github.com/Jimeux/go-samples/allocations
./main.go:10:2: moved to heap: res
```

编译器告诉我们它将 `res` 指针移至堆，触发堆分配，如下面的基准测试所示

```plain
$ go test -bench . -benchmem
BenchmarkStackIt2-8  70922517  16.0 ns/op  8 B/op  1 allocs/op
```

那么这是否意味着指针可以保证发生内存分配？让我们再次修改程序，这次将指针传递到栈中。

```plain
func main3() {
   y := 2
   _ = stackIt3(&y) // pass y down the stack as a pointer
}

//go:noinline
func stackIt3(y *int) int {
   res := *y * 2
   return res
}
```

然而运行基准测试显示没有任何内容分配给堆。

```plain
$ go test -bench . -benchmem
BenchmarkStackIt3-8  705347884  1.62 ns/op  0 B/op  0 allocs/op
```

编译器输出明确地告诉我们这一点。

```plain
$ go build -gcflags '-m -l'
# github.com/Jimeux/go-samples/allocations
./main.go:10:14: y does not escape
```

为什么会出现这种看似不一致的情况？`stackIt2` 将 `res` 向上传递到 `main`，在 `stackIt2`的栈帧已被释放后 `y` 仍将被引用。因此编译器判断 `y` 必须移动到堆中才能保持活动状态。如果它不这样做，那么在 `main` 中引用时就 `y` 不会存在。

而 `stackIt3`，`y` 向下传递到栈中，并且 `y` 不会在 `main3` 外任何地方引用。因此编译器判断 `y` 可以单独存在于栈中，而不需要分配到堆中。在任何情况下，通过引用 `y` ，我们都不会产生 nil 指针。

**我们可以从中推断出一个一般规则：向上传递栈结果的共享指针会导致分配，向下传递栈的共享指针则不会。** 但是，这并不能得到保证，因此您仍然需要使用 `gcflags` 或基准进行验证才能确定。我们可以肯定地说，任何减少 `allocs/op` 的尝试都将涉及寻找野生指针。

## 为什么我们关心堆分配？

我们已经了解了一些关于 `allocs/op` 的含义，以及如何验证是否触发了对堆的分配，为什么我们首先应该关心这个统计数据是否非零呢？我们可以用已经完成的基准测试来回答这个问题。

```plain
BenchmarkStackIt-8   680439016  1.52 ns/op  0 B/op  0 allocs/op
BenchmarkStackIt2-8  70922517   16.0 ns/op  8 B/op  1 allocs/op
BenchmarkStackIt3-8  705347884  1.62 ns/op  0 B/op  0 allocs/op
```

尽管所涉及的变量的分配内存没有太大差距，但 `BenchmarkStackIt2` 的 CPU 开销却很明显。我们可以通过生成和实现 `stackIt` 和 `stackIt2` 的 CPU 剖析火焰图来获得更多内容。

![](https://miro.medium.com/v2/resize:fit:1400/1*czZGGPLuR-wsNt22Vf2PdQ.png)



![](https://miro.medium.com/v2/resize:fit:1400/1*yj-4slhJ0L9lUxZG4gFxjQ.png)



`stackIt` 剖析正如预见地，沿着调用栈运行到 `stackIt` 函数本身。而 `stackIt2` ，使用了大量运行时函数，这些函数会消耗许多额外的 CPU 周期。这展示了分配到堆所涉及的复杂性，并初步了解每个操作额外的 10 纳秒左右的时间去了哪里。

## 那么在现实世界中呢？

如果没有生产条件，性能的许多方面都不会显现出来。您的单个函数可能在微基准测试中高效运行，但是当它为数千个并发用户提供服务时，它会对您的应用程序产生什么影响？

我们不会在这篇文章中重新创建整个应用程序，但我们将使用跟踪工具来了解一些更详细的性能诊断。让我们首先定义一个具有九个字段的（有点）大的结构。

```plain
type BigStruct struct {
   A, B, C int
   D, E, F string
   G, H, I bool
}
```

现在我们将定义两个函数：`CreateCopy`函数，它在栈帧之间复制 `BigStruct` 实例；以及 `CreatePointer` 函数，它共享栈上的 `BigStruct` 指针，避免复制，但会导致堆分配。

```plain
//go:noinline
func CreateCopy() BigStruct {
   return BigStruct{
      A: 123, B: 456, C: 789,
      D: "ABC", E: "DEF", F: "HIJ",
      G: true, H: true, I: true,
   }
}
//go:noinline
func CreatePointer() *BigStruct {
   return &BigStruct{
      A: 123, B: 456, C: 789,
      D: "ABC", E: "DEF", F: "HIJ",
      G: true, H: true, I: true,
   }
}
```

我们可以用目前使用的技术来验证上面的解释。

```plain
$ go build -gcflags '-m -l'
./main.go:67:9: &BigStruct literal escapes to heap
$ go test -bench . -benchmem
BenchmarkCopyIt-8     211907048  5.20 ns/op  0 B/op   0 allocs/op
BenchmarkPointerIt-8  20393278   52.6 ns/op  80 B/op  1 allocs/op
```

以下是我们将用于 `trace` 工具的测试结果。我们使用具有各自 `Create` 功能来创建 20,000,000 个 `BigStruct`。

```plain
const creations = 20_000_000

func TestCopyIt(t *testing.T) {
   for i := 0; i < creations; i++ {
      _ = CreateCopy()
   }
}

func TestPointerIt(t *testing.T) {
   for i := 0; i < creations; i++ {
      _ = CreatePointer()
   }
}
```

接下来，我们将 `CreateCopy` 跟踪输出保存到文件 `copy_trace.out`，并使用浏览器中的工具打开。

```plain
$ go test -run TestCopyIt -trace=copy_trace.out
PASS
ok   github.com/Jimeux/go-samples/allocations 0.281s
$ go tool trace copy_trace.out
Parsing trace...
Splitting trace...
Opening browser. Trace viewer is listening on http://127.0.0.1:57530
```

从菜单中选择 `View trace` 会向我们显示以下内容，这几乎与 `stackIt` 的火焰图一样不明显。八个逻辑核 (Procs) 中仅使用了两个，并且 goroutine G19 将绝大部分时间都花在运行循环上——这正是我们想要的。

![](https://miro.medium.com/v2/resize:fit:1400/1*NKzN-hax5TfP3PYsLzwozg.png)

跟踪 20,000,000 个 `CreateCopy` 调用

让我们生成 `CreatePointer` 代码的跟踪数据。

```plain
$ go test -run TestPointerIt -trace=pointer_trace.out
PASS
ok   github.com/Jimeux/go-samples/allocations 2.224s
go tool trace pointer_trace.out
Parsing trace...
Splitting trace...
Opening browser. Trace viewer is listening on http://127.0.0.1:57784
```

您可能已经注意到，`CreatePointer` 测试花费了 2.224 秒，而 `CreateCopy` 的测试花费了 0.281 秒，并且这次选择 `View trace` 显示的内容更加丰富多彩和忙碌。所有逻辑核心都被利用，并且堆操作、线程和 goroutine 似乎比上次多得多。

![](https://miro.medium.com/v2/resize:fit:1400/1*_DwGUNYyWcNJ_OlCi48ctA.png)

跟踪 20,000,000 个 `CreatePointer` 调用

如果我们放大到毫秒左右的跟踪范围，我们会看到许多 goroutine 执行与垃圾回收相关的操作。常见问题解答前面的引用使用了**垃圾回收堆**一词，因为垃圾回收器的工作是清理堆上不再被引用的任何内容。

![](https://miro.medium.com/v2/resize:fit:1400/1*9TJdonaURcVKcWb4WeaP1Q.png)

跟踪 `CreatePointer` 中 GC 活动的特写

尽管 Go 的垃圾回收器越来越高效，但这个过程并不是免费的。我们可以在上面的跟踪输出中直观地验证测试代码有时会完全停止。并非都如 `CreateCopy`，因为我们所有的 `BigStruct` 实例都保留在栈上，几乎没有 GC。

比较两组跟踪数据的 goroutine 分析可以更深入地了解这一点。`CreatePointer`（下面的图）花费了超过 15% 的执行时间来清理或暂停 (GC) 和调度 goroutine。

![](https://miro.medium.com/v2/resize:fit:1400/1*NaxhI4aXkyLh6ez9Nvqo3A.png)



![](https://miro.medium.com/v2/resize:fit:1400/1*DR8vDjAy8RkJfHxf9XlH0g.png)



查看跟踪数据中其他地方可用的一些统计数据，可以进一步说明堆分配的成本，生成的 Goroutine 数量存在明显差异，并且用于测试 `CreatePointer` 的 STW（stop the world）事件数量也接近 400 个。

```plain
+------------+------+---------+
|            | Copy | Pointer |
+------------+------+---------+
| Goroutines |   41 |  406965 |
| Heap       |   10 |  197549 |
| Threads    |   15 |   12943 |
| bgsweep    |    0 |  193094 |
| STW        |    0 |     397 |
+------------+------+---------+
```

尽管在典型程序中 `CreateCopy` 测试条件非常不现实。GC 使用一致数量的 CPU 是很正常的，并且指针是任何实际程序都会使用到的一个功能。然而，这让我们深入了解为什么我们想要跟踪统计 `allocs/op` 数据，并尽可能避免不必要的堆分配。

## 总结

希望这篇文章能让您深入了解 Go 程序中栈和堆之间的差异、`allocs/op` 统计的含义以及我们调查内存使用情况的一些方法。

我们代码的正确性和可维护性通常优先于减少指针使用和避免 GC 活动的棘手技术。现在每个人都知道关于过早优化的说法，Go 中的编码也不例外。

但是，如果我们确实有严格的性能要求或想以其他方式确定程序中的瓶颈，那么这里介绍的概念和工具将有望成为进行必要优化的有用起点。

如果您想尝试本文中的简单代码示例，请查看 [GitHub](https://github.com/Jimeux/go-samples/tree/master/allocations?source=post_page-----9a2631b5035d--------------------------------) 上的源代码和README。
