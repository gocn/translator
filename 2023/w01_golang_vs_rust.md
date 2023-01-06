# Golang vs Rust- Which Language to be choose for Server-Side Programming

- 原文地址：<https://medium.com/@golang_company/golang-vs-rust-which-language-to-be-choose-for-server-side-programming-628cd81c1184>
- 原文作者：Golang Company
- 本文永久链接：<https://github.com/gocn/translator/blob/master/2023/w01_golang_vs_rust.md>
- 译者：[pseudoyu](https://github.com/pseudoyu)

![title_pic](../static/images/2023/w01_golang_vs_rust/title_pic.jpeg)

Choosing a language for server-side programming should be based on your long-term goals and the requirements of the project. So, asking should I hire a Go developer or should I opt for Rust development aimlessly won’t help you out. However, if you find yourself to be in a spot of bother, then this blog will clear the air for you. So, let us get started.

Go is a statically typed, AOT-compiled language. On the other hand, Rust is a statically, strongly typed and AOT-compiled language. Rust is a multi-paradigm, high-level and general purpose language.

Let us assess both the languages on the basis of various parameters.

## 1. Simplicity in Go vs Rust

- Simplicity is one of the major Go selling points. Whereas a development process could take hours or days in the case of Golang, it could take upto weeks for Rust. This has a significant influence over collaborations.
- Go programs are easy to decipher, easy to write and simple to manage in large teams. On the other hand, Rust is a very complex language to learn. It takes hours to become productive in Rust.
- Furthermore, various useful features like generics which were at one time missing in Golang, have been incorporated in the version 1.18.

## 2. Go vs Rust Performance

- When it comes to performance, both Golang and Rust are highly sought-after. They have great internal, high-performance tools for managing dependencies and standard builds. Due to its perfectly alright control over how threads operate and how resources are shared across threads, Rust will nearly always defeat Go in run-time benchmarks.
- Both the languages- Rust and Go- make use of a similar formatting tool. You have rustfmt for Rust and you have gofmt for Go. They automatically reformat your code in accordance with canonical style.
- Go abstracts away from the architectural specifics to help programmers focus on the issue at hand. This is completely opposite to what we observe in Go.
- While Go lacks the runtime speed in comparison to Rust, it has faster development and compilation. This is because Rust compiler performs a number of optimizations and checks. This makes Rust unsuitable for large projects.
- However, in the case of deployment, both of them are the same. They produce static binary as an output. In order to run it, you won’t need an interpreter.

Meanwhile, if you are stuck with microservice development or building a server in Golang, you should [hire Go developers](https://golang.company/go-developers) from Golang.Company. They will assist you with various steps and build you a scalable and robust application.

The graph below depicts the state of benchmark test between Rust and Go.

![compare_graph](../static/images/2023/w01_golang_vs_rust/compare_graph.png)

## 3. Go vs Rust Concurrency

- Go has great support for concurrency. Most developers admit that goroutines and channels are the best features of Golang. However, these features are also available in Rust, that are accessible via the standard library or third-party libraries like Tokio.
- The Rust concurrency model is deemed to be ‘correct’. This means that the compiler is able to catch a class of thread safety bugs at the time compilation, before the execution of the program. This allows developers to avoid mistakes like writing it to the same shared variable without any synchronization.
- Goroutines are basically lightweight threads. These are run-time-managed Go objects that are scheduled across OS threads. Goroutines are very easy to create and cheaply, and the stack’s size can be adjusted over time. Because OS threads are far more expensive than goroutines, developers can build thousands of goroutines instead.
- This solution’s drawback is that it increases CPU and memory overhead in the case of Go. However, Rust has a solution for this issue as it strives to minimize even minor overheads.

## 4. Rust vs Go Error Handling

- Both programming languages have a similar approach to handling errors. In Golang, the functions return several values in addition to the error. The dedicated type, the enum, is introduced by Rust and has two subtypes: result type and error type.
- Error handling may be made less verbose than in Golang by unwrapping it with a question mark (? ). For both the languages, the handling is detailed and cleaner.
- These approaches help developers look for functions where the error is not handled properly. This makes code writing easier and safer in Rust and Go.

If you are willing to know the trend involving the interest over the languages, then you should take a look at the graph below.

![interest_graph](../static/images/2023/w01_golang_vs_rust/interest_graph.png)

## 5. Memory Safety and Security

- In Rust, one has to perform a lot of tasks in order to ensure that the code is secure. This is because the language ensures memory safety at the time of compilation utilizing innovative ownership mechanisms. The compiler is extremely ‘stringent’ as it does not let any unsafe memory code to pass through. Rust also presents multiple concurrency models to ensure that there are no lapses in memory safety.
- Go, on the other hand, is not memory safe. In Go, non-atomic multi word structs implement interfaces and slices. Furthermore, data races lead to invalid values which at times lead to memory corruption.
- However, Go, like Rust, can be considered safe for handling use-after-free and dangling pointers. Go uses an automated garbage collector to limit the issues related to memory leaks. On the other hand, the ownership and borrowing functionality is a great feature of Rust. According to this principle, every item has an owner which has the option of lending it out or giving it to someone else.
- Rust also allows us to build numerous immutable references or ONE AND ONLY changeable references. With this method, Rust fixes frequent memory issues without the need of a garbage collector, outperforming Golang in terms of performance.
- However, there is one point that you have to keep in mind. Even though the Rust compiler is extremely efficient in catching memory bugs and helps you write very performant code, it comes at a price. This is the Peter Parker principle, which means you have to be very careful when you use Rust.

Below is a graph that depicts the memory usage between Go and Rust (and Java).

![memory_compare](../static/images/2023/w01_golang_vs_rust/memory_compare.png)

## 6. Community

- While Golang came into the scene in 2009, Rust made the entry in the year 2013. So, coupled with Golang’s simplicity, it is one of the most popular languages among developers.
- Moreover, the libraries and frameworks are more mature in Go than in the case of Rust, especially the ones that are associated with web development.
- However, the developers of Rust are extremely communicative and being an open-source language like Go, is subject to further developments.

## 7. Career Opportunities

- Last but not the least, career opportunity is an aspect that you have to consider. If your goal is to get hired, you should look at the market that has the most jobs. One hand, if you see, you have next to no jobs in Rust. On the other hand, you have lots of jobs in Golang.
- Companies that are using Golang are Google, Uber, Twitch, Dailymotion, SendGrid, Dropbox, Soundcloud, etc. On the contrary, companies that are using Rust are Brave (Github), Atlassian, Amazon, Discord, etc.
- The average salary per annum of a Rust developer is around $120k per year. However, the average developer salary for Golang is around $135k per year.

If your project involves web development, distributable servers, then it is recommended that you opt for Go. The programming part is extremely easy and the concurrency model will help you out a lot. But if you are going for the development of a CLI application, then you should choose Rust because of string processing, the libraries it contains. Having said that, Rust is not one of the easiest languages to master.
