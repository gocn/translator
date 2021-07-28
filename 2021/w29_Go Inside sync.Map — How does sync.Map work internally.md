# Go: Inside sync.Map — How does sync.Map work internally?

# Go sync map 的内部实现

* 原文地址：https://sreramk.medium.com/go-inside-sync-map-how-does-sync-map-work-internally-97e87b8e6bf
* 原文作者：`Sreram K`
* 本文永久链接：

- 译者：[guzzsek](https://github.com/laxiaohong)
- 校对：[x'x](https:/github.com/**)

提示: 这篇文章有点长


## 目录
1.  _Introduction 
1. 引言 
    a. A brief introduction to concurrency and how it applies in this context_
    a. 简单介绍并发性及其在此上下文中的应用
2.  _The problem with using a map with sync.RWMutex_
2.  sync.RWMutex 和 map 一起使用的问题
3.  _Introducing sync.Map  
3.  介绍 sync.Map
    a. Where is sync.Map used?_
    a. 在哪些场景使用 sync.Map?
4.  _sync.Map: the implementation details
4. sync.Map 实现细节  
    a. How does load, store and delete work at a high level? 
    a. 加载、存储和删除如何在高层次上工作？ 
    b. The difference between storing expunged and just simply nil 
    b. 存储被删除和只是 nil 之间的区别 
    c. Store(key, value interface{})  
    c. Store(key, value interface) 
    d. Load(key interface{}) (value interface{}, ok bool) 
    d. Load(key interface{}) (value interface{}, ok bool)
    e. LoadOrStore(key, value interface{}) (actual interface{}, loaded bool)  
    e. LoadOrStore(key, value interface{}) (actual interface{}, loaded bool)
    f. LoadAndDelete(key interface{}) (value interface{}, loaded bool)  
    f. LoadAndDelete(key interface{}) (value interface{}, loaded bool)  
    g. Delete()(value interface{}, ok bool)  
    g. Delete()(value interface{}, ok bool)  
    h. Range(f func(key, value interface{}) bool)_
    h. Range(f func(key, value interface{}) bool)_
5.  _Discussion: sync.Map performance vs RWMutex guarded map’s performance. A quick guide on optimization_
5. sync.Map 和 RWMutex 保护的 map 之间的性能对比。快速优化指南
6.  _What does an extreme level of optimization look like?_
6. 极致的优化是什么样的？
7.  _Letter to the reader (actively_ **_looking for a job_** _:-) )_
7. 致读者的信

## Introduction
## 引言
_This article briefly introduces how sync.Map can be used, and also explains how sync.Map works._
这篇文章简单介绍了如何使用 sync.Map，同时解释 sync.Map 的工作原理。

Most operations rely on a hash map in their code. Therefore, they end up being a crucial bottleneck for performance if they are slow. Before the introduction of `sync.Map` the standard library only had to rely on the built-in `map` which was not thread safe. When it had to be called from multiple goroutines `sync.RWMutex` was relied on to synchronize access. But this did not really scale well with additional processor cores, and this was addressed by implementing `sync.Map` for go1.9. When run with 64 processor cores, the performance of `sync.RWMutex` significantly degrades.
在应用代码中，大多数操作都是依赖于 hash map。因此，如果 hash map 的读写很慢，它们最终会成为性能的关键瓶颈。在引入 `sync.Map` 之前，标准库只需要依赖于不是线程安全的内置 `map`。当多个 goroutines 调用它时，必须依赖 `sync.RWMutex` 来同步访问。但是这么做，并不能很好地扩展多核 CPU 的性能，所以在 go1.9 引入 `sync.Map` 来解决多核 CPU 操作 map 的性能问题。当程序运行在 64 核的机器上，`sync.RWMutex` 的性能下降会比较明显。
With `sync.RWMutex`, the value `readerCount` in `[sync.RWMutex](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L28)` was being incremented with each call to `RLock` , leading to cache contention. And this lead to a decrease in performance with additional processor cores. It is because with each additional core, the overhead of publishing updates to each core’s cache increased.
使用`sync.RWMutex`，`[sync.RWMutex](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L28)`中的值`readerCount`随着每次调用读锁而增加，这会导致缓存的竞争。最终导致处理器其他内核的性能下降。这是因为每增加一个核心，向每个核心的缓存发布更新的开销就会增加。
The documentation says: ([here](https://golang.org/pkg/sync/#Map))
[sync.Map 文档](https://golang.org/pkg/sync/#Map)
> The Map type is optimized for two common use cases:
>  snyc.Map 类型针对两个常见案例进行优化
> 
> (1) when the entry for a given key is only ever written once but read many times, as in caches that only grow, or
> (1) 当给定键的条目只写入一次但读取多次时，就像只会增长的缓存中一样
> 
> (2) when multiple goroutines read, write, and overwrite entries for disjoint sets of keys. In these two cases, use of a Map may significantly reduce lock contention compared to a Go map paired with a separate Mutex or RWMutex.
> (2) 当多个 goroutine 读取、写入和重写不相交的 keys 集合时。在这两种情况下，与使用单独的 Mutex 或 RWMutex 配对的 map 相比，使用 sync.Map 可以显着减少锁争用。

`map` with `sync.RWMutex` significantly reduces performance with the first case above, when the calls to `[atomic.AddInt32(&rw.readerCount, 1)](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L61)` and `[atomic.AddInt32(&rw.readerWait, -1)](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L81)` are too frequent. The overhead of writes cannot be avoided, but we must expect reads to be extremely fast especially if it is a cache that is supposed to help with processing data in a fast pipeline.
带有读写锁的 map 在第一个 case 中，在频繁地调用`[atomic.AddInt32(&rw.readerCount, 1)](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L61)` and `[atomic.AddInt32(&rw.readerWait, -1)](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L81)` 下性能显著下降。写入的开销无法避免，但我们必须期望读取速度非常快，特别是它作为一个缓存，应该有助于在快速管道中处理数据。

## A brief introduction to concurrency and how it applies in this context
## 简单介绍并发性及其在此上下文中的应用

Modern applications have to deal with historically large amounts of data within short periods of time. For this, they rely on multi-core processors with high processing speeds.
现代应用程序必须在短时间内处理大量历史数据。为此，他们重度依赖高速的多核处理器。

Real-time inputs handled by these systems usually have unpredictable arrival times. This is where OS level threads and goroutines truly shine. These rely on a combination of locks and semaphores to put them to “sleep” while waiting for an input. This frees the CPU resources utilized by the virtual thread until it receives an interrupt that awakens it. A thread or a goroutine awaiting an interrupt is similar to a callback waiting to be invoked on the arrival of an input — the interrupt signal originates when unlocking a mutex it was waiting on (or when a semaphore becomes zero).
这些系统处理的实时输入通常具有不可预测的到达时间。这正是操统级线程和 goroutines 真正闪耀的地方。这些依赖锁和信号量的组合来让它们在等待输入时 "休眠"。这会释放虚拟线程使用的 CPU 资源，直到它收到唤醒它的中断。等待中断的线程或 goroutine 类似于等待在输入到达时调用的回调——中断信号在解锁它正在等待的互斥锁时（或当信号量变为零时）产生。

Ideally, we would expect an application designed to run in a multi-threaded environment to scale with the increase in the number of processor cores. But not all applications scale well even if it is built to run multiple tasks on separate goroutines.

在理想情况下，我们希望应用程序处理数据的能力随着计算机核心数增加而增加。但并非所有应用程序都能很好地扩展，即使它一开始的设计是多个 goroutines 处理多个任务。

Certain blocks of code might need to synchronize with locks or atomic instructions, turning those parts into a forcefully synchronized execution blocks. An example for this could be a central cache which is accessible by each goroutine. These lead to lock contention preventing the application from improving in performance with additional cores. Or worse, these could lead to a degradation in performance. Atomic instructions also come with an overhead but it is much smaller than what is caused by locks.
某些代码块可能需要锁或 atomic 指令进行同步，将这些部分变成强制同步执行的代码块。比如每个 goroutine 都可以访问的中央缓存。这些会导致锁争用，从而阻止应用程序通过附加内核提高性能。甚至更糟的是，这些可能会导致性能下降。atomic 指令也会带来开销，但它比锁引起的开销小得多。

Hardware level atomic instructions used to access the memory do not always guarantee reading the latest value. This is because, each processor core maintains a local cache which could be outdated. To avoid this problem, atomic write operations are usually followed by instructions forcing each cache to update. And to top that, it must also prevent [memory reordering](https://en.cppreference.com/w/cpp/atomic/memory_order) which is in place (both at the hardware and software level) to improve performance.
硬件级原子指令对于内存的访问并不总是保证读取最新值。原因是，每个处理器内核都维护一个可能已过时的本地缓存。为了避免这个问题，原子写操作通常跟在指令之后强制每个缓存更新。最重要的是，为了提升（在硬件和软件级别）的性能，它还必须防止 [内存重新排序(就是我们常说的指令重排，cpu 的一种优化手段)](https://en.cppreference.com/w/cpp/atomic/memory_order)。

The `map` structure is so widely used that almost every practical application rely on a it in their code. And to use one in a concurrent application reads and writes to it must be synchronized with `_sync.RWMutex_` in the Go world. Doing so leads to the excessive use of `atomic.AddInt32(...)` which leads to frequent cache-contention, forcing cache update and memory ordering. This reduces performance.

`map` 结构被广泛使用，以至于几乎每个应用程序都在其代码中依赖它。并且要在并发应用程序中使用它，读取和写入它必须与 Go 中的 `_sync.RWMutex_` 同步。这样做会导致对 `atomic.AddInt32(...)` 的过度使用，从而导致频繁的缓存争用，强制刷新缓存和内存(指令)排序。这会降低性能(译者注: 这里说的缓存是 CPU 中的缓存)。

`sync.Map` uses a combination of both the atomic instructions and locks, but ensures the path to the read operations are as short as possible, with just one atomic load operation for each call to `Load(...)` in most cases. Atomic store instructions are usually the ones that force the caches (of each core) to be updated, whereas, atomic load might just have to enforce memory ordering along with ensuring its atomicity. And `atomic.AddInt32(...)` is worse, as its contention with other atomic updates to the same variable will cause it to busy wait until the update which relies on a compare-and-swap instruction succeeds.

`sync.Map` 使用 atomic 指令和锁的组合，但确保读取操作的路径尽可能短，大多数情况下，每次调用 `Load(...)` 只需一个原子加载操作案件。atomic 存储指令通常是强制更新（每个内核的）缓存的指令，而 atomic 加载可能只需要强制执行内存排序并确保其原子性。只有 `atomic.AddInt32(...)` 最糟糕，因为它与对同一变量的其他原子更新的争用将导致它忙于等待，直到依赖于比较和交换(译者注:这里便是CAS指令，在汇编中一个指令完成两个操作)指令的更新成功。


## The problem with using a map with sync.RWMutex
## sync.RWMutex 和 map 一起使用的问题

An example of using `sync.RWMutex` to synchronize access to the map: [https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/map\_reference\_test.go#L25](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/map_reference_test.go#L25)

使用 `sync.RWMutex` 来同步访问 map 的一个例子: [https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/map\_reference\_test.go#L25](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/map_reference_test.go#L25)

For convenience, the above code is mirrored here:
为方便起见，将上面的代码镜像到这里:
> 源代码 1
```go
// Taken from here: https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/map_reference_test.go#L25
// RWMutexMap is an implementation of mapInterface using a sync.RWMutex.
type RWMutexMap struct {
	mu    sync.RWMutex
	dirty map[interface{}]interface{}
}

func (m *RWMutexMap) Load(key interface{}) (value interface{}, ok bool) {
	m.mu.RLock()
	value, ok = m.dirty[key]
	m.mu.RUnlock()
	return
}

func (m *RWMutexMap) Store(key, value interface{}) {
	m.mu.Lock()
	if m.dirty == nil {
		m.dirty = make(map[interface{}]interface{})
	}
	m.dirty[key] = value
	m.mu.Unlock()
}

func (m *RWMutexMap) LoadOrStore(key, value interface{}) (actual interface{}, loaded bool) {
	m.mu.Lock()
	actual, loaded = m.dirty[key]
	if !loaded {
		actual = value
		if m.dirty == nil {
			m.dirty = make(map[interface{}]interface{})
		}
		m.dirty[key] = value
	}
	m.mu.Unlock()
	return actual, loaded
}

func (m *RWMutexMap) LoadAndDelete(key interface{}) (value interface{}, loaded bool) {
	m.mu.Lock()
	value, loaded = m.dirty[key]
	if !loaded {
		m.mu.Unlock()
		return nil, false
	}
	delete(m.dirty, key)
	m.mu.Unlock()
	return value, loaded
}

func (m *RWMutexMap) Delete(key interface{}) {
	m.mu.Lock()
	delete(m.dirty, key)
	m.mu.Unlock()
}

func (m *RWMutexMap) Range(f func(key, value interface{}) (shouldContinue bool)) {
	m.mu.RLock()
	keys := make([]interface{}, 0, len(m.dirty))
	for k := range m.dirty {
		keys = append(keys, k)
	}
	m.mu.RUnlock()

	for _, k := range keys {
		v, ok := m.Load(k)
		if !ok {
			continue
		}
		if !f(k, v) {
			break
		}
	}
}

```


When performance is critical we can address this either by reducing the frequency of acquiring the same locks in parallel (thus, reducing the frequency of lock contention) or by entirely replacing locks with atomic instructions like atomic-load, atomic-store and atomic-compare-and-swap. Atomic operations are also not a silver bullet, as state updates which rely on atomic-compare-and-swap run in an infinite loop until the update succeeds. The updates usually never happen when there is a contention, therefore leading them to busy wait when there are a lot of concurrent updates.

当性能很重要时，我们可以通过减少并行获取相同锁的频率（从而减少锁争用的频率）或完全用 atomic 指令（如 atomic-load、atomic-store 和 atomic-compare）代替锁来解决这个问题和交换。atomic 操作也不是灵丹妙药，因为依赖于 atomic 比较和交换的状态更新在无限循环中运行，直到更新成功。当存在争用时，更新通常不会发生，因此当有大量并发更新时，导致它们忙等待。

Most applications usually rely on a combination of both. Even those applications try to choose a more faster alternative, like reducing the number of calls to atomic-compare-and-swap instructions spinning in a loop.

大多数应用程序通常依赖于两者的组合。甚至有些应用程序也尝试选择更快的替代方案，例如减少对循环中旋转的 atomic 比较和交换指令的调用次数。

`[sync.RWMutex](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L28)` uses a combination of semaphores along with two additional variables `readerCount` and `readerWait` to keep track on the number of read accesses.
`[sync.RWMutex](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L28)` 使用信号量的组合以及两个附加变量 `readerCount` 和 `readerWait` 来记录正在读取和等待读取的数量。

To understand why we need to go for `sync.Map` when our environment has too many processor cores, instead of using the built-in `map` guarded by `sync.RWMutex`, we must dive into [how](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba) `[sync.RWMutex](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba)` [works internally.](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba)

要理解在多核环境中我们需要使用 `sync.Map`，而不是使用由 `sync.RWMutex` 保护的内置 `map`，那么，我们必须深入研究 [how](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba) `[sync.RWMutex](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba)` 的[内部工作。](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba)

`sync.Map` contains these following methods, which are self explanatory (taken from [here](https://golang.org/pkg/sync/#Map))
`sync.Map` 有下面这些一看就懂的方法（取自 [这里](https://golang.org/pkg/sync/#Map)）

> 源代码 2
```go
//Delete deletes the value for a key.
func (m *Map) Delete(key interface{})

//Load returns the value stored in the map for a key, or nil if no 
//value is present. The ok result indicates whether value was found 
//in the map.
func (m *Map) Load(key interface{}) (value interface{}, ok bool)

//LoadAndDelete deletes the value for a key, returning the previous 
//value if any. The loaded result reports whether the key was 
//present.
func (m *Map) LoadAndDelete(key interface{}) (value interface{}, loaded bool)

//LoadOrStore returns the existing value for the key if present. 
//Otherwise, it stores and returns the given value. The loaded 
//result is true if the value was loaded, false if stored.
func (m *Map) LoadOrStore(key, value interface{}) (actual interface{}, loaded bool)

//Range calls f sequentially for each key and value present in the 
//map. If f returns false, range stops the iteration.
//Range does not necessarily correspond to any consistent snapshot 
//of the Map's contents: no key will be visited more than once, but 
//if the value for any key is stored or deleted concurrently, Range 
//may reflect any mapping for that key from any point during the 
//Range call.
//Range may be O(N) with the number of elements in the map even if f 
//returns false after a constant number of calls.
func (m *Map) Range(f func(key, value interface{}) bool)

//Store sets the value for a key.
func (m *Map) Store(key, value interface{})
```

Before going ahead trying to understand how `sync.Map` works, it is important to understand [why do we absolutely need the methods](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa) `[LoadAndDelete(...)](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa)` [and](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa) `[LoadOrStore(...)](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa)`.

在继续尝试了解 `sync.Map` 的原理之前，还要了解 [为什么我们绝对需要这些方法](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa) `[LoadAndDelete (...)](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa)` [和](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa) `[LoadOrStore(...)](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa)`。

`sync.Map` maintains two `map` objects at any given time, one for the reads and one for the writes. The read map is partially immutable, whereas the write map is fully mutable.

`sync.Map` 总是维护两个 `map` 对象，一个用于读取，一个用于写入。读映射是部分不可变的，而写映射是完全可变的。

At any given time, the readable map is not expected to be fully updated, whereas, the writable map is assumed to be fully updated representing the store’s accurate state (while it was not set to `nil`). Whenever there is a key miss in the read-map, it is read from the write-map with a `sync.Mutex` lock held.

在任何时候，可读 map 都不会被完全更新，而可写的 map 被假定为完全更新，表示存储的准确状态（即使它没有设置为 `nil`）。每当从只读 map 未命中键时，它就会从带有 `sync.Mutex` 锁的写入映射中读取。

While deleting a key, the key could either be present only in the writable map or it could be present in the writable map and the readable map. If it was present only in writable map, it is completely removed with the built-in `delete` operation. But if it was present in both the writable map and the readable map, it is only set to `nil` (note, the update operation of setting the field to `nil` is reflected within the read-map and the write-map simultaneously, as they point to the same `entry` object; more on this later).

删除一个键的时候，键可以只存在于可写 map 中，也可以存在于可写 map 和可读 map 中。如果它仅存在于可写 map 中，则使用内置的 `delete` 操作将其完全删除。但是如果它同时存在于可写 map 和可读 map 中，则它只设置为`nil`（注意，将字段设置为 `nil` 的更新操作同时反映在读 map 和写 map 中，因为它们指向同一个 `entry` 对象；稍后会详细介绍）。

Every access to the writable map is guarded by `sync.Mutex` and they also have the overhead of atomic instructions. Therefore, it must have an overhead slightly greater than a built-in `map` guarded by `sync.RWMutex`.

对可写 map 的每次访问都由 `sync.Mutex` 保护，它们也有原子指令的开销。因此，它的开销必须略大于由 `sync.RWMutex` 保护的内置 `map`。

So one of the objectives of this implementation should be to reduce the frequency of read-misses. This is done by promoting the writable map as the next readable map (while setting the pointer to the writable map as `nil`) when the number of read misses are larger than the length of the writable map (this length is computed using `len`). The outdated readable map is then discarded.

因此，此实现的目标之一应该是减少读取未命中的频率。这是通过将可写 map 提升为下一个可读的 map 来完成的（同时将指向可写 map 的指针设置为 `nil`），当读取未命中数大于可写 map 的长度时（此长度使用 `len `）。然后丢弃过时的可读 map。

Upon the first attempt to add a key to the writable map, a new map object is created by copying the contents of the new readable map to the writable map. Immediately after the promotion, the readable map will represent the store’s most accurate state. But after being promoted it becomes “immutable” and there will not be any new keys added to it. Therefore, adding additional keys to `sync.Map` will make the readable map outdated.

在第一次尝试向可写的 map 添加键时，通过将新可读 map 的内容复制到可写的 map 来创建新 map 对象。数据搬移结束之后，可读的 map 将存储最准确的状态。但是被搬移之后就变成了 "不可变"，不会再有新的 key 被添加进去。因此，向 `sync.Map` 添加额外的键会使可读的 map 失效。

There are two different ways in which an update happens. If the key being added (with the `sync.Map`’s `Store(...)` or `LoadOrStore(…)` operation) already exists in the readable map, the value associated with the key in the readable map is updated atomically (note: the changes done to the value field this way will be immediately reflected on the writable map as well. How this happens will be explained later in this article). If the key only exists in the writable map or if the key does not exist at all, the update is made only in the writable region with a `sync.Mutex` lock held.
更新有两种不同的方式。如果添加的键（使用`sync.Map` 的`Store(...)` 或`LoadOrStore(...)` 操作）已经存在于可读的 map 中，则可读的 map 中与键关联的值是以原子方式更新（注意：以这种方式对 value 字段所做的更改也将立即反映在可写映射上。本文稍后将解释这是如何做到的）。如果键只存在于可写的 map 中，或者键根本不存在，则更新仅在可写区域中进行，并需要使用 “sync.Mutex”锁。

## Where is sync.Map used?
## sync.Map 的使用场景

`sync.Map` was originally created to reduce the overhead incurred by the Go’s standard library packages that have been using a `map` guarded by `sync.RWMutex`. So the Go authors discovered that having a store like `sync.Map` does not increase the memory overhead too much (an alternate memory intensive solution is to have a separate copy of the map for each goroutine used, but have them updated synchronously) while also improving the performance in a multi-core environment. Therefore, the original purpose of `sync.Map` was to address the [problems within the standard packages](https://github.com/golang/go/issues/40999#issuecomment-679449778), but it was still made public in hope that people find it useful.

`sync.Map` 最初是为了减少 Go 的标准库包所产生的开销，这些包一直使用由 `sync.RWMutex` 保护的 `map`。所以 Go 的作者们发现像 `sync.Map` 这样的存储不会增加太多的内存开销（另一种内存密集型解决方案是为每个使用的 goroutine 提供一个单独的映射副本，但让它们同步更新）而还提高程序在多核环境中的性能。因此，`sync.Map` 的初衷是为了解决[标准包中的问题](https://github.com/golang/go/issues/40999#issuecomment-679449778)，但还是公开了，希望大家觉得有用。

The documentation does not really go into the details of where exactly will `sync.Map` be of most use. [Benchmarking](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c) `[sync.Map](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c)` has revealed there is a gain in efficiency over the use of `map` guarded by `sync.RWMutex` only when it is run on a system with more than 4 cores. And the most ideal use case for `sync.Map` is having it used as cache that witnesses a frequent access to disjoint keys; or having it extensively read from the same set of keys.

但是，文档并没有真正详细说明 `sync.Map` 究竟在哪里最有用。 通过[基准测试](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c) 和 `[sync.Map](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c)` 表明，仅当它在具有超过 4 个核的系统上运行时，使用 `sync.Map` 比使用由 `sync.RWMutex` 保护的 `map` 更加高率。 `sync.Map` 最理想的用例是将其用作缓存，特别是频繁访问不相交的键；或从同一组键中广泛读取它。

The keys that are newly added are likely to stay in the writable map, while the keys that were accessed most frequently are likely to stay in the readable map. `sync.Map` will perform the least when a finite set of keys are being added, read from and deleted where each operation happens with the same frequency.This happens when you do not let the keys in the write-map to be promoted by frequently adding and deleting them.In this situation, we might be better off using `map` with `sync.RWMutex` or `sync.Mutex` (The exact choice for a concurrent hash-map is usually decided through benchmarking)

新添加的键可能会留在可写的 map 中，而最常访问的键可能会留在可读的 map 中。当添加、读取和删除一组有限的键时，`sync.Map` 将执行最少的操作，其中每个操作都以相同的频率发生。当你不让写 map 中的键被提升时，就会发生这种情况经常添加和删除它们。在这种情况下，我们最好将 `map` 与 `sync.RWMutex` 或 `sync.Mutex` 一起使用（并发散列映射的确切选择通常通过基准测试决定）。

Whenever a key is deleted in `sync.Map` it only has its associated value field marked as `[nil](https://github.com/golang/go/blob/21a04e33353316635b5f3351e807916f3bb1e844/src/sync/map.go#L297)` but the key isn’t really removed until the first write after the writable-map was promoted as the readable-map. This leads to a memory overhead. But this overhead is only temporary, as with the next promotion cycle, the overhead comes down.

每当一个键在 `sync.Map` 中被删除，它只将其关联的值字段标记为 `[nil](https://github.com/golang/go/blob/21a04e33353316635b5f3351e807916f3bb1e844/src/sync/map.go#L297)`，但直到第一次写入后，key 才真正删除 writable-map 作为可读 map。这会导致内存开销。但是这种开销只是暂时的，随着下一个促销周期，开销会下降。

## sync.Map: the implementation details 
## sync.Map 实现细节
`[sync.map](https://github.com/golang/go/blob/21a04e33353316635b5f3351e807916f3bb1e844/src/sync/map.go#L12)`[’s structure is given here for convenience:](https://github.com/golang/go/blob/21a04e33353316635b5f3351e807916f3bb1e844/src/sync/map.go#L12)
方便起见，这里给出 `[sync.map](https://github.com/golang/go/blob/21a04e33353316635b5f3351e807916f3bb1e844/src/sync/map.go#L12)` 的结构。

> 源代码 3
```go
// Map is like a Go map[interface{}]interface{} but is safe for concurrent use
// by multiple goroutines without additional locking or coordination.
// Loads, stores, and deletes run in amortized constant time.
//
// The Map type is specialized. Most code should use a plain Go map instead,
// with separate locking or coordination, for better type safety and to make it
// easier to maintain other invariants along with the map content.
//
// The Map type is optimized for two common use cases: (1) when the entry for a given
// key is only ever written once but read many times, as in caches that only grow,
// or (2) when multiple goroutines read, write, and overwrite entries for disjoint
// sets of keys. In these two cases, use of a Map may significantly reduce lock
// contention compared to a Go map paired with a separate Mutex or RWMutex.
//
// The zero Map is empty and ready for use. A Map must not be copied after first use.
type Map struct {
	mu Mutex

	// read contains the portion of the map's contents that are safe for
	// concurrent access (with or without mu held).
	//
	// The read field itself is always safe to load, but must only be stored with
	// mu held.
	//
	// Entries stored in read may be updated concurrently without mu, but updating
	// a previously-expunged entry requires that the entry be copied to the dirty
	// map and unexpunged with mu held.
	read atomic.Value // readOnly

	// dirty contains the portion of the map's contents that require mu to be
	// held. To ensure that the dirty map can be promoted to the read map quickly,
	// it also includes all of the non-expunged entries in the read map.
	//
	// Expunged entries are not stored in the dirty map. An expunged entry in the
	// clean map must be unexpunged and added to the dirty map before a new value
	// can be stored to it.
	//
	// If the dirty map is nil, the next write to the map will initialize it by
	// making a shallow copy of the clean map, omitting stale entries.
	dirty map[interface{}]*entry

	// misses counts the number of loads since the read map was last updated that
	// needed to lock mu to determine whether the key was present.
	//
	// Once enough misses have occurred to cover the cost of copying the dirty
	// map, the dirty map will be promoted to the read map (in the unamended
	// state) and the next store to the map will make a new dirty copy.
	misses int
}
```

As we can see, `sync.Map` has one `dirty` map store and one `atomic.Value` field that is used for storing the “clean” `read` map. All accesses to the `dirty` map are always guarded by `mu`. Before we look at how each individual methods work we must understand the working of `sync.Map` and its design ideas from a higher level.

正如我们所见，`sync.Map` 有一个 `dirty` map 存储和一个用于存储 “clean” 的 `read` map 的 `atomic.Value` 字段。所有对 `dirty` 的访问总是由 `mu` 保护。在我们查看每个独立的方法如何工作之前，我们必须对 `sync.Map` 的工作原理和设计思想有一个宏观的了解。

The `[entry](https://github.com/golang/go/blob/c1cc9f9c3d5ed789a080ef9f8dd9c11eca7e2026/src/sync/map.go#L73)` structure is vital for the function of `sync.Map` .
The `[键值对构成的 entry ](https://github.com/golang/go/blob/c1cc9f9c3d5ed789a080ef9f8dd9c11eca7e2026/src/sync/map.go#L73)` 结构对于`sync.Map`的功能至关重要

> 源代码 4
```go

type entry struct {
	// p points to the interface{} value stored for the entry.
	//
	// If p == nil, the entry has been deleted, and either m.dirty == nil or
	// m.dirty[key] is e.
	//
	// If p == expunged, the entry has been deleted, m.dirty != nil, and the entry
	// is missing from m.dirty.
	//
	// Otherwise, the entry is valid and recorded in m.read.m[key] and, if m.dirty
	// != nil, in m.dirty[key].
	//
	// An entry can be deleted by atomic replacement with nil: when m.dirty is
	// next created, it will atomically replace nil with expunged and leave
	// m.dirty[key] unset.
	//
	// An entry's associated value can be updated by atomic replacement, provided
	// p != expunged. If p == expunged, an entry's associated value can be updated
	// only after first setting m.dirty[key] = e so that lookups using the dirty
	// map find the entry.
	p unsafe.Pointer // *interface{}
}

```

The `entry` structure acts as a “container” or a “box” that holds the value being stored associated with the key. Instead of directly storing a value with `m[key] = value`, you have the `value` encapsulated within a convenient container of type `entry`. The address of `entry` is then stored into the `map` object associated to the key.

`entry` 结构相当于 “容器”或“盒子”，保存和键相关联的值。不是直接用 `m[key] = value` 存储值，而是将 `value` 封装在一个方便的 `entry` 类型容器中。然后将 `entry` 的地址存储到与键关联的 `map` 对象中。

At any given time, `entry` is assumed to satisfy one of these three properties:
在任何的时间节点中，都假定 `entry` 满足以下三个属性之一：

1.  It holds a valid value: `p != expunged && p != nil` . `expunged` (which means removed permanently) is defined as `var expunged = unsafe.Pointer(new(interface{}))`, which is an arbitrary global value set only once. It does not take on any value. It is there just to distinguish the “expunged” value from every other `nil` and non-`nil` value in arbitrary `entry` fields.
1. 它包含一个有效值：`p != expunged && p != nil`。 `expunged`（意味着永久删除）被定义为 `var expunged = unsafe.Pointer(new(interface{}))`，这是一个只设置一次的任意全局值。它没有任何价值。它只是为了将 “删除” 值与任意 `entry` 字段中的所有其他 `nil` 和非 `nil` 值区分开来。

2.  It holds `nil`.

2. 它包含 `nil`。

3.  It holds `expunged` (we’ll soon go into the details of how `nil` state differs from the `expunged` state).

3. 它包含 `expunged`（我们很快就会详细介绍 `nil` 状态与 `expunged` 状态有何不同）。

It is extremely convenient to wrap up the pointer under a structure like `entry`. If you are changing the state of an `entry`, you can expect it to be instantly updated at every other location that has the pointer to the `entry` object.

将指针包裹在一个像 `entry` 这样的结构下是非常方便的。如果您正在更改 `entry` 的状态，您可以期望它在每个其他具有指向 `entry` 对象的指针的位置立即更新。

So, if you share the address to `entry` between the readable map and the writable map, updating the readable map’s `entry` will reflect the changes on the writable map as well and visa-verse (note that, in both source 3 and source 5 the map is defined as `map[inerface{}]*entry` , where the key is an `interface{}` and the entry is stored as a pointer).

所以，如果您在可读的 map 和可写的 map 之间共享 `entry` 的地址，更新可读 map 的 `entry`也将反映可写的 map 上的更改以及反之亦然（请注意，在源 3 和可写映射中）源 5 映射被定义为`map[inerface{}]entry`，其中键是一个`interface{}`，并且该 entry 存储为一个指针）。

Source 5: readOnly structure

> 源代码 5：只读结构体
```go
// readOnly is an immutable struct stored atomically in the Map.read field.
type readOnly struct {
	m       map[interface{}]*entry
	amended bool // true if the dirty map contains some key not in m.
}
```

The `read` field of `sync.Map` structure is an `atomic.Value` field, which holds a reference to `readOnly`(source 5). This structure contains another field `amended` which is true when the `sync.Map` object was extended by adding a new key and a promotion did not happen yet since the new key was added. In this case, the key goes into the writable map without there being a record of it in the readable map. The `amended` field being true signifies this specific state where the `dirty` map contains a record `read` doesn’t.

`sync.Map` 结构的 `read` 字段是一个 `atomic.Value` 字段，它保存对 `readOnly`（源代码 5）的引用。此结构包含另一个字段 `amended`，当 `sync.Map` 对象通过添加新键进行扩展并且自添加新键后尚未发生升级时，该字段为真。在这种情况下，键进入可写的 map，而可读 map 中没有它的记录。 `amended` 字段为 true 时，表示这种特定状态，其中 `dirty` 映射包含的记录，但是 `read` 不包含记录。

## How does load, store and delete work at a high level?
## 加载、存储和删除如何在高层次上工作？

The read part of these operations are usually inexpensive (relatively). This is because, the pointer to a `readOnly` object is retrieved from the `atomic.Value` field and the value associated with the key is quickly searched for. If the value exists, it gets returned.
这些操作的读取部分通常是廉价的（相对）。原因是从 `atomic.Value` 字段中检索到 `readOnly` 对象的指针，并快速搜索与键关联的值。如果该值存在，则返回。

If it doesn’t exist, then it is likely to have been added more recently. In which case the `dirty` field needs to be checked (with `mu` held). If the key exists in the `dirty` field, it is retrieved as the result.

如果它不存在，那么它很可能是最近添加的。在这种情况下，需要检查 `dirty` 字段（保留 `mu`）。如果键存在于 `dirty` 字段中，则将其作为结果进行检索。

The read operations have a slow path in this implementation. With each miss in the `readOnly` object, the value of the field `misses` is atomically incremented. When the `misses` count is larger than the size of `dirty`, it gets promoted (directly moving its pointer) to the `read` field, by creating a new `readOnly` object to contain it. The previous value of the `read` field is discarded when this happens.

在此实现中(译者注: dirty map)，读操作会比较慢。随着 `readOnly` 对象中的每次未命中，字段 `misses` 的值自动递增。当 `misses` 计数大于 `dirty` 的大小时，通过创建一个新的 `readOnly` 对象来包含它，它会被提升（直接移动它的指针）到 `read` 字段。发生这种情况时，会丢弃 `read` 字段的先前值。

All operations involving the `dirty` map are carried out within a region guarded by the mutex `mu` .

所有涉及 `dirty` map 的操作都在互斥锁 `mu` 保护的区域内执行。

When record is being stored into `sync.Map`, it is handled in one of these three ways:

当记录被存储到 `sync.Map` 中时，它会通过以下三种方式之一进行处理:

1.  Modifying the instance of `entry` returned by `(read.Load().(readOnly))[key]` if it was successfully retrieved. The modification is done by adding the value to the `entry` field.
1、修改 `(read.Load().(readOnly))[key]` 返回的 `entry` 实例，如果检索成功。修改是通过将值添加到 `entry` 字段来完成的。

2.  Modifying the instance of `entry` returned by `dirty[key]`, if it was retrieved successfully. The modification is done by replacing the value in the `entry` object (stored inside the `read` object which is of type `atomic.Value`). This is done if step one had failed.

2.修改 `dirty[key]` 返回的 `entry` 实例，如果检索成功。修改是通过替换 `entry` 对象（存储在 `atomic.Value` 类型的 `read` 对象内）中的值来完成的。如果第一步失败，则执行此操作。

3.  If `dirty` is `nil` (which will be the case when `read.amended` is false), create a new `map` and copy everything in the read only map to it. The record is then just added to `dirty` (notice that with the fields being copied, the address to the `entry` objects are the ones being copied. Therefore, each key present in the read map and the write map point to the exact same `entry` object.)

3.如果 `dirty` 为 `nil`（当`read.amended`为false时就是这种情况），创建一个新的 `map` 并将只读 map 中的所有内容复制到它。然后将记录添加到 `dirty`（注意，随着字段被复制，`entry` 对象的地址就是被复制的对象。因此，读映射和写映射中存在的每个键都指向准确的相同的 `条目` 对象。）

In case of delete, if the key was present in the `readOnly` object in `read`, its `entry` instance is atomically updated to be `nil`. This operation does not need `mu` to be acquired. But `mu` will need to be acquired when the key is searched for in the `dirty` field. If the key is not present in `read`, it is looked for in `dirty` while being guarded by `mu`. If it is found only in `dirty`, the `entry` object is directly removed with the built-in `delete` function.

在删除的情况下，如果键存在于 `read` 中的 `readOnly` 对象中，它的 `entry` 实例会自动更新为 `nil`。这个操作不需要获取 `mu`。但是在 `dirty` 字段中搜索键时需要获取 `mu`。如果键不存在于 `read` 中，它会在 `dirty` 中查找，同时由 `mu` 保护。如果只在 `dirty` 中找到，则直接使用内置的 `delete` 函数删除 `entry` 对象。

Therefore the read, write and delete operations will be fully atomic when the key is found in the `readOnly` instance held by the `read` field. Whereas, the other cases that needs to go though `dirty` will be guarded by `mu`.

因此，当在 read 字段持有的 readOnly 实例中找到键时，读取、写入和删除操作将是完全原子的。而其他需要通过 `dirty` 处理的情况将由 `mu` 保护。

And any modification done to the `entry` field will be reflected at both the `readOnly` object in `read` and the `dirty` map. Because, whenever a new `map[interface{}]*entry` object is created from copying the `readOnly` instance, only the address of the `entry` objects are copied.

对 `entry` 字段所做的任何修改都将反映在 `read` 和 `dirty` map 中的 `readOnly` 对象上。因为，每当通过复制 `readOnly` 实例创建新的 `map[interface{}]entry` 对象时，只会复制 `entry` 对象的地址。

## The difference between storing `expunged` and just simply `nil`
## 存储 `expunged` 和简单的 `nil` 之间的区别

The following properties are always said to hold:
始终认为以下属性成立：

1.  `entry` holds a pointer in it. At any given time, its pointer can hold `expunged`, `nil` or a pointer to the interface holding a valid value provided through the `Store(…)` or `LoadOrStore(…)` methods by the user.

1. `entry` 里面有一个指针。在任何时间，它的指针都可以保存 `expunged`、`nil` 或指向接口的指针，该指针保存了用户通过`Store(...)` 或 `LoadOrStore(...)` 方法提供的有效值。

2.  If `entry` holds `nil`, it signifies that the value associated with the key was deleted by calling `Delete(…)` or `LoadAndDelete(…)` while it was present in the `readOnly` object and the `dirty` map.

2. 如果 `entry` 保存的是 `nil`，则表示与键关联的值已通过调用 `Delete(...)` 或 `LoadAndDelete(...)` 进行删除，而它存在于 `readOnly` 对象中，并且 `脏` map。

3.  If `entry` holds `expunged`, it signifies that a non-`nil` `dirty` map exists which does not have the same key that associates the `entry` field.

3. 如果 `entry` 包含 `expunged`，则表示存在非 `nil` `dirty` 映射，该映射不具有关联 `entry` 字段的相同键。

When `misses > len(dirty)` (`misses` is a field in `sync.Map` structure), the `dirty` map is copied into the `read` field, which is of type `atomic.Value`. The code for doing that is: `m.read.Store(readOnly{m: m.dirty})` where, the `Store` here is an atomic store operation.

当`misses > len(dirty)`（`misses` 是`sync.Map` 结构中的一个字段）时，`dirty` map 被复制到 `atomic.Value` 类型的 `read` 字段中。这样做的代码是： `m.read.Store(readOnly{m: m.dirty})` 其中，这里的 `Store` 是一个原子存储操作。


The `readOnly` object has two fields in it. One for the map, and the other for the `amended` variable which says if a new key was added to the `sync.Map` object after a promotion. The first attempt to insert a key following a promotion causes the map inside the `readOnly` object to be copied to the `dirty` map key by key. Every key that associates to an `entry` object storing `nil` is not copied into the `dirty` map and has its `entry` object updated to contain `expunged`.

`readOnly` 对象中有两个字段。一个用于 map，另一个用于 `amended` 变量，该变量表示升级后是否将新键添加到 `sync.Map` 对象。第一次尝试在升级后插入键会导致 `readOnly` 对象内的 map 被逐键复制到 `dirty` map 键。与存储 `nil` 的 `entry` 对象相关联的每个键都不会被复制到 `dirty` 映射中，而是将其 `entry` 对象更新为包含`expunged`。

Therefore, `expunged` keys are only present in the “clean” map without having them copied into the new `dirty` map. This is done with an assumption that the key that was deleted once is not likely to be added again.

因此，`expunged` 的键仅存在于 `干净` 映射中，而不会将它们复制到新的 `dirty`map。这是在假设不会再次添加被删除一次的键的情况下完成的。


There are two separate unexported methods,`missLocked()`and `dirtyLocked()` defined for `sync.Map`. These are respectively responsible for,

有两个独立的未导出方法，为 `sync.Map` 定义的 `missLocked()` 和 `dirtyLocked()`。他们的责任如下:

1.  promoting the `dirty` map (which also sets the `dirty` field in `sync.Map` to `nil`)
1. 传播 `dirty` 映射（同时将`sync.Map`中的`dirty`字段设置为`nil`）
2.  copying the key-value pairs in the `readOnly` object (which has its `amended` field set to `false`) to the newly created `dirty` map object (by ignoring the keys that are associated with `entry` object set to `nil` and making them `expunged`; as they are not copied into the `dirty` map).
2. 将 `readOnly` 对象（其 `amended` 字段设置为 `false`）中的键值对复制到新创建的 `dirty` map 对象（通过忽略与 `entry` 对象关联的键）设置为 `nil` 并使它们`expunged`；因为它们没有被复制到`dirty` map 中）。


`missLocked()` is called each time there is a key miss while reading the `readOnly` object. The call could be triggered by every exported method defined in `sync.Map` other than `Range(…)`, as they all try retrieving the stored record first and accept a `key` as an argument. `missLocked()` only promotes the `dirty` map when the size of it is smaller than the number of misses.

`missLocked()` 每次在读取 `readOnly` 对象时出现键未命中时都会被调用。除了 `Range(…)` 之外，`sync.Map` 中定义的每个导出方法都可以触发调用，因为它们都首先尝试检索存储的记录并接受 `key` 作为参数。 `missLocked()` 仅在其大小小于未命中数时才会提升 `dirty` 映射。

## `Store(key, value interface{})`:

## `Store(key, value interface{})` 接口:

> 源代码 6: Store 方法
```go
// Store sets the value for a key.
func (m *Map) Store(key, value interface{}) {
	
	/// PART 1
	read, _ := m.read.Load().(readOnly)
	if e, ok := read.m[key]; ok && e.tryStore(&value) {
		return
	}
	///------------------------------------------------------------
	
	
	/// PART 2
	m.mu.Lock()
	read, _ = m.read.Load().(readOnly)
	if e, ok := read.m[key]; ok {
		if e.unexpungeLocked() {
			// The entry was previously expunged, which implies that there is a
			// non-nil dirty map and this entry is not in it.
			m.dirty[key] = e
		}
		e.storeLocked(&value)
	///--------------------------------------------------------------
	
	/// PART 3
	} else if e, ok := m.dirty[key]; ok {
		e.storeLocked(&value)
	/// -------------------------------------------------------------
		
		
	/// PART 4
	} else {
		if !read.amended {
			// We're adding the first new key to the dirty map.
			// Make sure it is allocated and mark the read-only map as incomplete.
			m.dirtyLocked()
			m.read.Store(readOnly{m: read.m, amended: true})
		}
		m.dirty[key] = newEntry(value)
	}
	m.mu.Unlock()
	/// --------------------------------------------------------------
}
```

Let’s break the above code into four parts (the region containing each part is marked above). The first part attempts to retrieve the value from `read`, which is a `sync.Value` field containing the `readOnly` object. If the read was successful, it attempts to store the value into the `entry` object atomically. Source 7 shows how it is done.

让我们将上面的代码分成四部分（上面标记了包含每个部分的区域）。第一部分尝试从 `read` 中检索值，这是一个包含 `readOnly` 对象的 `sync.Value` 字段。如果读取成功，它会尝试将值以原子方式存储到 `entry` 对象中。源代码 7 显示了它是如何完成的。

The atomic update in the `tryStore(…)` operation contains an infinite loop that terminates when the value was previously `expunged`. This is because, an `expunged` value signifies that there isn’t a copy of the same key field in the `dirty` map, while there is one in the `readOnly` object. Therefore, updating the pointer in this case will not reflect on the `dirty` map, which is always supposed to contain the fully updated and accurate state of `sync.Map`. Except for the case where it was just recently promoted. In which case, the `dirty` field will temporary hold `nil` until the first attempted write to it since it was set to `nil`.

`tryStore(…)` 操作中的 atomic 更新包含一个无限循环，该循环在值之前被 `expunged` 时终止。这是因为，`expunged` 值表示在 `dirty` map 中没有相同键字段的副本，而在 `只读` 对象中有一个。因此，在这种情况下更新指针不会反映在 `dirty` map 上，它总是应该包含 `sync.Map` 的完全更新和准确状态。除了最近刚刚推广的情况。在这种情况下，`dirty` 字段将暂时保留 `nil`，直到第一次尝试写入它，因为它被设置为 `nil`。

The infinite loop in source 7 is there to cause the function to stay in a “busy wait” state until the update succeeds. Atomic compare and swap operation accepts three arguments. The pointer to be modified, the likely old value contained in the pointer and the new value. The new value is stored in the pointer if the old value was the same as the original value held in the pointer.

源代码 7 中的无限循环导致函数保持 “忙等待” 状态，直到更新成功。原子比较和交换操作接受三个参数。要修改的指针、指针中可能包含的旧值和新值。如果旧值与指针中保存的原始值相同，则新值存储在指针中。

In source 7, the pointer is first atomically loaded from the `entry` object and it is checked if it was `expunged`. If it was, then `tryStore` fails because, an `expunged` entry signifies that the `entry` object is not present in the `dirty` map associated with its key. Therefore, storing the value into the `entry` object retrieved from the `read` map will no longer be useful (as the modifications will not reflect on the `dirty` map).

在源代码 7 中，指针首先从 `entry` 对象中自动加载，并检查它是否被 `expunged`。如果是，那么`tryStore` 会失败，因为`expunged` 表示`entry` 对象不存在于与其键关联的 `dirty` map 中。因此，将值存储到从 `read` 映射中检索到的 `entry` 对象将不再有用（因为修改不会反映在 `dirty` map 上）。

The atomic-compare-and-swap instruction in line 11 of source 7 is responsible for adding the new value, if `e.p` (which is the pointer stored inside the `entry` object) was same as the value of `p` previously read at line 8 of source 7. If a method running in a different goroutine had atomically modified the underlying value of `p` before the execution of line 11, the compare-and-swap-pointer operation fails causing the loop to continue. If `p` was modified to hold `expunged`, then the loop breaks because of the conditional branch at line 8.

如果 `e.p`（存储在 `entry` 对象中的指针）与之前的 `p` 值相同，则源代码 7 第 11 行中的 atomic-compare-and-swap 指令负责添加新值在源代码 7 的第 8 行读取。如果在不同的 goroutine 中运行的方法在第 11 行执行之前原子地修改了 `p` 的底层值，比较和交换指针操作失败导致循环继续。如果 `p` 被修改为包含 `expunged`，那么循环会因为第 8 行的条件分支而中断。

This infinite loop will go on until `e.p` was not modified by a different goroutine while statements from line 7 to 11 were being executed. This is why contention will be more heavy on the CPU when we use atomic instructions instead of locks that put goroutines to sleep until they are needed to run again. Atomic instructions cause a “busy wait” to occur until there are no contentions.

这个无限循环将一直持续到在第 7 行到第 11 行的语句被执行时 `e.p` 没有被不同的 goroutine 修改。这就是为什么当我们使用 atomic 指令而不是让 goroutine 休眠直到需要再次运行的锁时，CPU 上的争用会更加严重。原子指令导致 “忙等待” 发生，直到没有争用。


> 源代码 7：tryStore 方法
```go
// tryStore stores a value if the entry has not been expunged.
//
// If the entry is expunged, tryStore returns false and leaves the entry
// unchanged.
func (e *entry) tryStore(i *interface{}) bool {
	for {
		p := atomic.LoadPointer(&e.p)
		if p == expunged {
			return false
		}
		if atomic.CompareAndSwapPointer(&e.p, p, unsafe.Pointer(i)) {
			return true
		}
	}
}
```

The remaining parts 2, 3 and 4 (in Source 6) all run within a region guarded by the `mu` lock. Part 1 returns when the key was present in the `readOnly` object and the `tryStore` operation (explained above) was successful.
其余部分 2、3 和 4（在 Source 6 中）都在一个由 `mu` 锁保护的区域内运行。第 1 部分在 key 存在于 `readOnly` 对象中并且 `tryStore` 操作（如上所述）成功时返回。

But Part 1 failing signifies that either the key was not present in the `readOnly` object or it was expunged. Proceeding to Part 2, the read value is reloaded within the locked region again.
但是第 1 部分失败意味着 key 不存在于 `readOnly` 对象中，或者它已被删除。继续第 2 部分，读取值再次重新加载到锁定区域内。

This is done because the pointer to the `readOnly` object stored within `atomic.Value` could have been replaced following a call to `missLocked()` executed from a different goroutine, which will also be executed after acquiring `mu`(_Note, every function with the postfix “Locked” is supposed to be executed within the locked region guarded by_ `_mu_`). But because part 1 does not acquire `mu` the value retrieved at line 6 in source 6 can become outdated.
可能会在调用从不同 goroutine 执行的 `missLocked()` 之后被替换，该 goroutine 也将在获取 `mu` 后执行（_Note ，每个带有后缀 `Locked` 的函数都应该在由 `mu` 保护的锁定区域内执行）。但是因为第 1 部分没有获取 `mu`，在源代码 6 的第 6 行检索到的值可能会过时。

In Part 2 the `entry` pointer is retrieved again. Now, a call to `e.unexpungeLocked()` checks if the value stored in the entry was `expunged` or not:

在第 2 部分中，再次检索了 `entry` 指针。现在，调用`e.unexpungeLocked()` 检查存储在条目中的值是否被 `expunged`：

1.  If it was `nil` or anything else, it indicates that the same key must also be present in the `dirty` map.
1. 如果它是 `nil` 或其他任何东西，则表示在 `dirty` 映射中也必须存在相同的键。
2.  But if it is `expunged`, it signifies that the key is not present in the `dirty` map and it must be added to it as well. Therefore, the pointer to the `entry` object retrieved by `read.m[key]` is stored into `dirty` being associated with its appropriate key. Because the same pointer is used, any changes to the underlying `entry` object reflects in both the “clean” map and the “dirty” map.
2. 但如果它是 `expunged`，则表示该键不存在于 `dirty` 映射中，并且必须将其添加到其中。因此，由 `read.m[key]` 检索到的 `entry` 对象的指针被存储到与其适当的键相关联的`dirty` 中。因为使用了相同的指针，对底层 `entry` 对象的任何更改都会反映在 “干净” map 和 “dirty” map中。

A call to `unexpungeLocked()` executes the statement `return atomic.CompareAndSwapPointer(&e.p, expunged, nil)` (which is the only statement in its definition). This ensures that `e.p` is only updated when it is `expunged`. You don’t have to busy wait here to allow the update to happen. This is because the “old pointer” argument of `CompareAndSwapPointer(…)` is a constant (`expunged`) and it can never change.
对 `unexpungeLocked()` 的调用会执行语句 `return atomic.CompareAndSwapPointer(&e.p, expunged, nil)` （这是其定义中唯一的语句）。这确保了 `e.p` 仅在它被 `expunged` 时更新。您不必在这里忙着等待以允许更新发生。这是因为 `CompareAndSwapPointer(...)` 的 “旧指针” 参数是一个常量（`expunged`）并且它永远不会改变。

Both `tryStore()` and `unexpungeLocked()` can update `e.p` though they aren’t mutually guarded by the same mutex. Thus they could potentially attempt to update `e.p` simultaneously from different goroutines. But this does not become a race condition as `unexpungeLocked()` is supposed to modify the `entry` object only when its pointer (the `p` field of the entry object) was set to `expunged`.
`tryStore()` 和 `unexpungeLocked()` 都可以更新 `e.p`，尽管它们不是由同一个互斥锁相互保护的。因此，他们可能会尝试从不同的 goroutines 同时更新 `e.p`。但这不会成为竞争条件，因为 `unexpungeLocked()` 应该仅在其指针（入口 entry 的 p 字段）设置为 `expunged` 时修改入口 entry。


`unexpungeLocked()` running on a different goroutine could execute its `CompareAndSwapPointer(…)` statement anywhere between lines 7 and 11 in Source 7. If it was executed between these lines, the value of the underlying pointer will have been changed before the compare-and-swap operation at line 11 which will cause the loop to fail and repeat again. Therefore, a successful execution of the region between the lines 7 and 11 in Source 7 cannot occur if,
在不同的 goroutine 上运行的 `unexpungeLocked()` 可以在 Source 7 的第 7 行和第 11 行之间的任何地方执行它的 `CompareAndSwapPointer(…)` 语句。如果它在这些行之间执行，底层指针的值将在第 11 行的比较和交换操作将导致循环失败并再次重复。因此，如果出现以下情况，则无法成功执行 Source 7 中第 7 行和第 11 行之间的区域：

1.  a different goroutine executes the same region trying to modify the same underlying pointer or,
1. 不同的 goroutine 执行相同的区域，试图修改相同的底层指针，或者，
2.  if `unexpungeLocked()` was concurrently executed within the same time frame.
2. 如果`unexpungeLocked()` 在同一时间范围内同时执行。

In Part 2, the value is finally stored into the `entry` object by a call to `storeLocked(...)`. Now moving on to Part 3. The condition in Part 2 fails on two possibilities (note, we have already ruled out the possibility that the key could be present in the `readOnly` object):
在第 2 部分中，值最终通过调用 `storeLocked(...)` 存储到 `entry` 对象中。现在转到第 3 部分。 第 2 部分中的条件在两种可能性下失败（注意，我们已经排除了键可能存在于 `readOnly` 对象中的可能性）：

1.  The key is present in the `dirty` map.
1. 键存在于 `dirty` map 中。
2.  The key is absent in the `dirty` map.
2. 键不在 `dirty` map 中。

Part 3 handles the first case. It simply stores the record into the `entry` object. Now part 4 handles these following two possibilities:

第 3 部分处理第一种情况。它只是将记录存储到 `entry` 对象中。现在第 4 部分处理以下两种可能性：

1.  The `dirty` map is `nil`
1. `dirty` map 是 `nil`
2.  The `dirty` map is not `nil`
2. `dirty` map 不是 `nil`

If the `dirty` map was `nil`, it must be created by copying the entries from `readOnly` object before the new key is added. Otherwise, the new key is added directly without any changes.
如果 `dirty` map 是 `nil`，则必须在添加新键之前通过从 `readOnly` 对象复制条目来创建它。否则，直接添加键而不做任何更改。

The `dirty` map being `nil` also signifies that no new entries were added into the `sync.Map` object ever since its `dirty` map was promoted as the “clean” map. Therefore, the field `read.amended` in source 5 is supposed to be `false` if `dirty` was `nil`.

`dirty` 映射为 `nil` 也表示自从它的 `dirty` map 被提升为“干净” map 以来，没有新条目被添加到 `sync.Map` 对象中。因此，如果 `dirty` 是 `nil`，则源 5 中的字段 `read.amended` 应该是 `false`。

While promoting a `dirty` map to a clean map (this happens with a call to `missLocked()` defined within the structure `sync.Map`; it is only executed when `Load(…)`, `LoadOrStore(…)`, `LoadAndDelete(…)` or `Delete(…)` are called) it just gets directly copied into the “clean” map. When this happens, the users are free to delete the keys in the clean map concurrently (which will just be an atomic operation) and re-add them. But with the first attempt to add a new key into the map after the promotion, the contents of the clean map are copied into the dirty map. But while this happens, the keys with `nil` in their `entry` object’s pointer fields are ignored and within the “clean” map, they are atomically changed to `expunged`.
在将 `dirty` map 提升为干净 map 时（这发生在对结构 `sync.Map` 中定义的 `missLocked()` 的调用时；它仅在 `Load(...)`、`LoadOrStore(...)`时执行、`LoadAndDelete(...)` 或 `Delete(...)` 被调用）它只是被直接复制到“干净”的 map 中。发生这种情况时，用户可以自由地同时删除干净map中的键（这只是一个原子操作）并重新添加它们。但是在升级后第一次尝试将新键添加到map中时，干净映射的内容被复制到脏映射中。但是当发生这种情况时，在其 `entry` 对象的指针字段中带有 `nil` 的键被忽略，并且在“干净” map 中，它们被原子地更改为 `expunged`。

In part 4, a call to `dirtyLocked()` is made to populate the `dirty` map. The [source for](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L362) `[dirtyLocked()](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L362)` is given below:
在第 4 部分中，调用了 `dirtyLocked()` 来填充 `dirty` 映射。 [来源](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L362) `[dirtyLocked()](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L362)` 


> 源码 8：dirtyLocked() — 通过复制可读 map 的内容创建一个新 map 并将其存储在 `dirty` 中
```go
func (m *Map) dirtyLocked() {
	if m.dirty != nil {
		return
	}

	read, _ := m.read.Load().(readOnly)
	m.dirty = make(map[interface{}]*entry, len(read.m))
	for k, e := range read.m {
		if !e.tryExpungeLocked() {
			m.dirty[k] = e
		}
	}
}
```

`tryExpungeLocked()` is defined below:
`tryExpungeLocked()` 定义如下：

> 源码 9：`tryExpungeLocked()`——如果它是 `nil`，则用 expunged 更新条目的指针
```go

func (e *entry) tryExpungeLocked() (isExpunged bool) {
	p := atomic.LoadPointer(&e.p)
	for p == nil {
		if atomic.CompareAndSwapPointer(&e.p, nil, expunged) {
			return true
		}
		p = atomic.LoadPointer(&e.p)
	}
	return p == expunged
}
```

Like `tryStore(…)` defined in source 7, source 8 also relies on a completely atomic operation in setting `expunged` to the pointer. As we can see in Source 8, the creation of the new `dirty` map and the eventual update only happens when `dirty` is `nil` . And the line 9 of source 8 makes it clear that only if `tryExpungeLocked()` fails, the key is added into the `dirty` map.
像源代码 7 中定义的 `tryStore(...)` 一样，源代码 8 也依赖于一个完全原子的操作来将 `expunged` 设置为指针。正如我们在 Source 8 中看到的，新的 `dirty` map 的创建和最终更新仅在 `dirty` 为 `nil` 时发生。源代码 8 的第 9 行清楚地表明，只有当 `tryExpungeLocked()` 失败时，才会将键添加到 `dirty` map中。

`tryExpungeLocked()` ensures that the pointer field in the `entry` object is set to `expunged` if it was originally `nil` (see line 4 of source 9). If the pointer was modified before the compare-and-swap operation, the swap fails and the loop exits. This loop continues until `p` is not `nil`. This could change from being `nil` before the compare-and-swap is executed; for example, it could be replaced by a goroutine executing a call to the `Store(...)` method in the `sync.Map` structure.
`tryExpungeLocked()` 确保 `entry` 对象中的指针字段设置为 `expunged`，如果它最初是 `nil`（参见源代码 9 的第 4 行）。如果在比较和交换操作之前修改了指针，则交换失败并且循环退出。这个循环一直持续到 `p` 不是 `nil`。这可能会在执行比较和交换之前从 `nil` 改变；例如，它可以被一个 goroutine 替换，该 goroutine 执行对 `sync.Map` 结构中的 `Store(...)` 方法的调用。


Following the call to `dirtyLocked()`, the read map is marked as “amended”. This expresses that the map in the `read` field is outdated.

在调用 `dirtyLocked()` 之后，读取的map被标记为“已修改”。这表示 `read` 字段中的map已经失效。

## `Load(key interface{}) (value interface{}, ok bool) :`
## `Load(key interface{}) (value interface{}, ok bool) :`

_Note: if you haven’t read the_ `_Store(…)_` _part, I recommend you to do so. The line of reasoning I used there also applies here and every other methods that are explained below. Therefore I won’t be reexplaining them here._
_注意：如果您还没有阅读_`Store(...)` _部分，我建议您阅读。我在那里使用的推理路线也适用于这里以及下面解释的所有其他方法。因此我不会在这里重新解释它们。_


> 源代码 10：Load 
```go
// Load returns the value stored in the map for a key, or nil if no
// value is present.
// The ok result indicates whether value was found in the map.
func (m *Map) Load(key interface{}) (value interface{}, ok bool) {
	read, _ := m.read.Load().(readOnly)
	e, ok := read.m[key]
	if !ok && read.amended {
		m.mu.Lock()
		// Avoid reporting a spurious miss if m.dirty got promoted while we were
		// blocked on m.mu. (If further loads of the same key will not miss, it's
		// not worth copying the dirty map for this key.)
		read, _ = m.read.Load().(readOnly)
		e, ok = read.m[key]
		if !ok && read.amended {
			e, ok = m.dirty[key]
			// Regardless of whether the entry was present, record a miss: this key
			// will take the slow path until the dirty map is promoted to the read
			// map.
			m.missLocked()
		}
		m.mu.Unlock()
	}
	if !ok {
		return nil, false
	}
	return e.load()
}
```

1.  Retrieves the `readOnly` object atomically.
1. 以原子方式检索 `readOnly` 对象。
2.  Checks if the key along with its `entry` is present in it
2. 检查键及其 `entry` 是否存在于其中
3.  If it succeeds, return the result. At this point, no locks were used.
3. 如果成功，返回结果。此时，没有使用锁。
4.  If it fails, and if `read.amended` was true (which signifies that the `dirty` field is not `nil`), the value is read from the writable map (which is the `dirty` map).
4. 如果失败，并且`read.amended` 为真（表示`dirty` 字段不是`nil`），则从可写的 map（即`dirty` 映射）中读取该值。
5.  Step 4 runs within a locked region guarded by `mu`. The lines 5, 6 and 7 in source 10 are repeated again in the lines 12, 13 and 14; but this is done from within the locked region. This is done because, a new `entry` object could have been added during this time by a different goroutine associated with that key. But all writes synchronize with the lock. Therefore, there won’t be any race conditions here.
5. 第 4 步在一个由 `mu` 保护的锁定区域内运行。源代码 10 中的第 5、6 和 7 行在第 12、13 和 14 行中再次重复；但这是在锁定区域内完成的。这样做是因为，在此期间，与该键关联的不同 goroutine 可能添加了一个新的 `entry` 对象。但是所有的写操作都与锁同步。因此，这里不会有任何竞争条件。
6.  If the retrieval through the readable map fails, it is retrieved from the writable map.
6、如果通过可读的 map 检索失败，则从可写的 map 中检索。

## LoadOrStore(key, value interface{}) (actual interface{}, loaded bool)
## LoadOrStore(key, value interface{}) (actual interface{}, loaded bool)

The source for `LoadOrStore(…)` can be found [here](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L200).
 `LoadOrStore(…)` 的源代码[点击这里](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L200).

For the most part `LoadOrStore(…)` is similar to `Load(…)` except that it uses `e.tryLoadOrStore(value)` in place of `e.tryLoad()` and also makes a call to `missLocked(…)` if the key was absent in the readable map.
在大多数情况下，`LoadOrStore(...)` 与 `Load(...)` 类似，除了它使用 `e.tryLoadOrStore(value)` 代替 `e.tryLoad()` 并且还调用了 `missLocked( ...)` 如果键在可读的map中不存在。

The implementation of `tryLoadOrStore(…)` is similar to any atomic update strategy using the compare-and-swap instruction. This method only succeeds when the `entry` object holds any pointer other than `expunged` (which includes `nil`).
`tryLoadOrStore(...)` 的实现类似于使用比较和交换指令的任何原子更新策略。只有当 `entry` 对象持有除 `expunged`（包括 `nil`）以外的任何指针时，此方法才会成功。

## `LoadAndDelete(key interface{}) (value interface{}, loaded bool):`
## `LoadAndDelete(key interface{}) (value interface{}, loaded bool):`

The [strategy followed](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L269) isn’t very unique from the ones mentioned above. First read is attempted with the `readOnly` object. If it succeeds, `e.delete()` is called which atomically sets the `entry` object’s pointer to `nil`. If it fails, the `entry` object is retrieved from the `dirty` map with within a locked region. The call to `e.delete()` is made if the `dirty` map had the key.
[跟随的策略](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L269) 与上面提到的策略并不是很独特。第一次读取尝试使用 `readOnly` 对象。如果成功，`e.delete()` 被调用，它以原子方式将 `entry` 对象的指针设置为 `nil`。如果失败，则从锁定区域内的 `dirty` map 中检索 `entry` 对象。如果 `dirty` 映射有键，就会调用 `e.delete()`。
The key is not removed at this point. It is just set to `nil`.
此时未移除键。它只是设置为 `nil`。

## `Delete()(value interface{}, ok bool):`
## `Delete()(value interface{}, ok bool):`

This just calls `LoadAndDelete(…)`
内部调用 `LoadAndDelete(…)`

## `Range(f func(key, value interface{}) bool)`
## `Range(f func(key, value interface{}) bool)`

1.  First tries retrieving the key from the `readOnly` object
1. 首先尝试从 `readOnly` 对象中检索密钥
2.  If it succeeds, the range loop is computed immediately (from line 341 to 349 in the [source](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L341)) with the returned object.
2. 如果成功，则立即使用返回的对象计算范围循环（从 [源码](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L341)) 中的第 341 行到 349 行）。
3.  If it fails, a check at [line 325](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L325) sees if the `sync.Map` object was “amended” by extending it with an additional key after the most recent `dirty` map promotion.
3. 如果失败，则在 [line 325](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L325) 处检查, 查看 `sync.Map` 对象是否通过在最近的`dirty` map 升级后使用附加键对其进行扩展来 “修改”。
4.  If the check at [line 325](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L325) succeeds, the `dirty` map is immediately promoted. This is done because, a range operation is most likely to be O(N) assuming all the keys are visited. Therefore, after promoting the `dirty` map and setting `dirty` to `nil`, we can expect the next following store operation (`Store(…)` or `LoadOrStore(…)` that introduces a new key) to follow the slow path of creating a new `dirty` map which is an O(N) operation. But having the call to `Range(…)` which is itself an O(N) operation, to precede the O(N) operation of creating a new `dirty` map ensures that an O(N) operation (of creating a new `dirty` map) only follows another O(N) operation. Thus we can amortize them as one O(N) operation
4.如果在[line 325](https:github.comgolanggoblobaa4e0f528e1e018e2847decb549cfc5ac07ecf20srcsyncmap.goL325)处检查成功，则立即提升`dirty`map。这样做是因为，假设访问了所有键，范围操作最有可能是 O(N)。因此，在提升 `dirty` 映射并将 `dirty` 设置为 `nil` 之后，我们可以期待接下来的存储操作（引入新键的 `Store(...)` 或 `LoadOrStore(...)`）遵循创建新的 `dirty` map 的缓慢路径，这是一个 O(N) 操作。但是调用 `Range(...)` 本身就是一个 O(N) 操作，在 O(N) 操作创建一个新的 `dirty` map 之前确保 O(N) 操作（创建一个新的`dirty` map）只跟在另一个 O(N) 操作之后。因此我们可以将它们摊销为一个 O(N) 操作
5.  Following step 4, the range operation is performed.
5. 在步骤 4 之后，执行范围操作。

## Discussion: sync.Map performance vs RWMutex guarded map’s performance. A quick guide on optimization
## sync.Map 和 RWMutex 保护的 map 之间的性能对比。快速优化指南
[This article](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c) (The new kid in town — Go’s sync.Map by [Ralph Caraveo III](https://medium.com/@deckarep)) goes into a great detail of how a simple `sync.RWMutex` guarded map is way better than `sync.Map` when we are using only a few processor cores. The benchmarks in the article shows that beyond 4 cores, the performance of `sync.Map` seemed to be significantly higher than a `map` guarded by `sync.RWMutex`.
[这篇文章](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c)（go 中的新成员 -- sync.Map by [Ralph Caraveo III](https://medium.com/@deckarep)) 详细说明了当我们仅使用几个核心处理器时，简单的 `sync.RWMutex`保护 map 如何比 `sync.Map` 性能更好。文章中的基准测试表明，超过 4 个内核，`sync.Map` 的性能似乎明显高于由 `sync.RWMutex` 保护的 `map`。

It it therefore necessary to build a prototype that can later be benchmarked to check its relative performance with each variant of its implementation. This can help us choose which variant will be most appropriate for each situation. This shares similarity with how deep neural networks work. In DNNs we have a loss function the value of which we try to minimize. The loss function in this case expresses the objective of the neural network model.

因此，有必要构建一个原型，稍后可以对其进行基准测试，以测试其实现的每个变体的相对性能。这可以帮助我们选择最适合每种情况的变体。这与深度神经网络的工作方式有相似之处。在 DNN 中，我们有一个损失函数，我们试图将其值最小化。这种情况下的损失函数表达了神经网络模型的目标。

The same way, applications must view their test cases and benchmarks together as a “loss function” that expresses the objective of the entire project. If you measure the performance, in time you can improve it. Because, **you cannot adjust what you don’t measure.**

同样，应用程序必须将它们的测试用例和基准一起视为表达整个项目目标的 “损失函数”。如果你衡量绩效，及时你可以改进它。因为，你无法调整你没有衡量的东西。

Premature optimization really becomes a problem when what you optimize does not improve the overall performance of your application, or the change in performance is just too negligibly small.

当您优化的内容没有提高应用程序的整体性能，或者性能的变化太小可以忽略不计时，过早的优化确实会成为一个问题。

**Let’s see an example:**
**让我们看一个例子：**
Assume you have an application which is supposed to receive profile info along with a specific meta-data through API calls, transform it to a different format and send them over to a different microservice. Let’s say you write a procedure to filter a specific pattern in the data being read — assume you receive customer profile data and your application is supposed to filter profiles that are older than 8 years and send it’s ID over to a different message queue while also storing the profile in a cache.

假设您有一个应用程序，它应该通过 API 调用接收配置文件信息以及特定的元数据，将其转换为不同的格式并将它们发送到不同的微服务。假设您编写了一个过程来过滤正在读取的数据中的特定模式 - 假设您收到客户资料数据，并且您的应用程序应该过滤超过 8 年的资料并将其 ID 发送到不同的消息队列，同时还存储缓存中的配置文件。

Should you use `sync.Map` or a map guarded by `sync.RWMutex`?
你应该使用`sync.Map` 还是使用 `sync.RWMutex` 保护的 map？

Assume that out of every 100 profile data received by the application, one of them is 8 years old. So should you really bother thinking about which map to use? Either of those choices make no difference here because, the overall performance of the system is usually not impaired by your choice. Maybe because this cache isn’t the slowest step.

假设在应用程序收到的每 100 个配置文件数据中，其中一个是 8 年前的。那么你真的应该考虑使用哪种类型的 map 吗？这些选择中的任何一个在这里都没有区别，因为您的选择通常不会损害系统的整体性能。也许是因为这个缓存不是最慢的一步。

When we work as a team, it is not uncommon to have different people handle different tasks. So you won’t benefit from having people make their part of the code run faster through testing them with localized benchmarks. The benchmarks must reflect the overall objective of the application.

当我们以一个团队的方式工作时，让不同的人处理不同的任务很常见。因此，让人们通过使用本地化基准测试使他们的代码部分运行得更快，您不会从中受益。基准必须反映应用程序的总体目标。

Any amount of work that goes into improving performance of a part of the code base will be wasted if it was not really the bottle neck. But things are a bit different when you are writing a library where most functions are exposed to the user. Writing benchmarks at the application level (including the exposed APIs) help set the objective the team wishes to achieve.

如果它不是真正的瓶颈，那么任何用于提高部分代码库性能的工作都将被浪费掉。但是当您编写一个大多数功能都向用户公开的库时，情况就有些不同了。在应用程序级别（包括公开的 API）编写基准测试有助于设定团队希望实现的目标。

If reading this article had given you the impression that the Go authors were optimizing prematurely, I have to say, that’s not true. Go is a general purpose language and I am sure even its authors cannot fully anticipate all of its use cases. But it is always possible for them to figure out the most common use cases and optimize for that. Their priorities should be tweaking the parts that have the most impact in their ecosystem. For this, they definitely need a very rigid feedback loop from all their users. Their main focus should be on fixing the pain points.

如果阅读这篇文章给你的印象是 Go 作者过早地优化，我不得不说，那不是真的。 Go 是一种通用语言，我相信即使是它的作者也无法完全预测它的所有用例。但是他们总是有可能找出最常见的用例并为此进行优化。他们的首要任务应该是调整对其生态系统影响最大的部分。为此，他们绝对需要来自所有用户的非常严格的反馈循环。他们的主要重点应该是解决痛点。

## What does an extreme level of optimization look like?
## 极致的优化是什么样的？
For the reasons I mentioned before it is not really needed to improve performance within an application beyond a point. That said, if you do want to make your application super fast for whatever reason, then read on!

由于我之前提到的原因，实际上并不需要将应用程序中的性能提高到某一点。也就是说，如果您确实希望出于某种原因使您的应用程序超快，那么请继续阅读！

SQL database systems do everything in their power to make things run faster. They do this by implementing multiple “strategies” for the same task. When you query for an unindexed record you will observe the worse-case performance. This happens when the query engine falls back to using brute force search.

SQL 数据库系统竭尽全力使事情运行得更快。他们通过为同一任务实施多个 “策略” 来做到这一点。当您查询未编入索引的记录时，您将观察到最坏情况的性能。当查询引擎回退到使用暴力搜索时，就会发生这种情况。

But if you had an index built, the query engine has a chance to choose a better algorithm (of just referring to the index) for improving the query execution time. The “query planning” phase takes care of determining the right strategy to use. If you have multiple indexes built, you are essentially giving the query engine too many options and strategies to choose from. In this case, it may even rely on execution statistics to choose the best strategy to use internally.

但是如果您建立了索引，查询引擎就有机会选择更好的算法（仅引用索引）来提高查询执行时间。 “查询计划” 阶段负责确定要使用的正确策略。如果您构建了多个索引，那么您实际上是在为查询引擎提供太多可供选择的选项和策略。在这种情况下，它甚至可能依靠执行统计来选择最佳策略以供内部使用。

Likewise, if you want a _super fast_ concurrent map the following might help with that:

同样，如果您想要一个 _super fast_ 并发 map，以下内容可能会有所帮助：


源代码 11：超高效同步 map
```go
import (
  "sync"
)

// RWMutexMap is an implementation of mapInterface using a sync.RWMutex.
type RWMutexMap struct {
	mu    sync.RWMutex
	dirty map[interface{}]interface{}
}

func (m *RWMutexMap) Load(key interface{}) (value interface{}, ok bool) {
	m.mu.RLock()
	value, ok = m.dirty[key]
	m.mu.RUnlock()
	return
}

func (m *RWMutexMap) Store(key, value interface{}) {
	m.mu.Lock()
	if m.dirty == nil {
		m.dirty = make(map[interface{}]interface{})
	}
	m.dirty[key] = value
	m.mu.Unlock()
}

func (m *RWMutexMap) LoadOrStore(key, value interface{}) (actual interface{}, loaded bool) {
	m.mu.Lock()
	actual, loaded = m.dirty[key]
	if !loaded {
		actual = value
		if m.dirty == nil {
			m.dirty = make(map[interface{}]interface{})
		}
		m.dirty[key] = value
	}
	m.mu.Unlock()
	return actual, loaded
}

func (m *RWMutexMap) LoadAndDelete(key interface{}) (value interface{}, loaded bool) {
	m.mu.Lock()
	value, loaded = m.dirty[key]
	if !loaded {
		m.mu.Unlock()
		return nil, false
	}
	delete(m.dirty, key)
	m.mu.Unlock()
	return value, loaded
}

func (m *RWMutexMap) Delete(key interface{}) {
	m.mu.Lock()
	delete(m.dirty, key)
	m.mu.Unlock()
}

func (m *RWMutexMap) Range(f func(key, value interface{}) (shouldContinue bool)) {
	m.mu.RLock()
	keys := make([]interface{}, 0, len(m.dirty))
	for k := range m.dirty {
		keys = append(keys, k)
	}
	m.mu.RUnlock()

	for _, k := range keys {
		v, ok := m.Load(k)
		if !ok {
			continue
		}
		if !f(k, v) {
			break
		}
	}
}

// MapInterface is the interface Map implements.
type MapInterface interface {
	Load(interface{}) (interface{}, bool)
	Store(key, value interface{})
	LoadOrStore(key, value interface{}) (actual interface{}, loaded bool)
	LoadAndDelete(key interface{}) (value interface{}, loaded bool)
	Delete(interface{})
	Range(func(key, value interface{}) (shouldContinue bool))
}

func NewSuperEfficientSyncMap(numOfCores int) MapInterface {
  if numOfCores == 0 {
    numOfCores = GOMAXPROCS(0)
  }
  
  // Or this could include more complex logic with multiple 
  // strategies.
  
  if numOfCores > 4 {
    return sync.Map{}
  }
  
  return RWMutexMap{}
}
```

The strategy pattern can be used almost everywhere giving different parts of your application a huge control over its performance. You could also write modules for noting down the statistics and devising the right strategy for your application more like how the query planner does it.

策略模式几乎可以在任何地方使用，让应用程序的不同部分可以对其性能进行巨大的控制。您还可以编写模块来记下统计信息并为您的应用程序设计正确的策略，更像是查询计划器的工作方式。

This way, your application will use a different set of strategy for each environment! This will be really useful if your customers are concerned for performance and you are supporting a wide range of platforms. Or, it will be most useful if you are building a language.

这样，您的应用程序将为每个环境使用一组不同的策略！如果您的客户关心性能并且您支持广泛的平台，这将非常有用。或者，如果您正在构建一种语言，它将最有用。

That said, premature optimization can always be avoided if you are clear about your team’s objectives. Without rigid objectives, you cannot really know what counts as “optimization” and what doesn’t.
也就是说，如果您清楚团队的目标，总是可以避免过早优化。如果没有严格的目标，您就无法真正知道什么是 “优化”，什么不是。
