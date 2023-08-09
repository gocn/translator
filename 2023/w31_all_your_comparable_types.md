# All your comparable types
# 所有类型都可以比较

- [原文链接](https://go.dev/blog/comparable)
- 原文作者：Robert Griesemer
- [本文永久链接](https://github.com/gocn/translator/blob/master/2023/w31_all_your_comparable_types.md)
- 译者：[小超人](https://github.com/fcorpo)
- 校对：[-](https://github.com/)

2 月 1 号，我们发布了最新的 Go 1.20 版本，其中包括一些语言层面上的变更。在这里，我们将讨论其中一个变更：现在所有可比较的类型都可以满足之前的[可比较类型](https://go.dev/ref/spec#Comparison_operators)约束。令人惊讶的是，在 Go 1.20 之前，一些可比较的类型并不满足可比较性！

如果你对此感到困惑，那么你来对地方了。那么我们先声明一个有效的 map。

``` go
var lookupTable map[any]string
```

其中 map 的键类型为 any(这是一个[可比较的类型](https://go.dev/ref/spec#Comparison_operators))。这在 Go 中可以完美运行。另外，在 Go 1.20 之前，这种定义可以看似等效的泛型的 map 类型

``` go
type genericLookupTable[K comparable, V any] map[K]V
```

是否看似可以像普通的 map 类型一样使用，但是在将 any 用作键类型时产生编译时错误

``` go
var lookupTable genericLookupTable[any, string] // ERROR: any does not implement comparable (Go 1.18 and Go 1.19)
```

从 Go 1.20 开始，这段代码可以很好地编译。

在 Go 1.20 之前，comparable 的行为特别令人讨厌，因为它阻止了我们编写一开始希望使用泛型编写的泛型库。从 [`maps.Clone`](https://go.dev/issue/57436) 函数的提议

``` go
func Clone[M ~map[K]V, K comparable, V any](m M) M { … }
```

可以编写，但不能用于像 `lookupTable` 这样的 map，原因与我们的 `genericLookupTable` 不能与 `any` 作为键类型一样。

在这篇博文中，我们希望对这一切背后的语言机制有所启发。为了做到这一点，我们从一些背景信息开始。

## 类型参数和约束

从 Go 1.18 开始引入了泛型，并将[类型参数](https://go.dev/ref/spec#Type_parameter_declarations)作为新的语言结构。

在普通函数中，参数的取值范围是受其类型限制的一组值。类似地，在泛型函数(或类型)中，类型参数的范围超过受其类型约束限制的一组类型。因此，类型约束定义了允许作为类型参数的类型集。

GO 1.18 还改变了我们定义接口的方式：在过去一个接口定义了一组方法，现在接口定义了一组类型。这种新方式完全向后兼容：对于由接口定义的任何给定的方法集，我们可以想象所有实现这些方法的（无限）集。例如，给定一个 [`io.Writer`](https://go.dev/pkg/io#Writer) 接口，我们可以想象所有具有适当签名的 `Write` 方法的无限集。所有这些类型都实现了接口，因为它们都具有所需的 `Write` 方法。

但是，从新的类型集合来看比旧方法集更强大：我们可以明确地描述一组类型，而不仅仅是通过方法间接描述。这为我们提供了控制类型集的新方法。从 GO 1.18 开始，接口不仅可以嵌入其他接口，还可以嵌入任何类型，类型的结合或共享相同[基础类型](https://go.dev/ref/spec#Underlying_types)的无限类型。然后将这些类型包含在[类型集计算](https://go.dev/ref/spec#General_interfaces)中：联合符号 `A|B` 表示 "A型或类型B"，并且 `〜T` 表示法代表“具有基础类型 `T` 的所有类型”。

``` go
interface {
    ~int | ~string
    io.Writer
}
```

这个是定义所有基础类型是 `int` 或字符串，并且还实现了 `io.Writer` 的 `Write` 方法的接口。

这种广义接口不能用作变量类型。但是因为它们描述了类型集，所以它们被用作类型约束，即类型集。例如，我们可以写一个泛型的 `min` 函数

``` go
func min[P interface{ ~int64 | ~float64 }](x, y P) P
```

它接受任何 `int64` 或 `float64` 参数。(当然，更好的实现应该使用约束，用 `<` 操作符枚举所有基本类型。)

顺便说一句，由于没有方法的枚举明确类型是常见的，因此一点点的[语法糖](https://en.wikipedia.org/wiki/Syntactic_sugar)允许我们[忽略闭包接口](https://go.dev/ref/spec#General_interfaces)，从而更加符合我们的使用习惯。

``` go
func min[P ~int64 | ~float64](x, y P) P { … }
```

从新的类型集合来看，我们还需要一种新的方式来解释实现[接口](https://go.dev/ref/spec#Implementing_an_interface)意味着什么。如果一个类型 `T` 是接口类型集合的一个元素，那么 (非接口)类型 `T` 实现接口 `I`。如果 `T` 本身是一个接口，它描述了一个类型集。该集合中的每一个类型必须也在 `I` 的类型集合中，否则 `T` 将包含不实现 `I` 的类型。因此，如果 `T` 是一个接口，如果 `T` 的类型集合是`I` 的类型集合的子集，它实现接口 `I`。

现在，我们已经具备了理解满足约束的所有要素。正如我们之前看到的，类型约束描述了可接受参数类型的类型参数集。如果类型参数在约束接口描述的集合中，则类型参数满足相应的类型参数约束。这是说类型参数实现约束的另一种方式。在 GO 1.18 和 GO 1.19 中，满足约束条件意味着实现约束。正如我们将一点点看到的那样，在 GO 1.20 满足约束条件不再是实现约束。

## 对类型参数值的操作

类型约束不仅指定类型参数可以接受的类型参数，还确定了类型参数值可能的操作。正如我们所期望的那样，如果一个约束定义了诸如 `Write`，则可以根据相应类型参数的值调用 `Write` 方法。一般来说，由约束定义的类型集中所有类型支持的操作允许使用相应类型参数的值, 比如 `+` 或者 `*` 操作。

例如，拿 `min` 函数来举例，在函数体中，允许在包含所有基本算术操作的类型参数 P 的值上使用 int64 和 float64 类型支持的任何操作，但也可以比较 <。但它不包括诸如 `＆` 或 `|` 之类的位操作因为这些操作未在 float64 值上定义。

## 可比较的类型

与其他一般和二进制操作相反，`==` 不仅在有限的[预先声明类型](https://go.dev/ref/spec#Types)中定义，而且在无限的类型上，包括数组，结构和接口。不可能在约束中列举所有这些提到过的类型。如果我们关心的是预期类型，我们需要一种不同的机制来表达类型参数必须支持 `==`（当然了也包括 `!=` ）。

我们通过 Go 1.18 中引入的预声明类型 [`comparable`](https://go.dev/ref/spec#Predeclared_identifiers) 解决了这个问题。`Comparable` 是一个类型集是可比较类型的无限集的接口类型，当需要类型实参来支持 `==` 时，可将其用作约束。

但是，可比较组成的类型集与 GO 规格定义的所有[可比类型](https://go.dev/ref/spec#Comparison_operators)的集合并不相同。通过[构造](https://go.dev/ref/spec#Interface_types)，接口指定的类型（包括可比较类型）不包含接口本身（或任何其他接口）。因此，即使所有接口支持 ==，诸如 `any` 接口之类的接口也不包含在 `comparable` 中。这是为什么呢？

如果真正保存在接口的动态值并不具备可比较行，那么在运行时可能会发生恐慌，即使是可比较类型的接口和包含可比较性的复合类型。就拿一开始的 `lookupTable` 来举例: 它的键可以接受任意类型的值。但是， 如果我们尝试使用不支持 `==` 运算的类型作为键， 比如说， 切片，那么， 我们会得到运行时的恐慌:

``` go
lookupTable[[]int{}] = "slice"  // PANIC: runtime error: hash of unhashable type []int
```

相比之下，`可比较` 仅仅是编译器保证不会因为 `==` 运算而引发恐慌的类型。我们称这些类型为严格可比较的。

在大多数情况下，这种结果是符合我们预期的并且是令人欣慰的，如果我们操作数满足 `可比较性` 的约束，`==` 在泛型函数中并不会引发恐慌并且得到我们期望的结果。

不幸的是，这种可比较的定义和满足这种约束规则放在一起，导致我们无法编写有效的通用代码，比如，前面提到的 `genericLookupTable` 类型， 对于 `any` 来说可以接受任意类型的参数，但是 `any` 必须满足可比较性。但是， any 是一个满足可比较类型的大集合并且包含了没有实现可比较类型的集合类型的集合。

``` go
var lookupTable GenericLookupTable[any, string] // ERROR: any does not implement comparable (Go 1.18 and Go 1.19)
```

用户很早就意识到了这个问题，并在短时间内提出了许多问题和建议([#51338](https://go.dev/issue/51338), [#52474](https://go.dev/issue/52474), [#52531](https://go.dev/issue/52531), [#52614](https://go.dev/issue/52614), [#52624](https://go.dev/issue/52624), [#53734](https://go.dev/issue/53734), etc)。显然，这是我们需要解决的问题。

最简单的解决方案是将不具备严格的可比较性的的类型放入可比较类型的集合中。但是，这将会导致在类型集合的模型中产生不一致的行为，比如说下面这个例子：

``` go
func f[Q comparable]() { … }

func g[P any]() {
        _ = f[int] // (1) ok: int implements comparable
        _ = f[P]   // (2) error: type parameter P does not implement comparable
        _ = f[any] // (3) error: any does not implement comparable (Go 1.18, Go.19)
}
```

函数 `f` 需要严格可比的类型参数。很明显，我们可以用 int 类型的实例去调用函数 `f`, 因为 int 实现了可比较类型，int 类型的值永远不会在 `==` 运算符上产生恐慌行为(这是场景 1)。另外，如果使用 `P` 去实例化函数 `f`, 这将不会被允许的，因为 `P` 类型定于的约束为 `any`, 而 `any` 则代表了所有可能的集合。这个类型集合包含了根本不具备可比较性的类型，因为，`P` 没有实现可比较性所以不能用来实例化函数 `f`(这是场景 2)。最后，使用 `any`（而不是被 `any` 限制的类型参数） 类型也不能工作，这个问题和上面描述的一样(这是场景 3)。

但是，在这种情况下，我们依然系统能够使用 `any` 来作为类型参数。唯一能够改变当前困境的方式就是以某种方式改变语言。 但是如果改变呢？

## 接口实现 vs 满足约束

如先前所言，满足约束条件是实现接口， 如果类型参数 `T` 满足 `C` 的约束，那么认为 `T` 实现 `C` . 这是有意义的，实现接口的真正定义是 `T` 必须满足类型 `C` 的期望。

但是，这也是一个问题，因为这阻止我们使用不严格的可比较类型作为可比较类型的参数。

因此，对于 Go 1.20 来说，经过了一年多的公开讨论多个可替代的方案（请参见上述提议），我们决定仅仅针对这个场景破例一次。避免概念不一致，而不是更改可比较的含义，我们区分了接口实现，这个与类型参数传值有关，和满足约束， 这个和类型参数传递的参数类型有关。我们正针对提案[#56548](https://go.dev/issue/56548)将二者分开定义，一旦分开，我们就可以针对每个概念赋予不同的规则。

好消息是，这个 [规范](https://go.dev/ref/spec#Satisfying_a_type_constraint) 相当地接地气。并且满足约束和实现接口基本一致，但是仍然有需要注意的地方:

> A type `T` satisfies a constraint `C` if
> 
> -   `T` implements `C`; or
> -   `C` can be written in the form `interface{ comparable; E }`, where `E` is a basic interface and `T` is [comparable](https://go.dev/ref/spec#Comparison_operators) and implements `E`.


第二个要点是一个例外。在没有深入理解规范的情况下，就如期望所说的如下: `C` 的约束是期望严格的可比较类型(并且还有可能其他的需求，比如方法 `E`)是支持 `==` 运算的任意类型 `T` (当然了，也可能实现了 `E` 接口下的多个方法)。简而言之，一个支持 `==` 运算的类型同样也满足了可比较性(即使它可能没有实现它)。

我们马上就能看到这个变化的向后兼容性， 在 Go 1.20 之前，满足约束和接口实现是一样的，并且我们依然有这个规则(在第一点)。所有的依赖于改规则的代码依然能够像以前一样继续工作。只有当该规则失败时，我们才需要关注异常。


让我们回顾一下前面的例子

``` go
func f[Q comparable]() { … }

func g[P any]() {
        _ = f[int] // (1) ok: int satisfies comparable
        _ = f[P]   // (2) error: type parameter P does not satisfy comparable
        _ = f[any] // (3) ok: satisfies comparable (Go 1.20)
}
```

Now, `any` does satisfy (but not implement!) `comparable`. Why? Because Go permits `==` to be used with values of type `any` (which corresponds to the type `T` in the spec rule), and because the constraint `comparable` (which corresponds to the constraint `C` in the rule) can be written as `interface{ comparable; E }` where `E` is simply the empty interface in this example (case 3).

现在，`any` 类型都满足(但是没有实现)可比性。这是为什么呢？因为  Go 允许 `==` 操作运算符被用在 `any` 类型(这对应规则中的 `T` 类型)，因为可比较的约束(对应规则中 C 的约束) `E` 类型还可以写为 `interface {comparable; E}`，其中 `E` 表示空接口(这个场景 3).

Interestingly, `P` still does not satisfy `comparable` (case 2). The reason is that `P` is a type parameter constrained by `any` (it _is not_ `any`). The operation `==` is _not_ available with all types in the type set of `P` and thus not available on `P`; it is not a [comparable type](https://go.dev/ref/spec#Comparison_operators). Therefore the exception doesn't apply. But this is ok: we do like to know that `comparable`, the strict comparability requirement, is enforced most of the time. We just need an exception for Go types that support `==`, essentially for historical reasons: we always had the ability to compare non-strictly comparable types.

有趣的是，`P` 依然没有满足可比较性(场景 2)。原因是 `P` 是一个受 `any` 约束的类型参数(但是它不是 `any`)。 `==` 运算操作并不适用于 `P` 所在的所有类型的集合也包括 `P` 本身；它并不是[可比较类型](https://go.dev/ref/spec#Comparison_operators)。因此，期望并不成立，不过，没有关系: 我们确实想要知道严格的可比性要求，并且在大部分时间强制执行。出于历史的缘故(我们总是有能力去比较非严格的可比较类型)，我们只是想要知道 Go 中支持 `==` 操作的的类型。

## 后果和补救措施

我们 Gophers 引以为豪的是，我们在语言规范中用一套相当简洁的规则来解释和简化特定语言的行为。多年来，我们不断完善这些规则，并在可能的情况下让它们变得更简单、更通用。我们还注意保持规则的正交性，时刻警惕意外和不幸的后果。解决争议的方法是查阅规范，而不是颁布法令。这是我们从 Go 诞生之初就一直追求的目标。

在精心设计的类型系统中，不能简单地添加一个特性而不产生后果！

那么，问题出在哪里呢？有一个明显的（或者是较小的）缺点，还有一个不那么明显的（更严重的）缺点。很明显，我们现在有了一个更复杂的约束满足规则，可以说没有以前那么优雅了。但这对我们的日常工作影响不大。

但是，我们这是要为这个例外付出代价: 在 Go 1.20 中，依赖于可比较类型的参数不再是静态类型安全的。如果将 `==` 和 `!=` 应用于可比较类型参数的操作数，即使在声明说他们是严格的可比较类型的，也有可能会引起恐慌行为。一个不是可比较类型的值会偷偷穿过多个泛型函数或者类型从而引起恐慌行为。在 Go 1.20 中，我们现在可以声明

``` go
var lookupTable genericLookupTable[any, string]
```

编译时不会出错，但如果我们在这种情况下使用了非严格可比的键类型，就会在运行时出现恐慌，就像使用内置的 map 类型一样。为了运行时检查，我们放弃了静态类型安全。

可能在某些情况下，这样做还不够好，我们需要强制执行严格的可比性。下面的观点允许我们至少以有限的形式做到这一点：类型参数并不受益于我们添加到约束满足规则中的例外情况。例如，在我们前面的例子中，函数 `g` 中的类型参数 `P` 受 `any` 约束（`any` 本身具有可比性，但不具有严格可比性），因此 `P` 不满足可比性。我们可以利用这些知识，为给定的 `T` 类型编写一个编译时断言：

``` go
type T struct { … }
```

我们要断言 T 是严格可比的。我们很想写出这样的内容：

``` go
// isComparable may be instantiated with any type that supports ==
// including types that are not strictly comparable because of the
// exception for constraint satisfaction.
func isComparable[_ comparable]() {}

// Tempting but not quite what we want: this declaration is also
// valid for types T that are not strictly comparable.
var _ = isComparable[T] // compile-time error if T does not support ==
```

虚变量（空白）声明就是我们的 "断言"。但由于约束满足规则中的例外情况，`isComparable[T]` 只有在 `T` 完全不可比的情况下才会失败；如果 `T` 支持 `==` 则会成功。 我们可以不把 `T` 作为类型参数，而是作为类型约束来解决这个问题：

``` go
func _[P T]() {
    _ = isComparable[P] // P supports == only if T is strictly comparable
}
```

下面是一个演示场中有一个[通过](https://go.dev/play/p/9i9iEto3TgE)和[失败](https://go.dev/play/p/5d4BeKLevPB)的示例，说明了这一机制。

## 最后意见

有趣的是，直到 Go 1.18 发布前两个月，编译器实现满足约束的方式与我们现在在 Go 1.20 中实现的方式完全相同。但由于当时的满足约束意味着接口实现，我们的实现确实与语言规范不一致。第 [issue #50646](https://go.dev/issue/50646) 号问题提醒了我们这一事实。当时距离发布时间已经非常接近，我们必须尽快做出决定。在没有令人信服的解决方案的情况下，最稳妥的做法似乎是使实现与规范保持一致。一年后，我们有足够的时间来考虑不同的方法，现在看来，我们所采用的实现方式正是我们最初想要的实现方式。我们绕了一个大圈。

如果有任何不尽如人意的地方，请一如既往地通过 [https://go.dev/issue/new](https://go.dev/issue/new) 向我们提出问题。

谢谢！
