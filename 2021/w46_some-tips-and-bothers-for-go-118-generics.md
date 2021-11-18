# Go 1.18 泛型的一些技巧和困扰
- 原文地址：https://dev.to/codehex/some-tips-and-bothers-for-go-118-generics-lc7
- 原文作者：[Kei Kamikawa](https://github.com/Code-Hex)
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w46_some-tips-and-bothers-for-go-118-generics.md
- 译者：[Cluas](https://github.com/Cluas)

截至 2021 年 11 月 17 日，社区可能还没有使用 Go 1.18 泛型功能的缓存库。

我尝试在这里实现了第一个 Go 1.18 泛型的缓存库。如果你能够给的 GitHub 加个 Star，我会感到非常高兴。
[https://github.com/Code-Hex/go-generics-cache](https://github.com/Code-Hex/go-generics-cache)

在这篇文章中，我将介绍我在开发这个缓存库时注意到的关于 Go 泛型的一些情况，以及我发现的一些技巧和困扰。

## 对任何类型都返回零值

你经常会写一些返回 `any`和 `error`的代码，比如说下面这样。当一个函数发生错误时，你会写一些返回零值和错误的代码，但现在你需要换一种思维方式。
```go
func Do[V any](v V) (V, error) {
    if err := validate(v); err != nil {
        // What should we return here?
    }
    return v, nil
}

func validate[V any](v V) error
```

假设你在这里写`return 0, err`。这将是一个编译错误。原因是`any`类型可以是`int`类型以外的类型，比如`string`类型。那么我们应该怎么做呢？

让我们用类型参数的`V`声明一次变量。然后你可以把它写成可编译的形式，如下：

```go
func Do[V any](v V) (V, error) {
    var ret V
    if err := validate(v); err != nil {
        return ret, err
    }
    return v, nil
}
```

此外，可以使用带命名的返回值来简化单行的书写。

```go
func Do[V any](v V) (ret V, _ error) {
    if err := validate(v); err != nil {
        return ret, err
    }
    return v, nil
}
```
[https://gotipplay.golang.org/p/0UqA0PIO9X8](https://gotipplay.golang.org/p/0UqA0PIO9X8)
## 不要试图用`约束`做类型转换

我想提供两个方法，`Increment`和`Decrement`。它们可以从[go-generics-cache](https://github.com/Code-Hex/go-generics-cache)库中增加或减少值，如果存储的值满足[Number 约束](https://github.com/Code-Hex/go-generics-cache/blob/d5c3dda0e57b4c533c1e744869032c33a4fc2d9e/constraint.go#L5-L8)。

让我们用`Increment`方法作为一个例子。我最初写的代码是这样的：

```go
type Cache[K comparable, V any] struct {
    items map[K]V
}

func (c *Cache[K, V]) Increment(k K, n V) (val V, _ error) {
    got, ok := c.items[k]
    if !ok {
        return val, errors.New("not found")
    }

    switch (interface{})(n).(type) {
    case Number:
        nv := got + n
        c.items[k] = nv
        return nv, nil
    }
    return val, nil
}
```

我在考虑使用值`n V`的类型来匹配被满足的约束。如果满足`Number`约束，这个方法就会增加，否则什么都不做。

这将不会被编译。

1. Go 不为约束条件提供条件分支
2. 约束是一个接口，Go 不允许使用接口进行类型断言
3. `n`的类型没有确定，所以`+`操作是不可能的
4. 首先，不能保证`items`的类型与`n`的类型相同

为了解决这些问题，我决定嵌入`Cache`结构。我还定义了一个`NumberCache`结构，可以一直处理`Number`约束。

- 继承 `Cache`结构体所持有的字段数据
- 处理 `Cache`的方法

```go
type NumberCache[K comparable, V Number] struct {
    *Cache[K, V]
}
```

这样，我们可以保证传递给`Cache`结构的值的类型永远是`Number`的约束。所以我们可以给`NumberCache`结构添加一个`Increment`方法。

```go
func (c *NumberCache[K, V]) Increment(k K, n V) (val V, _ error) {
    got, ok := c.Cache.items[k]
    if !ok {
        return val, errors.New("not found")
    }
    nv := got + n
    c.Cache.items[k] = nv
    return val, nil
}
```
[https://gotipplay.golang.org/p/poQeWw4UE_L](https://gotipplay.golang.org/p/poQeWw4UE_L)

## 使我困扰的点

让我们再看一下`Cache`结构的定义。

```go
type Cache[K comparable, V any] struct {
    items map[K]V
}
```
Go 范型被定义为一种带有约束的语言规范，这种约束被称为 [comparable](https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md#comparable-types-in-constraints)。这允许只有类型可以使用 `==` 和 `!=`。

我觉得这个约束条件让我很困扰。让我解释一下困扰我的原因。

我定义了一个函数来比较两个 `comparable` 的值。

```go
func Equal[T comparable](v1, v2 T) bool {
    return v1 == v2
}
```
只允许 `comparable` 的类型，如果在编译时将不可比较的类型传递给函数，就会导致错误。你可能认为这很有用。

然而，根据 Go 的规范，`interface{}`也满足这个可比较的约束。

如果`interface{}`可以被满足，下面的代码就可以被编译了。

```go
func main() {
    v1 := interface{}(func() {})
    v2 := interface{}(func() {})
    Equal(v1, v2)
}
```
这表明`func()`类型是一个不可比较的类型。但可以通过将其转换为`interface{}`类型来转换为可比较的类型。

`interface{}`类型只有在运行时才能知道它是否是一个可比较的类型。

如果这是一段复杂的代码，可能很难被注意到。

[https://gotipplay.golang.org/p/tbKKuehbzUv](https://gotipplay.golang.org/p/tbKKuehbzUv)

我相信我们需要另一个不接受`interface{}`的可比约束，以便在编译时注意到。

这种约束可以由 Go 用户来定义吗？目前的答案是不能。

这是因为`comparable`约束包含 "可比较的结构体" 和 "可比较的数组"。

这些约束目前不能由 Go 用户定义。因此，我想把它们作为 Go 规范来提供。

我还为此创建了一个提案，如果你也认同这个说法，请在 GitHub 问题上给我👍，我将不胜感激。
[https://github.com/golang/go/issues/49587](https://github.com/golang/go/issues/49587)

## 文中提到的链接
- comparable  https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md#comparable-types-in-constraints
