# 基于性能分析的优化预览

- 原文地址：https://go.dev/blog/pgo-preview
- 原文作者：Michael Pratt
- 本文永久链接：https://github.com/gocn/translator/blob/master/2023/w08_Profile_guided_optimization_prview.md
- 译者：[cvley](https://github.com/cvley)
- 校对：[Cluas](https://github.com/Cluas)


当你构建一个 Go 二进制文件时，Go 编译器会执行优化，以尝试生成性能最佳的二进制文件。 例如，常量传播可以在编译时计算常量表达式，从而避免运行时计算成本。逃逸分析可避免为局部范围的对象分配堆内存，从而避免 GC 开销。内联将简单函数的主体复制到调用者中，通常会在调用方中进一步优化（例如额外的常量传播或更好的转义分析）。

Go 随着版本的升级不断提升优化，但这并不总是一件容易的事。有些优化是可调的，但编译器不能只在每个函数上”将其调到 11”，因为过于激进的优化实际上会降级性能或导致构建时间过长。其他的优化要求编译器对函数中的“常见”和“不常见”路径进行判断调用。 编译器必须根据静态启发式方法做出最佳猜测，因为它无法知道哪些情况在运行时是常见的。

或者说它能吗？

由于没有关于如何在生产环境中使用代码的明确信息，编译器只能对包的源代码进行操作。 但我们确实有一个评估生产行为的工具：[性能分析](https://go.dev/doc/diagnostics#profiling)。如果我们向编译器提供性能分析文件，它可以做出更明智的决策：更积极地优化最常用的函数，或者更准确地选择常见情况。

使用应用程序行为的性能分析文件进行编译器的优化称为基于分析文件的优化 （Profile-Guided Optimization，PGO）_（也称为反馈导向优化 （Feedback-Directed Optimization，FDO））_。

Go 1.20 包含用于预览的 PGO 的初始支持。 完整文档请参阅[按配置文件优化用户指南](https://go.dev/doc/pgo)。仍然有一些粗糙的边界情况可能无法在生产环境使用，但我们希望您尝试一下，并将[遇到的任何问题反馈或建议发送给我们](https://go.dev/issue/new)。

## 示例

让我们构建一个将 Markdown 转换为 HTML 的服务：用户将 Markdown 源代码上传到 `/render`，然后返回转换好的 HTML。 我们可以使用 [`gitlab.com/golang-commonmark/markdown`](https://pkg.go.dev/gitlab.com/golang-commonmark/markdown) 轻松实现这一点。

### 建立开发环境

```plain
$ go mod init example.com/markdown
$ go get gitlab.com/golang-commonmark/markdown@bf3e522c626a
```

在 `main.go`:

```plain
package main

import (
    "bytes"
    "io"
    "log"
    "net/http"
    _ "net/http/pprof"

    "gitlab.com/golang-commonmark/markdown"
)

func render(w http.ResponseWriter, r *http.Request) {
    if r.Method != "POST" {
        http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
        return
    }

    src, err := io.ReadAll(r.Body)
    if err != nil {
        log.Printf("error reading body: %v", err)
        http.Error(w, "Internal Server Error", http.StatusInternalServerError)
        return
    }

    md := markdown.New(
        markdown.XHTMLOutput(true),
        markdown.Typographer(true),
        markdown.Linkify(true),
        markdown.Tables(true),
    )

    var buf bytes.Buffer
    if err := md.Render(&buf, src); err != nil {
        log.Printf("error converting markdown: %v", err)
        http.Error(w, "Malformed markdown", http.StatusBadRequest)
        return
    }

    if _, err := io.Copy(w, &buf); err != nil {
        log.Printf("error writing response: %v", err)
        http.Error(w, "Internal Server Error", http.StatusInternalServerError)
        return
    }
}

func main() {
    http.HandleFunc("/render", render)
    log.Printf("Serving on port 8080...")
    log.Fatal(http.ListenAndServe(":8080", nil))
}

```

构建并运行服务器：

```plain
$ go build -o markdown.nopgo.exe
$ ./markdown.nopgo.exe
2023/01/19 14:26:24 Serving on port 8080...
```

让我们尝试从另一个终端发送一些 Markdown。我们可以将 Go 项目中的 README 文件作为示例文档：

```plain
$ curl -o README.md -L "https://raw.githubusercontent.com/golang/go/c16c2c49e2fa98ae551fc6335215fadd62d33542/README.md"
$ curl --data-binary @README.md http://localhost:8080/render
<h1>The Go Programming Language</h1>
<p>Go is an open source programming language that makes it easy to build simple,
reliable, and efficient software.</p>
...
```

### 性能分析

现在我们有一个可用的服务，让我们收集一个性能分析文件并使用 PGO 重新构建，看看是否获得了更好的性能。

在 `main.go` 中，我们引用了 [net/http/pprof](https://pkg.go.dev/net/http/pprof)，它会自动向服务器添加一个接口来获取 CPU 的性能分析文件。

通常，您希望从生产环境中收集性能分析文件，以便编译器获得生产环境中代表性行为。 由于此示例没有“生产”环境，因此我们将创建一个简单的程序来生成负载，以便收集性能分析文件。 复制此[程序](https://go.dev/play/p/yYH0kfsZcpL)的源代码到 `load/main.go` 中并启动负载生成器（确保服务器仍在运行！）。

```plain
$ go run example.com/markdown/load
```

在负载生成器还在运行中，从服务器上下载一个性能分析文件：

```plain
$ curl -o cpu.pprof "http://localhost:8080/debug/pprof/profile?seconds=30"
```

一旦下载完成，关闭负载生成器和服务器。

### 使用性能分析文件

我们可以在 `go build` 中使用 `-pgo` 标记让 Go 工具链使用 PGO 进行构建。`-pgo` 接受两种参数：要使用的性能分析文件的路径，或者 `auto`，`auto` 将使用主包目录下的 `default.pgo` 文件。

我们建议将配置文件提交到代码仓库中。将性能分析文件与源代码一起存储可确保用户只需拉取仓库（通过版本控制系统或通过 `go get`）即可自动访问性能分析文件，并且保证构建可重现。 在 Go 1.20 中，`-pgo=off` 是默认设置，因此用户仍然需要添加 `-pgo=auto` ，但预计 Go 的未来版本会将默认值更改为 `-pgo=auto`，这将自动为构建二进制文件的任何人提供 PGO 的好处。

让我们构建：

```plain
$ mv cpu.pprof default.pgo
$ go build -pgo=auto -o markdown.withpgo.exe
```

### 评估

我们将使用负载生成器的 Go 基准版本来评估 PGO 对性能的影响。 [将此基准复制到](https://go.dev/play/p/6FnQmHfRjbh) `load/bench_test.go`。

首先，我们将对没有 PGO 的服务器进行基准测试。启动该服务器：

```plain
$ ./markdown.nopgo.exe
```

在服务器运行时，执行一些基准测试迭代：

```plain
$ go test example.com/markdown/load -bench=. -count=20 -source ../README.md > nopgo.txt
```

完成后，终止原服务器并启动 PGO 版本的服务器：

```plain
$ ./markdown.withpgo.exe
```

在服务器运行时，执行一些基准测试迭代：

```plain
$ go test example.com/markdown/load -bench=. -count=20 -source ../README.md > withpgo.txt
```

完成后，我们对比结果：

```plain
$ go install golang.org/x/perf/cmd/benchstat@latest
$ benchstat nopgo.txt withpgo.txt
goos: linux
goarch: amd64
pkg: example.com/markdown/load
cpu: Intel(R) Xeon(R) W-2135 CPU @ 3.70GHz
        │  nopgo.txt  │            withpgo.txt             │
        │   sec/op    │   sec/op     vs base               │
Load-12   393.8µ ± 1%   383.6µ ± 1%  -2.59% (p=0.000 n=20)
```

新版本快了大约 2.6%！ 在 Go 1.20 中，工作负载通常会通过启用 PGO 获得 2% 到 4% 的 CPU 使用率改进。 性能分析文件包含有关应用程序行为的大量信息，Go 1.20 刚刚开始使用这些信息进行内联。随着编译器的更多部分利用 PGO，未来的版本将继续提高性能。

## 下一步

在此示例中，在收集性能分析文件后，我们使用与原始构建中使用的完全相同的源代码重新编译了服务器。在现实世界中，开发过程是持续不断的。因此，我们可能会从生产环境中收集一个性能分析文件，该文件来自运行上周代码的服务，并使用它来构建今天的源代码。这完全没问题！Go 中的 PGO 完全可以正确处理对源码的微小更改。

有关使用 PGO 的更多信息、最佳实践和需要注意的注意事项，请参阅[按性能分析文件用户指南](https://go.dev/doc/pgo)。

请将您的反馈发送给我们！ PGO 仍处于预览阶段，我们很想听到任何难以使用、无法正常工作等内容。 请在 <https://go.dev/issue/new> 提交问题。
