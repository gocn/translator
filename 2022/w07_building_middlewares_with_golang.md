# 从零到一实现一个 Go 语言 HTTP 中间件

- 原文地址：https://ghostmac.hashnode.dev/understanding-and-crafting-http-middlewares-in-go
- 原文作者：MacBobby Chibuzor
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w07_building_middlewares_with_golang.md
- 译者：[张宇](https://github.com/pseudoyu)
- 校对：

## 简介

当运行在不同计算机上的客户端与服务器进行通信时，就需要使用中间件。通过本文，读者将会了解什么是中间件、中间件用例以及它们是如何在 Go 语言中构建的。

### 什么是 HTTP 中间件

为了更好理解 HTTP 中间件是什么，先要解释一些基本概念。假如一个开发者想要建立两台计算机之间的通信（其中一台计算机为另一台提供资源或服务），他将会构建一个 client/server 系统来实现。服务器等待客户端请求资源或服务，并将请求的资源转发给客户端作为响应。请求的资源或服务可能为：

- 客户端身份校验
- 确认客户端对服务器提供的特定服务是否有访问权限
- 提供服务
- 保障数据安全，确保客户端无法访问未授权数据，防止数据被窃取

服务器分为无状态和有状态两类，无状态服务器不关心客户机通信状态，而有状态服务器则关心。

中间件是一种将软件或企业应用连接到另一个软件应用，并构成分布式系统的软件实体。HTTP 请求被发送到 API 服务器，而服务器向客户端返回 HTTP 响应。

中间件具备接收请求功能，可以在请求到达处理方法之前对其进行预处理。然后，它将处理具体方法，并将其响应结果发送给客户端。

## 中间件用例

最常见的用例为：

- 日志记录器，用于记录每个 REST API 访问请求
- 验证用户 session，并保持通信存活 
- 用户鉴权
- 编写自定义逻辑以抽取请求数据
- 为客户端提供服务时将属性附在响应信息

## 中间件 Handlers

在 Go 语言中，中间件 Handler 是封装另一个 `http.Handler` 以对请求进行预处理或后续处理的 `http.Handler`。它介于 Go Web 服务器与实际的处理程序之间，因此被称为“中间件”。

[Middleware Handlers]: ../static/images/2022/w07_building_middlewares_with_golang/middleware_handlers.png
![Middleware Handlers][Middleware Handlers]
<center style="font-size:14px;color:#C0C0C0;text-decoration">中间件 Handler</center> 

下面是一个基本的中间件 Handler：

```go
package main 
import (
    "fmt"
    "net/http"
)

func middleware(handler http.Handler) http.Handler {
     return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
         fmt.Println("Executing middleware before request phase!")
         // 将控制权交回 Handler
         handler.ServeHTTP(w, r)         
         fmt.Println("Executing middleware after response phase!")
     })
 }
 func mainLogic(w http.ResponseWriter, r *http.Request) {
     // 业务逻辑
     fmt.Println("Executing mainHandler...")
     w.Write([]byte("OK")) } func main() {
     // HandlerFunc 返回 HTTP Handler 
     mainLogicHandler := http.HandlerFunc(mainLogic)
     http.Handle("/", middleware(mainLogicHandler))
     http.ListenAndServe(":8000", nil)
}
```

在终端运行代码，得到以下输出结果：

```bash
go run middleware.go

Executing middleware before request phase!
Executing mainHandler...
Executing middleware after response phase!
```

### 日志中间件 Handler

为了更好讲解日志中间件 Handler 是如何工作的，我们将实际构建一个并执行一些方法。以下示例创建了两个中间件 Handler：`middlewareGreetingsHandler` 和 `middlewareTimeHandler`。Gorilla Mux 路由的 `HandleFunc()` 方法用于处理中间件方法。

```go
package main

import (
    "fmt"
    "log"
    "net/http"
    "os"
    "time"
)

func middlewareGreetingsHandler(w http.ResponseWriter, r *http.Request) {
    w.Write([]byte("Happy New Year, 2022!"))
}

func middlewareTimeHandler(w http.ResponseWriter, r *http.Request) {
    curTime := time.Now().Format(time.Kitchen)
    w.Write([]byte(fmt.Sprintf("the current time is %v", curTime)))
}

func main() {
    addr := os.Getenv("ADDR")

    mux := http.NewServeMux()
    mux.HandleFunc("/v1/greetings", middlewareHelloHandler)
    mux.HandleFunc("/v1/time", middlewareTimeHandler)

    log.Printf("server is listening at %s", addr)
    log.Fatal(http.ListenAndServe(addr, mux))
}
```

先设置 ADDR 环境变量为空闲端口，并执行 `go run main.go` 命令来运行服务：

```bash
export ADDR=localhost:8080
go run main.go
```

服务运行成功后，在浏览器中访问 `localhost:8080/v1/greetings` 查看 `middlewareGreetingsHandler` 的响应信息，访问 `localhost:8080/v1/time` 查看 `middlewareTimeHandler` 的响应信息。完成后，我们需要创建日志中间件来记录所有服务访问请求信息，列举请求方法、资源路径以及处理时间。首先我们要初始化一个新的结构体来实现 `http.Handler` 接口的 `ServeHTTP()` 方法。这个结构体将会有一个字段来追溯进程调用中的 `http.Handler`。

```go
// 创建一个名为 Logger 的请求日志中间件 Handler 结构体 
type Logger struct {
    handler http.Handler
}

// ServeHTTP 将请求传递给真正的 Handler 并记录请求细节
func (l *Logger) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    start := time.Now()
    l.handler.ServeHTTP(w, r)
    log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
}

// NewLogger 构造了一个新的日志中间件 Handler
func NewLogger(handlerToWrap http.Handler) *Logger {
    return &Logger{handlerToWrap}
}
```

`NewLogger()` 接收 `http.Handler`，并返回一个新的封装后的 `Logger` 实例。由于 `http.ServeMux` 满足 `http.Handler` 接口，可以使用日志中间件封装整个 mux。除此之外，由于 `Logger` 实现了 `ServeHTTP()` 方法并满足 `http.Handler` 接口，它也可以被传递至 `http.ListenAndServe()` 方法而非封装 mux。最后，修改 `main()` 方法：


```go
func main() {
    addr := os.Getenv("ADDR")

    mux := http.NewServeMux()
    mux.HandleFunc("/v1/greetings", middlewareGreetingsHandler)
    mux.HandleFunc("/v1/time", middlewareTimeHandler)
    // 使用日志中间件封装 mux
    wrappedMux := NewLogger(mux)

    log.Printf("server is listening at %s", addr)
    // 使用 wrappedMux 而不是 mux 作为根 handler
    log.Fatal(http.ListenAndServe(addr, wrappedMux))
}
```

重新启动服务并请求 API，不论请求路径是什么，所有的请求日志都会展示在终端。

## 使用 Gorilla's `Handlers` 中间件进行日志记录

Gorilla Mux 路由有一个 `Handlers` 包，为常见任务提供各种中间件，包括：

- `LoggingHandler`：以 Apache 通用日志格式进行记录
- `CompressionHandler`：压缩响应信息
- `RecoveryHandler`: 从 panic 错误中恢复

在以下示例中，我们使用 `LoggingHandler` 来实现 API 日志记录。首先，使用 `go get` 命令安装包：

```bash
go get "github.com/gorilla/handlers"
```

导入包，并在 `loggingMiddleware.go` 程序中使用：

```go
package main 
import (
    "github.com/gorilla/handlers"
    "github.com/gorilla/mux"


    "log"
    "os"
    "net/http"
)

func mainLogic(w http.ResponseWriter, r *http.Request) {
     log.Println("Processing request!")
     w.Write([]byte("OK"))
     log.Println("Finished processing request")
 } 

func main() {
     r := mux.NewRouter()
     r.HandleFunc("/", mainLogic)     
     loggedRouter := handlers.LoggingHandler(os.Stdout, r)
     http.ListenAndServe(":8080", loggedRouter)
}
```

运行服务：

```bash
go run loggingMiddleware.go
```

在浏览器中访问 `localhost:8080`，会显示以下输出结果：

```bash
2022/01/05 10:51:44 Processing request!
2022/01/01 10:51:44 Finished processing request
127.0.0.1 - - [05/January/2022:10:51:44 +0530] "GET / HTTP/1.1" 
200 2 127.0.0.1 - - [05/January/2017:10:51:44 +0530] "GET /favicon.ico HTTP/1.1" 404 19
```

本示例仅介绍了 Gorilla Mux `Handlers` 包的用法。

## 总结

本文向读者介绍了什么是中间件。为了便于理解，从零开始构建了一个日志中间件程序，并通过 API 实现了一个用例。此外，还介绍并实践了一种在 Go 程序中构造中间件更简单的解决方案（即使用 Gorilla Mux Handler）。在未来的文章中，我将讲解如何在 Go 中构建 RPC 服务与客户端。