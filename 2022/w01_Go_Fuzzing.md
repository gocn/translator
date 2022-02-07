# Go 模糊测试

- 原文地址：https://tip.golang.org/doc/fuzz/
- 原文作者：Go Team
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2022/w01_Go_Fuzzing.md
- 译者：[fivezh](https://github.com/fivezh)
- 校对：[zxmfke](https://github.com/zxmfke)

从 Go 1.18 版本开始，标准工具集开始支持模糊测试。

## 概述

模糊测试（Fuzzing）是一种自动化测试方法，通过不断地控制程序输入来发现程序错误。Go 中模糊测试使用覆盖率引导来智能浏览被测试代码，发现并向用户报告错误。因为模糊测试可以触达人们常常忘记的边界测试用例，所以对查找安全隐患和漏洞特别有价值。

下面是 [模糊测试](https://tip.golang.org/doc/fuzz/#glos-fuzz-test) 的一个例子，标注了其中主要组成部分。

![示例代码中展示了整个模糊测试的情况，其中有一个模糊目标。用f.Add在模糊目标之前添加测试种子语料库，模糊目标的参数作为模糊参数被突出显示。](../static/images/2022/w1_Go_Fuzzing/example.png)

## 编写和运行模糊测试

### 要求

下面是模糊测试必须遵守的规则：

- 模糊测试必须是以 `FuzzXxx` 命名的函数，只能接收一个 `*testing.F` 的参数，且没有返回值
- 模糊测试必须在 *_test.go 文件中运行
- 一个 [模糊目标](https://tip.golang.org/doc/fuzz/#glos-fuzz-target) 必须是调用 `(*testing.F).Fuzz` 的方法，该方法接收 `*testing.T` 作为首个参数，紧随之后的是模糊参数。该函数没有返回值
- 每个模糊测试中必须有一个模糊目标
- 所有的 [语料库](https://tip.golang.org/doc/fuzz/#glos-seed-corpus) 中的条目必须和 [模糊参数](https://tip.golang.org/doc/fuzz/#fuzzing-arguments) 相同类型、顺序一致。 这一要是适用于调用 `(*testing.F).Add` 函数和模糊测试 `testdata/fuzz` 目录下的所有文件
- 模糊参数只能是如下类型：
    - `string`, `[]byte`
    - `int`, `int8`, `int16`, `int32`/`rune`, `int64`
    - `uint`, `uint8`/`byte`, `uint16`, `uint32`, `uint64`
    - `float32`, `float64`
    - `bool`

### 建议

下面的建议将帮助你从模糊处理中获得最大收益。

- 模糊测试应该在支持覆盖检测的平台上运行（目前是 AMD64 和 ARM64），如此语料库可以在运行过程中进行有意义的增长，并且在模糊测试时可以覆盖更多代码
- 模糊目标应该是快速和确定的，这样模糊引擎就能有效地工作，新的失败和代码覆盖率就能轻易地重现
- 由于模糊目标是以非确定性的顺序在多个 worker 间并行调用，所以模糊目标的状态不应该在每次调用结束后持续存在，而且模糊目标的行为不应该依赖于全局状态

### 自定义设置

默认的 go 命令设置适用于大多数模糊测试的情况。通常情况下，在命令行上执行的模糊测试应该是这样的

```plain
$ go test -fuzz={FuzzTestName}
```

然而，`go`命令在运行模糊测试时也提供了一些设置，这些设置在 [`cmd/go`包文档](https://pkg.go.dev/cmd/go) 中。

其中几个:

- `-fuzztime`: 在退出前执行模糊目标的总时间或迭代次数，默认为无限期地
- `-fuzzminimizetime`: 在每次最小化尝试中，模糊目标将被执行的时间或迭代次数，默认为 60 秒。你可以通过 `-fuzzminimizetime 0` 完全禁用最小化设置
- `-parallel`: 同时运行的模糊处理进程的数量，默认为`$GOMAXPROCS`。目前，在模糊摸索过程中设置 `-cpu` 没有作用

### 语料库文件格式

语料库文件是以一种特殊的格式进行编码的。这对于[种子语料库](https://tip.golang.org/doc/fuzz/#glos-seed-corpus)和[生成语料库](https://tip.golang.org/doc/fuzz/#glos-generated-corpus)是相同的格式。

下面是一个语料库文件的例子：

```plain
go test fuzz v1
[]byte("hello\\xbd\\xb2=\\xbc ⌘")
int64(572293)
```

第一行是用来通知模糊测试引擎文件的编码版本。虽然目前没有计划未来的编码格式版本，但设计上必须支持这种可能性。

下面的每一行都是构成语料库条目的值，如果需要，可以直接复制到 Go 代码中。

在上面的例子中，我们有一个`[]byte`，后面是一个`int64`。这些类型必须与模糊处理的参数完全类型匹配、顺序一致。这些类型的模糊测试目标会是这样的：

```plain
f.Fuzz(func(*testing.T, []byte, int64) {})
```

指定自定义种子语料库的最简单方法是使用`(*testing.F).Add`方法。在上面的例子中，可以这样操作：

```plain
f.Add([]byte("hello\\xbd\\xb2=\\xbc ⌘"), int64(572293))
```

然而，可能有一些大的二进制文件，你不希望将其作为代码复制到你的测试中，而是作为单独的种子语料库条目保留在 `testdata/fuzz/{FuzzTestName}` 目录下。[`file2fuzz`](https://pkg.go.dev/golang.org/x/tools/cmd/file2fuzz)工具可以用来将这些二进制文件转换成以 `[]byte` 编码的语料库文件。

如此使用该工具:

```plain
$ go install golang.org/x/tools/cmd/file2fuzz@latest
$ file2fuzz
```

## 相关资源

- 教程:

    - 关于用 Go 进行模糊测试的介绍性教程，请参见[博文](https://go.dev/blog/fuzz-beta)
    - 更多内容即将来临!

- 文档:

    - [`testing`](https://pkg.go.dev//testing#hdr-Fuzzing)包文档描述了在编写模糊测试时使用的`testing.F`类型
    - [`cmd/go`](https://pkg.go.dev/cmd/go) 包文档描述了与模糊处理相关的标志

- 技术细节:

    - [设计初稿](https://golang.org/s/draft-fuzzing-design)
    - [提案](https://golang.org/issue/44551)

## 词汇表

**语料库条目（corpus entry）:** 语料库中的一条输入记录，可以在模糊测试时使用。这可以是一个特殊格式的文件，或者是对`(*testing.F).Add`的调用

**覆盖面指导（coverage guidance）:** 一种使用代码覆盖率的扩展来确定哪些语料库条目值得保留以供将来使用的模糊测试方法

**模糊目标（fuzz target）:** 模糊测试的函数，用来在模糊测试时执行语料库条目和生成对应的值。它通过向`(*testing.F).Fuzz`传递函数来提供给模糊测试

**模糊测试（fuzz test）:** 测试文件中用于模糊处理的一个函数，其形式为`func FuzzXxx(*testing.F)`

**模糊化（fuzzing）:** 一种自动测试，它不断地操纵程序的输入，以发现代码潜在问题，如错误或[漏洞](https://tip.golang.org/doc/fuzz/#glos-vulnerability)

**模糊参数（fuzzing arguments）:** 传递给模糊目标的类型，并由[mutator](https://tip.golang.org/doc/fuzz/#glos-mutator)进行变异处理

**模糊引擎（fuzzing engine）:** 一个管理模糊处理的工具，包括维护语料库、调用突变器、识别新的覆盖范围和报告错误

**生成的语料库（generated corpus）:** 一个语料库，它由模糊引擎在模糊处理过程中长期维护，以跟踪进展。它被保存在`$GOCACHE/fuzz`中

**突变器（ mutator）:** 一个在模糊处理时使用的工具，在将语料库条目传递给模糊处理目标之前，对其进行随机处理

**包（package）:** 同一目录下的源文件的集合，这些文件被编译在一起。请参阅 Go 语言规范中的 [Packages 部分](https://tip.golang.org/ref/spec#Packages)。

**种子语料库（seed corpus）:** 用户为模糊测试提供的语料库，可用于指导模糊测试引擎。它由模糊测试中`f.Add`调用添加的语料库条目，以及软件包中`testdata/fuzz/{FuzzTestName}`目录下的文件组成

**测试文件（test file）:** 一个格式为 xxx_test.go 的文件，可以包含测试、基准、例子和模糊测试

**漏洞（vulnerability）:** 一种代码中安全敏感的弱点，可被攻击者所利用

## 反馈

如果你遇到任何问题或有一个关于功能的想法，欢迎[提交问题](https://github.com/golang/go/issues/new?&labels=fuzz)

关于该功能的讨论和一般反馈，也可以参与 Gophers Slack 的[#fuzzing 频道](https://gophers.slack.com/archives/CH5KV1AKE)