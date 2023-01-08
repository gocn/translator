- 原文地址：https://teivah.medium.com/profiling-and-execution-tracing-in-go-a5e646970f5b
- 原文作者：Teiva Harsanyi
- 本文永久链接：https://github.com/gocn/translator/edit/master/2022/w53_Profiling_and_Execution_Tracing_in_Go.md
- 译者：[Fivezh](https://github.com/fivezh)
- 校对：[]()

# Go 中的性能分析和执行跟踪

![img](../static/images/2022/w53_Profiling_and_Execution_Tracing_in_Go/11.webp)

Go 提供了一些优秀的诊断工具来帮助我们深入分析应用程序的执行情况。 这篇文章核心关注点是：分析和执行跟踪器。 这两个工具都非常重要，它们应该成为任何对优化感兴趣的 Go 开发人员的核心工具集的一部分。 首先，我们来讨论下性能分析。

# 性能分析 Profiling

分析工具提供了对应用程序执行的洞察力。 它使我们能够解决性能问题、检测竞争、定位内存泄漏等。 这些信息可以通过几个分析工具来收集：

- `CPU`— 确定应用程序的时间花在了哪里
- `Goroutine`— 报告正在运行的 goroutines 堆栈跟踪
- `Heap`— 报告堆内存分配以监视当前内存使用情况并检查可能的内存泄漏
- `Mutex`— 报告锁争情况来分析代码中互斥锁使用行为以及应用程序是否在锁定调用上花费了太多时间
- `Block`— 显示 goroutines 阻塞等待同步原语的位置

性能分析是通过 `分析器(profiler)` 工具进行检测来实现的，在 Go 中使用称为 `pprof`。 首先，让我们了解如何和何时启用 `pprof`，然后再讨论最关键的配置分析类型。

## 开启 pprof

有几种方法可以启用 `pprof`。 例如，我们可以使用 `net/http/pprof` 包通过 HTTP 提供分析数据：

```
package main

import (
    "fmt"
    "log"
    "net/http"
    _ "net/http/pprof" // Blank import to pprof
)

func main() {
    // Exposes an HTTP endpoint
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "")
    })
    log.Fatal(http.ListenAndServe(":80", nil))
}
```

导入 `net/http/pprof` 的作用是，我们可以通过`http://host/debug/pprof` 来访问 pprof。 请注意，即使在生产环境中启用 `pprof` 也是安全的 (https://go.dev/doc/diagnostics#profiling)。 影响性能的分析，比如 CPU 分析，默认情况下是不启用的，也不会连续运行。它们仅在特定时间段内被激活。

现在我们已经了解了如何公开 `pprof` 访问路由，接下来讨论最常见的几种分析。

## CPU 分析

CPU 分析器依赖于操作系统和信号。 当它被激活时，应用程序默认通过 `SIGPROF` 信号要求操作系统每 10 毫秒中断一次。 当应用程序收到 `SIGPROF` 时，它会暂停当前活动并将执行转移到分析器。 分析器收集诸如当前 goroutine 活动之类的数据，并汇总可以检索的执行统计信息；然后停止分析并继续执行直到下一次的 `SIGPROF`。

我们可以访问 [/debug/pprof/profile](https://teivah.medium.com/debug/pprof/profile) 路由来激活 CPU 分析。 默认情况下，访问此路由会执行 30 秒的 CPU 分析。 在 30 秒内，我们的应用程序每 10 毫秒中断一次。 请注意，可以更改这两个默认值：使用 `seconds` 参数将分析应该持续多长时间传递给路由（例如 [/debug/pprof/profile?seconds=15](https://teivah.medium.com/debug/pprof/profile?seconds=15)），也可以更改中断率（甚至小于 10 毫秒）。 但多数情况下，10 毫秒应该足够了，在减小这个值（意味着增加频率）时，我们应该注意不要对性能产生影响。 30 秒后，就可以下载 CPU 分析器的结果。

**注意：** 也可以通过  `-cpuprofile` 标志来开启 CPU 分析器，比如在运行基准测试时就可以用这种方式。 例如，执行以下命令后可通过 `/debug/pprof/profile` 下载到相同的分析结果文件。

```
$ go test -bench=. -cpuprofile profile.out
```

从这个文件，我们可以使用 `go tool` 来查看结果分析：

```
$ go tool pprof -http=:8080 <file>
```

此命令会打开一个显示调用图的 Web UI。 图 1 显示了一个示例。 箭头越大，这条分支就越是热路径。 通过可以分析此图表就可以进一步分析程序的执行情况。

![img](../static/images/2022/w53_Profiling_and_Execution_Tracing_in_Go/12.webp)

**图1:** 程序在30秒内的调用图

例如，图2 中的图表告诉我们，在 30 秒内，`*FetchResponse` 接收者的`decode`方法花费了 0.06 秒。 在这 0.06 秒中，0.02 秒用于`RecordBatch.decode`，0.01 秒用于`makemap`（创建一个map）。

![img](../static/images/2022/w53_Profiling_and_Execution_Tracing_in_Go/13.webp)

**图2:** 调用图示例

我们还可以从具有不同表示形式的 Web UI 访问此类信息。 例如，Top 视图按执行时间对函数进行排序，而 Flame Graph 可视化执行时间层次结构。 UI 甚至可以逐行显示源代码中执行最耗时的部分。

**注意:** *我们还可以通过命令行深入分析数据。 然而，这篇文章中专注于 Web UI。*

多亏了这些数据，我们可以大致了解应用程序的行为方式：

- 对 runtime.mallogc 的调用过多，意味着我们可以尝试减少过多的小堆分配。
- 在通道操作或互斥锁上花费太多时间，可能表明过度竞争正在损害应用程序的性能。
- 在 `syscall.Read` 或 `syscall.Write` 上花费太多时间，意味着应用程序在内核模式下花费了大量时间。 处理 I/O 缓冲可能是改进的途径。

这些是可以从 CPU 分析器中获得的信息。 了解最频繁的代码路径和识别程序瓶颈是很有价值，但它不会确定超过特定频率，因为 CPU 分析器是以固定速度执行分析的（默认情况下为 10 毫秒）。 为了获得更细粒度的分析数据，我们应该使用跟踪器(`tracing`)，将在本文后面讨论。

**注意:** *我们还可以为不同的功能附加标签。 例如，想象一个从不同客户端调用的通用函数，要跟踪两个客户端花费的时间，可以使用 pprof.Labels。*

## 堆分析

堆分析允许我们获得有关当前堆使用情况的统计信息。 与 CPU 分析一样，堆分析也是基于采样的。 可以改变采样频率，但不应该过于细化，因为采样频率提升越多，堆分析收集数据所需的额外工作就越多。 默认情况下，样本在每 512 KB 堆分配一次就执行一次。

访问 [/debug/pprof/heap/](https://teivah.medium.com/debug/pprof/heap/)，会得到难以阅读的原始数据。 但是，可以使用 [/debug/pprof/heap/?debug=0](https://teivah.medium.com/debug/pprof/heap/?debug=0) 下载堆分析文件，然后使用  `go tool`（与上一节中的命令相同）打开，就可以使用 Web UI 来分析数据。

图3 显示了堆图的示例。 调用`MetadataResponse.decode`方法会导致分配 1536 KB 的堆数据（占总堆的 6.32%）。 但是，这 1536 KB 中有 0 块是由该函数直接分配的，因此我们需要检查第二层的调用。 `TopicMetadata.decode` 方法分配了 1536 KB 中的 512 KB； 其余的——1024 KB——是用另一种方法分配的。

![img](../static/images/2022/w53_Profiling_and_Execution_Tracing_in_Go/14.webp)

**图3:** 堆分配图示

This is how we can navigate the call chain to understand what part of an application is responsible for most of the heap allocations. We can also look at different sample types:

- `alloc_objects`— Total number of objects allocated
- `alloc_space`— Total amount of memory allocated
- `inuse_objects` — Number of objects allocated and not yet released
- `inuse_space`— Amount of memory allocated and not yet released

Another very helpful capability with heap profiling is tracking memory leaks. With a GC-based language, the usual procedure is the following:

1. Trigger a GC.
2. Download heap data.
3. Wait for a few seconds/minutes.
4. Trigger another GC.
5. Download another heap data.
6. Compare.

Forcing a GC before downloading data is a way to prevent false assumptions. For example, if we see a peak of retained objects without running a GC first, we cannot be sure whether it’s a leak or objects that the next GC will collect.

Using `pprof`, we can download a heap profile and force a GC in the meantime. The procedure in Go is the following:

1. Go to [/debug/pprof/heap?gc=1](https://teivah.medium.com/debug/pprof/heap?gc=1) (trigger the GC and download the heap profile).
2. Wait for a few seconds/minutes.
3. Go to [/debug/pprof/heap?gc=1](https://teivah.medium.com/debug/pprof/heap?gc=1) again.
4. Use go tool to compare both heap profiles:

```
$ go tool pprof -http=:8080 -diff_base <file2> <file1>
```

Figure 4 shows the kind of data we can access. For example, the amount of heap memory held by the `newTopicProducer` method (top left) has decreased (–513 KB). In contrast, the amount held by `updateMetadata` (bottom right) has increased (+512 KB). Slow increases are normal. The second heap profile may have been calculated in the middle of a service call, for example. We can repeat this process or wait longer; the important part is to track steady increases in allocations of a specific object.

![img](https://miro.medium.com/max/1400/1*Y7TZjGIdxWSJJN9X4rOmjA.png)

**Figure 4:** The differences between the two heap profiles

**NOTE:** *Another type of profiling related to the heap is* `allocs`*, which reports allocations. Heap profiling shows the current state of the heap memory. To get insights about past memory allocations since the application started, we can use allocations profiling. As discussed, because stack allocations are cheap, they aren’t part of this profiling, which only focuses on the heap.*

## Goroutine 分析

The `goroutine` profile reports the stack trace of all the current goroutines in an application. We can download a file using [/debug/pprof/goroutine/?debug=0](https://teivah.medium.com/debug/pprof/goroutine/?debug=0) and use go tool again. Figure 5 shows the kind of information we can get.

![img](https://miro.medium.com/max/1400/1*aDyJKIuEXYHIXRsXkptYZA.png)

**Figure 5:** Goroutine graph

We can see the current state of the application and how many goroutines were created per function. In this case, `withRecover` has created 296 ongoing goroutines (63%), and 29 were related to a call to `responseFeeder`.

This kind of information is also beneficial if we suspect goroutine leaks. We can look at goroutine profiler data to know which part of a system is the suspect.

## Block Profiling

The `block` profile reports where ongoing goroutines block waiting on synchronization primitives. Possibilities include

- Sending or receiving on an unbuffered channel
- Sending to a full channel
- Receiving from an empty channel
- Mutex contention
- Network or filesystem waits

Block profiling also records the amount of time a goroutine has been waiting and is accessible via [/debug/pprof/block](https://teivah.medium.com/debug/pprof/block). This profile can be extremely helpful if we suspect that performance is being harmed by blocking calls.

The `block` profile isn’t enabled by default: we have to call `runtime.SetBlockProfileRate` to enable it. This function controls the fraction of goroutine blocking events that are reported. Once enabled, the profiler will keep collecting data in the background even if we don’t call the [/debug/pprof/block endpoint](https://teivah.medium.com/debug/pprof/block endpoint). Let’s be cautious if we want to set a high rate so we don’t harm performance.

![img](https://miro.medium.com/max/1400/1*Pui8Qco3znI5_2dVV94k-Q.png)

**NOTE:** *If we face a deadlock or suspect that goroutines are in a blocked state, the full goroutine stack dump (*[*/debug/pprof/goroutine/?debug=2*](https://teivah.medium.com/debug/pprof/goroutine/?debug=2)*) creates a dump of all the current goroutine stack traces. This can be helpful as a first analysis step. For example, the following dump shows a Sarama goroutine blocked for 1,420 minutes on a channel-receive operation:*

```
goroutine 2494290 [chan receive, 1420 minutes]:
github.com/Shopify/sarama.(*syncProducer).SendMessages(0xc00071a090,
[CA]{0xc0009bb800, 0xfb, 0xfb})
    /app/vendor/github.com/Shopify/sarama/sync_producer.go:117 +0x149
```

![img](https://miro.medium.com/max/1400/1*Pui8Qco3znI5_2dVV94k-Q.png)

## Mutex 互斥锁分析

The last profile type is related to blocking but only regarding mutexes. If we suspect that our application spends significant time waiting for locking mutexes, thus harming execution, we can use mutex profiling. It’s accessible via [/debug/pprof/mutex](https://teivah.medium.com/debug/pprof/mutex).

This profile works in a manner similar to that for blocking. It’s disabled by default: we have to enable it using `runtime.SetMutexProfileFraction`, which controls the fraction of mutex contention events reported.

Following are a few additional notes about profiling:

- We haven’t mentioned the `threadcreate` profile because it’s been broken since 2013 (https://github.com/golang/go/issues/6104).
- Be sure to enable only one profiler at a time: for example, do not enable CPU and heap profiling simultaneously. Doing so can lead to erroneous observations.
- `pprof` is extensible, and we can create our own custom profiles using `pprof.Profile`.

We have seen the most important profiles that we can enable to help us understand how an application performs and possible avenues for optimization. In general, enabling `pprof` is recommended, even in production, because in most cases it offers an excellent balance between its footprint and the amount of insight we can get from it. Some profiles, such as the CPU profile, lead to performance penalties but only during the time they are enabled.

Let’s now look at the execution tracer.

# 执行跟踪器（Execution Tracer）

The execution tracer is a tool that captures a wide range of runtime events with `go tool` to make them available for visualization. It is helpful for the following:

- Understanding runtime events such as how the GC performs
- Understanding how goroutines execute
- Identifying poorly parallelized execution

Let’s try it with an example given the [Concurrency isn’t Always Faster in Go](https://medium.com/@teivah/concurrency-isnt-always-faster-in-go-de325168907c) post. We discussed two parallel versions of the merge sort algorithm. The issue with the first version was poor parallelization, leading to the creation of too many goroutines. Let’s see how the tracer can help us in validating this statement.

We will write a benchmark for the first version and execute it with the -trace flag to enable the execution tracer:

```
$ go test -bench=. -v -trace=trace.out
```

![img](https://miro.medium.com/max/1400/1*Pui8Qco3znI5_2dVV94k-Q.png)

**NOTE:** We can also download a remote trace file using the [/debug/pprof/ trace?debug=0](https://teivah.medium.com/debug/pprof/ trace?debug=0) pprof endpoint.

![img](https://miro.medium.com/max/1400/1*Pui8Qco3znI5_2dVV94k-Q.png)

This command creates a trace.out file that we can open using go tool:

```
$ go tool trace trace.out
2021/11/26 21:36:03 Parsing trace...
2021/11/26 21:36:31 Splitting trace...
2021/11/26 21:37:00 Opening browser. Trace viewer is listening on
    http://127.0.0.1:54518
```

The web browser opens, and we can click View Trace to see all the traces during a specific timeframe, as shown in figure 6. This figure represents about 150 ms. We can see multiple helpful metrics, such as the goroutine count and the heap size. The heap size grows steadily until a GC is triggered. We can also observe the activity of the Go application per CPU core. The timeframe starts with user-level code; then a “stop the
world” is executed, which occupies the four CPU cores for approximately 40 ms.

![img](https://miro.medium.com/max/1400/1*pjaPOfbf0IkQyGk3WMu-dg.png)

**Figure 6:** Showing goroutine activity and runtime events such as a GC phase

Regarding concurrency, we can see that this version uses all the available CPU cores on the machine. However, figure 7 zooms in on a portion of 1 ms. Each bar corresponds to a single goroutine execution. Having too many small bars doesn’t look right: it means execution that is poorly parallelized.

![img](https://miro.medium.com/max/1400/1*IfFZHlK-AgO9XtBD3v23CA.png)

**Figure 7:** Too many small bars mean poorly parallelized execution

Figure 8 zooms even closer to see how these goroutines are orchestrated. Roughly 50% of the CPU time isn’t spent executing application code. The white spaces represent the time the Go runtime takes to spin up and orchestrate new goroutines.

![img](https://miro.medium.com/max/1400/1*1upoAIA1TXjPX0ugz8wsEg.png)

**Figure 8:** About 50% of CPU time is spent handling goroutine switches

Let’s compare this with the second parallel implementation, which was about an order of magnitude faster. Figure 9 again zooms to a 1 ms timeframe.

![img](https://miro.medium.com/max/1400/1*PLJRdGUNGRqeso9ZLKXG1g.png)

**Figure 9:** The number of white spaces has been significantly reduced, proving that the CPU is more fully occupied.

Each goroutine takes more time to execute, and the number of white spaces has been significantly reduced. Hence, the CPU is much more occupied executing application code than it was in the first version. Each millisecond of CPU time is spent more efficiently, explaining the benchmark differences.

Note that the granularity of the traces is per goroutine, not per function like CPU profiling. However, it’s possible to define user-level tasks to get insights per function or group of functions using the `runtime/trace` package.

For example, imagine a function that computes a Fibonacci number and then writes it to a global variable using atomic. We can define two different tasks:

```
var v int64
// Creates a fibonacci task
ctx, fibTask := trace.NewTask(context.Background(), "fibonacci")
trace.WithRegion(ctx, "main", func() {
    v = fibonacci(10)
})
fibTask.End()

// Creates a store task
ctx, fibStore := trace.NewTask(ctx, "store")
trace.WithRegion(ctx, "main", func() {
    atomic.StoreInt64(&result, v)
})
fibStore.End()
```

Using `go tool`, we can get more precise information about how these two tasks perform. In the previous trace UI (figure 12.42), we can see the boundaries for each task per goroutine. In User-Defined Tasks, we can follow the duration distribution (see figure 10).

![img](https://miro.medium.com/max/1400/1*Ndr0ZNXLY7qyxTPiWTcBSg.png)

**Figure 10:** Distribution of user-level tasks

We see that in most cases, the `fibonacci` task is executed in less than 15 microseconds, whereas the `store` task takes less than 6309 nanoseconds.

In the previous section, we discussed the kinds of information we can get from CPU profiling. What are the main differences compared to the data we can get from user-level traces?

- CPU profiling:
  – Sample-based
  – Per function
  – Doesn’t go below the sampling rate (10 ms by default)
- User-level traces:
  – Not sample-based
  – Per-goroutine execution (unless we use the `runtime/trace` package)
  – Time executions aren’t bound by any rate

In summary, the execution tracer is a powerful tool for understanding how an application performs. As we have seen with the merge sort example, we can identify poorly parallelized execution. However, the tracer’s granularity remains per goroutine unless we manually use `runtime/trace` compared to a CPU profile, for example. We can use both profiling and the execution tracer to get the most out of the standard Go diagnostics tools when optimizing an application.

![img](https://miro.medium.com/max/384/1*03RQSWDABp4MbzmPjlWK5A.png)

This post is taken from my book, [*100 Go Mistakes and How to Avoid Them*](https://www.manning.com/books/100-go-mistakes-and-how-to-avoid-them), which was released in August 2022 (mistake *#98*).

> 100 Go Mistakes and How to Avoid Them *shows you how to replace common programming problems in Go with idiomatic, expressive code. In it, you’ll explore dozens of interesting examples and case studies as you learn to spot mistakes that might appear in your own applications.*
>
> Save 35% with the code **au35har**.

Meanwhile, here’s the GitHub repository summarizing all the mistakes in the book: https://github.com/teivah/100-go-mistakes.