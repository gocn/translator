# Go runtime: 4 years later

- 原文地址：https://go.dev/blog/go119runtime
- 原文作者：Michael Knyszek
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2022/w43_Go_runtime_4_years_later.md
- 译者：[iddunk](https://github.com/iddunk)
- 校对：

自从我们发布 [2018 年关于 Go GC 的最后一篇博文](https://go.dev/blog/ismmkeynote) 以来，Go GC 和 Go 运行时一直在稳步改进。 我们已经处理了一些大型项目，这些项目是真实的 Go 程序和 Go 用户实际面临的挑战。 让我们来带你看看这些亮点！

### 一些新变化

- `sync.Pool` 是一个 GC 感知工具，用于重用内存，相比之前它现在具有 [更低的延迟](https://go.dev/cl/166960) 和 [更有效地内存回收](https://go. dev/cl/166961) 。 （Go 1.13）
- Go 运行时 [更主动地](https://go.dev/issue/30333) 将不需要的内存返还给操作系统，从而减少了过多的内存消耗和内存不足错误的可能性。 这能减少多达 20%的空闲内存消耗。 （Go 1.13 和 Go1.14）
- 在许多情况下，Go 运行时能够更容易地抢占 goroutine，从而将 stop-the-world 延迟降低多达 90%。 [在此处观看 Gophercon 2020 的演讲。](https://www.youtube.com/watch?v=1I1WmeSjRSw) (Go 1.14)
- Go 运行时 [比以前更有效地管理计时器](https://go.dev/cl/171883)，尤其是在多核 CPU 机器上。 （Go 1.14）
- 在大多数情况下，使用 `defer` 语句延迟调用的函数现在与常规函数调用成本一样少。 [在此处观看 Gophercon 2020 的演讲。](https://www.youtube.com/watch?v=DHVeUsrKcbM) (Go 1.14)
- 内存分配器的慢速路径 [规模化](https://go.dev/issue/35112) [更适合](https://go.dev/issue/37487) CPU 内核，这将吞吐量提高到 10% 并减少了 30% 的尾部延迟，尤其是在高并发的程序中。 （Go 1.14 和 Go1.15）
- Go 内存统计信息现在可以通过更精细、灵活和高效的 API 访问，即 [runtime/metrics](https://pkg.go.dev/runtime/metrics) 包。 这将获取运行时统计信息的延迟降低了两个数量级（毫秒到微秒）。 （Go 1.16）
- Go 调度程序花费 [减少 30% 的 CPU 时间来调度](https://go.dev/issue/43997)。 （Go 1.17）
- Go 代码现在在 amd64、arm64 和 ppc64 上遵循 [基于寄存器的调用约定](https://go.dev/issues/40724)，将 CPU 效率提高了 15%。 （Go 1.17 和Go 1.18）
- Go GC 的内部计数和调度已经[重新设计](https://go.dev/issue/44167)，解决了与效率和健壮性相关的各种长期存在的问题。 对于 goroutine 堆栈占内存使用量很大一部分的应用程序，这会显著降低应用程序尾部延迟（高达 66%）。 （Go 1.18）
- Go GC 现在限制了 [当应用程序空闲时 CPU 的使用](https://go.dev/issue/44163)。 这样做的结果就是非常空闲的应用程序在 GC 时其 CPU 利用率降低了 75%，从而减少了可能使用户感到困惑的 CPU 峰值。 （Go 1.19）

这些变化对用户来说大多是不可见的：他们知道让 Go 代码运行得更好，只需升级 Go。

### 一个新的旋钮

Go 1.19 带来了一个长期要求的功能，它需要一些额外的工作才能使用，但同时它具有很大的潜力：[Go 运行时的软内存限制](https://pkg.go.dev/runtime/debug#SetMemoryLimit) .

多年来，Go GC 只有一个调优参数：`GOGC`。 `GOGC` 让用户可以调整 [Go GC 在 CPU 开销和内存开销之间的权衡](https://pkg.go.dev/runtime/debug#SetGCPercent)。 多年来，这个“旋钮”一直很好地服务于 Go 社区，社区中存在着各种各样的用例。

Go 运行时团队一直不愿意在 Go 运行时中添加新的旋钮，这是有充分理由的：每个新旋钮都代表了我们需要测试和维护的配置空间中的一个新的*维度*，而且这可能是永远的。 旋钮的激增也给 Go 开发人员带来了理解和使用它们的负担，随着旋钮的增多，这会变得更加困难。 因此，Go 运行时总是倾向于以最少的配置合理地运行。

那么为什么要添加内存限制旋钮呢？

内存不像 CPU 时间片那样可替代。 CPU 时间片，只要你稍等片刻，总会拥有更多的时间片。 但是内存不一样，你所拥有的是有限度的。

内存限制解决了两个问题。

首先是当应用程序的内存使用峰值不可预测时，单独的 `GOGC` 几乎无法提供内存不足的保护。 仅使用 `GOGC` ，Go 运行时根本不知道它有多少可用内存。 设置内存限制使运行时能够知道何时需要更努力地工作以减少内存开销，从而对瞬态、可恢复的负载峰值保持稳健。

二是在不使用内存限制的情况下避免内存溢出错误，`GOGC` 必须根据内存峰值进行调优，导致需要更高的GC CPU开销来维持较低的内存开销，即使应用程序并没有达到内存峰值，并且有足够的可用内存。 这在我们的容器化世界中尤其重要，程序被放置在具有特定和隔离内存预留的沙盒中； 我们不妨利用它们！ 通过提供对负载峰值的保护，设置内存限制允许 `GOGC` 在 CPU 开销方面进行更积极的调整。

内存限制旨在易于使用且稳健。 例如，它限制了应用程序的 Go 部分的整个内存占用，而不仅仅是 Go 堆，因此用户不必担心考虑 Go 运行时开销。 运行时还会根据内存限制调整其内存清理策略，以便更主动地将内存返还给操作系统以响应内存压力。

虽然内存限制是一个强大的工具，但是你仍需谨慎使用它。 其中一个大问题就是它会使你的程序面临 GC 抖动：程序花费太多时间执行 GC ，导致没有足够的时间花在有意义的进展上。 例如，如果将内存限制设置得太低而无法满足程序实际需要的内存量，Go 程序可能会崩溃。 GC 抖动在以前是不太可能发生的事情，除非 `GOGC` 被显式调整。 我们选择内存不足而不是抖动，因此作为一种缓解措施，运行时会将 GC 限制为总 CPU 时间的 50%，即使这意味着超出内存限制。

所有这一切都需要考虑很多，因此作为这项工作的一部分，我们发布了[一个闪亮的新 GC 指南](https://go.dev/doc/gc-guide)，其中包含可视化交互以帮助你理解 GC 成本以及如何操纵它们。

### 结论

试试内存限制！ 在生产中使用它！ 阅读 [GC 指南](https://go.dev/doc/gc-guide)！

我们一直在寻找有关如何改进 Go 的反馈，同时这也有助于你了解它何时能为你工作。 [给我们反馈](https://groups.google.com/g/golang-dev)！