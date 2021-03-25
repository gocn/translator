# Generics in Go
- 原文地址：https://bitfieldconsulting.com/golang/generics
- 原文作者：John Arundel
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w13_Generics_in_Go.md
- 译者：[haoheipi](https://github.com/haoheipi)
- 校对：[](https://github.com/)

Generics what now? This friendly, down-to-earth tutorial explains what generic functions and types are, why we need them, how they work in Go, and where we can use them. It's easy and fun, so let's dance!

> John Arundel is a Go teacher and consultant, and the author of 'For the Love of Go', a series of downloadable ebooks about modern software engineering in Go for complete beginners.
![](../static/images/w13_Generics_in_Go/Covers.png)
《For the Love of Go》 is a series of fun, easy-to-follow ebooks introducing software engineering in Go.

## What are generics?

As you know, Go is a *typed* language, meaning that every variable and value in your program has some specific type, like `int` or `string`. When we write functions, we need to specify the type of their parameters in what's called the *function signature*, like this:

```go
func PrintString(s string) {
```

Here, the parameter `s` is of type `string`. We can imagine writing similar versions of this function which take an `int`, a `float64`, an arbitrary struct type, and so on. But that would be inconvenient for more than a handful of specific types, and though we can sometimes use *interfaces* to solve this problem (as described in the [map[string]interface tutorial](https://bitfieldconsulting.com/golang/map-string-interface), for example), that approach has many limitations.

## Generic functions in Go

Instead, we would like to declare a *generic function* `PrintAnything`, which takes an argument of *any* arbitrary type (let's call it `T`), and does something with it.

Here's what that looks like:

```go
func PrintAnything[T any](thing T) {
```

Simple, right? The `any` indicates that `T` can be any type.

How do we call such a function? Equally simply:

```go
PrintAnything("Hello!")
```

> (Note:The support for generics in Go that I describe here isn't yet released, but it's [being implemented now](https://github.com/golang/go/issues/43651), for release very soon. Right now you can play with it in the [generics-enabled version of the Go Playground](https://go2goplay.golang.org/), or you can use the experimental [go2go tool](https://go.googlesource.com/go/+/refs/heads/dev.go2go/README.go2go.md) to try Go's generics support in your own programs.)

## Constraints

It's pretty easy to implement the `PrintAnything` function, because the `fmt` library can print anything anyway. Suppose we wanted to write our own version of something like `strings.Join`, which takes a slice of T, and returns a single string that joins them all together. Let's try:

```go
// I have a bad feeling about this.
func Join[T any](things []T) (result string) {
    for _, v := range things {
        result += v.String()
    }
    return result
}
```

We've created a generic function `Join()` which takes, for an arbitrary type T, a parameter which is a slice of T. Great, but now we run into a problem:

```go
output := Join([]string{"a", "b", "c"})
// v.String undefined (type bound for T has no method String)
```

Thing is, inside the `Join()` function, we want to call `.String()` on each slice element `v` to turn it into a `string`. But Go needs to be able to check in advance that type T has a `String()` method, and since it doesn't know what T is, it can't do that!

What we need to do is *constrain* the type T slightly. Instead of accepting literally any T, we're really only interested in types which have a `String()` method. Any such type will be an acceptable input to our `Join()` function, so how do we express that constraint in Go? We use an *interface*:

```go
type Stringer interface {
    String() string
}
```

This specifies that a given type has a `String()` method. So now we can apply this constraint to the type of our generic function:

```go
func Join[T Stringer] ...
```

Since `Stringer` guarantees that any value of type T will have a `String()` method, Go will now happily let us call it inside the function. But if you try to call the `Join()` function with a slice of some type that *doesn't* satisfy `Stringer` (for example `int`), Go will complain:

```go
result := Join([]int{1, 2, 3})
// int does not satisfy Stringer (missing method String)
```

## The comparable constraint

Constraints based on method sets, like `Stringer`, are useful, but what if we want to do something with our generic input that doesn't involve calling a method?

For example, suppose we want to write an `Equal` function which takes two parameters of type T, and return `true` if they are equal, or `false` otherwise. Let's have a go:

```go
// This won't work.
func Equal[T any](a, b T) bool {
    return a == b
}

fmt.Println(Equal(1, 1))
// cannot compare a == b (operator == not defined for T)
```

This is the same kind of issue as we had in `Join()` with the `String()` method, but since we're not *calling* a method now, we can't use a constraint based on a method set. Instead, we need to constrain T to only types that work with the `==` or `!=` operators, which are known as *comparable* types. Fortunately there's a straightforward way to specify this: use the built-in comparable constraint, instead of `any`.

```go
func Equal[T comparable] ...
```

## The constraints package

Just to be difficult, suppose we want to do something with values of T which isn't either comparing them or calling methods on them. For example, suppose we want to write a `Max()` function for a generic type T which takes a slice of T and returns the element with the highest value. We might try something like this:

```go
// Nope.
func Max[T any](input []T) (max T) {
    for _, v := range input {
        if v > max {
            max = v
        }
    }
    return max
}
```

I'm not feeling very optimistic about this, but let's see what happens:

```go
fmt.Println(Max([]int{1, 2, 3}))
// cannot compare v > max (operator > not defined for T)
```

Again, Go can't prove ahead of time that the type T will work with the `>` operator (that is to say, that T is *ordered*). How can we fix this? We could simply list every possible allowed type in a constraint, like this (known as a *type list*):

```go
type Ordered interface {
    type int, int8, int16, int32, int64,
        uint, uint8, uint16, uint32, uint64, uintptr,
        float32, float64,
        string
}
```

Fortunately for your keyboard, this and other useful `constraints` are already defined for us in the standard library's constraints package, so we can import that and use it like this:

```go
func Max[T constraints.Ordered] ...
```

Problem solved!

## Generic types

So far, so cool. We know how to write functions that can take arguments of any type. But what if we want to create a *type* that can contain any type? For example, a 'slice of anything' type. That turns out to be very easy:

```go
type Bunch[T any] []T
```

We're saying that for any given type T, a `Bunch[T]` is a slice of values of type T. For example, a `Bunch[int]` is a slice of `int`. We can create values of that type in the normal way:

```go
x := Bunch[int]{1, 2, 3}
```

Just as you'd expect, we can write generic functions which take generic types:

```go
func PrintBunch[T any](b Bunch[T]) {
```

Methods, too:

```go
func (b Bunch[T]) Print() {
```

We can also apply constraints to generic types:

```go
type StringableBunch[T Stringer] []T
```

Video: [Code Club: Generics](https://youtu.be/x3KULj5406g?list=PLEcwzBXTPUE_YQR7R0BRtHBYJ0LN3Y0i3)

## Golang generics playground

So that you can play with the current implementation of the generics proposal (for example to try the code samples in this tutorial), the Go team have provided a generics-enabled version of the Go Playground here:

[Golang generics playground](https://go2goplay.golang.org/)

It works exactly the same way as the normal [Go playground](https://play.golang.org/) we know and love, except that it supports the generic syntax described here. Because it's not possible to run all Go code in the playground (for example, code that makes network calls or accesses the filesystem), you can also try out the [go2go tool](https://go.googlesource.com/go/+/refs/heads/dev.go2go/README.go2go.md), which translates code using generics to code which compiles with the current version of Go.

## Questions

### What is the Go generics proposal?

You can read the complete draft design document here:

- [Type Parameters - Draft Design](https://go.googlesource.com/proposal/+/master/design/go2draft-type-parameters.md)

### Will Golang get generics?

Yes. The current proposal for generics support in Go, as outlined in this tutorial, was announced in June 2020 in a blog post: [The Next Step](https://blog.golang.org/generics-next-step) for Generics, and the [Github issue](https://github.com/golang/go/issues/43651) to add generics has now been accepted in the form I describe here.

The [Go blog](https://blog.golang.org/generics-proposal) says that generics support may be included in a beta version of Go 1.18, which will be available in December 2021.

Until then you can use the [Generics Playground](https://go2goplay.golang.org/) to experiment with it and try out the examples here.

### Generics vs interfaces: are there alternatives to generics?

As I mentioned in my [map[string]interface tutorial](https://bitfieldconsulting.com/golang/map-string-interface), we can already write Go code that handles values of any type, without using generic functions or types, by means of *interfaces*. However, if you want to write a library that implements things like collections of arbitrary types, using a generic type is much simpler and more convenient than using an interface.

### What's the deal with any?

When defining generic functions or types, the input type must have a *constraint*. Type constraints can be interfaces (such as `Stringer`), type lists (such as `constraints.Ordered`), or the keyword `comparable`. But what if you really want no constraint at all; that is to say, literally *any* type `T`?

The logical way to express this is to use `interface{} ` (the interface that says nothing at all about a type's method set). But since this is such a common constraint, the predeclared name `any` is provided as an alias for `interface{}`. You can only use this name in type constraints, so `any` is not a general synonym for `interface{}`.

### Can I use code generation instead of generics?

The 'code generator' approach has been the other traditional way of dealing with such problems before the advent of generics in Go. Essentially, it involves using the [go generate tool](https://blog.golang.org/generate) to produce Go code for each of the specific types that you need to handle in your library.

While this works, it's awkward to use, limited in its flexibility, and requires an extra build step. While code generation is still useful for some things, it's nice that we no longer have to use it to simulate generic functions and types in Go.

### What are contracts?

An earlier [draft design](https://go.googlesource.com/proposal/+/master/design/go2draft-contracts.md) for generics in Go used a similar syntax to what we have today, but it implemented type constraints using a new keyword `contract`, instead of the existing `interface`. This was not popular for various reasons, and is now superseded.

## Further reading

- [A Proposal for Adding Generics](https://blog.golang.org/generics-proposal)
- [The Next Step for Generics](https://blog.golang.org/generics-next-step)
- [Why Generics?](https://blog.golang.org/why-generics)
- [Go Generics: Applying the Draft Design to a Real-World Use Case](https://secrethub.io/blog/go-generics/)
- [Experimenting with Generics in Go](https://medium.com/swlh/experimenting-with-generics-in-go-39ffa155d6a1)
 


