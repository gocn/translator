# Generic functions on slices with Go type parameters

原文地址：https://eli.thegreenplace.net/2021/generic-functions-on-slices-with-go-type-parameters/
原文作者： Eli Bendersky
本文永久链接：https://github.com/gocn/translator/blob/master/2021/w10_Generic_functions_on_slices_with_Go_type_parameters.md
译者：Jancd
校对：

After many years in the making, Go's generics proposal has been accepted this week! This is great news for the Go community; the earliest attempt to add generics to Go was in 2010, before the release of Go 1.0.

I believe the current proposal strikes a good balance between expressivity and comprehensibility. It should allow Go programmers to express 95% of the things generics were most wanted for, while making it hard or impossible to write inscrutable code for which generics have a bad name in other languages. As it stands now, the Go team is working on getting generics into the language in 1.18 (beta will be available in Dec 2021), though these timelines aren't final.

Last month I wrote a post about why writing generic functions on slices in Go is hard. To celebrate the proposal acceptance milestone, here's a post that shows how this will become a non-issue once generics land in Go.

## Generic functions for slices?

Let's start by defining the problem; Ian Lance Taylor has an excellent [talk and blog post called "Why Generics?"](https://blog.golang.org/why-generics) on the topic, and I highly recommend you watch/read that first.

I'll be using Ian's function to reverse slices as a motivating example, and will move quickly through the topics that are already covered in that talk.

Suppose we want to write a function to reverse a slice in Go; we can start with a concrete function to reverse a slice of ints :

```go
func ReverseInts(s []int) {
  first := 0
  last := len(s) - 1
  for first < last {
    s[first], s[last] = s[last], s[first]
    first++
    last--
  }
}
```

How about reversing a slice of strings?

```go
func ReverseStrings(s []string) {
  first := 0
  last := len(s) - 1
  for first < last {
    s[first], s[last] = s[last], s[first]
    first++
    last--
  }
}
```

Well, it looks exactly like the previous function, with a simple `int->string` substitution in the type. Can't we write this function only once?

Go permits polymorphism via interfaces; let's try to write a "generic" function to reverse a slice of any type:

```go
func ReverseAnything(s []interface{}) {
  first := 0
  last := len(s) - 1
  for first < last {
    s[first], s[last] = s[last], s[first]
    first++
    last--
  }
}
```

We can call it as follows, and it works as expected:

```go
iints := []interface{}{2, 3, 4, 5}
ReverseAnything(iints)

istrings := []interface{}{"joe", "mike", "hello"}
ReverseAnything(istrings)
```

So wait, is this it? Go has had generics all along? Not quite. While `ReverseAnything` will dutifilly reverse a slice of interface{}, we don't typically hold data in such slices in Go. We could do it, theoretically, but that would forego much of Go's static typing, relying on (runtime) type assertions at every turn [1]

It would all work great if we could just pass our `[]int` into `ReverseAnything`; but that's not possible, for a [variety of good reasons](https://eli.thegreenplace.net/2021/go-internals-invariance-and-memory-layout-of-slices/).

We could also copy our `[]int` into a `[]interface{}` prior to reversing it, but this carries significant disadvantages:

 1. Much more code: instead of reversing a slice, we have to copy our slice into a `[]interface{}`, then call the reverse function, then copy the result back into a `[]int`.
 2. Efficiency hit - lots of copying data arround and allocations of new slices, whereas a simple call to `ReverseInts(intslice)` is a single loop with no unnecessary copies and zero allocations.

