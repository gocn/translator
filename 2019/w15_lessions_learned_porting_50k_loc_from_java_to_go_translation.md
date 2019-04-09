# 将 5 万行 Java 代码移植到 Go 学到的经验

- 原文地址：[Lessons learned porting 50k loc from Java to Go](https://blog.kowalczyk.info/article/19f2fe97f06a47c3b1f118fd06851fad/lessons-learned-porting-50k-loc-from-java-to-go.html)
- 原文作者：Krzysztof Kowalczyk
- 译文出处: https://blog.kowalczyk.info
- 本文永久链接：https://github.com/gocn/translator/blob/master/2019/w15_lessions_learned_porting_50k_loc_from_java_to_go_translation.md
- 译者：[cvley](https://github.com/cvley)
- 校对：[Ryan](https://github.com/ryankwak)

我曾经签订了一个把大型的 Java 代码库迁移至 Go 的工作合同。

这份代码是 [RavenDB](https://ravendb.net/) 这一 NoSQL JSON 文档数据库的 Java 客户端。包含测试代码，一共有约 5 万行。

移植的结果是一个 [Go 的客户端](https://github.com/ravendb/ravendb-go-client)。

本文描述了我在这个迁移过程中学到的知识。

## 测试，代码覆盖率

自动化测试和代码覆盖率追踪，可以让大型醒目获益匪浅。

我使用 TravisCI 和 AppVeyor 进行测试。[Codecov.io](http://codecov.io/) 用来检测代码覆盖率。还有许多其他的类似服务。

我同时使用 AppVeyor 和 TravisCI，是因为 Travis 在一年前不再支持 Windows，而 AppVeyor 不支持 Linux。

如果现在让我重新选择这些工具，我将只使用 AppVeyor，因为它现在支持 Linux 和 Windows 平台的测试，而 TravisCI 在被私募股权公司收购并炒掉原始开发团队后，前景并不明朗。

Codecov 几乎无法胜任代码覆盖率检测。对于
Go，它将非代码的行（比如注释）当做是未执行的代码。使用这个工具不可能得到 100% 的代码覆盖率。Coveralls 看起来也有同样的问题。

聊胜于无，但有计划让情况变得更好，尤其是对于 Go 程序而言。

## Go 的竞争检测非常棒

一部分代码使用了并发，而并发很容易出错。

Go 提供了竞争检测器，在编译时使用`-race`字段可以开启它。

它会让程序变慢，但额外的检查可以探测是否在同时修改同一个内存位置。

我一直开启`-race`运行测试，通过它的报警，我可以很快地修复那些竞争问题。

## 构建用于测试的特定工具

大型项目很难通过肉眼检查验证正确性。你的大脑一次很难保持太多的代码。

当测试失败时，仅从测试失败的信息中找到原因也是一个挑战。

数据库客户端驱动与 RavenDB 数据库服务端使用 HTTP 交互，命令和结果使用 JSON 编码。

当把 Java 测试代码移植到 Go 时，如果可以获取 Java 客户端与服务端的 HTTP 流量，并与移植到 Go 的代码生成的 HTTP 流量对比，这个信息将非常有用。

我构建了一些特定的工具，帮我完成这些工作。

为了获取 Java 客户端的 HTTP 流量，我使用 Go 构建了一个 [logging HTTP 代理](https://github.com/kjk/httplogproxy)，Java 客户端使用这个代理与服务端交互。

对于 Go 客户端，我构建了一个可以拦截 HTTP 请求的[钩子](https://github.com/ravendb/ravendb-go-client/blob/20fade9ee6d22d60c7babf4a155c4de5bf4cfd3b/request_executor.go#L23)。我使用它把流量记录在文件中。

然后我就可以对比 Java 客户端与 Go 移植的客户端生成的 HTTP 流量的区别了。

## 移植的过程

你不能随机开始迁移 5 万行代码。我知道，不进行测试和验证的每一小步，都将让我迷失在复杂性中。

对于 RavenDB 和 Java 代码库，我是新手。所以我的第一步是深入理解这份 Java 代码的工作原理。

客户端的核心是与服务端通过 HTTP 协议交互。我捕获并研究了流量，编写最简单的与服务器交互的 Go 代码。

当这么做有效果之后，我自信可以复制这些功能。

我的第一个里程碑是移植足够的代码，可以通过移植最简单的 Java 测试代码的测试。

我使用了自底向上和自上到下结合的方法。

自底向上的部分是指，我定位并移植那些用于向服务器发送命令和解析响应的调用链底层的代码。

自上到下的部分是指，我逐步跟踪要移植的测试代码，来确定需要移植实现的功能代码部分。

在成功完成第一步移植后，剩下的工作就是一次移植一个测试，同时移植可通过这个测试的所有需要的代码。

当测试移植并测试通过后，我做了一些让代码更加 Go 风格的改进。

我相信这种一步一步渐进的方法，对于完成移植工作是很重要的。

从心理学角度来看，在面对一个长年累月的项目时，设置简短的中间态里程碑是很重要的。不断的完成这些里程碑让我干劲十足。

一直让代码保持可编译、可运行和可通过测试的状态也很好。当最终要面对那些日积月累的缺陷时，你将很难下手解决。

## 移植 Java 到 Go 的挑战

移植的目标是要尽可能与 Java 代码库一致，因为移植的代码需要与 Java 未来的变化保持同步。

有时我吃惊于自己以一行一行的方式移植的代码量。而移植过程中，最耗费时间的部分是颠倒变量的声明顺序，Java 的声明顺序是`type name`，而 Go 的声明顺序是`name type`。我真心希望有工具可以帮我完成这部分工作。

### String vs. string

在 Java 中，`String` 是一个本质上是引用（指针）的对象。因此，字符串可以为`null`。

在 Go 中 `string` 是一个值类型。它不可能是`nil`，仅仅为空。

这并不是什么大问题，大多情况下我可以无脑地将`null`替换为`""`。

### Errors vs. exceptions

Java 使用异常来传递错误。

Go 返回`error`接口的值。

移植不难，但需要修改大量的函数签名，来支持返回错误值并在调用栈上传播。

### 泛型

Go （目前）并不支持泛型。

移植泛型的接口是最大的挑战。

下面是 Java 中一个泛型方法的例子：

```Java
public <T> T load(Class<T> clazz, String id) {
```

调用者：

```Java
Foo foo = load(Foo.class, "id")
```

在 Go 中，我使用两种策略。

其中之一是使用`interface{}`，它由值和类型组成，与 Java 中的`object`类似。不推荐使用这种方法。虽然有效，但对于这个库的用户而言，操作`interface{}`并不恰当。

在一些情况下我可以使用反射，上面的代码可以移植为：

```Go
func Load(result interface{}, id string) error
```

我可以使用反射来获取`result`的类型，再从 JSON 文档中创建这个类型的值。

调用方的代码：

```Go
var result *Foo
err := Load(&result, "id")
```

### 函数重载

Go 不支持（很大可能用于不会支持）函数重载。

我不确定我是否找到了正确的方式来移植这种代码。

在一些情况下，重载用于创建更简短的帮助函数：

```Java
void foo(int a, String b) {}
void foo(int a) { foo(a, null); }
```

有时我会直接丢掉更简短的帮助函数。

有时我会写两个函数：

```Go
func foo(a int) {}
func fooWithB(a int, b string) {}
```

当潜在的参数数量很大时，有时我会这么做：

```Go
type FooArgs struct {
	A int
	B string
}
func foo(args *FooArgs) { }
```

### 继承

Go 并不是面向对象语言，没有继成。

简单情况下的继承可以使用嵌套的方法移植。

```Java
class B : A { }
```

有时可以移植为：

```Go
type A struct { }
type B struct {
	A
}
```

我们把`A`嵌入到`B`中，因此`B`继承了`A`所有的方法和字段。

这种方法对于虚函数无效。

并没有好方法移植那些使用虚函数的代码。

模拟虚函数的一个方式是将结构体和函数指针嵌套。这本质上来说，是重新实现了 Java
免费提供的，作为`object`实现一部分的虚表。

另一种方式是写一个独立的函数，通过类型判断来调度给定类型的正确函数。

### 接口

Java 和 Go 都有接口，但它们是不一样的内容，就像苹果和意大利香肠的区别一样。

在很少的情况下，我确实会创建 Go 的接口类型来复制 Java 接口。

大多数情况下，我放弃使用接口，而是在 API 中暴露具体的结构体。

### 依赖包的循环引入

Java 允许包的循环引入。

Go 不允许。

结果就是，我无法在移植中复制 Java 代码的包结构。

为了简化，我使用一个包。这种方法不太理想，因为这个包最后会变得很臃肿。实际上，这个包臃肿到在 Windows 下 Go 1.10 无法处理单个包内的那么多源文件。幸运的是，Go 1.11 修复了这个问题。

### 私有、公开、保护

Go 的设计者对此未加以重视。这与他们简化概念的能力不匹配，权限控制就是其中的一个例子。

其他语言倾向于细粒度的权限控制：（每个类的字段和方法）指定最小可能粒度的公开、私有和保护。

结果就是当外部代码使用这个库时，这个库实现的一些功能和这个库中其他的类有一样的访问权限。

Go 简化了这个概念，只拥有公开和私有，访问的范围限制在包的级别。

这更合理一些。

当我想要写一个库，比如说，解析 markdown，我不想把内部实现暴漏给这个库的使用者。但对于我自己隐藏这些内部实现，效果恰恰相反。

Java
开发者注意到这个问题，有时会使用接口作为修复暴漏过度的类的技巧。通过返回一个接口，而不是具体的类，这个类的使用者就无法看到一些可用的公开接口。

### 并发

简单来说，Go 的并发是最好的，内建的竞争检测器非常有助于解决并发的问题。

我刚才说过，我进行的第一个移植是模拟 Java 接口。比如，我实现了 Java `CompletableFuture` 类的复制。

一旦代码可以运行，我就会重写组织，让代码更加符合 Go 的风格。

### 流畅的函数链式调用

RavenDB 用于复杂的查询能力。Java 客户端使用链式方法进行查询构建：

```Java
List<ReduceResult> results = session.query(User.class)
                        .groupBy("name")
                        .selectKey()
                        .selectCount()
                        .orderByDescending("count")
                        .ofType(ReduceResult.class)
                        .toList();
```

链式调用仅在通过异常进行错误交互的语言中有效。当一个函数额外返回一个错误，就没法向上面那样进行链式调用。

为了在 Go 中复制链式调用，我使用了一个“状态错误”的方法：

```Go
type Query struct {
	err error
}

func (q *Query) WhereEquals(field string, val interface{}) *Query {
	if q.err != nil {
		return q
	}
	// logic that might set q.err
	return q
}

func (q *Query) GroupBy(field string) *Query {
if q.err != nil {
		return q
	}
	// logic that might set q.err
	return q
}

func (q *Query) Execute(result inteface{}) error {
	if q.err != nil {
		return q.err
	}
	// do logic
}
```

链式调用可以这么些：

```Go
var result *Foo
err := NewQuery().WhereEquals("Name", "Frank").GroupBy("Age").Execute(&result)
```

### JSON 解析

Java 没有内建的 JSON 解析函数，客户端使用 Jackson JSON 库。

Go 在标准库中有 JSON 的支持，但它并没有提供太多调整解析过程的钩子。

我并没有尝试匹配所有的 Java 功能，因为 Go 内置的 JSON 支持看起来已经足够灵活。

### Go 代码更短

这与其说是 Java 的属性，倒不如说是一种文化，即符合语言习惯的代码是什么样的。

在 Java 中，setter 和 getter 方法很常见。比如，Java 代码：

```Java
class Foo {
	private int bar;

	public void setBar(int bar) {
		this.bar = bar;
	}

	public int getBar() {
		return this.bar;
	}
}
```

Go 语言版本如下：

```Go
type Foo struct {
	Bar int
}
```

3 行 vs 11 行。当你有大量的类，类内有很多成员时，这么做可以不断累加这些类。

大部分其他的代码最后长度基本差不多。

### 使用 Notion 来组织工作

我是 [Notion.so](https://www.notion.so/) 的重度用户。用最简单的话来说，Notion 是一个多级笔记记录应用。可以把它看做是 Evernote 和 wiki 的结合，是由顶级软件设计师精心设计和实现。

下面是我使用 Notion 组织 Go 移植工作的方式：

![](https://d33wubrfki0l68.cloudfront.net/9a1b2705f96b0a6897d5cd86e2504ea898d02a42/542c0/img/025d77f41148194a80a6f87846c0b12225a7c922.png)

下面是具体的内容：

- 上面没有展示，我有一个带日历视图的页面，用来记录在特定时间工作内容和花费时间的简短笔记。因为这次合约是按小时收费，所以这是很重要的信息。感谢这些笔记，我知道我在 11 个月里花费了 601 个小时。

- 客户喜欢了解进展。我有一个页面，记录了每月的工作总结，如下所示：

![](https://d33wubrfki0l68.cloudfront.net/71643f46a5e8a2d70d766f3ec7b380c344d8047c/6362b/img/4a3abd0bdbfa079bed495229ae7786105037568c.png)

这些页面与客户共享。

- 当开始每天的工作时，短期的待办列表很有用。

![](https://d33wubrfki0l68.cloudfront.net/f9649c1c901a565ca8d85f9f92a16e058b84cda7/e6c75/img/c145ac2f6f21c39228e8c1316e75180dd57fc5e1.png)

- 我甚至用 Notion 页面管理发票，使用“导出为 PDF”功能来生成发票的 PDF 版本。

## 待招聘的 Go 程序员

你公司需要额外的 Go 程序员吗？你可以[雇用我](https://blog.kowalczyk.info/goconsultantforhire.html)

## 额外的资源

针对问题，我提供了一些额外的评论：

- [Hacker News discussion](https://news.ycombinator.com/item?id=19589614)
- [/r/golang discussion](https://old.reddit.com/r/golang/comments/ba0lsm/lessons_learned_porting_50k_loc_from_java_to_go/)

其他资料：

- 如果你需要一个 NoSQL，JSON 文档数据库，可以试一下 [RavenDB](https://ravendb.net/)。它拥有完备的高级特性。
- 如果你使用 Go 编程，可以免费阅读 [Essential Go](https://www.programming-books.io/essential/go/) 这本编程书籍。
- 如果你对 Notion 感兴趣，我是 Notion 世界级的高级用户：
	- 我[逆向](https://blog.kowalczyk.info/article/88aee8f43620471aa9dbcad28368174c/how-i-reverse-engineered-notion-api.html)了 Notion API
	- 我写了一个 Notion API 的非官方的 [Go 库](https://github.com/kjk/notionapi)
	- 本网站的所有内容都是使用 Notion 编写，并使用[我定制化的工具链](https://github.com/kjk/notionapi)发布。
