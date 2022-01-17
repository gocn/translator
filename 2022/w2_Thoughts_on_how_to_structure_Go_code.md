# 关于 Go 代码结构的思考
***
- 原文地址：https://changelog.com/posts/on-go-application-structure
- 原文作者：Jon Calhoun
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w2_Thoughts_on_how_to_structure_Go_code.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[]()
***
应用程序结构复杂。

良好的应用程序结构可提升开发人员体验。它可以帮助您隔离他们正在处理的内容，而无需将整个代码库放在脑海中。一个结构良好的应用程序可以通过解耦组件和容易编写有用的测试来帮助防止错误。

结构不佳的应用程序可能会适得其反；它会使测试变得更难，并难以查找相关代码。它还会引入不必要的复杂性和冗余，从而拖累您的开发速度。

最后一点很重要——使用比实际所需复杂得多的结构是弊大于利的。

我在这里写的东西对任何人来说可能都不是新鲜事。程序员很早就被教导组织代码的重要性。无论是命名变量和函数，还是命名和组织文件，这几乎是每门编程课程的早期主题。

所有这些都引出了一个问题—— 为什么很难弄清楚如何结构化 Go 代码?

### 按环境组织

在过去的 Go Time 问答集中，我们被问及如何构建 Go 应用程序，Peter Bourgon 回答如下：