There are other approaches we could take, like [code generation](https://blog.golang.org/generate), but these have different issues that make them cumbersome.

This is where the [type parameters proposal](https://go.googlesource.com/proposal/+/refs/heads/master/design/go2draft-type-parameters.md) comes in.

## Writing generic code with type parameters

Using the type parameters proposal, writing a generic slice reversal function is simple:

```go
func ReverseSlice[T any](s []T) {
  first := 0
  last := len(s) - 1
  for first < last {
    s[first], s[last] = s[last], s[first]
    first++
    last--
  }
}
```

The square bracket region following the function's name defines a type parameter for the function's use. `[T any]` means that T is a type parameter that can be *any type*. Not surprisingly, the body of the function remains exactly the same as in our non-generic versions.

Here's how we use it:

```go
s := []int{2, 4, 8, 11}
ReverseSlice(s)

ss := []string{"joe", "mike", "hello"}
ReverseSlice(ss)
```

Due to *type inference*, we don't have to specify the type parameters when we invoke `ReverseSlice` in this case (and in the vast majority of other cases, actually); it "just works".

I won't go into details about how the compiler accomplishes this, because the implementation details are still in flux. Moreover, different Go compilers may choose to implement this differently, and that's fine.

I will highlight one important aspect of the proposal, however: **values of type parameters are not boxed**. This has significant implications for efficiency! It means that whatever overhead generic functions add (in terms of run time and memory footprint), it's likely to be a constant overhead that's not a function of the slice's size.

## More examples of generic slice functions

Type parameters finally allow programmers to write generic functions like `map`, `reduce` and `filter`! Whether you think such functions are a good stylistic fit to Go or not, they are a good demonstration of the capabilities of this new functionality in Go. Let's take `map`, for example:

```go
func Map[T, U any](s []T, f func(T) U) []U {
  r := make([]U, len(s))
  for i, v := range s {
    r[i] = f(v)
  }
  return r
}
```

It's parameterized by two types - one for the slice element, one for the returned slice element. Here's a hypothetical usage scenario:

```go
s := []int{2, 4, 8, 11}
ds := Map(s, func(i int) string {return strconv.Itoa(2*i)})
```

The mapping function takes an `int` and returns a `string`. This is enough for Go's type inference to understand that `T` is `int` and `U` is `string` in the call to `Map`, and we don't have to specify any types explicitly. ds is inferred to be `[]string`.

Naturally, we could also use `Map` with existing functions from the standard library, e.g.:

```go
names := []string{"joe", "mike", "sue"}
namesUpper := Map(names, strings.ToUpper)
```

Here's Filter:

```go
func Filter[T any](s []T, f func(T) bool) []T {
  var r []T
  for _, v := range s {
    if f(v) {
      r = append(r, v)
    }
  }
  return r
}
```

We would use it as follows:

```go
evens := Filter(s, func(i int) bool {return i % 2 == 0})
```

Finally, here's Reduce:

```go
func Reduce[T, U any](s []T, init U, f func(U, T) U) U {
  r := init
  for _, v := range s {
    r = f(r, v)
  }
  return r
}
```

And sample usage:

```go
product := Reduce(s, 1, func(a, b int) int {return a*b})
```

## Trying type parameters today

Even though generics will not be available in Go before 1.18, you can play with them today and try all the code I pasted in this post (and whatever else strikes your fancy). There are a couple of ways.

The easiest way to try small snippets is on the [go2go version of the Go Playground](https://go2goplay.golang.org/). It's kept reasonably in sync with the type parameters development branch of the Go toolchain.

To be on the bleeding edge and/or to write more substantial pieces of code, you can:

1. Clone the Go repository (following [these instructions](https://golang.org/doc/contribute.html#checkout_go)).
2. Check out the dev.go2go branch.
3. Build the toolchain (also detailed in the link in step 1)
4. Use go tool go2go to run code samples.

In the [source repository accompanying this post](https://github.com/eliben/code-for-blog/tree/master/2021/go-generic-slice), you'll find a simple bash script that set ups env vars properly to do step 4. Feel free to use it for your own needs.

Once you've cloned the repo and checked out the dev.go2go branch, take a look at the directory src/cmd/go2go/testdata/go2path/src. It contains many examples of generic Go code using type parameters that are very interesting to study.