# 选择技术栈

原文地址：[Choosing a (Language) Stack](https://engineering.wework.com/choosing-a-language-stack-cac3726928f6)

原文作者：[wework](https://engineering.wework.com/@nick.wework)

译文出处: https://engineering.wework.com/choosing-a-language-stack-cac3726928f6

本文永久链接：???

译者：[louyuting](https://github.com/louyuyting)

校对：[mozart34](https://github.com/mozart34)

This post and the experiment was a collaborative effort by Michael Farinacci (Load Testing), Nick Gordon (Ruby), Iain McGinniss (Kotlin), and Kevin Steuer (Go).

本文和文中相关实验是由Michael Farinacci(负载测试)、Nick Gordon (Ruby)、Iain McGinniss (Kotlin)和Kevin Steuer (Go)一起合作完成的。

# Introduction
# 背景介绍
Our team has been tasked with building the next generation of Identity infrastructure for WeWork. With the anticipated rate at which WeWork and its sibling businesses are growing, it is important that this new system be efficient, globally distributed, scalable, and permit reasonable evolution as requirements change over the coming years.

我们团队的任务是为 WeWork 构建下一代的身份认证基础设施。随着最近几年 WeWork以及其兄弟公司业务的可预期增长，这套新系统必须高效、全球分布式、可伸缩并能够进行合理的演进以满足未来公司需求的变化，这十分重要。

Based on these challenges, the team felt it was worth investing the time to compare the available languages and software stacks for building microservices. We had three candidate languages: Go, Kotlin, and Ruby. The comparison was made by building the same realistic component of an Identity system in each. We chose a token mint service, which produces bearer tokens like refresh and access tokens in an OAuth2 based infrastructure. Each language has some precedent in other systems built at WeWork, and each implementation was written by a developer with experience in that language.

基于这些挑战，团队认为花时间去调研对比构建微服务的语言和技术栈是非常必要的。我们有三个可选的语言: Go、Kotlin 和 Ruby。比较的方法是在每一个身份认证系统中构建相同的真实组件。我们选择了token mint服务作为测试组件，它基于OAuth2的基础设施生成诸如 refresh 和 access token 之类的承载 token 。这三种语言在WeWork的其余系统中都已经有一些实际应用，并且基于这些语言的应用都由有经验的工程师编码实现。

Upon completion of these implementations, they were compared across the following qualitative and quantitative metrics by the team:

* Qualitative comparison of the readability of the code.
* Qualitative comparison of how straightforward it was to test each implementation, at a unit and integration test level.
* Qualitative comparison of the “boilerplate” necessary in each implementation, versus the code that represents the essence of the service.
* Qualitative comparison of the tools available for each stack, such as IDEs, static analysis, debuggers, profilers, etc.
* Quantitative comparison of the performance of each implementation, such as round trip time percentiles and host resource utilization.

在完成这三种语言的token mint服务的实现之后，团队通过以下定性和定量指标对它们进行了比较:

* 定性比较代码的可读性
* 定性比较测试每个实现的单元测试和集成测试的难易程度
* 定性比较每个实现中必需的“样板文件”与表示服务本质的代码
* 定性比较每个技术栈可用工具，如ide、静态分析、调试器、分析器等
* 定量比较每个实现的性能，如RT的百分比和机器资源利用率。

Ultimately, an experiment like this cannot be wholly scientific — software engineering is influenced by sociological factors as much as by science and mathematics. Our goal was primarily to pick a good all-rounder language and tool set, that the team will be comfortable working with over the next five years.

最后，像这样的实验不可能完全是科学的——软件工程受社会学因素的影响不亚于受科学和数学的影响。我们的首要目标是选择一个优秀全面的语言和工具集，使得团队在接下来的五年里能够很舒适的使用它。

# The Token Mint Service
# The Token Mint Service

The service selected for this exercise was a “token mint”, which produces three types of bearer tokens: refresh tokens, access tokens, and “action” tokens. Isolating token production and verification into its own service can help to isolate the use of cryptographic keys, that are critical to system-wide security.

对于这个测试，所选择的服务是 token mint, 它生成三种类型的承载令牌:刷新令牌、访问令牌和“操作”令牌。将 Tokem 生产和验证隔离到自己的服务中，可以帮助隔离对系统安全性至关重要的加密密钥的使用。

The refresh and access tokens produced by this service have the usual OAuth2 semantics: refresh tokens do not expire but can be revoked and are used to produce access tokens that expire after 18 hours. “Action” tokens are a non-standard addition; access tokens are exchanged for action tokens in the context of a single external API call. We would perform this exchange using a request interceptor at the API gateway (we use Kong), in order to help to decrease the risks associated with accidental or malicious token logging or exfiltration in misbehaving downstream services.

此服务生成的refresh和access令牌具有通常的OAuth2语义:refresh Token不会过期，但可以撤消，并用于生成18小时后过期的 access Token。“action” token是非标准的添加;访问令牌在单个外部API调用的上下文中交换为操作令牌。我们将在API网关上使用请求拦截器执行此交换(我们使用Kong)，以帮助降低在行为不端的下游服务中意外或恶意令牌日志记录或过滤相关的风险。

The produced token values, from the perspective of any other system or client, are just url-safe ASCII strings. They do, however, have internal structure. They are Base64 encodings of a binary protocol buffer, that contains token metadata and a digital signature. The signature algorithm used in the experiment is ECDSA, over the NIST P-256 curve.

从任何其他系统或客户端的角度来看，生成的token只是url安全的ASCII字符串。然而，它们确实有内部结构。它们是二进制协议缓冲区的Base64编码，其中包含token元数据和数字签名。实验中使用的签名算法是ECDSA，在NIST P-256曲线上。

The service offers five operations to other authorized components of the Identity system, over gRPC:

* Mint a refresh token for a specified user
* Revoke a refresh token
* Mint an access token, given a non-revoked refresh token
* Mint an action token, given a non-expired access token
* Get info on a supplied token

该服务基于gRPC向身份系统的其他授权组件提供五项操作:

* 为指定的用户生成一个refresh token
* 撤销refresh token
* 给定一个不可撤销的refresh token，生成一个access token
* 给定一个不会过期的access token, 生成一个action token
* 在一个已经提供的token上获取信息

The service is simple enough to be implemented in a few weeks by a single engineer, while being representative of the real systems we must build:

* The service must interact with a database to store information on the tokens it generates, and to remember which refresh tokens have been revoked.
* The service must handle multiple concurrent requests, and be able to scale and distribute to handle thousands of requests per second.
* As a security sensitive service, inputs and outputs must be carefully validated, and careful use of cryptographic primitives is necessary.

该服务非常简单，只需一个工程师在几周内就可以实现，但是必须代表我们构建的真实系统:

* 该服务必须与数据库进行交互，以存储其生成的token上的信息，并记住哪些refresh token已被撤销。
* 该服务必须处理高并发请求，并且能够扩展和分发以处理数千的QPS
* 作为一个对安全十分敏感的系统，系统的输入和输出都必须验证，并且需要仔细使用密码原语

A system of this nature is primarily I/O bound and performs database writes and queries over a network. The most compute-intensive operations are the generation and validation of digital signatures. Production and validation of token metadata and protocol buffers is computationally trivial in comparison.

这种性质的系统主要是I/O操作的，并在网络上执行数据库读写。该系统计算最密集的操作是生成和验证数字签名。对比数字签名的验证，token元数据和协议缓冲区的生成在计算消耗上是微不足道的。

# Load testing
# 负载测试
A load test client was implemented in Go, using gRPC client stubs generated from the service definition. The load tester simulated a population of users interacting with the system, given a reasonable approximation of expected usage patterns.

负载测试的客户端使用Go语言实现，使用从服务定义生成的gRPC客户端。负载测试器模拟了与系统交互的用户群，给出了预期使用模式的合理近似值。

For one user, we may expect (on average) one refresh token request per six months, one access token request per day, and one action token request per hour. Combining these assumptions with a simulated population size p produces an estimation of the average load on the system: l(p) = p × 2.894 × 10⁻⁴ requests per second, with 95% of those requests being action token requests. Given a population size of 100k users, the load tester would generate roughly 29 token requests per second. By adjusting the simulated population size, and/or running multiple load test processes in parallel (on different machines, if necessary), the load on the service was adjusted.

对于一个用户，我们可能期望(平均)每六个月有一个refresh token的请求，每天有一个access token请求，每小时有一个action token请求。将这些假设与模拟人口规模p产生估计的平均负载系统:l(p) = p×2.894×10⁻⁴ QPS,与95%的请求被action token请求。假设用户总数为10万，那么负载测试器每秒将生成大约29个token请求。通过调整模拟的总体大小或并行运行多个负载测试进程(如果需要，在不同的机器上)，可以调整服务上的负载。

The load testing client recorded the round trip time for every request made in microseconds, and any errors that occur. This information was then used to produce request scatter plots, histograms, and other statistics. We could tell when a service starts to reach its scaling limits when its average latency and/or 90th percentile starts to climb noticeably — this typically indicated some form of resource starvation.

负载测试客户端记录了以微秒为单位发出的每个请求的RT，以及发生的任何错误。然后使用这些信息生成请求散点图、直方图和其他统计信息。当服务的平均延迟时间或90%的开始显著上升时，我们就可以知道服务何时开始达到其伸缩性限制—这通常表示某些资源匮乏。

# Load Test Results
# 负载测试的结果
The database started to throttle throughput at a population size of around 1.5 million, we compared the performance of the implementations at 1.0 million. At this population size, the load testing client attempted to generate an average of 289.4 requests per second. The most interesting stats were:

在大约150万人口的情况下数据库开始产生吞吐量性能限制，我们比较了在100万人口情况下实现的性能。在这个总体大小下，负载测试客户端试图平均每秒生成289.4个请求。最有趣的数据是:
[https://github.com/louyuting/translator/blob/master/static/images/w14_choosing_a_language_stack/1_loading_test_result.jpeg](https://github.com/louyuting/translator/blob/master/static/images/w14_choosing_a_language_stack/1_loading_test_result.jpeg)

Here, we can see each implementation offers very similar median response times, within fractions of a millisecond. However, the Kotlin implementation starts to exhibit measurably worse 95th and 99th percentile latencies; we speculate that this may be due to the context switches involved in passing data between the network, coroutine execution and JDBC query thread pools that the implementation used. Such context switching was unnecessary in both the Go and Ruby implementations. It was also clear that Go required the least compute time of the three implementations to handle the supplied load. Ruby’s CPU usage stats may have been slightly misleading, as the errors (~3% of requests) produced had minimal impact on CPU usage: requests were rejected prior to any real processing.

从上表我们可以看到三种技术栈的平均响应时间几乎差不多，差距不到一毫秒。然而，Kotlin语言的实现开始出现更糟的95和99百分位延迟;我们推测，这可能是因为该实现方案使用的网络、协程执行和JDBC查询线程池之间传递数据时涉及到上下文切换。然而这种上下文切换在Go和Ruby实现中都是不必要的。同样明显的是，在这三种实现中，Go处理所提供的负载所需的计算时间最少。Ruby的CPU使用统计数据可能有一点误导人，请求在实际处理之前被拒绝导致产生的错误(约3%的请求)对CPU使用的影响很小。

# Load Test Conclusions
# 负载测试的结论
Despite the preconceptions we may have had, it is clear that each stack was perfectly capable of implementing a performance sensitive service. Each implementation, with a single container on modest hardware, was able to handle a population size that we do not expect to see at WeWork until 2021, and could likely handle significantly more with some optimization of our database usage patterns.

尽管我们可能有先入之见，但很明显，这三个技术栈都完全能够实现性能敏感的服务。每个实现都运行于现代的硬件上的一个容器，都能够处理直到2021年我们在 WeWork 中才能看到的人口规模，并且通过优化我们的数据库模型可以处理更多的用户规模。

Ruby’s use of native code for the most compute intensive parts of the implementation mean that its interpreted nature is barely noticeable; it is only the quality of the Ruby gRPC implementation that let it down. The Go implementation appears to be the most efficient of the three implementations, and had the most predictable performance characteristics as we increased load on the service.

Ruby实现的版本中计算最密集的部分使用了本地原生代码，这意味着我们几乎不必关注它的解释器的性能影响;影响Ruby实现版本的只是Ruby gRPC实现的质量。Go实现似乎是三种实现中效率最高的，并且在我们增加服务负载时其性能特征最具有可预测性。

All three implementations could likely be optimized further — these load test results were produced with no specific attempt to profile or improve the performance of the implementations. As the implementations stand, Go has a slight edge. The JVM has the best tools for profiling and the most configuration options to squeeze performance out of a running system, but such optimization is brittle; it is better to invest that time in performance optimization at the architectural level.

这三种实现都可以进一步优化——这些负载测试结果并没有对实现的性能进行分析或改进。从实现的角度来看，Go有一点优势。JVM有最好的分析工具和最多的配置选项来从运行的系统中挤出性能，但是这种优化是脆弱的;最好将这些时间投资于架构级别的性能优化。

Overall, we make the banal conclusion that performance has much more to do with the choice of approach than the choice of language. Good performance can be achieved in almost any stack, by skilled engineers who understand its nuances.

总的来说，我们得出了一个比较平庸的结论，即性能更多地与设计方法的选择有关，而不是语言的选择。只要资深的工程师理解各个语言技术栈的细微差别，该系统的实现几乎在任何技术栈中都可以实现良好的性能。

# And the winner was…
# 我们最后的选择
Go, by the team’s majority vote. Kotlin came second, Ruby third. The team felt that Go was the better technology choice for the following reasons:

* A simpler language naturally constrains programmers to simpler code, which will make it easier to review and maintain on a day-to-day basis. We need strong recommendations on tool choice and architecture to ensure this extends to higher-level concerns — simpler code, in aggregate, can be harder to understand if care is not taken in how it is composed.
* The development lifecycle is typically simpler with Go — there is little difference between running a service directly on a dev machine, to running it in a container, to running clustered instances of the service. Containers produced for Go microservices are very compact, as Go binaries have essentially no external requirements aside from POSIX OS interfaces.
* Go provided marginally better performance than the other languages, with minimal fuss. Its built-in asynchronous processing mechanisms and associated libraries appear to make it better suited to the types of microservices we are likely to write in the Core Platform group.

经过团队的投票，我们最后选择了Go,Kotlin第二，Ruby第三。对于选择Go,团队有一下理由：

* 一个更简单的语言自然能够驱动程序员写成更简单的代码，这将使他们更容易在日常基础上进行检查和维护。我们需要关于工具选择和架构的强有力建议，以确保其可以扩展到更高层次的关注点——如果不注意代码的组成架构，那么总的来说，再简单的代码可能也很难理解。
* 通常Go的开发生命周期更简单——直接在开发机器上运行服务、在容器中运行服务、以及运行服务的集群实例之间没有什么区别。为Go微服务生成的容器非常简洁，因为除了POSIX OS接口外，Go二进制文件基本上没有外部依赖。
* Go的性能比其他语言稍好一点，并且没有太多麻烦。其内置的异步处理机制和相关库似乎使其更适合于我们可能在核心平台组中编写的微服务类型。

This choice comes with the strong caveat that we must provide rules or recommendations on:

* Dependency management. We are likely to adopt go modules for this purpose, once it is ready.
* Error propagation and handling — this is a notoriously weak part of the language, for which we must define a workable approach.
* Channel and goroutine usage — beginners can tie themselves in knots with this. However, it is no worse than async/await in EcmaScript, or ReactiveX patterns; this is rapidly becoming a normal part of software engineering practice.

选择Go技术栈带有强烈的警告，我们必须在以下方面强制规则或建议:

* 依赖关系管理。go官方一旦完善了模块化管理工具go modules, 我们很可能采用这个方案做方案管理。
* 错误或异常的传递和处理——这是Go语言中出了名的薄弱部分，我们必须为此定义一个可行的方案。
* channel 和 goroutine 的使用-初学者可以将这两者联合起来使用。实际上，它并不比 EcmaScript 中的async/wait 或 ReactiveX 模式要差;这在成软件工程实践中越来越常见。

# Implementation Details
# 实现细节
The following sections are in-depth discussions of each implementation, with the various pros and cons of each specifically discussed.

下面几节将深入讨论Go、Kotlin、Ruby的实现，并具体讨论每种实现的各种优缺点。

## Evaluating Kotlin
## 评估Kotlin

Kotlin is a statically typed, object-functional language designed by JetBrains, first released in 2011. It is primarily compiled to JVM bytecode, but has experimental support for compiling native binaries (via LLVM), and transpiling to Javascript.

Kotlin是JetBrains设计的一种静态类型的对象函数式语言，于2011年首次发布。它主要编译为JVM字节码，但对编译本地二进制文件(通过LLVM)和转换为Javascript提供了实验性支持。

We regard Kotlin as a more flexible, less verbose alternative to Java, and a simpler alternative to Scala. It has rapidly grown in popularity in the Android ecosystem, where it is now supported by Google as a first-class citizen for Android apps and libraries.

我们认为Kotlin比Java的更灵活、更简洁，比Scala也更简单，Kotlin可以作为Java或者是Scala的替代品。它在Android生态系统中迅速流行起来，现在谷歌将Kotlin作为Android应用程序和库的第一语言选择。

### Implementation notes
### 实现注意事项
Three key decisions were made in the Kotlin implementation, that had a strong influence on the structure of the resultant code and likely on performance:

* Frameworks were avoided in the code, with the exception of the framework-like elements introduced by gRPC-java itself. The service is simple enough that we felt frameworks such as Spring Boot, Lagom or Vert.x would do little but obfuscate the implementation, particularly for those not familiar with Kotlin or the JVM. As a result, the initialization logic and interaction with the database was more explicit than what one may have found with the use of a framework.
* The Arrow functional-programming library was used extensively to facilitate a mostly-functional style. In particular the Either type was used pervasively instead of thrown exceptions for errors. This gave the code a Go-like feel, with explicit error checking on method calls, though Arrow’s monad comprehensions or flatMap chaining were used to make this less disruptive to readability than the equivalent imperative Go code.
* Coroutines were used, in combination with async/await, in an attempt to simplify the concurrent and asynchronous parts of the code.

在Kotlin的实现中有三个非常重要的因素，它们对最终代码的结构和性能有很大的影响:

* 除了gRPC-java本身引入的类似框架的元素外，我们的代码(Token Mint Service)中应该避免引入框架。我们的服务非常简单，我们感觉Spring Boot、Lagom或Vert之类的框架带来的好处很少，相反这些框架很重，反而会混给实现代码带来复杂性，让我们的工程师对代码产生混淆，特别是对于那些不熟悉Kotlin或JVM的工程师。因此，系统的初始化逻辑和与数据库的交互应该比使用框架要更加直白。
* 函数式编程库Arrow被广泛的应用在促进函数式编程风格，特别是，这两种类型都被广泛使用，而不是使用为错误抛出异常的方式。在方法调用上显式地检查错误，这让代码风格看起来很像Go一样，不过Arrow的monad comprehensions 和 flatMap chaining 的使用相比同等的命令式Go代码来说，其对可读性的破坏要小一些。
* 协程与async/ wait结合使用，试图简化代码的并发和异步部分。

### Strong Points
### 优点
Kotlin is a good all-rounder language: linguistically it matches Ruby’s expressiveness, while retaining strong static type safety. Its linguistic features allows for more compact, expressive code than Java, without being overly opinionated on the OOP / FP dichotomy. This linguistic flexibility is particularly well suited to building domain-specific abstractions to help in solving problems. This is also a core strength of Ruby, and arguably a core weakness of Go.

Kotlin是一种优秀的全面性语言:在语言特性上它与Ruby的表达能力相匹配，同时保持了强大的静态类型安全性。它的语言特性使得它比Java更紧凑和更富表现力，而不会对于面向对象还是函数式编程更好保持一方面武断。这种语言灵活性特别适合于构建特定领域的抽象，以帮助解决问题。这也是Ruby的核心优势，也可以说是Go的核心弱点.

Extension methods are a great feature, and helped with the readability of the code. A “fluent” style of programming through method chaining can be easily added to existing types through the use of extension methods, which we put to good use in implementing builders and validators for protocol buffer messages.

扩展方法是一个很好的特性，有助于提高代码的可读性。通过使用扩展方法，fluent的编码风格的函数链可以轻松地添加到现有类型中，我们在实现协议缓冲区消息的构造器和验证器时很好地使用了扩展方法。

Straightforward interop with JVM libraries, tools and frameworks is also a core strength: Java programmers can get started in Kotlin in minutes, and even if they do not adapt their programming style to include functional patterns, they can see meaningful productivity gains. It is also not surprising that Kotlin has an excellent IDE, given its origin at JetBrains.

可以与JVM库、工具和框架的直接相互操作也是一个核心优势:Java程序员可以在几分钟内开始使用Kotlin，即使他们不调整自己的编程风格以适应函数式编程，他们也可以看到有意义的生产力提高。此外Kotlin起源于JetBrains，所以它也拥有一个优秀的IDE。

### Pain Points
### 缺点
While a flexible, pragmatic approach to functional programming in Kotlin is a distinct strength, it can also be viewed as a weakness: it is easy to get carried away with the functional style, and end up with difficult-to-read code. This happened in the implementation where we went too deep with usage of the Arrow library — while equivalent imperative code may be longer, it can be easier to understand and less nuanced.

虽然用Kotlin实现函数式编程非常的灵活、实用，可以作为Kotlin的一种独特的优点，但它也可以被看作是一种缺点:很容易被函数式的代码风格搞得晕头转向，最终导致代码难以阅读。当我们深入的使用Arrow库的时候这种情况就会发生——虽然等效的命令式风格的代码可能更长，但它更容易理解，而且其区别并不大。

As a relatively new language that gives the programmer a wide variety of linguistic tools, there are no well-established best practices for using the language. As a result, this will lead to wildly different coding styles and approaches to problems across projects, teams and individuals. Go and Ruby, by comparison, have more established idioms.

作为一种相对较新的语言，它为程序员提供了各种各样的语言工具，目前使用该语言还没有成熟的最佳实践方法论。因此，这将导致跨项目、团队和个人对问题采用截然不同的编码风格和方法。相比之下，Go和Ruby有更多的固定用法。

Some awkward issues were found in using Kotlin coroutines, which are still an experimental part of the language. In particular, composing coroutines with Arrow’s Either type monad comprehensions is difficult. Arrow’s EitherT monad transformer helps but is somewhat magical to a layman.

比较尴尬的是，Kotlin的协程任然处于实验性阶段，并不完善，所以使用起来有很多顾略。特别是，组合协程和Arrow的任意一种类型的理解都是困难的。Arrow的EitherT monad转换器对理解有帮助，但对一个外行人来说，这个可能比较神奇

Some of the core Java APIs are starting to show their age, and do not fit well with contemporary asynchronous programming. JDBC is a prime example: operations like acquiring a database connection and dispatching queries are blocking operations. Until the asynchronous successor to JDBC is available, JDBC calls must be made via a separate thread pool to avoid blocking coroutine threads.

一些核心Java api已经比较老旧，并且不适合现代的异步编程。JDBC是一个典型的例子:像获取数据库连接和分派查询这样的操作都是阻塞操作。在JDBC的异步后继可用之前，必须通过单独的线程池进行JDBC调用，以避免阻塞协程线程。


## Evaluating Go
## 评估Go
Go is a statically typed, imperative language that was first released by Google in 2009. It was motivated by the need to solve large-scale software engineering problems at Google, and is typically compiled to statically-linked native binaries.

Go是一种静态类型的命令式语言，于2009年由谷歌首次发布。它诞生于谷歌需要解决大规模的软件工程问题，并且通常编译为静态链接的本地二进制文件。

We regard Go as a contemporary alternative to C/C++, that preserves linguistic simplicity, while providing built-in essentials like garbage collection and asynchronous programming primitives. Go is being adopted by many engineering organizations for backend systems, including Uber, Slack, Dropbox, and Twitch.

Go一般被看做是C/C++的替代品，它保持了语言的简单性，同时又提供了内置的基本功能，比如垃圾收集和异步编程原语。Go越来越多的被用于工程组织的后端系统，包括Uber、Slack、Dropbox和Twitch。

### Implementation notes
### 实现注意事项
We used the go grpc framework, leveraging go-grpc-middleware, handling our common infrastructure patterns for handling panics, opentracing, and request attribute validation. This resulted in a clean common server pattern that we can reuse across our microservices.

我们使用Go的grpc框架，利用 go-grpc-middleware 来处理一些公共的基础逻辑，比如处理异常、opentracing和请求参数的校验。这样我们就可以得到一个非常干净的公共服务组件，并且在我们的微服务中可以重用。

For our libraries we adopted the functional options pattern with smart defaults, inspired by Dave Cheney’s blog post and gRPC.

对于我们的库，我们使用了带有智能默认值的函数选项模式，灵感来自 Dave Cheney’s blog post 和 gRPC。

### Strong Points
### 优点
Strong points are covered under why we chose Go, with a few additional reasons:

* Concurrency principles are built in. Channels and goroutines enables concurrent applications to be written with great readability.
* Auto formatting. We don’t have to discuss tabs vs spaces :)
* godoc. Documentation is built in as a standard to the go tooling

我们选择Go的原因包括以下几个优点:

* 内置并发模块。channel和goroutine使得并发程序能被轻易写出，并且具有可读性。
* 自动格式化代码，让我们不必讨论编码风格，比如是使用tab还是空格键。
* godoc文档是go tools的一个标准内置功能。

### Implementation Pain Points
### 缺点
For the implementation the biggest tooling pain point encountered was around the database unit tests using go-sqlmock. Initially the SQL statements were written for the MYSQL flavor vs Postgres and wasn’t caught until the integration tests ran. Another approach may be to use an in-memory db database that speaks the postgres protocol.

对于go语言的实现版本，遇到的最大问题是使用go-sqlmock进行数据库单元测试。最初SQL语句是为MYSQL风格vs Postgres，直到集成测试运行时才捕获。另一种方法可能是使用基于postgres协议的内存db数据库。

Errors in Go are arguably too simple and error checks seem to be tedious and represent a large portion of the code. This results in teams coming up with their own error types or strategies.

Go中的Errors机制比较简单，错误检查也很单调，而且代表了代码的很大一部分。这导致团队需要提出他们自己的错误类型或策略。

Fragmentation of dependency management tools causes confusion on which one to adopt. Go modules was recently shipped in Go 1.11 so this may be fully addressed.
依赖管理工具的混乱导致团队对于选择哪一种管理工具具有困惑。新的依赖管理工具Go modules 最近已经在Go 1.11中发布，所以这个问题可能会得到全面解决。

## Evaluating Ruby
## 评估Ruby
Ruby is a dynamically typed, object oriented, interpreted scripting language. It was first released in 1995 by Yukihiro “Matz” Matsumoto, who remains heavily involved in the design of the language to this day. Ruby’s interpreter is written in a mixture of C and Ruby, with the ability for packages (called “gems”) to include native extensions, such as C, C++, or Rust.

Ruby是一种动态类型的、面向对象的解释脚本语言。1995年，松本幸弘(Yukihiro Matz)首次发布了这款语言。直到今天，松本幸弘仍然积极参与这款语言的设计。Ruby的解释器是用C和Ruby混合编写的，可以基于包(称为“gems”)做本地原生扩展，如C、c++或Rust。

We regard Ruby as one of the more flexible dynamically typed languages and the company has a large amount of experience with it. The majority of WeWork’s applications (as of June 2018) are written in Ruby, primarily using Ruby on Rails.

我们认为Ruby是一种更灵活的动态类型语言，公司在这方面有丰富的经验。WeWork的大多数应用程序(截至2018年6月)都是用Ruby编写的，主要使用Ruby on Rails。

### Implementation notes
### 实现注意事项
No framework was used in the Ruby implementation, but the code was organized in a fashion that would be familiar to Ruby on Rails developers (model, controller, services, etc.). Due to the simplicity of the data models, a simple wrapper around the pg gem was written, rather than using activerecord or other DAO/ORM libraries.

Ruby版本的实现中没有使用框架，但是代码结构的组织类似于Ruby on Rails(模型、控制器、服务等)。由于我们的数据模型的比较简单，我们编写了一个简单的pg gem包装器，而不是使用 activerecord 或其他 DAO/ORM 库。

We used gruf, written by BigCommerce, to manage gRPC requests. It abstracts out the majority of the boilerplate-level concerns with managing GRPC servers while still exposing the underlying configuration if desired.

我们使用 BigCommerce 编写的 gruf 来管理 gRPC 请求。它抽象出管理 GRPC 服务器的大部分中间层的关注点，同时如果需要，仍然公开底层配置。

### Multithreading/Horizontal Scaling
### 多线程/水平扩展
Asynchronicity is handled purely at the server level — each request operates in its own thread from the Controller down to the Database calls. The interpreter has a global lock, and therefore more complex threading is generally not idiomatic in application-level Ruby code. This may cause the alternate implementations to scale horizontally more easily.

服务端的处理是完全异步的——从controller到数据库死亡调用，每个请求都在自己的线程中运行。解释器有一个全局锁，因此更复杂的线程在Ruby应用程序代码中并不常用。相对于Ruby，其他语言的实现更容易水平扩展。

The Docker images are noticeably larger (a comparable deploy image using alpine is still 2.5x the size of the Kotlin or Go containers), but this is not a huge difference in most deployments since only the initial pull to the orchestration will be dealing with the network time.

Docker映像相对来说明显更大(使用alpine的类似部署镜像仍然是Kotlin或Go容器大小的2.5倍)，但在大多数部署中，这并不是很大的差别，因为只有在初始拉取镜像的时候才需要耗用网络处理时间。

Ruby gRPC server (using the official library) does not queue requests (since the merge of this pr), which means that under heavy load it will reject many incoming requests.

Ruby gRPC 服务端(使用官方库)不适用队列处理请求(因为合并了这个pr)，这意味着在高负载下它将拒绝许多的请求。

### Strong Points
### 优点
As part of the test suite, integration tests were written which were easy to package as an acceptance test suite for other implementations of the suite. RSpec is very well supported and easily extensible, while producing readable failures for non-ruby devs as well.

作为测试套件的一部分，编写了集成测试，这些测试很容易打包为套件的其他实现的验收测试套件。RSpec做了很好的支持，并且易于扩展，但是对于非ruby开发人员来说，代码的可读性带来了很大的障碍。

While the database logic in this project was straightforward enough that the author did not feel it necessary to do anything more complicated that the base Ruby postgres gem, more complex database projects could switch to using ActiveRecord and take advantage of the ORM that makes Rails so powerful.

虽然这个项目中的数据库逻辑足够简单，以至于作者觉得没有必要做任何比基本的Ruby postgres gem更复杂的事情，但是更复杂的数据库项目可以切换到使用 ActiveRecord，并利用ORM来实现Rails的强大功能。

While OpenTracing was not added into the project at the time of this writing, adding in NewRelic tracing and monitoring required adding a simple Gruf interceptor. Additional instrumentation was also added to fine-tune and required minimal changes to the code.

虽然在撰写本文时OpenTracing还没有添加到项目中，但是在NewRelic tracking和monitoring中添加一个简单的Gruf拦截器是必需的。在微调中还添加了额外的工具，并且需要对代码进行最小的更改。

### Pain Points
### 缺点
Much of the message contents for this project were around Bytes and Cryptography.

这个项目的大部分消息内容都是围绕字节和加密的。

Dealing with UUIDs as bytes is not difficult to do, but it is not a first class citizen. This required writing a few helper methods, which were simple to write but were an additional overhead in the context of a project like this.

将uuid作为字节处理并不困难，但它不是第一选择。这需要编写一些helper方法，这些方法编写起来很简单，但是在这样的项目上下文中会增加额外的开销。

Cryptography in Ruby is generally done through system libraries (Ruby NaCl or OpenSSL), but this project in particular specified Tink. Since Tink is not implemented in Ruby (only in C++, Java, and Go at the time of this posting), multiple imports and handlers were needed to match the other implementations.

Ruby中的密码学通常通过系统库(Ruby NaCl或OpenSSL)来完成，但是这个项目特别指定了Tink。由于Tink不是用Ruby实现的(在本文发布时仅用c++、Java和Go实现)，因此需要多个导入和处理程序来匹配其他实现。

A major pain point in the syntax of the Ruby generated code has been resolved as of the writing of this analysis: ruby_package can now be used to declare namespaces dynamically, making the Ruby code a bit more idiomatic (release and gRPC pr).

在编写本文时，Ruby生成代码语法中的一个主要痛点已经得到了解决:ruby_package现在可以用来动态地声明名称空间，这使得Ruby代码更加符合习惯(release和gRPC pr)。
