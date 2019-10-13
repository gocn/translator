# Uber Go 语言代码风格指南

- 原文地址：https://github.com/uber-go/guide/blob/master/style.md
- 译文出处：https://github.com/uber-go/guide
- 本文永久链接：https://github.com/gocn/translator/blob/master/2019/w38_uber_go_style_guide.md
- 译者：[咔叽咔叽](https://github.com/watermelo)
- 校对者：[fivezh](https://github.com/fivezh)，[cvley](https://github.com/cvley)

## 目录

- [介绍](#introduction)
- [指南](#guidelines)
  - [接口的指针](#pointers-to-interfaces)
  - [接收者和接口](#receivers-and-interfaces)
  - [零值 Mutexes 是有效的](#zero-value-mutexes-are-valid)
  - [复制 Slice 和 Map](#copy-slices-and-maps-at-boundaries)
  - [Defer 的使用](#defer-to-clean-up)
  - [channel 的大小是 1 或者 None](#channel-size-is-one-or-none)
  - [枚举值从 1 开始](#start-enums-at-one)
  - [Error 类型](#error-types)
  - [Error 包装](#error-wrapping)
  - [处理类型断言失败](#handle-type-assertion-failures)
  - [避免 Panic](#dont-panic)
  - [使用 go.uber.org/atomic](#use-gouberorgatomic)
- [性能](#performance)
  - [strconv 优于 fmt](#prefer-strconv-over-fmt)
  - [避免 string 到 byte 的转换](#avoid-string-to-byte-conversion)
- [代码样式](#style)
  - [聚合相似的声明](#group-similar-declarations)
  - [包的分组导入的顺序](#import-group-ordering)
  - [包命名](#package-names)
  - [函数命名](#function-names)
  - [别名导入](#import-aliasing)
  - [函数分组和顺序](#function-grouping-and-ordering)
  - [减少嵌套](#reduce-nesting)
  - [不必要的 else](#unnecessary-else)
  - [顶层变量的声明](#top-level-variable-declarations)
  - [在不可导出的全局变量前面加上 _](#prefix-unexported-globals-with-_)
  - [结构体的嵌入](#embedding-in-structs)
  - [使用字段名去初始化结构体](#use-field-names-to-initialize-structs)
  - [局部变量声明](#local-variable-declarations)
  - [nil 是一个有效的 slice](#nil-is-a-valid-slice)
  - [减少变量的作用域](#reduce-scope-of-variables)
  - [避免裸参数](#avoid-naked-parameters)
  - [使用原生字符串格式来避免转义](#use-raw-string-literals-to-avoid-escaping)
  - [初始化结构体](#initializing-struct-references)
  - [在 Printf 之外格式化字符串](#format-strings-outside-printf)
  - [Printf-style 函数的命名](#naming-printf-style-functions)
- [设计模式](#patterns)
  - [表格驱动测试](#test-tables)
  - [函数参数可选化](#functional-options)

## 介绍

代码风格是代码的一种约定。用风格这个词可能有点不恰当，因为这些约定涉及到的远比源码文件格式工具 gofmt 所能处理的更多。

本指南的目标是通过详细描述 Uber 在编写 Go 代码时的取舍来管理代码的这种复杂性。这些规则的存在是为了保持代码库的可管理性，同时也允许工程师更高效地使用 go 语言特性。

本指南最初由 [Prashant Varanasi] 和 [Simon Newton] 为了让同事们更便捷地使用 go 语言而编写。多年来根据其他人的反馈进行了一些修改。

  [Prashant Varanasi]: https://github.com/prashantv
  [Simon Newton]: https://github.com/nomis52

本文记录了 uber 在使用 go 代码中的一些习惯用法。许多都是 go 语言常见的指南，而其他的则延伸到了一些外部资料：

1. [Effective Go](https://golang.org/doc/effective_go.html)
2. [The Go common mistakes guide](https://github.com/golang/go/wiki/CodeReviewComments)

所用的代码在运行 `golint` 和 `go vet` 之后不会有报错。建议将编辑器设置为：

- 保存时运行 goimports
- 运行 `golint` 和 `go vet` 来检查错误

你可以在下面的链接找到 Go tools 对一些编辑器的支持：<https://github.com/golang/go/wiki/IDEsAndTextEditorPlugins>

## 指南

### 接口的指针

你几乎不需要指向接口的指针，应该把接口当作值传递，它的底层数据仍然可以当成一个指针。

一个接口是两个字段：

1. 指向特定类型信息的指针。你可以认为这是 "type."。
2. 如果存储的数据是指针，则直接存储。如果数据存储的是值，则存储指向此值的指针。

如果你希望接口方法修改底层数据，则必须使用指针。

### 接收者和接口

具有值接收者的方法可以被指针和值调用。

例如,

```go
type S struct {
  data string
}

func (s S) Read() string {
  return s.data
}

func (s *S) Write(str string) {
  s.data = str
}

sVals := map[int]S{1: {"A"}}

// 使用值只能调用 Read 方法
sVals[1].Read()

// 会编译失败
//  sVals[0].Write("test")

sPtrs := map[int]*S{1: {"A"}}

// 使用指针可以调用 Read 和 Write 方法
sPtrs[1].Read()
sPtrs[1].Write("test")
```

类似的，即使方法是一个值接收者，但接口仍可以被指针类型所满足。

```go
type F interface {
  f()
}

type S1 struct{}

func (s S1) f() {}

type S2 struct{}

func (s *S2) f() {}

s1Val := S1{}
s1Ptr := &S1{}
s2Val := S2{}
s2Ptr := &S2{}

var i F
i = s1Val
i = s1Ptr
i = s2Ptr

// 以下不能被编译，因为 s2Val 是一个值，并且 f 没有值接收者
//   i = s2Val
```

Effective Go 对 [Pointers vs. Values] 分析的不错.

  [Pointers vs. Values]: https://golang.org/doc/effective_go.html#pointers_vs_values

### 零值 Mutexes 是有效的

零值的 `sync.Mutex` 和 `sync.RWMutex` 是有效的，所以你几乎不需要指向 mutex 的指针。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
mu := new(sync.Mutex)
mu.Lock()
```

</td><td>

```go
var mu sync.Mutex
mu.Lock()
```

</td></tr>
</tbody></table>

```go
var mu sync.Mutex

mu.Lock()
defer mu.Unlock()
```

如果你使用一个指针指向的结构体，mutex 可以作为一个非指针字段，或者，最好是直接嵌入这个结构体。

<table>
<tbody>
<tr><td>

```go
type smap struct {
  sync.Mutex

  data map[string]string
}

func newSMap() *smap {
  return &smap{
    data: make(map[string]string),
  }
}

func (m *smap) Get(k string) string {
  m.Lock()
  defer m.Unlock()

  return m.data[k]
}
```

</td><td>

```go
type SMap struct {
  mu sync.Mutex

  data map[string]string
}

func NewSMap() *SMap {
  return &SMap{
    data: make(map[string]string),
  }
}

func (m *SMap) Get(k string) string {
  m.mu.Lock()
  defer m.mu.Unlock()

  return m.data[k]
}
```

</td></tr>

</tr>
<tr>
<td>为私有类型或需要实现 Mutex 接口的类型嵌入</td>

<td>对于导出的类型，使用私有锁。</td>
</tr>

</tbody></table>

### 复制 Slice 和 Map 

slice 和 map 包含指向底层数据的指针，因此复制的时候需要当心。

#### 接收 Slice 和 Map 作为入参

需要留意的是，如果你保存了作为参数接收的 map 或 slice 的引用，可以通过引用修改它。

<table>
<thead><tr><th>Bad</th> <th>Good</th></tr></thead>
<tbody>
<tr>
<td>

```go
func (d *Driver) SetTrips(trips []Trip) {
  d.trips = trips
}

trips := ...
d1.SetTrips(trips)

// Did you mean to modify d1.trips?
trips[0] = ...
```

</td>
<td>

```go
func (d *Driver) SetTrips(trips []Trip) {
  d.trips = make([]Trip, len(trips))
  copy(d.trips, trips)
}

trips := ...
d1.SetTrips(trips)

// We can now modify trips[0] without affecting d1.trips.
trips[0] = ...
```

</td>
</tr>

</tbody>
</table>

#### 返回 Slice 和 Map

类似的，当心 map 或者 slice 暴露的内部状态是可以被修改的。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
type Stats struct {
  sync.Mutex

  counters map[string]int
}

// Snapshot 方法返回当前的状态
func (s *Stats) Snapshot() map[string]int {
  s.Lock()
  defer s.Unlock()

  return s.counters
}

// snapshot 不再被锁保护
snapshot := stats.Snapshot()
```

</td><td>

```go
type Stats struct {
  sync.Mutex

  counters map[string]int
}

func (s *Stats) Snapshot() map[string]int {
  s.Lock()
  defer s.Unlock()

  result := make(map[string]int, len(s.counters))
  for k, v := range s.counters {
    result[k] = v
  }
  return result
}

// 现在 Snapshot 是一个副本
snapshot := stats.Snapshot()
```

</td></tr>
</tbody></table>

### Defer 的使用

使用 defer 去关闭文件句柄和释放锁等类似的这些资源。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
p.Lock()
if p.count < 10 {
  p.Unlock()
  return p.count
}

p.count++
newCount := p.count
p.Unlock()

return newCount

// 多个返回语句导致很容易忘记释放锁
```

</td><td>

```go
p.Lock()
defer p.Unlock()

if p.count < 10 {
  return p.count
}

p.count++
return p.count

// 更可读
```

</td></tr>
</tbody></table>

defer 的开销非常小，只有在你觉得你的函数执行需要在纳秒级别的情况下才需要考虑避免使用。使用 defer 换取的可读性是值得的。这尤其适用于具有比简单内存访问更复杂的大型方法，这时其他的计算比 defer 更重要。

### channel 的大小是 1 或者 None

channel 的大小通常应该是 1 或者是无缓冲的。默认情况下，channel 是无缓冲的且大小为 0。任何其他的大小都必须经过仔细检查。应该考虑如何确定缓冲的大小，哪些因素可以防止 channel 在负载时填满和阻塞写入，以及当这种情况发生时会造成什么样的影响。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
// Ought to be enough for anybody!
c := make(chan int, 64)
```

</td><td>

```go
// size 为 1
c := make(chan int, 1) // 或者
// 非缓冲 channel，size 为 0
c := make(chan int)
```

</td></tr>
</tbody></table>

### 枚举值从 1 开始

在 Go 中引入枚举的标准方法是声明一个自定义类型和一个带 `iota` 的 `const` 组。由于变量的默认值为 0，因此通常应该以非零值开始枚举。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
type Operation int

const (
  Add Operation = iota
  Subtract
  Multiply
)

// Add=0, Subtract=1, Multiply=2
```

</td><td>

```go
type Operation int

const (
  Add Operation = iota + 1
  Subtract
  Multiply
)

// Add=1, Subtract=2, Multiply=3
```

</td></tr>
</tbody></table>

在某些情况下，使用零值是有意义的，例如零值是想要的默认值。

```go
type LogOutput int

const (
  LogToStdout LogOutput = iota
  LogToFile
  LogToRemote
)

// LogToStdout=0, LogToFile=1, LogToRemote=2
```

<!-- TODO: section on String methods for enums -->

### Error 类型

声明 error 有多种选项:

- [`errors.New`] 声明简单静态的字符串
- [`fmt.Errorf`] 声明格式化的字符串
- 实现了 `Error()` 方法的自定义类型
- 使用 [`"pkg/errors".Wrap`] 包装 error

返回 error 时，可以考虑以下因素以确定最佳选择：

- 不需要额外信息的一个简单的 error? 那么 [`errors.New`] 就够了
- 客户端需要检查并处理这个 error？那么应该使用实现了 `Error()` 方法的自定义类型
- 是否需要传递下游函数返回的 error？那么请看 [section on error wrapping](#error-wrapping)
- 否则, 可以使用 [`fmt.Errorf`] 

  [`errors.New`]: https://golang.org/pkg/errors/#New
  [`fmt.Errorf`]: https://golang.org/pkg/fmt/#Errorf
  [`"pkg/errors".Wrap`]: https://godoc.org/github.com/pkg/errors#Wrap

如果客户端需要检查这个 error，你需要使用 [`errors.New`] 和 var 来创建一个简单的 error。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
// package foo

func Open() error {
  return errors.New("could not open")
}

// package bar

func use() {
  if err := foo.Open(); err != nil {
    if err.Error() == "could not open" {
      // handle
    } else {
      panic("unknown error")
    }
  }
}
```

</td><td>

```go
// package foo

var ErrCouldNotOpen = errors.New("could not open")

func Open() error {
  return ErrCouldNotOpen
}

// package bar

if err := foo.Open(); err != nil {
  if err == foo.ErrCouldNotOpen {
    // handle
  } else {
    panic("unknown error")
  }
}
```

</td></tr>
</tbody></table>

如果你有一个 error 可能需要客户端去检查，并且你想增加更多的信息（例如，它不是一个简单的静态字符串），这时候你需要使用自定义类型。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
func open(file string) error {
  return fmt.Errorf("file %q not found", file)
}

func use() {
  if err := open(); err != nil {
    if strings.Contains(err.Error(), "not found") {
      // handle
    } else {
      panic("unknown error")
    }
  }
}
```

</td><td>

```go
type errNotFound struct {
  file string
}

func (e errNotFound) Error() string {
  return fmt.Sprintf("file %q not found", e.file)
}

func open(file string) error {
  return errNotFound{file: file}
}

func use() {
  if err := open(); err != nil {
    if _, ok := err.(errNotFound); ok {
      // handle
    } else {
      panic("unknown error")
    }
  }
}
```

</td></tr>
</tbody></table>

在直接导出自定义 error 类型的时候需要小心，因为它已经是包的公共 API。最好暴露一个 matcher 函数（译者注：以下示例的 IsNotFoundError 函数）去检查 error。

```go
// package foo

type errNotFound struct {
  file string
}

func (e errNotFound) Error() string {
  return fmt.Sprintf("file %q not found", e.file)
}

func IsNotFoundError(err error) bool {
  _, ok := err.(errNotFound)
  return ok
}

func Open(file string) error {
  return errNotFound{file: file}
}

// package bar

if err := foo.Open("foo"); err != nil {
  if foo.IsNotFoundError(err) {
    // handle
  } else {
    panic("unknown error")
  }
}
```

<!-- TODO: Exposing the information to callers with accessor functions. -->

### Error 包装

如果调用失败，有三个主要选项用于 error 传递：

- 如果没有额外增加的上下文并且你想维持原始 error 类型，那么返回原始 error
- 使用 [`"pkg/errors".Wrap`] 增加上下文，以至于 error 信息提供更多的上下文，并且 [`"pkg/errors".Cause`] 可以用来提取原始 error
- 如果调用者不需要检查或者处理具体的 error 例子，那么使用  [`fmt.Errorf`]

推荐去增加上下文信息取代描述模糊的 error，例如 "connection refused"，应该返回例如 "failed to
call service foo: connection refused" 这样更有用的 error。

请参考 [Don't just check errors, handle them gracefully].

  [`"pkg/errors".Cause`]: https://godoc.org/github.com/pkg/errors#Cause
  [Don't just check errors, handle them gracefully]: https://dave.cheney.net/2016/04/27/dont-just-check-errors-handle-them-gracefully

### 处理类型断言失败

简单的返回值形式的[类型断言]在断言不正确的类型时将会 panic。因此，需要使用 ", ok" 的常用方式。 

  [类型断言]: https://golang.org/ref/spec#Type_assertions

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
t := i.(string)
```

</td><td>

```go
t, ok := i.(string)
if !ok {
  // handle the error gracefully
}
```

</td></tr>
</tbody></table>

<!-- TODO: There are a few situations where the single assignment form is
fine. -->

### 避免 Panic

生产环境跑的代码必须避免 panic。它是导致 [级联故障] 的主要原因。如果一个 error 产生了，函数必须返回 error 并且允许调用者决定是否处理它。

  [级联故障]: https://en.wikipedia.org/wiki/Cascading_failure

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
func foo(bar string) {
  if len(bar) == 0 {
    panic("bar must not be empty")
  }
  // ...
}

func main() {
  if len(os.Args) != 2 {
    fmt.Println("USAGE: foo <bar>")
    os.Exit(1)
  }
  foo(os.Args[1])
}
```

</td><td>

```go
func foo(bar string) error {
  if len(bar) == 0
    return errors.New("bar must not be empty")
  }
  // ...
  return nil
}

func main() {
  if len(os.Args) != 2 {
    fmt.Println("USAGE: foo <bar>")
    os.Exit(1)
  }
  if err := foo(os.Args[1]); err != nil {
    panic(err)
  }
}
```

</td></tr>
</tbody></table>

panic/recover 不是 error 处理策略。程序在发生不可恢复的时候会产生 panic，例如对 nil 进行解引用。一个例外是在程序初始化的时候：在程序启动时那些可能终止程序的问题会造成 panic。

```go
var _statusTemplate = template.Must(template.New("name").Parse("_statusHTML"))
```

甚至在测试用例中，更偏向于使用 `t.Fatal` 或者 `t.FailNow` 解决 panic 确保这个测试被标记为失败。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
// func TestFoo(t *testing.T)

f, err := ioutil.TempFile("", "test")
if err != nil {
  panic("failed to set up test")
}
```

</td><td>

```go
// func TestFoo(t *testing.T)

f, err := ioutil.TempFile("", "test")
if err != nil {
  t.Fatal("failed to set up test")
}
```

</td></tr>
</tbody></table>

<!-- TODO: Explain how to use _test packages. -->

### 使用 go.uber.org/atomic

使用 [sync/atomic] 对原生类型（例如，`int32`，`int64`）进行原子操作的时候，很容易在读取或者修改变量的时候忘记使用原子操作。

[go.uber.org/atomic] 通过隐藏底层类型使得这些操作是类型安全的。此外，它还包含一个比较方便的 `atomic.Bool` 类型。

  [go.uber.org/atomic]: https://godoc.org/go.uber.org/atomic
  [sync/atomic]: https://golang.org/pkg/sync/atomic/

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
type foo struct {
  running int32  // atomic
}

func (f* foo) start() {
  if atomic.SwapInt32(&f.running, 1) == 1 {
     // already running…
     return
  }
  // start the Foo
}

func (f *foo) isRunning() bool {
  return f.running == 1  // race!
}
```

</td><td>

```go
type foo struct {
  running atomic.Bool
}

func (f *foo) start() {
  if f.running.Swap(true) {
     // already running…
     return
  }
  // start the Foo
}

func (f *foo) isRunning() bool {
  return f.running.Load()
}
```

</td></tr>
</tbody></table>

## 性能

指定的性能指南仅适用于 **hot path**（译者注：hot path 指频繁执行的代码路径）

### strconv 优于 fmt

对基本数据类型的字符串表示的转换，`strconv` 比
`fmt` 速度快。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
var i int = ...
s := fmt.Sprint(i)
```

</td><td>

```go
var i int = ...
s := strconv.Itoa(i)
```

</td></tr>
</tbody></table>

### 避免 string 到 byte 的转换

不要重复用固定 string 创建 byte slice。相反，执行一次转换后保存结果，避免重复转换。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
for i := 0; i < b.N; i++ {
  w.Write([]byte("Hello world"))
}
```

</td><td>

```go
data := []byte("Hello world")
for i := 0; i < b.N; i++ {
  w.Write(data)
}
```

</tr>
<tr><td>

```plain
BenchmarkBad-4   50000000   22.2 ns/op
```

</td><td>

```plain
BenchmarkGood-4  500000000   3.25 ns/op
```

</td></tr>
</tbody></table>

## 代码风格

### 聚合相似的声明

Go 支持分组声明。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
import "a"
import "b"
```

</td><td>

```go
import (
  "a"
  "b"
)
```

</td></tr>
</tbody></table>

也能应用于常量，变量和类型的声明。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go

const a = 1
const b = 2



var a = 1
var b = 2



type Area float64
type Volume float64
```

</td><td>

```go
const (
  a = 1
  b = 2
)

var (
  a = 1
  b = 2
)

type (
  Area float64
  Volume float64
)
```

</td></tr>
</tbody></table>

只需要对相关类型进行分组声明。不相关的不需要进行分组声明。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
type Operation int

const (
  Add Operation = iota + 1
  Subtract
  Multiply
  ENV_VAR = "MY_ENV"
)
```

</td><td>

```go
type Operation int

const (
  Add Operation = iota + 1
  Subtract
  Multiply
)

const ENV_VAR = "MY_ENV"
```

</td></tr>
</tbody></table>

分组不受限制。例如，我们可以在函数内部使用它们。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
func f() string {
  var red = color.New(0xff0000)
  var green = color.New(0x00ff00)
  var blue = color.New(0x0000ff)

  ...
}
```

</td><td>

```go
func f() string {
  var (
    red   = color.New(0xff0000)
    green = color.New(0x00ff00)
    blue  = color.New(0x0000ff)
  )

  ...
}
```

</td></tr>
</tbody></table>

### 包的分组导入的顺序

有两个导入分组：

- 标准库
- 其他库

这是默认情况下 goimports 应用的分组。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
import (
  "fmt"
  "os"
  "go.uber.org/atomic"
  "golang.org/x/sync/errgroup"
)
```

</td><td>

```go
import (
  "fmt"
  "os"

  "go.uber.org/atomic"
  "golang.org/x/sync/errgroup"
)
```

</td></tr>
</tbody></table>

### 包命名

当给包命名的时候，可以参考以下方法，

- 都是小写字母。没有大写字母或者下划线
- 在大多数场景下没必要重命名包
- 简明扼要。记住，每次调用时都会通过名称来识别。
- 不要复数。例如，要使用 `net/url`,  不要使用 `net/urls`
- 不要使用 "common", "util", "shared", "lib" 诸如此类的命名。这种方式不太好，无法从名字中获取有效信息。

也可以参考 [Package Names] 和 [Style guideline for Go packages].

  [Package Names]: https://blog.golang.org/package-names
  [Style guideline for Go packages]: https://rakyll.org/style-packages/

### 函数命名

我们遵循 Go 社区的习惯方法，使用[驼峰法命名函数]。测试函数是个例外，包含下划线是为了分组相关的测试用例。例如，`TestMyFunction_WhatIsBeingTested`。

  [驼峰法命名函数]: https://golang.org/doc/effective_go.html#mixed-caps

### 别名导入

如果包名和导入路径的最后一个元素不匹配，则要使用别名导入。

```go
import (
  "net/http"

  client "example.com/client-go"
  trace "example.com/trace/v2"
)
```

在大部分场景下，除非导入的包有直接的冲突，应该避免使用别名导入。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
import (
  "fmt"
  "os"


  nettrace "golang.net/x/trace"
)
```

</td><td>

```go
import (
  "fmt"
  "os"
  "runtime/trace"

  nettrace "golang.net/x/trace"
)
```

</td></tr>
</tbody></table>

### 函数分组和顺序

- 函数应该按大致的调用顺序排序
- 同一个文件的函数应该按接收者分组

因此，导出的函数应该在 `struct`，`const`，`var` 定义之后。

`newXYZ()`/`NewXYZ()` 应该在类型定义之后，并且在接收者的其余的方法之前出现。 

因为函数是按接收者分组的，所以普通的函数应该快到文件末尾了。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
func (s *something) Cost() {
  return calcCost(s.weights)
}

type something struct{ ... }

func calcCost(n int[]) int {...}

func (s *something) Stop() {...}

func newSomething() *something {
    return &something{}
}
```

</td><td>

```go
type something struct{ ... }

func newSomething() *something {
    return &something{}
}

func (s *something) Cost() {
  return calcCost(s.weights)
}

func (s *something) Stop() {...}

func calcCost(n int[]) int {...}
```

</td></tr>
</tbody></table>

### 减少嵌套

在可能的情况下，代码应该通过先处理 错误情况/特殊条件 并提前返回或继续循环来减少嵌套。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
for _, v := range data {
  if v.F1 == 1 {
    v = process(v)
    if err := v.Call(); err == nil {
      v.Send()
    } else {
      return err
    }
  } else {
    log.Printf("Invalid v: %v", v)
  }
}
```

</td><td>

```go
for _, v := range data {
  if v.F1 != 1 {
    log.Printf("Invalid v: %v", v)
    continue
  }
  
  v = process(v)
  if err := v.Call(); err != nil {
    return err
  }
  v.Send()
}
```

</td></tr>
</tbody></table>

### 不必要的 else

如果在 if 的两个分支中都设置同样的变量，则可以用单个 if 替换它。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
var a int
if b {
  a = 100
} else {
  a = 10
}
```

</td><td>

```go
a := 10
if b {
  a = 100
}
```

</td></tr>
</tbody></table>

### 顶层变量的声明

在顶层，使用标准的 `var` 关键字。不要指定类型，除非它与表达式的类型不同。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
var _s string = F()

func F() string { return "A" }
```

</td><td>

```go
var _s = F()
// F 已经声明了返回一个 string，我们不需要再次指定类型

func F() string { return "A" }
```

</td></tr>
</tbody></table>

如果表达式的类型与请求的类型不完全匹配，请指定类型。

```go
type myError struct{}

func (myError) Error() string { return "error" }

func F() myError { return myError{} }

var _e error = F()
// F 返回了一个 myError 类型的对象，但是我们想要 error
```

### 在不可导出的全局变量前面加上 _

在不可导出的顶层 `var` 和 `const` 的前面加上 `_`，以便明确它们是全局符号。

特例：不可导出的 error 值前面应该加上 `err` 前缀。

理论依据：顶层变量和常量有一个包作用域。使用通用的名称很容易在不同的文件中意外地使用错误的值

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
// foo.go

const (
  defaultPort = 8080
  defaultUser = "user"
)

// bar.go

func Bar() {
  defaultPort := 9090
  ...
  fmt.Println("Default port", defaultPort)

  // 我们将 Bar() 的第一行删除，将不会看到编译错误
}
```

</td><td>

```go
// foo.go

const (
  _defaultPort = 8080
  _defaultUser = "user"
)
```

</td></tr>
</tbody></table>

### 结构体的嵌入

嵌入的类型（例如 mutex）应该在结构体字段的头部，并且在嵌入字段和常规字段间保留一个空行来隔离。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
type Client struct {
  version int
  http.Client
}
```

</td><td>

```go
type Client struct {
  http.Client

  version int
}
```

</td></tr>
</tbody></table>

### 使用字段名去初始化结构体

当初始化结构体的时候应该指定字段名称，现在在使用 [`go vet`] 的情况下是强制性的。

  [`go vet`]: https://golang.org/cmd/vet/

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
k := User{"John", "Doe", true}
```

</td><td>

```go
k := User{
    FirstName: "John",
    LastName: "Doe",
    Admin: true,
}
```

</td></tr>
</tbody></table>

特例：当有 3 个或更少的字段时，可以在测试表中省略字段名。

```go
tests := []struct{
}{
  op Operation
  want string
}{
  {Add, "add"},
  {Subtract, "subtract"},
}
```

### 局部变量声明

短变量声明（`:=`）应该被使用在有明确值的情况下。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
var s = "foo"
```

</td><td>

```go
s := "foo"
```

</td></tr>
</tbody></table>

然而，使用 `var` 关键字在某些情况下会让默认值更清晰，[声明空 Slice]，例如

  [声明空 Slice]: https://github.com/golang/go/wiki/CodeReviewComments#declaring-empty-slices

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
func f(list []int) {
  filtered := []int{}
  for _, v := range list {
    if v > 10 {
      filtered = append(filtered, v)
    }
  }
}
```

</td><td>

```go
func f(list []int) {
  var filtered []int
  for _, v := range list {
    if v > 10 {
      filtered = append(filtered, v)
    }
  }
}
```

</td></tr>
</tbody></table>

### nil 是一个有效的 slice

`nil` 是一个长度为 0 的 slice。意思是，

- 使用 `nil` 来替代长度为 0 的 slice 返回

  <table>
  <thead><tr><th>Bad</th><th>Good</th></tr></thead>
  <tbody>
  <tr><td>

  ```go
  if x == "" {
    return []int{}
  }
  ```

  </td><td>

  ```go
  if x == "" {
    return nil
  }
  ```

  </td></tr>
  </tbody></table>

- 检查一个空 slice，应该使用 `len(s) == 0`，而不是 `nil`。

  <table>
  <thead><tr><th>Bad</th><th>Good</th></tr></thead>
  <tbody>
  <tr><td>

  ```go
  func isEmpty(s []string) bool {
    return s == nil
  }
  ```

  </td><td>

  ```go
  func isEmpty(s []string) bool {
    return len(s) == 0
  }
  ```

  </td></tr>
  </tbody></table>

- The zero value (a slice declared with `var`) is usable immediately without
  `make()`.

- 零值（通过 `var` 声明的 slice）是立马可用的，并不需要 `make()` 。

  <table>
  <thead><tr><th>Bad</th><th>Good</th></tr></thead>
  <tbody>
  <tr><td>

  ```go
  nums := []int{}
  // or, nums := make([]int)

  if add1 {
    nums = append(nums, 1)
  }

  if add2 {
    nums = append(nums, 2)
  }
  ```

  </td><td>

  ```go
  var nums []int

  if add1 {
    nums = append(nums, 1)
  }

  if add2 {
    nums = append(nums, 2)
  }
  ```

  </td></tr>
  </tbody></table>

### 减少变量的作用域

在没有 [减少嵌套](#reduce-nesting) 相冲突的情况下，尽量减少变量的作用域。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
err := f.Close()
if err != nil {
 return err
}
```

</td><td>

```go
if err := f.Close(); err != nil {
 return err
}
```

</td></tr>
</tbody></table>

如果在 if 之外需要函数调用的结果，则不要缩小作用域。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
if f, err := os.Open("f"); err == nil {
  _, err = io.WriteString(f, "data")
  if err != nil {
    return err
  }
  return f.Close()
} else {
  return err
}
```

</td><td>

```go
f, err := os.Open("f")
if err != nil {
   return err
}

if _, err := io.WriteString(f, "data"); err != nil {
  return err
}

return f.Close()
```

</td></tr>
</tbody></table>

### 避免裸参数

函数调用中的裸参数不利于可读性。当参数名的含义不明显时，添加 C 语言风格的注释（`/*…*/`）。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
// func printInfo(name string, isLocal, done bool)

printInfo("foo", true, true)
```

</td><td>

```go
// func printInfo(name string, isLocal, done bool)

printInfo("foo", true /* isLocal */, true /* done */)
```

</td></tr>
</tbody></table>

更好的方法是，用自定义类型替换裸 `bool` 类型，以获得更可读的和类型安全的代码。这使得该参数未来的状态是可以增加的，不仅仅是两种（true/false）。

```go
type Region int

const (
  UnknownRegion Region = iota
  Local
)

type Status int

const (
  StatusReady = iota + 1
  StatusDone
  // 可能未来我们将有一个 StatusInProgress 的状态
)

func printInfo(name string, region Region, status Status)
```

### 使用原生字符串格式来避免转义

Go 支持 [原生字符串格式](https://golang.org/ref/spec#raw_string_lit) ，它可以跨越多行并包含引号。使用这些来避免手动转义的字符串，因为手动转义的可读性很差。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
wantError := "unknown name:\"test\""
```

</td><td>

```go
wantError := `unknown error:"test"`
```

</td></tr>
</tbody></table>

### 初始化结构体

在初始化结构体的时候使用 `&T{}` 替代 `new(T)`，以至于结构体初始化是一致的。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
sval := T{Name: "foo"}

// 不一致
sptr := new(T)
sptr.Name = "bar"
```

</td><td>

```go
sval := T{Name: "foo"}

sptr := &T{Name: "bar"}
```

</td></tr>
</tbody></table>

### 在 Printf 之外格式化字符串

如果你在 `Printf` 风格函数的外面声明一个格式化字符串，请使用 `const` 值。

这有助于 `go vet` 对格式化字符串执行静态分析。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
msg := "unexpected values %v, %v\n"
fmt.Printf(msg, 1, 2)
```

</td><td>

```go
const msg = "unexpected values %v, %v\n"
fmt.Printf(msg, 1, 2)
```

</td></tr>
</tbody></table>

### Printf-style 函数的命名

当你声明一个 `Printf` 风格的函数，请确认 `go vet` 能够发现并检查这个格式化字符串。

这意味着你应该尽可能为 `Printf` 风格的函数名进行预定义 。`go vet` 默认会检查它们。查看 [Printf family] 获取更多信息。 

  [Printf family]: https://golang.org/cmd/vet/#hdr-Printf_family

如果预定义函数名不可取，请用 f 作为名字的后缀即 `wrapf`，而不是 `wrap`。`go vet` 可以检查特定的 `printf` 风格的名称，但它们必须以 f 结尾。

```shell
$ go vet -printfuncs=wrapf,statusf
```

请参考 [go vet: Printf family check]。

  [go vet: Printf family check]: https://kuzminva.wordpress.com/2017/11/07/go-vet-printf-family-check/

## 设计模式

### 表格驱动测试

当核心测试逻辑重复的时候，用 [subtests] 做表格驱动测试（译者注：table-driven tests 即 TDT 表格驱动方法）可以避免重复的代码。

  [subtests]: https://blog.golang.org/subtests

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
// func TestSplitHostPort(t *testing.T)

host, port, err := net.SplitHostPort("192.0.2.0:8000")
require.NoError(t, err)
assert.Equal(t, "192.0.2.0", host)
assert.Equal(t, "8000", port)

host, port, err = net.SplitHostPort("192.0.2.0:http")
require.NoError(t, err)
assert.Equal(t, "192.0.2.0", host)
assert.Equal(t, "http", port)

host, port, err = net.SplitHostPort(":8000")
require.NoError(t, err)
assert.Equal(t, "", host)
assert.Equal(t, "8000", port)

host, port, err = net.SplitHostPort("1:8")
require.NoError(t, err)
assert.Equal(t, "1", host)
assert.Equal(t, "8", port)
```

</td><td>

```go
// func TestSplitHostPort(t *testing.T)

tests := []struct{
  give     string
  wantHost string
  wantPort string
}{
  {
    give:     "192.0.2.0:8000",
    wantHost: "192.0.2.0",
    wantPort: "8000",
  },
  {
    give:     "192.0.2.0:http",
    wantHost: "192.0.2.0",
    wantPort: "http",
  },
  {
    give:     ":8000",
    wantHost: "",
    wantPort: "8000",
  },
  {
    give:     "1:8",
    wantHost: "1",
    wantPort: "8",
  },
}

for _, tt := range tests {
  t.Run(tt.give, func(t *testing.T) {
    host, port, err := net.SplitHostPort(tt.give)
    require.NoError(t, err)
    assert.Equal(t, tt.wantHost, host)
    assert.Equal(t, tt.wantPort, port)
  })
}
```

</td></tr>
</tbody></table>

表格驱动测试使向错误消息添加上下文、减少重复逻辑和添加新测试用例变得更容易。

我们遵循这样一种约定，即结构体 slice 被称为 `tests`，每个测试用例被称为 `tt`。此外，我们鼓励使用 `give` 和 `want` 前缀解释每个测试用例的输入和输出值。

```go
tests := []struct{
  give     string
  wantHost string
  wantPort string
}{
  // ...
}

for _, tt := range tests {
  // ...
}
```

### 函数参数可选化

函数参数可选化（functional options）是一种模式，在这种模式中，你可以声明一个不确定的 `Option` 类型，该类型在内部结构体中记录信息。函数接收可选化的参数，并根据在结构体上记录的参数信息进行操作

将此模式用于构造函数和其他需要扩展的公共 API 中的可选参数，特别是在这些函数上已经有三个或更多参数的情况下。

<table>
<thead><tr><th>Bad</th><th>Good</th></tr></thead>
<tbody>
<tr><td>

```go
// package db

func Connect(
  addr string,
  timeout time.Duration,
  caching bool,
) (*Connection, error) {
  // ...
}

// timeout 和 caching 必须要提供，哪怕用户想使用默认值

db.Connect(addr, db.DefaultTimeout, db.DefaultCaching)
db.Connect(addr, newTimeout, db.DefaultCaching)
db.Connect(addr, db.DefaultTimeout, false /* caching */)
db.Connect(addr, newTimeout, false /* caching */)
```

</td><td>

```go
type options struct {
  timeout time.Duration
  caching bool
}

// Option 重写 Connect.
type Option interface {
  apply(*options)
}

type optionFunc func(*options)

func (f optionFunc) apply(o *options) {
  f(o)
}

func WithTimeout(t time.Duration) Option {
  return optionFunc(func(o *options) {
    o.timeout = t
  })
}

func WithCaching(cache bool) Option {
  return optionFunc(func(o *options) {
    o.caching = cache
  })
}

// Connect 创建一个 connection
func Connect(
  addr string,
  opts ...Option,
) (*Connection, error) {
  options := options{
    timeout: defaultTimeout,
    caching: defaultCaching,
  }

  for _, o := range opts {
    o(&options)
  }

  // ...
}

// Options 只在需要的时候提供

db.Connect(addr)
db.Connect(addr, db.WithTimeout(newTimeout))
db.Connect(addr, db.WithCaching(false))
db.Connect(
  addr,
  db.WithCaching(false),
  db.WithTimeout(newTimeout),
)
```

</td></tr>
</tbody></table>

请参考,

- [Self-referential functions and the design of options]
- [Functional options for friendly APIs]

  [Self-referential functions and the design of options]: https://commandcenter.blogspot.com/2014/01/self-referential-functions-and-design.html
  [Functional options for friendly APIs]: https://dave.cheney.net/2014/10/17/functional-options-for-friendly-apis
