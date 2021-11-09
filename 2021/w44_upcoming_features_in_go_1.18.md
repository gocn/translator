# UPCOMING FEATURES IN GO 1.18
Go 1.18 will be a significant release of the programming language that will contain some major features that I’m excited about. The upcoming version is scheduled for early 2021. The first beta should be out in a month. Let’s take a look at some of the new features that will be available.

## GENERICS
The long-awaited generics support will land in Go 1.18. The lack of generics in Go was the biggest point of criticism of the developer community. It took some years from the design phase to the actual implementation that will land in Go 1.18.

The topic is too large to explain in detail in this blog post. There are already a lot of good blog posts about it. The following is my favorite that covers all relevant aspects of it: [https://bitfieldconsulting.com/golang/generics](https://bitfieldconsulting.com/golang/generics). If you want to play with Go generics, there’s a hosted Go Playground available [here](https://go2goplay.golang.org/).

## WORKSPACES
Workspaces enable developers to work on multiple modules at the same time much easier. Until Go 1.17, it’s only possible with the `go.mod` `replace` directive, which can be painful to use if you have many modules in development. What’s also a huge pain is the fact that every time you want to commit your code, you have to remove the `replace` lines to be able to use a stable/released version of a module.

With workspaces, these development situations get much simpler to handle. A new file named `go.work` can be added to the project that contains paths to local development versions of dependent modules. The `go.mod` remains untouched without the need to use the `replace` directive.
```go
go 1.17

directory (
    ./baz // contains foo.org/bar/baz
    ./tools // contains golang.org/x/tools
)

replace golang.org/x/net => example.com/fork/net v1.4.5
```

In usual project situations, it’s recommended to not commit the `go.work` file, as its main use case is local development.

If you want to build your project locally without the workspace feature, you can do so by providing the following command line flag:
```sh
go build -workfile=off
```
With running the `go build` command like this, you can be sure that your project builds without the local development versions of the dependent modules.

## OFFICIAL FUZZING SUPPORT
Official fuzzing support will also be available in Go 1.18. The fuzzing features will be considered experimental, and the API will not be covered by the Go 1 compatibility promise yet. It should serve as a proof-of-concept and the Go team asks for feedback from the community.

f you haven’t heard of fuzzing yet, the [blog post](https://go.dev/blog/fuzz-beta) of the beta announcement describes it very well:

***Fuzzing is a type of automated testing which continuously manipulates inputs to a program to find issues such as panics or bugs. These semi-random data mutations can discover new code coverage that existing unit tests may miss, and uncover edge case bugs which would otherwise go unnoticed. Since fuzzing can reach these edge cases, fuzz testing is particularly valuable for finding security exploits and vulnerabilities.***

You can read the design doc by Katie Hockman [here](https://go.googlesource.com/proposal/+/master/design/draft-fuzzing.md). There’s also [Go Time podcast episode](https://changelog.com/gotime/187) with Katie that covers this topic.

## NEW PACKAGE NET/NETIP
The new package `net/netip` adds a new IP address type, which has many advantages compared to the `net.IP` type. The TLDR version is: it’s small, comparable, and doesn’t allocate. There’s already a [detailed blog post](https://tailscale.com/blog/netaddr-new-ip-type-for-go/) from Brad Fitzpatrick about all the details. If you prefer video, there is also a section in the [talk of Brad at FOSDEM 2021](https://www.youtube.com/watch?v=csbE6G9lZ-U&t=1125s) starting at time 18:45.

## FASTER (?) GO FMT RUNS
The `go fmt` command runs formatting in parallel now. As described in the [Github issue](https://github.com/golang/go/issues/43566), formatting large codebases should be much faster - but I was wondering why I didn’t notice it in a first test on my machine. It got much worse.

I tested it on the [repository of CockroachDB](https://github.com/cockroachdb/cockroach) on my Macbook Pro 2019 (2,6 GHz 6-Core Intel Core i7, 16 GB 2667 MHz DDR4) with the following command:
```sh
time go test ./pkg/...
```
With Go 1.17 it took **56 seconds** to format all files. With the latest `gotip` version, it took **1 minute and 20 seconds**. I also had to increase the ulimit on my machine to prevent a crash. Let’s see how this feature evolves until the stable release.

## TRY OUT THE UPCOMING FEATURES
You can also play with the latest experimental Go version called `gotip` directly on your machine. When you’ve already installed a stable version of Go, you just have to run the following commands:
```sh
go install golang.org/dl/gotip@latest
gotip download
```
When the installation was successful, you can use the `gotip` command just like the usual `go` command with all subcommands.

This blog post does not cover all the new features that will be available in Go 1.18. If you want to read about all the bug fixes and features, you can see a list of Go 1.18 issues [here](https://dev.golang.org/release#Go1.18).