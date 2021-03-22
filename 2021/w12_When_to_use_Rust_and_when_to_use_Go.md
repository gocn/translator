- 原文地址：https://medium.com/codex/when-to-use-rust-and-when-to-use-go-590bcbb49bec
- 译者：[tt](https://github.com/1-st)

Right off the bat, there are clear differences between Go and Rust. Go has a stronger focus on building web APIs and small services that can scale endlessly, especially with the power of goroutines. The latter is also possible with Rust, but things are much harder from a developer experience point of view.


![](../static/images/w12_When_To_Use_Rust_And_When_To_Use_Go/go_vs_rust.jpg)

Rust works well for processing large amounts of data and other CPU-intensive operations, such as executing algorithms. This is Rust’s biggest edge over Go. Projects that demand high performance are generally better suited for Rust.

In this tutorial, we’ll compare and contrast Go and Rust, evaluating each programming language for performance, concurrency, memory management, and the overall developer experience. We’ll also present an overview of these elements to help you pick the right language for your project at a glance.

If you’re all caught up, let’s dive in!

## Performance
Originally designed by Google’s engineers, Go was introduced to the public in 2009. It was created to offer an alternative to C++ that was easier to learn and code and was optimized to run on multicore CPUs.

Since then, Go has been great for developers who want to take advantage of the concurrency the language offers. The language provides goroutines that enable you to run functions as subprocesses.

A big advantage of Go is how easily you can use goroutines. Simply adding the go syntax to a function makes it run as a subprocess. Go’s concurrency model allows you to deploy workloads across multiple CPU cores, making it a very efficient language.

```go
package main
import (
    "fmt"
    "time"
)
func f(from string) {
    for i := 0; i < 3; i++ {
        fmt.Println(from, ":", i)
    }
}
func main() {
    f("direct")
    go f("goroutine")
    time.Sleep(time.Second)
    fmt.Println("done")
}
```
Despite the multicore CPU support, Rust still manages to outperform Go. Rust is more efficient in executing algorithms and resource-intensive operations. The Benchmarks Game compares Rust and Go for various algorithms, such as binary trees. For all the tested algorithms, Rust was at least 30 percent faster; in the case of binary tree calculations, it was up to 1,000 percent. A study by Bitbucket shows similar results in which Rust performs on par with C++.

![](../static/images/w12_When_To_Use_Rust_And_When_To_Use_Go/benchmark.png)

*(Source: Benchmarks Game)*

## Concurrency
As mentioned above, Go supports concurrency. For example, let’s say you’re running a web server that handles API requests. You can use Go’s goroutines to run each request as a subprocess, maximizing efficiency by offloading tasks to all available CPU cores.

Goroutines are part of Go’s built-in functions, while Rust has only received native async/await syntax to support concurrency. As such, the developer experience edge goes to Go when it comes to concurrency. However, Rust is much better at guaranteeing memory safety.

Here’s an example of simplified threads for Rust:

```rust
use std::thread;
use std::time::Duration;
fn main() {
    // 1. create a new thread
    for i in 1..10 {
        thread::spawn(|| {
            println!("thread: number {}!", i);
            thread::sleep(Duration::from_millis(100));
        });
    }
    println!("hi from the main thread!");
}
```
Concurrency has always been a thorny problem for developers. It’s not an easy task to guarantee memory-safe concurrency without compromising the developer experience. However, this extreme security focus led to the creation of provably correct concurrency. Rust experimented with the concept of ownership to prevent unsolicited access of resources to prevent memory safety bugs.

Rust offers four different concurrency paradigms to help you avoid common memory safety pitfalls. We’ll take a closer look at two common paradigms: channel and lock.

## Channel
A channel helps transfer a message from one thread to another. While this concept also exists for Go, Rust allows you to transfer a pointer from one thread to another to avoid racing conditions for resources. Through passing pointers, Rust can enforce thread isolation for channels. Again, Rust displays its obsession with memory safety in regards to its concurrency model.

## Lock
Data is only accessible when the lock is held. Rust relies on the principle of locking data instead of cod, which is often found in programming languages such as Java.

For more details on the concept of ownership and all concurrency paradigms, check out “Fearless Concurrency with Rust.”

## Memory safety
The earlier concept of ownership is one of Rust’s main selling points. Rust takes type safety, which is also important for enabling memory-safe concurrency, to the next level.

According to the Bitbucket blog, “Rust’s very strict and pedantic compiler checks every variable you use and every memory address you reference. It avoids possible data race conditions and informs you about undefined behavior.”

This means you won’t end up with a buffer overflow or a race condition due to Rust’s extreme obsession with memory safety. However, this also has its disadvantages. For example, you have to be hyperaware of memory allocation principles while writing code. It’s not easy to always have your memory safety guard up.

## Developer experience
First of all, let’s look at the learning curve associated with each language. Go was designed with simplicity in mind. Developers often refer to it as a “boring” language, which is to say that its limited set of built-in features makes Go easy to adopt.

Furthermore, Go offers an easier alternative to C++, hiding aspects such as memory safety and memory allocation. Rust takes another approach, forcing you to think about concepts such as memory safety. The concept of ownership and the ability to pass pointers makes Rust a less attractive option to learn. When you’re constantly thinking about memory safety, you’re less productive and your code is bound to be more comlex.

The learning curve for Rust is pretty steep compared to Go. It’s worth mentioning, however, that Go has a steeper learning curve than more dynamic languages such as Python and JavaScript.

## When to use Go
Go works well for a wide variety of use cases, making it a great alternative to Node.js for creating web APIs. As noted by Loris Cro, “Go’s concurrency model is a good fit for server-side applications that must handle multiple independent requests”. This is exactly why Go provides goroutines.

What’s more, Go has built-in support for the HTTP web protocol. You can quickly design a small API using the built-in HTTP support and run it as a microservice. Therefore, Go fits well with the microservices architecture and serves the needs of API developers.

In short, Go is a good fit if you value development speed and prefer syntax simplicity over performance. On top of that, Go offers better code readability, which is an important criterion for large development teams.

Choose Go when:
* You care about simplicity and readability
* You want an easy syntax to quickly write code
* You want to use a more flexible language that supports web development

## When to use Rust
Rust is a great choice when performance matters, such as when you’re processing large amounts of data. Furthermore, Rust gives you fine-grained control over how threads behave and how resources are shared between threads.
On the other hand, Rust comes with a steep learning curve and slows down development speed due to the extra complexity of memory safety. This is not necessarily a disadvantage; Rust also guarantees that you won’t encounter memory safety bugs as the compiler checks each and every data pointer. For complex systems, this assurance can come in handy.

Choose Rust when:
* You care about performance
* You want fine-grained control over threads
* You value memory safety over simplicity

## Go vs. Rust: My honest take
Let’s start by highlighting the similarities. Both Go and Rust are open-source and designed to support the microservices architecture and parallel computing environments. Both optimize the utilization of available CPU cores through concurrency.

But at the end of the day, which language is best?

There many ways to approach this question. I’d recommend thinking about what type of application you want to build. Go serves well for creating web applications and APIs that take advantage of its built-in concurrency features while supporting the microservices architecture.

You can also use Rust to develop a web API, but it wasn’t designed with this use case in mind. Rust’s focus on memory-safety increases complexity and development time, especially for a fairly simple web API. However, the larger amount of control you have over your code allows you to write more optimized, memory-efficient, and performant code.

To put it as simply as possible, the Go versus Rust debate is really a question of simplicity versus security.