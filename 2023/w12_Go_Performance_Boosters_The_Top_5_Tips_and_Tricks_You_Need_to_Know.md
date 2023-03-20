# Go Performance Boosters: The Top 5 Tips and Tricks You Need to Know

- 原文地址：<https://medium.com/@func25/go-performance-boosters-the-top-5-tips-and-tricks-you-need-to-know-e5cf6e5bc683>
- 原文作者：Go Performance Boosters: The Top 5 Tips and Tricks You Need to Know
- 本文永久链接：<https://github.com/gocn/translator/blob/master/2023/w12_Go_Performance_Boosters_The_Top_5_Tips_and_Tricks_You_Need_to_Know.md>
- 译者：[小超人](https://github.com/focozz)
- 校对：[]()

>  How to turn your slow and clunky Go applications into lean, mean, code-crunching machines with these top 5 tips and tricks for optimizing your Go code

![](../static/images/2023/w12_Go_Performance_Boosters_The_Top_5_Tips_and_Tricks_You_Need_to_Know/1_7pKdwB_c5boKS_235L9DRQ.png)

Go Performance Boosters: The Top 5 Tips and Tricks You Need to Know

Attention Go gurus and beginners alike! Are you tired of slow, clunky Go applications that make you want to pull your hair out? Well, fear not, because we’ve got the solution.

In this post, I’m sharing the top 5 tips and tricks for optimizing your Go applications and turning them into lean, mean, code-crunching machines.

So grab a cup of coffee, sit back, and get ready to take your Go skills to the next level.

## 1. Avoid reflection

Reflection is a powerful feature of Go that allows a program to introspect and modify its own structure and behavior at runtime.

You can use reflection to determine the type of a value, access its fields, and call its methods.

``` go

package main

import (
	"fmt"
	"reflect"
)

func main() {
	x := 100
	v := reflect.ValueOf(x)
	t := v.Type()
	fmt.Println("Type:", t)
}

```

**But!**

When using reflection, it involves introspection and manipulation of values at runtime, rather than at compile time.

The Go runtime must perform additional work to determine the type and structure of the reflected value, which can add overhead and slow down the program.

Reflection can also make code more difficult to read and understand, which can impact productivity.

## 2. Avoid string concatenation

It is generally more efficient to use the `bytes.Buffer` type to build strings rather than concatenating strings using the `+` operator.

Look at this poor performance code:

``` go

s := ""
for i := 0; i < 100000; i++ {
	s += "x"
}
fmt.Println(s)

```

This code will create a new string on each iteration of the loop, which can be inefficient and may lead to poor performance.

Instead, you can use the `bytes.Buffer` to build the string more efficiently:

``` go

var buffer bytes.Buffer
for i := 0; i < 100000; i++ {
	buffer.WriteString("x")
}
s := buffer.String()
fmt.Println(s)

```

Thanks to

suggestion, here is **another solution**: using `strings.Builder`. Its usage is similar to `bytes.Buffer`, but it provides even better performance:

``` go

var builder strings.Builder

for i := 0; i < 100000; i++ {
	builder.WriteString("x")
}
s := builder.String()
fmt.Println(s)

```

> “Where is the benchmark (or something)?”

I have compared these 2 solutions and the result is…

-   Using `bytes.Buffer` is significantly faster than using string concatenation, with a performance boost of **over 250x** in some cases.
-   Using `strings.Builder` is approximately 1.5 times faster than `bytes.Buffer`

It is important to note that the exact performance boost may vary depending on factors such as the specific CPU and running context of the code

> Why strings.Builder is faster than `bytes.Buffer`?

This is because `strings.Builder` is specifically optimized for building strings. By contrast, `bytes.Buffer` is a more general-purpose buffer that can be used to build any type of data, but it may not be as optimized for building strings as `strings.Builder`

## 3. Pre-Allocating for slice, map

Allocating a slice with a capacity that is suitable for the number of elements it is expected to hold can improve performance in Go.

This is because allocating a slice with a larger capacity can reduce the number of times that the slice needs to be resized as elements are added.

Here is the benchmark:

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

Yes, we were able to boost the speed X3 FASTER with pre-allocation.

If you want to understand [why pre-allocation is faster](https://medium.com/@func25/go-secret-slice-a-deep-dive-into-slice-6bd7b0b70ec4), I have written a detailed explanation in a post about slices

## 4. Avoid using interfaces with a single concrete type

If you know that an interface will only ever have a single concrete type, you can use the concrete type directly to avoid the overhead of the interface.

Using the concrete type directly can be more efficient than using the interface because it avoids the overhead of storing the type and value in the interface.

Here is an example compares the performance of using an interface versus using a concrete type directly in Go:

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

Using interface costs **358μs**, concrete type costs **342μs.**

It’s important to note that this technique should only be used when you are certain that an interface will only ever have a single concrete type.

## 5. Using go vet

The `govet` tool is a static analysis tool without running code that can help you find potential issues in your Go code.

`govet` checks your code for all sorts of problems that could cause bugs or lead to poor performance. It's like a code quality police, constantly checking to make sure you're not doing anything stupid.

To use `govet`, you can run the `go tool vet` command and pass the names of the Go source files you want to check as arguments:

```go

go tool vet main.go

```

You can also pass the `-all` flag to `go tool vet` to check all the Go source files in the current directory and its subdirectories:

``` go

go tool vet -all

```

> The govet is too noisy. Some problems don’t need to be reported.

You can customize the behavior of `govet` by writing "vet comments" in your code. Vet comments are special comments that tell `govet` to ignore certain issues or to check for additional issues

Here is an example of a vet comment that tells `govet` to ignore an unused variable:

``` go

func main() {
	var x int  _ = x
}

```

## Ending on a High Note

Remember to keep an eye on memory allocation, interface, pre-allocating,… And if you want to take your Go code to the next level, there are plenty of other tips and tricks out there to explore.

Just remember to always keep learning and have fun with it, **happy coding**!
