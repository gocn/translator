# Go security cheatsheet: 8 security best practices for Go developers
# Go 安全性备忘单：Go 开发人员的 8 个安全性最佳实践
- 原文地址：https://snyk.io/blog/go-security-cheatsheet-for-go-developers/
- 原文作者：Eric Smalling, Gerred Dillon

- 本文永久链接：https:/github.com/gocn/translator/blob/master/2021/w10_Go_Security_cheatsheet.md
- 译者：[guzzsek](https:/github.com/guzzsek)
- 校对[](https:/github.com/)

In this installment of our cheatsheet series, we’re going to cover eight Go security best practices for Go developers. The Go language incorporates many built-in features that promote safer development practices—compared to older and lower-level languages like C—such as memory garbage collection and strongly-typed pointers. 

在我们的备忘单系列的这一部分中，我们将介绍 Go 开发人员的八项 Go 安全最佳实践。 Go 语言集成了许多内置功能，这些功能可以促进更安全的开发实践（与 C 等较早和较低级别的语言相比），例如内存垃圾回收和强类型指针。

These features help developers avoid bugs that can lead to exploits by removing the responsibility to self-manage memory. However, there are still security best practices that programmers should be aware of. This cheatsheet, authored by Eric Smalling, Gerred Dillon and with help from Dan Enman (Sr. Software Engineer at Snyk), addresses some of the more common topics.

这些功能通过消除自行管理内存的责任，帮助开发人员避免了可能导致利用的漏洞。 但是，仍然存在程序员应注意的安全最佳实践。 这份备忘单，由 Eric Smalling，Gerred Dillon 撰写，并在 Dan Enman（Snyk的高级软件工程师）的帮助下，解决了一些较常见的主题。

1. Use Go Modules

1. 使用 Go Modules

2. Scan dependencies for CVEs

2. 扫描 CVE 的依赖关系

3. Use Go standard crypto packages

3. 使用 Go 标准加密软件包

4. Use html/template to help avoid XSS attacks

4. 使用 html/template 来避免 XSS 攻击
   
5. Subshelling

5. 子壳化
   
6. Avoid unsafe and cgo

6. 避免使用 unsafe 和 cgo 特性
   
7. Use reflection sparingly

7. 谨慎使用反射
   
8. Minimizing container attack surface

8. 最小化容器攻击面
   



## 1\. Use Go Modules

## 1\.使用 Go Modules

