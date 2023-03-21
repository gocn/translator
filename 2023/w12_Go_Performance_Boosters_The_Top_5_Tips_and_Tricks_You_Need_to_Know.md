# Go性能加速器：你需要知道的5个诀窍和技巧

- 原文地址：<https://medium.com/@func25/go-performance-boosters-the-top-5-tips-and-tricks-you-need-to-know-e5cf6e5bc683>
- 原文作者：Aiden (@func25)
- 本文永久链接：<https://github.com/gocn/translator/blob/master/2023/w12_Go_Performance_Boosters_The_Top_5_Tips_and_Tricks_You_Need_to_Know.md>
- 译者：[小超人](https://github.com/focozz)
- 校对：[]()

> 通过这 5个诀窍和技巧来将那些运行缓慢，低效的 go 代码变成精简，高效，快速的机器代码。

![Go性能加速器：你需要知道的5个诀窍和技巧](../static/images/2023/w12_Go_Performance_Boosters_The_Top_5_Tips_and_Tricks_You_Need_to_Know/1_7pKdwB_c5boKS_235L9DRQ.png)

Go性能加速器：你需要知道的5个诀窍和技巧
各位 Go 大师和初学者们，你们是否已经厌倦了那些慢得让你想要抓狂的 Go 应用程序？别担心，我们有解决方案。
在这篇文章中，我将分享将 Go 应用程序变成精简、高效的前5个诀窍和技巧。
所以拿杯咖啡，放松一下，准备把你的 Go 技能提升到更高的水平。

## 1. 避免使用反射。

反射是 Go 中一个强大的特性，它允许程序在运行时自我检查和修改自身的结构和行为。
你可以使用反射来确定一个值的类型，访问其字段，并调用其方法。

``` go

package main

import (
	"fmt"
	"reflect"
)
// 通过反射来获取 x 的类型
func main() {
	x := 100
	v := reflect.ValueOf(x)
	t := v.Type()
	fmt.Println("Type:", t)
}

```

**但是！** 反射是在运行时进行值的自我检查和操作，而不是编译时。
Go运行时必须执行额外的工作来确定反射值的类型和结构，这可能会增加开销并减慢程序速度。
反射还会使代码更难以阅读和理解而使影响生产力受到影响。

## 2. 避免使用字符串拼接。

通常使用 `bytes.Buffer` 类型来构建字符串比使用 `+` 操作符连接字符串更有效率。

看看这个性能较差的代码：


``` go

s := ""
for i := 0; i < 100000; i++ {
	s += "x"
}
fmt.Println(s)

```

这段代码每次循环都会创建一个新的字符串，这会使效率低下且导致性能变差。

相反地，你可以使用 `bytes.Buffer` 更高效地构建字符串：

``` go
// 使用 bytes.Buffer 来构建字符串
var buffer bytes.Buffer
for i := 0; i < 100000; i++ {
	buffer.WriteString("x")
}
s := buffer.String()
fmt.Println(s)

```

另一个解决方案是使用 `strings.Builder`。它的用法类似于 `bytes.Buffer`，但提供更好的性能：

``` go

// 使用 strings.Builder 来构建字符串
var builder strings.Builder

for i := 0; i < 100000; i++ {
	builder.WriteString("x")
}
s := builder.String()
fmt.Println(s)

```

> 以下是基础测试

我已经比较了这两种解决方案，结果如下:

- 使用 `bytes.Buffer` 比使用字符串拼接快得多，在某些情况下性能提升超过 250 倍。
- 使用 `strings.Builder` 大约比 `bytes.Buffer` 快1.5倍。

需要注意的是，实际的性能提升可能因为特定的 CPU 和代码运行环境等因素而有所差异。

> strings.Builder比bytes.Buffer更快的原因有几个。


这是因为 `strings.Builder` 专门针对字符串的构建进行了优化。相比之下，`bytes.Buffer` 是一个更通用的缓冲区，可以用于构建任何类型的数据，但它可能没有像 `strings.Builder` 那样专门优化字符串构建的性能。

## 3. 预分配切片和 map 的空间。


在Go中，为预期容纳的元素数量适当分配切片的容量可以提高性能。

这是因为分配具有更大容量的切片可以减少在添加元素时需要调整切片大小的次数。

下面是压力测试:

``` go

func main() {
	start := time.Now()
	s := make([]int, 0, 10)
	for i := 0; i < 100000; i++ {
		s = append(s, i)
	}
	elapsed := time.Since(start)
	fmt.Printf("Allocating slice with small capacity: %v\n", elapsed)
	start = time.Now()
	s = make([]int, 0, 100000)
	for i := 0; i < 100000; i++ {
		s = append(s, i)
	}
	elapsed = time.Since(start)
	fmt.Printf("Allocating slice with larger capacity: %v\n", elapsed)
}

```

是的，通过预分配，我们能够将速度提升3倍。

我已经在一篇关于切片的文章中对于[为什么预分配更快](https://medium.com/@func25/go-secret-slice-a-deep-dive-into-slice-6bd7b0b70ec4)写了一个详细的解释，你可以直接点击链接查看。

## 4. 避免使用只有一个具体类型的接口。

如果你知道一个接口只会有一个具体类型，你可以直接使用该具体类型，以避免接口的开销。

直接使用具体类型可以比使用接口更高效，因为它避免了在接口中存储类型和值的开销。

这里有一个例子，比较了在 Go 中使用接口和直接使用具体类型的性能：

``` go

func main() {
	start := time.Now()
	var s Shape = &Circle{radius: 10}
	for i := 0; i < 100000; i++ {
		s.Area()
	}
	elapsed := time.Since(start)
	fmt.Printf("Using Shape interface: %s\n", elapsed)
	start = time.Now()
	c := Circle{radius: 10}
	for i := 0; i < 100000; i++ {
		c.Area()
	}
	elapsed = time.Since(start)
	fmt.Printf("Using Circle type directly: %s\n", elapsed)
}

```

使用接口的耗时为358微秒，而使用具体类型的耗时为342微秒。

需要注意的是，只有当你确信一个接口只会有一个具体类型时，才应该使用这种技术。

## 5. Using go vet
## 5. 使用 go vet


govet 工具是一种静态分析工具，它可以在不运行代码的情况下帮助你找到 Go 代码中可能存在的问题。

`govet` 检查您的代码以查找可能导致错误或性能问题的各种问题。它就像是一个代码质量警察，不断检查以确保你没有犯任何低级错误。

要使用 `govet`，可以运行 `go tool vet` 命令，并将要检查的 Go 源文件的名称作为参数传递:

```go

go tool vet main.go

```

你也可以在 `go tool vet` 命令中加入 `-all` 标志，以检查当前目录及其子目录中的所有 Go 源文件：


``` go

go tool vet -all

```

> govet 可能会不断地报告不需要报告的问题。

你可以通过在代码中编写 "vet comments" 来自定义 `govet` 的行为。Vet 注释是特殊的注释，告诉 `govet` 忽略某些问题或检查其他问题。

以下是一个 vet 注释的例子，告诉 `govet` 忽略未使用的变量：

``` go

func main() {
 var x int
 //go:noinline
 _ = x
}

```

## 总结

记得要密切关注内存分配、接口、预分配等问题。如果你想将你的 Go 代码提升到更高的水平，还有很多其他的技巧和窍门可以探索。

只要保持学习的态度，并享受编程的乐趣，就可以了！祝编程愉快！
