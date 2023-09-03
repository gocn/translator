# Go 1.21 中新增功能的全面概述

- 原文地址：https://younisjad.medium.com/whats-new-in-go-1-21-a-comprehensive-notes-96017750b390
- 原文作者：Younis Jad
- 本文永久链接：https://github.com/gocn/translator/blob/master/2023/w26_Whats_New_in_Go_1.21_a_Comprehensive_Notes.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[zxmfke](https://github.com/zxmfke)
***

![Go 1.21 Exciting Updates and Enhancements: A Comprehensive Overview](https://github.com/gocn/translator/raw/master/static/images/2023/w26/1_OWUGPbMTINTQEZmSi3n-hQ.png)


Go 语言发布了 1.21 版本的第一个候选版本 (RC)，其中包含新的功能、改进和性能提升。本文概述了 Go 1.21 中的显著变化和功能，以及标准库中的一些令人兴奋的新增内容。

## 工具改进：

## 配置文件引导优化 (PGO) 功能

在 Go 1.21 中，启用 PGO 优化的过程已得到简化。默认情况下，标准方法是将文件名“default.pgo”的 pprof CPU 配置文件存储在分析二进制文件的主包目录中。go build 命令会自动检测此配置文件，从而在构建过程中启用 PGO 优化。

```
# 将 default.pgo 配置文件存储在主包目录中
$ go build
# 如果存在 default.pgo，在构建过程中将会应用 PGO 优化
```

**在源代码仓库中提交配置文件**

为了确保可重复且高性能的构建，建议将配置文件直接提交到源代码仓库中。这种方法简化了构建方式，因为除了获取源代码之外，不需要任何额外的步骤来获取配置文件。

```
# 提交 default.pgo 配置文件到源代码仓库中
├── main.go
└── default.pgo
# 开发者可以直接使用提交的配置文件构建代码
$ go build
```

**PGO 配置文件的选择**

在更复杂的场景中，`go build` 命令也提供了 `-pgo` 标识来控制 PGO 配置文件的选择。此标志默认为 `-pgo=auto`，将会使用 `default.pgo` 文件。

```
# 使用 -pgo 标志手动指定配置文件
$ go build -pgo=/tmp/foo.pprof
```

**禁用 PGO 优化**

如果不需要 PGO 优化，可以将 `-pgo` 标志设置为 `-pgo=off` 来完全禁用它们。

```
# 使用 -pgo 标志禁用 PGO 优化
$ go build -pgo=off
```

这些示例简单演示了 go build 命令的用法，相同的原则也适用于其他构建命令，例如 go install 和 go run。

> 注意：从 Go 1.21 开始，默认启用 PGO 优化。在 Go 1.21 之前，必须使用 -pgo 标志显式启用 PGO。

## 向后和向前语言兼容性

Go 1.21 在 go 工具中引入了向后和向前的语言兼容性支持，使开发人员更容易确保他们的代码与不同语言版本保持兼容。

示例：在 *_test.go 文件中使用 //go:debug 指令

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
		// 测试代码   
		result := mypackage.MyFunction()    
		// 断言代码
}
```

在此示例中，`//go:debug mysetting=1` 指令包含在测试包的 *_test.go 文件中。该指令用于测试 main 包，并且可以覆盖测试期间特定调试设置的默认行为。这允许通过启用特定的调试设置来执行不同的测试场景。

**列出 main 包的默认 GODEBUG 设置**

```
go list -f '{{.DefaultGODEBUG}}' my/main/package
```

执行此命令时，其中 my/main/package 是主包的路径，Go 工具链将列出会编译到主包的默认 GODEBUG 设置。此命令对于查看当前设置与基本 Go 工具链默认值的差异时非常有用。

## 语言变化：

## 新的内置函数：min、max 和 clear

Go 1.21 引入了三个新的内置函数: min、max 和 clear，它们为对数值的操作提供了方便的选项。

**最小、最大值函数**

min 和 max 函数成为了 Go 中的内置函数，它们分别能够计算固定数量的有序类型数据的最小值或最大值。这些函数需要至少传递一个参数。

适用于运算符规则的数据类型也同样适用于这些函数。对于有序参数 x 和 y，如果加法 x + y 有效，则调用 min(x, y) 也是有效的。min(x, y) 返回结果的类型与 x + y 的类型相同，对于 max 函数也是如此。如果传递给这些函数的所有参数都是常量，那么这些函数返回的结果也是常量。

