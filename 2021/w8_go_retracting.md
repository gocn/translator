# Go 1.16 新功能：Go Module 支持版本撤回

- 原文地址：https://golangtutorial.dev/tips/retract-go-module-versions/
- 原文作者：Arunkumar Gudelli
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2021/w8_go_retracting.md
- 译者：[咔叽咔叽](https:/github.com/watermelo)
- 校对：[fivezh](https://github.com/fivezh)


Go 1.16 的一个很酷的功能是支持 Go Module 版本撤回。

## 什么是撤回

我们使用版本机制将 Go Module 发布到 Github。

假设其中一个模块带着错误并以新的版本号(v0.1.0)被发布到了产品中。

与此同时，我们发现了这个错误，并发布了一个新的修复版本(v0.2.0)。

我们不能修改 v0.1.0 中的代码，可能有些人已经在使用它们了。

在此之前我们没有好办法去通知用户**不要使用这个版本**。

> **Go 1.16 撤回功能**通过将版本标记为**retract**来解决这个问题。

我们通过一个例子来进一步理解。

首先检查你的 Go 版本，我使用的是 Go 1.16 RC1 版本。

```plain
    go1.16rc1 version

    go version go1.16rc1 windows/amd64
```

按照 [Go-1.16 RC1 released](https://golangtutorial.dev/news/g-1.16rc1-released/) 文章中提到的方法安装 Go 1.16 RC1。

我为这个示例创建了一个 github 仓库。

```plain
    git clone https://github.com/arungudelli/Retract-Go-Module-Versions.git
```

并且使用 Go 1.16 版本创建了一个名为 `hello` 的模块。

```plain
    go1.16rc1 mod init github.com/arungudelli/Retract-Go-Module-Versions

    go: creating new go.mod: module github.com/arungudelli/Retract-Go-Module-Versions
    go: to add module requirements and sums:
            go mod tidy
```

它将生成 `go.mod` 文件。

```plain
    module github.com/arungudelli/Retract-Go-Module-Versions

    go 1.16
```

并创建了一个名为 `hello.go` 的文件，内容如下。

```golang
    package hello

    // Welcome Message
    func Welcome() string {
    	return "Hello, gophers From Go 1.16"
    }
```

我的初始版本已经准备就绪。所以，我需要为模块添加标签并发布。

```plain
    >git tag v0.1.0
    >git push -q origin v0.1.0
```

现在我们能在 github 上看到这个版本了。

![Github version](../static/images/w8_go_retracting/github.png)

为了使用这个模块，我创建了一个 `go` 程序，它将使用 `hello.go` 模块中的功能。

```plain
    go1.16rc1 mod init gopher116
```

`go.mod` 文件。

```plain
    module gopher116

    go 1.16
```

`gopher116.go` 的内容如下。

```golang
    package main

    import (
    	"fmt"

    	"github.com/arungudelli/Retract-Go-Module-Versions"
    )

    func main() {
    	fmt.Println(hello.Welcome())
    }
```

上述的代码包含以下功能，

1.  导入 `github.com/arungudelliRetract-Go-Module-Versions` 包，这样我们就有了对这个包的依赖。
2.  使用 fmt.Println 打印 `hello.Welcome()` 返回的消息。

要添加对 `github.com/arungudelliRetract-Go-Module-Versions` 的依赖，需要使用以下命令。

```plain
    >go1.16rc1 get github.com/arungudelli/Retract-Go-Module-Versions@v0.1.0

    go: downloading github.com/arungudelli/Retract-Go-Module-Versions v0.1.0
    go get: added github.com/arungudelli/Retract-Go-Module-Versions v0.1.0
```

现在我们使用 `go run` 命令来运行这段程序。

```plain
    >go1.16rc1 run .

    //Hello, gophers From Go 1.16
```

## 发布一个新的版本

假设我们需要修改 `gopher116.go` 的消息内容，修改后的代码如下。

```plain
    package hello

    //Welcom message
    func Welcome() string {
    	return "Hello, gophers From Go 1.15"
    }
```

并发布了标签版本为 2（v0.2.0）的包。

```plain
    >git tag v0.2.0
    >git push -q origin v0.2.0
```

我们的程序发现依赖的模块有新版本发布，然后更新了包。

```plain
    > go1.16rc1 get github.com/arungudelli/Retract-Go-Module-Versions@v0.2.0
    go: downloading github.com/arungudelli/Retract-Go-Module-Versions v0.2.0
    go get: upgraded github.com/arungudelli/Retract-Go-Module-Versions v0.1.0 => v0.2.0
```

随后重新运行程序。

```plain
    >go1.16rc1 run .

    //Hello, gophers From Go 1.15
```

我们发现了一个错误，即程序中的 `Go 1.16` 被错误的修改为 `Go 1.15`。


## 撤回 Go Module 版本

GO 1.16 版自带撤回功能。

作为一个发布者，我们必须修复代码，并通知用户版本中所发生的错误。

> **要将 Go module 的版本标记为撤回，需要使用 ‘-retract’ 标志。**

使用 `go mod edit` 命令修改 `go.mod` 文件，然后在后面加上 `-retract` 标志。

```plain
    go1.16rc1 mod edit -retract=v0.2.0
```

这会使 `go.mod` 文件中添加上撤回的版本信息。

```plain
    module github.com/arungudelli/Retract-Go-Module-Versions

    go 1.16

    retract v0.2.0
```

更好的做法是在上面的 `retract` 指令中添加注释，为什么这个版本需要撤回。

```plain
    module github.com/arungudelli/Retract-Go-Module-Versions

    go 1.16

    // Mistake happened in the version DO NOT USE
    retract v0.2.0
```

现在发布新版本的变更。

```plain
    >git tag v0.3.0
    >git push -q origin v0.3.0
```

## 在 Go 中查询撤回的 Module 版本

我们的 `gopher116.go` 仍然使用 `v0.2.0` 版本。

因此，要想知道 Go 中已撤回的模块版本，可以使用 `go list -m -u all` 命令。

```plain
    >go1.16rc1 list -m -u all
    gopher116
    github.com/arungudelli/Retract-Go-Module-Versions v0.2.0 (retracted) [v0.3.0]
```

现在版本 2.0 被标记为 `(retracted)`。

所以我们需要升级到版本 3(v0.3.0)。

```plain
    >go1.16rc1 get github.com/arungudelli/Retract-Go-Module-Versions@v0.3.0

    go: downloading github.com/arungudelli/Retract-Go-Module-Versions v0.3.0
    go get: upgraded github.com/arungudelli/Retract-Go-Module-Versions v0.2.0 => v0.3.0
```

然后重新运行程序。

```plain
    >go1.16rc1 run .

    //Hello, gophers From Go 1.15
```

还是显示的老信息。

因为在第 3 版中，我把第 2 版标记为撤回，但代码没有改变。

所以我们需要把第 3 版也标记为撤回。

## 撤回多个 Go Module 版本

编辑 `go.mod` 文件，并使用下面的命令将版本 3 标记为撤回。

```plain
    go1.16rc1 mod edit -retract=v0.3.0
```

新的 `go.mod` 文件内容如下。

```plain
    module github.com/arungudelli/Retract-Go-Module-Versions

    go 1.16

    retract (
        // Failed to update the message DO NOT USE
    	v0.3.0
    	// Mistake happened in the version DO NOT USE
    	v0.2.0
    )
```

增加了版本 3 的变更原因。

如果需要撤回多个版本，就在 `retract` 指令中逐行添加模块版本。

这次修改的是 `hello.go` 文件中的信息。

```golang
    package hello

    // Welcome Message
    func Welcome() string {
    	return "Hello, gophers From Go 1.16 verion"
    }
```

使用以下命令发布新的版本。

```plain
    >git tag v0.3.1

    >git push -q origin v0.3.1
```

我们的 `gopher116.go` 通过再次运行 `go list` 命令，就可以查询到撤回的包。

```plain
    >go1.16rc1 list -m -u all

    gopher116
    github.com/arungudelli/Retract-Go-Module-Versions v0.3.0 (retracted) [v0.3.1]
```

随后使用 `go get` 命令将包更新为新版本。

```plain
    >go1.16rc1 get github.com/arungudelli/Retract-Go-Module-Versions@v0.3.1

    //go get: upgraded github.com/arungudelli/Retract-Go-Module-Versions v0.3.0 => v0.3.1
```

现在终于解决了这个问题。

```plain
    >go1.16rc1 run .

    //Hello, gophers From Go 1.16 version
```

## 安装最新的且非撤回的 Go Module 版本

要跟踪一个 Go 模块的所有版本是很困难的。

所以要安装最新的且非撤回的 Go 模块版本，请使用 `@latest` 标签来代替版本。

```plain
    >go1.16rc1 get github.com/arungudelli/Retract-Go-Module-Versions@latest

    go get: upgraded github.com/arungudelli/Retract-Go-Module-Versions v0.3.0 => v0.3.1
```

## 列出所有 Go Module 的版本

如果需要列出一个 Go 模块或包的所有版本，请使用 `go list` 命令。

```plain
    >go1.16rc1 list -m -versions github.com/arungudelli/Retract-Go-Module-Versions

    //OUTPUT
    github.com/arungudelli/Retract-Go-Module-Versions v0.1.0 v0.3.1
```

`go list -m -versions` 命令不包括撤回的版本。(v0.2.0 和 v0.3.0 不可见)

## 列出所有已撤回的 Go Module 版本

如果需要列出一个 Go 模块的所有撤回版本，请使用标志 `-retracted` 和 `go list` 命令。


```plain
    >go1.16rc1 list -m -versions -retracted github.com/arungudelli/Retract-Go-Module-Versions

    //OUTPUT
    github.com/arungudelli/Retract-Go-Module-Versions v0.1.0 v0.2.0 v0.3.0 v0.3.1
```

输出中包含了已撤回的版本。

![List all versions of GO Modules](../static/images/w8_go_retracting/Listing-go-module-versions.png)

## 安装撤回的 Go Module 版本

虽然我们将版本标记为撤回，但我们仍然可以下载和使用这些软件包。

例如，如果我们尝试使用 `go get` 命令安装已撤回的模块版本，它将显示警告信息。

```plain
    go1.16rc1 get github.com/arungudelli/Retract-Go-Module-Versions@v0.2.0
    go: warning: github.com/arungudelli/Retract-Go-Module-Versions@v0.2.0: retracted by module author: Mistake happened in the version DO NOT USE
    go: to switch to the latest unretracted version, run:
            go get github.com/arungudelli/Retract-Go-Module-Versions@latestgo get: downgraded github.com/arungudelli/Retract-Go-Module-Versions v0.3.1 => v0.2.0
```

![List all versions of GO Modules](../static/images/w8_go_retracting/Retracted-version-message.png)

显示的提示是在 `go.mod` 文件对应的撤回版本上的注释。

所以在添加撤回版本的同时，需要给用户一个有意义的信息。

你可以下载或者克隆 [示例代码](https://github.com/arungudelli/Retract-Go-Module-Versions).

```plain
    git clone https://github.com/arungudelli/Retract-Go-Module-Versions.git
```

希望你喜欢这篇文章，如果喜欢请与他人分享。

如果有疑问可以在 [twitter](https://twitter.com/arunGudelli), [facebook](https://www.facebook.com/gudelliArun), [github](https://github.com/arungudelli/) 上关注我，与我取得联系。
