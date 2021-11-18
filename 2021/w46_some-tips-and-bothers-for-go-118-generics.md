# Some tips and bothers for Go 1.18 Generics

As of 2021-11-17, there is probably no cache library that uses the Go 1.18 Generics feature.

I've tried to implement the first Go 1.18 generics cache library here. I'm very happy if you give me a GitHub star.

[https://github.com/Code-Hex/go-generics-cache](https://github.com/Code-Hex/go-generics-cache)

In this article, I'll introduce some of the things I noticed about Go Generics while developing this cache library, as well as some of the tips and bothers I found.

## Return zero value for any type

You will often write code that returns any and error, such as the following. When an error occurs in a function, you would have written code that returns zero-value and error, but now you need to think a little bit differently.

```go
func Do[V any](v V) (V, error) {
    if err := validate(v); err != nil {
        // What should we return here?
    }
    return v, nil
}

func validate[V any](v V) error
```

Let’s suppose you write `return 0, err` here. This will be a compilation error. The reason is that `any` type can be a type other than `int` type, such as `string` type. So how do we do this?

Let's declare a variable once using `V` of the type parameter. Then you can write it in a compilable form as follows.

```go
func Do[V any](v V) (V, error) {
    var ret V
    if err := validate(v); err != nil {
        return ret, err
    }
    return v, nil
}
```

In addition, named return values can be used to simplify the writing for a single line.

```go
func Do[V any](v V) (ret V, _ error) {
    if err := validate(v); err != nil {
        return ret, err
    }
    return v, nil
}
```
[https://gotipplay.golang.org/p/0UqA0PIO9X8](https://gotipplay.golang.org/p/0UqA0PIO9X8)
## Don't try to do type switch with `constraints`

I wanted to provide two methods, `Increment` and `Decrement`.They can add or subtract values from the [go-generics-cache](https://github.com/Code-Hex/go-generics-cache) library if the stored value satisfies the [Number constraint](https://github.com/Code-Hex/go-generics-cache/blob/d5c3dda0e57b4c533c1e744869032c33a4fc2d9e/constraint.go#L5-L8).

Let's use `Increment` method as an example. I initially wrote code like this.

```go
type Cache[K comparable, V any] struct {
    items map[K]V
}

func (c *Cache[K, V]) Increment(k K, n V) (val V, _ error) {
    got, ok := c.items[k]
    if !ok {
        return val, errors.New("not found")
    }

    switch (interface{})(n).(type) {
    case Number:
        nv := got + n
        c.items[k] = nv
        return nv, nil
    }
    return val, nil
}
```

I was thinking of using the type of the value `n V` to match the constraints that are satisfied. This method that adds if the `Number` constraint is satisfied, and does nothing otherwise.

This will not compile.

1. Go does not provide conditional branching for constraints.
1. constraints is an interface. Go does not allow type assertions using interface.
1. The type of `n` is not determined, so `+` operation is not possible.
1. In the first place, there is no guarantee that `items` type is the same type as `n`.

To solve this problem, I redesigned the interface. Why did I want to create methods in the `Cache` struct?

- To inherit the data of the fields held by the `Cache` struct.
- To handle methods of the `Cache`.

To solve these points, I decided to embed the `Cache` struct. And I defined a `NumberCache` struct that can always handle `Number` constraints.

```go
type NumberCache[K comparable, V Number] struct {
    *Cache[K, V]
}
```

This way, we can guarantee that the type of the value passed to the `Cache` struct will always be a `Number` constraint. So we can add an `Increment` method to `NumberCache` struct.

```go
func (c *NumberCache[K, V]) Increment(k K, n V) (val V, _ error) {
    got, ok := c.Cache.items[k]
    if !ok {
        return val, errors.New("not found")
    }
    nv := got + n
    c.Cache.items[k] = nv
    return val, nil
}
```
[https://gotipplay.golang.org/p/poQeWw4UE_L](https://gotipplay.golang.org/p/poQeWw4UE_L)

## The point of bothered me

Let's look at the definition of the `Cache` struct again.

```go
type Cache[K comparable, V any] struct {
    items map[K]V
}
```
Go Generics is defined as a language specification with a constraint which is called [comparable](https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md#comparable-types-in-constraints). Which allows only types can use `==` and `!=`.

I feel that this constraint is bothered me. Let’s explain the reasons why bother me.

I defined a function that compares two `comparable` values.
```go
func Equal[T comparable](v1, v2 T) bool {
    return v1 == v2
}
```
Allowing only `comparable` types are going to result in an error if an incomparable type is passed to the function at compile-time. You may think this is useful.

However, according to Go's specification, `interface{}` also satisfies this comparable constraint.

If `interface{}` can be satisfied, the following code can be compiled.

```go
func main() {
    v1 := interface{}(func() {})
    v2 := interface{}(func() {})
    Equal(v1, v2)
}
```
This shows that `func()` type which is a non-comparable type. but can be converting as a comparable type by casting it to the `interface{}` type.

`interface{}` type will only know at runtime whether it is a comparable type or not.

If this is a complex code, it may be difficult to notice.

[https://gotipplay.golang.org/p/tbKKuehbzUv](https://gotipplay.golang.org/p/tbKKuehbzUv)

I believe that we need another comparable constraints that do not accept `interface{}` to notice at compile-time.

Can this constraints be defined by Go users? The answer is currently not.

This is because `comparable` constraint contains "comparable structures" and "comparable arrays". These constraints cannot currently be defined by Go users. Therefore, I would like to provide them as a Go specification.

I also created a proposal for it, so if you can relate to it, I would appreciate it if you could give me 👍 in GitHub issue.
[https://github.com/golang/go/issues/49587](https://github.com/golang/go/issues/49587)
