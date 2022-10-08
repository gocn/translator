- 原文地址：[Exploring Go's Profile-Guided Optimizations (polarsignals.com)](https://www.polarsignals.com/blog/posts/2022/09/exploring-go-profile-guided-optimizations/)
- 原文作者：**Polar Signals**
- 本文永久链接：[https://github.com/gocn/translator/blob/master/2022/w40_Exploring_Gos_Profile_Guided_Optimizations.md](https://github.com/gocn/translator/blob/master/2022/w40_w40_Exploring_Gos_Profile_Guided_Optimizations.md)
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：

## 探究 Go Profile-Guided Optimizations(PGO)

> Profile-Guided Optimizations可以理解为一种运行时编译器优化，在下面描述中用 PGO 来当做缩写

使用 PGO 在不修改代码的前提下来提高代码执行速度。

在 Polar Signals，后端代码 100% 都是用 Go 写的。因此，自从2021年底谷歌的 Go 编译器团队开始对 PGO 进行[原型设计](https://github.com/golang/go/issues/28262#issuecomment-945837783)时，我们就非常兴奋。在这个伯克利，我们将会描述一下什么是 PGO，它是如何工作的，以及为什么它是令人兴奋的一个工具。

Go 编译器对 PGO 的支持目前定在 1.20 版本(根据以前的版本可能会在 2023 年 2 月/ 3 月发布，而这个[issue现在是在活动栏中](https://github.com/golang/go/issues/55022#issuecomment-1254050321))。

## 什么是 PGO ？

总的来说，PGO 就是使用以 profiling 数据格式 的 runtime 信息，在编译时进行优化，这个其实不是一个好的思路，但通过 runtime 所提供的信息，可以预期会有一个正向的积极影响。

Go 编译器引入的第一个 PGO 是使用 profiling 数据来内联函数，否则可能不会内联。如果你不熟悉内联函数或者想要重新复习一下，可以看一下我们发布的博客[为什么编译器内联函数如此重要](https://www.polarsignals.com/blog/posts/2021/12/15/why-compiler-function-inlining-matters/)

所以 PGO 到底是如何进行函数内联的呢？Go 编译器对一个函数的内联成本有一个启发式的判断。通常情况下，如果内联成本高于 80，那它是不会被内联的。然而，在 PGO 的加持下如果 profiling 数据建议这个函数能在内联后获得提升，那即使函数的内联成本高于 80，也依旧会被内联，

让我们来看一个具体的例子，在写这篇文章时，使用目前提议后对 Go 编译器的修改。

如果你想跟随着这篇博文，在你的代码库中尝试 PGO ，或者只是复制这篇博文所演示的内容，请勾选该补丁并使用它编译 Go runtime：

```bash
git clone https://go.googlesource.com/go
cd go
git fetch https://go.googlesource.com/go refs/changes/63/429863/3 && git checkout -b change-429863 FETCH_HEAD
cd src
./all.bashcd 
..export PATH="$(pwd)/bin:$PATH" # or add the path to your bashrc/zshrc
```

方便的是，编译器的补丁包含一个小的代码范例，演示了 PGO 的内联，来用于测试。

```bash
cd src/cmd/compile/internal/test/testdata/pgo/inline
```

让我们运行它，让 go benchmark 输出 profiling 数据，然后我们可以在随后的调用中使用，以启用 PGO。

```bash
go test -o inline_hot.test -bench=. -cpuprofile inline_hot.pprof
```

首先，然我们看下在用 PGO 之前有哪些函数被内联：

> `-run=none -tags=”” -gcflags=”-m -m”`标志允许我们只编译单元测试，而不需要执行他们，同时也可以输出内联成本以及编译器做的内联决定。

```bash
go test -run=none -tags='' -timeout=9m0s -gcflags="-m -m" 2>&1 | grep "can inline"
./inline_hot.go:15:6: can inline D with cost 7 as: func(uint) int { return int((i + (wSize - 1)) >> lWSize) }
./inline_hot.go:19:6: can inline N with cost 20 as: func(uint) *BS { bs = &BS{...}; return bs }
./inline_hot.go:28:6: can inline (*BS).S with cost 14 as: method(*BS) func(uint) *BS { b.s[i >> lWSize] |= 1 << (i & (wSize - 1)); return b }
./inline_hot.go:40:6: can inline T with cost 12 as: func(uint64) uint { return uint(jn[v & -v * 0x03f79d71b4ca8b09 >> 58]) }
./inline_hot_test.go:5:6: can inline BenchmarkA with cost 60 as: func(*testing.B) { benchmarkB(b) }
_testmain.go:37:6: can inline init.0 with cost 3 as: func() { testdeps.ImportPath = "cmd/compile/internal/test/testdata/pgo/inline" }
```

正如我们看到的所有内联函数的成本均在80及以下。现在让我们开启 PGO，再运行一次，看下现在哪些函数被内联了。 从 Go 团队在跟踪的 issue ，其中正在进行讨论的对话来看，启用 PGO 的标志似乎不会一直是这样的，但使用这个补丁，可以使用`-gcflags="-pgoprofile <file>"`标志来启用它：

```bash
go test -run=none -tags='' -timeout=9m0s -gcflags="-m -m -pgoprofile inline_hot.pprof"
```

为了使你不需要比较这两个输出，这里列出了这两个指令的差异：

```bash
diff <(go test -run=none -tags='' -timeout=9m0s -gcflags="-m -m" 2>&1 | grep "can inline") <(go test -run=none -tags='' -timeout=9m0s -gcflags="-m -m -pgoprofile inline_hot.pprof" 2>&1 | grep "can inline")
> ./inline_hot.go:44:6: can inline (*BS).NS with cost 106 as: method(*BS) func(uint) (uint, bool) { x := int(i >> lWSize); if x >= len(b.s) { return 0, false }; w := b.s[x]; w = w >> (i & (wSize - 1)); if w != 0 { return i + T(w), true }; x = x + 1; for loop; return 0, false }
```

正如我们看到的函数内联的成本是106，远高于标准的 80。

事实上现在运行 benchmarks 然后比较结果就可以看到差异：

```bash
go test -o inline_hot.test -bench=. -cpuprofile inline_hot.pprof -count=100 > without_pgo.txt
go test -o inline_hot.test -bench=. -gcflags="-pgoprofile inline_hot.pprof" -count=100 > with_pgo.txt
benchstat without_pgo.txt with_pgo.txt
name  old time/op  new time/op  delta
A-10   960µs ± 2%   950µs ± 1%  -1.05%  (p=0.000 n=98+83)
```

1% 的改进对代码完全没有影响，是非常完美的，但实际上这是一段测试代码，在一个 benchmark 中内联一个函数，这实际上只是用来测试这个特定的内联优化是否像预期的那样工作。

## 结束语

这只是添加到 Go 编译器中的第一个 PGO，但我们对它的发展方向感到非常兴奋。正在讨论下一步的优化，包括[剖析告知逃逸分析](https://github.com/golang/go/issues/55022#issuecomment-1252526633)，[devirtualization](https://github.com/golang/go/issues/55022#issuecomment-1252191950)，以及[更多](https://github.com/golang/go/issues/55022#issuecomment-1245605666)。

使用 PGO 的实际经验表明，在真实的工作负载上，使用真实的 profiling 数据[1]\[2]，通常会有 5 - 15% 的提升，因此我们对 Go 的未来与 PGO 的关系感到兴奋。

接下来，我们很高兴用真实的工作负载来测试 Go 即将推出的 PGO 支持，并使用 [Parca Agent](https://github.com/parca-dev/parca-agent) 收集的profiles 来代替来自 Go runtime 的 profiles ，但我们会把这个问题留给未来的文章，敬请关注！

[1] https://lists.llvm.org/pipermail/llvm-dev/2019-September/135393.html

[2] https://github.com/google/autofdo/blob/master/docs/OptimizeClangO3WithPropeller.md
