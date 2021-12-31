# Rust vs. Go: Why They’re Better Together
- 原文地址：https://thenewstack.io/rust-vs-go-why-theyre-better-together/
- 原文作者：[Jonathan](https://thenewstack.io/author/jonathanturner/) Turner and [Steve Francia](https://thenewstack.io/author/stevefrancia/)
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2021/w52_rust_vs_go_why_there_are_better_together.md.md
- 译者：[xkkhy](https:/github.com/xkkhy)

![](../static/images/2021_w52_rust_vs_go_why_there_better_together/4adf69c9-vehicle-2275456_1280-1024x682.jpg)


[Steve Francia](https://github.com/spf13)
![](../static/images/2021_w52_rust_vs_go_why_there_better_together/84ce064f-image.png)
Over the past 25 years Steve Francia has built some of the most innovative and successful technologies and companies which have become the foundation of cloud computing, embraced by enterprises and developers all over the world. He is currently product and strategy lead for the Go Programming Language at Google. He is the creator of Hugo, Cobra, Viper, spf13-vim and many additional open source projects, having the unique distinction of leading five of the world's largest open source projects


[Jonathan Turner](https://www.jonathanturner.org/)
![](../static/images/2021_w52_rust_vs_go_why_there_better_together/82608378-jonathan_turner_photo.jpg)
Jonathan Turner has worked in open source for more than 20 years, from small projects to large ones, including helping Microsoft transition to open source. He was part of the team that created TypeScript and helped it to grow as program manager and leader of the design team. He also worked on Rust both as a Rust community member and as part of the Mozilla Rust team, which included co-designing Rust's error messages and IDE support.



While others may see [Rust](https://www.rust-lang.org/) and [Go](https://go.dev/) as competitive programming languages, neither the Rust nor the Go teams do. Quite the contrary, our teams have deep respect for what the others are doing, and see the languages as complimentary with a shared vision of modernizing the state of software development industry-wide.
虽然有一些人可能会将 Rust 和 Go 视为互为竞争的编程语言，但 Rust 和 Go 团队都不这么认为。恰恰相反，我们的团队非常尊重其他人正在做的事情，并将这些语言视为对整个软件开发行业现代化的共同愿景的补充。

In this article, we will discuss the pros and cons of Rust and Go and how they supplement and support each other, and our recommendations for when each language is most appropriate.
在本文中，我们将讨论 Rust 和 Go 的优点和缺点以及他们是如何补充和支持彼此，以及我们对这两种语言最合适的建议。

Companies are finding value in adopting both languages and in their complimentary value. To shift from our opinions to hands-on user experience, we spoke with three such companies, [Dropbox](https://www.dropbox.com/), [Fastly](https://www.fastly.com/), and [Cloudflare](https://www.cloudflare.com/), about their experience in using Go and Rust together. There will be quotes from them throughout this article to give further perspective.

已经有一些公司发现同时使用这两种语言具有互补价值。为了让我们的意见更加贴切真实的用户体验，我们和 [dropbox](https://www.dropbox.com/), [fastly](https://www.fastly.com/) 和 [Cloudflare](https://www.cloudflare.com/) 一起发表了关于 Rust 和 Go 一起使用的经验。在本文中将使用引号，以进一步的观点。

## Language Comparison
## 语言比较

Language

Go

Rust

Creation Date

2009

2010

Created at

Google

Mozilla

Notable software written in language

Kubernetes, Docker, Github CLI, Hugo, Caddy, Drone, Ethereum, Syncthing, Terraform

Firefox, ripgrep, alacritty, deno, Habitat

Key workloads

APIs, Web Apps, CLI apps, DevOps, Networking, Data Processing, cloud apps

IoT, processing engines, security-sensitive apps, system components, cloud apps

Developer adoption

8.8% (#12)

5.1% (#19)

Most loved

62.3% (#5)

86.1% (#1)

Most wanted

17.9% (#3)

14.6% (#5)

| 语言                         | Go                                                           | Rust                                                         |
| ---------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 创立日期                     | 2009                                                         | 2010                                                         |
| 创作组织                     | Google                                                       | Mozilla                                                      |
| 用该语言编写的著名软件       | Kubernetes, Docker, Github CLI, Hugo, Caddy, Drone, Ethereum, Syncthing, Terraform | Firefox, ripgrep, alacritty, deno, Habitat                   |
| 主要应用场景                 | APIs, Web Apps, CLI apps, DevOps, Networking, Data Processing, cloud apps | IoT, processing engines, security-sensitive apps, system components, cloud apps |
| 开发者接受程度                 | 8.8% (#12)                                                   | 5.1% (#19)                                                   |
| 最受开发者喜爱的编程语言排行榜 | 62.3% (#5)                                                   | 86.1% (#1)                                                   |
| 开发者最想学习的编程语言排行榜   | 17.9% (#3)                                                   | 14.6% (#5)                                                   |



## Similarities
## 相似之处


Go and Rust have a lot in common. Both are modern software languages born out of a need to provide a safe and scalable solution to the problems impacting software development. Both were created as reactions to shortcomings the creators were experiencing with existing languages in the industry, particularly shortcomings of developer productivity, scalability, safety and concurrency.
Go 和 Rust 有很多共同点。他们都是现代编程语言，他们的诞生都是为了解决软件的安全性和可伸缩性。他们创建的目的都是为了解决当前行业中现有语言的缺陷，特别是开发者的生产率、软件的可伸缩性、安全性和并发性方面的不足。

Most of today’s popular languages were designed over 30 years ago. When those languages were designed there were five key differences from today:
现在流行的编程语言大多是在 30 多年前设计的。当这些语言被设计的时候，与现在有五个关键的区别:

1.  Moore’s law was thought to be eternally true.
1. 摩尔定律被认为是不变的。
2.  Most software projects were written by small teams, often working in person together.
2. 大多数软件项目是由小型团队编写的，他们经常在一起工作。
3.  Most software had a relatively small number of dependencies, mostly proprietary.
3. 大部分软件是相对较少的依赖，可能大部分还是专有的。
4.  Safety was a secondary concern… or not a concern at all.
4. 比较少关注软件的安全问题，或者根本不考虑这一块的内容。
5.  Software was typically written for a single platform.
5. 软件一般不能跨平台运行。

In contrast, both Rust and Go were written for today’s world and generally took similar approaches to design a language for today’s development needs.
相比之下，Rust 和 Go 都是为满足当今世界的开发环境来编写的，他们采用类似的设计方法来解决当今的软件来发需求。

### 1\. Performance and Concurrency
### 1. 性能和并发性

Go and Rust are both compiled languages focused on producing efficient code. They also provide easy access to the multiple processors of today’s machines, making them ideal languages for writing efficient parallel code.
Go 和 Rust 都是编译型语言,专注于代码的执行效率。它们还可以轻松访问当今机器的多个处理器，使其成为编写有效并行代码的理想语言。

_“Using Go allowed MercadoLibre to cut the number of servers they use for this service to one-eighth the original number (from 32 servers down to four), plus each server can operate with less power (originally four CPU cores, now down to two CPU cores). With Go, the company obviated 88 percent of their servers and cut CPU on the remaining ones in half—producing a tremendous cost-savings.”_— “[MercadoLibre Grows with Go](https://go.dev/solutions/mercadolibre/)”
"使用 Go 之后，“MercadoLibre” 将原本用于服务器数量减少到原来的八分之一(从32台服务器减少到4台)，而且每个服务器可以使用更少的算力(原来是4个CPU核，现在减少到2个CPU核)。使用 Go 之后，MercadoLibre 减少了88%的服务器费用，并将剩余服务器的CPU削减了一半, 节省了成本" -- [MercadoLibre Grows with Go](https://go.dev/solutions/mercadolibre/)

_“In our tightly managed environments where we run Go code, we have seen a CPU reduction of approximately ten percent \[vs C++\] with cleaner and maintainable code.”_ — [Bala Natarajan, Paypal](https://go.dev/solutions/paypal/)
"在我们严格管控的环境中，我们运行Go代码，我们看到CPU减少了大约10%(与c++相比)，代码更整洁、更加容易维护。"— [Bala Natarajan, Paypal](https://go.dev/solutions/paypal/)

_“Here at AWS, we love Rust, too, because it helps AWS write highly performant, safe infrastructure-level networking and other systems software. Amazon’s first notable product built with Rust, Firecracker, launched publicly in 2018 and provides the open source virtualization technology that powers AWS Lambda and other serverless offerings. But we also use Rust to deliver services such as Amazon Simple Storage Service (Amazon S3), Amazon Elastic Compute Cloud (Amazon EC2), Amazon CloudFront, Amazon Route 53, and more. Recently we launched Bottlerocket, a Linux-based container operating system written in Rust.” — [Matt Asay, Amazon Web Services](https://aws.amazon.com/blogs/opensource/why-aws-loves-rust-and-how-wed-like-to-help/)_
"在 AWS，我们也喜欢 Rust，Rust 助力 AWS 编写高性能、安全的基础设施级网络和其他系统软件。Firecracker 是亚马逊用在 2008 年推出的第一款用 Rust 实现的虚拟化软件，主要是为 AWS  的 Lambda 架构和其他 serverless 产品提供支持。但我们也使用 Rust 来提供Amazon Simple Storage Service (Amazon S3)、Amazon Elastic Compute Cloud (Amazon EC2)、Amazon CloudFront、Amazon Route 53等服务。最近，我们推出了使用 Rust 编写的基于linux的容器操作系统——botlerocket"[Matt Asay, Amazon Web Services](https://aws.amazon.com/blogs/opensource/why-aws-loves-rust-and-how-wed-like-to-help/)_

_We “saw an extraordinary 1200-1500% increase in our speed! We went from 300-450ms in release mode with Scala with fewer parsing rules implemented, to 25-30ms in Rust with more parsing rules implemented!” — [Josh Hannaford, IBM](https://developer.ibm.com/technologies/web-development/articles/why-webassembly-and-rust-together-improve-nodejs-performance/)_
我们看到我们的速度惊人地增长了1200-1500%! 我们从用 scala 实现的产品化更多的时间做更少的事情(300-500ms)，到 Rust 实现的产品花费更少的时间做更多的事情(25-30ms)![Josh Hannaford, IBM](https://developer.ibm.com/technologies/web-development/articles/why-webassembly-and-rust-together-improve-nodejs-performance/)_

### 2\. Team Scalable — Reviewable
### 2\. 团队可伸缩, 代码可走读

Software development today is built by teams that grow and expand, often collaborating in a distributed way using source control. Go and Rust are both designed for how teams work, improving code reviews by removing unnecessary concerns like formatting, security, and complex organization. Both languages require relatively little context to understand what the code is doing, allowing reviewers to more quickly work with code written by other people and review code by both team members and code contributed by open source developers outside of your team.
当今软件的开发团队可能是不断变化的(团队成员可能是不断扩充)，一般是以分布式的方式进行代码管理。Go和Rust都是为团队的工作方式而设计的，通过消除不必要的问题，如格式、安全性和复杂的组织，来改善代码审查。这两种语言都需要相对较少的上下文来理解代码正在做什么，从而允许审查人员更快地处理其他人编写的代码，包括团队成员的代码和外部的开源代码。

_“Building Go and Rust code, having come from a Java and Ruby background in my early career, felt like an impossible weight off my shoulders. When I was at Google, it was a relief to come across a service that was written in Go, because I knew it would be easy to build and run. This has also been true of Rust, though I’ve only worked on that at a much smaller scale. I’m hoping that the days of infinitely configurable build systems are dead, and languages all ship with their own purpose-built build tools that just work out of the box.”— [Sam Rose, CV Partner](https://bitfieldconsulting.com/golang/rust-vs-go)_
"在我早期的职业生涯中，有过Java和Ruby经历，所以编写Go和Rust的代码感觉得很轻松。在谷歌的时候，用 Go 编写的服务让我如释重负，因为我知道它很容易构建和运行。当然了 Rust 也是如此，尽管我只在一些小规模的项目中应用过。我期待无休止地配置构建环境的日子已经一去不复返了，所有的语言都有自己的专用构建工具，并且这些工具可以开箱即用。-"[Sam Rose, CV Partner](https://bitfieldconsulting.com/golang/rust-vs-go)_

_“I tend to breathe a sigh of relief when writing a service in Go since it has a very simple, easy to reason about, static type system compared to dynamic languages, concurrency is a first-class citizen, and Go’s standard library is both unbelievably polished and powerful, yet also to the point. Take a standard Go install, throw in a grpc library and a database connector, and you need very little else to build anything on the server-side, and every engineer will be able to read the code and understand the libraries. When writing a module in Rust, Dropbox engineers felt Rust’s growing pains on the server-side before Async-await stabilized in 2019, but since then, crates are converging to use it and we get the benefit of async patterns coupled with fearless concurrency.” — Daniel Reiter Horn, Dropbox_
"用 Go 编写服务是相对轻松的事情, 与动态语言相比，它有一个非常简单、易于推理的静态类型系统，并发性是一等公民，而且 Go 的标准库既令人难以置信的优美又强大，但也恰到好处。使用一个标准的 Go 程序，添加一个grpc库和一个数据库连接器，您只需要很少的其他东西就可以在服务器端构建任何东西，并且每个工程师都能够阅读代码并理解这些库。在用 Rust 编写模块时，在 2019 年的时候, Dropbox 的工程师在 Async-await 模块稳定之前就感受到了 Rust 在服务器端的强大之处，所以从那时起，Dropbox 就开始尝试使用它，并从中获得了异步模式和强大并发能力的好处" - Daniel Reiter Horn, Dropbox_

### 3\. Open Source-aware
### 3\. 开源意识

The number of dependencies used by the average software project today is staggering. The decades-long goal of software reuse has been achieved in modern development, where today’s software is built using 100s of projects. To do so, developers use software repositories, which increasingly has become a staple of software development across a broadening range of applications. Each of the packages a developer includes, in turn, has its own dependencies. Languages for today’s programming environments need to handle this complexity effortlessly.
今天，普通软件项目所使用的依赖项的数量是惊人的。几十年来的软件重用目标已经在现代开发中实现了，今天的软件是使用数百个项目构建的。所以，代码仓库已经逐渐成为各种应用程序中软件开发的主要内容。开发者所包含的每个包都有自己的依赖项。所以当今编程环境的语言需要轻松地处理这种复杂的依赖。

Both Go and Rust have package-management systems that allow developers to make a simple list of the packages they’d like to build on, and the language tools automatically fetch and maintain those packages for them, so that developers can focus more on their own code and less on the management of others.
Go和Rust都有自己的包管理工具，这些管理工具会自动管理开发者获取和维护开发这构建的软件包列表，这样开发者就能更加专注于自己的业务代码。

### 4\. Safety
### 4\. 安全

The security concerns of today’s applications are well-addressed by both Go and Rust, which ensure that code built in the languages run without exposing the user to a variety of classic security vulnerabilities like buffer overflows, use-after-free, etc. By removing these concerns, developers can focus on the problems at hand and build applications that are more secure by default.
Go和Rust都很好地解决了当今应用程序的安全问题，它们确保用这些语言构建的代码在运行时不会暴露给用户各种经典的安全漏洞，如缓冲区溢出、释放后可重用等。没有这些顾虑，开发者可以更加专注于自己的业务问题，并构建默认情况下更安全的应用程序。

_“The \[Rust\] compiler really holds your hand when working through the errors that you do get. This lets you focus on your business objectives rather than bug hunting or deciphering cryptic messages.” — [Josh Hannaford, IBM](https://developer.ibm.com/technologies/web-development/articles/why-webassembly-and-rust-together-improve-nodejs-performance/)_
"当处理你遇到的错误时，Rust的编译器会帮助解决。这使您可以专注于业务，而不是寻找bug或处理棘手的问题。"— [Josh Hannaford, IBM](https://developer.ibm.com/technologies/web-development/articles/why-webassembly-and-rust-together-improve-nodejs-performance/)_

_“In short, the flexibility, safety, and security of Rust outweighs any inconvenience of having to follow strict lifetime, borrowing, and other compiler rules or even the lack of a garbage collector. These features are a much-needed addition to cloud software projects and will help avoid many bugs commonly found in them.” — [Taylor Thomas, Sr., Microsoft](https://msrc-blog.microsoft.com/2020/04/29/the-safety-boat-kubernetes-and-rust/)._
"总的来说，Rust是灵活性和安全性的,并且它的安全性超过了必须遵守严格的生命周期、借用和其他编译器规则，另外值得注意的是, Rust 是没有垃圾回收机制的。这些特性是云软件项目非常需要的功能，将有助于避免许多常见的bug。"— [Taylor Thomas, Sr., Microsoft](https://msrc-blog.microsoft.com/2020/04/29/the-safety-boat-kubernetes-and-rust/)._

_“Go is strongly and statically typed with no implicit conversions, but the syntactic overhead is still surprisingly small. This is achieved by simple type inference in assignments together with untyped numeric constants. This gives Go stronger type safety than Java (which has implicit conversions), but the code reads more like Python (which has untyped variables).” — [Stefan Nilsson, computer science professor](https://yourbasic.org/golang/advantages-over-java-python/)._
"Go是强静态类型，没有隐式转换，但语法开销仍然非常小。这是通过简单的类型推断在赋值与无类型的数值常量一起实现的。这给了Go比Java (Java有隐式转换)更强的类型安全，但代码读起来更像Python (Python有无类型变量)。" — [Stefan Nilsson, computer science professor](https://yourbasic.org/golang/advantages-over-java-python/)

_“When building our Brotli compression library for storing block data at Dropbox, we limited ourselves to the safe subset of Rust and, further, to the core library (no-stdlib) as well, with the allocator specified as a generic. Using the subset of Rust this way made it very easy to call the Rust-Brotli library from Rust on the client-side and using the C FFI from both Python and Go on the Server. This compilation mode also provided [substantial security guarantees](https://dropbox.tech/infrastructure/lossless-compression-with-brotli). After some tuning, the Rust Brotli implementation, despite being 100% safe, array-bounds-checked code, was still faster than the corresponding native Brotli code in C.” — Daniel Reiter Horn, Dropbox_
"在构建用于在 Dropbox 存储块数据的 Brotli 压缩库时，我们将自己限制在 Rust 的安全子集，此外，还限制到核心库（no-stdlib），并将分配器指定为泛型。以这种方式使用 Rust 的子集使得在客户端从 Rust 调用 Rust-Brotli 库并在服务器上使用来自 Python 和 Go 的 C FFI 变得非常容易。这种编译方式还提供了[实质性的安全保证](https:dropbox.techinfrastructurelossless-compression-with-brotli)。经过一些调整，Rust Brotli 在实现 100% 安全情况下，同时拥有数组边界检查的代码仍然比 C 中实现的 Brotli 代码快"- Daniel Reiter Horn, Dropbox_

### 5\. Truly Portable
### 5\. 真的轻便

It is trivial in both Go and Rust to write one piece of software that runs on many different operating systems and architectures. “Write once, compile anywhere.” In addition, both Go and Rust natively support cross-compilation eliminating the need for “build farms” commonly associated with older compiled languages.
对于Go和Rust来说，编写一个可以在多个不同的操作系统和架构上运行的软件是比较容易的。编写一次，在任何地方编译。此外，Go和Rust都天生支持交叉编译，不需要配置构建环境。

_“Golang possesses great qualities for production optimization such as having a small memory footprint, which supports its capability for being building blocks in large-scale projects, as well as easy cross-compilation to other architectures out of the box. Since Go code is compiled into a single static binary, it allows easy containerization and, by extension, makes it almost trivial to deploy Go into any highly available environment such as Kubernetes.” — [Dewet Diener, Curve](https://jaxenter.com/golang-curve-163187.html)._
"Golang 构建出来的产品具有优秀的品质，比如内存占用小，这支持它在大型项目中作为其中模块的能力，以及易于交叉编译到其他现成的架构。由于Go代码被编译成单一的静态二进制，它允许很容易的容器化，并通过扩展，使得将Go部署到任何高可用性的环境(如Kubernetes)中几乎很容易" — [Dewet Diener, Curve](https://jaxenter.com/golang-curve-163187.html)

_“When you look at a cloud-based infrastructure, often you’re using something like a Docker container to deploy your workloads. With a static binary that you build in Go, you could have a Docker file that’s 10, 11, 12 megabytes instead of bringing in the entire Node.js ecosystem, or Python, or Java, where you’ve got these hundreds of megabyte-sized Docker files. So, shipping that tiny binary is amazing.” — [Brian Ketelsen, Microsoft](https://cloudblogs.microsoft.com/opensource/2018/02/21/go-lang-brian-ketelsen-explains-fast-growth/)._
"当你查看基于云的基础设施时，你通常使用Docker容器之类的组件来部署你的应用。使用Go构建的静态二进制文件，你可以有一个10、11、12兆字节的Docker文件，而不是引入整个Node.js生态系统，或Python或Java，在那里你有这些数百兆字节大小的Docker文件。所以，传送这个微小的二进制是令人惊奇的。" — [Brian Ketelsen, Microsoft](https://cloudblogs.microsoft.com/opensource/2018/02/21/go-lang-brian-ketelsen-explains-fast-growth/)._

_“With Rust, we’ll have a high-performance and portable platform that we can easily run on Mac, iOS, Linux, Android, and Windows.” — [Matt Ronge, Astropad](https://blog.astropad.com/why-rust/)._
"使用Rust，我们将拥有一个高性能和方便的平台，我们可以轻松在Mac，iOS，Linux，Android和Windows上运行。" [Matt Ronge, Astropad](https://blog.astropad.com/why-rust/)

## Differences
## 不同点

In design, there are always trade-offs that must be made. While Go and Rust emerged around the same time with similar goals, as they faced decisions at times they chose different trade-offs that separated the languages in key ways.
在设计方面，总是必须进行权衡。虽然Go和Rust是在同一时间出现的，但他们的目标也很相似，因为他们有时会做出不同的决定，从而在关键方面区分了两种语言。

### 1\. Performance
### 1\. 性能

Go has excellent performance right out of the box. By design, there are no knobs or levers that you can use to squeeze more performance out of Go. Rust is designed to enable you to squeeze every last drop of performance out of the code; in this regard, you really can’t find a faster language than Rust today. However, Rust’s increased performance comes at the cost of additional complexity.
Go在开箱即用的时候就有很好的表现。从设计上看，Go 中没有提供可以让你获得更多性能方式。Rust的目标是使你能够从代码中挤出给你更多的性能; 在这方面，今天你真的找不到比Rust更快的语言了。然而，Rust 是以增加复杂性作为提升性能的代价。

_“Remarkably, we had only put very basic thought into optimization as the Rust version was written. Even with just basic optimization, Rust was able to outperform the hyper-hand-tuned Go version. This is a huge testament to how easy it is to write efficient programs with Rust compared to the deep dive we had to do with Go.” — [Jesse Howarth, Discord](https://blog.discord.com/why-discord-is-switching-from-go-to-rust-a190bbca2b1f)._
"值得注意的是，使用Rust编写软件时，我们只需要做基本的优化。即使只进行了最基本的优化, 使用 Rust 编写的软件在性能方面还是超越了使用 Go 大规模重构的版本。这是一个有力的证明，与Go相比，使用Rust编写高效的程序是多么容易。" — [Jesse Howarth, Discord](https://blog.discord.com/why-discord-is-switching-from-go-to-rust-a190bbca2b1f)._

_“Dropbox engineers often see 5x performance and latency improvements by porting line-for-line Python code into Go, and memory usage often drops dramatically as compared with Python as there is no GIL and the process count may be reduced. However, when we are memory constrained, as on desktop client software or in certain server processes, we move over to Rust as the manual memory management in Rust is substantially more efficient than the Go GC.” — Daniel Reiter Horn, Dropbox_
"Dropbox的工程发现，通过逐行移植Python代码到Go中，性能提高了5倍和延迟降低了5倍，内存使用通常比Python显著下降，因为没有GIL，进程数可能会减少。然而，当我们受到内存限制时，比如在桌面客户端软件或某些服务器进程中，我们会转向Rust，因为Rust中的手动内存管理比Go GC更高效。" — Daniel Reiter Horn, Dropbox_

### 2\. Adaptability/Interability
### 2\. 适应能力

Go’s strength of quick iteration allows developers to try ideas quickly and hone in on working code that solves the task at hand. Often, this is sufficient and frees the developer to move onto other tasks. Rust, on the other hand, has longer compiles compared with Go, leading to slower iteration times. This leads Go to work better in scenarios where faster turnaround time allows developers to adapt to changing requirements, while Rust thrives in scenarios where more time can be given to making a more refined and performant implementation.
Go的快速迭代的优势允许开发人员快速尝试想法，并在解决手头任务的工作代码中得到锻炼。一般来说，这已经足够了，开发人员可以自由地转移到其他任务上。另一方面，与Go相比，Rust的编译时间更长，导致迭代时间更慢。这使得Go在更快的周转时间允许开发人员适应不断变化的需求的情况下工作得更好，而Rust在更多的时间可以用来制作更精细和性能更好的实现的情况下工作得更好。

_“The genius of the Go type system is that callers can define the Interfaces, allowing libraries to return expansive structs but require narrow interfaces. The genius of the Rust type system is the combination of match syntax with Result<>, where you can be statically certain every eventuality is handled and never have to invent null values to satisfy unused return parameters.” — Daniel Reiter Horn, Dropbox_
Go类型系统的强大之处在于，调用者可以定义接口，允许库返回扩展的结构，但需要收缩的接口。Rust类型系统的强大之处是匹配语法与Result<>的结合，在这里您可以静态地确定每个可能性都得到了处理，并且永远不必创建空值来满足未使用的返回参数。— Daniel Reiter Horn, Dropbox_

_“(I)f your use case is closer to customers, it’s more vulnerable to shifting requirements, then Go is a lot nicer because the cost of continuous refactor is a lot cheaper. It’s how fast you can express the new requirements and try them out.” — Peter Bourgon, Fastly_
如果你的用例更接近客户，它更容易受到需求变化的影响，那么Go就更好，因为持续重构的成本更低。而是您可以多快地表达新的要求并尝试它们。— Peter Bourgon, Fastly_

### 3\. Learnability
### 3\. 易学性

Simply put, there really isn’t a more approachable language than Go. There are many stories of teams who were able to adopt Go and put Go services/applications into production in a few weeks. Additionally, Go is relatively unique among languages in that its language design and practices are quite consistent over it’s 10+ year lifetime. So time invested in learning Go maintains its value for a long time. By comparison, Rust is considered a difficult language to learn due to its complexity. It generally takes several months of learning Rust to feel comfortable with it, but with this extra complexity comes precise control and increased performance.
简单地说，真的没有比 Go 更平易近人的语言。许多团队几个星期就能够适应 Go 并且将Go编写的程序用于生产。另外，Go在语言中相对独一无二，因为它的语言设计和实践在它10多年的生命周期中是相当一致的。所以学习 Go 语言是值得的。相比之下，Rust 由于其复杂性而被认为是一种难以学习的语言。它通常需要几个月的学习并且适应 Rust，但这种额外的复杂性带来了精准控制和更高的性能。

_“At the time, no single team member knew Go, but within a month, everyone was writing in Go” – [Jaime Garcia, Capital One](https://medium.com/capital-one-tech/a-serverless-and-go-journey-credit-offers-api-74ef1f9fde7f)_
"当时，没有一个团队成员知道 Go，但在一个月内，每个人都在写 Go" -  [Jaime Garcia, Capital One](https://medium.com/capital-one-tech/a-serverless-and-go-journey-credit-offers-api-74ef1f9fde7f)_

_“What makes Go different from other programming languages is cognitive load. You can do more with less code, which makes it easier to reason about and understand the code that you do end up writing. The majority of Go code ends up looking quite similar, so, even if you’re working with a completely new codebase, you can get up and running pretty quickly.” — Glen Balliet Engineering Director of loyalty platforms at American Express [American Express Uses Go for Payments & Rewards](https://go.dev/solutions/americanexpress/)_
"Go 不同于其它编程语言的地方是使用 Go 编写的代码更加贴切于常人的理解。您可以用更少的代码做更多的事情，这使得您更容易对最终编写的代码进行推理和理解。大多数的Go代码最终看起来非常相似，所以，即使你正在使用一个全新的代码库，你也可以很快上手并运行。"- 美国运通忠诚平台Glen Balliet工程总监[American Express Uses Go for Payments & Rewards](https://go.dev/solutions/americanexpress/)_

_“However, unlike other programming languages, Go was created for maximum user efficiency. Therefore developers and engineers with Java or PHP backgrounds can be upskilled and trained in using Go within a few weeks — and in our experience, many of them end up preferring it.” — [Dewet Diener, Curve](https://jaxenter.com/golang-curve-163187.html)_
"然而，与其他编程语言不同的是，Go是为了最大限度地提高用户效率而创建的。因此，具有Java或PHP背景的开发人员和工程师可以在几周内提高使用Go的技能，并接受培训，根据我们的经验，许多人最终会更喜欢它。"— [Dewet Diener, Curve](https://jaxenter.com/golang-curve-163187.html)_

### 4\. Precise Control
### 4\. 精准控制

Perhaps one of Rust’s greatest strengths is the amount of control the developer has over how memory is managed, how to use the available resources of the machine, how code is optimized, and how problem solutions are crafted. This is not without a large complexity cost when compared to Go, which is designed less for this type of precise crafting and more for faster exploration times and quicker turnaround times.
也许Rust的最大优势之一是开发者对在内存管理、机器可用资源的使用、代码优化以及问题解决方案的设计等方面拥有大量的控制权。Go 并没有这种精准控制的设计, 而Go的设计更适合于更快的探索时间和更快的交付周期。

_“As our experience with Rust grew, it showed advantages on two other axes: as a language with strong memory safety it was a good choice for processing at the edge and as a language that had tremendous enthusiasm it became one that became popular for de novo components.”  — John Graham-Cumming, Cloudflare_
"随着我们使用Rust的经验的增长，它在其他两个轴上显示出了优势:作为一种具有强大的内存安全性的语言，它是边缘处理的好选择;作为一种具有巨大热情的语言，它成为了一种流行于从头开始的组件的语言。"— John Graham-Cumming, Cloudflare_

## Summary/Key Takeaways
## 总结

Go’s simplicity, performance, and developer productivity make Go an ideal language for creating user-facing applications and services. The fast iteration allows teams to quickly pivot to meet the changing needs of users, giving teams a way to focus their energies on flexibility.
Go的简单性、性能和开发者的生产力使它成为创建面向用户的应用程序和服务的理想语言。快速迭代允许团队快速调整以满足用户不断变化的需求，为团队提供一种将精力集中在灵活性上的方式。

Rust’s finer control allows for more precision, making Rust an ideal language for low-level operations that are less likely to change and that would benefit from the marginally improved performance over Go, especially if deployed at very large scales.
Rust的更精细的控制允许更精确的操作，这使得Rust成为低级别操作的理想语言，这些操作不太可能发生变化，而且与Go相比，它的性能略有改善，尤其是在大规模部署的情况下。

Rust’s strengths are at the most advantageous closest to the metal. Go’s strengths are at their most advantageous closer to the user. This isn’t to say that either can’t work in the other’s space, but it would have increased friction to doing so. As your requirements shift from flexibility to efficiency it makes a stronger case to rewrite libraries in Rust.
Rust的优势是最接近机器的最有利的。Go的优势是他们最有利的更近的用户。这并不是说要么不能在另一个空间中工作，但它会增加难度。随着您的需求从灵活性转变为效率，它会更加强大的情况来重写 Rust 库。

While the designs of Go and Rust differ significantly, their designs play to a compatible set of strengths, and — when used together — allow both great flexibility and performance.
虽然Go和Rust的设计有很大的不同，但它们的设计发挥了一套兼容的优势，当它们一起使用时，可以实现很大的灵活性和性能。

## Recommendations
## 建议

For most companies and users, Go is the right default option. Its performance is strong, Go is easy to adopt, and Go’s highly modular nature makes it particularly good for situations where requirements are changing or evolving.
对于大多数公司和用户来说，Go 是正确的默认选项。它的性能强大，Go很容易使用，并且Go的高度模块化特性使它特别适合需求变化或演进的情况。

As your product matures, and requirements stabilize, there may be opportunities to have large wins from marginal increases in performance. In these cases, using Rust to maximize performance may well be worth the initial investment.
随着产品的成熟和需求的稳定，可能会有机会从性能的微小增长中获得巨大的收益。在这些情况下，使用Rust来最大化性能可能值得最初的投资。