# 深入理解 golang 的互斥锁

- 原文地址：<https://levelup.gitconnected.com/deep-understanding-of-golang-mutex-9964b02c56e9>
- 原文作者：Dwen
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2022/w47_Deep_Understanding_of_Golang_Mutex.md
- 译者：[小超人](https://github.com/focozz)
- 校对：[]()

> How to implement Golang Mutex
> 如何实施 Golang Mutex

![.](../static/images/2022/w47_Deep_Understanding_of_Golang_Mutex/1_BWLrf8Kh0LvhK9nuqnH9jg.jpeg)

Photo by [Daniil Silantev](https://unsplash.com/@betagamma?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText) on [Unsplash](https://unsplash.com/s/photos/home?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText)

在开始之前，我们需要知道锁实现的几种方式。

**\# 信号量**
操作系统中有 P 和 V 操作。P 操作是将信号量值减去 1，V 操作是将信号量值增加 1.因此信号量的操作模式为：

- 初始化，给它一个非负整数值。
- 在程序试图进入临界区之前需要先运行 P 操作，然后会有两种情况。

2. 当信号量 S 减少到负值时，该过程将被阻止并且无法继续。这个时候，进程会被阻塞。
3. 当信号量 S 不为负时，进程可以进入临界区。

- 在程序离开临界区时，需要执行 V 操作。当信号量 S 不是为负时，之前被阻止的其他进程将允许进临界区。

**\# 信号量和锁**
尽管信号量和锁看起来相似，例如，当信号量为 1 时，实现了互斥锁，但实际上，它们具有不同的含义。

锁用于保护临界资源，例如读和写不能同时执行场景。

信号量是用于确保进程 (线程或 goroutine) 被调度。比如，三个进程共同计算 `c = a+b`。首先，`a+b` 的计算和赋值操作不能同时执行。其次，必须确保首先执行 `a+b`。c 在赋值之后执行，因此这个位置需要以信号量的形式执行。

此外，可以通过信号量实现锁，然后 goroutine 可以根据规则阻塞和唤醒锁；也可以通过自旋的方式实现锁，goroutine 将持有 CPU，直到解锁。

这两种方式之间的区别是是否需要调度 goroutine，但是从本质上讲，锁是为了确保不会错误地访问临界资源。

**\# 自旋锁**
CAS 理论是一种自旋锁。

在同一时间只有一个线程获得锁，而没有获得锁的线程通常有两种处理方式:

- 一直循环等待，以确定资源是否释放了锁。这种锁称为自旋锁，它不会阻塞线程(NON-BLOCKING)。
- 一直阻塞，等待重新调度，这种是实现方式是一个互斥锁。

自旋锁的原理相对简单。如果持有锁的线程可以在短时间内释放锁定资源，那么等待锁的其他线程不需要在内核态和用户态之间切换来回切换阻止状态，他们只需要通过自旋的方式等一会，等待持有锁的线程释放锁，然后获取锁，这种方式避免用户进程在内核切换。

但如果长时间未释放锁，那么自旋锁的开销会非常大，它会阻止其他线程的运行和调度。

线程持有锁的时间越长，持有锁的线程被 OS 调度中断的风险就越大。

如果发生终端，其他线程将保持自旋状态(反复尝试获取锁)，而持有锁的线程不打算释放锁，这将导致无限延迟，直到持有锁的线程完成并释放锁。

解决上述情况的一个好方法是为自旋锁定设置一个自旋时间，并在时间一到就释放自旋锁。

**\# #悲观锁定和乐观锁定**
悲观锁定是一种悲观思维。它总是认为最坏的情况可能会发生。它认为这些数据很可能被其他人修改过。无论是读还是写，悲观锁都是在执行操作之前锁定的。

乐观锁定的思想与悲观锁定的思想相反。它始终认为资源和数据不会被别人修改，所以读取不会被锁定，但是乐观锁定会在写操作时确定当前数据是否被修改过。

乐观锁定的实现方案主要包括 CAS 和版本号机制。乐观锁定适用于多读场景这可以提高吞吐量。

CAS 是一个著名的基于比较和交换无锁算法。

也就是在不使用锁的情况下实现多个线程之间的变量同步，(即在不阻塞线程的情况下实现变量同步)，所以又称非阻塞同步。

CAS 涉及三种关系: 指向内存区域的指针 V、旧值 a 和要写入的新值 B。

由 CAS 实现的乐观锁将带来 ABA 问题。同时，整个乐观锁会在数据不一致的情况下触发等待和重试机制，这对性能有很大的影响。

版本号机制通过版本的值实现版本控制。

有了以上的基础知识，我们就可以开始分析 golang 是如何实现互斥锁的了。

Golang 的 Mutex 实现一直在改进，到目前为止，主要经历了 4 个版本:

- V1:实现简单
- V2:新的 goroutine 参加锁的竞争
- V3：给新的 goroutines 更多参与竞争的机会
- V4：解决老 goroutine 饥饿的问题

每一次改进都是为了提高系统的整体性能。这个升级是渐进的、持续的，因此有必要从 V1 版本开始慢慢地看 Mutex 的演变过程。

**V1: 实现简单**
在 V1 版本中，互斥的完整源代码如下。[commit](https://github.com/golang/go/blob/d90e7cbac65c5792ce312ee82fbe03a5dfc98c6f/src/pkg/sync/mutex.go)

核心代码如下:

```golang

func cas(val *int32, old, new int32) bool
func semacquire(*int32)
func semrelease(*int32)
// The structure of the mutex, containing two fields
type Mutex struct {
  key int32 // Indication of whether the lock is held
  sema int32 // Semaphore dedicated to block/wake up goroutine
}
// Guaranteed to successfully increment the value of delta on val
func xadd(val *int32, delta int32) (new int32) {
    for {
        v := *val
        if cas(val, v, v+delta) {
            return v + delta
     }
    }
    panic("unreached")
}
// request lock
func (m *Mutex) Lock() {
    if xadd(&m.key, 1) == 1 { // Add 1 to the ID, if it is equal to 1, the lock is successfully acquired
    return
}
    semacquire(&m.sema) // Otherwise block waiting
}
func (m *Mutex) Unlock() {
    if xadd(&m.key, -1) == 0 { // Subtract 1 from the flag, if equal to 0, there are no other waiters
return
}
    semrelease(&m.sema) // Wake up other blocked goroutines
}
```

[code here](https://gist.github.com/tengergou/3851ef5ae21e4530272618ec096990ee#file-20220921-1-go)

首先，互斥锁的结构非常简单，包括两个字段，`key` 和 sema。

`key` 表示有几个 gorutines 正在使用或准备使用该锁。如果 `key==0`，表示当前互斥锁已解锁，否则，`key>0` 表示当前互斥锁已锁定。

`sema` 是实际导致 goroutine 阻塞和唤醒的信号量。

`xadd` 是一个基于 cas 的加减法函数。

Lock 和 Unlock 是锁定当前互斥锁的核心函数，但逻辑非常简单。

`Unlock` 使用 xadd 方法对 `key` 进行 -1 操作。如果结果不是 0，则意味着 goroutine 当前正在等待，需要调用 `semrelease` 来唤醒 goroutine。

想象一下这样一个场景: 被阻塞的 goroutine(命名为 g1)不能占用 CPU，因此需要在 g1 被唤醒后执行上下文切换。如果此时出现一个新的 goroutine (g2)，它就拥有 CPU 资源。

如果把锁给 g2，那么它可以立即执行并返回结果(而不是等待 g1 的上下文切换)，这样整体效率就可以提高到更高的水平。

**V2:新 goroutine 参加锁竞赛.**

完整的源代码地址 [https://github.com/golang/go/blob/weekly.2011-07-07/src/pkg/sync/mutex.go](https://github.com/golang/go/blob/weekly.2011-07-07/src/pkg/sync/mutex.go)

在 V2 版本中，核心特性是 goroutine 在被唤醒后不会立即执行任务，而是重复抢占锁的过程，以便新的 goroutine 有机会获得锁，这就是给后来者机会。

互斥锁结构和常量的定义如下:

```golang
// A Mutex is a mutual exclusion lock.
// Mutexes can be created as part of other structures;
// the zero value for a Mutex is an unlocked mutex.
type Mutex struct {
    state int32
    sema  uint32
}

const (
    mutexLocked = 1 << iota // mutex is locked
    mutexWoken
    mutexWaiterShift = iota
)
```

[code here](https://gist.github.com/tengergou/3a4613c2a729f06f331c1182ba250bb0#file-20220921-2-go)

虽然互斥锁结构的定义基本不变，但从 V1 的 `key` 到 V2 的 `state`，它们的内部结构却有很大的不同。

第 0 位表示锁定状态(L)，即 0 表示解锁，1 表示锁定; 第 1 位表示唤醒状态(W)，第 2 位到第 31 位表示阻塞等待的计数。

![.](../static/images/2022/w47_Deep_Understanding_of_Golang_Mutex/1__aGSxVA7YJpaUsb7fmQaMA.png)

`mutexLocked` 的值是 0x1, `mutexawake` 的值是 0x2, `mutexWaiterShift` 的值是 0x2, `mutexWaiterShift` 表示任何表示阻塞等待数量的数组都需要左移两位。

V2 版本的主要在于 `Lock` 方法的改进，代码如下:

```golang
// Lock locks m.
// If the lock is already in use, the calling goroutine
// blocks until the mutex is available.
func (m *Mutex) Lock() {
 // Fast path: grab unlocked mutex.
 if atomic.CompareAndSwapInt32(&m.state, 0, mutexLocked) {
  return
 }

 awoke := false
 for {
  old := m.state
  new := old | mutexLocked
  if old&mutexLocked != 0 {
   new = old + 1<<mutexWaiterShift
  }
  if awoke {
   // The goroutine has been woken from sleep,
   // so we need to reset the flag in either case.
   new &^= mutexWoken
  }
  if atomic.CompareAndSwapInt32(&m.state, old, new) {
   if old&mutexLocked == 0 {
    break
   }
   runtime.Semacquire(&m.sema)
   awoke = true
  }
 }
}
```

[code here](https://gist.github.com/tengergou/77d6f4ab3acf0a951114fe045e1429a2#file-20220921-3-go)

第 2 行和第 4 行中的代码逻辑应用于解锁状态，goroutine 通过 CAS 将 L 位从 0 设置为 1 获得锁。

此时不存在任何争用，因此获取锁几乎不需要花费任何成本。

然后，goroutine 进入一个循环，其中 CAS 方法可确保正确叠加新状态。

- 尝试获得锁。
- 尝试将等待锁的数量增加 1。

由于更改不是原子的，它可能会导致旧 `state` 的值变得无效。

同样，即使当前状态被锁定，由于等待者的数量，旧状态也将过时。

因此，您需要继续通过循环获得新的旧状态。

在旧状态未过时并覆盖新状态后，进入真正的锁定步骤。

如果旧状态未解锁，则直接获得锁，否则，通过信号量机制阻塞当前 goroutine。

与 V1 不同的是，当前进程在被唤醒后，仍然会陷入 for 循环再次获取锁，这主要是给新的 goroutine 机会

- 如果旧的 goroutine 在上下文切换期间有一个新的 goroutine，锁将被赋予新的 goroutine。
- 如果在完成上下文切换后，旧的 goroutine 仍然没有新的 goroutine，那么锁将被交给旧的 goroutine。

Unlock 方法相对简单。代码如下:

```golang
// Unlock unlocks m.
// It is a run-time error if m is not locked on entry to Unlock.
//
// A locked Mutex is not associated with a particular goroutine.
// It is allowed for one goroutine to lock a Mutex and then
// arrange for another goroutine to unlock it.
func (m *Mutex) Unlock() {
 // Fast path: drop lock bit.
 new := atomic.AddInt32(&m.state, -mutexLocked)
 if (new+mutexLocked)&mutexLocked == 0 {
  panic("sync: unlock of unlocked mutex")
 }

 old := new
 for {
  // If there are no waiters or a goroutine has already
  // been woken or grabbed the lock, no need to wake anyone.
  if old>>mutexWaiterShift == 0 || old&(mutexLocked|mutexWoken) != 0 {
   return
  }
  // Grab the right to wake someone.
  new = (old - 1<<mutexWaiterShift) | mutexWoken
  if atomic.CompareAndSwapInt32(&m.state, old, new) {
   runtime.Semrelease(&m.sema)
   return
  }
  old = m.state
  }
}
```

[code here](https://gist.github.com/tengergou/53d9b51646b23369ae9e030631aca9b5#file-20220921-4-go)

有两个主要的解锁逻辑。

- 如果没有等待锁的 goroutine，或者当前系统处于解锁状态，并且有唤醒程序，则直接返回。
- 如果不满足上述要求，则等待的数量将减少 1，队列头部的 goroutine 将通过信号量被唤醒。

**V3：给新的 goroutines 更多机会**
这个版本的优化，关键提交是[https://github.com/golang/go/commit/edcad8639a902741dc49f77d000ed62b0cc6956f](https://github.com/golang/go/commit/edcad8639a902741dc49f77d000ed62b0cc6956f)

在 V2 的基础上，如何进一步提高性能? 在大多数情况下，协程互斥锁定期间的数据操作的耗时是非常低的，这可能比唤醒+切换上下文的耗时更低。

想象一个场景: GoroutineA 拥有 CPU 资源，GoroutineB 位于阻塞队列的头部。然后，当 GoroutineA 试图获取锁时，它发现当前锁已被占用。根据 V2 策略，GoroutineA 立即被阻塞，假设锁此时处于阻塞状态。如果释放，则 GoroutineB 将按计划被唤醒，即整个运行时间包括 GoroutineB 的唤醒+上下文切换时间。

在 V3 版本的实现中，新的 Goroutine (GoroutineA)被允许通过旋转等待一段时间。如果在等待时间内释放锁，新的 Goroutine 立即获取锁资源，避免了旧 Goroutine 唤醒+上下文切换的耗时，提高了整体工作效率。

同样，V3 的改进主要集中在 `Lock` 方法上，代码如下。

```golang

// Lock locks m.
// If the lock is already in use, the calling goroutine
// blocks until the mutex is available.
func (m *Mutex) Lock() {
    // Fast path: grab unlocked mutex.
    if atomic.CompareAndSwapInt32(&m.state, 0, mutexLocked) {
        if raceenabled {
            raceAcquire(unsafe.Pointer(m))
        }
        return
    }

    awoke := false
    iter := 0
    for {
        old := m.state
        new := old | mutexLocked
        if old&mutexLocked != 0 {
            if runtime_canSpin(iter) {
                // Active spinning makes sense.
                // Try to set mutexWoken flag to inform Unlock
                // to not wake other blocked goroutines.
                if !awoke && old&mutexWoken == 0 && old>>mutexWaiterShift != 0 &&
                    atomic.CompareAndSwapInt32(&m.state, old, old|mutexWoken) {
                    awoke = true
                }
                runtime_doSpin()
                iter++
                continue
            }
            new = old + 1<<mutexWaiterShift
        }
        if awoke {
            // The goroutine has been woken from sleep,
            // so we need to reset the flag in either case.
            if new&mutexWoken == 0 {
                panic("sync: inconsistent mutex state")
            }
            new &^= mutexWoken
        }
        if atomic.CompareAndSwapInt32(&m.state, old, new) {
            if old&mutexLocked == 0 {
                break
            }
            runtime_Semacquire(&m.sema)
            awoke = true
            iter = 0
        }
    }

    if raceenabled {
        raceAcquire(unsafe.Pointer(m))
    }
}
```

[code here](https://gist.github.com/tengergou/13e1eff9a75821c5441cab49345e7c5d#file-20220921-5-go)

与 V2 的实现代码相比，它主要集中在第 14-25 行，多了两个自旋锁的核心函数 `runtime_canSpin` 和 `runtime_doSpin`。

第一个是 `runtime_canSpin` 函数。传入参数是迭代器（代表当前旋转的数量）。`runtime_canSpin` 函数的实现功能是确定是否可以输入当前的旋转等待状态。

如前所述，旋转锁在等待时不会释放 CPU 资源，也不会消耗上下文切换，但如果旋转时间过长，则会导致无意义的 CPU 消耗，这将进一步影响性能。

因此，在使用自旋锁时，必须严格控制自旋锁的进入过程。

最后一个是 `runtime_doSpin` 函数，可以简单地理解为 CPU 空闲一段时间，这就是自旋过程。

整个过程非常清晰。所有持有 CPU 的 goroutine 在 `runtime_canSpin` 函数通过检查后执行自旋操作。如果在旋转操作完成后，它们仍然没有持有锁，则 Goroutine 将被阻塞。其他逻辑与 V2 相同。

**V4：解决老 Goroutine 的饥饿问题.**

源地址如下: [https://github.com/golang/go/blob/go1.15.5/src/sync/mutex.go](https://github.com/golang/go/blob/go1.15.5/src/sync/mutex.go)

从 V2 到 V3 的改进是为新的 goroutines 提供更多的机会，这导致了老的 goroutine 饥饿问题，即新的获取锁的机会不会让给老的 goroutines，因此这个问题主要集中在 V4 中改进。

首先是互斥锁结构的 State 字段有了新的变化，增加了饥饿指示器(S)。

0 表示没有发生饥饿，1 表示发生了饥饿。(图片中的 S 标志位)

![.](../static/images/2022/w47_Deep_Understanding_of_Golang_Mutex/1_zJxfWDDhhfFv7sGFisDCQQ.png)

在新的定义中，常数的定义也发生了一些变化。

```go
const (
    mutexLocked = 1 << iota // mutex is locked
    mutexWoken
    mutexStarving // separate out a starvation token from the state field
    mutexWaiterShift = iota
    starvationThresholdNs = 1e6
)
```

Lock 方法的逻辑如下所示。

```golang
// Lock locks m.
// If the lock is already in use, the calling goroutine
// blocks until the mutex is available.
func (m *Mutex) Lock() {
 // Fast path: grab unlocked mutex.
 if atomic.CompareAndSwapInt32(&m.state, 0, mutexLocked) {
  if race.Enabled {
   race.Acquire(unsafe.Pointer(m))
  }
  return
 }
 // Slow path (outlined so that the fast path can be inlined)
 m.lockSlow()
}

func (m *Mutex) lockSlow() {
 var waitStartTime int64
 starving := false
 awoke := false
 iter := 0
 old := m.state
 for {
  // Don't spin in starvation mode, ownership is handed off to waiters
  // so we won't be able to acquire the mutex anyway.
  if old&(mutexLocked|mutexStarving) == mutexLocked && runtime_canSpin(iter) {
   // Active spinning makes sense.
   // Try to set mutexWoken flag to inform Unlock
   // to not wake other blocked goroutines.
   if !awoke && old&mutexWoken == 0 && old>>mutexWaiterShift != 0 &&
    atomic.CompareAndSwapInt32(&m.state, old, old|mutexWoken) {
    awoke = true
   }
   runtime_doSpin()
   iter++
   old = m.state
   continue
  }
  new := old
  // Don't try to acquire starving mutex, new arriving goroutines must queue.
  if old&mutexStarving == 0 {
   new |= mutexLocked
  }
  if old&(mutexLocked|mutexStarving) != 0 {
   new += 1 << mutexWaiterShift
  }
  // The current goroutine switches mutex to starvation mode.
  // But if the mutex is currently unlocked, don't do the switch.
  // Unlock expects that starving mutex has waiters, which will not
  // be true in this case.
  if starving && old&mutexLocked != 0 {
   new |= mutexStarving
  }
  if awoke {
   // The goroutine has been woken from sleep,
   // so we need to reset the flag in either case.
   if new&mutexWoken == 0 {
    throw("sync: inconsistent mutex state")
   }
   new &^= mutexWoken
  }
  if atomic.CompareAndSwapInt32(&m.state, old, new) {
   if old&(mutexLocked|mutexStarving) == 0 {
    break // locked the mutex with CAS
   }
   // If we were already waiting before, queue at the front of the queue.
   queueLifo := waitStartTime != 0
   if waitStartTime == 0 {
    waitStartTime = runtime_nanotime()
   }
   runtime_SemacquireMutex(&m.sema, queueLifo, 1)
   starving = starving || runtime_nanotime()-waitStartTime > starvationThresholdNs
   old = m.state
   if old&mutexStarving != 0 {
    // If this goroutine was woken and mutex is in starvation mode,
    // ownership was handed off to us but mutex is in somewhat
    // inconsistent state: mutexLocked is not set and we are still
    // accounted as waiter. Fix that.
    if old&(mutexLocked|mutexWoken) != 0 || old>>mutexWaiterShift == 0 {
     throw("sync: inconsistent mutex state")
    }
    delta := int32(mutexLocked - 1<<mutexWaiterShift)
    if !starving || old>>mutexWaiterShift == 1 {
     // Exit starvation mode.
     // Critical to do it here and consider wait time.
     // Starvation mode is so inefficient, that two goroutines
     // can go lock-step infinitely once they switch mutex
     // to starvation mode.
     delta -= mutexStarving
    }
    atomic.AddInt32(&m.state, delta)
    break
   }
   awoke = true
   iter = 0
  } else {
   old = m.state
  }
 }

 if race.Enabled {
  race.Acquire(unsafe.Pointer(m))
 }
}
```

[code here](https://gist.github.com/tengergou/a10a675929d7ae203816c65cbf564672#file-20220921-6-go)

我们主要关注 lockSlow 方法。在深入研究代码之前，我们首先需要理解在什么情况下当前锁被认为是饥饿的:

- (场景 1)旧的 Goroutine 被唤醒，但锁被新的 Goroutine 占据，对于旧的 Goroutine，我被唤醒了，但什么也没做，并立即再次被阻塞。
- (场景二)Goroutine 被阻塞的总时间超过阈值(默认为 1ms)。

所以核心是记录当前 Goroutine 开始等待的时间: 对于第一次进入锁的 Goroutine，开始等待时间为 0。对于场景 1，判断标准为开始等待时间是否为 0。如果它不是 0，就意味着它以前被阻塞过。通过(第 45 行)。

对于场景 2，判断标准为当前时间与开始等待时间的差值是否超过阈值。如果是这样，这意味着 Goroutine 已经等待太久，应该进入饥饿状态(第 50 行)。

进一步，当我们知道如何判断饥饿状态时，饥饿模式和非饥饿模式的区别是什么

首先，如果当前锁被耗尽，任何新的 goroutine 都不会旋转(第 15 行)。

其次，如果当前 Goroutine 处于饥饿状态，那么当它被阻塞时，它将被添加到等待队列的头部(下一个唤醒操作肯定会唤醒当前处于饥饿状态的 Goroutine，第 45 行和第 49 行)。

最后，允许饥饿的 goroutine 在被唤醒后立即持有锁，而不必与其他 goroutine 重新竞争锁(比较 V2，第 52 行和 62 行)。

V4 对应的 Unlock 也根据饥饿状态进行了调整。代码如下

```golang
func (m *Mutex) Unlock() {
 if race.Enabled {
  _ = m.state
  race.Release(unsafe.Pointer(m))
 }

 // Fast path: drop lock bit.
 new := atomic.AddInt32(&m.state, -mutexLocked)
 if new != 0 {
  // Outlined slow path to allow inlining the fast path.
  // To hide unlockSlow during tracing we skip one extra frame when tracing GoUnblock.
  m.unlockSlow(new)
 }
}

func (m *Mutex) unlockSlow(new int32) {
 if (new+mutexLocked)&mutexLocked == 0 {
  throw("sync: unlock of unlocked mutex")
 }
 if new&mutexStarving == 0 {
  old := new
  for {
   // If there are no waiters or a goroutine has already
   // been woken or grabbed the lock, no need to wake anyone.
   // In starvation mode ownership is directly handed off from unlocking
   // goroutine to the next waiter. We are not part of this chain,
   // since we did not observe mutexStarving when we unlocked the mutex above.
   // So get off the way.
   if old>>mutexWaiterShift == 0 || old&(mutexLocked|mutexWoken|mutexStarving) != 0 {
    return
   }
   // Grab the right to wake someone.
   new = (old - 1<<mutexWaiterShift) | mutexWoken
   if atomic.CompareAndSwapInt32(&m.state, old, new) {
    runtime_Semrelease(&m.sema, false, 1)
    return
   }
   old = m.state
  }
 } else {
  // Starving mode: handoff mutex ownership to the next waiter, and yield
  // our time slice so that the next waiter can start to run immediately.
  // Note: mutexLocked is not set, the waiter will set it after wakeup.
  // But mutex is still considered locked if mutexStarving is set,
  // so new coming goroutines won't acquire it.
  runtime_Semrelease(&m.sema, true, 1)
 }
}
```

[code here](https://gist.github.com/tengergou/0ff186760513855ace82c56a68c6bc58#file-20220921-7-go)

与上锁操作相比，解锁操作更容易理解。

谢谢阅读
