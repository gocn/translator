# Understanding and Crafting HTTP Middlewares in Go

- 原文地址：https://ghostmac.hashnode.dev/understanding-and-crafting-http-middlewares-in-go
- 原文作者：MacBobby Chibuzor
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w07_building_middlewares_with_golang.md
- 译者：[张宇](https://github.com/pseudoyu)
- 校对：

Go 中的错误处理与其他主流编程语言如 Java、JavaScript 或 Python 有些不同。Go 的内置错误不包含堆栈痕迹，也不支持传统的`try/catch`方法来处理它们。相反，Go 中的错误只是由函数返回的值，它们的处理方式与其他数据类型基本相同 - 这带来了令人惊叹的轻量级和简单设计。

在这篇文章中，我将展示 Go 中处理错误的基础知识，以及一些你可以在代码中遵循的简单策略，以确保你的程序健壮且易于调试。

## Introduction

When communication is needed between a client and a server running on different computers, a middleware is implemented. In this article, the reader will be introduced to Middlewares, their use cases, and how they are crafted in the Go Programming Language.

What Are HTTP Middlewares? To better understand what HTTP Middlewares are, some underlying concepts must be explained. Assuming a programmer wants two computers to communicate, where one would provide the other with a resource or service. The programmer would quickly build a client/server system to make this happen. The server waits for the client to request for a resource or service, then forwards the requested resource to the client in response. The requested resource or service may be:

- Authentication—verifying that the client is who it claims to be
- Authorization—determining whether the given client is permitted to access any of the services the server supplies
- Providing services
- Data security—guaranteeing that a client is not able to access data that the client is not permitted to access, preventing data from being stolen

Servers are built to be stateless or stateful. Stateless servers do not concern themselves with the status of client communication, while stateful servers do.

Middleware is a software entity that hooks one software or enterprise application to another, forming a distributed system. An HTTP request is sent to an API server, which returns an HTTP response to the client.

Middlewares have a request receiver function to process requests before they reach the handler function. It then processes the handler function, before processing a response and sending it out to the client.

## Middleware Use Cases

The most common use cases are:

- Loggers for logging each and every request hitting the REST API
- Validation of user session, and keeping the communication alive
- User authentication
- Writing custom logic to scrape request data
- Attach properties to responses while serving the client

## Middleware Handlers

In Go, a middleware handler is an `http.Handler` that wraps another http.Handler to do some pre- and/or post-processing of the request. It's called "middleware" because it sits in the middle between the Go web server and the actual handler.

[Middleware Handlers]: ../static/images/2022/w07_building_middlewares_with_golang/middleware_handlers.png
![Middleware Handlers][Middleware Handlers]
<center style="font-size:14px;color:#C0C0C0;text-decoration">Middlerware Handlers</center> 

A basic middleware handler is written below:

```go
package main 
import (
    "fmt"
    "net/http"
)

func middleware(handler http.Handler) http.Handler {
     return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
         fmt.Println("Executing middleware before request phase!")
         // Pass control back to the handler
         handler.ServeHTTP(w, r)         fmt.Println("Executing middleware after response phase!")
     })
 }
 func mainLogic(w http.ResponseWriter, r *http.Request) {
     // Business logic goes here
     fmt.Println("Executing mainHandler...")
     w.Write([]byte("OK")) } func main() {
     // HandlerFunc returns a HTTP Handler
     mainLogicHandler := http.HandlerFunc(mainLogic)
     http.Handle("/", middleware(mainLogicHandler))
     http.ListenAndServe(":8000", nil)
}
```

Running the code above in the terminal gives the following output:

```bash
go run middleware.go

Executing middleware before request phase!
Executing mainHandler...
Executing middleware after response phase!
```

Logging Middleware Handler To explain how a logging middleware handler works in example use cases, we will build one to execute some functions. This example creates two middleware handlers: `middlewareGreetingsHandler` and `middlewareTimeHandler`. The Gorilla Mux router has a `HandleFunc( )` method for handling the middleware functions.

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

To run this server, set the ADDR environment variable to a free port, and use go run main.go:

```bash
export ADDR=localhost:8080
go run main.go
```

When the server is live, visit localhost:8080/v1/greetings in your browser to see the `middlewareGreetingsHandler` response, and localhost:8080/v1/time to see the `middlewareTimeHandler` response. With this achieved, creating the logging middleware to log all requests made to this server, list the request method, resource path, and how long it took to handle, comes next. To do so, we will initialize a new struct that implements the `ServeHTTP()` method of the `http.Handler` interface. The struct will have a field to track the real `http.Handler` for process calls.

```go
//Create a request logging middleware handler called Logger
type Logger struct {
    handler http.Handler
}

//ServeHTTP handles the request by passing it to the real handler and logging the request details
func (l *Logger) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    start := time.Now()
    l.handler.ServeHTTP(w, r)
    log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
}

//NewLogger constructs a new Logger middleware handler
func NewLogger(handlerToWrap http.Handler) *Logger {
    return &Logger{handlerToWrap}
}
```

`NewLogger()` takes an `http.Handler` to wrap. It then returns a new `Logger` instance wrapped around it. Since an `http.ServeMux` satisfies the `http.Handler` interface, it is possible to wrap an entire mux with the logger middleware. Further, since `Logger` implements the `ServeHTTP()` method, it also satisfies the `http.Handler` interface, so it can be passed to the `http.ListenAndServe()` function instead of the mux wrapped. Finally, change the `main()` function to look like this:

```go
func main() {
    addr := os.Getenv("ADDR")

    mux := http.NewServeMux()
    mux.HandleFunc("/v1/greetings", middlewareGreetingsHandler)
    mux.HandleFunc("/v1/time", middlewareTimeHandler)
    //wrap entire mux with logger middleware
    wrappedMux := NewLogger(mux)

    log.Printf("server is listening at %s", addr)
    //use wrappedMux instead of mux as root handler
    log.Fatal(http.ListenAndServe(addr, wrappedMux))
}
```

After starting the server and requesting for the APIs again, all requests will be logged to the terminal, despite the resource path requested.

## Using Gorilla's `Handlers` middleware for Logging

The Gorilla Mux router has a `Handlers` package that provides various kinds of middleware for common tasks including:

- `LoggingHandler`: For logging in Apache Common Log Format
- `CompressionHandler`: For zipping the responses
- `RecoveryHandler`: For recovering from unexpected panics

Below, we use the `LoggingHandler` to perform API-wide logging. First, install this library using `go get`:

```bash
go get "github.com/gorilla/handlers"
```

Next, import and use it in a go file `loggingMiddleware.go`:

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
     r.HandleFunc("/", mainLogic)     loggedRouter := handlers.LoggingHandler(os.Stdout, r)
     http.ListenAndServe(":8080", loggedRouter)
}
```

Run the server:

```bash
go run loggingMiddleware.go
```

Navigating to localhost:8080 in the browser will show the following output:

```
2022/01/05 10:51:44 Processing request!
2022/01/01 10:51:44 Finished processing request
127.0.0.1 - - [05/January/2022:10:51:44 +0530] "GET / HTTP/1.1" 
200 2 127.0.0.1 - - [05/January/2017:10:51:44 +0530] "GET /favicon.ico HTTP/1.1" 404 19
```

This example introduces the use of Gorilla Mux `Handlers` package and nothing more.

## Conclusion

In this article, the reader is introduced to Middlewares. A logging middleware was built from scratch for easy understanding. Next, a use case was implemented in an API. Afterwards, a simpler solution to crafting Middlewares in Go (i.e. the Gorilla Mux Handlers) was introduced and implemented in an example. In a future article, Crafting RPC Servers and Clients in Go will be explained.

My name is MacBobby Chibuzor and I am a Contract Technical Writer for Wevolver.com, and ReachExt K. K. I have over 7 years experience in writing commercially, with 2 years in Software. I write about Software Development, Security, ML, IoT, and more recently, Blockchain. Leave me a message if you need my services: theghostmac@gmail.com.