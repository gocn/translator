## Go 中的随机性测试

- 原文地址：[[Random testing in Go — Bitfield Consulting](https://bitfieldconsulting.com/golang/random-testing)](https://vidhyanshu.medium.com/implementing-clean-architecture-in-go-56aca59311b3)
- 原文作者：[John Arundel](https://bitfieldconsulting.com/golang?author=5e10bdc11264f20181591485)
- 本文永久链接：[translator/w18_Random_testing_in_Go.md at master · gocn/translator · GitHub](https://github.com/gocn/translator/blob/master/2023/w18_Random_testing_in_Go.md)
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：[fivezh](https://github.com/fivezh)

> *我瞄准天空发射了一支箭，
> *它落到了地面，我不知道落在何处。*
>
> -Henry Wadsworth Longfellow,["那支箭与那首歌"](https://www.poetryfoundation.org/poems/44624/the-arrow-and-the-song)

这是关于 Go 语言模糊测试的四部分教程系列的第一部分:

1. Go 语言中的随机测试
2. [Go 语言中的模糊测试](https://bitfieldconsulting.com/golang/fuzz-tests)
3. 写一个 Go 语言的模糊测试目标(即将推出)
4. 通过模糊化发现漏洞(即将推出)

为我们的 Go 程序选择好的测试用例有点看运气。有时我们很幸运找到一个错误的输入或者甚至造成崩溃，但通常来说，随机选择输入不是一个发现 bug 的好方法。

或者说有可能吗？如果我们把这个想法发挥到极致，使用很多不同的输入呢？比如一百万个，或者十亿个。有这么多的输入，找到一个触发问题的奇怪值的可能性变得相当大。

听起来太多重复的输入工作了？我同意你的观点，所以让计算机来做这项工作吧。毕竟，那不就是它们的用途吗?

## 生成随机测试的输入值

好的，我们知道如何在 Go 中生成随机数：我们可以使用 `math/rand`（或者，对于更高级别的随机性，[`bitfield/qrand`](https://github.com/bitfield/qrand)）。让我们试试看。

假设我们有一对函数 `Encode` 和 `Decode`。它们确切地做什么并不重要，但我们可以假设如果你对某些东西进行了 `Encode`，然后对结果进行 `Decode`。只要这些函数正常工作，你应该得到你最初的数据。

这里有一个测试，它生成一个介于 0 和 9 之间的随机整数，并将其通过两个函数 `Encode` 和 `Decode` 进行 *往返处理*：

```go
import "math/rand"

func TestEncodeFollowedByDecodeGivesStartingValue(t *testing.T) {
    t.Parallel()
    input := rand.Intn(10)
    encoded := codec.Encode(input)
    t.Logf("encoded value: %#v", encoded)
    want := input
    got := codec.Decode(encoded)
    // after the round trip, we should get what we started with
    if want != got {
        t.Errorf("want %d, got %d", want, got)
    }
}
```

([Listing `codec/1`](https://github.com/bitfield/tpg-tests/blob/main/codec/1/codec_test.go))

你可能会担心，如果这个值是 *真正* 随机的，那么我们可能会得到一个不稳定的测试结果。如果 `Encode` 或 `Decode` 中存在某些输入触发的 bug，那么像这样的测试有时会通过，有时会失败，对吗？

这确实是一种可能性。避免这种情况的一种方法是使用某个固定值对随机数生成器进行 *种子*（seed）处理：这样，生成的序列将始终相同，使我们的测试具有确定性。

例如，我们可以编写以下代码，它将为测试创建一个新的随机生成器，种子的值为 1：

```go
var rng = rand.New(rand.NewSource(1))
```

我们不必使用 1 作为种子；任何固定值都可以。关键是，给定某个特定的种子，调用 `rng.Intn` 将始终产生相同的值序列：

```go
fmt.Println(rng.Intn(10)) // 1
fmt.Println(rng.Intn(10)) // 7
fmt.Println(rng.Intn(10)) // 7
fmt.Println(rng.Intn(10)) // 9
fmt.Println(rng.Intn(10)) // 1
```

如果我们确实希望每次运行测试时都获得不同的序列，那么我们可以使用一些 *不固定* 的种子值。例如，当前的时钟时间：

```go
var rng = rand.New(rand.NewSource(time.Now().Unix()))
```

## 对一组已知的输入进行随机置换

使用随机性的一个好方法，不会导致不稳定的测试或需要手动设置随机数生成器的种子，是对一组输入进行 *排列* ——即以某种随机顺序重新排列它们。

例如，以下代码生成一个包含从 0 到 99 的整数的切片，以随机顺序排序：

```go
inputs := rand.Perm(100)
for _, n := range inputs {
    ... // test with input n
}
```

`rand.Perm(100)` 生成的 100 个整数序列本身并不是随机的，因为从 0 到 99 的每个值都将恰好出现一次。这对于随机 *选择* 的数字来说是不成立的，因为某些值会多次出现，而其他值则不会出现。

相反，这个序列是随机 *排列* 的（即随机排序）。这就像洗牌一副牌：你知道每张牌仍然会出现恰好一次，只是不知道出现的顺序。

与 `rand.Intn` 一样，每次测试运行的结果都会不同，除非你创建一个使用已知种子初始化的自己的随机数生成器。

## 基于属性的测试

随机性可以是发现有趣的新测试用例的好方法，这些测试用例可能是你自己想不到的。例如，如果您的函数接受整数，您可能已经尝试使用 1、5、7 等进行测试。您可能没有想到尝试将 *零* 作为输入，但随机生成器很可能会在某个时候产生它。如果您的函数在给定零时出现问题，那么这是您肯定想知道的。

通常，好的测试人员擅长提出打破程序的输入，因为 *程序员* 没有考虑到它们。随机性可以帮助这个过程。

随机测试输入的一个问题可能已经出现在您的脑海中：如果我们事先不知道要使用什么输入，我们就无法知道期望的结果是什么。

例如：

```go
func TestSquareGivesCorrectResult(t *testing.T) {
    t.Parallel()
    input := rand.Intn(100)
    got := square.Square(input)
    want := ... // uh-oh, what to put here?
```

这里的 `want` 值是什么？我们不知道，因为我们不知道在测试运行时 `input` 的值将是什么，以及它的平方将是什么。如果我们知道 `input` 将是 10，那么我们可以让测试期望答案为 100，但我们 *不知道*。我们陷入了困境。

我们不想在测试中尝试 *计算* 期望结果，因为很明显我们可能会计算错误。在最恶劣的情况下，我们可能会在测试中使用与 *系统* 中相同的代码路径来计算它，因此我们最终什么也没测试到。

如果我们无法预测对于给定的输入 `Square` 的 *确切* 结果，那么有没有任何一般性的描述呢？

实际上，有一些我们可以说的东西：它不应该是负数！无论输入是什么，如果 `Square` 返回一个负数，那么就有问题了。因此，尽管如果系统正确，我们无法预测 `Square` 的 *确切* 结果，但我们仍然可以确定它应该具有的一些 *属性*。

因此，我们可以编写一个测试，调用 `Square` 并使用许多不同的输入，检查结果是否为负数：

```go
func TestSquareResultIsAlwaysNonNegative(t *testing.T) {
    t.Parallel()
    inputs := rand.Perm(100)
    for _, n := range inputs {
        t.Run(strconv.Itoa(n), func(t *testing.T) {
            got := square.Square(n)
            if got < 0 {
                t.Errorf("Square(%d) is negative: %d", n, got)
            }
        })
    }
}
```

([Listing `square/1`](https://github.com/bitfield/tpg-tests/blob/main/square/1/square_test.go))

这种方法有时被称为 *基于属性的测试*，以区别于到目前为止我们一直在做的 *基于示例的测试*。

另一种思考方法是，基于属性的测试描述系统的行为，不是根据确切的值，而是根据 *不变量*：不论输入是什么，结果中不会改变的东西。例如，对于 `Square`，其结果应该始终为正数。

基于属性的随机测试有助于解决函数可能仅适用于我们考虑的特定示例的问题。虽然我们会随机 *生成* 输入，但一旦我们找到一些触发错误的值，它就应该成为常规基于示例的测试的一部分。

我们可以通过在表格测试的输入集中手动添加这些值来实现这一点，但没有必要。Go 提供了一种自动将随机生成的破坏性输入转换为静态测试用例的方法，称为 *模糊测试*。

在本系列的 [第二部分](https://bitfieldconsulting.com/golang/fuzz-tests) 中，我们将介绍 Go 模糊测试，并了解它们如何用于查找难以发现的能够触发错误的输入。敬请关注！
