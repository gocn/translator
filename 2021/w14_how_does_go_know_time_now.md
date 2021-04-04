- 原文地址：https://tpaschalis.github.io/golang-time-now/
- 原文作者：Paschalis
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w14_how_does_go_know_time_now.md
- 译者：[cvley](https://github.com/cvley)
- 校对：[](https://github.com/)

# How does Go know time.Now?

I thought about this just before I went to sleep the other day, and the answer was more interesting than I’d imagined!

This post may be a little longer than usual, so grab your coffees, grab your teas and without further ado, let’s dive in and see what we can come up with.

All code snippets point to a stable reference; in this case to [release-branch.go1.16](https://github.com/golang/go/tree/release-branch.go1.16).

About time.Time
---------------

First off, it’s useful to understand just _how_ time is embodied in Go.

The `time.Time` struct can represent instants in time with nanosecond-precision. In order to more reliably measure elapsed time for comparisons, additions and subtractions, `time.Time` may also contain an optional, nanosecond-precision reading of the _current process’_ monotonic clock. This is to avoid reporting erroneous durations, eg. in case of DST.

    type Time struct {
    	wall uint64
    	ext  int64
    	loc *Location
    }


The Τime struct took this form back in early 2017; you can browse the relevant [issue](https://github.com/golang/go/issues/12914), [proposal](https://go.googlesource.com/proposal/+/master/design/12914-monotonic.md) and [implementation](https://go-review.googlesource.com/c/go/+/36255/) by the man himself, Russ Cox.

So, first off there’s `wall` value providing a straightforward ‘wall clock’ reading, and `ext` which provides this _ext_ended information in the form of the monotonic clock.

Breaking down `wall` it contains a 1-bit `hasMonotonic` flag in the highest bit; then 33 bits for keeping track of seconds; and finally 30 bits for keeping track of nanoseconds, in the \[0, 999999999\] range.

    mSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
    ^                   ^                   ^
    hasMonotonic        seconds             nanoseconds


The `hasMonotonic` flag is always _on_ for Go >= 1.9 and dates between 1885 to 2157, but due to the compatibility promise as well as extreme cases, Go makes sure these time values are handled correctly as well.

More precisely, here’s how the behavior differs:

**If the `hasMonotonic` bit is 1**, then the 33-bit field stores the unsigned wall seconds since Jan 1 Year 1885, and ext holds a signed 64-bit monotonic clock reading, nanoseconds since process start. This is what usually happens in most of your code.

**If the `hasMonotonic` bit is 0**, then the 33-bit field is zero, and the full signed 64-bit wall seconds since Jan 1 year 1 is stored in `ext` as it did before the monotonic change.

Finally, each `Time` value contains a Location, which is used when computing its _presentation form_; changing the location only changes the representation eg. when printing the value, it doesn’t affect the instant in time being stored. A nil location (the default) means ‘UTC’.

Again, to reiterate, to make things clear; usual _time-telling operations use the wall clock reading, but time-measuring operations, specifically comparisons and subtractions, use the monotonic clock reading._.

Great, but how is the _current_ time calculated?
------------------------------------------------

Here’s how `time.Now()` and `startNano` are defined in Go code.

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


The code is pretty straightforward if we peek at some constants

    hasMonotonic         = 1 << 63
    unixToInternal int64 = (1969*365 + 1969/4 - 1969/100 + 1969/400) * secondsPerDay
    wallToInternal int64 = (1884*365 + 1884/4 - 1884/100 + 1884/400) * secondsPerDay
    minWall              = wallToInternal               // year 1885
    nsecShift            = 30


The if-branch checks whether we can fit the seconds value in the 33-bit field or we need to go with `hasMonotonic=off`. As the monotonic draft mentions, 2^33 seconds are 272 years, so effectively we look whether we’re _after_ year (1885+272=) 2157 to return early.

Otherwise, we end up with the usual `hasMonotonic=on` case as described above.

Phew that was a lot!
--------------------

I have to agree! But even with this information, there are two mysteries remaining;

_Where are the unexported `now()` and `runtimeNano()` defined?_ and

_Where does Local come from?_

Here’s where it gets interesting!

Mystery No.1
------------

Let’s start with the first question. Conventional logic would say that we’d look into the same package, but we’ll probably find nothing there!

These two functions are [_linkname’d_](https://tpaschalis.github.io/golang-linknames/) from the runtime package.

    // Provided by package runtime.
    func now() (sec int64, nsec int32, mono int64)
    
    // runtimeNano returns the current value of the runtime clock in nanoseconds.
    //go:linkname runtimeNano runtime.nanotime
    func runtimeNano() int64


As the linkname directive informs us, to find `runtimeNano()` we’d have to search for `runtime.nanotime()`, where we find two occurrences.

Similarly, if we continue looking in the `runtime` package, we’ll come across [`timestub.go`](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/timestub.go) which contains the linknamed definition for time.Now() that uses `walltime()`.

    // Declarations for operating systems implementing time.now
    // indirectly, in terms of walltime and nanotime assembly.
    
    // +build !windows
    ...
    //go:linkname time_now time.now
    func time_now() (sec int64, nsec int32, mono int64) {
    	sec, nsec = walltime()
    	return sec, nsec, nanotime()
    }


A ha! Now we’re getting somewhere!

Both `walltime()` and `nanotime()` feature a [‘fake’](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/time_fake.go#L42-L49) implementation meant to be used for the Go playground, as well as the [‘real’](https://github.com/golang/go/blob/9c7463ca903863a0c67b3f76454b37da0a400c13/src/runtime/time_nofake.go#L17-L24) one, which calls to `walltime1` and `nanotime1`.

    //go:nosplit
    func nanotime() int64 {
    	return nanotime1()
    }
    
    func walltime() (sec int64, nsec int32) {
    	return walltime1()
    }


In turn, both `nanotime1` and `walltime1` are defined for [several](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/os_plan9.go#L351-L360) [different](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/sys_darwin.go#L246-L264) [platforms](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/sys_linux_amd64.s) and [architectures](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/sys_linux_arm64.s).

Diving deeper
-------------

I apologize in advance for any erroneous statement; I’m sometimes like a deer caught in the headlights when confronted with assembly, but let’s try to understand how walltime is calculated for amd64 Linux [here](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/sys_linux_amd64.s#L206-L270).

Please don’t hesitate to reach out for comments and corrections!

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


As far as I can understand, here’s how the process goes.

1.  Since we don’t know how much stack space the code will need we switch over to `g0` which is the first goroutine created for each OS thread, responsible for scheduling other goroutines. We keep track of the thread local storage using `get_tls` to load it into the `CX` register and our current goroutine using a couple of `MOVQ` statements.
  
2.  The code then stores the values for `vdsoPC` and `vdsoSP` (Program Counter and Stack Pointer) to restore them before exiting so that the function can be _re-entrant_.
  
3.  The code checks whether it is already on `g0`, where it jumps to `noswitch`, otherwise changes to `g0` with the following lines
  
        MOVQ	m_g0(BX), DX
        MOVQ	(g_sched+gobuf_sp)(DX), SP	// Set SP to g0 stack
  
4.  Next up, it tries to load the address of `runtime·vdsoClockgettimeSym` into the `AX` register; if it is not zero it calls it and moves on to the `ret` block where it retrieves the second and nanosecond values, restores the real Stack Pointer, restores the vDSO program counter and stack pointer and finally returns
  
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
   
5.  On the other hand, if the address of `runtime·vdsoClockgettimeSym` is zero, then it jumps to the `fallback` tag where it tries to use a different method to get the system’s time, that is `$SYS_clock_gettime`
  
         MOVQ	runtime·vdsoClockgettimeSym(SB), AX
         CMPQ	AX, $0
         JEQ	fallback
        ...
        ...
        fallback:
         MOVQ	$SYS_clock_gettime, AX
         SYSCALL
         JMP ret
   
    
   

The same file defines `$SYS_clock_gettime`

    #define SYS_clock_gettime	228


which actually corresponds to the [`__x64_sys_clock_gettime`](https://github.com/torvalds/linux/blob/v4.17/arch/x86/entry/syscalls/syscall_64.tbl#L239) [syscall](https://filippo.io/linux-syscall-table/) when looking up the syscall table from the Linux source code!

What’s with these two different options?
----------------------------------------

The ‘preferred’ `vdsoClockgettimeSym` mode is defined in `vdsoSymbolKeys`

    var vdsoSymbolKeys = []vdsoSymbolKey{
    	{"__vdso_gettimeofday", 0x315ca59, 0xb01bca00, &vdsoGettimeofdaySym},
    	{"__vdso_clock_gettime", 0xd35ec75, 0x6e43a318, &vdsoClockgettimeSym},
    }


which matches the exported vDSO symbol found in the [documentation](https://man7.org/linux/man-pages/man7/vdso.7.html).

_Why is `__vdso_clock_gettime` preferred over `__x64_sys_clock_gettime`, and what’s the difference between them?_

[vDSO](https://en.wikipedia.org/wiki/VDSO) stands for _virtual dynamic shared object_ and is a kernel mechanism for exporting a subset of the kernel space routines to user space applications so that these kernel space routines can be called in-process without incurring the performance penalty of switching from user mode to kernel mode.

The [vDSO documentation](https://man7.org/linux/man-pages/man7/vdso.7.html) contains the relevant example of `gettimeofday` for explaining its benefits.

To quote the docs

> There are some system calls the kernel provides that user-space code ends up using frequently, to the point that such calls can dominate overall performance. This is due both to the frequency of the call as well as the context- switch overhead that results from exiting user space and entering the kernel.

> Making system calls can be slow, but triggering a software interrupt to tell the kernel you wish to make a system call is expensive as it goes through the full interrupt-handling paths in the processor’s microcode as well as in the kernel.

> One frequently used system call is gettimeofday(2). This system call is called directly by user-space applications. This information is also not secret—any application in any privilege mode (root or any unprivileged user) will get the same answer. Thus the kernel arranges for the information required to answer this question to be placed in memory the process can access. Now a call to gettimeofday(2) changes from a system call to a normal function call and a few memory accesses.

So, the vDSO call is preferred as the method of getting clock information as it doesn’t have to go through the kernel’s interrupt-handling path, but can be called more quickly.

To wrap things up, the current time in Linux AMD64 is ultimately derived from either `__vdso_clock_gettime` or the `__x64_sys_clock_gettime` syscall. To ‘fool’ `time.Now()` you’d have to tamper with either of these.

Windows Weirdness
-----------------

An observant reader may ask, _in timestub.go, we use `// +build !windows`. What’s up with that?_

Well, Windows implements `time.Now()` directly in assembly and the result is linknamed from the [`timeasm.go`](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/timeasm.go) file.

We can see the relevant assembly code in [`sys_windows_amd64.s`](https://github.com/golang/go/blob/release-branch.go1.16/src/runtime/sys_windows_amd64.s).

As far as I understand, the code path here is somewhat similar to the Linux case. The first thing that the `time·now` assembly does is check whether it can use [QPC](https://docs.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps) to obtain the time using the [`nowQPC`](https://github.com/golang/go/blob/1d967ab95c43b6b8810ca53d6a18aff85e59a3b6/src/runtime/os_windows.go#L514-L526) function.

    	CMPB	runtime·useQPCTime(SB), $0
    	JNE	useQPC
    
    useQPC:
    	JMP	runtime·nowQPC(SB)
    	RET


If that’s not the case the code will try to use the following two addresses from the [`KUSER_SHARED_DATA`](http://www.nirsoft.net/kernel_struct/vista/KUSER_SHARED_DATA.html) structure, also known as `SharedUserData`. This structure holds some kernel information that is shared with user-mode, in order to avoid multiple transitions to the kernel, similar to what vDSO does.

    #define _INTERRUPT_TIME 0x7ffe0008
    #define _SYSTEM_TIME 0x7ffe0014
    
    KSYSTEM_TIME InterruptTime;
    KSYSTEM_TIME SystemTime;


The part which uses these two addresses is presented below. The information is fetched as [`KSYSTEM_TIME`](http://www.nirsoft.net/kernel_struct/vista/KSYSTEM_TIME.html) structs.

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


The issue with `_SYSTEM_TIME` is that it is of lower resolution, having an update period of 100 nanoseconds; and that’s probably why QPC time is prefered.

It’s been so long since I’ve worked with Windows, but [here’s](https://www.matteomalvica.com/minutes/windows_kernel/#kuser-shared-data) [some](moz-extension://3b9164ce-6b20-1541-a720-5d6cc82dcebd/www.uninformed.org/?v=3&a=4&t=pdf) [more](https://gist.github.com/alastorid/ecaeba6b3f2a521c25b28efd81ac0a2d) [resources](http://uninformed.org/index.cgi?v=2&a=2&p=20) [if](https://gist.github.com/m-schwenk/d312c02ec6b230c19dc2) [you’re](https://docs.microsoft.com/en-us/windows/win32/api/profileapi/nf-profileapi-queryperformancecounter) [interested](https://docs.microsoft.com/en-us/uwp/api/windows.perception.perceptiontimestamp.systemrelativetargettime?view=winrt-19041).

Mystery No.2
------------

What was that again? Oh, we haven’t figured _where does Local come from?_

The exported `Local *Location` symbol points to the `localLoc` address at first.

    var Local *Location = &localLoc


If this address is nil, as we mentioned, the UTC location is returned. Otherwise, the code attempts to set up the package-level `localLoc` variable by using the `sync.Once` primitive the first time that location information is needed.

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


The [`initLocal()`](https://github.com/golang/go/blob/release-branch.go1.16/src/time/zoneinfo_unix.go#L28-L69) function looks for the contents of `$TZ` to find a time zone to use.

If the `$TZ` variable is unset, Go uses a system default file such as `/etc/localtime` to load the timezone. If it is set, but empty, it uses UTC, while if it contains a non-valid timezone, it tries to find a file with the same name in the system timezone directory. The default sources that will be searched are

    var zoneSources = []string{
    	"/usr/share/zoneinfo/",
    	"/usr/share/lib/zoneinfo/",
    	"/usr/lib/locale/TZ/",
    	runtime.GOROOT() + "/lib/time/zoneinfo.zip",
    }


There are platform-specific `zoneinfo_XYZ.go` files to find the default timezone using a similar logic eg. for Windows or WASM. In the past, when I wanted to use timezones in a stripped-down container image all I had to do was to add the following line to the Dockerfile when building from a Unix-like system.

    COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo


On the other hand, in cases where we cannot control the build environment, there’s the `tzdata` package which provides an _embedded copy_ of the timezone database. If this package is imported anywhere or we build with the `-tags timetzdata` flag, the program size will be increased by about ~450KB, but will also provide a fallback in cases that Go cannot find `tzdata` file on the host system.

Finally, we can set up the location manually from our code by using the [`LoadLocation`](https://github.com/golang/go/blob/release-branch.go1.16/src/time/zoneinfo.go#L617-L664) function, eg. for testing purposes.

Outro
-----

That’s all for today! I hope y’all either learned something new, or had some fun and you’re now more confident to jump into the Go codebase!

Feel free to reach out for comments, corrections or advice via email or on [Twitter](https://twitter.com/tpaschalis_).

See you soon, take care of yourself!

Bonus : What’s with `funcname1` in Go?
--------------------------------------

Throughout the Go codebase, you’ll see many references to `funcname1()` or `funcname2()`, especially as you’re getting to lower-level code.

As far as I understand they serve two purposes; they help keep up with Go’s Compatibility Promise by more easily altering the internals of an unexported function, and also to ‘group’ similar and/or chaining functionality together.

While someone may scoff at this, I think it’s a simple and _great_ idea to keep the code readable and maintainable


[Source](https://tpaschalis.github.io/golang-time-now/)
