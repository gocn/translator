- 原文地址：https://tpaschalis.github.io/golang-time-now/
- 原文作者：Paschalis
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w14_how_does_go_know_time_now.md
- 译者：[cvley](https://github.com/cvley)

# Go 如何知道 time.Now

几天前，我在睡前想过这个问题，而答案比我想象的还要有意思！

这篇博客可能比之前的稍长一些，所以拿起你的咖啡、你的茶，找一个安静的地方，一起来深入看看我们可以发现什么。

所有的代码片段都有完整的参考信息；文中的参考是[release-branch.go1.16](https://github.com/golang/go/tree/release-branch.go1.16)。

关于 time.Time
---------------

首先，理解 Go 中_如何_嵌入时间非常有用。

 `time.Time` 结构体可以表示纳秒精度的时间度量。为了更可信的描述用于对比、加减的耗时，`time.Time` 也会包含一个可选的、纳秒精度的读取_当前进程_单调时钟的操作。这么做是为了避免表达错误的时段，比如，夏令时（Daylight Saving time，DST）。
```go
    type Time struct {
    	wall uint64
    	ext  int64
    	loc *Location
    }
```

Τime 结构体在 2017 年早期就是当前这个形式；你可以浏览 Russ Cox 提出的相关[issue](https://github.com/golang/go/issues/12914), [提案](https://go.googlesource.com/proposal/+/master/design/12914-monotonic.md)和[实现](https://go-review.googlesource.com/c/go/+/36255/)。

因此，首先有一个 `wall` 值用于提供直接读取的 “时钟”时间， `ext` 提供了这种单调时钟形式下的_额外_信息。

分解 `wall` 参数，它在最高位包含 1 比特的 `hasMonotonic` 标志；接下来是表示秒的 33 比特；最后 30 个比特用于表示纳秒，范围在 \[0, 999999999\] 之间。
```plain
    mSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
    ^                   ^                   ^
    hasMonotonic        seconds             nanoseconds
```

在 Go >= 1.9 的版本中，`hasMonotonic` 标志都是开启的，日期是在 1885 到 2157 之间，但由于兼容性考虑和一些极端情况，Go 可以保证这些时间内的值都可以被正确处理。

更准确的来说，下面是具体的行为差异：

**如果 `hasMonotonic` 比特是 1**，那么 33 比特的位置存储的就是从 1885 年 1 月 1 日开始的无符号的秒表示的时间，ext 表示的是从进程开始时的 64 比特单调时钟的纳秒精度的值。在代码中，大多数是这种情况。

**如果 `hasMonotonic` 比特是 0**，那么 33 比特的位置是 0，从公元 1 月开始的完整 64 比特的有符号时钟的秒值存在 `ext` 中，直到其单调性改变。

最后，每个 `Time`  的值都包含一个 Location，用于计算_表示形式_的时间；位置的改变仅改变这个表示，即打印的值，它不会影响存储的实际时间。nil 位置（默认情况）表示的是 “UTC”。

为了表述更加清楚，再重申一遍；一般  _报时的操作用的是读取的时钟时间，但衡量时间的操作，特别是比较和减法，使用的是单调时钟时间_。

很棒，但_当前_时间是如何计算的？
------------------------------------------------

下面是 Go 代码中如何定义  `time.Now()` 和 `startNano` 。
```go
    // Monotonic times are reported as offsets from startNano.
    var startNano int64 = runtimeNano() - 1
    
    // Now returns the current local time.
    func Now() Time {
    	sec, nsec, mono := now()
    	mono -= startNano
    	sec += unixToInternal - minWall
    	if uint64(sec)>>33 != 0 {
    		return Time{uint64(nsec), sec + minWall, Local}
    	}
    	return Time{hasMonotonic | uint64(sec)<<nsecShift | uint64(nsec), mono, Local}
    }
```

如果我们了解了一些常量后，代码就非常明确易懂
```go
    hasMonotonic         = 1 << 63
    unixToInternal int64 = (1969*365 + 1969/4 - 1969/100 + 1969/400) * secondsPerDay
    wallToInternal int64 = (1884*365 + 1884/4 - 1884/100 + 1884/400) * secondsPerDay
    minWall              = wallToInternal               // year 1885
    nsecShift            = 30
```

if 分支检查秒的值是否可以存储在 33 比特内，否则就需要设置 `hasMonotonic=off`。因为单调的粗略计算， 2^33 秒是 272 年，所以我们可以通过确定是否在 (1885+272=) 2157 年之后就可以高效快速得到结果。

否则，我们按上面描述的方法设置 `hasMonotonic=on` 的情况。

哎呀信息有些多！
--------------------

我当然同意！但即使有了这些信息，还有两个未知的情况；

_定义的未引出的 `now()` 和 `runtimeNano()` 在哪里？_ 以及

_Local 又是从何而来？_

下面就越来越意思了！

第一个未解之谜
------------

我们先来看第一个问题。按约定的逻辑，我们应该在相同的包内查看，但可能什么也找不到！

这两个函数是从 runtime 包中通过[_链接名字_](https://tpaschalis.github.io/golang-linknames/) 的方式获取的。
```go
    // Provided by package runtime.
    func now() (sec int64, nsec int32, mono int64)
    
    // runtimeNano returns the current value of the runtime clock in nanoseconds.
    //go:linkname runtimeNano runtime.nanotime
    func runtimeNano() int64
```

正如链接名字所示，要找到 `runtimeNano()` ，就必须找到 `runtime.nanotime()`，而我们会发现它出现了两次。

相似的，如果我们继续在 `runtime` 包中寻找，我们将会遇到 [`timestub.go`](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/timestub.go) 中包含 time.Now() 定义的链接名字使用了 `walltime()`。
```go
    // Declarations for operating systems implementing time.now
    // indirectly, in terms of walltime and nanotime assembly.
    
    // +build !windows
    ...
    //go:linkname time_now time.now
    func time_now() (sec int64, nsec int32, mono int64) {
    	sec, nsec = walltime()
    	return sec, nsec, nanotime()
    }
```

啊哈！现在我们有了一些进展！

 `walltime()` 和 `nanotime()` 表示的是一个 [‘虚拟’](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/time_fake.go#L42-L49) 实现，主要用于在 Go playground 中使用，而[‘真正’](https://github.com/golang/go/blob/9c7463ca903863a0c67b3f76454b37da0a400c13/src/runtime/time_nofake.go#L17-L24) 的实现，调用的是 `walltime1` 和 `nanotime1`。

```golang
//go:nosplit
func nanotime() int64 {
	return nanotime1()
}

func walltime() (sec int64, nsec int32) {
	return walltime1()
}
```


对应的， `nanotime1` 和 `walltime1` 按[几种](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/os_plan9.go#L351-L360)[不同的平台](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/sys_darwin.go#L246-L264)和[架构](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/sys_linux_arm64.s)进行了定义。

更加深入
-------------

我先为任何错误的表达道歉；在遇到汇编语言时，我有时就像一只在车灯前的小鹿一样迷茫，但我们可以尝试理解在 [amd64 Linux 下](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/sys_linux_amd64.s#L206-L270)是如何计算 walltime。

发现问题请一定要评论来修改，不要犹豫！
```plain
    // func walltime1() (sec int64, nsec int32)
    // non-zero frame-size means bp is saved and restored
    TEXT runtime·walltime1(SB),NOSPLIT,$16-12
    	// We don't know how much stack space the VDSO code will need,
    	// so switch to g0.
    	// In particular, a kernel configured with CONFIG_OPTIMIZE_INLINING=n
    	// and hardening can use a full page of stack space in gettime_sym
    	// due to stack probes inserted to avoid stack/heap collisions.
    	// See issue #20427.
    
    	MOVQ	SP, R12	// Save old SP; R12 unchanged by C code.
    
    	get_tls(CX)
    	MOVQ	g(CX), AX
    	MOVQ	g_m(AX), BX // BX unchanged by C code.
    
    	// Set vdsoPC and vdsoSP for SIGPROF traceback.
    	// Save the old values on stack and restore them on exit,
    	// so this function is reentrant.
    	MOVQ	m_vdsoPC(BX), CX
    	MOVQ	m_vdsoSP(BX), DX
    	MOVQ	CX, 0(SP)
    	MOVQ	DX, 8(SP)
    
    	LEAQ	sec+0(FP), DX
    	MOVQ	-8(DX), CX
    	MOVQ	CX, m_vdsoPC(BX)
    	MOVQ	DX, m_vdsoSP(BX)
    
    	CMPQ	AX, m_curg(BX)	// Only switch if on curg.
    	JNE	noswitch
    
    	MOVQ	m_g0(BX), DX
    	MOVQ	(g_sched+gobuf_sp)(DX), SP	// Set SP to g0 stack
    
    noswitch:
    	SUBQ	$16, SP		// Space for results
    	ANDQ	$~15, SP	// Align for C code
    
    	MOVL	$0, DI // CLOCK_REALTIME
    	LEAQ	0(SP), SI
    	MOVQ	runtime·vdsoClockgettimeSym(SB), AX
    	CMPQ	AX, $0
    	JEQ	fallback
    	CALL	AX
    ret:
    	MOVQ	0(SP), AX	// sec
    	MOVQ	8(SP), DX	// nsec
    	MOVQ	R12, SP		// Restore real SP
    	// Restore vdsoPC, vdsoSP
    	// We don't worry about being signaled between the two stores.
    	// If we are not in a signal handler, we'll restore vdsoSP to 0,
    	// and no one will care about vdsoPC. If we are in a signal handler,
    	// we cannot receive another signal.
    	MOVQ	8(SP), CX
    	MOVQ	CX, m_vdsoSP(BX)
    	MOVQ	0(SP), CX
    	MOVQ	CX, m_vdsoPC(BX)
    	MOVQ	AX, sec+0(FP)
    	MOVL	DX, nsec+8(FP)
    	RET
    fallback:
    	MOVQ	$SYS_clock_gettime, AX
    	SYSCALL
    	JMP ret
```

从我的理解来看，这个计算过程如下。

1.  因为我们不知道代码需要多少的栈空间，所以需要切换至 `g0`，它是每个系统线程创建的第一个 goroutine ，用于调度其他的 goroutines。我们保持追踪这个线程的本地存储，使用 `get_tls` 将它载入到 `CX` 寄存器，当前的 goroutine 使用了几次 `MOVQ` 语句。
  
2.  接下来代码存储 `vdsoPC` 和 `vdsoSP` (程序计数器和栈指针 ) 的值，用于在退出前存储它们，这样程序就可以 _重新进入_。
  
3.  代码检测它是否已经在 `g0`，是的话就跳转到 `noswitch`，否则使用下面的代码切换至 `g0` 
```plain  
        MOVQ	m_g0(BX), DX
        MOVQ	(g_sched+gobuf_sp)(DX), SP	// Set SP to g0 stack
``` 
4.  接下来，尝试载入 `runtime·vdsoClockgettimeSym` 进 `AX` 寄存器；如果它非零就调用并跳转到 `ret` 代码块，并获取秒和纳秒的值，并存储真实的栈指针和 vDSO 程序计数器和栈指针并返回
  ```plain
         MOVQ	0(SP), AX	// sec
         MOVQ	8(SP), DX	// nsec
         MOVQ	R12, SP		// Restore real SP
         // Restore vdsoPC, vdsoSP
         // We don't worry about being signaled between the two stores.
         // If we are not in a signal handler, we'll restore vdsoSP to 0,
         // and no one will care about vdsoPC. If we are in a signal handler,
         // we cannot receive another signal.
         MOVQ	8(SP), CX
         MOVQ	CX, m_vdsoSP(BX)
         MOVQ	0(SP), CX
         MOVQ	CX, m_vdsoPC(BX)
         MOVQ	AX, sec+0(FP)
         MOVL	DX, nsec+8(FP)
         RET
   ```
5.  另外，如果 `runtime·vdsoClockgettimeSym` 的地址为零，那么就会跳转到 `fallback` 标签，尝试使用不同的方法来获取系统时间，即 `$SYS_clock_gettime`
  ```plain
         MOVQ	runtime·vdsoClockgettimeSym(SB), AX
         CMPQ	AX, $0
         JEQ	fallback
        ...
        ...
        fallback:
         MOVQ	$SYS_clock_gettime, AX
         SYSCALL
         JMP ret
  ``` 

同样的文件定义了 `$SYS_clock_gettime`
``` plain
    #define SYS_clock_gettime	228
```

它实际对应的是 [`__x64_sys_clock_gettime`](https://github.com/torvalds/linux/blob/v4.17/arch/x86/entry/syscalls/syscall_64.tbl#L239) [syscall](https://filippo.io/linux-syscall-table/) ，在 Linux 源码中的系统调用表中可以找到。

两个不同的选项有何不同？
----------------------------------------

 “优选”的 `vdsoClockgettimeSym` 模式定义在 `vdsoSymbolKeys`
```go
    var vdsoSymbolKeys = []vdsoSymbolKey{
    	{"__vdso_gettimeofday", 0x315ca59, 0xb01bca00, &vdsoGettimeofdaySym},
    	{"__vdso_clock_gettime", 0xd35ec75, 0x6e43a318, &vdsoClockgettimeSym},
    }
```

与从 [文档](https://man7.org/linux/man-pages/man7/vdso.7.html) 中找到 vDSO 符号匹配。

_为什么选择 `__vdso_clock_gettime` 而不是 `__x64_sys_clock_gettime`，它们有什么不同？_

[vDSO](https://en.wikipedia.org/wiki/VDSO) 表示的是 _虚拟动态共享对象_ ，它是一种将内核空间的子集暴漏到用户空间应用的一种内核机制，这样内核空间就可以在进程中调用，而无需从用户态切换至内核态而产生性能损耗。

 [vDSO 文档](https://man7.org/linux/man-pages/man7/vdso.7.html) 包含了 `gettimeofday` 的相关例子，解释了使用它的好处。

引用文档

> 有些内核提供的系统调动，在用户空间频繁使用时，会遇到这些调用主导整体性能的情况。这不仅是频繁的系统调用导致，还是从用户空间退出并进入内核的上下文切换的结果。

> 系统调用会比较慢，但触发一次软件中断来告诉内核你希望进行系统调用的性能开销也很大，因为它贯穿处理器的微代码和内核的整个终端处理的路径。

> 一个频繁使用的系统调用是 gettimeofday(2)。这个系统调用是直接由用户空间的应用调用。这个信息也不是秘密——任何在任意权限模式下（root 或其他非特权用户）应用将得到相同的结果。 因此内核将这个问题需要的信息放在了进程可以获取的内存中。现在调用 gettimeofday(2) 从一个系统调用变为一个正常的有几次内存访问的函数调用。

因此， vDSO 调用被优先选择作为获取时钟信息的方法，是因为它不需要贯穿内核的中断处理路径，但可以更快的调用。

将它们封装起来，Linux AMD64 的当前时间最后要么从 `__vdso_clock_gettime` 或 `__x64_sys_clock_gettime` 系统调用获取。为了“愚弄” `time.Now()` 你不得不修改其中一个方法。

Windows 的奇怪之处
-----------------

有观察力的读者可能会问， _在 timestub.go 中，我们使用了 `// +build !windows`。. 这有什么用？_

这是因为，Windows 直接在汇编里实现了 `time.Now()` ，结果是 [`timeasm.go`](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/timeasm.go) 文件中的链接名字。

我们可以在 [`sys_windows_amd64.s`](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/sys_windows_amd64.s) 中看到相关的汇编代码。

据我所知，这里的代码路径和 Linux 下的有些相似。 `time·now` 汇编首先做的也是检查是否使用 [QPC](https://docs.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps) 来获取 [`nowQPC`](https://github.com/golang/go/blob/1d967ab95c43b6b8810ca53d6a18aff85e59a3b6/src/runtime/os_windows.go#L514-L526) 函数的时间。
```plain
    	CMPB	runtime·useQPCTime(SB), $0
    	JNE	useQPC
    
    useQPC:
    	JMP	runtime·nowQPC(SB)
    	RET
```

如果不是这种情况，代码将会尝试使用下面[`KUSER_SHARED_DATA`](http://www.nirsoft.net/kernel_struct/vista/KUSER_SHARED_DATA.html) 结构体中的两个地址，也叫做`SharedUserData`。这个结构体保存了一些内核信息，与用户态共享，是为了避免向内核多次传输，和 vDSO 类似。
```plain
    #define _INTERRUPT_TIME 0x7ffe0008
    #define _SYSTEM_TIME 0x7ffe0014
    
    KSYSTEM_TIME InterruptTime;
    KSYSTEM_TIME SystemTime;
```

使用这两个地址的部分如下所示。获取的信息存在 [`KSYSTEM_TIME`](http://www.nirsoft.net/kernel_struct/vista/KSYSTEM_TIME.html) 结构体中。
```plain
    	CMPB	runtime·useQPCTime(SB), $0
    	JNE	useQPC
    	MOVQ	$_INTERRUPT_TIME, DI
    loop:
    	MOVL	time_hi1(DI), AX
    	MOVL	time_lo(DI), BX
    	MOVL	time_hi2(DI), CX
    	CMPL	AX, CX
    	JNE	loop
    	SHLQ	$32, AX
    	ORQ	BX, AX
    	IMULQ	$100, AX
    	MOVQ	AX, mono+16(FP)
    	MOVQ	$_SYSTEM_TIME, DI

```
 `_SYSTEM_TIME` 的问题是更低的解析度，更新周期为 100 纳秒；这也可能是优先选择 QPC 的原因。

在 Windows 部分我花费了很长的时间，[若](https://gist.github.com/m-schwenk/d312c02ec6b230c19dc2) [你](https://docs.microsoft.com/en-us/windows/win32/api/profileapi/nf-profileapi-queryperformancecounter) [感兴趣](https://docs.microsoft.com/en-us/uwp/api/windows.perception.perceptiontimestamp.systemrelativetargettime?view=winrt-19041)，[这里](https://www.matteomalvica.com/minutes/windows_kernel/#kuser-shared-data) [有一些](moz-extension://3b9164ce-6b20-1541-a720-5d6cc82dcebd/www.uninformed.org/?v=3&a=4&t=pdf) [更详细的](https://gist.github.com/alastorid/ecaeba6b3f2a521c25b28efd81ac0a2d) [信息](http://uninformed.org/index.cgi?v=2&a=2&p=20) 

第 2 个未解之谜
------------

这个问题是什么来着？噢，我们还没弄清楚 _ Local 从何而来？_

导出的 `Local *Location` 符号首先指向了 `localLoc` 的地址。
```go
    var Local *Location = &localLoc
```

如果这个地址是 nil，那么就如我们所说，返回的是 UTC 位置。否则，代码会在需要位置信息的第一次调用时，通过使用 `sync.Once` 语句来设置包级别的`localLoc` 变量。
```go
    // localLoc is separate so that initLocal can initialize
    // it even if a client has changed Local.
    var localLoc Location
    var localOnce sync.Once
    
    func (l *Location) get() *Location {
    	if l == nil {
    		return &utcLoc
    	}
    	if l == &localLoc {
    		localOnce.Do(initLocal)
    	}
    	return l
    }
``
 [`initLocal()`](https://github.com/golang/go/blob/release-branch.go1.16/src/time/zoneinfo_unix.go#L28-L69) 函数使用 `$TZ` 的内容来找到使用的时区。

如果 `$TZ` 变量没有设置，Go 会使用系统默认的文件如 `/etc/localtime` 来载入时区。如果设置但为空，Go 将使用 UTC 时区，而当它为无效的时区时，它会从系统时区文件夹中找同名的文件。默认的搜索路径是
```go
    var zoneSources = []string{
    	"/usr/share/zoneinfo/",
    	"/usr/share/lib/zoneinfo/",
    	"/usr/lib/locale/TZ/",
    	runtime.GOROOT() + "/lib/time/zoneinfo.zip",
    }
```

平台相关的 `zoneinfo_XYZ.go` 文件使用相似的逻辑来寻找默认的时区，比如 Windows 或 WASM。过去，当我在类 Unix 系统下，需要在定制的容器镜像中使用时区时，只需要在 Dockerfile 中添加下面的命令。
```Dockerfile
    COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
```

另外，在无法控制构建环境的情况下， `tzdata` 包提供了一个 _嵌入复制_ 的时区数据库。若这个包在任意位置引入或我们使用 `-tags timetzdata` 构建标签，程序文件大小将会增加约 ~450KB，但将可以在 Go 无法在宿主系统中无法找到 `tzdata` 文件时，提供一个备用的方式。

最后，我们也可以在代码中使用[`LoadLocation`](https://github.com/golang/go/blob/release-branch.go1.16/src/time/zoneinfo.go#L617-L664) 函数手动设置时区，比如在测试的情况下。

结尾
-----

今天就这么多！我希望你们都可以学到一些新知识，或者了解一些有趣的知识点，并更加有信心去阅读 Go 的源码库！

欢迎通过邮件或者 [Twitter](https://twitter.com/tpaschalis_) 联系、提出修改建议。

再见，保重！

奖励：Go 中的 `funcname1` 是什么
--------------------------------------

在 Go 的代码库中，你将会见到很多 `funcname1()` 或 `funcname2()` 的引用，尤其是当你看底层的代码时。

据我理解，它们有两个目的；它们有助于保持 Go 的兼容性保证，可以更加轻松的切换未导出函数的内部实现，通过也可以将相似功能“组合”和/或链接起来。

有些人可能嘲笑这种方式，但我认为它是保持代码可读性和维护性的一种简单有效的方法。
