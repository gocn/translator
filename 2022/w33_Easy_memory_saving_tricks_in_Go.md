# Easy memory-saving tricks in Go
***
- 原文地址：https://www.ribice.ba/golang-memory-savings/
- 原文作者：Emir Ribic
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[]()
***

Unless you’re prototyping a service - you probably care about the memory usage of your application. With a smaller memory footprint, the infrastructure costs are reduced and scaling becomes a bit easier/delayed. Even though Go is known for not consuming a lot of memory, there are ways to further reduce the consumption. Some of them require lots of refactoring, but many are very easy to do.

![](https://www.ribice.ba/img/38/go_memory.png#c)

### Pre-allocate your slices

To understand this optimization, we have to understand how slices work in Go and to do that we have to understand arrays first.

There is a very good blog post on this topic [on go.dev](https://go.dev/blog/slices-intro).

Arrays are a collection of the same type with continuous memory. An array type definition specifies a length and an element type.

The main issue with arrays is that they are fixed size - they cannot be resized, as the length of the array is part of their type.

Unlike array type, slice type doesn’t have a specified length. A slice is declared the same way as an array, without the element count.

Slices are wrappers for arrays, they do not own any data - they are references to arrays. They consist of a pointer to the array, the length of the segment, and its capacity (number of elements in the underlying array).

When you append to a slice that doesn’t have the capacity for a new value - a new array is created with a larger capacity and the values from the current array are copied to the new one. This leads to unnecessary allocations and CPU cycles.

To better understand this, let’s take a look at the following snippet:

```
func main() {
    var ints []int
    for i := 0; i < 5; i++ {
        ints = append(ints, i)
        fmt.Printf("Address: %p, Length: %d, Capacity: %d, Values: %v\n",
            ints, len(ints), cap(ints), ints)
    }
}
```

The above outputs:

```
Address: 0xc000018030, Length: 1, Capacity: 1, Values: [0]
Address: 0xc000018050, Length: 2, Capacity: 2, Values: [0 1]
Address: 0xc000082020, Length: 3, Capacity: 4, Values: [0 1 2]
Address: 0xc000082020, Length: 4, Capacity: 4, Values: [0 1 2 3]
Address: 0xc000084040, Length: 5, Capacity: 8, Values: [0 1 2 3 4]
```

Looking at the output, we can conclude that whenever capacity had to be increased (by a factor of 2), a new underlying array had to be created (new memory address) and values were copied to the new array.

Fun fact, the factor of capacity growth used to be 2x for capacity <1024, and 1.25x for >= 1024. As of Go 1.18, this has been [made more linear](https://github.com/golang/go/commit/2dda92ff6f9f07eeb110ecbf0fc2d7a0ddd27f9d).

```
func BenchmarkAppend(b *testing.B) {
    var ints []int
    for i := 0; i < b.N; i++ {
        ints = append(ints, i)
    }
}

func BenchmarkPreallocAssign(b *testing.B) {
    ints := make([]int, b.N)
    for i := 0; i < b.N; i++ {
        ints[i] = i
    }
}
```

```
name               time/op
Append-10          3.81ns ± 0%
PreallocAssign-10  0.41ns ± 0%

name               alloc/op
Append-10           45.0B ± 0%
PreallocAssign-10   8.00B ± 0%

name               allocs/op
Append-10            0.00
PreallocAssign-10    0.00
```

Looking at the above benchmark, we can conclude that there is a large difference between assigning values to preallocated slices and appending values to slice.

Two linters help with preallocating slices:

-   [prealloc](https://github.com/alexkohler/prealloc): A static analysis tool to find slice declarations that could potentially be preallocated.
-   [makezero](https://github.com/ashanbrown/makezero): A static analysis tool to find slice declarations that are not initialized with zero length and are later used with append.

### Order fields in structs

You may not have thought of this before, but the order of fields in a struct matters for memory consumption.

Take the following struct for example:

```
type Post struct {
    IsDraft     bool      // 1 byte
    Title       string    // 16 bytes
    ID          int64     // 8 bytes
    Description string    // 16 bytes
    IsDeleted   bool      // 1 byte
    Author      string    // 16 bytes
    CreatedAt   time.Time // 24 bytes
}

func main(){
    p := Post{}
    fmt.Println(unsafe.Sizeof(p))
}
```

The output of the above function is 96 (bytes), while all the fields add to 82 bytes. Where are the additional 14 bytes coming from?

Modern 64-bit CPUs take data in chunks of 64 bits (8 bytes). If we have an older 32-bit CPU, it would be doing chunks of 32 bits (4 bytes).

The first cycle takes 8 bytes, pulling the ‘IsDraft’ field occupying 1 byte and having 7 unused bytes. It can’t take ‘half’ of a field.

The second and third cycles take the `Title` string, the fourth one takes the ID, and so on. Again with IsDeleted field it takes 1 byte and has 7 unused bytes.

What really matters is sorting the fields by their size top to bottom. Sorting the above struct, the size of gets reduced to 88 bytes. The last two fields, IsDraft and IsDeleted, are taken in the same chunk, thus reducing the number of unused bytes from 14 (2x7) to 6 (1 x 6), saving 8 bytes in the process.

```
type Post struct {
    CreatedAt   time.Time // 24 bytes
    Title       string    // 16 bytes
    Description string    // 16 bytes
    Author      string    // 16 bytes
    ID          int64     // 8 bytes
    IsDraft     bool      // 1 byte
    IsDeleted   bool      // 1 byte
}

func main(){
    p := Post{}
    fmt.Println(unsafe.Sizeof(p))
}
```

Types in Go that occupy <8 bytes on 64-bit architecture:

-   bool: 1 byte
-   int8/uint8: 1 byte
-   int16/uint16: 2 bytes
-   int32/uint32/rune: 4 bytes
-   float32: 4 bytes
-   byte: 1 byte

Instead of manually checking your structs and sorting them by size, there are linter that finds these and (used to) report ‘correct’ sorting.

-   [maligned](https://github.com/mdempsky/maligned) - A deprecated linter that used to report misaligned structs and print out correctly sorted fields. It was deprecated a year ago, but you can still install the older version and use it.
-   govet/fieldalignment: A part of gotools and `govet` linter, `fieldalignment` prints out misaligned structs and the current/ideal size of struct.

To install and run fieldalignment:

```
go install golang.org/x/tools/go/analysis/passes/fieldalignment/cmd/fieldalignment@latest
fieldalignment -fix <package_path>
```

Using govet/fieldalignment on the above code:

```
fieldalignment: struct of size 96 could be 88 (govet)
```

### Use map\[string\]struct{} instead of map\[string\]bool

Go doesn’t have a built-in set and usually `map[string]bool{}` is used to represent a set. Even though it’s more readable, which is very important, using it as a set is wrong as it has two states (false/true) and uses extra memory compared to an empty struct.

The empty struct (`struct{}`) is a [struct type](https://go.dev/ref/spec#Struct_types) with no extra fields, occupying zero bytes of storage. There is a [detailed blog post](https://dave.cheney.net/2014/03/25/the-empty-struct) from Dave Chaney on the empty struct.

I wouldn’t recommend doing this unless your map/set holds a very large number of values and you need to get extra memory or you’re developing for a low-memory platform.

Using an extreme example of 100 000 000 writes to the map:

```
func BenchmarkBool(b *testing.B) {
    m := make(map[uint]bool)

    for i := uint(0); i < 100_000_000; i++ {
        m[i] = true
    }
}

func BenchmarkEmptyStruct(b *testing.B) {
    m := make(map[uint]struct{})

    for i := uint(0); i < 100_000_000; i++ {
        m[i] = struct{}{}
    }
}
```

I get the following results (MBP 14 2021, 10C M1 Pro), which were pretty consistent throughout runs:

```
name            time/op
Bool          12.4s ± 0%
EmptyStruct   12.0s ± 0%

name            alloc/op
Bool         3.78GB ± 0%
EmptyStruct  3.43GB ± 0%

name            allocs/op
Bool          3.91M ± 0%
EmptyStruct   3.90M ± 0%
```

Using these numbers, we can conclude that writes were 3.2% faster and 10% less memory was allocated using the empty struct map.

In addition, using `map[type]struct{}` is the correct workaround for implementing sets, as there is one value associated with every key. With `map[type]bool` there are two possible values for each key, which is not a set and can be misused if creating a set is the goal.

However, readability is most of the time more important than (neglectable) memory improvements. The lookups are much easier to grasp with boolean values compared to empty struct ones:

```
m := make(map[string]bool{})
if m["key"]{
 // Do something
}

v := make(map[string]struct{}{})
if _, ok := v["key"]; ok{
    // Do something
}
```
