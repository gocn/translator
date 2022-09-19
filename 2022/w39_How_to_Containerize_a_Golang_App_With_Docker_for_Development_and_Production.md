- 原文地址：https://bartlomiejmika.com/posts/2022/how-to-containerize-a-golang-app-with-docker-for-development-and-production/
- 原文作者：**Bartlomiej Mika**
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w39_How_to_Containerize_a_Golang_App_With_Docker_for_Development_and_Production.md
- 译者：[朱亚光](https://github.com/zhuyaguang)
- 校对：

# 如何在开发和生产环境中使用 Docker 容器化 Golang 应用

如何在开发和生产环境中使用 Docker 容器化 Golang 应用

![Docker](https://bartlomiejmika.com/img/2022/07/ian-taylor-jOqJbvo1P9g-unsplash.jpg) Photo by [Ian Taylor](https://unsplash.com/@carrier_lost) on [Unsplash](https://unsplash.com/photos/jOqJbvo1P9g).

你是否想写一个使用 Docker 容器化的 Golang 应用程序？本文的目的就是帮助你快速将你的 Golang 应用程序容器化，以用于**开发**（带热加载）和**生产**目的。

## 开始之前

请先安装 [Docker Desktop](https://www.docker.com/get-started/) ，然后再继续。 安装后，启动桌面应用程序，如果它运行成功，你就可以开始了。

此外，我假设你有一个 `$GOPATH` 目录，你可以在里面放置你正在处理的 Golang 源代码。 比如我的是：`~/go/src/github.com/bartmika`。

## … 但我不熟悉 Docker 怎么办？

别担心！ Docker 是一个成熟的工具集，它已经存在了足够长的时间，可以提供大量优秀的教育资源来帮助你学习。 我推荐以下内容，因为它对我帮助很大：

查看我写的另外一篇文章，可以帮助你学习基础知识

-   [绝对是面向 Golang 编程初学者的 Docker 学习资源](https://bartlomiejmika.com/post/2021/docker-learning-resources-for-absolute-beginners-programming-with-golang/)

## 将Golang 和 Docker 用于热加载的开发环境

将Golang 和 Docker 用于热加载的开发环境

在本节中，你将学习如何在你的机器上设置你的 Golang 应用程序进行本地开发。 开发容器的目的是保存所有依赖项（例如：第三方包，如 [GORM](https://gorm.io/index.html)）、基础设施（例如：数据库、内存缓存等）和你的代码方式，以帮助和改进你开发的方式。

1. 创建我们应用程序的仓库

   ```shell
   mkdir mullberry-backend
   cd mullberry-backend
   go mod init github.com/bartmika/mullberry-backend
   ```

2. 每次你想要增加依赖，你都会关闭当前运行的容器并安装依赖项。按照如下方式安装我们的依赖项：

   ```shell
   go get github.com/labstack/echo/v4
   go get github.com/labstack/echo/v4/middleware@v4.7.2
   ```
   
3. 等等，你需要在本地安装 Golang 吗？那么容器的意义何在？[这个 Stackoverflow](https://stackoverflow.com/a/71297861) 用户在讨论为开发目的设置 `Dockerfile` 时解释得最好：

   > 当你想要把应用打包到容器中以准备部署时，`Dockerfile`是非常棒的。对于希望将源代码放在容器外部的开发和希望正在运行的容器对源代码的改变作出反应的开发来说，就不是很合适了。

   所以从本质上讲，如果你对这个限制没意见，那就继续吧！
   
4. 在你的项目的根目录创建  `main.go` 文件，并复制粘贴下面代码：

   ```go
package main
   
   import (
   "net/http"
   "os"
   
   "github.com/labstack/echo/v4"
   "github.com/labstack/echo/v4/middleware"
   )
   
   func main() {
   
   e := echo.New()
   
   e.Use(middleware.Logger())
   e.Use(middleware.Recover())
   
   e.GET("/", func(c echo.Context) error {
   return c.HTML(http.StatusOK, "Hello, Docker! <3")
   })
   
   e.GET("/ping", func(c echo.Context) error {
   return c.JSON(http.StatusOK, struct{ Status string }{Status: "OK"})
   })
   
   httpPort := os.Getenv("HTTP_PORT")
   if httpPort == "" {
   httpPort = "8080"
   }
   
   e.Logger.Fatal(e.Start(":" + httpPort))
   }
   ```
   
   注意，上面的代码是从 Docker 文档[构建你的 Go 镜像](https://docs.docker.com/language/golang/build-images/) 复制而来。

5. 在创建任何与 docker 相关的内容之前，请创建一个 `.dockerignore` 文件并复制并粘贴以下内容：

   ```shell
bin
   .dockerignore
   Dockerfile
   docker-compose.yml
   dev.Dockerfile
   dev.docker-compose.yml
   .env
   ```
   
   什么是 `.dockerignore` 文件？ 本质上，它类似于 `.gitignore` 其中某些文件/文件夹不会保存到 docker 容器和镜像中。

6. 创建 `dev.Dockerfile` 文件并将以下内容复制并粘贴到其中。

   ```dockerfile
FROM golang:1.18
   
   # Copy application data into image
   COPY . /go/src/bartmika/mullberry-backend
   WORKDIR /go/src/bartmika/mullberry-backend
   
   COPY go.mod ./
   COPY go.sum ./
   RUN go mod download
   
   # Copy only `.go` files, if you want all files to be copied then replace `with `COPY . .` for the code below.
   COPY *.go .
   
   # Install our third-party application for hot-reloading capability.
   RUN ["go", "get", "github.com/githubnemo/CompileDaemon"]
   RUN ["go", "install", "github.com/githubnemo/CompileDaemon"]
   
   ENTRYPOINT CompileDaemon -polling -log-prefix=false -build="go build ." -command="./mullberry-backend" -directory="./"
   ```
   
    如果你阅读上面的注释，你会注意到 `CompileDaemon` (https://github.com/githubnemo/CompileDaemon) 的用法。那是什么？本质上它是你的热加载器！它在一个目录中监视你的 .go 文件，如果文件发生变化，它会调用 `go build`。 例如，你在 `Atom` IDE 中打开这个项目，修改 `main.go` 文件并点击 _Save_，然后 [`CompileDaemon`](https://github.com/githubnemo/CompileDaemon) 将重建你容器中的 Go 应用程序，所以你可以看到最新的构建！

7. 创建我们的 `dev.docker-compose.yml` 文件：

   ```yaml
version: '3.6'
   
   services:
       api:
           container_name: mullberry-backend
           image: mullberry-backend
           ports:
               - 8000:8080
           volumes:
               - ./:/go/src/bartmika/mullberry-backend
   build:
           dockerfile: dev.Dockerfile
   ```
   
   等等，为什么我对这些 Docker 文件名使用 `dev.` 前缀？ 原因是因为我想区分用于**生产**和**开发**目的的 Docker 文件。

8. 在你的终端中，使用以下命令启动开发环境：

   ```shell
   $ docker-compose -f dev.docker-compose.yml up
   ```
   
9. 确认我们可以访问它。

   ```shell
   $ curl localhost:8000/
   ```
   
10. 你将在你的终端中看到以下输出：

    ```sh
    Hello, Docker! <3   
    ```
    
    如果你看到这个，恭喜你已经准备好开始开发了！ 如果你想了解更多信息，请随时通过他们的 Docker 文档查看[构建你的 Go 映像](https://docs.docker.com/language/golang/build-images/)一文。

## 将 Golang 和 Docker 用于生产环境

本节的目的是让你的 Golang 应用程序容器化并准备好在生产环境中运行。

### 选项 1：单阶段

最简单的设置就是单阶段构建。这样构建的问题就是你的 Docker 镜像将非常大。

首先，在你的项目根文件夹中创建一个 `Dockerfile` 并将以下内容复制并粘贴到其中：

```dockerfile
FROM golang:1.18

# Copy application data into image
COPY . /go/src/bartmika/mullberry-backend
WORKDIR /go/src/bartmika/mullberry-backend

COPY go.mod ./
COPY go.sum ./
RUN go mod download

# Copy only `.go` files, if you want all files to be copied then replace `with `COPY . .` for the code below.
COPY *.go .

# Build our application.
RUN go build -o ./bin/mullberry-backend


EXPOSE 8080

# Run the application.
CMD ["./bin/mullberry-backend"]
```

 然后运行 `up` 命令，你将会看到它工作：

```shell
$ docker-compose up
```

### 选项 2：多阶段

 一个更复杂的设置被称为_多阶段构建_可以节省磁盘空间。主要思路是你在一个容器中构建你的 Golang 应用程序，然后将它移动到另一个更小的容器中，从而丢弃了磁盘空间沉重的容器。

如果你想尝试一下，请在项目根文件夹中创建一个 `Dockerfile`，然后将以下内容复制并粘贴到其中：

```dockerfile
##
## Build
##
FROM golang:1.18-alpine as dev-env

# Copy application data into image
COPY . /go/src/bartmika/mullberry-backend
WORKDIR /go/src/bartmika/mullberry-backend

COPY go.mod ./
COPY go.sum ./
RUN go mod download

# Copy only `.go` files, if you want all files to be copied then replace `with `COPY . .` for the code below.
COPY *.go .

# Build our application.
# RUN go build -o /go/src/bartmika/mullberry-backend/bin/mullberry-backend
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -gcflags "all=-N -l" -o /server

##
## Deploy
##
FROM alpine:latest
RUN mkdir /data

COPY --from=dev-env /server ./
CMD ["./server"]
```

 然后运行 `up` 命令，你将会看到它工作：

```shell
$ docker-compose up
```

