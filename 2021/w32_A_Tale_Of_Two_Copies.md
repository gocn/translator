# A Tale Of Two Copies?
- 原文地址：https://storj.io/blog/a-tale-of-two-copies
- 原文作者：Jeff Wendling
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w32_A_Tale_Of_Two_Copies
- 译者：[haoheipi](https://github.com/haoheipi)
- 校对：[]()

It was the best of times, it was the worst of times. That's when I hit a performance mystery that sent me down a multi-day rabbit hole of adventure. I was writing some code to take some entries, append them into a fixed size in-memory buffer, and then flush that buffer to disk when it was full. The main bit of code looked a little something like this:

```
type Buffer struct {
	fh  *os.File
	n   uint
	buf [numEntries]Entry
}

func (b *Buffer) Append(ent Entry) error {
	if b.n < numEntries-1 {
		b.buf[b.n] = ent
		b.n++
		return nil
	}
	return b.appendSlow(ent)
}
```

with the idea being that when there's space in the buffer, we just insert the entry and increment a counter, and when we're full, it falls back to the slower path that writes to disk. Easy, right? Easy...


## The Benchmark

I had a question about what size the entries should be. The minimum size I could pack them into was 28 bytes, but that's not a nice power of 2 for alignment and stuff, so I wanted to compare it to 32 bytes. Rather than just relying on my intuition, I decided to write a benchmark. The benchmark would Append a fixed number of entries per iteration (100,000) and the only thing changing would be if the entry size was 28 or 32 bytes.

Even if I'm not relying on my intuition, I find it fun and useful to try to predict what will happen anyway. And so, I thought to myself:

> Everyone knows that I/O is usually dominating over small CPU potential inefficiencies. The 28 byte version writes less data and does less flushes to disk than the 32 byte version. Even if it's somehow slower filling the memory buffer, which I doubt, that will be more than made up for by the extra writes that happen.

Maybe you thought something similar, or maybe something completely different. Or maybe you didn't sign up to do thinking right now and just want me to get on with it. And so, I ran the following benchmark:

```
func BenchmarkBuffer(b *testing.B) {
	fh := tempFile(b)
	defer fh.Close()

	buf := &Buffer{fh: fh}
	now := time.Now()
	ent := Entry{}

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		fh.Seek(0, io.SeekStart)

		for i := 0; i < 1e5; i++ {
			_ = buf.Append(ent)
		}
		_ = buf.Flush()
	}

	b.ReportMetric(float64(time.Since(now).Nanoseconds())/float64(b.N)/1e5, "ns/key")
	b.ReportMetric(float64(buf.flushes)/float64(b.N), "flushes")
}
```


## Confusion

And here are the results: 

```
BenchmarkBuffer/28       734286 ns/op      171.0 flushes      7.343 ns/key
BenchmarkBuffer/32       436220 ns/op      196.0 flushes      4.362 ns/key
```

That's right, a nearly 2x difference in performance where the benchmark writing to disk MORE is FASTER!

And so began my journey. The following is my best effort in remembering the long, strange trip I took diagnosing what I thought was happening. Spoiler alert: I was wrong a lot, and for a long time.


# The Journey

## CPU Profiles

CPU profiles have a huge power to weight ratio. To collect them from a Go benchmark, all you have to do is specify `-cpuprofile=<some file>` on the command line and that's it. So of course this is the first thing I reached for. 

One thing to keep in mind, though, is that Go benchmarks by default will try to run for a fixed amount of time, and if one benchmark takes longer to do its job vs another, you get less iterations of it. Since I wanted to compare the results more directly, I made sure to also pass a fixed number of iterations to the command with `-benchtime=2000x`.

So let's take a look at these profiles. First, the 32 byte version:

```
       .          .     24:func (b *Buffer) Append(ent Entry) error {
      30ms       30ms     25:	if b.n < numEntries-1 {
     110ms      110ms     26:		b.buf[b.n] = ent
      90ms       90ms     27:		b.n++
         .          .     28:		return nil
         .          .     29:	}
      10ms      520ms     30:	return b.appendSlow(ent)
         .          .     31:}
```

The first column shows the amount of time spent on that line just in the context of the shown function, and the second column is the amount of time spent on that line including any functions it may have called.

From that, we can see that, as expected, most of the time is spent flushing to disk in appendSlow compared to writing to the in memory buffer.

And now here's the 28 byte version:

```
         .          .     24:func (b *Buffer) Append(ent Entry) error {
      20ms       20ms     25:	if b.n < numEntries-1 {
     840ms      840ms     26:		b.buf[b.n] = ent
      20ms       20ms     27:		b.n++
         .          .     28:		return nil
         .          .     29:	}
         .      470ms     30:	return b.appendSlow(ent)
         .          .     31:}
```

A couple of things stand out to me here. First of all, WHAT? Second of all, it spends less time flushing to disk compared to the 32 byte version. That's at least expected because it does that less often (171 vs 196 times). And finally, WHAT?

Maybe the penalty for writing unaligned memory was worse than I thought. Let's take a look at the assembly to see what instruction it's stuck on.


## The Assembly

Here's the section of code responsible for the 840ms on line 26 in the above profile:

```
         .          .     515129: IMULQ $0x1c, CX, CX          (1)
      90ms       90ms     51512d: LEAQ 0xc0(SP)(CX*1), CX      (2)
         .          .     515135: MOVUPS 0x7c(SP), X0          (3)
     670ms      670ms     51513a: MOVUPS X0, 0(CX)             (4)
      80ms       80ms     51513d: MOVUPS 0x88(SP), X0          (5)
         .          .     515145: MOVUPS X0, 0xc(CX)           (6)
```

If you've never read assembly before, this may be a bit daunting, so I've numbered the lines and will provide a brief explanation. The most important bits to know are that `CX` , `SP` and `X0` are registers, and the syntax `0x18(CX)` means the value at address `CX` + `0x18` . Armed with that knowledge, we can understand the lines:

1. Multiply the `CX` register by `0x1c` and store it into `CX` . `0x1c` is the hex encoding of the decimal value 28.

    1. This computes the address we'll be storing the entry into. It computes `0xc0` + `SP` + `(CX*1)` and stores it into `CX` . From this, we deduce that the start of the entry array is at `0xc0(SP)` .

2. This loads 16 bytes starting at `0x7c(SP)` and stores it into `X0` .

3. This stores the 16 bytes we just loaded into `0(CX)` .

4. This loads 16 bytes starting at `0x88(SP)` and stores it into `X0` .

5. This stores the 16 bytes we just loaded into `0xc(CX)` .

I don't know about you, but I saw no reason why line 4 should have so much weight compared to the other lines. So, I compared it to the 32 byte version to see if the generated code was different:

```
      40ms       40ms     515129: SHLQ $0x5, CX
      10ms       10ms     51512d: LEAQ 0xc8(SP)(CX*1), CX
         .          .     515135: MOVUPS 0x80(SP), X0
      10ms       10ms     51513d: MOVUPS X0, 0(CX)
      40ms       40ms     515140: MOVUPS 0x90(SP), X0
      10ms       10ms     515148: MOVUPS X0, 0x10(CX)
```

It looks like the only difference, aside from almost no time at all being spent in these instructions, is the SHLQ vs the IMULQ. The former is doing a "left shift" of 5, which effectivly multiplies by 2 to the 5th power, or 32, and the latter, as we previously saw, multiplies by 28. Could this possibly be the performance difference?

## Pipelines and Ports

Modern CPUs are complex beasts. Maybe you have the mental model that your CPU reads instructions in and executes them one at a time as I once did. That couldn't be further from the truth. Instead, they execute multiple instructions at once, possibly out of order, in a [pipeline](https://en.wikipedia.org/wiki/Instruction_pipelining). But it gets even better: they have limits on how many of each kind of instruction can be run simultaneously. This is done by the CPU having multiple "ports", and certain instructions require and can run on different subsets of these ports.

So what does that have to do with IMULQ vs SHLQ? Well, you may have noticed that the LEAQ following the IMULQ/SHLQ has a multiply in it (CX*1 ). But, because there aren't infinite ports, there must be a limited number of ports able to do multiplies.

The LLVM project has lots of tools to help you understand what computers do, and one of them is a tool called [llvm-mca](https://www.llvm.org/docs/CommandGuide/llvm-mca.html#how-llvm-mca-works) . Indeed, if we run the two first instructions of the 32 and 28 byte versions through llvm-mca , it gives us an idea of what ports will be used when they are executed:

```
Resource pressure by instruction (32 byte version):
[2]    [3]     [7]    [8]     Instructions:
0.50    -       -     0.50    shlq  $5, %rcx
 -     0.50    0.50    -      leaq  200(%rsp,%rcx), %rcx

Resource pressure by instruction (28 byte version):
[2]    [3]     [7]    [8]    Instructions:
 -     1.00     -      -     imulq  $28, %rcx, %rcx
 -      -      1.00    -     leaq   192(%rsp,%rcx), %rcx
```

The numbers are what percent of the time each instruction ran on the port (here, numbered 2, 3, 7 and 8) when executed in a loop.

So that's saying that in the 32 byte version, the SHLQ ran on port 2 half the time and port 8 the other half, and the LEAQ ran on port 3 half the time and port 7 the other half. This is implying that it can have 2 parallel executions at once. For example, on one iteration, it can use ports 2 and 3, and on the next iteration it can use ports 7 and 8, even if ports 2 and 3 are still being used. However, for the 28 byte version, the IMULQ must happen solely on port 3 due to the way the processor is built, which in turn limits the maximum throughput.

And for a while, this is what I thought was happening. In fact, a first draft of this very blog post had that as the conclusion, but the more I thought about it, the less good of an explanation it seemed.


## Trouble in Paradise

Here are some thoughts that you may be having:

1. In the worst case, that can only be a 2x speed difference.

2. Aren't there other instructions in the loop? That has to make it so that it's much less than 2x in practice.

3. The 32 byte version spends 230ms in the memory section and the 28 byte version spends 880ms.

4. That is much bigger than 2x bigger.

5. Oh no.

Well, maybe that last one was just me. With those doubts firmly in my mind, I tried to figure out how I could test to see if it was because of the IMULQ and SHLQ. Enter `perf` .


## Perf

[perf](https://perf.wiki.kernel.org/index.php/Main_Page) is a tool that runs on linux that allows you to execute programs and expose some detailed counters that CPUs keep about how they executed instructions (and more!). Now, I had no idea if there was a counter that would let me see something like "the pipeline stalled because insufficient ports or whatever", but I did know that it had counters for like, everything.

If this were a movie, this would be the part where the main character is shown trudging through a barren desert, sun blazing, heat rising from the earth, with no end in sight. They'd see a mirage oasis and jump in, gulping down water, and suddenly realize it was sand.

A quick estimate shows that perf knows how to read over 700 different counters on my machine, and I feel like I looked at most of them. Take a look at [this huge table](https://perfmon-events.intel.com/skylake.html) if you're interested. I couldn't find any counters that could seem to explain the large difference in speed, and I was starting to get desparate.


## Binary Editing for Fun and Profit

At this point, I had no idea what the problem was, but it sure seemed like it wasn't port contention like I thought. One of the only other things that I thought it could be was alignment. CPUs tend to like to have memory accessed at nice multiples of powers of 2, and 28 is not one of those, and so I wanted to change the benchmark to write 28 byte entries but at 32 byte offsets.

Unfortunately, this wasn't as easy as I hoped. The code under test is very delicately balanced with respect to the Go compiler's inliner. Basically any changes to Append cause it to go over the threshold and stop it from being inlined, which really changes what's being executed.

Enter binary patching. It turns out that in our case, the IMULQ instruction encodes to the same number of bytes as the SHLQ. Indeed, the IMULQ encodes as `486bc91c` , and the SLHQ as `48c1e105` . So it's just a simple matter of replacing those bytes and running the benchmark. I'll (for once) spare you the details of how I edited it (Ok, I lied: I hackily used dd ). The results sure did surprise me:

```
BenchmarkBuffer/28@32    813529 ns/op      171.0 flushes      8.135 ns/key
```

I saw the results and felt defeated. It wasn't the IMULQ making the benchmark go slow. That benchmark has no IMULQ in it. It wasn't due to unaligned writes. The slowest instruction was written with the same alignment as in the 32 byte version as we can see from the profiled assembly:

```
         .          .     515129: SHLQ $0x5, CX
      60ms       60ms     51512d: LEAQ 0xc0(SP)(CX*1), CX
         .          .     515135: MOVUPS 0x7c(SP), X0
     850ms      850ms     51513a: MOVUPS X0, 0(CX)
     120ms      120ms     51513d: MOVUPS 0x88(SP), X0
         .          .     515145: MOVUPS X0, 0xc(CX)
```

What was left to try?


# A Small Change

Sometimes when I have no idea why something is slow, I try writing the same code but in a different way. That may tickle the compiler just right to cause it to change which optimizations it can or can't apply, giving some clues as to what's going on. So in that spirit I changed the benchmark to this:

```
func BenchmarkBuffer(b *testing.B) {
	// ... setup code

	for i := 0; i < b.N; i++ {
		fh.Seek(0, io.SeekStart)

		for i := 0; i < 1e5; i++ {
			_ = buf.Append(Entry{})
		}
		_ = buf.Flush()
	}

	// .. teardown code
}
```

It's hard to spot the difference, but it changed to passing a new entry value every time instead of passing the ent variable manually hoisted out of the loop. I ran the benchmarks again.

```
BenchmarkBuffer/28       407500 ns/op      171.0 flushes      4.075 ns/key
BenchmarkBuffer/32       446158 ns/op      196.0 flushes      4.462 ns/key
```

IT DID SOMETHING? How could that change possibly cause that performance difference? It's finally running faster than the 32 byte version! As usual, time to look at the assembly.

```
      50ms       50ms     515109: IMULQ $0x1c, CX, CX
         .          .     51510d: LEAQ 0xa8(SP)(CX*1), CX
         .          .     515115: MOVUPS X0, 0(CX)
     130ms      130ms     515118: MOVUPS X0, 0xc(CX)
```

It's no longer loading the value from the stack to store it into the array, and instead just storing directly into the array from the already zeroed register. But we know from all the pipeline analysis done earlier that the extra loads should effectively be free, and the 32 byte version confirms that. It didn't get any faster even though it also is no longer loading from the stack.

So what's going on?


## Overlapping Writes

In order to explain this idea, it's important to show the assembly of the full inner loop instead of just the code that writes the entry to the in-memory buffer. Here's a cleaned up and annotated version of the slow 28 byte benchmark inner loop:

```
loop:
  INCQ AX                     (1)
  CMPQ $0x186a0, AX
  JGE exit

  MOVUPS 0x60(SP), X0         (2)
  MOVUPS X0, 0x7c(SP)
  MOVUPS 0x6c(SP), X0
  MOVUPS X0, 0x88(SP)

  MOVQ 0xb8(SP), CX           (3)
  CMPQ $0x248, CX
  JAE slow

  IMULQ $0x1c, CX, CX         (4)
  LEAQ 0xc0(SP)(CX*1), CX
  MOVUPS 0x7c(SP), X0         (5)
  MOVUPS X0, 0(CX)
  MOVUPS 0x88(SP), X0
  MOVUPS X0, 0xc(CX)

  INCQ 0xb8(SP)               (6)
  JMP loop

slow:
   // ... slow path goes here ...

exit:
```

1. Increment `AX` and compare it to 100,000 exiting if it's larger.

2. Copy 28 bytes on the stack from offsets `[0x60, 0x7c]` to offsets `[0x7c, 0x98] `.

3. Load the memory counter and see if we have room in the memory buffer

4. Compute where the entry will be written to in the in-memory buffer.

5. Copy 28 bytes on the stack at offsets `[0x7c, 0x98]` into the in-memory buffer.

6. Increment the memory counter and loop again.

Steps 4 and 5 are what we've been looking at up to now.

If step 2 seems silly and redundant, that's because it is. There's no reason to copy a value on the stack to another location on the stack and then load from that copy on the stack into the in-memory buffer. Step 5 could have just used offsets `[0x60, 0x7c]` instead and step 2 could have been eliminated. The Go compiler could be doing a better job here.

But that shouldn't be why it's slow, right? The 32 byte code does almost the exact same silly thing and it goes fast, because of pipelines or pixie dust or something. What gives?

There's one crucial difference: the writes in the 28 byte case overlap. The MOVUPS instruction writes 16 bytes at a time, and as everyone knows, 16 + 16 is usually more than 28. So step 2 writes to bytes `[0x7c, 0x8c]` and then writes to bytes `[0x88, 0x98]` . This means the range `[0x88, 0x8c]` was written to twice. Here's a helpful ASCII diagram:

```
0x7c             0x8c
├────────────────┤
│  Write 1 (16b) │
└───────────┬────┴──────────┐
            │ Write 2 (16b) │
            ├───────────────┤
            0x88            0x98
```


## Store Forwarding

Remember how CPUs are complex beasts? Well it gets even better. An optimization that some CPUs do is they have something called a "[write buffer](https://en.wikipedia.org/wiki/Write_buffer)". You see, memory access is often the slowest part of what CPUs do. Instead of, you know, actually writing the memory when the instruction executes, CPUs place the writes into a buffer first. I think the idea is to coalesce a bunch of small writes into larger sizes before flushing out to the slower memory subsystem. Sound familiar?

So now it has this write buffer buffering all of the writes. What happens if a read comes in for one of those writes? It would slow everything down if had to wait for that write to actually happen before reading it back out, so instead it tries to service the read from the write buffer directly if possible, and no one is the wiser. You clever little CPU. This optimization is called [store forwarding](https://easyperf.net/blog/2018/03/09/Store-forwarding).

But what if those writes overlap? It turns out that, on my CPU at least, this inhibits that "store forwarding" optimization. There's even a perf counter that keeps track of when this happens: [ld_blocks.store_forward](https://perfmon-events.intel.com/index.html?pltfrm=skylake.html&evnt=LD_BLOCKS.STORE_FORWARD).

Indeed, the documentation about that counter says

> Counts the number of times where store forwarding was prevented for a load operation. The most common case is a load blocked due to the address of memory access (partially) overlapping with a preceding uncompleted store.

Here's how often that counter hits for the different benchmarks so far where "Slow" means that the entry is constructed outside of the loop, and "Fast" means that the entry is constructed inside of the loop on every iteration:

```
BenchmarkBuffer/28-Slow      7.292 ns/key      1,006,025,599 ld_blocks.store_forward
BenchmarkBuffer/32-Slow      4.394 ns/key          1,973,930 ld_blocks.store_forward
BenchmarkBuffer/28-Fast      4.078 ns/key          4,433,624 ld_blocks.store_forward
BenchmarkBuffer/32-Fast      4.369 ns/key          1,974,915 ld_blocks.store_forward
```

Well, a billion is usually bigger than a million. Break out the champagne.


# Conclusion

After all of that, I have a couple of thoughts.

Benchmarking is hard. People often say this, but maybe the only thing harder than benchmarking is adequately conveying how hard benchmarking is. Like, this was closer to the micro-benchmark than macro-benchmark side of things but still included performing millions of operations including disk flushes and actually measured a real effect. But at the same time, this would almost never be a problem in practice. It required the compiler to spill a constant value to the stack unnecessarily very closely to the subsequent read in a tight inner loop to notice. Doing any amount of real work to create the entries would cause this effect to vanish.

A recurring theme as I learn more about how CPUs work is that the closer you get to the "core" of what it does, the leakier and more full of edge cases and hazards it becomes. Store forwarding not working if there was a partially overlapping write is one example. Another is that the caches aren't [fully associative](https://en.wikipedia.org/wiki/CPU_cache#Associativity), so you can only have so many things cached based on their memory address. Like, even if you have 1000 slots available, if all your memory accesses are multiples of some factor, they may not be able to use those slots. [This blog post](https://danluu.com/3c-conflict/) has a great discussion. Totally speculating, but maybe this is because you have less "room" to solve those edge cases when under ever tighter physical constraints.

Before now, I've never been able to concretely observe the CPU slowing down from port exhaustion issues in an actual non-contrived setting. I still haven't. I've heard the adage that you can imagine every CPU instruction taking 0 cycles except for the ones that touch memory. As a first approximation, it seems pretty true.

I've put up the full code sample in [a gist](https://gist.github.com/zeebo/4c9e28ac277c74ae450ad1bff8068f93) for your viewing/downloading/running/inspecting pleasure.

Often, things are more about the journey than the destination, and I think that's true here, too. If you made it this far, thanks for coming along on the journey with me, and I hope you enjoyed it. Until next time.