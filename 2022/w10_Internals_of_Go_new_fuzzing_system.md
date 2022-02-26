# Internals of Go's new fuzzing system

- 原文地址：https://jayconrod.com/posts/123/internals-of-go-s-new-fuzzing-system
- 原文作者：jayconrod
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2022/w10_Internals_of_Go_new_fuzzing_system.md
- 译者：[cvley](https://github.com/cvley)
- 校对：[](https://github.com/)

Go 1.18 is coming out soon, hopefully in a few weeks. It's a huge release with a lot to look forward to, but native fuzzing has a special place in my heart. (I'm super-biased of course: before I [left Google](https://jayconrod.com/posts/122/leaving-google), I worked with Katie Hockman and Roland Shoemaker to build the fuzzing system). Generics are cool too, I guess, but having fuzzing integrated into the `testing` package and `go test` will make fuzz testing more accessible to everyone which makes it easier to write secure, correct code in Go.

Not much has been written yet on how Go's fuzzing system actually works, so I'll talk a bit about that here. If you'd like to try it out, [Getting started with fuzzing](https://go.dev/doc/tutorial/fuzz) is a great tutorial.

## What is fuzzing?

Fuzzing is a testing technique where the testing infrastructure calls your code with randomly generated inputs to check that it produces correct results or reasonable errors. Fuzz testing complements unit testing, where you test that your code produces the correct outputs, given a static set of inputs. Unit testing is limited in that you only really test with expected inputs; fuzz testing is great at discovering _unexpected_ inputs that expose weird behavior. A good fuzzing system also instruments the code being tested so it can efficiently generate inputs that expand code coverage.

Fuzz testing is commonly used to check parsers and validators, especially anything used in a security context. Fuzzing is great at finding bugs that cause security issues, like invalid lengths in a binary encoding, truncated input, integer overflows, invalid unicode, and more.

There are other ways to use fuzzing, too. For example, differential fuzzing verifies that two implementations of the same thing have the same behavior by feeding in the same random inputs to both implementations and checking that the outputs match. You can also use fuzzing for user interface "monkey" testing: the fuzzing engine could produce random taps, keystrokes, and clicks, and the test verifies that the app doesn't crash.

## What's happening with fuzzing in Go

Fuzzing is not new to Go. [go-fuzz](https://github.com/dvyukov/go-fuzz) is probably the most widely used tool today, and we certainly borrowed from its design when developing native fuzzing. The new thing in Go 1.18 is that fuzzing is integrated directly into `go test` and the `testing` package. The interface is very similar to the testing interface, [`testing.T`](https://pkg.go.dev/testing@go1.18beta2#T).

For example, if you have a function named `ParseSomething`, you could write a fuzz test like the one below. This checks that for any random input, `ParseSomething` either succeeds or returns a `ParseError`.

```
package parser

import (
"errors"
"testing"
)

var seeds = [][]byte{
nil,
[]byte("123"),
[]byte("(12)"),
}

func FuzzParseSomething(f *testing.F) {
for _, seed := range seeds {
f.Add(seed)
}
f.Fuzz(func(t *testing.T, input []byte) {
err := ParseSomething(input)
if err == nil {
return
}
if parseErr := (*ParseError)(nil); !errors.As(err, &parseErr) {
t.Fatal(err)
}
})
}
```

When `go test` is run normally (without the `-fuzz` flag), `FuzzParseSomething` is treated like a unit test. The fuzz function provided to [`F.Fuzz`](https://pkg.go.dev/testing@go1.18beta2#F.Fuzz) is called with inputs from the seed corpus: inputs registered with [`F.Add`](https://pkg.go.dev/testing@go1.18beta2#F.Add) and inputs read from files in `testdata/corpus/FuzzParseSomething`. If the fuzz function panics or calls [`T.Fail`](https://pkg.go.dev/testing@go1.18beta2#T.Fail), the test fails, and `go test` exits with a non-zero status.

Fuzzing can be enabled by running `go test` with the `-fuzz` flag, like this:

```
go test -fuzz=FuzzParseSomething
```

In this mode, the fuzzing system will call the fuzz function with randomly generated inputs, using the inputs from the seed corpus and a cached corpus as a starting point. Generated inputs that expand coverage are minimized and added to the cached corpus. Generated inputs that cause errors are minimized and added to the seed corpus, effectively becoming new regression test cases. Later `go test` runs will fail until the problem is fixed, even when fuzzing is not enabled.

Again, there's nothing really novel here compared with other systems. The strength is in the familiarity of the interface and its ease of use. Writing your first fuzz test is easy, since fuzzing follows the conventions of the `testing` package. There's no need for everyone on a team to install and learn a new tool.

## How does the fuzzing system work?

You may already know that `go test` builds a test executable for each package being tested, then runs those executables to get test and benchmark results. Fuzzing follows this pattern, though there are some differences.

When `go test` is invoked with the `-fuzz` flag, `go test` compiles the test executable with additional coverage instrumentation. The Go compiler already had instrumentation support for [libFuzzer](https://llvm.org/docs/LibFuzzer.html), so we reused that. The compiler adds an 8-bit counter to each basic block. The counter is fast and approximate: it wraps on overflow, and there's no synchronization across threads. (We had to tell the race detector not to complain about writes to these counters). The counter data is used at run-time by the [internal/fuzz](https://pkg.go.dev/internal/fuzz) package, where most of the fuzzing logic is.

After `go test` builds an instrumented executable, it runs it as usual. This is called the coordinator process. This process is started with most of the flags that were passed to `go test`, including `-fuzz=pattern`, which it uses to identify which target to fuzz; for now, only one target may be fuzzed per `go test` invocation ([#46312](https://github.com/golang/go/issues/46312)). When that target calls [`F.Fuzz`](https://pkg.go.dev/testing@go1.18beta2#F.Fuzz), control is passed to [`fuzz.CoordinateFuzzing`](https://pkg.go.dev/internal/fuzz#CoordinateFuzzing), which initializes the fuzzing system and begins the coordinator event loop.

The coordinator starts several worker processes, which run the same test executable and perform the actual fuzzing. Workers are started with an undocumented command line flag that tells them to be workers. Fuzzing must be done in separate processes so that if a worker process crashes entirely, the coordinator can still find and record the input that caused the crash.

![Diagram showing the relationship between fuzzing processes. At the top is a box showing "go test (cmd/go)". An arrow points downward to a box labelled "coordinator (test binary)". From that, three arrows point downward to three boxes labelled "worker (test binary)".](https://jayconrod.com/images/fuzz-processes.svg)

The coordinator communicates with each worker using an improvised JSON-based RPC protocol over a pair of pipes. The protocol is pretty basic because we didn't need anything sophisticated like gRPC, and we didn't want to introduce anything new into the standard library. Each worker also keeps some state in a memory mapped temporary file, shared with the coordinator. Mostly this is just an iteration count and random number generator state. If the worker crashes entirely, the coordinator can recover its state from shared memory without requiring the worker to politely send a message over the pipes first.

After the coordinator starts the workers, it gathers baseline coverage by sending workers inputs from the seed corpus and the fuzzing cache corpus (in a subdirectory of `$GOCACHE`). Each worker runs its given input, then reports back with a snapshot of its coverage counters. The coordinator coarsens and merges these counters into a combined coverage array.

Next, the coordinator sends out inputs from the seed corpus and cached corpus for fuzzing: each worker is given an input and a copy of the baseline coverage array. Each worker then randomly mutates its input (flipping bits, deleting or inserting bytes, etc.) and calls the fuzz function. In order to reduce communication overhead, each worker can keep mutating and calling for 100 ms without further input from the coordinator. After each call, the worker checks whether an error was reported (with [`T.Fail`](https://pkg.go.dev/testing@go1.18beta2#T.Fail)) or new coverage was found compared with the baseline coverage array. If so, the worker reports the "interesting" input back to the coordinator immediately.

When the coordiantor receives an input that produces new coverage, it compares the worker's coverage to the current combined coverage array: it's possible that another worker already discovered an input that provides the same coverage. If so, the new input is discarded. If the new input actually does provide new coverage, the coordinator sends it back to a worker (perhaps a different worker) for minimization. Minimization is like fuzzing, but the worker performs random mutations to create a smaller input that still provides at least some new coverage. Smaller inputs tend to be faster, so it's worth spending the time to minimize up front to make the fuzzing process faster later. The worker process reports back when it's done minimizing, even if it failed to find anything smaller. The coordinator adds the minimized input to the cached corpus and continues. Later on, the coordinator may send the minimized input out to workers for further fuzzing. This is how the fuzzing system adapts to find new coverage.

When the coordinator receives an input that causes an error, it again sends the input back to workers for minimization. In this case, a worker attempts to find a smaller input that still causes an error, though not necessarily the same error. After the input is minimized, the coordinator saves it into `testdata/corpus/$FuzzTarget`, shuts worker processes down gracefully, then exits with a non-zero status.

![Diagram showing communication between coordinator and worker. Two arrows point down: the left is labelled "coordinator", the right is labelled "worker". Three pairs of horizontal arrows point from the coordinator to the worker and back. The top pair is labelled "baseline coverage", the middle is labelled "fuzz", the bottom is labelled "minimize".](https://jayconrod.com/images/fuzz-communication.svg)

If a worker process crashes while fuzzing, the coordinator can recover the input that caused the crash using the input sent to the worker, and the worker's RNG state and iteration count (both left in shared memory). Crashing inputs are generally not minimized, since minimization is a highly stateful process, and each crash blows that state away. It is [theoretically possible](https://github.com/golang/go/issues/48163) but hasn't been done yet.

Fuzzing usually continues until an error is discovered or the user interrupts the process by pressing Ctrl-C or the deadline set with the `-fuzztime` flag is passed. The fuzzing engine handles interrupts gracefully, whether they are delivered to the coordinator or worker processes. For example, if a worker is interrupted while minimizing an input that caused an error, the coordinator will save the unminimized input.

## Future of fuzzing

I'm very excited for this release, though I have to admit, Go's new fuzzing engine is still a ways from reaching feature and performance parity with other fuzzing systems. Many improvements are possible, but it's already in a useful state, and the API is stable. I'm glad it's shipping now.

You can find a list of [open issues](https://github.com/golang/go/issues?q=is%3Aissue+is%3Aopen+label%3Afuzz) on the issue tracker with the `fuzz` label. Those with the [Go1.19](https://github.com/golang/go/issues?q=is%3Aissue+is%3Aopen+label%3Afuzz+milestone%3AGo1.19) milestone are considered the highest priority, though issues may get reprioritized depending on user feedback and developer bandwidth.

Anyway, go try it out, report bugs, and request features! If you find any good bugs in your own code (or someone else's!), add them to the [Fuzzing trophy case](https://github.com/golang/go/wiki/Fuzzing-trophy-case) on the Go wiki.
