# go 中更加强大的 traces

- 原文地址：[More powerful Go execution traces](https://go.dev/blog/execution-traces-2024)
- 原文作者：Michael Knyszek
- 本文永久链接：<https://github.com/gocn/translator/blob/master/2024/w12_more_powerful_go_execution_traces.md>
- 译者：[小超人](https://github.com/xx1906)
- Go 版本: 1.22+

- [runtime/trace](https://go.dev/pkg/runtime/trace)包包含一个用于理解并且排查 go 程序问题的强大工具。通过这个功能我们可以跟踪每个
  goroutine 在一段时间内的执行情况。使用[`go tool trace` 命令](https://go.dev/pkg/cmd/trace)(或优秀的开源 ([gotraceui](https://gotraceui.dev/)工具) )
  ，可以对这些跟踪数据进行可视化处理和探索。

trace 的神奇之处在于轻松地揭秘程序，这是通过其他的方式是很难办到的。例如，如果没有执行采样，在 CPU 的 profile 文件中很难看到大量
goroutines 因为同一通道而阻塞的并发瓶颈。但在执行 trace 中，阻塞执行的情况会以惊人的清晰度显示出来，阻塞的 goroutines 堆栈 traces
会迅速指出罪魁祸首。

![](../static/images/2024/w12_more_powerful_go_execution_traces/gotooltrace.png)

Go开发者甚至可以使用[tasks](https://go.dev/pkg/runtime/trace#Task), [regions](https://go.dev/pkg/runtime/trace#WithRegion),
和 [logs](https://go.dev/pkg/runtime/trace#Log) 这些工具来观测自己的程序，从而将高层关注点与低层执行细节关联起来。

## 问题

遗憾的是，执行 trace 中的大量信息是被丢弃的。从历史上看，有四大问题阻碍了执行 trace 。

- trace 开销大。
- trace 不能很好地扩展，并且可能会变得太大而无法分析。
- 没有量化的指标确定从什么时候开始捕获程序中出现的一些不良的行为。
- 由于缺乏解析和解释执行 trace 的公共软件包，只有最具有探索精神的 gophers 才能通过编程分析 trace。

如果你在过去几年中有使用过 trace，那么你很可能会因为其中一个或多个问题而感到失望。但我们很高兴地告诉大家，在过去的两个 Go 版本中，我们在所有这四个方面都取得了很大的进步。

## 低成本 tracing

在 Go 1.21 之前，对于许多应用程序来说，trace 会占用 CPU 的 10-20% 的开销，这就限制了 trace 的使用场景，而不能像持续 CPU profileing 那样使用。
事实证明，trace 的大部分使用成本都来自于回溯。运行时产生的许多事件都附有 trace 的堆栈信息，这对于实际确定 goroutines 在执行过程中的关键时刻在做什么非常有价值。


得益于 Felix Geisendörfer 和 Nick Ripley 在优化回溯效率方面所做的工作，执行 trace 的 CPU 运行时开销已大幅降低，许多应用程序的
CPU 运行时开销已降至 1-2%。你可以在 Felix[Felix’s 的精彩博客](https://blog.felixge.de/reducing-gos-execution-tracer-overhead-with-frame-pointer-unwinding/)中阅读更多相关信息。

## 可扩展的 trace

trace 格式及其事件是围绕相对高效的排放来进行设计的，但需要工具来解析和保持整个 trace 的状态。分析一个几百兆的 trace 可能需要几个 G 的内存！

不幸的是，这个问题在生成 trace 的时候造成的。为了降低运行时开销，所有事件都被写入线程本地的缓冲区。但这意味着事件的出现顺序与真实顺序不符，因此 trace 工具就有责任弄清到底发生了什么。

要在保持较低开销的同时扩大 trace 范围，关键在于偶尔分割正在生成的 trace。每个分割点的行为有点像一次同时禁用并重新启用trace。到目前为止的所有trace数据将代表一个完整的、自成一体的trace，而新的 trace 数据将无缝地从原来的位置开始。

可以想象，要解决这个问题，[需要重新思考并重写trace运行时的基础工作](https://go.dev/issue/60773)。我们很高兴地宣布，这项工作已在 Go 1.22
中完成，并已普遍可用。重写带来了[很多很好的改进](https://go.dev/doc/go1.22#runtime/trace)，包括对
[`go tool trace` 命令](https://go.dev/doc/go1.22#trace)的一些改进。如果你想了解更多细节，请参阅[设计文档](https://github.com/golang/proposal/blob/master/design/60773-execution-tracer-overhaul.md)。

(备注：`go tool trace` 仍会将完整的 trace 加载到内存中，但对于 Go 1.22+ 程序生成的 trace 来说，[取消这一限制](https://go.dev/issue/65315)并且现在是可用的）。

## 黑匣子

假设你正在处理一项网络服务，而 RPC 耗时很长。你不能在知道 RPC 已经耗时很长时间时之后才开始跟踪，因为导致请求缓慢的根本原因已经过去了，而且没有被记录下来。

有一种技术可以帮助解决这个问题，叫做黑匣子，你可能已经在其他编程环境中熟悉了这种技术。黑匣子的原理是持续 tracing，并始终保持最新的跟踪数据，以防万一。然后，一旦有有趣的事情发生，程序就可以直接写出它所拥有的一切！

在 tracing 可以拆分之前，这几乎是不可能实现的。但是，由于连续跟踪的开销较低，而且运行时可以随时拆分跟踪，因此现在可以直接实现黑匣子。

因此，我们很高兴地宣布将在 [golang.org/x/exp/trace package](https://go.dev/pkg/golang.org/x/exp/trace#FlightRecorder)
软件包中提供实验性的黑匣子记录器。

请试用一下！下面是一个设置黑匣子用来记录长 HTTP 请求的示例，供你开始使用。

```
    
    fr := trace.NewFlightRecorder()
    fr.Start()

    
    var once sync.Once
    http.HandleFunc("/my-endpoint", func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        
        doWork(w, r)

        
        if time.Since(start) &gt; 300*time.Millisecond {
            
            once.Do(func() {
                
                var b bytes.Buffer
                _, err = fr.WriteTo(&amp;b)
                if err != nil {
                    log.Print(err)
                    return
                }
                
                if err := os.WriteFile("trace.out", b.Bytes(), 0o755); err != nil {
                    log.Print(err)
                    return
                }
            })
        }
    })
    log.Fatal(http.ListenAndServe(":8080", nil))
```

如果你有任何反馈意见，无论是正面的还是负面的，[proposal issue 63185](https://go.dev/issue/63185)都请与我们分享！

## trace reader API

在重写 trace 实现的同时，我们还努力重构其他 trace 内部结构，如 `go tool trace`。因此，我们尝试创建一个足以共享的 trace reader 
API，使 trace 更方便使用。

就像黑匣子一样，我们很高兴地宣布，我们也有一个实验性的 trace reader 的 API，希望与大家分享。[它和黑匣子在同一个软件包中](https://go.dev/pkg/golang.org/x/exp/trace#Reader)。

我们认为在此基础上进行开发已经足够好了，所以请试用一下！下面是一个示例，用于检测因为等待网络而阻塞的 goroutine 的比例。

```
    
    r, err := trace.NewReader(os.Stdin)
    if err != nil {
        log.Fatal(err)
    }

    var blocked int
    var blockedOnNetwork int
    for {
        
        ev, err := r.ReadEvent()
        if err == io.EOF {
            break
        } else if err != nil {
            log.Fatal(err)
        }

        
        if ev.Kind() == trace.EventStateTransition {
            st := ev.StateTransition()
            if st.Resource.Kind == trace.ResourceGoroutine {
                id := st.Resource.Goroutine()
                from, to := st.GoroutineTransition()

                
                if from.Executing(); to == trace.GoWaiting {
                    blocked++
                    if strings.Contains(st.Reason, "network") {
                        blockedOnNetwork++
                    }
                }
            }
        }
    }
    
    p := 100 * float64(blockedOnNetwork) / float64(blocked)
    fmt.Printf("%2.3f%% instances of goroutines blocking were to block on the network\n", p)
```

就像黑匣子一样，有一个[问题的提案](https://go.dev/issue/62627) 也是留下反馈意见的好地方！

Dominik Honnef 很早就试用了这个 API，并提供了很好的反馈，还为旧版本的 trace API 提供了支持。

## 谢谢！

这项工作的完成，在很大程度上要归功于诊断工作组成员[diagnostics working group](https://go.dev/issue/57175)
的帮助。诊断工作组在一年多之前成立，由 go 社区相关人员组成，并向公众开放。

在此，我们要向去年定期参加诊断会议的社区成员：Felix Geisendörfer、Nick Ripley、Rhys Hiltner、Dominik Honnef、Bryan
Boreham 和 thepudds 表示感谢。


你们的讨论、反馈和付出对我们取得今天的成绩起到了至关重要的作用。谢谢你们

## 引用

1. [gotraceui tool](https://gotraceui.dev/)
2. [rethinking and rewriting a lot of the foundation of the trace implementation](https://go.dev/issue/60773)
3. [trace tasks](https://go.dev/pkg/runtime/trace#Task)
4. [trace regions](https://go.dev/pkg/runtime/trace#WithRegion)
5. [trace logs](https://go.dev/pkg/runtime/trace#Log)
6. [felix’s great blog post](https://blog.felixge.de/reducing-gos-execution-tracer-overhead-with-frame-pointer-unwinding/)
7. [rethinking and rewriting a lot of the foundation of the trace implementation](https://go.dev/issue/60773)
8. [A lot of nice improvements](https://go.dev/doc/go1.22#runtime/trace)
9. [tracer design document](https://github.com/golang/proposal/blob/master/design/60773-execution-tracer-overhaul.md)
10. [1.22 removing this limitation](https://go.dev/issue/65315)