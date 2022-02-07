# Rust 与 Go: 为何相得益彰

- 原文地址：https://thenewstack.io/rust-vs-go-why-theyre-better-together/
- 原文作者：[Jonathan](https://thenewstack.io/author/jonathanturner/) Turner and [Steve Francia](https://thenewstack.io/author/stevefrancia/)
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2021/w52_rust_vs_go_why_there_are_better_together.md.md
- 译者：[xkkhy](https:/github.com/xkkhy)
- 校对：[lsj1342](https://github.com/lsj1342)

![](https://github.com/gocn/translator/raw/master/static/images/2021_w52_rust_vs_go_why_there_better_together/4adf69c9-vehicle-2275456_1280-1024x682.jpg)


虽然有一些人可能会将 Rust 和 Go 视为互为竞争的编程语言，但 Rust 和 Go 团队都不这么认为。恰恰相反，我们的团队非常尊重其他人正在做的事情，并将这些语言视为对整个软件开发行业现代化的共同愿景的补充。

在本文中，我们将讨论 Rust 和 Go 的优点和缺点以及他们是如何补充和支持彼此，以及这两种语言最适合在什么时候使用。


已经有一些公司发现同时使用这两种语言具有互补价值。为了让我们的想法更贴合用户体验，我们同三家这样的公司（Dropbox、Fastly 和 Cloudflare）探讨了关于 Rust 和 Go 一起使用方面的经验。在本文中将引用各个团队的观点。

## 语言比较


| 语言                         | Go                                                           | Rust                                                         |
| ---------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 创立日期                     | 2009                                                         | 2010                                                         |
| 创作组织                     | Google                                                       | Mozilla                                                      |
| 用该语言编写的著名软件       | Kubernetes, Docker, Github CLI, Hugo, Caddy, Drone, Ethereum, Syncthing, Terraform | Firefox, ripgrep, alacritty, deno, Habitat                   |
| 主要应用场景                 | APIs, Web Apps, CLI apps, DevOps, Networking, Data Processing, cloud apps | IoT, processing engines, security-sensitive apps, system components, cloud apps |
| 开发者接受程度                 | 8.8% (#12)                                                   | 5.1% (#19)                                                   |
| 最受开发者喜爱的编程语言排行榜 | 62.3% (#5)                                                   | 86.1% (#1)                                                   |
| 开发者最想学习的编程语言排行榜   | 17.9% (#3)                                                   | 14.6% (#5)                                                   |



## 相似之处


Go 和 Rust 有很多共同点。他们都是现代编程语言，他们的诞生都是为了解决软件的安全性和可伸缩性。他们创建的目的都是为了解决当前行业中现有语言的缺陷，特别是开发者的生产率、软件的可伸缩性、安全性和并发性方面的不足。

现在流行的编程语言大多是在 30 多年前设计的。这些语言被设计出来的年代，与如今有五个关键的区别:

1. 摩尔定律被认为是不变的。
2. 大多数软件项目是由小型团队编写的，他们经常在一起工作。
3. 大部分软件是相对较少的依赖，可能大部分还是专有的。
4. 比较少关注软件的安全问题，或者根本不考虑这一块的内容。
5. 软件一般不能跨平台运行。

相比之下，Rust 和 Go 都是为满足当今的开发环境来编写的，他们采用类似的设计方法来解决当今的软件来发需求。

### 1. 性能和并发性

Go 和 Rust 都是编译型语言,专注于代码的执行效率。它们还可以轻松访问当今机器的多个处理器，使其成为编写有效并行代码的理想语言。

"使用 Go 之后，“MercadoLibre” 将原本服务器数量减少到原来的八分之一(从 32 台服务器减少到 4 台)，而且每个服务器可以使用更少的算力(原来是 4 个 CPU 核，现在减少到 2 个 CPU 核)。使用 Go 之后，MercadoLibre 减少了 88%的服务器费用，并将剩余服务器的 CPU 削减了一半, 节省了成本" -- [MercadoLibre Grows with Go](https://go.dev/solutions/mercadolibre/)

"在我们严格管控的环境中，我们运行 Go 代码，我们看到 CPU 减少了大约 10%(与 c++相比)，代码更整洁、更加容易维护。"— [Bala Natarajan, Paypal](https://go.dev/solutions/paypal/)

"在 AWS，我们也喜欢 Rust，Rust 助力 AWS 编写高性能、安全的基础设施级网络和其他系统软件。Firecracker 是亚马逊用在 2008 年推出的第一款用 Rust 实现的虚拟化软件，主要是为 AWS  的 Lambda 架构和其他 serverless 产品提供支持。但我们也使用 Rust 来提供 Amazon Simple Storage Service (Amazon S3)、Amazon Elastic Compute Cloud (Amazon EC2)、Amazon CloudFront、Amazon Route 53 等服务。最近，我们推出了使用 Rust 编写的基于 linux 的容器操作系统——botlerocket"[Matt Asay, Amazon Web Services](https://aws.amazon.com/blogs/opensource/why-aws-loves-rust-and-how-wed-like-to-help/)_

我们看到我们的速度惊人地增长了 1200-1500%! 我们从用 scala 实现的产品化更多的时间做更少的事情(300-500ms)，到 Rust 实现的产品花费更少的时间做更多的事情(25-30ms)![Josh Hannaford, IBM](https://developer.ibm.com/technologies/web-development/articles/why-webassembly-and-rust-together-improve-nodejs-performance/)_

### 2\. 团队可伸缩, 代码可走读

当今软件的开发团队可能是不断变化的(团队成员可能是不断扩充)，一般是以分布式的方式进行代码管理。Go 和 Rust 都是为团队的工作方式而设计的，通过消除不必要的问题，如格式、安全性和复杂的组织，来改善代码审查。这两种语言都需要相对较少的上下文来理解代码正在做什么，从而允许审查人员更快地处理其他人编写的代码，包括团队成员的代码和外部的开源代码。

"在我早期的职业生涯中，有过 Java 和 Ruby 经历，所以编写 Go 和 Rust 的代码感觉得很轻松。在谷歌的时候，用 Go 编写的服务让我如释重负，因为我知道它很容易构建和运行。当然了 Rust 也是如此，尽管我只在一些小规模的项目中应用过。我期待无休止地配置构建环境的日子已经一去不复返了，所有的语言都有自己的专用构建工具，并且这些工具可以开箱即用。-"[Sam Rose, CV Partner](https://bitfieldconsulting.com/golang/rust-vs-go)_

"用 Go 编写服务是相对轻松的事情, 与动态语言相比，它有一个非常简单、易于推理的静态类型系统，并发性是一等公民，而且 Go 的标准库既令人难以置信的优美又强大，但也恰到好处。使用一个标准的 Go 程序，添加一个 grpc 库和一个数据库连接器，您只需要很少的其他东西就可以在服务器端构建任何东西，并且每个工程师都能够阅读代码并理解这些库。在用 Rust 编写模块时，在 2019 年的时候, Dropbox 的工程师在 Async-await 模块稳定之前就感受到了 Rust 在服务器端的强大之处，所以从那时起，Dropbox 就开始尝试使用它，并从中获得了异步模式和强大并发能力的好处" - Daniel Reiter Horn, Dropbox_

### 3\. 开源意识

今天，普通软件项目所使用的依赖项的数量是惊人的。几十年来的软件重用目标已经在现代开发中实现了，今天的软件是使用数百个项目构建的。所以，代码仓库已经逐渐成为各种应用程序中软件开发的主要内容。开发者所包含的每个包都有自己的依赖项。所以当今编程环境的语言需要轻松地处理这种复杂的依赖。

Go 和 Rust 都有自己的包管理工具，这些管理工具会自动管理开发者获取和维护开发这构建的软件包列表，这样开发者就能更加专注于自己的业务代码。

### 4\. 安全

Go 和 Rust 都很好地解决了当今应用程序的安全问题，它们确保用这些语言构建的代码在运行时不会暴露给用户各种经典的安全漏洞，如缓冲区溢出、释放后可重用等。没有这些顾虑，开发者可以更加专注于自己的业务问题，并构建默认情况下更安全的应用程序。

"当处理你遇到的错误时，Rust 的编译器会帮助解决。这使您可以专注于业务，而不是寻找 bug 或处理棘手的问题。"— [Josh Hannaford, IBM](https://developer.ibm.com/technologies/web-development/articles/why-webassembly-and-rust-together-improve-nodejs-performance/)_

"总的来说，Rust 是灵活性和安全性的,并且它的安全性超过了必须遵守严格的生命周期、借用和其他编译器规则，另外值得注意的是, Rust 是没有垃圾回收机制的。这些特性是云软件项目非常需要的功能，将有助于避免许多常见的 bug。"— [Taylor Thomas, Sr., Microsoft](https://msrc-blog.microsoft.com/2020/04/29/the-safety-boat-kubernetes-and-rust/)._

"Go 是强静态类型，没有隐式转换，但语法开销仍然非常小。这是通过简单的类型推断在赋值与无类型的数值常量一起实现的。这给了 Go 比 Java (Java 有隐式转换)更强的类型安全，但代码读起来更像 Python (Python 有无类型变量)。" — [Stefan Nilsson, computer science professor](https://yourbasic.org/golang/advantages-over-java-python/)

"在构建用于在 Dropbox 存储块数据的 Brotli 压缩库时，我们将自己限制在 Rust 的安全子集，此外，还限制到核心库（no-stdlib），并将分配器指定为泛型。以这种方式使用 Rust 的子集使得在客户端从 Rust 调用 Rust-Brotli 库并在服务器上使用来自 Python 和 Go 的 C FFI 变得非常容易。这种编译方式还提供了[实质性的安全保证](https:dropbox.techinfrastructurelossless-compression-with-brotli)。经过一些调整，Rust Brotli 在实现 100% 安全情况下，同时拥有数组边界检查的代码仍然比 C 中实现的 Brotli 代码快"- Daniel Reiter Horn, Dropbox_

### 5\. 真的轻便

对于 Go 和 Rust 来说，编写一个可以在多个不同的操作系统和架构上运行的软件是比较容易的。编写一次，在任何地方编译。此外，Go 和 Rust 都天生支持交叉编译，不需要配置构建环境。

"Golang 构建出来的产品具有优秀的品质，比如内存占用小，这支持它在大型项目中作为其中模块的能力，以及易于交叉编译到其他现成的架构。由于 Go 代码被编译成单一的静态二进制，它允许很容易的容器化，并通过扩展，使得将 Go 部署到任何高可用性的环境(如 Kubernetes)中几乎很容易" — [Dewet Diener, Curve](https://jaxenter.com/golang-curve-163187.html)

"当你查看基于云的基础设施时，你通常使用 Docker 容器之类的组件来部署你的应用。使用 Go 构建的静态二进制文件，你可以有一个 10、11、12 兆字节的 Docker 文件，而不是引入整个 Node.js 生态系统，或 Python 或 Java，在那里你有这些数百兆字节大小的 Docker 文件。所以，传送这个微小的二进制是令人惊奇的。" — [Brian Ketelsen, Microsoft](https://cloudblogs.microsoft.com/opensource/2018/02/21/go-lang-brian-ketelsen-explains-fast-growth/)._

"使用 Rust，我们将拥有一个高性能和方便的平台，我们可以轻松在 Mac，iOS，Linux，Android 和 Windows 上运行。" [Matt Ronge, Astropad](https://blog.astropad.com/why-rust/)

## 不同点

在设计方面，总是必须进行权衡。虽然 Go 和 Rust 是在同一时间出现的，但他们的目标也很相似，因为他们有时会做出不同的决定，从而在关键方面区分了两种语言。

### 1\. 性能

Go 在开箱即用的时候就有很好的表现。从设计上看，Go 中没有提供可以让你获得更多性能方式。Rust 的目标是使你能够从代码中挤出给你更多的性能; 在这方面，今天你真的找不到比 Rust 更快的语言了。然而，Rust 是以增加复杂性作为提升性能的代价。

"值得注意的是，使用 Rust 编写软件时，我们只需要做基本的优化。即使只进行了最基本的优化, 使用 Rust 编写的软件在性能方面还是超越了使用 Go 大规模重构的版本。这是一个有力的证明，与 Go 相比，使用 Rust 编写高效的程序是多么容易。" — [Jesse Howarth, Discord](https://blog.discord.com/why-discord-is-switching-from-go-to-rust-a190bbca2b1f)._

"Dropbox 的工程发现，通过逐行移植 Python 代码到 Go 中，性能提高了 5 倍和延迟降低了 5 倍，内存使用通常比 Python 显著下降，因为没有 GIL，进程数可能会减少。然而，当我们受到内存限制时，比如在桌面客户端软件或某些服务器进程中，我们会转向 Rust，因为 Rust 中的手动内存管理比 Go GC 更高效。" — Daniel Reiter Horn, Dropbox_

### 2\. 适应能力

Go 的快速迭代的优势允许开发人员快速尝试想法，并在解决手头任务的工作代码中得到锻炼。一般来说，这已经足够了，开发人员可以自由地转移到其他任务上。另一方面，与 Go 相比，Rust 的编译时间更长，导致迭代时间更慢。这使得 Go 在更快的周转时间允许开发人员适应不断变化的需求的情况下工作得更好，而 Rust 在面对有更多时间来实现更精细和更好性能的场景下工作得更好。

Go 类型系统的强大之处在于，调用者可以定义接口，允许库返回扩展的结构，但需要收敛接口。Rust 类型系统的强大之处是匹配语法与 Result<>的结合，在这里您可以静态地确定每个可能性都得到了处理，并且永远不必创建空值来满足未使用的返回参数。— Daniel Reiter Horn, Dropbox_

如果你的用例更接近客户，它更容易受到需求变化的影响，那么 Go 就更好，因为持续重构的成本更低。而是您可以多快地表达新的要求并尝试它们。— Peter Bourgon, Fastly_

### 3\. 上手难度

简单地说，真的没有比 Go 更平易近人的语言。许多团队几个星期就能够适应 Go 并且将 Go 编写的程序用于生产。另外，Go 在语言中相对独一无二，因为它的语言设计和实践在它 10 多年的生命周期中是相当一致的。所以学习 Go 语言是值得的。相比之下，Rust 由于其复杂性而被认为是一种难以学习的语言。它通常需要几个月的学习并且适应 Rust，但这种额外的复杂性带来了精准控制和更高的性能。

"当时，没有一个团队成员知道 Go，但在一个月内，每个人都在写 Go" -  [Jaime Garcia, Capital One](https://medium.com/capital-one-tech/a-serverless-and-go-journey-credit-offers-api-74ef1f9fde7f)_

"Go 不同于其它编程语言的地方是使用 Go 编写的代码更加贴切于常人的理解。您可以用更少的代码做更多的事情，这使得您更容易对最终编写的代码进行推理和理解。大多数的 Go 代码最终看起来非常相似，所以，即使你正在使用一个全新的代码库，你也可以很快上手并运行。"- 美国运通忠诚平台 Glen Balliet 工程总监[American Express Uses Go for Payments & Rewards](https://go.dev/solutions/americanexpress/)_

"然而，与其他编程语言不同的是，Go 是为了最大限度地提高用户效率而创建的。因此，具有 Java 或 PHP 背景的开发人员和工程师可以在几周内提高使用 Go 的技能，并接受培训，根据我们的经验，许多人最终会更喜欢它。"— [Dewet Diener, Curve](https://jaxenter.com/golang-curve-163187.html)_

### 4\. 精准控制

也许 Rust 的最大优势之一是开发者对在内存管理、机器可用资源的使用、代码优化以及问题解决方案的设计等方面拥有大量的控制权。Go 并没有这种精准控制的设计, 而 Go 的设计更适合于更快的探索时间和更快的交付周期。

"随着我们使用 Rust 的经验的增长，它在其他两个轴上显示出了优势:作为一种具有强大的内存安全性的语言，它是边缘处理的好选择;作为一种具有巨大热情的语言，它成为了一种流行于从头开始的组件的语言。"— John Graham-Cumming, Cloudflare_

## 总结

Go 的简单性、性能和开发者的生产力使它成为创建面向用户的应用程序和服务的理想语言。快速迭代允许团队快速调整以满足用户不断变化的需求，为团队提供一种将精力集中在灵活性上的方式。

Rust 的更精细的控制允许更精确的操作，这使得 Rust 成为低级别操作的理想语言，这些操作不太可能发生变化，而且与 Go 相比，它的性能略有改善，尤其是在大规模部署的情况下。

Rust 的优势是最接近机器。Go 的优势们更接近的用户。这并不是说要么不能在另一个空间中工作，但它会增加难度。随着您的需求从灵活性转变为效率，用 Rust 重写库是非常有利的。

虽然 Go 和 Rust 的设计有很大的不同，但它们的设计发挥了一套兼容的优势，当它们一起使用时，可以实现很大的灵活性和性能。

## 建议

对于大多数公司和用户来说，Go 是正确的默认选项。它的性能强大，Go 很容易使用，并且 Go 的高度模块化特性使它特别适合需求变化或演进的情况。

随着产品的成熟和需求的稳定，可能会有机会从性能的微小增长中获得巨大的收益。在这些情况下，使用 Rust 来最大化性能可能更值得。
