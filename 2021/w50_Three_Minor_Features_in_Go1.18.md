# Three Minor Features in Go 1.18

- 原文地址：https://go.dev/doc/tutorial/generics
- 原文作者：go.dev
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w49_Tutorial_Getting_started_with_generics.md
- 译者：[Jancd](https://github.com/Jancd)
- 校对：[](https://github.com/)

Everyone is excited that after [a decade or so](https://blog.carlmjohnson.net/post/google-go-the-good-the-bad-and-the-meh/) of devs asking for generics, the Go programming language is getting [generic types and functions](https://blog.carlmjohnson.net/post/google-go-the-good-the-bad-and-the-meh/) in Go 1.18 in Q1 2022. Generics are no doubt going to lead to a lot of experiments, some good, some bad, some just weird. Go 1.18 is also poised to lead to an increase in software reliability by [including fuzzing](https://go.dev/blog/fuzz-beta) as part of the standard testing package. But today, I want to look at some minor changes in Go 1.18 that might otherwise get lost in all the excitement around the marquee features.

## 1. Version control information included in the binary

In both my post on `//go:generate` and on `//go:embed`, one of the motivating examples was being able to embed information about the Git commit hash used to create a binary into it. In Go 1.18, this becomes an automatic part of the everyday `go` command.

The [`runtime/debug.BuildInfo`](https://pkg.go.dev/runtime/debug@master#BuildInfo) returned by [runtime/debug.ReadBuildInfo()](https://pkg.go.dev/runtime/debug@master#ReadBuildInfo) has been updated to include a new field `Settings []debug.BuildSetting`. `Settings` in turn are key-value pairs describing a binary. The commit hash is the value for the key `vcs.revision`, and `vcs.time` does what you would expect. There’s even `vcs.modified` to tell you if the build was “dirty” or “clean”.

Because reading this out of a slice of `debug.BuildSetting` is slightly convoluted, I wrote a small package called [versioninfo](https://github.com/carlmjohnson/versioninfo/) that sets `versioninfo.Revision`, `versioninfo.LastCommit`, and `versioninfo.DirtyBuild` by reading the debug info at startup, but [feel free to write your own helper library](https://blog.carlmjohnson.net/post/2020/avoid-dependencies/).

## 2. New `http.MaxBytesHandler` middleware

There’s not much to say about [http.MaxBytesHandler](https://pkg.go.dev/net/http@master#MaxBytesHandler), except to brag that [I wrote it](https://golang.org/cl/346569). Unlike flag.Func, I didn’t actually design it though. It’s just a five line function that had been requested and approved in the Go issues tracker, and I figured it was simple enough to write and submit between other tasks.

Here’s the docstring:

MaxBytesHandler returns a Handler that runs h with its ResponseWriter and Request.Body wrapped by a MaxBytesReader.

The use case for this is if you’re exposing your server directly to the internet, you may want to put a cap on how large of requests you’ll process to avoid denial of service attacks. This could already be done inside a handler with http.MaxBytesReader, but by enforcing a limit at the middleware level, now you can ensure that it’s not accidentally forgotten in some neglected corner of your web server.

## 3. Unreasonably effective `strings.Cut` function

Something I don’t have any connection to, whatsoever! I just think it’s neat. (Although the name is a little confusing.) [strings.Cut](https://pkg.go.dev/strings@master#Cut) is similar to [str.partition in Python](https://docs.python.org/3/library/stdtypes.html#str.partition). It cuts a string into two pieces at the first place it find the separator substring. As Russ Cox wrote [in the issue introducing the function](https://github.com/golang/go/issues/46336):

*The Unreasonable Effectiveness of Cut*
To attempt to cut off the bikeshedding this time, let me present data showing why Cut is worth adding.

Anecdotally, after the discussion on [#40135](https://github.com/golang/go/issues/40135) I copied the suggested implementation of Cut into every program that I wrote that could use it for a while, and that turned out to be just about every program I wrote that did anything with strings. That made me think there is something here.

To check that belief, I recently searched for uses of strings.Index, strings.IndexByte, or strings.IndexRune in the main repo and converted the ones that could use strings.Cut instead. Calling those all “Index” for the sake of discussion (any call with a constant sep should use Index anyway), there were:

- 311 Index calls outside examples and testdata.
- 20 should have been Contains
- 2 should have been 1 call to IndexAny
- 2 should have been 1 call to ContainsAny
- 1 should have been TrimPrefix
- 1 should have been HasSuffix

That leaves 285 calls. Of those, 221 were better written as Cut, leaving 64 that were not. That is, 77% of Index calls are more clearly written using Cut. That’s incredible!

A typical rewrite is to replace:

```go
  // The first equals separates the key from the value.
  eq := strings.IndexByte(rec, '=')
  if eq == -1 {
      return "", "", s, ErrHeader
  }
  k, v = rec[:eq], rec[eq+1:]
with

  // The first equals separates the key from the value.
  k, v, ok = strings.Cut(rec, "=")
  if !ok {
      return "", "", s, ErrHeader
  }
```

……

Looking in my public Go corpus, I found 88,230 calls to strings.SplitN. Of these, 77,176 (87%) use a fixed count 2. I expect that essentially all of them would be more clearly written using Cut.

It is also worth noting that something like Cut had been reinvented in two different packages as an unexported function: golang.org/x/mod/sumdb/note’s chop (7 uses) and net/url’s split (4 uses). Clearly, slicing out the separator is an incredibly common thing to do with the result of strings.Index.

The conversions described here can be viewed in [CL 322210](https://golang.org/cl/322210).

As noted in #40135, Cut is similar to Python’s str.partition(sep), which returns (before, sep, after) if sep is found and (str, "" , "") if not. The boolean result seems far more idiomatic in Go, and it was used directly as a boolean in over half the Cut calls I introduced in the main repo. That is, the fact that str.partition is useful in Python is added evidence for Cut, but we need not adopt the Pythonic signature. (The more idiomatic Go signature was first suggested by @nightlyone.)

Again, Cut is a single function that replaces and simplifies the overwhelming majority of the usage of four different standard library functions at once (Index, IndexByte, IndexRune, and SplitN), and it has been invented twice in the main repo. That seems above the bar for the standard library.

Anyhow, since reading about `strings.Cut`, I’ve been copying and pasting cut [into everything](https://www.reddit.com/r/golang/comments/rincmj/why_i_wrote_my_own_go_http_client/hoybhxi/?context=1) while I wait for it to come out, and it really is super-useful. Is it maybe even my most hotly anticipated feature in Go 1.18?

Nah, but it is a really nice minor feature.
