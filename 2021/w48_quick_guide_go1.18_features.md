# Go 快速指南：go1.18特性
- 原文地址：https://medium.com/@emreodabas_20110/quick-guide-go-1-18-features-e236d5b351ef
- 原文作者：Emre Odabas
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w48_quick_guide_go1.18_features.md
- 译者：[cuua](https://github.com/cuua)
- 校对：

即将在2022年第一季发布的Go 1.18版本，有很多新特性正等着我们。

这个版本将是Go历史版本里最关键的版本，我们将在一个月内尝鲜到beta版。到底有哪些更新呢？

# 参数类型（泛型）
Go期待已久的参数类型特性，也就是其他语言里的泛型。有了这个特性，我们可以给函数传递动态类型。让我们深入到一个简单的例子，通过编写一个函数来查找任意两个int变量中的最小值

```
func minInt(x int, y int) int {
   if x < y {
      return x
   } else {
      return y
   }
}
```
当我们需要为float32变量提供相同功能时，我们需要重新写一个类似的函数
```
func minFloat(x float32, y float32) float32 {
   if x < y {
      return x
   } else {
      return y
   }
}
```
通过泛型的能力，我们可以轻松的定义一个函数，这样我们可以得到所需类型的变量。通过定义类型，我们还可以看到一个名为~的新操作符。这个操作符实际上返回给我们的是类型信息的接口，因此我们可以进行类型限制，让我们来编写相同的min函数来覆盖int和float32，如下所示：

```
type OrderTypes interface { 
   ~int | ~float32 
}
func min[P OrderTypes](x, y P) P {
    if x < y {
      return x
    } else {
      return y
    }
}
```
这看起来很可靠 ，对吧。Go还建议使用已经定义类型组的约束库。例如，我们可以为所有有序类型实现我们的函数。
```
func min[P constraints.Ordered](x, y P) P {
    if x < y {
      return x
    } else {
      return y
    }
}
```
当然，泛型的使用不仅仅限于这个例子。它可能在ORM风格的问题中特别有用，我们通常创建使用多种类型的函数，此外你还可以看到Go团队分享的示例。如果你想看细节，团队在GopherCon做了一个很棒的演示。

除此之外，我们可以进行实验的在线编辑（playground）也很有用。如果你希望使用1.18在你自己的环境，你可以下载gotip并使用Go的活跃的分支。

#模糊测试
随着Go1.18软件包的发布，"模糊化"功能将进入我们的生活。有了这个在beta版提供的测试库，我们将能够在单元测试中自动做随机突变输入。

作为软件开发者，我们有时会忘记边缘测试。这种数据多样性的缺乏可能会被滥用，导致安全漏洞，特别是在关键库上。我们可以通过模糊测试来预防这种情况。

为了实现模糊测试，你可以使用以模糊前缀开头的方法包装单元测试。你还可以使用Go的测试页作为示例代码。
```
func FuzzHex(f *testing.F) {
  for _, seed := range [][]byte{{}, {0}, {9}, {0xa}, {0xf}, {1, 2, 3, 4}} {
    f.Add(seed)
  }
  f.Fuzz(func(t *testing.T, in []byte) {
    enc := hex.EncodeToString(in)
    out, err := hex.DecodeString(enc)
    if err != nil {
      t.Fatalf("%v: decode: %v", in, err)
    }
    if !bytes.Equal(in, out) {
      t.Fatalf("%v: not equal after round trip: %v", in, out)
    }
  })
}
```
#工作区
此功能有助于开发人员同时处理多个模块。尽管可以在go.mod 1.17版本中使用replace命令更改module版本。但是在提交代码的时候，常常忘记清除这些replace命令。对于我们开发人员来说，每次插入或删除该行都是一件非常麻烦的事情。

使用工作区功能，你可以创建一个名为go.work的新文件，在那里编写replace命令。此文件允许我们更改特定工作环境的modules且无需更改已有的go.mod文件。例如，你可以查看property提出的设计页面

```
go 1.17

directory (
    ./baz // foo.org/bar/baz
    ./tools // golang.org/x/tools
)

replace golang.org/x/net => example.com/fork/net v1.4.5
```
综上，Go1.18提供了有用的模糊化和工作区特性，以及讨论、研究超过一年的泛型特性。除此之外，此版本还提供许多改进和修复，您可以通过此[链接](https://github.com/golang/go/milestone/201) 了解版本的状态及其包含的内容。
