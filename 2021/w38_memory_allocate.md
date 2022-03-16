# 谈谈 Go 中的内存

* 原文地址：https://dave.cheney.net/2021/01/05/a-few-bytes-here-a-few-there-pretty-soon-youre-talking-real-memory
* 原文作者：`dave`
* 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w38_memory_allocate.md

- 译者：[咔叽咔叽](https:/github.com/watermeloooo)
- 校对：

今天的文章来自于最近的 Go 代码测试。请看下面的基准测试代码。[1](#easy-footnote-bottom-1-4231)

```
func BenchmarkSortStrings(b *testing.B) {
        s := []string{"heart", "lungs", "brain", "kidneys", "pancreas"}
        b.ReportAllocs()
        for i := 0; i < b.N; i++ {
                sort.Strings(s)
        }
}
```

作为 `sort.Sort(sort.StringSlice(s))` 的一个封装，`sort.Strings` 对输入进行了原地排序，所以它不应该被分配内存（至少 43% 的 tweeps 回应者是这么认为的）。然而，事实证明至少在最近的 Go 版本中，benchmark 的每一次迭代都会导致一次堆内存分配。为什么会发生这种情况？

所有 Go 程序员都应该知道，接口是以[两个变量](https://research.swtch.com/interfaces)的结构来实现的。每个接口值都包含一个保存接口内容类型的字段，以及一个指向接口内容的指针。[2](#easy-footnote-bottom-2-4231)

用 Go 的伪代码来表述，一个接口可能看起来是这样的：

```
type interface struct {
        // the ordinal number for the type of the value
        // assigned to the interface 
        type uintptr

        // (usually) a pointer to the value assigned to
        // the interface
        data uintptr
}
```

`interface.data` 在大多数情况下可以容纳一个 8 字节变量，但 `[]string` 是 24 个字节；其中一个变量指向切片底层数组的指针；一个变量是长度；还有一个变量是底层数组的剩余容量，那么 Go 是如何将 24 个字节装入 8 个字节的呢？使用书中最古老的技巧 - 引用。例如，`[]string` 是 24 个字节，但 `*[]string` - 一个指向字符串切片的指针 - 只有 8 字节。

## 逃逸到堆

为了使这个例子更加明确，我们去掉了 `sort.Strings` 函数：

```
func BenchmarkSortStrings(b *testing.B) {
        s := []string{"heart", "lungs", "brain", "kidneys", "pancreas"}
        b.ReportAllocs()
        for i := 0; i < b.N; i++ {
                var ss sort.StringSlice = s
                var si sort.Interface = ss // allocation
                sort.Sort(si)
        }
}
```

为了使接口发挥作用，编译器将赋值改写为 `var si sort.Interface = &ss`  ss 的地址被分配给了接口值。现在的情况就变成接口值持有一个指向 ss 的指针，但它指向哪里呢？ss 在内存中的什么位置呢？

从 benchmark 报告中来看，似乎 `ss` 被分配到了堆上。

```
  Total:    296.01MB   296.01MB (flat, cum) 99.66%
      8            .          .           func BenchmarkSortStrings(b *testing.B) { 
      9            .          .           	s := []string{"heart", "lungs", "brain", "kidneys", "pancreas"} 
     10            .          .           	b.ReportAllocs() 
     11            .          .           	for i := 0; i < b.N; i++ { 
     12            .          .           		var ss sort.StringSlice = s 
     13     296.01MB   296.01MB           		var si sort.Interface = ss // allocation 
     14            .          .           		sort.Sort(si) 
     15            .          .           	} 
     16            .          .           } 
```

发生分配的原因是编译器不能说服自己 `ss` 比 `si` 存活时间长。Go 编译器的黑客们的普遍态度好像是：[ 这一点可以改进](https://github.com/golang/go/issues/23676)，但这又是另外一个话题了。目前，`ss` 被分配在堆中。因此问题就变成了，每次迭代分配多少个字节？我们可以用 `testing` 来看看。

```
% go test -bench=. sort_test.go 
goos: darwin
goarch: amd64 
cpu: Intel(R) Core(TM) i7-5650U CPU @ 2.20GHz 
BenchmarkSortStrings-4 12591951 91.36 ns/op 24 B/op 1 allocs/op 
PASS 
ok command-line-arguments 1.260s
```

在 amd64 平台上使用 Go 1.16 beta1，每次操作分配 24 个字节。[4](#easy-footnote-bottom-4-4231) 然而，在同一平台上，之前的 Go 版本每次操作消耗 32 个字节。

```
% go1.15 test -bench=. sort_test.go 
goos: darwin 
goarch: amd64 BenchmarkSortStrings-4 11453016 96.4 ns/op 32 B/op 1 allocs/op 
PASS 
ok command-line-arguments 1.225s
```

这将把我们带回这篇文章的主题，即 Go 1.16 中的一个有趣的改进。但在谈论它之前，我需要讨论一下内存尺寸级别 (size classes)。

## 内存尺寸级别 - Size classes

要解释什么是 size classes，让我们思考一下 Go 运行时如何在堆上分配 24 字节。一个简单的方法是用一个指向堆上最后分配的字节的指针来跟踪到目前为止分配的所有内存。要分配 24 个字节，堆的指针则要增加 24，并将前一个值返回给调用者。只要请求 24 字节的代码不写超这个标记，这个机制就没有开销。遗憾的是，在现实生活中，内存分配器并不只是分配内存，有时他们还必须释放内存。

最终 Go 运行时将不得不释放这 24 个字节，但从运行时的角度来看，它知道的是它给调用者的起始地址。它不知道这个地址之后分配了多少字节。为了释放内存，我们假设的 Go 运行时分配器必须为堆上的每次分配记录其长度。这些长度的分配在哪里？当然是在堆上。

在我们的方案中，当运行时想分配内存时，它可以请求比被请求稍多一点的内存，并使用它来存储所请求的数量。对于我们的切片例子，当我们请求 24 字节时，需要消耗 24 字节再加上一些开销来存储数字 24。这个开销有多大？事实证明，最小的量是一个字面量。[5](#easy-footnote-bottom-5-4231)

要记录一个 24 字节的分配，开销是 8 个字节。25% 不是很大，但也不小，随着分配大小的增加，开销会变得微不足道。然而，如果我们只想在堆上存储 1 个字节，会发生什么？开销是请求数量的八倍，是否有更有效的方法来解决堆上少量数据的分配？

如果所有相同大小的内存都存储在一起，而不是将长度与分配的内存存储在一起，会发生什么？如果所有长度为 24 字节的内存都存储在一起，那么运行时将自动知道它们有多大。运行时只需要一个位来指示一个 24 字节的区域是否被使用。在 Go 中，这些区域被称为 size classes，因为所有相同大小的内存都存储在一起（想想学校的班级--所有的学生都是同一年级的，而不是 C++ 班级）。当运行时需要分配少量内存时，它会使用能容纳请求内存的最小的 size classes 来执行操作。

## 不限大小的 size classes

现在我们知道了 size classes 的工作原理，还有一个问题是，它们被存储在哪里呢？毫不奇怪，size classes 的内存来自于堆。为了最大限度地减少开销，运行时从堆中分配一个较大的数量（通常是系统页大小的倍数），然后将该空间用于分配单一尺寸的内存。但是，有一个问题。

如果分配大小的数量是固定的(最好是小的)，那么分配一个大区域来存储相同尺寸的东西是很好的，但是在通用语言中，程序可以在运行时分配任何尺寸。

例如，假设向运行时请求 9 字节。9 字节是一个不常见的大小，所以很可能需要为 9 字节大小的内存建立一个新的 size classes。由于 9 字节的情况并不常见，因此很可能会浪费剩余的 4 KB 或更大的分配空间。正因为如此，size classes 的集合是固定的。如果没有确切数额的 size classes 可用，则分配被四舍五入到下一个大小的 size classes。在我们的例子中，9 个字节可能被分配到 12 个字节的 size classes 中。3 字节的开销总比整个 size classes 分配了大部分未使用的字节好。

## 总结

这是最后的总结。Go 1.15 没有 24 字节大小的 size classes，所以 `ss` 的堆分配是在 32 字节大小的 size classes 中的。多亏了 Martin Möhrmann 的工作，Go 1.16 有了一个 24 字节大小的 size classes，这对分配给接口的 slice 值来说是非常合适的。

1. 这不是对排序函数进行基准测试的正确方法，因为在第一次迭代之后，输入已经被排序。[](#easy-footnote-1-4231)
2. 这个声明的准确性取决于所使用的 Go 版本。例如，Go 1.15 增加了[将一些整数直接存储在接口值中，](https://golang.org/doc/go1.15#runtime)省去了分配和引用的功能。然而，对于大多数的值，如果它不是已经有了指针类型，它的地址就会被存储在接口值中。[](#easy-footnote-2-4231)
3. 编译器在接口值的类型字段中会进行跟踪，所以它记得分配给 `si` 的类型是 `sort.StringSlice`，而不是 `*sort.StringSlice`。
4. 在 32 位平台上，这个数字会减半，[但是我们不回头看](https://www.tallengestore.com/products/i-never-look-back-darling-it-distracts-from-the-now-edna-mode-inspirational-quote-tallenge-motivational-poster-collection-large-art-prints)。[](#easy-footnote-4-4231)
5. 如果你将分配限制在 4 G 或 64 kb，你可以使用较少的内存来存储分配的大小，但这意味着分配的第一个字不是自然对齐的，所以在实践中，使用少于一个字来存储长度头并不会达到有效节省的效果。[](#easy-footnote-5-4231)
6. 将相同大小的东西存储在一起也是对抗内存碎片化的有效策略[](#easy-footnote-6-4231)
7. 这并不是一个牵强的场景，字符串有大小各不同，生成一个新大小的字符串可以像附加一个空格一样简单。

## 相关文章

1. [I’m talking about Go at DevFest Siberia 2017](https://dave.cheney.net/2017/08/23/im-talking-about-go-at-devfest-siberia-2017)

2. [If aligned memory writes are atomic, why do we need the sync/atomic package?](https://dave.cheney.net/2018/01/06/if-aligned-memory-writes-are-atomic-why-do-we-need-the-sync-atomic-package)

3. [A real serial console for your Raspberry Pi](https://dave.cheney.net/2014/01/05/a-real-serial-console-for-your-raspberry-pi)

4. [Why is a Goroutine’s stack infinite ?](https://dave.cheney.net/2013/06/02/why-is-a-goroutines-stack-infinite）