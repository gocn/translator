# Data Race Patterns in Go

# Go 中的数据竞争模型

[Milind Chabbi](https://eng.uber.com/author/milind-chabbi/) and [Murali Krishna Ramanathan](https://eng.uber.com/author/murali-ramanathan/)

![Data Race Patterns in Go](../static/images/2022/w24_data_race_patterns_in_go/coverphoto.webp "Data Race Patterns in Go")

Uber has [adopted](https://eng.uber.com/go-monorepo-bazel/) Golang (Go for short) as a primary programming language for developing microservices. Our Go monorepo consists of about 50 million lines of code (and growing) and contains approximately 2,100 unique Go services (and growing).

Uber 把Golang(简称 Go)作为开发微服务的主要编程语言。我们的 Go monorepo 仓库中大约包含了 5000 万行代码(这个数量还在增长)，其中大约包含了 2100 个独立的 Go 服务(这个数量同样也在增长)。

Go makes concurrency a first-class citizen; prefixing function calls with the go keyword runs the call asynchronously. These asynchronous function calls in Go are called goroutines. Developers hide latency (e.g., IO or RPC calls to other services) by creating goroutines. Two or more goroutines can communicate data either via message passing ([channels](https://go101.org/article/channel.html)) or [shared memory](https://en.wikipedia.org/wiki/Shared_memory#:~:text=In%20computer%20science%2C%20shared%20memory,of%20passing%20data%20between%20programs.). Shared memory happens to be the most commonly used means of data communication in Go.

并发作为 Go 中的一等公民；在函数调用之前使用 go 关键字就会以异步的方式调用。这些异步函数调用在 Go 中被称为 goroutines。开发者通过创建 goroutines 来缩短延迟时间（比如在 IO 或 RPC 
调用等场景）。多个 goroutine 之间可以通过 ([channels](https://go101.org/article/channel.html) 来传递消息或者使用 [共享内存](https://en.wikipedia.org/wiki/Shared_memory#:~:text=In%20computer%20science%2C%20shared%20memory,of%20passing%20data%20between%20programs.
) ) 来进行通信。共享内存恰好是 Go 中最常用的通信方式。

Goroutines are considered "[lightweight](https://medium.com/the-polyglot-programmer/what-are-goroutines-and-how-do-they-actually-work-f2a734f6f991)" and since they are easy to create, Go programmers use goroutines liberally. As a result, we notice that _programs written in Go, typically, expose significantly more concurrency than programs written in other languages_. For example, by scanning hundreds of thousands of microservice instances running our data centers, we found out that Go microservices expose ~8x more concurrency compared to Java microservices. Higher concurrency also means potential for more concurrency bugs. A data race is a concurrency bug that occurs when two or more goroutines access the same datum, at least one of them is a write, and there is no ordering between them. Data races are insidious bugs and must be [avoided at all costs](https://www.usenix.org/legacy/events/hotpar11/tech/final_files/Boehm.pdf).

Go 程序员可以随意使用 goroutines, 因为它们被认为是 "[轻量级](https://medium.
com/the-polyglot-programmer/what-are-goroutines-and-how-do-they-actually-work-f2a734f6f991)" 并且创建 goroutines 
是一件很容易的事。最后，我们注意到，在使用 Go 编写的程序通常比使用其他语言编写的程序表现出更高的并发性能。例如，通过扫描运行我们数据中心的数十万个微服务实例，我们发现使用 Go 编写的微服务表现出的并发能力大约是 java 的 8 
倍。更高的并发也意味着可能发生更多并发错误。数据竞争是两个或者多个 goroutines 同时以无序并且至少有一个是以写的方式访问同一个数据时产生的并发错误。数据竞争是潜在的错误，必须 [不惜一切代价避免](https://www.
usenix.org/legacy/events/hotpar11/tech/final_files/Boehm.pdf)。

We developed a system to detect data races at Uber using a dynamic data race detection technique. This system, over a period of six months, detected about 2,000 data races in our Go code base, of which our developers already fixed ~1,100 data races.

我们使用动态数据竞争检测技术开发了一个系统来检测 Uber 的数据竞争。这个系统在六个月的时间里，在我们的 Go 代码库中检测到大约 2,000 个数据竞争，其中我们的开发人员已经修复了大约 1,100 个数据竞争。

In this blog, we will show various data race patterns we found in our Go programs. This study was conducted by analyzing over 1,100 data races fixed by 210 unique developers over a six-month period. Overall, we noticed that Go makes it easier to introduce data races, due to certain language design choices. There is a complicated interplay between the language features and data races.

在这篇博客中，我们将展示我们在 Go 程序中发现的各种数据竞争模型。这项研究是通过分析 210 位独特的开发人员在六个月内修复的 1,100 多个数据竞争进行的。总的来说，我们注意到，由于某些语言设计选择，使得 Go 
更容易引入数据竞争。其中语言特性和数据竞争之间存在复杂的相互作用。

## Data Race Patterns in Go\_

## Go 中的数据竞争模型_

We investigated each of the ~1,100 data races fixed by our developers and bucketed them into different categories. Our study of these data races showed some common patterns and some arcane reasons that cause data races in Go:

我们研究了由开发者修复的约 1,100 个数据竞争的问题，并将它们划分为不同的类别。我们对这些数据竞争的研究显示了导致 Go 数据竞争的一些常见模型和一些神秘的原因：

### 1. Go’s design choice to _transparently_ capture free variables _by reference_ in goroutines is a recipe for data races

### 1. 在 Go 的设计中，goroutines 可以以引用的方式不加限制地捕捉自由引用变量是引发数据竞争的重要因素

Nested functions (a.k.a., [closures](https://go.dev/tour/moretypes/25)), in Go transparently capture all free variables by reference. The programmer does not explicitly specify which free variables are captured in the closure syntax.

嵌套函数（又称[闭包](https://go.dev/tour/moretypes/25)），在 Go 中可以通过引用的方式捕获所有自由变量。程序员不需要明确指定在闭包语法中捕获哪些自由变量。

This mode of usage is different from Java and C++. Java [lambdas](https://docs.oracle.com/javase/tutorial/java/javaOO/lambdaexpressions.html) only capture by value and they consciously took that design choice to avoid concurrency bugs [[1](https://www.baeldung.com/java-lambda-effectively-final-local-variables), [2](http://www.lambdafaq.org/what-are-the-reasons-for-the-restriction-to-effective-immutability/)]. C++ requires developers to [explicitly specify](https://en.cppreference.com/w/cpp/language/lambda) capture by value or by reference.

这种使用模式与 Java 和 C ++ 不同。Java [lambdas](https://docs.oracle.com/javase/tutorial/java/javaOO/lambdaexpressions.html) 
只能够捕捉值，他们有意识地采取了该设计选择来避免并发错误 [[1](https://www.baeldung.com/java-lambda-effectively-final-local-variables), [2](http://www.lambdafaq.org/what-are-the-reasons-for-the-restriction-to-effective-immutability/)]。C ++ 要求开发者明确指定按值还是引用的方式指定捕获方式。

Developers are quite often unaware that a variable used inside a closure is a free variable and captured by reference, especially when the closure is large. More often than not, Go developers use closures as goroutines. As a result of capture-by-reference and goroutine concurrency, Go programs end up potentially having unordered accesses to free variables unless explicit synchronization is performed. We demonstrate this with the following three examples:

尤其是在大闭包的情况下, 开发者通常不知道闭包内部使用的变量是通过引用方式捕获的自由变量。很多时候，Go 开发者通常会使用闭包函数作为 goroutines。由于使用引用捕捉和并发执行 goroutine, 
除非有显式的同步操作，否则 Go 程序最终会以无序访问这些自由变量。我们用下面三个示例证明了这一点：

**_Example 1: Data race due to loop index variable capture_**

示例 1：在循环中捕捉临时变量引起的数据竞争

The code in Figure 1A shows iterating over a Go slice jobs and processing each element job via the ProcessJob function.

图 1A 中的代码显示了迭代 Go  `jobs` 切片并通过 `ProcessJob` 函数处理每个 `job` 变量。

![figure1a](../static/images/2022/w24_data_race_patterns_in_go/Figure1a-1068x204.png)

Here, the developer wraps the expensive ProcessJob in an anonymous goroutine that is launched once per item. However, the loop index variable job is captured by reference inside the goroutine. When the goroutine launched for the first loop iteration is accessing the job variable, the for loop in the parent goroutine will be advancing through the slice and updating the same loop-index variable job to point to the second element in the slice, causing a data race. This type of data race happens for value and reference types; slices, array, and maps; and read-only and write accesses in the loop body. Go recommends a coding idiom to hide and privatize the loop index variable in the loop body, which is not always followed by developers, unfortunately.

在这里，开发者将耗时的 `ProcessJob` 函数包装在匿名函数中，并且在每次循环遍历的时候都以 goroutine 的方式启动。但是，在循环中是在 goroutine 
内部通过引用的方式来捕捉变量 `job`。当第一个循环迭代启动的 goroutine 访问了变量 `job` 时，父 goroutine 中的 for 循环将通过 slice 前进并更新变量 `job` 的值，以指向 slice 
中的第二个元素，从而导致数据竞争。这种类型的数据竞争发生在循环体中对传值和引用类型元素进行读和写访问(包括切片，数组和 map)。Go 
推荐一个编码习惯来隐藏和私有化循环体中的循环索引变量，很遗憾，开发者并不总是遵守这些规范。

**_Example 2: Data race due to idiomatic err variable capture._**

示例 2：由于习惯捕获错误而引发的数据竞争。

![Data race due to idiomatic "err" variable capture.](../static/images/2022/w24_data_race_patterns_in_go/Figure1b-815x420.png)

Figure 1B: Data race due to idiomatic “err” variable capture.

图 1B：由于习惯捕获错误而引发的数据竞争。

Go [advocates multiple return values](https://www.digitalocean.com/community/tutorials/handling-errors-in-go) from functions. It is common to return the actual return value(s) and an error object to indicate if there was an error as shown in Figure 1B. The actual return value is considered to be meaningful if and only if the error value is nil. It is a common practice to assign the returned error object to a variable named err followed by checking for its nilness. However, since multiple error-returning functions can be called inside a function body, there will be several assignments to the err variable followed by the nilness check each time. When developers mix this idiom with a goroutine, the err variable gets captured by reference in the closure. As a result, the accesses (both read and write) to err in the goroutine run concurrently with subsequent reads and writes to the same err variable in the enclosing function (or multiple instances of the goroutine), which causes a data race.

Go [提倡函数有多个返回值](https://www.digitalocean.com/community/tutorials/handling-errors-in-go)。实际上，如图 
1B 所示，函数除了实际的返回值以外，还会返回一个用于指示是否发生错误的错误对象。仅当错误值为 `nil` 时，实际的返回值才会被认为是有意义的。一种常见的做法是将返回的错误对象分配给名称为 
`err` 
的变量，然后检查其零值。但是，由于可以在函数主体内调用多个返回错误的函数，，因此每次都会对 `err` 变量进行多次赋值，然后每次进行空值检查。当开发者将此惯用方式与 goroutine 混合在一起时，在闭包中通过引用捕获 `err`
。最终，在闭包函数（或多个 goroutine 实例）中对相同的 `err` 变量同时读取并将其写入，这就会导致数据竞争。

**_Example 3: Data race due to named return variable capture._**

示例 3：由于捕捉命名返回变量而引起的数据竞争。

![Data race due to named return variable capture](../static/images/2022/w24_data_race_patterns_in_go/Figure1c.png)

Figure 1C: Data race due to named return variable capture.

图 1C：由于捕捉命名返回变量而引起的数据竞争。

Go introduces a syntactic sugar called [_named return values_](https://yourbasic.org/golang/named-return-values-parameters/). The named return variables are treated as variables defined at the top of the function, whose scope outlives the body of the function. A return statement without arguments, known as a “naked” return, returns the named return values. In the presence of a closure, mixing normal (non-naked) returns with named returns or using a deferred return in a function with a named return is risky, as it can introduce a data race.

Go 引入了一种 [命名返回值](https://yourbasic.org/golang/named-return-values-parameters/)
的语法糖。命名返回变量被看作是定义在函数顶部的变量，其作用范围超出了函数的主体。函数的返回分两种，没有参数的返回语句的裸返回和命名的返回值。在存在闭包的情况下，将正常（非裸返回）返回值与命名返回混合使用或在命名返回的函数中使用延迟返回是有风险的，因为它会引入数据竞争。

The function NamedReturnCallee in Figure 1C returns an integer, and the return variable is named as result. The rest of the function body can read and write to result without having to declare it because of this syntax. If the function returns at line 4, which is a naked return, as a result of the assignment result=10 on line 2, the caller at line 13 would see the return value of 10. The compiler arranges for copying result to retVal. A named return function can also use the standard return syntax, as shown on line 9. This syntax makes the compiler copy the return value, 20, in the return statement to be assigned to the named return variable result. Line 6 creates a goroutine, which captures the named return variable result. In setting up this goroutine, even a concurrency expert might believe that the read from result on line 7 is safe because there is no other write to the same variable; the statement return 20 on line 9 is, after all, a constant return, and does not seem to touch the named return variable, result. The code generation, however, turns the return 20 statement into a write to result, as previously mentioned. Now we suddenly have a concurrent read and a write to the shared result variable, a case of a data race.

图 1C 中名为 `NamedReturnCallee` 的函数返回名为 `result` 的整型值。由于这个语法的特性，在函数体中都可以对 `result` 变量进行读写操作。如果该函数在第 4 行裸返回第 2 
行的分配 `result = 10` 的结果，则第 13 行的 `Caller` 将看到返回值为 10。编译器将会复制 `result` 的值并赋值给变量 `retVal`。如第 9
行所示，命名的返回函数还可以使用标准返回语法。这种情况下，编译器会将 20 赋值给命名返回变量 `result`。第 6 行创建了一个 goroutine，该 goroutine 捕获了命名的返回变量 `result`。在编写这个 
goroutine 时，即使是并发专家也可能会认为，第 7 行的读操作是安全的，因为没有其他地方对同一个变量进行写入操作。毕竟，第 9 行上的语句返回常量 20 ，并且似乎没有触及命名的返回变量结果。但是，像前面所说的一样，这份代码，将 
`return 20` 这个语句转换为写入结果。现在我们突然对共享结果变量进行并发读取和写入，这是数据竞争的一种情况。

### 2. Slices are confusing types that create subtle and hard-to-diagnose data races

### 2.切片令人困惑的类型，产生出微妙而难以诊断的数据竞争

[Slices](https://go.dev/ref/spec#Slice_types) are dynamic arrays and reference types. Internally, a [slice](https://dev.to/herocod3r/understanding-slices-and-the-internals-in-go-4hb1) contains a pointer to the underlying array, its current length, and the maximum capacity to which the underlying array can expand. For ease of discussion, we refer to these variables as _meta fields_ of a slice. A common operation on a slice is to grow it via the append operation. When the size reaches the capacity, a new allocation (e.g., double the current size) is made, and the meta fields are updated. When a slice is concurrently accessed by goroutines, it is natural to protect accesses to it by a mutex.

[切片](https://go.dev/ref/spec#Slice_types)
是一种动态数组的引用类型。一个[切片](https://dev.to/herocod3r/understanding-slices-and-the-internals-in-go-4hb1)
内部包含指向基础数组的指针，当前长度和基础数组可以扩展的最大容量。为了易于讨论，我们将这些变量称为切片的元字段。切片上的一个常见操作是通过追加数据操作而使它扩容。当大小达到容量时，进行了新的分配（例如，有可能是当前 len 
的两倍），并更新了元字段的值。当多个 goroutines 同时访问切片时，自然可以通过 `mutex` 访问这些受保护的信息。

![Data race in slices even after using locks.](../static/images/2022/w24_data_race_patterns_in_go/Figure2-1068x519.png)

Figure 2: Data race in slices even after using locks.

图 2：即使在使用锁后，切片也有可能产生数据竞争。

In Figure 2, the developer thinks that lock-protecting the slice append on line 6 is sufficient to protect from data race. However, a data race happens when a slice is passed as an argument to the goroutine on line 14, which is not lock-protected. The invocation of the goroutine causes the meta fields of the slice to be copied from the call site (line 14) to the callee (line 11). Given that a slice is a reference type, the developer assumed its passing (copying) to a callee caused a data race. However, a slice is not the same as a pointer type (the meta fields are copied by value) and hence the subtle data race.

在图 2 中，开发者认为，第 6 行使用锁对切片进行 append 操作足以避免数据竞争。但是，当将切片作为参数传递给第 14 行的 goroutine 时，就会发生数据竞争，而这并未受到锁的保护。goroutine 
的调用导致切片的元字段从调用方（第 14 行）拷贝到 `Callee`（第 11 行）。鉴于切片是一种引用类型，开发者假设其通过（拷贝）向 `Callee` 引起了数据竞争。但是，切片与指针类型不同（元字段按值拷贝），因此是微妙的数据竞争。

### 3. Concurrent accesses to Go’s built-in, thread-unsafe maps cause frequent data races

### 3.同时访问 Go 内置的线程不安全的 map 会导致频繁的数据竞争

![Data race due to concurrent map access.](../static/images/2022/w24_data_race_patterns_in_go/Figure3.png)

Figure 3: Data race due to concurrent map access.

图 3：由于并发访问 map 而引起的数据竞争。

Hash table ([map](https://go.dev/blog/maps)) is a built-in language feature in Go and is not thread-safe. If multiple goroutines simultaneously access the same hash table with at least one of them trying to modify the hash table (insert or delete an item), data race ensues. We observe that developers make a fundamental, but common assumption (and a mistake) that the different entries in the hash table can be concurrently accessed. This assumption stems from developers viewing the table[key] syntax used for map accesses and misinterpreting them to be accessing disjoint elements. However, a map (hash table), unlike an array or a slice, is a sparse data structure, and accessing one element might result in accessing another element; if during the same process another insertion/deletion happens, it will modify the sparse data structure and cause a data race. We even found more complex concurrent map access data races resulting from the same hash table being passed to deep call paths and developers losing track of the fact that these call paths mutate the hash table via asynchronous goroutines. Figure 3 shows an example of this type of data race.

哈希表（[map](https://go.dev/blog/maps)）是 Go 中内置的非线程安全的数据结构。如果多个 goroutines 
同时访问同一哈希表，其中至少一个试图修改哈希表（插入或删除其中的数据)，就会出现数据竞争问题。我们观察到开发者做出了一个基本但普遍的假设（这是一个错误的假设），即哈希表中的不同条目可以同时访问。这种假设源于开发者用于哈希表访问的 
`table[key]` 语法并将它们误解为访问不相交的元素。但是，和数组或切片不同，map
（哈希表）是稀疏的数据结构，访问一个元素可能会导致访问另一个元素。如果在同一过程中发生另一个插入/删除，它将修改稀疏数据结构并引起数据竞争。我们甚至发现了更复杂的并发访问哈希表引起的数据竞争，原因是同一个哈希表被传递到深度调用路径，并且开发者忘记了这些调用路径通过异步的 goroutine 改变哈希表的事实。图 3 显示了此类数据竞争的示例。

While hashtable leading to data races is not unique to Go, the following reasons make it more prone to data races in Go:

虽然哈希表导致的数据竞争并不是 Go 独有的，但以下原因使其更容易在 Go 中发生数据竞争：

1. Go developers use maps more frequently than the developers in other languages because the map is a built-in language construct. For example, in our Java repository, we found 4,389 map constructs per MLoC, whereas the same for Go is 5,950 per MLoC, which is 1.34x higher.

2. Go 开发者比其他语言的开发者更频繁地使用 map，因为 map 是语言内置的数据结构。例如，在我们的 Java 存储库中，我们发现每个 MLoC 有 4,389 个 map 结构，而 Go 同样是每 MLoC 5,950，高出 1.
   34 倍。

3. The hash table access syntax is just like array-access syntax (unlike Java’s get/put APIs), making it easy to use 
and hence accidentally confused for a random access data structure. In Go, a non-existing map element can easily be queried with the table\[key\] syntax, which simply returns the default value without producing any error. This error tolerance makes developers complacent when using Go map.

4. 哈希表访问语法就像数组访问语法（与 Java 的 get/put API 不同）一样，使其易于使用，这种访问语法不出意外地混淆了对数据结构的随机访问。在 Go 中，可以使用 `table[key]`
语法轻松查询不存在的 map 元素，该语法只需返回默认值而不会产生任何错误。这种容错性让开发者在 Go 中使用 map 时感到很满意。

### 4. Go developers often err on the side of pass-by-value (or methods over values), which can cause non-trivial data races

### 4. Go 开发者经常在传递值（或在方法上传值）方面犯错，这可能导致非凡的数据竞争

Pass-by-value semantics are [recommended](https://goinbigdata.com/golang-pass-by-pointer-vs-pass-by-value/) in Go because it simplifies escape analysis and gives variables a better chance to be allocated on the stack, which reduces pressure on the garbage collector.

按值传递语义是 Go [推荐](https://goinbigdata.com/golang-pass-by-pointer-vs-pass-by-value/)
，因为它简化了逃逸分析并为变量提供了更好的在栈上分配的机会，这减少了垃圾回收的压力。

Unlike Java, where all objects are reference types, in Go, an object can be a value type (struct) or a reference type (interface). There is no syntactic difference, and this leads to incorrect use of synchronization constructs such as sync.Mutex and sync.RWMutex, which are value types (structures) in Go. If a function creates a mutex structure and passes by value to multiple goroutine invocations, those concurrent executions of the goroutines operate on distinct mutex objects, which share no internal state. This defeats mutually exclusive access to the shared memory region that is guarded, exemplified in Figure 4 below.

和 Java 中所有对象都是引用类型不同的是，在 Go 中，对象可以是值类型（struct）或引用类型（接口）。这两者在语法方面没有差异，但是这会导致不正确使用同步结构体，例如 `sync.Mutex` 和 `sync.
RWMutex`，在是 Go 
中的值类型（结构）。如果一个函数创建了一个互斥体结构并以传值的方式给多个 goroutine 调用，这些并发执行的 goroutine 
在不共享内部状态的互斥对象上执行操作。如下图 4 所示，这会破坏对受保护的共享内存区域的互斥访问。

![Data race due to method invocation by-reference or by-pointer.](../static/images/2022/w24_data_race_patterns_in_go/Figure4a-1024x449.png)

Figure 4A: Data race due to method invocation by-reference or by-pointer.

图 4A：由于方法调用按引用或按指针引起的数据竞争。

![sync.Mutex Lock/Unlock signature.](../static/images/2022/w24_data_race_patterns_in_go/Figure4b-1068x324.png)

Figure 4B: sync.Mutex Lock/Unlock signature.

图 4B：`Sync.Mutex` 的 `Lock`/`Unlock` 签名。

Since Go syntax is the same for invoking a method over pointers vs. values, less attention is given by the developer to the question that m.Lock() is working on a copy of mutex instead of a pointer. The caller can still invoke these APIs on a mutex value, and the compiler transparently arranges to pass the address of the value. Had this transparency not been there, the bug could have been detected as a compiler type-mismatch error.

由于 Go 语法对于在指针和值上调用方法是相同的，因此开发者不太关注 `m.Lock()` 使用的是拷贝而不是指针的问题。调用者仍然可以在互斥量值上调用这些 
API，并且编译器会透明地使用传地址的方式调用。如果不存在这种透明度，则该错误可能会被编译器检测为类型不匹配的错误。

A converse of this situation happens when developers accidentally implement a method where the receiver is a pointer to the structure instead of a value/copy of the structure. In these situations, multiple goroutines invoking the method end up accidentally sharing the same internal state of the structure, whereas the developer intended otherwise. Here, also, the caller is unaware that the value type was transparently converted to a pointer type at the receiver.

当开发者意外地实现了一个方法，其中接收者是指向结构的指针而不是结构的值拷贝时，就会发生与这种情况相反的情况。在这钟情况下，调用这个方法的多个 goroutine 
最终会意外地共享结构的相同内部状态，而可能不是开发者开发者想要的。在这里，调用者也没有意识到值类型在接收者被透明地转换为指针类型。

### 5\. Mixed use of message passing (channels) and shared memory makes code complex and susceptible to data races

### 5.混合使用(通道)消息传递和共享内存会使代码变得复杂并且容易受到数据竞争的影响

![Data race when mixing message passing with shared memory.](../static/images/2022/w24_data_race_patterns_in_go/Figure5-1068x511.png)

Figure 5: Data race when mixing message passing with shared memory.
图 5：将消息传递与共享内存同时使用引起的数据竞争。

Figure 5 shows an example of a generic [future](https://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Future.html) implementation by a developer using a channel for signaling and waiting. The future can be started by calling the Start() method, and one can block for the future’s completion by calling the Wait() method on the Future. The Start()method creates a goroutine, which executes a function registered with the Future and records its return values (response and err). The goroutine signals the completion of the future to the Wait() method by sending a message on the channel ch as shown on line 6. Symmetrically, the Wait() method blocks to fetch the message from the channel (line 11).

图 5 显示的是一个由开发者使用 `channel` 的信号和等待机制实现的一个泛型的 [future](https://docs.oracle.
com/javase/7/docs/api/java/util/concurrent/Future.
html)。这个 Future 可以通过调用 `Start()` 方法来启动，并且可以通过调用 Future 的 `Wait()` 方法来阻塞直到 Future 的完成。`Start()` 方法创建一个 
goroutine，它执行注册到 Future 的函数并记录其返回值（响应和错误）。 goroutine 通过在通道 ch 上发送一条消息来向 `Wait()` 方法发出 future 完成的信号，如第 6 行所示。对称地，`Wait()` 
方法阻塞以从 channel 中获取消息（第 11 行）。

[Contexts](https://pkg.go.dev/context) in Go carry deadlines, cancelation signals, and other request-scoped values across API boundaries and between processes. This is a common pattern in microservices where timelines are set for tasks. Hence, Wait() blocks either on the context being canceled (line 13) or the future to have completed (line 11). Furthermore, the Wait() is wrapped inside a [select](https://go.dev/ref/spec#Select_statements) statement (line 10), which blocks until at least one of the select arms is ready.

Go 中的 [Contexts](https://pkg.go.dev/context) 在横跨 API 和进程之间携带截止日期、取消信号和其他请求相关的值。这种为任务设置截止时间的默认在微服务中很常见。因此，`Wait()` 
在上下文被取消（第 13 
行）或 阻塞直到 future 
完成（第 11 
行）。此外，`Wait()` 包含在 [select](https://go.dev/ref/spec#Select_statements) 语句（第 10 行）中，这个语句会阻塞，直到至少有一个分支是 ready 状态的。

If the context times out, the corresponding case records the err field of Future as ErrCancelled on line 14. This write to err races with the write to the same variable in the future on line 5.

如果上下文超时，则相应的案例在第 14 行将 Future 的 err 字段记录为 `ErrCancelled`。这个对 err 的写入与第 5 行对 future 相同变量的写入竞争。

### 6\. Go offers more leeway in its group synchronization construct sync.WaitGroup, but the incorrect placement of Add/Done methods leads to data races

### 6. `sync.WaitGroup` 为 Go 在其组同步结构中提供了更多选择，但 `Add/Done` 方法的不正确使用也会导致数据竞争

![ Data race due to incorrect WaitGroup.Add() placement.](../static/images/2022/w24_data_race_patterns_in_go/Figure6a-1068x432.png)

Figure 6A: Data race due to incorrect WaitGroup.Add() placement.

图 6A：由于 `WaitGroup.Add()` 使用不正确导致的数据竞争。

The [sync.WaitGroup](https://pkg.go.dev/sync#WaitGroup) structure is a group synchronization construct in Go. Unlike [C++ barrier](https://en.cppreference.com/w/cpp/thread/barrier), [pthreads](https://pubs.opengroup.org/onlinepubs/009696899/functions/pthread_barrier_init.html), or Java [barrier](https://docs.oracle.com/javase/7/docs/api/java/util/concurrent/CyclicBarrier.html) or [latch](https://docs.oracle.com/javase/7/docs/api/java/util/concurrent/CountDownLatch.html) constructs, the number of participants in a WaitGroup is not determined at the time of construction but is updated dynamically. Three operations are allowed on a WaitGroup object — Add(int), Done(), and Wait(). Add()increments the _count_ of participants, and the Wait() blocks until Done() is called _count_ number of times (typically once by each participant). WaitGroup is extensively used in Go. As shown previously in Table 1, group synchronization is 1.9x higher in Go than in Java.

[sync.WaitGroup](https://pkg.go.dev/sync#WaitGroup) 结构是 Go 中的组同步结构。不同于 [C++ 屏障](https://en.cppreference.
com/w/cpp/thread/barrier)，[pthreads](https://pubs.opengroup.org/onlinepubs/009696899/functions/pthread_barrier_init.
html) 或 Java [屏障](https://docs.oracle.com/javase/7/docs/api/java/util/concurrent/CyclicBarrier.html) 或 [latch]
(https://docs.oracle.com/javase/7/docs/api/java/util/concurrent/CountDownLatch.html) 结构，`WaitGroup` 
中的参与者数量不是在构造时确定的，而是动态更新的。在 `WaitGroup` 对象上允许进行三种操作 - `Add(int)`、`Done()` 和 `Wait()`。 `Add()` 增加参与者的 `count` 值，并且 `Wait
()` 阻塞直到 `Done()` 被调用 `count` 次（通常每个参与者都会调用一次）。 `WaitGroup` 在 Go 中被广泛使用。如表 1 所示，Go 中的组同步比 Java 高 1.9 倍。

In Figure 6, the developer intends to create as many goroutines as the number of elements in the slice itemIds and process the items concurrently. Each goroutine records its success or failure status in results slice at different indices and the parent function blocks at line 12 until all goroutines finish. It then accesses all elements of results serially to count the number of successful processings.

在图 6 中，开发者打算创建与切片 `itemId` 中的元素数量一样多的 goroutine 来同时处理这些 `item`。每个 goroutine 在不同索引的结果切片中记录其成功或失败状态，并在第 12 行记录父功能块，直到所有 
goroutine 完成。然后它依次访问结果的所有元素以计算成功处理的数量。

For this code to work correctly, when Wait() is invoked on line 12, the number of registered participants must be already equal to the length of itemIds. This is possible only if wg.Add(1)is executed as many times as the length of itemIds prior to invoking wg.Wait(), which means wg.Add(1)should have been placed on line 5, prior to each goroutine invocation. However, the developer incorrectly places wg.Add(1)inside the body of the goroutines on line 7, which is not guaranteed to have been executed by the time the outer function WaitGrpExample invokes Wait(). As a result, there can be fewer than the length of itemIds registered with the WaitGroup when the Wait()is invoked. For that reason, the Wait()can unblock prematurely, and the WaitGrpExample function can start to read from the slice results (line 13) while some goroutines are concurrently writing to the same slice.

为了使此代码正常工作，当在第 12 行调用 `Wait()` 时，注册参与者的数量必须已经等于 `itemIds` 的长度。仅当 wg.Add(1) 在调用 wg.Wait() 之前执行的次数与 itemIds 的长度一样多时才有可能，这意味着 wg.Add(1) 应该在每个 goroutine 之前放置在第 5 行调用。但是，开发者在第 7 行错误地将 `wg.Add(1)` 放置在 goroutine 的主体中，这不能保证在外部函数 `WaitGrpExample` 调用 `Wait()` 时已经执行。因此，调用 `Wait()` 时，注册到 `WaitGroup` 的 `itemId` 的长度可能会少于此长度。出于这个原因，`Wait()` 可以提前解除阻塞，并且 `WaitGrpExample` 函数可以开始从切片结果中读取（第 13 行），同时一些 goroutine 正在同时写入同一个切片。

We also found data races arising from a premature placement of the wg.Done()call on a Waitgroup. A subtle version of premature wg.Done()is shown below in Figure B, which results from its interaction with Go’s defer statement. When multiple defer statements are encountered, they are executed in the last-in-first-out order. Here, wg.Wait()on line 9 finishes before the doCleanup()runs. The parent goroutine accesses the locationErr on line 10 while the child goroutine may be still writing to the locationErr inside the deferred doCleanup()function (not shown for brevity).

我们还发现过早将调用 `Waitgroup` 上的 `wg.Done()` 方法会导致数据竞争。如下图 B 所示，过早地调用 `wg.Done()` 与 Go 的 defer 语句交互的结果的微妙版本。当遇到多个 defer 
语句时，按照后进先出的顺序执行。在这里，第 9 行的 `wg.Wait()` 在 `doCleanup()` 运行之前完成。父 goroutine 在第 10 行访问 `locationErr`，而子 goroutine 
可能仍在延迟的 `doCleanup()` 函数内写入 `locationErr`（为简洁起见并未显示）。

![data race duce to defer statement ordering leading to incrrect warit group done](../static/images/2022/w24_data_race_patterns_in_go/Figure6b.png)

Figure 6B: Data race due to defer statement ordering leading to incorrect WaitGroup.Done() placement.

图 6B：由于 defer 语句调用`WaitGroup.Done()` 顺序导致的数据竞争错误。

### 7\. Running tests in parallel for Go’s table-driven test suite idiom can often cause data races, either in the product or test code

### 7.为 Go 的表驱动测试套件用法并行运行测试通常会导致生产或测试代码中的数据竞争

[Testing](https://pkg.go.dev/testing) is a built-in feature in Go. Any function with the prefix _Test_ in a file with suffix \_test.go can be run as a test via the Go build system. If the test code calls an API testing.T.Parallel(), it will run concurrently with other such tests. We found a large class of data races happen due to such concurrent test executions. The root causes of these data races were sometimes in the test code and sometimes in the product code. Additionally, within a single Test\-prefixed function, Go developers often write many subtests and execute them via the Go-provided suite package. Go recommends a [table-driven test suite idiom](https://dave.cheney.net/2019/05/07/prefer-table-driven-tests) to write and run a test suite. Our developers extensively write tens or hundreds of subtests in a test, which our systems run in parallel. This idiom becomes a source of problem for a test suite where the developer either assumed serial test execution or lost track of using shared objects in a large complex test suite. Problems also arise when the product API(s) were written without thread safety (perhaps because it was not needed), but were invoked in parallel, violating the assumption.

[测试](https://pkg.go.dev/testing) 是 Go 中的内置功能。带有后缀`_test.go` 的文件中的前缀测试的任何功能都可以通过 Go 构建系统作为测试运行。如果测试代码调用 API 
`testing.T.Parallel()` ，Go 会并发运行这些测试用例。我们发现，由于这种并发执行的测试引发了大量的数据竞争。这些数据竞争的根本原因有时是在测试代码中，有时是在生产代码中。另外，在单个测试函数中，Go
开发者通常会编写许多子测验，并通过 Go 提供的测试工具软件包执行它们。 Go
建议使用[表格驱动测试习惯](https://dave.cheney.net/2019/05/07/prefer-table-driven-tests)
来编写和运行一个测试套件。我们的系统并行地执行我们开发者编写的数十个或者数百个自测试时。这个习惯用法成为测试套件问题的根源，开发人员要么假设串行测试执行，要么忘记在大型复杂测试套件中使用共享对象。当生产 API 
编写时没有线程安全（可能是因为不需要它），但被并行调用时，也会出现问题，这违反了假设。

## Summary of Findings

## 总结

We analyzed the fixed data races to classify the reasons behind them. These issues are tabulated as follows. The labels are not mutually exclusive.

我们分析了修复的数据竞争问题，以对其背后的原因进行分类。这些问题被列为如下。这些标签并不是互斥的。

![summary of data races](../static/images/2022/w24_data_race_patterns_in_go/Figure7.png)

Figure 7: Summary of data races.

图 7：数据竞争的摘要。

An example for each pattern of a data race is available from [this](https://zenodo.org/record/6330164) link.

从此链接获得了每个数据竞争模式的一个示例。

In summary, based on observed (including fixed) data races, we elaborated the Go language paradigms that make it easy to introduce races in Go programs. We hope that our experiences with data races in Go will help Go developers pay more attention to the subtleties of writing concurrent code. Future programming language designers should carefully weigh different language features and coding idioms against their potential to create common or arcane concurrency bugs.

总而言之，根据观察到的（包括已经修复的）数据竞争，我们详细阐述了在 Go 程序中更加容易引入数据竞争问题的范式。我们希望我们在 Go 中进行数据竞争的经验帮助 Go 
开发者更多地关注编写巧妙的并发代码。未来的编程语言设计师应仔细权衡不同的语言功能和编码习惯，减少创建常见和隐蔽的并发问题。

### Threats to Validity

### 不足

The discussion herein is based on our experiences with data races in Uber’s Go monorepo and may have missed additional patterns of data races that may happen elsewhere. Also, as dynamic race detection does not detect all possible races due to code and interleaving coverage, our discussion may have missed a few patterns of races. Despite these threats to the universality of our results, the discussion on the patterns in this paper and the deployment experiences hold independently.

本文的讨论是基于我们在 Uber 的 Go Monorepo 
中进行数据竞争的经验，并且可能错过了其他可能发生数据竞争的模式。同样，由于动态竞争检测并未检测到由于代码和交织的覆盖而无法检测到所有有可能引起的数据竞争问题，因此我们的讨论可能错过了一些数据竞争模式。尽管对我们结果的普遍性有这些不足，但本文和部署经验中有关模式的讨论独立存在。

This is the second of a two-part blog post series on our experiences with data race in Go code. An elaborate [_version_](https://arxiv.org/pdf/2204.00764.pdf) _of our experiences will appear in the ACM SIGPLAN Programming Languages Design and Implementation (PLDI), 2022. In the_ [_first part_](https://eng.uber.com/dynamic-data-race-detection-in-go-code/) _of the blog series, we discuss our learnings pertaining to deploying dynamic race detection at scale for Go code._

这是有关我们在 GO 代码中数据竞争的经验的两部分博客文章系列中的第二个。我们的经验的详尽版本将出现在 ACM Sigplan 编程语言设计与实施（PLDI），2022 年。在博客系列的第一部分中，我们讨论了与以 GO 代码为大规模部署动态竞争检测有关的学习。
