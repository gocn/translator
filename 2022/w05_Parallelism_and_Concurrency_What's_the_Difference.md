## 以Go为例-探究并行与并发的区别

- 原文地址：https://benjiv.com/parallelism-vs-concurrency/
- 原文作者：Benjamin Vesterby
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w05_Parallelism_and_Concurrency_What's_the_Difference.md
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：[ ]( )

在软件内并行是指多条指令同时执行。每个编程语言都有各自实现并行，或者像Go，将并行作为语言的一部分，提供原生支持。并行让软件工程师能够同时在多核处理器上并行执行任务，从而抛开硬件的物理限制。[1](https://benjiv.com/parallelism-vs-concurrency/#fn:1)

通常情况下，由于[构建并行模块](https://benjiv.com/parallelism-vs-concurrency/#building-blocks-of-parallelism)的复杂性，一个应用程序的并行程度取决于工程师编写软件的能力。

**并行任务的例子：**

- 多人同时在餐厅点单
- 多个收银员在杂货铺
- [多核CPU](https://benjiv.com/quick-recap-single-multi-core/#multi-core-and-multiple-cpu-processing)

事实上，在任何一个应用程序中都有多层含义的并行。有应用程序本身的并行，这是由应用程序开发人员定义的，还有由操作系统协调的物理硬件上的CPU执行的指令的并行（或复用）。

> **注意**：一般情况下，应用程序必须明确写出他们使用并行。这个需要工程师需要有技能写出"正确"的可并行的代码。



Table Of Content

[Building Blocks of Parallelism](#bbop)

- [Processes](#processes)
- [Threads](#threads)
- [Critical Sections](#cs)
- [Complications of Parallelism](#cop)
  - [Race Conditions](#rc)
  - [DeadLocks](#deadlock)
- [Barriers](#barriers)
  - [Mutual Exclusions Locks(Mutexes)](#mutexes)
  - [Semaphores](#semaphores)
  - [Busy Waiting](#bw)
  - [Wait Groups](#wg)

[What is Concurrency](#wic)


<h3 id="bbop" >构建并行</h3>

应用程序开发人员利用抽象概念来描述一个应用程序的并行。这些抽象概念通常在每个实现并行的编程语言上会有所不同，但是概念是一样的。举个例子，在C语言，并行是通过[pthread](https://en.wikipedia.org/wiki/Pthreads)来定义的。在Go，并行是通过[goroutines](https://en.wikipedia.org/wiki/Goroutine)来定义的。

<h4 id="processes" >进程</h4>

一个进程是一个单一的执行单元，包含它自己的"程序计数器，寄存器和变量"。从概念上来讲，每个进程有它自己的虚拟CPU"[2](https://benjiv.com/parallelism-vs-concurrency/#fn:2)。这一点很重要，因为涉及到进程在创建和管理过程中的开销。除了创建进程时的开销，每个进程只允许访问自己的内存。这表示进程不能访问其他进程的内存。

如果多个执行线程(并行任务)需要访问一些共享资源时，这会是一个问题。

<h4 id="threads" >线程</h4>

线程是作为一种方法被引入的，它允许在同一进程中访问共享内存，但在不同的并行执行单元上。线程基本上是自己的进程，但是可以访问父进程的共享地址空间。

线程相较于进程只需要更少的开销，因为它们不需要为了每个线程创建新进程，并且资源可以被共享或者复用。

这里有一个在Ubuntu 18.04下，克隆进程和创建线程的开销比较:[3](https://benjiv.com/parallelism-vs-concurrency/#fn:3)

```shell
# Borrowed from https://stackoverflow.com/a/52231151/834319
# Ubuntu 18.04 start_method: fork
# ================================
results for Process:

count    1000.000000
mean        0.002081
std         0.000288
min         0.001466
25%         0.001866
50%         0.001973
75%         0.002268
max         0.003365 

Minimum with 1.47 ms
------------------------------------------------------------

results for Thread:

count    1000.000000
mean        0.000054
std         0.000013
min         0.000044
25%         0.000047
50%         0.000051
75%         0.000058
max         0.000319 

Minimum with 43.89 µs
------------------------------------------------------------
Minimum start-up time for processes takes 33.41x longer than for threads.
```

<h4 id="cs" >临界区</h4>

临界区是共享的内存部分，它被进程中的各种并行任务所需要。这个部分可能是共享数据，类型或者资源。(见下方的范例[4](https://benjiv.com/parallelism-vs-concurrency/#fn:4))

<img src="https://github.com/gocn/translator/blob/master/static/images/2022/w05_Parallelism_and_Concurrency_What's_the_Difference%3F/1.png?raw=true" style="zoom:50%"/>

<h4 id="cop" >并行的复杂性</h4>

由于一个进程的线程在同一内存空间中执行，因此存在着临界区被多个线程同时访问的风险。在应用程序中这个可能导致数据损坏或其他无法预料的行为。

这里有2个主要问题当多个线程同一时间访问共享内存的时候。

<h5 id="rc" >竞态</h5>

举个例子，想象一个进程的线程正在从一个共享内存地址读取一个数值，同时其他线程正在往同一个地址写一个新的数值。如果第一个线程在第二个线程写数值之前读取了数值，第一个线程就会读取到旧的数值。

这个导致应用程序出现不符合预期的情况。

<h5 id="deadlock" >死锁</h5>

当两个或多个线程在等待对方做某事时，就会出现死锁。这个会导致应用程序挂起或者崩溃。

有一个例子是这样的，当一个线程等待一个时机去执行临界区的同时，另一个线程也正在等待其他线程满足条件后去执行相同的临界区。如果第一个线程正在等待满足时机，然后第二个线程也正在等待第一个线程，那这两个线程将一直等待下去。

第二种形式的死锁会发生在尝试使用[互斥锁](https://benjiv.com/parallelism-vs-concurrency/#mutual-exclusions-locks-mutexes)保护竞态。

![1643206061070](https://github.com/gocn/translator/blob/master/static/images/2022/w05_Parallelism_and_Concurrency_What's_the_Difference%3F/2.png?raw=true)

<h4 id="barriers" >屏障</h4>

屏障可以称为一个同步点，它管理一个进程中多个线程对共享资源或临界区的访问。

这些屏障允许应用程序开发者去控制并行访问，从而保证资源不会在不安全的情况下被访问。


<h5 id="mutexes" >互斥锁(Mutexes)</h5>

互斥锁是屏障的一个类型，它只允许一个线程在同一时间访问共享资源。这对于防止在读取或写入共享资源时通过锁定和解锁出现竞态的情况非常有用。


```go
// Example of a mutex barrier in Go
import (
  "sync"
  "fmt"
)

var shared string
var sharedMu sync.Mutex

func main() {

  // Start a goroutine to write to the shared variable
  go func() {
    for i := 0; i < 10; i++ {
      write(fmt.Sprintf("%d", i))
    }
  }()

  // read from the shared variable
  for i := 0; i < 10; i++ {
    read(fmt.Sprintf("%d", i))
  }
}

func write(value string) {
  sharedMu.Lock()
  defer sharedMu.Unlock()

  // set a new value for the `shared` variable
  shared = value
}

func read() {
  sharedMu.Lock()
  defer sharedMu.Unlock()

  // print the critical section `shared` to stdout
  fmt.Println(shared)
}
```

如果我们看上面的例子，我们可以看到`共享`变量被互斥锁保护着。这意味着只有一个线程在一个时间点可以访问`共享`变量。这个保证了`共享`变量不被损坏，并且是一个可预计的行为。

> **注意**: 在使用互斥锁时，需要注意的一个点是，要在函数返回的时候释放互斥锁。在Go，举个例子，这个操作可以通过关键字`defer`实现。这个保证了其他线程可以访问到共享资源。

<h5 id="semaphores" >信号</h5>

信号是一种类型的屏障，允许一个时间点一定数量的线程访问共享资源。这个和互斥锁的区别在于，访问资源的线程数量不会被限制为1个。

在Go标准库没有信号的实现，但是可以通过channels[5](https://benjiv.com/parallelism-vs-concurrency/#fn:5)来实现。

<h5 id="bw" >忙等待</h5>

忙等待是一个技术用于线程等待一个满足的条件。通常用于等待一个计数器达到某个数值。

```go
// Example of Busy Waiting in Go
var x int

func main() {
  go func() {
    for i := 0; i < 10; i++ {
      x = i
    }
  }()

  for x != 1 { // Loop until x is set to 1
    fmt.Println("Waiting...")
    time.Sleep(time.Millisecond * 100)
  }  
}
```

因此，忙等待需要一个等待条件满足的循环，该循环对共享资源进行读取或写入，必须由一个互斥锁来保护以确保正确的行为。

上面例子的问题是那个循环在访问一个没有被互斥锁保护的临界区。这可能导致竞态，这个循环读取的数值可能已经被另一个进程里的线程修改了。事实上，上面的例子是一个很好的竞态例子。很有可能这个应用程序永远都不会退出，因为无法保证这个循环是否会足够快地读取到`x`的数值，同时读取出来的数值都是`1`，这就意味着循环永远不会退出。

如果我们要用互斥锁保护变量`x`，那么循环就会被保护并且应用程序会退出，但这仍然不完美，设置`x`的循环仍然可以快到在读取值的循环执行之前击中互斥锁两次（尽管不太可能）。

```go
import "sync"

var x int
var xMu sync.Mutex

func main() {
  go func() {
    for i := 0; i < 10; i++ {
      xMu.Lock()
      x = i
      xMu.Unlock()
    }
  }()

  var value int
  for value != 1 { // Loop until x is set to 1
    xMu.Lock()
    value = x // Set value == x
    xMu.Unlock()
  }  
}
```

通常情况下忙等待不是一个好的想法。最好的办法是使用信号或者一个互斥锁去确保临界区是受保护的。 我们将介绍在Go中处理这个问题的更好方法，但它说明了编写 "正确的"可并行代码的复杂性。

<h5 id="wg" >等待组(Wait Groups)</h5>

等待组是一个用来保证所有并行代码路径在继续之前完成处理的方法。在Go里，这个用标准库中的`sync`包中提供的`sync.WaitGroup`来实现。

```go
// Example of a `sync.WaitGroup` in Go
import (
  "sync"
)

func main() {
  var wg sync.WaitGroup
  var N int = 10

  wg.Add(N)
  for i := 0; i < N; i++ {
    go func() {
      defer wg.Done()
      
      // do some work      
    }()
  }

  // wait for all of the goroutines to finish
  wg.Wait()
}
```

在上面这个例子的`wg.Wait()`是一个阻塞调用。这个表示主线程会等到所有协程完成后再继续执行，并且对应的`defer wg.Done()`已经被调用。WaitGroup的内部实现是一个计数器，当每个协程在调用`wg.Add(N)`后会加1，同时协程被加到WaitGroup内。当计数器计到0，主线程会继续执行或者在这个例子中会退出。

<h3 id="wic" >什么是并发？</h3>

并发和并行经常混为一谈。为了更好地理解并发和并行的区别，让我们看一个现实生活中的并发例子。

如果我们用餐厅来当做例子，餐厅里面会有几种不同工作类型(或可复制的程序)的组别。

1. 接待（负责为客人安排座位）
2. 服务员（负责接单，并提供食物）
3. 厨房（负责烹饪食物）
4. 售货员（负责清理桌子
5. 洗碗工（负责清理餐具）

每个组别负责不同的任务，所有这些任务的最终结果都是让顾客吃到一顿饭。**这称之为并发**，专门的工作中心，可以专注于单独的任务，这些任务结合起来就会产生一个结果。

如果餐厅只雇佣一个员工来做所有的任务，这对于一个高效率的餐厅是一个限制。这称之为序列化。如果在餐厅里只有一个服务员，那么在一个时间只能够处理一个订单。

并行性是指将并发的任务分配到多个资源上的能力。在餐厅中，这可能会包含服务，食物准备和清理。如果有多个服务员，那么同一时间就可以处理多个订单。

每个组可以专注在他们自己的工作中心，不需要担心上下文切换，最大吞吐量，或最小延迟。

其他有同时进行的工作中心的行业例子包括工厂工人和装配线工人。从本质上讲，任何可以被分解成较小的可重复任务的过程都可以被认为是并发的，因此*当使用合适的并发设计*的时候可以被并行处理。

**TL:DR**：并发实现正确的并行，但是并行对并发代码不是必要的。[6](https://benjiv.com/parallelism-vs-concurrency/#fn:6)

---

1. Andrew S. Tanenbaum and Herbert Bos, *Modern Operating Systems* (Boston, MA: Prentice Hall, 2015), 517. [↩︎](https://benjiv.com/parallelism-vs-concurrency/#fnref:1)
2. Andrew S. Tanenbaum and Herbert Bos, *Modern Operating Systems* (Boston, MA: Prentice Hall, 2015), 86. [↩︎](https://benjiv.com/parallelism-vs-concurrency/#fnref:2)
3. [Benchmarking Process Fork vs Thread Creation on Ubuntu 18.04](https://stackoverflow.com/a/52231151/834319)  [↩︎](https://benjiv.com/parallelism-vs-concurrency/#fnref:3)
4. [Flowgraph description of critical section - Kartikharia](https://commons.wikimedia.org/wiki/File:Critical_section_fg.jpg)  [↩︎](https://benjiv.com/parallelism-vs-concurrency/#fnref:4)
5. [Example semaphore implementation in Go](http://www.golangpatterns.info/concurrency/semaphores)  [↩︎](https://benjiv.com/parallelism-vs-concurrency/#fnref:5)
6. [Concurrency is not Parallelism by Rob Pike](https://youtu.be/oV9rvDllKEg)  [↩︎](https://benjiv.com/parallelism-vs-concurrency/#fnref:6)
