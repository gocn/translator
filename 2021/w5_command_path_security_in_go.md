# Go语言命令行执行路径的安全性

- 原文地址：https://blog.golang.org/path-security
- 原文作者：Russ Cox
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w5_command_path_security_in_go.md
- 译者：[zhuyaguang](https://github.com/zhuyaguang)
- 校对：
> Russ Cox
> 2021年1月19日

今天  [Go安全发布](https://groups.google.com/g/golang-announce/c/mperVMGa98w/m/yo5W5wnvAAAJ) 解决了一个涉及在不受信任的目录中查找路径的问题，该问题可能导致在运行 go get 命令时发生远程执行。我们希望大家能够了解这个问题到底意味着什么以及在你们自己的程序中是否也存在此类问题。这篇文章详细介绍了该 bug 、我们建议的解决办法、怎样判断你们自己的程序是否容易受到类似问题的攻击、以及如果遇到了，你可以做些什么。

## Go命令和远程执行

大多数 go 命令（包括 go build、go doc、go get、go install 和 go list）的设计目标之一就是不会运行从 internet 下载的任何代码。这里有几个明显的例外：很显然 go run，go test 和 go generate 会运行任意代码。（毕竟这是它们工作）。但是其他的命令就不行，因为各种各样的原因，包括可复制的构建和安全性。因此 go get 可以被诱骗执行任意代码，我们认为这是一个安全缺陷。

如果 go get 不能运行任何代码，那么很不幸，这意味着它涉及的所有程序，比如编译器和版本控制系统，也都在安全范围内。例如，我们过去遇到过这样的问题：在版本控制系统中巧妙使用晦涩难懂的编译器特性或者远程执行bugs，就变成了在Go中远程执行bug。（关于这一点，go1.16 旨在通过引入一个 GOVCS 的设置来改善这种情况，通过该配置可以准确配置允许哪些版本控制系统以及何时允许。）

然而，今天的 bug 完全是我们的错。不是 gcc 或 git 的bug或模糊特性。这个 bug 涉及到 Go 和其他程序如何找到其他的可执行文件。因为在了解细节之前，我们需要花一点时间来研究它。

## 命令、可执行路径和Go语言

所有操作系统都有一个可执行路径的概念（Unix 上是`$path`，Windows 上是 `%PATH%`，为简单起见，我们只用术语`PATH` ），这是一个目录列表。在 shell 提示符键入命令时，shell 会依次在每一个目录里面寻找你键入的可执行文件。它要么运行找到的第一个命令或者打印一条类似于 “command not found” 的消息。

在 Unix 上，这个想法首先出现在第七版 `Unix's Bourne shell (1979)` 。手册解释说：

> shell 参数 $PATH 定义了包含命令行的目录的搜索路径。每个备选目录名用冒号（：）分割。默认路径是：/bin:/usr/bin。如果命令包含`/` 则不使用搜索路径。否则，将在路径中的每个目录搜索可执行文件。

注意默认值：当前目录（这里用空字符串表示，但我们称之为`dot`）列在 /bin 和 /usr/bin 之前。MS-DOS 和 Windows 选择了硬编码这种行为：在这些系统上，总是首先自动搜索 dot ，然后再考虑 `%PATH%`中列出的目录。

正如 Grampp 和 Morris 在他们的经典论文 [“UNIX操作系统安全性”](chrome-extension://ikhdkkncnoglghljlkmcimlnlhkeamad/pdf-viewer/web/viewer.html?file=https%3A%2F%2Fpeople.engr.ncsu.edu%2Fgjin2%2FClasses%2F246%2FSpring2019%2FSecurity.pdf)（1984）中指出的那样：`PATH`中将 dot 放在系统目录前面，意味着如果你 cd 进入某个目录并运行 ls ,那么你有可能得到的是该目录的恶意副本而不是系统实用程序。如果你可以欺骗系统管理员用 root 用户身份登录，在主目录运行 ls ，那么你可以运行任何你想要运行的代码。由于这个问题和其他类似的问题，基本上所有现代 Unix 发行版本都将新用户的默认 PATH 设置为排除 dot，但 Windows系统仍然会先搜索 dot，不管 PATH 怎么说。

例如，你输入命令 

```shell
go version
```

在典型配置 Unix 上，shell 从你的`PATH`中的系统目录运行 go 可执行文件。但当你在 Windows 输入命令时，`cmd.exe`会先检查 dot。如果 .\go.exe（或者 .\go.bat 或者许多其他选择）存在，`cmd.exe`会直接运行一个可执行的，而不是从你的`PATH`找一个。

对于 Go 语言来说，PATH 的搜索由 [exec.LookPath](https://pkg.go.dev/os/exec#LookPath) 处理，被[`exec.Command`](https://pkg.go.dev/os/exec#Command) 自动调用。为了更好地融入主机系统，Go语言的`exec.LookPath` 在Unix上实现了Unix规则并且在 Windows 上实现了 Windows 规则。比如下面这个命令

```go
out, err := exec.Command("go", "version").CombinedOutput()
```

当在操作系统 shell命令窗口 键入 go version 时，大家行为都一样。在 Windows 上，如果 `.\go.exe` 存在的话，会直接运行。（值得注意的是，Windows PowerShell 改变了这种行为，删除了 dot 的隐式搜索，但是 `命令行程序.exe`和 Windows  C 库的 SearchPath 函数还是继续延续了这种行为。Go 继续匹配命令行程序）

## 关于这个Bug

当 go get 下载并构建一个包含`import "C"`包时，它会运行一个名为`cgo`的程序来准备与相关 C 代码等价的 Go 代码 。go 命令在包含有包的源代码的目录下运行 cgo 。一旦 cgo 生成了它的Go语言的输出文件，Go 命令本身就会调用生成的 Go 文件上的 Go 编译器和宿主的 C 编译器（gcc 或 clang）来构建该包中所有 C 源文件。所有的这些运行良好，但是 Go 命令去哪里找宿主机上 C 编译器呢。当然，看起来像是在 `PATH` 里面。幸运的是，当它在包源文件目录下运行 C 编译器时，它从调用 go 命令的原始目录找到了 PATH ：

```go
cmd := exec.Command("gcc", "file.c")
cmd.Dir = "badpkg"
命令行程序Run()
```

因此，即使 Windows 系统上存在`badpkg\gcc.exe` 该代码块也不会找到它。发生在 `exec.Command`的查找不知道 `badpkg` 目录。

go 命令使用同样的代码来调用 cgo，在这种情况下甚至没有路径查找，因为 cgo 总是来自于GOROOT：

```go
cmd := exec.Command(GOROOT+"/pkg/tool/"+GOOS_GOARCH+"/cgo", "file.go")
cmd.Dir = "badpkg"
cmd.Run()
```

这个代码甚至要比之前的代码块更安全：没有机会运行任何可能存在的坏 `cgo.exe`

但事实证明，cgo自己也会调用宿主机的 C 编译器，来产生一些零时文件。以为它会执行以下代码：

```go
// running in cgo in badpkg dir
cmd := exec.Command("gcc", "tmpfile.c")
cmd.Run()
```

现在，因为 cgo本身运行在 `badpkg`中，而不是 go 命令运行的目录。所以如果`badpkg\gcc.exe`文件存在的话，会直接运行`badpkg\gcc.exe`，而不是去找系统的 gcc 。

因此，攻击者可以创建一个使用 cgo 并包含 `gcc.exe`的恶意包。然后，任何 Windows 用户运行 go get  来下载并构建攻击者的包，会优先运行攻击者提供的 `gcc.exe` 而不是系统路径下的任何 gcc 。

Unix 用户首先避免了该问题，因为 dot 通常不在`PATH`里面。其次是因为模块解包不会在它写的文件上设置执行位。但是 Unix 用户如果在他们的 PATH 中存在 dot 优先于系统目录，并且使用`GOPATH`模式，也会像 Windows 用户一样受影响。（如果这是对你的描述，今天是一个好日子，来把 dot 从你的PATH 里面移走，并且开始使用 Go modules。）

（多谢 [RyotaK](https://twitter.com/ryotkak) 向我们[报告这个问题](https://golang.org/security)）

## 解决方案

很明显用 go get 命令下载并运行恶意的`gcc.exe` 是不可接受的。但真正的错误是什么？解决办法又是什么？

一个可能的答案是，该错误是 cgo 在不受信任的目录中搜寻宿主机的 C 编译器，而不是在 go 命令调用的目录搜寻。如果这是错误的，那么修复的办法是更改 go 命令，将完整的宿主机 C 编译器的路径传给 cgo ，这样 cgo 就不用在不受信任的目录中进行路径查找。

另外一个可能的答案是，错误是在 PATH 查找路径中找到了 dot 。无论是在 Windows 上自动执行还是由于在 Unix 系统  PATH 显式输入了。用户可能希望查看 dot 来查找他们在控制台或者 window shell  中键入的命令，但是他们不太可能希望在那里查找键入命令的子进程的子进程。

我们认为这两个都是错误，因此我们同时应用了这两个补丁。现在 go 命令将宿主机 C  编译器的完整路径传递给 cgo 。除此之外，cgo、go、和 go 发行版中其他命令都使用`os/exec`包的实例。如果它曾经使用的是 dot 的可执行文件，那么就会报错。`go/build` 和  `go/import`包调用 go 命令和其他工具时使用相同的策略。这样就可以排除任何可能存在的类似的安全问题。

出于过分的谨慎，我们还对`goimports`和`gopls`等命令以及库`golang.org/x/tools/go/analysis`和`golang.org/x/tools/go/packages`进行了类似的修复，这些库将 go 命令作为子进程调用。如果你在不可信的目录代码运行这些程序（比如你 git checkout 到不可信的仓库并且 cd 进入其中，然后运行类似的程序，而且你使用的是 Windows 或者 在你的PATH中加入了 dot 的 Unix）那么你也应该更新这些命令的副本。如果你计算机上唯一不受信任的目录是go get 管理的模块缓存中的目录，那么你只需要新的 go 版本。

更新到新的 Go 版本后，你可以通过下面方式更新到最新的`gopls`

```go
GO111MODULE=on \
go get golang.org/x/tools/gopls@v0.6.4
```

 你可以通过下面方式更新最新的 `goimports`和其他工具

```go
GO111MODULE=on \
go get golang.org/x/tools/cmd/goimports@v0.1.0
```

你可以更新依赖于`golang.org/x/tools/go/packages`的程序，甚至在它们的作者之前，通过在go get中添加一个显式的依赖升级:

```go
GO111MODULE=on \
go get example.com/cmd/thecmd golang.org/x/tools@v0.1.0
```

对于使用 `go/build` 的程序，使用更新的 go 版本重新编译就够了。

同样，如果你是 Windows 用户 或者是 在 PATH 中使用了 dot的用户，并且你在不信任的可能包含恶意程序的源目录里面运行这些程序，则只需要更新这些程序。

## 你的代码受影响了吗

如果你的代码里使用了 `exec.LookPath` 或者 `exec.Command` 你只需要担心你（或者你的客户）是否在包含不可信内容的目录中运行程序。如果是这样，那么就可以使用 dot 中的可执行文件启动子进程，而不是系统目录。（同样， 使用来自 dot 的可执行文件通常发生在 Windows 上，和非常规`PATH`设置的Unix上。 ）

如果你担心的话，我们已经发布了更受限制的`os/exec`变体  [`golang.org/x/sys/execabs`](https://pkg.go.dev/golang.org/x/sys/execabs) 只需要简单替换

```go
import "os/exec"
```

为

```go
import exec "golang.org/x/sys/execabs"
```

然后重新编译下即可。

## 默认情况下保护`os/exec`

我们一直在讨论[golang.org/issue/38736](https://golang.org/issue/38736)，Windows 在 PATH 查找中首选当前目录的行为（在执行`exec.Command`和 `exec.LookPath` 过程中）是否应该改变。赞成这一改变的理由是，它结束了本文讨论的各种安全问题。一个支持的论据是尽管 Windows SearchPath API 和 `cmd.exe` 仍然总是搜索当前目录。`cmd.exe` 的继任者 PowerShell 没有明显认识到最初的行为是一个错误。反对这一更改的理由是，它可能会破坏原本就打算在当前目录中查找程序的现有 Windows 程序。我们不知道有多少这样的程序存在，但是如果在 PATH 查找过程中完全跳过当前目录，可能会出现无法解释的失败。

我们在`golang.org/x/sys/execabs` 中采取的办法可能是一个中间办法。它会在旧的 PATH 查找中找到结果，然后会返回一个明确的错误而不是使用当前目录的结果。当 `prog.exe` 存在时，`exec.Command("prog")` 会返回一个类似错误：

```shell
prog resolves to executable in current directory (.\prog.exe)
```

对于确实改变行为的程序，这个错误很清楚显示了发生了什么。打算从当前目录运行的程序可以使用`exec.Command("./prog")` 代替。（这个语法适用于所有系统，甚至是 Windows）

我们已经把这个想法作为一个新的提案交了，[golang.org/issue/43724](https://golang.org/issue/43724)。
