# Go Native Concurrency Primitives & Best Practices

- 原文地址：https://benjiv.com/go-native-concurrency-primitives/
- 原文作者：**Benjamin Vesterby**
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w08_Go_Native_Concurrency_Primitives_&_Best_Practices.md
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：

The Go programming language was created with concurrency as a first class citizen. It is a language that allows you to write programs that are highly parallel with ease by abstracting away the details of parallelism behind concurrency primitives[1](https://benjiv.com/go-native-concurrency-primitives/#fn:1) within the language.

Most languages focus on parallelization as part of the standard library or expect the developer ecosystem to provide a parallelization library. By including the concurrency primitives in the language, Go, allows you to write programs that leverage parallelism without needing to understand the ins and outs of writing parallel code.

Table Of Contents

- [Concurrent Design](#cd)
  - [Communicating Sequential Processes (CSP)](#csp)
  - [Concurrency through Communication](#ctc)
    - [Blocking vs Communicating](#bvc)
- [Go’s Native Concurrency Primitives](#cncp)
  - [Go Routines](#go)
    - [What are Go Routines?](#wagr)
    - [Leaking Go Routines](#lgr)
    - [Panicking in Go Routines](#pigr)
  - [Channels](#channels)
    - [What are Channels in Go?](#wacig)
    - [How do Channels work in Go?](#hdcwig)
      - [Closing a Channel](#cac)
    - [Types of Channels](#toc)
      - [Unbuffered Channels](#uc)
      - [Buffered Channels](#bc)
      - [Read-Only & Write-Only Channels](#rwc)
    - [Design Considerations for Channels](#dcfc)
      - [Owner Pattern](#op)
    - [Looping over Channels](#loc)
    - [Forwarding Channels](#fc)
  - [Select Statements](#ss)
    - [Testing Select Statements](#tss)
    - [Work Cancellation with Context](#wcwc)

<h2 id="cd">Concurrent Design</h2>
The designers of Go put heavy emphasis on concurrent design as a methodology which is based on the idea of communicating[2](https://benjiv.com/go-native-concurrency-primitives/#fn:2) critical information rather than blocking and sharing that information.[3](https://benjiv.com/go-native-concurrency-primitives/#fn:3)

The emphasis on concurrent design allows for application code to be executed in sequence or in parallel *correctly* without designing and implementing for parallelization, which is the norm.[4](https://benjiv.com/go-native-concurrency-primitives/#fn:4) The idea of concurrent design is not new and in fact a good example is the move from waterfall to agile development which is actually a move to concurrent engineering practices (early iteration, repeatable process).[5](https://benjiv.com/go-native-concurrency-primitives/#fn:5)

Concurrent design is about writing a “correct” program versus writing a “parallel” program.

Questions to ask when building concurrent programs in Go:

- Am I blocking on critical regions?
- Is there a more *correct* (i.e. Go centric) way to write this code?
- Can I improve the functionality and readability of my code by communicating?

If any of these are Yes, then you should consider rethinking your design to use Go best practices.

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)


<h3 id="csp">Communicating Sequential Processes (CSP)</h3>
The basis for part of the Go language[6](https://benjiv.com/go-native-concurrency-primitives/#fn:6) comes from a paper by Hoare[7](https://benjiv.com/go-native-concurrency-primitives/#fn:7) that discusses the need for languages to treat concurrency as a part of the language rather than an afterthought. The paper proposes a threadsafe queue of sorts which allows for data communication between different processes in an application.

If you read through the paper you will see that the `channel` primitive in Go is very similar to the description of the primitives in the paper and in fact comes from previous work on building languages based on CSP by Rob Pike.[8](https://benjiv.com/go-native-concurrency-primitives/#fn:8)

In one of Pike’s lectures he identifies the real problem as the “need [for] an approach to writing concurrent software that guides our design and implementation."[9](https://benjiv.com/go-native-concurrency-primitives/#fn:9) He goes on to say concurrent programming is not about parallelizing programs to run faster but instead “using the power of processes and communication to design elegant, responsive, reliable systems."[9](https://benjiv.com/go-native-concurrency-primitives/#fn:9)

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h3 id="ctc">Concurrency through Communication</h3>
One of the most common phrases we hear from the creators of Go is:[2](https://benjiv.com/go-native-concurrency-primitives/#fn:2) [3](https://benjiv.com/go-native-concurrency-primitives/#fn:3)

> Don’t communicate by sharing memory, share memory by communicating.
>
> \- Rob Pike

This sentiment is a reflection of the fact that Go is based on [CSP](https://benjiv.com/go-native-concurrency-primitives/#communicating-sequential-processes-csp) and the language has native primitives for communicating[10](https://benjiv.com/go-native-concurrency-primitives/#fn:10) between threads (go routines).

An example of communicating rather than using a mutex to manage access to a shared resource is the following code:[11](https://benjiv.com/go-native-concurrency-primitives/#fn:11)

```go
// Adapted from https://github.com/devnw/ttl
// a TTL cache implementation for Go.
func readwriteloop(
  incoming <-chan interface{},
) <-chan interface{} {
   // Create a channel to send data to.
  outgoing = make(chan interface{})

  go func(
    incoming <-chan interface{},
    outgoing chan<- interface{},
    ) {
    defer close(outgoing)

    // `value` is the shared 
    // resource or critical section.
    var value interface{}

    for {
      select {

      // incoming is the channel where data is
      // sent to set the shared resource.
      case v, ok := <-incoming:
        if !ok {
          return // Exit the go routine.
        }

        // Write the data to the shared resource.
        value = v.v

      // outgoing is the channel that 
      // the shared resource on request
      case outgoing <- value:
      }
    }
  }(incoming, outgoing)
  
  return outgoing
}
```

Let’s take a look at the code and see what it does.

1. Notice that this is *not* using the `sync` package or *any* blocking functions.
2. This code only uses the Go concurrency primitives `go`, `select`, and `chan`
3. [Ownership](https://benjiv.com/go-native-concurrency-primitives/#owner-pattern) of the shared resource is managed by the go routine. (Line 17)
4. Even though the method contains a go routine, access to the shared resources does *not* happen in parallel. (Lines 30, and 34)
5. The [`select` statement](https://benjiv.com/go-native-concurrency-primitives/#select-statements) is used to check for read or write requests. (Lines 24, and 34)
6. A channel read from the incoming channel updates the value. (Line 24)
7. A channel read from outside the routine executes a channel write to the outgoing channel with the current value of the shared resource. (Line 34)

Since there is no parallelism within the go routine itself the shared resource is safe to access via the returned [read-only channel](https://benjiv.com/go-native-concurrency-primitives/#read-only--write-only-channels) . In fact, the use of the `select` statement here provides a number of benefits. The [select primitive](https://benjiv.com/go-native-concurrency-primitives/#select-statements) section goes into more detail on this.

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h4 id="bvc"> Blocking vs Communicating</h4>
Blocking[12](https://benjiv.com/go-native-concurrency-primitives/#fn:12)

- Stops process on critical section read / write
- Requires knowledge of the **need** for blocking
- Requires an understanding of how to avoid races and deadlocks
- Memory elements are shared directly by multiple processes/threads

Communicating[12](https://benjiv.com/go-native-concurrency-primitives/#fn:12)

- Critical data is shared on request
- Processes work when there is something to do
- Memory elements are communicated, not shared directly

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h1 id="gncp"> Go’s Native Concurrency Primitives</h1>
<h2 id="gr">Go Routines</h2>
<h3 id="wagr">What are Go Routines?</h3>
Go routines are lightweight *threadlike* processes which enable logical process splitting similar to the `&` after a bash command[4](https://benjiv.com/go-native-concurrency-primitives/#fn:4). Once the go routine is split from the parent routine it is handed off to the Go runtime for execution. Unlike the `&` in `bash` however these processes are scheduled for execution in the Go runtime and not necessarily executed in parallel.[4](https://benjiv.com/go-native-concurrency-primitives/#fn:4)

![1643795792968](./1.png)

**Figure 1: Example of a Go Routine Process Split**

>  **NOTE:** The distinction here of “scheduled” is important because the Go runtime multiplexes the execution of go routines to improve performance on top of the operating system’s scheduling. This means that no assumptions can be made as to *when* the routine will execute.

<h3 id="lgr"> Leaking Go Routines</h3>
Created by the `go` primitive, go routines are cheap, but its important to know that they are **not** free.[13](https://benjiv.com/go-native-concurrency-primitives/#fn:13) Cleaning up routines is important to ensure proper garbage collection of resources in the Go runtime.

Time should be spent on designing with cleanup in mind. Ensuring that long running routines properly exit in the event of failure. It is also important to not create an unbounded number of go routines.

It is simple enough to spawn a go routine and because of that just using the `go` primitive any time you want parallelization is tempting, but each routine spawned has a minimum overhead of about 2kb.[14](https://benjiv.com/go-native-concurrency-primitives/#fn:14) If your code creates too many routines and they each have large overhead you can blow the stack. This is incredibly difficult to debug in production environments because it is hard to tell where the stack is overflowing and where the stack is leaking.

When a stack overflow occurs, the runtime will panic and the program will exit and each of the go routines will have stack information printed to standard error. This creates a great deal of noise in logs and is not very useful. Not only is the stack information not useful, but there is a huge amount of data that will be output (a log for every go routine, including it’s identifier and state). This is additionally difficult to debug because generally the log buffer on the operating system is likely too small to hold all of the stack information.

>  **NOTE:** In fairness, I have only seen this happen in production environments where the application was using **>400,000** large go routines. This is most likely very uncommon and is not a problem for most applications.

TL;DR: Design go routines with the end in mind so that they properly stop when completed.[13](https://benjiv.com/go-native-concurrency-primitives/#fn:13)

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h3 id="pigr"> Panicking in Go Routines</h3>
In general, panicking in a Go application is against best practices[15](https://benjiv.com/go-native-concurrency-primitives/#fn:15) and should be avoided. In lieu of panicking, you should return and handle errors from your functions. However, in the event that using `panic` is necessary it is important to know that panicking in a Go routine without a `defer` recover (directly in that routine) will crash your application *EVERY TIME*.

> **BEST PRACTICE:**
> Do NOT Panic!

This is incredibly difficult to debug in a production environment because it requires the `stderr` to be redirected to a file because it is likely your application is running as a daemon. This is easier if you have a log aggregator and it is set to monitor stderr, or the flat-file log. With Docker this is a bit different, but it is still a problem.

> Each Go routine needs its own `defer`/`recover` code[16](https://benjiv.com/go-native-concurrency-primitives/#fn:16)

```go
defer func() {
  if r := recover(); r != nil {
      // Handle Panic HERE
  }
}()
```

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h2 id="channels"> Channels</h2>
<h3 id="wacig"> What are Channels in Go?</h3>
What is a channel?

Derived from the Communicating Sequential Processes paper by Hoare (1977)[7](https://benjiv.com/go-native-concurrency-primitives/#fn:7) a channel is a communication mechanism in Go which supports data transfer in a threadsafe manner. It can be used to communicate between parallel go routines safely and efficiently without the need for a mutex.

Channels abstract away the difficulties of building parallel code to the Go runtime and provide a simple way to communicate between go routines. Essentially in it’s simplest form a channel is a queue of data.

In the words of Rob Pike: “Channels orchestrate; mutexes serialize."[17](https://benjiv.com/go-native-concurrency-primitives/#fn:17)

<h3 id="hdcwig"> How do Channels work in Go?</h3>
Channels are block by default. This means that if you try to read from a channel it will block processing of that go routine until there is something to read (i.e. data being sent to the channel). Similarly, if you try to write to a channel and there is no consumer for the data (i.e. reading from the channel) it will block processing of that go routine until there is a consumer.

There are some very important behaviors surrounding channels in Go. The Go runtime is designed to be very efficient and because of that if there is a Go routine which is blocked on a channel read or write the runtime will sleep the routine while it waits for something to do. Once the channel has a producer or consumer it will wake up the blocked routine and continue processing.

This is very important to understand because it allows you to explicitly leverage the CPU contention of the system through the use of channels.

>  **NOTE:** A `nil` channel will **ALWAYS** block.

<h4 id="cac"> Closing a Channel</h4>
When you are done with a channel it is best practice to close it. This is done using the `close` function on the channel.

Sometimes it may not be possible to close a channel because it will cause a panic elsewhere in your application (due to a channel write on a closed channel). In that situation when the channel goes out of scope it will be garbage collected.

```go
  // Create the channel
  ch := make(chan int)

  // Do something with the channel

  // Close the channel
  close(ch)
```

If the channel is limited to the same scope (i.e. function) you can use the `defer` keyword to ensure that the channel is closed when the function returns.

```go
  // Create the channel
  ch := make(chan int)
  defer close(ch) // Close the channel when func returns

  // Do something with the channel
```

When a channel is closed it will no longer be able to be written to. It is very important to be mindful of how you close channels because if you attempt to write to a closed channel the runtime will *panic*. So closing a channel prematurely can have unexpected side effects.

After a channel is closed it will no longer block on read. What this means is that all of the routines that are blocked on a channel will be woken up and continue processing. The values returned on the read will be the `zero` values of the type of the channel and the second read parameter will be `false`.

```go
  // Create the channel
  ch := make(chan int)

  // Do something with the channel

  // Close the channel
  close(ch)

  // Read from closed channel
  data, ok := <-ch
  if !ok {
    // Channel is closed
  }
```

The `ok` parameter will be `false` if the channel is closed in the example above.

>  **NOTE:** Only standard and [write-only](https://benjiv.com/go-native-concurrency-primitives/#read-only--write-only-channels) channels can be closed using the `close` function.

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h3 id="toc"> Types of Channels</h3>
There are a few different types of channels in Go. Each of them have different benefits and drawbacks.

<h4 id="uc"> Unbuffered Channels</h4>
```go
  // Unbuffered channels are the simplest type of channel.
  ch := make(chan int)
```

To create an unbuffered channel you call the `make` function, supplying the channel type. Do **not** provide a size value in the second argument as seen in the example above and voila! You have an unbuffered channel.

As described in [the previous section](https://benjiv.com/go-native-concurrency-primitives/#how-do-channels-work-in-go) , unbuffered channels are block by default, and will block the go routine until there is something to read or write.

<h4  id="bc"> Buffered Channels</h4>
```go
  // Buffered channels are the other primary type of channel.
  ch := make(chan int, 10)
```

To create a buffered channel you call the `make` function, supplying the channel type and the size of the buffer. The example above will create a channel with a buffer of size 10. If you attempt to write to a channel that is full it will block the go routine until there is room in the buffer. If you try to read from a channel that is empty it will block the go routine until there is something to read.

**If however you want to write to the channel and the buffer has space available it will NOT block the go routine.**

>  **NOTE:** In general, only use buffered channels when you *absolutely* need to. **Best practice is to use unbuffered channels.**

<h4 id="rowoc"> Read-Only & Write-Only Channels</h4>
One interesting use case for channels is to have a channel that is only used for reading or writing. This is useful for when you have a go routine that needs to read from a channel but you do not want the routine write to it, or vice versa. This is particularly useful for the [Owner Pattern](https://benjiv.com/go-native-concurrency-primitives/#owner-pattern) described below.

This is the syntax for creating a read-only or write-only channel.

```go
  // Define the variable with var
  var writeOnly chan<- int
  var readOnly <-chan int

  mychan := make(chan int)

  // Assign the channel to the variable
  readOnly = mychan
  writeOnly = mychan
```

The arrows indicate the direction of the channel. The arrow before `chan` is meant to indicate the flow of data is *into* the channel whereas the arrow after `chan` is meant to indicate the flow of data is *out of* the channel.

An example of a read-only channel is the `time.Tick` method:

```go
  // Tick is a convenience wrapper for NewTicker providing access to the ticking
  // channel only
  func Tick(d Duration) <-chan Time
```

This method returns a read-only channel which the `time` package writes to internally at the specified interval. This pattern ensures that the implementation logic of ticking the clock is isolated to the `time` package since the user does not need to be able to write to the channel.

Write-only channels are useful for when you need to write to a channel but you know the routine does not need to read from it. A great example of this is the [Owner Pattern](https://benjiv.com/go-native-concurrency-primitives/#owner-pattern) described below.

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h3 id="dcfc"> Design Considerations for Channels</h3>
It is important to think about the use of channels in your application.

Design Considerations include:

1. Which scope *owns* the channel?
2. What capabilities do non-owners have?
   1. Full ownership
   2. Read-Only
   3. Write-Only
3. How will the channel be cleaned up?
4. Which go routine is responsible for cleaning up the channel?

<h4 id="op"> Owner Pattern</h4>
The Owner Pattern is a common design pattern in Go and is used to ensure that ownership of a channel is correctly managed by the creating or owning routine. This allows for a routine to manage the full lifecycle of a channel and ensure that the channel is properly closed and the routine is cleaned up.

Here is an example of the Owner Pattern in Go:

```go
func NewTime(ctx context.Context) <-chan time.Time {
  tchan := make(chan time.Time)

  go func(tchan chan<- time.Time) {
    defer close(tchan)

    for {
      select {
      case <-ctx.Done():
        return
      case tchan <- time.Now():
      }
    }
  }(tchan)

  return tchan
}
```

**Benefits:**

- NewTime Controls the channel instantiation and cleanup (Lines 2, and 5)
- Enforces good hygiene by defining read-only/write-only boundaries
- Limits possibility of inconsistent behavior

Important notes about this example. The `ctx` context is passed to the function `NewTime` and is used to signal the routine to stop. The `tchan` channel is a normal unbuffered channel but is returned as read-only.

When passed to the internal Go routine, the `tchan` channel is passed as a write-only channel. Because the internal Go routine is supplied with a write-only channel it has the responsibility to close the channel when it is done.

With the use of the `select` statement the `time.Now()` call is executed only on a read from the channel. This ensures that the execution of the `time.Now()` call is synchronized with the read from the channel. This type of pattern helps minimize CPU cycles pre-emptively.

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h3 id="loc"> Looping over Channels</h3>
One method of reading from a channel is to use a `for` loop. This can be useful in some cases.

```go
  var tchan <-chan time.Time

  for t := range tchan {
    fmt.Println(t)
  }
```

There are a couple of reasons I do not recommend this approach. First, there is no guarantee that the channel will be closed (breaking the loop). Second, the loop does not adhere to the context meaning that if the context is canceled the loop will never exit. **This second point is especially important because there is no graceful way to exit the routine.**

Instead of looping over the channel I recommend the following pattern where you use a infinite loop with a `select` statement. This pattern ensures that the context is checked and if it is canceled the loop exits, while also allowing the loop to still read from the channel.

```go
  var tchan <-chan time.Time

  for {
    select {
    case <-ctx.Done(): // Graceful exit
      return
    case t, ok := <-tchan: // Read from the time ticker
      if !ok { // Channel closed, exit
        return
      }
      fmt.Println(t)
    }
  }
```

I discuss this method and the `select` statement in more detail in the [Select Statement](https://benjiv.com/go-native-concurrency-primitives/#select-statements) section.

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h3 id="fc"> Forwarding Channels</h3>
Forwarding channels from one to another can also be a useful pattern in the right circumstances. This is done using the `<- <-` operator.

Here is an example of forwarding one channel into another:

```go
func forward(ctx context.Context, from <-chan int) <-chan int {
  to := make(chan int)

  go func() {
    for {
      select {
      case <-ctx.Done():
        return
      case to <- <-from: // Forward from into the to channel
      }
    }
  }()

  return to
}
```

>  **NOTE:** Using this pattern you are unable to detect when the `from` channel is closed. This means that the `from` channel will continually send data to the `to` channel and the internal routine will never exit causing a flood of zero value data and a leaking routine.

Depending on your use case this could be desirable, however, it is important to note that this pattern is not a good idea when you need to detect a closed channel.

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h2 id="ss"> Select Statements</h2>
The `select` statement allows for the management of multiple channels in a Go application and can be used to trigger actions, manage data, or otherwise create logical concurrent flow.

```go
select {
case data, ok := <- incoming: // Data Read
  if !ok {
    return
  }

  // ...

case outgoing <- data: // Data Write
  // ...

default: // Non-blocking default action
  // ... 
}
```

> One important caveat to the `select` statement is that it is *stochastic* in nature. Meaning that if there are multiple channels that are ready to be read from or written to at the same time, the `select` statement will randomly choose one of the case statement to execute.[18](https://benjiv.com/go-native-concurrency-primitives/#fn:18)

<h3 id="tss"> Testing Select Statements</h3>
The stochastic nature of the select statement can make testing select statements a bit tricky, especially when testing to ensure that a context cancellation properly exits the routine.

[Here is an example](https://github.com/devnw/plex/blob/2d4f8fe223ab71f488d2d6f5e3dcfad77250d28d/plex_test.go#L202) of how to test the select statement using a statistical test where the number of times the test executes ensures that there is a low statistical likelihood of the test failing. This allows for additional coverage and ensures that the test is not flaky.

This test works by running the same cancelled context through a parallel routine 100 times with only one of the two contexts having been cancelled. In this situation there is always a consumer of the channel so there is a 50% likelyhood each time the loop runs that the [context case](https://github.com/devnw/plex/blob/2d4f8fe223ab71f488d2d6f5e3dcfad77250d28d/plex.go#L239) will be executed.

By running 100 times with a 50% chance of the select tripping the context case there is a very, very low chance that the test will fail to detect the context cancellation for *all* of the 100 tests.

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

<h3 id="wcwc"> Work Cancellation with Context</h3>
In the early days of building Go applications users were building out applications with a `done` channel where they would create a channel that looked like this: `done := make(chan struct{})`. This was a very simple way to signal to a routine that it should exit because all you have to do is close the channel and use that as a signal to exit.

```go
// Example of a simple done channel
func main() {
  done := make(chan struct{})

    
  go doWork(done)

  go func() {
    // Exit anything using the done channel
    defer close(done)

    // Do some more work
  }()

  <-done
}

func doWork(done <-chan struct{}) {
  for {
    select {
    case <-done:
      return
    default: 
      // ...
    }
  }
}
```

This pattern became so ubiquitous that the Go team created the [context package](https://golang.org/pkg/context/) as a replacement. This package provides an interface `context.Context` that can be used to signal to a routine that it should exit when listening to the returned read-only channel of the `Done` method.

```go
  import "context"

  func doWork(ctx context.Context) {
    for {
      select {
      case <-ctx.Done():
        return
      default: 
        // ...
    }
  }
}
```

Along with this they provided a few methods for creating hierarchical contexts, timeout contexts, and a context that can be cancelled.

- `context.WithCancel`
  - Returns a `context.Context` as well as a `context.CancelFunc` function literal that can be used to cancel the context.
- `context.WithTimeout`
  - Same returns as `WithCancel` but with a background timeout that will cancel the context after the specified `time.Duration` has elapsed.
- `context.WithDeadline`
  - Same returns as `WithCancel` but with a background deadline that will cancel the context after the specified `time.Time` has passed.

>
> **BEST PRACTICE:**
> The first parameter of a function that accepts a context should ***always*** be the context, and it should be named `ctx`.

[*Back To Top*](https://benjiv.com/go-native-concurrency-primitives/#top)

---

1. [Programming Language Primitives are the simplest elements of a language](https://en.wikipedia.org/wiki/Language_primitive)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:1)
2. [Don’t communicate by sharing memory, share memory by communicating.](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=2m48s)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:2)
3. [Share Memory By Communicating](https://go.dev/blog/codelab-share)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:3)
4. [Concurrency is not Parallelism by Rob Pike](https://youtu.be/oV9rvDllKEg)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:4)
5. [Concurrent engineering](https://en.wikipedia.org/wiki/Concurrent_engineering)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:5)
6. [Bell Labs and CSP Threads](https://swtch.com/~rsc/thread/)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:6)
7. [Communicating Sequential Processes by Hoare 1978](https://www.cs.cmu.edu/~crary/819-f09/Hoare78.pdf)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:7)
8. [Newsqueak: A Language for Communicating with Mice - Rob Pike](https://swtch.com/~rsc/thread/newsqueak.pdf)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:8)
9. [Introduction to Concurrent Programming - Rob Pike](http://herpolhode.com/rob/lec1.pdf)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:9)
10. [Communication - Go Proverbs by Rob Pike](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=2m48s)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:10)
11. [TTL (Time To Live) Cache Implementation for Go](https://github.com/devnw/ttl)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:11)
12. [Channels Vs Mutex - Rob Pike](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=4m20s)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:12)
13. [Goroutine Lifetimes](https://github.com/golang/go/wiki/CodeReviewComments#goroutine-lifetimes)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:13)
14. [Minimum Stack Size of a Go Routine](https://github.com/golang/go/blob/8f2db14cd35bbd674cb2988a508306de6655e425/src/runtime/stack.go#L72)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:14)
15. [Don’t Panic](https://github.com/golang/go/wiki/CodeReviewComments#dont-panic)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:15)
16. [Defer, Panic, and Recover](https://go.dev/blog/defer-panic-and-recover)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:16)
17. [Channels orchestrate; mutexes serialize](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=4m20s)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:17)
18. [Stochasticity of the Select statement](https://github.com/golang/go/blob/6178d25fc0b28724b1b5aec2b1b74fc06d9294c7/src/runtime/select.go#L177)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:18)