# 你想知道的 Go 泛型
- 原文地址：https://bitfieldconsulting.com/golang/generics
- 原文作者：John Arundel
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w13_Generics_in_Go.md
- 译者：[haoheipi](https://github.com/haoheipi)
- 校对：[](https://github.com/)

泛型现在进展如何？这个友好而实用的教程将解释泛型函数和类型是什么，为什么我们需要它们，它们在 Go 中如何工作，以及我们可以在哪里使用它们。这是非常简单有趣的，让我们开始吧！

> John Arundel 是一位 Go 语言的老师兼顾问，也是《For the Love of Go》一书的作者。这是一套关于现代软件工程在 Go 语言中实践的电子书，完全面向初学者。
![](../static/images/w13_Generics_in_Go/Covers.png)
《For the Love of Go》是一系列有趣并且容易理解的电子书，专门介绍软件工程在 Go 语言中的实践。

## 什么是泛型

大家都知道， Go 是一种 *强类型* 语言，这意味着程序中的每个变量和值都有特定的类型，如 `int` 或 `string` 。当我们编写函数时，我们需要在所谓的 *函数签名* 中指定它们的形参类型，像这样：

```go
func PrintString(s string) {
```

这里，形参 `s` 的类型是 `string` 。我们可以想象编写这个函数接受 `int` 、 `float64` 、任意结构类型等形参的版本。但是当需要处理的不仅仅是这些明确类型时，多少是不太方便的，尽管我们有时可以使用 *接口* 来解决这个问题（例如 [map[string]interface 教程](https://bitfieldconsulting.com/golang/map-string-interface) 中所描述），但这种方法也有很多局限性。

## Go 泛型函数

相反，现在我们可以声明一个 *泛型函数* `PrintAnything`，它接受一个表示任意类型的 `any` 参数（我们称它为 `T` ），并使用它做一些事情。

这是它看起来的样子：

```go
func PrintAnything[T any](thing T) {
```

很简单对吧？这里的 `any` 表示 `T` 可以是任何类型。

我们怎么样调用这个函数？这也同样很简单：

```go
PrintAnything("Hello!")
```

> 注意：我在这里描述的对 Go 泛型的支持还没有发布，但它 [正在实现中](https://github.com/golang/go/issues/43651) ，很快就会发布。现在你可以在 [支持泛型的 Go Playground](https://go2goplay.golang.org/) 中使用它，或者在你的项目中使用实验性的 [go2go 工具](https://go.googlesource.com/go/+/refs/heads/dev.go2go/README.go2go.md) 来尝试获得 Go 泛型支持。

## 约束

要实现 `PrintAnything` 函数其实非常容易，因为 `fmt` 库就可以打印任何东西。假设我们想实现我们自己版本的 `strings.Join` 函数，它接受一个 `T` 类型的切片，并返回一个将它们连接在一起的字符串。让我们来试一试：

```go
// 我有一种不好的预感
func Join[T any](things []T) (result string) {
    for _, v := range things {
        result += v.String()
    }
    return result
}
```

我们已经创建了一个泛型函数 `Join()` ，它接受一个任意类型 `T` 的切片参数。很好，但是现在我们遇到了一个问题：

```go
output := Join([]string{"a", "b", "c"})
// v.String 没有被定义（绑定的类型 T 没有 String 方法）
```

也就是说在 `Join()` 函数中，我们想对每个切片元素 `v` 调用 `.String()` 方法 ，将其转换为 `string` 。但是 Go 需要能够提前检查 `T` 类型是否有 `String()` 方法，然而它并不知道 `T` 是什么，所以它不能直接调用！

我们需要做的是稍微地约束下 `T` 类型。实际上我们只对具有 `String()` 方法的类型感兴趣，而不是直接接受任何类型的 `T` 。任何具有这种方法的类型才能作为 `Join()` 函数的输入，那么我们如何用 Go 表达这个约束呢？我们可以使用一个 *接口* ：

```go
type Stringer interface {
    String() string
}
```

当给定类型实现了 `String()` 方法，现在我们就可以把这个约束应用到泛型函数的类型上：

```go
func Join[T Stringer] ...
```

因为 `Stringer` 保证了任何类型 `T` 的值都有 `String()` 方法，Go 现在很乐意让我们在函数内部调用它。但是，如果你尝试使用某个未实现 `Stringer` 类型的切片（例如 `int` ）来调用 `Join()` 方法时 ，Go 将会抱怨：

```go
result := Join([]int{1, 2, 3})
// int 未实现 Stringer 接口（未找到 String 方法）
```

## 可比较的约束

基于方法集的约束（如 `Stringer` ）是有用的，但如果我们想对我们的泛型输入做一些不涉及方法调用的事情呢？

例如，假设我们想编写一个 `Equal` 函数，它接受两个 `T` 类型的形参，如果它们相等则返回 `true` ，否则返回 `false` 。让我们试一试：

```go
// 这将不会有效
func Equal[T any](a, b T) bool {
    return a == b
}

fmt.Println(Equal(1, 1))
// 不能比较 a == b （类型 T 没有定义操作符 == ）
```

这与在 `Join()` 中使用 `String()` 方法遇到的问题相同，但由于我们现在没有直接调用方法，所以不能使用基于方法集的约束。相反，我们需要将 `T` 约束为可使用 `==` 或 `!=` 操作符，这被称为 *可比较* 类型。幸运的是，有一种直接的方式来指定这种类型：使用内置的 `comparable` 约束，而不是  `any` 。

```go
func Equal[T comparable] ...
```

## constraints 包

增加点难度，假设我们想用 `T` 的值做一些事情，既不比较它们也不调用它们的方法。例如，假设我们想为泛型 `T` 类型编写一个 `Max()` 函数，它接受 `T` 的一个切片，并返回切片元素中的最大值。我们可以尝试这样做：

```go
// Nope.
func Max[T any](input []T) (max T) {
    for _, v := range input {
        if v > max {
            max = v
        }
    }
    return max
}
```

我对此不太乐观，但让我们看看会发生什么：

```go
fmt.Println(Max([]int{1, 2, 3}))
// 不能比较 v > max （ T 类型没有定义操作符 > ）
```

同样，Go 不能提前验证 `T` 类型可以使用 `>` 操作符（也就是说，`T` 是 *有序的* ）。我们如何解决这个问题？我们可以简单地在约束中列出所有可能允许的类型，像这样（称为 *列表类型* ）：

```go
type Ordered interface {
    type int, int8, int16, int32, int64,
        uint, uint8, uint16, uint32, uint64, uintptr,
        float32, float64,
        string
}
```

幸运的是，在标准库的 `constraints` 包中已经为我们定义了一些实用的约束条件，所以我们只需要动动键盘就可以导入并像这样来使用：

```go
func Max[T constraints.Ordered] ...
```

问题解决了！

## 泛型类型

到目前为止，一切都很酷。我们知道如何编写可以接受任何类型参数的函数。但是如果我们想要创建一个可以包含任何类型的类型呢？例如，一个 “任意类型的切片” 。这其实也很简单：

```go
type Bunch[T any] []T
```

这里指对于任何给定的 `T` 类型 ， `Bunch[T]` 是 `T` 类型的切片。例如， `Bunch[int]` 是 `int` 的切片。我们可以用常规的方法来创建该类型的值：

```go
x := Bunch[int]{1, 2, 3}
```

正如你所期望的，我们可以编写接受泛型类型的泛型函数：

```go
func PrintBunch[T any](b Bunch[T]) {
```

方法也同样可以：

```go
func (b Bunch[T]) Print() {
```

我们也可以对泛型类型施加约束：

```go
type StringableBunch[T Stringer] []T
```

视频：[Code Club: Generics](https://youtu.be/x3KULj5406g?list=PLEcwzBXTPUE_YQR7R0BRtHBYJ0LN3Y0i3)

## 泛型 Golang playground

Go 团队提供了一个支持泛型的 Go Playground 版本，你可以在上面使用当前泛型提案的实现（例如尝试本教程中的代码示例）。

[泛型 Golang Playground](https://go2goplay.golang.org/)

它的工作方式与我们所了解和喜爱的普通 [Go Playground](https://play.golang.org/) 完全相同，只是它支持本文描述的泛型语法。由于在 Playground 中不可能运行所有的 Go 代码（例如网络调用或者访问文件系统的代码），你可以尝试使用 [go2go 工具](https://go.googlesource.com/go/+/refs/heads/dev.go2go/README.go2go.md)，它可以将使用泛型的代码翻译成当前 Go 版本能编译的代码。

## Q&A

### Go 泛型提案是什么

你可以在这里阅读完整的设计文档草稿：

- [类型参数 - 设计草稿](https://go.googlesource.com/proposal/+/master/design/go2draft-type-parameters.md)

### Golang 会支持泛型吗

是的。正如本教程的概述，在 Go 中目前对于支持泛型的提案已经在 2020 年 6 月一篇博客文章： [泛型的下一阶段](https://blog.golang.org/generics-next-step) 中宣布了。并且这篇 [Github issue](https://github.com/golang/go/issues/43651) （关于新增上文所描述形式的泛型）也已经被接受了。

[Go 博客](https://blog.golang.org/generics-proposal) 表示，在 Go 1.18 的测试版本可能会包含对泛型的支持，该测试版本将于 2021 年 12 月发布。

在此之前，你可以使用 [泛型 Playground](https://go2goplay.golang.org/) 来试验它，并尝试运行此文的示例。

### 泛型 vs 接口：这是泛型的另一种选择吗

正如我在 [map[string]interface 教程](https://bitfieldconsulting.com/golang/map-string-interface) 中提到的，我们可以通过 *接口* 来编写 Go 代码处理任何类型的值，而不需要使用泛型函数或类型。但是，如果你想编写实现任意类型的集合之类的库，那么使用泛型类型要比使用接口简单得多，也方便得多。

### any 因何而来

当定义泛型函数或类型时，输入类型必须有一个约束。类型约束可以是接口（如 `Stringer` ）、列表类型（如 `constraints.ordered` ）或关键字 `comparable` 。但如果你真的不想要约束，也就是说，像字面意义上的 *任何* `T` 类型 ？

符合逻辑的方法是使用 `interface{}` （接口对类型的方法集没有任何限制）来表达。由于这是一个常见的约束，所以预先声明关键字 `any` 被提供来作为 `interface{}` 的别名。但是你只能在类型约束中使用这个关键字，所以 `any` 并不是等价于 `interface{}` 。

### 我可以使用代码生成器代替泛型吗

在 Go 的泛型出现之前，“代码生成器” 方法是处理此类问题的另一种传统方法。本质上，针对每种你的库中需要处理的特定类型，它都需要使用 [go 生成器工具](https://blog.golang.org/generate) 产生新的 Go 代码。

这虽然可行，但使用起来很笨拙，它的灵活性受到限制，并且需要额外的构建步骤。虽然代码生成器在某些情况下仍然有用，但我们不再需要使用它来模拟 Go 中的泛型函数和类型。

### 什么是合约

早期的 [设计草案](https://go.googlesource.com/proposal/+/master/design/go2draft-contracts.md) 中泛型使用了与我们今天相似的语法，但是它使用了一个新的关键字 `contract` 来实现类型约束，而非现有的 `interface` 。由于种种原因，它不太受欢迎，现在已经被废弃了。

## Further reading 延伸阅读

- [一个增加泛型的提案](https://blog.golang.org/generics-proposal)
- [泛型的下一阶段](https://blog.golang.org/generics-next-step)
- [为什么使用泛型？](https://blog.golang.org/why-generics)
- [Go 泛型：将设计草案应用到真实的用例中](https://secrethub.io/blog/go-generics/)
- [在 Go 中尝试泛型](https://medium.com/swlh/experimenting-with-generics-in-go-39ffa155d6a1)