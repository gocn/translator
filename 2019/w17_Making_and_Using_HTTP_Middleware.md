# Making and Using HTTP Middleware

- 原文地址：[Making and Using HTTP Middleware](https://www.alexedwards.net/blog/making-and-using-middleware)
- 原文作者：Alex Edwards
- 译文出处: https://www.alexedwards.net/
- 本文永久链接：https://github.com/gocn/translator/blob/master/2019/w17_Making_and_Using_HTTP_Middleware.md
- 译者：[咔叽咔叽](https://github.com/watermelo)
- 校对：[fivezh](https://github.com/fivezh)

在构建 Web 应用程序时，可能需要为很多（甚至所有）的 HTTP 请求运行一些共有的函数。在执行一些繁重的处理之前，你可能想给每个请求记录日志，用 gzip 压缩每个返回数据或者检查缓存。

实现这种共有函数的一种方法是将其设置为中间件，它在正常的应用处理程序之前或之后用自包含代码的方式独立地处理请求。在 Go 中，使用中间件的常见位置是 ServeMux 和应用处理程序之间，因此 HTTP 请求的控制流程如下所示：

```sh
ServeMux => Middleware Handler => Application Handler
```

在这篇文章中，我将解释如何实现这种模式下的自定义中间件，并运行一些使用第三方中间件的具体示例。

## 基本原则

在 Go 中实现和使用中间件基本上是比较简单的。我们需要以下几点：

- 实现我们的中间件，使它满足[http.Handler](https://golang.org/pkg/net/http/#Handler)接口。
- 构建链式的处理程序，包含我们的中间件处理程序和我们的普通应用处理程序，我们可以使用[http.ServeMux](https://golang.org/pkg/net/http/#ServeMux)进行注册。

我来解释一下怎么回事儿。

希望你已经熟悉了下面构造处理程序的方法（如果没有，最好在继续之前先阅读[入门手册](https://www.alexedwards.net/blog/a-recap-of-request-handling)）。

```golang
func messageHandler(message string) http.Handler {
  return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    w.Write([]byte(message)
  })
}
```

在这个处理程序中，我们将逻辑（一个简单的`w.Write`）放在一个匿名函数中，然后引用函数体外的`message`变量以形成一个闭包。我们通过使用[http.HandlerFunc](https://golang.org/pkg/net/http/#HandlerFunc)适配器来将此闭包转换为处理程序，然后返回它。

我们可以使用相同的方法来实现链式的处理程序，即使用调用链中的下一个处理程序取代字符串作为变量传递给闭包（如上所述），然后通过调用它的`ServeHTTP()`方法将控制转移到下一个处理程序。

下面提供了一个构建中间件的完整模式：

```golang
func exampleMiddleware(next http.Handler) http.Handler {
  return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    // Our middleware logic goes here...
    next.ServeHTTP(w, r)
  })
}
```

你将注意到此中间件函数有一个`func(http.Handler) http.Handler`的函数签名。它接收一个处理程序作为参数并返回另一个处理程序。这有两个原因：

- 因为它返回一个处理程序，我们可以直接使用标准库  net/http 包提供的 ServeMux 来注册中间件函数。
- 我们可以通过将中间件函数嵌套在彼此内部来实现任意长的链式处理程序。例如：

```golang
http.Handle("/", middlewareOne(middlewareTwo(finalHandler)))
```

## 控制流程的说明

让我们看一个简化的示例，其中包含一些只是将日志消息写入 stdout 的中间件：

> File: main.go

```golang
package main

import (
  "log"
  "net/http"
)

func middlewareOne(next http.Handler) http.Handler {
  return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    log.Println("Executing middlewareOne")
    next.ServeHTTP(w, r)
    log.Println("Executing middlewareOne again")
  })
}

func middlewareTwo(next http.Handler) http.Handler {
  return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    log.Println("Executing middlewareTwo")
    if r.URL.Path != "/" {
      return
    }
    next.ServeHTTP(w, r)
    log.Println("Executing middlewareTwo again")
  })
}

func final(w http.ResponseWriter, r *http.Request) {
  log.Println("Executing finalHandler")
  w.Write([]byte("OK"))
}

func main() {
  finalHandler := http.HandlerFunc(final)

  http.Handle("/", middlewareOne(middlewareTwo(finalHandler)))
  http.ListenAndServe(":3000", nil)
}
```

运行此应用程序并请求[http://localhost:3000](http://localhost:3000/)。你应该能看到类似的日志输出：

```sh
$ go run main.go
2014/10/13 20:27:36 Executing middlewareOne
2014/10/13 20:27:36 Executing middlewareTwo
2014/10/13 20:27:36 Executing finalHandler
2014/10/13 20:27:36 Executing middlewareTwo again
2014/10/13 20:27:36 Executing middlewareOne again
```

很显然可以看到程序依据处理链嵌套的顺序来传递控制，然后再以*相反的方向*返回。

我们随时可以通过让中间件处理程序使用`return`来停止控制在链中的传播。

在上面的例子中，我在`middlewareTwo`函数中包含了一个满足条件的返回。尝试访问[http://localhost:3000/foo](http://localhost:3000/foo)并再次检查日志 - 你会看到，这次请求在通过中间件调用链的时候不会超过`middlewareTwo`。

## 理解了吗，再来一个恰当的例子如何

好吧，假设我们正在构建一个处理 XML 格式请求的服务。我们想创建一些中间件，a）检查请求体的存在，b）确保请求体是 XML 格式。如果其中任何一项检查失败，我们希望中间件写入错误消息并阻止请求到达我们的应用处理程序。

> File: main.go

```golang
package main

import (
  "bytes"
  "net/http"
)

func enforceXMLHandler(next http.Handler) http.Handler {
  return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    // Check for a request body
    if r.ContentLength == 0 {
      http.Error(w, http.StatusText(400), 400)
      return
    }
    // Check its MIME type
    buf := new(bytes.Buffer)
    buf.ReadFrom(r.Body)
    if http.DetectContentType(buf.Bytes()) != "text/xml; charset=utf-8" {
      http.Error(w, http.StatusText(415), 415)
      return
    }
    next.ServeHTTP(w, r)
  })
}

func main() {
  finalHandler := http.HandlerFunc(final)

  http.Handle("/", enforceXMLHandler(finalHandler))
  http.ListenAndServe(":3000", nil)
}

func final(w http.ResponseWriter, r *http.Request) {
  w.Write([]byte("OK"))
}
```

看起来好像没毛病。让我们创建一个简单的 XML 文件来测试它：

```sh
$ cat > books.xml
<?xml version="1.0"?>
<books>
  <book>
    <author>H. G. Wells</author>
    <title>The Time Machine</title>
    <price>8.50</price>
  </book>
</books>
```

使用 cURL 来发送一些请求：

```sh
$ curl -i localhost:3000
HTTP/1.1 400 Bad Request
Content-Type: text/plain; charset=utf-8
Content-Length: 12

Bad Request
$ curl -i -d "This is not XML" localhost:3000
HTTP/1.1 415 Unsupported Media Type
Content-Type: text/plain; charset=utf-8
Content-Length: 23

Unsupported Media Type
$ curl -i -d @books.xml localhost:3000
HTTP/1.1 200 OK
Date: Fri, 17 Oct 2014 13:42:10 GMT
Content-Length: 2
Content-Type: text/plain; charset=utf-8

OK
```

## 使用第三方中间件

有时你可能想用第三方的包，而不是一直使用自己写的中间件。我们来看看两个例子：[goji/httpauth](http://elithrar.github.io/article/httpauth-basic-auth-for-go/) 和 [LoggingHandler](http://www.gorillatoolkit.org/pkg/handlers#LoggingHandler)。

goji/httpauth 包提供 HTTP 基本身份验证功能。它有一个叫[SimpleBasicAuth](https://godoc.org/github.com/goji/httpauth#SimpleBasicAuth)
的辅助函数，它返回一个带有`func(http.Handler) http.Handler`签名的函数。这意味着我们可以像用自定义中间件完全相同的方式来使用它。

```sh
$ go get github.com/goji/httpauth
```

> File: main.go

```golang
package main

import (
  "github.com/goji/httpauth"
  "net/http"
)

func main() {
  finalHandler := http.HandlerFunc(final)
  authHandler := httpauth.SimpleBasicAuth("username", "password")

  http.Handle("/", authHandler(finalHandler))
  http.ListenAndServe(":3000", nil)
}

func final(w http.ResponseWriter, r *http.Request) {
  w.Write([]byte("OK"))
}
```

如果你运行这个例子，你将会得到一个有效凭证和无效凭证的预期响应：

```sh
$ curl -i username:password@localhost:3000
HTTP/1.1 200 OK
Content-Length: 2
Content-Type: text/plain; charset=utf-8

OK
$ curl -i username:wrongpassword@localhost:3000
HTTP/1.1 401 Unauthorized
Content-Type: text/plain; charset=utf-8
Www-Authenticate: Basic realm=""Restricted""
Content-Length: 13

Unauthorized
```

Gorilla 的`LoggingHandler`  - 记录了[Apache 风格的日志](http://httpd.apache.org/docs/1.3/logs.html#common) - 这个中间件跟之前的会有一点不同。

它使用签名`func(out io.Writer, h http.Handler) http.Handler`，因此它不仅需要下一个处理程序，还需要用来写入日志的[io.Writer](http://golang.org/pkg/io/#Writer)。

下面这个简单的例子，我们将日志写入 server.log 文件：

```sh
go get github.com/gorilla/handlers
```

> File: main.go

```golang
package main

import (
  "github.com/gorilla/handlers"
  "net/http"
  "os"
)

func main() {
  finalHandler := http.HandlerFunc(final)

  logFile, err := os.OpenFile("server.log", os.O_WRONLY|os.O_CREATE|os.O_APPEND, 0666)
  if err != nil {
    panic(err)
  }

  http.Handle("/", handlers.LoggingHandler(logFile, finalHandler))
  http.ListenAndServe(":3000", nil)
}

func final(w http.ResponseWriter, r *http.Request) {
  w.Write([]byte("OK"))
}
```

在这样一个简单的例子中，我们的代码相当清楚。但是，如果我们想将`LoggingHandler`作为更长的中间件调用链的一部分，会发生什么？我们很容易得到一个看起来像这样的声明……

```golang
http.Handle("/", handlers.LoggingHandler(logFile, authHandler(enforceXMLHandler(finalHandler))))
```

……这种方式真是让我很头疼！

一种让它更清晰的方法是使用签名`func(http.Handler) http.Handler`来创建一个构造函数（命名为`myLoggingHandler`）。这会使得它与其他中间件的嵌套更整洁：

```golang
func myLoggingHandler(h http.Handler) http.Handler {
  logFile, err := os.OpenFile("server.log", os.O_WRONLY|os.O_CREATE|os.O_APPEND, 0666)
  if err != nil {
    panic(err)
  }
  return handlers.LoggingHandler(logFile, h)
}

func main() {
  finalHandler := http.HandlerFunc(final)

  http.Handle("/", myLoggingHandler(finalHandler))
  http.ListenAndServe(":3000", nil)
}
```

如果你运行此应用并发送一些请求给它，你的`server.log`文件应如下所示：

```sh
$ cat server.log
127.0.0.1 - - [21/Oct/2014:18:56:43 +0100] "GET / HTTP/1.1" 200 2
127.0.0.1 - - [21/Oct/2014:18:56:36 +0100] "POST / HTTP/1.1" 200 2
127.0.0.1 - - [21/Oct/2014:18:56:43 +0100] "PUT / HTTP/1.1" 200 2
```

如果你有兴趣，这里给出一份把该文章的[3 个中间件处理函数](https://gist.github.com/alexedwards/6f9496caecb2996ac61d)的要点结合在了一个例子。

边注：注意`Gorilla LoggingHandler`正在记录日志中的响应状态（`200`）和响应长度（`2`）。这比较有趣，上游日志记录中间件怎么获取了应用处理程序写入的响应体的信息？

它通过定义自己的`responseLogger`类型来实现这一点，该类型装饰`http.ResponseWriter`，并创建自定义`responseLogger.Write()`和`responseLogger.WriteHeader()`方法。这些方法不仅可以写入响应，还可以存储响应的大小和状态以供后面检查。 Gorilla 的`LoggingHandler`将`responseLogger`传递给链中的下一个处理程序，取代了普通的`http.ResponseWriter`。

## 额外的工具

[Alice by Justinas Stankevičius](https://github.com/justinas/alice)是一个巧妙且非常轻量级的包，为链式中间件处理程序提供了一些语法糖。最基本的 Alice 包可以让你重新下面的代码：

```golang
http.Handle("/", myLoggingHandler(authHandler(enforceXMLHandler(finalHandler))))
```

变为：

```golang
http.Handle("/", alice.New(myLoggingHandler, authHandler, enforceXMLHandler).Then(finalHandler))
```

至少在我看来，瞥一眼这个代码就能让人大致理解了。但是，Alice 包的真正好处是只需要指定一次处理链，并能将其重用于多个路由当中。像这样：

```golang
stdChain := alice.New(myLoggingHandler, authHandler, enforceXMLHandler)

http.Handle("/foo", stdChain.Then(fooHandler))
http.Handle("/bar", stdChain.Then(barHandler))
```

如果你喜欢这篇博文，请不要忘记查看我的新书[《用 Go 构建专​​业的 Web 应用程序》](https://lets-go.alexedwards.net/)

在推特上关注我 [@ajmedwards](https://twitter.com/ajmedwards)

此文章中的所有代码都可以在[MIT Licence](http://opensource.org/licenses/MIT)许可下免费使用。