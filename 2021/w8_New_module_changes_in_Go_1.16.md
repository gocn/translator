# Go 1.16 中 Module 功能新变化

原文地址：https://blog.golang.org/go116-module-changes
原文作者：Jay Conrod
本文永久链接：https://github.com/gocn/translator/blob/master/2021/w8_New_module_changes_in_Go_1.16.md
译者：Kevin
校对：

希望您喜欢 Go 1.16! 这个版本有很多新功能，特别是对 Module 而言。[发行说明](https://golang.org/doc/go1.16)中简要介绍了这些变化，但让我们深入发掘一下其中的一些变化。

## Module 功能默认开启

go 命令现在默认以 module-aware 模式构建包，即使没有`go.mod`文件存在。这是向在所有项目中使用 Module 功能迈出的一大步。

通过设置`GO111MODULE`环境变量为`off`，仍然可以在`GOPATH`模式下构建包。你也可以将`GO111MODULE`设置为`auto`，只有当当前目录或任何父目录中存在`go.mod`文件时才启用 module-aware 模式。这在以前是默认的。请注意，您可以使用`go env -w`来永久地设置`GO111MODULE`和其他变量。

```plain
go env -w GO111MODULE=auto
```

我们计划在 Go 1.17 中放弃对`GOPATH`模式的支持。换句话说，Go 1.17 将忽略`GO111MODULE`。如果您的项目没有以 module-aware 模式构建，现在是时候迁移了。如果有问题妨碍您迁移，请考虑提交[问题](https://github.com/golang/go/issues/new)或[体验报告](https://github.com/golang/go/wiki/ExperienceReports)。

## 不会自动更改 go.mod 和 go.sum

在之前的版本中，当`go`命令发现`go.mod`或`go.sum`有问题时，比如缺少`require`指令或缺少`sum`，它会尝试自动修复问题。我们收到了很多反馈，认为这种行为是出乎大家意料的，尤其是对于像`go list`这样通常不会产生副作用的命令。自动修复并不总是可取的：如果一个导入的包没有被任何需要的 Module 提供，`go`命令会添加一个新的依赖关系，可能会触发普通依赖关系的升级。即使是拼写错误的导入路径也会导致（失败的）网络查找。

在 Go 1.16 中，module-aware 命令在发现`go.mod`或`go.sum`中的问题后会报告一个错误，而不是尝试自动修复问题。在大多数情况下，错误信息建议使用命令来修复问题。

```plain
$ go build
example.go:3:8: no required module provides package golang.org/x/net/html; to add it:
    go get golang.org/x/net/html
$ go get golang.org/x/net/html
$ go build
```

和之前一样，如果存在`vendor`目录，`go`命令可能会使用该目录（详见[`Vendoring`](https://golang.org/ref/mod#vendoring)）。像`go get`和`go mod tidy`这样的命令仍然会修改`go.mod`和`go.sum`，因为它们的主要目的是管理依赖关系。

## 在特定版本上安装可执行文件

`go install`命令现在可以通过指定`@version`后缀来安装特定版本的可执行文件。

```plain
go install golang.org/x/tools/gopls@v0.6.5
```

当使用这种语法时，`go install`命令会从该 Module 的制定版本安装，而忽略当前目录和父目录中的任何 go.mod 文件。(如果没有@version 后缀，go install 会像往常一样继续运行，使用当前 Module 的 go.mod 中列出的版本要求和替换来构建程序。)

我们曾经推荐使用`go get -u`程序来安装可执行文件，但这种使用方式对`go.mod`中添加或更改 Module 版本需求的意义造成了太多的混淆。而为了避免意外修改`go.mod`，人们开始建议使用更复杂的命令，比如：

```plain
cd $HOME; GO111MODULE=on go get program@latest
```

现在我们都可以用`go install program@latest`来代替。详情请看[go install](https://golang.org/ref/mod#go-install)。

为了消除使用哪个版本的歧义，当使用这种安装语法时，对程序的 go.mod 文件中可能存在的指令有一些限制。特别是，至少在目前，替换和排除指令是不允许的。从长远来看，一旦新的`go install program@version`在足够多的用例中运行良好，我们计划让`go get`停止安装命令二进制文件。详情请参见[issue 43684](https://golang.org/issue/43684)。

## Module 撤回

您是否曾经在 Module 版本准备好之前不小心发布过？或者您是否在版本发布后就发现了一个需要快速修复的问题？发布的版本中的错误是很难纠正的。为了保持 Module 构建的确定性，一个版本在发布后不能被修改。即使你删除或更改了版本标签，[`proxy.golang.org`](https://proxy.golang.org/)和其他代理可能已经有了原始版本的缓存。

Module 作者现在可以使用`go.mod`中的`retract`指令撤回 Module 版本。撤回的版本仍然存在，并且可以被下载（所以依赖它的构建不会中断），但在解析`@latest`这样的版本时，`go`命令不会自动选择它，`go get`和`go list -m -u`会打印关于现有使用版本的警告。

例如，假设一个流行库`example.com/lib`的作者发布了`v1.0.5`，然后发现了一个新的安全问题。他们可以在他们的 go.mod 文件中添加如下指令。

```plain
// Remote-triggered crash in package foo. See CVE-2021-01234.
retract v1.0.5
```

接下来，作者可以标记并推送`v1.0.6`版本，即新的最高版本。在这之后，已经依赖 v1.0.5 的用户在检查更新或升级依赖的软件包时，就会被通知版本撤回。通知信息可能会包含来自`retract`指令上方注释的文字。

```plain
$ go list -m -u all
example.com/lib v1.0.0 (retracted)
$ go get .
go: warning: example.com/lib@v1.0.5: retracted by module author:
    Remote-triggered crash in package foo. See CVE-2021-01234.
go: to switch to the latest unretracted version, run:
    go get example.com/lib@latest
```

关于交互式的、基于浏览器的使用指南，请查看[`play-with-go.dev`](https://play-with-go.dev/)上的[`Retract Module Versions`](https://play-with-go.dev/retract-module-versions_go116_en/)。可以查看[`retract指令文档`](https://golang.org/ref/mod#go-mod-file-retract)以了解语法细节。

## 用 GOVCS 控制版本管理工具

`go`命令可以从[`proxy.golang.org`](https://proxy.golang.org/)这样的镜像中下载 Module 源代码，或者直接从使用`git`、`hg`、`svn`、`bzr`或`fossil`的版本管理仓库中下载。直接的版本控制访问是很重要的，特别是对于那些在代理上无法使用的私有 Module，但这也是一个潜在的安全问题：版本控制工具中的一个 bug 可能会被恶意服务器利用，运行非预期的代码。

Go 1.16 引入了一个新的配置变量`GOVCS`，让用户可以指定哪些 Module 可以使用特定的版本控制工具。`GOVCS`接受一个以逗号分隔的`pattern:vcslist`规则列表。`pattern`是一个[`path.Match`](https://golang.org/pkg/path#Match)模式，匹配一个 Module 路径的一个或多个前缀元素。特殊模式 public 和 private 匹配公共和私有 Module（private 被定义为由 GOPRIVATE 中的模式匹配的 Module；public 是其他所有 Module）。`vcslist`是一个以管道符分隔的允许的版本控制命令列表，或关键字`all`或`off`。

例如

```plain
GOVCS=github.com:git,evil.com:off,*:git|hg
```

在此设置下，路径在`github.com`上的 Module 可以使用`git`下载；路径在`evil.com`上的 Module 不能使用任何版本管理程序下载，其他所有路径（*匹配所有）可以使用`git`或`hg`下载。

如果没有设置`GOVCS`，或者一个 Module 不符合任何模式，`go`命令就会使用这个默认值：公共 Module 允许使用`git`和`hg`，私有 Module 允许使用所有工具。只允许`Git`和`Mercurial`的理由是，这两个系统作为不受信任的服务器的客户端运行的问题最受关注。相比之下，`Bazaar`、`Fossil`和`Subversion`主要是在受信任的、经过认证的环境中使用，作为攻击面的审查程度不高。也就是说，默认的设置是

```plain
GOVCS=public:git|hg,private:all
```

更多细节请参见使用[`GOVCS控制版本管理工具`](https://golang.org/ref/mod#vcs-govcs)。

## 下一步

我们希望您觉得这些功能很有用。我们已经在努力为 Go 1.17 开发新的 Module 功能，特别是[`懒惰Module加载`](https://github.com/golang/go/issues/36460)，这将使 Module 加载过程更快、更稳定。和以往一样，如果您遇到新的 bug，请在[问题跟踪](https://github.com/golang/go/issues)上告诉我们。Happy coding!
