# What Made GoLang So Popular? The Language’s Creators Look Back

- 原文地址：https://thenewstack.io/what-made-golang-so-popular-the-languages-creators-look-back/
- 原文作者：David Cassel
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w18_Golang_creators_look_back.md
- 译者：[张宇](https://github.com/pseudoyu)
- 校对：

![golang](../static/images/2022/w18_Golang_creators_look_back/golang.png)

Since the day it was open sourced in 2009, the [Go programming language](https://go.dev/) has consistently grown in popularity. Now the five Google software engineers behind its original creation [are taking a look back at what fueled that growth](https://cacm.acm.org/magazines/2022/5/260357-the-go-programming-language-and-environment/fulltext#R16).

Writing in Communications of the ACM, Go’s five original creators stress that even their earliest work “benefited greatly from advice and help from many colleagues at Google.” And the paper’s second sentence emphasizes that it’s now a public project “with contributions from thousands of individuals and dozens of companies.”

Backed by a strong community, Go has attained undeniable and widespread popularity. In the most recent [Tiobe Index](https://www.tiobe.com/tiobe-index/), an estimation of the world’s most popular programming languages, Go ranked in as #14.

[Docker](https://thenewstack.io/category/containers/) and [Kubernetes](https://thenewstack.io/category/kubernetes/) are both written in Go, their paper points out, adding that the language is also “the foundation for critical infrastructure at every major cloud provider, and is the implementation for most projects hosted at the [Cloud Native Computing Foundation](https://cncf.io/?utm_content=inline-mention).”

But a more interesting question is why Go became so popular...

The paper argues it was Go’s “development-focused philosophy” that helped its community thrive, and then credits that community — and the technology that it built — for ultimately making Go “a significant component of the modern cloud computing environment.”

In short, when looking back over the last 13 years, Go’s creators believe the language succeeded by training its focus on “the overall environment” where software projects get engineered. “Go’s approach is to treat language features as no more important than environmental ones.”

The authors for this paper were [Russ Cox](https://twitter.com/_rsc?lang=en), [Robert Griesemer](https://github.com/griesemer), [Rob Pike](https://twitter.com/rob_pike?lang=en), [Ian Lance Taylor](https://www.linkedin.com/in/ianlancetaylor/) and [Ken Thompson](https://www.computer.org/profiles/kenneth-thompson).

# The Early Days

It didn’t hurt that Go came from Google, just a little over 10 years after the search engine company had first launched in 1998. And Go’s compact binaries were also easier to deploy — since (unlike Java binaries) they didn’t require a separate runtime environment to execute.

Other language features also helped to make it attractive, since Go was one of the languages that included a “garbage collection” feature to automatically free up memory no longer being used by variables. And for this, the paper points out, Go took advantage of the new multicore processors, running its garbage collection on a dedicated core to lower the impact on latency.

This kind of concurrency was provided as a core part of the language — and not as a separate optional library. In fact, this explains much of why Go was built the way that it was. A section in the paper titled “Origins” describes how Go grew from experiences at Google, with a vast multilanguage codebase shared by roughly 4,000 active developers.

Their day-to-day experience showed the need for a better way to process at-scale loads, tapping the power of new multicore chips. Looking back, the language’s creators write that Go “is our answer to the question of what a language designed to meet these challenges might look like.” Go was specifically designed to offer top-notch support for concurrency and parallelism — meaning Go could not only process multiple tasks effectively, but also be executing multiple tasks at the same time.

In the world before Go, engineers had been stuck using awkward syntax and “large, fixed-size thread stacks,” the paper argues, and concurrency-enabling threads were unpopular because they were hard to create, hard to use, and hard to manage. A footnote even references a [1995 paper](https://web.stanford.edu/~ouster/cgi-bin/papers/threads.pdf) from the creator of the TCl scripting language, John Ousterhout titled “Why threads are a bad idea (for most purposes).”

“Resolving this tension was one of the prime motivations for creating Go,” they write, later calling it the language’s “principal unusual property...”

# Beyond Language Design

The paper also acknowledges that Go’s popularity today is in part because the broader tech industry now routinely uses cloud service providers — and the at-scale production environments they enable (which Go was designed to address). There’s some other distinct advantages.

Later the paper points out that Go “removes undefined behaviors that cause so many problems in C and C++ programs.” (For example, Go simply throws a runtime exception and stops running a program if the code tries something risky like dereferencing a null pointer or using an index beyond the bounds of an array or slice.)

But Go’s creators attribute Go’s popularity to something else. They stress that “more significant was the early work that established fundamentals for packaging, dependencies, build test, deployment, and other workaday tasks of the software development world, aspects that are not usually foremost in language design.” This attracted developers who “seeded” their ecosystem with useful packages. And while the original release only supported Linux and MacOS X, this enthusiastic community had soon created Windows versions for Go’s compiler and libraries, along with porting them to other operating systems.

Then the paper argues that a focus on developers permeates the language’s development. For example, early on it notes Go’s high-quality cryptography libraries (including support for the secure-communications protocols SSL and TLS). And Go’s standard library also includes a built-in HTTPS client and server for interacting with other systems online.

But what’s more significant is the way Go handles its libraries. Go’s compiler was designed to carefully import only the necessary libraries for inclusion in its binaries, which avoided a behavior seen in other languages where entire libraries were imported, just to ensure the one necessary functionality had been included.

And keeping developers in mind, Go allows easy importing of external libraries from other domains (along with a way to automatically check for compatible versions). “As befits a language for distributed computing, in Go there is no central server where Go packages must be published,” the paper points out. (Although there is now a public mirror of available Go packages plus a cryptographically-signed log with their expected contents.)

Go also boasts support in the standard distribution for optimization techniques like program profiling, as well as support for testing features like fuzzing. The paper notes that Go even has a convention for the layout of code. (And Go’s `gofmt` tool parses source code into this standardized layout.) This and other built-in tools helped make it easier to build everything from IDE plugins and debuggers, to frameworks and build automators. Go’s creators argue their language was specifically designed to encourage the creation of tools and automation, and “As a result, the Go world has a rich, ever-expanding, and interoperating toolkit.”

So the language was only part of its appeal, their paper argues. “The full story must involve the entire Go environment: the libraries, tools, conventions, and overall approach to software engineering.”

# Staying Consistent

Another section of their paper also touts the language’s consistency. Go’s creators acknowledge that in its earliest years “we tinkered with and adjusted it in each weekly release. Users often had to change their programs when updating to a new Go version.”

But ever since 2012 (with the official release of Go version 1), “we publicly committed to making only backward-compatible changes to the language and standard library, so that programs would continue running unchanged when compiled with newer Go versions.”

The result? Since then the language “has been all but frozen,” the paper explains — but with a dramatic growth in tools. Specifically, it was “better compilers, more powerful build and testing tools, and improved dependency management, not to mention a huge collection of open source tools that support Go.” The paper argues this helped encourage the creation of educational materials — and attracted users and “a thriving ecosystem of third-party packages.”

> “Although the design of most languages concentrates on innovations in syntax, semantics, or typing, Go is focused on the software development process itself.”

> The Go Programming Language and Environment | May 2022 | Communications of the ACM

> [The Go Programming Language and Environment](https://cacm.acm.org/magazines/2022/5/260357-the-go-programming-language-and-environment/fulltext)

At one point the paper even argues that Go’s carefully-balanced feature set avoided overextending the language’s developers. But the paper closes by looking at the exception to this rule, when Go did in fact add a major new feature. Barely two months ago, Go added [parametric polymorphism](https://github.com/golang/proposal/blob/4a54a00950b56dd0096482d0edae46969d7432a6/design/go2draft-contracts.md), which was “tailored to fit well with the rest of Go...”

“Making such a large language change while staying true to the principles of consistency, completeness, and community will be a severe test of this approach.”

Go’s creators recognize that it takes a community to sustain a programming language. And maybe it also takes a community to build one. The paper ends with a grateful acknowledgment to their colleagues at Google for advice and support in Go’s earliest days — a group that foreshadows the flood of community support to come. “Since the public release, Go has grown and improved thanks to an expanded Go team at Google along with a tremendous set of open source contributors. Go is now the work of a literal cast of thousands, far too many to enumerate here.

“We are grateful to everyone who has helped make Go what it is today.”