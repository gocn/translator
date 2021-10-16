# Go's pprof tool & format
# go 中的 pprof 工具和格式

* 原文地址：https://github.com/DataDog/go-profiler-notes/blob/main/pprof.md
* 原文作者：`felixge`
* 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w39_go_profiler_notes_pprof_tool_format

- 译者：[小超人](https:/github.com/laxiaohong)
- 校对：

The various profilers built into Go are designed to work with the pprof visualization tool. [pprof](https://github.com/google/pprof) itself is an inofficial Google project that is designed to analyze profiling data from C++, Java and Go programs. The project defines a protocol buffer format that is used by all Go profilers and described in this document.

在 Go 中内置的几种分析器都是为使用 pprof 的可视化工具而设计的。[pprof](https://github.com/google/pprof) 本身不是谷歌的官方项目，pprof 一开始设计的目的是分析来自 c++、Java 和 Go 程序的数据。该项目使用 protocol buffer 协议定义了所有 Go 分析器的格式，本文都会对他们进行描述。

The Go project itself [bundles](https://github.com/golang/go/tree/master/src/cmd/pprof) a version of pprof that can be invoked via `go tool pprof`. It's largely the same as the upstream tool, except for a few tweaks. Go recommends to always use `go tool pprof` instead of the upstream tool for working with Go profiles.
Go 项目本身[捆绑了](https://github.com/golang/go/tree/master/src/cmd/pprof) 一个可以通过 `go tool pprof` 命令调用的 pprof 工具。 除了一些调整外，它与原本的 pprof 工具大致相同。 Go 建议始终使用 `go tool pprof` 命令来进行分析，而不是原来的 pprof 工具来分析 Go 。

## Features
## 特点

The pprof tool features an interactive command line interface, but also a Web UI, as well as various other output format options.

pprof 工具提供一个交互式命令行界面，一个Web UI，还包括各种其他输出格式选项。

## File Format
## 文件格式

### Description
### 描述

The pprof format is defined in the [profile.proto](https://github.com/google/pprof/blob/master/proto/profile.proto) protocol buffer definition which has good comments. Additionally there is an official [README](https://github.com/google/pprof/blob/master/proto/README.md) for it. pprof files are always stored using gzip-compression on disk.
pprof 相关的格式定义在 [profile.proto](https://github.com/google/pprof/blob/master/proto/profile.proto) 文件中, 这是一个使用 protocol buffer 协议定义的文件，并且这个文件带有比较全面的注释。另外，还有一个官方的[说明](https://github.com/google/pprof/blob/master/proto/README.md) 。pprof 保存在磁盘的文件使用的是 gzip 格式压缩的。

A picture is worth a thousand words, so below is an automatically [generated](https://github.com/seamia/protodot) visualization of the format. Please note that fields such as `filename` are pointers into the `string_table` which are not visualized, improvements for this would be welcome!
俗话说，一张图胜过千言万语，下面是 pprof 工具的可视化格式，这张图片是使用[protodot](https://github.com/seamia/protodot) 工具自动生成的。

[![profile.proto visualized](../static/images/2021_w39/profile.png)](../static/images/2021_w39/profile.png)

pprof's data format appears to be designed to for efficency, multiple languages and different profile types (CPU, Heap, etc.), but because of this it's very abstract and full of indirection. If you want all the details, follow the links above. If you want the **tl;dr**, keep reading:
pprof 的数据格式似乎是为效率、多语言(编程语言)和不同的性能分析类型(CPU、堆等)而设计的，但正因为如此，它非常抽象，显得不直观。如果你想了解所有细节，请点击[这里](https://github.com/google/pprof/blob/master/proto/profile.proto) 。继续向下阅读也能知道这么设计的原因。
A pprof file contains a list of **stack traces** called _samples_ that have one or more numeric **value** associated with them. For a CPU profile the value might be the CPU time duration in nanoseonds that the stack trace was observed for during profiling. For a heap profile it might be the number of bytes allocated. The **value types** themselves are described in the beginning of the file and used to populate the "SAMPLE" drop down in the pprof UI. In addition to the values, each stack trace can also include a set of **labels**. The labels are key-value pairs and can even include a unit. In Go those labels are used for [profiler labels](https://rakyll.org/profiler-labels/).
pprof 文件包含采集的堆栈列表，这些堆栈信息具有一个或多个与之关联的数值。 比如对于 CPU 性能分析，该值可能是在性能分析期间观察到堆栈的 CPU 持续时间（以纳秒为单位）。 对于堆性能分析，它可能是分配的字节数。 值类型本身在文件的开头进行了描述，并用于填充 pprof UI 中的“SAMPLE”下拉列表。 除了值之外，每个堆栈跟踪还可以包括一组标签。 标签是键值对，甚至可以包含一个单元。 在 Go 中，这些标签应用在[分析器标签](https://rakyll.org/profiler-labels/) 上 。



The profile also includes the **time** (in UTC) that the profile was recorded, and the **duration** of the recording.
性能分析还包括记录性能分析的时间（UTC格式）以及记录的持续时间。


Additionally the format allows for **drop/keep** regexes for excluding/including certain stack traces, but they're [not used](https://github.com/golang/go/blob/go1.15.6/src/runtime/pprof/proto.go#L375-L376) by Go. There is also room for a list of **comments** ([not used](https://github.com/golang/go/search?q=tagProfile_Comment) either), as well as describing the **periodic** interval at which samples were taken.
另外，这个格式允许删除/保留正则表达式以排除/包括某些堆栈跟踪信息，但 Go [不使用](https://github.com/golang/go/blob/go1.15.6/src/runtime/pprof/proto.go#L375-L376) 它们。 还有一个注释列表（也[没有使用](https://github.com/golang/go/search?q=tagProfile_Comment)），以及描述采样的周期间隔时间。


The code for generating pprof output in Go can be found in: [runtime/pprof/proto.go](https://github.com/golang/go/blob/go1.15.6/src/runtime/pprof/proto.go).
在 Go 中生成 pprof 输出的代码可以在：[runtime/pprof/proto.go](https://github.com/golang/go/blob/go1.15.6/src/runtime/pprof/proto.go) 中找到。

### Decoding
### 解码

Below are a few tools for decoding pprof files into human readable text output. They are ordered by the complexity of their output format, with tools showing simplified output being listed first:
下面是一些用于将 pprof 文件解码为人类可读文本输出的工具。 它们按输出格式的复杂程度排序，显示简化输出的工具列在最前面： 

#### Using `pprofutils`
### 使用 pprofutils 来进行辅助分析
[pprofutils](https://github.com/felixge/pprofutils) is a small tool for converting between pprof files and Brendan Gregg's [folded text](https://github.com/brendangregg/FlameGraph#2-fold-stacks) format. You can use it like this:
[pprofutils](https://github.com/felixge/pprofutils) 是一个用于在 pprof 文件和 Brendan Gregg 的[折叠文本](https://github.com/brendangregg/FlameGraph#2-fold-stacks) 格式之间转换的小工具。你可以这样使用它

```
$ pprof2text < examples/cpu/pprof.samples.cpu.001.pb.gz

golang.org/x/sync/errgroup.(*Group).Go.func1;main.run.func2;main.computeSum 19
golang.org/x/sync/errgroup.(*Group).Go.func1;main.run.func2;main.computeSum;runtime.asyncPreempt 5
runtime.mcall;runtime.gopreempt_m;runtime.goschedImpl;runtime.schedule;runtime.findrunnable;runtime.stopm;runtime.notesleep;runtime.semasleep;runtime.pthread_cond_wait 1
runtime.mcall;runtime.park_m;runtime.schedule;runtime.findrunnable;runtime.checkTimers;runtime.nanotime;runtime.nanotime1 1
runtime.mcall;runtime.park_m;runtime.schedule;runtime.findrunnable;runtime.stopm;runtime.notesleep;runtime.semasleep;runtime.pthread_cond_wait 2
runtime.mcall;runtime.park_m;runtime.resetForSleep;runtime.resettimer;runtime.modtimer;runtime.wakeNetPoller;runtime.netpollBreak;runtime.write;runtime.write1 7
runtime.mstart;runtime.mstart1;runtime.sysmon;runtime.usleep 3
```

#### Using `go tool pprof`
### 使用 `go tool pprof` 命令

`pprof` itself has an output mode called `-raw` that will show you the contents of a pprof file. However, it should be noted that this is not as `-raw` as it gets, checkout `protoc` below for that:
`pprof` 本身有一个名为 `-raw` 的输出模式，它将向您显示 pprof 文件的内容。但是，应该注意的是，这并不像它得到的那样原始，签出协议如下所示

```
$ go tool pprof -raw examples/cpu/pprof.samples.cpu.001.pb.gz

PeriodType: cpu nanoseconds
Period: 10000000
Time: 2021-01-08 17:10:32.116825 +0100 CET
Duration: 3.13
Samples:
samples/count cpu/nanoseconds
         19  190000000: 1 2 3
          5   50000000: 4 5 2 3
          1   10000000: 6 7 8 9 10 11 12 13 14
          1   10000000: 15 16 17 11 18 14
          2   20000000: 6 7 8 9 10 11 18 14
          7   70000000: 19 20 21 22 23 24 14
          3   30000000: 25 26 27 28
Locations
     1: 0x1372f7f M=1 main.computeSum /Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/cpu/main.go:39 s=0
     2: 0x13730f2 M=1 main.run.func2 /Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/cpu/main.go:31 s=0
     3: 0x1372cf8 M=1 golang.org/x/sync/errgroup.(*Group).Go.func1 /Users/felix.geisendoerfer/go/pkg/mod/golang.org/x/sync@v0.0.0-20201207232520-09787c993a3a/errgroup/errgroup.go:57 s=0
     ...
Mappings
1: 0x0/0x0/0x0   [FN]
```

The output above is truncated, [examples/cpu/pprof.samples.cpu.001.pprof.txt](https://github.com/DataDog/go-profiler-notes/blob/main/examples/cpu/pprof.samples.cpu.001.pprof.txt) has the full version.
上面的样例没有给出全部的内容，[点击这里查看所有的内容](../static/txt/2021_w39/examples/cpu/pprof.samples.cpu.001.pprof.txt)。
#### Using `protoc`
### 使用 `protoc`

For those interested in seeing data closer to the raw binary storage, we need the `protoc` protocol buffer compiler. On macOS you can use `brew install protobuf` to install it, for other platform take a look at the [README's install section](https://github.com/protocolbuffers/protobuf#protocol-compiler-installation).
对于有兴趣研究更接近原始二进制存储的数据开发者，则需要借助 protocol buffer 的编译器。在macOS 上，您可以使用 `brew install protobuf` 来安装它，对于其他平台，请查看[protocol buffer 安装部分的内容](https://github.com/protocolbuffers/protobuf#protocol-compiler-installation) 。


Now let's take a look at the same CPU profile from above:
现在让我们来分析上面的 CPU 的性能分析数据:


```
$ gzcat examples/cpu/pprof.samples.cpu.001.pb.gz | protoc --decode perftools.profiles.Profile ./profile.proto

sample_type {
  type: 1
  unit: 2
}
sample_type {
  type: 3
  unit: 4
}
sample {
  location_id: 1
  location_id: 2
  location_id: 3
  value: 19
  value: 190000000
}
sample {
  location_id: 4
  location_id: 5
  location_id: 2
  location_id: 3
  value: 5
  value: 50000000
}
...
mapping {
  id: 1
  has_functions: true
}
location {
  id: 1
  mapping_id: 1
  address: 20393855
  line {
    function_id: 1
    line: 39
  }
}
location {
  id: 2
  mapping_id: 1
  address: 20394226
  line {
    function_id: 2
    line: 31
  }
}
...
function {
  id: 1
  name: 5
  system_name: 5
  filename: 6
}
function {
  id: 2
  name: 7
  system_name: 7
  filename: 6
}
...
string_table: ""
string_table: "samples"
string_table: "count"
string_table: "cpu"
string_table: "nanoseconds"
string_table: "main.computeSum"
string_table: "/Users/felix.geisendoerfer/go/src/github.com/felixge/go-profiler-notes/examples/cpu/main.go"
...
time_nanos: 1610122232116825000
duration_nanos: 3135113726
period_type {
  type: 3
  unit: 4
}
period: 10000000
```

The output above is truncated also, [pprof.samples.cpu.001.protoc.txt](https://github.com/DataDog/go-profiler-notes/blob/main/examples/cpu/pprof.samples.cpu.001.protoc.txt) has the full version.
这份输出样例也是没有给出全部的内容，[点击这里查看所有的内容](../static/txt/2021_w39/examples/cpu/pprof.samples.cpu.001.pprof.txt)。

## History
## 历史


The [original pprof tool](https://github.com/gperftools/gperftools/blob/master/src/pprof) was a perl script developed internally at Google. Based on the copyright header, development might go back to 1998. It was first released in 2005 as part of [gperftools](https://github.com/google/tcmalloc/blob/master/docs/gperftools.md), and [added](https://github.com/golang/go/commit/c72fb37425f6ee6297371e0053d6d1f958d49a41) to the Go project in 2010.

[最初的 pprof工具](https://github.com/gperftools/gperftools/blob/master/src/pprof) 是谷歌内部使用 perl 开发的脚本。根据版权标题，开发可能要追溯到1998年。它于2005年作为 [gperftools ](https://github.com/google/tcmalloc/blob/master/docs/gperftools.md) 的一部分首次发布，并于2010年 [添加](https://github.com/golang/go/commit/c72fb37425f6ee6297371e0053d6d1f958d49a41) 到Go项目中。

In 2014 the Go project [replaced](https://github.com/golang/go/commit/8b5221a57b41a19abcb4e3dde20014af494048c2) the perl based version of the pprof tool with a Go implementation by  that was already used inside of Google at this point. This implementation was re-released as a [standalone project](https://github.com/google/pprof) in 2016. Since then the Go project has been vendoring a copy of the upstream project, [updating](https://github.com/golang/go/commits/master/src/cmd/vendor/github.com/google/pprof) it on a regular basis.
2014年，Go项目用 [Raul Silvera](https://www.linkedin.com/in/raul-silvera-a0521b55/) 的Go实现[取代了](https://github.com/golang/go/commit/8b5221a57b41a19abcb4e3dde20014af494048c2) 基于perl的pprof工具，目前谷歌已经使用了这个实现的工具。这个实现在2016年作为[一个独立的项目](https://github.com/google/pprof) 进行重新发布。从那时起，Go项目一直在提供上游项目的 pprof，并定期对其进行 [更新](https://github.com/golang/go/commits/master/src/cmd/vendor/github.com/google/pprof) 。



Go 1.9 (2017-08-24) added support for pprof labels. It also started including symbol information into pprof files by default, which allows viewing profiles without having access to the binary.
Go 1.9(2017-08-24)增加了对pprof标签的支持。它还开始在默认情况下将符号信息包含到pprof文件中，这允许在不访问二进制文件的情况下查看程序性能。

## Todo
## Todo

-   Write more about using `go tool pprof` itself.
- 更多的篇幅应该专注于 `go tool pprof` 工具本身.

-   Explain why pprof can be given a path to the binary the profile belongs to.
- 解释为什么可以给 pprof一个路径到概要文件所属的二进制文件。
  
-   Get into more details about line numbers / addresses.
- 更加多关于行号和地址的细节信息
-   Talk about mappings and when a Go binary might have more than one
- 讨论 go 的二进制文件有多个版本时的关联映射问题
## Disclaimers
## 免责声明


I'm [felixge](https://github.com/felixge) and work at [Datadog](https://www.datadoghq.com/) on [Continuous Profiling](https://www.datadoghq.com/product/code-profiling/) for Go. You should check it out. We're also [hiring](https://www.datadoghq.com/jobs-engineering/#all&all_locations) : ).
我是 [felixge](https://github.com/felixge) ，在[Datadog](https://www.datadoghq.com/) 关于 [go 代码性能分析](https://www.datadoghq.com/product/code-profiling/) 的工作。你应该去看看。我们也在 [招聘](https://www.datadoghq.com/jobs-engineering/#all&all_locations) :)。


The information on this page is believed to be correct, but no warranty is provided. Feedback is welcome!
本页上的信息不保证是正确的。我们欢迎你的反馈。
