## Go 编程风格指南 - 最佳实践

https://google.github.io/styleguide/go/best-practices

[概述](https://google.github.io/styleguide/go/index) | [指南](https://google.github.io/styleguide/go/guide) | [决策](https://google.github.io/styleguide/go/decisions) | [最佳实践](https://google.github.io/styleguide/go/best-practices)

**注意：**本文是 Google [Go 风格](https://google.github.io/styleguide/go/index) 系列文档的一部分。本文档是 **[规范性(normative)](https://google.github.io/styleguide/go/index#normative) 但不是[强制规范(canonical)](https://google.github.io/styleguide/go/index#canonical )**，并且从属于[Google 风格指南](https://google.github.io/styleguide/go/guide)。请参阅[概述](https://google.github.io/styleguide/go/index#about)获取更多详细信息。

## 关于

本文件记录了**关于如何更好地应用 Go 风格指南的指导意见**。该指导旨在解决经常出现的通用问题，但不一定适用于所有情况。在可能的情况下，我们讨论了多种替代方法，以及决定何时该用和何时不该用这些方法的考虑因素。

查看[概述](https://google.github.io/styleguide/go/index#about)来获取完整的风格指导文档

## 命名

### 函数和方法名称

#### 避免重复

在为一个函数或方法选择名称时，要考虑该名称将被阅读的环境。请考虑以下建议，以避免在调用地点出现过多的[重复](https://google.github.io/styleguide/go/decisions#repetition):

- 以下内容一般可以从函数和方法名称中省略。

  - 输入和输出的类型（当没有冲突的时候）
  - 方法的接收器的类型
  - 一个输入或输出是否是一个指针

- 对于函数，不要[重复软件包的名称](https://google.github.io/styleguide/go/decisions#repetitive-with-package)。

  ```go
  // Bad:
  package yamlconfig
  
  func ParseYAMLConfig(input string) (*Config, error)
  ```

  ```go
  // Good:
  package yamlconfig
  
  func Parse(input string) (*Config, error)
  ```

- 对于方法不要重复方法接收器的名称。

  ```go
  // Bad:
  func (c *Config) WriteConfigTo(w io.Writer) (int64, error)
  ```

  ```go
  // Good:
  func (c *Config) WriteTo(w io.Writer) (int64, error)
  ```

-  不要重复传参的变量名称

  ```go
  // Bad:
  func OverrideFirstWithSecond(dest, source *Config) error
  ```

  ```go
  // Good:
  func Override(dest, source *Config) error
  ```

- 不要重复返回值的名称和类型

  ```go
  // Bad:
  func TransformYAMLToJSON(input *Config) *jsonconfig.Config
  ```

  ```go
  // Good:
  func Transform(input *Config) *jsonconfig.Config
  ```


当有必要区分类似名称的函数时，包含额外信息是可以接受的。

```go
// Good:
func (c *Config) WriteTextTo(w io.Writer) (int64, error)
func (c *Config) WriteBinaryTo(w io.Writer) (int64, error)
```

#### [命名约定](https://google.github.io/styleguide/go/best-practices#naming-conventions)

在为函数和方法选择名称时，还有一些常见的约定：

- 有返回结果的函数使用类名词的名称。

  ```
  // Good:
  func (c *Config) JobName(key string) (value string, ok bool)
  ```

  这方面的一个推论是，函数和方法名称应该[避免使用前缀`Get`](https://google.github.io/styleguide/go/decisions#getters)。

  ```
  // Bad:
  func (c *Config) GetJobName(key string) (value string, ok bool)
  ```

- 做事的函数被赋予类似动词的名称。

  ```
  // Good:
  func (c *Config) WriteDetail(w io.Writer) (int64, error)
  ```

- 只因所涉及的类型而不同，而功能相同的函数在名称的末尾带上类型的名称。

  ```
  // Good:
  func ParseInt(input string) (int, error)
  func ParseInt64(input string) (int64, error)
  func AppendInt(buf []byte, value int) []byte
  func AppendInt64(buf []byte, value int64) []byte
  ```

  如果有一个明确的 "主要 "版本，该版本的名称中可以省略类型：

  ```
  // Good:
  func (c *Config) Marshal() ([]byte, error)
  func (c *Config) MarshalText() (string, error)
  ```


### 测试替身包和类型

有几个原则你可以应用于[命名](https://google.github.io/styleguide/go/guide#naming)包和类型，提供测试辅助函数，特别是[测试替身](https://en.wikipedia.org/wiki/Test_double)。一个测试替身可以是一个桩、假的、模拟的或间谍的。
这些例子大多使用打桩。如果你的代码使用假的或其他类型的测试替身，请相应地更新你的名字。
假设你有一个重点突出的包，提供与此类似的生产代码：

```go
package creditcard

import (
    "errors"

    "path/to/money"
)

// ErrDeclined indicates that the issuer declines the charge.
var ErrDeclined = errors.New("creditcard: declined")

// Card contains information about a credit card, such as its issuer,
// expiration, and limit.
type Card struct {
    // omitted
}

// Service allows you to perform operations with credit cards against external
// payment processor vendors like charge, authorize, reimburse, and subscribe.
type Service struct {
    // omitted
}

func (s *Service) Charge(c *Card, amount money.Money) error { /* omitted */ }
```

#### 创建测试辅助包

假设你想创建一个包，包含另一个包的测试替身。在这个例子中我们将使用`package creditcard`（来自上面）。
一种方法是在生产包的基础上引入一个新的 Go 包进行测试。一个安全的选择是在原来的包名后面加上`test`这个词（"creditcard" + "test"）。

```
// Good:
package creditcardtest
```

除非另有明确说明，以下各节中的所有例子都在 `package creditcardtest` 中。

#### 简单案例

你想为`Service`添加一组测试替身。因为`Card`是一个有效的哑巴数据类型，类似于协议缓冲区的消息，它在测试中不需要特殊处理，所以不需要替身。如果你预计只有一种类型（如`Service'）的测试替身，你可以采取一种简洁的方法来命名替身。

```go
// Good:
import (
    "path/to/creditcard"
    "path/to/money"
)

// Stub stubs creditcard.Service and provides no behavior of its own.
type Stub struct{}

func (Stub) Charge(*creditcard.Card, money.Money) error { return nil }
```

严格来说，这比像 `StubService` 或非常差的 `StubCreditCardService` 这样的命名选择要好，因为基础包的名字和它的域类型意味着 `creditcardtest.Stub` 是什么。
最后，如果该包是用 Bazel 构建的，确保该包的新 `go_library` 规则被标记为 `testonly`。

```go
# Good:
go_library(
    name = "creditcardtest",
    srcs = ["creditcardtest.go"],
    deps = [
        ":creditcard",
        ":money",
    ],
    testonly = True,
)
```

上述方法是常规的，其他工程师也会很容易理解。

另见:

-   [Go Tip #42: 为测试便编写桩](https://google.github.io/styleguide/go/index.html#gotip)

#### 多重测试替身行为

当一种桩不够用时（例如，你还需要一种总是失败的桩），我们建议根据它们所模拟的行为来命名桩。这里我们把`Stub`改名为`AlwaysCharges`，并引入一个新的桩，叫做`AlwaysDeclines`：

```go
// Good:
// AlwaysCharges stubs creditcard.Service and simulates success.
type AlwaysCharges struct{}

func (AlwaysCharges) Charge(*creditcard.Card, money.Money) error { return nil }

// AlwaysDeclines stubs creditcard.Service and simulates declined charges.
type AlwaysDeclines struct{}

func (AlwaysDeclines) Charge(*creditcard.Card, money.Money) error {
    return creditcard.ErrDeclined
}
```

#### 多种类型的多重替身

但现在假设 `package creditcard` 包含多个值得创建替身的类型，如下面的 `Service` 和 `StoredValue` ：

```go
package creditcard

type Service struct {
    // omitted
}

type Card struct {
    // omitted
}

// StoredValue manages customer credit balances.  This applies when returned
// merchandise is credited to a customer's local account instead of processed
// by the credit issuer.  For this reason, it is implemented as a separate
// service.
type StoredValue struct {
    // omitted
}

func (s *StoredValue) Credit(c *Card, amount money.Money) error { /* omitted */ }
```

In this case, more explicit test double naming is sensible:

在这种情况下，更明确的测试替身命名是明智的：

```go
// Good:
type StubService struct{}

func (StubService) Charge(*creditcard.Card, money.Money) error { return nil }

type StubStoredValue struct{}

func (StubStoredValue) Credit(*creditcard.Card, money.Money) error { return nil }
```

#### 测试中的局部变量

当你的测试中的变量引用替身时，要根据上下文选择一个能最清楚地区分替身和其他生产类型的名称。考虑一下你要测试的一些生产代码：

```go
package payment

import (
    "path/to/creditcard"
    "path/to/money"
)

type CreditCard interface {
    Charge(*creditcard.Card, money.Money) error
}

type Processor struct {
    CC CreditCard
}

var ErrBadInstrument = errors.New("payment: instrument is invalid or expired")

func (p *Processor) Process(c *creditcard.Card, amount money.Money) error {
    if c.Expired() {
        return ErrBadInstrument
    }
    return p.CC.Charge(c, amount)
}
```

在测试中，一个被称为 "间谍 "的 `CreditCard` 的测试替身与生产类型并列，所以给名字加前缀可以提高清晰度。

```go
// Good:
package payment

import "path/to/creditcardtest"

func TestProcessor(t *testing.T) {
    var spyCC creditcardtest.Spy

    proc := &Processor{CC: spyCC}

    // declarations omitted: card and amount
    if err := proc.Process(card, amount); err != nil {
        t.Errorf("proc.Process(card, amount) = %v, want %v", got, want)
    }

    charges := []creditcardtest.Charge{
        {Card: card, Amount: amount},
    }

    if got, want := spyCC.Charges, charges; !cmp.Equal(got, want) {
        t.Errorf("spyCC.Charges = %v, want %v", got, want)
    }
}
```

这比没有前缀的名字更清楚。

```go
// Bad:
package payment

import "path/to/creditcardtest"

func TestProcessor(t *testing.T) {
    var cc creditcardtest.Spy

    proc := &Processor{CC: cc}

    // declarations omitted: card and amount
    if err := proc.Process(card, amount); err != nil {
        t.Errorf("proc.Process(card, amount) = %v, want %v", got, want)
    }

    charges := []creditcardtest.Charge{
        {Card: card, Amount: amount},
    }

    if got, want := cc.Charges, charges; !cmp.Equal(got, want) {
        t.Errorf("cc.Charges = %v, want %v", got, want)
    }
}
```

### 阴影

**注意：**本解释使用了两个非正式的术语，_stomping_ 和 _shadowing_。它们不是 Go 语言规范中的正式概念。
像许多编程语言一样，Go 有可变的变量：对一个变量的赋值会改变其值。

```go
// Good:
func abs(i int) int {
    if i < 0 {
        i *= -1
    }
    return i
}
```

当使用[短变量声明](https://go.dev/ref/spec#Short_variable_declarations)与 `:=` 操作符时，在某些情况下不会创建一个新的变量。我们可以把这称为 _stomping_。当不再需要原来的值时，这样做是可以的。

```go
// Good:
// innerHandler is a helper for some request handler, which itself issues
// requests to other backends.
func (s *Server) innerHandler(ctx context.Context, req *pb.MyRequest) *pb.MyResponse {
    // Unconditionally cap the deadline for this part of request handling.
    ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
    defer cancel()
    ctxlog.Info("Capped deadline in inner request")

    // Code here no longer has access to the original context.
    // This is good style if when first writing this, you anticipate
    // that even as the code grows, no operation legitimately should
    // use the (possibly unbounded) original context that the caller provided.

    // ...
}
```

不过要小心在新的作用域中使用短的变量声明 `：` 这将引入一个新的变量。我们可以把这称为对原始变量的 "阴影"。块结束后的代码指的是原来的。这里是一个有条件缩短期限的错误尝试:

```go
// Bad:
func (s *Server) innerHandler(ctx context.Context, req *pb.MyRequest) *pb.MyResponse {
    // Attempt to conditionally cap the deadline.
    if *shortenDeadlines {
        ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
        defer cancel()
        ctxlog.Info(ctx, "Capped deadline in inner request")
    }

    // BUG: "ctx" here again means the context that the caller provided.
    // The above buggy code compiled because both ctx and cancel
    // were used inside the if statement.

    // ...
}
```

正确版本的代码应该是：

```go
// Good:
func (s *Server) innerHandler(ctx context.Context, req *pb.MyRequest) *pb.MyResponse {
    if *shortenDeadlines {
        var cancel func()
        // Note the use of simple assignment, = and not :=.
        ctx, cancel = context.WithTimeout(ctx, 3*time.Second)
        defer cancel()
        ctxlog.Info(ctx, "Capped deadline in inner request")
    }
    // ...
}
```

在我们称之为 stomping 的情况下，因为没有新的变量，所以被分配的类型必须与原始变量的类型相匹配。有了 shadowing，一个全新的实体被引入，所以它可以有不同的类型。有意的影子可以是一种有用的做法，但如果能提高[清晰度](https://google.github.io/styleguide/go/guide#clarity)，你总是可以使用一个新的名字。

除了非常小的范围之外，使用与标准包同名的变量并不是一个好主意，因为这使得该包的自由函数和值无法访问。相反，当为你的包挑选名字时，要避免使用那些可能需要[导入重命名](https://google.github.io/styleguide/go/decisions#import-renaming)或在客户端造成阴影的其他好的变量名称。

```go
// Bad:
func LongFunction() {
    url := "https://example.com/"
    // Oops, now we can't use net/url in code below.
}
```

### 工具包

Go 包在 `package` 声明中指定了一个名称，与导入路径分开。包的名称比路径更重要，因为它的可读性。

Go 包的名字应该是[与包所提供的内容相关](https://google.github.io/styleguide/go/decisions#package-names)。将包命名为 `util`、`helper`、`common` 或类似的名字通常是一个糟糕的选择（但它可以作为名字的一部分）。没有信息的名字会使代码更难读，而且如果使用的范围太广，很容易造成不必要的[导入冲突](https://google.github.io/styleguide/go/decisions#import-renaming)。

相反，考虑一下调用站会是什么样子。

```go
// Good:
db := spannertest.NewDatabaseFromFile(...)

_, err := f.Seek(0, io.SeekStart)

b := elliptic.Marshal(curve, x, y)
```

即使不知道导入列表，你也能大致知道这些东西的作用（`cloud.google.com/go/spanner/spannertest`，`io`，和`crypto/elliptic`）。如果名称不那么集中，这些可能是：

```go
// Bad:
db := test.NewDatabaseFromFile(...)

_, err := f.Seek(0, common.SeekStart)

b := helper.Marshal(curve, x, y)
```

## 包大小

如果你在问自己，你的 Go 包应该有多大，是把相关的类型放在同一个包里，还是把它们分成不同的包，可以从[关于包名的 Go 博文](https://go.dev/blog/package-names)开始。尽管帖子的标题是这样的，但它并不仅仅是关于命名的。它包含了一些有用的提示并引用了一些有用的文章和讲座。

这里有一些其他的考虑和说明。

用户在一页中看到包的 [godoc](https://pkg.go.dev/)，任何由包提供的类型导出的方法都按其类型分组。Godoc 还将构造函数与它们返回的类型一起分组。如果_客户端代码_可能需要两个不同类型的值来相互作用，那么把它们放在同一个包里对用户来说可能很方便。

包内的代码可以访问包内未导出的标识符。如果你有几个相关的类型，它们的_实现_是紧密耦合的，把它们放在同一个包里可以让你实现这种耦合，而无需用这些细节污染公共 API。

综上所述，把你的整个项目放在一个包里可能会使这个包变得太大。当一个东西在概念上是不同的，给它一个自己的小包可以使它更容易使用。客户端所知道的包的短名称和导出的类型名称一起构成了一个有意义的标识符：例如`bytes.Buffer`, `ring.New`。[博文](https://go.dev/blog/package-names)有更多的例子。

Go 风格在文件大小方面很灵活，因为维护者可以将包内的代码从一个文件移到另一个文件而不影响调用者。但作为一般准则：通常情况下，一个文件有几千行，或者有许多小文件，都不是一个好主意。没有像其他一些语言那样的 "一个类型，一个文件 "的约定。作为一个经验法则，文件应该足够集中，以便维护者可以知道哪个文件包含了什么东西，而且文件应该足够小，以便一旦有了这些东西，就很容易找到。标准库经常将大型包分割成几个源文件，将相关的代码按文件分组。[`bytes` 包](https://go.dev/src/bytes/) 的源代码就是一个很好的例子。有很长包文档的包可以选择专门的一个文件，称为`doc.go`，其中有[包文档](https://google.github.io/styleguide/go/decisions#package-comments)，包声明，而没有其他内容，但这不是必须的。

在 Google 代码库和使用 Bazel 的项目中，Go 代码的目录布局与开源 Go 项目不同：你可以在一个目录中拥有多个`go_library`目标。如果你期望在未来将你的项目开源，那么给每个包提供自己的目录是一个很好的理由。

另见：

-   [测试替身包](https://google.github.io/styleguide/go/best-practices#naming-doubles)

## 导入

### Protos and stubs

由于其跨语言的特性，Proto 库导入的处理方式与标准 Go 导入不同。重命名的 proto 导入的约定是基于生成包的规则：

-   `pb`后缀一般用于 `go_proto_library` 规则。
-   `grpc`后缀一般用于 `go_grpc_library` 规则。

一般来说，使用简短的一个或两个字母的前缀：

```go
// Good:
import (
    fspb "path/to/package/foo_service_go_proto"
    fsgrpc "path/to/package/foo_service_go_grpc"
)
```

如果一个包只使用一个 proto，或者该包与该 proto 紧密相连，那么前缀可以省略：

import ( pb “path/to/package/foo\_service\_go\_proto” grpc “path/to/package/foo\_service\_go\_grpc” )

如果 proto 中的符号是通用的，或者没有很好的自我描述，或者用首字母缩写来缩短包的名称是不明确的，那么一个简短的词就可以作为前缀：

```go
// Good:
import (
    mapspb "path/to/package/maps_go_proto"
)
```

在这种情况下，如果有关的代码还没有明确与地图相关，那么 `mapspb.Address` 可能比 `mpb.Address` 更清楚。

### 导入顺序

导入通常按顺序分为以下两（或更多）块。

1. 标准库导入（例如，`"fmt"`）。
2. 导入（例如，"/path/to/somelib"）。
3. （可选）Protobuf 导入（例如，`fpb "path/to/foo_go_proto"`）。
4. （可选）无使用导入（例如，`_ "path/to/package"`)

如果一个文件没有上述可选类别组，相关的导入将包含在项目倒入组中。

任何清晰和容易理解的导入分组通常都是好的。例如，一个团队可以选择将 gRPC 导入与 protobuf 导入分开分组。

> **注意：** 对于只维护两个强制组的代码 (一个组用于标准库，一个组用于所有其他的导入)， `goimports` 工具产生的输出与这个指南一致。
> 然而， `goimports` 并不了解强制性组以外的组；可选组很容易被该工具废止。当使用可选的组别时，作者和审稿人都需要注意，以确保组别符合要求。
> 两种方法都可以，但不要让进口部分处于不一致的、部分分组的状态。

## 错误处理

在 Go 中，[错误就是价值](https://go.dev/blog/errors-are-values)；它们由代码创造，也由代码消耗。错误可以是：

- 转化为诊断信息，显示给程序员看
- 由维护者使用
- 向终端用户解释

错误信息也显示在各种不同的渠道，包括日志信息、错误转储和渲染的 UI。

处理（产生或消耗）错误的代码应该刻意这样做。忽略或盲目地传播错误的返回值可能是很诱人的。然而，值得注意的是，调用框架中的当前函数是否被定位为最有效地处理该错误。这是一个很大的话题，很难给出明确的建议。请使用你自己的判断，但要记住以下的考虑。

- 当创建一个错误值时，决定是否给它任何[结构](https://google.github.io/styleguide/go/best-practices#error-structure)。
- 当处理一个错误时，考虑[添加信息](https://google.github.io/styleguide/go/best-practices#error-extra-info)，这些信息你有，但调用者和/或被调用者可能没有。
- 也请参见关于[错误记录](https://google.github.io/styleguide/go/best-practices#error-logging)的指导。

虽然忽略一个错误通常是不合适的，但一个合理的例外是在协调相关操作时，通常只有第一个错误是有用的。包[`errgroup`](https://pkg.go.dev/golang.org/x/sync/errgroup)为一组操作提供了一个方便的抽象，这些操作都可以作为一个组失败或被取消。

也请参见:

-   [Effective Go on errors](https://go.dev/doc/effective_go#errors)
-   [Go博客关于错误的文章](https://go.dev/blog/go1.13-errors)
-   [`errors` 包](https://pkg.go.dev/errors)
-   [`upspin.io/errors`包](https://commandcenter.blogspot.com/2017/12/error-handling-in-upspin.html)
-   [GoTip #89: 何时使用规范的状态码作为错误？](https://google.github.io/styleguide/go/index.html#gotip)
-   [GoTip #48: 错误的哨兵值](https://google.github.io/styleguide/go/index.html#gotip)
-   [GoTip #13: 设计用于检查的错误](https://google.github.io/styleguide/go/index.html#gotip)

### 错误结构

如果调用者需要询问错误（例如，区分不同的错误条件），请给出错误值结构，这样可以通过编程完成，而不是让调用者进行字符串匹配。这个建议适用于生产代码，也适用于关心不同错误条件的测试。

最简单的结构化错误是无参数的全局值。

```go
type Animal string

var (
    // ErrDuplicate occurs if this animal has already been seen.
    ErrDuplicate = errors.New("duplicate")

    // ErrMarsupial occurs because we're allergic to marsupials outside Australia.
    // Sorry.
    ErrMarsupial = errors.New("marsupials are not supported")
)

func pet(animal Animal) error {
    switch {
    case seen[animal]:
        return ErrDuplicate
    case marsupial(animal):
        return ErrMarsupial
    }
    seen[animal] = true
    // ...
    return nil
}
```

调用者可以简单地将函数返回的错误值与已知的错误值之一进行比较：

```go
// Good:
func handlePet(...) {
    switch err := process(an); err {
    case ErrDuplicate:
        return fmt.Errorf("feed %q: %v", an, err)
    case ErrMarsupial:
        // Try to recover with a friend instead.
        alternate = an.BackupAnimal()
        return handlePet(..., alternate, ...)
    }
}
```

上面使用了哨兵值，其中误差必须等于（在`==`的意义上）预期值。这在很多情况下是完全足够的。如果`process`返回包装好的错误（下面讨论），你可以使用[`errors.Is`](https://pkg.go.dev/errors#Is)。

```go
// Good:
func handlePet(...) {
    switch err := process(an); {
    case errors.Is(err, ErrDuplicate):
        return fmt.Errorf("feed %q: %v", an, err)
    case errors.Is(err, ErrMarsupial):
        // ...
    }
}
```

不要试图根据字符串的形式来区分错误。(参见[Go Tip #13: 设计用于检查的错误](https://google.github.io/styleguide/go/index.html#gotip)以了解更多信息）。

```go
// Bad:
func handlePet(...) {
    err := process(an)
    if regexp.MatchString(`duplicate`, err.Error()) {...}
    if regexp.MatchString(`marsupial`, err.Error()) {...}
}
```

如果错误中有调用者需要的额外信息，最好是以结构化方式呈现。例如，[`os.PathError`](https://pkg.go.dev/os#PathError) 类型的记录是将失败操作的路径名，放在调用者可以轻松访问的结构域中。

其他错误结构可以酌情使用，例如一个包含错误代码和细节字符串的项目结构。[Package `status`](https://pkg.go.dev/google.golang.org/grpc/status) 是一种常见的封装方式；如果你选择这种方式（你没有义务这么做），请使用 [规范错误码](https://pkg.go.dev/google.golang.org/grpc/codes)。参见 [Go Tip #89: 何时使用规范的状态码作为错误](https://google.github.io/styleguide/go/index.html#gotip) 以了解使用状态码是否是正确的选择。

### 为错误添加信息

任何返回错误的函数都应该努力使错误值变得有用。通常情况下，该函数处于一个调用链的中间，并且只是在传播它所调用的其他函数的错误（甚至可能来自另一个包）。这里有机会用额外的信息来注解错误，但程序员应该确保错误中有足够的信息，而不添加重复的或不相关的细节。如果你不确定，可以尝试在开发过程中触发错误条件：这是一个很好的方法来评估错误的观察者（无论是人类还是代码）最终会得到什么。

习惯和良好的文档有帮助。例如，标准包`os`宣传其错误包含路径信息，当它可用时。这是一种有用的风格，因为得到错误的调用者不需要用他们已经提供了失败的函数的信息来注释它。

```go
// Good:
if err := os.Open("settings.txt"); err != nil {
    return err
}

// Output:
//
// open settings.txt: no such file or directory
```

如果对错误的_意义_有什么有趣的说法，当然可以加入。只需考虑调用链的哪一层最适合理解这个含义。

```go
// Good:
if err := os.Open("settings.txt"); err != nil {
    // We convey the significance of this error to us. Note that the current
    // function might perform more than one file operation that can fail, so
    // these annotations can also serve to disambiguate to the caller what went
    // wrong.
    return fmt.Errorf("launch codes unavailable: %v", err)
}

// Output:
//
// launch codes unavailable: open settings.txt: no such file or directory
```

与这里的冗余信息形成鲜明对比：

```go
// Bad:
if err := os.Open("settings.txt"); err != nil {
    return fmt.Errorf("could not open settings.txt: %w", err)
}

// Output:
//
// could not open settings.txt: open settings.txt: no such file or directory
```

当添加信息到一个传播的错误时，你可以包裹错误或提出一个新的错误。用`fmt.Errorf`中的`%w`动词来包装错误，允许调用者访问原始错误的数据。这在某些时候是非常有用的，但在其他情况下，这些细节对调用者来说是误导或不感兴趣的。更多信息请参见[关于错误包装的博文](https://blog.golang.org/go1.13-errors)。包裹错误也以一种不明显的方式扩展了你的包的 API 表面，如果你改变了你的包的实现细节，这可能会导致破坏。

最好避免使用`%w`，除非你也记录（并有测试来验证）你所暴露的基本错误。如果你不期望你的调用者调用`errors.Unwrap`, `errors.Is`等等，就不要费心使用`%w`。

同样的概念适用于[结构化错误](https://google.github.io/styleguide/go/best-practices#error-structure)，如[`*status.Status`](https://pkg.go.dev/google.golang.org/grpc/status)（见[规范错误码](https://pkg.go.dev/google.golang.org/grpc/codes)）。例如，如果你的服务器向后端发送畸形的请求，并收到一个`InvalidArgument` 错误码，这个代码不应该传播给客户端，假设客户端没有做错。相反，应该向客户端返回一个`内部`的规范码。

然而，注解错误有助于自动日志系统保留错误的状态有效载荷。例如，在一个内部函数中注释错误是合适的：

```go
// Good:
func (s *Server) internalFunction(ctx context.Context) error {
    // ...
    if err != nil {
        return fmt.Errorf("couldn't find remote file: %w", err)
    }
}
```

直接位于系统边界的代码（通常是RPC、IPC、存储等之类的）应该使用规范的错误空间报告错误。这里的代码有责任处理特定领域的错误，并以规范的方式表示它们。比如说：

```go
// Bad:
func (*FortuneTeller) SuggestFortune(context.Context, *pb.SuggestionRequest) (*pb.SuggestionResponse, error) {
    // ...
    if err != nil {
        return nil, fmt.Errorf("couldn't find remote file: %w", err)
    }
}
```

```go
// Good:
import (
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/status"
)
func (*FortuneTeller) SuggestFortune(context.Context, *pb.SuggestionRequest) (*pb.SuggestionResponse, error) {
    // ...
    if err != nil {
        // Or use fmt.Errorf with the %w verb if deliberately wrapping an
        // error which the caller is meant to unwrap.
        return nil, status.Errorf(codes.Internal, "couldn't find fortune database", status.ErrInternal)
    }
}
```

### 错误中的 %w 的位置

倾向于将`%w`放在错误字符串的末尾。

错误可以用[`%w`动词](https://blog.golang.org/go1.13-errors)来包装，或者把它们放在一个实现`Unwrap()错误`的[结构化错误](https://google.github.io/styleguide/go/index.html#gotip)中（例如：[`fs.PathError`](https://pkg.go.dev/io/fs#PathError)）。

被包裹的错误形成错误链：每一层新的包裹都会在错误链的前面增加一个新的条目。错误链可以用`Unwrap()error`方法进行遍历。比如说：

```
err1 := fmt.Errorf("err1")
err2 := fmt.Errorf("err2: %w", err1)
err3 := fmt.Errorf("err3: %w", err2)
```

这就形成了一个错误链的形式，

```
flowchart LR
  err3 == err3 wraps err2 ==> err2;
  err2 == err2 wraps err1 ==> err1;
```

不管`%w`动词放在哪里，返回的错误总是代表错误链的前面，而`%w`是下一个子节点。同样，`Unwrap()error`总是从最新的错误到最旧的错误穿越错误链。

然而，`%w`动词的位置会影响错误链是从最新到最旧，从最旧到最新，还是两者都不影响：

```go
// Good:
err1 := fmt.Errorf("err1")
err2 := fmt.Errorf("err2: %w", err1)
err3 := fmt.Errorf("err3: %w", err2)
fmt.Println(err3) // err3: err2: err1
// err3 is a newest-to-oldest error chain, that prints newest-to-oldest.
```

```go
// Bad:
err1 := fmt.Errorf("err1")
err2 := fmt.Errorf("%w: err2", err1)
err3 := fmt.Errorf("%w: err3", err2)
fmt.Println(err3) // err1: err2: err3
// err3 is a newest-to-oldest error chain, that prints oldest-to-newest.
```

```go
// Bad:
err1 := fmt.Errorf("err1")
err2 := fmt.Errorf("err2-1 %w err2-2", err1)
err3 := fmt.Errorf("err3-1 %w err3-2", err2)
fmt.Println(err3) // err3-1 err2-1 err1 err2-2 err3-2
// err3 is a newest-to-oldest error chain, that neither prints newest-to-oldest
// nor oldest-to-newest.
```

因此，为了使错误文本反映错误链结构，最好将`%w`动词放在最后，形式为`[...]: %w`。

### 错误日志

函数有时需要告诉外部系统一个错误，而不把它传播给其调用者。在这里，日志是一个明显的选择；但要注意记录错误的内容和方式。

- 像[好的测试失败信息](https://google.github.io/styleguide/go/decisions#useful-test-failures)一样，日志信息应该清楚地表达出错的原因，并通过包括相关信息来帮助维护者诊断问题。
- 避免重复。如果你返回一个错误，通常最好不要自己记录，而是让调用者处理。调用者可以选择记录错误，也可以使用[`rate.sometimes`](https://pkg.go.dev/golang.org/x/time/rate#Sometimes)限制记录的速度。其他选择包括尝试恢复，甚至是[停止程序](https://google.github.io/styleguide/go/best-practices#checks-and-panics)。在任何情况下，让调用者控制有助于避免日志垃圾。
  然而，这种方法的缺点是，任何日志都是用调用者的行座标写的。
- 对[PII](https://en.wikipedia.org/wiki/Personal_data)要小心。许多日志汇不是敏感的终端用户信息的合适目的地。
- 尽量少使用`log.Error`。ERROR级别的日志会导致刷新，比低级别的日志更昂贵。这可能会对你的代码产生严重的性能影响。当决定错误级别还是警告级别时，考虑最佳实践，即错误级别的消息应该是可操作的，而不是比警告 "更严重"。
- 在谷歌内部，我们有监控系统，可以设置更有效的警报，而不是写到日志文件，希望有人注意到它。这与标准库[` expvar` 包](https://pkg.go.dev/expvar)类似，但不完全相同。

#### 自定义日志级别

使用日志分级([`log.V`](https://pkg.go.dev/github.com/golang/glog#V))对你有利。分级的日志对开发和追踪很有用。建立一个关于粗略程度的约定是有帮助的。比如说。

- 在 `V(1) `写少量的额外信息
- 在 `V(2)`中跟踪更多信息
- 在 `V(3)`中倾倒大量的内部状态。

为了尽量减少粗略记录的成本，你应该确保即使在 `log.V` 关闭的情况下也不要意外地调用昂贵的函数。`log.V`提供两个API。更方便的那个带有这种意外支出的风险。如有疑问，请使用稍显粗略的风格。

```go
// Good:
for _, sql := range queries {
  log.V(1).Infof("Handling %v", sql)
  if log.V(2) {
    log.Infof("Handling %v", sql.Explain())
  }
  sql.Run(...)
}
```

```go
// Bad:
// sql.Explain called even when this log is not printed.
log.V(2).Infof("Handling %v", sql.Explain())
```

### 程序初始化

程序的初始化错误（如坏的标志和配置）应该向上传播到`main`，它应该调用`log.Exit`，并说明如何修复错误。在这些情况下，一般不应使用`log.Fatal`，因为指向检查的堆栈跟踪不可能像人工生成的可操作信息那样有用。

### 程序检查和 panic

正如[反对 panic 的决定](https://google.github.io/styleguide/go/decisions#dont-panic)中所述，标准的错误处理应该围绕错误返回值进行结构化。库应该倾向于向调用者返回错误，而不是中止程序，特别是对于瞬时错误。

偶尔有必要对一个不变量进行一致性检查，如果违反了这个不变量，就终止程序。一般来说，只有当不变量检查失败意味着内部状态已经无法恢复时，才会这样做。在谷歌代码库中，最可靠的方法是调用`log.Fatal`。在这种情况下使用`panic`是不可靠的，因为延迟函数有可能会出现死锁或进一步破坏内部或外部状态。

同样，抵制恢复 panic 以避免崩溃的诱惑，因为这样做可能导致传播损坏的状态。你离 panic 越远，你对程序的状态就越不了解，它可能持有锁或其他资源。然后，程序可以发展出其他意想不到的故障模式，使问题更加难以诊断。与其试图在代码中处理意外的 panic，不如使用监控工具来浮现出意外的故障，并高度优先修复相关的错误。

**注意：**标准的[`net/http`服务器](https://pkg.go.dev/net/http#Server)违反了这个建议，从请求处理程序中恢复 panic。有经验的 Go 工程师的共识是，这是一个历史性的错误。如果你对其他语言的应用服务器的日志进行采样，通常会发现有大量的堆栈轨迹没有被处理。在你的服务器中应避免这种陷阱。

### 何时 panic

标准库对 API 的误用感到 panic。例如，[`reflect`](https://pkg.go.dev/reflect)在许多情况下，如果一个值的访问方式表明它被误读，就会发出 panic。这类似于对核心语言错误的 panic，如访问一个越界的 slice 元素。代码审查和测试应该发现这样的错误，这些错误预计不会出现在生产代码中。这些 panic 作为不依赖库的不变性检查，因为标准库不能访问谷歌代码库使用的[levelled `log`](https://google.github.io/styleguide/go/decisions#logging) 包。

另一种情况下，panic 可能是有用的，尽管不常见，是作为一个包的内部实现细节，在调用链中总是有一个匹配的恢复。解析器和类似的深度嵌套、紧密耦合的内部函数组可以从这种设计中受益，其中管道错误返回增加了复杂性而没有价值。这种设计的关键属性是，这些 panic 永远不允许跨越包的边界，不构成包的API的一部分。这通常是通过一个顶层的延迟恢复来实现的，它将传播的 panic 转化为公共API表面的返回错误。

当编译器无法识别不可到达的代码时，例如使用像`log.Fatal`这样不会返回的函数时，也会使用 Panic：

```go
// Good:
func answer(i int) string {
    switch i {
    case 42:
        return "yup"
    case 54:
        return "base 13, huh"
    default:
        log.Fatalf("Sorry, %d is not the answer.", i)
        panic("unreachable")
    }
}
```

[不要在标志被解析之前调用`log`函数](https://pkg.go.dev/github.com/golang/glog#pkg-overview)。如果你必须在 `init`函数中死亡，可以接受用 panic 来代替日志调用。

## 文档

### 公约

本节是对决策文件的[注释](https://google.github.io/styleguide/go/decisions#commentary)部分的补充。
以熟悉的风格记录的 Go 代码比那些错误记录或根本没有记录的代码更容易阅读，更不容易被误用。可运行的[实例](https://google.github.io/styleguide/go/decisions#examples)会出现在 Godoc 和代码搜索中，是解释如何使用你的代码的绝佳方式。

#### 参数和配置

不是每个参数都必须在文档中列举出来。这适用于

- 函数和方法参数
- 结构字段
- API的选项

将易出错或不明显的字段和参数记录下来，说说它们为什么有趣。

在下面的片段中，突出显示的注释对读者来说没有增加什么有用的信息：

```go
// Bad:
// Sprintf formats according to a format specifier and returns the resulting
// string.
//
// format is the format, and data is the interpolation data.
func Sprintf(format string, data ...interface{}) string
```

然而，这个片段展示了一个与之前类似的代码场景，其中评论反而说明了一些不明显或对读者有实质性帮助的东西：

```go
// Good:
// Sprintf formats according to a format specifier and returns the resulting
// string.
//
// The provided data is used to interpolate the format string. If the data does
// not match the expected format verbs or the amount of data does not satisfy
// the format specification, the function will inline warnings about formatting
// errors into the output string as described by the Format errors section
// above.
func Sprintf(format string, data ...interface{}) string
```

在选择文档的内容和深度时，要考虑到你可能的受众。维护者、新加入团队的人、外部用户，甚至是六个月后的你，可能会与你第一次来写文档时的想法略有不同的信息。

也请参见。

-   [GoTip #41: 识别函数调用参数](https://google.github.io/styleguide/go/index.html#gotip)
-   [GoTip #51: 配置的模式](https://google.github.io/styleguide/go/index.html#gotip)

#### 上下文

这意味着取消一个上下文参数会中断提供给它的函数。如果该函数可以返回一个错误，习惯上是`ctx.Err()`。

这个事实不需要重述：

```go
// Bad:
// Run executes the worker's run loop.
//
// The method will process work until the context is cancelled and accordingly
// returns an error.
func (Worker) Run(ctx context.Context) error
```

因为这句话是隐含的，所以下面的说法更好:

```go
// Good:
// Run executes the worker's run loop.
func (Worker) Run(ctx context.Context) error
```

如果上下文行为是不同的或不明显的，应该明确地记录下来：

- 如果函数在取消上下文时返回一个除`ctx.Err()`以外的错误：

  ```go
  // Good:
  // Run executes the worker's run loop.
  //
  // If the context is cancelled, Run returns a nil error.
  func (Worker) Run(ctx context.Context) error
  ```

- 如果该功能有其他机制，可能会中断它或影响其生命周期：

  ```go
  // Good:
  // Run executes the worker's run loop.
  //
  // Run processes work until the context is cancelled or Stop is called.
  // Context cancellation is handled asynchronously internally: run may return
  // before all work has stopped. The Stop method is synchronous and waits
  // until all operations from the run loop finish. Use Stop for graceful
  // shutdown.
  func (Worker) Run(ctx context.Context) error
  
  func (Worker) Stop()
  ```

- 如果该函数对上下文的生命周期、脉络或附加值有特殊期望：

  ```go
  // Good:
  // NewReceiver starts receiving messages sent to the specified queue.
  // The context should not have a deadline.
  func NewReceiver(ctx context.Context) *Receiver
  
  // Principal returns a human-readable name of the party who made the call.
  // The context must have a value attached to it from security.NewContext.
  func Principal(ctx context.Context) (name string, ok bool)
  ```

  **警告：**避免设计对其调用者提出这种要求（比如上下文没有截止日期）的API。以上只是一个例子，说明在无法避免的情况下该如何记录，而不是对该模式的认可。

#### 并发

Go 用户认为概念上的只读操作对于并发使用是安全的，不需要额外的同步。

在这个 Godoc 中，关于并发性的额外说明可以安全地删除：

```go
// Len returns the number of bytes of the unread portion of the buffer;
// b.Len() == len(b.Bytes()).
//
// It is safe to be called concurrently by multiple goroutines.
func (*Buffer) Len() int
```

然而，变异操作并不被认为对并发使用是安全的，需要用户考虑同步化。
同样地，这里可以安全地删除关于并发的额外注释：

```go
// Grow grows the buffer's capacity.
//
// It is not safe to be called concurrently by multiple goroutines.
func (*Buffer) Grow(n int)
```

强烈鼓励在以下情况下提供文档：

- 目前还不清楚该操作是只读的还是变异的。

  ```go
  // Good:
  package lrucache
  
  // Lookup returns the data associated with the key from the cache.
  //
  // This operation is not safe for concurrent use.
  func (*Cache) Lookup(key string) (data []byte, ok bool)
  ```

  为什么？在查找密钥时，缓存命中会在内部突变一个 LRU 缓存。这一点是如何实现的，对所有的读者来说可能并不明显。

- 同步是由 API 提供的

  ```go
  // Good:
  package fortune_go_proto
  
  // NewFortuneTellerClient returns an *rpc.Client for the FortuneTeller service.
  // It is safe for simultaneous use by multiple goroutines.
  func NewFortuneTellerClient(cc *rpc.ClientConn) *FortuneTellerClient
  ```

  为什么？Stubby 提供了同步性。

  **注意：**如果API是一个类型，并且 API 完整地提供了同步，传统上只有类型定义记录了语义。

- 该 API 消费用户实现的接口类型，并且该接口的消费者有特殊的并发性要求：

  ```go
  // Good:
  package health
  
  // A Watcher reports the health of some entity (usually a backen service).
  //
  // Watcher methods are safe for simultaneous use by multiple goroutines.
  type Watcher interface {
      // Watch sends true on the passed-in channel when the Watcher's
      // status has changed.
      Watch(changed chan<- bool) (unwatch func())
  
      // Health returns nil if the entity being watched is healthy, or a
      // non-nil error explaining why the entity is not healthy.
      Health() error
  }
  ```

  为什么？一个 API 是否能被多个 goroutines 安全使用是其契约的一部分。

#### 清理

记录 API 的任何明确的清理要求。否则，调用者不会正确使用 API，导致资源泄漏和其他可能的错误。

调出由调用者决定的清理工作：

```go
// Good:
// NewTicker returns a new Ticker containing a channel that will send the
// current time on the channel after each tick.
//
// Call Stop to release the Ticker's associated resources when done.
func NewTicker(d Duration) *Ticker

func (*Ticker) Stop()
```

如果有可能不清楚如何清理资源，请解释如何清理：

```go
// Good:
// Get issues a GET to the specified URL.
//
// When err is nil, resp always contains a non-nil resp.Body.
// Caller should close resp.Body when done reading from it.
//
//    resp, err := http.Get("http://example.com/")
//    if err != nil {
//        // handle error
//    }
//    defer resp.Body.Close()
//    body, err := io.ReadAll(resp.Body)
func (c *Client) Get(url string) (resp *Response, err error)
```

### 预览

Go 的特点是有一个[文档服务器](https://pkg.go.dev/golang.org/x/pkgsite/cmd/pkgsite)。建议在代码审查前和审查过程中预览你的代码产生的文档。这有助于验证[ godoc 格式化](https://google.github.io/styleguide/go/best-practices#godoc-formatting)是否正确呈现。

### Godoc 格式化

[Godoc](https://pkg.go.dev/)为[格式化文档](https://go.dev/doc/comment)提供了一些特定的语法。

- 段落之间需要有一个空行：

  ```go
  // Good:
  // LoadConfig reads a configuration out of the named file.
  //
  // See some/shortlink for config file format details.
  ```

- 测试文件可以包含[可运行的例子](https://google.github.io/styleguide/go/decisions#examples)，这些例子出现在 godoc 中相应的文档后面：

  ```go
  // Good:
  func ExampleConfig_WriteTo() {
    cfg := &Config{
      Name: "example",
    }
    if err := cfg.WriteTo(os.Stdout); err != nil {
      log.Exitf("Failed to write config: %s", err)
    }
    // Output:
    // {
    //   "name": "example"
    // }
  }
  ```

- 缩进的行数再加上两个空格，就可以将它们逐字排开：

  ```go
  // Good:
  // Update runs the function in an atomic transaction.
  //
  // This is typically used with an anonymous TransactionFunc:
  //
  //   if err := db.Update(func(state *State) { state.Foo = bar }); err != nil {
  //     //...
  //   }
  ```

  然而，请注意，把代码放在可运行的例子中，而不是把它放在注释中，往往会更合适。
  这种逐字格式化可以用于非godoc原生的格式化，如列表和表格：

  ```go
  // Good:
  // LoadConfig reads a configuration out of the named file.
  //
  // LoadConfig treats the following keys in special ways:
  //   "import" will make this configuration inherit from the named file.
  //   "env" if present will be populated with the system environment.
  ```

- 一行以大写字母开始，除括号和逗号外不含标点符号，后面是另一个段落，其格式为标题：

  ```go
  // Good:
  // The following line is formatted as a heading.
  //
  // Using headings
  //
  // Headings come with autogenerated anchor tags for easy linking.
  ```


### 信号增强

有时一行代码看起来很普通，但实际上并不普通。这方面最好的例子之一是`err == nil`的检查（因为`err != nil`更常见）。下面的两个条件检查很难区分：

```go
// Good:
if err := doSomething(); err != nil {
    // ...
}
```

```go
// Bad:
if err := doSomething(); err == nil {
    // ...
}
```

你可以通过添加评论来 "提高 "条件的信号：

```go
// Good:
if err := doSomething(); err == nil { // if NO error
    // ...
}
```

该评论提请注意条件的不同。

## 变量声明

### 初始化

为了保持一致性，当用非零值初始化一个新的变量时，首选`:=`而不是`var`。

### 非指针式零值

下面的声明使用[零值](https://golang.org/ref/spec#The_zero_value)：

```go
// Good:
var (
    coords Point
    magic  [4]byte
    primes []int
)
```

当你想要传递一个空值**以供以后使用**时，你应该使用零值声明。使用带有显式初始化的复合字面会显得很笨重：

```go
// Bad:
var (
    coords = Point{X: 0, Y: 0}
    magic  = [4]byte{0, 0, 0, 0}
    primes = []int(nil)
)
```

零值声明的一个常见应用是当使用一个变量作为反序列化时的输出：

```go
// Good:
var coords Point
if err := json.Unmarshal(data, &coords); err != nil {
```

在你的结构体中，如果你需要一个[不得复制](https://google.github.io/styleguide/go/decisions#copying)的锁或其他字段，可以将其设为值类型以利用零值初始化。这确实意味着，现在必须通过指针而不是值来传递包含的类型。该类型的方法必须采用指针接收器。

```go
// Good:
type Counter struct {
    // This field does not have to be "*sync.Mutex". However,
    // users must now pass *Counter objects between themselves, not Counter.
    mu   sync.Mutex
    data map[string]int64
}

// Note this must be a pointer receiver to prevent copying.
func (c *Counter) IncrementBy(name string, n int64)
```

对复合体（如结构体和数组）的局部变量使用值类型是可以接受的，即使它们包含这种不可复制的字段。然而，如果复合体是由函数返回的，或者如果对它的所有访问最终都需要获取一个地址，那么最好在一开始就将变量声明为指针类型。同样地，protobufs 也应该被声明为指针类型。

```go
// Good:
func NewCounter(name string) *Counter {
    c := new(Counter) // "&Counter{}" is also fine.
    registerCounter(name, c)
    return c
}

var myMsg = new(pb.Bar) // or "&pb.Bar{}".
```

这是因为`*pb.Something`满足[`proto.Message`](https://pkg.go.dev/google.golang.org/protobuf/proto#Message)而`pb.Something`不满足。

```go
// Bad:
func NewCounter(name string) *Counter {
    var c Counter
    registerCounter(name, &c)
    return &c
}

var myMsg = pb.Bar{}
```

> **重要的是：** Map 类型在被修改之前必须明确地初始化。然而，从零值 Map 中读取是完全可以的。
> 对于 map 和 slice 类型，如果代码对性能特别敏感，并且你事先知道大小，请参见[size hints](https://google.github.io/styleguide/go/best-practices#vardeclsize)部分。

### 复合字面量

以下是[复合字面量](https://golang.org/ref/spec#Composite_literals)的声明：

```go
// Good:
var (
    coords   = Point{X: x, Y: y}
    magic    = [4]byte{'I', 'W', 'A', 'D'}
    primes   = []int{2, 3, 5, 7, 11}
    captains = map[string]string{"Kirk": "James Tiberius", "Picard": "Jean-Luc"}
)
```

当你知道初始元素或成员时，你应该使用复合字面量来声明一个值。

相比之下，与[零值初始化]相比，使用复合字面量声明空或无成员值可能会在视觉上产生噪音

当你需要一个指向零值的指针时，你有两个选择：空复合字面和`new`。两者都很好，但是`new`关键字可以提醒读者，如果需要一个非零值，这个复合字面量将不起作用：

```go
// Good:
var (
  buf = new(bytes.Buffer) // non-empty Buffers are initialized with constructors.
  msg = new(pb.Message) // non-empty proto messages are initialized with builders or by setting fields one by one.
)
```

### size 提示

以下是利用 size 提示来预分配容量的声明方式：

```go
// Good:
var (
    // Preferred buffer size for target filesystem: st_blksize.
    buf = make([]byte, 131072)
    // Typically process up to 8-10 elements per run (16 is a safe assumption).
    q = make([]Node, 0, 16)
    // Each shard processes shardSize (typically 32000+) elements.
    seen = make(map[string]bool, shardSize)
)
```

根据对代码及其集成的经验分析，对创建性能敏感和资源高效的代码，size 提示和预分配是重要的步骤。

大多数代码不需要 size 提示或预分配，可以允许运行时根据需要增长 slice 或 map。当最终大小已知时，预分配是可以接受的（例如，在 slice 或 map 之间转换时），但这不是一个可读性要求，而且在少数情况下可能不值得这样做。

**警告：**预先分配比你需要的更多的内存，会在队列中浪费内存，甚至损害性能。如有疑问，请参阅[GoTip #3: Benchmarking Go Code](https://google.github.io/styleguide/go/index.html#gotip)并默认为[零初始化](https://google.github.io/styleguide/go/best-practices#vardeclzero)或[复合字面量声明](https://google.github.io/styleguide/go/best-practices#vardeclcomposite)。

### [Channel 方向](https://google.github.io/styleguide/go/best-practices#channel-direction)

尽可能地指定[ Channel 方向](https://go.dev/ref/spec#Channel_types)。

```go
// Good:
// sum computes the sum of all of the values. It reads from the channel until
// the channel is closed.
func sum(values <-chan int) int {
    // ...
}
```

这可以防止在没有规范的情况下可能出现的随意编码错误。

```go
// Bad:
func sum(values chan int) (out int) {
    for v := range values {
        out += v
    }
    // values must already be closed for this code to be reachable, which means
    // a second close triggers a panic.
    close(values)
}
```

当方向被指定时，编译器会捕捉到像这样的简单错误。它还有助于向类型传达一种所有权的措施。
也请看 Bryan Mills 的演讲 "重新思考经典的并发模式"。[PPT链接](https://drive.google.com/file/d/1nPdvhB0PutEJzdCq5ms6UI58dp50fcAN/view?usp=sharing) [视频链接](https://www.youtube.com/watch?v=5zXAHh5tJqQ)。

## 函数参数列表

不要让一个函数的签名变得太长。当一个函数中的参数越多，单个参数的作用就越不明确，同一类型的相邻参数就越容易混淆。有大量参数的函数不容易被记住，在调用点也更难读懂。

在设计 API 时，可以考虑将一个签名越来越复杂的高配置函数分割成几个更简单的函数。如果有必要的话，这些函数可以共享一个（未导出的）实现。

当一个函数需要许多输入时，可以考虑为一些参数引入一个 option 模式，或者采用更高级的变体选项技术。选择哪种策略的主要考虑因素应该是函数调用在所有预期的使用情况下看起来如何。

下面的建议主要适用于导出的 API，它比未导出的 API 的标准要高。这些技术对于你的用例可能是不必要的。使用你的判断，并平衡清晰性和最小机制的原则。

也请参见。[Go技巧#24：使用特定案例的结构]((https://google.github.io/styleguide/go/index.html#gotip))

### option 模式

option 模式是一种结构类型，它收集了一个函数或方法的部分或全部参数，然后作为最后一个参数传递给该函数或方法。(该结构只有在导出的函数中使用时，才应该导出)。

使用 option 模式有很多好处。

- 结构体字面量包括每个参数的字段和值，这使得它们可以自己作为文档，并且更难被交换。

- 不相关的或 "默认 "的字段可以被省略。

- 调用者可以共享 option 模式，并编写帮助程序对其进行操作。

- 与函数参数相比，结构体提供了更清晰的每个字段的文档。

- option 模式可以随着时间的推移而增长，而不会影响到调用点。

  下面是一个可以改进的函数的例子：

```go
// Bad:
func EnableReplication(ctx context.Context, config *replicator.Config, primaryRegions, readonlyRegions []string, replicateExisting, overwritePolicies bool, replicationInterval time.Duration, copyWorkers int, healthWatcher health.Watcher) {
    // ...
}
```

上面的函数可以用一个 option 模式重写如下：

```go
// Good:
type ReplicationOptions struct {
    Config              *replicator.Config
    PrimaryRegions      []string
    ReadonlyRegions     []string
    ReplicateExisting   bool
    OverwritePolicies   bool
    ReplicationInterval time.Duration
    CopyWorkers         int
    HealthWatcher       health.Watcher
}

func EnableReplication(ctx context.Context, opts ReplicationOptions) {
    // ...
}
```

然后，该函数可以在不同的包中被调用：

```go
// Good:
func foo(ctx context.Context) {
    // Complex call:
    storage.EnableReplication(ctx, storage.ReplicationOptions{
        Config:              config,
        PrimaryRegions:      []string{"us-east1", "us-central2", "us-west3"},
        ReadonlyRegions:     []string{"us-east5", "us-central6"},
        OverwritePolicies:   true,
        ReplicationInterval: 1 * time.Hour,
        CopyWorkers:         100,
        HealthWatcher:       watcher,
    })

    // Simple call:
    storage.EnableReplication(ctx, storage.ReplicationOptions{
        Config:         config,
        PrimaryRegions: []string{"us-east1", "us-central2", "us-west3"},
    })
}
```

**注意**：[option 模式中从不包含上下文](https://google.github.io/styleguide/go/decisions#contexts)。

当遇到以下某些情况时，通常首选 option 模式：

- 所有调用者都需要指定一个或多个选项。
- 大量的调用者需要提供许多选项。
- 用户要调用的多个函数之间共享这些选项。

### 可变 option 模式

使用可变 option 模式，可以创建导出的函数，其返回的闭包可以传递给函数的[variadic（`...`）参数](https://golang.org/ref/spec#Passing_arguments_to_..._parameters)。该函数将选项的值作为其参数（如果有的话），而返回的闭包接受一个可变的引用（通常是一个指向结构体类型的指针），该引用将根据输入进行更新。

使用可变 option 模式可以提供很多好处。

- 当不需要配置时，选项在调用点不占用空间。
- 选项仍然是值，所以调用者可以共享它们，编写帮助程序，并积累它们。
- 选项可以接受多个参数（例如：`cartesian.Translate(dx, dy int) TransformOption`）。
- 选项函数可以返回一个命名的类型，以便在 godoc 中把选项组合起来。
- 包可以允许（或阻止）第三方包定义（或不定义）自己的选项。

**注意：**使用可变 option 模式需要大量的额外代码（见下面的例子），所以只有在好处大于坏处时才可以使用。

下面是一个可以改进的功能的例子：

```go
// Bad:
func EnableReplication(ctx context.Context, config *placer.Config, primaryCells, readonlyCells []string, replicateExisting, overwritePolicies bool, replicationInterval time.Duration, copyWorkers int, healthWatcher health.Watcher) {
  ...
}
```

上面的例子可以用可变 option 模式重写如下：

```go
// Good:
type replicationOptions struct {
    readonlyCells       []string
    replicateExisting   bool
    overwritePolicies   bool
    replicationInterval time.Duration
    copyWorkers         int
    healthWatcher       health.Watcher
}

// A ReplicationOption configures EnableReplication.
type ReplicationOption func(*replicationOptions)

// ReadonlyCells adds additional cells that should additionally
// contain read-only replicas of the data.
//
// Passing this option multiple times will add additional
// read-only cells.
//
// Default: none
func ReadonlyCells(cells ...string) ReplicationOption {
    return func(opts *replicationOptions) {
        opts.readonlyCells = append(opts.readonlyCells, cells...)
    }
}

// ReplicateExisting controls whether files that already exist in the
// primary cells will be replicated.  Otherwise, only newly-added
// files will be candidates for replication.
//
// Passing this option again will overwrite earlier values.
//
// Default: false
func ReplicateExisting(enabled bool) ReplicationOption {
    return func(opts *replicationOptions) {
        opts.replicateExisting = enabled
    }
}

// ... other options ...

// DefaultReplicationOptions control the default values before
// applying options passed to EnableReplication.
var DefaultReplicationOptions = []ReplicationOption{
    OverwritePolicies(true),
    ReplicationInterval(12 * time.Hour),
    CopyWorkers(10),
}

func EnableReplication(ctx context.Context, config *placer.Config, primaryCells []string, opts ...ReplicationOption) {
    var options replicationOptions
    for _, opt := range DefaultReplicationOptions {
        opt(&options)
    }
    for _, opt := range opts {
        opt(&options)
    }
}
```

然后，该函数可以在不同的包中被调用：

```go
// Good:
func foo(ctx context.Context) {
    // Complex call:
    storage.EnableReplication(ctx, config, []string{"po", "is", "ea"},
        storage.ReadonlyCells("ix", "gg"),
        storage.OverwritePolicies(true),
        storage.ReplicationInterval(1*time.Hour),
        storage.CopyWorkers(100),
        storage.HealthWatcher(watcher),
    )

    // Simple call:
    storage.EnableReplication(ctx, config, []string{"po", "is", "ea"})
}
```

当遇到很多以下情况时，首选可变 option 模式：

- 大多数调用者不需要指定任何选项。
- 大多数选项不经常使用。
- 有大量的选项。
- 选项需要参数。
- 选项可能会失败或设置错误（在这种情况下，选项函数会返回一个`错误'）。
- 选项需要大量的文档，在一个结构中很难容纳。
- 用户或其他软件包可以提供自定义选项。

这种风格的选项应该接受参数，而不是在命名中标识来表示它们的价值；后者会使参数的动态组合变得更加困难。例如，二进制设置应该接受一个布尔值（例如，`rpc.FailFast(enable bool)`比`rpc.EnableFailFast()`更合适）。枚举的选项应该接受一个枚举的常数（例如`log.Format(log.Capacitor)`比`log.CapacitorFormat()`更好）。另一种方法使那些必须以编程方式选择传递哪些选项的用户更加困难；这种用户被迫改变参数的实际组成，而不是改变参数到选项。不要假设所有的用户都会知道全部的选项。

一般来说，option 应该被按顺序处理。如果有冲突或者一个非累积的选项被多次传递，将应用最后一个参数。

在这种模式下，选项函数的参数通常是未导出的，以限制选项只在包本身内定义。这是一个很好的默认值，尽管有时允许其他包定义选项也是合适的。

参见[Rob Pike 的原始博文](http://commandcenter.blogspot.com/2014/01/self-referential-functions-and-design.html)和[Dave Cheney的演讲](https://dave.cheney.net/2014/10/17/functional-options-for-friendly-apis)，以更深入地了解这些选项的使用方法。

## 复杂的命令行界面

一些程序希望为用户提供丰富的命令行界面，包括子命令。例如，`kubectl create`，`kubectl run`，以及许多其他的子命令都是由程序`kubectl`提供。至少有以下常用的库可以实现这个目的。

如果你没有偏好或者其他考虑因素相同，推荐使用[subcommands](https://pkg.go.dev/github.com/google/subcommands)，因为它是最简单的，而且容易正确使用。然而，如果你需要它所不提供的不同功能，请挑选其他选项之一。

- **[cobra](https://pkg.go.dev/github.com/spf13/cobra)**
  * 习惯标志：getopt
  * 在谷歌代码库之外很常见。
  * 许多额外的功能。
  * 使用中的陷阱（见下文）。
- **[subcommands](https://pkg.go.dev/github.com/google/subcommands)**
  * 习惯标志：Go
  * 简单且易于正确使用。
  * 如果你不需要额外的功能，推荐使用。

**警告**：cobra 命令函数应该使用 `cmd.Context()` 来获取上下文，而不是用 `context.Background` 来创建自己的根上下文。使用子命令包的代码已经将正确的上下文作为一个函数参数接收。

你不需要把每个子命令放在一个单独的包中，而且通常也没有必要这样做。应用与任何 Go 代码库相同的关于包边界的考虑。如果你的代码既可以作为库也可以作为二进制文件使用，通常将 CLI 代码和库分开是有好处的，使 CLI 只是其客户端中的一个。(这不是专门针对有子命令的CLI的，但在此提及，因为它经常出现。）

## 测试

### 把测试留给 `Test` 函数

Go 区分了 "测试辅助函数 "和 "断言辅助函数"。

- **测试辅助函数**就是做设置或清理任务的函数。所有发生在测试辅助函数中的故障都被认为是环境的故障（而不是来自被测试的代码）--例如，当一个测试数据库不能被启动，因为在这台机器上没有更多的空闲端口。对于这样的函数，调用`t.Helper`通常是合适的，[将其标记为测试辅助函数](https://google.github.io/styleguide/go/decisions#mark-test-helpers)。参见 [测试辅助函数的错误处理](https://google.github.io/styleguide/go/best-practices#test-helper-error-handling) 了解更多细节。
- **断言辅助函数**是检查系统正确性的函数，如果没有达到预期，则测试失败。断言辅助函数在 Go 中[不被认为是常见用法](https://google.github.io/styleguide/go/decisions#assert)。

测试的目的是报告被测试代码的通过/失败情况。测试失败的理想场所是在`Test`函数本身，因为这样可以确保[失败信息](https://google.github.io/styleguide/go/decisions#useful-test-failures)和测试逻辑是清晰的。

随着你的测试代码的增长，可能有必要将一些功能分解到独立的函数中。标准的软件工程考虑仍然适用，因为_测试代码仍然是代码_。如果这些功能不与测试框架交互，那么所有的常规规则都适用。然而，当通用代码与框架交互时，必须注意避免常见的陷阱，这些陷阱会导致语焉不详的失败信息和不可维护的测试。

如果许多独立的测试用例需要相同的验证逻辑，请以下列方式之一安排测试，而不是使用断言辅助函数或复杂的验证函数。

- 在`Test`函数中内联逻辑（包括验证和失败），即使它是重复的。这在简单的情况下效果最好。
- 如果输入是类似的，可以考虑把它们统一到一个[表格驱动的测试](https://google.github.io/styleguide/go/decisions#table-driven-tests)，同时在循环中保持逻辑的内联。这有助于避免重复，同时在 "测试 "中保持验证和失败。
- 如果有多个调用者需要相同的验证功能，但表格测试不适合（通常是因为输入不够简单或验证需要作为操作序列的一部分），安排验证功能，使其返回一个值（通常是一个 "错误"），而不是接受一个 "testing.T "参数并使用它来让测试失败。在`测试`中使用逻辑来决定是否失败，并提供[有用的测试失败](https://google.github.io/styleguide/go/decisions#useful-test-failures)。你也可以创建测试辅助函数，以剔除常见的模板设置代码。

最后一点中概述的设计保持了正交性。例如，[`cmp` 包 ](https://pkg.go.dev/github.com/google/go-cmp/cmp)不是为了测试失败而设计的，而是为了比较（和差异）值。因此，它不需要知道进行比较的上下文，因为调用者可以提供这个。如果你的普通测试代码为你的数据类型提供了一个`cmp.Transformer`，这通常是最简单的设计。对于其他的验证，可以考虑返回一个`error`值。

```go
// Good:
// polygonCmp returns a cmp.Option that equates s2 geometry objects up to
// some small floating-point error.
func polygonCmp() cmp.Option {
    return cmp.Options{
        cmp.Transformer("polygon", func(p *s2.Polygon) []*s2.Loop { return p.Loops() }),
        cmp.Transformer("loop", func(l *s2.Loop) []s2.Point { return l.Vertices() }),
        cmpopts.EquateApprox(0.00000001, 0),
        cmpopts.EquateEmpty(),
    }
}

func TestFenceposts(t *testing.T) {
    // This is a test for a fictional function, Fenceposts, which draws a fence
    // around some Place object. The details are not important, except that
    // the result is some object that has s2 geometry (github.com/golang/geo/s2)
    got := Fencepost(tomsDiner, 1*meter)
    if diff := cmp.Diff(want, got, polygonCmp()); diff != "" {
        t.Errorf("Fencepost(tomsDiner, 1m) returned unexpected diff (-want+got):\n%v", diff)
    }
}

func FuzzFencepost(f *testing.F) {
    // Fuzz test (https://go.dev/doc/fuzz) for the same.

    f.Add(tomsDiner, 1*meter)
    f.Add(school, 3*meter)

    f.Fuzz(func(t *testing.T, geo Place, padding Length) {
        got := Fencepost(geo, padding)
        // Simple reference implementation: not used in prod, but easy to
        // reasonable and therefore useful to check against in random tests.
        reference := slowFencepost(geo, padding)

        // In the fuzz test, inputs and outputs can be large so don't
        // bother with printing a diff. cmp.Equal is enough.
        if !cmp.Equal(got, reference, polygonCmp()) {
            t.Errorf("Fencepost returned wrong placement")
        }
    })
}
```

`polygonCmp`函数对它的调用方式是不可知的；它不接受具体的输入类型，也不规定在两个对象不匹配的情况下该怎么做。因此，更多的调用者可以使用它。

**注意：**在测试辅助函数和普通库代码之间有一个类比。库中的代码通常应该[不 panic](https://google.github.io/styleguide/go/decisions#dont-panic)，除非在极少数情况下；从测试中调用的代码不应该停止测试，除非[继续进行没有意义](https://google.github.io/styleguide/go/best-practices#t-fatal)。

### 设计可扩展的验证API

风格指南中关于测试的大部分建议都是关于测试你自己的代码。本节是关于如何为其他人提供设施来测试他们编写的代码，以确保它符合你的库的要求。

#### 验收测试

这种测试被称为[验收测试](https://en.wikipedia.org/wiki/Acceptance_testing)。这种测试的前提是，使用测试的人不知道测试中发生的每一个细节；他们只是把输入交给测试机构来完成。这可以被认为是一种[控制反转](https://en.wikipedia.org/wiki/Inversion_of_control)的形式。

在典型的Go测试中，测试函数控制着程序流程，[无断言](https://google.github.io/styleguide/go/decisions#assert)和[测试函数](https://google.github.io/styleguide/go/best-practices#test-functions)指南鼓励你保持这种方式。本节解释了如何以符合 Go 风格的方式来编写对这些测试的支持。

在深入探讨如何做之前，请看下面摘录的[`io/fs`](https://pkg.go.dev/io/fs)中的一个例子：

```go
type FS interface {
    Open(name string) (File, error)
}
```

虽然存在众所周知的`fs.FS`的实现，但 Go 开发者可能会被期望编写一个。为了帮助验证用户实现的`fs.FS`是否正确，在[`testing/fstest`](https://pkg.go.dev/testing/fstest)中提供了一个通用库，名为[`fstest.TestFS`](https://pkg.go.dev/testing/fstest#TestFS)。这个API将实现作为一个黑箱来处理，以确保它维护了`io/fs`契约的最基本部分。

#### 撰写验收测试

现在我们知道了什么是验收测试以及为什么要使用验收测试，让我们来探讨为`package chess`建立一个验收测试，这是一个用于模拟国际象棋游戏的包。`chess` 的用户应该实现 `chess.Player` 接口。这些实现是我们要验证的主要内容。我们的验收测试关注的是棋手的实现是否走了合法的棋，而不是这些棋是否聪明。

1.为验证行为创建一个新的包，[习惯上命名为](https://google.github.io/styleguide/go/best-practices#naming-doubles-helper-package)，在包名后面加上 "test "一词（例如：`chesstest`）。

2.创建执行验证的函数，接受被测试的实现作为参数，并对其进行练习：

```go
// ExercisePlayer tests a Player implementation in a single turn on a board.
// The board itself is spot checked for sensibility and correctness.
//
// It returns a nil error if the player makes a correct move in the context
// of the provided board. Otherwise ExercisePlayer returns one of this
// package's errors to indicate how and why the player failed the
// validation.
func ExercisePlayer(b *chess.Board, p chess.Player) error
```

测试应该注意哪些不变式被破坏，以及如何破坏。你的设计可以选择两种失败报告的原则：

- **快速失败**：一旦实现违反了一个不变式，就返回一个错误。

  这是最简单的方法，如果预计验收测试会快速执行，那么它的效果很好。简单的错误 [sentinels](https://google.github.io/styleguide/go/index.html#gotip)和[自定义类型](https://google.github.io/styleguide/go/index.html#gotip)在这里可以很容易地使用，反过来说，这使得测试验收测试变得很容易。

  ```go
  for color, army := range b.Armies {
      // The king should never leave the board, because the game ends at
      // checkmate.
      if army.King == nil {
          return &MissingPieceError{Color: color, Piece: chess.King}
      }
  }
  ```

- **集合所有的失败**：收集所有的失败，并报告它们。
  这种方法类似于[keep going](https://google.github.io/styleguide/go/decisions#keep-going)的指导，如果验收测试预计会执行得很慢，这种方法可能更可取。

  你如何聚集故障，应该由你是否想让用户或你自己有能力询问个别故障（例如，为你测试你的验收测试）来决定的。下面演示了使用一个[自定义错误类型](https://google.github.io/styleguide/go/index.html#gotip)，[聚合错误](https://google.github.io/styleguide/go/index.html#gotip)。

  ```go
  var badMoves []error
  
  move := p.Move()
  if putsOwnKingIntoCheck(b, move) {
      badMoves = append(badMoves, PutsSelfIntoCheckError{Move: move})
  }
  
  if len(badMoves) > 0 {
      return SimulationError{BadMoves: badMoves}
  }
  return nil
  ```


验收测试应该遵守 [keep going](https://google.github.io/styleguide/go/decisions#keep-going) 的指导，不调用`t.Fatal`，除非测试检测到被测试系统中的不变量损坏。
例如，`t.Fatal`应该保留给特殊情况，如[设置失败](https://google.github.io/styleguide/go/best-practices#test-helper-error-handling)，像往常一样：

```go
func ExerciseGame(t *testing.T, cfg *Config, p chess.Player) error {
    t.Helper()

    if cfg.Simulation == Modem {
        conn, err := modempool.Allocate()
        if err != nil {
            t.Fatalf("no modem for the opponent could be provisioned: %v", err)
        }
        t.Cleanup(func() { modempool.Return(conn) })
    }
    // Run acceptance test (a whole game).
}
```

这种技术可以帮助你创建简明、规范的验证。但不要试图用它来绕过[断言指南](https://google.github.io/styleguide/go/decisions#assert)。
最终产品应该以类似这样的形式提供给终端用户：

```go
// Good:
package deepblue_test

import (
    "chesstest"
    "deepblue"
)

func TestAcceptance(t *testing.T) {
    player := deepblue.New()
    err := chesstest.ExerciseGame(t, chesstest.SimpleGame, player)
    if err != nil {
        t.Errorf("deepblue player failed acceptance test: %v", err)
    }
}
```

### 使用真正的传输工具

当测试组件集成时，特别是 HTTP 或 RPC 被用作组件之间的底层传输时，最好使用真正的底层传输来连接到测试版本的后端。

例如，假设你要测试的代码（有时被称为 "被测系统 "或SUT）与实现[长期运行操作](https://pkg.go.dev/google.golang.org/genproto/googleapis/longrunning) API 的后端交互。为了测试你的 SUT，使用一个真正的[OperationsClient](https://pkg.go.dev/google.golang.org/genproto/googleapis/longrunning#OperationsClient)，它连接到[OperationsServer](https://en.wikipedia.org/wiki/Test_double)的[替身测试](例如，mock、stub或fake)上。

为了确保测试代码贴切于生产环境，相对于使用手工实现的客户端，我们更加推荐使用生产的客户端和专用的测试服务器来模拟生产环境的复杂性。

**提示：**在可能的情况下，使用由被测服务的作者提供的测试库。

### [`t.Error` vs. `t.Fatal`](https://google.github.io/styleguide/go/best-practices#terror-vs-tfatal)

正如在[执行策略](https://google.github.io/styleguide/go/decisions#keep-going)中讨论的一样, 测试过程不应该在遇到问题的地方中断。

然而，有些情况需要终止当前测试。当某些测试需要标记失败时，调用t.Fatal是合适的，特别是在 使用测试辅助函数时，没有它，你就不能运行测试的其余部分。在表格驱动的测试中，t.Fatal适合于在测试在进入循环之前整个测试函数标记为失败状态。它只会影响整个测试列表中被标记为失败的测试函数不能继续向前推进, 而不会影响其他的测试函数, 所以, 错误报告应该像下面这样:

- 如果你不使用 `t.Run子` 测试，使用 `t.Error`，后面跟一个 `continue` 语句，继续到下一个测试项。
- 如果你使用子测试（并且你在调用`t.Run`时），使用`t.Fatal`，结束当前子测试，并允许你的测试用例进入下一个子测试。

**警告：**调用和`t.Fatal`和类似函数并不总是安全的。[更多细节在这里](https://google.github.io/styleguide/go/best-practices#t-fatal-goroutine)。

### 在测试辅助函数中处理错误

**注意：**本节讨论的[测试辅助函数](https://google.github.io/styleguide/go/decisions#mark-test-helpers)是 Go 使用的术语：这些函数用于准备测试环境和清理测试现场，而不是普通的断言设施。更多的讨论请参见 [test functions](https://google.github.io/styleguide/go/best-practices#test-functions) 部分。

由测试辅助函数执行的操作有时会失败。例如，设置一个带有文件的目录涉及到 I/O，这可能会失败。当测试辅助函数失败时，它们的失败往往标志着测试不能继续，因为一个设置的前提条件失败了。当这种情况发生时，最好在辅助函数中调用一个`Fatal`函数：

```go
// Good:
func mustAddGameAssets(t *testing.T, dir string) {
    t.Helper()
    if err := os.WriteFile(path.Join(dir, "pak0.pak"), pak0, 0644); err != nil {
        t.Fatalf("Setup failed: could not write pak0 asset: %v", err)
    }
    if err := os.WriteFile(path.Join(dir, "pak1.pak"), pak1, 0644); err != nil {
        t.Fatalf("Setup failed: could not write pak1 asset: %v", err)
    }
}
```

这就使调用测试辅助函数返回错误给测试本身更清晰：

```go
// Bad:
func addGameAssets(t *testing.T, dir string) error {
    t.Helper()
    if err := os.WriteFile(path.Join(d, "pak0.pak"), pak0, 0644); err != nil {
        return err
    }
    if err := os.WriteFile(path.Join(d, "pak1.pak"), pak1, 0644); err != nil {
        return err
    }
    return nil
}
```

**警告：**调用和 `t.Fatal`类似函数并不总是安全的。点击这里查看[更多细节](https://google.github.io/styleguide/go/best-practices#t-fatal-goroutine)。

失败信息应该包括对错误的详细描述信息。这一点很重要，因为你可能会向许多用户提供测试 API，特别是在测试辅助函数中产生错误的场景增多时。用户应该知道在哪里，以及为什么产生错误。

**提示：** Go 1.14引入了一个[`t.Cleanup`](https://pkg.go.dev/testing#T.Cleanup)函数，可以用来注册清理函数，在你的测试完成后运行。该函数也适用于测试辅助函数。参见 [GoTip #4: Cleaning Up Your Tests](https://google.github.io/styleguide/go/index.html#gotip) 以获得简化测试辅助程序的指导。

下面是一个名为`paint_test.go`的虚构文件中的片段，演示了`(*testing.T).Helper`如何影响 Go 测试中的失败报告：

```go
package paint_test

import (
    "fmt"
    "testing"
)

func paint(color string) error {
    return fmt.Errorf("no %q paint today", color)
}

func badSetup(t *testing.T) {
    // This should call t.Helper, but doesn't.
    if err := paint("taupe"); err != nil {
        t.Fatalf("could not paint the house under test: %v", err) // line 15
    }
}

func mustGoodSetup(t *testing.T) {
    t.Helper()
    if err := paint("lilac"); err != nil {
        t.Fatalf("could not paint the house under test: %v", err)
    }
}

func TestBad(t *testing.T) {
    badSetup(t)
    // ...
}

func TestGood(t *testing.T) {
    mustGoodSetup(t) // line 32
    // ...
}
```

下面是运行该输出的一个例子。请注意突出显示的文本和它的不同之处：

```go
=== RUN   TestBad
    paint_test.go:15: could not paint the house under test: no "taupe" paint today
--- FAIL: TestBad (0.00s)
=== RUN   TestGood
    paint_test.go:32: could not paint the house under test: no "lilac" paint today
--- FAIL: TestGood (0.00s)
FAIL
```

`paint_test.go:15`的错误是指在`badSetup`中失败的设置函数的那一行：
`t.Fatalf("could not paint the house under test: %v", err)`
而`paint_test.go:32`指的是在`TestGood`中失败的那一行测试：
`goodSetup(t)`。

正确地使用`(*testing.T).Helper`可以更好地归纳出失败的位置，当：

- 辅助函数数量增加
- 在辅助函数中使用其他的辅助函数
- 测试函数使用辅助函数的数量增加

**提示：**如果一个辅助函数调用`(*testing.T).Error`或`(*testing.T).Fatal`，在格式字符串中提供一些上下文，以帮助确定出错的原因。

**提示：**如果一个辅助函数没有做任何事情会导致测试失败，那么它就不需要调用`t.Helper`。通过从函数参数列表中删除`t`来简化其签名。

### 不要从独立的 goroutines 中调用`t.Fatal`

正如[package testing](https://pkg.go.dev/testing#T)中记载的那样，在测试函数或子测试函数之外的任何 goroutine 中调用 `t.FailNow`，`t.Fatal` 等都是不正确的。如果你的测试启动了新的 goroutine，它们不能从这些 goroutine 内部调用这些函数。

[测试辅助函数](https://google.github.io/styleguide/go/best-practices#test-functions)通常不会从新的 goroutine 发出失败信号，因此它们使用`t.Fatal`是完全正确的。如果有疑问，可以调用 t.Error 并返回。

```go
// Good:
func TestRevEngine(t *testing.T) {
    engine, err := Start()
    if err != nil {
        t.Fatalf("Engine failed to start: %v", err)
    }

    num := 11
    var wg sync.WaitGroup
    wg.Add(num)
    for i := 0; i < num; i++ {
        go func() {
            defer wg.Done()
            if err := engine.Vroom(); err != nil {
                // This cannot be t.Fatalf.
                t.Errorf("No vroom left on engine: %v", err)
                return
            }
            if rpm := engine.Tachometer(); rpm > 1e6 {
                t.Errorf("Inconceivable engine rate: %d", rpm)
            }
        }()
    }
    wg.Wait()

    if seen := engine.NumVrooms(); seen != num {
        t.Errorf("engine.NumVrooms() = %d, want %d", seen, num)
    }
}
```

在测试或子测试中添加`t.Parallel`并不会使调用`t.Fatal`变得不安全。

当所有对 `testing` API 的调用都在 [test function](https://google.github.io/styleguide/go/best-practices#test-functions) 中时，通常很容易发现不正确的用法，因为`go`关键字是显而易见的。传递`testing.T`参数会使跟踪这种用法更加困难。通常，传递这些参数的原因是为了引入一个测试辅助函数，而这些测试辅助函数不应该依赖于被测系统。因此，如果一个测试辅助函数[注册了一个致命的测试失败](https://google.github.io/styleguide/go/best-practices#test-helper-error-handling)，它可以而且应该从测试的 goroutine 中这样做。

### 对结构字使用字段标签

在表格驱动的测试中，最好为每个测试用例指定密钥。当测试用例覆盖了大量的垂直空间（例如，超过20-30行），当有相同类型的相邻字段，以及当你希望省略具有零值的字段时，这是有帮助的。比如说：

```go
// Good:
tests := []struct {
    foo     *pb.Foo
    bar     *pb.Bar
    want    string
}{
    {
        foo: pb.Foo_builder{
            Name: "foo",
            // ...
        }.Build(),
        bar: pb.Bar_builder{
            Name: "bar",
            // ...
        }.Build(),
        want: "result",
    },
}
```

### 保持设置代码在特定的测试范围内

在可能的情况下，资源和依赖关系的设置应该尽可能地与具体的测试用例密切相关。例如，给定一个设置函数：

```go
// mustLoadDataSet loads a data set for the tests.
//
// This example is very simple and easy to read. Often realistic setup is more
// complex, error-prone, and potentially slow.
func mustLoadDataset(t *testing.T) []byte {
    t.Helper()
    data, err := os.ReadFile("path/to/your/project/testdata/dataset")

    if err != nil {
        t.Fatalf("could not load dataset: %v", err)
    }
    return data
}
```

在需要的测试函数中明确调用`mustLoadDataset`：

```Go
// Good:
func TestParseData(t *testing.T) {
    data := mustLoadDataset(t)
    parsed, err := ParseData(data)
    if err != nil {
        t.Fatalf("unexpected error parsing data: %v", err)
    }
    want := &DataTable{ /* ... */ }
    if got := parsed; !cmp.Equal(got, want) {
        t.Errorf("ParseData(data) = %v, want %v", got, want)
    }
}

func TestListContents(t *testing.T) {
    data := mustLoadDataset(t)
    contents, err := ListContents(data)
    if err != nil {
        t.Fatalf("unexpected error listing contents: %v", err)
    }
    want := []string{ /* ... */ }
    if got := contents; !cmp.Equal(got, want) {
        t.Errorf("ListContents(data) = %v, want %v", got, want)
    }
}

func TestRegression682831(t *testing.T) {
    if got, want := guessOS("zpc79.example.com"), "grhat"; got != want {
        t.Errorf(`guessOS("zpc79.example.com") = %q, want %q`, got, want)
    }
}
```

测试函数`TestRegression682831`不使用数据集，因此不调用`mustLoadDataset`，这可能会很慢且容易失败：

```go
// Bad:
var dataset []byte

func TestParseData(t *testing.T) {
    // As documented above without calling mustLoadDataset directly.
}

func TestListContents(t *testing.T) {
    // As documented above without calling mustLoadDataset directly.
}

func TestRegression682831(t *testing.T) {
    if got, want := guessOS("zpc79.example.com"), "grhat"; got != want {
        t.Errorf(`guessOS("zpc79.example.com") = %q, want %q`, got, want)
    }
}

func init() {
    dataset = mustLoadDataset()
}
```

用户希望在与其他函数隔离的情况下运行一个函数，不应受到这些因素的影响：

```sh
# No reason for this to perform the expensive initialization.
$ go test -run TestRegression682831
```

#### 何时使用自定义的 `TestMain` 入口点

如果**包中的所有测试**都需要共同设置，并且**设置需要拆解**，你可以使用[自定义测试主入口](https://golang.org/pkg/testing/#hdr-Main)。如果测试用例所需的资源的设置特别昂贵，而且成本应该被摊销，就会发生这种情况。通常情况下，你在这一点上已经从测试套件中提取了任何无关的测试。它通常只用于[功能测试](https://en.wikipedia.org/wiki/Functional_testing)。

使用自定义的 `TestMain` **不应该是你的首选**，因为要正确使用它，必须要有足够的谨慎。首先考虑[_摊销普通测试设置_](https://google.github.io/styleguide/go/best-practices#t-setup-amortization)部分的解决方案或普通的[测试辅助函数](https://google.github.io/styleguide/go/best-practices#t-common-setup-scope)是否足以满足你的需求。

```go
// Good:
var db *sql.DB

func TestInsert(t *testing.T) { /* omitted */ }

func TestSelect(t *testing.T) { /* omitted */ }

func TestUpdate(t *testing.T) { /* omitted */ }

func TestDelete(t *testing.T) { /* omitted */ }

// runMain sets up the test dependencies and eventually executes the tests.
// It is defined as a separate function to enable the setup stages to clearly
// defer their teardown steps.
func runMain(ctx context.Context, m *testing.M) (code int, err error) {
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()

    d, err := setupDatabase(ctx)
    if err != nil {
        return 0, err
    }
    defer d.Close() // Expressly clean up database.
    db = d          // db is defined as a package-level variable.

    // m.Run() executes the regular, user-defined test functions.
    // Any defer statements that have been made will be run after m.Run()
    // completes.
    return m.Run(), nil
}

func TestMain(m *testing.M) {
    code, err := runMain(context.Background(), m)
    if err != nil {
        // Failure messages should be written to STDERR, which log.Fatal uses.
        log.Fatal(err)
    }
    // NOTE: defer statements do not run past here due to os.Exit
    //       terminating the process.
    os.Exit(code)
}
```

理想情况下，一个测试用例在自身的调用和其他测试用例之间是密封的。

至少要确保单个测试用例重置他们所修改的任何全局状态，如果他们已经这样做了（例如，如果测试是与外部数据库一起工作）。

#### 摊销共同测试设置

如果普通设置中存在以下情况，使用 `sync.Once`  可能是合适的，尽管不是必须的。

- 它很昂贵。
- 它只适用于某些测试。
- 它不需要拆解。

```go
// Good:
var dataset struct {
    once sync.Once
    data []byte
    err  error
}

func mustLoadDataset(t *testing.T) []byte {
    t.Helper()
    dataset.once.Do(func() {
        data, err := os.ReadFile("path/to/your/project/testdata/dataset")
        // dataset is defined as a package-level variable.
        dataset.data = data
        dataset.err = err
    })
    if err := dataset.err; err != nil {
        t.Fatalf("could not load dataset: %v", err)
    }
    return dataset.data
}
```

当`mustLoadDataset` 被用于多个测试函数时，其成本被摊销：

```go
// Good:
func TestParseData(t *testing.T) {
    data := mustLoadDataset(t)

    // As documented above.
}

func TestListContents(t *testing.T) {
    data := mustLoadDataset(t)

    // As documented above.
}

func TestRegression682831(t *testing.T) {
    if got, want := guessOS("zpc79.example.com"), "grhat"; got != want {
        t.Errorf(`guessOS("zpc79.example.com") = %q, want %q`, got, want)
    }
}
```

普通拆解之所以棘手，是因为没有统一的地方来注册清理线程。如果设置函数（本例中为`loadDataset`）依赖于上下文，`sync.Once`可能会有问题。这是因为对设置函数的两次调用中的第二次需要等待第一次调用完成后再返回。这段等待时间不容易做到尊重上下文的取消。

## 字符串拼接

在 Go 中，有几种字符串拼接的方法。包括下面几种例子：

- "+"运算符
- `fmt.Sprintf`
- `strings.Builder `
- `text/template`
- `safehtml/template`

尽管选择哪种方法没有一刀切的规则，但下面的指南概述了在什么情况下哪种方法是首选。

### 简单情况下，首选 "+"

当连接几个字符串时，更愿意使用 "+"。这种方法在语法上是最简单的，不需要导入包。

```go
// Good:
key := "projectid: " + p
```

### 格式化时首选`fmt.Sprintf`

当建立一个带有格式化的复杂字符串时，倾向于使用`fmt.Sprintf`。使用许多 "+"运算符可能会掩盖最终的结果。

```go
// Good:
str := fmt.Sprintf("%s [%s:%d]-> %s", src, qos, mtu, dst)
```

```go
// Bad:
bad := src.String() + " [" + qos.String() + ":" + strconv.Itoa(mtu) + "]-> " + dst.String()
```

**最佳做法：**当构建字符串操作的输出是一个`io.Writer`时，不要用`fmt.Sprintf`构建一个临时字符串，只是为了把它发送给 Writer。相反，使用`fmt.Fprintf`来直接向 Writer 发送。

当格式化更加复杂时，请酌情选择 [`text/template`](https://pkg.go.dev/text/template) 或 [`safehtml/template`](https://pkg.go.dev/github.com/google/safehtml/template)。

### 倾向于使用`strings.Builder`来零散地构建一个字符串

在逐位建立字符串时，更倾向于使用`strings.Builder`。`strings.Builder`需要摊销的线性时间，而 "+"和`fmt.Sprintf`在连续调用以形成一个较大的字符串时需要二次时间。

```go
// Good:
b := new(strings.Builder)
for i, d := range digitsOfPi {
    fmt.Fprintf(b, "the %d digit of pi is: %d\n", i, d)
}
str := b.String()
```

**注意**。更多的讨论，请参见[GoTip #29: 高效地构建字符串](https://google.github.io/styleguide/go/index.html#gotip)。

### 常量字符串

在构建常量、多行字符串变量时，倾向于使用反引号（`）。

```go
// Good:
usage := `Usage:

custom_tool [args]`
```

```go
// Bad:
usage := "" +
  "Usage:\n" +
  "\n" +
  "custom_tool [args]"
```