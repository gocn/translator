# 写了50万行 Go 代码后，我明白这些道理

_By Kevin Dangoor_

Back in December 2019, I first [wrote about Goliath](https://blog.khanacademy.org/go-services-one-goliath-project/), Khan Academy’s project to migrate our backend from a Python 2 monolith to services written in Go, along with other changes needed to make that journey. I also wrote about how we’re [making this change as incrementally as can be](https://blog.khanacademy.org/incremental-rewrites-with-graphql/).

早在2019年12月，我第一次写一个[关于 Goliath ](https://blog.khanacademy.org/go-services-one-goliath-project/)的可汗学院的项目，该项目的目的是将我们的后端从 python2 单体架构迁移到 Go 的微服务架构，以及在该过程中的一些[其他必要的改变](https://blog.khanacademy.org/incremental-rewrites-with-graphql/)。

When we started Goliath, no one on the team knew Go beyond the experiments we ran to validate that Go would be a better choice for us than our other options. Today, all of our backend and full-stack engineers write Go, and our incremental delivery of Goliath has vaulted us over a big milestone: More than 500,000 lines of Go now running in production. This seemed like a good point to reflect on Go itself.

当我们开始 Goliath 的时候，我们团队没有一个人知道Go，直到我们进行实验才发现相比于其他语言，Go 对我们来说是最好的选择。今天，我们所有的后端和全栈工程师都在写 Go ，Goliath 的增量交付让我们跨越了一个重大的里程碑：超过50万行 Go 代码运行在我们的生产环境中。这似乎是一个对 Go  本身进行反思的好时机。

## Our engineers like Go

我们的工程师喜欢 Go

I asked for some open-ended responses from engineers about Go, and I heard feedback like “it’s easy to read and write,” and “I like Go more the more I work with it!”

我向 Go 工程师询问了一些关于 Go 的开发式回答，我听到的反馈是“读起来和写起来都很容易”和“我越用Go 就越喜欢它!”。

One engineer had spent years in .NET land and valued exception-style error handling, which is quite different from Go’s error handling. In case you’re not familiar with the topic, [Go errors are values](https://blog.golang.org/errors-are-values) returned from functions that could have error conditions. Our former .NET engineer now says, “Being able to call a function that doesn’t return an error and know for sure that it must succeed is really nice.”

一位工程师在 .NET 领域工作多年，推崇exception风格的错误处理，这与Go的错误处理非常不同。如果你对这方面不熟悉，你可以理解为 [Go 的错误](https://blog.golang.org/errors-are-values)都是存在错误条件的函数的返回值。我们的前.NET工程师现在说，“能够调用一个不返回错误的函数，并且确信它一定会成功，这真的很好。

![](https://blog.khanacademy.org/wp-content/uploads/2021/05/gopher.png)

Another engineer cited Go’s [standard library documentation](https://pkg.go.dev/net/http). He loves “that it’s available via e.g. go doc io.Writer for internetless browsing. 5/5 best documentation, would read again.”

另外一个工程师引用了 Go 的[标准库文档](https://pkg.go.dev/net/http)。他喜欢 可以通过 `go doc io.Writer`等方式获得离线浏览文档体验。100%最好的文档，可以反复阅读。

Renee French’s gopher mascot also won praise for bringing fun and cuteness to the language.

Renee French 的吉祥物地鼠也因给这门语言带来乐趣和可爱而获得赞誉。

In general, Go tooling is fantastic. The compiler is quick, and having formatting being a part of the standard toolchain helps eliminate most conversations about formatting. Though I still see grumbles on the internet about Go modules, they work better than previous package management approaches in Go and, at this point, nicely overall in our experience. We’ve also had no trouble finding tools and libraries for things we needed to accomplish, like [gqlgen](https://github.com/99designs/gqlgen).

总的来说，Go 工具很棒。编译速度很快，并且将格式化作为标准工具链的一部分，这有助于消除大多数关于格式化的争议。尽管我仍在互联网上看到关于  Go module 的抱怨，但是它比以前的 Go 包管理工具要好很多，关于这包管理一块，从我们的经验来看整体上还算不错。我们还可以毫不费力找到所需的工具和库，比如 [gqlgen](https://github.com/99designs/gqlgen)。

## We want generics, and Go is a bit more verbose otherwise

 我们想要泛型，不然的话 Go 有点冗长

Most of the time, writing Go code without generic types is fine. _Most_ of the time, but there are plenty of times when we’ve been writing internal library code or even just working with slices when we felt their absence.

大多数时候，没有泛型写 Go 代码是可以的。大多数时候，但也有很多时候，当我们在写内部库代码或者当我们在使用 slices 的时候，我们会感受到泛型的缺失。

Lack of generics was the biggest complaint people had about Go. The engineers I surveyed appreciated the fact that the Go team has taken the time to make generics that fit Go, and we’re excited that the work is moving forward. At least we’ll only be a couple years into our use of Go when they’re released.

缺少泛型是人们对 Go 的最大抱怨。我调查过的工程师对于 Go 团队花时间来开发适合 Go 的泛型这一事实，非常欣赏。我们对这项工作的进展也感到兴奋。等到 Go 泛型正式发布的时候，我们至少还得花几年功夫去使用。

While porting Python code, an engineer noted that certain language constructs took more effort to write in Go, but that Go’s relatively fewer language features made the code more consistent and quicker to read. For one part of our system, we needed 2.7x lines of Go to handle the same features as our Python code, though a portion of this was due to replacing some function calls with cross-service queries.

在移植 python 代码时，一位工程师指出，对于特定的语言结构使用 Go 语言花费更多的努力，但是 Go 相对较少的语言特性使得代码更加一致，阅读速度更快。对于我们系统的某一部分，和 python 代码相比，我们需要2.7倍的 Go 代码来处理同样的特性。虽然这部分是由于用跨服务查询替换了一些函数调用。

Another engineer wanted to be able to make better use of higher-order functions, and the proposed [slices package](https://github.com/golang/go/issues/45955) looks like a nice addition along these lines. Ultimately, we’re looking to write a bit less code, and the options we get with generics will help with that.

另外一个工程师希望能够更好地利用高阶函数，这个 [slices 包](https://github.com/golang/go/issues/45955)的提议是对这方面很好的补充。最终，我们希望能少写一点代码，而选择泛型将对此有所帮助。

## Performance and concurrency

性能和并发

Coming from Python (Python _2_, no less), we have found Go’s performance to be excellent. We are doing as close to a 1:1 port as possible from Python to Go, while still ending up with something Go-like at the end, rather than code that looks like Python-in-Go. In the process, we’re explicitly _not_ prioritizing performance work, unless there’s a real regression.

从python（至少是python2）转过来，我们发现 Go 的性能表现非常出色。我们尽可能按照1:1的方式将python移植到 Go，直到最后会得到类似 Go 的东西，而不是像  Python-in-Go 那样的代码。在这个过程中，我们没有明确地以性能优先，除非有真正性能瓶颈。

One engineer noted that certain bulk data changes used to produce around 100 Google Cloud Datastore contention warnings per hour in the Python version and has close to zero in the Go version, because of how much quicker it is at processing the data. We have an outlier case of a class containing 1,000 students that could take 28 seconds to load in Python, but only 4 seconds in Go.

一位工程师指出，某些批量数据更改在 python 版本中每小时会产生大约100多个谷歌云数据存储争用告警，而在 Go 版本中趋近于0，因为 Go 的处理数据速度非常快。我们有一个异常的例子，一个包含1000个学生的类，在 python 中加载需要28秒，而在 Go 中只需要4秒。

Though we’re doing a straight port from largely single-threaded Python, we do make some uses of Go’s concurrency features already. One engineer noted that though channels were a much-highlighted feature of Go, we’ve used the features of the sync package far more than channels. It will be interesting to see if our preferences change over time.

虽然我们是从主要为单线程的python 直接移植过来，但是我们已经使用了一些 Go 的并发特性。一位工程师指出，虽然通道是 Go 中的一个非常突出的特性，但是我们使用 sync 包的功能远远多于通道。看看我们的偏好是不是随着时间推移而改变，这会非常有意思。

## Go after 500,000 lines

写完 50万行 Go 代码后

To summarize:

总结：

-   Yep, Go is more verbose in general than Python…
-   是的，Go 通常比 python 更冗长 ...
-   But we like it! It’s fast, the tooling is solid, and it runs well in production
-   但是我们喜欢它，它速度快，工具稳定，而且在生产中运行良好

Our engineers come from a variety of programming backgrounds, so we certainly do have a diversity of opinion on Go vs. other languages. That said, Go is doing the job we “hired” it to do when we started Goliath, and we’re thankful for the team driving its continued evolution and the community that has built up around it!

我们的工程师来自不同的编程背景，所以我们对于 Go 和其他语言有着不同的看法。也就是说，当我们启动一个项目时，Go 能够胜任我们赋予它的工作。我们很感谢 Go 团队能够推动它的持续发展，并且围绕着它构建社区。