```go
	var x, y int
	m := min(x)                 // m == x
	m := min(x, y)              // m 是 x 和 y 的最小值
	m := max(x, y, 10)          // m 是 x 和 y 中较大的一个，但至少为 10
	c := max(1, 2.0, 10)        // c == 10.0 (浮点型)
	f := max(0, float32(x))     // f 为 float32 类型
	var s []string
	_ = min(s...)               // 无效：不允许使用切片参数
	t := max("", "foo", "bar")  // t == "foo" （字符串类型）

```

**清空函数**

clear 函数是一个内置函数，它接受类型为 map、slice 或类型参数。它用于删除或清空所提供的数据结构中的所有元素。

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

## 泛型函数的类型推断的改进

泛型函数的类型推断在 Go 1.21 中得到了多项改进。Go 说明中现在包含了对类型推断的扩充和清晰的描述，使开发人员更容易理解和利用这一强大的功能。

```
// 泛型函数的类型推断的改进
```

```go
func genericFunc[T any](x T) {
    // 函数实现
}
value := 42
genericFunc(value) // 类型推断自动检测值的类型
```

## 循环变量捕获改进的预览功能

Go 1.21 引入了预览功能，旨在解决 Go 编程中循环变量捕获的常见挑战。开发人员可以通过使用环境变量 `GOEXPERIMENT=loopwar` 启用此功能。

```go
var out []*int
for i := 0; i < 3; i++ {
	out = append(out, &i)
}
fmt.Println("Values:", *out[0], *out[1], *out[2])
fmt.Println("Addresses:", out[0], out[1], out[2])
```

`goroutine`  打印  `1…10` 的例子

```go
for i := 1; i <= 10; i++ {
 go func() {
  fmt.Println(i)
 }()
}
```

## 新引入的包

-   用于结构化日志记录的新 [log/slog包](https://pkg.go.dev/log/slog@master) 
-   用于切片常见操作的新 [slices包](https://pkg.go.dev/slices@master) 
-   字典常用操作的新 [map包](https://pkg.go.dev/maps@master) 
-   用于比较有序值的新 [cmp包](https://pkg.go.dev/cmp@master)


## 性能提升

使用 PGO 改进性能：除了启用 PGO 带来的性能改进之外，Go 1.21 还对整体性能带来了额外的增强。

## WebAssembly System Interface（WASI）的新实验端口：

Go 1.21 引入了 WebAssembly System Interface (WASI)  的实验性端口 - Preview 1，这将允许开发人员为 WebAssembly 平台编译 Go 代码。

## 总结

Go 1.21 在工具、语言功能、标准库添加和性能优化方面提供了增强，使 Go 成为适用于各种场景的更强大、更高效的编程语言。随着候选版本的推出，我们鼓励开发人员进行试验、测试并提供反馈，以帮助制定定于 2023 年 8 月发布的最终版本。

来源: [https://go.dev/blog/go1.21rc#:~:text=Go%201.21%20adds%20an%20experimental,WASM%20host%3A%20go%3Awasmimport%20.](https://go.dev/blog/go1.21rc#:~:text=Go%201.21%20adds%20an%20experimental,WASM%20host%3A%20go%3Awasmimport%20.)

参考:

-   [https://go.dev/blog/go1.21rc#:~:text=Go%201.21%20adds%20an%20experimental,WASM%20host%3A%20go%3Awasmimport%20.](https://go.dev/blog/go1.21rc#:~:text=Go%201.21%20adds%20an%20experimental,WASM%20host%3A%20go%3Awasmimport%20.)
-   [https://go.dev/doc/pgo#:~:text=Profile%2Dguided%20optimization%20(PGO)%2C%20also%20known%20as%20feedback,information%20to%20make%20more%20informed](https://go.dev/doc/pgo#:~:text=Profile%2Dguided%20optimization%20(PGO)%2C%20also%20known%20as%20feedback,information%20to%20make%20more%20informed)
-   [https://tip.golang.org/doc/godebug](https://tip.golang.org/doc/godebug)
-   [https://tip.golang.org/ref/spec#Min\_and\_max](https://tip.golang.org/ref/spec#Min_and_max)
-   [https://github.com/golang/go/wiki/CommonMistakes](https://github.com/golang/go/wiki/CommonMistakes)
