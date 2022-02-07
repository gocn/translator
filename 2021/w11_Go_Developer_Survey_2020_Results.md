# 2020 年 Go 开发者调查结果

- 原文地址：https://blog.golang.org/survey2020-results
- 原文作者：Alice Merrick
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w11_Go_Developer_Survey_2020_Results.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[guzzsek](https://github.com/guzzsek)

#### 感谢您带来令人兴奋的回应

2020 年，我们的参与人数达到了 9,648 人，这个数据大约和[2019 年](https://blog.golang.org/survey2020-results)时一样多。感谢您抽出宝贵的时间为社区提供了有关于您在使用 Go 时的一些见解！

#### 新的模块化设计调查

您可能注意到一些问题的样本量("n=")是比其他样本小的。这是因为某些问题是向所有人公开的，而另一些问题仅向随机的一部分受访者展示。

#### 重点

-   Go 的使用场景和在企业中的应用正在不断地扩大，其中 76%的受访者表示[在工作中使用 Go](https://blog.golang.org/survey2020-results#TOC_4.1)，并且 66%的受访者表示[Go 语言对他们公司的成功有至关重要的作用](https://blog.golang.org/survey2020-results#TOC_6.1)。
-   [总体满意度](https://blog.golang.org/survey2020-results#TOC_6.)很高，其中 92%的受访者在使用 Go 时感到满意。。
-   大多数的受访者在不到三个月的时间里[察觉到了 Go 的生产力](https://blog.golang.org/survey2020-results#TOC_6.2)，81%的受访者觉得 Go 的生产力非常高或极其高。
-   受访者报告称约 76%的人在前 5 个月就已[迅速升级到了 Go 的最新版本](https://blog.golang.org/survey2020-results#TOC_7.)。
-   [使用 pkg.go.dev 的受访者(91%)](https://blog.golang.org/survey2020-results#TOC_12.)比非使用者(82%)更能成功的找到 Go 软件包。
-   [Go 模块已经被普遍采用了](https://blog.golang.org/survey2020-results#TOC_8.)，满意度为 77%，受访者们强调还需要改进文档。
-   Go 仍然大量用于[API、CLI、Web、DevOps 和数据处理]((https://blog.golang.org/survey2020-results#TOC_7.)。
-   [代表性不足的群体](https://blog.golang.org/survey2020-results#TOC_12.1) 在社区中往往会受到较少的欢迎。

#### 我们聆听了谁的声音

受访者统计问题可以帮助我们辨识出，哪些年度差异是由我们的调查受访者们的情绪或行为导致的。因为我们受访者特征和去年相似，所以我们可以有把握的相信受访者特征对年度差异变化的影响不大。

例如，从 2019 年到 2020 年，组织规模、开发者的经验和行业的分布大致相同。

![Bar chart of organization size for 2019 to 2020 where the majority have fewer than 1000 employees](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/orgsize.svg) ![Bar chart of years of professional experience for 2019 to 2020 with the majority having 3 to 10 years of experience](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/devex_yoy.svg) ![Bar chart of organization industries for 2019 to 2020 with the majority in Technology](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/industry_yoy.svg)

几乎一半(48%)的受访者使用 Go 的时间不到两年。到 2020 年，我们已经很少能收到使用 Go 不到一年的人对调查的回应。

![Bar chart of years of experience using Go](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/goex_yoy.svg)

大多数人表示，他们会在工作(76%)和工作外(62%)时使用 Go。工作中使用 Go 的受访者比例逐年上升。

![Bar chart where Go is being used at work or outside of work](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/where_yoy.svg)

今年我们提出了有关主要工作职责的新问题。我们发现，有 70％的受访者的主要责任是开发软件和应用，但也有相当一部分受访者正在设计 IT 系统和体系结构。

![Primary job responsibilities](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/job_responsibility.svg)

与往年一样，我们发现大多数受访者并不是 Go 开源项目的频繁贡献者，有 75％的受访者表示他们“很少”或“从不”这么做。

![How often respondents contribute to open source projects written in Go from 2017 to 2020 where results remain about the same each year and only 7% contribute daily](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/foss_yoy.svg)

#### 开发人员工具和实践

与往年一样，绝大多数被调查者表示在 Linux（63％）和 macOS（55％）系统上使用 Go。随着时间的推移，主要在 Linux 上进行开发的受访者比例略有下降。

![Primary operating system from 2017 to 2020](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/os_yoy.svg)

编辑器的偏好似乎第一次稳定了下来：VS Code 仍然是最受欢迎的编辑器（41%），其次是 Goland（35%）。这两类就占据了 76%的比例，其他的编辑器喜好并没有像往年一样继续下降，

![Editor preferences from 2017 to 2020](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/editor_pref_yoy.svg)

今年，我们要求受访者在假设他们拥有 100 个“GopherCoins”（一种虚拟货币）的情况下，会花多少钱来优先改善他们的编辑器。代码自动补全功能获得的 GopherCions 的平均数量最高。 一半的受访者表示愿意花费 10 个或者更多的 GopherCoins 来改善这四个功能（代码补全、代码导航、编辑器性能和重构）。

![Bar char of average number of GopherCoins spent per respondent](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/editor_improvements_means.svg)

大多数的受访者（63%）会花费他们 10-30%的时间来重构，这表明重构是一项常见任务，并且我们希望研究一些方法来改善它。这也解释了为什么编辑器支持重构是获得投币数量最多的改进之一。

![Bar chart of time spent refactoring](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/refactor_time.svg)

去年，我们询问了一些特定的开发技能，其中接近 90% 的受访者正在使用文本日志的方式进行调试，为了找出这个问题的原因，我们今年增加了一个后续的问题。结果表明，有 43%的人是因为跨语言时可以使用相同的调试策略，还有 42%的人更喜欢文本记录而不是其他的调试技术。但是，有 27%的人是不知道如何开始使用 Go 的调试工具，还有 24%的人从未尝试过使用 Go 的调试工具，因此就有机会在发现性、可用性和文档方面来改进调试工具。此外，由于四分之一的受访者从未尝试使用调试工具，因此该痛点可能被低估。

![](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/why_printf.svg)

#### 对 Go 的态度

今年，我们是第一次询问人们对 Go 的整体满意度。92%的受访者表示，在过去的一年里，他们在使用 Go 时感到非常满意。

![Bar chart of overall satisfaction on a 5 points scale from very dissatisfied to very satisfied](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/csat.svg)

这是我们第三年问”你会推荐...“这样的[净推荐值问题](https://en.wikipedia.org/wiki/Net_Promoter)（NPS）。今年我们得到的 NPS 值为 61（“推荐者”为 68%，“拒绝者”为 6%），结果与 2019 年和 2018 年相比没有变化。

![Stacked bar chart of promoters, passives, and detractors](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/nps.svg)

与前几年相似，有 91％的受访者表示他们更愿意将 Go 用于其下一个新项目。89％的人说 Go 在他们的团队表现很好。今年，我们看到认同 Go 对公司成功至关重要的受访者从 2019 年的 59％增加到 2020 年的 66％。在拥有 5,000 名或更多员工的组织中工作的受访者不太可能认同（63％），而那些在较小的组织中的受访者，更可能会认同（73％）。

![Bar chart of agreement with statements I would prefer to use Go for my next project, Go is working well for me team, 89%, and Go is critical to my company's success](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/attitudes_yoy.svg)

与去年一样，我们要求受访者根据满意度和重要性对 Go 开发的特定领域进行评分。云服务，调试和模块（去年的改进重点）的满意度有所增加，而大多数重要性分数却保持不变。我们还引入了两个新主题：API 和 Web 框架。我们看到 Web 框架的满意度低于其他领域（64％）。对于大多数当前用户而言，它并不是那么重要（只有 28％的受访者表示它非常重要），但是对于潜在的 Go 开发人员来说，它可能是缺失的关键特性。

![Bar chart of satisfaction with aspects of Go from 2019 to 2020, showing highest satisfaction with build speed, reliability and using concurrency and lowest with web frameworks](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/feature_sat_yoy.svg)

81％的受访者表示，使用 Go 时会感到非常高效。大型组织的受访者比小型组织的受访者更能感受到这一点。

![Stacked bar chart of perceived productivity on 5 point scale from not all to extremely productive ](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/prod.svg)

我们听到，使用 Go 可以轻松快速地实现生产。我们询问了那些感受到 Go 的高效的受访者，他们花费多长的时间才能变得高效。93%的人说用了不到一年的时间，大多数人在 3 个月内就感觉到了高效。

![Bar chart of length of time before feeling productive](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/prod_time.svg)

尽管与去年大致相同，但认同“在 Go 社区中我感到受欢迎”这一说法的受访者的百分比似乎随着时间的推移呈下降趋势，或者至少没有与其他领域保持相同的上升趋势。

我们还发现，认为 Go 的项目领导理解他们需求的受访者比例逐年显著上升（63%）。

所有这些结果表明，从大约两年开始，更多的认同与 Go 的体验提高相关。换句话说，受访者使用 Go 的时间越长，他们越可能同意这些陈述。

![Bar chart showing agreement with statements I feel welcome in the Go community, I am confident in the Go leadership, I feel welcome to contribute, The Go project leadership understands my needs, and The process of contributing to the Go project is clear to me](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/attitudes_community_yoy.svg)

我们询问了一个关于如何使 Go 社区更受欢迎的开放问题。最普遍的建议（21%）是与学习资源和文档不同形式的改进/增加相关的。

![Bar chart of recommendations for improving the welcomeness of the Go community](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/more_welcoming.svg)

#### 使用 Go

构建 API/RPC 服务（74％）和 CLI（65％）仍然是 Go 的最常见用途。与去年相比，我们在选项的排序中引入了随机化之后，看不到任何重大变化。（在 2019 年之前，选择列表开头的选项不成比例。）我们还根据组织规模对此进行了细分，发现受访者在大型企业或小型组织中使用 Go 的方式相似，尽管大型组织使用 Go 来做返回 HTML 的 Web 服务的可能性更小。

![Bar chart of Go use cases from 2019 to 2020 including API or RPC services, CLIs, frameworks, web services, automation, agents and daemons, data processing, GUIs, games and mobile apps](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/app_yoy.svg)

今年，我们对被访者在家中还是在工作中用 Go 写哪种软件进行了更好的了解。尽管返回 HTML 的 Web 服务是最常见的第 4 个用例，但这是由于与工作无关的使用所致。与返回 HTML 的 Web 服务相比，更多的受访者将 Go 用于自动化/脚本，代理和守护程序以及用于工作的数据处理。大部分非常规用途（台式机/ GUI 应用程序，游戏和移动应用程序）是在工作以外编写的。

![Stacked bar charts of proportion of use case is at work, outside of work, or both ](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/app_context.svg)

另一个新问题是，对于每个用例，受访者的满意度如何。CLI 的满意度最高，有 85％的受访者表示对 Go for CLI 的使用感到非常，中等或略微满意。Go 的常用用法往往具有较高的满意度得分，但满意度和受欢迎程度并不完全对应。例如，代理和守护程序的满意度比例第二高，但使用率排名第六。


![Bar chart of satisfaction with each use case](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/app_sat_bin.svg)

其他后续问题探讨了不同的用例，例如，受访者使用其 CLI 的平台。Linux（93％）和 macOS（59％）的高占有率并不奇怪，因为开发人员对 Linux、macOS 和 Linux 云的使用率很高。但是，Windows 也成为了将近三分之一的 CLI 开发人员的目标。

![Bar chart of platforms being targeted for CLIs](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/cli_platforms.svg)

仔细研究 Go 的数据处理可以发现，Kafka 是唯一被广泛采用的引擎，但是大多数受访者表示，他们将 Go 与自定义的数据处理引擎一起使用。

![Bar chart of data processing engines used by those who use Go for data processing](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/dpe.svg)

我们还询问了受访者使用 Go 的更大领域。到目前为止，最常见的领域是 Web 开发（68％），但其他常见的领域包括数据库（46％），DevOps（42％）网络编程（41％）和系统编程（40％）。

![Bar chart of the kind of work where Go is being used](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/domain_yoy.svg)

与去年相似，我们发现 76％的受访者会评估当前的 Go 版本以供生产使用，但是今年我们调整了时间范围，并且发现 60％的受访者在发布前或发布后 2 个月内开始评估新版本。这对于平台即服务提供商快速支持 Go 的新稳定版本方面是非常重要的。

![Bar chart of how soon respondents begin evaluating a new Go release](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/update_time.svg)

#### 模块

今年，我们发现 Go 模块几乎被普遍采用，并且仅使用模块来管理软件包的受访者比例显着增加。96％的受访者表示，他们正在使用模块进行软件包管理，而去年这一比例为 89％。87％的被调查者表示他们仅使用模块来包管理，而去年为 71％。同时，其他软件包管理工具的使用已经减少了。

![Bar chart of methods used for Go package management](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/modules_adoption_yoy.svg)

受访者对模块的满意度相比去年也有所提高。其中 77％的受访者表示，他们对模块感到非常，中度或略微满意，而这一比例在 2019 年为 68％。

![Stacked bar chart of satisfaction with using modules on a 7 point scale from very dissatisfied to very satisfied](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/modules_sat_yoy.svg)

#### 官方文档

大多数受访者表示，他们在使用官方文档时遇到困难。62％的受访者难以找到足够的信息来完全实现其应用程序的功能，并且三分之一以上的受访者则难以开始他们以前从未做过的事情。

![Bar chart of struggles using official Go documentation](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/doc_struggles.svg)

官方文档中最有问题的领域是模块使用和 CLI 开发，有 20％的受访者认为模块文档稍微有用或根本没有帮助，而 16％的受访者面对关于 CLI 开发的文档也是这样认为的。

![Stacked bar charts on helpfulness of specific areas of documentation including using modules, CLI tool development, error handling, web service development, data access, concurrency and file input/output, rated on a 5 point scale from not at all to very helpful](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/doc_helpfulness.svg)

#### 云上的 Go

Go 在设计时就考虑了现代的分布式计算，我们希望继续改善开发人员使用 Go 构建云服务的体验。

-   在调查受访者中，全球的三大云服务提供商（Amazon Web Services，Google Cloud Platform 和 Microsoft Azure）的使用率持续增加，而大多数的其他提供商在每年的调查中使用过的受访者比例都较小。尤其是 Azure，已经从 7%大幅增长到了 12%。
-   作为最常见的部署目标，在自有或公司的服务器本地部署的比例也在持续降低

![Bar chart of cloud providers used to deploy Go programs where AWS is the most common at 44%](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/cloud_yoy.svg)

部署在 AWS 和 Azure 的受访者见证了部署到托管 Kubernetes 平台的增长，现在分别为 40%和 54%。Azure 看到将 Go 程序部署到 VM 的用户比例显著下降，容器使用率从 18％增长到 25％。同时，在 GCP（已经有很大比例的受访者报告了托管的 Kubernetes 使用情况）可以看到无服务器化的 Cloud Run 部署从 10％增长到 17％。

![Bar charts of proportion of services being used with each provider](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/cloud_services_yoy.svg)

总体而言，大多数受访者对在三大主流云服务商提供的云上使用 Go 感到满意，并且统计数字与去年相比没有变化。受访者表示，对于 AWS（82％的满意）和 GCP（80％）上的 Go 开发，其满意程度相似。而 Azure 的满意度较低（满意度为 58％），自由回复中经常提到需要改进 Azure 的 Go SDK 和对 Azure 功能的 Go 版支持。

![Stacked bar chart of satisfaction with using Go with AWS, GCP and Azure](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/cloud_csat.svg)

#### 痛点

受访者不能继续使用 Go 的前几个主要原因是项目使用另一种语言进行开发（54%），工作团队更喜欢使用另一种语言（34%）以及 Go 本身缺乏一些关键特性（26%）。

今年，我们引入了一个新选项，“我已经在想用的任何地方都使用了 Go”，以便受访者可以选择不妨碍他们使用 Go 的选项。这大大降低了所有其他选项的选择率，但没有改变它们的相对顺序。我们还引入了一个“缺乏关键框架”选项。

如果我们仅看受访者不使用 Go 的原因，则可以更好地了解逐年趋势。使用另一种语言来处理现有项目和项目/团队/负责人对另一种语言的偏好正在减少。

![Bar charts of reasons preventing respondents from using Go more](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/goblockers_yoy_sans_na.svg)

在说 Go 缺乏他们所需语言特性的 26%的受访者中，88%的人认为泛型是 Go 缺乏的关键特性。其他重要缺失的特性是需要更好地错误处理（58%），空安全（44%），函数编程（42%）以及更强大/可扩展的类型系统（41%）。

需要明确的是，这些数字来自那些认为如果 Go 不缺失一个或多个关键特性，会更多地使用 Go 的受访者子集，而不是整个受访者群体。换个角度看，由于缺乏泛型，有 18％的受访者无法使用 Go。

![Bar chart of missing critical features](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/missing_features.svg)

受访者报告说，使用 Go 时遇到的最大挑战是 Go 缺乏泛型（18％），而模块/软件包管理以及学习曲线/最佳实践/文档的问题均占 13％。

![Bar chart of biggest challenges respondents face when using Go](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/biggest_challenge.svg)

#### Go 社区

今年，我们向受访者询问了他们用于回答与 Go 相关问题的前 5 个资源。去年，我们只要求前三个，因此结果不能直接比较，但是，StackOverflow 仍然是最受欢迎的资源，占 65％。阅读源代码（57％）仍然是另一种流行的资源，而对 godoc.org 的依赖（39％）大大减少了。软件包发现站点 pkg.go.dev 是今年第一次出现在列表，是 32％受访者的首选资源。使用 pkg.go.dev 的受访者更加认同在此能够快速找到所需的 Go 软件包/库：pkg.go.dev 用户为 91％，其他人为 82％。

![Bar chart of top 5 resources respondents use to answer Go-related questions](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/resources.svg)

多年来，未参加任何与 Go 相关活动的受访者的比例一直在上升。由于 Covid-19，今年我们修改了有关 Go 活动的问题，并发现超过四分之一的受访者在线上 Go 频道上花费的时间比往年多，有 14％的人参加了 Go 的虚拟会议，是去年的两倍。参加虚拟活动的人中有 64％表示这是他们的第一次虚拟活动。

![Bar chart of respondents participation in online channels and events](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/events.svg)

我们发现 12％的受访者认为自己属于传统上代表性不足的群体（例如，种族，性别认同等），这个结果与 2019 年相同，而对此认同的 2％为女性，少于 2019 年（3％）。认同此想法的受访者与不认同的相比，对“我在 Go 社区表示欢迎”这一说法的异议率更高（10％vs. 4％）。这些问题使我们能够衡量社区中的多样性，并重视拓展和增长的机会。

![Bar chart of underrepresented groups](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/underrep.svg) ![Bar chart of those who identify as women](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/underrep_groups_women.svg) ![Bar chart of welcomeness of underrepresented groups](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/welcome_underrep.svg)

我们今年在辅助技术的使用上又增加了一个问题，发现 8％的受访者正在使用某种形式的辅助技术。最常用的辅助技术是对比度或颜色设置（2％）。这大大提醒我们，我们的用户具有访问性需求，这也有助于在 Go 团队管理的网站上推动我们的某些设计决策。

![Bar chart of assistive technology usage](https://github.com/gocn/translator/blob/master/static/images/w11_Go_Developer_Survey_2020_Results/at.svg)

Go 团队重视多样性和包容性，这不仅是做对的事情，还因为多样化的声音可以照亮我们的盲点，并最终使所有用户受益。根据数据隐私法规，我们询问敏感信息（包括性别和传统上代表性不足的群体）的方式已经改变，并且我们希望在未来使这些问题（尤其是有关性别多样性的问题）更具包容性。

#### 结论

感谢您与我们一起审查 2020 年开发者调查结果！了解开发人员的经验和挑战可帮助我们衡量进展并指导 Go 的未来。再次感谢为这项调查做出贡献的每个人-没有您，我们不可能做到。希望明年见！

## 相关文章

 - [Announcing the 2020 Go Developer Survey](https://blog.golang.org/survey2020)
 - [Go Developer Survey 2019 Results](https://blog.golang.org/survey2019-results)
 - [Proposals for Go 1.15](https://blog.golang.org/go1.15-proposals)
 - [Announcing the 2019 Go Developer Survey](https://blog.golang.org/survey2019)
 - [Contributors Summit 2019](https://blog.golang.org/contributors-summit-2019)
 - [Experiment, Simplify, Ship](https://blog.golang.org/experiment)
 - [Next steps toward Go 2](https://blog.golang.org/go2-next-steps)
 - [Go 2018 Survey Results](https://blog.golang.org/survey2018-results)
 - [Go 2, here we come!](https://blog.golang.org/go2-here-we-come)
 - [Nine years of Go](https://blog.golang.org/9years)
 - [Participate in the 2018 Go User Survey](https://blog.golang.org/survey2018)
 - [Participate in the 2018 Go Company Questionnaire](https://blog.golang.org/survey2018-company)
 - [Go 2 Draft Designs](https://blog.golang.org/go2draft)
 - [Go 2017 Survey Results](https://blog.golang.org/survey2017-results)
 - [Hello, 中国!](https://blog.golang.org/hello-china)
 - [Participate in the 2017 Go User Survey](https://blog.golang.org/survey2017)
 - [Eight years of Go](https://blog.golang.org/8years)
 - [Community Outreach Working Group](https://blog.golang.org/cwg)
 - [Contribution Workshop](https://blog.golang.org/contributor-workshop)
 - [Contributors Summit](https://blog.golang.org/contributors-summit)
 - [Toward Go 2](https://blog.golang.org/toward-go2)
 - [Go 2016 Survey Results](https://blog.golang.org/survey2016-results)
 - [Participate in the 2016 Go User Survey and Company Questionnaire](https://blog.golang.org/survey2016)
 - [Go, Open Source, Community](https://blog.golang.org/open-source)
 - [GopherChina Trip Report](https://blog.golang.org/gopherchina)
 - [Four years of Go](https://blog.golang.org/4years)
 - [Get thee to a Go meetup](https://blog.golang.org/meetups)
 - [Go turns three](https://blog.golang.org/3years)
 - [Getting to know the Go community](https://blog.golang.org/survey2011)
 - [The Go Programming Language turns two](https://blog.golang.org/2years)
 - [Spotlight on external Go libraries](https://blog.golang.org/external-libraries)
 - [Third-party libraries: goprotobuf and beyond](https://blog.golang.org/protobuf)


