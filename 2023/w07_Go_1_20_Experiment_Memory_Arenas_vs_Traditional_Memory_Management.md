# Go 1.20 实验：内存 Arenas vs 传统内存管理

- 原文地址：[Go 1.20 Experiment: Memory Arenas vs Traditional Memory Management | Open Source Continuous Profiling Platform (pyroscope.io)](https://pyroscope.io/blog/go-1-20-memory-arenas/)
- 原文作者：[Dmitry Filimonov](https://github.com/petethepig)
- 本文永久链接：[translator/w07_Go_1_20_Experiment_Memory_Arenas_vs_Traditional_Memory_Management.md at master · gocn/translator (github.com)](https://github.com/gocn/translator/blob/master/2023/w07_Go_1_20_Experiment_Memory_Arenas_vs_Traditional_Memory_Management.md)
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：

![6](C:\Users\zhengxm\Documents\notes\翻译\static\images\2023\w07-Go-1-20-Experiment-Memory-Arenas-vs-Traditional-Memory-Management\6.png)

> **注意**
>
> Go arenas 是一个实验性功能。API 和实现完全不受支持，Go 团队不保证兼容性，也不保证在任何未来版本中继续存在。
>
> 请通过[这个 github 讨论区](https://github.com/golang/go/issues/51317#issuecomment-1385623024)来了解更多信息。

## 简介

Go 1.20 引入了一个实验性的内存管理概念 "arenas"，可以用来提高Go程序的性能。在本博客文章中，我们将探讨：

- 什么是arenas
- 它们是如何工作的
- 如何确定你的程序是否可以从使用arenas中受益
- 我们如何使用arenas优化我们的一项服务

## 什么是内存 Arenas

Go语言是一种利用垃圾回收机制的编程语言，这意味着运行时会自动管理程序员的内存分配和释放。这消除了手动内存管理的需求，但也带来了代价：

**Go 运行时必须跟踪 \*每个\* 分配的对象，导致性能开销增加。**

在某些情形下，例如 HTTP 服务器处理具有大量 protobuf blob（其中包含许多小对象）的请求时，Go 运行时可能会花费大量时间跟踪每个分配，然后释放它们。因此，这也导致了明显的性能开销。

Arenas 提供了一种解决这个问题的方法，通过减少与许多小分配相关的开销。在这个 protobuf blob 示例中，可以在解析之前分配一大块内存（Arenas），以便所有已解析的对象可以放置在竞技场内并作为一个整体单元进行跟踪。

一旦解析完成，整个竞技场可以一次性释放，进一步减少释放许多小对象的开销。

![1](C:\Users\zhengxm\Documents\notes\翻译\static\images\2023\w07-Go-1-20-Experiment-Memory-Arenas-vs-Traditional-Memory-Management\1.png)

## 了解可从竞技场中受益的代码

任何分配大量小对象的代码都有可能从竞技场中受益。但是如何知道代码分配的过多？根据我们的经验，最好的方法是对程序进行分析。

使用 Pyroscope，我们可以获得其中一个[云服务](https://pyroscope.io/pricing/)的分配配置文件（`alloc_objects`）。

![2](C:\Users\zhengxm\Documents\notes\翻译\static\images\2023\w07-Go-1-20-Experiment-Memory-Arenas-vs-Traditional-Memory-Management\2.png)

你可以看到大部分分配（`533.30 M`）来自代码的一个区域 - 这是在底部调用函数`InsertStackA`的紫色节点。鉴于它代表65％的分配，这是使用竞技场的好候选者。但是，通过减少这些分配是否可以获得足够的性能收益？让我们看看同一服务的CPU分析（`cpu`）：

![3](C:\Users\zhengxm\Documents\notes\翻译\static\images\2023\w07-Go-1-20-Experiment-Memory-Arenas-vs-Traditional-Memory-Management\3.png)

几件事情很突出：

- 程序在相同的`InsertStackA`函数中花费了很多CPU时间，因此显然有潜在的重要性能改进潜力。
- 如果搜索`runtime.mallocgc`（底部的多个粉色节点），你会发现该函数在各种不同的地方频繁调用，它占用了我们总执行时间的约14％。
- 大约5％的CPU时间花费在`runtime.gcBgMarkWorker`（位于火焰图右侧的粉色节点）上。

因此，理论上，如果我们优化了这个程序中的所有分配，我们可以减少14％+5％= 19％的CPU时间。这将转化为我们所有客户的19％成本节约和延迟改进。在实践中，不太可能真正使这些数字降到零，但这仍然是应用程序执行的重要工作，可能值得优化。

## 我们做出的优化

如果您对此感兴趣，您可以在Pyroscope存储库中找到[公共拉取请求](https://github.com/pyroscope-io/pyroscope/pull/1804)作为参考。

- 首先，我们创建了[一个包装组件](https://github.com/pyroscope-io/pyroscope/pull/1804/files#diff-70ab4bbe796a97ad1a47d7970504296eff36b5307527ae2806d2b50f94f83a45)，负责处理切片或结构的分配。如果启用了竞技场，此组件使用竞技场分配切片，否则使用标准“make”函数。我们通过使用构建标记（`//go：build goexperiment.arenas`）实现此目的。这允许在构建时轻松地在竞技场分配和标准分配之间切换
- 然后，我们在解析器代码周围添加了[初始化](https://github.com/pyroscope-io/pyroscope/pull/1804/files#diff-32bf8c53a15c8a5f7eb424b21c8502dc4905ec3caa28fac50f64277361ae746fR417)和[清理](https://github.com/pyroscope-io/pyroscope/pull/1804/files#diff-34edf37e55842273380ee6cb31c9245f31ed25aa6d7898b0f2c25145f17d8ea0R170)调用竞技场
- 接下来，我们[用我们的包装组件中的make调用替换了常规的`make`调用](https://github.com/pyroscope-io/pyroscope/pull/1804/files#diff-abe15b6d3634170650f86bb7283aa15265de2197cffa969deda2dd5b26fcecd9R89-R92)
- 最后，我们在启用了 arenas 的情况下构建了 pyroscope，并逐渐部署到了我们的 [Pyroscope Cloud](https://pyroscope.io/pricing) 生产环境中。

## 我们 Arenas 实验的结论

![4](C:\Users\zhengxm\Documents\notes\翻译\static\images\2023\w07-Go-1-20-Experiment-Memory-Arenas-vs-Traditional-Memory-Management\4.png)

上面的火焰图表示我们实施更改后的配置文件。您可以看到，许多`runtime.mallocgc`调用现在已经消失，但被竞技场特定的等效项（`runtime.(*userArena).alloc`）替代，您也可以看到垃圾回收开销减少了一半。仅从火焰图上看准确的节省量很难看出，但是当我们查看结合了火焰图和AWS指标的CPU使用情况的Grafana仪表板时，我们发现CPU使用率大约减少了8％。这直接转化为该特定服务的云账单上的8％费用节省，使其成为一项有价值的改进。

![5](C:\Users\zhengxm\Documents\notes\翻译\static\images\2023\w07-Go-1-20-Experiment-Memory-Arenas-vs-Traditional-Memory-Management\5.png)

这可能看起来不多，但重要的是要注意，这是一项已经被优化得相当多的服务。例如，我们使用的Protobuf解析器根本不会分配任何额外的内存，垃圾回收开销（5％）也在我们服务的开销范围的低端。我们认为代码库的其他部分还有很多改进的空间，因此我们很高兴继续尝试竞技场。

## 权衡弊端

虽然 arenas 可以提供性能上的好处，但在使用它们之前有必要考虑利弊。使用 arenas 的主要缺点是，一旦使用 arenas，您现在必须手动管理内存，如果您不小心，这可能导致严重问题：

- 未能正确释放内存可能导致内存泄漏

- 尝试从已释放的场馆访问对象可能导致程序崩溃 

以下是我们的建议：

- 仅在关键代码路径中使用 arenas。不要在所有地方使用它们

- 在使用 arenas 前后对代码进行分析，以确保您在 arenas 可以提供最大效益的地方添加 arenas

- 密切关注在 arenas 上创建的对象的生命周期。确保不要将它们泄漏到程序的其他组件，其中对象可能超出 arenas 的生命周期

- 使用`defer a.Free()`确保不会忘记释放内存

- 使用`arena.Clone()`将对象克隆回堆上，如果您在 arenas 被释放后想要使用它们

Go arenas 目前的一个主要缺点是它是一项实验性特性。 API 和实现是完全不受支持的，Go 团队不对其兼容性或将来是否会继续存在进行任何保证。我们建议您将所有与 arenas 相关的代码提取到单独的包中，并使用 build tags 以确保如果您决定停止使用 arenas，它很容易从您的代码库中删除。[我们的代码](https://github.com/pyroscope-io/pyroscope/pull/1804/files#diff-70ab4bbe796a97ad1a47d7970504296eff36b5307527ae2806d2b50f94f83a45)可作为此方法的演示。

## 解决社区关注的问题

Go团队已经收到了关于竞技场的大量反馈，我们想要回应社区中我们所看到的一些关切。有关竞技场最常见的问题是它们添加了一种隐式且不立即显现问题的程序崩溃方式，使语言变得更加复杂。

大部分的批评是明确的但误导性的。我们不预期竞技场会变得普遍。我们认为竞技场是一个强大的工具，但只适用于特定情况。在我们看来，竞技场应该包含在标准库中，但它们的使用应该受到警惕，就像使用`unsafe`，`reflect`或`cgo`一样。

我们对竞技场的经验非常充分，我们能够证明竞技场可以显着减少垃圾回收和内存分配的时间。本文描述的实验关注的是一个单独的、已经高度优化的服务，我们仍然能够通过使用竞技场获得8%的额外性能。我们认为许多用户可以从在代码库中使用竞技场中获益更多。

此外，我们还发现，相比我们过去尝试的其他优化（如使用缓冲池或编写自定义无分配 protobuf 解析器），竞技场的实现更容易。与其他类型的优化相比，它们具有相同的缺点，但提供了更多的好处 - 因此，在我们看来，竞技场是一个净赢。我们希望未来能看到竞技场成为标准库的一部分（并且是常用包如 protobuf 或 JSON 解析器的一部分）。

## 总结

Go程序的优化工具，特别适用于处理大量protobuf或JSON块的情况。它们有可能带来显著的性能改进，但是需要注意的是它们是一个实验性的功能，不保证兼容性或在未来版本中的存在。

我们建议您对应用程序进行分析，并在代码库的有限部分尝试使用arenas，并将您的结果[报告给go团队](https://github.com/golang/go/issues/51317)。
