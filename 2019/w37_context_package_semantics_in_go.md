# Context Package Semantics In Go

- 原文地址：https://www.ardanlabs.com/blog/2019/09/context-package-semantics-in-go.html
- 原文作者：[William Kennedy](https://www.ardanlabs.com)
- 译文出处：https://www.ardanlabs.com
- 本文永久链接：https://github.com/gocn/translator/blob/master/2019/w37_context_package_semantics_in_go.md
- 译者：[咔叽咔叽](https://github.com/watermelo)
- 校对者：

## Introduction

The Go programming language has the built-in keyword `go` to create goroutines, but has no keywords or direct support for terminating goroutines. In a real world service, the ability to time-out and terminate goroutines is critical for maintaining the health and operation of a service. No request or task can be allowed to run forever so identifying and managing latency is a responsibility every programmer has.

A solution provided by the Go team to solve this problem is the Context package. It was written and introduced by [Sameer Ajmani](https://twitter.com/Sajma) back in 2014 at the Gotham Go conference. He also wrote a blog post for the Go blog.

Talk Video: [https://vimeo.com/115309491](https://vimeo.com/115309491)  
Slide Deck: [https://talks.golang.org/2014/gotham-context.slide#1](https://talks.golang.org/2014/gotham-context.slide#1)  
Blog Post: [https://blog.golang.org/context](https://blog.golang.org/context)

Through this published work and conversations I’ve had with Sameer over the years, a set of semantics have evolved. In this post, I will provide these semantics and do my best to show you examples in code.

## Incoming requests to a server should create a Context

The time to create a Context is always as early as possible in the processing of a request or task. Working with Context early in the development cycle will force you to design API’s to take a Context as the first parameter. Even if you are not 100% sure a function needs a Context, it’s easier to remove the Context from a few functions than try to add Context later.

**Listing 1**  
[https://github.com/ardanlabs/service/blob/master/internal/platform/web/web.go#L75](https://github.com/ardanlabs/service/blob/master/internal/platform/web/web.go#L75)

```go
 75 // Handle is our mechanism for mounting Handlers for a given HTTP verb and path
 76 // pair, this makes for really easy, convenient routing.
 77 func (a *App) Handle(verb, path string, handler Handler, mw ...Middleware) {
    ...
 85     // The function to execute for each request.
 86     h := func(w http.ResponseWriter, r *http.Request, params map[string]string) {
 87         ctx, span := trace.StartSpan(r.Context(), "internal.platform.web")
 88         defer span.End()
    ...
 106    // Add this handler for the specified verb and route.
 107    a.TreeMux.Handle(verb, path, h)
 108 }
```

In listing 1, you see code taken from the [service](https://github.com/ardanlabs/service) project we teach at Ardan Labs. Line 86 defines a handler function that is bound to all routes as shown on line 107\. It’s this function that starts to process any incoming requests. On line 87, a [span](https://opencensus.io/) is created for the request which takes as its first parameter a Context. This is the first time in the service code a Context is needed.

What’s great here is that the `http.Request` value already contains a Context. This was [added](https://golang.org/doc/go1.9#minor_library_changes) in version 1.9 of Go. This means the code doesn’t need to manually create a top-level Context. If we were using version 1.8 of Go, then you would need to create an empty Context before the call to `StartSpan` by using the `context.Background` function.

**Listing 2**  
[https://golang.org/pkg/context/#Background](https://golang.org/pkg/context/#Background)

```go
87    ctx := context.Background()
88    ctx, span := trace.StartSpan(ctx, "internal.platform.web")
89    defer span.End()
```

Listing 2 shows what the code would have to look like in version 1.8 of Go. As it’s described in the package documentation,

*Background returns a non-nil, empty Context. It’s never canceled, has no values, and has no deadline. It is typically used by the main function, initialization, and tests, and as the top-level Context for incoming requests.*

It’s an idiom in Go to use the variable name `ctx` for all Context values. Since a Context is an interface, no pointer semantics should be used.

**Listing 3**  
[https://golang.org/pkg/context/#Context](https://golang.org/pkg/context/#Context)

```go
type Context interface {
    Deadline() (deadline time.Time, ok bool)
    Done() <-chan struct{}
    Err() error
    Value(key interface{}) interface{}
}
```

Every function that accepts a Context should get its own copy of the interface value.

## Outgoing calls to servers should accept a Context

The idea behind this semantic is that higher level calls need to tell lower level calls how long they are willing to wait. A great example of this is with the `http` package and the version 1.9 changes made to the `Do` method to respect timeouts on a request.

**Listing 4**  
[https://play.golang.org/p/9x4kBKO-Y6q](https://play.golang.org/p/9x4kBKO-Y6q)

```go
06 package main
07 
08 import (
09     "context"
10     "io"
11     "log"
12     "net/http"
13     "os"
14     "time"
15 )
16 
17 func main() {
18
19     // Create a new request.
20     req, err := http.NewRequest("GET", "https://www.ardanlabs.com/blog/post/index.xml", nil)
21     if err != nil {
22         log.Println("ERROR:", err)
23         return
24     }
25
26     // Create a context with a timeout of 50 milliseconds.
27     ctx, cancel := context.WithTimeout(req.Context(), 50*time.Millisecond)
28     defer cancel()
29
30     // Bind the new context into the request.
31     req = req.WithContext(ctx)
32
33     // Make the web call and return any error. Do will handle the
34     // context level timeout.
35     resp, err := http.DefaultClient.Do(req)
36     if err != nil {
37       log.Println("ERROR:", err)
38       return
39     }
40
41     // Close the response body on the return.
42     defer resp.Body.Close()
43
44     // Write the response to stdout.
45     io.Copy(os.Stdout, resp.Body)
46 }
```

In listing 4, the program issues a request for the Ardan rss blog feed with a timeout of 50 milliseconds. On lines 20-24, the request is created to make a `GET` call against the provided URL. Lines 27-28 create a Context with a 50 millisecond timeout. A new API added to the `Request` value back in version 1.9 is the `WithContext` method. This method allows the `Request` value’s Context field to be updated. On line 31, that is exactly what the code is doing.

On line 35, the actual request is made using the `Do` method from the `http` package’s `DefaultClient` value. The `Do` method will respect the timeout value of 50 milliseconds that is now set inside the Context within the `Request` value. What you are seeing is my code (higher level function) telling the `Do` method (lower level function) how long I’m willing to wait for the `Do` operation to be completed.

## Do not store Contexts inside a struct type; instead, pass a Context explicitly to each function that needs it

Essentially, any function that is performing I/O should accept a Context value as it’s first parameter and respect any timeout or deadline configured by the caller. In the case of `Request`, there was backwards compatibility issues to consider. So instead of changing the API’s, the mechanic shown in the last section was implemented.

There are exceptions to every rule. However, within the scope of this post and any API’s from the standard library that take a Context, the idiom is to have the first parameter accept the Context value.

**Figure 1**  
![](https://github.com/gocn/translator/static/images/w37_context_package_semantics_in_go/figure1.png)

Figure 1 shows an example from the `net` package where the first parameter of each method takes a Context as the first parameter and uses the `ctx` variable name idiom.

## The chain of function calls between them must propagate the Context

This is an important rule since a Context is request or task based. You want the Context and any changes made to it during the processing of the request or task to be propagated and respected.

**Listing 5**  
[https://github.com/ardanlabs/service/blob/master/cmd/sales-api/internal/handlers/user.go#L24](https://github.com/ardanlabs/service/blob/master/cmd/sales-api/internal/handlers/user.go#L24)

```plain
23 // List returns all the existing users in the system.
24 func (u *User) List(ctx context.Context, w http.ResponseWriter, r *http.Request, params map[string]string) error {
25     ctx, span := trace.StartSpan(ctx, "handlers.User.List")
26     defer span.End()
27
28     users, err := user.List(ctx, u.db)
29     if err != nil {
30         return err
31     }
32
33     return web.Respond(ctx, w, users, http.StatusOK)
34 }
```

In listing 5, you see a handler function called `List` which is executed when a user makes an HTTP request for this endpoint. The handler accepts as its first parameter a Context, since it’s part of a request and will perform I/O. You can see on lines 25, 28 and 33 that the same Context value is propagated down the call stack.

A new Context value is not created since this function requires no changes to it. If a new top-level Context value would be created by this function, any existing Context information from a higher-level call associated with this request would be lost. This is not what you want.

**Listing 6**  
[https://github.com/ardanlabs/service/blob/master/internal/user/user.go#L34](https://github.com/ardanlabs/service/blob/master/internal/user/user.go#L34)

```plain
33 // List retrieves a list of existing users from the database.
34 func List(ctx context.Context, db *sqlx.DB) ([]User, error) {
35     ctx, span := trace.StartSpan(ctx, "internal.user.List")
36     defer span.End()
37
38     users := []User{}
39     const q = `SELECT * FROM users`
40
41     if err := db.SelectContext(ctx, &users, q); err != nil {
42         return nil, errors.Wrap(err, "selecting users")
43     }
44
45     return users, nil
46 }
```

In listing 6, you see the declaration of the `List` method that was called on line 28 in listing 5\. Once again this method accepts a Context as its first parameter. This value is then propagated down the call stack once again on lines 35 and 41. Since line 41 is a database call, that function should be respecting any timeout information set in the Context from any caller above.

## Replace a Context using WithCancel, WithDeadline, WithTimeout, or WithValue

Because each function can add/modify the Context for their specific needs, and those changes should not affect any function that was called before it, the Context uses value semantics. This means any change to a Context value creates a new Context value that is then propagated forward.

**Listing 7**  
[https://play.golang.org/p/8RdBXtfDv1w](https://play.golang.org/p/8RdBXtfDv1w)

```plain
18 func main() {
19
20     // Set a duration.
21     duration := 150 * time.Millisecond
22
23     // Create a context that is both manually cancellable and will signal
24     // cancel at the specified duration.
25     ctx, cancel := context.WithTimeout(context.Background(), duration)
26     defer cancel()
27
28     // Create a channel to receive a signal that work is done.
29     ch := make(chan data, 1)
30
31     // Ask the goroutine to do some work for us.
32     go func() {
33
34         // Simulate work.
35         time.Sleep(50 * time.Millisecond)
36
37         // Report the work is done.
38         ch <- data{"123"}
39     }()
40
41     // Wait for the work to finish. If it takes too long, move on.
42     select {
43         case d := <-ch:
44             fmt.Println("work complete", d)
45
46         case <-ctx.Done():
47             fmt.Println("work cancelled")
48     }
49 }
```

In listing 7, there is a small program that shows the value semantic nature of the `WithTimeout` function. On line 25, the call to `WithTimeout` returns a new Context value and a `cancel` function. Since the function call requires a parent Context, the code uses the `Background` function to create a top-level empty Context. This is what the `Background` function is for.

Moving forward the Context value created by the `WithTimeout` function is used. If any future functions in the call chain need their own specific timeout or deadline, they should also use the appropriate `With` function and this new Context value as the parent.

It’s critically important that any `cancel` function returned from a `With` function is executed before that function returns. This is why the idiom is to use the `defer` keyword right after the `With` call, as you see on line 26\. Not doing this will cause memory leaks in your program.

## When a Context is canceled, all Contexts derived from it are also canceled

The use of value semantics for the Context API means each new Context value is given everything the parent Context has plus any new changes. This means if a parent Context is cancelled, all children derived by that parent Context are cancelled as well.

**Listing 8**  
[https://play.golang.org/p/PmhTXiCZUP1](https://play.golang.org/p/PmhTXiCZUP1)

```plain
20 func main() {
21
22     // Create a Context that can be cancelled.
23     ctx, cancel := context.WithCancel(context.Background())
24     defer cancel()
25
26     // Use the Waitgroup for orchestration.
27     var wg sync.WaitGroup
28     wg.Add(10)
29
30     // Create ten goroutines that will derive a Context from
31     // the one created above.
32     for i := 0; i < 10; i++ {
33         go func(id int) {
34             defer wg.Done()
35
36             // Derive a new Context for this goroutine from the Context
37             // owned by the main function.
38             ctx := context.WithValue(ctx, key, id)
39
40             // Wait until the Context is cancelled.
41             <-ctx.Done()
42             fmt.Println("Cancelled:", id)
43         }(i)
44     }
45
46     // Cancel the Context and any derived Context's as well.
47     cancel()
48     wg.Wait()
49 }
```

In listing 8, the program creates a Context value that can be cancelled on line 23. Then on lines 32-44, ten goroutines are created. Each goroutine places their unique id inside their own Context value on line 38. The call to `WithValue` is passed the `main` function’s Context value as its parent. Then on line 41, each goroutine waits until their Context is cancelled.

On line 47, the main goroutine cancels its Context value and then waits on line 48 for all ten of the goroutines to receive the signal before shutting down the program. Once the `cancel` function is called, all ten goroutines on line 41 will become unblocked and print that they have been cancelled. One call to `cancel` to cancel them all.

This also shows that the same Context may be passed to functions running in different goroutines. A Context is safe for simultaneous use by multiple goroutines.

## Do not pass a nil Context, even if a function permits it. Pass a TODO context if you are unsure about which Context to use

One of my favorite parts of the Context package is the `TODO` function. I am a firm believer that a programmer is always drafting code. This is no different than a writer who is drafting versions of an article. You never know everything as you write code, but hopefully you know enough to move things along. In the end, you are constantly learning, refactoring and testing along the way.

There have been many times when I knew I needed a Context but was unsure where it would come from. I knew I was not responsible for creating the top-level Context so using the `Background` function was out of the question. I needed a temporary top-level Context until I figured out where the actual Context was coming from. This is when you should use the `TODO` function over the `Background` function.

## Use context values only for request-scoped data that transits processes and APIs, not for passing optional parameters to functions

This might be the most important semantic of all. Do not use the Context value to pass data into a function when that data is required by the function to execute its code successfully. In other words, a function should be able to execute its logic with an empty Context value. In cases where a function requires information to be in the Context, if that information is missing, the program should fail and signal the application to shutdown.

A classic example of the misuse of passing data into a function call using Context is with database connections. As a general rule, you want to follow this order when moving data around your program.

*   Pass the data as a function parameter This is the clearest way to move data around the program without hiding it.

*   Pass the data through the receiver If the function that needs the data can’t have its signature altered, then use a method and pass the data through the receiver.

**Quick example of using a receiver**

Request handlers are a classic example of the second rule. Since a handler function is bound to a specific declaration, the handler signature can’t be altered.

**Listing 9**  
[https://github.com/ardanlabs/service/blob/master/cmd/sales-api/internal/handlers/user.go#L24](https://github.com/ardanlabs/service/blob/master/cmd/sales-api/internal/handlers/user.go#L24)

```plain
23 // List returns all the existing users in the system.
24 func (u *User) List(ctx context.Context, w http.ResponseWriter, r *http.Request, params map[string]string) error {
25     ctx, span := trace.StartSpan(ctx, "handlers.User.List")
26     defer span.End()
27
28     users, err := user.List(ctx, u.db)
29     if err != nil {
30         return err
31     }
32
33     return web.Respond(ctx, w, users, http.StatusOK)
34 }
```

In listing 9, you see the `List` handler method from the service project. The signature of these methods are bound to the what the web framework defined and they can’t be altered. However, to make the business call on line 28, a database connection is required. This code finds the connection pool not from the Context value that is passed in, but from the receiver.

**Listing 10**  
[https://github.com/ardanlabs/service/blob/master/cmd/sales-api/internal/handlers/user.go#L15](https://github.com/ardanlabs/service/blob/master/cmd/sales-api/internal/handlers/user.go#L15)

```plain
15 // User represents the User API method handler set.
16 type User struct {
17     db            *sqlx.DB
18     authenticator *auth.Authenticator
19
20 // ADD OTHER STATE LIKE THE LOGGER AND CONFIG HERE.
21 }
```
In listing 10, you see the declaration of the receiver type. Anything that a request handler needs is defined as fields. This allows for information to not be hidden and for the business layer to function with an empty Context value.

**Listing 11**  
[https://github.com/ardanlabs/service/blob/master/cmd/sales-api/internal/handlers/routes.go#L14](https://github.com/ardanlabs/service/blob/master/cmd/sales-api/internal/handlers/routes.go#L14)

```plain
14 // API constructs an http.Handler with all application routes defined.
15 func API(shutdown chan os.Signal, log *log.Logger, db *sqlx.DB, authenticator *auth.Authenticator) http.Handler {
16
    ...
26     // Register user management and authentication endpoints.
27     u := User{
28         db:            db,
29         authenticator: authenticator,
30     }
31
32     app.Handle("GET", "/v1/users", u.List)
```

In listing 11, you see the code that constructs a `User` value and then binds the `List` method into the route. Once again, since the signature of a handler function is unchangeable, using a receiver and methods is the next best way to pass data without it being hidden.

**Debugging or tracing data is safe to pass in a Context**

Data that can be stored and received from a Context value is debug and tracing information.

**Listing 12**  
[https://github.com/ardanlabs/service/blob/master/internal/platform/web/web.go#L23](https://github.com/ardanlabs/service/blob/master/internal/platform/web/web.go#L23)

```plain
23 // Values represent state for each request.
24 type Values struct {
25     TraceID    string
26     Now        time.Time
27     StatusCode int
28 }
```

In listing 12, you see the declaration of a type that is constructed and stored inside each Context value created for a new request. The three fields provide tracing and debugging information for the request. This information is gathered as the request progresses.

**Listing 13**  
[https://github.com/ardanlabs/service/blob/master/internal/platform/web/web.go#L75](https://github.com/ardanlabs/service/blob/master/internal/platform/web/web.go#L75)

```plain
75 // Handle is our mechanism for mounting Handlers for a given HTTP verb and path
76 // pair, this makes for really easy, convenient routing.
77 func (a *App) Handle(verb, path string, handler Handler, mw ...Middleware) {
78
    ...
79     // The function to execute for each request.
80     h := func(w http.ResponseWriter, r *http.Request, params map[string]string) {
    ...
84     // Set the context with the required values to
85     // process the request.
86     v := Values{
87         TraceID: span.SpanContext().TraceID.String(),
88         Now:     time.Now(),
89     }
90     ctx = context.WithValue(ctx, KeyValues, &v)
```

In listing 13, you see how the `Values` type is constructed on line 86 and then stored inside the Context on line 90\. It’s the logging middleware that needs most of this information.

**Listing 14**  
[https://github.com/ardanlabs/service/blob/master/internal/mid/logger.go#L20](https://github.com/ardanlabs/service/blob/master/internal/mid/logger.go#L20)

```plain
20 // Create the handler that will be attached in the middleware chain.
21 h := func(ctx context.Context, w http.ResponseWriter, r *http.Request, params map[string]string) error {
    ...
25     // If the context is missing this value, request the service
26     // to be shutdown gracefully.
27     v, ok := ctx.Value(web.KeyValues).(*web.Values)
28     if !ok {
29         return web.NewShutdownError("web value missing from context")
30     }
    ...
34     log.Printf("%s : (%d) : %s %s -> %s (%s)",
35         v.TraceID, v.StatusCode,
36         r.Method, r.URL.Path,
37         r.RemoteAddr, time.Since(v.Now),
38     )
```

The consequence of passing information through the Context is shown in the code on lines 27-30 in listing 14\. The code is attempting to retrieve the `Values` data from the Context and checking if the data was there. If the data is not there, then a major integrity issue exists and the service needs to shutdown. This is done in the service code by sending a special error value back up through the application.

If you are passing database connections or user information into your business layer using a Context, you have two problems:

*   You need to be checking for integrity and you need a mechanism to shutdown the service quickly.

*   Testing and debugging becomes much harder and more complicated. You are walking away from better clarity and readability in your code.

## Conclusion

The Context package defines an API which provides support for deadlines, cancelation signals, and request-scoped values that can be passed across API boundaries and between goroutines. This API is an essential part of any application you will write in Go. Understanding the semantics is critical if your goal is to write reliable software with integrity.

In the post, I tried to breakdown the semantics that have been defined by the Go team. Hopefully you now have a better understanding of how to use Context more effectively. All the code examples are available to you. If you have any questions, please don’t hesitate to send me an email.

## Final Notes

*   Incoming requests to a server should create a Context.
*   Outgoing calls to servers should accept a Context.
*   Do not store Contexts inside a struct type; instead, pass a Context explicitly to each function that needs it.
*   The chain of function calls between them must propagate the Context.
*   Replace a Context using WithCancel, WithDeadline, WithTimeout, or WithValue.
*   When a Context is canceled, all Contexts derived from it are also canceled.
*   The same Context may be passed to functions running in different goroutines; Contexts are safe for simultaneous use by multiple goroutines.
*   Do not pass a nil Context, even if a function permits it. Pass a TODO context if you are unsure about which Context to use.
*   Use context values only for request-scoped data that transits processes and APIs, not for passing optional parameters to functions.
