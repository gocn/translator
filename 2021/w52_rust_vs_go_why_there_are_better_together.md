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

In this article, we will discuss the pros and cons of Rust and Go and how they supplement and support each other, and our recommendations for when each language is most appropriate.

Companies are finding value in adopting both languages and in their complimentary value. To shift from our opinions to hands-on user experience, we spoke with three such companies, [Dropbox](https://www.dropbox.com/), [Fastly](https://www.fastly.com/), and [Cloudflare](https://www.cloudflare.com/), about their experience in using Go and Rust together. There will be quotes from them throughout this article to give further perspective.

## Language Comparison

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

## Similarities



Go and Rust have a lot in common. Both are modern software languages born out of a need to provide a safe and scalable solution to the problems impacting software development. Both were created as reactions to shortcomings the creators were experiencing with existing languages in the industry, particularly shortcomings of developer productivity, scalability, safety and concurrency.

Most of today’s popular languages were designed over 30 years ago. When those languages were designed there were five key differences from today:

1.  Moore’s law was thought to be eternally true.
2.  Most software projects were written by small teams, often working in person together.
3.  Most software had a relatively small number of dependencies, mostly proprietary.
4.  Safety was a secondary concern… or not a concern at all.
5.  Software was typically written for a single platform.

In contrast, both Rust and Go were written for today’s world and generally took similar approaches to design a language for today’s development needs.

### 1\. Performance and Concurrency

Go and Rust are both compiled languages focused on producing efficient code. They also provide easy access to the multiple processors of today’s machines, making them ideal languages for writing efficient parallel code.

_“Using Go allowed MercadoLibre to cut the number of servers they use for this service to one-eighth the original number (from 32 servers down to four), plus each server can operate with less power (originally four CPU cores, now down to two CPU cores). With Go, the company obviated 88 percent of their servers and cut CPU on the remaining ones in half—producing a tremendous cost-savings.”_— “[MercadoLibre Grows with Go](https://go.dev/solutions/mercadolibre/)”

_“In our tightly managed environments where we run Go code, we have seen a CPU reduction of approximately ten percent \[vs C++\] with cleaner and maintainable code.”_ — [Bala Natarajan, Paypal](https://go.dev/solutions/paypal/)

_“Here at AWS, we love Rust, too, because it helps AWS write highly performant, safe infrastructure-level networking and other systems software. Amazon’s first notable product built with Rust, Firecracker, launched publicly in 2018 and provides the open source virtualization technology that powers AWS Lambda and other serverless offerings. But we also use Rust to deliver services such as Amazon Simple Storage Service (Amazon S3), Amazon Elastic Compute Cloud (Amazon EC2), Amazon CloudFront, Amazon Route 53, and more. Recently we launched Bottlerocket, a Linux-based container operating system written in Rust.” — [Matt Asay, Amazon Web Services](https://aws.amazon.com/blogs/opensource/why-aws-loves-rust-and-how-wed-like-to-help/)_

_We “saw an extraordinary 1200-1500% increase in our speed! We went from 300-450ms in release mode with Scala with fewer parsing rules implemented, to 25-30ms in Rust with more parsing rules implemented!” — [Josh Hannaford, IBM](https://developer.ibm.com/technologies/web-development/articles/why-webassembly-and-rust-together-improve-nodejs-performance/)_

### 2\. Team Scalable — Reviewable

Software development today is built by teams that grow and expand, often collaborating in a distributed way using source control. Go and Rust are both designed for how teams work, improving code reviews by removing unnecessary concerns like formatting, security, and complex organization. Both languages require relatively little context to understand what the code is doing, allowing reviewers to more quickly work with code written by other people and review code by both team members and code contributed by open source developers outside of your team.

_“Building Go and Rust code, having come from a Java and Ruby background in my early career, felt like an impossible weight off my shoulders. When I was at Google, it was a relief to come across a service that was written in Go, because I knew it would be easy to build and run. This has also been true of Rust, though I’ve only worked on that at a much smaller scale. I’m hoping that the days of infinitely configurable build systems are dead, and languages all ship with their own purpose-built build tools that just work out of the box.”— [Sam Rose, CV Partner](https://bitfieldconsulting.com/golang/rust-vs-go)_

_“I tend to breathe a sigh of relief when writing a service in Go since it has a very simple, easy to reason about, static type system compared to dynamic languages, concurrency is a first-class citizen, and Go’s standard library is both unbelievably polished and powerful, yet also to the point. Take a standard Go install, throw in a grpc library and a database connector, and you need very little else to build anything on the server-side, and every engineer will be able to read the code and understand the libraries. When writing a module in Rust, Dropbox engineers felt Rust’s growing pains on the server-side before Async-await stabilized in 2019, but since then, crates are converging to use it and we get the benefit of async patterns coupled with fearless concurrency.” — Daniel Reiter Horn, Dropbox_

### 3\. Open Source-aware

The number of dependencies used by the average software project today is staggering. The decades-long goal of software reuse has been achieved in modern development, where today’s software is built using 100s of projects. To do so, developers use software repositories, which increasingly has become a staple of software development across a broadening range of applications. Each of the packages a developer includes, in turn, has its own dependencies. Languages for today’s programming environments need to handle this complexity effortlessly.

Both Go and Rust have package-management systems that allow developers to make a simple list of the packages they’d like to build on, and the language tools automatically fetch and maintain those packages for them, so that developers can focus more on their own code and less on the management of others.

### 4\. Safety

The security concerns of today’s applications are well-addressed by both Go and Rust, which ensure that code built in the languages run without exposing the user to a variety of classic security vulnerabilities like buffer overflows, use-after-free, etc. By removing these concerns, developers can focus on the problems at hand and build applications that are more secure by default.

_“The \[Rust\] compiler really holds your hand when working through the errors that you do get. This lets you focus on your business objectives rather than bug hunting or deciphering cryptic messages.” — [Josh Hannaford, IBM](https://developer.ibm.com/technologies/web-development/articles/why-webassembly-and-rust-together-improve-nodejs-performance/)_

_“In short, the flexibility, safety, and security of Rust outweighs any inconvenience of having to follow strict lifetime, borrowing, and other compiler rules or even the lack of a garbage collector. These features are a much-needed addition to cloud software projects and will help avoid many bugs commonly found in them.” — [Taylor Thomas, Sr., Microsoft](https://msrc-blog.microsoft.com/2020/04/29/the-safety-boat-kubernetes-and-rust/)._

_“Go is strongly and statically typed with no implicit conversions, but the syntactic overhead is still surprisingly small. This is achieved by simple type inference in assignments together with untyped numeric constants. This gives Go stronger type safety than Java (which has implicit conversions), but the code reads more like Python (which has untyped variables).” — [Stefan Nilsson, computer science professor](https://yourbasic.org/golang/advantages-over-java-python/)._

_“When building our Brotli compression library for storing block data at Dropbox, we limited ourselves to the safe subset of Rust and, further, to the core library (no-stdlib) as well, with the allocator specified as a generic. Using the subset of Rust this way made it very easy to call the Rust-Brotli library from Rust on the client-side and using the C FFI from both Python and Go on the Server. This compilation mode also provided [substantial security guarantees](https://dropbox.tech/infrastructure/lossless-compression-with-brotli). After some tuning, the Rust Brotli implementation, despite being 100% safe, array-bounds-checked code, was still faster than the corresponding native Brotli code in C.” — Daniel Reiter Horn, Dropbox_

### 5\. Truly Portable

It is trivial in both Go and Rust to write one piece of software that runs on many different operating systems and architectures. “Write once, compile anywhere.” In addition, both Go and Rust natively support cross-compilation eliminating the need for “build farms” commonly associated with older compiled languages.

_“Golang possesses great qualities for production optimization such as having a small memory footprint, which supports its capability for being building blocks in large-scale projects, as well as easy cross-compilation to other architectures out of the box. Since Go code is compiled into a single static binary, it allows easy containerization and, by extension, makes it almost trivial to deploy Go into any highly available environment such as Kubernetes.” — [Dewet Diener, Curve](https://jaxenter.com/golang-curve-163187.html)._

_“When you look at a cloud-based infrastructure, often you’re using something like a Docker container to deploy your workloads. With a static binary that you build in Go, you could have a Docker file that’s 10, 11, 12 megabytes instead of bringing in the entire Node.js ecosystem, or Python, or Java, where you’ve got these hundreds of megabyte-sized Docker files. So, shipping that tiny binary is amazing.” — [Brian Ketelsen, Microsoft](https://cloudblogs.microsoft.com/opensource/2018/02/21/go-lang-brian-ketelsen-explains-fast-growth/)._

_“With Rust, we’ll have a high-performance and portable platform that we can easily run on Mac, iOS, Linux, Android, and Windows.” — [Matt Ronge, Astropad](https://blog.astropad.com/why-rust/)._

## Differences

In design, there are always trade-offs that must be made. While Go and Rust emerged around the same time with similar goals, as they faced decisions at times they chose different trade-offs that separated the languages in key ways.

### 1\. Performance

Go has excellent performance right out of the box. By design, there are no knobs or levers that you can use to squeeze more performance out of Go. Rust is designed to enable you to squeeze every last drop of performance out of the code; in this regard, you really can’t find a faster language than Rust today. However, Rust’s increased performance comes at the cost of additional complexity.

_“Remarkably, we had only put very basic thought into optimization as the Rust version was written. Even with just basic optimization, Rust was able to outperform the hyper-hand-tuned Go version. This is a huge testament to how easy it is to write efficient programs with Rust compared to the deep dive we had to do with Go.” — [Jesse Howarth, Discord](https://blog.discord.com/why-discord-is-switching-from-go-to-rust-a190bbca2b1f)._

_“Dropbox engineers often see 5x performance and latency improvements by porting line-for-line Python code into Go, and memory usage often drops dramatically as compared with Python as there is no GIL and the process count may be reduced. However, when we are memory constrained, as on desktop client software or in certain server processes, we move over to Rust as the manual memory management in Rust is substantially more efficient than the Go GC.” — Daniel Reiter Horn, Dropbox_

### 2\. Adaptability/Interability

Go’s strength of quick iteration allows developers to try ideas quickly and hone in on working code that solves the task at hand. Often, this is sufficient and frees the developer to move onto other tasks. Rust, on the other hand, has longer compiles compared with Go, leading to slower iteration times. This leads Go to work better in scenarios where faster turnaround time allows developers to adapt to changing requirements, while Rust thrives in scenarios where more time can be given to making a more refined and performant implementation.

_“The genius of the Go type system is that callers can define the Interfaces, allowing libraries to return expansive structs but require narrow interfaces. The genius of the Rust type system is the combination of match syntax with Result<>, where you can be statically certain every eventuality is handled and never have to invent null values to satisfy unused return parameters.” — Daniel Reiter Horn, Dropbox_

_“(I)f your use case is closer to customers, it’s more vulnerable to shifting requirements, then Go is a lot nicer because the cost of continuous refactor is a lot cheaper. It’s how fast you can express the new requirements and try them out.” — Peter Bourgon, Fastly_

### 3\. Learnability

Simply put, there really isn’t a more approachable language than Go. There are many stories of teams who were able to adopt Go and put Go services/applications into production in a few weeks. Additionally, Go is relatively unique among languages in that its language design and practices are quite consistent over it’s 10+ year lifetime. So time invested in learning Go maintains its value for a long time. By comparison, Rust is considered a difficult language to learn due to its complexity. It generally takes several months of learning Rust to feel comfortable with it, but with this extra complexity comes precise control and increased performance.

_“At the time, no single team member knew Go, but within a month, everyone was writing in Go” – [Jaime Garcia, Capital One](https://medium.com/capital-one-tech/a-serverless-and-go-journey-credit-offers-api-74ef1f9fde7f)_

_“What makes Go different from other programming languages is cognitive load. You can do more with less code, which makes it easier to reason about and understand the code that you do end up writing. The majority of Go code ends up looking quite similar, so, even if you’re working with a completely new codebase, you can get up and running pretty quickly.” — Glen Balliet Engineering Director of loyalty platforms at American Express [American Express Uses Go for Payments & Rewards](https://go.dev/solutions/americanexpress/)_

_“However, unlike other programming languages, Go was created for maximum user efficiency. Therefore developers and engineers with Java or PHP backgrounds can be upskilled and trained in using Go within a few weeks — and in our experience, many of them end up preferring it.” — [Dewet Diener, Curve](https://jaxenter.com/golang-curve-163187.html)_

### 4\. Precise Control

Perhaps one of Rust’s greatest strengths is the amount of control the developer has over how memory is managed, how to use the available resources of the machine, how code is optimized, and how problem solutions are crafted. This is not without a large complexity cost when compared to Go, which is designed less for this type of precise crafting and more for faster exploration times and quicker turnaround times.

_“As our experience with Rust grew, it showed advantages on two other axes: as a language with strong memory safety it was a good choice for processing at the edge and as a language that had tremendous enthusiasm it became one that became popular for de novo components.”  — John Graham-Cumming, Cloudflare_

## Summary/Key Takeaways

Go’s simplicity, performance, and developer productivity make Go an ideal language for creating user-facing applications and services. The fast iteration allows teams to quickly pivot to meet the changing needs of users, giving teams a way to focus their energies on flexibility.

Rust’s finer control allows for more precision, making Rust an ideal language for low-level operations that are less likely to change and that would benefit from the marginally improved performance over Go, especially if deployed at very large scales.

Rust’s strengths are at the most advantageous closest to the metal. Go’s strengths are at their most advantageous closer to the user. This isn’t to say that either can’t work in the other’s space, but it would have increased friction to doing so. As your requirements shift from flexibility to efficiency it makes a stronger case to rewrite libraries in Rust.

While the designs of Go and Rust differ significantly, their designs play to a compatible set of strengths, and — when used together — allow both great flexibility and performance.

## Recommendations

For most companies and users, Go is the right default option. Its performance is strong, Go is easy to adopt, and Go’s highly modular nature makes it particularly good for situations where requirements are changing or evolving.

As your product matures, and requirements stabilize, there may be opportunities to have large wins from marginal increases in performance. In these cases, using Rust to maximize performance may well be worth the initial investment.

The New Stack is a wholly owned subsidiary of Insight Partners, an investor in the following companies mentioned in this article: Docker.

Feature image [via](https://pixabay.com/photos/vehicle-wheel-chain-drive-metal-2275456/) Pixabay.