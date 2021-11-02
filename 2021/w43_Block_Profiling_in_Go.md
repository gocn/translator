***
- 原文地址：https://github.com/DataDog/go-profiler-notes/blob/main/block.md
- 原文作者：felixge
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w43_Block_Profiling_in_Go.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[]()
***

# Go中的阻塞分析

## 描述

Go 中的阻塞分析有助于您分析程序在等待下列阻塞操作上的花费时间：

- [select](https://github.com/golang/go/blob/go1.15.7/src/runtime/select.go#L511)
- [chan send](https://github.com/golang/go/blob/go1.15.7/src/runtime/chan.go#L279)
- [chan receive](https://github.com/golang/go/blob/go1.15.7/src/runtime/chan.go#L586)
- [semacquire](https://github.com/golang/go/blob/go1.15.7/src/runtime/sema.go#L150) ( [`Mutex.Lock`](https://golang.org/pkg/sync/#Mutex.Lock), [`RWMutex.RLock`](https://golang.org/pkg/sync/#RWMutex.RLock) , [`RWMutex.Lock`](https://golang.org/pkg/sync/#RWMutex.Lock), [`WaitGroup.Wait`](https://golang.org/pkg/sync/#WaitGroup.Wait))
- [notifyListWait](https://github.com/golang/go/blob/go1.15.7/src/runtime/sema.go#L515) ( [`Cond.Wait`](https://golang.org/pkg/sync/#Cond.Wait))

只有当 Go 通过将 goroutine 置于[等待](https://github.com/golang/go/blob/go1.15.7/src/runtime/runtime2.go#L51-L59)状态来暂停执行时，时间才会被跟踪。例如 `Mutex.Lock()`，如果锁可以立即或通过少量自旋被获得，那么这样的操作将不会出现在您的分析结果中。

上面的操作是 Go 运行时使用的[等待状态](https://github.com/golang/go/blob/go1.15.7/src/runtime/runtime2.go#L996-L1024)的子集，下面的操作**将不会**出现在分析文件中：

- [`time.Sleep`](https://golang.org/pkg/time/#Sleep)（但是 [`time.After`](https://golang.org/pkg/time/#After), [`time.Tick`](https://golang.org/pkg/time/#Tick) 和其他封装了channel的操作会显示出来）
- 垃圾回收
- 系统调用（例如[网络 I/O](https://github.com/DataDog/go-profiler-notes/tree/main/examples/block-net/)，文件 I/O 等）
- 运行时内部锁（例如 [stopTheWorld](https://github.com/golang/go/blob/go1.15.7/src/runtime/proc.go#L900)）
- [cgo](https://golang.org/cmd/cgo/) 阻塞调用
- 永远阻塞的事件（例如在 nil 通道上发送/接收）
- 阻止尚未完成的事件

在某些场景下， [Goroutine Profiling](https://github.com/gocn/translator/blob/master/2021/w40_Goroutine_Profiling_in_Go.md) (debug=2) 可能是阻塞分析的一个很好的文档，因为它涵盖了所有等待状态，并且可以显示尚未完成且正在进行的阻塞事件。

## 用法

阻塞分析器默认是被禁用的。您可以通过按下面方式通过传递 `rate > 0` 来启用它。

```
runtime.SetBlockProfileRate(rate)
```

参数 `rate` 会影响分析器的[精度](#精度)和[开销](#开销)。在文档中，rate 是这样描述的：

> SetBlockProfileRate 控制 goroutine 阻塞事件在阻塞分析中的比例。分析器旨在对每个阻塞事件耗时以纳秒级进行平均采样。
>
> 如果想要囊括全部的阻塞事件，可将 rate 置为 1。完全关闭则置为 0。

就个人而言，我很难理解第二句。我更喜欢这样描述 `rate`
（又名 `blockprofilerate`）：
- `rate <= 0` 完全禁用分析器（默认设置）
- `rate == 1` 跟踪每个阻塞事件，不论事件的 `duration` 是多少。
- `rate => 2` 设置纳秒采样率。每一个 `duration >= rate` 的事件都能被追踪到。对于 `duration < rate` 的事件，分析器将会[随机](https://github.com/golang/go/blob/go1.15.7/src/runtime/mprof.go#L408)采样 `duration / rate` 的事件。例如，假设您的事件耗时 `100ns` ，rate 值设为 `1000ns` ，那么事件就有 `10%` 的概率被分析器追踪。

阻塞持续时间在程序的整个生命周期内聚合（启用分析时）。要获取导致阻塞事件及其累积持续时间的当前堆栈信息的 [pprof 格式](https://github.com/gocn/translator/blob/master/2021/w39_go_profiler_notes_pprof_tool_format.md)的快照，您可以调用：

```go
pprof.Lookup("block").WriteTo(myFile, 0)
```

为了方便，你可以使用 [github.com/pkg/profile](https://pkg.go.dev/github.com/pkg/profile) 或 [net/http/pprof](https://golang.org/pkg/net/http/pprof/) 通过 http 查看分析，再或者使用[持续分析器](https://www.datadoghq.com/product/code-profiling/) 在生产环境中自动收集数据。

此外，您可以使用[`runtime.BlockProfile`](https://golang.org/pkg/runtime/#BlockProfile) API 以结构化格式获取相同的信息。

## 开销

当 `blockprofilerate` >= `10000` (10µs) 时，对生产环境应用的影响可以忽略不计，也包括那些争抢非常严重的应用。

### 实现细节

阻塞分析基本是在 Go 运行时内部实现的（有关代码，可以点击[描述](#描述)中的链接）。

```go
func chansend(...) {
  var t0 int64
  if blockprofilerate > 0 {
    t0 = cputicks()
  }
  // ... park goroutine in waiting state while blocked ...
  if blockprofilerate > 0 {
    cycles := cputicks() - t0
    if blocksampled(cycles) {
      saveblockevent(cycles)
    }
  }
}
```

这意味着如果您未启用阻塞分析，由于 CPU 分支预测，开销实际上是 0。

当开启阻塞分析时，每一个阻塞操作都会有两个 `cputicks()` 调用的开销。在 `amd64` 上，这是通过使用了 [RDTSC指令](https://en.wikipedia.org/wiki/Time_Stamp_Counter) 优化后的汇编来完成的，并且[在我的机器](https://github.com/felixge/dump/tree/master/cputicks)上花费了可忽略不计的 `~10ns/op` 。

根据设置的 `blockprofilerate`（在[精度](#精度)一节有更多相关内容），阻塞事件最终可能会被保存。这意味着堆栈跟踪信息被收集，此动作在[我的机器](https://github.com/felixge/dump/tree/master/go-callers-bench) 上耗时`~1µs`（堆栈深度=16）。通过增加相关 [`blockRecord`](https://github.com/golang/go/blob/go1.15.7/src/runtime/mprof.go#L133-L138) 计数和周期的方式，堆栈会作为键更新一个[内部哈希表](https://github.com/golang/go/blob/go1.15.7/src/runtime/mprof.go#L144)。

```go
type blockRecord struct {
	count  int64
	cycles int64
}
```

更新哈希表的开销大概和收集堆栈跟踪信息差不多，不过我还没测过。

### 基准

不管怎样，就您的应用程序开销而言，所有这些意味着什么？这通常意味着阻塞分析是**低开销**的。除非您的应用程序由于争用而花费几乎所有时间暂停和取消暂停 goroutine，这样的话即使对每个阻塞事件进行了采样，您也可能无法看到可衡量的影响。

话虽如此，下面的基准测试结果（详情见[Methodology](https://github.com/DataDog/go-profiler-notes/tree/main/bench/) ）会让您了解到阻塞分析在**理论最坏情况下**的开销。图  `chan(cap=0)` 展示了通过无缓冲通道发送消息时`blockprofilerate` 从 `1` 到 `1000` 的[工作负载](https://github.com/DataDog/go-profiler-notes/blob/main/bench/workload_chan.go) ，可看到吞吐量显著的下降。图 `chan(cap=128)` 使用的是缓冲通道，开销大大减少，所以对于不会将所有时间耗费在通道通信开销上的应用程序可能是无关紧要的。

值得注意的是，我无法基于负载看到[互斥锁](https://github.com/DataDog/go-profiler-notes/blob/main/bench/workload_mutex.go)的开销。我认为是互斥锁在争抢时在暂停 goroutine 之前使用的是自旋锁。如果有人对在 Go 中能表现出非自旋锁争抢的工作负载方面有好的想法，请告诉我！

无论如何，请记住，下图显示了专门设计用于触发您可以想象的最坏阻塞分析开销的工作负载。实际应用程序通常不会看到显着的开销，尤其是在使用 blockprofilerate>= 10000(10µs) 时。

<img src="https://github.com/gocn/translator/raw/master/static/images/2021_w43_Block_Profiling_in_Go/block_linux_x86_64.png" alt="block_linux_x86_64" style="zoom:80%;" />

### 内存使用情况

阻塞分析利用共享哈希表进行映射，即使表为空时也会[使用](https://github.com/golang/go/blob/go1.15.7/src/runtime/mprof.go#L207)  `1.4 MiB` 内存。除非您在程序中明确[禁用堆分析](https://twitter.com/felixge/status/1355846360562589696)，否则无论您是否使用了阻塞分析器，哈希表都会被分配内存。

此外，每个唯一的堆栈跟踪都会占用一些额外的内存。[`runtime.MemStats`](https://golang.org/pkg/runtime/#MemStats) 的 `BuckHashSys` 字段允许您在运行时检查使用情况。未来，我可能会尝试提供有关这方面的其他信息以及真实数据。

### 时间初始化

第一次调用 `runtime.SetBlockProfileRate()` 会耗费 `100ms`是因为它试图[测量](https://github.com/golang/go/blob/go1.15.7/src/runtime/runtime.go#L22-L47)挂钟和[TSC](https://en.wikipedia.org/wiki/Time_Stamp_Counter)时钟之间的速度比率。然而，最近关于异步抢占的更改[破坏](https://github.com/golang/go/issues/40653#issuecomment-766340860)了此代码，因此现在该调用耗时仅在 `~10ms`。

## 精度

### 采样偏差

在 Go 1.17 之前，阻塞分析器偏向于不频繁的长事件而不是频繁的短事件。一个[详细的分析](https://github.com/DataDog/go-profiler-notes/blob/main/block-bias.md)说明此问题。

### 时间戳计数器

`amd64` 和其他平台使用 [TSC](https://en.wikipedia.org/wiki/Time_Stamp_Counter) 实现了`cputicks()` 功能。这种技术历来受到频率缩放和其他类型 CPU 功率转换问题的挑战。现代 CPU 提供不变的 TSCs ，但是[仍有一些 Go 语言用户](https://github.com/golang/go/issues/16755#issuecomment-332279965)在提出该问题。我不知道这些是否是由于硬件损坏还是多路系统问题所引入的，但希望将来对此进行更多研究。

另请注意[时间初始化](#时间初始化)部分中的错误描述，可能会影响将 cputicks 转换为挂钟时间的精度。

### 堆栈深度

阻塞分析的最大堆栈深度为[32](https://github.com/golang/go/blob/go1.15.7/src/runtime/mprof.go#L31)。在更深的堆栈深度发生的阻塞事件仍将包含在阻塞分析中，但是结果数据可能就很难被处理了。

### 自旋锁

如前所述，存在争抢的 Go 互斥锁将先自旋一段时间，然后才服从调度器程序。如果自旋成功，阻塞事件就会跟踪不到。所以阻塞分析器更偏向于持续时间较长的事件。

🚧 本节需要更多的研究，我将在互斥分析器笔记中做这些研究。

## 与挂钟时间的关系

阻塞时间不受挂钟时间的限制。多个 goroutine 可以同时花费时间阻塞，这意味着分析中可以看到累积的阻塞持续时间超过程序运行时间。

## 与互斥分析的关系

Go 中的[互斥](https://github.com/DataDog/go-profiler-notes/blob/main/mutex.md)分析功能与阻塞分析功能重叠，似乎两者都可以用来理解互斥量争用。使用互斥分析器时，它会报告 `Unlock()` 的调用点，而阻塞分析中会报告 `Lock()` 的调用点。互斥量分析器还使用了更简单且可能是无偏的采样机制，这应该使其更准确。但是，互斥分析器不包括通道争用，因此阻塞分析器更灵活一些。当互斥和阻塞分析器都启用时，跟踪重复的争用事件可能会浪费一些开销。

🚧 本节需要更多的研究，我将在互斥分析器笔记中做这些研究。

## 分析器标签

阻塞分析器目前不支持[分析器标签](https://rakyll.org/profiler-labels/)，但这在未来很有可能被实现。

## pprof 输出

下面是一个以 [pprof 的 protobuf 格式](https://github.com/DataDog/go-profiler-notes/blob/1be84098ce82f7fbd66742e38c3d81e508a088f9/examples/block-sample/main.go)编码的阻塞分析示例。有两种值类型：

- contentions/count
- delay/nanoseconds

用于创建分析文件的`blockprofilerate` 没有包括在这里，也不属于[分析器标签](https://rakyll.org/profiler-labels/)。

```
$ go tool pprof -raw block.pb.gz 
PeriodType: contentions count
Period: 1
Time: 2021-02-08 14:53:53.243777 +0100 CET
Samples:
contentions/count delay/nanoseconds
      22820  867549417: 1 2 3 4 
      22748  453510869: 1 2 5 4 
Locations
     1: 0x10453af M=1 runtime.selectgo /usr/local/Cellar/go/1.15.6/libexec/src/runtime/select.go:511 s=0
     2: 0x10d082b M=1 main.simulateBlockEvents /Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/block-sample/main.go:71 s=0
     3: 0x10d0b72 M=1 main.eventB /Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/block-sample/main.go:57 s=0
             main.run.func2 /Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/block-sample/main.go:33 s=0
     4: 0x10d01b8 M=1 golang.org/x/sync/errgroup.(*Group).Go.func1 /Users/felix.geisendoerfer/go/pkg/mod/golang.org/x/sync@v0.0.0-20201207232520-09787c993a3a/errgroup/errgroup.go:57 s=0
     5: 0x10d0b12 M=1 main.eventA /Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/block-sample/main.go:53 s=0
             main.run.func1 /Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/block-sample/main.go:30 s=0
Mappings
1: 0x0/0x0/0x0   [FN]
```

## 历史

阻塞分析由 [Dmitry Vyukov](https://github.com/dvyukov)  [实现](https://codereview.appspot.com/6443115)，并首次出现在 [go1.1](https://golang.org/doc/go1.1) 版本 (2013-05-13) 中。

## 免责声明

我是 [felixge](https://github.com/felixge)，就职于 [Datadog](https://www.datadoghq.com/) ，主要工作内容为 Go 的[持续性能优化](https://www.datadoghq.com/product/code-profiling/) 。你应该了解下。我们也在[招聘](https://www.datadoghq.com/jobs-engineering/#all&all_locations): ).

本页面的信息可认为正确，但不提供任何保证。欢迎反馈！

