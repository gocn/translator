# Golang 中高效的错误处理

- 原文地址：https://earthly.dev/blog/golang-errors/
- 原文作者：Brandon Schurman
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w06_effective_error_handling_in_golang.md
- 译者：[Cluas](https://github.com/Cluas)
- 校对：

Go 中的错误处理与其他主流编程语言如 Java、JavaScript 或 Python 有些不同。Go 的内置错误不包含堆栈痕迹，也不支持传统的`try/catch`方法来处理它们。相反，Go 中的错误只是由函数返回的值，它们的处理方式与其他数据类型基本相同 - 这导致了令人惊叹的轻量级和简单设计。

在这篇文章中，我将展示 Go 中处理错误的基础知识，以及一些你可以在代码中遵循的简单策略，以确保你的程序健壮且易于调试。

## 错误类型
Go 中的错误类型是通过以下接口实现的：
```go
type error interface {
    Error() string
}
```
所以基本上，一个`error`是任何实现`Error()`方法的东西，它以字符串形式返回错误信息。就是这么简单！
### 构建错误
错误可以使用 Go 的内置 `errors` 包或 `fmt` 包来即时构建。例如，下面的函数使用 `errors` 包来返回一个带有静态错误信息的新错误：
```go
package main

import "errors"

func DoSomething() error {
    return errors.New("something didn't work")
}
```
同样地，`fmt`包可以用来给错误添加动态数据，比如一个`int`、`string`或其他 `error`。例如：
```go
package main

import "fmt"

func Divide(a, b int) (int, error) {
    if b == 0 {
        return 0, fmt.Errorf("can't divide '%d' by zero", a)
    }
    return a / b, nil
}
```

注意`fmt.Errorf`在用来包装另一个`%w`格式动词的错误时将被证明是非常有用的 - 我将在文章中进一步详细说明。

在上述例子中，还有一些重要的事情需要注意。
- `error`可以以`nil`的形式返回，事实上，它是 Go 中`error`的默认值，或者说 "零值"。这一点很重要，因为检查`if err != nil`是确定是否遇到错误的习惯用法（取代你在其他编程语言中可能熟悉的`try/catch`语句）。
- `error`通常作为一个函数的最后一个参数返回。因此在我们上面的例子中，我们依次返回一个`int`和一个`error`。
- 当我们确实返回一个`error`时，函数返回的其他参数通常会以其默认的 `零值` 返回。一个函数的用户可能期望，如果返回一个非零值的`error`，那么返回的其他参数就没有意义了。
- 最后，错误信息通常以小写字母书写，不以标点符号结束。但也有例外，例如，当包括一个专有名词、一个以大写字母开头的函数名称等。

### 定义预期的错误
Go 中另一个重要的技术是定义预期错误，这样就可以在代码的其他部分明确地检查这些错误。当你需要在遇到某种错误时执行不同的代码分支时，这就非常有用。

#### 定义哨兵错误
在前面的`Divide`函数的基础上，我们可以通过预先定义一个 "哨兵" 错误改进错误提示。调用函数可以使用`errors.Is`明确地检查这个`error`：
```go
package main

import (
    "errors"
    "fmt"
)

var ErrDivideByZero = errors.New("divide by zero")

func Divide(a, b int) (int, error) {
    if b == 0 {
        return 0, ErrDivideByZero
    }
    return a / b, nil
}

func main() {
    a, b := 10, 0
    result, err := Divide(a, b)
    if err != nil {
        switch {
        case errors.Is(err, ErrDivideByZero):
            fmt.Println("divide by zero error")
        default:
            fmt.Printf("unexpected division error: %s\n", err)
        }
        return
    }

    fmt.Printf("%d / %d = %d\n", a, b, result)
}
```
#### 定义自定义错误类型

大多数错误处理的用例都可以用上面的策略来覆盖，然而，有时你可能需要一些额外的功能。也许你想让一个`error`携带额外的数据字段，或者当错误信息被打印出来时，能用动态值来填充自己。

你可以在 Go 中通过实现自定义错误类型来做到这一点。

下面是对以前的例子的轻微改造。注意新的类型`DivisionError`，它实现了`Error`接口。我们可以利用`errors.As`来检查并从标准`error`转换到我们更具体的`DivisionError`。
```go
package main

import (
    "errors"
    "fmt"
)

type DivisionError struct {
    IntA int
    IntB int
    Msg  string
}

func (e *DivisionError) Error() string { 
    return e.Msg
}

func Divide(a, b int) (int, error) {
    if b == 0 {
        return 0, &DivisionError{
            Msg: fmt.Sprintf("cannot divide '%d' by zero", a),
            IntA: a, IntB: b,
        }
    }
    return a / b, nil
}

func main() {
    a, b := 10, 0
    result, err := Divide(a, b)
    if err != nil {
        var divErr *DivisionError
        switch {
        case errors.As(err, &divErr):
            fmt.Printf("%d / %d is not mathematically valid: %s\n",
              divErr.IntA, divErr.IntB, divErr.Error())
        default:
            fmt.Printf("unexpected division error: %s\n", err)
        }
        return
    }

    fmt.Printf("%d / %d = %d\n", a, b, result)
}
```
>注意：必要时，你也可以自定义`errors.Is`和`errors.As`的行为。请看[这个 Go.dev 博客](https://go.dev/blog/go1.13-errors)的一个例子。


>另一个说明：`errors.Is`是在 Go 1.13 中添加的，比检查`err == ...`更可取。下面有更多关于这个问题的内容。

## 包装错误
在迄今为止的这些例子中，`error`都是通过一个函数调用来创建、返回和处理的。换句话说，参与 "冒泡" `error`的函数堆栈只有一层深度。

通常在现实世界的程序中，可能会有更多的函数参与其中 -- 从产生`error`的函数，到最终处理`error`的地方，以及中间的任何数量的附加函数。

在 Go 1.13 中，引入了几个新的`errors` API，包括`errors.Wrap`和`errors.Unwrap`，它们在`error` "冒泡" 时对其应用额外的上下文，以及检查特定的`error`类型，不管一个`error`被包裹了多少次。

>***一段历史***: 在 2019 年 Go 1.13 发布之前，标准库并不包含很多处理错误的 API--基本上只有`errors.New`和`fmt.Errorf`。因此，你可能会在别的包里遇到没有实现一些较新错误 API 的遗留 Go 程序。 许多遗留程序也使用第三方错误库，如 [pkg/errors](https://github.com/pkg/errors)。 最后，[正式提案](https://go.googlesource.com/proposal/+/master/design/go2draft-error-inspection.md)在 2018 年被记录下来，其中提出了许多我们今天在 Go 1.13+ 中看到的功能。
### 旧的方式（Go 1.13 之前）
通过看一些旧的 API 有局限性的例子，对比一下就很容易看出 Go 1.13+ 中新的错误 API 多么有用。

让我们考虑一个管理用户数据库的简单程序。在这个程序中，我们将有几个函数参与到数据库错误的生命周期中。

为了简单起见，让我们用一个完全 "假" 的数据库来代替真正的数据库，我们从`"example.com/fake/users/db"`导入。

我们还假设这个假数据库已经包含了一些查找和更新用户记录的功能。而且，用户记录被定义为一个结构体，看起来像：

```go
package db

type User struct {
  ID       string
  Username string
  Age      int
}

func FindUser(username string) (*User, error) { /* ... */ }
func SetUserAge(user *User, age int) error { /* ... */ }
```

下面是我们的示例程序：

```go
package main

import (
    "errors"
    "fmt"

    "example.com/fake/users/db"
)

func FindUser(username string) (*db.User, error) {
    return db.Find(username)
}

func SetUserAge(u *db.User, age int) error {
    return db.SetAge(u, age)
}

func FindAndSetUserAge(username string, age int) error {
  var user *User
  var err error

  user, err = FindUser(username)
  if err != nil {
      return err
  }

  if err = SetUserAge(user, age); err != nil {
      return err
  }

  return nil
}

func main() {
    if err := FindAndSetUserAge("bob@example.com", 21); err != nil {
        fmt.Println("failed finding or updating user: %s", err)
        return
    }

    fmt.Println("successfully updated user's age")
}
```

现在，如果我们的一个数据库操作因为一些 `malformed request` (错误的请求) 而失败，会发生什么？

在`main`函数中的错误检查应该捕获它，并打印出类似这样的东西：
```bash
failed finding or updating user: malformed request
```

但这两个数据库操作中的哪一个产生了错误？不幸的是，我们的错误日志中没有足够的信息来知道它是来自`FindUser`还是`SetUserAge`。

Go 1.13 增加了一个简单的方法来添加这些信息。

### 错误更好地被包装起来
下面的代码段经过重构，使用`fmt.Errorf`和`%w`动词来 "包装" 错误，因为它们通过其他函数调用 "冒泡" 了。这增加了所需的上下文，从而有可能推断出在前面的例子中哪些数据库操作失败了。
```go
package main

import (
    "errors"
    "fmt"

    "example.com/fake/users/db"
)

func FindUser(username string) (*db.User, error) {
    u, err := db.Find(username)
    if err != nil {
        return nil, fmt.Errorf("FindUser: failed executing db query: %w", err)
    }
    return u, nil
}

func SetUserAge(u *db.User, age int) error {
    if err := db.SetAge(u, age); err != nil {
      return fmt.Errorf("SetUserAge: failed executing db update: %w", err)
    }
}

func FindAndSetUserAge(username string, age int) error {
  var user *User
  var err error

  user, err = FindUser(username)
  if err != nil {
      return fmt.Errorf("FindAndSetUserAge: %w", err)
  }

  if err = SetUserAge(user, age); err != nil {
      return fmt.Errorf("FindAndSetUserAge: %w", err)
  }

  return nil
}

func main() {
    if err := FindAndSetUserAge("bob@example.com", 21); err != nil {
        fmt.Println("failed finding or updating user: %s", err)
        return
    }

    fmt.Println("successfully updated user's age")
}
```

如果我们重新运行程序并遇到同样的错误，日志应该打印如下：
```bash
failed finding or updating user: FindAndSetUserAge: SetUserAge: failed executing db update: malformed request
```

现在我们的错误消息包含了足够的信息，我们可以看到问题起源于`db.SetUserAge`函数。咻！这无疑为我们节省了一些调试的时间！

如果使用得当，错误包装可以提供关于错误脉络的额外内容，其方式类似于传统的堆栈跟踪。

包装也保留了原始错误，这意味着`errors.Is`和`errors.As`同样有效，不管一个错误被封装了多少次。我们还可以调用`errors.Unwrap`来返回错误链中的前一个错误。

>好奇地想知道错误包装是如何工作的？看看 [fmt.Errorf](https://github.com/golang/go/blob/release-branch.go1.17/src/fmt/errors.go#L26), [%w 动词，](https://github.com/golang/go/blob/release-branch.go1.17/src/fmt/print.go#L574) 和 [错误 API](https://github.com/golang/go/blob/release-branch.go1.17/src/errors/wrap.go)的内部细节吧。

#### 何时包装
一般来说，在每次 "冒泡" 时，即每次从一个函数中收到错误并想继续将其返回到函数链中时，至少用函数的名称来包裹错误是个好主意。

[Wrapping an error adds the gift of context]: ../static/images/2022/w06_golang_errors/wrap.jpeg
![Wrapping an error adds the gift of context][Wrapping an error adds the gift of context]
<center style="font-size:14px;color:#C0C0C0;text-decoration">Wrapping an error adds the gift of context</center> 


然而，也有一些例外情况，在这种情况下，包装错误可能是不合适的。

由于包装错误总是保留原始的错误信息，有时暴露这些潜在的问题可能是一个安全、隐私，甚至是用户体验的问题。在这种情况下，可能值得处理错误并返回一个新的错误，而不是包装它。如果你正在编写一个开源库或 REST API，不希望将底层错误信息返回给第三方用户，就可能是这种情况。



## 结论
这是个总结！综上所述，这就是这里所涉及的主要内容：
- Go 中的错误只是一些轻量级的值，实现了`Error`的`interface`
- 预定义的错误将改善信号，允许我们检查是哪个错误发生了
- 包装错误以增加足够的上下文来跟踪函数调用（类似于堆栈跟踪）

我希望你觉得这个有效的错误处理指南很有用。如果你想了解更多，我附上了一些相关的文章，这些文章是我在 Go 中进行强大错误处理的过程中发现的。

## 参考文献

- [Error handling and Go](https://go.dev/blog/error-handling-and-go)
- [Go 1.13 Errors](https://go.dev/blog/go1.13-errors)
- [Go Error Doc](https://pkg.go.dev/errors@go1.17.5)
- [Go By Example: Errors](https://gobyexample.com/errors)
- [Go By Example: Panic](https://gobyexample.com/errors)

