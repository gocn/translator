# Go: Inside sync.Map — How does sync.Map work internally?

* 原文地址：https://sreramk.medium.com/go-inside-sync-map-how-does-sync-map-work-internally-97e87b8e6bf
* 原文作者：`Sreram K`
* 本文永久链接：

- 译者：[guzzsek](https://github.com/laxiaohong)
- 校对：[x'x](https:/github.com/cvley)
NOTE: this article is a long one. So it takes time to load (especially on mobile phones). By the way, I’m **actively looking for a job** :-) More on this in the “letter to the reader” part at the end (which may never finish loading).

1.  _Introduction  
    a. A brief introduction to concurrency and how it applies in this context_
2.  _The problem with using a map with sync.RWMutex_
3.  _Introducing sync.Map  
    a. Where is sync.Map used?_
4.  _sync.Map: the implementation details  
    a. How does load, store and delete work at a high level?  
    b. The difference between storing expunged and just simply nil  
    c. Store(key, value interface{})  
    d. Load(key interface{}) (value interface{}, ok bool)  
    e. LoadOrStore(key, value interface{}) (actual interface{}, loaded bool)  
    f. LoadAndDelete(key interface{}) (value interface{}, loaded bool)  
    g. Delete()(value interface{}, ok bool)  
    h. Range(f func(key, value interface{}) bool)_
5.  _Discussion: sync.Map performance vs RWMutex guarded map’s performance. A quick guide on optimization_
6.  _What does an extreme level of optimization look like?_
7.  _Letter to the reader (actively_ **_looking for a job_** _:-) )_

_This article briefly introduces how sync.Map can be used, and also explains how sync.Map works._

Most operations rely on a hash map in their code. Therefore, they end up being a crucial bottleneck for performance if they are slow. Before the introduction of `sync.Map` the standard library only had to rely on the built-in `map` which was not thread safe. When it had to be called from multiple goroutines `sync.RWMutex` was relied on to synchronize access. But this did not really scale well with additional processor cores, and this was addressed by implementing `sync.Map` for go1.9. When run with 64 processor cores, the performance of `sync.RWMutex` significantly degrades.

With `sync.RWMutex`, the value `readerCount` in `[sync.RWMutex](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L28)` was being incremented with each call to `RLock` , leading to cache contention. And this lead to a decrease in performance with additional processor cores. It is because with each additional core, the overhead of publishing updates to each core’s cache increased.

