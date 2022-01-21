# What I'd like to see in go2

- 原文地址：https://www.sethvargo.com/what-id-like-to-see-in-go-2
- 原文作者：Seth Vargo
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w03_What_id_like_to_see_in_go2
- 译者：[1-st](https://github.com/1-st)
- 校对：
 
![What id like to see in go2](https://github.com/gocn/translator/raw/master/static/images/2022/w03_What_id_like_to_see_in_go2/courses-app-screenshot.png) 

Go is one of my favorite programming languages, but it is still far from perfect. Over the past 10 years, I have used Go to both build small side projects and large scale applications. While the language has evolved significantly from its original release in 2009, this post highlights some of the areas where I think Go still has room for improvement.

Before we get started, I want to be absolutely clear: I am NOT criticizing individual humans or their contributions. My only intent is to try and make Go the best programming language.

## A modern templating engine 

The Go standard library has two templating packages: text/template and html/template. They use roughly the same syntax, but html/template handles entity escaping and a few other web-specific constructs. Unfortunately neither package is suitable or powerful enough for sufficiently advanced use cases without heavy developer investment.

- *Compile-time errors.* Unlike Go itself, the Go templating packages will happily let you pass an integer as a string, only to render an error at runtime. This means developers need to rigorously test all possible inputs into their templates, instead of being able to rely on the type system. Go's templating packages should support compile time type checking.

- *A range clause that matches Go*. After 10 years, I still mess up the order for the range clause in Go templating, because it is sometimes backwards from Go itself. With two arguments, the templating engine matches the standard library:

  ```go
  {{ range $a, $b := .Items }} // [$a = 0, $b = "foo"]
  for a, b := range items { // [a = 0, b = "foo"]
  ```
  However, with only one argument, the template engine yields the value while Go renders yields the index:

  ```go
  {{ range $a := .Items }} // [$a = "foo"]
  for a := range items { // [a = 0]
  ```
  Go's template package should match how the standard library works.

- *Batteries included, reflection optional.* As a general rule, I think most developers should never need to interact with reflection. However, if you want to do anything beyond basic addition and subtraction, Go's templating packages are going to force you into reflection. The built-in functions are incredibly minimal, and only satisfy a small subset of use cases.

  After I wrote [Consul Template](https://github.com/hashicorp/consul-template), it became pretty clear that the standard Go template functions were not sufficient to meet the needs of users. More than half of issues were about trying to use Go's templating language. Today, Consul Template has [more than 50 "helper" functions](https://github.com/hashicorp/consul-template/blob/master/docs/templating-language.md), the vast majority of which should really in the standard templating language.

  Consul Template isn't alone here. [Hugo](https://gohugo.io/) also has a [pretty expansive list of helper functions](https://gohugo.io/functions/), again, the vast majority of which should really be in the standard templating language. Even on my most recent project, [Exposure Notifications](https://g.co/ens), we [could not escape the reflection](https://github.com/google/exposure-notifications-verification-server/blob/0ec489ba95137d5be10e1617d1dcdc2d1ee6e5e9/pkg/render/renderer.go#L232-L280).

  Go's templating language really needs to have broader function surface area.

- *Short-circuit evaluation.*

  EDIT: As many have pointed out, this feature is [coming in Go 1.18](https://tip.golang.org/doc/go1.18#text/template).

  Go's templating language always evaluates an entire conditional in a clause, which makes for some really fun bugs (that again will not manifest until runtime.) Consider the following, where $foo could be nil:
  ```go
  {{ if (and $foo $foo.Bar) }}
  ```
  It may seem like this is fine, but both of the and conditions will be evaluated - there is no short-circuit logic within an expression. That means this will throw a runtime exception if $foo is nil.

  To get around this, you have to separate the conditional clauses:
  ```go
  {{ if $foo }}
  {{ if $foo.Bar }}
  {{ end }}
  ```
  Go's templating language should function like the standard library and stop executing a conditional on the first truthy value.

- *Investment in web-specific utilities.* I was a Ruby on Rails developer for many years, and I really loved how easy it was to build beautiful web applications. With Go's templating language, even the simplest of tasks - like printing a list of items to a sentence - is unapproachable for beginners, especially when compared to Rails' Enumerable#to_sentence.

## Improved range so as to not copy values
While it is very well-documented, it is always unexpected that values in a range clause are copied. For example, consider the following code:
```go
type Foo struct {
  bar string
}

func main() {
  list := []Foo{{"A"}, {"B"}, {"C"}}

  cp := make([]*Foo, len(list))
  for i, value := range list {
    cp[i] = &value
  }

  fmt.Printf("list: %q\n", list)
  fmt.Printf("cp: %q\n", cp)
}
```
What is the value of cp? If you said [A B C], sadly you are incorrect. The value of cp is actually:

```go
  [C C C]
```
This is because Go uses a copy of the value instead of the value itself in the range clause. In Go 2.0, the range clause should pass values by reference. There are already a few proposals for Go 2.0 in this space, including [improve for-loop ergonomics](https://github.com/golang/go/issues/24282) and [redefine range loop variables in each iteration](https://github.com/golang/go/issues/20733), so I am cautiously hopeful on this one.

## Deterministic select
In cases where multiple conditions of a select statement are true, the winning case is chosen via a uniform pseudo-random selection. This is a very subtle source of errors, and it is exacerbated by the similar-looking switch statement which does evaluate in the order in which it is written.

Consider the following code which we would like to behave as "if the system is stopped, do nothing. Otherwise wait for new work for up to 5 seconds, then timeout":
```go
for {
  select {
  case <-doneCh: // or <-ctx.Done():
    return
  case thing := <-thingCh:
    // ... long-running operation
  case <-time.After(5*time.Second):
    return fmt.Errorf("timeout")
  }
}
```
If multiple conditions are true when entering the select statement (e.g. doneCh is closed and more than 5 seconds have passed), it is undetermined behavior for which path will execute. This makes writing correct cancellation code annoyingly verbose:
```go
for {
  // Check here in case we've been CPU throttled for an extended time, we need to
  // check graceful stop or risk returning a timeout error.
  select {
  case <-doneCh:
    return
  default:
  }

  select {
  case <-doneCh:
    return
  case thing := <-thingCh:
    // Even though this case won, we still might ALSO be stopped.
    select {
    case <-doneCh:
      return
    default:
    }
    // ...
  default <-time.After(5*time.Second):
    // Even though this case won, we still might ALSO be stopped.
    select {
    case <-doneCh:
      return
    default:
    }
    return fmt.Errorf("timeout")
  }
}
```
If select were updated to be deterministic, the original code (which is much simpler and easier to reach in my opinion) would work as intended. However, due to the non-deterministic nature of select, we have to continuously check the dominant condition.

Tangentially related, I would love to see a shorthand syntax for "read from this channel if it contains any messages, otherwise continue along". The current syntax is verbose:
```go
select {
case <-doneCh:
  return
default:
}
I would love to see a more succinct version of this check, perhaps a syntax like:

select <-?doneCh: // not valid Go
```
## Structured logging interfaces
Go's standard library includes the log package, which is fine for basic use. However, most production systems want structured logging, and there is [no shortage](https://www.client9.com/logging-packages-in-golang/) of structured logging libraries in Go:

- [apex/log](https://github.com/apex/log)
- [go-kit/log](https://github.com/go-kit/kit/tree/master/log)
- [golang/glog](https://github.com/golang/glog)
- [hashicorp/go-hclog](https://github.com/hashicorp/go-hclog)
- [inconshreveable/log15](https://github.com/inconshreveable/log15)
- [rs/zerolog](https://github.com/rs/zerolog)
- [sirupsen/logrus](https://github.com/sirupsen/logrus)
- [uber/zap](https://github.com/uber-go/zap) 

Go's lack of opinion in this space has led to the proliferation of these packages, most of which have incompatible functions and signatures. As a result, it is impossible for a library author to emit structured logs. For example, I would love to be able to emit structured logs in [go-retry](https://github.com/sethvargo/go-retry), [go-envconfig](https://github.com/sethvargo/go-envconfig), or [go-githubactions](https://github.com/sethvargo/go-githubactions), but doing so would require tightly coupling with one of these libraries. Ideally I want my library users to have choice over their structure logging solution, but the lack of a common interface for structure logging makes this extremely difficult.

*The Go standard library needs to define a structured logging interface*, and all these existing upstream packages can choose to implement that interface. Then, as a library author, I can choose to accept a log.StructuredLogger interface and implementers can make their own choices:
```go
func WithLogger(l log.StructuredLogger) Option {
  return func(f *Foo) *Foo {
    f.logger = l
    return f
  }
}
```
I put together a quick sketch of what such an interface might look like:
```go
// StructuredLogger is an interface for structured logging.
type StructuredLogger interface {
  // Log logs a message.
  Log(message string, fields ...LogField)

  // LogAt logs a message at the provided level. Perhaps we could also have
  // Debugf, Infof, etc, but I think that might be too limiting for the standard
  // library.
  LogAt(level LogLevel, message string, fields ...LogField)

  // LogEntry logs a complete log entry. See LogEntry for the default values if
  // any fields are missing.
  LogEntry(entry *LogEntry)
}

// LogLevel is the underlying log level.
type LogLevel uint8

// LogEntry represents a single log entry.
type LogEntry struct {
  // Level is the log level. If no level is provided, the default level of
  // LevelError is used.
  Level LogLevel

  // Message is the actual log message.
  Message string

  // Fields is the list of structured logging fields. If two fields have the same
  // Name, the later one takes precedence.
  Fields []*LogField
}

// LogField is a tuple of the named field (a string) and its underlying value.
type LogField struct {
  Name  string
  Value interface{}
}
```
There is a lot of discussion to have around what the actual interface might look like, how to minimize allocations, and how to maximize compatibility, but the goal is to define an interface that other logging libraries could easily implement.

Back in my Ruby days, there was a proliferation of Ruby version managers, each with their own dotfile name and syntax. Fletcher Nichol managed to convince all the maintainers of those Ruby version managers to standardize on .ruby-version, simply by [writing a gist](https://gist.github.com/fnichol/1912050). It is my hope that we can do something similar in the Go community with structured logging.

## Multi-error handling
There are many cases, especially for background jobs or periodic tasks, where a system may process things in parallel or continue-on-error. In those cases, it's helpful to return a multi-error. There is no built-in support for handling collections of errors in the standard library.

Having clear and concise standard library definitions around multi-error handling could unify the community and reduce risks for improper error handling, as we saw with error wrapping and unwrapping.

## Marshalling for JSON error
Speaking of errors, did you know that embedding an error type into a struct field and then marshalling that struct as JSON will marshal the "error" field as {}?
```go
// https://play.golang.org/p/gl7BPJOgmjr
package main

import (
  "encoding/json"
  "fmt"
)

type Response1 struct {
  Err error `json:"error"`
}

func main() {
  v1 := &Response1{Err: fmt.Errorf("oops")}
  b1, err := json.Marshal(v1)
  if err != nil {
    panic(err)
  }

  // got: {"error":{}}
  // want: {"error": "oops"}
  fmt.Println(string(b1))
}
```
At least for the built-in errorString type, Go should marshal as the result of .Error(). Alternatively, for Go 2.0, JSON marshalling could return an error when trying to marshal an error type that does not implement custom marshalling logic.

## No more public variables in the standard library
As just one example, both http.DefaultClient and http.DefaultTransport are global variables with shared state. http.DefaultClient has no configured timeout, which makes it trivial to DOS your own service and create bottlenecks. Many packages mutate http.DefaultClient and http.DefaultTransport, which can waste days of developer resources tracking down bugs.

Go 2.0 should make these private and expose them via a function call that returns a unique allocation of the variable in question. Alternatively, Go 2.0 could implement "frozen" global variables, such that they cannot be mutated by other packages.

I also worry about this class of issues from a software supply chain standpoint. If I can develop a useful package that secretly modifies the http.DefaultTransport to use a custom RoundTripper that funnels all your traffic through my servers, that would make for a very bad time.

## Native support for buffered renderers
This is more of a "thing that isn't well-known or documented". Most examples, including the examples in the Go documentation, encourage behavior the following for marshalling JSON or rendering HTML via a web request:
```go
func toJSON(w http.ResponseWriter, i interface{}) {
  if err := json.NewEncoder(w).Encode(i); err != nil {
    http.Error(w, "oops", http.StatusInternalServerError)
  }
}

func toHTML(w http.ResponseWriter, tmpl string, i interface{}) {
  if err := templates.ExecuteTemplate(w, tmpl, i); err != nil {
    http.Error(w, "oops", http.StatusInternalServerError)
  }
}
```
However, for both of these cases, if i is sufficiently large, it is possible that encoding/execution fails after the first bytes (and a 200 status code) have been sent. At this point, the request is irrecoverable, since you can't change the response code.

The largely accepted solution to mitigate this is to render first, then copy to w. This still leaves a small room for error (where writing to w fails due to connection issues), but it ensures that encoding/execution is successful before sending the first byte. However, allocating a byte slice on each request can be expensive, so you typically [use a buffer pool](https://github.com/google/exposure-notifications-verification-server/blob/08797939a56463fe85f0d1b7325374821ee31448/pkg/render/html.go#L65-L91).

This approach is really verbose and pushes a lot of unnecessary complexity onto the implementer. Instead, it would be great if Go handled this buffer pool management automatically, potentially with functions like EncodePooled.

## Wrapping up
Go continues to be one of my favorite programming languages, which is why I feel comfortable highlighting these criticisms. As with any programming language, Go is constantly evolving. Do you think these are good ideas? Or are they terrible suggestions? Let me know [on Twitter](https://twitter.com/sethvargo)!

## About Seth
Seth Vargo is an engineer at Google. Previously he worked at HashiCorp, Chef Software, CustomInk, and some Pittsburgh-based startups. He is the author of [Learning Chef](https://www.amazon.com/Learning-Chef-Configuration-Management-Automation/dp/1491944935) and is passionate about reducing inequality in technology. When he is not writing, working on open source, teaching, or speaking at conferences, Seth advises non-profits.

Copyright © 2022 Seth Vargo • Licensed under the [CC BY-NC 4.0 license](https://www.sethvargo.com/license).