The [Go Modules](https://golang.org/ref/mod) system is the official dependency management system as of v1.11 with the older [Vendor](https://github.com/kardianos/govendor) and [Dep](https://github.com/golang/dep) systems having been deprecated. Go Modules allow for dependency version pinning, including transitive modules, and also provides assurance against unexpected module mutation via the `go.sum` checksum database.

从1.1.1版开始， [Go Modules](https://golang.org/ref/mod) 系统是正式的依赖项管理系统，而旧的 [Vendor](https://github.com/kardianos/govendor) 和 [Dep](https://github.com/golang/dep) 系统已被弃用。Go Modules 允许依赖项版本固定，包括可传递模块，还可以通过 `go.sum` 校验和数据库提供针对意外模块突变的保证。

First, you should initialize your project by running `go mod init [namespace/project-name]` in the top-most level directory.

首先，您应该通过在最顶层目录中运行 `go mod init [namespace/project-name]` 来初始化项目。

**$ go mod init mycorp.com/myapp**

**$ go mod init mycorp.com/myapp**


This will create a file in the current directory named `go.mod` which contains your project name and the version of Go that you are currently using. Assuming your source code has package imports in them, simply running `go build` (or `test`, `install`, etc) will update the `go.mod` file with modules used including their versions. You can also use `go get` to update your dependencies, which allows for updating dependencies to specific versions, and this will also update `go.mod`. 

这将在当前目录 `go.mod` 中创建一个文件，其中包含您的项目名称和当前使用的 Go 版本。假设您的源代码中包含程序包导入，则只需运行 `go build`（或 `test`，`install` 等），即可使用所使用的模块（包括其版本）更新`go.mod` 文件。 您还可以使用 `go get` 更新依赖关系，从而可以将依赖关系更新为特定版本，这也将更新`go.mod`。

Example `go.mod` file:

示例 `go.mod` 文件：

```
module mycorp.com/myapp
go 1.15
require (
  github.com/containerd/console v1.0.1
  rsc.io/quote/v3 v3.1.0
)
```

Notice that a file named `go.sum` was created as well.  This file contains a list of hashes for each module used which is leveraged by Go to validate that the same binaries are used for every build. Both the `go.mod` and `go.sum` files should be checked into source control with your application code.

请注意，还创建了一个名为 `go.sum` 的文件。 该文件包含每个所用模块的哈希列表，Go 可以利用该列表来验证每个构建都使用相同的二进制文件。 应该使用您的应用程序代码将 `go.mod` 和 `go.sum` 文件都检查到源代码控制中。

The tutorial [Using Go Modules](https://blog.golang.org/using-go-modules), found on the the official Go Blog, is an excellent resource for learning more about Go Modules including how to pin transitive dependency versions, clean up unused dependencies, and more. 

可在官方 Go Blog 上找到的  [Using Go Modules](https://blog.golang.org/using-go-modules) 教程，是学习有关 Go Modules 的更多信息的极好资源，包括如何固定传递依赖版本，清理未使用的依赖等等。

## 2\. Scan dependencies for CVEs

## 2\. 扫描 CVE 的依赖关系


As with most projects, the amount of code in the modules that your application depends on often outweighs that of your application itself, and these external dependencies are a common vector for security vulnerabilities to be introduced. Tools like Snyk—powered by our extensive [Vulnerability Database](https://snyk.io/product/vulnerability-database/)—can be used to test these graphs of dependencies for known vulnerabilities, suggest upgrades to fix issues found, and even continuously monitor your projects for any new vulnerabilities that are discovered in the future. 

与大多数项目一样，您的应用程序所依赖的模块中的代码量通常会超过应用程序本身的代码量，而这些外部依赖关系是引入安全漏洞的常见媒介。 借助由我们广泛的[漏洞数据库](https://snyk.io/product/vulnerability-database/)提供支持的 Snyk 之类的工具，可以测试这些依赖关系图中的已知漏洞，建议进行升级以修复所发现的问题，甚至可以持续监视您的项目中是否存在将来发现的任何新漏洞。

For example, simply running `synk test` on a Go application will parse your modules and report back any known [CVEs](https://snyk.io/learn/what-is-cve-vulnerablity/), as well as info about any fixed versions of them that you can upgrade to.  Additionally, the Snyk web-based tools can monitor your GitHub repositories directly and continually, alerting you to vulnerabilities that are found in the future even if you haven’t changed your code or run a CI build on it. 

例如，仅在 Go 应用程序上运行 `synk test` 将解析您的模块并报告任何已知的  [CVEs](https://snyk.io/learn/what-is-cve-vulnerablity/)，以及有关您可以升级到的任何固定版本的信息。 此外，基于 Web 的 Snyk 工具可以直接并连续监视 GitHub 存储库，即使在您未更改代码或在其上运行 CI 构建的情况下，也可以提醒您将来发现的漏洞。


## 3\. Use Go standard crypto packages as opposed to third-party
## 3\. 使用 Go 标准加密软件包而不是第三方


The Go standard library [crypto packages](https://golang.org/pkg/crypto/) are well audited by security researchers but, because they aren’t all-inclusive, you may be tempted to use third-party ones.

Go 标准库[加密程序包](https://golang.org/pkg/crypto/)已经过安全研究人员的严格审核，但由于它们并不全面，因此您可能会想使用第三方程序包。

Much like not rolling your own cryptographic algorithms, you should be very wary of third-party cryptographic libraries as they may or may not be audited with the same level of scrutiny. Know your source.

就像不使用自己的加密算法一样，您应该非常警惕第三方加密库，因为它们可能会或可能不会受到相同级别的审核。 您应该需要清除地知道您的应用程序所依赖包的来源。

## 4\. Use html/template to help avoid XSS attacks

## 4\.使用 html/template 来避免 XSS 攻击


Unfiltered strings passed back to a web client using either `io.WriteString()` or the `text/template` package can expose your users to cross-site scripting [(XSS) attacks](https://snyk.io/learn/cross-site-scripting/). This is because any HTML tags in the strings returned will be rendered to the output stream without encoding and may also be sent with an incorrectly defined `Content-Type: plain/text` response header if it’s not explicitly set. 

使用 `io.WriteString()` 或 `text/template` 包传递回 Web 客户端的未经过滤的字符串可能会使您的用户遭受跨站点脚本 [(XSS) 攻击](https://snyk.io/learn/cross-site-scripting/)。 这是因为返回的字符串中的所有 HTML 标签都将不进行编码而呈现到输出流中，并且如果未明确设置，则可能会发送带有错误定义的 `Content-Type: plain/text` 响应标头。

Using the `html/template` package is a simple way to automatically web encode content returned rather than trying to make sure you’ve manually done it in your application logic. The [OWASP/GO-SCP](https://github.com/OWASP/Go-SCP) documentation has an excellent chapter and example detailing this topic.

使用 `html/template` 包是一种简单的自动对返回的内容进行网络编码的方法，而不是尝试确保已在应用程序逻辑中手动完成了此操作。 [OWASP/GO-SCP](https://github.com/OWASP/Go-SCP) 文档有出色的章节和示例，详细介绍了此主题。

## 5\. Subshelling

## 5\.子壳化

In Go, a `subshell` basically gives direct shell access to your system and its use is typically restricted to command-line tool type applications. Where possible, always prefer solutions implemented natively in Go code using appropriate modules.   

在 Go 中，子外壳程序基本上可以直接对您的系统进行外壳程序访问，并且其使用通常仅限于命令行工具类型的应用程序。 在可能的情况下，始终希望使用适当的模块在 Go 代码中本地实现的解决方案。

If you do find yourself needing to use a subshell, take care to sanitize any external sourced data that might get passed into it, as well as the data returned, to ensure your application isn’t exposing unnecessary details about the underlying system. This care is similar to the attention you would give to attacks on rendered templates (see #4 above) or [SQL command injections](https://snyk.io/learn/sql-injection/). Also consider that putting a call to run an external process as part of an application request thread could have other side effects that you cannot control from your Go code, such as changes to the file system, calls to external dependencies or changes to the security landscape that might block such calls—for example, limits imposed by running in a container or by tools like AppArmor, SELinux, etc

如果您确实需要使用子外壳，请务必清理可能传递给该外壳的任何外部来源数据以及返回的数据，以确保您的应用程序不会暴露有关基础系统的不必要的详细信息。 这种关心类似于您对呈现模板的攻击（请参阅上面的＃4）或 [SQL 命令注入](https://snyk.io/learn/sql-injection/)所给予的关注。 还应考虑将调用运行外部流程作为应用程序请求线程的一部分进行操作可能会产生其他副作用，这些副作用是您无法从 Go 代码中控制的，例如对文件系统的更改，对外部依赖项的调用或对安全格局的更改 可能会阻止此类调用-例如，由在容器中运行或由 AppArmor，SELinux 等工具施加的限制

## 6\. Use caution with unsafe and cgo

## 6\.谨慎使用 unsafe 和 cgo

Much like the C language, Go supports the use of pointer type variables—however, it does so with strict type safety to protect developers from unintended or even malicious side-effects. In C you can always define the `void*` pointer which has no typing assigned; to do the same kind of thing in Go you use the aptly-named `unsafe` standard package to break type-safety restrictions. Using `unsafe` is generally discouraged in the Go documentation as it allows for direct memory access, which combined with user data can potentially enable attackers to break Go’s memory safety.  

与 C 语言非常相似，Go 支持使用指针类型变量-但是，它具有严格的类型安全性，以保护开发人员免受意外甚至恶意的副作用。 在C语言中，您始终可以定义未分配任何类型的 `void *` 指针； 要在 Go 中执行相同的操作，请使用恰当命名的 `unsafe` 标准包来打破类型安全性限制。 Go文档中通常不建议使用 `unsafe`，因为它可以直接访问内存，再加上用户数据，攻击者有可能破坏Go的内存安全性。

Of similar concern is the use of `cgo`, a powerful command that allows you to integrate arbitrary C libraries into your Go application. Like any power tool, `cgo` must be used with extreme caution because you are trusting a completely external dependency written in an unsafe language to have done everything correctly; the Go memory safety net is not there to save you if there are bugs or malicious routines lurking in that external code. `cgo` can be disabled by simply setting `CGO_ENABLED=0` in your build and this is usually a safe option to use if you don’t explicitly need it as most modern Go libraries are written in pure Go code.

同样令人关注的是使用 `cgo`，这是一个功能强大的命令，可让您将任意 C 库集成到 Go 应用程序中。 像任何强大的工具一样，必须非常谨慎地使用 `cgo`，因为您相信以不安全的语言编写的完全外部的依赖关系可以正确地完成所有操作。 如果该外部代码中潜伏着错误或恶意例程，那么Go内存安全网将无法为您提供保护。 可以通过在构建中简单地设置 `CGO_ENABLED = 0` 来禁用 `cgo`，如果您不需要显式使用 `cgo`，这通常是一个安全的选择，因为大多数现代的 Go 库都是用纯 Go 代码编写的。

## 7\. Reflection

## 7\. 反射

Go is a strongly-typed language, which means variable types are important. Sometimes you need type or value information about a variable reflected in your code at runtime. Go offers a \`reflect\` package that allows you to find and manipulate the typing and value of a variable of an arbitrary type, for example, to find out if a variable is of a certain type, or contains certain properties or funcs.

Go 是一种强类型语言，这意味着变量类型很重要。 有时，您需要有关在运行时代码中反映的变量的类型或值信息。 Go 提供了一个 `reflect` 包，它允许您查找和操纵任意类型的变量的类型和值，例如，确定变量是否属于某种类型，或者包含某些属性或函数。

While reflection can be useful, it also increases the risk of runtime typing errors in your Go code. If you attempt to modify a reflected variable in a way that is not allowed (e.g. setting a value that isn’t settable on a struct) your code will panic. It can also be difficult to get a good grasp on the code flow, and the various type kinds and value kinds that are being reflected. Lastly, when working with reflected types or values, you may need to assert typings which can be confusing in code, and lead to runtime errors.

尽管反射很有用，但也增加了在 Go 代码中运行时键入错误的风险。 如果您尝试以不允许的方式修改反映的变量（例如，设置无法在结构上设置的值），则代码会出现恐慌。 很难很好地掌握代码流以及所反映的各种类型和值类型。 最后，在使用反射类型或值时，您可能需要断言可能会使代码混淆的类型，并导致运行时错误。

Reflection can be a powerful tool, but with Go’s typing and interface system, it should be rarely used as it can easily cause unexpected problems.

反射功能可能很强大，但是在Go的键入和界面系统中，应很少使用它，因为它很容易引起意外问题。

## 8\. Minimizing container attack surface

## 8\. 最大限度地减小容器攻击面

Many Go applications have no external dependencies and are designed to run in containers, so we should strip down the filesystem available to them by using a couple of image building techniques. One of the easiest ways to do this is by using a [multi-stage](https://docs.docker.com/develop/develop-images/multistage-build/) Dockerfile where we build the application in a build stage and then utilize a `scratch` base image for the deployment artifact image.  

许多 Go 应用程序没有外部依赖关系，并且设计为可以在容器中运行，因此我们应该使用几种镜像构建技术来简化对它们可用的文件系统。 最简单的方法之一是使用[多阶段](https://docs.docker.com/develop/develop-images/multistage-build/) Dockerfile，在该阶段我们在构建阶段构建应用程序，然后将临时基础镜像用于部署工件镜像。

Take a look at the following Dockerfile example:

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

If you’re new to Dockerfiles, they are the step-by-step instructions that just about any OCI image build can use to build up the images; they are documented [here](https://docs.docker.com/engine/reference/builder/). This example is a Multi-Stage Dockerfile, with two distinct stages: a build stage and the final, runtime image stage

如果您是 Dockerfile 的新手，那么它们是逐步的说明，几乎所有 OCI 镜像构建都可以使用它们来构建镜像。 它们记录在这里。 此示例是一个多阶段 Dockerfile，具有两个不同的阶段：构建阶段和最终的运行时镜像阶段


### **Stage 1, lines 1–12: the build stage** 

### **阶段1，第1-12行：构建阶段**


Starting from the official `golang:1.15` base image, in this stage we are setting some environment variables and building our Go application. When this stage completes a temporary image will be cached with a label of `build` that we can refer to later.

从官方的 `golang：1.15` 基本镜像开始，在此阶段，我们将设置一些环境变量并构建我们的 Go 应用程序。 当此阶段完成时，将使用带有 `build` 标签的临时镜像进行缓存，稍后我们可以参考该标签。

You are probably wondering what all of the environment vars and arguments we are passing into the build are:

您可能想知道我们传递到构建中的所有环境 var 和参数是什么：

-   `GOPATH=””`: Clearing out this var (which was set in the `golang:1.15` base image) as it’s not needed when using Go Modules.

-   `GOPATH=””`：清除此变量（在 `golang：1.15`基本镜像中设置），因为在使用Go模块时不需要此变量。
  
-   `CGO_ENABLED=0`: Disables `cgo` (see section 6 above).

-   `CGO_ENABLED=0`：禁用 `cgo`（请参阅上面的第6节）。

-   `GOOS=linux`: Explicitly tells go to build for the linux operating system.

-   `GOOS=linux`：明确告诉go用于linux操作系统的构建。

-   `GOARCH=amd66`: Explicitly tells go to build for `amd64` (Intel) architecture.

-   `GOARCH=amd66`：明确告知 go 构建 `amd64`（Intel）体系结构的镜像。

-   `-trimpath`: Remove filesystem path information from the binary.

-   `-trimpath`：从二进制文件中删除文件系统路径信息。

-   `ldflag -s`: Omit the symbol table and debug information.

-   `ldflag -s`：省略符号表和调试信息。
-   `ldflag -w`: Omit the DWARF symbol table。

-   `ldflag -w`：省略DWARF符号表。

This collection of settings will build, pretty much, the most minimal binary file possible but some of these may not be appropriate for your application, so choose as needed.

该设置集合将构建几乎所有可能的最小二进制文件，但是其中一些可能不适用于您的应用程序，因此请根据需要进行选择。


### **Stage 2, lines 13–10: the runtime image stage**

### **第2阶段，第13-10行：运行时镜像阶段**

In this stage, we simply copy the static binary and `/etc/passwd` files from the `build` stage into an empty, [scratch filesystem](https://hub.docker.com/_/scratch), specify appropriate ownership and the command to run at container startup.

在此阶段，我们只需将静态二进制文件和 `/etc/passwd`  文件从 `build` 阶段复制到一个空的[暂存文件系统](https://hub.docker.com/_/scratch)中，指定适当的所有权和在容器启动时运行的命令。


To build this image, we simply run the following from the same directory as the Dockerfile: 

要构建此镜像，我们只需在与Dockerfile相同的目录中运行以下命令：

**docker build -t \[app image name\]:\[version tag\] .**

**docker build -t [app image name]:[version tag] `.`**

**Note:** the **.** at the end of that build line, it’s important as that tells the build system where to find the Dockerfile and any other files it might reference.

注意：`.` 在该构建行的末尾，这一点很重要，因为它告诉构建系统在哪里可以找到 Dockerfile 及其可能引用的任何其他文件。

The resulting image will have a filesystem containing exactly two files: our application and the passwd file that has our `moby` user (the name of the user is unimportant, we just don’t want to run anything as root in the container). There will be no `sh`, `ps` or any other files that an attacker can leverage.  Of course, if you _need_ other files for the operation of your application, you’ll want to include them or mount them at run time.

生成的镜像将具有一个包含两个文件的文件系统：我们的应用程序和具有 `moby` 用户的 passwd 文件（用户名无关紧要，我们只是不想在容器中以 root 身份运行任何文件）。 不会有 `sh`，`ps` 或攻击者可以利用的任何其他文件。 当然，如果您需要其他文件来运行应用程序，则需要包含这些文件或在运行时将其挂载。
