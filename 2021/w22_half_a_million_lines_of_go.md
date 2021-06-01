# Half a million lines of Go

- 原文地址：https://blog.khanacademy.org/half-a-million-lines-of-go/
- 原文作者：`Kevin Dangoor`
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w22_half_a_million_lines_of_go.md

- 译者：[朱亚光](https://github.com/zhuyaguang)

Back in December 2019, I first [wrote about Goliath](https://blog.khanacademy.org/go-services-one-goliath-project/), Khan Academy’s project to migrate our backend from a Python 2 monolith to services written in Go, along with other changes needed to make that journey. I also wrote about how we’re [making this change as incrementally as can be](https://blog.khanacademy.org/incremental-rewrites-with-graphql/).

When we started Goliath, no one on the team knew Go beyond the experiments we ran to validate that Go would be a better choice for us than our other options. Today, all of our backend and full-stack engineers write Go, and our incremental delivery of Goliath has vaulted us over a big milestone: More than 500,000 lines of Go now running in production. This seemed like a good point to reflect on Go itself.

## Our engineers like Go

I asked for some open-ended responses from engineers about Go, and I heard feedback like “it’s easy to read and write,” and “I like Go more the more I work with it!”

One engineer had spent years in .NET land and valued exception-style error handling, which is quite different from Go’s error handling. In case you’re not familiar with the topic, [Go errors are values](https://blog.golang.org/errors-are-values) returned from functions that could have error conditions. Our former .NET engineer now says, “Being able to call a function that doesn’t return an error and know for sure that it must succeed is really nice.”

![](https://blog.khanacademy.org/wp-content/uploads/2021/05/gopher.png)

Another engineer cited Go’s [standard library documentation](https://pkg.go.dev/net/http). He loves “that it’s available via e.g. go doc io.Writer for internetless browsing. 5/5 best documentation, would read again.”

Renee French’s gopher mascot also won praise for bringing fun and cuteness to the language.

In general, Go tooling is fantastic. The compiler is quick, and having formatting being a part of the standard toolchain helps eliminate most conversations about formatting. Though I still see grumbles on the internet about Go modules, they work better than previous package management approaches in Go and, at this point, nicely overall in our experience. We’ve also had no trouble finding tools and libraries for things we needed to accomplish, like [gqlgen](https://github.com/99designs/gqlgen).

## We want generics, and Go is a bit more verbose otherwise

Most of the time, writing Go code without generic types is fine. _Most_ of the time, but there are plenty of times when we’ve been writing internal library code or even just working with slices when we felt their absence.

Lack of generics was the biggest complaint people had about Go. The engineers I surveyed appreciated the fact that the Go team has taken the time to make generics that fit Go, and we’re excited that the work is moving forward. At least we’ll only be a couple years into our use of Go when they’re released.

While porting Python code, an engineer noted that certain language constructs took more effort to write in Go, but that Go’s relatively fewer language features made the code more consistent and quicker to read. For one part of our system, we needed 2.7x lines of Go to handle the same features as our Python code, though a portion of this was due to replacing some function calls with cross-service queries.

Another engineer wanted to be able to make better use of higher-order functions, and the proposed [slices package](https://github.com/golang/go/issues/45955) looks like a nice addition along these lines. Ultimately, we’re looking to write a bit less code, and the options we get with generics will help with that.

## Performance and concurrency

Coming from Python (Python _2_, no less), we have found Go’s performance to be excellent. We are doing as close to a 1:1 port as possible from Python to Go, while still ending up with something Go-like at the end, rather than code that looks like Python-in-Go. In the process, we’re explicitly _not_ prioritizing performance work, unless there’s a real regression.

One engineer noted that certain bulk data changes used to produce around 100 Google Cloud Datastore contention warnings per hour in the Python version and has close to zero in the Go version, because of how much quicker it is at processing the data. We have an outlier case of a class containing 1,000 students that could take 28 seconds to load in Python, but only 4 seconds in Go.

Though we’re doing a straight port from largely single-threaded Python, we do make some uses of Go’s concurrency features already. One engineer noted that though channels were a much-highlighted feature of Go, we’ve used the features of the sync package far more than channels. It will be interesting to see if our preferences change over time.

## Go after 500,000 lines

To summarize:

-   Yep, Go is more verbose in general than Python…
-   But we like it! It’s fast, the tooling is solid, and it runs well in production

Our engineers come from a variety of programming backgrounds, so we certainly do have a diversity of opinion on Go vs. other languages. That said, Go is doing the job we “hired” it to do when we started Goliath, and we’re thankful for the team driving its continued evolution and the community that has built up around it!
