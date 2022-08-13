# Go 中简单的内存节省技巧
***
- 原文地址：https://www.ribice.ba/golang-memory-savings/
- 原文作者：Emir Ribic
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w33_Easy_memory_saving_tricks_in_Go.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[]()
***

除非您正在对服务进行原型设计，否则您可能会关心应用程序的内存使用情况。占用更小的内存，会使基础设施成本降低，扩展变得更容易。尽管 Go 以不消耗大量内存而闻名，但仍有一些方法可以进一步减少消耗。其中一些需要大量重构，但很多都很容易做到。

![](https://www.ribice.ba/img/38/go_memory.png#c)

### 预先分配切片

要理解这种优化，我们必须了解切片在 Go 中是如何工作的，为此我们必须首先了解数组。

[go.dev](https://go.dev/blog/slices-intro) 上有一篇非常好的关于这个主题的文章。

数组是具有连续内存的相同类型的集合。数组类型定义时要指定长度和元素类型。

因为数组的长度是它们类型的一部分，数组的主要问题是它们大小固定，不能调整。

与数组类型不同，切片类型无需指定长度。切片的声明方式与数组相同，但没有数量元素。

切片是数组的包装器，它们不拥有任何数据——它们是对数组的引用。它们由指向数组的指针、长度及其容量（底层数组中的元素数）组成。

当您向没有足够容量的切片添加一个新值时 - 会创建一个具有更大容量的新数组，并将当前数组中的值复制到新数组中。这会导致不必要的内存分配和 CPU 周期。

为了更好地理解这一点，让我们看一下以下代码段：

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

输出：

```
Address: 0xc000018030, Length: 1, Capacity: 1, Values: [0]
Address: 0xc000018050, Length: 2, Capacity: 2, Values: [0 1]
Address: 0xc000082020, Length: 3, Capacity: 4, Values: [0 1 2]
Address: 0xc000082020, Length: 4, Capacity: 4, Values: [0 1 2 3]
Address: 0xc000084040, Length: 5, Capacity: 8, Values: [0 1 2 3 4]
```

凭借输出结果我们可以得出结论，无论何时必须增加容量（增加 2 倍），都必须创建一个新的底层数组（新的内存地址）并将值复制到新数组中。

有趣是，当容量<1024 时会涨为之前的 2 倍，当容量>=1024时会以 1.25 倍增长。从 Go 1.18 开始，这已经变得[更加线性](https://github.com/golang/go/commit/2dda92ff6f9f07eeb110ecbf0fc2d7a0ddd27f9d)。

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

由上述基准，我们可以得出结论，将值分配给预分配的切片和将值追加到切片之间是存在很大差异的。

两个工具有助于切片的预分配：

-    [prealloc](https://github.com/alexkohler/prealloc): 一个静态分析工具，用于查找可能被预分配的切片声明。
-    [makezero](https://github.com/ashanbrown/makezero): 一个静态分析工具，用于查找未以零长度初始化且稍后有追加的切片声明。

### 结构体中的字段顺序

您之前可能没有想到这一点，但结构体中字段的顺序对内存消耗有很大影响。

以下面的结构体为例：

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

上述的输出为 96 字节，而所有字段相加为 82 字节。那额外的 14 个字节是来自哪里呢？

现代 64 位 CPU 以 64 位（8 字节）的块获取数据。如果我们有一个较旧的 32 位 CPU，它将以 32 位（4 字节）的块进行。

第一个周期占用 8 个字节，拉取“IsDraft”字段占用了 1 个字节并且产生 7 个未使用字节。它不能占用“一半”的字段。

第二个和第三个周期取 Title 字符串，第四个周期取 ID，依此类推。到取 IsDeleted 字段时，它使用 1 个字节并有 7 个字节未使用。

对内存节省的关键是按字段占用大小从上到下对字段进行排序。对上述结构进行排序，大小可减少到 88 个字节。最后两个字段 IsDraft 和 IsDeleted 被放在同一个块中，从而将未使用的字节数从 14 (2x7) 减少到 6 (1 x 6)，在此过程中节省了 8 个字节。

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

在 64 位架构上占用小于 8 字节的 Go 类型：

-   bool: 1 个字节
-   int8/uint8: 1 个字节
-   int16/uint16: 2 个字节
-   int32/uint32/rune: 4 个字节
-   float32: 4 个字节
-   byte: 1 个字节

不需要手动检查您的结构体并按大小对其进行排序，而是使用 工具找到这些结构并报告“正确”的排序。

-    [maligned](https://github.com/mdempsky/maligned) - 已弃用，用于报告未对齐的结构并打印出正确排序的字段。它在一年前被弃用，但您仍然可以安装旧版本并使用它。
-   govet/fieldalignment: gotools 和 `govet` 的一部分工具，`fieldalignment` 可打印出未对齐的结构和结构的当前/理想大小。

安装和运行 fieldalignment：

```
go install golang.org/x/tools/go/analysis/passes/fieldalignment/cmd/fieldalignment@latest
fieldalignment -fix <package_path>
```

对上面的代码使用 govet/fieldalignment：

```
fieldalignment: struct of size 96 could be 88 (govet)
```

### 使用 map[string]struct{} 而不是 map[string]bool

Go 没有内置的集合，通常使用 `map[string]bool{}` 表示集合。尽管它更具可读性（这非常重要），但将其作为一个集合使用是错误的，因为它具有两种状态（假/真）并且与空结构体相比使用了额外的内存。

空结构体 (`struct{}`) 是没有额外字段的结构类型，占用零字节的存储空间。Dave Chaney 有一篇关于空结构的[详细博客](https://dave.cheney.net/2014/03/25/the-empty-struct) 。

除非您的 map/set 包含大量值并且需要获得额外的内存，否则我建议使用  `map[string]struct{}`。

100 000 000 次 map 写入的极端示例：

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

得到以下结果（MBP 14 2021，10C M1 Pro）：

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

通过这些数字，我们可以得出结论，使用空结构映射的写入速度提高了 3.2%，分配的内存减少了 10%。

此外，使用`map[type]struct{}`是实现集合的正确解决方法，因为每个键都有一个值。`map[type]bool` 每个键有两个可能的值，这不是一个集合，如果目标是创建一个集合，则可能会被滥用。

然而，可读性大多数时候比（可忽略的）内存改进更重要。与空结构体相比，使用布尔值更容易查找：


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
