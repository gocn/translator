GO 1.20 新功能：多重错误包装

- 原文地址：https://lukas.zapletalovi.com/posts/2022/wrapping-multiple-errors/
- 原文作者：Lukáš Zapletal
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w50_Wrapping_multiple_errors
- 译者：[haoheipi](https://github.com/haoheipi)
- 校对：[watermelo](https://github.com/watermelo)

预计将于 2023 年 2 月发布的 Go 1.20 有一个小的变化，对于那些大量使用错误包装的应用程序来说，可能会有效的改进它们的错误处理方法。让我们看一下它的用法，但首先，需要简要回顾一下什么是错误包装。如果已经掌握了可以直接跳到下面的 "Go 1.20 新功能" 部分以获取新的信息。

Go 中的错误是实现一个非常简单的接口：

```
type error interface {
    Error() string
}
```

错误类型可以是任何东西，从 `string` 本身到 `int`，但通常它们是 `struct` 类型。下面这个例子来自标准库：

```
type err struct {
    s string
}

func (e *err) Error() string {
    return e.s
}
```

要检查 Go 中的错误，你只需比较一个值（在本例中为 `int` 值）：

```
if err == io.EOF {
    // ...
}
```

第二种常见的用法是检查错误的类型，那也意味着要写更多的代码：

```
if nerr, ok := err.(net.Error) {
    // ... (use nerr which is a net.Error)
}
```

在上面的例子中，类型断言测试类型 `net.Error` 的 `err` 值，并创建一个新变量 `nerr` ，它可以在 if 语句中使用。 Go 中的错误易于理解、易于使用且非常高效。

## 错误包装

从 Go 1.13 开始，引入了错误包装。包装允许将错误嵌入到其他错误中，就像在其他语言中包装异常一样。这非常实用：比如函数遇到 "record not found" 错误时，可以向错误信息中添加更多上下文信息，例如 "unknown user: record not found"。

Go 中错误包装设计背后的有趣想法是，契约不用关心错误类型、结构或它们是如何创建的。而唯一关注的是解包过程和转换为字符串，因为这两者是必须的。这就非常容易实现：支持解包的错误类型必须实现 `Unwrap() error` 方法。标准库中没有（命名的）接口可以向您展示，因为接口是隐式实现的，没有必要单独写一个。这里我们写一个只是为了更好说明这篇文章：

```
type WrappedError interface {
    Unwrap() error
}
```

我们来看看 Go 标准库（实际上是 package fmt）中是如何实现包装错误的：

```
type wrapError struct {
    msg string
    err error
}

func (e *wrapError) Error() string {
    return e.msg
}

func (e *wrapError) Unwrap() error {
    return e.err
}
```

由于上面错误类型实现了 `Error() string` 方法，所以说 Go 中的错误实际上最终是 `字符串` 并没有错，因此需要一种创建这些字符串的良好机制。这就是标准库中的函数 `fmt.Errorf` 发挥作用的地方：

```
var RecordNotFoundErr = errors.New("not found")
const name, id = "lzap", 13

werr := fmt.Errorf("unknown user %q (id %d): %w", name, id, recordNotFoundErr)

fmt.Println(werr.Error())
```

一个特殊格式的动词 `%w`，每次调用只能使用一次（稍后会详细介绍），用于错误参数。除此之外，该函数的工作方式类似于 `fmt.Printf` 函数。上面的例子打印了这个结果：

```
unknown user "lzap" (id 13): not found
```

如你所见，错误包装本质上是一个链表。要解包错误，请使用 `errors.Unwrap` 函数，该函数将为链表中的最后一个错误值返回 `nil`。要检查错误类型或值，需要遍历整个列表，这对于需要进行频繁的错误检查不太实用。幸运的是，有两个辅助函数可以做到这一点。

检查包装错误列表中的值：

```
if errors.Is(err, RecordNotFoundErr) {
    // ...
}
```

要检查特定类型（下面例子是来自标准库的网络错误）:

```
var nerr *net.Error
if errors.As(err, &nerr) {
    // ... (use nerr which is a *net.Error)
}
```

以上总结了 Go 1.13 及更高版本中的错误包装。

## Go 1.20 新特性

让我们看看 Go 1.20 中真正的新功能，从函数 `errors.Join` 开始，它通过可变参数包装错误列表：

```
err1 := errors.New("err1")
err2 := errors.New("err2")

err := errors.Join(err1, err2)

fmt.Println(err)
```

当事先不知道错误数量时，此功能可用于将错误连接在一起。一个很好的例子是从 goroutines 收集错误。值得一提的是，该函数将列表中的错误与换行符连接起来。上面的代码片段打印：

```
err1
err2
```

对于许多应用程序或（日志记录）库来说，这可能会存在问题，它们期望错误通常只是没有换行符的字符串。幸运的是，Go 1.20 中的另一个变化改变了 `fmt.Errorf` 的行为：该函数现在接受多个 `%w` 格式说明符：

```
err1 := errors.New("err1")
err2 := errors.New("err2")

err := fmt.Errorf("%w + %w", err1, err2)

fmt.Println(err)
```

以前会导致格式错误的格式字符串现在可以正确打印：

```
err1 + err2
```

同时包装多个错误实现 `Unwrap() error` ，这是可能的吗? 事实证明，在 Go 1.20 标准库中有一种新的机制: 实现 `Unwrap() []error` 函数的错误类型可以包装多个错误。让我们来看看这是如何在库中实现的:

```
type joinError struct {
    errs []error
}

func (e *joinError) Error() string {
    // concatenate errors with a new line character
}

func (e *joinError) Unwrap() []error {
    return e.errs
}
```

一个理论上的接口，但标准库中实际不存在，如下所示：

```
type MultiWrappedError interface {
    Unwrap() []error
}
```

由于 Go 不允许方法重载，因此每种类型都可以实现 `Unwrap() error` 或 `Unwrap() []error`，但不能同时实现。还记得我提到过包装错误本质上是一个链表吗？实现前一个（新引入的）方法的类型实际上形成了一个链接树，函数 `errors.Is` 和 `errors.As` 的工作方式相同，只是现在它们需要遍历树而不是列表。根据文档，该实现执行预排序、深度优先遍历。

这确实是 Go 1.20 带来的全部，它可能看起来是一个小的变化，但它提供了如何有效和干净地处理错误的新方法。在展示真实示例之前，让我总结一下新功能：

- 新的 `Unwrap []error` 函数契约允许遍历错误树。
- 新的 `errors.Join` 函数，这是一个方便的函数，用于连接两个错误字符串值（使用换行符）。
- 现有函数 `errors.Is` 和 `errors.As` 已更新，可以同时处理错误列表和错误树。
- 现有函数 `fmt.Errorf` 现在接受多个 `%w` 格式动词。

## 实践

上面这一切都很棒，但是你如何在实践中利用它呢？在一个小型 REST API 微服务中，我们通过 `errors.New` 和 `fmt.Errorf` 处理来自 DAO 包（数据库）、REST 客户端（其他后端服务）和其他包的各种错误。返回的 HTTP 状态代码应该是 2xx、4xx 或 5xx，具体取决于错误状态以遵循最佳 REST API 实践。实现此过程的一种方法是解开主 HTTP 处理程序中的错误并找出它是哪种错误。

然而，通过多重错误包装，现在可以包装根本原因（例如数据库返回 "no records found" ）和返回给用户 HTTP 代码（在本例中为 404）。一个工作示例可能如下所示：

```
package main

import (
	"errors"
	"fmt"
)

// common HTTP status codes
var NotFoundHTTPCode = errors.New("404")
var UnauthorizedHTTPCode = errors.New("401")

// database errors
var RecordNotFoundErr = errors.New("DB: record not found")
var AffectedRecordsMismatchErr = errors.New("DB: affected records mismatch")

// HTTP client errors
var ResourceNotFoundErr = errors.New("HTTP client: resource not found")
var ResourceUnauthorizedErr = errors.New("HTTP client: unauthorized")

// application errors (the new feature)
var UserNotFoundErr = fmt.Errorf("user not found: %w (%w)",
    RecordNotFoundErr, NotFoundHTTPCode)
var OtherResourceUnauthorizedErr = fmt.Errorf("unauthorized call: %w (%w)",
    ResourceUnauthorizedErr, UnauthorizedHTTPCode)

func handleError(err error) {
	if errors.Is(err, NotFoundHTTPCode) {
		fmt.Println("Will return 404")
	} else if errors.Is(err, UnauthorizedHTTPCode) {
		fmt.Println("Will return 401")
	} else {
		fmt.Println("Will return 500")
	}
	fmt.Println(err.Error())
}

func main() {
	handleError(UserNotFoundErr)
	handleError(OtherResourceUnauthorizedErr)
}
```

这将打印：

```
Will return 404
user not found: DB: record not found (404)
Will return 401
unauthorized to call other service: HTTP client: unauthorized (401)
```

从这样的人工代码片段中可能看起来不太明显的是，实际上的错误声明通常分布在许多包中，并且不容易跟踪所有可能的错误以确保所需的 HTTP 状态代码。在这种方法中，所有在一个地方声明的应用程序级包装错误也包含了 HTTP 代码。

请注意，这在 Go 1.19 或更早版本中是不可能的，因为 `fmt.Errorf` 函数只会包装第一个错误。该代码确实在 1.19 上可以编译，甚至不会产生运行时恐慌，但它实际上不会工作。

显然，常见的 HTTP 状态代码很容易成为一种新的错误类型（基于 `int` 类型），因此可以通过 `errors.As` 轻松提取实际代码，但我想让示例保持简单。

Feel free to play around with the code on Go Playground. Make sure to use “dev branch” or 1.20+ version of Go.
可以在 Go Playground 上自由运行上述代码。确保使用 "dev branch" 或 Go 的 1.20+ 版本。

## 现有应用

在你的应用程序中实施新功能时，请注意 `errors.Unwrap` 函数。对于具有 `Unwrap() []error` 的错误类型，它总是返回 `nil`：

```
err1 := errors.New("err1")
err2 := errors.New("err2")

err := errors.Join(err1, err2)
unwrapped := errors.Unwrap(err)

fmt.Println(unwrapped)
```

由于 Go 1.X 兼容性承诺，这会打印出 "nil"。当你引入多个包装错误时，请确保检查展开代码。幸运的是，典型 Go 代码中的大部分错误检查都是使用 `errors.Is` 和 `errors.As` 完成的。

错误包装并不是 Go 中所有错误处理的最终解决方案。它只是提供了一种干净的方法来处理典型 Go 应用程序中的错误，对于简单应用程序来说也许就完全足够了。
