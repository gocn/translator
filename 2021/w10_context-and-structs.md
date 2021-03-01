```
原文地址：https://blog.golang.org/context-and-structs
原文作者：Jean de Klerk, Matt T. Proud
译者：Kevin
```


## 介紹

在许多Go API中，尤其是现代的API中，函数和方法的第一个参数通常是[`context.Context`](https://golang.org/pkg/context/)。上下文（Context）提供了一种方法，用于跨API边界和进程之间传输截止时间、调用者取消和其他请求范围的值。当一个库与远程服务器（如数据库、API等）直接或间接交互时，经常会用到它。

在[context的文档](https://golang.org/pkg/context/)中写道。

    上下文不应该存储在结构类型里面，而是传递给每个需要它的函数。

本文对这一建议进行了扩展，用具体例子解析为什么传递上下文而不是将其存储在其他类型中很重要。它还强调了一种罕见的情况，即在结构类型中存储上下文可能是有意义的，以及如何安全地这样做。

## 倾向于将上下文作为参数传递

为了深入理解不在结构中存储上下文的建议，我们来考虑一下首选的上下文作为参数的方法。

```go
type Worker struct { /* … */ }

type Work struct { /* … */ }

func New() *Worker {
  return &Worker{}
}

func (w *Worker) Fetch(ctx context.Context) (*Work, error) {
  _ = ctx // 每次调用中ctx用于取消操作，截止时间和元数据。
}

func (w *Worker) Process(ctx context.Context, w *Work) error {
  _ = ctx // A每次调用中ctx用于取消操作，截止时间和元数据。
}
```

在这个例子中，`(*Worker).Fetch`和`(*Worker).Process`方法都直接接受上下文。通过这种通过参数传递的设计，用户可以设置每次调用的截止时间、取消和元数据。而且，很清楚传递给每个方法的`context.Context`将如何被使用：没有期望传递给一个方法的`context.Context`将被任何其他方法使用。这是因为上下文的范围被限定在了小范围的必须操作内，这大大增加了这个包中上下文的实用性和清晰度。

## 将上下文存储在结构中会导致混乱

让我们再次使用上下文存储在结构体中这种方式审视一下上面的`Worker`例子。它的问题是，当你把上下文存储在一个结构中时，你会向调用者隐藏它的生命周期，甚至可能的是把两个不同的作用域以不可预料的方式互相干扰：

```go
type Worker struct {
  ctx context.Context
}

func New(ctx context.Context) *Worker {
  return &Worker{ctx: ctx}
}

func (w *Worker) Fetch() (*Work, error) {
  _ = w.ctx // 共享的w.ctx用于取消操作，截止时间和元数据。
}

func (w *Worker) Process(w *Work) error {
  _ = w.ctx // 共享的w.ctx用于取消操作，截止时间和元数据。
}
```

`(*Worker).Fetch`和`(*Worker).Process`方法都使用存储在`Worker`中的上下文。这防止了`Fetch`和`Process`的调用者（它们本身可能有不同的上下文）在每次调用的基础上指定截止日期、请求取消和附加元数据。例如：用户无法只为`(*Worker).Fetch`提供截止日期，也无法只取消`(*Worker).Process`的调用。调用者的生命期与共享上下文交织在一起，上下文的范围是创建`Worker`的生命周期。

与上下文作为参数的方法相比，该API也更容易让用户感到疑惑。用户可能会问自己：

* 既然`New`需要一个`context.Context`，那么构造函数是否在做取消或截止时间控制的工作？
* `New`传递进来的`context.Context`是否适用于`(*Worker).Fetch`和`(*Worker).Process`？都不适用？有一个而没有另一个？

API需要大量的文档来明确告诉用户`context.Context`到底是用来做什么的。用户可能还需要阅读代码，而不是能够依靠API结构获得信息。

最后，如果设计一个生产级服务器，其每个请求没有上下文，从而不能充分重视取消操作，这可能是相当危险的。如果没有能力设置每个调用的截止日期，[你的进程可能会积压资源](https://sre.google/sre-book/handling-overload/)并导致资源耗尽（如内存）!

## 规则的例外：保存向后的兼容性

当[引入context.Context](https://golang.org/doc/go1.7)的Go 1.7发布时，大量的 API 必须以向后兼容的方式添加上下文支持。例如，[`net/http`的`Client`方法](https://golang.org/pkg/net/http/)，如`Get`和`Do`，就是很好的上下文取消操作的应用。每一个用这些方法发送的外部请求都会受益于`context.Context`带来的截止时间、取消和元数据支持。

有两种方法可以以向后兼容的方式添加对`context.Context`的支持：将上下文包在一个结构中，正如我们稍后将看到的那样；复制函数，复制的函数接受`context.Context`作为参数，并将`Context`作为其函数名的后缀。复制的方法应该比在结构体中嵌入上下文的方式更可取，在[保持模块的兼容性](https://blog.golang.org/module-compatibility)中会进一步讨论。然而，在某些情况下，这是不切实际的：例如，如果你的API暴露了大量的函数，那么复制所有的函数可能是不可行的。

`net/http`包选择了上下文存储在结构体方式，这提供了一个有用的案例研究。让我们看看`net/http`的`Do`方法。在引入`context.Context`之前，`Do`的定义如下：

```go
func (c *Client) Do(req *Request) (*Response, error)
```

在Go 1.7之后，如果不考虑破坏向后的兼容性的问题，Do可能看起来像下面这样：

```go
func (c *Client) Do(ctx context.Context, req *Request) (*Response, error)
```

但是，保留向后的兼容性，遵守[Go 1的兼容性承诺](https://golang.org/doc/go1compat)对于标准库来说是至关重要的。所以，维护者选择在`http.Request`结构上添加一个`context.Context`，以便在不破坏向后兼容性的情况下支持`context.Context`：

```go
type Request struct {
  ctx context.Context

  // ...
}

func NewRequestWithContext(ctx context.Context, method, url string, body io.Reader) (*Request, error) {
  // 为了本文演示需要做了简化。
  return &Request{
    ctx: ctx,
    // ...
  }
}

func (c *Client) Do(req *Request) (*Response, error)

```

当改造你的API以支持上下文时，像上面那样在一个结构中添加一个`context.Context`可能是有意义的。但是，你需要首先考虑复制你的函数，这样可以在不牺牲实用性和理解性的前提下，向后兼容地改造`context.Context`。例如：

```go
func (c *Client) Call() error {
  return c.CallContext(context.Background())
}

func (c *Client) CallContext(ctx context.Context) error {
  // ...
}
```

## 总结

上下文使得重要的跨库和跨API信息很容易在调用栈中传播。但是，为了保持可理解性、易调试性和有效性，必须统一清晰地使用它。

当作为方法中的第一个参数而不是存储在结构类型中时，用户可以充分利用它的可扩展性，以便通过调用栈建立一个强大的取消、截止日期和元数据信息树。而且，最重要的是，当它作为一个参数传递进来时，它的范围被清晰的理解，从而导致堆栈上下的理解更加清晰和调试更加容易。

当设计一个带有上下文的API时，请记住这样的建议：将`context.Context`作为一个参数传递进来，不要将它存储在结构体中。
