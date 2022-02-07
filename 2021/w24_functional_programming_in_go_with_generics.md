# 使用 Go 泛型的函数式编程

* 原文地址：https://ani.dev/2021/05/25/functional-programming-in-go-with-generics/
* 原文作者：`Ani Channarasappa`
* 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w24_functional_programming_in_go_with_generics.md

- 译者：[cvley](https:/github.com/cvley)
- 校对：[](.)


时间：[2021 年 5 月 25 日](#)

函数式编程是很多语言正在支持或已经支持的日渐流行的编程范式。Go 已经支持了其中一部分的特性，比如头等函数和更高阶功能的支持，使函数式编程成为可能。

Go 缺失的一个关键特性是泛型。缺少这个特性，Go 的函数库和应用不得不从下面的两种方法中选择一种：类型安全 + 特定使用场景或类型不安全 + 未知使用场景。在 2022 年初即将发布的 Go 1.18 版本，[泛型将被加进来](https://blog.golang.org/generics-proposal)，从而使 Go 支持新型的函数式编程形式。

在本篇文章中，我将介绍一些[函数式编程的背景](#Background)，Go 函数式编程的现状调查，并讨论 Go 1.18 计划的特性以及如何将它们用于函数式编程。

## 背景

### 什么是函数式编程

[维基百科](https://en.wikipedia.org/wiki/Functional_programming)中定义的函数式编程是：

> 通过应用组合函数的编程范式。

更具体的说，函数式编程有以下几个关键特征：

*   **纯函数** - 使用相同的输入总是返回无共享状态、可变数据或副作用的相同输出的函数
*   **不可变数据** - 数据创建后不会再被分配或修改
*   **函数组合** - 组合多个函数对数据进行处理逻辑
*   **声明式而非指令式** - 表示的是函数的_处理方式_而无需定义 _如何_完成

对于函数式编程更详细的信息，可以参考这两篇有详细描述例子的文章：[函数式编程是什么？](https://medium.com/javascript-scene/master-the-javascript-interview-what-is-functional-programming-7f218c68b3a0)和[函数式的 Go](https://medium.com/@geisonfgfg/functional-go-bc116f4c96a4)

### 函数式编程的优势是什么

函数式编程是让开发者提升代码质量的一些模式。这些质量提升的模式并非函数式编程独有，而是一些“免费”的优势。

*   **可测性** - 测试纯函数更加简单，因为函数永远不会产生超出作用范围的影响（比如，终端输出、数据库的读取），并总会得到可预测的结果
*   **可表达性** - 函数式编程/库使用声明式的基础可以更高效地表达函数的原始意图，尽管需要额外学习这些基础
*   **可理解性** - 阅读和理解没有副作用、全局或可变的纯函数主观来看更简单

正如多数开发者从经验中学到的，如 Robert C. Martin 在[_代码整洁之道_](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)中所说：

> 确实，相对于写代码，花费在读代码上的时间超过 10 倍。为了写出新代码，我们一直在读旧代码。……\[因此，\] 让代码更易读，可以让代码更易写。

根据团队的经验或学习函数式编程的意愿，这些优势会产生很大的影响。相反，对于缺乏经验和足够时间投入学习的团队，或维护大型的代码仓库时，函数式编程将会产生相反的作用，上下文切换的引入或显著的重构工作将无法产生相应的价值。

## Go 函数式编程的现状

Go 不是一门函数语言，但确实提供了一些允许函数式编程的特性。有大量的 Go 开源库提供函数特性。我们将会讨论泛型的缺失导致这些库只能折衷选择。

### 语言特性

函数式编程的语言支持包括一系列从仅支持函数范式（比如 Haskell）到多范式和头等函数的支持（比如 Scale、Elixir），还包括多范式和部分支持（如 Javascript、Go）。在后面的语言中，函数式编程的支持一般是通过使用社区创建的库，它们复制了前面两个语言的部分或全部的标准库的特性。

属于后一种类别的 Go 要使用函数式编程需要下面这些特性：

| 语言特性     | 支持情况 |
| ------------------------------------------------------------ | ------- |
| [头等函数和高阶函数](https://golangbot.com/first-class-functions/) | ✓       |
| [闭包](https://tour.golang.org/moretypes/25)             | ✓       |
| [泛型](https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md) | ✓†      |
| [尾部调用优化](https://github.com/golang/go/issues/22624) | ✗       |
| [可变参数函数](https://gobyexample.com/variadic-functions) + [可变类型参数](https://en.wikipedia.org/wiki/Variadic_template) | ✗       |
| [柯里化](https://blog.bitsrc.io/understanding-currying-in-javascript-ceb2188c339) | ✗       |

† 将在 Go 1.18 中可用（2022 年初）

### 现有的库

在 Go 生态中，有大量函数式编程的库，区别在于流行度、特性和工效。由于缺少泛型，它们全部只能从下面两种选择中取一个：

1.  **类型安全和特定使用场景** - 选择这个方法的库实现的设计是类型安全，但只能处理特定的预定义类型。因为无法应用于自适应的类型或结构体，这些库的应用范围将受限制。
    *   比如，`func UniqString(data []string) []string` 和 `func UniqInt(data []int) []int` 都是类型安全的，但只能应用在预定义的类型
2.  **类型不安全和未知的应用场景** - 选择这个方法的库实现的是类型不安全但可以应用在任意使用场景的方法。这些库可以处理自定义类型和结构体，但折衷点在于必须使用[类型断言](https://tour.golang.org/methods/15)，这让应用在不合理的实现时有运行时崩溃的风险。
    *   比如，一个通用的函数可能有这样的命名：`func Uniq(data interface{}) interface{}`

这两种设计选择显示了两种相似的不吸引人的选项：有限的使用或运行时崩溃的风险。最简单也许最常见的选择是不使用 Go 的函数式编程库，坚持指令式的风格。

## 使用泛型的函数式 Go

在 2021 年 3 月 19 日，泛型的[设计提案](https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md)通过并定为 Go 1.18 发行版的一部分。有了泛型之后，函数式编程库就不再需要在可用性和类型安全之间进行折衷。

### Go 1.18 实验

Go 开发组发布了一个 [go 1.18 游乐场](https://go2goplay.golang.org/)，便于大家尝鲜泛型。同时也有一个实验性的编译器，在 go 代码仓库的[一个分支](https://github.com/golang/go/tree/dev.go2go)上实现了泛型特性的最小集合。这两个都是在 Go 1.18 上尝鲜泛型的不错选择。

### 一个使用场景的探索

在前面说到的那个 unique 函数使用了两种可能的设计方法。有了泛型，它可以重写为 `func Uniq[T](data []T) []T`，并可以使用任意类型来调用，比如 `Uniq[string any](data []string) []string` 或 `Uniq[MyStruct any](data []MyStruct) []MyStruct`。为了进一步阐述这个概念，下面是一个具体的例子，展示了在 Go 1.18 中如何使用函数式单元来解决实际问题。

#### 背景

一个在网络世界常见的案例是 HTTP 的请求响应，其中 API 接口返回的 JSON 数据一般会被消费应用转换为一些有用的结构。

#### 问题 & 输入数据

考虑下这个从 API 返回用户、得分和朋友信息的响应：

```plain
[
  {
    "id": "6096abc445dbb831decde62f",
    "index": 0,
    "isActive": true,
    "isVerified": false,
    "user": {
      "points": 7521,
      "name": {
        "first": "Ramirez",
        "last": "Gillespie"
      },
      "friends": [
        {
          "id": "6096abc46573cedd17fb0201",
          "name": "Crawford Arnold"
        },
        ...
      ],
      "company": "SEALOUD"
    },
    "level": "gold",
    "email": "ramirez.gillespie@sealoud.com",
    "text": "Consequat pariatur aliquip pariatur mollit mollit cillum sint. Elit est nisi velit cillum. Ex mollit dolor qui velit Lorem proident ullamco magna velit nulla qui. Elit duis non ad laborum ullamco irure nulla culpa. Proident culpa esse deserunt minim sint nisi duis culpa nostrud in incididunt ad. Amet qui laborum deserunt proident adipisicing exercitation quis.",
    "created_at": "Saturday, August 3, 2019 8:12 AM",
    "greeting": "Hello, Ramirez! You have 9 unread messages.",
    "favoriteFruit": "banana"
  },
  ...
]
```

假设目标是获取各个等级的高分用户。我们将看下函数式和指令式风格的样子。

#### 指令式

```golang
// imperative
func getTopUsers(posts []Post) []UserLevelPoints {

	postsByLevel := map[string]Post{}
	userLevelPoints := make([]UserLevelPoints, 0)

	for _, post := range posts {

		// Set post for group when group does not already exist
		if _, ok := postsByLevel[post.Level]; !ok {
			postsByLevel[post.Level] = post
			continue
		}

		// Replace post for group if points are higher for current post
		if postsByLevel[post.Level].User.Points < post.User.Points {
			postsByLevel[post.Level] = post
		}
	}

	// Summarize user from post
	for _, post := range postsByLevel {
		userLevelPoints = append(userLevelPoints, UserLevelPoints{
			FirstName:   post.User.Name.First,
			LastName:    post.User.Name.Last,
			Level:       post.Level,
			Points:      post.User.Points,
			FriendCount: len(post.User.Friends),
		})
	}

	return userLevelPoints

}

posts, _ := getPosts("data.json")
topUsers := getTopUsers(posts)

fmt.Printf("%+v\n", topUsers)
// [{FirstName:Ferguson LastName:Bryant Level:gold Points:9294 FriendCount:3} {FirstName:Ava LastName:Becker Level:silver Points:9797 FriendCount:2} {FirstName:Hahn LastName:Olsen Level:bronze Points:9534 FriendCount:2}]
```

[样例的完整代码](https://github.com/achannarasappa/pneumatic/blob/main/examples/imperative-transformation/main.go2)

#### 函数式

```golang
// functional
var getTopUser = Compose3[[]Post, []Post, Post, UserLevelPoints](
	// Sort users by points
	SortBy(func (prevPost Post, nextPost Post) bool {
		return prevPost.User.Points > nextPost.User.Points
	}),
	// Get top user by points
	Head[Post],
	// Summarize user from post
	func(post Post) UserLevelPoints {
		return UserLevelPoints{
			FirstName:   post.User.Name.First,
			LastName:    post.User.Name.Last,
			Level:       post.Level,
			Points:      post.User.Points,
			FriendCount: len(post.User.Friends),
		}
	},
)

var getTopUsers = Compose3[[]Post, map[string][]Post, [][]Post, []UserLevelPoints](
	// Group posts by level
	GroupBy(func (v Post) string { return v.Level }),
	// Covert map to values only
	Values[[]Post, string],
	// Iterate over each nested group of posts
	Map(getTopUser),
)

posts, _ := getPosts("data.json")
topUsers := getTopUsers(posts)

fmt.Printf("%+v\n", topUsers)
// [{FirstName:Ferguson LastName:Bryant Level:gold Points:9294 FriendCount:3} {FirstName:Ava LastName:Becker Level:silver Points:9797 FriendCount:2} {FirstName:Hahn LastName:Olsen Level:bronze Points:9534 FriendCount:2}]
```

[样例的完整代码](https://github.com/achannarasappa/pneumatic/blob/main/examples/functional-pipeline/main.go2)

从上面的样例中可以看出一些特性：

1.  指令式的实现在 Go 1.16 下是有效的（本文编写时的最新版本），而函数式的实现只在使用 Go 1.18（go2go）编译才有效
2.  函数式例子中的类型参数的泛型函数（如，`Compose3`、`Head` 等）仅 Go 1.18 支持
3.  两个实现在各自对应的风格下，使用了不同的逻辑来解决同样的问题
4.  指令式的实现相比使用及早求值（即本例中的[pneumatic](https://github.com/achannarasappa/pneumatic)）的函数来说，计算更加高效

### 使用 Go 1.18 函数式库的实验

在上面的例子中，两个使用场景使用了 go2go 编译器和一个叫做 [pneumatic](https://github.com/achannarasappa/pneumatic) 的 Go 1.18 库，它提供了与[Ramda](https://ramdajs.com/) (JavaScript), [Elixir 标准库](https://hexdocs.pm/elixir/api-reference.html#content)以及其他相似的常见函数式单元。鉴于 go2go 编译器有限的特性集，在本文发布时 pneumatic 只能用于实验目的，但从长期看，随着 Go 1.18 编译器的逐渐成熟，它会包含常见的函数式 Go 库。设置 pneumatic 和使用 Go 1.18 进行函数式编程的指导参见 [pneumatic readme](https://github.com/achannarasappa/pneumatic/blob/main/README.md)。

## 结论

Go 增加泛型将会支持新型的方案、方法和范式，从而成为众多支持函数式编程的语言之一。随着函数式编程的逐渐流行，函数式编程的支持也会越来越好，从而有机会吸引那些现在还没考虑学习 Go 的开发者并让社区持续发展——这是在我看来比较积极的一面。非常期待看到在后续支持泛型之后和它带来新的解决方法后，Go 社区和生态将会发展成什么样。

## 参考资料

*   Go 函数库调研
    *   [go-funk](https://github.com/thoas/go-funk) \[2.5k stars, type-safe or generic, active\]
    *   [go-underscore](https://github.com/tobyhede/go-underscore) \[1.2k stars, generic, abandoned\]
    *   [gubrak](https://github.com/novalagung/gubrak) \[336 stars, generic, active\]
    *   [fpGo](https://github.com/TeaEntityLab/fpGo) \[167 stars, generic, active\]
    *   [functional-go](https://github.com/logic-building/functional-go) \[92 stars, type-safe, active\]
*   文章
    *   [Go 泛型的过去、现在和将来](https://blog.logrocket.com/past-present-future-go-generics/)
