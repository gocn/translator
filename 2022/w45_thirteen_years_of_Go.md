原文地址：[Thirteen Years of Go - The Go Programming Language](https://go.dev/blog/13years)

原文作者：Russ Cox, for the Go team

本文永久链接：[https://github.com/gocn/translator/blob/master/2022/w45_thirteen_yeasr_of_Go.md](https://github.com/gocn/translator/blob/master/2022/w45_thirteen_yeasr_of_Go.md)

译者：[zxmfke](https://github.com/zxmfke)

校对：[pseudoyu](https://github.com/pseudoyu)

# Go 语言的 13 年

![](../static/images/2022/w45_thirteen_years_of_Go\gopherbelly300.jpg)

今天我们庆祝 Go 开源版本的十三岁生日。 [Gopher](https://go.dev/doc/gopher) 已经是一个青少年啦!

对于 Go 来说，今年是具有里程碑的一年。最重要的事件是 [3 月的 Go 1.18](https://go.dev/blog/go1.18)的发布，它带来了许多改进，但最引人注目的是 Go 工作区、模糊测试和泛型。

工作区使你可以很容易地同时处理多个模块，当你维护一组相关的模块并在它们之间有模块依赖关系时，这是最有用的。要了解工作区，请看 Beth Brown 的博文"[熟悉工作区](https://go.dev/blog/get-familiar-with-workspaces) "和[工作区指南](https://go.dev/ref/mod#workspaces)。

模糊测试是`go` `test` 的一个新功能，它可以帮助你找到你的代码不能正确处理的输入：你定义一个模糊测试，对任何输入都应该是通过的，然后模糊测试在代码覆盖率的指导下尝试不同的随机输入，试图使模糊测试失败。在开发对任意（甚至是攻击者控制的）输入都不出错的、鲁棒性的代码时，模糊测试尤其好用。要了解更多关于模糊测试的信息，请参阅教程"[模糊测试入门](https://go.dev/doc/tutorial/fuzz) "和[模糊测试指南](https://go.dev/security/fuzz/)，并留意 Katie Hockman 的 GopherCon 2022 演讲 "Fuzz Testing Made Easy"，该演讲即将上线。

泛型，很可能是 Go 最受欢迎的功能，它为 Go 增加了参数多态性，使编写的代码可以适用于各种不同的类型，但在编译时仍然是静态检查。要了解更多关于泛型的信息，请看教程《[泛型入门](https://go.dev/doc/tutorial/generics)》。更多详情请见博文"[泛型简介](https://go.dev/blog/intro-generics) "和"[何时使用泛型](https://go.dev/blog/when-generics)"，或 2021 年 Google 开源现场 Go Day 的讲座"[在 Go 中使用泛型](https://www.youtube.com/watch?v=nr8EpUO9jhw)"，以及 2021 年 GopherCon 的"[泛型！](https://www.youtube.com/watch?v=Pa_e9EeCdy8)"，由 Robert Griesemer 和 Ian Lance Taylor 撰写。

与 Go 1.18 相比，[8月发布的 Go 1.19](https://go.dev/blog/go1.19) 是一个相对平静的版本：它侧重于完善和改进 Go 1.18 引入的功能，以及内部稳定性改进和优化。Go 1.19 的一个明显变化是增加了对 [Go 文档注释中的链接、列表和标题](https://go.dev/doc/comment) 的支持。另一个变化是为垃圾收集器增加了一个[软内存限制](https://go.dev/doc/go1.19#runtime)，这在容器工作负载中特别有用。关于最近垃圾收集器的改进，请参见 Michael Knyszek 的博文"[Go 运行时间：4年后](https://go.dev/blog/go119runtime)"，他的演讲"[Respecting Memory Limits in Go](https://www.youtube.com/watch?v=07wduWyWx8M&list=PLtoVuM73AmsJjj5tnZ7BodjN_zIvpULSx)"，以及新的"[Go垃圾收集器指南](https://go.dev/doc/gc-guide)"。

我们一直致力于使 Go 开发能够优雅地扩展到更大的代码库，特别是在 VS Code Go 和 Gopls 语言服务器方面的工作。今年，Gopls 的发布侧重于提高稳定性和性能，同时提供对泛型的支持，以及新的分析和代码透镜。如果你还没有使用 VS Code Go 或 Gopls，请试一试。请参阅 Suzy Mueller 的讲座"[用 Go 编辑器构建更好的项目](https://www.youtube.com/watch?v=jMyzsp2E_0U) "以了解概况。作为奖励，[在 VS Code中调试 Go](https://go.dev/s/vscode-go-debug)在Delve的本地[调试适配器协议](https://microsoft.github.io/debug-adapter-protocol/)支持下变得更加可靠和强大。试试 Suzy的"[Debugging Treasure Hunt](https://www.youtube.com/watch?v=ZPIPPRjwg7Q)"!

开发规模的另一部分是项目中的依赖数量。在 Go 的 12 岁生日后一个月左右，[Log4shell 漏洞](https://en.wikipedia.org/wiki/Log4Shell)为业界敲响了警钟，让大家认识到调用链安全的重要性。Go 的模块系统就是专门为此而设计的，它可以帮助你了解和跟踪你的依赖关系，识别你正在使用的具体依赖关系，并确定其中是否有已知的漏洞。Filippo Valsorda 的博文"[Go 如何缓解调用链攻击](https://go.dev/blog/supply-chain) "对我们的方法进行了概述。9月，我们在 Julie Qiu 的博文"[Go 的漏洞管理](https://go.dev/blog/vuln) "中预览了Go的漏洞管理方法。这项工作的核心是一个新的、经过整理的漏洞数据库和一个新的 [govulncheck 命令](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)，它使用先进的静态分析来消除大部分仅使用模块要求而产生的误报。

我们致力于了解 Go 用户的一部分是我们每年的年终 Go 调查问卷。今年，我们的用户体验研究人员也增加了一个轻量级的年中 Go 调查问卷。我们的目标是收集足够多的回复，以便在不对整个 Go 社区造成负担的情况下进行统计学意义上的调查。有关结果，请参阅 Alice Merrick 的博文"[Go Developer Survey 2021 Results](https://go.dev/blog/survey2021-results) "和 Todd Kulesza 的文章"[Go Developer Survey 2022 Q2 Results](https://go.dev/blog/survey2022-q2-results)"。

随着世界上开始更多的旅行，我们也很高兴能在 2022 年的 Go 会议上见到你们中的许多人，特别是在 7 月柏林的 GopherCon Europe 和 10 月芝加哥的 GopherCon 上。上周我们举行了年度虚拟活动，[谷歌开源现场的Go Day](https://opensourcelive.withgoogle.com/events/go-day-2022)。以下是我们在这些活动中发表的一些演讲。

- “[How Go Became its Best Self](https://www.youtube.com/watch?v=vQm_whJZelc)”, by Cameron Balahan, at GopherCon Europe.
- “[Go team Q&A](https://www.youtube.com/watch?v=KbOTTU9yEpI)”, with Cameron Balahan, Michael Knyszek, and Than McIntosh, at GopherCon Europe.
- “[Compatibility: How Go Programs Keep Working](https://www.youtube.com/watch?v=v24wrd3RwGo)”, by Russ Cox at GopherCon.
- “[A Holistic Go Experience](https://www.gophercon.com/agenda/session/998660)”, by Cameron Balahan at GopherCon (video not yet posted)
- “[Structured Logging for Go](https://opensourcelive.withgoogle.com/events/go-day-2022/watch?talk=talk2)”, by Jonathan Amsterdam at Go Day on Google Open Source Live
- “[Writing your Applications Faster and More Securely with Go](https://opensourcelive.withgoogle.com/events/go-day-2022/watch?talk=talk3)”, by Cody Oss at Go Day on Google Open Source Live
- “[Respecting Memory Limits in Go](https://opensourcelive.withgoogle.com/events/go-day-2022/watch?talk=talk4), by Michael Knyszek at Go Day on Google Open Source Live

今年的另一个里程碑是在 *Communications of the ACM* 上发表了"[Go编程语言和环境](https://cacm.acm.org/magazines/2022/5/260357-the-go-programming-language-and-environment/fulltext)"，作者是 Russ Cox、Robert Griesemer、Rob Pike、Ian Lance Taylor 和 Ken Thompson。这篇文章由 Go 的原始设计者和实施者撰写，解释了我们认为是什么让 Go 如此受欢迎和富有成效。简而言之，Go 的工作重点是提供一个针对整个软件开发过程的完整的开发环境，并对大型软件工程工作和大型部署进行扩展。

在 Go 的第 14 个年头，我们将继续努力使 Go 成为大规模软件工程的最佳生态。我们计划特别关注调用链安全、改进的兼容性和结构化日志，所有这些都已经在这篇文章中提到了。此外，还将有大量的其他改进，包括配置文件指导下的优化。

## 感谢你！

Go 一直以来都远远超出了 Google 的 Go 团队的工作范围。感谢所有的人--我们的贡献者和 Go 社区的每个人--你们的帮助使 Go 成为今天成功的编程环境。我们祝愿你们在新的一年里一切顺利。
