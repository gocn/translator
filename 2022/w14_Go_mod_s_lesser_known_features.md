- 原文地址：https://verdverm.com/go-mods/
- 原文作者：**Dr. Tony Worm**
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w14_Go_mod_s_lesser_known_features.md
- 译者：[Fivezh](https://github.com/fivezh)
- 校对：[](https://github.com/)

# 鲜为人知的Go mod特性

模块(Module)是Go管理依赖关系的方式。模块是一组包的集合，它们被一起发布、版本化和分发。一个模块中的每个包都是同一目录下被一起编译的源文件的集合。

在这篇文章中，我们将探讨Go模块的设计，并学习它们是如何支持供应链安全。你可以在 `https://golang.org/ref/mod` 找到`go mod`的详细文档

说明:

*本文的描述限定于Go 1.17，并不全部适用于旧版本。*

*这篇文章与PackageCon2021上的一次谈话相关联，一旦有了视频后，将会加入进来。*

[此分享的pdf文件下载](../static/image/2022/w14_Go_mod_s_lesser_known_features/PackagingCon2021-GoMods.pdf)

## `go.mod` 文件剖析

```
// go.mod 示例文件
module github.com/org/module         // 当前模块名称

require (                            // 模块依赖说明
  github.com/foo/bar  v0.1.2
  github.com/cow/moo  v1.2.3
  mydomain.com/gopher v0.2.3-beta1
)
```

Go对模块名称是有限制的，我们后文会再讨论。版本是项目的一个特定的、最小的版本。注意，没有版本范围，只有单一的语义版本（Semantic Version）。当Go处理依赖关系树时，它会选择所发现的版本中*最大*的版本。这样一来，最小版本选择`MVS`就可以在没有锁文件的情况下创建一个可重复的依赖关系树。

## 最小版本选择 Minimum Version Selection

Golang使用MVS（最小版本选择）[1](https://research.swtch.com/vgo-mvs) [2](https://golang.org/ref/mod#minimal-version-selection )算法来选择依赖版本。这种确定性的算法对于可复制的构建有很好的特性，并且避免了运行时NP完全的复杂性。因为依赖性选择问题是受限制的，所以不需要SAT求解器。

这里的的核心，*告别一些细节*，MVS是一个广度优先的模块和版本的遍历机制。树是由模块的`go.mod`文件定义的，描述了项目的依赖关系、依赖到依赖的关系等等。

![Minimum Version Selection](../static/images/2022/w14_Go_mod_s_lesser_known_features/mvs-buildlist.svg)

术语`最小`是指这是一个无锁文件、确定性的依赖管理系统的最小实现。

## go.mod中的指令

`go.mod` 有一些列来控制版本依赖的指令：

```
module example.com/my/thing

go 1.16

require example.com/other/thing v1.0.2
require example.com/new/thing/v2 v2.3.4
exclude example.com/old/thing v1.2.3
replace example.com/bad/thing v1.4.5 => example.com/good/thing v1.4.5
retract [v1.9.0, v1.9.5]
```

- `go` - 设置最小的Go语法版本
- `require` - 指定直接的模块依赖关系
- `exclude` - 排除的依赖关系
- `replace` - 替换，而不是重命名
- `retract` - 本模块的次要和补丁版本

`//Deprecated` 可用在模块的主要版本，你可以添加一个评论并标记说明模块的新版本。

```
// Deprecated: use example.com/mod/v2 instead.
module example.com/mod
```

从Go 1.17开始，有两个require指令块，分别是直接和间接依赖，这用来支持懒惰加载。[3](https://golang.org/ref/mod#lazy-loading)

## 环境变量

Go支持一些环境变量，用于控制模块和模块感知命令[4](https://golang.org/ref/mod#mod-commands)的工作方式。下表包含了后面章节中提到的变量。关于完整的列表、更多的细节和例子，请参见。[5](https://golang.org/ref/mod#environment-variables) [6](https://golang.org/ref/mod#private-modules)

可以使用`go env`命令来查看当前环境变量设置

| 变量   | 用途 |
| ---------- | ------------------------------------------------------------ |
| GOMODCACHE | 模块相关文件的目录                           |
| GOPRIVATE  | 将模块中处理为私有的                            |
| GOPROXY    | 模块代理的有序列表                        |
| GONOPROXY  | 直接拉取的模块                               |
| GOSUMDB    | sumdb主机的有序列表                           |
| GONOSUMDB  | 忽略远程sumdb校验的模块                  |
| GOVCS      | 设置允许公共和私人访问的VCS工具         |
| GOINSECURE | 允许降级到http请求 |

## 哈希值和go.sum文件

当go命令下载一个模块时，它会计算出一个加密的哈希值，并将其与已知的值进行比较，以验证该文件自首次下载以来没有变化。模块将这些哈希值存储在`go.sum`文件中，Go命令会验证它们是否匹配。Go也将这些哈希值存储在模式模块缓存中，并将其与全局数据库进行比较。[8](https://golang.org/ref/mod#authenticating)

## 本地模块缓存

Go在你的本地系统上维护一个共享模块缓存。[9](https://golang.org/ref/mod#module-cache) 这是下载的模块存放的地方，其位置由`GOMODCACHE`变量决定。模块代码默认为只读，以防止本地修改和"它在我的机器上是工作"的问题。共享缓存也包含了预先构建的工件。所有这些意味着你的机器上的多个项目可以重复使用相同的下载和预处理的软件包。

## 全局服务模块和哈希值

Go团队维护全局代理的sumdb、cachedb以及全局哈希完整性和撤销检查。[10](https://golang.org/ref/mod#checksum-database)校验数据库可用于检测行为不端的来源和代理服务器。它有一个由`Trillian`项目提供的哈希值树的透明日志。缓存数据库代理公共模块，并将保持副本，即使源服务器删除它们。

Go团队已经认真得对待隐私问题，这些服务记录的信息非常少。你可以阅读[的隐私声明](https://sum.golang.org/privacy)了解详情。他们在GitHub上issues的交流也反映了这一点。例如，只有有限的认证功能被启用，因为他们在试图维护代理中的隐私时非常谨慎。

## 模块命名

Go有许多模块的命名规则。这些规则部分是专门设计的，使用代码托管方而不是包注册，但也是出于安全考虑。

> **要求域名成为模块标识符的第一部分**

域的要求本身是必须的，因为Go将模块解析到代码主机上。它还可以防止一类依赖关系的混乱，在下一节中讨论。

> **只包含ascii字母、数字和有限的标点符号 (`[.~_-]`)**

对允许的导入路径参数的限制可以防止**同音字**攻击。[11](https://blog.malwarebytes.com/101/2017/10/out-of-character-homograph-attacks-explained/) [12](https://www.securityweek.com/zero-day-homograph-domain-name-attack) [13](https://github.com/golang/go/issues/44970)

```sh
$ go mod init ɢoogle.com/chrome
go: malformed module path "ɢoogle.com/chrome": invalid char 'ɢ'
```

> **不能以斜线或点开始或结束**

斜线和点的限制使绝对和相对路径不能成为导入名的一部分。虽然这意味着它们更加冗长，但它也意味着

1. 你总是可以看到正在使用的确切的软件包
2. 相对和绝对路径攻击是不可能的

> **有更多的限制**

对于特定的上下文中，有更多的规则

- 域名部分有进一步的限制
- 避免使用Windows保留的文件名
- 主要版本后缀

访问 [14](https://golang.org/ref/mod#go-mod-file-ident) 获取更多详细。

## 只允许安全的远程访问

Go只与安全的代码托管方通信，更倾向于`https`和`git+ssh`。

你可以使用`GOINSECURE`来列出可以通过`http`和其他不安全协议获取的模块。以不安全方式获取的模块仍将根据校验数据库进行验证。

请查阅VCS计划表[15](https://golang.org/ref/mod#vcs)，了解哪些工具和协议被支持。你可能还需要设置GOVCS [16](https://golang.org/ref/mod#vcs-govcs)。

## 私有模块支持

Go支持私有开发的模块，你可以：

- 通过私有代码仓库拉取模块
- 防止私有模块被公共索引
- 运行私有的代理和校验数据库

有关私人模块部分的细节和必要的配置详见[17](https://golang.org/ref/mod#private-modules)。

为了对私有模块托管方进行认证，Go在直接下载时默认使用如`.gitconfig`的配置工具。对于 `https`的基本安全校验支持通过`.netrc`文件来验证。[18](https://golang.org/ref/mod#private-module-repo-auth)

## 防止依赖的混乱

**依赖混乱** [19](https://medium.com/@alex.birsan/dependency-confusion-4a5d60fec610) 描述了当获取与内部包同名的公共包时，Go 能有效防止这种情况发生

> **需要域来开始模块名和导入路径**

这意味着模块名称不能重叠，例如当恶意行为者在公共库中注册相同模块时。

> **忽略依赖关系中的替换指令**

受损的依赖项不能用替换托管在其他域下的依赖项

## 恶意版本更改

有两种主要的版本攻击方式：使用漏洞替换或添加标签。

> **替换标签**

重新标记实际上是不可能的，因为一个模块已经被任何人拉取过一次。 原始哈希将在全局 sumdb 中缓存，此时验证将会失败。 这当然取决于您的 `GO[NO]SUM`、`GO[NO]PROXY` 和 `GOPRIVATE` 设置。

> **创建新的标签**

在 Go 中，版本是特定的，而不是范围。 此外，Go 只会从列出的版本中进行选择。 按照此设计，Go 不会选择较新的模块，此时不受恶意版本增量的影响而相对安全。

## 没有前置或后置hook

go 模块系统缺少用于获取、构建或安装的任何前置或后置hook。这排除了一类攻击，例如在 `NPM` 中看到的攻击。

## 二进制文件中的信息

Go 将依赖信息添加到二进制文件中。这包括它们的路径、版本和 sumdb 哈希。

```
go version -m $(which binary)
```

在 Go 1.18 中，它还将包括主模块的构建标志、环境设置和 VCS 信息。 [20](https://github.com/golang/go/issues/37475)

## 可重现的构建

Go 的目标是 100% 可重现的工程构建。`MVS` 依赖管理是其中的部分核心，这确保了源代码是相同的。虽然这只是第一步，但即使在交叉编译时 Go 团队也能够实现这一目标。

## 了解更多

- [模块参考](https://golang.org/ref/mod)
- [Go & 版本](https://research.swtch.com/vgo)
- [mod原始提议](https://github.com/golang/go/issues/24301)
- [GitHub Issues](https://github.com/golang/go/issues?q=is%3Aopen+is%3Aissue+label%3Amodules)
