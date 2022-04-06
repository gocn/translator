- 原文地址：https://go.dev/blog/get-familiar-with-workspaces
- 原文作者：golang.org
- 本文永久链接：https://github.com/gocn/translator/edit/master/2022/w15_Get_familiar_with_workspaces.md
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：[cvley](https://github.com/cvley)


# 熟悉工作区

Beth Brown, for the Go team
5 April 2022

Go 1.18为Go增加了工作区模式，使你可以同时在多个模块上工作。

你可以通过访问[下载](https://go.dev/dl/)页面获得Go 1.18。[发布说明](https://go.dev/doc/go1.18)有关于所有变化的更多细节。

## 工作区

Go 1.18中的[工作区](https://go.dev/ref/mod#workspaces)可以让你同时处理多个模块，而不必为每个模块编辑go.mod文件。在解决依赖关系时，工作区中的每个模块都被视为根模块。

以前，如果要在一个模块中增加一个功能，并在另一个模块中使用，你需要在第一个模块中发布修改，或者[编辑依赖模块的go.mod](https://go.dev/doc/tutorial/call-module-code)文件，为你的本地未发布的模块变化添加`replace`指令。为了不出错地发布，你必须在向第一个模块发布本地修改后，从依赖模块的`go.mod`文件中删除replace指令。

通过Go工作区，你可以使用工作区目录根部的`go.work`文件来控制所有的依赖关系。`go.work`文件有`use`和`replace`指令，可以覆盖各个`go.mod`文件，所以不需要单独编辑每个`go.mod`文件。

你可以通过运行`go work init`来创建一个工作区，并将模块目录列表作为空格分隔的参数。工作区不需要包含你正在使用的模块。`init`命令创建一个`go.work`文件，列出工作区的模块。如果你在运行`go work init`时没有参数，该命令会创建一个空的工作区。

要向工作区添加模块，可以运行`go work use [moddir]` 或手动编辑`go.work`文件。运行`go work use -r`来递归添加参数目录中带有`go.mod`文件的目录到你的工作区。如果一个目录没有`go.mod`文件，或者不再存在，使用`use`指令的目录将会从`go.work`文件中删除。

`go.work`文件的语法与`go.mod`文件相似，包含以下指令：

- `go`：go工具链的版本，例如：`go 1.18`
- `use`：将磁盘上的一个模块添加到工作区的主模块集合中。它的参数是包含该模块`go.mod`文件的目录的相对路径。`use`指令不会在指定目录的子目录中添加模块。
- `replace`: 与`go.mod`文件中的`replace`指令类似，`go.work`文件中的replace指令用其他地方的内容替换一个模块的*特定版本*或*所有版本*。

## 工作流

工作区是灵活的，支持各种工作流程。以下部分是对我们认为最常见的工作区使用的简要概述。

### 在上游模块中增加一个功能，并在自己的模块中使用它

1. 为你的工作区创建一个目录。
2. 克隆你要编辑的上游模块。如果你以前没有为Go贡献过，请阅读[贡献指南](https://go.dev/doc/contribute)。
3. 将你的功能添加到上游模块的本地版本中。
4. 在工作区文件夹中运行`go work init [path-to-upstream-mod-dir]` 。
5. 对你自己的模块进行修改，以实现添加到上游模块的功能。
6. 在工作区文件夹中运行`go work use [path-to-your-module]`。

   `go work use`命令将模块的路径添加到你的`go.work`文件中：

```
   go 1.18
   
   use (
          ./path-to-upstream-mod-dir
          ./path-to-your-module
   )
```

7. 使用添加到上游模块的新功能运行并测试你的模块。
8. 发布带有新功能的上游模块。
9. 使用新功能发布你的模块。

### 在同一个资源库中与多个相互依赖的模块一起工作

在同一版本库中处理多个模块时，`go.work`文件定义了工作区，而不是在每个模块的`go.mod`文件中使用`replace`指令。

1. 为你的工作区创建一个目录。

2. 克隆你想编辑的模块的版本库。这些模块不一定要在你的工作区文件夹中，因为你可以用`use`指令指定每个模块的相对路径。

3. 在你的工作区目录下运行`go work init [path-to-module-one] [path-to-module-two]`。

   例子。你正在开发`example.com/x/tools/groundhog`，它依赖于`example.com/x/tools`模块中的其他软件包。

   你克隆了软件库，然后在你的工作区文件夹中运行`go work init tools tools/groundhog`。

   你的`go.work`文件的内容类似于以下内容：

   ```
   go 1.18
   
   use (
           ./tools
           ./tools/groundhog
   )
   ```

   在 `tool`模块中做出的任何本地修改都将被你的工作区中的`tool/groundhog`所使用。

### 在依赖性配置之间进行切换

为了用不同的依赖配置测试你的模块，你可以用独立的`go.work`文件创建多个工作区，或者保留一个工作区，在一个`go.work`文件中注释掉你不需要的`use`指令。

要创建多个工作区。

1. 为不同的依赖性需求创建单独的目录。
2. 在每个工作区的目录中运行`go work init`。
3. 通过 "go work use [path-to-dependency]"在每个目录中添加你想要的依赖性。
4. 在每个工作区目录中运行`go run [path-to-your-module]`，以使用其`go.work`文件所指定的依赖项。

要在同一工作区测试不同的依赖关系，请打开`go.work`文件，添加或注释所需的依赖关系。

### 还在使用GOPATH吗？

也许使用工作区会改变你的想法。`GOPATH`用户可以使用位于其`GOPATH`目录底部的`go.work`文件来解决他们的依赖关系。工作区的目的不是要完全重新创建所有的`GOPATH`工作流程，但它们可以创建一个设置，分享`GOPATH`的一些便利，同时仍然提供模块的好处。

要为GOPATH创建一个工作区:

1. 在你的`GOPATH`目录下运行`go work init`。
2. 要在你的工作区中使用一个本地模块或特定版本作为依赖，运行`go work use [path-to-module]`。
3. 要替换你的模块的`go.mod`文件中的现有依赖关系，请使用`go work replace [path-to-module]`。
4. 要添加你的GOPATH或任何目录中的所有模块，运行`go work use -r`来递归地添加有`go.mod`文件的目录到你的工作区。如果一个目录没有`go.mod`文件，或者不再存在，使用`use`指令的目录将会从 `go.work`文件中删除。

> 注意：如果你有没有`go.mod`文件的项目，你想把它添加到工作区，请换到它们的项目目录，运行`go mod init`，然后用`go work use [path-to-module]`把新模块添加到你的工作区。

## 工作区指令

除了`go work init`和`go use`之外，Go 1.18为工作区引入了以下命令：

- `go work sync`：将`go.work`文件中的依赖关系推回到每个工作区模块的`go.mod`文件中。
- `go work edit`：为编辑`go.work`提供一个命令行接口，主要供工具或脚本使用。

模块感知的构建命令和一些 `go mod`子命令会检查 `GOWORK`环境变量，以确定它们是否处于工作区环境中。

如果`GOWORK`变量命名的文件路径以`.work`结尾，则工作区模式被激活。要确定哪个`go.work`文件正在被使用，请运行`go env GOWORK`。如果`go`命令不在工作区模式下，则输出为空。

当工作区模式被启用时，`go.work`文件被解析以确定工作区模式的三个参数：一个Go版本，一个目录列表，以及一个替换列表。

在工作区模式下可以尝试一些命令（前提是你已经知道它们的作用！）：

```
go work init
go work sync
go work use
go list
go build
go test
go run
go vet
```

## 编辑器体验的改进

我们对Go语言服务器[gopls](https://pkg.go.dev/golang.org/x/tools/gopls)和[VSCode Go扩展](https://marketplace.visualstudio.com/items?itemName=golang.go)的升级感到特别兴奋，这使得在兼容LSP的编辑器中处理多个模块的工作变得顺利而有意义。

查找引用、代码补全和转到定义在工作区中跨模块工作。版本[0.8.1](https://github.com/golang/tools/releases/tag/gopls%2Fv0.8.1)的`gopls`引入了诊断、完成、格式化和对`go.work`文件的悬停。你可以用任何[LSP](https://microsoft.github.io/language-server-protocol/)兼容的编辑器来利用这些gopls的功能。

#### 编辑的具体说明

- 最新的[vscode-go版本](https://github.com/golang/vscode-go/releases/tag/v0.32.0)允许通过Go状态栏的快速选择菜单快速访问你的工作区的`go.work`文件。

![Access the go.work file via the Go status bar&rsquo;s Quick Pick menu](https://user-images.githubusercontent.com/4999471/157268414-fba63843-5a14-44ba-be82-d42765568856.gif)

- [GoLand](https://www.jetbrains.com/go/)支持工作区，并计划为`go.work`文件增加语法高亮和代码完成。

关于在不同编辑器中使用`gopls`的更多信息，请看`gopls`[文档](https://pkg.go.dev/golang.org/x/tools/gopls#readme-editors)。

## 接下来是什么？

- 下载并安装[Go 1.18](https://go.dev/dl/)。
- 尝试通过[Go工作区教程](https://go.dev/doc/tutorial/workspaces)来使用[工作区](https://go.dev/ref/mod#workspaces)。
- 如果你在使用工作区时遇到任何问题，或者想提出一些建议，请提交一个[issue](https://github.com/golang/go/issues/new/choose)。
- 阅读[工作区维护文档](https://pkg.go.dev/cmd/go#hdr-Workspace_maintenance)。
- 探索[在单一模块外工作](https://go.dev/ref/mod#commands-outside)的模块命令，包括`go work init`，`go work sync`等等。
