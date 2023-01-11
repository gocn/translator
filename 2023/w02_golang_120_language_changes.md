# What’s New in Go 1.20, Part I: Language Changes

- 原文地址：<https://blog.carlmjohnson.net/post/2023/golang-120-language-changes/>
- 原文作者：Carl M. Johnson
- 本文永久链接：<https://github.com/gocn/translator/blob/master/2023/w02_golang_120_language_changes.md>
- 译者：[pseudoyu](https://github.com/pseudoyu)
- 校对：[小超人](https://github.com/focozz)

Well, it’s that time once again. It’s time for a new release of the Go programming language. Go 1.18 in Q1 of 2022 was a major release that featured the long awaited addition of generics to the language and also had [lots of minor features](https://blog.carlmjohnson.net/post/2021/golang-118-minor-features/) and [quality of life improvements](https://blog.carlmjohnson.net/post/2022/golang-118-even-more-minor-features/). Go 1.19 in Q3 of 2022 was a [comparatively subdued](https://blog.carlmjohnson.net/post/2022/golang-119-new-features/) release. Now it’s 2023, and it’s time for Go 1.20. The [release candidates](https://groups.google.com/g/golang-nuts/c/HMUAm5j5raw/m/va3dxBFyAgAJ) have been released, and the final release is just around the corner. The Go team have already posted the [draft release notes](https://tip.golang.org/doc/go1.20).

In my view, the impact of Go 1.20 is somewhere in between 1.18 and 1.19, with more features and solutions to longstanding problems than 1.19, but nothing on the scale of adding generics to the language in 1.18. Still, I’m going to break up my look at “What’s New in Go 1.20” into a planned series of three blog posts. First, I’ll write about the language changes in Go 1.20 (below), and in the next post, I’ll write about the major changes to the standard library, and finally there will be a last post about some of my favorite minor additions to the standard library.

So, let’s look at the changes to the language. First of all, we have a minor revision to the rules of generics. With Go generics, you can write a function that, for example, gives you the keys of any map like this:

```go
func keys[K comparable, V any](m map[K]V) []K {
    var keys []K
    for k := range m {
        keys = append(keys, k)
    }
    return keys
}
```

In this code, `K comparable, V any` are “type constraints”. It means that K can be any type which has values that can be compared to each other, and V has no restrictions on what type it can be. Examples of comparable types are numbers, booleans, strings, and fixed sized compound types made up of all comparable elements. So, it would be legal for K be to an int and V to be a slice of bytes, but it would be illegal for K to be a slice of bytes.

I said that code above would give you the keys of any map, but in Go 1.18 and 1.19, that isn’t quite technically true. If you try to use it with a map whose keys are an interface type, it won’t compile:

```go
m := make(map[any]any) // ok
keys(m)
// compiler error (Go 1.19): any does not implement comparable
```

The issue comes down to some language lawyering around the meaning of `K comparable`. To be used as a map key, a type must be considered “comparable” by the Go compiler. For example, this is invalid:

```go
m := make(map[func()]any)
// compiler error: invalid map key type func()
```

However, you can get passed the compiler error and get a runtime error instead by using an interface.

```go
m := make(map[any]any) // ok
k := func() {}
m[k] = 1 // panic: runtime error: hash of unhashable type func()
```

So then, an interface type like `any` is a valid key type for a map, but if you try to put a key into the map that doesn’t have a valid concrete type underneath it, you will get a panic at runtime. Obviously, no one wants their code to panic at runtime, but that’s the only way to allow for map keys with dynamic types.

Here’s an example of the same problem from a different angle. Suppose I have an error type like this:

```go
type myerr func() string

func (m myerr) Error() string {
    return m()
}
```

And now I want to use my error type and do some comparisons:

```go
var err1 error = myerr(func() string { return "err1" })
var err2 error = myerr(func() string { return "err2" })
fmt.Println(err1 != nil, err2 != nil)  // true true

fmt.Println(err1 == err2)
// panic: runtime error: comparing uncomparable type main.myerr
```

As you can see, an interface value is considered comparable at compile time, but it can panic at runtime if the value it is holding is of an “uncomparable type”. You can see this same problem if you try to compare two `http.Handlers` and both happen to be `http.HandlerFuncs`.

When generics were being added to Go 1.18, [it was noticed](https://github.com/golang/go/issues/49587) that because of this duality of interfaces as considered comparable at compile time, but potentially containing uncomparable concrete types, if you wrote generic code with a type constraint of `comparable`, it was possible to get a runtime panic if the wrong value was stored in an interface. To be conservative, [the Go team decided](https://github.com/golang/go/issues/50646) to restrict the use of interfaces as `comparable` types in Go 1.18 while the full implications were being worked out.

Well, now it’s one year and two versions later, and after a ton of [lengthy debates on Github](https://github.com/golang/go/issues/51338), the Go team are satisfied that using interfaces as `comparable` types in generic code should be safe enough. If you run `keys(map[any]any{})` in Go 1.20, it will just work and you don’t have to think about any of the explanation above.

The other language change in Go 1.20 is easier to explain. If you have a slice, you can now easily convert it to an array of fixed length:

```go
s := []string{"a", "b", "c"}
a := [3]string(s)
```

If the slice is shorter than the array, you get an out of bounds panic:

```go
s := []int{1, 2, 3}
a := [4]int(s)
// panic: runtime error: cannot convert slice with length 3 to array or pointer to array with length 4
```

This follows from the addition of conversions to array pointers in Go 1.17:

```go
s := []string{"a", "b", "c"}
p := (*[3]string)(s)
```

In this case, p points to the backing array of s, and so modifying one will modify the other:

```go
s := []string{"a", "b", "c"}
p := (*[3]string)(s)
s[0] = "d"
p[1] = "e"
fmt.Println(s, p) // [d e c] &[d e c]
```

With the new slice to array conversions in Go 1.20 on the other hand, the array is a copy of the slice contents:

```go
s := []string{"a", "b", "c"}
a := [3]string(s)
s[0] = "d"
a[1] = "e"
fmt.Println(s, a)
// [d b c] [a e c]
```

Along with syntax to convert slices to arrays, Go 1.20 also brings a few additions to the unsafe package for working with slice data. The reflect package has always had [reflect.SliceHeader](https://pkg.go.dev/reflect#SliceHeader) and [reflect.StringHeader](https://pkg.go.dev/reflect#StringHeader) that are the runtime representation of slices and strings in Go:

```go
type SliceHeader struct {
    Data uintptr
    Len  int
    Cap  int
}

type StringHeader struct {
    Data uintptr
    Len  int
}
```

Both `reflect.SliceHeader` and `reflect.StringHeader` come with a warning that “It cannot be used safely or portably and its representation may change in a later release.” Misusing these types [has led to broken code](https://github.com/golang/go/issues/40701) and there was [an attempt to deprecate them](https://go-review.googlesource.com/c/go/+/401434). But in practice, so many programs rely on something like this being the layout of slices, it’s hard to imagine the Go team changing it without a lot of warning since so many programs would break.

To give Gophers an officially supported way of writing unsafe code, Go 1.17 added [unsafe.Slice](https://pkg.go.dev/unsafe#Slice), which lets you turn any pointer into a slice (whether it’s a good idea or not):

```go
obj := struct{ x, y, z int }{1, 2, 3}
slice := unsafe.Slice(&obj.x, 3)
obj.x = 4
slice[1] = 5
fmt.Println(obj, slice)
// {4 5 3} [4 5 3]
```

Now with Go 1.20, there are also [unsafe.SliceData](https://pkg.go.dev/unsafe@go1.20rc2#SliceData) (which returns a pointer to the data of a slice), [unsafe.String](https://pkg.go.dev/unsafe@go1.20rc2#String) (which unsafely builds a string out of a pointer to a byte), and [unsafe.StringData](https://pkg.go.dev/unsafe@go1.20rc2#StringData) (which unsafely gives you a pointer to the data behind a string).

These string functions are extra unsafe because they allow you to violate Go’s rule that strings are supposed to be immutable, but it also gives you a lot of power to convert to and from a byte slice without allocating new memory.

These are sharp tools that are very easy to cut yourself with, but it’s probably better that they’re directly supported in the language now instead of having people just using `unsafe.Pointer` and hoping that it works.

In the words of Hank Hill, [“Whatever you do, you should do right, even if it’s something wrong.”](https://www.getyarn.io/yarn-clip/08e52ddd-63ee-429b-b40c-b12c8ff6670b)
