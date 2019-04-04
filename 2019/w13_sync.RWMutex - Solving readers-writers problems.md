# sync.RWMutex - 解决并发读写问题

- 原文地址: https://medium.com/golangspec/sync-rwmutex-ca6c6c3208a0
- 原文作者: [Michał Łowicki](https://medium.com/@mlowicki)
- 译文出处: https://medium.com
- 本文永久链接: 
- 译者: [fivezh](https://github.com/fivezh), [watermelo](https://github.com/watermelo)
- 校对者:

![](https://cdn-images-1.medium.com/max/1000/1*qmHZVxZmPP9w5iMqN7GWMw.jpeg)

当多个线程访问共享数据时，会出现并发读写问题([Reader-Writer problems](https://en.wikipedia.org/wiki/Readers%E2%80%93writers_problem))。有两种访问数据的线程类型：
- 读线程Reader：只进行数据读取
- 写线程Writer：进行数据修改

当Writer获取到数据的访问权限后，其他任何线程(Reader或Writer)都无权限访问此数据。这种约束亦存在于现实中，比如，当Writer在修改数据无法保证原子性时(如数据库)，此时读取未完成的修改必须被阻塞，以防止加载脏数据(译者注：数据库中的脏读)。还有许多诸如此类的核心问题，例如：
- Writer不能无限等待
- Reader不能无限等待
- 不允许线程出现无限等待

多读/单写互斥锁(如[sync.RWMutex](https://golang.org/pkg/sync/#RWMutex))的具体实现解决了一种并发读写问题。接下来，让我们看下在`Go`语言中是如何实现的，同时它提供了哪些的数据可靠性保证机制。

作为额外的工作，我们将深入研究分析竞态情况下的互斥锁。

## 用法

在深入研究实现细节之前，我们先看看`sync.RWMutex`的使用实例。下面的程序使用读写互斥锁来保护临界区-`sleep()`函数调用。为了使整个过程可视化，临界区部分计算了当前正在执行的Reader和Writer的数量([源码](https://play.golang.org/p/xoiqW0RQQE9))。
```golang
package main
import (
    "fmt"
    "math/rand"
    "strings"
    "sync"
    "time"
)
func init() {
    rand.Seed(time.Now().Unix())
}
func sleep() {
    time.Sleep(time.Duration(rand.Intn(1000)) * time.Millisecond)
}
func reader(c chan int, m *sync.RWMutex, wg *sync.WaitGroup) {
    sleep()
    m.RLock()
    c <- 1
    sleep()
    c <- -1
    m.RUnlock()
    wg.Done()
}
func writer(c chan int, m *sync.RWMutex, wg *sync.WaitGroup) {
    sleep()
    m.Lock()
    c <- 1
    sleep()
    c <- -1
    m.Unlock()
    wg.Done()
}
func main() {
    var m sync.RWMutex
    var rs, ws int
    rsCh := make(chan int)
    wsCh := make(chan int)
    go func() {
        for {
            select {
            case n := <-rsCh:
                rs += n
            case n := <-wsCh:
                ws += n
            }
            fmt.Printf("%s%s\n", strings.Repeat("R", rs),
                    strings.Repeat("W", ws))
        }
    }()
    wg := sync.WaitGroup{}
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go reader(rsCh, &m, &wg)
    }
    for i := 0; i < 3; i++ {
        wg.Add(1)
        go writer(wsCh, &m, &wg)
    }
    wg.Wait()
}
```

> `play.golang.org`加载的程序环境是确定性的(比如开始时间)，所以`rand.Seed(time.Now().Unix())`总是返回相同的数值，此时程序的执行结果可能总是相同的。为了避免这种情况，可通过修改不同的随机种子值或者在自己的机器上执行程序。

程序执行结果：
```
W

R
RR
RRR
RRRR
RRRRR
RRRR
RRR
RRRR
RRR
RR
R

W

R
RR
RRR
RRRR
RRR
RR
R

W
```

> 译者注：不同机器上运行结果会有所相同

每次执行完一组`goroutine`(Reader和Writer)的临界区代码后，都会打印新的一行。很显然，RWMutex允许至少一个Reader(一个或多个Reader)而只能有一个Writer。

同样重要且将进一步讨论的是：一旦Writer调用`Lock()`，将会使新的Reader被阻塞。Writer会等待已存在的一组Reader完成正在执行的任务，当这一组任务完成后，Writer将开始执行。从输出可以很明显的看到，每一行的R都会递减一个，直到没有R之后将打印一个W。 (感觉这样比较容易理解)
```
...
RRRRR
RRRR
RRR
RR
R
W
...
```

一旦Writer结束，之前被阻塞的Reader将恢复，然后下一个Writer也将开始启动。值得一提的是，如果Writer完成并且有Reader和Writer都在等待，那么首个Reader将解除阻塞，然后轮到Writer。这种方式使得Writer需等待当前这组Reader完成，所以无论Reader还是Writer都不会有无限等待的情况。

## 实现

![](https://cdn-images-1.medium.com/max/1000/1*Gg_vmyWlU35r3w_L4r4SYw.jpeg)

> 注意，本文针对的`RWMutex`实现([Go: 718d6c58](https://github.com/golang/go/blob/718d6c5880fe3507b1d224789b29bc2410fc9da5/src/sync/rwmutex.go))在Go不同版本中可能随时有修改。

`RWMutex`为Reader提供两个方法(`RLock`和`RUnlock`)、也为Writer提供了两个方法`(Lock`和`Unlock`)

## 读锁RLock

为了简洁起见，我们先跳过源码中竞态检测相关部分(它们将被...代替)。
```golang
func (rw *RWMutex) RLock() {
    ...
    if atomic.AddInt32(&rw.readerCount, 1) < 0 {    
        runtime_SemacquireMutex(&rw.Readerem, false)
    }
    ...
}
```

`readerCount`字段是`int32`类型的值，表示待处理的Reader数量(正在读取数据或被Writer阻塞)。这基本上是已调用RLock函数，但尚未调用RUnlock函数的Reader数量。

[atomic.AddInt32](https://golang.org/pkg/sync/atomic/#AddInt32)等价于如下原子性表达：
```golang
*addr += delta
return *addr
```

`addr`是`*int32`类型变量，`delta`是`int32`类型。因为此操作具有原子性，所以累加`delta`操作不会影响其他线程(更多详见[Fetch-and-add](https://en.wikipedia.org/wiki/Fetch-and-add))。

> 如果Writer未参与，则`readerCount`总是大于或等于0，此时Reader只需要调用`atomic.AddInt32`，这是一种很快的非阻塞方式。

## 信号量Semaphore
信号量是`Edsger Dijkstra`发明的数据结构，在解决多种同步问题时很有用。其本质是一个整数，并关联两个操作：
- 申请`acquire`(也称为wait、decrement或P操作)
- 释放`release`(也称signal、increment或V操作)

`acquire`操作将信号量减一，如果结果值为负则线程阻塞，且直到其他线程进行了信号量累加。如结果为正数，线程则继续执行。

`release`操作将信号量加一，如存在被阻塞的线程，此时他们中的一个线程将解除阻塞。

Go的运行时提供的`runtime_SemacquireMutex`和`runtime_Semrelease`函数可用来实现`sync.RWMutex`互斥锁。

## 锁Lock
实现源码：
```golang
func (rw *RWMutex) Lock() {
    ...
    rw.w.Lock()
    r := atomic.AddInt32(&rw.readerCount, -rwmutexMaxReader) + rwmutexMaxReader
    if r != 0 && atomic.AddInt32(&rw.readerWait, r) != 0 {     
        runtime_SemacquireMutex(&rw.Writerem, false)
    }
    ...
}
```
Writer通过`Lock`方法获取共享数据的排他访问权限。首先，它会申请排斥其他写操作的互斥锁，此互斥锁在`Unlock`函数的最后才会进行解锁。下一步，将`readerCount`减去`rwmutexMaxReader`（值为1左移30位, `1<<30`）。当`readerCount`变为负数时，Rlock将阻塞接下来的所有读请求。

再回过头来看下`Rlock()`函数中逻辑：
```golang
if atomic.AddInt32(&rw.readerCount, 1) < 0 {
    // A writer is pending, wait for it.    
    runtime_SemacquireMutex(&rw.Readerem, false)
}
```

由于新的Reader将被阻塞，那么已运行的Reader会怎样呢？`readerWait`字段用来记录当前Reader的数量和阻塞的Writer的数量。当最后一个Reader在使用后面讨论的`RUnlock`方法解锁互斥锁后，此信号量将被解除阻塞。

如果没有有效的Reader，那么Writer将继续其执行。

## 最大Reader数rwmutexMaxReader
在[rwmutex.go](https://github.com/golang/go/blob/718d6c5880fe3507b1d224789b29bc2410fc9da5/src/sync/rwmutex.go)中定义的常量：
```golang
const rwmutexMaxReader = 1 << 30
```
那么，其用途是什么，以及`1<<30`表示什么意义呢？
`readerCount`字段是[int32](https://golang.org/pkg/builtin/#int32)类型，其范围为：`[-1 << 31, (1 << 31) — 1] or [-2147483648, 2147483647]`

`RWMutext`使用此字段来计算挂起的Reader和将被标记挂起的Writer。在`Lock`方法中：
```golang
r := atomic.AddInt32(&rw.readerCount, -rwmutexMaxReader) + rwmutexMaxReader
```
将`readerCount`字段减去`1<<30`，当`readerCount`负值时表示Writer挂起，且`readerCount + rwmutexMaxReader`是当前挂起的Reader数量。通过这种方式，限制可以被挂起的Reader数量。如果有`rwmutexMaxReader`或更多挂起的Reader，那么`readerCount`将是非负值，此时将导致整个机制的崩溃。所以，Reader实际的限制数是：`rwmutexMaxReader - 1`，而此值`1073741823`超过了`10亿`。

## 读解锁RUnlock

实现源码：
```golang
func (rw *RWMutex) RUnlock() {
    ...
    if r := atomic.AddInt32(&rw.readerCount, -1); r < 0 {
        if r+1 == 0 || r+1 == -rwmutexMaxReader {
            race.Enable()
            throw("sync: RUnlock of unlocked RWMutex")
        }
        // A writer is pending.
        if atomic.AddInt32(&rw.readerWait, -1) == 0 {
            // The last reader unblocks the writer.       
            runtime_Semrelease(&rw.Writerem, false)
        }
    }
    ...
}
```

此方法将使`readerCount`减小(RLock方法中增加)。如`readerCount`值为负，则表示当前存在Writer正在等待或运行。这是因为在`Lock()`方法中`readerCount`减去了`rwmutexMaxReader`。然后，当检查到将完成的Reader数量(readerWait数值)最终为0时，则表示Writer可以最终申请信号量。

## 解锁Unlock

实现源码：
```golang
func (rw *RWMutex) Unlock() {
    ...
    r := atomic.AddInt32(&rw.readerCount, rwmutexMaxReader)
    if r >= rwmutexMaxReader {
        race.Enable()
        throw("sync: Unlock of unlocked RWMutex")
    }
    for i := 0; i < int(r); i++ {
        runtime_Semrelease(&rw.Readerem, false)
    }
    rw.w.Unlock()
    ...
}
```
解锁被Writer持有的互斥锁时，首先通过`atomic.AddInt32`将`readerCount`加上`rwmutexMaxReader`，这时`readerCount`将变成非负值。如`readerCount`比0大，则表示存在Reader正在等待Writer执行完成，此时应唤醒这些等待的Reader。之后写锁将被释放，从而允许其他Writer为了写入而锁定互斥锁。

如果Reader或Writer尝试解锁未锁定的互斥锁时，调用`Unlock`和`Runlock`方法将抛出错误([示例源码](https://play.golang.org/p/YMdFET74olU))。
```golang
m := sync.RWMutex{}
m.Unlock()
```
输出：
```
fatal error: sync: Unlock of unlocked RWMutex
...
```
## 递归读锁定Recursive read locking
文档描述：
> 如果一个`goroutine`持有了读锁，而此时另一个`goroutine`调用`Lock`申请加写锁，此后在最初的读锁被释放前其他`goroutine`不能获取到读锁。实际上，这能防止递归读锁，这种策略保证了锁最终再次可用，已阻塞的`Lock`调用会阻止其他新的Reader来申请锁。

`RWMutex`的工作方式是，如果有一个等待中的Writer，那么不论读锁是否已获取到，所有尝试调用`RLock`的都将被阻塞。
> RWMutex works in a way that if there is a pending writer then all attempts to call RLock will lock no matter if e.g. read lock has been already acquired (source code):

示例代码：
```golang
package main
import (
    "fmt"
    "sync"
    "time"
)
var m sync.RWMutex
func f(n int) int {
    if n < 1 {
        return 0
    }
    fmt.Println("RLock")
    m.RLock()
    defer func() {
        fmt.Println("RUnlock")
        m.RUnlock()
    }()
    time.Sleep(100 * time.Millisecond)
    return f(n-1) + n
}
func main() {
    done := make(chan int)
    go func() {
        time.Sleep(200 * time.Millisecond)
        fmt.Println("Lock")
        m.Lock()
        fmt.Println("Unlock")
        m.Unlock()
        done <- 1
    }()
    f(4)
    <-done
}
```
输出：
```
RLock
RLock
RLock
Lock
RLock
fatal error: all goroutines are asleep - deadlock!
```

## 复制锁Copying locks
`go tool vet`可以检测锁是否被复制了，因为复制锁会导致死锁。更多关于此问题可参考之前的文章：[Detect locks passed by value in Go](https://medium.com/golangspec/detect-locks-passed-by-value-in-go-efb4ac9a3f2b)

## 性能Performance
之前有人发现，在CPU核数增多时RWMutex的性能会有下降，详见：[sync: RWMutex scales poorly with CPU count](https://github.com/golang/go/issues/17973)

## 争用Contention[TODO: 翻译待定]

Go版本≥1.8之后，支持分析争用的互斥锁([runtime: Profile goroutines holding contended mutexes.](https://github.com/golang/go/commit/ca922b6d363b6ca47822188dcbc5b92d912c7a4b))。我们来看下如何做：
```golang
package main
import (
    "net/http"
    _ "net/http/pprof"
    "runtime"
    "sync"
    "time"
)
func main() {
    var mu sync.Mutex
    runtime.SetMutexProfileFraction(5)
    for i := 0; i < 10; i++ {
        go func() {
            for {
                mu.Lock()
                time.Sleep(100 * time.Millisecond)
                mu.Unlock()
            }
        }()
    }
    http.ListenAndServe(":8888", nil)
}
> go build mutexcontention.go
> ./mutexcontention
```
当`mutexcontention`程序运行时，执行pprof：
```sh
> go tool pprof mutexcontention http://localhost:8888/debug/pprof/mutex?debug=1
Fetching profile over HTTP from http://localhost:8888/debug/pprof/mutex?debug=1
Saved profile in /Users/mlowicki/pprof/pprof.mutexcontention.contentions.delay.003.pb.gz
File: mutexcontention
Type: delay
Entering interactive mode (type "help" for commands, "o" for options)
(pprof) list main
Total: 57.28s
ROUTINE ======================== main.main.func1 in /Users/mlowicki/projects/golang/src/github.com/mlowicki/mutexcontention/mutexcontention.go
0     57.28s (flat, cum)   100% of Total
.          .     14:   for i := 0; i < 10; i++ {
.          .     15:           go func() {
.          .     16:                   for {
.          .     17:                           mu.Lock()
.          .     18:                           time.Sleep(100 * time.Millisecond)
.     57.28s     19:                           mu.Unlock()
.          .     20:                   }
.          .     21:           }()
.          .     22:   }
.          .     23:
.          .     24:   http.ListenAndServe(":8888", nil)
```

注意，为什么这里耗时57.28s，且指向了`mu.Unlock()`呢？

当`goroutine`调用`Lock`时阻塞在互斥锁时，记录当前发生的准确时间，就是`acquiretime`。当另一个`groutine`解锁互斥锁，至少存在一个`goroutine`在等待申请锁，则其中一个解除阻塞并调用其`mutexevent`函数。该函数检查通过`SetMutexProfileFraction`设置的速率来决定此事件应被保留还是丢弃。此事件包含整个等待的时间（当前时间-`acquiretime`时间）。被特定互斥锁阻塞的各`goroutines`的等待时间被收集和展示。

在Go 1.11（[sync: enable profiling of RWMutex](https://github.com/golang/go/commit/88ba64582703cea0d66a098730215554537572de)）中将增加读锁（Rlock和RUnlock）的争用的性能分析。
[TODO:最后一句翻译不太对，看原文commit是关于profile的]
Contention on reader lock (Rlock and RUnlock) will be added in Go 1.11.

### 资料Resources

- Allen B. Downey: The Little Book of Semaphores
- [Documentation of sync.RWMutex](https://golang.org/pkg/sync/#RWMutex)
- [Wikipedia: Reader-Writer problem](https://en.wikipedia.org/wiki/Reader%E2%80%93Writer_problem)
- [Reusable barriers in Golang](https://medium.com/golangspec/reusable-barriers-in-golang-156db1f75d0b)
- [Synchronization queues in Golang](https://medium.com/golangspec/synchronization-queues-in-golang-554f8e3a31a4)




备注：
- critical section：临界区
- Mutual exclusion，缩写 Mutex：互斥锁