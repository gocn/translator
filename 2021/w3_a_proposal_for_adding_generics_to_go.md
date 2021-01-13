# Go 语言增加泛型的提案

- 原文地址：https://blog.golang.org/generics-proposal
- 原文作者：Ian Lance Taylor
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w3_a_proposal_for_adding_generics_to_go.md
- 译者：[cvley](https://github.com/cvley)
- 校对：[guzzsek](https://github.com/guzzsek)

> Ian Lance Taylor
> 2021年1月12日

## 泛型提案

我们提出[一个Go语言变更提案](https://golang.org/issue/43651)，用于让类型系统和函数支持类型参数，类型参数使通用编程模式成为可能。

## 为什么支持泛型？

泛型可以提供强大的构建代码块，让代码共享和程序构建更加简便。泛型编程意味着可以先实现功能和定义数据结构，而准确的类型可以留到后面指定。比如，一个操作某些任意数据类型切片的函数，当函数被调用时才会指定实际的数据类型。或者，一个存储任意类型的数据结构，当创建这个数据结构实例时，才会指定实际存储的类型。

自从Go在2009年首次发布后，泛型的支持一直都是最常见的语言特性需求之一。在[之前的博文](https://blog.golang.org/why-generics)中，你可以了解更多泛型有用的原因。

尽管泛型有明确的使用场景，但将它融入到像Go一样的语言中是非常困难的。[在Go中首次（有缺陷的）添加泛型的尝试](https://golang.org/design/15292/2010-06-type-functions)可以追溯到2010年。在过去的十年中也有多次其他的尝试。

在过去的几年中，我们在设计草案上的一系列工作，最终形成了[一个基于类型参数的设计方案](https://golang.org/design/go2draft-type-parameters)。这份设计草案从Go编程社区博采众长，很多朋友在[之前博文](https://blog.golang.org/generics-next-step)中提到的[泛型游乐场](https://go2goplay.golang.org/)中进行了体验。Ian Lance Taylor 在[GopherCon 2019上的演讲](https://www.youtube.com/watch?v=WzgLqE-3IhY)中介绍了添加泛型的原因和我们现在遵循的策略。Robert Griesemer在[之后GopherCon 2020的演讲中分享了设计上的变更和实现细节](https://www.youtube.com/watch?v=TborQFPY2IM)。语言的变更是完全后向兼容的，因此现有的Go程序将继续如现在一般正常运行。我们认为设计草案已经足够好也足够简单，是时候提议将它加入到Go中了。

## 现在的进度是什么？

[语言变更提案流程](https://golang.org/s/proposal)是我们对Go语言进行变更的方法。现在我们已经[开始了将泛型添加到Go的未来一个版本的流程](https://golang.org/issue/43651)。我们欢迎实质性的批评和建议，但请避免重复之前的评论，也请[避免简单的加一和减一的评论](https://golang.org/wiki/NoPlusOne)。相反，你可以在赞同或反对的评论或者整个提案下添加`thumbs-up/thumbs-down emoji`表情。

和所有的语言变更提案一样，我们的目标是对加入泛型或终止这个提案达成共识。我们明白，这个量级的变更肯定无法让Go社区的每个人都满意，但我们期望可以达成所有人都能接受的决定。

如果通过了这个提案，那么在今年底或者作为Go 1.18 beta版本的一部分，我们将提供一个完备但可能并未完全优化的泛型实现供大家尝鲜。

## 相关文章 

- [泛型的下一步](https://blog.golang.org/generics-next-step)
- [Go 1.15的提案](https://blog.golang.org/go1.15-proposals)
- [试验性，简洁性，可移植](https://blog.golang.org/experiment)
- [为什么支持泛型？](https://blog.golang.org/why-generics)
- [Go 2的下一步规划](https://blog.golang.org/go2-next-steps)
- [Go 2，我们来了！](https://blog.golang.org/go2-here-we-come)
