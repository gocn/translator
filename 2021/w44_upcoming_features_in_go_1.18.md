# GO 1.18 中即将出现的特性功能
Go 1.18 将是 Go 语言的一个重要版本，它将包含一些令我兴奋的主要功能。即将到来的版本计划在 2021 年初发布。第一个测试版应该会在一个月内推出。让我们来提前看看将有哪些新功能被加入到这个版本中。

## 范型
期待已久的泛型支持将在 Go 1.18 中出现。Go 中缺乏泛型是开发者社区批评的最大问题。从设计阶段到将在 Go 1.18 中出现的实际实现，花了好几年时间。

这个话题太大，无法在这篇博文中详细解释。已经有很多关于它的好博文了。以下是我最喜欢的一篇，涵盖了所有相关方面：
 [https://bitfieldconsulting.com/golang/generics](https://bitfieldconsulting.com/golang/generics)。 如果你想玩 Go 泛型，[这里](https://go2goplay.golang.org/)有一个托管的 Go Playground 可供选择。

## 工作空间（WORKSPACES）
工作区使开发者能够更容易地同时处理多个模块的工作。在 Go 1.17 之前，这只能通过`go.mod``replace`指令来实现，如果你有很多模块在开发中，使用这个指令会很痛苦。同样令人痛苦的是，每次你想提交你的代码时，你必须删除`replace`行，以便能够使用一个模块的 稳定/发布 版本。

有了工作区，这些开发情况的处理就简单多了。一个名为`go.work`的新文件可以被添加到项目中，它包含了依赖模块的本地开发版本的路径。`go.mod`保持不动，不需要使用`replace`指令。
```go
go 1.17

directory (
    ./baz // contains foo.org/bar/baz
    ./tools // contains golang.org/x/tools
)

replace golang.org/x/net => example.com/fork/net v1.4.5
```

在通常的项目情况下，建议不要提交`go.work`文件，因为它的主要使用情况是本地开发。

如果你想在本地构建你的项目而不使用工作区功能，你可以通过提供以下命令行标志来实现：
```sh
go build -workfile=off
```
通过像这样运行`go build`命令，你可以确保你的项目在构建时没有依赖模块的本地开发版本。
## 官方模糊测试支持
在 Go 1.18 中也将提供正式的模糊测试支持。模糊功能将被视为实验性的，API 还没有被 Go 1 的兼容性承诺所覆盖。它应该作为一个概念验证，Go 团队请求社区提供反馈。

如果你还没有听说过模糊测试，测试版公告的[博文](https://go.dev/blog/fuzz-beta)对它进行了很好的描述：

***模糊测试是一种自动化测试，它持续操纵程序的输入，以发现问题，如 panic 或 bug。这些半随机的数据突变可以发现现有单元测试可能遗漏的新的代码覆盖范围，并发现被忽略或者未被覆盖的边缘案例的错误。由于模糊测试可以接触到这些边缘案例，所以模糊测试对于发现安全隐患和漏洞特别有价值。***

你可以在[这里](https://go.googlesource.com/proposal/+/master/design/draft-fuzzing.md)阅读 Katie Hockman 的设计文档。 还有[Go Time 播客集](https://changelog.com/gotime/187)，与 Katie 一起讨论的这个话题。
## 新的软件包 net/netip
新包`net/netip`增加了一个新的 IP 地址类型，与`net.IP`类型相比，它有很多优点。 简单来说：它很小，可比较，而且没有内存分配操作。 已经有一篇来自 Brad Fitzpatrick 的[详细博文](https://tailscale.com/blog/netaddr-new-ip-type-for-go/)介绍了所有的细节。如果你喜欢视频，在[布拉德在 FOSDEM 2021 的演讲](https://www.youtube.com/watch?v=csbE6G9lZ-U&t=1125s) 中也有一段介绍，从时间 18:45 开始观看。

## 更快的（？）go fmt 运行
`go fmt`命令现在以并行方式运行格式化。正如[Github issue](https://github.com/golang/go/issues/43566)中描述的那样，格式化大型代码库的速度应该会快很多。
> 但我很困惑为什么在我的机器上进行第一次测试时没有发现快很多，它变得更糟糕了。

The `go fmt` command runs formatting in parallel now. As described in the [Github issue](https://github.com/golang/go/issues/43566), formatting large codebases should be much faster - but I was wondering why I didn’t notice it in a first test on my machine. It got much worse.

我在我的 Macbook Pro 2019(2,6 GHz 6-Core Intel Core i7, 16 GB 2667 MHz DDR4) 的[CockroachDB 仓库](https://github.com/cockroachdb/cockroach)上用以下命令进行测试：
```sh
time go test ./pkg/...
```
使用 Go 1.17，花了**56 秒**来格式化所有文件。使用最新的`gotip`版本，花了**1分 20 秒**。我还不得不提高我机器上的 ulimit，以防止崩溃。让我们看看这个功能在稳定版之前是如何发展的。

## 试用即将推出的特性功能
你也可以直接在你的机器上玩最新的实验性 Go 版本`gotip`。当你已经安装了稳定版本的 Go，你只需要运行：
```sh
go install golang.org/dl/gotip@latest
gotip download
```
当安装成功后，你可以像通常的`go`命令一样使用`gotip`命令的所有子命令。

这篇博文并没有涵盖 Go 1.18 中的所有新功能。如果你想阅读所有的错误修复和新功能特性，你可以在[这里](https://dev.golang.org/release#Go1.18)看 Go 1.18 的问题列表。