# 并发安全的集中式指针管理设施

- 原文地址：https://golang.design/research/cgo-handle
- 原文作者：欧长坤
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w33_a_concurrent-safe_centralized_pointe.md
- 译者：[Cluas](https://github.com/Cluas)
- 校对：[laxiaohong](https://github.com/laxiaohong)

在Go 1.17发行版中，我们贡献了一个新的cgo设施[runtime/cgo.Handle](https://tip.golang.org/pkg/runtime/cgo/#Handle)，以帮助未来的cgo应用在Go和C之间传递指针的同时，更好、更容易地构建并发安全的应用。本文将通过询问该功能为我们提供了什么，为什么我们需要这样一个设施，以及我们最终究竟如何贡献具体实现来引导我们了解这个功能。
## 从 Cgo 和 X Window 剪贴板开始

Cgo是在Go中与C语言设施进行交互的事实标准。然而，我们有多少次需要在Go中与C语言进行交互呢？这个问题的答案取决于我们在系统层面上的工作程度，或者我们有多少次需要利用传统的C库，比如用于图像处理。每当Go程序需要使用一个来自C的遗留物时，它需要导入一种 `C`的专用包，如下所示，然后在Go方面，人们可以通过导入的`C`符号简单地调用`myprint`函数。

```go
/*
#include <stdio.h>

void myprint() {
	printf("Hello %s", "World");
}
*/
import "C"

func main() {
	C.myprint()
	// Output:
	// Hello World
}
```


几个月前，当我们在建立一个提供跨平台剪贴板访问的新的包[`golang.design/x/clipboard`](https://golang.design/x/clipboard)时， 我们发现，Go中缺乏这样的设施，尽管有很多野路子，但仍然存在健全性和性能问题。

在[`golang.design/x/clipboard`](https://golang.design/x/clipboard)软件包中，我们不得不与cgo合作来访问系统级的API（从技术上讲，它是一个来自传统的、广泛使用的C系统的API），但缺乏在C代码侧了解执行进度的设施。例如，在Go代码这边，我们必须在一个goroutine中调用C代码，然后并行地做其他事情。

```go
go func() {
	C.doWork() // Cgo: 调用一个C函数，并在C代码侧做一些事情
}()

// .. 在Go代码侧做点事 ..
```

然而，在某些情况下，我们需要一种机制来了解C代码的执行进度，这就带来了Go和C之间通信和同步的需要。例如，如果我们需要我们的Go代码等待C代码完成一些初始化工作，直到某个执行点执行，我们将需要这种类型的通信来精确的了解C函数的执行进度。

我们遇到的一个真实的例子是需要与剪贴板设施互动。在Linux的[X Window 环境](https://en.wikipedia.org/wiki/X_Window_System)中，剪贴板是分散的，只能由每个应用程序拥有。需要访问剪贴板信息的人需要创建他们的剪贴板实例。假设一个应用程序`A`想把某些东西粘贴到剪贴板上，它必须向X Window服务器提出请求，然后成为剪贴板的所有者，在其他应用程序发出复制请求时把信息送回去。

这种设计被认为是自然的，经常需要应用程序进行合作。如果另一个应用程序`B`试图提出请求，成为剪贴板的下一个所有者，那么`A`将失去其所有权。之后，来自应用程序`C`、`D`等的复制请求将被转发给应用程序`B`而不是`A`。类似于一个共享的内存区域被别人覆盖了，而原来的所有者失去了访问权。

根据以上的上下文信息，我们可以理解，在一个应用程序开始 "粘贴"（服务）剪贴板信息之前，它首先要获得剪贴板的所有权。在我们获得所有权之前，剪贴板信息将不能用于访问目的。
换句话说，如果一个剪贴板API被设计成如下方式:

```go
clipboard.Write("某些信息")
```

我们必须从内部保证，当函数返回时，信息应该可以被其他应用程序访问。


当时，我们处理这个问题的第一个想法是，从Go到C传递一个`channel`，然后通过`channel`从C到Go发送一个值。经过快速的研究，我们意识到这是不可能的，因为由于[Cgo中传递指针的规则](https://pkg.go.dev/cmd/cgo#hdr-Passing_pointers)，`channel`不能作为一个值在C和Go之间传递（见之前的[提案文件](https://golang.org/design/12416-cgo-pointers)）。即使有办法将整个`channel`的值传递给C，在C代码侧也没有设施可以通过该`channel`发送值，因为C没有`<-`操作符的语言支持。

下一个想法是传递一个函数回调，然后让它在C代码侧被调用。该函数的执行将使用所需的`channel`向等待的goroutine发送一个通知。

经过几次尝试，我们发现唯一可能的方法是附加一个全局函数指针，并通过一个函数包装器使其被调用:


```go
/*
int myfunc(void* go_value);
*/
import "C"

// 这个funcCallback试图避免在运行时直接出现恐慌错误。
// 传递给Cgo，因为它违反了指针传递规则:
//
//   panic: runtime error: cgo argument has Go pointer to Go pointer
var (
	funcCallback   func()
	funcCallbackMu sync.Mutex
)

type gocallback struct{ f func() }

func main() {
	go func() {
		ret := C.myfunc(unsafe.Pointer(&gocallback{func() {
			funcCallbackMu.Lock()
			f := funcCallback // 必须使用一个全局函数变量。
			funcCallbackMu.Unlock()
			f()
		}}))
		// ... 搞事 ...
	}()
	// ... 搞事 ...
}
```

在上面的例子中，Go一方的`gocallback`指针是通过C函数`myfunc`传递的。在C代码侧，将有一个使用`go_func_callback`的调用，通过传递结构`gocallback`作为参数，在C代码侧被调用:

```c
// myfunc将在需要时触发一个回调，c_func，并通过void*参数传递
// gocallback的数据通过void*参数。
void c_func(void *data) {
	void *gocallback = userData;
	// the gocallback is received as a pointer, we pass it as an argument
	// to the go_func_callback
	go_func_callback(gocallback);
}
```

`go_func_callback`知道它的参数被打造成`gocallback`。因此，一个类型转换是安全的，可以做调用:

```go
//go:export go_func_callback
func go_func_callback(c unsafe.Pointer) {
	(*gocallback)(c).call()
}

func (c *gocallback) call() { c.f() }
```

在 "gocallback "中的函数 "f "正是我们想要调用的东西:

```go
func() {
	funcCallbackMu.Lock()
	f := funcCallback // 必须使用一个全局函数变量。
	funcCallbackMu.Unlock()
	f()               // 得到调用
}
```

注意，`funcCallback`必须是一个全局函数变量。否则，就违反了前面提到的[cgo指针传递规则](https://pkg.go.dev/cmd/cgo/#hdr-Passing_pointers)。

此外，对于上述代码的可读性，人们的直接反应是：太复杂了。所演示的方法一次只能赋值一个函数，这也违反了并发的本质。任何按程序专用的应用程序都不会从这种方法中受益，因为它们需要按程序函数回调，而不是单一的全局回调。当时，我们不知道是否有更好的、优雅的方法来处理它。

通过研究，我们发现这个需求在社区中经常出现，而且在[golang/go#37033](https://golang.org/issue/37033)中也被提出。幸运的是，这样的设施现在已经在Go 1.17中准备就绪 :)

## 什么是`runtime/cgo.Handle`？


新的[runtime/cgo.Handle](https://tip.golang.org/pkg/runtime/cgo/#Handle)提供了一种在Go和C之间传递包含Go指针（由Go分配的内存指针）的值的方法，而不违反cgo的指针传递规则。`Handle`是一个整数值，可以代表任何Go值。`Handle`可以通过C语言传递并返回到Go，Go代码可以使用`Handle`来检索原始Go值。最终的API设计建议如下:

```go
package cgo

type Handle uintptr


// NewHandle 返回一个给定值的句柄。
//
// 该句柄在程序对其调用Delete之前一直有效。该句柄
// 使用资源，而且这个包假定C代码可能会保留这个句柄。
// 所以当句柄不再需要时，程序必须明确地调用Delete。
//
// 预期的用途是将返回的句柄传递给C代码，由C代码
// 将其传回给Go，由Go调用Value。
func NewHandle(v interface{}) Handle

// Value返回一个有效句柄的相关Go值。
//
// 如果句柄是无效的，该方法就会陷入恐慌。
func (h Handle) Value() interface{}

// Delete 会使一个句柄失效。这个方法应该只被调用一次
// 程序不再需要将句柄传递给C，并且C代码
// 不再有一个句柄值的拷贝。
//
// 如果句柄是无效的，该方法就会慌乱
func (h Handle) Delete()
```

我们可以看到:`cgo.NewHandle`为任何给定的值返回一个句柄；方法`cgo.(Handle).Value`返回该句柄对应的Go值；每当我们需要删除该值时，可以调用`cgo.(Handle).Delete`。

最直接的例子是使用`Handle`在Go和C之间传递一个字符串。在Go的一方:

```go
package main
/*
#include <stdint.h> // for uintptr_t
extern void MyGoPrint(uintptr_t handle);
void myprint(uintptr_t handle);
*/
import "C"
import "runtime/cgo"

func main() {
	s := "Hello The golang.design Initiative"
	C.myprint(C.uintptr_t(cgo.NewHandle(s)))
	// Output:
	// Hello The golang.design Initiative
}
```

字符串`s`通过一个创建的句柄传递给C函数`myprint`，在C代码侧:

```c
#include <stdint.h> // for uintptr_t

// A Go function
extern void MyGoPrint(uintptr_t handle);
// A C function
void myprint(uintptr_t handle) {
	MyGoPrint(handle);
}
```

`myprint`将句柄传回给Go函数`MyGoPrint`:

```go
//go:export MyGoPrint
func MyGoPrint(handle C.uintptr_t) {
	h := cgo.Handle(handle)
	s := h.Value().(string)
	println(s)
	h.Delete()
}
```

`MyGoPrint`使用`cgo.(Handle).Value()`查询该值并打印出来。然后使用`cgo.(Handle).Delete()`删除该值。

有了这个新设施，我们可以更好地简化之前提到的函数回调模式:

```go
/*
#include <stdint.h>

int myfunc(void* go_value);
*/
import "C"

func main() {

	ch := make(chan struct{})
	handle := cgo.NewHandle(ch)
	go func() {
		C.myfunc(C.uintptr_t(handle)) // myfunc将在需要时调用goCallback。
		...
	}()

	<-ch // 我们从myfunc得到了通知。
	handle.Delete() // 因此需要删除手柄。
	...
}

//go:export goCallback
func goCallback(h C.uintptr_t) {
	v := cgo.Handle(h).Value().(chan struct{})
	v <- struct{}
}
```

更重要的是，`cgo.Handle`是一个并发安全的机制，这意味着一旦我们有了句柄号码，我们就可以在任何地方获取这个值（如果仍然可用的话），而不会受到数据竞赛的影响。

下一个问题: 如何实现`cgo.Handle`？

## 第一次尝试

第一次尝试是很复杂的。由于我们需要一个集中的方式以并发安全的方式管理所有的指针，我们脑海中最快的想法是`sync.Map`，它将一个唯一的数字映射到所需的值。因此，我们可以很容易地使用一个全局的`sync.Map`:

```go
package cgo

var m = &sync.Map{}
```

然而，我们必须考虑到核心的挑战:
如何分配一个运行时级别的唯一ID？在Go和C之间传递一个整数是相对容易的，那么对于一个给定的值，什么才是唯一的表示呢？

第一个想法是内存地址。因为每个指针或值都存储在内存的某个地方，如果我们能得到这些信息，就可以很容易地将其作为值的ID，因为每个值都有唯一的内存地址，所以很容易被用作值的ID。

为了完成这个想法，我们需要谨慎一点：一个活生生的值的内存地址会不会在某个时候被改变？这个问题又引出了两个问题:

1. 如果一个值在goroutine堆栈上怎么办？如果是这样，当goroutine死亡时，该值将被释放。
2. 2.Go是一种垃圾回收的语言。如果垃圾收集器将该值移动并压缩到一个不同的地方怎么办？那么该值的内存地址也会被改变。

根据我们多年来对运行时的[经验和理解](https://golang.design/s/more)，我们了解到，1.17之前的Go的垃圾收集器总是不动，机制也很难改变。这意味着，如果一个值分配在堆里，它不会被移到其他地方。有了这个事实，我们就可以解决第二个问题了。

对于第一个问题来说，这有点棘手：堆栈上的一个值可能会随着堆栈的增长而移动。更难解决的是，编译器优化可能会在堆栈之间移动数值，而运行时可能会在堆栈用完后移动堆栈。

自然得，我们可能会问：是否有可能确保一个值总是被分配在堆上而不是堆上？答案是：可以！如果我们把它变成一个`interface{}`。在1.17之前，Go编译器的逃逸分析总是标记应该逃逸到堆的值，如果它被转换为`interface{}`。

有了上面的所有分析，我们可以写出利用逃逸值的内存地址的以下部分实现:

```go
// wrap wraps a Go value.
type wrap struct{ v interface{} }

func NewHandle(v interface{}) Handle {
	var k uintptr

	rv := reflect.ValueOf(v)
	switch rv.Kind() {
	case reflect.Ptr, reflect.UnsafePointer, reflect.Slice,
		reflect.Map, reflect.Chan, reflect.Func:
		if rv.IsNil() {
			panic("cgo: cannot use Handle for nil value")
		}

		k = rv.Pointer()
	default:
	    // 包裹并将一个值参数变成一个指针。这使得
		// 我们总是将传递的对象存储为指针，并有助于
		// 识别哪些对象最初是指针或值
		// 当Value被调用时。
		v = &wrap{v}
		k = reflect.ValueOf(v).Pointer()
	}

	...
}
```

请注意，上面的实现对这些值的处理是不同的。对于`reflect.Ptr`, `reflect.UnsafePointer`, `reflect.Slice`, `reflect.Map`, `reflect.Chan`, `reflect.Func`类型，它们已经是逃逸到堆的指针，我们可以安全地从它们那里得到地址。对于其他类型，我们需要把它们从一个值变成一个指针，并确保它们总是逃逸到堆上。这就是以下部分:

```go
	    // 包裹并将一个值参数变成一个指针。这使得
		// 我们总是将传递的对象存储为指针，并有助于
		// 识别哪些对象最初是指针或值
		// 当Value被调用时。
		v = &wrap{v}
		k = reflect.ValueOf(v).Pointer()
```

现在我们已经把一切都变成了堆上的一个逃逸值。接下来我们要问的是：如果这两个值是一样的呢？这意味着传递给`cgo.NewHandle(v)'的`v'是同一个对象。那么此时我们将在`k`中得到相同的内存地址。

当然，简单的情况是，如果地址不在全局map上，那么我们就不必考虑，而是将地址作为值的句柄返回:


```go
func NewHandle(v interface{}) Handle {
	...

    // 由于反射的原因，v被逃逸到了堆里。
    // 由于Go没有一个移动的GC（而且可能在未来很长一段时间内都是如此），
    // 在这个时候使用它的指针地址作为全局地图的键是安全的。
    // 如果在运行时内部引入移动GC，则必须重新考虑实现。

	actual, loaded := m.LoadOrStore(k, v)
	if !loaded {
	    return Handle(k)
	}

	...
}
```

否则，我们必须检查全局map中的旧值，如果它是相同的值，那么我们就返回预期的相同地址:

```go
func NewHandle(v interface{}) Handle {
	...

	arv := reflect.ValueOf(actual)
	switch arv.Kind() {
	case reflect.Ptr, reflect.UnsafePointer, reflect.Slice,
		reflect.Map, reflect.Chan, reflect.Func:
		// 给定的Go值的底层对象已经有其现有的句柄。
		if arv.Pointer() == k {
			return Handle(k)
		}

        // 如果加载的指针与新的指针不一致，说明由于GC的原因，
        // 该地址被用于不同的对象，其地址被重新用于新的围棋对象，
        // 也就是说，当不需要旧的Go值时，Handle没有明确调用Delete。
        // 认为这是对句柄的误用，做恐慌。
		panic("cgo: misuse of a Handle")
	default:
		panic("cgo: Handle implementation has an internal bug")
	}
}
```

如果现有的值与新请求的值有相同的地址, 这一定是对处理程序的误用。

因为我们用`wrap`结构把所有东西都变成了`reflect.Ptr`类型，所以不可能有其他种类的值从全局map中获取。如果发生这种情况，这是句柄实现中的一个内部错误。

在实现`Value()`方法时，我们看到为什么一个`wrap`结构有利:

```go
func (h Handle) Value() interface{} {
	v, ok := m.Load(uintptr(h))
	if !ok {
		panic("cgo: misuse of an invalid Handle")
	}
	if wv, ok := v.(*wrap); ok {
		return wv.v
	}
	return v
}
```

因为我们可以检查当存储的对象是一个`*wrap`指针，这意味着它是一个指针以外的值。我们返回该值而不是存储的对象。

最后，`Delete`方法变得微不足道:

```go
func (h Handle) Delete() {
	_, ok := m.LoadAndDelete(uintptr(h))
	if !ok {
		panic("cgo: misuse of an invalid Handle")
	}
}
```

见[golang.design/x/clipboard/internal/cgo](https://github.com/golang-design/clipboard/blob/main/internal/cgo/handle.go)中的完整实现。

## 被接受的方法

正如人们可能已经意识到的那样，前面的方法比预期的要复杂得多，而且非同小可：它依赖的基础是，运行时垃圾收集器不是一个移动的垃圾收集器，虽然接口会逃到堆里。

尽管内部运行时实现中的其他几个地方依赖于这些事实，例如`channel`实现，但它仍然比我们预期的要复杂一些。

值得注意的是，以前的`NewHandle`实际上表现为当提供的Go值指的是同一个对象时，会返回一个唯一的手柄。这就是带来实现复杂性的核心。然而，我们还有另一种可能：`NewHandle`总是返回一个不同的句柄，而一个Go值可以有多个句柄。

我们真的需要句柄是唯一的并保持它满足[幂等性](https://en.wikipedia.org/wiki/Idempotence)吗？经过与Go团队的简短讨论，我们达成共识，对于句柄的目的，似乎没有必要保持其唯一性，原因如下:

1. `NewHandle`的语义是返回一个*新的*句柄，而不是一个唯一的句柄。
2. 句柄不过是一个整数，保证它的唯一性可以防止句柄的误用，但它不能总是避免滥用，直到为时已晚。
3. 实现的复杂性。

因此，我们需要重新思考原来的问题。如何分配一个运行时间级别的唯一ID?

在现实中，这种方法更容易管理：我们只需要增加一个数字，而且永远不会停止。这是最常用的唯一ID生成方法。例如，在数据库应用中，表行的唯一ID总是递增的；在Unix时间戳中，时间总是递增的，等等。

如果我们使用同样的方法，可能的并发安全实现会是什么？使用`sync.Map`和`atomic`，我们可以产生这样的代码:

```go
func NewHandle(v interface{}) Handle {
	h := atomic.AddUintptr(&handleIdx, 1)
	if h == 0 {
		panic("runtime/cgo: ran out of handle space")
	}

	handles.Store(h, v)
	return Handle(h)
}

var (
	handles   = sync.Map{} // map[Handle]interface{}
	handleIdx uintptr      // atomic
)
```

每当我们想分配一个新的ID（`NewHandle`）时，可以原子式地增加句柄编号`handleIdx`，那么下一次分配将始终保证有一个更大的编号可以使用。有了这个分配的数字，我们可以很容易地把它存储到一个全局map上，这个map可以持久地保存所有的Go值。

剩下的工作就变得微不足道了。当我们想使用句柄来检索相应的Go值时，我们通过句柄号访问值map:

```go
func (h Handle) Value() interface{} {
	v, ok := handles.Load(uintptr(h))
	if !ok {
		panic("runtime/cgo: misuse of an invalid Handle")
	}
	return v
}
```

此外，如果我们完成了对句柄的处理，可以从值map中删除它:

```go
func (h Handle) Delete() {
	_, ok := handles.LoadAndDelete(uintptr(h))
	if !ok {
		panic("runtime/cgo: misuse of an invalid Handle")
	}
}
```

在这个实现中，我们不需要假设运行时机制，只需要使用语言。只要Go 1的兼容性能保持`sync.Map`的承诺，就不需要重做整个`Handle`的设计。由于其简单性，这是Go团队接受的方法（见[CL 295369](https://golang.org/cl/295369)）。

除了未来对`sync.Map`的重新实现优化了并行性之外，`Handle`将自动从中受益。让我们做一个最后的基准测试，比较一下以前的方法和现在的方法。

```go
func BenchmarkHandle(b *testing.B) {
	b.Run("non-concurrent", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			h := cgo.NewHandle(i)
			_ = h.Value()
			h.Delete()
	    }
	})
	b.Run("concurrent", func(b *testing.B) {
		b.RunParallel(func(pb *testing.PB) {
			var v int
			for pb.Next() {
				h := cgo.NewHandle(v)
				_ = h.Value()
				h.Delete()
			}
		})
	})
}
```

```
name                     old time/op  new time/op  delta
Handle/non-concurrent-8  407ns ±1%    393ns ±2%   -3.51%  (p=0.000 n=8+9)
Handle/concurrent-8      768ns ±0%    759ns ±1%   -1.21%  (p=0.003 n=9+9)
```

更简单，更快速，为什么不呢？

## 总结

这篇文章讨论了我们在Go 1.17版本中新引入的`runtime/cgo.Handle`设施。`Handle`工具使我们能够在Go和C之间来回传递Go值，而不违反cgo指针传递规则。在简单介绍了该功能的用法之后，我们首先讨论了基于运行时垃圾收集器不是移动的GC以及`interface{}`参数的逃逸行为的首次尝试实现。
在对Handle语义的模糊性和之前实现中的缺点进行了一些讨论后，我们还介绍了一种直接的、性能更好的方法，并展示了其性能。

作为一个现实世界的示范，我们已经在我们发布的两个包[golang.design/x/clipboard](https://github.com/golang-design/clipboard)和[golang.design/x/hotkey](https://github.com/golang-design/hotkey)中使用上述两种方法很长时间了。 之前在其`internal/cgo`包中，我们期待着在Go 1.17版本中切换到官方发布的`runtime/cgo`包。

对于未来的工作，可以预见，在已接受的实现中可能存在的限制是，在32位或更低的操作系统中，句柄数可能会很快耗尽句柄空间（类似于[2038年
当我们每秒分配100个句柄时，句柄空间可以在以下时间用完
0xFFFFFFF / (24 * 60 * 60 * 100) = 31 天。

*_如果你有兴趣并认为这是一个严重的问题，请在发送CL时[抄送我们](mailto:hi[at]golang.design)，我们也有兴趣阅读你的优秀做法。_


## 进一步阅读建议

- Alex Dubov. runtime: 为管理(c)go指针句柄提供集中的设施 2020年2月5日。 https://golang.org/issue/37033
- Changkun Ou. runtime/cgo: 添加用于管理(c)go指针的句柄 2021年2月21日。 https://golang.org/cl/294670
- Changkun Ou. runtime/cgo: 添加用于管理(c)go指针的句柄 2021年2月23日。https://golang.org/cl/295369
- Ian Lance Taylor. cmd/cgo: 指定Go和C之间传递指针的规则。 2015年8月31日。 https://golang.org/issue/12416
- Ian Lance Taylor. Proposal:  Go和C之间传递指针的规则，2015年10月。 https://golang.org/design/12416-cgo-pointers
- Go Contributors. cgo. 2019年3月12日。 https://github.com/golang/go/wiki/cgo
- The golang.design Initiative. 📋 Go中的跨平台剪贴板包。2021年2月25日。 https://github.com/golang-design/clipboard
- The golang.design Initiative. ⌨️ GO中的跨平台热键包。2021年2月27日。 https://github.com/golang-design/hotkey
