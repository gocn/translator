# **那些年我使用Go语言犯的错**

* 原文地址：https://henvic.dev/posts/my-go-mistakes/
* 原文作者：`Henrique Vicente`
* 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w13_My_Go_mistakes.md
* 译者：[朱亚光](https://github.com/zhuyaguang)

在这篇文章里，我主要分享六年来用Go编程过程中所犯过的一些错误。

## `init` 函数

在 Go 中，你可以在单个package或文件中定义多个特殊的函数 **`init`**，从 [Effective Go](https://golang.org/doc/effective_go.html#init) 中，我们知道

> `init` 函数是在包中所有变量初始化之后才会调用，而这些变量又是在所有导入的包初始化之后才初始化。

尽管在大多数情况下使用 `init` 函数是一种确定的行为，但你还是想减少使用它的次数。首先，`init` 函数最典型的应用就是初始化全局变量，那么你可以通过减少全局变量的数量来达到减少使用 `init` 函数的目的。

使用 `init` 函数之前最好要三思而行，主要的原因就是你不能从代码中调用 `init` 函数。另外一个原因是，虽然具有确定性，但是很难预测 `init` 函数的执行顺序。这个顺序依赖你导入的包和源码的文件名。移除一个package或者重命名一个文件都会影响这个顺序。

使用 `init` 函数最好的例子就是初始化一个计算成本很大的查找表。

**我在哪里后悔使用了 `init` 函数呢？**曾经我用 [cobra](https://github.com/spf13/cobra) 去构建一个 `CLI` 工具时，用 `init ` 函数去定义命令行的数据结构和 flags。现在我知道时完全没必要了。顺便说一句，Go 1.16昨天发布了，带来了一些好消息。

> 设置 `GODEBUG` 环境变量为 `inittrace=1`，现在会导致运行时会为每个包的 `init` 打印一行标准错误信息，总结其执行时间和内存分配。

## 常量

下面这个变量的值在代码库任何位置都没有更改过：

```go
// Version of the application
var Version = "master"
```

因此我想当然地把它看作一个常量。突然把 `var`  改成 `const`。就这样我不知不觉地破坏了我应用程序的更新通知系统，因为我在构建时修改了这个常量。

```go
$ go build \
  -ldflags="-X 'github.com/henvic/wedeploycli/defaults.Version=$NEW_RELEASE_VERSION' \
  -X 'github.com/henvic/wedeploycli/defaults.Build=$BUILD_COMMIT' \
  -X 'github.com/henvic/wedeploycli/defaults.BuildTime=$BUILD_TIME'"
```

原来...常量是不能修改的。

## 空指针引用

破坏了更新通知系统还不算完，我忘记检查指针是否为空，导致破坏了 update 命令。还好我在发布后的测试中发现了这个问题，花了几分钟就修复了，所以影响也不大。

## 注释和文档

有一次我读到一句话，当代码不能表达你的意图的时候，你就要写注释了，因为代码时间长了会过时和不同步。你以为通过恰当命名的变量、结构体、接口、和函数的代码来表达你的推理和想法，这就够了。但请你不要低估注释的力量！我以前就是这种心态，下意识地低估了注释的力量。还好，后来写了几年的 Go 。领略到良好注释的价值。如果你对什么是合理的注释或者要不要写注释存在疑问。我建议你读一读标准库的源码，看看它们是怎么写的。[Go代码评审中的注释部分](https://blog.golang.org/godoc) 也是一个不错的参考。

文档同样也很关键。你如果想要用 [godoc ](https://blog.golang.org/godoc) 给公共 `API` 生成文档。你只要遵循最小化和不张扬评论模式 。该模式使用起来相对简单，即使不是你喜欢的风格，你也能获得一致性的体验。

**记住：**代码只写一次，但是会被读多次。最好多花点时间写代码注释，让别人和未来的自己都能理解，而不是急着写代码，几个月或者几年后要花更多的时间去理解它。



## 创建的包太多了

```
I didn't need to write 133 packages.
I didn't need to write 133 packages.
I didn't need to write 133 packages.
I didn't need to write 133 packages.
```

现在想想有点羞耻，我在我的 `CLI` 工具代码里给需要的 [58个命令每一个都创建了一个包](https://github.com/henvic/wedeploycli/tree/master/command)。这58个目录每个目录都至少有一个文件(每个文件都是一个包)。我本可以用一个包包含10-15个中等大小的文件。其中 [command/list 包](https://github.com/henvic/wedeploycli/tree/master/command/list) 犯的错误最严重。

```cmake
./command/list
├── instances
│   └── instances.go (85 lines of code)
├── list.go (121 lines of code)
├── projects
│   └── projects.go (73 lines of code)
└── services
    └── services.go (109 lines of code)
Total: 388 lines of code
```

下面这些指标可能会过多地分解你的代码

-   只有几十行代码的小包或者文件
-   由于存在多个包同名，导包的时候使用自定义标志符

**那我们应该怎么解决呢？**`command` 包里面地`list.go`  文件最好少于350行代码。作为代码组织的优秀范例，我建议看一下 [net/http](https://golang.org/src/net/http/) 包的代码。在包含十几个文件的单个包中，实现了 Go HTTP客户端和服务端。

## 导出名

在 Go 中，如果一个名字是以大写字母开头，那么这个名称就称作[导出名](https://tour.golang.org/basics/3)。换句话说，就是其他包的代码可以直接访问。

下面是 [fmt](https://golang.org/pkg/fmt/) 包的函数:

```go
func Printf(format string, a ...interface{}) (n int, err error)
func Println(a ...interface{}) (n int, err error)
func newPrinter() *pp
```

只有前两个函数可以被 `fmt` 包外面的调用，如果你尝试在外面调用 `newPrinter` ，你会得到一个编译时错误

```
./prog.go:8:2: cannot refer to unexported name fmt.newPrinter
./prog.go:8:2: undefined: fmt.newPrinter
```

正如我在上一节中所提到的，如果我有更少的包，我将避免需要导出很多外部变量，从而大大简化依赖关系图。

### 内部包

现在，Go 有另外一个很棒的特性来划分你的代码：[内部包](https://golang.org/doc/go1.4#internalpackages)

`./a/b/c/internal/d/e/f` 现在只要用` ./a/b/c` 就可以导入了

使用内部包可以保护你的代码，除非你需要公共的 `API`。这对于那些不打算公开发布的私人项目非常有用。设定清晰的界限和期望，只暴露你打算支持的用例。如果你的 `API` 用户面很小的话，你可以很自由地进行内部代码变更，而不用担心升级了一个大版本后，导致后端不兼容和一堆bug。

你可能对该观点有所顾虑，因为你的代码在整个团队项目中至关重要。那么是时候来回顾一下下面这句 Go 谚语：

> 一点点复制总比一点点依赖好——[Rob Pike，Go谚语 ，2015.11.18 于 Gopherfest 。](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=568s)

你可以使用 [apidiff](https://go.googlesource.com/exp/+/refs/heads/master/apidiff/README.md) （一种检测`API`变更后兼容性的工具）来检测你的 `API` 连接。也可以看看2019年 `GopherCon` 上 Jonathan Amsterdam的 [检测 API 变更后兼容性](https://www.youtube.com/watch?v=JhdL5AkH-AQ) 的演讲（[文字版](https://about.sourcegraph.com/go/gophercon-2019-detecting-incompatible-api-changes/)）

## 全局变量和配置信息

*你还没开始阅读之前，可以看看我以前的关于[环境变量、配置、密钥和全局变量](https://henvic.dev/posts/env/)的博客。*

你希望你的代码看起来简洁，但是配置信息可能会妨碍你。一种可能的快速解决办法就是使用全局变量全局传递，对吗？当然如果你不介意引入并发安全或者不介意无法进行并行测试的话。这会让事情变得糟糕，而且重构的成本越来越大。注意如果你一次性把事情做对，后面就不会发生问题了。例如，初始化对象时，可以显示地传递配置信息。

如果你需要在你不需要了解的层之间传递参数的话，使用 [context](https://golang.org/pkg/context/) 非常有用。

```go
// Params for the metrics system.
type Params struct {
// Hostname of your service.
Hostname string

// Verbose flag.
Verbose bool
// ...
}

// paramsContextKey is the key for the params context.
// Using struct{} here to guarantee there are no conflicts with keys defined outside of this package.
type paramsContextKey struct{}

// Context returns a copy of the parent context with the given params.
func (p *Params) Context(ctx context.Context) context.Context {
return context.WithValue(ctx, paramsContextKey{}, p)
}

// FromContext gets params from context.
func FromContext(ctx context.Context) (*Params, error) {
if p, ok := ctx.Value(paramsContextKey{}).(*Params); ok {
return p, nil
}
return nil, errors.New("metrics system params not found")
}
```

可以看看 [Go Playground](https://play.golang.org/p/paDWRN_K5LZ) 里面另外一个例子，**注意避坑**。不要使用 context 直接传递具体配置信息。只有通过上下层传递一些一目了然东西，才可以使用 context 。所以使用 context 之前 最好好好思考下使用的最佳方式。

## 导入和生成大小

将人类可读的源代码转换成一系列机器操作指令需要大量的工作。现在有很多策略来解决这个问题，一些语言（例如 `Javascript`、`Python`、`Tcl`）是解释型语言。也就是说代码在解释器（比如浏览器或者运行时）执行期间就被翻译成机器码。Go 是一种静态编译语言，意味着代码要提前编译。静态编译语言的优点就是执行速度快。像[及时编译](https://en.wikipedia.org/wiki/Just-in-time_compilation)这样的东西结合了解释型和编译型的概念，说到这儿就有点离题了。无论何时运行 go build，经过代码解析，编译成机器码，链接之后，都会创建一个包含你所有程序和依赖，可以被机器执行的文件。

该构建过程很容易输入几K文本文件，然后经过机器码转换和链接依赖就变成了几M的二进制文件。尽管 Go 是非常高效和简洁，但除非  Gopher 会魔法，不然也少不了这个消耗。

回到我的例子，我在开发一个 [CLI](https://henvic.dev/portfolio/#wedeploy) 工具 有一个 deploy 命令涉及到多次调用 git。我们使用了 git 作为传输层和智能缓存层。缺点就是我们工具需要系统范围的依赖。遇到几个 git bug 后，我决定用 Go 实现一个 git （[go-git](https://github.com/go-git/go-git)）作为替代。我增加了一个 experimental flag后，就开始用纯 Go 库实现了。但是，我忘记评估后面这个实现带来的影响。它让文件的大小成倍增长，从不到 `4M` 增加到了 `9M` 。虽然影响不是很大，但也大幅度增加了文件的大小。我后悔没有意识到这一点，如果我注意到了，我会用构建标签来隐藏后面这种实现方法，一直到准备好进行A/B测试。

## 并发和流

我没有学习过 Go的并发编程，导致我犯了很多新手错误：往多个 `goroutines`或者 线程中写入导致文本混乱。

我甚至在终端中给文本动画写包的时候也犯过这个错误。如果你发现你也存在这个问题，你可以用 互斥锁来设置 哪个 `goroutine` 什么时候可以写，更复杂的情况可以使用 channel 来打印单个通道。另外，注意下如果输出顺序很重要，你可能需要同步打印标准错误 (`os.Stderr`) 或者标准输出(`os.Stdout`)。

> Tip：Go 有一个很棒的数据竞争检测器，你可以通过 在 go test或者 go build 命令加上 -race 标志来运行你的测试用例或程序。

## Sockets 和 WebSocket

曾经我解决了一个有意思的问题，就是实现 基于 `WebSocket` 的 SSH 功能时候，我们已经在后端系统上使用了 [socket.io](http://socket.io/) 协议。为了简单起见，我们希望将该功能也用于此协议，为此，我拉取并大量修改了现有的 Go `socket.io` 库代码。我花了繁重的工作去理解这个协议的实现，然后再让其能满足我们的需求。由于没有正式的` socket.io` 的规范，我甚至不得不对协议进行逆向工程。

最后看起来能够按预期运行的时候，我们向服务器发送了一个文件，并从连接中运行一个简单的测试用例：$ cat `hamlet.txt` 并比较输出。令人意外的时候，有些短语出现了乱序。错误的原因是，每接受到一条消息，库代码就创建一个新的 `goroutine`。

解决办法很简单：当前循环中删除 go 关键字，让其在同一线程内调用。你通常希望在最后一刻创建 `goroutine`。如果考虑到性能，你可能会马上创建一个。对我来说，这是一个典型的例子，里面有带案例的文档可以向用户解释他们需要什么。另外，里面还有不同的方式来定义阻塞和非阻塞程序。

感谢阅读。
