<h1 id="top"> Go原生并发基本原理与最佳做法</h1>

- 原文地址：https://benjiv.com/go-native-concurrency-primitives/
- 原文作者：**Benjamin Vesterby**
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w08_Go_Native_Concurrency_Primitives_&_Best_Practices.md
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：

Go语言在创立之初就将并发定为第一公民。 Go语言是一种通过在语言中抽象出并发基本原理[1](https://benjiv.com/go-native-concurrency-primitives/#fn:1)背后的并行细节，使开发者能够轻松地编写高度并行程序的编程语言。

绝大多数语言专注在将并行作为标准库的一部分，或者期望开发者生态提供一个并行库。通过在Go语言内包含并发原理，允让你可以写出利用并行性的程序，而不需要了解编写并行代码的来龙去脉。

目录

- [并发设计](#cd)
  - [通信顺序进程(CSP)](#csp)
  - [通过通信实现并发](#ctc)
    - [阻塞vs通信](#bvc)
- [Go原生并发原理](#gncp)
  - [Go Routines](#gr)
    - [什么是Go Routines?](#wagr)
    - [Go Routines泄漏](#lgr)
    - [Go Rouines的恐慌](#pigr)
  - [Channels](#channels)
    - [在Go里什么是Channels？](#wacig)
    - [在Go中channel如何运作？](#hdcwig)
      - [关闭一个channel](#cac)
    - [channels的类型](#toc)
      - [无缓冲channels](#uc)
      - [带缓冲的channels](#bc)
      - [只读和只写channels](#rowoc)
    - [设计channels的因素](#dcfc)
      - [Owner Pattern](#op)
    - [循环channels](#loc)
    - [Forwarding Channels](#fc)
  - [Select Statements](#ss)
    - [Testing Select Statements](#tss)
    - [Work Cancellation with Context](#wcwc)

<h2 id="cd">并发设计</h2>

Go的设计者们着重强调并发设计，将其作为一个方法论，其思想是重要信息之间是通过沟通[2](https://benjiv.com/go-native-concurrency-primitives/#fn:2)而不是阻塞和共享[3](https://benjiv.com/go-native-concurrency-primitives/#fn:3)。

重视并发设计使得应用程序代码可以按顺序或者在并行下*正确地*执行，而不需要设计和实现并行，这是一个标准[4](https://benjiv.com/go-native-concurrency-primitives/#fn:4)。并发设计的思想并不新鲜，事实上，从瀑布式开发到敏捷开发就是一个很好的例子，这实际上是向并发工程实现的转变(早期迭代，可重复的过程)[5](https://benjiv.com/go-native-concurrency-primitives/#fn:5)。

并发设计是关于编写一个"正确"的程序和编写一个"并行"的程序。

在Go中构建并发程序时要问的问题：

- 我是否阻塞了一个重要区域？
- 是否有更正确的方法去写这个代码？
- 我是否能通过通信来改善我的代码的功能性和可读性？

如果其中有任何一项是肯定的，那么你应该考虑重新思考你的设计，以使用Go的最佳做法。

[*返回顶部*](#top)


<h3 id="csp">通信顺序进程(CSP)</h3>

Go语言[6](https://benjiv.com/go-native-concurrency-primitives/#fn:6)的部分基础来自于Hoare[7](https://benjiv.com/go-native-concurrency-primitives/#fn:7)的一篇论文，该论文讨论了语言需要将并发作为语言的一部分，而不是事后考虑。论文提出了一种线程安全的队列，允许应用程序中的不同进程之间进行数据通信。

如果你通读了这篇论文，你会发现Go中的`channel`的基本原理与论文中原理的描述非常相似，事实上，它来自Rob Pike[8](https://benjiv.com/go-native-concurrency-primitives/#fn:8)之前基于CSP构建语言的工作。

在Pike的一门课程中，他指出的实际问题是 "需要一种编写并发软件的方法来指导我们的设计和实施"[9](https://benjiv.com/go-native-concurrency-primitives/#fn:9)。他继续说到并发编程不是为了让程序跑得更快而并行化，而是"用进程和通信的能力设计一个优雅的，反应灵敏的，高可用的系统"[9](https://benjiv.com/go-native-concurrency-primitives/#fn:9)。

[*返回顶部*](#top)

<h3 id="ctc">通过通信实现并发</h3>

我们从Go的创作者那里听到的最常见的一句话是：[2](https://benjiv.com/go-native-concurrency-primitives/#fn:2) [3](https://benjiv.com/go-native-concurrency-primitives/#fn:3)

> 别用共享内存来通信，而是用通信来共享内存。 --- Rob Pike

这个观点反映了Go是基于[CSP](#csp)设计的，线程间(go runtines)也是基于通信[10](https://benjiv.com/go-native-concurrency-primitives/#fn:10)的基本原理实现的。

下面的代码是一个通信而不是使用mutex来管理共享资源访问的例子：[11](https://benjiv.com/go-native-concurrency-primitives/#fn:11)

```go
// Adapted from https://github.com/devnw/ttl
// a TTL cache implementation for Go.
func readwriteloop(
  incoming <-chan interface{},
) <-chan interface{} {
   // Create a channel to send data to.
  outgoing = make(chan interface{})

  go func(
    incoming <-chan interface{},
    outgoing chan<- interface{},
    ) {
    defer close(outgoing)

    // `value` is the shared 
    // resource or critical section.
    var value interface{}

    for {
      select {

      // incoming is the channel where data is
      // sent to set the shared resource.
      case v, ok := <-incoming:
        if !ok {
          return // Exit the go routine.
        }

        // Write the data to the shared resource.
        value = v.v

      // outgoing is the channel that 
      // the shared resource on request
      case outgoing <- value:
      }
    }
  }(incoming, outgoing)
  
  return outgoing
}
```

让我们看一下上面的代码，看看它做了什么。

1. 注意一下，此代码*没有*用`sync`包或者*任何*阻塞函数。
2. 这个代码只用了Go原生并发关键字`go`，`select`和`chan`
3. go routine管理着共享资源的[所有权](#op)。(第17行)
4. 即使方法里面包含go routine，但是在并行的情况下*不会*出现同时访问共享资源。(第30和34行)
5. [`select`语句](#ss)用来校验是读还是写的请求。(第24和34行)
6. 一个channel从incoming channel读取数值，并更新。(第24行)
7. 一个channel从go routine之外读取，go routine之外执行了一个channel写入当前共享资源的数值。(第34行)

因为在go routine里面没有并行，所以共享资源可以安全地通过返回的[只读channel](#rowoc)访问。事实上，在这里使用`select`提供了很多的好处。[select基本原理](#ss)这个章节会详细描述。

[*返回顶部*](#top)

<h4 id="bvc"> 阻塞和通信</h4>

阻塞[12](https://benjiv.com/go-native-concurrency-primitives/#fn:12)

- 在临界区读和写时暂停进程
- 需要了解阻塞的必要性
- 需要了解如何避免竞态和死锁
- 内存元素被多个进程或携程共享

通信[12](https://benjiv.com/go-native-concurrency-primitives/#fn:12)

- 重要数据在请求时被共享
- 当有数据可以操作的时候才执行逻辑
- 记忆体元件之间是通信沟通的，而不是直接共享的

[*Back To Top*](#top)

<h1 id="gncp"> Go原生并发原理</h1>
<h2 id="gr">Go Routines</h2>
<h3 id="wagr">什么是Go Routines?</h3>

Go routines是轻量级的线程，可以实现逻辑上的进程分割，类似于bash命令后面的`&`[4](https://benjiv.com/go-native-concurrency-primitives/#fn:4)。一旦go routines从父routine分离出来，它就被交给Go runtime执行。然而，与`bash`中的`&`不同的是，这些进程是在Go运行时安排执行的，不一定是并行执行的。[4](https://benjiv.com/go-native-concurrency-primitives/#fn:4)

![1643795792968](https://github.com/gocn/translator/blob/165bb76d803daf69b5f2fe256733dfc42f49c75d/static/images/2022/w08_Go_Native_Concurrency_Primitives_&_Best_Practices.md/1.png)

**图1：Go Routine分离的例子**

>  **注意：** 在这里的"调度"的区别是很重要的，因为Go runtime运行时对go routines执行进行复用，以提高操作系统调度的性能。这意味着不能假设该routine*何时*执行。

<h3 id="lgr"> Go Routines泄漏</h3>

基于原语`go`创建的go routines消耗是低的，但要知道的是它们**不是**免费的 [13](https://benjiv.com/go-native-concurrency-primitives/#fn:13)。清理routines对于确保Go runtime资源的正确垃圾回收是非常重要。

应该花时间在设计清扫的问题上。确保长期运行的程序在发生故障时正确退出。同样重要的是，不要创建无限制数量的go rountines。

可以很简单地创建一个go routine，因为在任何时候你想要并行时，只需要使用原语`go`就可以实现是很诱人的，但是每个routine生成的时候最小的开销是2kb [14](https://benjiv.com/go-native-concurrency-primitives/#fn:14)。如果你的代码创建了太多的go routine，而且每个都有很大的开销，你就堆栈就会爆掉。这在生产环境debug是无比困难的，因为很难说堆栈在哪里溢出和在哪里泄漏。

当堆溢出时，runtime会恐慌，然后应用程序就会退出，同时每个go routines会打印堆信息到标准输出界面。这会往日志里面写入大量杂乱没有用的信息。不仅是堆信息没有用处，而且会有大量数据会输出(每个go routine的日志，包含标识和状态)。这给调试也带了一定难度，因为操作系统上的日志缓冲区可能太小，无法容纳所有的堆栈信息。

> **注意**：平心而论，我只在生产环境中见过这种情况，当时应用程序正在使用超过400,000个大型go routines。这对于大部分应用程序来说是不常见的，也不会是个问题。

TL;DR: 在设计go routines时，要考虑到目的，以便在完成后适当停止 [13](https://benjiv.com/go-native-concurrency-primitives/#fn:13)。

[*返回顶部*](#top)

<h3 id="pigr"> Go Rouines的恐慌</h3>

通常情况下，在Go应用程序中恐慌是违反最佳做法的 [15](https://benjiv.com/go-native-concurrency-primitives/#fn:15) 并且是需要避免的。取代恐慌的是，你应该返回并且处理从你函数返回的错误。然而， 如果有必要使用panic，重要的是要知道，在没有defer recover（直接在该routine中）的Go routine中恐慌，*每次* 都会使你的应用程序崩溃。

> **最佳做法：**
> 不要恐慌！

这在生产环境中调试是非常困难的，因为它需要`stderr`被重写到文件内，因为你的应用程序很可能是作为一个守护程序运行的。如果你有一个日志聚合器，并且它被设置为监视stderr，或平面文件日志，这就比较容易了。对于Docker来说，这有点不同，但它仍然是一个问题。

> 每个Go routine需要自己的`defer/recover` [16](https://benjiv.com/go-native-concurrency-primitives/#fn:16)

```go
defer func() {
  if r := recover(); r != nil {
      // Handle Panic HERE
  }
}()
```

[*返回顶部*](#top)

<h2 id="channels"> Channels</h2>

<h3 id="wacig"> 在Go里什么是Channels？</h3>

什么是channel?

源自Hoare的CSP论文(1977) [7](https://benjiv.com/go-native-concurrency-primitives/#fn:7)，在Go里channel是一个通信机制，支持以线程安全的方式下传输数据。它可以用于两个并行的go routines之间安全且有效地通信，并且不需要互斥锁。

channels将构建并行代码的困难，抽象为Go runtime时的困难，并且提供一个简单的方式让go routines之间通信。从本质上讲，channel的最简单形式就是一个数据队列。

用Rob Pike的话说:“channels是协作的；互斥锁是顺序的” [17](https://benjiv.com/go-native-concurrency-primitives/#fn:17)。

<h3 id="hdcwig"> 在Go中channel如何运作？</h3>

channel默认是阻塞的。这意味着如果你尝试从channel中读取数据，它将阻塞该go routine的执行直到有数据可以读取(例如，数据被写到channel中)。同样的，如果你尝试写入一个数据到channel中，没有接收者读取整个数据(比如，从channel中读取)，它也会阻塞go routine的执行直到有一个接收者。

在Go中channel有许多重要的特性。Go runtime被设计得十分高效，因为如果有一个Go routine在往channel读或者写时被阻塞了，runtime会将这个routine至于睡眠状态直到有事情可以做。一旦这个channel有生产者或者消费者，它会唤醒阻塞的routine，然后继续执行。

了解这一点非常重要，因为它允许你通过使用channel，有效地利用系统CPU的资源。

> **注意**：一个`nil`的channel会永久阻塞。

<h4 id="cac"> 关闭一个channel</h4>

如果你用完一个channel，最好的做法的是关掉它。这个用`close`函数来关闭channel。

有时候有可能不能关掉channel，因为它可能导致你应用程序在其他地方触发恐慌(因为有个channel在往关闭的channel写数据)。在这种情况下，当channel超出可触达的范围时，它将被垃圾回收。

```go
  // Create the channel
  ch := make(chan int)

  // Do something with the channel

  // Close the channel
  close(ch)
```

如果channel限制在同一个范围内(比如，函数)，你可以使用关键词`defer`来确保channel当函数返回时是关闭的。

```go
  // Create the channel
  ch := make(chan int)
  defer close(ch) // Close the channel when func returns

  // Do something with the channel
```

当一个channel被关闭后，它将不再被允许写入。你需要对你如何关闭channel了如指掌，因为一旦你往一个关闭的channel写入数据，runtime就会*恐慌*。所以过早地关闭一个channel会产生意想不到的副作用。

在channel关闭之后，它永远不会在读取时阻塞。这意味着所有阻塞在读取这个channel的routines会被唤醒，然后继续执行。读取后返回的值是这个channel类型的`零值`，同时第二个参数会是`false`。

```go
  // Create the channel
  ch := make(chan int)

  // Do something with the channel

  // Close the channel
  close(ch)

  // Read from closed channel
  data, ok := <-ch
  if !ok {
    // Channel is closed
  }
```

在上面这个例子中，参数`ok`会是`false`，如果channel是关闭的。

>  **注意**：只有标准和[只写](#rowoc)的channels才可以通过`close`函数关闭。

[*返回顶部*](#top)

<h3 id="toc"> channels的类型</h3>

在Go里面有不同类型的channels。每个类型都有不同的优点和缺点。

<h4 id="uc"> 无缓冲channels</h4>

```go
  // Unbuffered channels are the simplest type of channel.
  ch := make(chan int)
```

要创建一个无缓冲的channel，你可以通过`make`函数，提供channel的类型。不要在第二个参数中设置一个大小值，如上面的例子中所看到的那样，就可以了。你就有一个无缓存的channel。

正如[之前章节](#hdcwig)提到的，无缓冲channel默认是阻塞的，会一直阻塞直到有数据可以读或者写。

<h4 id="bc"> 带缓冲的channels</h4>

```go
  // Buffered channels are the other primary type of channel.
  ch := make(chan int, 10)
```

要创建一个带缓冲的channel，你要调用`make`函数，提供channel类型和缓冲区的大小。上面的例子将创建一个缓冲区大小为10的channel。如果你尝试写入一个已满的channel，它会阻塞go routine，直到缓冲区有空间。 如果你尝试从一个空的channel中读数据，它会阻塞go routine，直到有东西可读。

**然而，如果你想往channel写，此时缓冲区也有可写的空间，它就不会阻塞go routine。**

> **注意**：一般来说，只有在真的需要的时候才使用缓冲channel。**最佳做法是使用非缓冲channels**。

<h4 id="rowoc"> 只读和只写channels</h4>

channels的一个有趣的场景是有一个只用于读或写的channel。当你有一个go routine需要从一个channel中读取，但你不希望这个routine往里面写时，这就很有用，反之亦然。这对下面描述的[Owner Pattern](#op)特别有用。

这是创建一个只读或只写channel的语法。

```go
  // Define the variable with var
  var writeOnly chan<- int
  var readOnly <-chan int

  mychan := make(chan int)

  // Assign the channel to the variable
  readOnly = mychan
  writeOnly = mychan
```

箭头表示channel的方向。在`chan`之前的箭头表明数据流是*进入*channel的，而`chan  `之后的箭头表明数据流是*流出*channel的。

一个只读的例子是`time.Tick`的方法：

```go
  // Tick is a convenience wrapper for NewTicker providing access to the ticking
  // channel only
  func Tick(d Duration) <-chan Time
```

该方法返回一个只读的channel，`time`包以指定的时间间隔在内部写入该channel。这种模式确保了时钟滴答的实现逻辑与`time`包相隔离，因为用户不需要能够向channel写入。

当你需要向一个channel写东西，但你知道这个routine不需要从它那里读东西时，只写的channel就很有用。这方面的一个很好的例子是下面描述的[Owner Pattern](#op)。

[*返回顶部*](#top)

<h3 id="dcfc"> 设计channels的因素</h3>

在你的应用程序中是很有必要思考channel的用法的。

设计因素包含：

1. 哪个范围拥有channel？
2. 非所有者有什么能力？
   - 全部
   - 只读
   - 只写
3. channel如何被清理？
4. 哪一个go routine负责清理channel？

<h4 id="op"> Owner Pattern</h4>

Owner Pattern是Go中常见的设计模式，用于确保channel的所有权由创建或拥有该channel的routine正确地管理。这使得一个routine可以管理一个channel的整个生命周期，并确保该channel被正确关闭，然后routines被清理。

这是一个在Go中的Owner Pattern的例子：

```go
func NewTime(ctx context.Context) <-chan time.Time {
  tchan := make(chan time.Time)

  go func(tchan chan<- time.Time) {
    defer close(tchan)

    for {
      select {
      case <-ctx.Done():
        return
      case tchan <- time.Now():
      }
    }
  }(tchan)

  return tchan
}
```

**优点：**

- NewTime控制了channel的常见和清理(第2和第5行)
- 通过定义只读/只写的界限来确保创建的channel都有被清理
- 限制了行为不一致的可能性

关于这个例子的重要说明。`ctx`变量传递给`NewTime`函数，用于向routine发出停止信号。`tchan`是一个普遍的非缓冲channel，但作为只读返回。

当传递到Go routine内部，`tchan`被当做只写channel传递。因为Go routine内部是一个只写channel，所以它有责任去关闭一个用完的channel。

通过使用`select`语句，`time.Now()`的调用只在从channel中读取时执行。这确保了`time.Now()`调用的执行与从channel的读取同步。这种类型的模式有助于预先将CPU cycles降到最低。

[*返回顶部*](#top)

<h3 id="loc"> 循环channels</h3>

从一个channel读取数据的一种方法是使用`for`循环。这在某些情况下是很有用的。

```go
  var tchan <-chan time.Time

  for t := range tchan {
    fmt.Println(t)
  }
```

我不推荐这种做法的原因有几个。 首先，不能保证channel会被关闭（打破循环）。其次，循环不遵守上下文，这意味着如果上下文被取消，循环将永远不会退出。**这第二点特别重要，因为没有优雅的方式来退出routine。**

我建议不要对channel循环，而是采用以下模式，即用一个带有`select`语句的无限循环。这种模式可以确保检查上下文，如果取消了，循环就退出，同时也允许循环仍然从channel中读取。

```go
  var tchan <-chan time.Time

  for {
    select {
    case <-ctx.Done(): // Graceful exit
      return
    case t, ok := <-tchan: // Read from the time ticker
      if !ok { // Channel closed, exit
        return
      }
      fmt.Println(t)
    }
  }
```

我在[select语句](#ss)一节中更详细地讨论了这种方法和`select`语句。

[*返回顶部*](#top)

<h3 id="fc"> 转发channels</h3>

在适当的情况下，从一个channel转发到另一个channle也可以是一种有用的模式。这个用`<- <-`操作符来实现。

这里有一个将channel转发到另一个channel的例子：

```go
func forward(ctx context.Context, from <-chan int) <-chan int {
  to := make(chan int)

  go func() {
    for {
      select {
      case <-ctx.Done():
        return
      case to <- <-from: // Forward from into the to channel
      }
    }
  }()

  return to
}
```

> **注意：** 使用这种模式，你无法检测`from`channel何时关闭。这意味着`from`channel将不断向`to`channel发送数据，而内部程序将永远不会退出，导致零值数据泛滥和routine泄露。

根据你的使用情况，这可能是可取的，然而，重要的是要注意，当你需要检测一个关闭的channel时，这种模式不是一个好主意。

[*返回顶部*](#top)

<h2 id="ss"> select语句</h2>

`select`语句允许在Go应用程序中管理多个channel，可用于触发动作、管理数据或以其他方式创建逻辑并发流。

```go
select {
case data, ok := <- incoming: // Data Read
  if !ok {
    return
  }

  // ...

case outgoing <- data: // Data Write
  // ...

default: // Non-blocking default action
  // ... 
}
```

> `select`语句的一个重要注意事项是，它在本质上是*随机*的。意思是说，如果有多个channel准备同时被读取或写入，`select`语句将随机选择其中一个case语句来执行 [18](https://benjiv.com/go-native-concurrency-primitives/#fn:18)。

<h3 id="tss"> 测试select语句</h3>

select语句的随机性会使测试选择语句变得有点棘手，特别是在测试确保上下文取消正确退出routine时。

有一个如何使用统计测试来测试select语句的[例子](https://github.com/devnw/plex/blob/2d4f8fe223ab71f488d2d6f5e3dcfad77250d28d/plex_test.go#L202)，测试的执行次数可以确保测试失败的低概率。

这个测试的工作原理是，在两个上下文中只有一个被取消的情况下，通过一个并行routine运行同一个被取消的上下文100次。在这种情况下，总是有一个channel的消费者，所以每次循环运行时，有50%的可能性会执行[context用例](https://github.com/devnw/plex/blob/2d4f8fe223ab71f488d2d6f5e3dcfad77250d28d/plex.go#L239)。

在50%的机会没有执行上下文用例的情况下执行100次，*所有*100次测试中，测试不能检测到上下文取消的机会非常非常低。

[*返回顶部*](#top)

<h3 id="wcwc">用context来实现取消</h3>

在构建Go应用程序的早期，用户用一个`done` channel来构建应用程序，他们会创建一个看起来像这样的channel：`done := make(chan struct{})` 。这是一个非常简单的方法，向一个routine发出它应该退出的信号，因为你所要做的就是关闭channel并将其作为退出的信号。

```go
// Example of a simple done channel
func main() {
  done := make(chan struct{})

    
  go doWork(done)

  go func() {
    // Exit anything using the done channel
    defer close(done)

    // Do some more work
  }()

  <-done
}

func doWork(done <-chan struct{}) {
  for {
    select {
    case <-done:
      return
    default: 
      // ...
    }
  }
}
```

这种模式变得很普遍，以至于Go团队创建了[context包](https://golang.org/pkg/context/)作为替代。这个包提供了一个`context.Context`的接口，可以用来向一个routine发出信号，告诉它在监听到`Done`方法返回的只读channel时应该退出。

```go
  import "context"

  func doWork(ctx context.Context) {
    for {
      select {
      case <-ctx.Done():
        return
      default: 
        // ...
    }
  }
}
```

除此之外，他们还提供了一些方法来创建嵌套式的context、超时的context和一个可以被取消的context。

- `context.WithCancel`
  - 返回一个`context.Context`以及`context.CancelFunc`函数字段，可以用来取消context。
- `context.WithTimeout`
  - 与`WithCancel`的返回相同，但有一个背景超时，在指定的`time.Duration`过后将取消context。
- `context.WithDeadline`
  - 与`WithCancel`的返回相同，但有一个背景期限，在指定的`time.Time`过后，将取消context。

> **最佳做法：**
> 接收context的函数的第一个参数应该***始终是***context，而且应该命名为`ctx`。

[*返回顶部*](#top)

---

1. [Programming Language Primitives are the simplest elements of a language](https://en.wikipedia.org/wiki/Language_primitive)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:1)
2. [Don’t communicate by sharing memory, share memory by communicating.](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=2m48s)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:2)
3. [Share Memory By Communicating](https://go.dev/blog/codelab-share)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:3)
4. [Concurrency is not Parallelism by Rob Pike](https://youtu.be/oV9rvDllKEg)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:4)
5. [Concurrent engineering](https://en.wikipedia.org/wiki/Concurrent_engineering)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:5)
6. [Bell Labs and CSP Threads](https://swtch.com/~rsc/thread/)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:6)
7. [Communicating Sequential Processes by Hoare 1978](https://www.cs.cmu.edu/~crary/819-f09/Hoare78.pdf)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:7)
8. [Newsqueak: A Language for Communicating with Mice - Rob Pike](https://swtch.com/~rsc/thread/newsqueak.pdf)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:8)
9. [Introduction to Concurrent Programming - Rob Pike](http://herpolhode.com/rob/lec1.pdf)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:9)
10. [Communication - Go Proverbs by Rob Pike](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=2m48s)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:10)
11. [TTL (Time To Live) Cache Implementation for Go](https://github.com/devnw/ttl)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:11)
12. [Channels Vs Mutex - Rob Pike](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=4m20s)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:12)
13. [Goroutine Lifetimes](https://github.com/golang/go/wiki/CodeReviewComments#goroutine-lifetimes)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:13)
14. [Minimum Stack Size of a Go Routine](https://github.com/golang/go/blob/8f2db14cd35bbd674cb2988a508306de6655e425/src/runtime/stack.go#L72)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:14)
15. [Don’t Panic](https://github.com/golang/go/wiki/CodeReviewComments#dont-panic)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:15)
16. [Defer, Panic, and Recover](https://go.dev/blog/defer-panic-and-recover)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:16)
17. [Channels orchestrate; mutexes serialize](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=4m20s)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:17)
18. [Stochasticity of the Select statement](https://github.com/golang/go/blob/6178d25fc0b28724b1b5aec2b1b74fc06d9294c7/src/runtime/select.go#L177)  [↩︎](https://benjiv.com/go-native-concurrency-primitives/#fnref:18)
