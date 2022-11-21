# Go 风格指南 - 概述

- 原文地址：https://google.github.io/styleguide/go/index
- 原文作者：Google
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2022/w47_go_styleguide_overview.md
- 译者：[fivezh](https://github.com/fivezh)
- 校对：[]()

# Go 风格

原文：[https://google.github.io/styleguide/go](https://google.github.io/styleguide/go)

[概述](https://google.github.io/styleguide/go/index) | [指南](https://google.github.io/styleguide/go/guide) | [决策](https://google.github.io/styleguide/go/decisions) | [最佳实践](https://google.github.io/styleguide/go/best-practices)

## 关于

本文的 `Go` 风格指南和文档整理了当前编写可读和惯用的 Go 最佳方法。 遵守风格指南并不是绝对的，这份文件也永远不会详尽无遗。我们的目的是尽量减少编写可读 Go 代码的猜测，以便该语言的新手可以避免常见的错误。此风格指南也用于统一 Google 内 Go 代码review人的风格指南。

| 文档            | 链接                                                  | 主要受众    | [规范性(Normative)](https://google.github.io/styleguide/go/index#normative) | [规范(Canonical)](https://google.github.io/styleguide/go/index#canonical) |
| ------------------- | ----------------------------------------------------- | ------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| **风格指南**     | https://google.github.io/styleguide/go/guide          | 所有人            | Yes                                                          | Yes                                                          |
| **风格决策** | https://google.github.io/styleguide/go/decisions      | 可读性导师 | Yes                                                          | No                                                           |
| **最佳实践**  | https://google.github.io/styleguide/go/best-practices | 任何有兴趣的人   | No                                                           | No                                                           |



### 文档说明

1. **风格指南(Style Guide)** (https://google.github.io/styleguide/go/guide) 概述了 Google Go 风格的基础。本文档是权威的，用作风格决策和最佳实践中建议的基础。

2. **风格决策(Style Decisions)** (https://google.github.io/styleguide/go/decisions) 是一份更详细的文档，它总结了关于特定风格点的决策，并在适当的时候讨论了决策背后的原因。

   这些决定可能偶尔会根据新数据、新语言特性、新库或新出现的模式而改变，但不希望谷歌的个别 Go 程序员应该时刻关注本文档的同步更新。

3. **最佳实践(Best Practices)** (https://google.github.io/styleguide/go/best-practices) 描述了一些随时间演变的模式，这些模式可以解决通用问题，可读性强，并且对代码可维护的需要有很好的健壮性。

   这些最佳实践并不规范，但鼓励谷歌的Go程序员尽可能使用它们，以保持代码库的统一和一致。

这些文件旨在:

- 就权衡备选风格的一套原则达成一致
- 编撰最终的 Go 风格
- 记录并提供Go习语的典型示例
- 记录各种风格决策的利弊
- 帮助减少Go可读性review中的意外
- 帮助可读性导师使用一致的术语和指导

本文档**不是**旨在：

- 在可读性审查中给出的详尽评论列表
- 列出每个人在任何时候都应该记住和遵守的所有规则
- 在语言特型和风格的使用上取代良好的判断力
- 为了消除风格差异，证明大规模的改变是合理的

不同 Go 程序员之间以及不同团队的代码库之间总会存在差异。然而，我们的代码库尽可能保持一致符合 Google 和 Alphabet 的最大利益。 （有关一致性的更多信息，请参阅 [指南](https://google.github.io/styleguide/go/guide#consistency)。）为此，您可以随意进行风格改进，但不需要挑剔你发现的每一个违反风格指南的行为。特别是，这些文档可能会随着时间的推移而改变，这不是导致现有代码库额外改动的理由； 使用最新的最佳实践编写新代码并随着时间的推移解决附近的问题就足够了。

重要的是要认识到风格问题本质上是个人的，并且总是带有特定的权衡。这些文档中的大部分指南都是主观的，但就像 `gofmt` 一样，它提供的一致性具有重要价值。 因此，风格建议不会在未经适当讨论的情况下改变，谷歌的 Go 程序员被鼓励遵循风格指南，即使他们可能不同意。

## 定义

样式文档中使用的以下词语定义如下：

- **规范(Canonical)**: 制定规定性和持久性规则

  在这些文档中，“规范”用于描述被认为是所有代码（旧的和新的）都应该遵循的标准，并且预计不会随着时间的推移而发生重大变化。规范文档中的原则应该被作者和审稿人理解，因此规范文档中包含的所有内容都必须达到高标准。 因此，与非规范文档相比，规范文档通常更短并且规定的样式元素更少。

  https://google.github.io/styleguide/go#canonical

- **规范性(Normative)**: 旨在建立一致性

  在这些文档中，“规范”用于描述 Go 代码审查者使用的一致同意的风格元素，以便建议、术语和理由保持一致。 这些元素可能会随着时间的推移而发生变化，本文涉及的这些文件将反映出这些变化，以便审阅者可以保持一致和时刻最新。 Go 代码编写者不被要求熟悉此文档，但这些文档将经常被审阅者用作可读性审查的参考。

  https://google.github.io/styleguide/go#normative

- **惯用语(Idiomatic)**: 常见且熟悉

  在这些文档中，“惯用语”指在 Go 代码中普遍存在的东西，并已成为一种易于识别的常见模式。一般来说，如果两者在上下文中服务于相同的目的，那么惯用模式应该优先于非惯用模式，因为这是读者最熟悉的模式。

  https://google.github.io/styleguide/go#idiomatic

## 附加参考

本指南假定读者熟悉 [Effective Go](https://go.dev/doc/effective_go)，因为它为整个 Go 社区的 Go 代码提供了一个通用基线。

下面是一些额外的资源，供那些希望自学 Go 风格的人和希望在他们的评论中提供更多可链接的代码审阅者。 Go 可读性过程的参与者不应熟悉这些资源，但它们可能作为可读性审阅的上下文出现。

**外部参考**

- [Go 语言规范](https://go.dev/ref/spec)
- [Go FAQ](https://go.dev/doc/faq)
- [Go 内存模型](https://go.dev/ref/mem)
- [Go 数据结构](https://research.swtch.com/godata)
- [Go 接口](https://research.swtch.com/interfaces)
- [Go 谚语](https://go-proverbs.github.io/)
- Go 技巧 - 敬请期待

**相关的 马桶测试(Testing-on-the-Toilet) 文档**

- [TotT: 标识命令](https://testing.googleblog.com/2017/10/code-health-identifiernamingpostforworl.html)
- [TotT: 测试状态与 vs Testing Interactions](https://testing.googleblog.com/2013/03/testing-on-toilet-testing-state-vs.html)
- [TotT: 有效测试](https://testing.googleblog.com/2014/05/testing-on-toilet-effective-testing.html)
- [TotT: 风险驱动测试](https://testing.googleblog.com/2014/05/testing-on-toilet-risk-driven-testing.html)
- [TotT: 变化检测器测试被认为是有害的](https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html)

**额外的外部文档**

- [Go 和 教条](https://research.swtch.com/dogma)
- [少即是成倍的多](https://commandcenter.blogspot.com/2012/06/less-is-exponentially-more.html)
- [Esmerelda的想象力](https://commandcenter.blogspot.com/2011/12/esmereldas-imagination.html)
- [用于解析的正则表达式](https://commandcenter.blogspot.com/2011/08/regular-expressions-in-lexing-and.html)
- [Gofmt 的风格没有人喜欢，但 Gofmt 却是每个人的最爱](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=8m43s) (YouTube)