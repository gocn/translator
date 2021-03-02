# 带类型参数的切片上的泛型函数

- 原文地址：https://eli.thegreenplace.net/2021/generic-functions-on-slices-with-go-type-parameters/
- 原文作者： Eli Bendersky
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w10_Generic_functions_on_slices_with_Go_type_parameters.md
- 译者：Jancd
- 校对：

经过多年的努力，Go 的泛型提案已在本周被接受！对于 Go 社区来说，这是个好消息。Go 增加泛型特性这个事情最早能追溯到在 Go 1.0 发布之前的 2010 年。

我认为当前的这个提案在表达能力和可理解性之间取得了很好的平衡。 它应该能让 Go 程序员表达 95％ 泛型最需要的东西，同时也让编写那些在其他语言中被泛型贬损的难以理解的代码变得困难或不可能。目前，Go 团队正致力于在 1.18 版本中引入泛型（测试版将于 2021 年 12 月发布），尽管这些时间表还没有最终敲定。

上个月我写了一篇关于为什么在 Go 中在切片上编写泛型函数是困难的文章。为了庆祝这个提案被接受的里程碑，本篇博文展示了一旦这个泛型提案进入 Go，这将是一个不存在的问题。

## 切片的泛型函数？

让我们从定义问题开始；Ian Lance Taylor 有一篇非常棒的演讲和博客文章叫做[“为什么需要泛型?”]((https://blog.golang.org/why-generics))，我建议你先看看。

我将使用 Ian 的翻转切片函数作为示例，并将快速地讨论在那次演讲中已经涉及到的主题。

假设我们想写一个函数来反转 Go 中的切片；我们可以从一个具体的函数开始，比如下面的反转整型数的切片:

```go
func ReverseInts(s []int) {
  first := 0
  last := len(s) - 1
  for first < last {
    s[first], s[last] = s[last], s[first]
    first++
    last--
  }
}
```

那如何反转一个字符串切片？

```go
func ReverseStrings(s []string) {
  first := 0
  last := len(s) - 1
  for first < last {
    s[first], s[last] = s[last], s[first]
    first++
    last--
  }
}
```

emm，它看起来和上面的反转整形的函数很像，总结起来就是类型由 `int->string` 简单替换。那么问题来了，这个函数不能只写一次吗?

我们再看一个例子，Go 通过 interface 允许多态性；让我们试着写一个“泛型”函数来反转任何类型的切片：

```go
func ReverseAnything(s []interface{}) {
  first := 0
  last := len(s) - 1
  for first < last {
    s[first], s[last] = s[last], s[first]
    first++
    last--
  }
}
```

我们可以这样调用它，并且结果预期：

```go
iints := []interface{}{2, 3, 4, 5}
ReverseAnything(iints)

istrings := []interface{}{"joe", "mike", "hello"}
ReverseAnything(istrings)
```

那这就是我们想要的答案么？那么 Go 是不是一直都有泛型？虽然 `ReverseAnything` 会如期地反转 interface{} 切片，但在 Go 中我们通常不会在这样的切片中保存数据。理论上，我们可以这样做，但这将放弃大部分的 Go 静态类型，因为它在任何时候都需要依赖于(运行时)类型断言[1]

如果我们可以将 `[]int` 传递给 `ReverseAnything`，那一切好说。 但这是不可能的，[原因有很多](https://eli.thegreenplace.net/2021/go-internals-invariance-and-memory-layout-of-slices/)。

此外，我们也可以在反转之前将 `[]int` 复制到 `[]interface{}` 中，但这会有很多缺点：

 1. 更多的代码：我们必须将切片复制到 `[]interface{}` 中，然后调用反转函数，然后将结果复制回 `[]int` 中，而不是反转切片。
 2. 效率 - 大量的数据复制和分配新的切片，而简单的调用 `ReverseInts(intslice)` 是一个零分配的单一循环，也没有不必要的拷贝。

我们还可以采用其他方法，如[代码生成](https://blog.golang.org/generate)，但这些方法存在不同的问题，又会增加问题的复杂度。

所以我们需要[类型参数提案](https://go.googlesource.com/proposal/+/refs/heads/master/design/go2draft-type-parameters.md)。

## 编写带有类型参数的泛型代码

使用类型参数提案，编写一个通用的切片反转函数将很简单:

```go
func ReverseSlice[T any](s []T) {
  first := 0
  last := len(s) - 1
  for first < last {
    s[first], s[last] = s[last], s[first]
    first++
    last--
  }
}
```

函数名后面的方括号区域为函数的使用定义了一个类型参数。`[T any]` 表示 `T` 是一个类型形参，可以是*任何类型*。毫无疑问，函数体与我们的非泛型版本完全相同。

下面是我们如何使用它：

```go
s := []int{2, 4, 8, 11}
ReverseSlice(s)

ss := []string{"joe", "mike", "hello"}
ReverseSlice(ss)
```

得益于*类型推断*，当我们调用 `ReverseSlice` 时，我们不需要指定类型参数(实际上，在绝大多数其他情况下都是可行的)。

我不会详细介绍编译器是如何实现这一点的，因为实现细节仍在变化中。此外，不同的 Go 编译器可能会选择以不同的方式来实现这一点，那样挺好的。

但是，我将强调该建议的一个重要方面：类型参数的值并没有 'boxed'【译注：可理解为内存堆上分配】。这对效率有重要的影响！这意味着不管通用函数增加了什么开销(就运行时和内存占用而言)，它都可能是一个恒定的开销，而不是一个与切片大小有关的函数。

## 更多泛型切片函数的例子

类型参数最终允许程序员编写像 `map`，`reduce` 和 `filter` 这样的泛型函数！无论你是否认为这些函数在风格上适合 Go，它们都很好地展示了 Go 中这个新功能的能力。让我们以 `map` 为例:

```go
func Map[T, U any](s []T, f func(T) U) []U {
  r := make([]U, len(s))
  for i, v := range s {
    r[i] = f(v)
  }
  return r
}
```

它由两种类型参数化 —— 一种用于 slice 元素，另一种用于返回的 slice元 素。下面是一个假设的使用场景:

```go
s := []int{2, 4, 8, 11}
ds := Map(s, func(i int) string {return strconv.Itoa(2*i)})
```

映射函数接受 `int` 并返回 `string`。在调用 `Map` 时，这足以让 Go 的类型推断理解 `T` 是 `int`， `U` 是 `string`，而且我们不需要显式地指定任何类型。`ds` 被推断为 `[]string`。

当然，我们也可以将 `Map` 用于标准库中的现有函数，例如:

```go
names := []string{"joe", "mike", "sue"}
namesUpper := Map(names, strings.ToUpper)
```

Filter 示例:

```go
func Filter[T any](s []T, f func(T) bool) []T {
  var r []T
  for _, v := range s {
    if f(v) {
      r = append(r, v)
    }
  }
  return r
}
```

我们可以这样调用它:

```go
evens := Filter(s, func(i int) bool {return i % 2 == 0})
```

最后是 Reduce 示例:

```go
func Reduce[T, U any](s []T, init U, f func(U, T) U) U {
  r := init
  for _, v := range s {
    r = f(r, v)
  }
  return r
}
```

示例使用:

```go
product := Reduce(s, 1, func(a, b int) int {return a*b})
```

## 马上尝试类型参数

虽然泛型在 1.18 之前无法在 Go 中使用，但你今天就可以尝试我贴在这篇文章中的所有代码(以及任何你喜欢的代码)，有几种方法。

尝试小片段的最简单的方法是在[go2go版本的Go Playground](https://go2goplay.golang.org/)。它与 Go 工具链的类型参数开发分支保持了合理的同步。

要想尝新或编写更实质性的代码，你可以:

1. 克隆 Go 仓库(按照[这些说明](https://golang.org/doc/contribute.html#checkout_go))。
2. 切换到 dev.go2go 分支.
3. 构建工具链（在步骤 1 的链接中也有详细描述）
4. 使用工具 go2go 运行代码示例。

在[本文附带的代码仓库](https://github.com/eliben/code-for-blog/tree/master/2021/go-generic-slice)中，你可以找到一个简单的 bash 脚本，它可以正确地设置e nv vars 以执行步骤4。你可按需使用。

当你克隆 repo 并切换至 dev.go2go 分支后，建议查看 `src/cmd/go2go/testdata/go2path/src` 目录。它包含了许多使用类型参数的泛型 Go 代码示例，这些示例非常值得研究。