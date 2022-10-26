# 如何使用 Docker 创建一个 Go 私有模块

- 原文地址：https://medium.com/the-godev-corner/how-to-create-a-go-private-module-with-docker-b705e4d195c4
- 原文作者：Marvin Collins
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker.md
- 译者：[cvley](https://github.com/cvley)
- 校对：[]()

![](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_1.png)

## 介绍

自从 Go 1.11 引入模块后，Go 应用的依赖管理有了极大地提升。我们可以看到，使用 **GOPROXY** 能非常简单地拉取一个模块，更好地支持请求校验和流水线式的依赖版本等等。

但如果你想要创建自己的模块，要怎么开始开始呢？

好消息是，相对而言，公开的包与私有的相比，并没有太多的难度，反之亦然。但它们有一点 _不同_。

> _👉_ 注意：: 在本文中，Go 包和 Go 模块的含义是相同的。

不过，在私有平台如 bitbucket、Gitlab 或 Github 上发布 Go 模块是一项非常有用的技能，无论是创建一个个人项目，还是想要“在内部”保持私有的逻辑。所以我认为指导少量有这方面需求的人也是值得的。

作为额外的奖励，我也会展示如何使用 Docker 镜像来开发 Go 应用——那么坐好扶稳，我们这就出发。

## 简短的序言

### 到本文的结尾，你将可以：

\[可以按需跳至特定的部分\]

1.  [创建一个 GitHub 私有仓库](#section-1) (用于 Go 私有模块)
2.  [设置和配置](#section-2) Go 私有模块
3.  [在本地使用 Docker ](#section-3)
4.  [设置校验凭证](#section-4)
5.  [建立一个安全的连接](#section-5) (使用 SSH)
6.  [配置 Docker](#section-6) (并安全下载)
7.  以及 [构建应用 Docker 镜像](#section-7)

### 先决条件

- Go 模块知识
  （注意：如果你是 Go 模块新手，我建议你先从[官方文档](https://github.com/golang/go/wiki/Modules#go-111-modules) 开始学习）
- 已安装 Go 1.16+
- 熟悉 Git

## 开始

首先，我们将创建一个 GitHub 私有仓库，用于 Go 私有模块。

> \[为了简单地跟随内容，可以按情况跳到[这部分](#section-2)\]

### 下载示例项目代码

没有必要从零开始写示例 Go 模块。因此，按情况前往下列的 Github 仓库并下载项目的 zip 压缩包；是的，你没看错 —— 无需克隆代码仓库，仅需要下载 zip 压缩包。

[### GitHub - marvinhosea/filter: Article Repo](https://github.com/marvinhosea/filter)

点击仓库页面的代码，可以看到一个下拉菜单，如下所示。直接点击下载 zip 来下载代码。

![Two step visual process to download the required codebase](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_2.png)

在下载完成后，把 zip 文件解压到一个文件夹。在提交代码到一个私有 Github 仓库前，我们需要作出一个修改。使用你习惯的 IDE 打开解压的文件夹，编辑 **go.mod** 文件，把模块名字中的用户名改成你的 Github 用户名，如下所示。

```golang
module github.com/username/go-filter

go 1.19

require golang.org/x/exp v0.0.0-20220722155223-a9213eeb770e // indirect
```

### 创建 Github 私有仓库 <a name="section-1"></a>

我们把私有 Github 仓库看作一个私有的 Go 模块发布。所以打开 Github 并创建一个新的私有仓库，如下所示：

![Visual image of creating a new private repository within GitHub](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_3.png)

接下来，你将要把我们的 Go 模块文件添加到新建的 Github 私有仓库中。

- 在 Go 模块项目的根目录，运行下面的命令来 git 初始化文件夹：

```
git init
```

> _👉_ 在初始化项目后，我们使用 git 添加文件；因为我们已经配置了 git 忽略的配置文件，所以在运行 git add 时无需担心。如下所示：

```
git add --all
```

- 现在，如果你看下代码仓库，会发现我们有一个简单的测试。在我们提交代码前，先运行它来保证一切运行正常：

```
go test -v -cover ./...
```

- 如果成功完成，你将会看到如下所示内容：

![Code showing the initial test being run in your Go private module](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_4.png)

- 既然包的功能正常，让我们添加 git commit 信息：

> _👉_ 按需创建自己的信息

```
git commit -m 'first commit'
```

- 现在我们把远端 origin 添加到项目中：

```
git remote add origin git@github.com:username/private-filter.git
```

- 最后，运行下面的命令把项目推到远端仓库：

```
git push -u origin main
```

如果你刷新 Github 上的项目仓库，将会看到上面的命令成功将本地仓库的代码和文件传到了远端仓库。这就是我们所需要的全部。

## 使用 Go 私有模块

Go 模块允许开发者添加和管理依赖，但私有 Go 模块发布并非开箱即用的；我们需要对 Go 和设置上都做些额外的配置。

在修改后，获取 Go 模块的依赖将和使用 **go get** 命令获取 Go 公开模块相似。这将会从公开发布的镜像 [proxy.golang.org](http://www.proxy.golang.org) 中下载 Go 模块。

### Go 私有环境变量配置 <a name="chapter-2"></a>

因为我们使用 Go 模块，确保开启 **GO11MODULE**；如果没开启，运行下面的命令：

```
export GO111MODULE=on
```

> _👉_ Go 私有模块发布的位置一定要指明，在本例中是私有 Github 仓库。

**GOPRIVATE** 环境变量可以让我们发布 Go 私有模块，我们可以使用下面的命令来设置 **GOPRIVATE** 的值：

```
go env -w GOPRIVATE=github.com/username/*
```

为设置 Go 环境变量，可以使用 **go env -w**。前面的命令通知 Go 模块发布的源码而不是 Go 公开的发布包。**github.com/username/\*** 对应的是你的组织或个人的私有 Go 模块发布，可以是 Gitlab、Bitbucket或其他相似服务。

> 但如果我们有多个私有模块呢？

在这种情况下，我们可以使用逗号来分隔模块的发布源码，如下所示。

```
go env -w GOPRIVATE=github.com/username/*,gitlab.com/username/*
```

> _👉_ 我们使用星号，以允许发布地址中的任意 Go 模块。

我们也可以直接在 bashrc 或 zshrc 文件中添加了 **GOPRIVATE** 环境变量，但我把这个留给你来进一步探索，或者简单运行下面的指令来设置 **GOPRIVATE** 环境变量。

```
export GOPRIVATE=github.com/username/*
```

> 👉 设置 GOPRIVATE 并不妨碍 Go 公开模块的发布。

为了确认 **GOPRIVATE** 环境变量已经设置，运行下面的命令：

```
env | grep GOPRIVATE
```

输出应该与下面的内容类似：

```
GOPRIVATE=github.com/username/*
```

这些就是我们需要在 Go 中使用 Go 私有模块的全部设置内容。让我们来做些必要配置，让 Go 的工具可以从私有发布中下载 Go 私有模块。

### 设置凭证和 Go 私有模块访问权限  <a name="section-3"></a>

在本节中，我们将会看下如何在本地结合 Docker 使用 Go 私有模块。开始前，我们先 go get Go 私有模块：

- 进入你的开发目录，并创建一个简单的 Go 应用。在我的例子中，我叫它 **go-private-example:**

```
mkdir go-private-example && cd go-private-example
```

> _👉_ 上面的命令创建了一个空文件夹，然后进入这个文件夹

- 现在，我们在项目的根目录，把 go 模块添加到这个简单的 Go 应用中：

```
go mod init github.com/username/go-private-example
```

> _👉_ 上面的命令将会生成一个用于追踪依赖的 **go.mod** 文件。

- 接下来，在根目录下，创建一个 **main.go** 文件并把下面的内容贴进去：

```golang

package main

import "fmt"

func main(){
	fmt.Println("Go private module Example")
}
```

- 既然我们有了 main 包和 main 函数，它们都是作为我们样例程序的入口，让我们打开终端使用 **go get** 下载私有 Go 模块：

```
go get github.com/username/go-filter
```

如果你在终端中运行这个指令，在 \[Go 1.19\] 下会得到如下的输出：

![Visual code depicting how to download the go private module using go get](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_5.png)

> _👉_ 错误表示 Go 工具尝试访问 Go 私有模块，但因为拒绝访问而无法下载，因为我们还没有设置校验凭证。

接下来看我们如何解决这个问题：

## 提供凭证 <a name="section-4"></a>

此时，前路有分叉，你可以任选一条路：使用 ssh 的方法（更简单且推荐）或者使用 .netrc 方法。

我们将会详解两种方法，万一你都感兴趣，但我们以使用 ssh 开始。

> _💡_ 即使你设置了两种选项（即，ssh 和 .netrc），你将毫无疑问可以下载私有 Go 模块。

### 使用 ssh <a name="section-5"></a>

Git 在全局配置文件中提供了一个叫做 **insteadOf** 的选项，它告诉 git 应该使用哪个 URL 来替换默认的 HTTPS URL。比如，对于 “[https://github.com/](https://github.com/)”，使用 “ssh://[git@github.com](mailto:git@github.com)/”。

> _💡_ 当你配置好 ssh 并链接到你的私有 Go 模块发布时，你将拥有一个更加安全的链接。

让我们配置系统，以使用 ssh 而不是 HTTPS：

-  进入用户 home 目录 （**$HOME**），打开 **.gitconfig** 文件，在文件末尾添加这行内容：

```
...[url "ssh://git@github.com/"]   insteadOf = https://github.com/
```

这会指导 git 使用 ssh URL 而不是 HTTPS URL。

> _👉_ 这对于 Gitlab、Bitbucket 等也有效。

### 使用 .netrc 文件

> _💡_ **.netrc** 文件位于用户 home 文件夹下，用于保存无需手动输入的用于登录的凭证。更多信息可以参阅[这里](https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)。
>
> 同时，这个方法包含了潜在将未加密的凭证保存在磁盘上的操作，因此请谨慎操作。

开始前，我们先进入 home 目录（**$HOME**）并检查 **.netrc** 文件是否在目录中：

```
ls .netrc
```

- 如果文件不存在你会得到下面的错误。否则请跳过这部分并从我们添加文件内容的部分继续。

```
No such file or directory
```

- 如果不存在，通过运行下面命令来创建文件：

```
touch .netrc
```

- 如下所示，给它授权 600：

```
sudo chmod 600 .netrc
```

- 现在打开文件，在结尾添加下面的内容，并关闭它：

```
machine github.com login username password accesstoken
```

将上面一行中的 **username** 替换成你的 Github 用户名，然后生成你的个人访问令牌并在上一行中替换 **accesstoken** 。你可以在[这里](https://github.com/settings/tokens)生成一个新的访问令牌，对它仅分配相关的范围，然后复制它。

> _💡_ 当创建令牌时，确保检查相关的授权范围。心中牢记安全，以防令牌被盗用。不要使用你的账户密码。

> Gitlab 如何设置？

仅需要把 github.com URL 替换成 gitlab.com 或 bitbucket.com URL 亦或其他仓库服务地址。

现在，让我们重复下面的命令再次尝试获取 Go 私有模块：

```
go get github.com/username/go-filter
```

输出将和这个类似：

![Visual code explaining how to get the Go private module](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_6.png)

如你所见，我们的包已经下载并且添加到项目中。为了确认，使用你习惯的 IDE 打开项目并打开 **go.mod** 文件。里面的内容应该如下所示：

```golang
module github.com/username/go-private-example

go 1.19

require (
	github.com/username/go-filter v0.0.0-20220920084832-2774b2100989 // indirect
	golang.org/x/exp v0.0.0-20220916125017-b168a2c6b86b // indirect
)
```

这表明我们的 Go 私有模块已经被添加成为一个依赖项，我们可以轻松地在样例程序中使用它。通过拷贝下面的内容并替换到前面添加的内容，我们更新程序 **main.go** 文件：

```golang
package main

import (
	"fmt"
	"github.com/username/go-filter"
)

func main() {
	fmt.Println("Go private module Example")

	intArray1 := []int{1, 2, 3, 4, 5, 5}
	intArray2 := []int{0, 9, 45, 5}
	result := filter.Filter(intArray1, intArray2)
	fmt.Println(result)
}
```

本质上说，在上面的程序中，我们传入两个整数数组到我们的私有 Go 模块的过滤函数，它将会合并两个数组并过滤掉重复的值。如果我们现在运行程序，将得到下面的结果：

```
Go private module Example
[1 2 3 4 5 0 9 45]marvinhosea8
```

> _👉_ 这证明整体如预期运行。

## Docker 如何使用？<a name="section-6"></a>

最终，你将会在某个时刻需要创建一个 Docker 镜像。为此，我们将看下如何配置 Docker 和 Docker-compose 文件，以安全下载私有 Go 模块。

- 在我们的示例项目中，通过运行下面的命令创建一个 Docker 文件：

```
touch Dockerfile
```

- 在你创建 Dockerfile 后，在其中添加下面的内容：

```
## Build
FROM golang:1.19-alpine AS build

LABEL maintainer="Marvin Hosea"

RUN apk add --no-cache git ca-certificates

ARG GITHUB_TOKEN
ENV CGO_ENABLED=0 GO111MODULE=on GOOS=linux TOKEN=$GITHUB_TOKEN

RUN go env -w GOPRIVATE=github.com/marvinhosea/*
## Or you could use ENV GOPRIVATE=github.com/username

RUN git config --global url."https://${TOKEN}:x-oauth-basic@github.com/".insteadOf "https://github.com/"
# Gitlab
# RUN git config  --global url."https://oauth2:${TOKEN}@gitlab.com".insteadOf "https://gitlab.com"


WORKDIR /app

COPY go.mod ./
COPY go.sum ./
RUN go mod download

COPY . .

RUN go build -installsuffix cgo -ldflags '-s -w' -o main ./...

## Deploy
FROM scratch as final

COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=build /app .

ENTRYPOINT ["./main"]
```

> _☝️_因为 Docker 在本文范围之外，我将仅解释 Dockerfile 的特定部分。第 8 和 9 行如下所示：

```
ARG GITHUB_TOKENENV CGO_ENABLED=0 GO111MODULE=on GOOS=linux TOKEN=$GITHUB_TOKEN
```

我们定义了一个参数，将在 Docker 镜像构建时接收一个值。

> _💡_基于安全考虑，这个参数可以动态设置。我再怎么强调都不为过，你的密码和令牌**一定不要**硬编码在 Dockerfile 中。

接下来，当我们接收到 **GITHUB\_TOKEN** 这一表示私有访问令牌时，我们传入 **GITHUB\_TOKEN** 这个 docker 参数：

```
RUN go env -w GOPRIVATE=github.com/username/*
```

正如前面所说，第 11 行的命令将会设置 Go **GOPRIVATE** 环境变量：

```
RUN git config --global url."https://${TOKEN}:x-oauth-basic@github.com/".insteadOf "https://github.com/"
```

第 14 行表示我们将下载私有 Go 模块并使用以 **TOKEN** 传入的私有访问令牌来获取环境变量：

在开始之前，我们为项目创建 **.env** 文件。

- 在项目根目录，创建 **.env** 文件并添加下列内容：

```
GITHUB_USERNAME=username
GITHUB_TOKEN=PersonalAccessToken
```

我们完成 **.env** 之后，通过使用下面的命令构建我们的应用 Docker 镜像：

```
export $(egrep -v ‘^#’ .env | xargs) && docker build --build-arg GITHUB_TOKEN=${GITHUB_TOKEN} -t go-private-example .
```

在上面的命令中，我们从 **.env** 文件中获取值并输出为环境变量。然后我们运行 Docker 构建命令，使用从 **.env** 传入的环境变量参数构建 Docker 镜像。

在构建镜像之后，我们可以使用这个命令运行 Docker 镜像：

```
docker run go-private-example
```

输出应该如下所示：

```
Go private module Example [1 2 3 4 5 0 9 45]
```

### 使用 docker-compose <a name="section-7"></a>

在项目的根目录创建一个 **docker-compose.yml** 文件，其中的内容如下所示：

```
services:
  app:
    container_name: go-private-example
    env_file:
      - .env
    build:
      dockerfile: Dockerfile
      args:
        - GITHUB_TOKEN=GITHUB_TOKEN
    image: go-private-example

    # other configuration
```

docker-compose 文件与 Docker 运行的命令类似。使用 **env\_file** 标签来传递环境变量文件，执行 docker-compose 的命令如下所示：

```
docker compose up
```

输出应该与下面类似：

```
[+] Running 1/0
 ⠿ go-private-example  Warning: No resource found to remove
0.0s
[+] Running 2/2
 ⠿ Network go-private-example_default  Created
0.1s
 ⠿ Container go-private-example        Created
0.1s
Attaching to go-private-example
go-private-example  | Go private module Example
go-private-example  | [1 2 3 4 5 0 9 45]
go-private-example exited with code 0
```

现在你就得到了你自己的可用的 Go 私有模块了！

## 结论

在本文中，我们了解了处理和发布 Go 私有模块的方法。我们也讨论了如何配置证书来下载 Go 私有模块，以及在构建 Docker 应用镜像时如何使用 Go 私有模块。

> _💡_ 我仅仅想重新迭代 — 你应该注意配置和使用 Go 私有模块的发布证书，避免暴露它们，这也是它们标记为私有的原因。

在接下来的另一篇文章中，我将会讨论如何开始 Go 模块的开发。如果你还不熟悉 Go 模块的开发或想要快速有趣的阅读，可以在有时间时再重头读起。

我希望你会享受这篇简短的教程。如果你想阅读更多类似的文章，可以点击下面的 👏 图标，或者在评论中告诉我未来提升类似文章的方法。

## 参考资料

本文的代码仓库如下所示：

[### GitHub — marvinhosea/go-private-example](https://github.com/marvinhosea/go-private-example)

[### GitHub — marvinhosea/filter: Article Repo](https://github.com/marvinhosea/filter)

_声明：根据 Medium.com 的规则和指导方针，我公开承认_ [_UniDoc_](http://www.unidoc.io) _对本文的经济补偿。所有的想法、意见、代码、图片、文字等都归我所有。_
