# Go is on a Trajectory to Become the Next Enterprise Programming Language

 [![Go to the profile of Kevin Goslar](https://cdn-images-1.medium.com/fit/c/100/100/0-XdfObs4UVykr8LBr.jpg)](https://hackernoon.com/@kevingoslar?source=post_header_lockup)

 [Kevin Goslar](https://hackernoon.com/@kevingoslar)Follow

 Apr 10


![](https://cdn-images-1.medium.com/max/1600/1-oNcoMWxpNsVqcJE60WDZug.png)

### summary

Go — a programming language designed for large-scale software development — provides a robust development experience and avoids many issues that existing programming languages have. These factors make it one of the most likely candidates to succeed Java as the dominating enterprise software platform in the future. Companies and open-source initiatives looking for a safe and forward-looking technology choice for creating large-scale cloud infrastructures in the coming decades are well advised to consider Go as their primary programming language. The strengths of Go are that it:

- is based on real-world experience
- focuses on large-scale engineering
- focuses on maintainability
- keeps it simple and straightforward
- makes things explicit and obvious
- is easy to learn
- provides one way to do things
- allows easy, built-in concurrency
- provides compute-oriented language primitives
- uses OO — the good parts
- has a modern standard library
- enforces standardized formatting
- has an extremely fast compiler
- makes cross compilation easy
- executes very fast
- requires a small memory footprint
- results in a small deployment size
- deploys completely self-contained
- vendors dependencies
- provides a compatibility guarantee
- encourages good documentation
- is built as commercially backed open source

Read on for more details about each point. Before committing to Go, however, you should look out for:

- immature libraries
- upcoming changes
- no hard real-time

### introduction

Go, a programming language developed at Google, has seen a lot of success in the last couple of years. A large portion of modern cloud, networking, and DevOps software is written in Go, for example [Docker](https://www.docker.com/), [Kubernetes](https://kubernetes.io/), [Terraform](https://www.terraform.io/), [etcd](https://github.com/etcd-io/etcd), or [ist.io](https://github.com/istio/istio).[Many companies are using it](https://github.com/golang/go/wiki/GoUsers#united-states) for general-purpose development as well. The capabilities that Go enables have allowed these projects to attract a large number of users, while Go’s ease of use has enabled many contributions.

Go’s strengths come from combining simple and proven ideas while avoiding many of the problems found in other languages. This blog post outlines some of the design principles and engineering wisdom behind Go to show how — taken together — they qualify it as an excellent candidate to become the next large-scale software development platform. Many languages are stronger in individual areas, but no other language scores so consistently well when looking at all of them combined, especially in regards to large-scale software engineering.

### Based on real-world Experience

Go was created by experienced software industry veterans who have felt the pain from shortcomings of the existing languages for a long time. Rob Pike and Ken Thompson played a major role in the invention of Unix, C, and parts of Unicode many decades ago. Robert Griesemer has decades of experience around compilers and garbage collection after working on the V8 and HotSpot virtual machines for JavaScript and Java. Motivated by one too many times [they had to wait for their Google-sized C++/Java code bases to compile](http://radar.oreilly.com/2012/09/golang.html), they set out to create one more programming language that contains everything they learned through half a century of writing code.

### Focus on large-scale Engineering

Small engineering projects can be built successfully in pretty much any programming language. The really painful problems happen when thousands of developers collaborate under constant time pressure over decades on massive code bases containing tens of millions of lines of code. This leads to problems like:

- long compile times interrupt development
- the code base has been owned by several people/teams/departments/companies, mixing different programming styles
- the company employs thousands of engineers, architects, testers, Ops specialists, auditors, interns, etc who need to understand the code base but have a wide range of coding experience
- dependency on lots of external libraries or runtimes, some of them no longer existing in their original form
- each line of code has been [rewritten an average of 10 times](https://www.ybrikman.com/writing/2018/08/12/the-10-to-1-rule-of-writing-and-programming) over the course of the lifetime of the code base, leaving scars, warts, and technical drift
- incomplete documentation

Go focuses on [alleviating these large-scale engineering pains](https://talks.golang.org/2012/splash.article), sometimes at the cost of making engineering in the small a bit more cumbersome, for example by requiring a few extra lines of code here and there.

### Focus on Maintainability

Go emphasizes offloading as much work as possible to automated code maintenance tools. The Go toolchain provides the most frequently needed functionality like formatting code and imports, finding definitions and usages of symbols, simple refactorings, and identification of code smells. Thanks to standardized code formatting and a single idiomatic way of doing things, machine-generated code changes look very close to human-generated changes in Go and use similar patterns, allowing more seamless collaboration of humans and machines.

### Keep it Simple and Straightforward

> _Junior programmers create simple solutions to simple problems. Senior programmers create complex solutions to complex problems. Great programmers find simple solutions to complex problems. — _[_Charles Connell_](http://www.chc-3.com/pub/beautifulsoftware_v10.htm)

Many people are surprised that Go doesn’t contain concepts they love in other languages. Go is indeed a very small and simple language that contains only a minimal selection of orthogonal and proven concepts. This encourages developers to write the simplest possible code with the least amount of cognitive overhead so that many other people can understand and work with it.

### Make things Explicit and Obvious

> _Good code is obvious, avoids cleverness, obscure language features, twisted control flow, and indirections._

Many languages focus on making it efficient to write code. However, over the course of its lifetime, people will have spent far (100x) more time reading code than was needed to write it in the first place. Examples are to review, understand, debug, change, refactor, or reuse it. When looking at code, one typically only sees and understands small parts of it, often without a complete overview of the entire code base. To account for this, Go makes everything explicit.

An example is error handling. It would be easier to just let exceptions interrupt code at various points and bubble up the call chain. Go requires to [handle or return each error manually](https://tour.golang.org/methods/19). This makes it explicit exactly where code can be interrupted and how errors are handled or wrapped. Overall, this makes error handling more cumbersome to write but easier to understand.

### Easy to Learn

Go is so small and simple that the entire language and its underlying concepts can be studied in just a couple of days. In our experience, after no more than a week of training (compared to months in other languages) Go beginners can make sense of code written by Go experts and contribute to it. To make it easy to ramp up large numbers of people, the Go website provides all the tutorials and in-depth articles needed. These tutorials run in the browser, allowing people to learn and play with Go before even installing it on their local machine.

### One Way to do Things

> _Go empowers teamwork over individual self-expression._

In Go (and Python) all language features are orthogonal and complementary to each other and there is usually one way to do something. If you ask 10 Python or Go programmers to solve a problem, you’ll get 10 relatively similar solutions. The different programmers feel more at home in each other’s code bases. There are fewer [WTFs per minute](https://www.osnews.com/story/19266/wtfsm) when looking at other people’s code, and people’s work fits better into each other, adding up to a consistent whole that everybody is proud of and enjoys working on. This avoids large-scale engineering problems like:

- Developers dismiss good working code as “messy” and demand to rewrite it before they can work on it because they don’t think in the same way as the original author.
- Different team members write parts of the same code base in different subsets of the language.



![](https://cdn-images-1.medium.com/max/1600/1-5RhyUqWmrXugwrjchoA5rA.jpeg)

source: [https://www.osnews.com/story/19266/wtfsm](https://www.osnews.com/story/19266/wtfsm/)

### easy, built-in concurrency

> _Go is designed for modern multi-core hardware._

Most programming languages in use today (Java, JavaScript, Python, Ruby, C, C++) have been designed in the 1980s-2000s when most CPUs had only one compute core. That’s why they are single-threaded in nature and treat parallelization as an afterthought for edge cases, implemented via add-ons like threads and sync points that are cumbersome and difficult to use correctly. Third-party libraries offer easier forms of concurrency like the Actor model but there are always multiple options available, causing fragmentation of the language ecosystem. Today’s hardware has increasing numbers of compute cores and software must be parallelized to run efficiently on it. Go was written in the age of multi-core CPUs and has easy, high-level [CSP](https://en.wikipedia.org/wiki/Communicating_sequential_processes)-style concurrency built into the language.

### Compute-oriented Language Primitives

On a fundamental level, computer systems receive data, massage it (often over several steps), and output the resulting data. As an example, a web server receives an HTTP request from a client and transforms it into a series of database or backend calls. Once these calls return, it transforms the received data into HTML or JSON and outputs it to the caller. Go’s built-in language primitives support this paradigm directly:

- structs represent data
- readers and writers represent streaming IO
- functions process data
- goroutines provide (almost unlimited) concurrency
- channels pipe data between concurrent processing steps

Because all compute primitives are provided in a direct form by the language, Go source code expresses what a server does more directly.

### OO — the good parts


![](https://cdn-images-1.medium.com/max/1600/1-HzxrebFDiPqElPZIokHdoA.gif)

side effects of changing something in a base class

Object-orientation is incredibly useful. The last decades of using it have been productive and given us insights about which parts of it scale better than others. Go takes a fresh approach at object-orientation with those learnings in mind. It keeps the good parts like encapsulation and message passing. Go avoids inheritance because it is now [considered harmful](https://www.javaworld.com/article/2073649/why-extends-is-evil.html) and provides [first-class support for composition](https://golang.org/doc/effective_go.html#embedding) instead.

### Modern Standard Library

Many of the currently used programming languages (Java, JavaScript, Python, Ruby) were designed before the internet was the ubiquitous computing platform it is today. Hence, the standard libraries of these languages provide only relatively generic support for networking that isn’t optimized for the modern internet. Go was created a decade ago when the internet was already in full swing. Go’s standard library allows creating even sophisticated network services without third-party libraries. This prevents the usual problems with third-party libraries:

- **fragmentation:** there are always multiple choices implementing the same functionality
- **bloat:** libraries often implement more than what they are used for
- **dependency hell:** libraries often depend on other libraries at specific versions
- **unknown quality:** third-party code can have questionable quality and security
- **unknown support:** development of third-party libraries can stop at any time
- **unexpected changes:** third-party libraries are often not as rigorously versioned as standard libraries

[More background](https://research.swtch.com/deps) on this by Russ Cox.

### Standardized Formatting

> _Gofmt’s style is nobody’s favorite, but gofmt is everybody’s favorite. — Rob Pike_

Gofmt is a program that formats Go code in a standardized way. It is not the prettiest way of formatting, but the simplest and least disagreeable one. Standardized source code formatting has a surprising amount of positive effects:

1.  **focus conversations on important topics:** it eliminates a whole array of [bike-shed](https://en.wikipedia.org/wiki/Law_of_triviality) debates around tabs vs spaces, indentation depth, line length, empty lines, placement of curly braces, and others.
2.  **developers feel at home in each others code bases** because other code looks a lot like code they would have written. Everybody loves having the liberty to format code the way they prefer, but everybody hates it if others take the liberty to format code the way they prefer.
3.  **automated code changes** don’t mess up the formatting of hand-written code, for example by introducing accidental whitespace changes.

Many other language communities are developing gofmt equivalents now. When built as third-party solutions, there are often several competing formatting standards. The JavaScript world, for example, offers [Prettier](https://prettier.io/) and [StandardJS](https://standardjs.com/). One can use either or both together. Many JS projects adopt none of them because it is an extra decision to make. Go’s formatter is built into the standard toolchain of the language, so there is only one standard and everybody is using it.

### Fast Compilation


![](https://cdn-images-1.medium.com/max/1600/0-XEJeEXJHvRouzOZy)

source: [https://xkcd.com/303](https://xkcd.com/303/)

Long compilation times for large code bases was the drop in the bucket that sparked Go’s genesis. Google uses mostly C++ and Java, which compile relatively quickly compared to more sophisticated languages like Haskell, Scala, or Rust. Still, when compiling large code bases even small amounts of slowness compound to infuriating and flow-disrupting compilation delays. Go is designed from the ground up to make compilation efficient and as a result its compiler is so fast that there are almost no compilation delays. This gives a Go developer instant feedback similar to scripting languages, with the added benefits of static type checking.

### Cross-compilation

Because the language runtime is so simple, it has been ported to many platforms like macOS, Linux, Windows, BSD, ARM, and more. Go can compile binaries for all these platforms out of the box. This makes deployment from a single machine easy.

### Fast Execution

Go runs close to the speed of C. Unlike JITed languages (Java, JavaScript, Python, etc), Go binaries require no startup or warmup time because they ship as compiled and fully optimized native code. The Go garbage collector introduces only negligible pauses in the order of [microseconds](https://twitter.com/brianhatfield/status/804355831080751104). On top of its fast single-core performance, Go makes utilizing all CPU cores [easy](https://tour.golang.org/concurrency/1).

### Small Memory Footprint

Runtimes like the JVM, Python, or Node don’t just load your program code when running it. They also load large and highly complex pieces of infrastructure to compile and optimize your program each time you run it. This makes their startup time slower and causes them to use large amounts (hundreds of MB) of RAM. Go processes have less overhead because they are already fully compiled and optimized and just needs to run. Go also [stores data in very memory-efficient ways](https://dave.cheney.net/2014/06/07/five-things-that-make-go-fast). This is important in cloud environments where memory is limited and expensive, as well as during development where we want to boot up an entire stack on a single machine quickly while leaving memory for other software.

### Small Deployment Size

Go binaries are very concise in size. A Docker image for a Go application is often over [10x smaller](https://derickbailey.com/2017/03/09/selecting-a-node-js-image-for-docker) than the equivalent written in Java or Node because it doesn't need to contain compilers, JITs, and less runtime infrastructure. This matters when deploying large applications. Imagine deploying a simple application onto 100 production servers. When using Node/JVM, our docker registry has to serve 100 docker images @ 200 MB = 20 GB in total. This will take some time to serve. Imagine we want to deploy 100 times a day. When using Go services, the Docker registry only has to serve 100 docker images @ 20 MB = 2 GB. Large Go applications can be deployed faster and more frequently, allowing important updates to reach production faster.

### Self-contained Deployment

Go applications are deployed as a single executable file that includes all dependencies. No JVM, Node, or Python runtime at a specific version needs to be installed. No libraries have to be downloaded onto production servers. No changes to the machine running the Go binary have to be made at all. It isn’t even necessary to wrap Go binaries into Docker to share them. You just drop a Go binary onto a server and it will run there no matter what else is running on that server. The only exception to the above statement is dynamic linking against `glibc` when using the `net` and `os/user` packages.

### Vendoring Dependencies

Go intentionally avoids a central repository for third-party libraries. Go applications link directly to the respective Git repositories and download (“vendor”) all dependent code into their own code base. This has many advantages:

- We can review, analyze, and test third-party code before using it. This code is as much a part of our application as our own code and should conform to the same quality, security, and reliability standards.
- No need for permanent access to the various locations that store dependencies. Get your third-party libraries from anywhere (including private Git repos) once and you have them forever.
- No further downloads of dependencies are necessary to compile the code base after checkout.
- No surprises if a code repository somewhere on the internet suddenly serves different code.
- Deployments never break, even if package repositories slow down or hosted packages cease to exist

### Compatibility Guarantee

The Go team [promises](https://golang.org/doc/go1compat) that existing programs will continue to work on newer generations of the language. This makes it easy to upgrade even large projects to newer versions of the compiler and benefit from the many performance and security improvements they bring. At the same time, thanks to the fact that Go binaries include all the dependencies they need, it is possible to run binaries compiled with different versions of the Go compiler side by side on the same server machine, without the need for a complex setup of multiple versions of runtimes or virtualization.

### Documentation

When engineering in the large, documentation becomes important to make software accessible and maintainable. Similar to the other features, documentation is simple and pragmatic in Go:

- It is embedded in the source code so that both can be maintained at the same time.
- It requires no special syntax — documentation is just normal source code comments.
- Runnable unit tests are often the best form of documentation, so Go let’s you [embed them into the documentation](https://blog.golang.org/examples).
- All the documentation [utilities](https://blog.golang.org/godoc-documenting-go-code) are built into the toolchain and therefore everybody uses them.
- The Go linter requires documentation for exported elements to prevent the build-up of “documentation debt”.

### Commercially Backed Open Source

Some of the most popular and thoroughly engineered software happens when commercial entities develop in the open. This setup combines the strengths of commercial software development — consistency and polish to make a system robust, reliable, and performant — with the strengths of open development like widespread support across many industries, support from multiple large entities and many users, and long-term support even if commercial backing stops. Go is developed this way.

### Disadvantages

Of course, Go is not perfect and there are always pros and cons with every technical choice. Here is a small selection of areas to consider before committing to Go.

### Immaturity

While Go’s standard library is industry-leading in supporting many new concepts like [HTTP 2 server push](https://blog.golang.org/h2push), third-party Go libraries for external APIs can be less mature compared to what exists for example in the JVM ecosystem.

### Upcoming Changes

Knowing that it is almost impossible to change existing language elements, the Go team is careful to only add new features once they are fully developed. After an intentional phase of 10 years of stability, the Go team is contemplating a set of [larger improvements](https://blog.golang.org/go2draft) to the language as part of the journey towards Go 2.0.

### No Hard Real-time

While Go’s garbage collector introduces only very short interruptions, supporting hard real-time requires technologies without garbage collection like for example Rust.

### Conclusion

This blog post has given some background on the wise but often not so obvious choices that went into the design of Go and how they will save large engineering projects from many pains as their code bases and teams grow orders of magnitudes. Taken as a whole, they position Go as an excellent choice for large development projects looking for a modern programming language beyond Java.