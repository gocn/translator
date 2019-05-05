# Making and Using HTTP Middleware

- 原文地址：[Making and Using HTTP Middleware](https://www.alexedwards.net/blog/making-and-using-middleware)
- 原文作者：Alex Edwards
- 译文出处: https://www.alexedwards.net/
- 本文永久链接：https://github.com/gocn/translator/blob/master/2019/w17_Making_and_Using_HTTP_Middleware.md
- 译者：[咔叽咔叽](https://github.com/watermelo)
- 校对：[fivezh](https://github.com/fivezh)

When you're building a web application there's probably some shared functionality that you want to run for many (or even all) HTTP requests. You might want to log every request, gzip every response, or check a cache before doing some heavy processing.

One way of organising this shared functionality is to set it up as middleware – self-contained code which independently acts on a request before or after your normal application handlers. In Go a common place to use middleware is between a ServeMux and your application handlers, so that the flow of control for a HTTP request looks like:

```sh
ServeMux => Middleware Handler => Application Handler
```

In this post I'm going to explain how to make custom middleware that works in this pattern, as well as running through some concrete examples of using third-party middleware packages.

## The Basic Principles

Making and using middleware in Go is fundamentally simple. We want to:

- Implement our middleware so that it satisfies the [http.Handler](http://golang.org/pkg/net/http/#Handler) interface.
- Build up a chain of handlers containing both our middleware handler and our normal application handler, which we can register with a [http.ServeMux](http://golang.org/pkg/net/http/#ServeMux).

I'll explain how.

Hopefully you're already familiar with the following method for constructing a handler (if not, it's probably best to read [this primer](https://www.alexedwards.net/blog/a-recap-of-request-handling) before continuing).

```golang
func messageHandler(message string) http.Handler {
  return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    w.Write([]byte(message)
  })
}
```

In this handler we're placing our logic (a simple `w.Write`) in an anonymous function and closing-over the `message` variable to form a closure. We're then converting this closure to a handler by using the [http.HandlerFunc](http://golang.org/pkg/net/http/#HandlerFunc) adapter and returning it.

We can use this same approach to create a chain of handlers. Instead of passing a string into the closure (like above) we could pass the next handler in the chain as a variable, and then transfer control to this next handler by calling it's `ServeHTTP()` method.

This gives us a complete pattern for constructing middleware:

```golang
func exampleMiddleware(next http.Handler) http.Handler {
  return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    // Our middleware logic goes here...
    next.ServeHTTP(w, r)
  })
}
```

You'll notice that this middleware function has a `func(http.Handler) http.Handler` signature. It accepts a handler as a parameter and returns a handler. This is useful for two reasons:

- Because it returns a handler we can register the middleware function directly with the standard ServeMux provided by the net/http package.
- We can create an arbitrarily long handler chain by nesting middleware functions inside each other. For example:

```golang
http.Handle("/", middlewareOne(middlewareTwo(finalHandler)))
```

## Illustrating the Flow of Control

Let's look at a stripped-down example with some middleware that simply writes log messages to stdout:

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

Run this application and make a request to `http://localhost:3000`. You should get log output similar to this:

```sh
$ go run main.go
2014/10/13 20:27:36 Executing middlewareOne
2014/10/13 20:27:36 Executing middlewareTwo
2014/10/13 20:27:36 Executing finalHandler
2014/10/13 20:27:36 Executing middlewareTwo again
2014/10/13 20:27:36 Executing middlewareOne again
```

It's clear to see how control is being passed through the handler chain in the order we nested them, and then back up again in the *reverse direction*.

We can stop control propagating through the chain at any point by issuing a `return` from a middleware handler.

In the example above I've included a conditional return in the `middlewareTwo` function. 
Try it by visiting [http://localhost:3000/foo](http://localhost:3000/foo) and checking the log again – you'll see that this time the request gets no further than `middlewareTwo` before passing back up the chain.

## Understood. How About a Proper Example

OK, let's say that we're building a service which processes requests containing a XML body. We want to create some middleware which a) checks for the existence of a request body, and b) sniffs the body to make sure it is XML. If either of those checks fail, we want our middleware to write an error message and to stop the request from reaching our application handlers.

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

This looks good. Let's test it by creating a simple XML file:

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
And making some requests using cURL:

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

## Using Third-Party Middleware

Rather than rolling your own middleware all the time you might want to use a third-party package. We're going to look at a couple here: [goji/httpauth](http://elithrar.github.io/article/httpauth-basic-auth-for-go/) and Gorilla's [LoggingHandler](http://www.gorillatoolkit.org/pkg/handlers#LoggingHandler).

The goji/httpauth package provides HTTP Basic Authentication functionality. It has a [SimpleBasicAuth](https://godoc.org/github.com/goji/httpauth#SimpleBasicAuth) helper which returns a function with the signature `func(http.Handler) http.Handler`. This means we can use it in exactly the same way as our custom-built middleware.

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

If you run this example you should get the responses you'd expect for valid and invalid credentials:

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

Gorilla's LoggingHandler – which records [Apache-style logs](http://httpd.apache.org/docs/1.3/logs.html#common) – is a bit different.

It uses the signature `func(out io.Writer, h http.Handler) http.Handler`, so it takes not only the next handler but also the [io.Writer](http://golang.org/pkg/io/#Writer) that the log will be written to.

Here's a simple example in which we write logs to a `server.log` file:

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

In a trivial case like this our code is fairly clear. 
But what happens if we want to use LoggingHandler as part of a larger middleware chain? 
We could easily end up with a declaration looking something like this...

```golang
http.Handle("/", handlers.LoggingHandler(logFile, authHandler(enforceXMLHandler(finalHandler))))
```

... And that makes my brain hurt!

One way to make it clear is by creating a constructor function (let's call it `myLoggingHandler`) with the signature `func(http.Handler) http.Handler`. This will allow us to nest it more neatly with other middleware:

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

If you run this application and make a few requests your `server.log` file should look something like this:

```sh
$ cat server.log
127.0.0.1 - - [21/Oct/2014:18:56:43 +0100] "GET / HTTP/1.1" 200 2
127.0.0.1 - - [21/Oct/2014:18:56:36 +0100] "POST / HTTP/1.1" 200 2
127.0.0.1 - - [21/Oct/2014:18:56:43 +0100] "PUT / HTTP/1.1" 200 2
```

If you're interested, here's a gist of the [three middleware handlers](https://gist.github.com/alexedwards/6f9496caecb2996ac61d) from this post combined in one example.

As a side note: notice that the Gorilla LoggingHandler is recording the response status (`200`) and response length (`2`) in the logs. This is interesting. 
How did the upstream logging middleware get to know about the response body written by our application handler?

It does this by defining it's own `responseLogger` type which wraps `http.ResponseWriter`, and creating custom `responseLogger.Write()` and `responseLogger.WriteHeader()` methods. 
These methods not only write the response but also store the size and status for later examination. Gorilla's LoggingHandler passes `responseLogger` onto the next handler in the chain, instead of the normal `http.ResponseWriter`.

## Additional Tools

[Alice by Justinas Stankevičius](https://github.com/justinas/alice) is a clever and very lightweight package which provides some syntactic sugar for chaining middleware handlers. At it's most basic Alice lets you rewrite this:

```golang
http.Handle("/", myLoggingHandler(authHandler(enforceXMLHandler(finalHandler))))
```

As this:

```golang
http.Handle("/", alice.New(myLoggingHandler, authHandler, enforceXMLHandler).Then(finalHandler))
```

In my eyes at least, that code is slightly clearer to understand at a glance. However, the real benefit of Alice is that it lets you to specify a handler chain once and reuse it for multiple routes. Like so:

```golang
stdChain := alice.New(myLoggingHandler, authHandler, enforceXMLHandler)

http.Handle("/foo", stdChain.Then(fooHandler))
http.Handle("/bar", stdChain.Then(barHandler))
```

If you enjoyed this blog post, don't forget to check out my new book about how to [build professional web applications with Go](https://lets-go.alexedwards.net/)!

Follow me on Twitter [@ajmedwards](https://twitter.com/ajmedwards).

All code snippets in this post are free to use under the [MIT Licence](http://opensource.org/licenses/MIT).