> 很多语言对所有项目结构的约定大致相同，对于相同类型的项目......就像，如果你在 Ruby 中做一个 Web 服务，你会有这个布局，并且这些包将以您正在使用的架构模式命名。例如，MVC、控制器等。但在 Go 中，这并不是我们真正要做的。我们的包和项目结构基本上反映了我们正在实现的内容。不是我们使用的模式，不是脚手架，而是我们正在从事的项目领域中的特定类型和实体。
> 
> **因此，根据定义，它总是因项目而异**。对一个项目有意义的事情可能对另一个是没有意义的。这并不是说这是做事的唯一方式，但这是我们倾向于做的事情......所以是的，这是没有答案的，毋庸置疑的是在语言中使用惯用语会让很多人感到非常困惑，而且结果可能也会说明是错误的选择……我不知道，但我认为这是重点。
> 
> [Peter Bourgon](https://twitter.com/peterbourgon) 在 [Go Time #147](https://changelog.com/gotime/147#transcript-185)上提到。

大体上，大多数成功的 Go 应用程序的结构都不会是从别的项目照搬的。也就是说，我们不能采用通用文件夹结构并将其复制到新应用程序并期望它能够工作，因为新应用程序很可能有一组独特的环境可供使用。

开始的最好方法是考虑应用程序的环境，而不是寻找要复制的模板。为了帮助您理解我的意思，让我们尝试了解如何构建用于托管我的 Go 课程的 Web 应用程序。

![A screenshot of Jon's Go courses dashboard](https://github.com/gocn/translator/raw/master/static/images/2022/w2_Thoughts_on_how_to_structure_Go_code/courses-app-screenshot.png)

*_背景信息：我的 Go 课程应用程序是一个网站，学生可以在其中注册课程并查看课程中的个别课程。大多数课程都有视频组件、课程中使用的代码链接以及其他相关信息。如果您曾经使用过任何视频课程网站，您应该对它的外观有一个大致的了解，但如果您想进一步挖掘，您可以免费注册 [Gophercises](https://gophercises.com/) _*

在这一点上，我已经非常熟悉应用程序的需求，但我将尝试引导您完成我最初开始创建应用程序时的思考过程，因为这是您经常在开始时的状态。

开始时，我考虑了两个主要环境：

1.  学生
2.  管理员/教师

学生环境是大多数人所熟悉的。在这种情况下，用户登录帐户，查看包含他们有权访问的课程的仪表板，然后可以导航到各个课程。

管理员环境有点不同，大多数人不会看到它。作为管理员，我们不太担心课程的消费，而是更关心管理它们。我们需要能够为课程添加新课程、更新现有课程的视频等等。除了能够管理课程之外，管理员环境还需要管理用户、购买和退款。

为了创建这种分离环境，我的代码仓库将从两个包开始：

```
admin/
  ... (some go files here)
student/
  ... (some go files here)
```

通过分离这两个包，我能够在每个环境中以不同的方式定义实体。例如，`Lesson` 从学生 a 的角度来看，主要由资源的 URL 组成，并且它具有特定于用户的信息，例如 `CompletedAt` 代表该特定用户何时/是否完成课程的字段。

```
package student

type Lesson struct {
  Name         string 
  Video        string 
                      
  SourceCode   string 
  CompletedAt  *time.Time 
                         
}
```

同时，管理员的 `Lesson` 类型没有 `CompletedAt` 字段，因为在这种情况下这没有意义。该信息仅与登录用户查看课程相关，与管理课程内容的管理员无关。

相反，管理员的  `Lesson` 类型将提供对诸如 `Requirement` 之类的字段用于确定用户是否有权访问内容。其他字段看起来也会有些不同；`Video`  字段可能不是视频的 URL，而是有关视频托管位置的信息，因为这是管理员更新内容的方式。

```
package admin

type Lesson struct {
  Name string
  
  Video struct {
    Provider string 
    ExternalID string
  }
  
  SourceCode struct {
    Provider string 
    Repo     string 
    Branch   string 
  }
 
  Requirement string
}
```

我选择这样组织是因为我相信这两种情况的差异足以证明分离是合理的，但我对其足以适用于任何进一步的组织表示质疑。

我可以用不同的方式组织这段代码吗？绝对可以的！

我可能会改变结构的一种方法是进一步分离它。例如，`admin` 包的一些代码与管理用户有关，而其他代码则与管理课程有关。将其分为两个也会很容易。或者，我可以提取所有与身份验证相关的代码——注册、更改密码等，并将其放入一个 `auth` 包中。

与其想太多，不如选择一些看起来相当合适的方式并根据需要进行调整更有用。

### 包作为层

另一种分解应用程序的方法是依赖关系。Ben Johnson 在 [gobeyond.dev](https://www.gobeyond.dev/) 上对此进行了很好的讨论，特别是在文章 [Packages as layers, not groups](https://www.gobeyond.dev/packages-as-layers/) 中。这个概念与 Kat Zien 在 GopherCon 演讲“你如何构建你的 Go 应用程序”中提到的[六边形架构](https://www.youtube.com/watch?v=oL6JBUk6tj0&t=1614s) 非常相似。

在更深层次上，我们的想法是我们有一个核心域，在其中定义我们的资源和用来与它们交互的服务。

```
package app

type Lesson struct {
  ID string
  Name string
  
}

type LessonStore interface {
  Create(*Lesson) error
  QueryByPermissions(...Permission) ([]Lesson, error)
  
}
```

使用类似  `Lesson` 类型和类似 `LessonStore` 接口，我们可以编写一个完整的应用程序。没有实现 `LessonStore` 我们就无法运行我们的程序，但是我们可以编写所有的核心逻辑而不用担心它是如何实现的。

当我们准备好实现 `LessonStore` 接口时，我们的应用程序就添加一个新层。在这种情况下，它可能是一个 `sql` 包的形式。

```
package sql

type LessonStore struct {
  db *sql.DB
}

func Create(l *Lesson) error {
  
}

func QueryByPermissions(perms ...Permission) ([]Lesson, error) {
  
}
```

_如果您想了解有关此策略的更多信息，我强烈建议您查看 Ben 在[https://www.gobeyond.dev/](https://www.gobeyond.dev/) 上的文章。_

逐层打包的方法似乎与我在 Go 课程中选择的方法大不相同，但实际上混合适用这些策略比最开始的方法要容易得多。例如，如果我们将 `admin`  和 `student` 视为定义资源和服务的域，我们可以通过逐层封装的方法来实现这些服务。下面是一个使用 `admin` 包和实现了 `admin.LessonStore` 的 `sql` 包.

```
package admin

type Lesson struct {
  
}

type LessonStore interface {
  Create(*Lesson) error
  
}
```

```
package sql

import "github.com/joncalhoun/my-app/admin"

type AdminLessonStore struct { ... }

func (ls *AdminLessonStore) Create(lesson *admin.Lesson) error { ... }
```

这是应用程序的正确选择吗？我不知道。

使用这样的接口确实可以更轻松地测试更小的代码片段，但这只有在它提供真正的好处时才重要。否则，我们最终写完了接口、解耦了代码、创建了新包都是无用功，基本可以看做，我们的忙碌都是自己造成的。

### 唯一错误的决定是没有决定

除了这些结构之外，还有无数其他有意义的方式来构建（或不构建）代码，这取决于环境。我已经在多个项目中尝试过使用扁平结构——一个单独的包——但我仍然对它的效果感到震惊。当我第一次开始编写 Go 代码时，我几乎完全使用 MVC。这不仅比整个社区可能让你相信的效果更好，而且它让我克服了由于不知道如何构建我的应用程序而导致的决策瘫痪。

在 Q&A Go Time 的同一期中，我们被问及如何构建 Go 代码，Mat Ryer 阐明了没有固定的代码结构方式的好处：

> 我认为这可能是非常解放的，也是说，没有确切的方法可以做到这一点，也意味着你无法真正做错了。这完全适用于你的情况。
> 
> [Mat Ryer](https://twitter.com/matryer) 在 [Go Time #147](https://changelog.com/gotime/147#transcript-186) 提到。

如今我有丰富的 Go 使用经验，我完全同意 Mat 的观点。这种方式来决定每个应用程序适合的哪些结构是解放式的。我喜欢没有固定的做事方式，也没有真正的错误方式。尽管现在有这种感觉，但我还记得在我经验不足的时候没有具体的例子可以用时感到非常沮丧。

事实是，如果没有一些经验，几乎不可能决定哪种结构适合您的情况，但这又强迫我们在获得任何经验之前做出决定。这是我们入门之前的一个两难情形。

在这种情况下我没有放弃，而是选择了我所知道的结构——MVC。这让我可以编写代码，让某些东西正常工作，并从这些错误中吸取教训。随着时间的推移，我开始了解构建代码的其他方式，我的应用程序越来越不像 MVC，但这是一个非常渐进的过程。我怀疑如果我强迫自己立即获知正确的应用程序结构，我根本不会成功。只在经历了很大的挫折之后，我才会成功。

毫无疑问，MVC 永远不会像为项目量身定制的应用程序结构那样清晰。同样，对于几乎没有构建 Go 代码经验的人来说，为项目发现理想的应用程序结构并不是一个现实的目标。这需要练习、试验和重构才能做到正确。MVC 简单易懂。当我们没有足够的经验或背景来想出更好的东西时，这是一个合理的起点。

### 总结

正如我在本文开头所说，良好的应用程序结构旨在改善开发人员体验。它旨在帮助您以对您有意义的方式组织代码。这并不意味着让新来者陷入困境并不知道如何进行下去。

如果您发现自己陷入困境并且不确定如何继续，请问下自己怎样会更有效率 - 仍然陷入困境，或者选择任何一个应用程序结构并尝试一下？

使用前者，什么都做不了。使用后者，即使你做错了，你也可以从经验中吸取教训，下次做得更好。这听起来都比从不开始要好得多。

___

