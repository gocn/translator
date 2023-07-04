# 在本地构建你的 Golang 包文档

- 原文地址：https://mdaverde.com/posts/golang-local-docs/
- 原文作者：***Milan***
- 本文永久链接：https://github.com/gocn/translator/blob/master/2023/w22_Build_your_Golang_package_docs_locally.md
- 译者：[朱亚光](https://github.com/zhuyaguang)
- 校对：[吴雨浩](https://github.com/haoheipi)

从本地主机预览你的 Golang  HTML 文档。

## 编写 Golang 文档

最近我专注于 [eBPF](https://bpfdeploy.io/)，需要写比以前更多的东西。这也意味着要为各种生态系统撰写[文档](https://mdaverde.com/posts/hot-reloading-cargo-docs)。虽然某些工具在作者完成工作时产生阻力，但本文介绍我目前为编写 Golang 文档而设置的工作流程。

###  `godoc` 已被弃用

与我的 Rust 设置类似，我想在发布之前本地查看我的模块文档在 [pkg.go.dev](https://pkg.go.dev/) 上的呈现方式。这是[可能的](https://stackoverflow.com/a/13530336/1879774)，但自那时起 `godoc` 就已被[弃用](https://github.com/golang/go/issues/49212)，没有官方解决方案。

现在的建议是指导用户使用 [pkgsite](https://github.com/golang/pkgsite/tree/master/cmd/pkgsite)（用于渲染 pkg.go.dev 的工具），但确切的设置方式留给用户来[练习](https://github.com/golang/go/issues/40371)。

那我们开始练习吧。

## `pkgsite` 命令

[golang/pkgsite](https://github.com/golang/pkgsite) hosts the cli pkg.go.dev uses for docs rendering. The comments of the `pkgsite` cmd are [concise](https://github.com/golang/pkgsite/blob/master/cmd/pkgsite/main.go#L5) but can get us started:

[golang/pkgsite](https://github.com/golang/pkgsite) 托管了用于渲染文档的 `pkg.go.dev` 命令行界面。 `pkgsite` 命令的[注释](https://github.com/golang/pkgsite/blob/master/cmd/pkgsite/main.go#L5)虽然简洁，但可以让我们开始：

```
// Pkgsite 提取和生成 Go 程序的文档。
// 它作为 Web 服务器运行，将文档呈现为 Web 页面。
//
// 要安装，请从 pkgsite 存储库根目录运行 `go install ./cmd/pkgsite`。
```

我们将使用它来设置一个本地服务器版本的 `pkg.go.dev`，其中包含 Golang 包的文档渲染功能。所以让我们安装它。我在其他地方看到的建议是本地克隆此存储库，构建它并将其安装在 `$PATH` 中的某个位置，但这个 `go install` 应该就可以工作：

```
$ go install golang.org/x/pkgsite/cmd/pkgsite@latest
```

一旦安装完成，只需将其运行在我们的 Go 包仓库所在的位置即可：

```
$ cd /path/to/go/pkg
$ pkgsite
2022/06/16 10:13:55 Info: Listening on addr http://localhost:8080
```

你可以使用 `-http localhost:3030` 自定义绑定端口。

打开本地站点将显示一个类似于 pkg.go.dev 的页面，包含搜索栏和其他内容。当然，如果你进行搜索，你不会看到任何包，因为我们只渲染了本地包（虽然有一些参数可以更改这个行为）。

### 你的本地文档

现在，类似于 pkg.go.dev，你可以通过将 `go.mod` 中的模块路径附加到 URL 上来检查本地模块的文档：

```
http://localhost:8080/my/local/module/path
```

就是这样。现在你可以以 Web 形式查看你编写的模块文档了。只需安装 `pkgsite`，你就可以在发布之前预览 Go 项目的文档长什么样了。

但是，我们能不能进一步推动它呢？我不想手动保存文件，在思考之间杀死服务器，再重新启动服务器并刷新页面。我希望只需打开一个浏览器标签即可在我的文本编辑器中输入时渲染页面。

## 热加载

为此，我们需要更多的工具。一个用于监视我们的 Go 文件何时发生更改，另一个用于与我们的浏览器通信何时重新加载页面。理想情况下，这应该是一个_单独的_工具来完成（也许有一天 `pkgsite` 会内置这个功能...）。如果你来自前端 JavaScript 的世界，这是基本操作，通常会伴随着框架的工具。现在我们要开始工作了。

我选择的文件监视工具是 [nodemon](https://nodemon.io/)。它的工作表现很好，并且在需要时可以配置它（我们将需要这样做）。起初，我想找一个基于 Go 的文件监视器，但我找不到任何一个能满足我的需求。我甚至尝试将 [cosmtrek/air](https://github.com/cosmtrek/air) 强行塞进这个角色，但没有成功。

现在我们有了一个文件监视器，我们希望告诉浏览器何时重新加载页面。我们将使用 [browser-sync](https://browsersync.io/) 来实现这一点。

### 终端命令

以下是我们将使用的关键命令。为每个进程打开一个新终端，或者只是将其中一个放在后台：

```
$ browser-sync start --proxy "localhost:8080"
[Browsersync] Proxying: http://localhost:8080
[Browsersync] Access URLs:
 --------------------------------------
       Local: http://localhost:3000
    External: http://192.168.1.227:3000
 --------------------------------------
          UI: http://localhost:3001
 UI External: http://localhost:3001
 --------------------------------------
```

我们需要设置这个代理的原因是，我们需要一种自动通知浏览器某些东西已经改变的方式。为此，`browser-sync` 在我们的请求中注入了一小段 JavaScript 代码，它会监听一个信号以确定何时重新加载。

```
$ nodemon --signal SIGTERM --watch my-mod.go --exec "browser-sync reload && pkgsite ."
[nodemon] 2.0.16
[nodemon] to restart at any time, enter `rs`
[nodemon] watching path(s): my-mod.go
[nodemon] starting `browser-sync reload && pkgsite .`
```

这就是我们创建该信号的方式。`nodemon` 监视 `my-mod.go` 的文件更改，并自动重新启动 `pkgsite` 进程，同时向 `browser-sync` 发送信号。

## 总结

当这两个工具并行运行时，你现在应该具备了自动化的文档重载功能。我现在可以在我的文本编辑器中编写[go doc](https://go.dev/doc/comment) 注释，保存文件并查看选项卡重新加载。

现在没有借口不写注释了，但开发体验仍可以更好。显然除了设置这个痛苦之外，重新加载的速度也比必要的慢。我们不应该等待整个进程启动，然后再等待它渲染我的本地模块，才能在浏览器标签中看到它。

也许当你阅读这篇文章时，那个 [pkgsite 问题](https://github.com/golang/go/issues/40371) 已经解决了，并且会存在更多针对文档的工具。或者也许我会有一个空闲的周末，可以发送一些 PR。
