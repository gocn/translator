# My Go mistakes

Posted in Thursday, 18 February 2021.

In this post, I share mistakes I’ve made writing Go code for six years since the beginning of my journey with the language.

[![Gopher](https://henvic.dev/img/posts/my-go-mistakes/help.png)](https://golang.org/)

## init() functions

In Go, you can define the special function **init** multiple times on a single package or file. From [Effective Go](https://golang.org/doc/effective_go.html#init), we learn that:

> init is called after all the variable declarations in the package have evaluated their initializers, and those are evaluated only after all the imported packages have been initialized.

While there are cases where using init is the sure way to go, you want to reduce the number of times you use it. First, the typical use of this is to initialize globals, and you probably want to reduce your amount of globals.

A good reason to think twice before using it’s that you cannot call `init` functions from code. Another is that, despite being deterministic, it’s hard to predict your `init` functions' order of execution. The order depends on your imports and source-code filenames. Moving a package or renaming a file might change it.

A good case of using `init` is to initialize a lookup table that is expensive to calculate.

**Where do I regret using it?** I used `init` functions to define command structures and flags when using [cobra](https://github.com/spf13/cobra) to create CLI tools, but now I see it was unnecessary. By the way, Go 1.16 was released yesterday and offers some good news.

> Setting the GODEBUG environment variable to inittrace=1 now causes the runtime to emit a single line to standard error for each package init, summarizing its execution time and memory allocation. [Go 1.16 Release Notes](https://golang.org/doc/go1.16)

## Constants

This value wasn’t changed anywhere in the codebase:

```
// Version of the application
var Version = "master"
```

So I naively thought to make it a constant just for the sake of it! Suddenly, by changing `var` to `const`, I silently broke my application’s update notification system because I altered it during build time:

```
$ go build \
  -ldflags="-X 'github.com/henvic/wedeploycli/defaults.Version=$NEW_RELEASE_VERSION' \
  -X 'github.com/henvic/wedeploycli/defaults.Build=$BUILD_COMMIT' \
  -X 'github.com/henvic/wedeploycli/defaults.BuildTime=$BUILD_TIME'"
```

It turns out that… Constants are constants!

## Nil pointer dereference

As if breaking the update notification wasn’t enough, I forgot to check if a pointer value was `nil` and broke the update command. Thankfully, it was fixed minutes afterward, after I spotted it on my post-release tests, so the impact was _null_.

Once I read that you should only write comments when you fail to express yourself with code because they might get outdated and out of sync. While you should aim to express your reasoning and thoughts with code using proper naming for variables, structs, interfaces, and functions, don’t underestimate the power of comments! I used to underestimate comments subconsciously following this mindset. Thankfully, after a couple of years working with Go, I learned to value the power of good comments. If you have doubts about what is reasonable or not to express with comments, I suggest reading the standard library’s source code and seeing how they do it. The [Go Code Review Comments section on comments](https://github.com/golang/go/wiki/CodeReviewComments#doc-comments) is also a useful reference.

Documentation is also a key point. You want to use [godoc](https://blog.golang.org/godoc) to generate documentation for your public API. All it takes is for you to follow some minimal and unobtrusive commenting patterns. It’s relatively straight-forward to use it, and you gain consistency following it even if it’s not your preferred style!

**Remember:** Code is written once but read multiple times. It’s better to spend a little more time writing code comments in a way that others and your future self will understand than to hurry and months or years later spend much more time trying to make sense of it.

## Creating too many packages

```
I didn't need to write 133 packages.
I didn't need to write 133 packages.
I didn't need to write 133 packages.
I didn't need to write 133 packages.
```

Shame on me for creating [a package for each of the 58 commands](https://github.com/henvic/wedeploycli/tree/master/command) I needed on a CLI tool! That is 58 directories with at least a file each. I could’ve used a single package with 10-15 medium-sized files. Its [command/list package](https://github.com/henvic/wedeploycli/tree/master/command/list) is one of the worst offenders:

```
./command/list
├── instances
│   └── instances.go (85 lines of code)
├── list.go (121 lines of code)
├── projects
│   └── projects.go (73 lines of code)
└── services
    └── services.go (109 lines of code)
Total: 388 lines of code
```

The following are indicators that maybe you’re breaking down your code too much:

-   Tiny packages or files with only dozens of lines of code.
-   Using custom identifiers when importing packages because multiple packages share the same name.

**What should I have instead?** A list.go file with fewer than 350 lines of code inside the command package would be better. For an excellent example of code organization, I recommend checking out the [net/http package](https://golang.org/src/net/http/) code. In a single package with a dozen or so files, you’ll find an implementation for Go’s HTTP client and server.

## Exporting names

In Go, [a name is exported](https://tour.golang.org/basics/3) if it begins with a capital letter. In other words, code that other packages should be able to address directly.

Take the following functions of the [fmt](https://golang.org/pkg/fmt/) package:

```
func Printf(format string, a ...interface{}) (n int, err error)
func Println(a ...interface{}) (n int, err error)
func newPrinter() *pp
```

Only the first two can be called outside the fmt package. If you try to call newPrinter externally, you’ll end up with a compile-time error:

```
./prog.go:8:2: cannot refer to unexported name fmt.newPrinter
./prog.go:8:2: undefined: fmt.newPrinter
```

As I’ve hinted in the previous section, if I had fewer packages, I would avoid needing to export many names, reducing the dependency graph a lot.

### Internal packages

Now, Go has another great feature to set boundaries on your code: [internal packages](https://golang.org/doc/go1.4#internalpackages).

`./a/b/c/internal/d/e/f` can only be imported by code within the `./a/b/c` package.

Use internal packages to protect all your code except what needs a public API. It’s useful to use this even on private projects not intended for public distribution. Set clear boundaries and expectations only exposing use-cases you intend to support. If your API has a small surface, you’ll be free to do internal changes without worrying about releasing a major version due to backward incompatibility and breaking code elsewhere.

If you’re worried about this idea because certainly your code might be useful throughout your team projects, it might be a good time to reflect on the following [Go proverb](https://go-proverbs.github.io/):

> A little copying is better than a little dependency. [Go Proverbs - Rob Pike - Gopherfest - November 18, 2015](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=9m28s)

You can even use [apidiff](https://golang.org/s/apidiff-readme), a tool to detect incompatible API changes, to check your API contracts. Watch the GopherCon 2019’s [Detecting Incompatible API Changes](https://www.youtube.com/watch?v=JhdL5AkH-AQ) talk by Jonathan Amsterdam ([transcript](https://about.sourcegraph.com/go/gophercon-2019-detecting-incompatible-api-changes/)).

## Globals and configuration

_If you haven’t read yet, see my previous blog post on [environment variables, config, secrets, and globals](https://henvic.dev/posts/env/)._

You want your code to look clean, but then configuration might get in the way. One possible quick solution is to use a global for passing it around, right? Sure! – If you don’t mind introducing race conditions or making parallel testing impossible. Things can get ugly fast, and the cost of refactoring only increases. Be careful because if you leave making things right for later, later might never come! You usually can pass your configuration explicitly when initializing objects, for example.

**What if you need to pass params between layers that don’t need to know about it?** It might be the case to use a [context](https://golang.org/pkg/context/).

```
// Params for the metrics system.
type Params struct {
// Hostname of your service.
Hostname string

// Verbose flag.
Verbose bool
// ...
}

// paramsContextKey is the key for the params context.
// Using struct{} here to guarantee there are no conflicts with keys defined outside of this package.
type paramsContextKey struct{}

// Context returns a copy of the parent context with the given params.
func (p *Params) Context(ctx context.Context) context.Context {
return context.WithValue(ctx, paramsContextKey{}, p)
}

// FromContext gets params from context.
func FromContext(ctx context.Context) (*Params, error) {
if p, ok := ctx.Value(paramsContextKey{}).(*Params); ok {
return p, nil
}
return nil, errors.New("metrics system params not found")
}
```

See another [example](https://play.golang.org/p/paDWRN_K5LZ) in the Go Playground. **Tread light, in any case!** Don’t use a context for passing configuration that can be passed directly. Only use context for this if you **need** to pass something simple transparently through a layer. **Think about a better solution before doing this!**

## Imports and build size

Transforming human-readable source code to a set of instructions for machines involves a brutal amount of work. Now, there are many strategies to deal with this. Some languages (i.e., JavaScript, Python, Tcl) are interpreted, meaning that the code gets translated into machine code during execution by an interpreter (such as your browser or a runtime). Go is a compiled language, meaning the code gets translated beforehand. The main advantage of a compiled language is the speed of execution. Things like [Just-in-time compilation](https://en.wikipedia.org/wiki/Just-in-time_compilation) combine together concepts of interpretation and compilation, but this is off-topic. Whenever you run `go build`, it creates a machine-friendly file containing your whole application and its dependencies after parsing your code, compiling it into machine-code, and linking its parts.

This build process can easily take as input a couple of text files containing only a few Kilobytes and generate a binary file of Megabytes after converting your code to machine-friendly format and linking dependencies. Even though Go is very efficient and minimal, no Gopher magic can make this cost disappear.

In my case, I was working on [a CLI tool](https://henvic.dev/portfolio/#wedeploy) that had a `deploy` command that invoked `git` quite a few times behind the scenes. We were using git as both a transport layer and a smart cache layer. The downside was that our tool now required a system-wide dependency. Several git bugs later, I decided to try out a git implementation written in Go – [go-git](https://github.com/go-git/go-git) – as a replacement. I added a new `--experimental` flag and continued to move towards a pure Go library incrementally. However, I forgot to measure what was the impact of adding this second implementation. It doubled the compressed file size from slightly over 4 to 9 Megabytes. It was a substantial increase in file size, and although not critical, I regret not spotting this. Had I noticed, I’d hide this alternative implementation using build tags until it was ready for A/B testing.

## Concurrency and streams

I didn’t learn about concurrency with Go, but I committed the most rookie mistake possible quite a few times: writing from multiple goroutines or Threads will cause text to be all mingled.

I made this error even more so when writing packages for text animation in the terminal. If you find yourself with this issue, you can probably use a mutex to set what goroutine can write at the moment, or, in more complicated cases, use channels to print from a single goroutine. Also, be aware that if the output’s order is important, you might want to sync whether you’re printing to standard error (`os.Stderr`) or standard output (`os.Stdout`).

> Tip: Go has a fantastic data race detector. You can build your test or application with it by passing the `-race` flag to your `go test` or `go build` commands, respectively.

### Sockets and WebSocket

Something fun I solved was when implementing a “SSH over WebSocket” feature. We used the socket.io protocol on our backend systems already. For the sake of simplicity, we wanted to use that for this protocol. I forked and heavily modified an existing Go socket.io library for that. It required arduous work understanding how the protocol functioned to make it possible to do what we needed. I even had to reverse-engineer the protocol because there isn’t a formal socket.io specification!

When it finally appeared to be working as expected, I sent a file to the server and ran a simple test from the connection: `$ cat hamlet.txt`, and compared the output. To my surprise, some phrases showed up out of order. The error was that the library created a new goroutine whenever it received a message.

The fix was trivial: remove the go keyword from inside this routine loop to call the handler on the same routine. **You usually want to try to postpone the creation of goroutines until the last moment.** The idea of creating one right away was probably thinking about performance. For me, this is a typical case where good documentation with examples can do wonders in explaining to the user what they need to know. Alternatively, there could be different ways to define blocking and non-blocking handlers!

Thank you for reading.

If you click and buy any of these from Amazon after visiting the links above, I might get a commission from their [Affiliate program](https://affiliate-program.amazon.com/).

> My Go mistakes[https://t.co/hHSIZ3KxZs](https://t.co/hHSIZ3KxZs)
> 
> — Henrique Vicente (@henriquev) [February 18, 2021](https://twitter.com/henriquev/status/1362206448520945664?ref_src=twsrc%5Etfw)