- 原文地址：https://tip.golang.org/doc/go1.18
- 原文作者：**golang.org**
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w11_Go_1_18_Release_Notes_Draft.md
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：

# Go 1.18 发布说明

## 拟定发布 - Go 1.18介绍

**Go 1.18还没有发布。这些是正在进行中的发布说明。Go 1.18预计将于2022年2月发布。**

## Go语言的变化

### 泛型

Go 1.18包含一个在[类型参数提案](https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md)中描述的泛型特性的实现，这包括对语言的重大--但完全向后兼容的--改变。

这些新的变化需要编写大量新的代码，然而这些代码还没有在生产环境中进行过大量的测试。这只会在当越来越多人编写和使用泛型的时候才会发生。我们相信这些新特性的实现是优雅的，并且是高质量的。然而，与Go大多数方面不同的是，我们无法用现实世界的经验来支持这种信念。因此，虽然我们鼓励在某些需要使用的泛型的场景下使用泛型，但当部署泛型代码到生产环境时，请多谨慎一些。

以下是最明显的变化列表。关于更全面的概述，请看[提案](https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md)。详情见[语言规范](https://tip.golang.org/ref/spec)。

- [函数](https://tip.golang.org/ref/spec#Function_declarations)和[类型宣告](https://tip.golang.org/ref/spec#Type_declarations)的语法，现在接受[类型参数](https://tip.golang.org/ref/spec#Type_parameters)。
- 参数化的函数和类型可以通过在它们后面加上类型参数列表来进行实例化，类型参数列表放在方括号中。
- 添加了新的标识 `~` 到[运算符和标点符号](https://tip.golang.org/ref/spec#Operators_and_punctuation)。
- [接口类型](https://tip.golang.org/ref/spec#Interface_types)的语法现在已经支持嵌套任意类型(不只是接口的类型名称)，以及union和 `~T` 类型元素。这样的接口只能作为类型约束使用。现在一个接口定义了一组类型以及一组方法。
- 新的[提前宣告标识符(prdeclared identifyer)](https://tip.golang.org/ref/spec#Predeclared_identifiers) `any` 作为空接口的别名。这将取代原有的 `interface{}`
- 新的[提前宣告标识符(prdeclared identifyer)](https://tip.golang.org/ref/spec#Predeclared_identifiers) `comparable` 是一个接口表示所有可以通过`==`或者`!=`来比较的类型的集合。它只能用于(或者嵌套)一个类型约束。

有三个使用泛型实现的实验性质的包可能会有用。这些包在 x/exp仓库；它们的API不在Go的保证范围内，而且随着我们对泛型经验的增加，可能会发生变化。

- [`goland.org/x/exp/constraints`](https://pkg.go.dev/golang.org/x/exp/constraints)

  对泛型代码有用的约束，例如[constraints.Ordered](https://pkg.go.dev/golang.org/x/exp/constraints#Ordered)

- [`golang.org/x/exp/slices`](https://pkg.go.dev/golang.org/x/exp/slices)

  一个泛型函数的集合，可以对任何元素类型的切片进行操作。

- [`golang.org/x/exp/maps`](https://pkg.go.dev/golang.org/x/exp/maps)

  一个泛型函数的集合，可以对任何键或元素类型的map进行操作。

现在泛型的实现还有如下的限制：

- Go编译器目前不能处理泛型函数或者方法内的类型声明。我们希望在Go 1.19提供这个特性。
- Go编译器目前在预先声明函数的参数类型上不支持`real`、`imag`和`complex`类型。我们希望在Go 1.19移除这个限制。
- 如果`m`是由`P`的约束接口明确声明的，那Go编译器目前只支持在参数类型为`P`的值`x`上调用方法`m`。同样的，只在`m`是由`P`的约束接口明确声明的，才支持方法值`x.m`和方法表达式`P.m`， 即使由于`P`中的所有类型都实现了`m`，导致`m`在`P`的方法集中也不能支持上述的使用方式。我们希望在Go 1.19移除这个限制。
- 不允许将类型参数或指向类型参数的指针作为结构类型中的未命名字段嵌入。同样的，不允许将类型参数嵌入到一个接口类型。这个是否会被允许，目前还是未知的。
- 有一个以上元素的集合元素不能包含一个具有非空方法集的接口类型。这个是否会被允许，目前还是未知的。


### Bug修复

Go 1.18 编译器现在可以正确报告在函数字面中设置，但从未使用的变量的声明错误。在Go 1.18之前，编译器在这种情况下不会报告错误。这修复了长期存在的编译器问题。由于这一变化，（可能是不正确的）程序可能不再被编译。可以直接这么修改：如果程序实际上是不正确的，就修复它，或者使用了违规的变量，例如把它赋值给空白标识符`_`。由于`go vet`总是指出这个错误，受影响的程序数量可能非常少。

当将一个符文常量表达式，例如`'1' << 32`，作为一个参数传递给预先声明函数`print`和`pintln` 时，Go 1.18编译器会报告溢出，与用户定义的函数的行为一致。在Go 1.18之前，编译器对此情况不是报错误，而是如果它符合`int64`的要求，就会接收它。由于这一变化，（可能是不正确的）程序可能不再被编译。可以直接这么修改：如果程序实际上是不正确的，就修复它，或者使用了违规的变量，例如把它赋值给空白标识符`_`。由于`go vet`总是指出这个错误，受影响的程序数量可能非常少。

	
## Ports

### AMD64

Go 1.18介绍了新的环境变量`GOAMD64`，它在编译时选择了AMD64架构的最小目标版本。允许的值是`v1`，`v2`，`v3`，或者`v4`。每一个更高的级别都需要并利用额外的处理器功能。详细的描述可以在[这里](https://golang.org/wiki/MinimumRequirements#amd64)找到。

`GOAMD64`环境变量默认是`v1`。

### RISC-V

Linux 上的RISC-V 64位架构 (the `linux/riscv64` port) 现在支持`c-archive`和`c-shared`构建模式。

### Linux

Go 1.18需要Linux内核版本2.6.32或更高版本。

### Windows

 `windows/arm` and `windows/arm64` ports现在支持非合作式抢占，从而使所有四个 Windows ports都具备了这种能力，这有望解决在调用 Win32 函数时遇到的长时间阻塞的微妙错误。

### iOS

在iOS（ios/arm64 port）和基于AMD64的macOS（ios/amd64 port）上运行的iOS模拟器上，Go 1.18现在需要iOS 12或更高版本；对以前版本的支持已经停止了。

### FreeBSD

Go 1.18是在FreeBSD 11.x上支持的最后一个版本，FreeBSD 11.x已经到了生命末期。Go 1.19 将需要 FreeBSD 12.2+ 或 FreeBSD 13.0+。FreeBSD 13.0+ 需要一个设置了 COMPAT_FREEBSD12 选项的内核（这是默认的）。

## 工具

### Fuzzing

Go 1.18包含了[the fuzzing提案](https://golang.org/issue/44551)描述的fuzzing的实现。

详见[fuzzing landing page](https://go.dev/doc/fuzz)开始使用。

请注意的是fuzzing会消耗大量的内存，并且在运行时有可能会影响你机器的性能。还要注意的是，fuzzing引擎在运行时，会将扩大测试范围的数值写入`$GOCACHE/fuzz`内的fuzzing缓存目录，目前没有限制写入fuzzing缓存的文件数量或者写入的字节总数，所以它可能会占用大量的存储(有可能几个GBs)。

### Go指令

#### `go` `get`

`go` `get`不再在模块感知模式下构建或安装软件包。`go` `get`现在用来调整`go.mod`里的依赖。实际上，标志`-d`会被一直启用。要在当前模块的上下文之外安装一个可执行文件的最新版本，使用[go_install_example.com/cmd@latest](https://golang.org/ref/mod#go-install)，可以使用任何[版本的查询](https://golang.org/ref/mod#version-queries)来代替`latest`。在Go 1.16添加了这种形式的`go` `install`，所以支持旧版本的项目，可能需要提供`go` `install`和`go` `get`这两个安装指令说明。但在一个模块外使用的时候，`go` `get`现在会报告一个错误，因为那里没有`go.mod`文件来更新。在GOPATH模式下(`GO111MODULE=off`)，`go` `get`依旧会和之前一样构建和安装包。

#### `go.mod`和`go.sum`自动更新

 `go` `mod` `graph`, `go` `mod` `vendor`, `go` `mod` `verify`, 和 `go` `mod` `why` 子命令将不会自动更新`go.mod`和`go.sum`文件。(这些文件可以使用`go` `get`，`go` `mod` `tidy`，或者`go` `mod` `download`更新。)

#### `go` `version`

`go`命令现在可以在二进制文件中嵌入版本控制信息。 它包括当前签出的修订版，提交时间，以及表明是否存在已编辑或未跟踪的文件的标志。如果go命令是在Git、Mercurial、Fossil或Bazaar仓库中的一个目录中调用的，并且main包和其包含的main模块在同一个仓库中，那么版本控制信息就会被嵌入。这个信息可以通过标志`-buildvcs=false`省略。

此外，`go`命令还嵌入了关于构建的信息，包括构建和工具标签（用-tags设置），编译器、汇编器和链接器的标志（如-gcflags），cgo是否被启用，如果被启用，cgo环境变量的值（如CGO_CFLAGS）。 VCS和构建信息都可以使用`go` `version` `-m`文件或`runtime/debug.ReadBuildInfo`（针对当前运行的二进制文件）或新的[`debug/buildinfo`](https://tip.golang.org/doc/go1.18#debug/buildinfo)包与模块信息一起读取。

嵌入的构建信息的底层数据格式可能会随着新的go版本的发布而改变，所以旧版本的`go`可能无法处理用新版本的`go`产生的构建信息。要从用`go` 1.18构建的二进制文件中读取版本信息，请使用`go` `version`命令和`go` 1.18以上版本的`debug/buildinfo`包。

#### `go` `mod` `download`

如果主模块的`go.mod`文件指定了[`go`_`1.17`](https://tip.golang.org/ref/mod#go-mod-file-go)或更高版本，`go` `mod` `download`执行时不带参数，现在只下载主模块`go.mod`文件中明确要求的模块的源代码。(在go 1.17或更高版本的模块中，这个集合已经包括了构建主模块中的包和测试所需的所有依赖项)。要想同时下载跨平台依赖的源代码，请使用`go` `mod` `download` `all`。

#### `go` `mod` `vendor`

`go` `mod` `vendor` 子命令现在支持一个 `-o` 标志来设置输出目录。(当使用 `-mod=vendor` 加载软件包时，其他 `go` 命令仍然从模块根部的` vendor` 目录中读取，所以这个标志的主要用途是用于需要收集软件包源代码的第三方工具。)

#### `go` `mod` `tidy`

`go` `mod` `tidy` 命令现在在 `go.sum` 文件中为那些需要源代码的模块保留了额外的校验和，以验证每个导入的软件包在[构建列表](https://tip.golang.org/ref/mod#glos-build-list)中只由一个模块提供。因为这种情况比较少见，而且不应用它就会导致构建错误，所以这种改变*不*以主模块的`go.mod`文件中的`go`版本为条件。

#### `go` `work`

`go`命令现在支持 "工作区 "模式。如果在工作目录或父目录中发现`go.work`文件，或者用`GOWORK`环境变量指定了一个，它将使`go`命令进入工作区模式。在工作区模式下，`go.work`文件将被用来确定作为模块解析根基的一组主模块，而不是使用通常找到的`go.mod`文件来指定单一的主模块。更多信息请见[go work](https://tip.golang.org/pkg/cmd/go#hdr-Workspace_maintenance)文件。

#### `go` `build` `-asan`

`go` `build`命令和相关命令现在支持一个`-asan`标志，它能够与用内存错误检测工具（C编译器选项`-fsanitize=address·）编译的C（或C++）代码进行互操作。

#### `go` `test`

`go`命令现在支持额外的命令行选项，用于[上述新的fuzzing支持](#fuzzing)。

- `go test`支持`-fuzz`、`-fuzztime`和`-fuzzminimizetime`选项。关于这些的文档，请看[`go help testflag`](https://tip.golang.org/pkg/cmd/go#hdr-Testing_flags)。
- `go clean`支持一个`-fuzzcache`选项。文档见[`go help testflag`](https://tip.golang.org/pkg/cmd/go#hdr-Testing_flags)。


#### `//go:build` lines

Go 1.17引入了`//go:build`方式，作为一种更易读的方式来写构建约束，而不是`//+build`的方式。从Go 1.17开始，`gofmt`添加`//go:build`行来匹配现有的`+build`行，并保持它们的同步，而`go` `vet`则在它们不同步的时候进行诊断。

由于Go 1.18的发布标志着对Go 1.16支持的结束，所有支持的Go版本现在都能理解`//go:build`的方式。在Go 1.18中，`go` `fix`现在删除了在`go.mod`文件中声明`go` `1.17`或更高版本的模块中现已被淘汰的`//` `+build`行。

更多信息，见https://go.dev/design/draft-gobuild。

### Gofmt

`gofmt`现在可以并发地读取和格式化输入文件，内存限制与`GOMAXPROCS`成正比。在有多个CPU的机器上，`gofmt`现在应该会明显加快。

### Vet

#### 对泛型的更新

`vet`工具被更新以支持泛型代码。在大多数情况下，只要在同等的非泛型代码中用其类型集合中的类型替代类型参数后，它就会报告泛型代码的错误。举个例子，如下`vet`会报告一个格式错误

```go
func Print[T ~int|~string](t T) {
	fmt.Printf("%d", t)
}
```

因为它会在非泛型同等代码`Print[string]`报告一个格式错误

```
func PrintString(x string) {
	fmt.Printf("%d", x)
}
```



#### 现有检查器精准度的提高

`cmd/vet`检查器`copylock`、`printf`、`sortslice`、`testinggoroutine`和`test`都有适度的精度改进，以处理额外的代码模式。这可能会导致现有软件包中出现新的报告错误。例如，`printf`检查器现在跟踪由串联字符串常量创建的格式化字符串。所以`vet`会报告一个错误：

```
  // fmt.Printf formatting directive %d is being passed to Println.
  fmt.Println("%d"+` ≡ x (mod 2)`+"\n", x%2)
```



## Runtime

当确定运行频率时，垃圾收集器现在包括垃圾收集器工作的非栈资源（例如，堆栈扫描）。 因此，当这些资源明显增多的情况下，垃圾收集器的开销就更可预测。对于大多数应用这些改变基本微乎其微；然而，有一些Go应用程序可能使用少量的内存，而花更多的时间在垃圾回收，或者反过来说，比以前更多。打算采取的解决方法是在必要时调整`GOGC`。

现在，runtime更有效地将内存返回给操作系统，并因此而被调整为更积极地执行。

Go 1.17总体上改进了堆栈跟踪中参数的格式，但对于以寄存器传递的参数，可能会打印出不准确的值。在Go 1.18中，这一点得到了改进，在每个可能不准确的数值后面打印一个问号（`?`）

## 编译器

Go 1.17[实现](https://tip.golang.org/doc/go1.17#compiler)了一种新的方法，即在选定的操作系统上的64位x86架构上使用寄存器而不是堆栈来传递函数参数和结果。Go 1.18扩展了支持的平台，包括64位ARM（`GOARCH=arm64`），大、小二进制的64位PowerPC（`GOARCH=ppc64`，`ppc64le`），以及所有操作系统上的64位x86架构（`GOARCH=amd64`）。在64位ARM和64位PowerPC系统上，基准测试显示通常情况下性能改进为10%或以上。

正如Go 1.17发布说明中所[提到的](https://tip.golang.org/doc/go1.17#compiler)，这一变化不影响任何安全的Go代码的功能，并且旨在对大多数汇编代码没有影响。细节详见[Go 1.17发布说明](https://tip.golang.org/doc/go1.17#compiler)。

编译器现在可以内联包含range循环或标记的for循环的函数。

新的`-asan`编译器选项支持新的`go`命令`-asan`选项。

因为编译器的类型检查器被全部替换为支持泛型，所以现在一些错误信息可能使用与以前不同的语法。 在某些情况下，Go 1.18之前的错误信息提供了更多的细节或以更有帮助的方式表述。我们打算在Go 1.19中解决这些情况。

由于编译器中与支持泛型有关的变化，Go 1.18的编译速度可能比Go 1.17的编译速度大约慢15%。编译后的代码的执行时间不受影响。我们打算在Go 1.19中提高编译器的速度。

## 链接器

链接器发出的[重定位次数要少得多](https://tailscale.com/blog/go-linker/)。因此，大多数代码库的链接速度会更快，只需要更少的内存来链接，并产生更小的二进制文件。处理Go二进制文件的工具应该使用Go 1.18的`debug/gosym`包来透明地处理新旧二进制文件。

新的`-asan`链接器选项支持新的`go`命令`-asan`选项。

## Bootstrap

当从源码构建Go发行版且未设置`GOROOT_BOOTSTRAP`时，以前的Go版本会在`$HOME/go1.4`（Windows下为`%HOMEDRIVE%HOMEPATH%\go1.4`）目录下寻找Go 1.4或更高版本的引导工具链。Go现在首先寻找`$HOME/go1.17`或`$HOME/sdk/go1.17`，然后再返回到`$HOME/go1.4`。我们打算在Go 1.19中要求Go 1.17或更高版本的bootstrap，这一改变应该能使过渡更加顺利。详情请见[go.dev/issue/44505](https://go.dev/issue/44505)。

## 核心库

### 新包`debug/buildinfo`

新的[`debug/buildinfo`](https://tip.golang.org/pkg/debug/buildinfo)包提供了对模块版本、版本控制信息以及由`go`命令构建的可执行文件中嵌入的构建标志的访问。同样的信息也可以通过当前运行的二进制文件的[`runtime/debug.ReadBuildInfo`](https://tip.golang.org/pkg/runtime/debug#ReadBuildInfo)和命令行的`go` `version` `-m`获得。

### 新包`net/netip`

新包[`net/netip`](https://tip.golang.org/pkg/net/netip/)定义了新的IP地址类型，[Addr](https://tip.golang.org/pkg/net/netip/#Addr)。与现有的[net.IP](https://tip.golang.org/pkg/net/#IP)类型相比，`netip.Addr`类型占用更少的内存，是不可改变的，并且具有可比性，所以它支持`==`，可以作为一个map的key使用。

除了`Addr`，软件包还定义了[AddrPort](https://tip.golang.org/pkg/net/netip/#AddrPort)，代表一个IP和端口，以及[Prefix](https://tip.golang.org/pkg/net/netip/#Prefix)，代表一个网络CIDR前缀。

包也定义了几个方法来创建和校验这些新的类型： [`AddrFrom4`](https://tip.golang.org/pkg/net/netip#AddrFrom4), [`AddrFrom16`](https://tip.golang.org/pkg/net/netip#AddrFrom16), [`AddrFromSlice`](https://tip.golang.org/pkg/net/netip#AddrFromSlice), [`AddrPortFrom`](https://tip.golang.org/pkg/net/netip#AddrPortFrom), [`IPv4Unspecified`](https://tip.golang.org/pkg/net/netip#IPv4Unspecified), [`IPv6LinkLocalAllNodes`](https://tip.golang.org/pkg/net/netip#IPv6LinkLocalAllNodes), [`IPv6Unspecified`](https://tip.golang.org/pkg/net/netip#IPv6Unspecified), [`MustParseAddr`](https://tip.golang.org/pkg/net/netip#MustParseAddr), [`MustParseAddrPort`](https://tip.golang.org/pkg/net/netip#MustParseAddrPort), [`MustParsePrefix`](https://tip.golang.org/pkg/net/netip#MustParsePrefix), [`ParseAddr`](https://tip.golang.org/pkg/net/netip#ParseAddr), [`ParseAddrPort`](https://tip.golang.org/pkg/net/netip#ParseAddrPort), [`ParsePrefix`](https://tip.golang.org/pkg/net/netip#ParsePrefix), [`PrefixFrom`](https://tip.golang.org/pkg/net/netip#PrefixFrom)。

[`net`](https://tip.golang.org/pkg/net/)包包括与现有方法并行的新方法，但返回`netip.AddrPort`而不是更重的 [`net.IP`](https://tip.golang.org/pkg/net/#IP) 或 [`*net.UDPAddr`](https://tip.golang.org/pkg/net/#UDPAddr) 类型： [`Resolver.LookupNetIP`](https://tip.golang.org/pkg/net/#Resolver.LookupNetIP), [`UDPConn.ReadFromUDPAddrPort`](https://tip.golang.org/pkg/net/#UDPConn.ReadFromUDPAddrPort), [`UDPConn.ReadMsgUDPAddrPort`](https://tip.golang.org/pkg/net/#UDPConn.ReadMsgUDPAddrPort), [`UDPConn.WriteToUDPAddrPort`](https://tip.golang.org/pkg/net/#UDPConn.WriteToUDPAddrPort), [`UDPConn.WriteMsgUDPAddrPort`](https://tip.golang.org/pkg/net/#UDPConn.WriteMsgUDPAddrPort)。 新的`UDPConn`方法支持免分配的I/O。

`net`包现在还包括在现有的 [`TCPAddr`](https://tip.golang.org/pkg/net/#TCPAddr)/[`UDPAddr`](https://tip.golang.org/pkg/net/#UDPAddr) 类型和`netip.AddrPort`之间转换的函数和方法: [`TCPAddrFromAddrPort`](https://tip.golang.org/pkg/net/#TCPAddrFromAddrPort), [`UDPAddrFromAddrPort`](https://tip.golang.org/pkg/net/#UDPAddrFromAddrPort), [`TCPAddr.AddrPort`](https://tip.golang.org/pkg/net/#TCPAddr.AddrPort), [`UDPAddr.AddrPort`](https://tip.golang.org/pkg/net/#UDPAddr.AddrPort)。

### TLS 1.0和1.1默认在客户端禁用

如果没有设置[`Config.MinVersion`](https://tip.golang.org/pkg/crypto/tls/#Config.MinVersion)，它现在默认客户端连接为TLS 1.2。任何安全的最新服务器都应该支持TLS 1.2，而且浏览器自2020年以来就要求它。通过将`Config.MinVersion`设置为`VersionTLS10`，将仍然支持TLS 1.0和1.1。服务器端的默认值不变，为TLS1.0。

通过设置`GODEBUG=tls10default=1`环境变量，可以暂时将默认值恢复为TLS 1.0。这个选项将在 Go 1.19 中被删除。

### 拒绝SHA-1证书

`crypto/x509`现在将拒绝使用 SHA-1 哈希函数签名的证书。这并不适用于自签的根证书。[自2017年以来](https://shattered.io/)，针对SHA-1的实际攻击已经被证明，自2015年以来，公开信任的证书颁发机构已经不再颁发SHA-1证书。

这可以通过设置`GODEBUG=x509sha1=1`环境变量暂时恢复。这个选项将在Go 1.19中被删除。

### 对库的微小改动

和往常一样，在考虑到Go 1的[兼容性承诺](https://tip.golang.org/doc/go1compat)的前提下，对库进行了各种小的修改和更新。

- [bufio](https://tip.golang.org/pkg/bufio/)

  新的[`Writer.AvailableBuffer`](https://tip.golang.org/pkg/bufio#Writer.AvailableBuffer) 方法返回一个空的缓冲区，其容量可能不是空的，以便与类似append的API使用。在追加之后，缓冲区可以提供给后续的`Write`调用，并可能避免任何复制。 [`Reader.Reset`](https://tip.golang.org/pkg/bufio#Reader.Reset) 和 [`Writer.Reset`](https://tip.golang.org/pkg/bufio#Writer.Reset) 方法在对`nil`缓冲区对象调用时，现在使用默认的缓冲区大小。

- [bytes](https://tip.golang.org/pkg/bytes/)

  新的 [`Cut`](https://tip.golang.org/pkg/bytes/#Cut)函数将分隔符周围的`[]byte`切成片。它可以取代并简化 [`Index`](https://tip.golang.org/pkg/bytes/#Index), [`IndexByte`](https://tip.golang.org/pkg/bytes/#IndexByte), [`IndexRune`](https://tip.golang.org/pkg/bytes/#IndexRune), 和[`SplitN`](https://tip.golang.org/pkg/bytes/#SplitN).[`Trim`](https://tip.golang.org/pkg/bytes/#Trim), [`TrimLeft`](https://tip.golang.org/pkg/bytes/#TrimLeft), and [`TrimRight`](https://tip.golang.org/pkg/bytes/#TrimRight) 的许多常见用途，而且现在不需要分配，特别是对于小的ASCII切割集，速度可以提高10倍。[`Title`](https://tip.golang.org/pkg/bytes/#Title)函数现在已经废弃。它不处理Unicode标点符号和特定语言的大小写规则，并被[golang.org/x/text/cases](https://golang.org/x/text/cases) 包所取代。

- [crypto/elliptic](https://tip.golang.org/pkg/crypto/elliptic/)

  [`P224`](https://tip.golang.org/pkg/crypto/elliptic#P224), [`P384`](https://tip.golang.org/pkg/crypto/elliptic#P384), 和[`P521`](https://tip.golang.org/pkg/crypto/elliptic#P521) 曲线的实现现在都是由[addchain](https://github.com/mmcloughlin/addchain) 和[fiat-crypto](https://github.com/mit-plv/fiat-crypto) 项目产生的代码支持的，后者是基于正式验证的算术运算模型。他们现在使用更安全的完整公式和内部API。P-224和P-384现在大约快4倍。所有具体的曲线实现现在都是恒定时间的。在无效的曲线点(那些`IsOnCurve`方法返回false，并且[`Unmarshal`](https://tip.golang.org/pkg/crypto/elliptic#Unmarshal)或对有效点进行操作的`Curve`方法从未返回的点。)上操作一直是未定义的行为，可能导致密钥恢复攻击，现在新的后端不支持。如果一个无效的点被提供给`P224`、`P384`或`P521`方法，该方法现在将返回一个随机点。在未来发布的版本中，这种行为可能会改变为确定的panic。

- [crypto/tls](https://tip.golang.org/pkg/crypto/tls/)

  新的 [`Conn.NetConn`](https://tip.golang.org/pkg/crypto/tls/#Conn.NetConn) 方法允许访问底层的 [`net.Conn`](https://tip.golang.org/pkg/net#Conn).

- [crypto/x509](https://tip.golang.org/pkg/crypto/x509)

  [`Certificate.Verify`](https://tip.golang.org/pkg/crypto/x509/#Certificate.Verify) 现在使用平台API来验证macOS和iOS上的证书有效性，当它被一个nil的 [`VerifyOpts.Roots`](https://tip.golang.org/pkg/crypto/x509/#VerifyOpts.Roots)调用或者使用一个从[`SystemCertPool`](https://tip.golang.org/pkg/crypto/x509/#SystemCertPool)返回的root池的时候。[`SystemCertPool`](https://tip.golang.org/pkg/crypto/x509/#SystemCertPool)现在在Windows上可用。在Windows、macOS和iOS上，当 [`SystemCertPool`](https://tip.golang.org/pkg/crypto/x509/#SystemCertPool) 返回的[`CertPool`](https://tip.golang.org/pkg/crypto/x509/#CertPool)中添加了额外的证书时，[`Certificate.Verify`](https://tip.golang.org/pkg/crypto/x509/#Certificate.Verify) 将进行两次验证： 一个是使用平台验证器API和系统root，一个是使用Go验证器和附加root。由平台验证器API返回的链将被优先处理。[`CertPool.Subjects`](https://tip.golang.org/pkg/crypto/x509/#CertPool.Subjects)已经废弃了。在 Windows、macOS 和 iOS 上，由 [`SystemCertPool`](https://tip.golang.org/pkg/crypto/x509/#SystemCertPool)返回的 [`CertPool`](https://tip.golang.org/pkg/crypto/x509/#CertPool) 将返回一个池，其中不包括 `Subjects` 返回的切片中的系统root，因为静态列表不能适当地代表平台策略，而且可能根本无法从平台 APIs 中获得。

- [debug/dwarf](https://tip.golang.org/pkg/debug/dwarf/)

  [`StructField`](https://tip.golang.org/pkg/debug/dwarf#StructField) 和 [`BasicType`](https://tip.golang.org/pkg/debug/dwarf#BasicType) 结构现在都有字段`DataBitOffset`，如果`DW_AT_data_bit_offset`有值的话，它持有`DW_AT_data_bit_offset`属性的值。
  
- [debug/elf](https://tip.golang.org/pkg/debug/elf/)

  现已添加常量[`R_PPC64_RELATIVE`](https://tip.golang.org/pkg/debug/elf/#R_PPC64_RELATIVE) 。

- [debug/plan9obj](https://tip.golang.org/pkg/debug/plan9obj/)

  如果文件没有符号部分， [File.Symbols](https://tip.golang.org/pkg/debug/plan9obj#File.Symbols)方法现在会返回新的输出错误值[ErrNoSymbols](https://tip.golang.org/pkg/debug/plan9obj#ErrNoSymbols)。

- [go/ast](https://tip.golang.org/pkg/go/ast/)

  根据提案，对[go/ast和go/token进行了补充，以支持参数化的函数和类型](https://go.googlesource.com/proposal/+/master/design/47781-parameterized-go-ast.md)，以下是对 [`go/ast`](https://tip.golang.org/pkg/go/ast) 包的补充： [`FuncType`](https://tip.golang.org/pkg/go/ast/#FuncType) 和[`TypeSpec`](https://tip.golang.org/pkg/go/ast/#TypeSpec) 节点有一个新的字段`TypeParams`来保存类型参数，如果有的话。新的表达式节点[`IndexListExpr`](https://tip.golang.org/pkg/go/ast/#IndexListExpr)代表了多个索引的索引表达式，用于实例一个以上显式类型参数的函数和类型。

- [go/constant](https://tip.golang.org/pkg/go/constant/)

  新的[`Kind.String`](https://tip.golang.org/pkg/go/constant/#Kind.String) 方法为接收者类型返回一个可读的名称。

- [go/token](https://tip.golang.org/pkg/go/token/)

  新的常量 [`TILDE`](https://tip.golang.org/pkg/go/token/#TILDE) 代表了提案，[go/ast和go/token进行了补充，以支持参数化的函数和类型](https://go.googlesource.com/proposal/+/master/design/47781-parameterized-go-ast.md)，中的`~`的标记。

- [go/types](https://tip.golang.org/pkg/go/types/)

  新的 [`Config.GoVersion`](https://tip.golang.org/pkg/go/types/#Config.GoVersion)字段集合接收Go语言版本。根据提案，对[go/ast和go/token进行了补充，以支持参数化的函数和类型](https://go.googlesource.com/proposal/+/master/design/47781-parameterized-go-ast.md)，以下是对 [`go/types`](https://tip.golang.org/pkg/go/types)包的补充：增加了新的[`TypeParam`](https://tip.golang.org/pkg/go/types/#TypeParam)类型、工厂函数 [`NewTypeParam`](https://tip.golang.org/pkg/go/types/#NewTypeParam)和相关方法来表示一个类型参数。新类型 [`TypeParamList`](https://tip.golang.org/pkg/go/types/#TypeParamList) 持有一个类型参数的列表。新类型[`TypeList`](https://tip.golang.org/pkg/go/types/#TypeList)持有一个类型的列表。新的工厂函数 [`NewSignatureType`](https://tip.golang.org/pkg/go/types/#NewSignatureType)分配了一个带有（接收器或函数）类型参数的 [`Signature`](https://tip.golang.org/pkg/go/types/#Signature)。为了访问这些类型参数，`Signature`类型有两个新方法[`Signature.RecvTypeParams`](https://tip.golang.org/pkg/go/types/#Signature.RecvTypeParams) 和[`Signature.TypeParams`](https://tip.golang.org/pkg/go/types/#Signature.TypeParams)。[`Named`](https://tip.golang.org/pkg/go/types/#Named)  类型有四个新方法：[`Named.Origin`](https://tip.golang.org/pkg/go/types/#Named.Origin)用于获取实例化类型的原始参数化类型， [`Named.TypeArgs`](https://tip.golang.org/pkg/go/types/#Named.TypeArgs) 和 [`Named.TypeParams`](https://tip.golang.org/pkg/go/types/#Named.TypeParams) 用于获取实例化或参数化类型的类型参数， [`Named.SetTypeParams`](https://tip.golang.org/pkg/go/types/#Named.TypeParams)用于设置类型参数(例如，当导入一个命名的类型时，由于可能的循环，命名类型的分配和类型参数的设置不能同时进行)。接口类型有四个新方法：[`Interface.IsComparable`](https://tip.golang.org/pkg/go/types/#Interface.IsComparable) 和 [`Interface.IsMethodSet`](https://tip.golang.org/pkg/go/types/#Interface.IsMethodSet) 用于查询接口定义的类型集的属性， [`Interface.MarkImplicit`](https://tip.golang.org/pkg/go/types/#Interface.MarkImplicit) 和[`Interface.IsImplicit`](https://tip.golang.org/pkg/go/types/#Interface.IsImplicit) 用于设置和测试接口是否是围绕类型约束的隐式接口。新的类型 [`Union`](https://tip.golang.org/pkg/go/types/#Union) 和 [`Term`](https://tip.golang.org/pkg/go/types/#Term)，工厂函数[`NewUnion`](https://tip.golang.org/pkg/go/types/#NewUnion) 和[`NewTerm`](https://tip.golang.org/pkg/go/types/#NewTerm)，以及相关的方法被添加到接口中来表示类型集合。新函数 [`Instantiate`](https://tip.golang.org/pkg/go/types/#Instantiate) 实例化了一个参数化的类型。新的 [`Info.Instances`](https://tip.golang.org/pkg/go/types/#Info.Instances)  map通过新的[`Instance`](https://tip.golang.org/pkg/go/types/#Instance)类型记录函数和类型的实例化。增加了新的[`ArgumentError`](https://tip.golang.org/pkg/go/types/#ArgumentError)类型和相关方法来表示与类型参数有关的错误。增加了新的类型 [`Context`](https://tip.golang.org/pkg/go/types/#Context) 和工厂函数 [`NewContext`](https://tip.golang.org/pkg/go/types/#NewContext) ，以便通过新的[`Config.Context`](https://tip.golang.org/pkg/go/types/#Config.Context) 字段，在类型检查的包之间共享相同的类型实例。[`AssignableTo`](https://tip.golang.org/pkg/go/types/#AssignableTo), [`ConvertibleTo`](https://tip.golang.org/pkg/go/types/#ConvertibleTo), [`Implements`](https://tip.golang.org/pkg/go/types/#Implements), [`Identical`](https://tip.golang.org/pkg/go/types/#Identical), [`IdenticalIgnoreTags`](https://tip.golang.org/pkg/go/types/#IdenticalIgnoreTags), 和[`AssertableTo`](https://tip.golang.org/pkg/go/types/#AssertableTo) 现在也可以处理属于或包含泛型接口的参数，即接口在Go代码中只能作为类型约束所使用。 注意，如果第一个参数是一个泛型的接口，那么`AssertableTo`的行为是未定义的。

- [html/template](https://tip.golang.org/pkg/html/template/)

  在一个`range`管道内，新的`{{break}}`命令将提前结束循环，新的`{{continue}}`命令将立即开始下一个循环迭代。`and`函数不再对所有参数进行评估；它在第一个参数评估为false后就停止评估参数。同样，`or`函数现在在第一个参数评估为 true 后就停止评估参数。如果任何一个参数是一个函数调用，这就有区别了。

- [image/draw](https://tip.golang.org/pkg/image/draw/)

  当这些参数实现了 Go 1.17 中添加了可选的[`draw.RGBA64Image`](https://tip.golang.org/pkg/image/draw/#RGBA64Image) 和[`image.RGBA64Image`](https://tip.golang.org/pkg/image/#RGBA64Image) 接口时，`Draw` 和 `DrawMask` 的回退实现比（当参数不是最常见的图像类型时使用）现在更快。	

- [net](https://tip.golang.org/pkg/net/)

  [`net.Error.Temporary`](https://tip.golang.org/pkg/net#Error) 已经废弃。

- [net/http](https://tip.golang.org/pkg/net/http/)

  在WebAssembly目标上，[`Transport`](https://tip.golang.org/pkg/net/http/#Transport) 中的 `Dial`, `DialContext`, `DialTLS` 和 `DialTLSContext` 方法字段现在将被正确使用，如果要明确的话，就是用于创建HTTP请求。新的[`Cookie.Valid`](https://tip.golang.org/pkg/net/http#Cookie.Valid) 方法报告cookie是否有效。新的 [`MaxBytesHandler`](https://tip.golang.org/pkg/net/http#MaxBytesHandler)函数创建了一个`Handler`，用[`MaxBytesReader`](https://tip.golang.org/pkg/net/http#MaxBytesReader)包装它的`ResponseWriter`和`Request.Body`。
  
- [os/user](https://tip.golang.org/pkg/os/user/)

  [`User.GroupIds`](https://tip.golang.org/pkg/os/user#User.GroupIds)现在在cgo不可用时使用Go的原生实现。

- [reflect](https://tip.golang.org/pkg/reflect/)

  新的 [`Value.SetIterKey`](https://tip.golang.org/pkg/reflect/#Value.SetIterKey) 和[`Value.SetIterValue`](https://tip.golang.org/pkg/reflect/#Value.SetIterValue) 方法使用map迭代器作为源来设置一个Value。它们等同于`Value.Set(iter.Key())`和`Value.Set(iter.Value())`，但内存分配得更少。新的 [`Value.UnsafePointer`](https://tip.golang.org/pkg/reflect/#Value.UnsafePointer) 方法将Value的值作为一个[`unsafe.Pointer`](https://tip.golang.org/pkg/unsafe/#Pointer)返回。这允许调用者从 [`Value.UnsafeAddr`](https://tip.golang.org/pkg/reflect/#Value.UnsafeAddr) 和[`Value.Pointer`](https://tip.golang.org/pkg/reflect/#Value.Pointer) 迁移，以消除在调用的地方需要执行uintptr到unsafe.Pointer的转换（因为unsafe.Pointer规则要求）。新的[`MapIter.Reset`](https://tip.golang.org/pkg/reflect/#MapIter.Reset)方法改变了它的接收器，在一个不同的map上进行迭代。 使用[`MapIter.Reset`](https://tip.golang.org/pkg/reflect/#MapIter.Reset) 可以在多个map上进行无内存分配的迭代。一些方法（ [`Value.CanInt`](https://tip.golang.org/pkg/reflect#Value.CanInt), [`Value.CanUint`](https://tip.golang.org/pkg/reflect#Value.CanUint), [`Value.CanFloat`](https://tip.golang.org/pkg/reflect#Value.CanFloat), [`Value.CanComplex`](https://tip.golang.org/pkg/reflect#Value.CanComplex) ）已经被添加到[`Value`](https://tip.golang.org/pkg/reflect#Value)中，以测试转换是否安全。为了避免在[`Value.FieldByIndex`](https://tip.golang.org/pkg/reflect#Value.FieldByIndex)中通过一个指向嵌入式结构的空指针步进时发生的panic，添加了[`Value.FieldByIndexErr`](https://tip.golang.org/pkg/reflect#Value.FieldByIndexErr)。[`reflect.Ptr`](https://tip.golang.org/pkg/reflect#Ptr) 和[`reflect.PtrTo`](https://tip.golang.org/pkg/reflect#PtrTo) 已经分别更名为 [`reflect.Pointer`](https://tip.golang.org/pkg/reflect#Pointer) 和[`reflect.PointerTo`](https://tip.golang.org/pkg/reflect#PointerTo)，以便与 reflect 包的其他部分保持一致。旧的名字将继续工作，但在未来的Go版本中会被废弃。

- [regexp](https://tip.golang.org/pkg/regexp/)

  [regexp](https://tip.golang.org/pkg/regexp/)现在将UTF-8字符串的每个无效字节视为`U+FFFD`。

- [runtime/debug](https://tip.golang.org/pkg/runtime/debug/)

  [`BuildInfo`](https://tip.golang.org/pkg/runtime/debug#BuildInfo)结构有两个新字段，包含关于二进制文件如何构建的额外信息：[`GoVersion`](https://tip.golang.org/pkg/runtime/debug#BuildInfo.GoVersion)持有用于构建二进制文件的Go版本。.[`Settings`](https://tip.golang.org/pkg/runtime/debug#BuildInfo.Settings)是[`BuildSettings`](https://tip.golang.org/pkg/runtime/debug#BuildSettings)结构的一个切片，持有描述构建的键/值对。

- [runtime/pprof](https://tip.golang.org/pkg/runtime/pprof/)

  CPU剖析器现在在Linux上的每个线程使用定时器。这增加了剖析器可以观察到的最大CPU使用率，并减少了某些形式的偏差。

- [strconv](https://tip.golang.org/pkg/strconv/)

  [`strconv.Unquote`](https://tip.golang.org/pkg/strconv/#strconv.Unquote)现在拒绝接受Unicode surrogate halves。

- [strings](https://tip.golang.org/pkg/strings/)

  新的 [`Cut`](https://tip.golang.org/pkg/bytes/#Cut)函数将分隔符周围的`string`切成片。它可以取代并简化 [`Index`](https://tip.golang.org/pkg/bytes/#Index), [`IndexByte`](https://tip.golang.org/pkg/bytes/#IndexByte), [`IndexRune`](https://tip.golang.org/pkg/bytes/#IndexRune), 和[`SplitN`](https://tip.golang.org/pkg/bytes/#SplitN).新的[`Clone`](https://tip.golang.org/pkg/strings/#Clone)函数复制了输入字符串，返回的克隆字符串没有引用输入字符串的内存。[`Trim`](https://tip.golang.org/pkg/bytes/#Trim), [`TrimLeft`](https://tip.golang.org/pkg/bytes/#TrimLeft), and [`TrimRight`](https://tip.golang.org/pkg/bytes/#TrimRight) 的许多常见用途，而且现在不需要分配，特别是对于小的ASCII切割集，速度可以提高10倍。[`Title`](https://tip.golang.org/pkg/bytes/#Title)函数现在已经废弃。它不处理Unicode标点符号和特定语言的大小写规则，并被[golang.org/x/text/cases](https://golang.org/x/text/cases) 包所取代。

- [sync](https://tip.golang.org/pkg/sync/)

  新的方法[`Mutex.TryLock`](https://tip.golang.org/pkg/sync#Mutex.TryLock), [`RWMutex.TryLock`](https://tip.golang.org/pkg/sync#RWMutex.TryLock), 和[`RWMutex.TryRLock`](https://tip.golang.org/pkg/sync#RWMutex.TryRLock)，将在当前没有锁的情况下获取锁。

- [syscall](https://tip.golang.org/pkg/syscall/)

  为Windows引入了新的函数 [`SyscallN`](https://tip.golang.org/pkg/syscall/?GOOS=windows#SyscallN)，允许以任意数量的参数进行调用。因此，, [`Syscall`](https://tip.golang.org/pkg/syscall/?GOOS=windows#Syscall), [`Syscall6`](https://tip.golang.org/pkg/syscall/?GOOS=windows#Syscall6), [`Syscall9`](https://tip.golang.org/pkg/syscall/?GOOS=windows#Syscall9), [`Syscall12`](https://tip.golang.org/pkg/syscall/?GOOS=windows#Syscall12), [`Syscall15`](https://tip.golang.org/pkg/syscall/?GOOS=windows#Syscall15), 和 [`Syscall18`](https://tip.golang.org/pkg/syscall/?GOOS=windows#Syscall18) 将会被弃用，而使用 [`SyscallN`](https://tip.golang.org/pkg/syscall/?GOOS=windows#SyscallN)。现在在FreeBSD支持[`SysProcAttr.Pdeathsig`](https://tip.golang.org/pkg/syscall/?GOOS=freebsd#SysProcAttr.Pdeathsig) 。

- [syscall/js](https://tip.golang.org/pkg/syscall/js/)

  `Wrapper`接口现在被移除。

- [testing](https://tip.golang.org/pkg/testing/)

  在`-run`和`-bench`的参数中，`/`的优先级提高了。`A/B|C/D`过去被视为`A/(B|C)/D`，现在被视为`(A/B)|(C/D)`。如果`-run`选项没有选择任何测试，`-count`选项将被忽略。这可能会改变现有测试的行为，在不太可能的情况下，一个测试改变了每次运行测试函数本身时的子测试集。新的[`testing.F`](https://tip.golang.org/pkg/testing#F) 类型被[上述新的fuzzing支持所使用](#fuzzing)。Tests现在也支持命令行参数 `-test.fuzz`, `-test.fuzztime`, 和`-test.fuzzminimizetime`。

- [text/template](https://tip.golang.org/pkg/text/template/)

  在一个`range`管道内，新的`{{break}}`命令将提前结束循环，新的`{{continue}}`命令将立即开始下一个循环迭代。`and`函数不再对所有参数进行评估；它在第一个参数评估为false后就停止评估参数。同样，`or`函数现在在第一个参数评估为 true 后就停止评估参数。如果任何一个参数是一个函数调用，这就有区别了。

- [text/template/parse](https://tip.golang.org/pkg/text/template/parse/)

  该包通过新的常量 [`NodeBreak`](https://tip.golang.org/pkg/text/template/parse#NodeBreak)和新的 [`BreakNode`](https://tip.golang.org/pkg/text/template/parse#BreakNode)类型支持新的[text/template](https://tip.golang.org/pkg/text/template/) 和[html/template](https://tip.golang.org/pkg/html/template/)  `{{break}}`命令，同样也通过新的常量 [`NodeContinue`](https://tip.golang.org/pkg/text/template/parse#NodeContinue)和新的 [`ContinueNode`](https://tip.golang.org/pkg/text/template/parse#ContinueNode)类型支持新的`{{continue}}`命令。

- [unicode/utf8](https://tip.golang.org/pkg/unicode/utf8/)

  新的 [`AppendRune`](https://tip.golang.org/pkg/unicode/utf8/#AppendRune)函数将一个UTF-8编码的`rune`追加到一个`[]byte`上。
