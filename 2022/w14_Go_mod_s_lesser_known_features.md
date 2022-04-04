- 原文地址：https://verdverm.com/go-mods/
- 原文作者：**Dr. Tony Worm**
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w14_Go_mod_s_lesser_known_features.md
- 译者：[Fivezh](https://github.com/fivezh)
- 校对：[](https://github.com/)

# 鲜为人知的Go mod特性

模块(Module)是Go管理依赖关系的方式。模块是一组包的集合，它们被一起发布、版本化和分发。一个模块中的每个包都是同一目录下被一起编译的源文件的集合。

在这篇文章中，我们将探讨Go模块的设计，并学习它们是如何支持供应链安全。你可以在 `https://golang.org/ref/mod` 找到`go mod`的详细文档

### 目录

[Anatomy of a go.mod file](https://verdverm.com/go-mods/#anatomy-of-a-gomod-file)[Minimum Version Selection](https://verdverm.com/go-mods/#minimum-version-selection)[Directives in go.mod](https://verdverm.com/go-mods/#directives-in-gomod)[Environment variables](https://verdverm.com/go-mods/#environment-variables)[Hashes and the go.sum file](https://verdverm.com/go-mods/#hashes-and-the-gosum-file)[Local module cache](https://verdverm.com/go-mods/#local-module-cache)[Global services modules and hashes](https://verdverm.com/go-mods/#global-services-modules-and-hashes)[Module naming](https://verdverm.com/go-mods/#module-naming)[Only Secure Remotes](https://verdverm.com/go-mods/#only-secure-remotes)[Private module support](https://verdverm.com/go-mods/#private-module-support)[Preventing dependency confusion](https://verdverm.com/go-mods/#preventing-dependency-confusion)[Malicious version changes](https://verdverm.com/go-mods/#malicious-version-changes)[No pre or post hooks](https://verdverm.com/go-mods/#no-pre-or-post-hooks)[Information in the binaries](https://verdverm.com/go-mods/#information-in-the-binaries)[Reproducible Builds](https://verdverm.com/go-mods/#reproducible-builds)[Learning more](https://verdverm.com/go-mods/#learning-more)

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

## Hashes and the go.sum file



When the go command downloads a module, it computes a cryptographic hash and compares it with a known value to verify the file hasn’t changed since it was first downloaded. Modules store these hashes in a `go.sum` file and the Go command verifies they match. Go also stores these hashes in mode module cache and will compare them with a global database. [8](https://verdverm.com/go-mods/#fn:8)

## Local module cache



Go maintains a shared module cache on your local system. [9](https://verdverm.com/go-mods/#fn:9) This is where downloaded modules are stored. The location is determined by the `GOMODCACHE` variable. Module code is read-only by default to prevent local modifications and “it works on my machine” issues. The shared cache also contains prebuilt artifacts. All of this means that multiple projects on your machine can reuse the same downloaded and preprocessed packages.

## Global services modules and hashes



The Go team maintain global proxies for sumdb, cachedb, and global hash integrity and revocation checks. [10](https://verdverm.com/go-mods/#fn:10) The checksum database can be used to detect misbehaving origin and proxy servers. It has a merkel tree transparency log for hashes powered by the Trillian project. The cache database proxies public modules and will maintain copies even if the origin server removes them.

The Go team has taken privacy seriously. These services record very minimal information. You can read the [privacy statemnt for sum.golang.org/privacy](https://sum.golang.org/privacy) for details. Their communications in issues on GitHub reflects this. For example, only limited auth features have been enabled, because they are being careful in trying to maintain privacy in proxy.

## Module naming



Go has a number of module naming rules. These are partially by design, in using code hosts rather than package registries, but also for security resaons.

> **Requires a domain name to be the first part of the module identifier**

The domain requirement is itself required because Go resolves modules to the code host. It also prevents a class of dependency confusion, discussed in the next section.

> **Only contain ascii letters, digits, and limited punctuation (`[.~_-]`)**

Restrictions on allowed import path parameters prevents **homograph** or **homoglyph** attacks. [11](https://verdverm.com/go-mods/#fn:11) [12](https://verdverm.com/go-mods/#fn:12) [13](https://verdverm.com/go-mods/#fn:13)

```sh
$ go mod init ɢoogle.com/chrome
go: malformed module path "ɢoogle.com/chrome": invalid char 'ɢ'
```

> **Cannot begin or end with a slash or dot**

Slash and dot restrictions prevent absolute and relative path from being part of imports. While this means they are more verbose, it also means that

1. you can always see the exact package being used
2. relative and absolute path attacks are not possible

> **There are more restrictions**

For specific contexts, there are more rules

- The domain part has further restrictions
- Windows has reserved files to avoid
- Major version suffixes

See [14](https://verdverm.com/go-mods/#fn:14) for more details.

## Only Secure Remotes



Go will only talk to secure code hosts, preferring `https` and `git+ssh`.

You can use GOINSECURE to list module patterns which can be fetched over http and other insecure protocols. Modules fetched insecurly will still be validated against the checksum database.

Consult the table of VCS Schemes [15](https://verdverm.com/go-mods/#fn:15) to find which tools and protocols are supported. You may also need to set GOVCS [16](https://verdverm.com/go-mods/#fn:16).

## Private module support



Go supports modules developed in private. You can

- Fetch modules from private code repositories
- Prevent your private modules from being publicly indexed
- Run a private proxy and sumdb

See the private modules section [17](https://verdverm.com/go-mods/#fn:17) for details and necessary configuration.

To authenticate with private module hosts, Go defers to tool config like `.gitconfig` when downloading directly. For `https` BasicAuth is supported through the `.netrc` file. [18](https://verdverm.com/go-mods/#fn:18)

## Preventing dependency confusion



**Dependency confusion** [19](https://verdverm.com/go-mods/#fn:19) is when a public package with the same name as an internal package is fetched. Go helps to prevent this by

> **Requiring a domain to start module and import paths**

This means that module names cannot overlap, such as when a malicious actor registers the same module in a public registry.

> **Ignoring replace directives in dependencies**

A comprimised dependency cannot replace other dependencies with one hosted under a different domain.

## Malicious version changes



There are two main version attacks, replacing or adding a tag with an exploit.

> **Replacing a tag**

Retagging is practically impossible, given a module has been fetched once, by anyone. The original hash will be in the global sumdb and the validation will fail. This will of course depend on your `GO[NO]SUM`, `GO[NO]PROXY`, and `GOPRIVATE` settings.

> **Creating a new tag**

In Go, versions are specific, not a range. Additionally, Go will only select from versions which are listed. By design, Go will not select newer modules and is relatively safe from malicious version increments.

## No pre or post hooks



The go module system lacks any pre or post hooks for fetch, build, or install. This rules out a class of attacks, such as those seen with NPM.

## Information in the binaries



Go adds the dependency information into the binary. This includes their path, version, and sumdb hash.

```
go version -m $(which binary)
```

With Go 1.18, it will also include the build flags, environment settings, and VCS information for the main module. [20](https://verdverm.com/go-mods/#fn:20)

## Reproducible Builds



Go has a goal for 100% reproducible builds of artifacts. MVS dependency management is one part and core to this, ensuring that the source code is the same. While this is only the first step, the Go team has been able to reach this goal even when cross-compiling.

## Learning more



- [Module Reference](https://golang.org/ref/mod)
- [Go & Versioning](https://research.swtch.com/vgo)
- [Original Proposal](https://github.com/golang/go/issues/24301)
- [GitHub Issues](https://github.com/golang/go/issues?q=is%3Aopen+is%3Aissue+label%3Amodules)

------

1. https://research.swtch.com/vgo-mvs (part 4 of a series) [↩︎](https://verdverm.com/go-mods/#fnref:1)
2. https://golang.org/ref/mod#minimal-version-selection [↩︎](https://verdverm.com/go-mods/#fnref:2)
3. https://golang.org/ref/mod#lazy-loading [↩︎](https://verdverm.com/go-mods/#fnref:3)
4. https://golang.org/ref/mod#mod-commands [↩︎](https://verdverm.com/go-mods/#fnref:4)
5. https://golang.org/ref/mod#environment-variables [↩︎](https://verdverm.com/go-mods/#fnref:5)
6. https://golang.org/ref/mod#private-modules [↩︎](https://verdverm.com/go-mods/#fnref:6)
7. You probably shouldn’t use this [↩︎](https://verdverm.com/go-mods/#fnref:7)
8. https://golang.org/ref/mod#authenticating [↩︎](https://verdverm.com/go-mods/#fnref:8)
9. https://golang.org/ref/mod#module-cache [↩︎](https://verdverm.com/go-mods/#fnref:9)
10. https://golang.org/ref/mod#checksum-database [↩︎](https://verdverm.com/go-mods/#fnref:10)
11. https://blog.malwarebytes.com/101/2017/10/out-of-character-homograph-attacks-explained/ [↩︎](https://verdverm.com/go-mods/#fnref:11)
12. https://www.securityweek.com/zero-day-homograph-domain-name-attack [↩︎](https://verdverm.com/go-mods/#fnref:12)
13. https://github.com/golang/go/issues/44970 [↩︎](https://verdverm.com/go-mods/#fnref:13)
14. https://golang.org/ref/mod#go-mod-file-ident [↩︎](https://verdverm.com/go-mods/#fnref:14)
15. https://golang.org/ref/mod#vcs [↩︎](https://verdverm.com/go-mods/#fnref:15)
16. https://golang.org/ref/mod#vcs-govcs [↩︎](https://verdverm.com/go-mods/#fnref:16)
17. https://golang.org/ref/mod#private-modules [↩︎](https://verdverm.com/go-mods/#fnref:17)
18. https://golang.org/ref/mod#private-module-repo-auth [↩︎](https://verdverm.com/go-mods/#fnref:18)
19. https://medium.com/@alex.birsan/dependency-confusion-4a5d60fec610 [↩︎](https://verdverm.com/go-mods/#fnref:19)
20. https://github.com/golang/go/issues/37475 [↩︎](https://verdverm.com/go-mods/#fnref:20)