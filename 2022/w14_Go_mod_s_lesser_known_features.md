- 原文地址：https://verdverm.com/go-mods/
- 原文作者：**verdverm.com**
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w14_Go_mod_s_lesser_known_features.md
- 译者：[Fivezh](https://github.com/fivezh)
- 校对：[](https://github.com/)

# Go mod's lesser known features

Modules are how Go manages dependencies. A module is a collection of packages that are released, versioned, and distributed together. Each package within a module is a collection of source files in the same directory that are compiled together.

In this post, we will explore Go mododules design and learn how they support supply chain security. You can find the `go mod` documentation here: https://golang.org/ref/mod

### Contents

[Anatomy of a go.mod file](https://verdverm.com/go-mods/#anatomy-of-a-gomod-file)[Minimum Version Selection](https://verdverm.com/go-mods/#minimum-version-selection)[Directives in go.mod](https://verdverm.com/go-mods/#directives-in-gomod)[Environment variables](https://verdverm.com/go-mods/#environment-variables)[Hashes and the go.sum file](https://verdverm.com/go-mods/#hashes-and-the-gosum-file)[Local module cache](https://verdverm.com/go-mods/#local-module-cache)[Global services modules and hashes](https://verdverm.com/go-mods/#global-services-modules-and-hashes)[Module naming](https://verdverm.com/go-mods/#module-naming)[Only Secure Remotes](https://verdverm.com/go-mods/#only-secure-remotes)[Private module support](https://verdverm.com/go-mods/#private-module-support)[Preventing dependency confusion](https://verdverm.com/go-mods/#preventing-dependency-confusion)[Malicious version changes](https://verdverm.com/go-mods/#malicious-version-changes)[No pre or post hooks](https://verdverm.com/go-mods/#no-pre-or-post-hooks)[Information in the binaries](https://verdverm.com/go-mods/#information-in-the-binaries)[Reproducible Builds](https://verdverm.com/go-mods/#reproducible-builds)[Learning more](https://verdverm.com/go-mods/#learning-more)

Notes:

*The statements here reference Go 1.17 and not all applies to older versions.*

*This post is accompanied by a talk at PackageCon2021. The video will be added once available.*

[Download the slides](https://verdverm.com/PackagingCon2021-GoMods.pdf)

## Anatomy of a go.mod file



```
// Sample go.mod file
module github.com/org/module         // module name

require (                            // module dependencies
  github.com/foo/bar  v0.1.2
  github.com/cow/moo  v1.2.3
  mydomain.com/gopher v0.2.3-beta1
)
```

Go has restrictions on a module name which we will talk about later. The version is a specific and minimum version for your project. Note, there are no version ranges, only a single Semantic Version. As Go processes the dependency tree, it selects the *maximum* of the versions found. In doing so, MVS can create a reproducible dependency tree without a lockfile.

## Minimum Version Selection



Golang uses the MVS (minimum version selection) [1](https://verdverm.com/go-mods/#fn:1) [2](https://verdverm.com/go-mods/#fn:2) algorithm to select dependency versions. This deterministic algorithm has nice properties for reproducible builds and avoids the NP-complete runtime complexity. There is no need for a SAT solver because the dependency selection problem is constrained.

At its heart, *hand waving away some details*, MVS is a breadth-first traversal across modules and versions. The tree is defined by `go.mod` files for a module, its dependencies, its dependencies-dependencies, and so on.

![Minimum Version Selection](https://verdverm.com/images/mvs-buildlist.svg)

The `minimum` terminology is due to the idea that this is a minimal implementation for a lockfile free, deterministic dependecy management system.

## Directives in go.mod



The `go.mod` file has a number of directives for controlling versions and dependencies.

```
module example.com/my/thing

go 1.16

require example.com/other/thing v1.0.2
require example.com/new/thing/v2 v2.3.4
exclude example.com/old/thing v1.2.3
replace example.com/bad/thing v1.4.5 => example.com/good/thing v1.4.5
retract [v1.9.0, v1.9.5]
```

- `go` - sets the minimum Go syntax version
- `require` - specify direct module dependencies
- `exclude` - prevents a dependency version
- `replace` - substitutes without renaming
- `retract` - minor and patch versions of this module

`//Deprecated` can be used for major version of your modules. You add a comment and tag a new release.

```
// Deprecated: use example.com/mod/v2 instead.
module example.com/mod
```

As of Go 1.17, there are two require blocks, one for direct and indirect each, to support lazy loading. [3](https://verdverm.com/go-mods/#fn:3)

## Environment variables



Go supports a number of environment variables for controlling how modules and module aware commands [4](https://verdverm.com/go-mods/#fn:4) work. The following table contains the variables referenced in later sections. For a full list, more details, and examples, see: [5](https://verdverm.com/go-mods/#fn:5) [6](https://verdverm.com/go-mods/#fn:6)

You can use `go env` to see the current settings.

| variable   | used for                                                     |
| ---------- | ------------------------------------------------------------ |
| GOMODCACHE | directory for module related files                           |
| GOPRIVATE  | module globs to handle as private                            |
| GOPROXY    | ordered list of module proxies to use                        |
| GONOPROXY  | module globs to fetch directly                               |
| GOSUMDB    | ordered list of sumdb hosts to use                           |
| GONOSUMDB  | module globs to omit remote sumdb checks on                  |
| GOVCS      | sets VCS tools allowed for public and private access         |
| GOINSECURE | globs to allow fallback to http on [7](https://verdverm.com/go-mods/#fn:7) |

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