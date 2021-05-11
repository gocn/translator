# Go 的抢占式调度
- 原文地址：https://dtyler.io/articles/2021/03/29/goroutine_preemption_en/
- 原文作者：Hidetatsu
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w19_Preemption_in_Go.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[guzzsek](https://github.com/guzzsek)、[fivezh](https://github.com/fivezh)
* * *

我正在研究 Go 中 goroutine 的抢占。如果您能指出文中任何错误并告知我，将感激不尽。

Go1.14 版本中的抢占行为已经发生了变化。在 Go1.14 中，goroutine 是“异步抢占”的，如[发行版本所述](https://golang.org/doc/go1.14#runtime)。这意味着什么呢？

首先，让我们看一个简单的例子。思考下面的 Go 程序。

```
package main

import (
    "fmt"
)

func main() {
    go fmt.Println("hi")
    for {
    }
}

```

在主函数中，启动了一个只输出 “hi” 的 goroutine。此外，存在一个无限循环 `for {}`。

如果我们携带参数 `GOMAXPROCS=1` 运行程序时，将发生什么呢？程序似乎在输出 “hi” 后，由于无限循环而没有任何反应。实际上，我使用 Go1.14 或更高版本运行该程序时（我使用 Go1.16 上运行了该程序（在 WSL2 上的 Ubuntu ）），它能按照预期工作。

有两种方法可以阻止此程序运行。一种是使用 1.14 之前的 Go 版本运行它。另一种是运行它时携带参数 `GODEBUG=asyncpreemptoff=1`。

当我在本地计算机上尝试时，它的工作方式如下。

```
$ GOMAXPROCS=1 GODEBUG=asyncpreemptoff=1 go run main.go
# it blocks here
```

程序没有输出 “hi” 。在描述为什么会发生这种情况之前，让我先说明几种使该程序按预期方式运行的方法。

一种方法是在循环中添加以下代码。
```


*************** package main
*** 2,11 ****
--- 2,13 ----
  
  import (
      "fmt"
+     "runtime"
  )
  
  func main() {
      go fmt.Println("hi")
      for {
+         runtime.Gosched()
      }
  }

```

`runtime.Gosched()` 类似于 POSIX 的 [`sched_yield`](https://man7.org/linux/man-pages/man2/sched_yield.2.html)。`sched_yield` 强制当前线程放弃 CPU，以便其他线程可以运行。之所以命名为 `Gosched`，因为 Go 中是 goroutine，而不是线程（这是一个猜测）。换句话说，显式调用 runtime.Gosched() 将强制对 goroutines 进行重新安排，并且我们期望将当前运行的 goroutine 切换到另一个。

另一种方法是使用 [GOEXPERIMENT=preemptibleloops](https://github.com/golang/go/blob/87a3ac5f5328ea0a6169cfc44bdb081014fcd3ec/src/cmd/internal/objabi/util.go#L257)。它强制 Go 运行时在“循环”上进行抢占。这种方式不需要更改代码。

## 协作式调度 vs 抢占式调度

首先，有两种主要的多任务调度方法：“协作”和“抢占”。协作式多任务处理也称为“非抢占”。在协作式多任务处理中，程序的切换方式取决于程序本身。“协作”一词是指这样一个事实：程序应设计为可互操作的，并且它们必须彼此“协作”。在抢占式多任务处理中，程序的切换交给操作系统。调度是基于某种算法的，例如基于优先级，FCSV，轮询等。

那么现在，goroutine 的调度是协作式还是抢占式的？至少在 Go1.13 之前，它是协作式的。

我没有找到任何官方文档，但是我发现在以下情况会进行 goroutine 切换（并不详尽）。

-   等待读取或写入未缓冲的通道
-   由于系统调用而等待
-   由于 time.Sleep() 而等待
-   等待互斥量释放

此外，Go 会启动一个线程，一直运行着“sysmon”函数，该函数实现了抢占式调度（以及其他诸如使网络处理的等待状态变为非阻塞状态）的功能。sysmon 运行在 M（Machine，实际上是一个系统线程），且不需要 P（Processor）。术语 M，P 和 G 在类似[这样](https://developpaper.com/gmp-principle-and-scheduling-analysis-of-golang-scheduler/)的各种文章中都有解释。我建议您在需要时参考此类文章。

当 sysmon 发现 M 已运行同一个 G（Goroutine）10ms 以上时，它会将该 G 的内部参数 `preempt` 设置为 true。然后，在函数序言中，当 G 进行函数调用时，G 会检查自己的 `preempt` 标志，如果它为 true，则它将自己与 M 分离并推入“全局队列”。现在，抢占就成功完成。顺便说一下，全局队列是与“本地队列”不同的队列，本地队列是存储 P 具有的 G。全局队列有以下几个作用。

-   存储那些超过本地队列容量（256）的 G
-   存储由于各种原因而等待的 G
-   存储由抢占标志分离的 G

这是 Go1.13 及其之前版本的实现。现在，您将了解为什么上面的无限循环代码无法按预期工作。`for{}` 仅仅是一个死循环，所以如前所述它不会触发 goroutine 切换。您可能会想，“sysmon 是否设置了抢占标志，因为它已经运行了 10ms 以上？” **然而，如果没有函数调用，即使设置了抢占标志，也不会进行该标志的检查**。如前所述，抢占标志的检查发生在函数序言中，因此不执行任何操作的死循环不会发生抢占。

是的，随着 Go1.14 中引入“非协作式抢占”（异步抢占），这种行为已经改变。

## “异步抢占”是什么意思？

让我们总结到目前为止的要点；Go 具有一种称为“sysmon”的机制，可以监视运行 10ms 以上的 goroutine 并在必要时强制抢占。但是，由于它的工作方式，在 `for{}` 的情况下并不会发生抢占。

Go1.14 引入非协作式抢占，即抢占式调度，是一种使用信号的简单有效的算法。

首先，sysmon 仍然会检测到运行了 10ms 以上的 G（goroutine）。然后，sysmon 向运行 G 的 P 发送信号（`SIGURG`）。Go 的信号处理程序会调用P上的一个叫作 `gsignal` 的 goroutine 来处理该信号，将其映射到 M 而不是 G，并使其检查该信号。gsignal 看到抢占信号，停止正在运行的 G。

由于此机制会显式发出信号，因此无需调用函数，就能将正在运行死循环的 goroutine 切换到另一个 goroutine。

通过使用信号的异步抢占机制，上面的代码现在就可以按预期工作。`GODEBUG=asyncpreemptoff=1` 可用于禁用异步抢占。

顺便说一句，他们选择使用 SIGURG，是因为 SIGURG 不会干扰现有调试器和其他信号的使用，并且因为它不在 libc 中使用。([参考](https://github.com/golang/proposal/blob/master/design/24543-non-cooperative-preemption.md#other-considerations))

## 总结

不执行任何操作的无限循环不会将 CPU 传递给其他 goroutine，并不意味着 Go1.13 之前的机制是不好的。正如 [@davecheney](https://github.com/golang/go/issues/11462#issuecomment-116616022) 所说，通常不认为这是一个特殊问题。起初，异步抢占不是为了解决无限循环问题引出的。

尽管异步抢占的引入使调度更具抢占性，但也有必要在 GC 期间更加谨慎地处理“不安全点”。在这方面对实现上的考虑也非常有趣。有兴趣的读者可以自己阅读[议题：非协作式 goroutine 抢占](https://github.com/golang/proposal/blob/master/design/24543-non-%20cooperative-preemption.md)。

## 参考

-   [Proposal: Non-cooperative goroutine preemption](https://github.com/golang/proposal/blob/master/design/24543-non-cooperative-preemption.md)
-   [runtime: non-cooperative goroutine preemption](https://github.com/golang/go/issues/24543)
-   [runtime: tight loops should be preemptible](https://github.com/golang/go/issues/10958)
-   [runtime: golang scheduler is not preemptive - it’s cooperative?](https://github.com/golang/go/issues/11462)
-   [Source file src/runtime/preempt.go](https://golang.org/src/runtime/preempt.go)
-   [Goroutine preemptive scheduling with new features of go 1.14](https://developpaper.com/goroutine-preemptive-scheduling-with-new-features-of-go-1-14/)
-   [Go: Goroutine and Preemption](https://medium.com/a-journey-with-go/go-goroutine-and-preemption-d6bc2aa2f4b7)
-   [At which point a goroutine can yield?](https://stackoverflow.com/questions/64113394/at-which-point-a-goroutine-can-yield)
-   [Go: Asynchronous Preemption](https://medium.com/a-journey-with-go/go-asynchronous-preemption-b5194227371c)
-   [go routine blocking the others one [duplicate]](https://stackoverflow.com/questions/17953269/go-routine-blocking-the-others-one)
-   [(Ja) Golangのスケジューラあたりの話](https://qiita.com/takc923/items/de68671ea889d8df6904)
-   [(Ja) goroutineがスイッチされるタイミング](https://qiita.com/umisama/items/93333ffe4d9fc7e4ba1f)