The documentation says: ([here](https://golang.org/pkg/sync/#Map))

> The Map type is optimized for two common use cases:
> 
> (1) when the entry for a given key is only ever written once but read many times, as in caches that only grow, or
> 
> (2) when multiple goroutines read, write, and overwrite entries for disjoint sets of keys. In these two cases, use of a Map may significantly reduce lock contention compared to a Go map paired with a separate Mutex or RWMutex.

`map` with `sync.RWMutex` significantly reduces performance with the first case above, when the calls to `[atomic.AddInt32(&rw.readerCount, 1)](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L61)` and `[atomic.AddInt32(&rw.readerWait, -1)](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L81)` are too frequent. The overhead of writes cannot be avoided, but we must expect reads to be extremely fast especially if it is a cache that is supposed to help with processing data in a fast pipeline.

## A brief introduction to concurrency and how it applies in this context

Modern applications have to deal with historically large amounts of data within short periods of time. For this, they rely on multi-core processors with high processing speeds.

Real-time inputs handled by these systems usually have unpredictable arrival times. This is where OS level threads and goroutines truly shine. These rely on a combination of locks and semaphores to put them to “sleep” while waiting for an input. This frees the CPU resources utilized by the virtual thread until it receives an interrupt that awakens it. A thread or a goroutine awaiting an interrupt is similar to a callback waiting to be invoked on the arrival of an input — the interrupt signal originates when unlocking a mutex it was waiting on (or when a semaphore becomes zero).

Ideally, we would expect an application designed to run in a multi-threaded environment to scale with the increase in the number of processor cores. But not all applications scale well even if it is built to run multiple tasks on separate goroutines.

Certain blocks of code might need to synchronize with locks or atomic instructions, turning those parts into a forcefully synchronized execution blocks. An example for this could be a central cache which is accessible by each goroutine. These lead to lock contention preventing the application from improving in performance with additional cores. Or worse, these could lead to a degradation in performance. Atomic instructions also come with an overhead but it is much smaller than what is caused by locks.

Hardware level atomic instructions used to access the memory do not always guarantee reading the latest value. This is because, each processor core maintains a local cache which could be outdated. To avoid this problem, atomic write operations are usually followed by instructions forcing each cache to update. And to top that, it must also prevent [memory reordering](https://en.cppreference.com/w/cpp/atomic/memory_order) which is in place (both at the hardware and software level) to improve performance.

The `map` structure is so widely used that almost every practical application rely on a it in their code. And to use one in a concurrent application reads and writes to it must be synchronized with `_sync.RWMutex_` in the Go world. Doing so leads to the excessive use of `atomic.AddInt32(...)` which leads to frequent cache-contention, forcing cache update and memory ordering. This reduces performance.

`_sync.Map_` uses a combination of both the atomic instructions and locks, but ensures the path to the read operations are as short as possible, with just one atomic load operation for each call to `Load(...)` in most cases. Atomic store instructions are usually the ones that force the caches (of each core) to be updated, whereas, atomic load might just have to enforce memory ordering along with ensuring its atomicity. And `atomic.AddInt32(...)` is worse, as its contention with other atomic updates to the same variable will cause it to busy wait until the update which relies on a compare-and-swap instruction succeeds.

An example of using `sync.RWMutex` to synchronize access to the map: [https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/map\_reference\_test.go#L25](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/map_reference_test.go#L25)

For convenience, the above code is mirrored here:

Source 1: RWMutexMap

When performance is critical we can address this either by reducing the frequency of acquiring the same locks in parallel (thus, reducing the frequency of lock contention) or by entirely replacing locks with atomic instructions like atomic-load, atomic-store and atomic-compare-and-swap. Atomic operations are also not a silver bullet, as state updates which rely on atomic-compare-and-swap run in an infinite loop until the update succeeds. The updates usually never happen when there is a contention, therefore leading them to busy wait when there are a lot of concurrent updates.

Most applications usually rely on a combination of both. Even those applications try to choose a more faster alternative, like reducing the number of calls to atomic-compare-and-swap instructions spinning in a loop.

`[sync.RWMutex](https://github.com/golang/go/blob/912f0750472dd4f674b69ca1616bfaf377af1805/src/sync/rwmutex.go#L28)` uses a combination of semaphores along with two additional variables `readerCount` and `readerWait` to keep track on the number of read accesses.

To understand why we need to go for `sync.Map` when our environment has too many processor cores, instead of using the built-in `map` guarded by `sync.RWMutex`, we must dive into [how](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba) `[sync.RWMutex](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba)` [works internally.](https://sreramk.medium.com/go-sync-rwmutex-internals-and-usage-explained-9eb15865bba)

`sync.Map` contains these following methods, which are self explanatory (taken from [here](https://golang.org/pkg/sync/#Map))

Source 2: sync.Map methods documentation

Before going ahead trying to understand how `sync.Map` works, it is important to understand [why do we absolutely need the methods](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa) `[LoadAndDelete(...)](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa)` [and](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa) `[LoadOrStore(...)](https://sreramk.medium.com/go-why-does-sync-map-97342f12b3fa)`.

`sync.Map` maintains two `map` objects at any given time, one for the reads and one for the writes. The read map is partially immutable, whereas the write map is fully mutable.

At any given time, the readable map is not expected to be fully updated, whereas, the writable map is assumed to be fully updated representing the store’s accurate state (while it was not set to `nil`). Whenever there is a key miss in the read-map, it is read from the write-map with a `sync.Mutex` lock held.

While deleting a key, the key could either be present only in the writable map or it could be present in the writable map and the readable map. If it was present only in writable map, it is completely removed with the built-in `delete` operation. But if it was present in both the writable map and the readable map, it is only set to `nil` (note, the update operation of setting the field to `nil` is reflected within the read-map and the write-map simultaneously, as they point to the same `entry` object; more on this later).

Every access to the writable map is guarded by `sync.Mutex` and they also have the overhead of atomic instructions. Therefore, it must have an overhead slightly greater than a built-in `map` guarded by `sync.RWMutex`.

So one of the objectives of this implementation should be to reduce the frequency of read-misses. This is done by promoting the writable map as the next readable map (while setting the pointer to the writable map as `nil`) when the number of read misses are larger than the length of the writable map (this length is computed using `len`). The outdated readable map is then discarded.

Upon the first attempt to add a key to the writable map, a new map object is created by copying the contents of the new readable map to the writable map. Immediately after the promotion, the readable map will represent the store’s most accurate state. But after being promoted it becomes “immutable” and there will not be any new keys added to it. Therefore, adding additional keys to `sync.Map` will make the readable map outdated.

There are two different ways in which an update happens. If the key being added (with the `sync.Map`’s `Store(...)` or `LoadOrStore(…)` operation) already exists in the readable map, the value associated with the key in the readable map is updated atomically (note: the changes done to the value field this way will be immediately reflected on the writable map as well. How this happens will be explained later in this article). If the key only exists in the writable map or if the key does not exist at all, the update is made only in the writable region with a `sync.Mutex` lock held.

## Where is sync.Map used?

`sync.Map` was originally created to reduce the overhead incurred by the Go’s standard library packages that have been using a `map` guarded by `sync.RWMutex`. So the Go authors discovered that having a store like `sync.Map` does not increase the memory overhead too much (an alternate memory intensive solution is to have a separate copy of the map for each goroutine used, but have them updated synchronously) while also improving the performance in a multi-core environment. Therefore, the original purpose of `sync.Map` was to address the [problems within the standard packages](https://github.com/golang/go/issues/40999#issuecomment-679449778), but it was still made public in hope that people find it useful.

The documentation does not really go into the details of where exactly will `sync.Map` be of most use. [Benchmarking](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c) `[sync.Map](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c)` has revealed there is a gain in efficiency over the use of `map` guarded by `sync.RWMutex` only when it is run on a system with more than 4 cores. And the most ideal use case for `sync.Map` is having it used as cache that witnesses a frequent access to disjoint keys; or having it extensively read from the same set of keys.

The keys that are newly added are likely to stay in the writable map, while the keys that were accessed most frequently are likely to stay in the readable map. `sync.Map` will perform the least when a finite set of keys are being added, read from and deleted where each operation happens with the same frequency.This happens when you do not let the keys in the write-map to be promoted by frequently adding and deleting them.In this situation, we might be better off using `map` with `sync.RWMutex` or `sync.Mutex` (The exact choice for a concurrent hash-map is usually decided through benchmarking)

Whenever a key is deleted in `sync.Map` it only has its associated value field marked as `[nil](https://github.com/golang/go/blob/21a04e33353316635b5f3351e807916f3bb1e844/src/sync/map.go#L297)` but the key isn’t really removed until the first write after the writable-map was promoted as the readable-map. This leads to a memory overhead. But this overhead is only temporary, as with the next promotion cycle, the overhead comes down.

`[sync.map](https://github.com/golang/go/blob/21a04e33353316635b5f3351e807916f3bb1e844/src/sync/map.go#L12)`[’s structure is given here for convenience:](https://github.com/golang/go/blob/21a04e33353316635b5f3351e807916f3bb1e844/src/sync/map.go#L12)

source 3: Map structure

As we can see, `sync.Map` has one `dirty` map store and one `atomic.Value` field that is used for storing the “clean” `read` map. All accesses to the `dirty` map are always guarded by `mu`. Before we look at how each individual methods work we must understand the working of `sync.Map` and its design ideas from a higher level.

The `[entry](https://github.com/golang/go/blob/c1cc9f9c3d5ed789a080ef9f8dd9c11eca7e2026/src/sync/map.go#L73)` structure is vital for the function of `sync.Map` .

Source 4: entry structure

The `entry` structure acts as a “container” or a “box” that holds the value being stored associated with the key. Instead of directly storing a value with `m[key] = value`, you have the `value` encapsulated within a convenient container of type `entry`. The address of `entry` is then stored into the `map` object associated to the key.

At any given time, `entry` is assumed to satisfy one of these three properties:

1.  It holds a valid value: `p != expunged && p != nil` . `expunged` (which means removed permanently) is defined as `var expunged = unsafe.Pointer(new(interface{}))`, which is an arbitrary global value set only once. It does not take on any value. It is there just to distinguish the “expunged” value from every other `nil` and non-`nil` value in arbitrary `entry` fields.
2.  It holds `nil`.
3.  It holds `expunged` (we’ll soon go into the details of how `nil` state differs from the `expunged` state).

It is extremely convenient to wrap up the pointer under a structure like `entry`. If you are changing the state of an `entry`, you can expect it to be instantly updated at every other location that has the pointer to the `entry` object.

So, if you share the address to `entry` between the readable map and the writable map, updating the readable map’s `entry` will reflect the changes on the writable map as well and visa-verse (note that, in both source 3 and source 5 the map is defined as `map[inerface{}]*entry` , where the key is an `interface{}` and the entry is stored as a pointer).

Source 5: readOnly structure

The `read` field of `sync.Map` structure is an `atomic.Value` field, which holds a reference to `readOnly`(source 5). This structure contains another field `amended` which is true when the `sync.Map` object was extended by adding a new key and a promotion did not happen yet since the new key was added. In this case, the key goes into the writable map without there being a record of it in the readable map. The `amended` field being true signifies this specific state where the `dirty` map contains a record `read` doesn’t.

## How does load, store and delete work at a high level?

The read part of these operations are usually inexpensive (relatively). This is because, the pointer to a `readOnly` object is retrieved from the `atomic.Value` field and the value associated with the key is quickly searched for. If the value exists, it gets returned.

If it doesn’t exist, then it is likely to have been added more recently. In which case the `dirty` field needs to be checked (with `mu` held). If the key exists in the `dirty` field, it is retrieved as the result.

The read operations have a slow path in this implementation. With each miss in the `readOnly` object, the value of the field `misses` is atomically incremented. When the `misses` count is larger than the size of `dirty`, it gets promoted (directly moving its pointer) to the `read` field, by creating a new `readOnly` object to contain it. The previous value of the `read` field is discarded when this happens.

All operations involving the `dirty` map are carried out within a region guarded by the mutex `mu` .

When record is being stored into `sync.Map`, it is handled in one of these three ways:

1.  Modifying the instance of `entry` returned by `(read.Load().(readOnly))[key]` if it was successfully retrieved. The modification is done by adding the value to the `entry` field.
2.  Modifying the instance of `entry` returned by `dirty[key]`, if it was retrieved successfully. The modification is done by replacing the value in the `entry` object (stored inside the `read` object which is of type `atomic.Value`). This is done if step one had failed.
3.  If `dirty` is `nil` (which will be the case when `read.amended` is false), create a new `map` and copy everything in the read only map to it. The record is then just added to `dirty` (notice that with the fields being copied, the address to the `entry` objects are the ones being copied. Therefore, each key present in the read map and the write map point to the exact same `entry` object.)

In case of delete, if the key was present in the `readOnly` object in `read`, its `entry` instance is atomically updated to be `nil`. This operation does not need `mu` to be acquired. But `mu` will need to be acquired when the key is searched for in the `dirty` field. If the key is not present in `read`, it is looked for in `dirty` while being guarded by `mu`. If it is found only in `dirty`, the `entry` object is directly removed with the built-in `delete` function.

Therefore the read, write and delete operations will be fully atomic when the key is found in the `readOnly` instance held by the `read` field. Whereas, the other cases that needs to go though `dirty` will be guarded by `mu`.

And any modification done to the `entry` field will be reflected at both the `readOnly` object in `read` and the `dirty` map. Because, whenever a new `map[interface{}]*entry` object is created from copying the `readOnly` instance, only the address of the `entry` objects are copied.

## The difference between storing `expunged` and just simply `nil`

The following properties are always said to hold:

1.  `entry` holds a pointer in it. At any given time, its pointer can hold `expunged`, `nil` or a pointer to the interface holding a valid value provided through the `Store(…)` or `LoadOrStore(…)` methods by the user.
2.  If `entry` holds `nil`, it signifies that the value associated with the key was deleted by calling `Delete(…)` or `LoadAndDelete(…)` while it was present in the `readOnly` object and the `dirty` map.
3.  If `entry` holds `expunged`, it signifies that a non-`nil` `dirty` map exists which does not have the same key that associates the `entry` field.

When `misses > len(dirty)` (`misses` is a field in `sync.Map` structure), the `dirty` map is copied into the `read` field, which is of type `atomic.Value`. The code for doing that is: `m.read.Store(readOnly{m: m.dirty})` where, the `Store` here is an atomic store operation.

The `readOnly` object has two fields in it. One for the map, and the other for the `amended` variable which says if a new key was added to the `sync.Map` object after a promotion. The first attempt to insert a key following a promotion causes the map inside the `readOnly` object to be copied to the `dirty` map key by key. Every key that associates to an `entry` object storing `nil` is not copied into the `dirty` map and has its `entry` object updated to contain `expunged`.

Therefore, `expunged` keys are only present in the “clean” map without having them copied into the new `dirty` map. This is done with an assumption that the key that was deleted once is not likely to be added again.

There are two separate unexported methods,`missLocked()`and `dirtyLocked()` defined for `sync.Map`. These are respectively responsible for,

1.  promoting the `dirty` map (which also sets the `dirty` field in `sync.Map` to `nil`)
2.  copying the key-value pairs in the `readOnly` object (which has its `amended` field set to `false`) to the newly created `dirty` map object (by ignoring the keys that are associated with `entry` object set to `nil` and making them `expunged`; as they are not copied into the `dirty` map).

`missLocked()` is called each time there is a key miss while reading the `readOnly` object. The call could be triggered by every exported method defined in `sync.Map` other than `Range(…)`, as they all try retrieving the stored record first and accept a `key` as an argument. `missLocked()` only promotes the `dirty` map when the size of it is smaller than the number of misses.

## `Store(key, value interface{})`:

Source 6: the Store method

Let’s break the above code into four parts (the region containing each part is marked above). The first part attempts to retrieve the value from `read`, which is a `sync.Value` field containing the `readOnly` object. If the read was successful, it attempts to store the value into the `entry` object atomically. Source 7 shows how it is done.

The atomic update in the `tryStore(…)` operation contains an infinite loop that terminates when the value was previously `expunged`. This is because, an `expunged` value signifies that there isn’t a copy of the same key field in the `dirty` map, while there is one in the `readOnly` object. Therefore, updating the pointer in this case will not reflect on the `dirty` map, which is always supposed to contain the fully updated and accurate state of `sync.Map`. Except for the case where it was just recently promoted. In which case, the `dirty` field will temporary hold `nil` until the first attempted write to it since it was set to `nil`.

The infinite loop in source 7 is there to cause the function to stay in a “busy wait” state until the update succeeds. Atomic compare and swap operation accepts three arguments. The pointer to be modified, the likely old value contained in the pointer and the new value. The new value is stored in the pointer if the old value was the same as the original value held in the pointer.

In source 7, the pointer is first atomically loaded from the `entry` object and it is checked if it was `expunged`. If it was, then `tryStore` fails because, an `expunged` entry signifies that the `entry` object is not present in the `dirty` map associated with its key. Therefore, storing the value into the `entry` object retrieved from the `read` map will no longer be useful (as the modifications will not reflect on the `dirty` map).

The atomic-compare-and-swap instruction in line 11 of source 7 is responsible for adding the new value, if `e.p` (which is the pointer stored inside the `entry` object) was same as the value of `p` previously read at line 8 of source 7. If a method running in a different goroutine had atomically modified the underlying value of `p` before the execution of line 11, the compare-and-swap-pointer operation fails causing the loop to continue. If `p` was modified to hold `expunged`, then the loop breaks because of the conditional branch at line 8.

This infinite loop will go on until `e.p` was not modified by a different goroutine while statements from line 7 to 11 were being executed. This is why contention will be more heavy on the CPU when we use atomic instructions instead of locks that put goroutines to sleep until they are needed to run again. Atomic instructions cause a “busy wait” to occur until there are no contentions.

Source 7: the tryStore method

The remaining parts 2, 3 and 4 (in Source 6) all run within a region guarded by the `mu` lock. Part 1 returns when the key was present in the `readOnly` object and the `tryStore` operation (explained above) was successful.

But Part 1 failing signifies that either the key was not present in the `readOnly` object or it was expunged. Proceeding to Part 2, the read value is reloaded within the locked region again.

This is done because the pointer to the `readOnly` object stored within `atomic.Value` could have been replaced following a call to `missLocked()` executed from a different goroutine, which will also be executed after acquiring `mu`(_Note, every function with the postfix “Locked” is supposed to be executed within the locked region guarded by_ `_mu_`). But because part 1 does not acquire `mu` the value retrieved at line 6 in source 6 can become outdated.

In Part 2 the `entry` pointer is retrieved again. Now, a call to `e.unexpungeLocked()` checks if the value stored in the entry was `expunged` or not:

1.  If it was `nil` or anything else, it indicates that the same key must also be present in the `dirty` map.
2.  But if it is `expunged`, it signifies that the key is not present in the `dirty` map and it must be added to it as well. Therefore, the pointer to the `entry` object retrieved by `read.m[key]` is stored into `dirty` being associated with its appropriate key. Because the same pointer is used, any changes to the underlying `entry` object reflects in both the “clean” map and the “dirty” map.

A call to `unexpungeLocked()` executes the statement `return atomic.CompareAndSwapPointer(&e.p, expunged, nil)` (which is the only statement in its definition). This ensures that `e.p` is only updated when it is `expunged`. You don’t have to busy wait here to allow the update to happen. This is because the “old pointer” argument of `CompareAndSwapPointer(…)` is a constant (`expunged`) and it can never change.

Both `tryStore()` and `unexpungeLocked()` can update `e.p` though they aren’t mutually guarded by the same mutex. Thus they could potentially attempt to update `e.p` simultaneously from different goroutines. But this does not become a race condition as `unexpungeLocked()` is supposed to modify the `entry` object only when its pointer (the `p` field of the entry object) was set to `expunged`.

`unexpungeLocked()` running on a different goroutine could execute its `CompareAndSwapPointer(…)` statement anywhere between lines 7 and 11 in Source 7. If it was executed between these lines, the value of the underlying pointer will have been changed before the compare-and-swap operation at line 11 which will cause the loop to fail and repeat again. Therefore, a successful execution of the region between the lines 7 and 11 in Source 7 cannot occur if,

1.  a different goroutine executes the same region trying to modify the same underlying pointer or,
2.  if `unexpungeLocked()` was concurrently executed within the same time frame.

In Part 2, the value is finally stored into the `entry` object by a call to `storeLocked(...)`. Now moving on to Part 3. The condition in Part 2 fails on two possibilities (note, we have already ruled out the possibility that the key could be present in the `readOnly` object):

1.  The key is present in the `dirty` map.
2.  The key is absent in the `dirty` map.

Part 3 handles the first case. It simply stores the record into the `entry` object. Now part 4 handles these following two possibilities:

1.  The `dirty` map is `nil`
2.  The `dirty` map is not `nil`

If the `dirty` map was `nil`, it must be created by copying the entries from `readOnly` object before the new key is added. Otherwise, the new key is added directly without any changes.

The `dirty` map being `nil` also signifies that no new entries were added into the `sync.Map` object ever since its `dirty` map was promoted as the “clean” map. Therefore, the field `read.amended` in source 5 is supposed to be `false` if `dirty` was `nil`.

While promoting a `dirty` map to a clean map (this happens with a call to `missLocked()` defined within the structure `sync.Map`; it is only executed when `Load(…)`, `LoadOrStore(…)`, `LoadAndDelete(…)` or `Delete(…)` are called) it just gets directly copied into the “clean” map. When this happens, the users are free to delete the keys in the clean map concurrently (which will just be an atomic operation) and re-add them. But with the first attempt to add a new key into the map after the promotion, the contents of the clean map are copied into the dirty map. But while this happens, the keys with `nil` in their `entry` object’s pointer fields are ignored and within the “clean” map, they are atomically changed to `expunged`.

In part 4, a call to `dirtyLocked()` is made to populate the `dirty` map. The [source for](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L362) `[dirtyLocked()](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L362)` is given below:

Source 8: dirtyLocked() — creates a new map by copying contents of the readable map and stores it in `dirty`

`tryExpungeLocked()` is defined below:

Source 9: `tryExpungeLocked()` — updates the entry’s pointer with expunged if it was `nil`

Like `tryStore(…)` defined in source 7, source 8 also relies on a completely atomic operation in setting `expunged` to the pointer. As we can see in Source 8, the creation of the new `dirty` map and the eventual update only happens when `dirty` is `nil` . And the line 9 of source 8 makes it clear that only if `tryExpungeLocked()` fails, the key is added into the `dirty` map.

`tryExpungeLocked()` ensures that the pointer field in the `entry` object is set to `expunged` if it was originally `nil` (see line 4 of source 9). If the pointer was modified before the compare-and-swap operation, the swap fails and the loop exits. This loop continues until `p` is not `nil`. This could change from being `nil` before the compare-and-swap is executed; for example, it could be replaced by a goroutine executing a call to the `Store(...)` method in the `sync.Map` structure.

Following the call to `dirtyLocked()`, the read map is marked as “amended”. This expresses that the map in the `read` field is outdated.

## `Load(key interface{}) (value interface{}, ok bool) :`

_Note: if you haven’t read the_ `_Store(…)_` _part, I recommend you to do so. The line of reasoning I used there also applies here and every other methods that are explained below. Therefore I won’t be reexplaining them here._

Source 10: Load

1.  Retrieves the `readOnly` object atomically.
2.  Checks if the key along with its `entry` is present in it
3.  If it succeeds, return the result. At this point, no locks were used.
4.  If it fails, and if `read.amended` was true (which signifies that the `dirty` field is not `nil`), the value is read from the writable map (which is the `dirty` map).
5.  Step 4 runs within a locked region guarded by `mu`. The lines 5, 6 and 7 in source 10 are repeated again in the lines 12, 13 and 14; but this is done from within the locked region. This is done because, a new `entry` object could have been added during this time by a different goroutine associated with that key. But all writes synchronize with the lock. Therefore, there won’t be any race conditions here.
6.  If the retrieval through the readable map fails, it is retrieved from the writable map.

## LoadOrStore(key, value interface{}) (actual interface{}, loaded bool)

The source for `LoadOrStore(…)` can be found [here](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L200).

For the most part `LoadOrStore(…)` is similar to `Load(…)` except that it uses `e.tryLoadOrStore(value)` in place of `e.tryLoad()` and also makes a call to `missLocked(…)` if the key was absent in the readable map.

The implementation of `tryLoadOrStore(…)` is similar to any atomic update strategy using the compare-and-swap instruction. This method only succeeds when the `entry` object holds any pointer other than `expunged` (which includes `nil`).

## `LoadAndDelete(key interface{}) (value interface{}, loaded bool):`

The [strategy followed](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L269) isn’t very unique from the ones mentioned above. First read is attempted with the `readOnly` object. If it succeeds, `e.delete()` is called which atomically sets the `entry` object’s pointer to `nil`. If it fails, the `entry` object is retrieved from the `dirty` map with within a locked region. The call to `e.delete()` is made if the `dirty` map had the key.

The key is not removed at this point. It is just set to `nil`.

## `Delete()(value interface{}, ok bool):`

This just calls `LoadAndDelete(…)`

## `Range(f func(key, value interface{}) bool)`

1.  First tries retrieving the key from the `readOnly` object
2.  If it succeeds, the range loop is computed immediately (from line 341 to 349 in the [source](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L341)) with the returned object.
3.  If it fails, a check at [line 325](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L325) sees if the `sync.Map` object was “amended” by extending it with an additional key after the most recent `dirty` map promotion.
4.  If the check at [line 325](https://github.com/golang/go/blob/aa4e0f528e1e018e2847decb549cfc5ac07ecf20/src/sync/map.go#L325) succeeds, the `dirty` map is immediately promoted. This is done because, a range operation is most likely to be O(N) assuming all the keys are visited. Therefore, after promoting the `dirty` map and setting `dirty` to `nil`, we can expect the next following store operation (`Store(…)` or `LoadOrStore(…)` that introduces a new key) to follow the slow path of creating a new `dirty` map which is an O(N) operation. But having the call to `Range(…)` which is itself an O(N) operation, to precede the O(N) operation of creating a new `dirty` map ensures that an O(N) operation (of creating a new `dirty` map) only follows another O(N) operation. Thus we can amortize them as one O(N) operation
5.  Following step 4, the range operation is performed.

[This article](https://medium.com/@deckarep/the-new-kid-in-town-gos-sync-map-de24a6bf7c2c) (The new kid in town — Go’s sync.Map by [Ralph Caraveo III](https://medium.com/@deckarep)) goes into a great detail of how a simple `sync.RWMutex` guarded map is way better than `sync.Map` when we are using only a few processor cores. The benchmarks in the article shows that beyond 4 cores, the performance of `sync.Map` seemed to be significantly higher than a `map` guarded by `sync.RWMutex`.

It it therefore necessary to build a prototype that can later be benchmarked to check its relative performance with each variant of its implementation. This can help us choose which variant will be most appropriate for each situation. This shares similarity with how deep neural networks work. In DNNs we have a loss function the value of which we try to minimize. The loss function in this case expresses the objective of the neural network model.

The same way, applications must view their test cases and benchmarks together as a “loss function” that expresses the objective of the entire project. If you measure the performance, in time you can improve it. Because, **you cannot adjust what you don’t measure.**

Premature optimization really becomes a problem when what you optimize does not improve the overall performance of your application, or the change in performance is just too negligibly small.

**Let’s see an example:**

Assume you have an application which is supposed to receive profile info along with a specific meta-data through API calls, transform it to a different format and send them over to a different microservice. Let’s say you write a procedure to filter a specific pattern in the data being read — assume you receive customer profile data and your application is supposed to filter profiles that are older than 8 years and send it’s ID over to a different message queue while also storing the profile in a cache.

Should you use `sync.Map` or a map guarded by `sync.RWMutex`?

Assume that out of every 100 profile data received by the application, one of them is 8 years old. So should you really bother thinking about which map to use? Either of those choices make no difference here because, the overall performance of the system is usually not impaired by your choice. Maybe because this cache isn’t the slowest step.

When we work as a team, it is not uncommon to have different people handle different tasks. So you won’t benefit from having people make their part of the code run faster through testing them with localized benchmarks. The benchmarks must reflect the overall objective of the application.

Any amount of work that goes into improving performance of a part of the code base will be wasted if it was not really the bottle neck. But things are a bit different when you are writing a library where most functions are exposed to the user. Writing benchmarks at the application level (including the exposed APIs) help set the objective the team wishes to achieve.

If reading this article had given you the impression that the Go authors were optimizing prematurely, I have to say, that’s not true. Go is a general purpose language and I am sure even its authors cannot fully anticipate all of its use cases. But it is always possible for them to figure out the most common use cases and optimize for that. Their priorities should be tweaking the parts that have the most impact in their ecosystem. For this, they definitely need a very rigid feedback loop from all their users. Their main focus should be on fixing the pain points.

For the reasons I mentioned before it is not really needed to improve performance within an application beyond a point. That said, if you do want to make your application super fast for whatever reason, then read on!

SQL database systems do everything in their power to make things run faster. They do this by implementing multiple “strategies” for the same task. When you query for an unindexed record you will observe the worse-case performance. This happens when the query engine falls back to using brute force search.

But if you had an index built, the query engine has a chance to choose a better algorithm (of just referring to the index) for improving the query execution time. The “query planning” phase takes care of determining the right strategy to use. If you have multiple indexes built, you are essentially giving the query engine too many options and strategies to choose from. In this case, it may even rely on execution statistics to choose the best strategy to use internally.

Likewise, if you want a _super fast_ concurrent map the following might help with that:

Source 11: super efficient sync map

The strategy pattern can be used almost everywhere giving different parts of your application a huge control over its performance. You could also write modules for noting down the statistics and devising the right strategy for your application more like how the query planner does it.

This way, your application will use a different set of strategy for each environment! This will be really useful if your customers are concerned for performance and you are supporting a wide range of platforms. Or, it will be most useful if you are building a language.

That said, premature optimization can always be avoided if you are clear about your team’s objectives. Without rigid objectives, you cannot really know what counts as “optimization” and what doesn’t.