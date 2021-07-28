# Go: Inside sync.Map — How does sync.Map work internally?

# Go sync map 的内部实现

* 原文地址：https://sreramk.medium.com/go-inside-sync-map-how-does-sync-map-work-internally-97e87b8e6bf
* 原文作者：`Sreram K`
* 本文永久链接：

- 译者：[guzzsek](https://github.com/laxiaohong)
- 校对：[x'x](https:/github.com/**)

提示: 这篇文章有点长


## 目录
1. 引言 
    a. 简单介绍并发性及其在此上下文中的应用
2.  sync.RWMutex 和 map 一起使用的问题
3.  介绍 sync.Map
    a. 在哪些场景使用 sync.Map?
4. sync.Map 实现细节  
    a. 加载、存储和删除如何在高层次上工作？ 
    b. 存储被删除和只是 nil 之间的区别 
    c. Store(key, value interface) 
    d. Load(key interface{}) (value interface{}, ok bool)
    e. LoadOrStore(key, value interface{}) (actual interface{}, loaded bool)
    f. LoadAndDelete(key interface{}) (value interface{}, loaded bool)  
    g. Delete()(value interface{}, ok bool)  
    h. Range(f func(key, value interface{}) bool)_
5. sync.Map 和 RWMutex 保护的 map 之间的性能对比。快速优化指南
6.  _What does an extreme level of optimization look like?_
6. 极致的优化是什么样的？


## 引言
这篇文章简单介绍了如何使用 sync.Map，同时解释 sync.Map 的工作原理。

在应用代码中，大多数操作都是依赖于 hash map。因此，如果 hash map 的读写很慢，它们最终会成为性能的关键瓶颈。在引入 `sync.Map` 之前，标准库只需要依赖于不是线程安全的内置 `map`。当多个 goroutines 调用它时，必须依赖 `sync.RWMutex` 来同步访问。但是这么做，并不能很好地扩展多核 CPU 的性能，所以在 go1.9 引入 `sync.Map` 来解决多核 CPU 操作 map 的性能问题。当程序运行在 64 核的机器上，`sync.RWMutex` 的性能下降会比较明显。

使用`sync.RWMutex`,[sync.RWMutex](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L28)中的值`readerCount`随着每次调用读锁而增加，这会导致缓存的竞争。最终导致处理器其他内核的性能下降。这是因为每增加一个核心，向每个核心的缓存发布更新的开销就会增加。
[sync.Map 文档](https://golang.org/pkg/sync/#Map)
>  snyc.Map 类型针对两个常见案例进行优化
> 
> (1) 当给定键的条目只写入一次但读取多次时，就像只会增长的缓存中一样
> 
> (2) 当多个 goroutine 读取、写入和重写不相交的 keys 集合时。在这两种情况下，与使用单独的 Mutex 或 RWMutex 配对的 map 相比，使用 sync.Map 可以显着减少锁争用。

带有读写锁的 map 在第一个 case 中，在频繁地调用[atomic.AddInt32(&rw.readerCount, 1)](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L61) and [atomic.AddInt32(&rw.readerWait, -1)](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L81) 下性能显著下降。写入的开销无法避免，但我们必须期望读取速度非常快，特别是它作为一个缓存，应该有助于在快速管道中处理数据。

## 简单介绍并发性及其在此上下文中的应用

现代应用程序必须在短时间内处理大量历史数据。为此，他们重度依赖高速的多核处理器。

这些系统处理的实时输入通常具有不可预测的到达时间。这正是操统级线程和 goroutines 真正闪耀的地方。这些依赖锁和信号量的组合来让它们在等待输入时 "休眠"。这会释放虚拟线程使用的 CPU 资源，直到它收到唤醒它的中断。等待中断的线程或 goroutine 类似于等待在输入到达时调用的回调——中断信号在解锁它正在等待的互斥锁时（或当信号量变为零时）产生。


在理想情况下，我们希望应用程序处理数据的能力随着计算机核心数增加而增加。但并非所有应用程序都能很好地扩展，即使它一开始的设计是多个 goroutines 处理多个任务。

某些代码块可能需要锁或 atomic 指令进行同步，将这些部分变成强制同步执行的代码块。比如每个 goroutine 都可以访问的中央缓存。这些会导致锁争用，从而阻止应用程序通过附加内核提高性能。甚至更糟的是，这些可能会导致性能下降。atomic 指令也会带来开销，但它比锁引起的开销小得多。

硬件级原子指令对于内存的访问并不总是保证读取最新值。原因是，每个处理器内核都维护一个可能已过时的本地缓存。为了避免这个问题，原子写操作通常跟在指令之后强制每个缓存更新。最重要的是，为了提升（在硬件和软件级别）的性能，它还必须防止 [内存重新排序(就是我们常说的指令重排，cpu 的一种优化手段)](https://en.cppreference.com/w/cpp/atomic/memory_order)。


`map` 结构被广泛使用，以至于几乎每个应用程序都在其代码中依赖它。并且要在并发应用程序中使用它，读取和写入它必须与 Go 中的 `_sync.RWMutex_` 同步。这样做会导致对 `atomic.AddInt32(...)` 的过度使用，从而导致频繁的缓存争用，强制刷新缓存和内存(指令)排序。这会降低性能(译者注: 这里说的缓存是 CPU 中的缓存)。


`sync.Map` 使用 atomic 指令和锁的组合，但确保读取操作的路径尽可能短，大多数情况下，每次调用 `Load(...)` 只需一个原子加载操作案件。atomic 存储指令通常是强制更新（每个内核的）缓存的指令，而 atomic 加载可能只需要强制执行内存排序并确保其原子性。只有 `atomic.AddInt32(...)` 最糟糕，因为它与对同一变量的其他原子更新的争用将导致它忙于等待，直到依赖于比较和交换(译者注:这里便是CAS指令，在汇编中一个指令完成两个操作)指令的更新成功。


## sync.RWMutex 和 map 一起使用的问题


使用 `sync.RWMutex` 来同步访问 map 的一个例子: [https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/map\_reference\_test.go#L25](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/map_reference_test.go#L25)

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



当性能很重要时，我们可以通过减少并行获取相同锁的频率（从而减少锁争用的频率）或完全用 atomic 指令（如 atomic-load、atomic-store 和 atomic-compare）代替锁来解决这个问题和交换。atomic 操作也不是灵丹妙药，因为依赖于 atomic 比较和交换的状态更新在无限循环中运行，直到更新成功。当存在争用时，更新通常不会发生，因此当有大量并发更新时，导致它们忙等待。


大多数应用程序通常依赖于两者的组合。甚至有些应用程序也尝试选择更快的替代方案，例如减少对循环中旋转的 atomic 比较和交换指令的调用次数。

`[sync.RWMutex](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L28)` 使用信号量的组合以及两个附加变量 `readerCount` 和 `readerWait` 来记录正在读取和等待读取的数量。


要理解在多核环境中我们需要使用 `sync.Map`，而不是使用由 `sync.RWMutex` 保护的内置 `map`，那么，我们必须深入研究 [how](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba) `[sync.RWMutex](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba)` 的[内部工作。](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba)

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


在继续尝试了解 `sync.Map` 的原理之前，还要了解 [为什么我们绝对需要这些方法](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa) `[LoadAndDelete (...)](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa)` [和](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa) `[LoadOrStore(...)](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa)`。


`sync.Map` 总是维护两个 `map` 对象，一个用于读取，一个用于写入。读映射是部分不可变的，而写映射是完全可变的。


在任何时候，可读 map 都不会被完全更新，而可写的 map 被假定为完全更新，表示存储的准确状态（即使它没有设置为 `nil`）。每当从只读 map 未命中键时，它就会从带有 `sync.Mutex` 锁的写入映射中读取。


删除一个键的时候，键可以只存在于可写 map 中，也可以存在于可写 map 和可读 map 中。如果它仅存在于可写 map 中，则使用内置的 `delete` 操作将其完全删除。但是如果它同时存在于可写 map 和可读 map 中，则它只设置为`nil`（注意，将字段设置为 `nil` 的更新操作同时反映在读 map 和写 map 中，因为它们指向同一个 `entry` 对象；稍后会详细介绍）。


对可写 map 的每次访问都由 `sync.Mutex` 保护，它们也有原子指令的开销。因此，它的开销必须略大于由 `sync.RWMutex` 保护的内置 `map`。


因此，此实现的目标之一应该是减少读取未命中的频率。这是通过将可写 map 提升为下一个可读的 map 来完成的（同时将指向可写 map 的指针设置为 `nil`），当读取未命中数大于可写 map 的长度时（此长度使用 `len `）。然后丢弃过时的可读 map。


在第一次尝试向可写的 map 添加键时，通过将新可读 map 的内容复制到可写的 map 来创建新 map 对象。数据搬移结束之后，可读的 map 将存储最准确的状态。但是被搬移之后就变成了 "不可变"，不会再有新的 key 被添加进去。因此，向 `sync.Map` 添加额外的键会使可读的 map 失效。

更新有两种不同的方式。如果添加的键（使用`sync.Map` 的`Store(...)` 或`LoadOrStore(...)` 操作）已经存在于可读的 map 中，则可读的 map 中与键关联的值是以原子方式更新（注意：以这种方式对 value 字段所做的更改也将立即反映在可写映射上。本文稍后将解释这是如何做到的）。如果键只存在于可写的 map 中，或者键根本不存在，则更新仅在可写区域中进行，并需要使用 “sync.Mutex”锁。

## sync.Map 的使用场景


`sync.Map` 最初是为了减少 Go 的标准库包所产生的开销，这些包一直使用由 `sync.RWMutex` 保护的 `map`。所以 Go 的作者们发现像 `sync.Map` 这样的存储不会增加太多的内存开销（另一种内存密集型解决方案是为每个使用的 goroutine 提供一个单独的映射副本，但让它们同步更新）而还提高程序在多核环境中的性能。因此，`sync.Map` 的初衷是为了解决[标准包中的问题](https://github.com/golang/go/issues/40999#issuecomment-679449778)，但还是公开了，希望大家觉得有用。


但是，文档并没有真正详细说明 `sync.Map` 究竟在哪里最有用。 通过[基准测试](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c) 和 `[sync.Map](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c)` 表明，仅当它在具有超过 4 个核的系统上运行时，使用 `sync.Map` 比使用由 `sync.RWMutex` 保护的 `map` 更加高率。 `sync.Map` 最理想的用例是将其用作缓存，特别是频繁访问不相交的键；或从同一组键中广泛读取它。


新添加的键可能会留在可写的 map 中，而最常访问的键可能会留在可读的 map 中。当添加、读取和删除一组有限的键时，`sync.Map` 将执行最少的操作，其中每个操作都以相同的频率发生。当你不让写 map 中的键被提升时，就会发生这种情况经常添加和删除它们。在这种情况下，我们最好将 `map` 与 `sync.RWMutex` 或 `sync.Mutex` 一起使用（并发散列映射的确切选择通常通过基准测试决定）。


每当一个键在 `sync.Map` 中被删除，它只将其关联的值字段标记为 `[nil](https://github.com/golang/go/blob/21a04e33353316635b5f3351e807916f3bb1e844/src/sync/map.go#L297)`，但直到第一次写入后，key 才真正删除 writable-map 作为可读 map。这会导致内存开销。但是这种开销只是暂时的，随着下一个促销周期，开销会下降。

## sync.Map 实现细节

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


正如我们所见，`sync.Map` 有一个 `dirty` map 存储和一个用于存储 “clean” 的 `read` map 的 `atomic.Value` 字段。所有对 `dirty` 的访问总是由 `mu` 保护。在我们查看每个独立的方法如何工作之前，我们必须对 `sync.Map` 的工作原理和设计思想有一个宏观的了解。

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


`entry` 结构相当于 “容器”或“盒子”，保存和键相关联的值。不是直接用 `m[key] = value` 存储值，而是将 `value` 封装在一个方便的 `entry` 类型容器中。然后将 `entry` 的地址存储到与键关联的 `map` 对象中。

在任何的时间节点中，都假定 `entry` 满足以下三个属性之一：

1. 它包含一个有效值：`p != expunged && p != nil`。 `expunged`（意味着永久删除）被定义为 `var expunged = unsafe.Pointer(new(interface{}))`，这是一个只设置一次的任意全局值。它没有任何价值。它只是为了将 “删除” 值与任意 `entry` 字段中的所有其他 `nil` 和非 `nil` 值区分开来。


2. 它包含 `nil`。


3. 它包含 `expunged`（我们很快就会详细介绍 `nil` 状态与 `expunged` 状态有何不同）。


将指针包裹在一个像 `entry` 这样的结构下是非常方便的。如果您正在更改 `entry` 的状态，您可以期望它在每个其他具有指向 `entry` 对象的指针的位置立即更新。


所以，如果您在可读的 map 和可写的 map 之间共享 `entry` 的地址，更新可读 map 的 `entry`也将反映可写的 map 上的更改以及反之亦然（请注意，在源 3 和可写映射中）源 5 映射被定义为`map[inerface{}]entry`，其中键是一个`interface{}`，并且该 entry 存储为一个指针）。


> 源代码 5：只读结构体
```go
// readOnly is an immutable struct stored atomically in the Map.read field.
type readOnly struct {
	m       map[interface{}]*entry
	amended bool // true if the dirty map contains some key not in m.
}
```


`sync.Map` 结构的 `read` 字段是一个 `atomic.Value` 字段，它保存对 `readOnly`（源代码 5）的引用。此结构包含另一个字段 `amended`，当 `sync.Map` 对象通过添加新键进行扩展并且自添加新键后尚未发生升级时，该字段为真。在这种情况下，键进入可写的 map，而可读 map 中没有它的记录。 `amended` 字段为 true 时，表示这种特定状态，其中 `dirty` 映射包含的记录，但是 `read` 不包含记录。

## 加载、存储和删除如何在高层次上工作？

这些操作的读取部分通常是廉价的（相对）。原因是从 `atomic.Value` 字段中检索到 `readOnly` 对象的指针，并快速搜索与键关联的值。如果该值存在，则返回。


如果它不存在，那么它很可能是最近添加的。在这种情况下，需要检查 `dirty` 字段（保留 `mu`）。如果键存在于 `dirty` 字段中，则将其作为结果进行检索。


在此实现中(译者注: dirty map)，读操作会比较慢。随着 `readOnly` 对象中的每次未命中，字段 `misses` 的值自动递增。当 `misses` 计数大于 `dirty` 的大小时，通过创建一个新的 `readOnly` 对象来包含它，它会被提升（直接移动它的指针）到 `read` 字段。发生这种情况时，会丢弃 `read` 字段的先前值。


所有涉及 `dirty` map 的操作都在互斥锁 `mu` 保护的区域内执行。


当记录被存储到 `sync.Map` 中时，它会通过以下三种方式之一进行处理:

1、修改 `(read.Load().(readOnly))[key]` 返回的 `entry` 实例，如果检索成功。修改是通过将值添加到 `entry` 字段来完成的。


2.修改 `dirty[key]` 返回的 `entry` 实例，如果检索成功。修改是通过替换 `entry` 对象（存储在 `atomic.Value` 类型的 `read` 对象内）中的值来完成的。如果第一步失败，则执行此操作。


3.如果 `dirty` 为 `nil`（当`read.amended`为false时就是这种情况），创建一个新的 `map` 并将只读 map 中的所有内容复制到它。然后将记录添加到 `dirty`（注意，随着字段被复制，`entry` 对象的地址就是被复制的对象。因此，读映射和写映射中存在的每个键都指向准确的相同的 `条目` 对象。）


在删除的情况下，如果键存在于 `read` 中的 `readOnly` 对象中，它的 `entry` 实例会自动更新为 `nil`。这个操作不需要获取 `mu`。但是在 `dirty` 字段中搜索键时需要获取 `mu`。如果键不存在于 `read` 中，它会在 `dirty` 中查找，同时由 `mu` 保护。如果只在 `dirty` 中找到，则直接使用内置的 `delete` 函数删除 `entry` 对象。


因此，当在 read 字段持有的 readOnly 实例中找到键时，读取、写入和删除操作将是完全原子的。而其他需要通过 `dirty` 处理的情况将由 `mu` 保护。


对 `entry` 字段所做的任何修改都将反映在 `read` 和 `dirty` map 中的 `readOnly` 对象上。因为，每当通过复制 `readOnly` 实例创建新的 `map[interface{}]entry` 对象时，只会复制 `entry` 对象的地址。

## 存储 `expunged` 和简单的 `nil` 之间的区别

始终认为以下属性成立：


1. `entry` 里面有一个指针。在任何时间，它的指针都可以保存 `expunged`、`nil` 或指向接口的指针，该指针保存了用户通过`Store(...)` 或 `LoadOrStore(...)` 方法提供的有效值。


2. 如果 `entry` 保存的是 `nil`，则表示与键关联的值已通过调用 `Delete(...)` 或 `LoadAndDelete(...)` 进行删除，而它存在于 `readOnly` 对象中，并且 `脏` map。

3.  If `entry` holds `expunged`, it signifies that a non-`nil` `dirty` map exists which does not have the same key that associates the `entry` field.

3. 如果 `entry` 包含 `expunged`，则表示存在非 `nil` `dirty` 映射，该映射不具有关联 `entry` 字段的相同键。


当`misses > len(dirty)`（`misses` 是`sync.Map` 结构中的一个字段）时，`dirty` map 被复制到 `atomic.Value` 类型的 `read` 字段中。这样做的代码是： `m.read.Store(readOnly{m: m.dirty})` 其中，这里的 `Store` 是一个原子存储操作。



`readOnly` 对象中有两个字段。一个用于 map，另一个用于 `amended` 变量，该变量表示升级后是否将新键添加到 `sync.Map` 对象。第一次尝试在升级后插入键会导致 `readOnly` 对象内的 map 被逐键复制到 `dirty` map 键。与存储 `nil` 的 `entry` 对象相关联的每个键都不会被复制到 `dirty` 映射中，而是将其 `entry` 对象更新为包含`expunged`。


因此，`expunged` 的键仅存在于 `干净` 映射中，而不会将它们复制到新的 `dirty`map。这是在假设不会再次添加被删除一次的键的情况下完成的。



有两个独立的未导出方法，为 `sync.Map` 定义的 `missLocked()` 和 `dirtyLocked()`。他们的责任如下:

1. 传播 `dirty` 映射（同时将`sync.Map`中的`dirty`字段设置为`nil`）
2. 将 `readOnly` 对象（其 `amended` 字段设置为 `false`）中的键值对复制到新创建的 `dirty` map 对象（通过忽略与 `entry` 对象关联的键）设置为 `nil` 并使它们`expunged`；因为它们没有被复制到`dirty` map 中）。



`missLocked()` 每次在读取 `readOnly` 对象时出现键未命中时都会被调用。除了 `Range(…)` 之外，`sync.Map` 中定义的每个导出方法都可以触发调用，因为它们都首先尝试检索存储的记录并接受 `key` 作为参数。 `missLocked()` 仅在其大小小于未命中数时才会提升 `dirty` 映射。


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


让我们将上面的代码分成四部分（上面标记了包含每个部分的区域）。第一部分尝试从 `read` 中检索值，这是一个包含 `readOnly` 对象的 `sync.Value` 字段。如果读取成功，它会尝试将值以原子方式存储到 `entry` 对象中。源代码 7 显示了它是如何完成的。


`tryStore(…)` 操作中的 atomic 更新包含一个无限循环，该循环在值之前被 `expunged` 时终止。这是因为，`expunged` 值表示在 `dirty` map 中没有相同键字段的副本，而在 `只读` 对象中有一个。因此，在这种情况下更新指针不会反映在 `dirty` map 上，它总是应该包含 `sync.Map` 的完全更新和准确状态。除了最近刚刚推广的情况。在这种情况下，`dirty` 字段将暂时保留 `nil`，直到第一次尝试写入它，因为它被设置为 `nil`。


源代码 7 中的无限循环导致函数保持 “忙等待” 状态，直到更新成功。原子比较和交换操作接受三个参数。要修改的指针、指针中可能包含的旧值和新值。如果旧值与指针中保存的原始值相同，则新值存储在指针中。


在源代码 7 中，指针首先从 `entry` 对象中自动加载，并检查它是否被 `expunged`。如果是，那么`tryStore` 会失败，因为`expunged` 表示`entry` 对象不存在于与其键关联的 `dirty` map 中。因此，将值存储到从 `read` 映射中检索到的 `entry` 对象将不再有用（因为修改不会反映在 `dirty` map 上）。


如果 `e.p`（存储在 `entry` 对象中的指针）与之前的 `p` 值相同，则源代码 7 第 11 行中的 atomic-compare-and-swap 指令负责添加新值在源代码 7 的第 8 行读取。如果在不同的 goroutine 中运行的方法在第 11 行执行之前原子地修改了 `p` 的底层值，比较和交换指针操作失败导致循环继续。如果 `p` 被修改为包含 `expunged`，那么循环会因为第 8 行的条件分支而中断。


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

其余部分 2、3 和 4（在 Source 6 中）都在一个由 `mu` 锁保护的区域内运行。第 1 部分在 key 存在于 `readOnly` 对象中并且 `tryStore` 操作（如上所述）成功时返回。

但是第 1 部分失败意味着 key 不存在于 `readOnly` 对象中，或者它已被删除。继续第 2 部分，读取值再次重新加载到锁定区域内。

可能会在调用从不同 goroutine 执行的 `missLocked()` 之后被替换，该 goroutine 也将在获取 `mu` 后执行（_Note ，每个带有后缀 `Locked` 的函数都应该在由 `mu` 保护的锁定区域内执行）。但是因为第 1 部分没有获取 `mu`，在源代码 6 的第 6 行检索到的值可能会过时。


在第 2 部分中，再次检索了 `entry` 指针。现在，调用`e.unexpungeLocked()` 检查存储在条目中的值是否被 `expunged`：

1. 如果它是 `nil` 或其他任何东西，则表示在 `dirty` 映射中也必须存在相同的键。
2. 但如果它是 `expunged`，则表示该键不存在于 `dirty` 映射中，并且必须将其添加到其中。因此，由 `read.m[key]` 检索到的 `entry` 对象的指针被存储到与其适当的键相关联的`dirty` 中。因为使用了相同的指针，对底层 `entry` 对象的任何更改都会反映在 “干净” map 和 “dirty” map中。

对 `unexpungeLocked()` 的调用会执行语句 `return atomic.CompareAndSwapPointer(&e.p, expunged, nil)` （这是其定义中唯一的语句）。这确保了 `e.p` 仅在它被 `expunged` 时更新。您不必在这里忙着等待以允许更新发生。这是因为 `CompareAndSwapPointer(...)` 的 “旧指针” 参数是一个常量（`expunged`）并且它永远不会改变。

`tryStore()` 和 `unexpungeLocked()` 都可以更新 `e.p`，尽管它们不是由同一个互斥锁相互保护的。因此，他们可能会尝试从不同的 goroutines 同时更新 `e.p`。但这不会成为竞争条件，因为 `unexpungeLocked()` 应该仅在其指针（入口 entry 的 p 字段）设置为 `expunged` 时修改入口 entry。


在不同的 goroutine 上运行的 `unexpungeLocked()` 可以在 Source 7 的第 7 行和第 11 行之间的任何地方执行它的 `CompareAndSwapPointer(…)` 语句。如果它在这些行之间执行，底层指针的值将在第 11 行的比较和交换操作将导致循环失败并再次重复。因此，如果出现以下情况，则无法成功执行 Source 7 中第 7 行和第 11 行之间的区域：

1. 不同的 goroutine 执行相同的区域，试图修改相同的底层指针，或者，
2. 如果`unexpungeLocked()` 在同一时间范围内同时执行。

在第 2 部分中，值最终通过调用 `storeLocked(...)` 存储到 `entry` 对象中。现在转到第 3 部分。 第 2 部分中的条件在两种可能性下失败（注意，我们已经排除了键可能存在于 `readOnly` 对象中的可能性）：

1. 键存在于 `dirty` map 中。
2. 键不在 `dirty` map 中。


第 3 部分处理第一种情况。它只是将记录存储到 `entry` 对象中。现在第 4 部分处理以下两种可能性：

1. `dirty` map 是 `nil`
2. `dirty` map 不是 `nil`

如果 `dirty` map 是 `nil`，则必须在添加新键之前通过从 `readOnly` 对象复制条目来创建它。否则，直接添加键而不做任何更改。


`dirty` 映射为 `nil` 也表示自从它的 `dirty` map 被提升为“干净” map 以来，没有新条目被添加到 `sync.Map` 对象中。因此，如果 `dirty` 是 `nil`，则源 5 中的字段 `read.amended` 应该是 `false`。

在将 `dirty` map 提升为干净 map 时（这发生在对结构 `sync.Map` 中定义的 `missLocked()` 的调用时；它仅在 `Load(...)`、`LoadOrStore(...)`时执行、`LoadAndDelete(...)` 或 `Delete(...)` 被调用）它只是被直接复制到“干净”的 map 中。发生这种情况时，用户可以自由地同时删除干净map中的键（这只是一个原子操作）并重新添加它们。但是在升级后第一次尝试将新键添加到map中时，干净映射的内容被复制到脏映射中。但是当发生这种情况时，在其 `entry` 对象的指针字段中带有 `nil` 的键被忽略，并且在“干净” map 中，它们被原子地更改为 `expunged`。

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

像源代码 7 中定义的 `tryStore(...)` 一样，源代码 8 也依赖于一个完全原子的操作来将 `expunged` 设置为指针。正如我们在 Source 8 中看到的，新的 `dirty` map 的创建和最终更新仅在 `dirty` 为 `nil` 时发生。源代码 8 的第 9 行清楚地表明，只有当 `tryExpungeLocked()` 失败时，才会将键添加到 `dirty` map中。

`tryExpungeLocked()` 确保 `entry` 对象中的指针字段设置为 `expunged`，如果它最初是 `nil`（参见源代码 9 的第 4 行）。如果在比较和交换操作之前修改了指针，则交换失败并且循环退出。这个循环一直持续到 `p` 不是 `nil`。这可能会在执行比较和交换之前从 `nil` 改变；例如，它可以被一个 goroutine 替换，该 goroutine 执行对 `sync.Map` 结构中的 `Store(...)` 方法的调用。



在调用 `dirtyLocked()` 之后，读取的map被标记为“已修改”。这表示 `read` 字段中的map已经失效。

## `Load(key interface{}) (value interface{}, ok bool) :`

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

1. 以原子方式检索 `readOnly` 对象。
2. 检查键及其 `entry` 是否存在于其中
3. 如果成功，返回结果。此时，没有使用锁。
4. 如果失败，并且`read.amended` 为真（表示`dirty` 字段不是`nil`），则从可写的 map（即`dirty` 映射）中读取该值。
5. 第 4 步在一个由 `mu` 保护的锁定区域内运行。源代码 10 中的第 5、6 和 7 行在第 12、13 和 14 行中再次重复；但这是在锁定区域内完成的。这样做是因为，在此期间，与该键关联的不同 goroutine 可能添加了一个新的 `entry` 对象。但是所有的写操作都与锁同步。因此，这里不会有任何竞争条件。
6、如果通过可读的 map 检索失败，则从可写的 map 中检索。

## LoadOrStore(key, value interface{}) (actual interface{}, loaded bool)

 `LoadOrStore(…)` 的源代码[点击这里](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L200).

在大多数情况下，`LoadOrStore(...)` 与 `Load(...)` 类似，除了它使用 `e.tryLoadOrStore(value)` 代替 `e.tryLoad()` 并且还调用了 `missLocked( ...)` 如果键在可读的map中不存在。

`tryLoadOrStore(...)` 的实现类似于使用比较和交换指令的任何原子更新策略。只有当 `entry` 对象持有除 `expunged`（包括 `nil`）以外的任何指针时，此方法才会成功。

## `LoadAndDelete(key interface{}) (value interface{}, loaded bool):`

[跟随的策略](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L269) 与上面提到的策略并不是很独特。第一次读取尝试使用 `readOnly` 对象。如果成功，`e.delete()` 被调用，它以原子方式将 `entry` 对象的指针设置为 `nil`。如果失败，则从锁定区域内的 `dirty` map 中检索 `entry` 对象。如果 `dirty` 映射有键，就会调用 `e.delete()`。
The key is not removed at this point. It is just set to `nil`.
此时未移除键。它只是设置为 `nil`。

## `Delete()(value interface{}, ok bool):`

内部调用 `LoadAndDelete(…)`

## `Range(f func(key, value interface{}) bool)`

1. 首先尝试从 `readOnly` 对象中检索密钥
2. 如果成功，则立即使用返回的对象计算范围循环（从 [源码](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L341)) 中的第 341 行到 349 行）。
3. 如果失败，则在 [line 325](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L325) 处检查, 查看 `sync.Map` 对象是否通过在最近的`dirty` map 升级后使用附加键对其进行扩展来 “修改”。
4.如果在[line 325](https:github.comgolanggoblobaa4e0f528e1e018e2847decb549cfc5ac07ecf20srcsyncmap.goL325)处检查成功，则立即提升`dirty`map。这样做是因为，假设访问了所有键，范围操作最有可能是 O(N)。因此，在提升 `dirty` 映射并将 `dirty` 设置为 `nil` 之后，我们可以期待接下来的存储操作（引入新键的 `Store(...)` 或 `LoadOrStore(...)`）遵循创建新的 `dirty` map 的缓慢路径，这是一个 O(N) 操作。但是调用 `Range(...)` 本身就是一个 O(N) 操作，在 O(N) 操作创建一个新的 `dirty` map 之前确保 O(N) 操作（创建一个新的`dirty` map）只跟在另一个 O(N) 操作之后。因此我们可以将它们摊销为一个 O(N) 操作
5. 在步骤 4 之后，执行范围操作。

## sync.Map 和 RWMutex 保护的 map 之间的性能对比。快速优化指南
[这篇文章](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c)（go 中的新成员 -- sync.Map by [Ralph Caraveo III](https://medium.com/@deckarep)) 详细说明了当我们仅使用几个核心处理器时，简单的 `sync.RWMutex`保护 map 如何比 `sync.Map` 性能更好。文章中的基准测试表明，超过 4 个内核，`sync.Map` 的性能似乎明显高于由 `sync.RWMutex` 保护的 `map`。


因此，有必要构建一个原型，稍后可以对其进行基准测试，以测试其实现的每个变体的相对性能。这可以帮助我们选择最适合每种情况的变体。这与深度神经网络的工作方式有相似之处。在 DNN 中，我们有一个损失函数，我们试图将其值最小化。这种情况下的损失函数表达了神经网络模型的目标。


同样，应用程序必须将它们的测试用例和基准一起视为表达整个项目目标的 “损失函数”。如果你衡量绩效，及时你可以改进它。因为，你无法调整你没有衡量的东西。


当您优化的内容没有提高应用程序的整体性能，或者性能的变化太小可以忽略不计时，过早的优化确实会成为一个问题。

**让我们看一个例子：**

假设您有一个应用程序，它应该通过 API 调用接收配置文件信息以及特定的元数据，将其转换为不同的格式并将它们发送到不同的微服务。假设您编写了一个过程来过滤正在读取的数据中的特定模式 - 假设您收到客户资料数据，并且您的应用程序应该过滤超过 8 年的资料并将其 ID 发送到不同的消息队列，同时还存储缓存中的配置文件。

你应该使用`sync.Map` 还是使用 `sync.RWMutex` 保护的 map？


假设在应用程序收到的每 100 个配置文件数据中，其中一个是 8 年前的。那么你真的应该考虑使用哪种类型的 map 吗？这些选择中的任何一个在这里都没有区别，因为您的选择通常不会损害系统的整体性能。也许是因为这个缓存不是最慢的一步。


当我们以一个团队的方式工作时，让不同的人处理不同的任务很常见。因此，让人们通过使用本地化基准测试使他们的代码部分运行得更快，您不会从中受益。基准必须反映应用程序的总体目标。


如果它不是真正的瓶颈，那么任何用于提高部分代码库性能的工作都将被浪费掉。但是当您编写一个大多数功能都向用户公开的库时，情况就有些不同了。在应用程序级别（包括公开的 API）编写基准测试有助于设定团队希望实现的目标。


如果阅读这篇文章给你的印象是 Go 作者过早地优化，我不得不说，那不是真的。 Go 是一种通用语言，我相信即使是它的作者也无法完全预测它的所有用例。但是他们总是有可能找出最常见的用例并为此进行优化。他们的首要任务应该是调整对其生态系统影响最大的部分。为此，他们绝对需要来自所有用户的非常严格的反馈循环。他们的主要重点应该是解决痛点。

## 极致的优化是什么样的？

由于我之前提到的原因，实际上并不需要将应用程序中的性能提高到某一点。也就是说，如果您确实希望出于某种原因使您的应用程序超快，那么请继续阅读！


SQL 数据库系统竭尽全力使事情运行得更快。他们通过为同一任务实施多个 “策略” 来做到这一点。当您查询未编入索引的记录时，您将观察到最坏情况的性能。当查询引擎回退到使用暴力搜索时，就会发生这种情况。


但是如果您建立了索引，查询引擎就有机会选择更好的算法（仅引用索引）来提高查询执行时间。 “查询计划” 阶段负责确定要使用的正确策略。如果您构建了多个索引，那么您实际上是在为查询引擎提供太多可供选择的选项和策略。在这种情况下，它甚至可能依靠执行统计来选择最佳策略以供内部使用。


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


策略模式几乎可以在任何地方使用，让应用程序的不同部分可以对其性能进行巨大的控制。您还可以编写模块来记下统计信息并为您的应用程序设计正确的策略，更像是查询计划器的工作方式。


这样，您的应用程序将为每个环境使用一组不同的策略！如果您的客户关心性能并且您支持广泛的平台，这将非常有用。或者，如果您正在构建一种语言，它将最有用。

也就是说，如果您清楚团队的目标，总是可以避免过早优化。如果没有严格的目标，您就无法真正知道什么是 “优化”，什么不是。
