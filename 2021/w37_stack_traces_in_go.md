- 原文地址：
- 原文作者：张洋
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w37_stack_traces_in_go.md
- 译者：[cuua](https://github.com/cuua)
- 校对：

# go的栈追踪

栈跟踪在Go分析中起着关键作用。因此，让我们试着了解它，看看它如何影响我们程序分析的准确性。

## 介绍

所有Go分析器都通过收集堆栈跟踪的样本并将其放入[pprof配置文件]（./pprof.md）中来工作。让我们忽略一些细节，pprof配置文件只是堆栈跟踪的频率表，如下所示：

| stack trace  | count |
| ------------ | ----- |
| main;foo     | 5     |
| main;foo;bar | 3     |
| main;foobar  | 4     |

让我们放大上表中的第一个栈跟踪：`main.fo`。Go开发人员通常更熟悉看到由'panic（）'或['runtime.stack（）`]呈现的这样的堆栈跟踪(https://golang.org/pkg/runtime/#Stack)如下图所示：

```
goroutine 1 [running]:
main.foo(...)
	/path/to/go-profiler-notes/examples/stack-trace/main.go:9
main.main()
	/path/to/go-profiler-notes/examples/stack-trace/main.go:5 +0x3a
```

此文本格式已在[其他地方描述](https://www.ardanlabs.com/blog/2015/01/stack-traces-in-go.html)所以我们这里不讨论细节。相反，我们将深入研究这些数据的来源。

## Goroutine栈

顾名思义，栈跟踪源自“栈”。尽管细节各不相同，但大多数编程语言都有栈的概念，并使用它来存储局部变量、参数、返回值和返回地址等内容。生成栈跟踪通常涉及在称为[Unwinding](#unwinding)在程序中的对栈的导航，稍后将详细描述该过程。

像“x86-64”这样的平台定义了[栈布局](https://eli.thegreenplace.net/2011/09/06/stack-frame-layout-on-x86-64) 和 [呼叫约定](https://github.com/hjl-tools/x86-psABI/wiki/x86-64-psABI-1.0.pdf) 并鼓励其他编程语言采用它来实现互操作性。Go不遵循这些惯例，而是使用自己独特的 [呼叫惯例](https://dr-knz.net/go-calling-convention-x86-64.html). Go（1.17？）的未来版本将采用更传统的 [基于注册](https://go.googlesource.com/proposal/+/refs/changes/78/248178/1/design/40724registercalling.md) 约定来提高性能。然而，即使是新的约定也不会与平台兼容，因为这会对goroutine的可伸缩性产生负面影响。

Go的栈布局在不同平台上略有不同。为了使事情易于管理，我们将假定在本文档的其余部分使用“x86-64”。

### 栈布局

现在让我们仔细看看栈。每个goroutine都有自己的栈，至少为[2 KiB](https://sourcegraph.com/search?q=repo:golang/go+repo:%5Egithub%5C.com/golang/go%24+\uStackMin+%3D&patternType=literal) 并从高内存地址向低内存地址增长。这可能有点让人困惑，而且主要是一种历史惯例，当时地址空间非常有限，人们不得不担心栈与程序使用的其他内存区域发生冲突。

下图显示了当前调用`main.foo（）`的示例goroutine的堆栈，如上面的示例所示：

![](../static/images/2021_w37_stack_traces_in_go/goroutine-stack.png)

这张图片中有很多内容，但现在让我们关注以红色突出显示的内容。要获得栈追踪，我们首先需要的是当前程序计数器（`pc`）。这可以在一个名为“rip”（指令指针寄存器）的CPU寄存器中找到，并指向另一个内存区域，该区域保存程序的可执行机器代码。由于我们当前正在调用'main.foo()'，'rip'指向该函数中的一条指令。如果您不熟悉寄存器，可以将其视为访问速度非常快的特殊CPU变量。其中一些命令，如'rip'、'rsp'或'rbp'有特殊用途，而其他命令则可以由编译器根据需要使用。

现在我们知道了当前函数的程序计数器，是时候查找调用者的'pc'值了，即所有也以红色突出显示的'return address（pc）值。有各种各样的技术可以实现这一点，在[Unwinding]（#unwinding）一节中有描述。最终结果是一个程序计数器列表，这些计数器表示栈跟踪，就像您可以从[`runtime.Callers()`](https://golang.org/pkg/runtime/#Callers) 获取的栈跟踪一样. 最后但并非最不重要的一点是，这些“pc”值通常被翻译成人类可读的文件/行/函数名，如下面的[符号化]（#符号化）部分所述。在Go本身中，您只需调用l[`runtime.CallerFramers()`](https://golang.org/pkg/runtime/#CallersFrames) 表示“pc”值列表的符号。

### 真实案例
查看好看的图片可以很好地获得对栈的高级理解，但也有其局限性。有时，为了全面理解，您需要查看原始位和字节。如果你对此不感兴趣，请跳到下一节。

要查看栈，我们将使用[delve](https://github.com/go-delve/delve)这是一个很好的go调试器。为了检查栈，我编写了一个名为 [stackannotate.star](./delve/stackannotate.star) 的脚本，可用于打印一个简单的[example程序]（./examples/stackannotate/main.go）的带注释栈：


```
$ dlv debug ./examples/stackannotate/main.go 
Type 'help' for list of commands.
(dlv) source delve/stackannotate.star
(dlv) continue examples/stackannotate/main.go:19
Breakpoint 1 set at 0x1067d94 for main.bar() ./examples/stackannotate/main.go:19
> main.bar() ./examples/stackannotate/main.go:19 (hits goroutine(1):1 total:1) (PC: 0x1067d94)
    14:	}
    15:	
    16:	func bar(a int, b int) int {
    17:		s := 3
    18:		for i := 0; i < 100; i++ {
=>  19:			s += a * b
    20:		}
    21:		return s
    22:	}
(dlv) stackannotate
regs    addr        offset  value               explanation                     
        c00004c7e8       0                   0  ?                               
        c00004c7e0      -8                   0  ?                               
        c00004c7e8     -16                   0  ?                               
        c00004c7e0     -24                   0  ?                               
        c00004c7d8     -32             1064ac1  return addr to runtime.goexit   
        c00004c7d0     -40                   0  frame pointer for runtime.main  
        c00004c7c8     -48             1082a28  ?                               
        c00004c7c0     -56          c00004c7ae  ?                               
        c00004c7b8     -64          c000000180  var g *runtime.g                
        c00004c7b0     -72                   0  ?                               
        c00004c7a8     -80     100000000000000  var needUnlock bool             
        c00004c7a0     -88                   0  ?                               
        c00004c798     -96          c00001c060  ?                               
        c00004c790    -104                   0  ?                               
        c00004c788    -112          c00001c060  ?                               
        c00004c780    -120             1035683  return addr to runtime.main     
        c00004c778    -128          c00004c7d0  frame pointer for main.main     
        c00004c770    -136          c00001c0b8  ?                               
        c00004c768    -144                   0  var i int                       
        c00004c760    -152                   0  var n int                       
        c00004c758    -160                   0  arg ~r1 int                     
        c00004c750    -168                   1  arg a int                       
        c00004c748    -176             1067c8c  return addr to main.main        
        c00004c740    -184          c00004c778  frame pointer for main.foo      
        c00004c738    -192          c00004c778  ?                               
        c00004c730    -200                   0  arg ~r2 int                     
        c00004c728    -208                   2  arg b int                       
        c00004c720    -216                   1  arg a int                       
        c00004c718    -224             1067d3d  return addr to main.foo         
bp -->  c00004c710    -232          c00004c740  frame pointer for main.bar      
        c00004c708    -240                   0  var i int                       
sp -->  c00004c700    -248                   3  var s int
```

脚本并不完美，栈上有一些地址暂时无法自动注释（欢迎提供）。但是一般来说，您应该能够使用它来对照前面介绍的抽象栈图来检查您的理解。

如果您想自己尝试一下，可以修改示例程序，将`main.foo()`作为goroutine生成，并观察其对栈的影响。

### cgo

上面描述的Go的栈实现在与使用遵循平台调用约定（如C）的语言编写的代码交互时，正在进行重要的权衡。Go不能直接调用这些函数，而必须执行[cgo](https://golang.org/src/runtime/cgocall.go) 用于在goroutine堆栈和可以运行C代码的OS分配堆栈之间切换。这会带来一定的性能开销，而且在分析期间捕获栈跟踪也会带来复杂的问题，请参见[runtime.SetCgoTraceback()](https://golang.org/pkg/runtime/#SetCgoTraceback).

🚧 我将在未来尝试更详细地描述这一点。

## Unwinding
展开（或栈遍历）是从栈收集所有返回地址的过程（请参见[stack Layout](#stack Layout)）中的红色元素）。它们与当前的指令指针寄存器（`rip`）一起构成一个程序计数器（`pc`）值列表，可以通过[符号化]（#符号化）将这些值转换为人类可读的栈跟踪。

Go的运行时，包括内置探查器，专门使用[gopclntab]（#gopclntab）进行解卷。但是，我们将首先描述[Frame Pointer]（#Frame Pointer）展开，因为它更容易理解，并且可能[在将来得到支持](https://github.com/golang/go/issues/16638). 在此之后，我们还将讨论[DWARF]（#DWARF），这是另一种展开Go栈的方法。

对于那些不熟悉它的人，下面是一个简单的图表，显示了我们将在这里讨论的典型Go二进制文件的相关部分。它们总是包装在ELF、Mach-O或PE容器格式中，具体取决于操作系统。

<img src="./go-binary.png" width="200"/>

![](../static/images/2021_w37_stack_traces_in_go/go-binary.png)

### 帧指针

帧指针展开是一个简单的过程，它遵循基本指针寄存器（`rbp`）指向栈上指向下一帧指针的第一个帧指针，依此类推。换句话说，它在[栈布局](#栈布局)图形中的橙色线之后。对于每个访问的帧指针，位于帧指针上方8个字节的返回地址（pc）将沿着该路径收集，就是这样:)

帧指针的主要缺点是，在正常程序执行期间，将其推到栈上会给每个函数调用增加一些性能开销。Go作者在[Go 1.7发行说明](https://golang.org/doc/go1.7) 中评估，平均程序的平均执行开销为2%. 另一个数据点是Linux内核，它的开销为[5-10%](https://lore.kernel.org/lkml/20170602104048.jkkzssljsompjdwy@) 使用de/T/#u），例如sqlite和pgbench。正因为如此，`gcc`之类的编译器提供了诸如`fomit frame pointers`之类的选项来省略它们以获得更好的性能。然而，这是一个魔鬼的交易：它会立即给您带来小的性能胜利，但它会降低您在将来调试和诊断性能问题的能力。因此，一般建议如下：

>始终使用帧指针编译。忽略帧指针是一种有害的编译器优化，会破坏调试器，遗憾的是，这通常是默认的。

>-[Brendan Gregg](http://www.brendangregg.com/perf.html)

在go中，你甚至不需要这个建议。由于64位二进制文件默认启用Go 1.7帧指针，并且没有可用的`-fomit帧指针`-footgun。这允许Go与第三方调试器和分析器（如[Linux perf]）兼容(http://www.brendangregg.com/perf.html)开箱即用。

如果您想看到一个简单的帧指针展开实现，可以查看[这个玩具项目](https://github.com/felixge/gounwind) 它有一个轻量级的选项来替代“runtime.Callers（）”。与下文所述的其他退绕方法相比，简单性本身就是明证。还应该清楚的是，帧指针展开具有'O（N）`时间复杂度，其中'N'是需要遍历的堆栈帧数。

尽管看起来很简单，但帧指针展开并不是灵丹妙药。帧指针由被调用方推送到栈，因此对于基于中断的评测，存在一种固有的条件，可能会导致您错过栈跟踪中当前函数的调用方。此外，单独展开帧指针无法识别内联函数调用。因此，至少[gopclntab](#gopclntab) 或[DWARF](#DWARF) 的一些复杂性对于实现准确的退绕至关重要。

### gopclntab

尽管帧指针在64位平台上可用，但Go并没有利用它们来展开（[这可能会改变](https://github.com/golang/go/issues/16638)). 相反，Go附带了它自己的特殊展开表，这些表嵌入在任何Go二进制文件的“gopclntab”部分中`gopclntab`代表“go程序计数器行表”，但这有点用词不当，因为它包含展开和符号化所需的各种表和元数据。

就展开而言，一般的想法是在“gopclntab”内部嵌入一个“虚拟帧指针表”（称为“pctab”），该表将程序计数器（`pc`）映射到栈指针（`rsp`）与其上方的“返回地址（pc）”之间的距离（也称为`sp delta`）。此表中的初始查找使用“rip”指令指针寄存器中的“pc”，然后使用“返回地址（pc）”进行下一次查找，依此类推。这样，无论栈上是否有物理帧指针，都可以始终展开。

Russ Cox最初在他的[Go 1.2运行时符号信息](https://golang.org/s/go12symtab) 中描述了一些涉及的数据结构文档，但它现在已经非常过时了，最好直接查看当前的实现。相关文件为[runtime/traceback.go](https://github.com/golang/go/blob/go1.16.3/src/runtime/traceback.go) 和[runtime/symtab.go](https://github.com/golang/go/blob/go1.16.3/src/runtime/symtab.go) ，那么让我们开始吧。

Go的栈跟踪实现的核心是[`gentraceback()`](https://github.com/golang/go/blob/go1.16.3/src/runtime/traceback.go#L76-L86) 从不同位置调用的函数。如果调用方是例如`runtime.Callers()`函数只需要进行展开，但是例如`panic（）`需要文本输出，这也需要符号化。此外，代码必须处理[链接寄存器架构](https://en.wikipedia.org/wiki/Link_register) 之间的差异比如ARM，它的工作原理与x86略有不同。对于Go团队中的系统开发人员来说，这种展开、符号化、对不同体系结构的支持和定制数据结构的组合可能只是日常工作中的一部分，但这对我来说肯定很棘手，因此请注意我下面描述中的潜在不准确之处。

每个帧查找都从传递给[`findfunc()`](https://github.com/golang/go/blob/go1.16.3/src/runtime/symtab.go#L671) 的当前'pc'开始它查找包含“pc”的函数的元数据。历史上，这是使用'O(logn)二进制搜索完成的，但[现在](https://go-review.googlesource.com/c/go/+/2097/) 有一个类似哈希映射的索引[`findfuncbucket`](https://github.com/golang/go/blob/go1.16.3/src/runtime/symtab.go#L671) 结构，通常使用'O(1)`算法直接引导我们找到正确的条目。

[_func](https://github.com/golang/go/blob/9baddd3f21230c55f0ad2a10f5f20579dcf0a0bb/src/runtime/runtime2.go#L825) 我们刚刚检索到的元数据包含一个进入“pctab”表的“pcsp”偏移量，该表将程序计数器映射到栈指针增量。要解码此信息，我们调用[`funcspdelta()`](https://github.com/golang/go/blob/go1.16.3/src/runtime/symtab.go#L903) 它对所有更改函数的'sp delta'的程序计数器进行线性搜索，直到找到最接近的（'pc'，'sp delta'）对。对于具有递归调用周期的栈，使用一个微小的程序计数器缓存来避免执行大量重复的工作。

现在我们有了栈指针delta，我们几乎可以找到调用者的下一个`returnaddress(pc)`值，并对其执行相同的查找，直到到达栈的“底部”。但在此之前，我们需要检查当前的'pc'是否是一个或多个内联函数调用的一部分。这是通过检查当前`_func`的`_FUNCDATA_InlTree`数据并对该表中的（`pc`，`inline index`）对进行另一次线性搜索来完成的。以这种方式找到的任何内联调用都会将虚拟栈帧'pc'添加到列表中。然后我们继续使用本段开头提到的`返回地址（pc）`一词。

综上所述，在合理的假设下，`gocplntab`展开的有效时间复杂度与帧指针展开相同，即`O(N)`其中`N`是栈上的帧数，但具有更高的恒定开销。这是可以[实验](https://github.com/DataDog/go-profiler-notes/tree/main/examples/stack-unwind-overhead) 验证的，但对于大多数应用程序，一个好的经验法则是假定展开栈跟踪的成本为`~1µs`。因此，如果您的目标是在生产中实现<1%的CPU评测开销，那么您应该尝试将评测器配置为每个内核每秒跟踪的事件数不超过~10k。这是一个相当可观的数据量，但对于某些工具，如[内置跟踪器](https://golang.org/pkg/runtime/trace/) 栈展开可能是一个重要的瓶颈。将来，这可以通过Go core添加[对帧指针展开的支持]来克服(https://github.com/golang/go/issues/16638) 这可能会快[50倍](https://github.com/felixge/gounwind) 而不是当前的“gopclntab”实现。

最后但并非最不重要的是，值得注意的是，Go附带了两个`.gopclntab`实现。除了我刚才描述的一个，在[debug/gosym](https://golang.org/pkg/debug/gosym/) 中还有另一个链接器、`go tool addr2line`和其他人似乎使用的包。如果您愿意，您可以将它与[debug/elf](./examples/pclnttab/linux.go) 或（[debug/macho](./examples/pclnttab/darwin.go)）结合使用，作为您自己的[gopclntab冒险](./examples/pclnttab) 的起点，无论是好的还是[坏的](https://tuanlinh.gitbook.io/ctf/golang-function-name-obfuscation-how-to-fool-analysis-tools).

### DWARF
[DWARF](https://en.wikipedia.org/wiki/DWARF) 是一种被许多调试器理解的标准化调试格式（例如，[delve](https://github.com/go-delve/delve) ）和分析器（例如Linux[perf](http://www.brendangregg.com/perf.html)). 它支持“gopclntab”中的超集功能，包括展开和符号化，但因其非常复杂而闻名。众所周知，Linux内核拒绝对内核栈跟踪采用DWARF展开：

>unwinders的全部（也是唯一）目的是在出现bug时简化调试[…]。一个几百行长的unwinders对我来说根本不感兴趣。

>-[Linus Torvalds](https://lkml.org/lkml/2012/2/10/356)

这导致[创造](https://lwn.net/Articles/728339/) [ORC unwinders](https://www.kernel.org/doc/html/latest/x86/orc-unwinder.html) 它现在作为另一种unwinders在内核中可用。然而，ORCs在go中不扮演任何角色，我们只需要在这里与ELFs和DWARFs作战。

Go编译器总是为它生成的二进制文件发出DWARF（v4）信息。该格式是标准化的，因此与“gopclntab”不同，外部工具可以依赖它。但是，DWARF数据在很大程度上与“gopclntab”冗余，并对构建时间和二进制大小产生负面影响。因此，罗布·派克提议[默认禁用它](https://github.com/golang/go/issues/26074) ，但仍在讨论中。

与“gopclntab”不同，DWARF信息可以在构建时轻松地从二进制文件中剥离，如下所示：

```
go build -ldflags=-w <pkg>
```

就像“fomit frame pointers”一样，这有点像魔鬼交易，但有些人不相信DWARF和魔鬼之间的区别。因此，如果你愿意签署一份对同事的责任豁免书，你可以继续。说真的，如果DWARF符号能解决你的一个重要问题，我建议你只去掉它。一旦DWARF信息被剥离，您将无法使用perf、delve或其他工具来评测或调试生产中的应用程序。

## 符号化

符号化是将一个或多个程序计数器（`pc`）地址转换为人类可读的符号（如函数名、文件名和行号）的过程。例如，如果您有两个类似以下的'pc'值：

```
0x1064ac1
0x1035683
```

您可以使用符号化将它们转换为人类可读的栈跟踪，如下所示：

```
main.foo()
	/path/to/go-profiler-notes/examples/stack-trace/main.go:9
main.main()
	/path/to/go-profiler-notes/examples/stack-trace/main.go:5
```

在Go的运行时，符号化始终使用[gopclntab](#gopclntab)部分中包含的符号信息。也可以通过[`runtime.CallerFramers()`](https://golang.org/pkg/runtime/#CallersFrames) 访问此信息.

第三方探查器（如Linux性能）不能使用[gopclntab](#gopclntab)，而必须依赖[DWARF](#DWARF) 进行符号化。

## 历史
为了支持第三方探测器，如[perf](http://www.brendangregg.com/perf.html) [Go 1.7](https://golang.org/doc/go1.7) （2016-08-15）版本开始在默认情况下为[64位二进制文件](https://sourcegraph.com/search?q=framepointer_enabled+repo:%5Egithub%5C.com/golang/go%24+&patternType=literal) 启用帧指针

## 学分
非常感谢[迈克尔·普拉特](https://github.com/prattmic)供[审阅](https://github.com/DataDog/go-profiler-notes/commit/6a62d5908079ddac9c92d319f49fde846f329c55#r49179154) 本文档中“gopclntab”部分，并捕获我分析中的一些重大错误。

