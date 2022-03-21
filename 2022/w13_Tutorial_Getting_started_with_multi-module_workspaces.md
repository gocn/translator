- 原文地址：https://go.dev/doc/tutorial/workspaces
- 原文作者：**go.dev**
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w13_Tutorial_Getting_started_with_multi-module_workspaces.md
- 译者：[Jancd](https://github.com/Jancd)
- 校对：

# 教程：开始使用多模块工作区模式

内容列表
- [前期准备](#前期准备)
- [为你的代码创建一个模块](#为你的代码创建一个模块)
- [创建工作区](#创建工作区)
- [下载并修改`golang.org/x/example`模块](#下载并修改-golang.org/x/example-模块)
- [了解有关工作区的更多信息](#了解有关工作区的更多信息)

本教程介绍了 Go 中多模块工作区的基本知识。通过多模块工作区，将可以同时编写多个模块的代码，并轻松地在这些模块中构建和运行代码。

在本教程中，你将在一个共享的多模块工作空间中创建两个模块，对这些模块进行修改，并在构建中检验这些修改的结果。

**提示**: 对于其他教程, [更多请看](https://go.dev/doc/tutorial/index.html).

## 前期准备

- **安装了 Go 1.18 或更高版本**.
- **一个编辑你的代码的工具**，任何文本编辑器都可以正常工作。
- **一个命令终端**， Go 在 Linux 和 Mac 上的任何终端以及 Windows 中的 PowerShell 或 cmd 上都能很好地工作。

本教程需要 go1.18 或更高版本。 使用 `go.dev/dl` 中的链接，确保你已使用 Go 1.18 或更高版本。

## 为你的代码创建一个模块

首先，为你的代码创建一个模块。

1. 打开命令行，进入到你的 `home` 目录。

在 Linux 或 Mac 上:

```shell
$ cd
```
在 Windows 上:

```shell
C:\> cd %HOMEPATH%
```

教程的其余部分将显示 `$` 作为命令行提示。同理，这些命令在 Windows 上也可以使用。

2. 在命令行下，为你的代码创建一个名为 `workspace` 的目录。

```shell
$ mkdir workspace
$ cd workspace
```

3. 初始化模块

为例子创建一个新的模块 `hello`，它将依赖于 `golang.org/x/example` 模块。

创建 `hello` 模块。

```shell
$ mkdir hello
$ cd hello
$ go mod init example.com/hello
go: creating new go.mod: module example.com/hello
```

通过使用 `go get` 添加对 `golang.org/x/example` 模块的依赖。

```shell
$ go get golang.org/x/example
```

在 `hello` 目录下创建 `hello.go`，内容如下。

```go
package main

import (
    "fmt"

    "golang.org/x/example/stringutil"
)

func main() {
    fmt.Println(stringutil.Reverse("Hello"))
}
```

执行 `hello` 程序:

```shell
$ go run example.com/hello
olleH
```

## 创建工作区

在这一步，我们将创建一个 `go.work` 文件，以指定一个带有模块的工作空间。

### 初始化工作区

在工作区目录中，执行：

```shell
$ go work init ./hello
```

`go work init` 命令会让 go 为包含 `./hello` 目录下的模块的工作空间创建一个 `go.work` 文件。

这个 go 命令产生一个 `go.work` 文件，看起来像这样。

```shell
go 1.18

use ./hello
```

`go.work` 文件的语法与 go.mod 相似。

这个指令让 go 编译器明确应该用哪个版本的 go 来解释该文件。它与 `go.mod` 文件中的 go 指令类似。

`use` 指令告诉 go 编译器，在进行构建时，`hello` 目录下的模块应该是主模块。

因此，在工作区的任何子目录中，该模块都将处于活跃状态。

### 运行工作区目录下的程序

在 `workspace` 目录中，运行：

```shell
$ go run example.com/hello
olleH
```
这个 go 命令将工作区中的所有模块都作为主模块。这样，我们就可以引用模块中的包，甚至在模块之外的包。在模块或工作区之外运行 `go run` 命令会导致错误，因为 `go` 命令不知道要使用哪些模块。

接下来，我们将在工作区添加一个 `golang.org/x/example` 模块的本地拷贝。然后我们将在 `stringutil` 包中添加一个新的函数，我们可以用它代替 `Reverse`。

## 下载并修改`golang.org/x/example`模块

在这一步，我们将下载一份包含 `golang.org/x/example` 模块的 git 管理仓库副本，将其添加到工作区，然后为其添加一个新函数，我们将在 `hello` 程序中使用该函数。

1. 拷贝代码仓库

在工作区目录下，运行 git 命令来拷贝代码仓库：

```shell
$ git clone https://go.googlesource.com/example
Cloning into 'example'...
remote: Total 165 (delta 27), reused 165 (delta 27)
Receiving objects: 100% (165/165), 434.18 KiB | 1022.00 KiB/s, done.
Resolving deltas: 100% (27/27), done.
```

2. 将该模块添加到工作区

```shell
$ go work use ./example
```

`go work use` 命令在 `go.work` 文件中增加了一个新模块。现在它的布局如下：

```shell
go 1.18

use (
    ./hello
    ./example
)
```

该模块现在同时包括 `example.com/hello` 模块和 `golang.org/x/example` 模块。

这将使我们能够使用我们将在 `stringutil` 模块副本中编写的新代码，而不是我们用 `go get` 命令下载的模块缓存中的模块版本。

3. 添加新函数

我们将在 `golang.org/x/example/stringutil` 包中添加一个新的函数来对字符串进行大写。

在 `workspace/example/stringutil` 目录下添加一个新的文件夹，包含以下内容。

```go
package stringutil

import "unicode"

// ToUpper uppercases all the runes in its argument string.
func ToUpper(s string) string {
    r := []rune(s)
    for i := range r {
        r[i] = unicode.ToUpper(r[i])
    }
    return string(r)
}
```

4. 修改 `hello` 程序以使用该函数

修改 `workspace/hello/hello.go` 的内容，如下：

```go
package main

import (
    "fmt"

    "golang.org/x/example/stringutil"
)

func main() {
    fmt.Println(stringutil.ToUpper("Hello"))
}
```

### 在工作区执行代码

从工作区目录，执行：

```shell
$ go run example/hello
HELLO
```

这个 go 命令在 `go.work` 文件指定的 `hello`目录下找到命令行中指定的 `example.com/hello` 模块，并同样使用 `go.work` 文件解析 `golang.org/x/example` 导入。

`go.work`可以用来代替添加替换指令，便于在多个模块间工作。

由于这两个模块在同一个工作区，所以很容易出现在一个模块中做出改变并在另一个模块中使用的情况。

### 版本控制

现在，为了正确发布这些模块，我们需要对 `golang.org/x/example` 模块进行版本发布，例如 `v0.1.0` 。这通常是通过在模块的版本控制库中标记一个提交来完成的。更多细节见[模块发布工作流程文档](https://go.dev/doc/modules/release-workflow)。一旦发布完成，我们可以在 `hello/go.mod` 中增加对 `golang.org/x/example`模块的版本约束。 

```shell
cd hello
go get example.com/dep@v0.1.0
```

这样， go 命令可以正确解析工作区之外的模块。

## 了解有关工作区的更多信息

除了我们在本教程前面看到的 `go work init` 之外，还有几个子命令用于处理工作空间。

- `go work use [-r] [dir]` 在 `go.work` 文件中会将目录 `dir` 作为一个模块，如果目录不存在，则放弃使用目录。`-r` 标志会递归地检查dir的子目录。
- `go work edit` 编辑 `go.work` 文件，与`go mod edit`类似。
- `go work sync` 将工作区构建列表中的依赖项同步到每个工作区模块中。

关于工作空间和 `go.work` 文件的更多细节，[请参见 go modules 的文章](https://go.dev/ref/mod#workspaces)。