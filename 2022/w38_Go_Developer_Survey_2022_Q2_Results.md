- 原文地址：[Go Developer Survey 2022 Q2 Results - The Go Programming Language (golang.org)](https://tip.golang.org/blog/survey2022-q2-results)
- 原文作者：**golang.org**
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w12_Go_Developer_Survey_2022_Q2_Results.md
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：

# 2022 Q2 GO开发者问卷调查结果

Todd Kulesza
8 September 2022

## 简述

本文分享了2022年6月版Go开发者调查的结果。我代表Go团队，感谢5752位告诉我们他们使用Go 1.18中引入的新功能的经验，包括泛型、安全工具和工作空间。你们帮助我们更好地了解开发者是如何发现和使用这一功能的，正如本文将讨论的那样，为额外的改进提供了有用的见解。谢谢你们 💙

### 关键发现

- **泛型已被迅速采用**。绝大多数受访者都知道泛型已经包含在Go 1.18版本中，大约四分之一的受访者表示他们已经开始在Go代码中使用泛型。虽然最常见的与泛型相关的反馈是 "谢谢你！"，但很明显的是开发者已经遇到了初始泛型实现的一些限制。
- **对于大多数Go开发者来说，模糊测试是个新事物**。受访者对Go的内置模糊测试的认识远远低于泛型，而且受访者对为何或何时会考虑使用模糊测试有更多的不确定性。
- **第三方依赖关系是一个最重要的安全问题**。避免与已知漏洞的依赖关系是受访者面临的首要安全相关挑战。更广泛地说，安全工作往往是无计划和无回报的，这意味着工具需要尊重开发者的时间和注意力。
- **在宣布新功能时，我们可以做得更好**。与通过Go博客找到调查的人相比，随机抽样的参与者不太可能知道最近的Go工具发布。这表明我们应该在博客文章之外寻找机会来交流Go生态系统的变化，或者扩大努力来更广泛地分享这些文章。
- **错误处理仍然是一个挑战**。在泛型的发布之后，受访者在使用Go时面临的最大挑战转向了错误处理。然而，总的来说，人们对Go的满意度仍然很高，而且我们发现受访者说他们使用Go的方式没有明显变化。

### 如何阅读这些结果

在这篇文章中，我们把调查结果以图表的形式来为作为我们所发现的证据。所有这些图表都使用类似的格式。标题是调查对象看到的确切问题。除非另有说明，问题都有多个选项，参与者只能选择一个选项。每张图表的副标题会告诉你该问题是否允许有多个回答选项，或者是一个开放式文本框而不是一个多选题。对于开放式文本答复的图表，Go小组的成员阅读并对所有的答复进行手工分类。许多开放式问题收到了各种各样的回答；为了保持图表的合理性，我们把它们浓缩为最多10个主题，其他主题都归入 "其他"。

为了帮助读者了解每项发现所依据的证据的分量，我们在图表上体现了反馈的95%置信区间的误差条；越窄的误差条表示置信度提高。有时两个或更多的反应有重叠的误差条，这意味着这些反应的相对顺序在统计上没有意义(例如，某些反馈是关系是并列的)。每张图表的右下方以 "n=[受访者人数]"的形式，显示了图表中包含的回答人数。

### 关于调查方法的说明

大多数调查对象是 "自我选择 "参加调查的，这意味着他们是在[the Go blog](https://go.dev/blog)， [@golang on Twitter](https://twitter.com/golang)，或其他Go社区上发现的。这种方法的一个潜在问题是，不关注这些渠道的人不太可能了解到调查的情况，而且可能与密切关注这些渠道的人有不同的反应。大约三分之一的受访者是随机抽样的，这意味着他们是在VS Code中看到提示后才对调查做出回应的（在2022年6月1日至6月21日期间使用VS Code Go插件的所有人都有10%的机会收到这种随机提示）。这个随机抽样的群体有助于我们将这些发现推广到更大的Go开发者群体中。大多数调查问题在这些群体之间没有显示出有意义的差异，但在少数有重要差异的情况下，读者会看到将回答分为 "随机抽样 "和 "自选 "组的图表。

## 泛型

"[泛型]似乎是我第一次使用该语言时唯一明显缺少的功能。这对减少代码重复有很大帮助"。- 一位讨论泛型的调查对象

在Go 1.18发布并支持类型参数（通常称为*泛型*）后，我们想了解对泛型的初始影响和运用情况，以此来明确使用泛型的常见挑战或障碍。

绝大多数调查对象（86%）已经知道泛型是作为Go 1.18版本推出的一部分功能。我们曾以为在这里是一个小的大多数，但其实这比我们预期的要多得多。我们还发现，大约四分之一的受访者已经开始在Go代码中使用泛型（26%），包括14%的人说他们已经在生产或发布的代码中使用泛型。大多数受访者（54%）并不反对使用泛型，但目前没有这方面的需求。我们还发现，8%的受访者希望在Go中使用泛型，但目前被一些东西所阻挡。

![Chart showing most respondents were aware Go 1.18 included generics](https://go.dev/blog/survey2022q2/generics_awareness.svg) ![Chart showing 26% of respondents are already using Go generics](https://go.dev/blog/survey2022q2/generics_use.svg)

是什么阻碍了一些开发者使用泛型？大多数受访者属于两类中的一类。首先，30%的受访者表示，他们遇到了目前泛型实现的限制，比如希望有参数化的方法，改进类型推理，或在类型上切换。受访者说，这些问题限制了泛型的潜在用例，或者认为它们使泛型代码变得不必要地冗长。第二类是依赖不支持泛型的东西--linter是最常见的阻碍采用的工具，但这一名单也包括一些，如组织仍在使用早期的Go版本，或依赖尚未提供Go 1.18软件包的Linux发行版（26%）。12%的受访者提到了学习曲线过长或缺乏有用的文件。除了这些首要问题，受访者还告诉我们一系列不太常见的（但仍然有意义的）挑战，如下图所示。为了避免专注于假设，本分析只包括那些说他们已经在使用泛型的人，或者那些试图使用泛型但被某些东西阻挡的人。

![Chart showing the top generic challenges](https://go.dev/blog/survey2022q2/text_gen_challenge.svg)

我们也尝试让使用泛型的调查对象分享任何额外的反馈。令人鼓舞的是，十分之一的受访者说泛型已经简化了他们的代码，或者减少了代码的重复。最常见的回答是 "谢谢你！"或积极情绪（43%）；相比之下，只有6%的受访者表现出负面的反应或情绪。与上述 "最大的挑战 "问题的结果相呼应，近三分之一的受访者讨论到了Go实现泛型的限制。Go团队正在使用这组结果来帮助决定是否或如何放宽其中的一些限制。

![Chart showing most generics feedback was positive or referenced a limitation of the current implementation](https://go.dev/blog/survey2022q2/text_gen_feedback.svg)

## 安全

"[最大的挑战是]找到时间来比较优先级；企业客户希望他们的功能高于安全。" - 一位讨论安全挑战的调查对象

在[2020年SolarWinds](https://en.wikipedia.org/wiki/2020_United_States_federal_government_data_breach#SolarWinds_exploit)漏洞事件之后，安全开发软件的做法再次受到关注。 Go团队已经将这一领域的工作列为优先事项，包括创建[软件材料清单（SBOM）的工具](https://pkg.go.dev/debug/buildinfo)、[模糊测试](https://go.dev/doc/fuzz/)，以及最近的[漏洞扫描](https://go.dev/blog/vuln/)。为了支持这些成果，本次调查提出了几个关于软件开发安全实践和挑战的问题。我们特别想了解：

- Go开发人员现在正在使用哪些类型的安全工具？
- Go开发人员如何发现和解决漏洞？
- 编写安全的Go软件，最大挑战是什么？

我们的结果表明，虽然静态分析工具被广泛使用（65%的受访者），但少数受访者目前使用它来寻找漏洞（35%）或以其他方式提高代码安全性（33%）。受访者表示，安全工具最常在CI/CD时间内运行（84%），少数人表示开发人员在开发期间在本地运行这些工具（22%）。这与我们团队进行的其他安全研究相吻合，发现在CI/CD时间进行安全扫描是一个理想的后盾，但开发人员往往认为这对于第一次通知来说太晚了。他们更愿意在建立一个依赖关系之前知道它可能有漏洞，或者验证一个版本的更新是否解决了一个漏洞，而不需要等待CI对他们的PR运行一整套额外的测试。

![Chart showing prevalence of 9 different development techniques](https://go.dev/blog/survey2022q2/dev_techniques.svg) ![Chart showing most respondents run security tools during CI](https://go.dev/blog/survey2022q2/security_sa_when.svg)

我们还询问了受访者有关开发安全软件的最大挑战。最广泛的困难是评估第三方库的安全性（57%的受访者），一个漏洞扫描器专题（如[GitHub’s dependabot](https://github.com/dependabot)或Go团队的[govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)）可以帮助解决。其他最主要的挑战表明了增加安全工具的机会：受访者说，在编写代码时很难一致地应用最佳实践，并验证所产生的代码没有漏洞。

![Chart showing the most common security challenge is evaluating the security of third-party libraries](https://go.dev/blog/survey2022q2/security_challenges.svg)

模糊测试是另一种提高应用程序安全性的方法，对大多数受访者来说仍然相当陌生。只有12%的人说他们在工作中使用它，5%的人说他们已经采用了Go的内置模糊工具。一个开放式的后续问题问到是什么让模糊测试难以使用，发现主要原因不是技术问题：排名前三的回答是不了解如何使用模糊测试（23%），缺乏时间用于模糊测试或更广泛的安全（22%），以及了解为什么和何时开发人员可能想要使用模糊测试（14%）。这些发现表明，在宣传模糊测试的价值、什么应该被模糊测试以及如何将其应用于各种不同的代码库方面，我们仍有工作要做。

![Chart showing most respondents have not tried fuzz testing yet](https://go.dev/blog/survey2022q2/fuzz_use.svg) ![Chart showing the biggest fuzz testing challenges relate to understanding, rather than technical issues](https://go.dev/blog/survey2022q2/text_fuzz_challenge.svg)

围绕漏洞检测和解决，其中为了更好地了解常见任务，我们询问受访者在过去一年中是否了解到他们的Go代码或其依赖的任何漏洞。对于这些人，我们追问他们最近的漏洞是如何被发现的，他们是如何调查和/或解决这个问题的，以及整个过程中最具挑战性的是什么。

首先，我们发现有证据表明漏洞扫描是有效的。四分之一的受访者说，他们已经了解到他们的一个第三方依赖中的漏洞。然而，只有大约⅓的受访者在使用漏洞扫描--当我们看那些说他们运行某种漏洞扫描器的人的回答时，这个比例几乎翻了一番，从25%→46%。除了依赖关系或Go本身的漏洞外，12%的受访者表示他们在自己的代码中了解到了漏洞。

大多数受访者表示他们是通过安全扫描器了解到漏洞的（65%）。受访者最常引用的工具是[GitHub’s dependabot](https://github.com/dependabot) （38%），其比其他所有漏洞扫描器的总和（27%）还更经常被使用。在扫描工具之后，最常见的了解漏洞的方法是公共报告，如发行说明和CVEs（22%）。

![Chart showing that most respondents have not found security vulnerabilities during the past year](https://go.dev/blog/survey2022q2/security_found_vuln.svg) ![Chart showing that vulnerability scanners are the most common way to learn about security vulnerabilities](https://go.dev/blog/survey2022q2/text_vuln_find.svg)

一旦受访者了解到一个漏洞，最常见的解决办法是升级有漏洞的依赖关系（67%）。在讨论使用漏洞扫描器的受访者中（代表讨论第三方依赖性中的漏洞的参与者），这一比例增加到85%。不到三分之一的受访者讨论了阅读CVE或漏洞报告（31%），只有12%的受访者提到了深入调查以了解他们的软件是否（以及如何）受到漏洞的影响。

只有12%的受访者表示，他们对其代码中的漏洞是否可以触及，或对其服务可能产生的潜在影响进行了调查，这令人惊讶。为了更好地理解这一点，我们还研究了受访者所说的应对安全漏洞的最大挑战是什么。他们以大致相同的比例描述了几个不同的主题，从确保依赖性更新不会破坏任何东西，到了解如何通过go.mod文件更新间接依赖性。在这个列表中，还有为了解漏洞的影响或根本原因所需的调查类型。然而，当我们只关注那些说他们进行这些调查的受访者时，我们看到了一个明显的相关性。70%的受访者说他们对漏洞的潜在影响进行了调查，他们认为这是这个过程中最具挑战性的部分。原因不仅包括任务的难度，还包括这往往是没有计划的和没有回报的工作。

Go团队认为，这些更深入的调查需要了解应用程序如何使用有漏洞的依赖关系，这对于了解漏洞可能给组织带来的风险，以及了解是否发生了数据泄露或其他安全漏洞至关重要。因此，[我们设计的govulncheck](https://go.dev/blog/vuln)只在漏洞被调用时提醒开发者，并指出开发者在其代码中使用漏洞函数的确切位置。我们的希望是，这将使开发人员更容易快速调查对他们的应用程序真正重要的漏洞，从而减少这一领域的非计划性工作的总量。

![Chart showing most respondents resolved vulnerabilities by upgrading dependencies](https://go.dev/blog/survey2022q2/text_vuln_resolve.svg) ![Chart showing a 6-way tie for tasks that were most challenging when investigating and resolving security vulnerabilities](https://go.dev/blog/survey2022q2/text_vuln_challenge.svg)

## 工具的使用

接下来，我们调查了三个侧重于工具的问题：

- 自我们上次调查以来，编辑器的情况是否发生了变化？
- 开发者是否在使用工作空间？如果是的话，他们在开始时遇到了什么挑战？
- 开发者如何处理内部包的文档？

在调查对象中，VS Code似乎持续流行，自2021年以来，它是调查对象首选的Go语言编辑器的比例从42%增加到45%。VS Code和GoLand这两个最受欢迎的编辑器，在小型和大型组织之间的受欢迎程度没有差异，尽管业余开发者更倾向于VS Code而不是GoLand。这项分析不包括随机抽样的VS Code受访者--正如我们所看到的，我们期望我们邀请的人对用于分发邀请的工具表现出偏好（91%的随机抽样受访者喜欢VS Code）。

在2021年通过[gopls语言服务器为VS Code的Go支持提供动力](https://go.dev/blog/gopls-vscode-go)后，Go团队一直想了解与gopls有关的开发者痛点。虽然我们从目前使用gopls的开发者那里收到了大量的反馈，但我们想知道是否有很大一部分开发者在发布后不久就禁用了它，这可能意味着我们没有听到关于特别的有问题的用例的反馈。为了回答这个问题，我们询问了那些说他们更喜欢支持gopls的编辑器的受访者，无论他们是否*使用*gopls，最后发现只有2%的人说他们禁用了gopls；具体到VS Code，这个比例下降到1%。这增加了我们的信心，我们听到了来自一个有代表性的开发者群体的反馈。对于那些对gopls仍有未解决的问题的读者，请在[GitHub上提交一个issue](https://github.com/golang/go/issues)，让我们知道。

![Chart showing the top preferred editors for Go are VS Code, GoLand, and Vim / Neovim](https://go.dev/blog/survey2022q2/editor_self_select.svg) ![Chart showing only 2% of respondents disabled gopls](https://go.dev/blog/survey2022q2/use_gopls.svg)

关于工作区，似乎很多人是通过这次调查第一次了解到Go对多模块工作区的支持。通过VS Code的随机提示得知该调查的受访者尤其有可能说他们之前没有听说过工作区（53%的随机抽样受访者和33%的自选受访者），我们也观察到了对泛型的认识趋势（尽管这两组受访者的认识都比较高，93%的自选受访者知道泛型在Go 1.18中出现，而随机抽样受访者只有68%）。一种解释是，我们目前没有通过Go博客或现有的社交媒体渠道接触到大量的Go开发者，而传统上这是我们分享新功能的主要机制。

我们发现，9%的受访者表示他们已经尝试过工作空间，还有5%的受访者想尝试，但被一些东西挡住了。受访者讨论了在尝试使用Go工作空间时遇到的各种挑战。缺乏文档和来自`go work`命令的有用的错误信息位居榜首（21%），其次是技术挑战，如重构现有的仓库（13%）。与安全部分讨论的挑战类似，我们在这份清单中再次看到 "缺乏时间/不是优先事项"--我们将其解释为，与工作空间提供的好处相比，理解和设置工作空间的门槛仍然有点太高，可能是因为开发人员已经有了变通方法。

![Chart showing a majority of randomly sampled respondents were not aware of workspaces prior to this survey](https://go.dev/blog/survey2022q2/workspaces_use_s.svg) ![Chart showing that documentation and error messages were the top challenge when trying to use Go workspaces](https://go.dev/blog/survey2022q2/text_workspace_challenge.svg)

在 Go 模块发布之前，组织能够运行内部文档服务器（如支持 [godoc.org 的服务器](https://github.com/golang/gddo)），为员工提供私有的内部 Go 包的文档。[pkg.go.dev](https://pkg.go.dev/)依然如此，但建立这样的服务器要比过去复杂得多。为了了解我们是否应该投资使这一过程更容易，我们问受访者他们今天如何看待内部Go模块的文件，以及这是否是他们喜欢的工作方式。

结果显示，目前查看Go内部文档最常见的方式是阅读代码（81%），虽然约有一半的受访者对此感到满意，但有很大一部分人希望有一个内部文档服务器（39%）。我们同时询问了谁最有可能配置和维护这样的服务器：以2比1的比例，受访者认为应该是软件工程师，而不是专门的IT支持或运营团队的人。这强烈地表明，文档服务器应该是一个一条龙的解决方案，或者至少对单个开发人员来说很容易快速运行（例如，在午休时间），理论上，这种类型的工作是在已经全负荷的开发人员上的又一个责任。

![Chart showing most respondents use source code directly for internal package documentation](https://go.dev/blog/survey2022q2/doc_viewing_today.svg) ![Chart showing 39% of respondents would prefer to use a documentation server instead of viewing source for docs](https://go.dev/blog/survey2022q2/doc_viewing_ideal.svg) ![Chart showing most respondents expect a software engineer to be responsible for such a documentation server](https://go.dev/blog/survey2022q2/doc_server_owner.svg)

## 受访者从哪里来

总的来说，自我们[2021年的调查](https://go.dev/blog/survey2021-results)以来，受访者在人口统计学和公司统计学的角度上没有发生有意义的变化。少数受访者（53%）有至少两年的Go使用经验，而其余的则是Go社区的新成员。大约⅓的受访者在小型企业（<100名员工）工作，¼在中型企业（100-1000名员工）工作，¼在企业（>1000名员工）工作。与去年类似，我们发现我们的VS代码提示有助于鼓励北美和欧洲以外的调查参与。

![Chart showing distribution of respondents' Go experience](https://go.dev/blog/survey2022q2/go_exp.svg) ![Chart showing distribution of where respondents' use Go](https://go.dev/blog/survey2022q2/where.svg) ![Chart showing distribution of organization sizes for survey respondents](https://go.dev/blog/survey2022q2/org_size.svg) ![Chart showing distribution of industry classifications for survey respondents](https://go.dev/blog/survey2022q2/industry.svg) ![Chart showing where in the world survey respondents live](https://go.dev/blog/survey2022q2/location_s.svg)

## 受访者使用Go来做什么

与上一节类似，我们没有发现受访者在使用Go的方式上有任何统计意义上的同比变化。两个最常见的使用情况仍然是构建API/RPC服务（73%）和编写CLI（60%）。我们使用线性模型来调查受访者使用Go的时间长短与他们用Go构建的东西的类型之间是否存在关系。我们发现，拥有<1年Go经验的受访者更有可能正在构建该图表下半部分的东西（GUI、物联网、游戏、ML/AI或移动应用程序），这表明人们对在这些领域使用Go有兴趣，但一年经验后的下降也意味着，开发人员在这些领域使用围Go时遇到了重大障碍。

大多数受访者在使用Go开发时使用Linux（59%）或macOS（52%），而且绝大多数人都部署在Linux系统上（93%）。本次我们增加了在Windows Subsystem for Linux（WSL）上开发的回答选项，发现有13%的受访者在使用Go时使用这个选项。

![Chart showing distribution of what respondents build with Go](https://go.dev/blog/survey2022q2/go_app.svg) ![Chart showing Linux and macOS are the most common development systems](https://go.dev/blog/survey2022q2/os_dev.svg) ![Chart showing Linux is the most common deployment platform](https://go.dev/blog/survey2022q2/os_deploy.svg)

## 感受与挑战

最后，我们询问了受访者在过去一年中对Go的总体满意或不满意程度，以及他们在使用Go时面临的最大挑战。我们发现93%的受访者表示他们 "有点"（30%）或 "非常"（63%）满意，这与2021年Go开发者调查期间92%的受访者表示满意的情况没有统计学差异。

在多年来泛型一直是使用Go时最常讨论的挑战之后，Go 1.18中对类型参数的支持终于带来了新的顶级挑战：我们的老朋友，错误处理。可以肯定的是，错误处理在统计上与其他一些挑战联系在一起，包括某些领域的库缺失或不成熟，帮助开发者学习和实施最佳实践，以及对类型系统的其他修订，如对枚举的支持或更多的函数式编程语法。在泛型之后，Go开发者面临的挑战似乎有一个很长的尾巴。

![Chart showing 93% of survey respondents are satisfied using Go, with 4% dissatisfied](https://go.dev/blog/survey2022q2/csat.svg) ![Chart showing a long tail of challenges reported by survey respondents](https://go.dev/blog/survey2022q2/text_biggest_challenge.svg)

## 调查方法

我们在2022年6月1日通过[go.dev/blog](https://go.dev/blog)和Twitter上的@golang公开宣布了这项调查。我们还在6月1日至21日期间通过Go插件随机提示了10%的VS Code用户。调查于6月22日结束，部分回复（即开始但没有完成调查的人）也被记录下来。我们过滤掉了那些完成调查特别快（<30秒）或倾向于勾选多选题的所有回答选项的受访者的数据。这样就剩下5,752个回答。

大约⅓的受访者来自随机的VS代码提示，这部分人的Go经验往往比通过Go博客或围棋的社交媒体渠道找到调查的人少。我们用线性和逻辑模型来研究这些群体之间的明显差异是否可以用这种经验差异来更好地解释，通常都是这样的。文中指出了例外情况。

今年，我们非常希望能与社区分享原始数据集，类似于 [Stack Overflow](https://insights.stackoverflow.com/survey)、 [JetBrains](https://www.jetbrains.com/lp/devecosystem-2021/), 和其他公司的开发者调查。不幸的是，最近的法律指导使我们现在无法这样做，但我们正在努力，并期望能够在下一次围棋开发者调查中分享原始数据集。

## 总结

这次Go开发者调查的重点是Go 1.18版本的新功能。我们发现，泛型的运用正在顺利进行中，开发者已经遇到了当前实现的一些限制。摸索测试和工作区的运用速度较慢，但主要不是因为技术原因：两者的主要挑战是了解何时和如何使用它们。另一个挑战是开发人员没有时间关注这些主题，这个主题也延续到安全工具中。 这些发现正在帮助Go团队确定我们下一步工作的优先级，并将影响我们对未来工具设计的态度。

感谢你加入我们的Go开发者研究之旅--我们希望它是有洞察力的、有趣的。最重要的是，感谢多年来对我们的调查做出回应的每个人。您的反馈帮助让我们更了解 Go 开发者工作中的限制，并确定他们所面临的挑战。通过分享这些经验，你将会帮助为每个人改善 Go 生态系统。我们代表世界各地的Gopher们，感谢您的支持!