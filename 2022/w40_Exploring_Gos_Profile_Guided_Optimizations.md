# Exploring Go's Profile-Guided Optimizations

Making code faster without modifying it using Profile-Guided Optimizations.



At Polar Signals 100% of our backend code is written in Go, so we have been very excited ever since the momentum on Profile-Guided Optimizations (PGO) picked up in late 2021, when the Go compiler team at Google [started prototyping it](https://github.com/golang/go/issues/28262#issuecomment-945837783). In this blog post we’ll go over what PGO is, how it works, and why it’s exciting.

PGO support in the Go compiler is currently slated for the 1.20 release (based on previous releases probably going out February/March 2023, and the [issue now being in the active column](https://github.com/golang/go/issues/55022#issuecomment-1254050321)).

## What is PGO?

PGO boils down to using runtime information in the form of profiling data to apply optimizations at compile time that are not generally a good idea, but informed by the provided runtime information, can be expected to have a net positive impact.

The first Profile-Guided Optimization the Go compiler is introducing is using profiling data to inline functions that may not be inlined otherwise. If you’re unfamiliar with function inlining or want a refresher, check out our blog post on [Why Compiler Function Inlining Matters](https://www.polarsignals.com/blog/posts/2021/12/15/why-compiler-function-inlining-matters/).

So how does PGO work with function inlining? The Go compiler has a heuristic of a function’s cost of inlining. By default, if the cost of inlining is higher than 80, it will not be inlined. However, with PGO even functions that have a higher inlining cost than 80 may still be inlined, if the provided profiling data suggests that that this function would still benefit from inlinining.

Let’s look at a concrete example using the currently proposed changes to the Go compiler at the time of writing this article.

If you would like to follow along with this blog post and try PGO on your codebase or just replicate what this blog post demonstrates, checkout the patch and compile the Go runtime with it:

```bash
git clone https://go.googlesource.com/go
cd go
git fetch https://go.googlesource.com/go refs/changes/63/429863/3 && git checkout -b change-429863 FETCH_HEAD
cd src
./all.bashcd 
..export PATH="$(pwd)/bin:$PATH" # or add the path to your bashrc/zshrc
```

Conveniently the patch for the compiler contains a small code sample that demonstrates PGO inlining for testing purposes.

```bash
cd src/cmd/compile/internal/test/testdata/pgo/inline
```

Let’s run it and have the go benchmark output profiling data that we can then use in subsequent calls to enable PGO.

```bash
go test -o inline_hot.test -bench=. -cpuprofile inline_hot.pprof
```

First let’s have a look at what functions were inlined without PGO:

> The `-run=none -tags=”” -gcflags=”-m -m”` flags allow us to just compile the tests without running them, while also outputting inlining cost and decisions the compiler makes.

```bash
go test -run=none -tags='' -timeout=9m0s -gcflags="-m -m" 2>&1 | grep "can inline"
./inline_hot.go:15:6: can inline D with cost 7 as: func(uint) int { return int((i + (wSize - 1)) >> lWSize) }
./inline_hot.go:19:6: can inline N with cost 20 as: func(uint) *BS { bs = &BS{...}; return bs }
./inline_hot.go:28:6: can inline (*BS).S with cost 14 as: method(*BS) func(uint) *BS { b.s[i >> lWSize] |= 1 << (i & (wSize - 1)); return b }
./inline_hot.go:40:6: can inline T with cost 12 as: func(uint64) uint { return uint(jn[v & -v * 0x03f79d71b4ca8b09 >> 58]) }
./inline_hot_test.go:5:6: can inline BenchmarkA with cost 60 as: func(*testing.B) { benchmarkB(b) }
_testmain.go:37:6: can inline init.0 with cost 3 as: func() { testdeps.ImportPath = "cmd/compile/internal/test/testdata/pgo/inline" }
```

As we can see all the inlined functions have a cost of 80 or less. Now let’s run that again with PGO enabled and see what functions are now inlined. Judging by an ongoing conversation by the Go team on the tracking issue it appears that the flag to enable PGO won’t stay like this, but using this patch, it can be enabled using the `-gcflags=”-pgoprofile <file>”` flag:

```bash
go test -run=none -tags='' -timeout=9m0s -gcflags="-m -m -pgoprofile inline_hot.pprof"
```

To save you from having to compare the output, there is the diff between the two commands:

```bash
diff <(go test -run=none -tags='' -timeout=9m0s -gcflags="-m -m" 2>&1 | grep "can inline") <(go test -run=none -tags='' -timeout=9m0s -gcflags="-m -m -pgoprofile inline_hot.pprof" 2>&1 | grep "can inline")
> ./inline_hot.go:44:6: can inline (*BS).NS with cost 106 as: method(*BS) func(uint) (uint, bool) { x := int(i >> lWSize); if x >= len(b.s) { return 0, false }; w := b.s[x]; w = w >> (i & (wSize - 1)); if w != 0 { return i + T(w), true }; x = x + 1; for loop; return 0, false }
```

As we can see the cost of the function inlined is 106, much higher than the typical 80.

Actually now running the benchmarks and comparing the result shows the change:

```bash
go test -o inline_hot.test -bench=. -cpuprofile 
inline_hot.pprof -count=100 > without_pgo.txtgo test -o inline_hot.test -bench=. -gcflags="-pgoprofile inline_hot.pprof" -count=100 > with_pgo.txt
benchstat without_pgo.txt with_pgo.txt
name  old time/op  new time/op  delta
A-10   960µs ± 2%   950µs ± 1%  -1.05%  (p=0.000 n=98+83)
```

1% improvement for doing absolutely nothing to the code, is pretty awesome, but the reality is this is a piece of test code that inlines a single function in a single benchmark, which is really just used to test whether this particular inlining optimization works as expected.

## Closing thoughts

This is only the very first profile-guided optimization added to the Go compiler, but we are very excited where it is headed. Next optimizations being discussed include [profiling informed escape analysis](https://github.com/golang/go/issues/55022#issuecomment-1252526633), [devirtualization](https://github.com/golang/go/issues/55022#issuecomment-1252191950), and [more](https://github.com/golang/go/issues/55022#issuecomment-1245605666).

Real world experience with PGO has shown a typical 5-15% improvement on real workloads with real profiling data [1][2], so we are excited for Go’s future with PGO.

Next we are excited to put Go’s upcoming PGO support to the test with real workloads and use [Parca Agent](https://github.com/parca-dev/parca-agent) collected profiles to use instead of those coming from the Go runtime, but we’ll leave that for a future post, so stay tuned!

[1] https://lists.llvm.org/pipermail/llvm-dev/2019-September/135393.html

[2] https://github.com/google/autofdo/blob/master/docs/OptimizeClangO3WithPropeller.md