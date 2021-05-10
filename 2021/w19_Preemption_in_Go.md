# Preemption in Go
- 原文地址：https://dtyler.io/articles/2021/03/29/goroutine_preemption_en/
- 原文作者：Hidetatsu
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w19_Preemption_in_Go.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[]()
* * *

I was looking into the preemption of goroutine in Go. It would be appreciatee if you could point out any mistakes and tell me it.

The behavior of preemption in Go changed at Go1.14 release. On Go1.14, goroutine is “asynchronously preemptible” as described in [Release Notes](https://golang.org/doc/go1.14#runtime). What does this mean?

First, let’s look at a simple example. Consider the following Go program.

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

In the main function, it starts one goroutine that just outputs “hi”. In addition, it loops infinitely with `for {}`.

What will happen if we run this program with `GOMAXPROCS=1`? It seems to output “hi” and then nothing happens because of the infinite loop. In fact, when I run this program on Go1.14 or later (I ran it on Go1.16 (on Ubuntu on WSL2)), it works as it should.

There are two ways to prevent this program from running as it should. One is to run it with a version of Go earlier than 1.14. The other is to run it with `GODEBUG=asyncpreemptoff=1`.

When I tried it in local machine, it worked as follows.

```
$ GOMAXPROCS=1 GODEBUG=asyncpreemptoff=1 go run main.go
# it blocks here
```

No “hi” is output. Before describing why this happens, let me explain a couple of ways to make this program behave as expected.

One way is to add the following process in the loop.

```


*************** package main
*** 2,11 ****
--- 2,13 ----
  
  import (
  "fmt"
+ "runtime"
  )
  
  func main() {
  go fmt.Println("hi")
  for {
+ runtime.Gosched()
  }
  }

```

`runtime.Gosched()` is something like POSIX’s [`sched_yield`](https://man7.org/linux/man-pages/man2/sched_yield.2.html), where `sched_yield` forces the thread to give up CPU so that other threads can run. It is named `Gosched` because Go is a goroutine, not a thread (this is a guess). In other words, explicitly calling `runtime.Gosched()` will force the goroutines to be rescheduled, and we can expect the current-running-goroutine is switched to another one.

Another way is using [GOEXPERIMENT=preemptibleloops](https://github.com/golang/go/blob/87a3ac5f5328ea0a6169cfc44bdb081014fcd3ec/src/cmd/internal/objabi/util.go#L257). It forces the Go runtime to do the preemption on the “loop”. The way doesn’t require the code change.

## Cooperative vs. Preemptive scheduling in Go

To begin with, there are two main methods for scheduling multitasking; “Cooperative” and “Preemptive”. Cooperative multitasking is also called “non-preemptive”. In cooperative multitasking, how the program switches depends on the program itself. It seems that the term “cooperative” is intended to refer to the fact that the programs should be designed to be interoperable and they must “cooperate” each other. In preemptive multitasking, the switch of the program is left to the OS. The scheduling method is based on some algorithm, such as priority-based, FCSV, round-robin, etc.

So now, is the scheduling of goroutine cooperative or preemptive? At least up to Go1.13, it was cooperative.

I couldn’t find any official documentation, but I found out that goroutine switches happen in the following cases (this is not exhaustive.) ;

-   Waiting to read or write to an unbuffered channel
-   Waiting due to system call invocation
-   Waiting because of time.Sleep()
-   Waiting for mutex to be released

In addition, Go has a component that keeps executing a function called “sysmon”, which does preemption (and other things like making the waiting state of network processing non-blocking). The sysmon component is M (Machine, it is actually an OS thread), but it runs without P (Processor). The term M, P and G is explained in various articles like [this](https://developpaper.com/gmp-principle-and-scheduling-analysis-of-golang-scheduler/). I recommend that you refer to such articles if needed.

When sysmon finds that M has been running the same G (Goroutine) for more than 10ms, it sets the `preempt` flag, an internal parameter of that G, to true. Then, in the function prologue when the G makes a function call, the G checks its own `preempt` flag, and if it is true, it detaches itself from M and pushes itself to a queue called “global queue”. Now, the preemption is done successfully. By the way, the global queue is a different queue from the “local queue”, a queue to store G that P has. There are several purposes of a global queue.

-   To store Gs that exceed the capacity (256) of local queue.
-   To store Gs that are waiting for various reasons.
-   To store Gs that are detached by the preempt flag.

This is the implementation up to Go1.13. Now, you’ll understand why the infinite looping code above did not work as expected. The `for {}` is just a busy loop, so it does not trigger the goroutine switch as described earlier. You may think, “Isn’t the preempt flag set by sysmon because it has been running for more than 10ms?” However, **if there is no function call, even if the preempt flag is set, the check of the flag does not occur**. As I mentioned earlier, the check of the preempt flag occurs in function prologue, so a busy loop with doing nothing could not reach the execution of preemption.

And yes, this behavior has changed with the introduction of “non-cooperative preemption” (asynchronous preemption) in Go1.14.

## What does “asynchronously preemptible” mean?

Let’s summarize the points so far; Go has a mechanism, called “sysmon”, to monitor goroutines running for more than 10ms and force preemption when necessary. However, due to the way it worked, preemption did not occur in cases like `for {}`.

With the non-cooperative preemption introduced in Go1.14, the scheduler in Goroutine can now be called preemptive. It is a simple but effective algorithm that uses signals.

First, sysmon still detects a G (goroutine) that has been moving for more than 10ms. Then, sysmon sends a signal ( `SIGURG` ) to the thread (P) that is running that G. Go’s signal handler invokes another goroutine called `gsignal` on P to handle the signal, maps it to M instead of G, and makes it check the signal. The gsignal sees that preemption has been ordered and stops the G that was running until then.

Because this mechanism explicitly emits a signal, don’t need to call a function in other words, just a goroutine which is running busy loop can be switched to another goroutine.

With this asynchronous preemption mechanism using signals, the above code now works as expected. `GODEBUG=asyncpreemptoff=1` can be used to disable the asynchronous preemption.

Incidentally, they chose to use SIGURG because SIGURG does not interfere with the use of existing debuggers and other signals, and because it is not used in libc. ([Reference](https://github.com/golang/proposal/blob/master/design/24543-non-cooperative-preemption.md#other-considerations))

## Summary

Just because an infinite loop that doesn’t do anything doesn’t pass holding CPU to other goroutines, it doesn’t mean that the mechanism up to Go1.13 is bad. As [@davecheney](https://github.com/golang/go/issues/11462#issuecomment-116616022) has said, this is usually not considered a particular problem. In the first place, asynchronous preemption was not introduced to solve this infinite loop problem.

Although the introduction of asynchronous preemption made scheduling more preemptive, it also made it necessary to be more careful in handling “unsafe points” during GC. The implementation considerations in this area are also very interesting. Readers who are interested can read it themselves [Proposition: Non-cooperative goroutine preemption](https://github.com/golang/proposal/blob/master/design/24543-non-%20cooperative-preemption.md).

## References

-   [Proposal: Non-cooperative goroutine preemption](https://github.com/golang/proposal/blob/master/design/24543-non-cooperative-preemption.md)
-   [runtime: non-cooperative goroutine preemption](https://github.com/golang/go/issues/24543)
-   [runtime: tight loops should be preemptible](https://github.com/golang/go/issues/10958)
-   [runtime: golang scheduler is not preemptive - it’s cooperative?](https://github.com/golang/go/issues/11462)
-   [Source file src/runtime/preempt.go](https://golang.org/src/runtime/preempt.go)
-   [Goroutine preemptive scheduling with new features of go 1.14](https://developpaper.com/goroutine-preemptive-scheduling-with-new-features-of-go-1-14/)
-   [Go: Goroutine and Preemption](https://medium.com/a-journey-with-go/go-goroutine-and-preemption-d6bc2aa2f4b7)
-   [At which point a goroutine can yield?](https://stackoverflow.com/questions/64113394/at-which-point-a-goroutine-can-yield)
-   [Go: Asynchronous Preemption](https://medium.com/a-journey-with-go/go-asynchronous-preemption-b5194227371c)
-   [go routine blocking the others one \[duplicate\]](https://stackoverflow.com/questions/17953269/go-routine-blocking-the-others-one)
-   [(Ja) Golangのスケジューラあたりの話](https://qiita.com/takc923/items/de68671ea889d8df6904)
-   [(Ja) goroutineがスイッチされるタイミング](https://qiita.com/umisama/items/93333ffe4d9fc7e4ba1f)

