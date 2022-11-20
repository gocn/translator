# Deep Understanding of Golang Mutex

> How to implement Golang Mutex

![.](../static/images/2022/w47_Deep_Understanding_of_Golang_Mutex/1_BWLrf8Kh0LvhK9nuqnH9jg.jpeg)

Photo by [Daniil Silantev](https://unsplash.com/@betagamma?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText) on [Unsplash](https://unsplash.com/s/photos/home?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText)

Before we start, we need to add several ways to implement locks.

**\# Semaphore.**

There are P and V operations in the OS. The P operation is to change the semaphore by -1, and the V operation is to increase the semaphore by 1, so the operation mode of the semaphore is:

- Initialize, give it a non-negative integer value.
- The process of the program attempting to enter the critical block needs to run P first. Then there will be 2 scenarios.

1. When the semaphore S is reduced to a negative value, the process will be blocked and cannot continue. At this time, the process is blocked.
2. When the semaphore S is not negative, the process can be admitted to the critical block.

- To end the process leaving the critical block, V will be run. When the semaphore S is not negative, other processes that were previously blocked will be allowed to enter the critical block.

**\# Semaphores and locks.**

Although semaphores and locks look similar, for example, when the semaphore is 1, a mutual exclusion lock is implemented, but in fact, they have different meanings.

Locks are used to protecting critical resources, such as reading and writing cannot be performed at the same time.

The semaphore is to ensure that the process (or thread or goroutine) is scheduled. For example, three processes jointly calculate c=a+b. First, the calculation of a+b and the assignment operation cannot be performed at the same time. Secondly, it is necessary to ensure that a+b is executed first. c is executed after the assignment, so this place needs to be done in the form of a semaphore.

Further, the lock can be implemented by a semaphore, then the goroutine can be blocked and woken up according to the regulations, or it can be implemented by a spin lock, then the goroutine will occupy the CPU until it is unlocked.

The difference between these two methods is whether goroutine scheduling is required, but in essence, the implementation of locks is to ensure that critical resources will not be accessed by mistake.

**\# Spin lock.**

CAS theory is a kind of spinlock.

Only one thread can acquire the lock at the same time, and the thread that does not acquire the lock usually has two processing methods:

- It has been waiting in a loop to determine whether the resource has released the lock. This kind of lock is called a spin lock, and it does not block the thread (NON-BLOCKING).
- Block yourself, waiting for rescheduling requests, this is a mutex.

The principle of the spin lock is relatively simple. If the thread holding the lock can release the lock resource in a short time, then those threads waiting for the competing lock do not need to switch between the kernel mode and the user mode to enter the blocking state, they only need to Wait a minute (spin), wait until the thread holding the lock releases the lock and then acquire it, thus avoiding the consumption of user processes and kernel switching.

But if locked for a long time, the spinlock can be very expensive, it prevents other threads from running and scheduling.

The longer a thread holds a lock, the greater the risk that the thread holding that lock will be interrupted by the OS scheduler.

In the event of an interruption, other threads will remain spinning (repeatedly trying to acquire the lock) and the thread holding the lock does not intend to release the lock, which results in an indefinite delay until the thread holding the lock can complete and release it.

A good way to solve the above situation is to set a spin time for the spin lock and release the spin lock as soon as the time expires.

The purpose of spin locks is to occupy CPU resources without releasing them and process them immediately when the locks are acquired.

**\# Pessimistic locking and optimistic locking.**

Pessimistic locking is a kind of pessimistic thinking. It always thinks that the worst situation may occur. It thinks that data is likely to be modified by others. Regardless of reading or writing, pessimistic locks are locked before performing operations.

Both read and write need to be locked, resulting in low performance, so there are not many opportunities for pessimistic locking. However, in the case of multiple writes, there is still a chance to use pessimistic locks, because optimistic locks will keep retrying in the case of inconsistent writes, which will waste more time.

The idea of optimistic locking is contrary to the idea of pessimistic locking. It always believes that resources and data will not be modified by others, so reading will not be locked, but optimistic locking will determine whether the current data has been modified when writing operations. .

The implementation scheme of optimistic locking mainly includes CAS and version number mechanism. Optimistic locking is suitable for multi-read scenarios and can improve throughput.

CAS stands for Compare And Swap, which is a well-known lock-free algorithm.

That is, to achieve variable synchronization between multiple threads without using locks, that is, to achieve variable synchronization without threads being blocked, so it is also called non-blocking synchronization.

CAS involves three relationships: a pointer V to a region of memory, the old value A, and the new value B to be written.

The optimistic lock implemented by CAS will bring about the ABA problem. At the same time, the entire optimistic lock will trigger the waiting and retry mechanism in the case of data inconsistency, which has a great impact on performance.

The version number mechanism implements version control through a version number version.

Well, with the above basic knowledge, we can start to analyze how Mutex is implemented in Golang.

Golang’s implementation of Mutex has been improving, and as of now, it has mainly improved 4 versions:

- V1: Simple implementation.
- V2: The new goroutine participates in the lock competition.
- V3: Give new goroutines some more chances.
- V4: Solve the old goroutine starvation problem.

Each improvement is to improve the overall performance of the system. This upgrade is gradual and continuous, so it is necessary to start slowly from the V1 version to see the evolution of Mutex.

**V1: Simple implementation.**

In the V1 version, the entire source code of Mutex is as follows. [commit](https://github.com/golang/go/blob/d90e7cbac65c5792ce312ee82fbe03a5dfc98c6f/src/pkg/sync/mutex.go)

The main core code is as follows:

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

First of all, the structure of `Mutex` is very simple, including two flags, `key` and `sema`.

The `key` indicates that there are several goroutines currently using or preparing to use the lock. If `key==0`, it means that the current mutex is unlocked, otherwise, `key>0` means that the mutex is locked.

The `sema` is the semaphore, which is what actually causes the `goroutine` to block and wake up.

The `xadd` function is a CAS-based addition and subtraction function.

The `Lock` and `Unlock` functions are the core of locking the current mutex, but the logic is very simple.

The `Lock` function uses the `xadd` method to `key+1`. If the result is `1`, it means that the original lock is in an unlocked state, so you don’t need to pay attention to the semaphore to directly acquire the lock. If not, call the `semacquire` method to block the current goroutine.

The `Unlock` function uses the `xadd` method to pair `key-1`. If the result is not `0`, it means that a goroutine is currently waiting, and it is necessary to call `semrelease` to wake up a goroutine.

In the current V1 version, the locking and unlocking are completely based on the FIFO method. Although this method is very fair, it is not optimal from the perspective of efficiency.

Imagine a scenario: the blocked goroutine (name the current goroutine as g1) must not occupy the CPU, so the context switch needs to be performed after g1 is woken up. If a new goroutine (g2) comes at this time, it has the CPU resource.

If the lock is given to g2, then it can execute and return the result immediately (not waiting for the context switch of g1), so that the overall efficiency can be improved to a higher level.

**V2: New Goroutine participates in lock competition.**

The full source code address is at:[https://github.com/golang/go/blob/weekly.2011-07-07/src/pkg/sync/mutex.go](https://github.com/golang/go/blob/weekly.2011-07-07/src/pkg/sync/mutex.go)

In the V2 version, the core feature is that a goroutine does not execute tasks immediately after being woken up, but still repeats the process of preempting locks so that new goroutines have the opportunity to acquire locks, which is the so-called opportunity for newcomers.

Mutex structures and constants are defined as follows.

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

Although the definition of the Mutex structure is basically unchanged, from the `key` of V1 to the `state` of V2, their internal structure is very different.

The 0th bit represents the lock state (L), that is, `0` represents unlocking, `1` represents locking, the 1st bit represents the wake-up state (W), and the 2nd to 31st bits represent the number of blocking waits.

![.](../static/images/2022/w47_Deep_Understanding_of_Golang_Mutex/1__aGSxVA7YJpaUsb7fmQaMA.png)

The value of `mutexLocked` is `0x1`, the value of `mutexWoken` is `0x2`, the value of `mutexWaiterShift` is `0x2`, and `mutexWaiterShift` indicates that any array representing the number of blocked waits needs to be shifted left by two bits.

The main improvement of the V2 version exists in the Lock method, the code is as follows.

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

The code logic in lines 2–4 applies to the unlocked state, and the goroutine acquires the lock through CAS by setting the L bit from `0` to `1`.

There is no contention at this point, so acquiring the lock costs almost nothing.

The following code is accessed to indicate that it is currently locked, that is, the L bit is `1`.

The goroutine then enters a loop in which the CAS method ensures that the new state is properly superimposed.

The main changes from the old state to the new state (new) include:

- Attempt to acquire the lock.
- Try increasing the number of waiters by 1.

Since the change is not atomic, it may cause the old state to become stale.

For example, it is currently in the unlocked state, and two goroutines acquire the old state at the same time, both of which are in the unlocked state, but there is always one that can get the lock and the other that cannot.

Similarly, even if the current state is locked, the old state will be out of date due to the number of waiters.

So you need to continue to get the new old state through the loop.

After the old state is not obsolete and overwrites the new state, the real locking step is entered.

If the old state is unlocked, the lock is obtained directly, otherwise, the current goroutine is blocked through the semaphore mechanism.

After being awakened, unlike V1, the current process will still fall into the for loop to grab the lock again, which is the embodiment of giving newcomers a chance:

- If the old goroutine has a new goroutine during the context switch, the lock will be given to the new goroutine.
- If the old goroutine still does not have a new goroutine after the context switch is completed, the lock will be given to the old goroutine.

The Unlock method is relatively simple. The code is as follows.

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

There are two main unlocking logics.

- Returns directly if there is no waiter or the current system is unlocked and there is a wake-up goroutine.
- If the above requirements are not met, the number of waiting will be reduced by one and the Goroutine at the head of the queue will be woken up through the semaphore.

**V3: Give new goroutines some more chances.**

The optimization of this version, the key commit is at

[https://github.com/golang/go/commit/edcad8639a902741dc49f77d000ed62b0cc6956f](https://github.com/golang/go/commit/edcad8639a902741dc49f77d000ed62b0cc6956f)

On the basis of V2, how can the performance be further improved? Most of the time, the operation of the data during the exclusive lock period of the coroutine is actually very low, which may be lower than the time-consuming of waking up + switching the context.

Imagine a scenario: GoroutineA has CPU resources, and GoroutineB is at the head of the blocking queue. Then when GoroutineA tries to acquire the lock, it finds that the current lock is occupied. According to the V2 policy, GoroutineA is blocked immediately, assuming that the lock is at this moment. If it is released, then GoroutineB will be woken up as planned, that is, the entire running time includes GoroutineB’s wake-up + context switching time.

In V3, the new Goroutine (GoroutineA) is allowed to wait for a certain period of time by spinning. If the lock is released during the waiting time, the new Goroutine immediately obtains the lock resource, avoiding the time-consuming of the old Goroutine’s wake-up + context switching, and improving the overall work efficiency.

Similarly, the improvement of V3 mainly focuses on the `Lock` method, and the code is as follows.

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

Compared with the implementation code of V2, it mainly focuses on lines 14–25, and there are two more functions `runtime_canSpin` and `runtime_doSpin`, which are the core of the spin lock.

The first is the `runtime_canSpin` function. The incoming parameter is `iter` (representing the current number of spins). The implementation function of the runtime_canSpin function is to determine whether the current spin wait state can be entered.

As mentioned earlier, spin locks wait without releasing CPU resources, and there is no consumption of context switching, but if the spin time is too long, it will lead to meaningless CPU consumption, which will further affect performance.

Therefore, when using the spinlock, the entry process of the spin lock must be strictly controlled.

The last is the `runtime_doSpin` function, which can be simply understood as the CPU idle for a period of time, that is the spin process.

The whole process is very clear. All Goroutines that hold the CPU perform spin operations after the runtime_canSpin function has passed the check. If they still do not hold the lock after the spin operation is completed, the Goroutine is blocked. Other logic remains the same as V2.

**V4: Solve the old goroutine starvation problem.**

The source address is at: [https://github.com/golang/go/blob/go1.15.5/src/sync/mutex.go](https://github.com/golang/go/blob/go1.15.5/src/sync/mutex.go)

The improvement from V2 to V3 is to give new goroutines more opportunities, which leads to the starvation problem that old goroutines may not be able to grab new goroutines, so this problem is focused on improving in V4.

The first is that the State field of the Mutex structure has a new change, adding a hunger indicator (S).

Where `0` means starvation did not occur and `1` means starvation occurred.

![.](../static/images/2022/w47_Deep_Understanding_of_Golang_Mutex/1_zJxfWDDhhfFv7sGFisDCQQ.png)

In the new definition, the definitions of constants have also changed a bit.

```go
const (
    mutexLocked = 1 << iota // mutex is locked
    mutexWoken
    mutexStarving // separate out a starvation token from the state field
    mutexWaiterShift = iota
    starvationThresholdNs = 1e6
)
```

The logic of the Lock method is as follows.

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

We focus on the lockSlow method. Before diving into the code, we first need to understand under what circumstances the current lock is considered to be starved:

- (Scenario 1) The old Goroutine is woken up but the lock is taken by the new Goroutine, for the old Goroutine “I was woken up and did nothing and was immediately blocked again”.
- (Scenario 2) The total time a Goroutine is blocked exceeds the threshold (default is 1ms).

So the core is to record the time when the current Goroutine starts to wait: for the Goroutine that first enters the lock, the start waiting time is 0. For scenario 1, the judgment criterion is whether the start waiting time is 0. If it is not 0, it means that it has been blocked before. passed (line 45).

For scenario 2, the judgment criterion is whether the difference between the current time and the start waiting time exceeds the threshold. If so, it means that the Goroutine has been waiting for too long and should enter a starvation state (line 50).

Further, when we know how the starvation state is judged, what is the difference between the starvation mode and the non-starvation mode?

First, if the current lock is starved, any new Goroutines will not spin (line 15).

Second, if the current Goroutine is in a starving state, it will be added to the head of the waiting queue when it is blocked (the next wakeup operation will definitely wake up the currently starved Goroutine, lines 45–49).

Finally, the starved goroutine is allowed to hold the lock immediately after being woken up, without re-competing for the lock with other goroutines (compare V2, lines 52–62).

The Unlock corresponding to V4 has also been adjusted according to the starvation state. The code is as follows:

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

Compared with the locking operation, the unlocking operation is much easier to understand.

In normal mode, the unlocking operation is the same as in previous versions. In starvation mode, the coroutine at the top of the blocking queue will be awakened directly.

Thanks for reading.

If you like such stories and want to support me, please give me a clap.

Your support is very important to me — thank you.
