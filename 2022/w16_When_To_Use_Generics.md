# 何时使用泛型

- 原文地址：https://go.dev/blog/when-generics
- 原文作者：Ian Lance Taylor(Go Team)
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2022/w16_When_To_Use_Generics.md
- 译者：[haoheipi](https://github.com/haoheipi)
- 校对：[]()

## 介绍

这是作者在 Google Open Source Live 和 GopherCon 2021 上演讲的博客版本：
[Go Day 2021 on Google Open Source Live | Using Generics in Go](https://youtu.be/nr8EpUO9jhw)
[GopherCon 2021: Robert Griesemer & Ian Lance Taylor - Generics!](https://youtu.be/Pa_e9EeCdy8)

Go 1.18 版本增加了一个主要的新语言特性：支持泛型编程。在本文中，不会描述什么是泛型，也不会描述如何使用它们。本文将关注在 Go 编程中何时使用泛型，何时不使用泛型。

需要明确的是，本文提供的是一般的指导准则，而不是硬性规定。是否采用取决于你自己的判断，但如果你不确定，建议使用这里讨论的指导准则。

## 编写代码

让我们从编写 Go 的一般准则开始：通过编写代码来编写 Go 程序，而不是通过定义类型。当涉及泛型时，如果你通过定义类型参数约束来开始编写程序，则可能走错了方向。所以，首先应编写函数，然后当你清楚地看到可以使用类型参数时，再添加类型参数就很容易了。

## 类型参数什么时候有用？

再说明了上面这一点之后，现在让我们看看类型参数在哪些情况下可能有作用。

### 当使用语言自身定义的容器类型

一种情况是，对该语言中定义的特殊容器类型进行操作的函数（`slices`, `maps`, `channels`），如果函数具有这些类型的参数，并且函数代码没有对元素类型做出任何特定的假设，那么使用类型参数可能会很有用。

例如下面这个函数，它返回一个 `map` 中所有键的 `slice`，且函数中没有对 `map` 中的键值对类型做任何约束：

```golang
// MapKeys returns a slice of all the keys in m.
// The keys are not returned in any particular order.
func MapKeys[Key comparable, Val any](m map[Key]Val) []Key {
    s := make([]Key, 0, len(m))
    for k := range m {
        s = append(s, k)
    }
    return s
}
```

这段代码没有假设任何关于 `map` 键类型的内容，它也根本不依赖 `map` 值类型。它适用于任何 `map` 类型，这就使它成为使用类型参数的好选择。

对于这类函数，类型参数的替代方法通常是使用反射，但这是一种更笨拙的编程模型，在构建时不会进行静态类型检查，而且通常运行时也更慢。

### 通用的数据结构

类型参数可能有用的另一种情况是用于通用数据结构。这里所说的通用数据结构类似于 `slice` 或者 `map`，但没有内置在语言中，例如链表或二叉树。

目前，需要此类数据结构的程序通常会采用下面两种方法实现：使用特定的元素类型进行编写，或者使用接口类型。而将特定的元素类型替换为类型参数，可以生成更通用的数据结构，以用在程序的其他部分或其他程序中。将接口类型替换为类型参数，可以更高效地存储数据，节省内存资源；它还意味着代码可以避免类型断言，而且在编译时就进行全面的类型检查。

例如，使用类型参数的二叉树数据结构，看上去可能是这样的：

```golang
// Tree is a binary tree.
type Tree[T any] struct {
    cmp  func(T, T) int
    root *node[T]
}

// A node in a Tree.
type node[T any] struct {
    left, right  *node[T]
    val          T
}

// find returns a pointer to the node containing val,
// or, if val is not present, a pointer to where it
// would be placed if added.
func (bt *Tree[T]) find(val T) **node[T] {
    pl := &bt.root
    for *pl != nil {
        switch cmp := bt.cmp(val, (*pl).val); {
        case cmp < 0:
            pl = &(*pl).left
        case cmp > 0:
            pl = &(*pl).right
        default:
            return pl
        }
    }
    return pl
}

// Insert inserts val into bt if not already there,
// and reports whether it was inserted.
func (bt *Tree[T]) Insert(val T) bool {
    pl := bt.find(val)
    if *pl != nil {
        return false
    }
    *pl = &node[T]{val: val}
    return true
}
```

树中的每个节点都包含类型参数 `T` 的值。当使用特定的类型参数将该二叉树实例化时，该类型实参的值将直接存储在节点中，而不会作为接口类型存储。

这是对类型参数的合理使用，因为该树的数据结构甚至方法中的代码，在很大程度上独立于元素类型 `T`。

该树的数据结构需要知道如何比较元素类型 `T` 的值；它使用传入的比较函数来实现这目的。可以在 `find` 方法的第四行对 `bt.cmp` 的调用中看到这一点。除此之外，类型参数没有任何其他作用。

### 对于类型参数，首选函数而不是方法

上面树的示例说明了另一条准则：当你需要使用比较函数等功能时，最好选择函数而不是方法来实现。

我们可以定义 `Tree` 类型，该元素类型需要一个 `Compare` 或 `Less` 方法。为此可以通过编写一个需要该方法的约束条件来实现，这也意味着用于实例化 `Tree` 类型的任何类型实参都需要具有该方法。

而结果是，任何想将 `Tree` 与 `int` 这样的简单数据类型一起使用的人都必须定义自己的 `int` 类型，并编写自己的 `Compare` 方法。如果我们将 `Tree` 定义可以接受一个比较函数，就像上面看到的示例代码那样，那么很容易传入所需的函数。且编写比较函数就像编写方法一样容易。

如果 `Tree` 的元素类型碰巧已经有了一个 `Compare` 方法，那么我们可以简单地传入类似 `ElementType.Compare` 的方法表达式作为比较函数。

换句话说，将方法转换为函数要比向类型中添加方法简单得多。因此，对于通用数据类型，最好使用函数，而不是限制需要编写一个方法。

### 实现一个通用方法

类型参数可能有用的另一种情况是，当不同的类型需要实现一些公共方法，而针对各种类型的实现看起来都一样时。

例如，考虑标准库的 `sort.Interface` 接口。它要求一个类型实现三种方法：`Len`、`Swap`和 `Less` 。

下面是一个实现 `sort.Interface` 接口的泛型类型 `SliceFn` 的示例。该泛型类型适用于任何切片类型：

```golang
// SliceFn implements sort.Interface for a slice of T.
type SliceFn[T any] struct {
    s    []T
    less func(T, T) bool
}

func (s SliceFn[T]) Len() int {
    return len(s.s)
}
func (s SliceFn[T]) Swap(i, j int) {
    s.s[i], s.s[j] = s.s[j], s.s[i]
}
func (s SliceFn[T] Less(i, j int) bool {
    return s.less(s.s[i], s.s[j])
}
```

对于任何切片类型而言，`Len` 和 `Swap` 方法都完全相同。而 `Less` 方法则需要一个比较函数，也就是 `SliceFn` 中的 `Fn` 部分。与前面的 `Tree` 示例一样，我们将在创建 `SliceFn` 时传入一个这样的函数。

下面代码显示了如何通过比较函数来使用 `SliceFn` 对任何类型切片进行排序：

```golang
// SortFn sorts s in place using a comparison function.
func SortFn[T any](s []T, less func(T, T) bool) {
    sort.Sort(SliceFn[T]{s, cmp})
}
```

这与标准库函数 `sort.Slice` 类似，但是比较函数是使用值而不是 `slice` 的索引编写的。

对这类代码使用类型参数是合适的，因为所有切片类型对应的方法看起来都完全相同。

（我应该提到的是，Go 1.19，而不是 1.18，很可能会包含一个泛型函数，该函数使用比较函数对切片进行排序，并且该泛型函数很可能不会使用 `sort.Interface` 。见[提案#47619](https://go.dev/issue/47619)。但是，即使这个特定的示例今后很可能没有用处，其总体观点仍然是正确的：当你需要实现对所有相关类型看起来都相同的方法时，使用类型参数是合理的。）

## 类型参数什么时候没有用？

现在，让我们谈谈问题的另一面：什么情况下不适用泛型。

### 不要用类型参数替换接口类型

众所周知，Go 具有接口类型，接口类型已经可以允许某种泛型编程。

例如，广泛使用的 `io.Reader` 接口提供了一种泛型机制，用于从包含信息（如文件）或生成信息（如随机数生成器）的任何值中读取数据。对于某个类型的值，如果只需要对该值调用一个方法，请使用接口类型，而不是类型参数。`io.Reader` 接口简单易读且高效。从值中读取数据时，比如像调用 `Read` 方法，不需要使用类型参数。

例如，下面的第一个函数签名（仅使用接口类型）可能很容易更改为第二个版本（使用类型参数）。

```golang
func ReadSome(r io.Reader) ([]byte, error)

func ReadSome[T io.Reader](r T) ([]byte, error)
```

但不要做这种改变。使用接口类型会使函数更易于编写和阅读，并且执行时间可能相同。

最后值得强调的一点是。虽然可以用几种不同的方式实现泛型，而且实现会随着时间的推移而改变和改进。但在 Go 1.18 许多情况下的实现是，对于处理类型为类型参数的值，就像处理类型为接口类型的值一样。这意味着使用类型参数通常不会比使用接口类型更快。所以不要为了速度而从接口类型更改为类型参数，因为它很可能不会运行得更快。

### 如果方法实现不同，不要使用类型参数

在决定是否使用类型参数或接口类型时，请先考虑方法的实现。前面我们说过，如果一个方法的实现对于所有类型都是相同的，那么就使用一个类型参数。相反，如果每种类型的实现不同，则使用接口类型并编写不同的方法实现，不要使用类型参数。

例如，从文件中 `Read` 数据的实现与从随机数生成器中 `Read` 的实现完全不同。这意味着我们应该编写两种不同的读取方法，并使用 `io.Reader` 的接口类型。

### 适当的时候使用反射

Go 也有[运行时反射](https://pkg.go.dev/reflect)的功能。反射也能实现某种泛型编程，因为它允许你编写适用于任何类型的代码。

如果某些操作必须支持甚至没有方法的类型，那么接口类型就不起作用。并且如果每个类型的操作不同，那么类型参数也不合适。这个时候请使用反射。

[encoding/json](https://pkg.go.dev/encoding/json) 包就是一个例子。我们不能要求我们编码的每个类型都支持 `MarshalJSON` 方法，所以我们不能使用接口类型。但是对接口类型和对结构类型的编码完全不同，所以我们不应该使用类型参数。因此，标准库中使用的是反射，代码并不简单，但却很有效。有关详细信息，请参阅[源代码](https://go.dev/src/encoding/json/encode.go).

## 一个简单的准则

最后，关于何时使用泛型的讨论可以简化为一个简单的准则。

如果你发现自己多次编写完全相同的代码，其中代码之间的唯一差异是使用不同的类型，那么考虑是否可以使用类型参数。

另一种说法是，应该避免使用类型参数，直到你注意到自己即将编写多次完全相同的代码。
