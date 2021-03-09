# Go security cheatsheet: 8 security best practices for Go developers
# Go 安全性备忘单：Go 开发者的 8 个安全性最佳实践
- 原文地址：https://snyk.io/blog/go-security-cheatsheet-for-go-developers/
- 原文作者：Eric Smalling, Gerred Dillon
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2021/w10_Go_Security_cheatsheet.md
- 译者：[guzzsek](https:/github.com/guzzsek)
- 校对: [lsj1342](github.com/lsj1342)
- 校对: [fivezh](https://github.com/fivezh)
- 校对: [](github.com/)




在我们的备忘单系列中，我们将为 Go 开发者介绍八项有关于 Go 安全的最佳实践。 Go 语言集成了许多内置特性，这些功能（与 C 等较早和较低级别的语言相比）比如 -- 内存垃圾回收和强类型指针，可以促进更安全的开发实践。


这些功能通过移除开发者自我管理内存的责任，帮助开发者避免了可能被利用的漏洞。 但是，依然存在开发者应注意的安全最佳实践。 在 Dan Enman（Snyk的高级软件工程师）的帮助下，由 Eric Smalling 和 Gerred Dillon 撰写的这份备忘单，涉及到其中的一些更常见的主题。

1. 使用 Go Modules
2. 扫描 CVE 之间的依赖关系
3. 使用 Go 标准加密软件包
4. 使用 html/template 来避免 XSS 攻击
5. shell 子进程
6. 避免使用 unsafe 和 cgo 特性
7. 谨慎使用反射
8. 最小化容器攻击面





## 1\.使用 Go Modules


从 go 1.11 版本开始， [Go Modules](https://golang.org/ref/mod) 正式成为 go 版本依赖的管理工具，而旧的 [Vendor](https://github.com/kardianos/govendor) 和 [Dep](https://github.com/golang/dep) 工具已被弃用。Go Modules 允许指定依赖版本，包括可传递模块，还可以通过 `go.sum` 文件提供的校验和数据库，校验发生变化的依赖模块。


首先，您应该在当前目录的中运行 `go mod init [namespace/project-name]` 命令来初始化项目。


**$ go mod init mycorp.com/myapp**



这将在当前目录中创建一个 `go.mod` 文件，其中包含您的项目名称和当前使用的 Go 版本。假如您的源代码需要引入第三方库，则只需运行 `go build`（或 `test`，`install` 等）命令，即可使用所依赖的第三方库（包括所指定的版本）并且更新 `go.mod` 文件。 您还可以使用 `go get` 更新您的依赖第三方库，这会将依赖的第三方库更新为指定版本，这也将更新 `go.mod` 文件。


示例 `go.mod` 文件：

```
module mycorp.com/myapp
go 1.15
require (
  github.com/containerd/console v1.0.1
  rsc.io/quote/v3 v3.1.0
)
```


请注意，**go mod init mycorp.com/myapp** 还创建了一个名为 `go.sum` 的文件。 这个文件包含每个第三方库的哈希列表，Go 可以利用该列表来验证每次构建是否都使用相同的依赖。 您应该将 `go.mod` 和 `go.sum` 文件都加入到版本管理中。


可以在 Go 的官方博客上找到关于  [Using Go Modules](https://blog.golang.org/using-go-modules) 的教程，这是学习更多有关于 Go Modules 的极好资源，包括学习如何指定依赖版本，清理未使用的依赖等等。


## 2\. 扫描 CVE 之间的依赖关系



与大多数项目一样，您的应用程序所依赖的模块中的代码量通常会超过应用程序本身的代码量，而依赖的这些第三方库通常是引入安全漏洞的一个途径。 借助 Snyk 这类的工具， 一款由我们提供的通用[漏洞数据库](https://snyk.io/product/vulnerability-database/)，可以测试这些依赖关系图中的已知漏洞，建议进行升级以修复所发现的问题，甚至以持续监视您的项目中是否存在将来发现的任何新漏洞。


例如，仅在 Go 应用程序上运行 `synk test` 将解析您的模块并报告任何已知的  [CVEs](https://snyk.io/learn/what-is-cve-vulnerablity/)，以及有关您可以升级到的任何修复版本的信息。 此外，基于 Web 的 Snyk 工具可以直接并连续监视 GitHub 仓库，即使在您未更改代码或在其上运行 CI 构建的情况下，也可以提醒您将来发现的漏洞。


## 3\. 使用 Go 标准加密软件包而不是第三方所提供的



Go 标准库[加密程序包](https://golang.org/pkg/crypto/)已经过安全研究人员的严格审核，但由于它们提供的功能并不全面，因此您可能会想使用第三方程序包。


就像不使用自己的加密算法一样，您应该非常警惕第三方加密库，因为它们可能会或可能不会受到相同级别的审核。 您应该需要清楚地知道您的应用程序所依赖包的来源。


## 4\.使用 html/template 来避免 XSS 攻击



使用 `io.WriteString()` 或 `text/template` 包传递回 Web 客户端的未经过滤的字符串， 这可能会使您的用户遭受跨站点脚本 [(XSS) 攻击](https://snyk.io/learn/cross-site-scripting/)。 这是因为返回的字符串中的所有 HTML 标签都将不进行编码而呈现到输出流中，并且如果未明确设置，则可能会发送带有错误定义的 `Content-Type: plain/text` 响应标头。


使用 `html/template` 包是一种简单的自动对返回的内容进行网络编码的方法，而不是尝试在应用逻辑中自己实现。 [OWASP/GO-SCP](https://github.com/OWASP/Go-SCP) 文档有出色的章节和示例，详细介绍了有关这方面的内容。


## 5\. shell 子进程


在 Go 中，shell 子进程基本上可以直接对您的系统进行访问，并且这种方式通常仅限于命令行工具类型的应用程序。 在可能的情况下，始终希望使用适当的模块在 Go 代码中本地实现（译者注：尽量使用 go 代码实现， 而不是依赖于调用系统外部命令）。


如果您确实需要使用 shell 子进程，请务必清理可能传递给 shell 的任何外部来源数据以及返回的数据，以确保您的应用程序不会暴露有关基础系统的不必要的详细信息（译者注： 就是不要对外暴露操作系统的基本信息）。这种考虑类似于要注意模板渲染攻击（请参阅上面的＃4）或者 [SQL 命令注入](https://snyk.io/learn/sql-injection/)。 还应考虑将调用运行外部流程作为应用程序请求线程的一部分进行操作可能会产生其他副作用，这些副作用是您无法从 Go 代码中控制的，例如对文件系统的更改，对外部依赖项的调用或对安全格局的更改 可能会阻止此类调用-例如，由在容器中运行或由 AppArmor，SELinux 等工具施加的限制


## 6\.谨慎使用 unsafe 和 cgo


与 C 语言非常相似，Go 支持使用指针类型变量, 但是，go 语言中的指针具有严格的类型安全性，以保护开发者免受意外或者恶意的副作用。 在C语言中，您始终可以定义未分配任何类型的 `void *` 指针； 要在 Go 中执行相同的操作，请使用恰当命名的 `unsafe` 标准包来打破类型安全性限制。 Go文档中通常不建议使用 `unsafe`，因为它可以直接访问内存，再加上用户数据，攻击者有可能破坏 Go 的内存安全性。


同样令人关注的是使用 `cgo`，这是一个功能强大的命令，可让您将任意 C 库集成到 Go 应用程序中。 像任何强大的工具一样，必须非常谨慎地使用 `cgo`，因为您正相信以不安全的语言编写的完全外部的依赖关系可以正确地完成所有操作。 如果该外部代码中潜伏着错误或恶意例程，那么Go内存安全网将无法为您提供保护。 可以通过在构建中简单地设置 `CGO_ENABLED = 0` 来禁用 `cgo`，如果您不需要显式使用 `cgo`，这通常是一个安全的选择，因为大多数现代的 Go 库都是用纯 Go 代码编写的。


## 7\. 反射


Go 是一种强类型语言，这意味着变量类型很重要。 有时，您需要有关在运行时代码中反映的变量的类型或值信息。 Go 提供了一个 `reflect` 包，它允许您查找和操纵任意类型的变量的类型和值，例如，确定变量是否属于某种类型，或者包含某些属性或函数。


尽管反射很有用，但也增加了在 Go 代码中运行时引入错误的风险。 如果您尝试以错误的方式修改被反射的变量（例如，设置无法在结构上设置的值），则代码会引发 panic。 很难很好地掌握代码流以及所反映的各种类型和值类型。 最后，在使用反射类型或值时，您可能需要断言这可能会使代码混淆的类型，并导致运行时错误。


尽管反射功能很强大，但是在 Go 的类型和接口系统中，应很少使用它，因为它很容易引发意想不到的问题。


## 8\. 最大限度地减小容器攻击面


许多 Go 应用程序没有外部依赖关系，并且设计为可以在容器中运行，因此我们应该使用几种镜像构建技术来简化对它们可用的文件系统。 最简单的方法之一是使用[多阶段](https://docs.docker.com/develop/develop-images/multistage-build/) Dockerfile，在该阶段我们在构建阶段构建应用程序，然后将临时基础镜像用于部署工件镜像。


看一下以下 Dockerfile 示例：

```
  1| FROM golang:1.15 as build
  2| 
  3| COPY . .
  4|
  5| ENV GOPATH=""
  6| ENV CGO_ENABLED=0
  7| ENV GOOS=linux
  8| ENV GOARCH=amd64
  9| RUN go build -trimpath -v -a -o myapp -ldflags="-w -s"
 10| RUN chmod +x go-goof
 11| 
 12| RUN useradd -u 12345 moby
 13| 
 14| FROM scratch
 15| COPY --from=build /go/myapp /myapp
 16| COPY --from=build /etc/passwd /etc/passwd
 17| USER moby
 18| 
 19| ENTRYPOINT ["/myapp"]
```


如果您是 Dockerfile 的新手，那么它们是逐步的说明，几乎所有 OCI 镜像构建都可以使用它们来构建镜像。 它们记录在这里。 此示例是一个多阶段 Dockerfile，具有两个不同的阶段：构建阶段和最终的运行时镜像阶段



### **阶段1，第1-12行：构建阶段**



从官方的 `golang：1.15` 基础镜像开始，在此阶段，我们将设置一些环境变量并构建我们的 Go 应用程序。 当此阶段完成时，将使用带有 `build` 标签的临时镜像进行缓存，稍后我们可以参考该标签。


您可能想知道我们传递到构建中的所有环境 var 和参数是什么：

-   `GOPATH=””`：清除此变量（在 `golang：1.15` 基础镜像中设置），因为在使用Go模块时不需要此变量。
-   `CGO_ENABLED=0`: Disables `cgo` (see section 6 above).
-   `CGO_ENABLED=0`：禁用 `cgo`（请参阅上面的第6节）。
-   `GOOS=linux`: Explicitly tells go to build for the linux operating system.
-   `GOOS=linux`：明确告诉go用于linux操作系统的构建。
-   `GOARCH=amd66`：明确告知 go 构建 `amd64`（Intel）体系结构的镜像。
-   `-trimpath`：从二进制文件中删除文件系统路径信息。
-   `ldflag -s`：省略符号表和调试信息。
-   `ldflag -w`：省略DWARF符号表。


该设置集合将构建几乎所有可能的最小二进制文件，但是其中一些可能不适用于您的应用程序，因此请根据需要进行选择。


### **Stage 2, lines 13–10: the runtime image stage**

### **第2阶段，第13-10行：运行时镜像阶段**


在此阶段，我们只需将静态二进制文件和 `/etc/passwd`  文件从 `build` 阶段复制到一个空的[暂存文件系统](https://hub.docker.com/_/scratch)中，指定适当的所有权和在容器启动时运行的命令。



要构建此镜像，我们只需在与Dockerfile相同的目录中运行以下命令：


**docker build -t [app image name]:[version tag] `.`**


注意：`.` 在该构建行的末尾，这一点很重要，因为它告诉构建系统在哪里可以找到 Dockerfile 及其可能引用的任何其他文件。


生成的镜像将具有一个包含两个文件的文件系统：我们的应用程序和具有 `moby` 用户的 passwd 文件（用户名无关紧要，我们只是不想在容器中以 root 身份运行任何文件）。 不会有 `sh`，`ps` 或攻击者可以利用的任何其他文件。 当然，如果您需要其他文件来运行应用程序，则需要包含这些文件或在运行时将其挂载。
