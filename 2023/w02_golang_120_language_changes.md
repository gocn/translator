# Go 1.20 新变化！第一部分：语言特性

- 原文地址：<https://blog.carlmjohnson.net/post/2023/golang-120-language-changes/>
- 原文作者：[Carl M. Johnson](https://carlmjohnson.net/)
- 本文永久链接：<https://github.com/gocn/translator/blob/master/2023/w02_golang_120_language_changes.md>
- 译者：[pseudoyu](https://github.com/pseudoyu)
- 校对：[小超人](https://github.com/focozz)

又到了 Go 发布新版本的时刻了！2022 年第一季度的 Go 1.18 是一个主版本，它在语言中增加了期待已久的泛型，同时还有[许多微小功能更新](https://blog.carlmjohnson.net/post/2021/golang-118-minor-features/)与[优化](https://blog.carlmjohnson.net/post/2022/golang-118-even-more-minor-features/)。2022 年第三季度的 Go 1.19 是一个[比较低调的](https://blog.carlmjohnson.net/post/2022/golang-119-new-features/)版本。现在是 2023 年，Go 1.20 [RC 版本](https://groups.google.com/g/golang-nuts/c/HMUAm5j5raw/m/va3dxBFyAgAJ)已经发布，而正式版本也即将到来，Go 团队已经发布了[版本说明草案](https://tip.golang.org/doc/go1.20)。

在我看来，Go 1.20 的影响介于 1.18 和 1.19 之间，比 1.19 有更多的功能更新并解决了一些长期存在的问题，但没有达到 1.18 中为语言增加泛型这样的重磅规模。尽管如此，我还是要把我对“Go 1.20 的新变化”的看法分成系列三篇博文。首先，我写了 Go 1.20 中的语言变化（如下），在下一篇文章中，我将写标准库的重要变化，最后一篇将是我对最喜欢的标准库的一些小补充。

---

那么，让我们来看看语言方面的变化。首先，对泛型的规则做了一个小小的修改。有了 Go 泛型，你可以通过一个函数获取任何 `map` 的键：

```go
func keys[K comparable, V any](m map[K]V) []K {
    var keys []K
    for k := range m {
        keys = append(keys, k)
    }
    return keys
}
```

在这段代码中，`K comparable, V any`为“类型约束”。这意味着 K 可以是任何 comparable 的类型，而 V 则没有类型限制。comparable 类型为数字、布尔、字符串和由 comparable 元素组成的固定大小的复合类型等。因此，K 为 int，V 为一个 bytes 切片是合法的，但 K 是一个 bytes 切片是非法的。

我说过上面的代码会给你任何 `map` 的键，但在 Go 1.18 和 1.19 中，这并不是完全正确的。如果你试图把它用在一个键值为接口类型的 `map` 上，它将不会被编译。

```go
m := make(map[any]any) // ok
keys(m)
// 编译器错误（Go 1.19）：any 没有实现 comparable
```

这个问题归结为围绕 `K comparable` 含义的解读。要作为 `map` 键使用，类型必须被 Go 编译器认为是 comparable 的。例如，这是无效的：

```go
m := make(map[func()]any)
// 编译器错误：无效的 map 键类型 func()
```

然而，你可以通过使用接口来得到一个运行时错误而不是编译器错误：

```go
m := make(map[any]any) // 正确
k := func() {}
m[k] = 1 // panic：运行时错误：哈希值为不可哈希的类型 func()
```

所以，像 `any` 这样的接口类型是 map 的有效键类型，但如果你试图把一个缺少有效类型定义的键放到 map 中，就会在运行时出现 panic 错误。显然，没有人希望他们的代码在运行时出现 panic 错误，但这是在 map 中允许动态类型键的唯一方法。

下面是一个从不同角度看同一问题的例子。假设我有一个这样的错误类型：

```go
type myerr func() string

func (m myerr) Error() string {
    return m()
}
```

而现在我想使用自定义的错误类型进行比较：

```go
var err1 error = myerr(func() string { return "err1" })
var err2 error = myerr(func() string { return "err2" })
fmt.Println(err1 != nil, err2 != nil)  // 正确

fmt.Println(err1 == err2)
// panic：运行时错误：对 main.myerr 不可比类型进行比较
```

正如你所看到的，一个接口值在编译时被认为是 `comparable` 类型，但是如果它被赋的值是一个“不可比类型”，则在运行时就会出现 panic。如果你试图比较两个 `http.Handler`，而它们恰好都是 `http.HandlerFuncs`，你同样可以看到这个问题。

当 Go 1.18 支持了泛型后，[大家发现](https://github.com/golang/go/issues/49587)，由于接口在编译时被认为是 ，但可能会包含不可比较的具体类型。如果你写的泛型代码的类型约束是`comparable`，但错误的值被存储在一个接口中，就有可能出现运行时 panic。保守起见，[Go 团队决定](https://github.com/golang/go/issues/50646)在评估（此特性）的全部影响阶段，Go 1.18 限制使用接口作为`comparable` 类型。

现在已经过了一年了，也发布了两个版本，经过大量在 [Github 上进行的冗长讨论](https://github.com/golang/go/issues/51338)，Go 团队认为在通用代码中使用接口作为 `comparable` 类型应该是足够安全的。如果你在 Go 1.20 中运行`keys(map[any]any{})`，它可以正常运行，你不必考虑上面的任何说明。

---

Go 1.20 中的另一个语言变化更容易解释。如果你有一个切片，现在你可以很容易地将其转换为一个固定长度的数组：

```go
s := []string{"a", "b", "c"}
a := [3]string(s)
```

如果切片比数组短，你会因越界而产生 panic：

```go
s := []int{1, 2, 3}
a := [4]int(s)
// panic: 运行时错误: 不能将长度为 3 的切片转换成长度为 4 的数组或数组指针
```

这源于 Go 1.17 中增加的数组指针转换特性：

```go
s := []string{"a", "b", "c"}
p := (*[3]string)(s)
```

在这种情况下，p 指向 s 定义的数组，因此修改一个就会修改另一个：

```go
s := []string{"a", "b", "c"}
p := (*[3]string)(s)
s[0] = "d"
p[1] = "e"
fmt.Println(s, p) // [d e c] &[d e c]
```

另一方面，随着 Go 1.20 中新增的切片转换为数组特性，数组是 切片内容的副本：

```go
s := []string{"a", "b", "c"}
a := [3]string(s)
s[0] = "d"
a[1] = "e"
fmt.Println(s, a)
// [d b c] [a e c]
```

---

除了将切片转换为数组的语法外，Go 1.20 还为处理切片数据的 `unsafe` 包带来了一些新增内容。`reflect` 包一直有[reflect.SliceHeader](https://pkg.go.dev/reflect#SliceHeader)和[reflect.StringHeader](https://pkg.go.dev/reflect#StringHeader)，它们是 Go 中切片和字符串的运行时表示:

```go
type SliceHeader struct {
    Data uintptr
    Len  int
    Cap  int
}

type StringHeader struct {
    Data uintptr
    Len  int
}
```

`reflect.SliceHeader` 和 `reflect.StringHeader`都有一个 Warning 提示：“它的表示方法可能在以后的版本中改变，因此不能确保障安全或可移植”，并且在[试图废除它们](https://go-review.googlesource.com/c/go/+/401434)。误用这些类型可能会[导致代码崩溃](https://github.com/golang/go/issues/40701)，但是在实践中，很多程序都依赖于类似这样的切片布局，很难想象 Go 团队会在没有大量警告的情况下改变它，因为很多程序会崩溃。

为了给 Gopher 们提供一种官方支持的编写不安全代码的方式，Go 1.17 增加了[unsafe.Slice](https://pkg.go.dev/unsafe#Slice)，它允许你把任何指针变成一个切片（不管是否是个好主意）。

```go
obj := struct{ x, y, z int }{1, 2, 3}
slice := unsafe.Slice(&obj.x, 3)
obj.x = 4
slice[1] = 5
fmt.Println(obj, slice)
// {4 5 3} [4 5 3]
```

在 Go 1.20 中，还有 [unsafe.SliceData](https://pkg.go.dev/unsafe@go1.20rc2#SliceData)（它返回一个指向切片数据的指针），[unsafe.String](https://pkg.go.dev/unsafe@go1.20rc2#String)（它以不安全的方式通过一个 byte 指针创建字符串），以及 [unsafe.StringData](https://pkg.go.dev/unsafe@go1.20rc2#StringData)（它以不安全的方式返回一个指向字符串数据的指针）。

这些字符串函数是额外增加的不安全方式，因为它们允许你违反 Go 的字符串不可变规则，但它也给了你很大的控制权，可以在不分配新内存的前提下转换 byte 切片。

这些工具像利刃一样，好用却很容易割伤自己。在语言中直接支持这些工具可能更好，而不是仅仅让大家使用 `unsafe.Pointer` 来祈祷它奏效。

用 Hank Hill 的话来形容，[“无论你做什么，你都应该以正确的方式去做，即使是错误的事情。”](https://www.getyarn.io/yarn-clip/08e52ddd-63ee-429b-b40c-b12c8ff6670b)
