- 原文地址：https://medium.com/@cheikhhseck/atomic-pointers-in-go-1-19-cad312f82d5b
- 原文作者：**Cheikh seck**
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/2022/w32_atomic_pointers_in_go_1_19.md
- 译者：[Fivezh](https://github.com/fivezh)
- 校对：[]()

# Go 1.19 中的原子指针

![img](../static/images/2022/w32_atomic_pointers_in_go_1_19/atomic-pointers.png)

在计算机编程中，"原子"是指一次执行一个操作。`Objective-C`有原子属性，它确保了从不同的线程对一个属性进行安全的读写。在`Objective-C`中，它是与不可变类型一起使用的。这是因为为了改变不可变类型，实际上是 "重新创建"它。换句话说，在你的代码中改变一个不可变的类型不会导致编译器抛出一个错误。然而，当你这样做的时候，它会实例化一个新的对象。一个典型的例子是`Go`的`append`函数，它每次调用都会产生一个新的切片。在`Objective-C`中，原子属性将确保操作是一个接一个进行的，以防止线程同时访问一个内存地址。由于`Go`是多线程的，它也支持原子操作。`Go` 1.19引入了新的原子类型。我最喜欢的新增类型是`atomic.Pointer`，它为`atomic.Value`提供了一个平滑的替代方案。它也很好地展示了泛型是如何增强开发者体验的。

# atomic.Pointer 原子指针

`atomic.Pointer` 是一个通用类型。与`Value`不同，它不需要断言你的存储值就可以访问。下面是一段定义和存储指针的代码:

```go
package main
import (
 "fmt"
 "net"
 "sync/atomic"
)
type ServerConn struct {
 Connection net.Conn
 ID string
 Open bool
}
func main() {
 p := atomic.Pointer[ServerConn]{}
 s := ServerConn{ ID : "first_conn"}
 p.Store( &s )
 fmt.Println(p.Load()) // Will display value stored.
}
```

将变量`p`实例化为一个指针结构字面量，然后将变量`s`的指针存储在`p`中，`s`代表一个服务器连接。至此，我们已经通过了实现原子性的第一步。通过将变量存储为原子值，我们将确保没有同时访问内存地址的情况。例如，如果同时并行读取和写入`map`，将导致程序恐慌。锁是防止这些恐慌发生的一个好方法，原子操作也是如此。


# 关于原子指针的使用示例

在之前提供的代码基础上，我将使用一个`atomic.Pointer`来每13秒重新创建一个数据库连接。首先编写一个函数，用来记录每10秒的连接ID。这将是查看新连接对象是否被传播的机制。然后，将定义一个内联函数，每13秒改变一次连接。下面是代码的样子：

```go
...
func ShowConnection(p * atomic.Pointer[ServerConn]){
for {
  time.Sleep(10 * time.Second)
  fmt.Println(p, p.Load())
 }
 
}
func main() {
 c := make(chan bool)
 p := atomic.Pointer[ServerConn]{}
 s := ServerConn{ ID : "first_conn"}
 p.Store( &s )
 go ShowConnection(&p)
 go func(){
   for {
    time.Sleep(13 * time.Second)
    newConn := ServerConn{ ID : "new_conn"}
    p.Swap(&newConn)
   }
 }()
 <- c
}
```

`ShowConnection`是作为一个`Goroutine`调用，内联函数将实例化一个新的`ServerConn`对象，并将其与当前连接对象交换。这在指针上是可行的，但是，这需要实现一个 "锁定-解锁 "系统。`atomic`包对此进行了抽象，并确保每个加载和保存都是一个接一个地处理。这是一个简单的例子，也是一个不那么常见的用例。另外，使用`atomic.Pointer`可能是一个 "过度工程"的案例，因为我程序的`Goroutine`s是在不同时间段运行的。我将使用Go的`race`标志来查看我的程序的`Goroutine`s是否在同一时间访问同一个内存地址。下面，将使用指针方式重写上述代码，而不是`atomic.Pointer`方式。

# 数据竞争

"当两个`Goroutine`同时访问同一个变量，并且至少有一个访问是写的时候，就会发生数据竞争"。为了快速验证数据竞赛，你可以执行`go run`，加上标志`race`参数来进行测试。为了演示原子类型如何防止这种情况，我们来重写上面的例子，使用经典的Go指针。下面是代码的样子：

```go
package main

import (
 "fmt"
 "net"
 "time"
)
type ServerConn struct {
 Connection net.Conn
 ID string
 Open bool
}
func ShowConnection(p * ServerConn){
for {
  time.Sleep(10 * time.Second)
  fmt.Println(p, *p)
 }
 
}
func main() {
 c := make(chan bool)
 p :=  ServerConn{ ID : "first_conn"}
 go ShowConnection(&p)
 go func(){
   for {
    time.Sleep(13 * time.Second)
    newConn := ServerConn{ ID : "new_conn"}
    p = newConn
   }
 }()
 <- c
}
```

在检查了数据竞争后，终端上的输出是这样的：

```go
~/go/src/atomic$ go run -race main_classic.go 
&{<nil> first_conn false} {<nil> first_conn false}
==================
WARNING: DATA RACE
Write at 0x00c000074570 by `Goroutine` 8:
  main.main.func1()
      /home/cheikh/go/src/atomic/main_classic.go:37 +0x6fPrevious read at 0x00c000074570 by `Goroutine` 7:
  runtime.convT()
      /usr/lib/go-1.18/src/runtime/iface.go:321 +0x0
  main.ShowConnection()
      /home/cheikh/go/src/atomic/main_classic.go:19 +0x65
  main.main.func2()
      /home/cheikh/go/src/atomic/main_classic.go:30 +0x39`Goroutine` 8 (running) created at:
  main.main()
      /home/cheikh/go/src/atomic/main_classic.go:33 +0x16e`Goroutine` 7 (running) created at:
  main.main()
      /home/cheikh/go/src/atomic/main_classic.go:30 +0x104
==================
&{<nil> new_conn false} {<nil> new_conn false}
&{<nil> new_conn false} {<nil> new_conn false}
&{<nil> new_conn false} {<nil> new_conn false}
```

虽然这两个函数在不同的时间间隔运行，但它们在某些时候会发生碰撞（译者注：处理耗时变化，会导致可能退化为并行读写）。有原子指针的代码没有返回关于数据竞争的反馈。这是一个例子，说明原子指针在多线程环境中表现得更好。

# 总结

`Go`原子类型是管理共享资源的一种简单方法。它消除了不断实现互斥来控制资源访问的需要。这并不意味着`mutex`已经过时了，因为在某些操作中仍然需要它们。总之，`atomic.Pointer`是将原子内存原语引入你的程序的一个好方法。它是一个简单防止数据竞争的方法，而不需要花哨的互斥代码。访问这个[链接](https://go.dev/doc/articles/race_detector)，可以看到这篇文章中使用的代码。