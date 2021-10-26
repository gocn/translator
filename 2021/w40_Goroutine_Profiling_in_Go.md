## Go 语言的 goroutine 性能分析

* 原文地址：https://github.com/DataDog/go-profiler-notes/blob/main/goroutine.md
* 原文作者：`felixge`
* 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w40_Goroutine_Profiling_in_Go.md

- 译者：[朱亚光](https://github.com/zhuyaguang)
- 校对：

⬅ [完整的 Go 性能分析和采集系列笔记戳这儿](https://github.com/DataDog/go-profiler-notes/blob/main/README.md)

本文档最后一次更新时所用的 Go版本是 1.15.6，但是大多数情况下，新老版本都适用。

## 描述

Go 运行时在一个称为 [allgs](https://github.com/golang/go/blob/3a778ff50f7091b8a64875c8ed95bfaacf3d334c/src/runtime/proc.go#L500) 简单切片追踪所有的 goroutines。这里面包含了活跃的和死亡的 goroutine 。死亡的 goroutine 保留下来，等到生成新的 goroutine 时重用。

Go 有各种 API 来监测 `allgs `中活跃的 goroutine 和这些 goroutines 当前的堆栈跟踪信息，以及各种其他属性。一些 API 将这些信息公开为统计摘要，而另外一些 API 则给每个单独的 goroutine 信息提供查询接口。

尽管 API 之间有差异，但是活跃的 goroutine 都有如下[共同](https://github.com/golang/go/blob/9b955d2d3fcff6a5bc8bce7bafdc4c634a28e95b/src/runtime/mprof.go#L729) [定义](https://github.com/golang/go/blob/9b955d2d3fcff6a5bc8bce7bafdc4c634a28e95b/src/runtime/traceback.go#L931)

-   非[死](https://github.com/golang/go/blob/go1.15.6/src/runtime/runtime2.go#L65-L71)
-   不是[系统 goroutine](https://github.com/golang/go/blob/9b955d2d3fcff6a5bc8bce7bafdc4c634a28e95b/src/runtime/traceback.go#L1013-L1021)，也不是 finalizer goroutine。

换句话说，正在运行的 goroutine 和那些等待  i/o、锁、通道、调度的 goroutine 一样，都被认为是活跃的。尽管人们可能会天真的认为后面那几种等待的 goroutine 是不活跃的。

## 开销

Go 中 所有可用的 goroutine 分析都需要一个 `O(N)` **stop-the-world** 阶段。这里的 `N` 是指已分配 goroutine 的数量。一个简单的[基准测试](https://github.com/felixge/fgprof/blob/fe01e87ceec08ea5024e8168f88468af8f818b62/fgprof_test.go#L35-L78) [表明](https://github.com/felixge/fgprof/blob/master/BenchmarkProfilerGoroutines.txt)，当使用 [runtime.GoroutineProfile()](https://golang.org/pkg/runtime/#GoroutineProfile) API时，每个goroutine 的世界会停止约1个µs。但是这个数字可能会随着诸如程序的平均堆栈深度、死掉的 goroutines 数量等因素的变化而波动。

根据经验，对于延迟非常敏感并使用数千个活跃 goroutine 的应用程序，在生产中使用 goroutine 分析可能需要谨慎一些。因此，对于包含大量的 goroutine ，甚至 Go 本身这样的应用程序来说，使用 goroutine 分析可能不是一个好主意。

大多数应用程序不会产生大量的 goroutine，并且可以容忍几毫秒的额外延迟，在生产中持续 goroutine 性能分析应该没有问题。

## Goroutine 属性

Goroutines 有很多[属性](https://github.com/golang/go/blob/go1.15.6/src/runtime/runtime2.go#L406-L486) 可以帮助调试 Go 应用程序。下面的属性非常有趣，并且可以通过文章后面描述的 API 不同程度地暴露。

-   [`goid`](https://github.com/golang/go/blob/go1.15.6/src/runtime/runtime2.go#L428): goroutine 的唯一 id， 主 goroutine 的 id 为`1`.
-   [`atomicstatus`](https://github.com/golang/go/blob/go1.15.6/src/runtime/runtime2.go#L14-L105): goroutine 的状态如下：
    -   `idle`: 刚分配
    -   `runnable`: 在运行队列上，等待调度
    -   `running`: 在操作系统线程上执行
    -   `syscall`: 在系统调用时阻塞
    -   `waiting`: 等待调度，见`g.waitreason`
    -   `dead`: 刚刚退出或被重新初始化
    -   `copystack`: 堆栈当前正在移动
    -   `preempted`: 抢占
-   [`waitreason`](https://github.com/golang/go/blob/go1.15.6/src/runtime/runtime2.go#L996-L1024):goroutine 等待的原因，比如 sleep、channel 操作、i/o、gc等等。
-   [`waitsince`](https://github.com/golang/go/blob/go1.15.6/src/runtime/runtime2.go#L430): goroutine 进入 `waiting` 或者 `syscall` 状态的大约时间戳，由等待启动后第一个 GC 确定。
-   [`labels`](https://github.com/golang/go/blob/go1.15.6/src/runtime/runtime2.go#L472): A set of key/value [profiler labels](https://rakyll.org/profiler-labels/) that can be attached to goroutines.
-   `stack trace`: 当前正在执行的函数及其调用者。要么是文件名、函数名和行号的纯文本输出，要么是程序计数器地址的一个切片(pcs)。 你也可以进一步研究更多的细节比如： 文件名、函数名和行号的纯文本可以转换成pcs吗？
-   [`gopc`](https://github.com/golang/go/blob/go1.15.6/src/runtime/runtime2.go#L466):  `go ...` 调用程序计数地址 (pc) 导致 goroutine 的创建。可以转换为文件、函数名和行号。
-   [`lockedm`](https://github.com/golang/go/blob/go1.15.6/src/runtime/runtime2.go#L460): 该 goroutine 的锁定的线程，如果有的话。

## 特征矩阵

下面的特征矩阵让你快速了解，调用这些 API 时，这些属性当前的可用性。也可以通过[谷歌表格](https://docs.google.com/spreadsheets/d/1txMRjhDA0NC9eSNRRUMMFI5uWJ3FBnACGVjXYT1gKig/edit?usp=sharing)获取。

[![goroutine feature matrix](https://github.com/DataDog/go-profiler-notes/raw/main/goroutine-matrix.png)](https://github.com/DataDog/go-profiler-notes/blob/main/goroutine-matrix.png)

## APIs

### [`runtime.Stack()`](https://golang.org/pkg/runtime/#Stack) / [`pprof.Lookup(debug=2)`](https://golang.org/pkg/runtime/pprof/#Lookup)

该 API 将返回非结构化文本输出，显示所有活动 goroutines 的堆栈信息以及上面特性矩阵中列出的属性。

`waitsince`属性包含了以分钟为单位的`nanotime() - gp.waitsince()`，但当持续时间超过1分钟。

pprof.Lookup(debug=2) 是如何使用 profile 简单的别名。实际调用是下面这样：

~~~go
profile := pprof.Lookup("goroutine")
profile.WriteTo(os.Stdout, 2)
~~~

简单调用下 `runtime.Stack()`就可以实现 profile 

下面是返回输出的截短示例，完整例子可以看 [2.runtime.stack.txt](https://github.com/DataDog/go-profiler-notes/blob/main/examples/goroutine/2.runtime.stack.txt) 

```shell
goroutine 1 [running]:
main.glob..func1(0x14e5940, 0xc0000aa7b0, 0xc000064eb0, 0x2)
/Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/goroutine/main.go:29 +0x6f
main.writeProfiles(0x2, 0xc0000c4008, 0x1466424)
/Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/goroutine/main.go:106 +0x187
main.main()
/Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/goroutine/main.go:152 +0x3d2

goroutine 22 [sleep, 1 minutes]:
time.Sleep(0x3b9aca00)
/usr/local/Cellar/go/1.15.6/libexec/src/runtime/time.go:188 +0xbf
main.shortSleepLoop()
/Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/goroutine/main.go:165 +0x2a
created by main.indirectShortSleepLoop2
/Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/goroutine/main.go:185 +0x35

goroutine 3 [IO wait, 1 minutes]:
internal/poll.runtime_pollWait(0x1e91e88, 0x72, 0x0)
/usr/local/Cellar/go/1.15.6/libexec/src/runtime/netpoll.go:222 +0x55
internal/poll.(*pollDesc).wait(0xc00019e018, 0x72, 0x0, 0x0, 0x1465786)
/usr/local/Cellar/go/1.15.6/libexec/src/internal/poll/fd_poll_runtime.go:87 +0x45
internal/poll.(*pollDesc).waitRead(...)
/usr/local/Cellar/go/1.15.6/libexec/src/internal/poll/fd_poll_runtime.go:92
internal/poll.(*FD).Accept(0xc00019e000, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0)
/usr/local/Cellar/go/1.15.6/libexec/src/internal/poll/fd_unix.go:394 +0x1fc

...
```

### [`pprof.Lookup(debug=1)`](https://golang.org/pkg/runtime/pprof/#Lookup)

该分析方法调用和`pprof.Lookup(debug=2)` 一样，但是会产生的数据却大相径庭：

-   不会列出单独的 goroutines 信息，把拥有相同堆栈信息和标签的 goroutines 和他们的数量一起列出。
-   包含了 pprof 标签，`debug=2`不包含标签。
-   Most other goroutine properties from `debug=2` are not included.
-   不包含`debug=2`中大多数 goroutine 属性。
-   输出格式也是基于文本的，但看起来与' debug=2 '非常不同。

下面是返回输出的截短示例，完整例子可以看 [2.pprof.lookup.goroutine.debug1.txt](https://github.com/DataDog/go-profiler-notes/blob/main/examples/goroutine/2.pprof.lookup.goroutine.debug1.txt) 

```shell
goroutine profile: total 9
2 @ 0x103b125 0x106cd1f 0x13ac44a 0x106fd81
# labels: {"test_label":"test_value"}
#0x106cd1etime.Sleep+0xbe/usr/local/Cellar/go/1.15.6/libexec/src/runtime/time.go:188
#0x13ac449main.shortSleepLoop+0x29/Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/goroutine/main.go:165

1 @ 0x103b125 0x10083ef 0x100802b 0x13ac4ed 0x106fd81
# labels: {"test_label":"test_value"}
#0x13ac4ecmain.chanReceiveForever+0x4c/Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/goroutine/main.go:177

1 @ 0x103b125 0x103425b 0x106a1d5 0x10d8185 0x10d91c5 0x10d91a3 0x11b8a8f 0x11cb72e 0x12df52d 0x11707c5 0x117151d 0x1171754 0x1263c2c 0x12d96ca 0x12d96f9 0x12e09ba 0x12e5085 0x106fd81
#0x106a1d4internal/poll.runtime_pollWait+0x54/usr/local/Cellar/go/1.15.6/libexec/src/runtime/netpoll.go:222
#0x10d8184internal/poll.(*pollDesc).wait+0x44/usr/local/Cellar/go/1.15.6/libexec/src/internal/poll/fd_poll_runtime.go:87
#0x10d91c4internal/poll.(*pollDesc).waitRead+0x1a4/usr/local/Cellar/go/1.15.6/libexec/src/internal/poll/fd_poll_runtime.go:92
#0x10d91a2internal/poll.(*FD).Read+0x182/usr/local/Cellar/go/1.15.6/libexec/src/internal/poll/fd_unix.go:159
#0x11b8a8enet.(*netFD).Read+0x4e/usr/local/Cellar/go/1.15.6/libexec/src/net/fd_posix.go:55
#0x11cb72dnet.(*conn).Read+0x8d/usr/local/Cellar/go/1.15.6/libexec/src/net/net.go:182
#0x12df52cnet/http.(*connReader).Read+0x1ac/usr/local/Cellar/go/1.15.6/libexec/src/net/http/server.go:798
#0x11707c4bufio.(*Reader).fill+0x104/usr/local/Cellar/go/1.15.6/libexec/src/bufio/bufio.go:101
#0x117151cbufio.(*Reader).ReadSlice+0x3c/usr/local/Cellar/go/1.15.6/libexec/src/bufio/bufio.go:360
#0x1171753bufio.(*Reader).ReadLine+0x33/usr/local/Cellar/go/1.15.6/libexec/src/bufio/bufio.go:389
#0x1263c2bnet/textproto.(*Reader).readLineSlice+0x6b/usr/local/Cellar/go/1.15.6/libexec/src/net/textproto/reader.go:58
#0x12d96c9net/textproto.(*Reader).ReadLine+0xa9/usr/local/Cellar/go/1.15.6/libexec/src/net/textproto/reader.go:39
#0x12d96f8net/http.readRequest+0xd8/usr/local/Cellar/go/1.15.6/libexec/src/net/http/request.go:1012
#0x12e09b9net/http.(*conn).readRequest+0x199/usr/local/Cellar/go/1.15.6/libexec/src/net/http/server.go:984
#0x12e5084net/http.(*conn).serve+0x704/usr/local/Cellar/go/1.15.6/libexec/src/net/http/server.go:1851

...
```

### [`pprof.Lookup(debug=0)`](https://golang.org/pkg/runtime/pprof/#Lookup)

该分析方法调用和`pprof.Lookup(debug=1)` 一样，并且产生的数据也一样。唯一的不同技术数据格式是 [pprof](https://github.com/DataDog/go-profiler-notes/blob/main/pprof.md) protocol buffer 格式。

下面是通过 `go tool pprof -raw` 命令返回输出的截短示例，完整例子可以看[2.pprof.lookup.goroutine.debug0.pb.gz](https://github.com/DataDog/go-profiler-notes/blob/main/examples/goroutine/2.pprof.lookup.goroutine.debug0.pb.gz) 

```shell
PeriodType: goroutine count
Period: 1
Time: 2021-01-14 16:46:23.697667 +0100 CET
Samples:
goroutine/count
          2: 1 2 3 
                test_label:[test_value]
          1: 1 4 5 6 
                test_label:[test_value]
          1: 1 7 8 9 10 11 12 13 14 15 16 17 18 19 20 
          1: 1 7 8 9 10 11 12 21 14 22 23 
                test_label:[test_value]
          1: 1 7 8 9 24 25 26 27 28 29 30 
          1: 1 31 32 
                test_label:[test_value]
          1: 1 2 33 
                test_label:[test_value]
          1: 34 35 36 37 38 39 40 41 
                test_label:[test_value]
Locations
     1: 0x103b124 M=1 runtime.gopark /usr/local/Cellar/go/1.15.6/libexec/src/runtime/proc.go:306 s=0
     2: 0x106cd1e M=1 time.Sleep /usr/local/Cellar/go/1.15.6/libexec/src/runtime/time.go:188 s=0
     3: 0x13ac449 M=1 main.shortSleepLoop /Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/goroutine/main.go:165 s=0
     4: 0x10083ee M=1 runtime.chanrecv /usr/local/Cellar/go/1.15.6/libexec/src/runtime/chan.go:577 s=0
     5: 0x100802a M=1 runtime.chanrecv1 /usr/local/Cellar/go/1.15.6/libexec/src/runtime/chan.go:439 s=0
     6: 0x13ac4ec M=1 main.chanReceiveForever /Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/goroutine/main.go:177 s=0
...
Mappings
1: 0x0/0x0/0x0   [FN]
```

### [`runtime.GoroutineProfile()`](https://golang.org/pkg/runtime/#GoroutineProfile)

该函数实际返回一个slice，包含了所有活跃 goroutines 和他们当前的堆栈跟踪信息。堆栈跟踪信息以函数地址的形式给出，可以使用[`runtime.CallersFrames()`](https://golang.org/pkg/runtime/#CallersFrames)将函数地址解析为函数名。

该方法被我的开源项目 [fgprof](https://github.com/felixge/fgprof) 用来实现挂钟分析。

下面的特性是不可用的，但是很期待在未来的 Go 项目中可能会被加入进去。

-   包含上面但是目前还不能使用的 goroutine 属性，特别是标签。
-   通过pprof标签过滤，这可以减少 stop-the-world ，但会需要额外的运行时内务。
-   将返回的 goroutine 的数量限制为一个随机子集，也可以减少 stop-the-world，而且可能比按标签过滤更容易实现。

下面是返回输出的截短示例，完整例子可以看 [2.runtime.goroutineprofile.json](https://github.com/DataDog/go-profiler-notes/blob/main/examples/goroutine/2.runtime.goroutineprofile.json) 。

~~~json
[
  {
    "Stack0": [
      20629256,
      20629212,
      20627047,
      20628306,
      17018153,
      17235329,
      ...
    ]
  },
  {
    "Stack0": [
      17019173,
      17222943,
      20628554,
      17235329,
      ...
    ]
  },
  ...
]
~~~



### [`net/http/pprof`](https://golang.org/pkg/net/http/pprof/)

这个包通过  HTTP endpoints 暴露上面描述的 [`pprof.Lookup("goroutine")`](https://golang.org/pkg/runtime/pprof/#Lookup) 分析结果，输出和上面 API 是一样的。

## 历史

Goroutine 性能分析是由 [Russ Cox](https://github.com/rsc) [实现](https://codereview.appspot.com/5687076/) ，第一次出现在 [2012-2-22的周例会上](https://golang.org/doc/devel/weekly.html#2012-02-22)，在 go1 之前发布。

## 免责声明

我是 [felixge](https://github.com/felixge)，就职于 [Datadog](https://www.datadoghq.com/) ，主要工作内容为 Go 的 [持续性能优化](https://www.datadoghq.com/product/code-profiling/)。你应该了解下。我们也在[招聘](https://www.datadoghq.com/jobs-engineering/#all&all_locations) : ).

本页面的信息可认为正确，但不提供任何保证。欢迎反馈！