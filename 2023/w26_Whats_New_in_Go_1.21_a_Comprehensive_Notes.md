# What’s New in Go 1.21 a Comprehensive Notes

- 原文地址：https://younisjad.medium.com/whats-new-in-go-1-21-a-comprehensive-notes-96017750b390
- 原文作者：Younis Jad
- 本文永久链接：
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[]()
***

![Go 1.21 Exciting Updates and Enhancements: A Comprehensive Overview](https://github.com/gocn/translator/raw/master/static/images/2023/w26/1*OWUGPbMTINTQEZmSi3n-hQ.png)


The Go programming language has released its first Release Candidate (RC) for version 1.21, which is packed with new features, improvements, and performance enhancements. This article provides an overview of the notable changes and features in Go 1.21, along with some exciting additions to the standard library.

## Tool Improvements:

## The Profile Guided Optimization (PGO) feature

In Go 1.21, the process of enabling PGO optimization has been streamlined. By default, the standard approach is to store a pprof CPU profile with the filename “default.pgo” in the main package directory of the profiled binary. This profile is automatically detected by the go build command, enabling PGO optimizations during the build.

```
# Store default.pgo profile in the main package directory
$ go build
# Assuming default.pgo exists, PGO optimizations will be applied during the build process
```

**Committing Profiles in Source Repository**

To ensure reproducible and performant builds, it is recommended to commit the profiles directly into the source repository. This approach simplifies the build experience as there are no additional steps required to fetch the profiles other than fetching the source code.

```
# Committing default.pgo profile in the source repository
├── main.go
└── default.pgo
# Developers can directly build the code with the committed profile

$ go build
```

**Advanced PGO Profile Selection**

In more complex scenarios, the go build command provides the `-pgo` flag to control the PGO profile selection. By default, this flag is set to -`pgo=auto,` which follows the behavior described above using the `default.pgo` profile.

```
# Using -pgo flag to manually specify the profile for optimization
$ go build -pgo=/tmp/foo.pprof
```

**Disabling PGO Optimization**

In cases where PGO optimizations are not desired, the `-pgo` flag can be set to `-pgo=off` to disable them entirely.

```
# Disabling PGO optimizations using the -pgo flag
$ go build -pgo=off
```

These examples demonstrate the usage of the go build command for simplicity. The same principles apply to other build commands such as go install and go run.

> Note: Starting from Go 1.21, PGO optimizations are enabled by default. Prior to Go 1.21, PGO had to be explicitly enabled using the -pgo flag.

## Backward and Forward Language Compatibility

Go 1.21 introduces backward and forward language compatibility support in the go tool, making it easier for developers to ensure their code remains compatible with different language versions.

Example: Testing package with //go:debug directive in \*\_test.go file

```
package mypackage_test
```

```go
//go:debug mysetting=1
import (    
		"testing"    
		"mypackage"
)
func TestMyFunction(t *testing.T) 
{    
		// Test code    
		result := mypackage.MyFunction()    
		// Assertion code
}
```

In this example, the `//go:debug mysetting=1` directive is included in the `*_test.go` file of the package being tested. This directive serves as a directive for the test’s main package and can override the default behavior for specific debug settings during testing. This allows different test scenarios to be executed by enabling specific debug settings.

**Reporting default GODEBUG settings for a main package**

```
go list -f '{{.DefaultGODEBUG}}' my/main/package
```

When executing this command, where my/main/package is the path to the main package, the Go toolchain will report the default GODEBUG settings that will be compiled into the main package. This command is useful to see the differences from the base Go toolchain defaults.

## Language Changes:

## New Built-in Functions: min, max, and clear

Go 1.21 introduces three new built-in functions, namely min, max, and clear, which provide convenient options for performing basic operations on numeric data.

**Min, Max Functions**

The min and max functions are built-in functions in Go that calculate the smallest or largest value, respectively, among a fixed number of arguments of ordered types. These functions require at least one argument to be passed.

The same type rules that apply to operators also apply to these functions. For ordered arguments x and y, calling min(x, y) is valid if the addition x + y is valid. The type of the result returned by min(x, y) is the same as the type of x + y, and the same applies to the max function. If all the arguments passed to these functions are constant, the result returned by these functions is also constant.

```go
	var x, y int
	m := min(x)                 // m == x
	m := min(x, y)              // m is the smaller of x and y
	m := max(x, y, 10)          // m is the larger of x and y but at least 10
	c := max(1, 2.0, 10)        // c == 10.0 (floating-point kind)
	f := max(0, float32(x))     // type of f is float32
	var s []string
	_ = min(s...)               // invalid: slice arguments are not permitted
	t := max("", "foo", "bar")  // t == "foo" (string kind)

```

**Clear Function**

The clear function is a built-in function that takes an argument of type map, slice, or type parameter type. It is used to delete or zero out all the elements within the provided data structure.

```
var a = [...]int{0, 1, 2, 3, 4, 5, 6, 7}
```

```go
package main
import (
 "fmt"
 "math"
)
func main() {
 	a := map[float64]bool{100: true, 1000: true, math.NaN(): true, math.NaN(): true}
 	delete(a, math.NaN())
 	fmt.Printf("before clear, a len: %d\n", len(a))
 	clear(a)
 	fmt.Printf("after clear, a len: %d\n", len(a))
}
```

## Improved Type Inference for Generic Functions

The type inference system for generic functions has received several improvements in Go 1.21. The Go specification now includes an expanded and clarified description of type inference, making it easier for developers to understand and utilize this powerful feature.

```
// Improved type inference for generic functions
```

```go
func genericFunc[T any](x T) {
    // Function implementation
}
value := 42
genericFunc(value) // Type inference automatically detects the type of value
```

## Preview of Loop Variable Capture Improvement

Go 1.21 introduces a preview feature aimed at addressing the common challenge of loop variable capture in Go programming. Developers can enable this feature in their code using an environment variable.

```go
var out []*int
for i := 0; i < 3; i++ {
	out = append(out, &i)
}
fmt.Println("Values:", *out[0], *out[1], *out[2])
fmt.Println("Addresses:", out[0], out[1], out[2])
```

`goroutine` Example that prints `1…10`

```go
for i := 1; i <= 10; i++ {
 go func() {
  fmt.Println(i)
 }()
}
```

## New Introduced Packages:

-   New [log/slog Package](https://pkg.go.dev/log/slog@master) for Structured Logging
-   New [slices Package](https://pkg.go.dev/slices@master) for Common Operations on Slices
-   New [maps Package](https://pkg.go.dev/maps@master) for Common Operations on Maps
-   New [cmp Package](https://pkg.go.dev/cmp@master) for Comparing Ordered Values

## Improved Performance:

Improved Performance with PGO:In addition to the performance improvements from enabling PGO, Go 1.21 brings additional enhancements to overall performance.

## New Experimental Port for WebAssembly System Interface (WASI):

Go 1.21 introduces an experimental port for the WebAssembly System Interface (WASI) — Preview 1, allowing developers to compile their Go code for the WebAssembly platform.

## Conclusion

Go 1.21 offers enhancements in tooling, language features, standard library additions, and performance optimizations make Go an even more robust and efficient programming language for various use cases. With the availability of the Release Candidate, developers are encouraged to experiment, test, and provide feedback to help shape the final release slated for August 2023.

source: [https://go.dev/blog/go1.21rc#:~:text=Go%201.21%20adds%20an%20experimental,WASM%20host%3A%20go%3Awasmimport%20.](https://go.dev/blog/go1.21rc#:~:text=Go%201.21%20adds%20an%20experimental,WASM%20host%3A%20go%3Awasmimport%20.)

Reference:

-   [https://go.dev/blog/go1.21rc#:~:text=Go%201.21%20adds%20an%20experimental,WASM%20host%3A%20go%3Awasmimport%20.](https://go.dev/blog/go1.21rc#:~:text=Go%201.21%20adds%20an%20experimental,WASM%20host%3A%20go%3Awasmimport%20.)
-   [https://go.dev/doc/pgo#:~:text=Profile%2Dguided%20optimization%20(PGO)%2C%20also%20known%20as%20feedback,information%20to%20make%20more%20informed](https://go.dev/doc/pgo#:~:text=Profile%2Dguided%20optimization%20(PGO)%2C%20also%20known%20as%20feedback,information%20to%20make%20more%20informed)
-   [https://tip.golang.org/doc/godebug](https://tip.golang.org/doc/godebug)
-   [https://tip.golang.org/ref/spec#Min\_and\_max](https://tip.golang.org/ref/spec#Min_and_max)
-   [https://github.com/golang/go/wiki/CommonMistakes](https://github.com/golang/go/wiki/CommonMistakes)
