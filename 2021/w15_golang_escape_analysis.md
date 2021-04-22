- 原文地址：http://www.agardner.me/golang/garbage/collection/gc/escape/analysis/2015/10/18/go-escape-analysis.html
- 原文作者：  
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w15_golang_escape_analysis.md
- 译者：[cuua](https://github.com/cuua)
- 校对：[](https://github.com/)

# Golang escape analysis

Oct 18, 2015

Garbage collection is a convenient feature of Go - automatic memory management makes code cleaner and memory leaks less likely. However, GC also adds overhead as the program periodically needs to stop and collect unused objects. The Go compiler is smart enough to automatically decide whether a variable should be allocated on the heap, where it will later need to be garbage collected, or whether it can be allocated as part of the stack frame of the function which declared it. Stack-allocated variables, unlike heap-allocated variables, don’t incur any GC overhead because they’re destroyed when the rest of the stack frame is destroyed - when the function returns.

Go’s escape analysis is more basic than the HotSpot JVM, for example. The basic rule is that if a reference to a variable is returned from the function where it is declared, it “escapes” - it can be referenced after the function returns, so it must be heap-allocated. This is complicated by:

* functions calling other functions
* references being assigned to struct members
* slices and maps
* cgo taking pointers to variables

To perform escape analysis, Go builds a graph of function calls at compile time, and traces the flow of input arguments and return values. A function may take a reference to one of it’s arguments, but if that reference is not returned, the variable does not escape. A function may also return a reference, but that reference may be dereferenced or not returned by another function in the stack before the function which declared the variable returns. To illustrate a few simple cases, we can run the compiler with `-gcflags '-m'`, which will print verbose escape analysis information:

```
package main

type S struct {}

func main() {
  var x S
  _ = identity(x)
}

func identity(x S) S {
  return x
}
```

You’ll have to build this with `go run -gcflags '-m -l'` - the `-l` flag prevents the function `identity` from being inlined (that’s a topic for another time). The output is: nothing! Go uses pass-by-value semantics, so the `x` variable from `main` will always be copied into the stack of `identity`. In general code without references always uses stack allocation, trivially. There’s no escape analysis to do. Let’s try something harder:

```
package main

type S struct {}

func main() {
  var x S
  y := &x
  _ = *identity(y)
}

func identity(z *S) *S {
  return z
}
```

And the output:

```
./escape.go:11: leaking param: z to result ~r1
./escape.go:7: main &x does not escape
```

The first line shows that the variable “flows through”: the input variable is returned as an output. But `identity` doesn’t take a reference to `z`, so the variable doesn’t escape. No references to `x` survive past `main` returning, so `x` can be allocated as part of the stack frame of `main`.

A third experiment:

```
package main

type S struct {}

func main() {
  var x S
  _ = *ref(x)
}

func ref(z S) *S {
  return &z
}
```

And the output:

```
./escape.go:10: moved to heap: z
./escape.go:11: &z escapes to heap
```

Now there’s some escaping going on. Remember that Go has pass-by-value semantics, so `z` is a copy of the variable `x` from `main`. `ref` return a reference to `z`, so `z` can’t be part of the stack frame for `ref` - where would the reference point when `ref` returns? Instead it escapes to the heap. Even though `main` immediately throws away the reference without dereferencing it, Go’s escape analysis is not sophisticated enough to figure this out - it only looks at the flow of input and return variables. It’s worth noting that in this case `ref` would be inlined by the compiler if we weren’t stopping it.

What if a reference is assigned to a struct member?

```
package main

type S struct {
  M *int
}

func main() {
  var i int
  refStruct(i)
}

func refStruct(y int) (z S) {
  z.M = &y
  return z
}
```

Output:

```
./escape.go:12: moved to heap: y
./escape.go:13: &y escapes to heap
```

In this case Go can still trace the flow of references, even though the reference is a member of a struct. Since `refStruct` takes a reference and returns it, `y` must escape. Compare with this case:

```
package main

type S struct {
  M *int
}

func main() {
  var i int
  refStruct(&i)
}

func refStruct(y *int) (z S) {
  z.M = y
  return z
}
```

Output:

```
./escape.go:12: leaking param: y to result z
./escape.go:9: main &i does not escape
```

Since `main` takes the reference and passes it to `refStruct`, the reference never outlives the stack frame where the referenced variable was declared. This and the preceding program have slightly different semantics, but if the second program is sufficient it would be more efficient: in the first example `i` must be allocated on the stack of `main`, then re-allocated on the heap and copied as an argument to `refStruct`. In the second example `i` is only allocated once, and a reference is passed around.

A slightly more insidious example:

```
package main

type S struct {
  M *int
}

func main() {
  var x S
  var i int
  ref(&i, &x)
}

func ref(y *int, z *S) {
  z.M = y
}
```

Output:

```
./escape.go:13: leaking param: y
./escape.go:13: ref z does not escape
./escape.go:9: moved to heap: i
./escape.go:10: &i escapes to heap
./escape.go:10: main &x does not escape
```

The problem here is that `y` is assigned to a member of an input struct. Go can’t trace that relationship - inputs are only allowed to flow to outputs - so the escape analysis fails and the variable must be heap allocated. There are many documented, pathological cases (as of Go 1.5) where variables must be heap allocated due to limitations of Go’s escape analysis - [see this link](https://docs.google.com/document/d/1CxgUBPlx9iJzkz9JWkb6tIpTe5q32QDmz8l0BouG0Cw/preview).

Finally, what about maps and slices? Remember that slices and maps are actually just Go structs with pointers to heap-allocated memory: the slice struct is exposed in the `reflect` package ([SliceHeader](https://golang.org/pkg/reflect/#SliceHeader)). The map struct is harder to find, but it exists: [hmap](https://golang.org/src/runtime/hashmap.go#L102). If these structures don’t escape they’ll be stack-allocated, but the data itself in the backing array or hash buckets will be heap-allocated every time. The only way to avoid this would be to allocate a fixed-size array (like `[10000]int`).

If you’ve (profiled your program’s heap usage)[http://blog.golang.org/profiling-go-programs] and need to reduce GC time, there may be some wins from moving frequently allocated variables off the heap. It’s also just a fascinating topic: for further reading about how the HotSpot JVM handles escape analysis, check out [this paper](http://www.cc.gatech.edu/~harrold/6340/cs6340_fall2009/Readings/choi99escape.pdf) which talks about stack allocation, and also about detecting when synchronization can be elided.