# Go 语言中的插件

- 原文地址：https://eli.thegreenplace.net/2021/plugins-in-go/
- 原文作者：Eli Bendersky
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w35-Plugins%20in%20Go.md
- 译者：[朱亚光](https://github.com/zhuyaguang)
- 校对：

很多年以前我就开始写一系列关于[插件的文章](https://eli.thegreenplace.net/tag/plugins)：介绍这些插件在不同的系统和编程语言下是如何设计和实现的。今天这篇文章，我打算把这个系列扩展下，讲讲 Go 语言中一些插件的例子。

需要提醒的是，本系列[头几篇的文章](https://eli.thegreenplace.net/2012/08/07/fundamental-concepts-of-plugin-infrastructures)就介绍了插件的四个基本概念，并且声明几乎所有的插件系统，都可以将它们的设计映射到以下 4 个概念来描述和理解：

1. 发现

2. 注册

3. 插件附着到应用程序上的钩子（又称，”挂载点“）

4. 将应用程序能力暴露给插件（又称，扩展 API）

   

![Gopher holding an Ethernet cable plugged into the wall](https://eli.thegreenplace.net/images/2021/gopherplug.png)

## 两种类型插件

和其他静态编译编程语言一样，Go 中通常会讨论两种一般类型的插件:编译时插件和运行时插件。这两种我们都会讲到。

## 编译时插件

编译时插件由一系列代码包组成，这些代码包编译进了应用程序的二进制文件中。一旦二进制文件编译好，它的功能就固定了。

最有名的 Go 编译时插件系统就是 database/sql 包的驱动程序。我已经写了[一整篇关于这个话题的文章](https://eli.thegreenplace.net/2019/design-patterns-in-gos-databasesql-package/)(https://eli.thegreenplace.net/2019/design-patterns-in-gos-databasesql-package/)，大家可以看下。

简单概括下：数据库驱动是主应用程序通过一个空白导入 `_ "name"` 导入的包。这些包通过它们的 `init`函数使用`sql.Register`向`database/sql`注册。

关于基本插件的概念， 下面有一个编译时插件如何运作的例子（以`database/sql`为例）

2.  发现：这点很明确，`import`一个插件包。插件可以在它们`init`函数自动执行注册。
4.  注册：由于插件被编译到主应用程序之中，它可以直接从插件中调用一个注册函数(例如 sql.Register)。
6.  应用程序钩子：通常，插件将实现应用程序提供的接口，注册过程将连接接口实现。插件使用`database/sql`实现驱动程序。驱动程序接口和实现该接口的值将使用 sql.Register 注册。
7.  将应用程序能力暴露给插件:对于编译时插件，这很简单;由于插件被编译成二进制文件，它可以从主应用程序中导入实用程序包，并根据需要在代码中使用它们。

## 运行时插件

运行时插件的代码不会被编译到主应用程序的原始二进制文件中；相反，它在运行时连接到这个应用程序。在编译语言中，实现这一目标的常用工具是共享库。Go 也支持这种方法。本节的后面部分将提供一个使用共享库，在 Go 中开发插件系统的例子;最后还会讨论其他方式实现的运行时插件。

Go 自带一个内置在标准库中的插件包。这个包让我们可以写出编译进共享库，而不是可执行二进制文件的 Go 程序。另外，它还提供了简单函数来从插件包里面加载共享库和获取符号。

在这篇文章中，我开发了一个完整的运行时插件系统示例；它复制了之前关于[插件基础设施](https://eli.thegreenplace.net/2012/08/07/fundamental-concepts-of-plugin-infrastructures)的文章中的`htmlize`源码，并且它的设计和后面那篇[C 语言中的插件](https://eli.thegreenplace.net/2012/08/24/plugins-in-c)文章类似。这个示例程序很简单，就是把一些标记语言（比如 [reStructuredText](https://en.wikipedia.org/wiki/ReStructuredText) 或者 Markdown）转换成 HTML，并支持插件，使得我们能够调整某些标记元素的处理方式。完整的示例代码在[这篇文章](https://github.com/eliben/code-for-blog/tree/master/2021/go-htmlize-plugin)里(https://github.com/eliben/code-for-blog/tree/master/2021/go-htmlize-plugin)。

![Directory contents of the plugin sample](https://eli.thegreenplace.net/images/2021/plugin-dir-contents.png)

让我们用插件的基本概念来分析这个例子。

**发现和注册**：是通过文件系统查找完成。主应用程序有一个带有`LoadPlugins`函数的插件包。这个函数扫描给定目录中以.so 结尾的文件，并将所有此类文件视为插件。它希望在每个共享库中找到一个名为`InitPlugin`的全局函数，并调用它，为它提供一个`PluginManager`(稍后会详细介绍)。

插件最开始是怎么变成`.so`文件的呢？通过 命令 `-buildmode=plugin` 构建。具体更多的细节，可以看[示例源码](https://github.com/eliben/code-for-blog/blob/master/2021/go-htmlize-plugin/) 中的`buildplugins.sh`脚本和 README 文件。

**应用程序勾子**：现在是描述`PluginManager`类型的好时机。这是插件和主应用程序之间通信的主要类型。流程如下:

-   应用程序在 LoadPlugins 新建一个 PluginManager，并将其传给它找到的所有插件。
-   每个插件使用`PluginManager`来给各种勾子注册自己的处理程序。
-   LoadPlugins 在所有的插件注册后，将`PluginManager`返回给主程序。
-   当应用程序运行时，使用  PluginManager 来根据需要调用已注册插件的勾子。

举个例子，PluginManager 有下面这个函数：

~~~go
func (pm *PluginManager) RegisterRoleHook(rolename string, hook RoleHook)
~~~

RoleHook 是一个函数类型：

~~~go
// RoleHook takes the role contents, DB and Post and returns the text this role
// should be replaced with.
type RoleHook func(string, *content.DB, *content.Post) string
~~~

插件可以调用`RegisterRoleHook` 来注册一个特定文本角色的处理程序。请注意，尽管这个设计并没有使用 Go 的 interfaces ，但是其他设计也可以实现同样功能，取决于应用程序的具体情况。

**将应用程序能力暴露给插件**：正如上面 RoleHook 类型那样，应用程序将数据对象传递给插件使用。content.DB 提供了对应用程序数据库的访问。content.Post 提供了当前格式化插件的特定的 Post。插件可以根据需要使用这些对象，来获取应用程序的数据或者行为。

## 运行时插件的替代方法

考虑到插件包只是在 [Go1.8](https://golang.org/doc/go1.8) 中新增的，还有前面描述的种种限制，所以也难怪 Go 生态系统中出现了其他插件方法。

其中最有趣的一个方向就是，IMHO，通过 RPC 调用插件。我一直很喜欢将应用程序解耦到独立的进程中，然后通过 RPC 或本地主机上的 TCP 进行通信。（我猜他们现在称之为 微服务），因为它有几个重要的优点：

-   隔离性：插件的崩溃不会导致整个应用程序崩溃。
-   语言之间的交互性：如果 RPC 是接口，你还会在乎插件使用什么语言写的吗？
-   分布式：如果插件通过网络接口，我们可以很容易将它们分发到不同机器上，来提高性能、可靠性等等。

另外，Go 标准库中有一个很强大的 RPC 包：net/rpc，让这一点实现起来相当容易。

最广泛使用的基于 RPC 的插件系统就是[hashicorp/go-plugin](https://github.com/hashicorp/go-plugin)，Hashicorp 以创建优秀的 Go 软件而闻名，显然他们在许多系统中使用了 Go 插件，因此这些插件都是经过实战测试过的。（尽管他们的文档可以写的更好点）

Go 插件运行在 net/rpc 之上，当然也支持 gRPC。像 gRPC 这样的高级 RPC 协议非常适合插件，因为它们包含了开箱即用的版本控制，解决了不同版本的插件与主应用程序之间的互操作性问题。