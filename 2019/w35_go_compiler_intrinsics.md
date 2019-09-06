# Go compiler intrinsics

- 原文地址：https://dave.cheney.net/2019/08/20/go-compiler-intrinsics
- 原文作者：[Dave Cheney](https://dave.cheney.net/)
- 译文出处：https://dave.cheney.net/
- 本文永久链接：https://github.com/gocn/translator/blob/master/2019/w35_go_compiler_intrinsics.md
- 译者：[fivezh](https://github.com/fivezh)、[咔叽咔叽](https://github.com/watermelo)
- 校对者：

如有需要，Go允许使用者通过汇来编写函数。这被称作 *stub* 或 *forward* 声明.

```go
package asm

// Add returns the sum of a and b.
func Add(a int64, b int64) int64
```

这里，我们声明了`Add`函数，其接受2个`int64`类型入参，并返回二者之和。`Add`函数除了不包含函数体部分外，是常见的Go形式的函数声明。

如果我们尝试编译这个包时，编译器自然是会给出警告信息的：

```shell
% go build
examples/asm
./decl.go:4:6: missing function body
```

为了满足编译器要求，我们通过汇编的方式为`Add`提供函数体，这里可以在同一个包下新增`.s`文件。

```plain
TEXT ·Add(SB),$0-24
        MOVQ a+0(FP), AX
        ADDQ b+8(FP), AX
        MOVQ AX, ret+16(FP)
        RET
```

现在我们可以进行`build`，`test`操作，像普通的Go代码一样使用`Add`函数。但是，有一个问题，汇编函数无法被内联。

这一直是被Go开发者所抱怨的，他们希望通过汇编来提高性能或访问未被语言暴露的操作。比如说，矢量指令，原子指令等等。如果没有内联汇编的能力，在Go中编写这些函数会产生相对较大的负担。

```go
var Result int64

func BenchmarkAddNative(b *testing.B) {
        var r int64
        for i := 0; i < b.N; i++ {
                r = int64(i) + int64(i)
        }
        Result = r
}

func BenchmarkAddAsm(b *testing.B) {
        var r int64
        for i := 0; i < b.N; i++ {
                r = Add(int64(i), int64(i))
        }
        Result = r
 }
```

```plain
BenchmarkAddNative-8  1000000000        0.300 ns/op
BenchmarkAddAsm-8     606165915         1.93 ns/op
```

> 译者注：Go原生的方式，性能优于汇编方式，这也就是本文关注的Go内建函数的优化。

多年来，已经有多种提案来支持内联汇编的语法，比如类似与gcc的`asm(...)`指令。但没有任何一个提案被Go团队接受。相反，Go添加了一种内建函数*intrinsic functions*。
> 注1：内建函数 可能不是他们的正式名称，但是这个词在编译器及其测试中是很常用的。
> 译者注：参见维基百科[Intrinsic function](https://en.wikipedia.org/wiki/Intrinsic_function)

内建函数*intrinsic function*是使用常规Go编写的Go代码。这些函数在Go编译器中是已知的，它包含可在编译期间进行替换的待替换元素。从Go 1.13开始，编译器支持的包有：

- `math/bits`
- `sync/atomic`

这些包中的函数具有巴洛克式签名（译者注：这里是形容复古的签名形式），但在你的系统架构支持更有效的执行方式时，编译器可以使用相近的原生指令来进行透明的替换函数调用。

对于本文的其余部分，我们将研究Go编译器使用内建函数*intrinsic function*生成更高效代码的两种不同方式。

## Ones count 位为1的计数

一个词中位为“1”的数量，这类计数是一种重要的加密和压缩原语。因为这是一项基础且重要的操作，所以大多数现代CPU都提供了原生硬件实现。

`math / bits`包通过`OnesCount`系列函数提供了对该操作的支持。 各种`OnesCount`函数被编译器识别，并且取决于CPU体系结构和Go的版本，将被本机硬件指令替换。

要了解这有多么有效，我们可以比较三种不同的计数实现。 第一个是Kernighan在《The C Programming Language 2nd Ed, 1998》书中提到的算法。

> 注2：Kernighan 《The C Programming Language 2nd Ed, 1998》，C语言Bible

```go
func kernighan(x uint64) int {
        var count int
        for ; x > 0; x &= (x - 1) {
                count++
        }
        return count
}
```

该算法最大循环次数由数字本身的位数决定; 数字具有的位数越多，则它的循环次数越多。

第二个算法会令黑客们会心一笑，来自[issue 14813](https://github.com/golang/go/issues/14813)。

```go
func hackersdelight(x uint64) int {
        const m1 = 0x5555555555555555
        const m2 = 0x3333333333333333
        const m4 = 0x0f0f0f0f0f0f0f0f
        const h01 = 0x0101010101010101

        x -= (x >> 1) & m1
        x = (x & m2) + ((x >> 2) & m2)
        x = (x + (x >> 4)) & m4
        return int((x * h01) >> 56)
 }
```

如果输入是一个常量（如果编译器可以在编译器时间找出答案的话，整个事情会优化掉），这个版本算法中很多比特位都会在恒定时间内运行并且非常好地优化。

让我们根据`math / bits.OnesCount64`对这些实现进行基准测试。

```go
var Result int

func BenchmarkKernighan(b *testing.B) {
        var r int
        for i := 0; i < b.N; i++ {
                r = kernighan(uint64(i))
        }
        Result = r
}

func BenchmarkPopcnt(b *testing.B) {
        var r int
        for i := 0; i < b.N; i++ {
                r = hackersdelight(uint64(i))
        }
        Result = r
}

func BenchmarkMathBitsOnesCount64(b *testing.B) {
        var r int
        for i := 0; i < b.N; i++ {
                r = bits.OnesCount64(uint64(i))
        }
        Result = r
}
```

为了保持公平，我们在为每个被测函数提供相同的输入：从零到“b.N”的整数序列。 这对于Kernighan的方法更为公平，因为它的运行时间随着入参的位数而主键增加。

> 注3：作为加分小作业，可以尝试将`0xdeadbeefdeadbeef`传递给每个被测试的函数，看看运行结果如何。

来看下测试结果：`go test -bench=. -run=none`

```plain
BenchmarkKernighan-8        100000000       11.2 ns/op
BenchmarkPopcnt-8           618312062       2.02 ns/op
BenchmarkMathBitsOnesCount64-8  1000000000  0.565 ns/op
```

胜出的是`math/bits.OnesCount64`，有近4倍的速度优势，但是这真的是使用硬件指令，还是编译器在代码优化方面做得更好？让我们来检查下汇编的过程。

```plain
% go test -c
% go tool objdump -s MathBitsOnesCount popcnt-intrinsic.test
TEXT examples/popcnt-intrinsic.BenchmarkMathBitsOnesCount64(SB) /examples/popcnt-intrinsic/popcnt_test.go
   popcnt_test.go:45     0x10f8610               65488b0c2530000000      MOVQ GS:0x30, CX
   popcnt_test.go:45     0x10f8619               483b6110                CMPQ 0x10(CX), SP
   popcnt_test.go:45     0x10f861d               7668                    JBE 0x10f8687
   popcnt_test.go:45     0x10f861f               4883ec20                SUBQ $0x20, SP
   popcnt_test.go:45     0x10f8623               48896c2418              MOVQ BP, 0x18(SP)
   popcnt_test.go:45     0x10f8628               488d6c2418              LEAQ 0x18(SP), BP
   popcnt_test.go:47     0x10f862d               488b442428              MOVQ 0x28(SP), AX
   popcnt_test.go:47     0x10f8632               31c9                    XORL CX, CX
   popcnt_test.go:47     0x10f8634               31d2                    XORL DX, DX
   popcnt_test.go:47     0x10f8636               eb03                    JMP 0x10f863b
   popcnt_test.go:47     0x10f8638               48ffc1                  INCQ CX
   popcnt_test.go:47     0x10f863b               48398808010000          CMPQ CX, 0x108(AX)
   popcnt_test.go:47     0x10f8642               7e32                    JLE 0x10f8676
   popcnt_test.go:48     0x10f8644               803d29d5150000          CMPB $0x0, runtime.x86HasPOPCNT(SB)
   popcnt_test.go:48     0x10f864b               740a                    JE 0x10f8657
   popcnt_test.go:48     0x10f864d               4831d2                  XORQ DX, DX
   popcnt_test.go:48     0x10f8650               f3480fb8d1              POPCNT CX, DX // math/bits.OnesCount64
   popcnt_test.go:48     0x10f8655               ebe1                    JMP 0x10f8638
   popcnt_test.go:47     0x10f8657               48894c2410              MOVQ CX, 0x10(SP)
   popcnt_test.go:48     0x10f865c               48890c24                MOVQ CX, 0(SP)
   popcnt_test.go:48     0x10f8660               e87b28f8ff              CALL math/bits.OnesCount64(SB)
   popcnt_test.go:48     0x10f8665               488b542408              MOVQ 0x8(SP), DX
   popcnt_test.go:47     0x10f866a               488b442428              MOVQ 0x28(SP), AX
   popcnt_test.go:47     0x10f866f               488b4c2410              MOVQ 0x10(SP), CX
   popcnt_test.go:48     0x10f8674               ebc2                    JMP 0x10f8638
   popcnt_test.go:50     0x10f8676               48891563d51500          MOVQ DX, examples/popcnt-intrinsic.Result(SB)
   popcnt_test.go:51     0x10f867d               488b6c2418              MOVQ 0x18(SP), BP
   popcnt_test.go:51     0x10f8682               4883c420                ADDQ $0x20, SP
   popcnt_test.go:51     0x10f8686               c3                      RET
   popcnt_test.go:45     0x10f8687               e884eef5ff              CALL runtime.morestack_noctxt(SB)
   popcnt_test.go:45     0x10f868c               eb82                    JMP examples/popcnt-intrinsic.BenchmarkMathBitsOnesCount64(SB)
   :-1                   0x10f868e               cc                      INT $0x3
   :-1                   0x10f868f               cc                     INT $0x3 
```

这里输出了很多内容，但关键的内容是第48行（取自`_test.go`文件的源代码），程序确实使用了我们期望的x86`POPCNT`指令。事实证明这比操作位运算更快。

有趣的是比较`POPCNT`之前的两条指令：

```palin
CMPB $0x0, runtime.x86HasPOPCNT(SB)
```

并非所有的英特尔CPU都支持`POPCNT`，如果CPU支持此指令，那么Go运行时在启动时，就会将此结果存储在`runtime.x86HasPOPCNT`中。这样每次进行基准测试循环时，程序通过检查*CPU是否支持POPCNT*，然后再发出`POPCNT`请求。

`runtime.x86HasPOPCNT`的值在程序执行期间不会变化，因此检查结果是高度可预测的，这使得这种检查的成本相对低廉。

## Atomic counter 原子计数器

除了生成更高效的代码之外，内建函数*intrinsic functions*只是常规的Go代码，内联规则（包括中间堆栈内联）同样适用于它们。

这是一个原子计数器类型的例子。它有类型的方法，深层的方法调用，多个包等情况。

```go
import (
         "sync/atomic"
)

type counter uint64

func (c counter) get() uint64 {
         return atomic.LoadUint64((uint64)(c))
}

func (c counter) inc() uint64 {
        return atomic.AddUint64((uint64)(c), 1)
}

func (c counter) reset() uint64 {
        return atomic.SwapUint64((uint64)(c), 0)
}

var c counter

func f() uint64 {
        c.inc()
        c.get()
        return c.reset()
}
```

> 译者注：原文代码有误无法编译，代码进行了部分修改， `(uint64)(c)`修改为`(*uint64)(&c)`

你会认为上述这种操作会产生很多开销，这是可以原谅的。 但由于内联和编译器内建函数之间的交互，这些代码在大多数平台上会转换为很高效的原生代码。

```plain
TEXT main.f(SB) examples/counter/counter.go
   counter.go:23         0x10512e0               90                      NOPL
   counter.go:29         0x10512e1               b801000000              MOVL $0x1, AX
   counter.go:13         0x10512e6               488d0d0bca0800          LEAQ main.c(SB), CX
   counter.go:13         0x10512ed               f0480fc101              LOCK XADDQ AX, 0(CX) // c.inc
   counter.go:24         0x10512f2               90                      NOPL
   counter.go:10         0x10512f3               488b05fec90800          MOVQ main.c(SB), AX // c.get
   counter.go:25         0x10512fa               90                      NOPL
   counter.go:16         0x10512fb               31c0                    XORL AX, AX
   counter.go:16         0x10512fd               488701                  XCHGQ AX, 0(CX) // c.reset
   counter.go:16         0x1051300               c3                      RET 
```

下面我们逐一解释下。第一个操作，`counter.go:13`是`c.inc`一个`LOCK`和`XADDQ`指令，这在x86上是一个原子性的增量。第二个，`counter.go:10`是`c.get`，由于x86强大的内存一致性模型，它是内存级的常规操作。最后一个操作，`counter.go:16`，`c.reset`是`CX`中地址与`AX`的原子交换，而`AX`在前一行被归零(`XORL AX, AX`，按位异或，相当于清零)。这将`AX`中的值（零）放入存储在`CX`中的地址中，而先前存储在`（CX）`的值被丢弃。

## Conclusion 总结

内建函数是一种简洁的解决方案，它使Go程序员可以进行低层架构的操作，而无需扩展语言规范。如果某个体系结构没有特定的`sync/atomic`原语（比如某些ARM的变体）或者`math/bits`操作，那么编译器会隐式地降级为用纯Go编写的操作。

## Related posts 相关文章

1.  [Notes on exploring the compiler flags in the Go compiler suite](https://dave.cheney.net/2012/10/07/notes-on-exploring-the-compiler-flags-in-the-go-compiler-suite "Notes on exploring the compiler flags in the Go compiler suite")
2.  [Padding is hard](https://dave.cheney.net/2015/10/09/padding-is-hard "Padding is hard")
3.  [Should methods be declared on T or *T](https://dave.cheney.net/2016/03/19/should-methods-be-declared-on-t-or-t "Should methods be declared on T or *T")
4.  [Wednesday pop quiz: spot the race](https://dave.cheney.net/2015/11/18/wednesday-pop-quiz-spot-the-race "Wednesday pop quiz: spot the race")
