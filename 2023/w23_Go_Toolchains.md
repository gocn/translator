- 原文地址：https://go.dev/doc/toolchain
- 原文作者：**Go Team**
- 本文永久链接：
- 译者：[cvley](https://github.com/cvley)
- 校对：[Cluas](https://github.com/Cluas)


## 介绍

从 Go 1.21 开始，Go 发行版由一个 `go` 命令和一个捆绑的 Go 工具链组成，其中包括标准库以及编译器、汇编器和其他工具。`go` 命令可以使用其捆绑的 Go 工具链以及在本地 `PATH` 中找到或根据需要下载的其他版本。

当前使用的 Go 工具链的选择取决于 `GOTOOLCHAIN` 环境设置以及主模块的 `go.mod` 文件或当前工作区的 `go.work` 文件中的 `go` 和 `toolchain` 行。当您在不同的主模块和工作区之间移动时，当前使用的工具链版本可能会有所不同，就像模块依赖版本一样。

在标准配置中，`go` 命令在其捆绑的工具链与主模块或工作区中的 `go` 或 `toolchain` 行中的版本至少一样新时使用自己的捆绑工具链。例如，在使用 Go 1.21.3 捆绑的 `go` 命令中，主模块指定 `go 1.21.0` 时，`go` 命令使用 Go 1.21.3。当 `go` 或 `toolchain` 行比捆绑的工具链更新时，`go` 命令将运行更新的工具链。例如，在使用Go 1.21.3捆绑的go命令中，主模块声明 `go 1.21.9` 时，go 命令会查找并运行 `Go 1.21.9`。它首先在PATH中查找名为 `go1.21.9` 的程序，否则会下载并缓存 Go 1.21.9 工具链。可以禁用此自动工具链切换，但在这种情况下，为了更精确的向前兼容性，`go` 命令将拒绝在 `go` 行要求更高版本的 Go 的主模块或工作区中运行。也就是说，`go` 行设置了使用模块或工作区所需的最低 Go 版本。

作为其他模块的依赖项的模块可能需要将最低Go版本要求设置为低于在该模块中直接工作时要使用的首选工具链。在这种情况下，`go.mod` 或 `go.work` 中的 `toolchain` 行设置了一个首选工具链，这个工具链在 `go` 命令决定使用哪个工具链时优先于 `go` 行。

可以将 `go` 和 `toolchain` 行视为指定模块对 Go 工具链本身的依赖关系的版本要求，就像 `go.mod` 中的 `require` 行指定对其他模块的依赖关系的版本要求一样。`go get` 命令管理 Go 工具链依赖关系，就像管理对其他模块的依赖关系一样。例如，`go get go@latest` 会更新模块以要求最新发布的 Go 工具链。

`GOTOOLCHAIN` 环境设置可以强制使用特定的 Go 版本，覆盖 `go` 和 `toolchain` 行。例如，要使用 Go 1.21rc3 测试一个包：

```
GOTOOLCHAIN=go1.21rc3 go test
```

默认的 `GOTOOLCHAIN` 设置为 `auto`，这启用了之前描述的工具链切换。替代形式 `<name>+auto` 在决定是否进一步切换之前设置要使用的默认工具链。例如，`GOTOOLCHAIN=go1.21.3+auto` 指示 `go` 命令从默认使用 Go 1.21.3 开始做出决策，但如果由 `go` 和 `toolchain` 行指示，则仍然使用更新的工具链。由于默认的 `GOTOOLCHAIN` 设置可以通过 `go env -w` 更改，因此如果您安装了Go 1.21.0或更高版本，那么：

```
go env -w GOTOOLCHAIN=go1.21.3+auto
```

将您的 Go 1.21.0 安装替换为 Go 1.21.3。

本文档的其余部分将更详细地解释 Go 工具链的版本控制、选择和管理。

## Go 版本

发布的 Go 版本使用版本语法 “1.N.P”，表示 Go 1.N 的第 _P_ 次已发布版本。初始版本为 1.N.0，例如 “1.21.0”。后续版本如 1.N.9 通常被称为补丁版本。

Go 1._N_的发布候选版本，在 1.N.0 之前发布，使用 ‘1.N_rc_R’ 的版本语法。Go 1.N 的第一个发布候选版本是1._N_rc1，如 `1.23rc1`。

语法 “1.N” 被称为“语言版本”。它表示实现该版本 Go 语言和标准库的 Go 发布的整个系列。

Go 版本的语言版本是将 N 之后的所有内容截断的结果：1.21、1.21rc2 和 1.21.3都实现了语言版本 1.21。

已发布的 Go 工具链如 Go 1.21.0 和 Go 1.21rc1 报告特定版本（例如 `go1.21.0` 或 `go1.21rc1`）从 `go version` 和`[runtime.Version](/pkg/runtime/#Version)`中。未发布（仍在开发中）的Go工具链从Go开发存储库构建，只报告语言版本（例如 `go1.21`）。

任何两个 Go 版本都可以进行比较，以确定一个是否小于、大于或等于另一个。如果语言版本不同，那么就决定了比较：1.21.9 < 1.22。在语言版本内，从最小到最大的排序是：语言版本本身，然后按_R_排序的发布候选版本，然后按_P_排序的发布版本。

例如，1.21 < 1.21rc1 < 1.21rc2 < 1.21.0 < 1.21.1 < 1.21.2。

在 Go 1.21 之前，Go 工具链的初始版本是 1._N_，而不是 1._N_.0，因此对于 _N_ < 21，排序会调整为将 1._N_ 放在发布候选版本之后。

例如，1.20rc1 < 1.20rc2 < 1.20rc3 < 1.20 < 1.20.1。

早期版本的 Go 有 beta 版本，版本号为 1.18beta2 之类的版本。Beta 版本放在版本排序中的发布候选版本之前。

例如，1.18beta1 < 1.18beta2 < 1.18rc1 < 1.18 < 1.18.1。

## Go 工具链命名

标准的 Go 工具链命名为 `go_V_`，其中 _V_ 是表示 beta 版本、发布候选版本或发布版本的 Go 版本。例如，`go1.21rc1` 和 `go1.21.0` 是工具链名称；`go1.21` 和 `go1.22` 不是（最初的发布版本是 `go1.21.0` 和 `go1.22.0`），但 `go1.20` 和 `go1.19` 是。

非标准工具链使用 `go_V_-_suffix_` 形式的名称，其中 suffix 可以是任何后缀。

通过比较嵌入在名称中的版本 `_V_`（删除初始的 `go` 并丢弃任何以 `-` 开头的后缀）来比较工具链。例如，`go1.21.0` 和 `go1.21.0-custom` 在排序目的上相等。

## 模块和工作区配置

Go 模块和工作区在其 `go. mod` 或 `go.work` 文件中指定与版本相关的配置。

`go` 行声明了使用模块或工作区所需的最低 Go 版本。出于兼容性原因，如果 `go. mod` 文件中省略了 `go` 行，则该模块被认为具有隐式 `go 1.16` 行，如果 `go.work` 文件中省略了 go 行，则该工作区被认为具有隐式 `go 1.18` 行。

`toolchain` 行声明了与模块或工作区一起使用的建议工具链。如下面的 “[Go工具链选择](https://go.dev/doc/toolchain#select])”中所述，如果默认工具链的版本小于建议工具链的版本，则 `go` 命令可以在该模块或工作区中运行此特定工具链。如果省略 `toolchain` 行，则模块或工作区被认为具有隐式 `toolchain go_V_` 行，其中 _V_ 是 `go` 行的 Go 版本。

例如，一个说 `go 1.21.0` 但没有 `toolchain` 行的 `go. mod` 被解释为它有一个 `toolchain go1.21.0` 行。

Go 工具链拒绝加载声明最低所需 Go 版本大于工具链自己版本的模块或工作区。

例如，Go 1.21.2 将拒绝加载带有 `go 1.21.3` 或 `go 1.22` 行的模块或工作区。

模块的 `go` 行必须声明一个版本大于或等于要求语句中列出的每个模块声明的 `go` 版本。工作区的 `go` 行必须声明一个版本大于或等于 `use` 语句中列出的每个模块声明的 `go` 版本。

例如，如果模块 _M_ 需要一个依赖项 _D_ 和一个声明 `go 1.22.0` 的 `go.mod`，那么 _M_ 的 `go.mod` 不能说 `go 1.21.3`。

每个模块的 `go` 行设置编译器在编译该模块中的包时强制执行的语言版本。可以使用[构建约束](https://go.dev/cmd/go#hdr-Buid_constraints)在每个文件的基础上更改语言版本。

例如，包含使用 Go 1.21 语言版本的代码的模块应该有一个 `go. mod` 文件，其中包含 `go` 行，例如 `go 1.21` 或 `go 1.21.3`。如果特定的源文件应该仅在使用较新的 Go 工具链时编译，则在该源文件中添加 `//go：build go1.22` 既可以确保只有 Go 1.22 和较新的工具链会编译该文件，又可以将该文件中的语言版本更改为 Go 1.22。

使用 `go get` 可以最方便、最安全地修改 `go` 和 `toolchain` 行；请参阅[下面专门介绍 go get 的部分](https://go.dev/doc/toolchain#get)。

在 Go 1.21 之前，Go 工具链将 `go` 行视为一个建议性要求：如果构建成功，工具链会假设一切正常，如果没有，它会打印一个关于潜在版本不匹配的注释。Go 1.21 将 `go` 行更改为强制性要求。这种行为部分向后移植到更早的语言版本：从 Go 1.19.11 开始的 Go 1.19 版本和从 Go 1.20.6 开始的 Go 1.20 版本，拒绝加载声明 Go 1.21 或更高版本的工作区或模块。

在 Go 1.21 之前，工具链不要求模块或工作区的 `go` 行大于或等于其每个依赖模块所需的 `go` 版本。

`go` 命令根据 `GOTOOLCHAIN` 设置选择要使用的 Go 工具链。要查找 `GOTOOLCHAIN` 设置，`go` 命令使用任何 Go 环境设置的标准规则：

- 如果 `GOTOOLCHAIN` 在进程环境中设置为非空值（由 [os.Getenv](https://go.dev/pkg/os/#Getenv) 查询），则 `go` 命令使用该值。

- 否则，如果在用户的环境默认文件（使用 [`go env -w` 和 `go env -u`](https://go.dev/cmd/go/#hdr-Print_Go_environment_information) 管理）中设置了 `GOTOOLCHAIN`，则 `go` 命令使用该值。

- 否则，如果在捆绑的 Go 工具链的环境默认文件（`$GOROOT/go. env）中设置了 `GOTOOLCHAIN`，则 `go` 命令使用该值。


在标准 Go 工具链中，`$GOROOT/go.env` 文件设置默认的 `GOTOOLCHAIN=auto`，但重新打包的 Go 工具链可能会更改此值。

如果 `$GOROOT/go.env` 文件丢失或未设置默认值，则 `go` 命令假定 `GOTOOLCHAIN=local`。

运行 `go env GOTOOLCHAIN` 打印 `GOTOOLCHAIN` 设置。

## Go toolchain 选择

在启动时，`go` 命令会选择要使用的 Go 工具链。它会查阅 `GOTOOLCHAIN` 设置，该设置采用 `<name>`、`<name>+auto` 或 `<name>+path` 的形式。`GOTOOLCHAIN=auto` 是 `GOTOOLCHAIN=local+auto` 的简写；同样，`GOTOOLCHAIN=path` 是 `GOTOOLCHAIN=local+path` 的简写。其中 `<name>` 设置默认的 Go 工具链：`local` 表示捆绑的 Go 工具链（与运行 go 命令的工具链相同），否则 `<name>` 必须是特定的 Go 工具链名称，例如 `go1.21.0`。`go` 命令更喜欢运行默认的 Go 工具链。如上所述，从 Go 1.21 开始，Go 工具链拒绝在需要更新的 Go 版本的工作区或模块中运行。相反，它们会报告错误并退出。

当 `GOTOOLCHAIN` 设置为 `local` 时，`go` 命令始终运行捆绑的 Go 工具链。

当 `GOTOOLCHAIN` 设置为 `<name>`（例如，`GOTOOLCHAIN=go1.21.0`） 时，`go` 命令始终运行该特定的 Go 工具链。如果在系统 PATH 中找到具有该名称的二进制文件，则 `go` 命令使用它。否则，`go` 命令使用它下载并验证的 Go 工具链。

当 `GOTOOLCHAIN` 设置为 `<name>+auto` 或 `<name>+path`（或简写 `auto` 或 `path`）时，`go` 命令根据需要选择并运行更新的 Go 版本。具体来说，它会查阅当前工作区的 `go.work` 文件或（当没有工作区时）主模块的 `go.mod` 文件中的 `toolchain` 和 `go` 行。如果 `go.work` 或 `go.mod` 文件具有 `toolchain <tname>` 行，并且 `<tname>` 比默认的 Go 工具链更新，则 `go` 命令会运行 `<tname>`。如果文件具有 `toolchain default` 行，则 `go` 命令会运行默认的 Go 工具链，禁用任何尝试更新到 `<name>` 之外的操作。否则，如果文件具有 `go <version>` 行，并且 `<version>` 比默认的 Go 工具链更新，则 `go` 命令会运行 `go<version>`。

要运行除捆绑的 Go 工具链之外的工具链，`go` 命令会在进程的可执行路径（Unix 和 Plan 9 上的 `$PATH`，Windows 上的 `%PATH%`）中搜索具有给定名称的程序（例如 `go1.21.3`），并运行该程序。如果找不到这样的程序，则 `go` 命令会下载并运行指定的 Go 工具链。使用 `GOTOOLCHAIN` 形式 `<name>+path` 会禁用下载回退，导致 `go` 命令在搜索可执行路径后停止。

运行 `go version` 会打印所选的 Go 工具链的版本（通过运行所选工具链的 `go version` 实现）。

运行 `GOTOOLCHAIN=local go version` 会打印捆绑的 Go 工具链的版本。

## Go toolchain 替换

对于大多数命令，工作区的 `go.work` 或主模块的 `go.mod` 将具有至少与任何模块依赖项中的 `go` 行一样新的 `go` 行，由于版本排序[配置要求](https://go.dev/doc/toolchain#config)。在这种情况下，启动工具链选择运行足够新的 Go 工具链以完成命令。

一些命令将新模块版本作为其操作的一部分：`go get` 将新模块依赖项添加到主模块；`go work use` 将新的本地模块添加到工作区；`go work sync` 重新同步工作区和可能自创建工作区以来已更新的本地模块；`go install package@version` 和 `go run package@version` 在空主模块中有效地运行并将 `package@version` 添加为新的依赖项。所有这些命令都可能遇到一个需要比当前执行的 Go 版本更新的 `go.mod` `go` 行的模块。

当命令遇到需要更新的 Go 版本的模块并且 `GOTOOLCHAIN` 允许运行不同的工具链（它是`auto`或`path`形式之一）时，`go` 命令选择并切换到适当的更新工具链以继续执行当前命令。

每当 `go` 命令在启动工具链选择后切换工具链时，它都会打印一条解释原因的消息。例如：

```
go: module example.com/widget@v1.2.3 requires go >= 1.24rc1; switching to go 1.27.9
```

如示例所示，`go` 命令可能会切换到比发现的要求更新的工具链。一般来说，`go` 命令旨在切换到受支持的 Go 工具链。

为选择工具链，`go` 命令首先获取可用工具链列表。对于 `auto` 形式，`go` 命令下载可用工具链列表。对于 `path` 形式，`go` 命令扫描 PATH 中任何命名为有效工具链的可执行文件，并使用它找到的所有工具链列表。使用该工具链列表，`go` 命令识别出最多三个候选项：

- 未发布的 Go 语言版本的最新发布候选版本（1._N_₃rc_R_₃），
- 最近发布的 Go 语言版本的最新补丁版本（1._N_₂._P_₂），以及
- 上一个 Go 语言版本的最新补丁版本（1._N_₁._P_₁）。

这些是根据 Go 的[发布政策](https://go.dev/doc/devel/release#policy)支持的 Go 发布版本。与[最小版本选择](https://research.swtch.com/vgo-mvs)一致，`go` 命令然后保守地使用满足新要求的_最小_（最旧）版本的候选项。

例如，假设 `example.com/widget@v1.2.3` 需要 Go 1.24rc1 或更高版本。`go` 命令获取可用工具链列表，并发现最近两个 Go 工具链的最新补丁版本是 Go 1.28.3 和 Go 1.27.9，还有发布候选版 Go 1.29rc2。在这种情况下，`go` 命令将选择 Go 1.27.9。如果 `widget` 需要 Go 1.28 或更高版本，则 `go` 命令将选择 Go 1.28.3，因为 Go 1.27.9 太旧了。如果 `widget` 需要 Go 1.29 或更高版本，则 `go` 命令将选择 Go 1.29rc2，因为 Go 1.27.9 和 Go 1.28.3 都太旧了。

命令集成了需要新的 Go 版本的新模块版本，将新的最小 `go` 版本要求写入当前工作区的 `go.work` 文件或主模块的 `go.mod` 文件，更新 `go` 行。为了[重复性](https://research.swtch.com/vgo-principles#repeatability)，任何更新 `go` 行的命令也会更新 `toolchain` 行以记录其自己的工具链名称。下次在该工作区或模块中运行 `go` 命令时，它将在 [toolchain 选择](https://go.dev/doc/toolchain#select)期间使用更新后的 `toolchain` 行。

例如，`go get example.com/widget@v1.2.3` 可能会打印类似上面的切换通知并切换到 Go 1.27.9。Go 1.27.9 将完成 `go get` 并更新工具链行以表示 `toolchain go1.27.9`。下一个在该模块或工作区中运行的 `go` 命令将在启动期间选择 `go1.27.9`，并且不会打印任何切换消息。

通常，如果运行任何 `go` 命令两次，如果第一个打印了切换消息，则第二个不会打印，因为第一个还更新了 `go.work` 或 `go.mod` 以在启动时选择正确的工具链。例外是 `go install package@version` 和 `go run package@version` 形式，它们在没有工作区或主模块的情况下运行，无法编写 `toolchain` 行。每次需要切换到较新工具链时，它们都会打印切换消息。

## 下载 toolchains

当使用 `GOTOOLCHAIN=auto` 或 `GOTOOLCHAIN=<name>+auto` 时，Go 命令会根据需要下载更新的工具链。这些工具链被打包为特殊模块，模块路径为 `golang.org/toolchain`，版本为 `v0.0.1-goVERSION.GOOS-GOARCH`。工具链像其他模块一样被下载，这意味着可以通过设置 `GOPROXY` 来代理工具链下载，并通过Go校验和数据库检查它们的校验和。由于使用的特定工具链取决于系统自己的默认工具链以及本地操作系统和架构（GOOS 和 GOARCH），因此在 `go.sum` 中编写工具链模块的校验和不实际。相反，如果 `GOSUMDB=off`，则工具链下载失败缺乏验证。`GOPRIVATE` 和 `GONOSUMDB` 模式不适用于工具链下载。

## 使用 `go get` 管理 Go 版本模块的需求

通常，`go` 命令将 `go` 和 `toolchain` 行视为声明主模块的版本化工具链依赖项。`go get` 命令可以像管理指定版本化模块依赖项的 `require` 行一样管理这些行。

例如，`go get go@1.22.1 toolchain@1.24rc1` 会更改主模块的 `go.mod` 文件，以读取 `go 1.22.1` 和 `toolchain go1.24rc1`。

`go` 命令理解 `go` 依赖项需要具有更高或等于 Go 版本的 `toolchain` 依赖项。

继续上面的例子，稍后的 `go get go@1.25.0` 也会将工具链更新为 `go1.25.0`。当工具链与 `go` 行完全匹配时，可以省略并暗示它，因此此 `go get` 将删除工具链行。

在降级时也适用相同的要求：如果 `go.mod` 从 `go 1.22.1` 和 `toolchain go1.24rc1` 开始，则 `go get toolchain@go1.22.9` 仅会更新工具链行，但 `go get toolchain@go1.21.3` 将同时将 `go` 行降级为 `go 1.21.3`。效果将是只留下 `go 1.21.3` 而没有工具链行。

特殊形式 `toolchain@none` 表示删除任何工具链行，例如 `go get toolchain@none` 或 `go get go@1.25.0 toolchain@none`。

`go` 命令理解 `go` 和 `toolchain` 依赖项的版本语法以及查询。

例如，就像 `go get example.com/widget@v1.2` 使用 `example.com/widget` 的最新 `v1.2` 版本（可能是 `v1.2.3`），`go get go@1.22` 使用 Go 1.22 语言版本的最新可用版本（可能是 `1.22rc3`，也可能是 `1.22.3`）。对于 `go get toolchain@go1.22` 也是一样的。

`go get` 和 `go mod tidy` 命令维护 `go` 行大于或等于任何所需依赖模块的 `go` 行。

例如，如果主模块具有 `go 1.22.1`，并且我们运行 `go get example.com/widget@v1.2.3`，它声明 `go 1.24rc1`，则 `go get` 将更新主模块的 `go` 行为 `go 1.24rc1`。

继续上面的例子，稍后的 `go get go@1.22.1` 将降级 `example.com/widget` 到与 Go 1.22.1 兼容的版本，否则将完全删除 `example.com/widget` 的要求，就像降级 example.com/widget 的任何其他依赖项一样。

在 Go 1.21 之前，将模块更新到新的 Go 版本（例如 Go 1.22）的建议方法是 `go mod tidy -go=1.22`，以确保在更新 `go` 行的同时进行特定于 Go 1.22 的任何调整。该形式仍然有效，但现在更喜欢简单的 `go get go@1.22`。

当在工作区根目录中包含的目录中的模块中运行`go get`时，`go get`大多数情况下会忽略工作区，但它会更新`go.work`文件以在工作区的`go`行过时时升级`go`行。

## 使用 `go work` 管理 Go 版本的工作区需求

如前所述，运行 `go get` 命令时，如果在工作区根目录内的目录中运行，它将更新 `go.work` 文件中的 `go` 行，使其大于或等于该根目录内的任何模块。但是，工作区还可以引用根目录之外的模块；在这些目录中运行 `go get` 命令可能会导致无效的工作区配置，其中 `go.work` 中声明的 `go` 版本小于一个或多个 `use` 指令中的模块。

命令 `go work use` 用于添加新的 `use` 指令，还会检查 `go.work` 文件中的 `go` 版本是否足够新，以适用于所有现有的 `use` 指令。要更新已与其模块的版本不同步的工作区，请运行不带参数的 `go work use` 命令。

命令 `go work init` 和 `go work sync` 也会根据需要更新 `go` 版本。

要从 `go.work` 文件中删除 `toolchain` 行，请使用 `go work edit -toolchain=none` 命令。
