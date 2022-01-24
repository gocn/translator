# Go2.0 展望

- 原文地址：https://www.sethvargo.com/what-id-like-to-see-in-go-2
- 原文作者：Seth Vargo
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w03_What_id_like_to_see_in_go2
- 译者：[1-st](https://github.com/1-st)
- 校对：[cuua](https://github.com/cuua)
 
![What id like to see in go2](https://raw.githubusercontent.com/gocn/translator/master/static/images/2022/w03_Waht_id_like_to_see_in_go2/what-id-like-to-see-in-go-2.jpg) 

Go是我最喜欢的编程语言之一，但它离完美还很远。在过去的10年里，我使用Go来构建小项目和大规模应用程序。虽然从2009年的最初版本开始，Go已经有了很大的发展，但本文仍然要强调一些我认为Go语言可以改进的地方。

在我们开始之前，我想明确一点:我不是在批评一些人或他们的贡献。我唯一的目的就是让Go成为最好的编程语言。

## 一个现代模板引擎

Go标准库有两个模板包: text/template 和 html/template. 他们几乎用着同样的语法, 但是 html/template 处理实体转义和一些其他的web特定构造. 不幸的是，如果不进行大量的开发人员投入，这两个包对于高级用例来说都不够合适和强大。

- **编译时错误**。 不像Go本身，Go模板包会很乐意让你以字符串形式传递一个整数，只是在运行时呈现一个错误。这意味着开发人员需要严格地测试模板中所有可能的输入，而不是依赖于类型系统。Go的模板包应该支持编译时类型检查。

- **匹配Go的range子句** 。10年过去了，我仍然把Go模板中range子句的顺序搞得一团糟，因为它有时是向后的。使用两个参数，模板引擎匹配标准库:

  ```go
  {{ range $a, $b := .Items }} // [$a = 0, $b = "foo"]
  for a, b := range items { // [a = 0, b = "foo"]
  ```
  然而，只有一个参数时，模板引擎会生成值，而Go呈现时会生成索引:

  ```go
  {{ range $a := .Items }} // [$a = "foo"]
  for a := range items { // [a = 0]
  ```
  Go的模板包应该与标准库的工作方式相匹配。

- **功能齐备，反射可选**。作为一个普遍的规则，我认为大多数开发者不应该需要与反射交互。然而，如果你想做一些基本的加法和减法之外的事情，Go的模板包将迫使你使用反射。内置函数非常小，只满足用例的一小部分。

  在我编写了[Consul Template](https://github.com/hashicorp/consul-template)之后，很明显，标准的Go模板功能不足以满足用户的需求。超过一半的问题是关于尝试使用Go的模板语言。今天，Consul Template拥有[超过50个“助手”函数](https://github.com/hashicorp/consul-template/blob/master/docs/templating-language.md)，其中绝大多数应该使用标准模板语言。

  Consul Template并不是唯一一个这样做的。[Hugo](https://gohugo.io/)也有一个[非常广泛的助手函数列表](https://gohugo.io/functions/)，同样，其中绝大多数应该是在标准的模板语言中。甚至在我最近的项目[Exposure Notifications](https://g.co/ens)中，我们[无法逃避反射](https://github.com/google/exposure-notifications-verification-server/blob/0ec489ba95137d5be10e1617d1dcdc2d1ee6e5e9/pkg/render/renderer.go#L232-L280)。

  Go的模板语言确实需要更大的函数表。

- **短路评估**。

  编辑:正如许多人指出的那样，这个特性将会在Go 1.18中出现(https://tip.golang.org/doc/go1.18#text/template)。

  Go的模板语言总是在子句中计算整个条件，这导致了一些非常有趣的bug(同样，这些bug在运行时才会显示出来)。考虑下面的例子，其中$foo可以是nil:
  ```go
  {{if (and $foo $foo. bar)}}
  ```
  这看起来似乎很好，但是和条件都将被求值——表达式中没有短路逻辑。这意味着如果$foo为nil，这将抛出一个运行时异常。

  为了解决这个问题，你必须将条件句分开:
  ```go
  {{if $foo}}
  {{如果$ foo。酒吧}}
  {{结束}}
  ```
  Go的模板语言应该像标准库一样，在第一个值为真时停止执行条件。

- **往网络专用库投入精力**。我是一名经验丰富的Ruby on Rails开发人员，我非常喜欢它能够轻松地构建漂亮的web应用程序。使用Go的模板语言，即使是最简单的任务——比如将条目列表打印成一个句子——对于初学者来说也是无法实现的，尤其是与Rails的Enumerable#to_sentence相比

## 改进 range ,以便不用复制值
虽然有很好的文档，但是range子句中的值总是会被复制。例如，考虑以下代码:
```go
type Foo struct {
  bar string
}

func main() {
  list := []Foo{{"A"}, {"B"}, {"C"}}

  cp := make([]*Foo, len(list))
  for i, value := range list {
    cp[i] = &value
  }

  fmt.Printf("list: %q\n", list)
  fmt.Printf("cp: %q\n", cp)
}
```
cp的值是什么？如果你认为是[A B C],不好意思你错了，正确的值是[C C C]

```go
  [C C C]
```
这是因为go在range子句里使用了复制品而不是元素本身。 在Go2.0中，range子句应该采取引用传值. 在这方面已经有了些许提案, 包括 [improve for-loop ergonomics](https://github.com/golang/go/issues/24282) 和 [redefine range loop variables in each iteration](https://github.com/golang/go/issues/20733), 所以我非常希望能有这样的改动.

## 决定性的 select
在一个select语句的多个条件为真的情况下，胜出的情况是通过一致的伪随机选择来选择的。这是一个非常微妙的错误来源，而且类似的switch语句会加重这种错误，switch语句按照写入的顺序求值。

考虑下面的代码，我们希望其表现是“如果系统停止了，什么也不做；否则等待5秒，然后提示超时":
```go
for {
  select {
  case <-doneCh: // or <-ctx.Done():
    return
  case thing := <-thingCh:
    // ... long-running operation
  case <-time.After(5*time.Second):
    return fmt.Errorf("timeout")
  }
}
```
如果在进入select语句时多个条件为真(例如doneCh是关闭的，已经超过5秒)，则该路径将执行的行为是未知的。这使得编写正确的取消代码非常繁琐:
```go
for {
  // Check here in case we've been CPU throttled for an extended time, we need to
  // check graceful stop or risk returning a timeout error.
  select {
  case <-doneCh:
    return
  default:
  }

  select {
  case <-doneCh:
    return
  case thing := <-thingCh:
    // Even though this case won, we still might ALSO be stopped.
    select {
    case <-doneCh:
      return
    default:
    }
    // ...
  default <-time.After(5*time.Second):
    // Even though this case won, we still might ALSO be stopped.
    select {
    case <-doneCh:
      return
    default:
    }
    return fmt.Errorf("timeout")
  }
}
```
如果select被更新为确定性的，那么原始代码(在我看来更简单、更容易获得)就会像预期的那样工作。然而，由于选择的非确定性，我们必须不断地检查优势条件。

与此相关的是，我希望看到“如果这个通道包含任何消息，则从它读取，否则继续”的简写语法,而当前的语法是冗余的:
```go
select {
case <-doneCh:
  return
default:
}
我希望看到这个检查的更简洁的版本，可能是这样的语法:
select <-?doneCh: // not valid Go
```
## 结构化日志接口
Go的标准库包含了日志包，这对于基本的使用是很好的。然而，大多数生产系统都需要结构化日志记录，并且Go语言[不缺少](https://www.client9.com/logging-packages-in-golang/)结构化的日志库:

- [apex/log](https://github.com/apex/log)
- [go-kit/log](https://github.com/go-kit/kit/tree/master/log)
- [golang/glog](https://github.com/golang/glog)
- [hashicorp/go-hclog](https://github.com/hashicorp/go-hclog)
- [inconshreveable/log15](https://github.com/inconshreveable/log15)
- [rs/zerolog](https://github.com/rs/zerolog)
- [sirupsen/logrus](https://github.com/sirupsen/logrus)
- [uber/zap](https://github.com/uber-go/zap) 

Go在这方面的意见缺乏导致了这些包的泛滥，其中大多数具有不功能和标识符都不兼容。因此，库作者不可能作出结构化的日志。例如,我希望能够实现结构化登录[go-retry](https://github.com/sethvargo/go-retry), [go-envconfig](https://github.com/sethvargo/go-envconfig),或[go-githubactions](https://github.com/sethvargo/go-githubactions),但这样做需要与其中一个库紧密耦合。理想情况下，我希望我的库用户能够选择他们的结构日志记录解决方案，但是缺乏用于结构日志记录的通用接口使这变得非常困难。

Go标准库需要定义一个结构化的日志接口，所有这些现有的上游包可以选择实现这个接口。然后，作为一个库作者，我可以选择接受log.StructuredLogger接口并且实现者可以做出自己的选择:
```go
func WithLogger(l log.StructuredLogger) Option {
  return func(f *Foo) *Foo {
    f.logger = l
    return f
  }
}
```
我做出了这种interface的草稿
```go
// StructuredLogger is an interface for structured logging.
type StructuredLogger interface {
  // Log logs a message.
  Log(message string, fields ...LogField)

  // LogAt logs a message at the provided level. Perhaps we could also have
  // Debugf, Infof, etc, but I think that might be too limiting for the standard
  // library.
  LogAt(level LogLevel, message string, fields ...LogField)

  // LogEntry logs a complete log entry. See LogEntry for the default values if
  // any fields are missing.
  LogEntry(entry *LogEntry)
}

// LogLevel is the underlying log level.
type LogLevel uint8

// LogEntry represents a single log entry.
type LogEntry struct {
  // Level is the log level. If no level is provided, the default level of
  // LevelError is used.
  Level LogLevel

  // Message is the actual log message.
  Message string

  // Fields is the list of structured logging fields. If two fields have the same
  // Name, the later one takes precedence.
  Fields []*LogField
}

// LogField is a tuple of the named field (a string) and its underlying value.
type LogField struct {
  Name  string
  Value interface{}
}
```
关于实际的接口可能是什么样子、如何最小化分配以及如何最大化兼容性有很多讨论，但我们的目标是定义一个其他日志库可以轻松实现的接口。

在我的Ruby时代，Ruby版本管理器的数量激增，每个版本管理器都有自己的dotfile名称和语法。Fletcher Nichol仅仅通过[写一个gist](https://gist.github.com/fnichol/1912050)就成功地说服了所有Ruby版本管理器的维护者对.ruby-version进行标准化。我希望我们可以在Go社区做一些类似的结构化日志记录。

## 多错误处理
在很多情况下，特别是在后台任务或周期性任务中，系统可能并行处理一些事情或在错误时继续处理。在这些情况下，返回一个多重错误是有帮助的。标准库中没有处理错误集合的内置支持。

围绕多错误处理拥有清晰而简明的标准库定义可以统一社区，并减少错误处理不当的风险，就像我们在error wrapping和unwrapping时看到的那样。

## JSON 序列化error
说到error，您知道将error类型嵌入到结构字段中，然后将该结构序列化为JSON时候会将error字段序列化为{}吗?
```go
// https://play.golang.org/p/gl7BPJOgmjr
package main

import (
  "encoding/json"
  "fmt"
)

type Response1 struct {
  Err error `json:"error"`
}

func main() {
  v1 := &Response1{Err: fmt.Errorf("oops")}
  b1, err := json.Marshal(v1)
  if err != nil {
    panic(err)
  }

  // got: {"error":{}}
  // want: {"error": "oops"}
  fmt.Println(string(b1))
}
```
至少对于内置的errorString类型，Go应该作为.Error()的结果进行序列化。另外，对于Go2.0，当试图序列化一个error类型而没有实现自定义序列化逻辑时，JSON序列化可能会返回一个error。

## 标准库中不再有公共变量
这只是一个例子，两者都是http.DefaultClient和http.DefaultTransport具有共享状态的全局变量。http.DefaultClient没有配置超时，这使得创建自己的服务很简单，并容易产生瓶颈。许多包会改变http.DefaultClient和http.DefaultTransport，这可能会浪费开发人员数天的成本来追踪错误。

Go 2.0应该将这些变量设为私有的，并通过一个函数调用来公开它们，该函数调用将返回有问题的变量的唯一分配。或者，Go 2.0可以实现“冻结”全局变量，这样它们就不会被其他包改变。

从软件供应链的角度来看，我也担心这类问题。如果我能开发一个有用的包，秘密修改http.DefaultTransport使用自定义的RoundTripper，通过我的服务器过滤您的所有流量，这将是一个非常糟糕的时刻。

## 缓冲渲染的原生支持
这更像是一件“不为人知或没有记录在案的事情”。大多数例子，包括Go文档中的例子，都鼓励通过web请求来序列化JSON或渲染HTML:
```go
func toJSON(w http.ResponseWriter, i interface{}) {
  if err := json.NewEncoder(w).Encode(i); err != nil {
    http.Error(w, "oops", http.StatusInternalServerError)
  }
}

func toHTML(w http.ResponseWriter, tmpl string, i interface{}) {
  if err := templates.ExecuteTemplate(w, tmpl, i); err != nil {
    http.Error(w, "oops", http.StatusInternalServerError)
  }
}
```
但是，对于这两种情况，如果i足够大，那么在第一个字节(和200状态码)被发送之后，encoding/execution就可能失败。此时，请求是不可恢复的，因为您不能更改响应代码。

为了缓解这个问题，被广泛接受的解决方案是先渲染，然后复制到w。这仍然为错误留下一个小空间(写入w会由于连接问题失败)，但它确保在发送第一个字节之前encoding/execution是成功的。然而，为每个请求分配一个byte slice的代价可能很高，所以通常[使用缓冲池](https://github.com/google/exposure-notifications-verification-server/blob/08797939a56463fe85f0d1b7325374821ee31448/pkg/render/html.go#L65-L91)。

这种方法非常冗长，给实现者带来了很多不必要的复杂性。相反，如果Go能够自动管理这个缓冲池将会很棒，可能可以使用EncodePooled这样的函数。

## 结束语
Go仍然是我最喜欢的编程语言之一，这也是我乐于强调这些批评的原因。与任何编程语言一样，Go也在不断发展。你认为这些是好主意吗?或者它们是糟糕的建议?请在[Twitter](https://twitter.com/sethvargo)上告诉我!

Copyright © 2022 Seth Vargo • Licensed under the [CC BY-NC 4.0 license](https://www.sethvargo.com/license).
