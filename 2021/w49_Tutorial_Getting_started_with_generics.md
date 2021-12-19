# 教程：如何开始使用泛型

- 原文地址：https://go.dev/doc/tutorial/generics
- 原文作者：go.dev
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w49_Tutorial_Getting_started_with_generics.md
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：[cvley](https://github.com/cvley)

目录

- [前提条件](#prerequire)
- [为你的代码创建一个文件夹](#add_folder)
- [添加非泛型函数](#add_non_genertic_function)
- [添加一个泛型函数来处理多种类型](#add_generic_function)
- [在调用泛型函数时删除类型参数](#delete_type_arguement)
- [声明一个类型约束](#declare_type_constrant)
- [结论](#conclusion)
- [完整代码](#complete_code)

> 备注：这是一个beta版本的内容

这个教程介绍了Go泛型的基础概念。 通过泛型，你可以声明并使用函数或者是类型，那些用于调用代码时参数需要兼容多个不同类型的情况。

在这个教程里，你会声明两个普通的函数，然后复制一份相同的逻辑到一个泛型的方法里。

你会通过以下几个章节来进行学习：

1. 为你的代码创建一个文件夹；
2. 添加非泛型函数；
3. 添加一个泛型函数来处理多种类型；
4. 在调用泛型函数时删除类型参数；
5. 声明一个类型约束。

> 备注：对其他教程，可以查看[教程](https://go.dev/doc/tutorial/)
>
> 备注：你同时也可以使用 ["Go dev branch"模式](https://go.dev/play/?v=gotip)来编辑和运行你的代码，如果你更喜欢以这种形式的话

<h2 id="prerequire"> 前提条件 </h2>

- 安装Go 1.18 Beta 1或者更新的版本。对安装流程，请看安装并使用beta版本。
- 代码编辑器。任何你顺手的代码编辑器。
- 一个命令终端。Go在任何终端工具上都很好使用，比如Linux 、Mac、PowerShell或者Windows上的cmd。

### 安装并使用beta版本

这个教程需要Beta 1的泛型特性。安装beta版本，需要通过下面几个步骤：

1. 执行下面的指令安装beta版本

   ```shell
   $ go install golang.org/dl/go1.18beta1@latest
   ```

2. 执行下面的指令下载更新

   ```shell
   $ go1.18beta1 download
   ```

3. 用beta版本执行go命令，而不是Go的发布版本(如果你本地有安装的话)

   你可以使用beta版本名称或者把beta重命名成别的名称来执行命令。

   - 使用beta版本名称，你可以通过go1.18beta1来执行指令而不是go：

     ```shell
     $ go1.18beta1 version
     ```

   - 通过对beta版本名称重命名，你可以简化指令：

     ```shell
     $ alias go=go1.18beta1
     $ go version
     ```

在这个教程中将假设你已经对beta版本名称进行了重命名。

<h2 id="add_folder"> 为你的代码创建一个文件夹 </h2>

在一开始，先给你要写的代码创建一个文件夹

1. 打开一个命令提示符并切换到/home文件夹

   在Linux或者Mac上：

   ```shell
   $ cd
   ```

   在windows上：

   ```shell
   C:\> cd %HOMEPATH%
   ```

   在接下去的教程里面会用`$`来代表提示符。指令在windows上也适用。

2. 在命令提示符下，为你的代码创建一个名为generics的目录

   ```shell
   $ mkdir generics
   $ cd generics
   ```

3. 创建一个module来存放你的代码

   执行`go mod init`指令，参数为你新代码的module路径
   
   ```go
   $ go mod init example/generics
   go: creating new go.mod: module example/generics
   ```

   > 备注：对生产环境，你会指定一个更符合你自己需求的module路径。更多的请看[依赖管理](https://go.dev/doc/modules/managing-dependencies) 

接下来，你会增加一些简单的和maps相关的代码。

<h2 id="add_non_genertic_function"> 添加普通函数 </h2>

在这一步中，你将添加两个函数，每个函数都会累加 map 中的值 ，并返回总和。

你将声明两个函数而不是一个，因为你要处理两种不同类型的map：一个存储int64类型的值，另一个存储float64类型的值。

### 写代码

1. 用你的文本编辑器，在generics文件夹里面创建一个叫main.go的文件。你将会在这个文件内写你的Go代码。

2. 到main.go文件的上方，粘贴如下的包的声明。

   ```go
   package main
   ```

   一个独立的程序（相对于一个库）总是在main包中。

3. 在包的声明下面，粘贴以下两个函数的声明。

   ```go
   // SumInts adds together the values of m.
   func SumInts(m map[string]int64) int64 {
       var s int64
       for _, v := range m {
           s += v
       }
       return s
   }
   
   // SumFloats adds together the values of m.
   func SumFloats(m map[string]float64) float64 {
       var s float64
       for _, v := range m {
           s += v
       }
       return s
   }
   ```

   在这段代码中，你：

   - 声明两个函数，将一个map的值加在一起，并返回总和。
     - SumFloats接收一个map，key为string类型，value为floa64类型。
     - SumInt接收一个map，key为string类型，value为int64类型。

4. 在main.go的顶部，包声明的下面，粘贴以下main函数，用来初始化两个map，并在调用你在上一步中声明的函数时将它们作为参数。

   ```go
   func main() {
   // Initialize a map for the integer values
   ints := map[string]int64{
       "first": 34,
       "second": 12,
   }
   
   // Initialize a map for the float values
   floats := map[string]float64{
       "first": 35.98,
       "second": 26.99,
   }
   
   fmt.Printf("Non-Generic Sums: %v and %v\n",
       SumInts(ints),
       SumFloats(floats))
   }
   ```

   在这段代码中，你：

   - 初始化一个key为string，value为`float64`的map和一个key为string，value为`int64`的map，各有2条数据；
   - 调用之前声明的两个方法来获取每个map的值的总和；
   - 打印结果。

5. 靠近main.go顶部，仅在包声明的下方，导入你刚刚写的代码所需要引用的包。

   第一行代码应该看起来如下所示：

   ```go
   package main
   import "fmt"
   ```

6. 保存main.go.

### 运行代码

在main.go所在目录下，通过命令行运行代码

```shell
$ go run .
Non-Generic Sums: 46 and 62.97
```

有了泛型，你可以只写一个函数而不是两个。接下来，你将为maps添加一个泛型函数，来允许接收整数类型或者是浮点数类型。

<h2 id="add_generic_function"> 添加泛型函数处理多种类型 </h2>

在这一节，你将会添加一个泛型函数来接收一个map，可能值是整数类型或者浮点数类型的map，有效地用一个函数替换掉你刚才写的2个函数。

为了支持不同类型的值，这个函数需要有一个方法来声明它所支持的类型。另一方面，调用代码将需要一种方法来指定它是用整数还是浮点数来调用。

为了实现上面的描述，你将会声明一个除了有普通函数参数，还有`类型参数`的函数。这个类型参数实现了函数的通用性，使得它可以处理多个不同的类型。你将会用`类型参数`和普通函数参数来调用这个泛型函数。

每个类型参数都有一个`类型约束`，类似于每个类型参数的meta-type。每个类型约束都指定了调用代码时每个对应输入参数的可允许的类型。

虽然类型参数的约束通常代表某些类型，但是在编译的时候类型参数只代表一个类型-在调用代码时作为类型参数。如果类型参数的类型不被类型参数的约束所允许，代码则无法编译。

需要记住的是类型参数必须满足泛型代码对它的所有的操作。举个例子，如果你的代码尝试去做一些string的操作(比如索引)，而这个类型参数包含数字的类型，那代码是无法编译的。

在下面你要编写的代码里，你会使用允许整数或者浮点数类型的限制。

### 写代码

1. 在你之前写的两个函数的下方，粘贴下面的泛型函数

   ```go
   // SumIntsOrFloats sums the values of map m. It supports both int64 and float64
   // as types for map values.
   func SumIntsOrFloats[K comparable, V int64 | float64](m map[K]V) V {
       var s V
       for _, v := range m {
           s += v
       }
       return s
   }
   ```

   在这段代码里，你：

   - 声明了一个带有2个类型参数(方括号内)的SumIntsOrFloats函数，K和V，一个使用类型参数的参数，类型为map[K]V的参数m。
     - 为K类型参数指定可比较的类型约束。事实上，针对此类情况，在Go里面可比较的限制是会提前声明。它允许任何类型的值可以作为比较运算符==和!=的操作符。在Go里面，map的key是需要可比较的。因此，将K声明为可比较的是很有必要的，这样你就可以使用K作为map变量的key。这样也保证了调用代码方使用一个被允许的类型做map的key。
     - 为V类型参数指定一个两个类型合集的类型约束：int64和float64。使用`|`指定了2个类型的合集，表示约束允许这两种类型。任何一个类型都会被编译器认定为合法的传参参数。
     - 指定参数m为类型map[K]V，其中K和V的类型已经指定为类型参数。注意到因为K是可比较的类型，所以map[K]V是一个有效的map类型。如果我们没有声明K是可比较的，那么编译器会拒绝对map[K]V的引用。

2. 在main.go里，在你现在的代码下方，粘贴如下代码：

   ```go
   fmt.Printf("Generic Sums: %v and %v\n",
       SumIntsOrFloats[string, int64](ints),
       SumIntsOrFloats[string, float64](floats))
   ```

   在这段代码里，你：

   - 调用你刚才声明的泛型函数，传递你创建的每个map。

   - 指定类型参数-在方括号内的类型名称-来明确你所调用的函数中应该用哪些类型来替代类型参数。

     你将会在下一节看到，你通常可以在函数调用时省略类型参数。Go通常可以从代码里推断出来。

   - 打印函数返回的总和。

### 运行代码

在main.go所在目录下，通过命令行运行代码

```shell
$ go run .
Non-Generic Sums: 46 and 62.97
Generic Sums: 46 and 62.97
```

为了运行你的代码，在每次调用的时候，编译器都会用该调用中指定的具体类型替换类型参数。

在调用你写的泛型函数时，你指定了类型参数来告诉编译器用什么类型来替换函数的类型参数。正如你将在下一节所看到的，在许多情况下，你可以省略这些类型参数，因为编译器可以推断出它们。

<h2 id="delete_type_arguement"> 当调用泛型函数时移除类型参数 </h2>

在这一节，你会添加一个泛型函数调用的修改版本，通过一个小的改变来简化代码。在这个例子里你将移除掉不需要的类型参数。

当Go编译器可以推断出你要使用的类型时，你可以在调用代码中省略类型参数。编译器从函数参数的类型中推断出类型参数。

注意这不是每次都可行的。举个例子，如果你需要调用一个没有参数的泛型函数，那么你需要在调用函数时带上类型参数。

### 写代码

- 在main.go的代码下方，粘贴下面的代码。

  ```go
  fmt.Printf("Generic Sums, type parameters inferred: %v and %v\n",
      SumIntsOrFloats(ints),
      SumIntsOrFloats(floats))
  ```

  在这段代码里，你：

  - 调用泛型函数，省略类型参数。

### 运行代码

在main.go所在目录下，通过命令行运行代码

```shell
$ go run .
Non-Generic Sums: 46 and 62.97
Generic Sums: 46 and 62.97
Generic Sums, type parameters inferred: 46 and 62.97
```

接下来，你将通过把整数和浮点数的合集定义到一个你可以重复使用的类型约束中，比如从其他的代码，来进一步简化这个函数。

<h2 id="declare_type_constrant"> 声明类型约束 </h2>

在最后一节中，你将把你先前定义的约束移到它自己的interface中，这样你就可以在多个地方重复使用它。以这种方式声明约束有助于简化代码，尤其当一个约束越来越复杂的时候。

你将类型参数定义为一个interface。约束允许任何类型实现这个interface。举个例子，如果你定义了一个有三个方法的类型参数interface，然后用它作为一个泛型函数的类型参数，那么调用这个函数的类型参数必须实现这些方法。

你将在本节中看到，约束interface也可以指代特定的类型。

### 写代码

1. 在main函数上面，紧接着import下方，粘贴如下代码来定义类型约束。

   ```go
   type Number interface {
       int64 | float64
   }
   ```

   在这段代码里，你：

   - 声明一个Number interface类型作为类型限制

   - 在interface内声明int64和float64的合集

     本质上，你是在把函数声明中的合集移到一个新的类型约束中。这样子，当你想要约束一个类型参数为int64或者float64，你可以使用Number interface而不是写 int64 | float64。

2. 在你已写好的函数下方，粘贴如下泛型函数，SumNumbers。

   ```go
   // SumNumbers sums the values of map m. Its supports both integers
   // and floats as map values.
   func SumNumbers[K comparable, V Number](m map[K]V) V {
       var s V
       for _, v := range m {
           s += v
       }
       return s
   }
   ```

   在这段代码，你：

   - 声明一个泛型函数，其逻辑与你之前声明的泛型函数相同，但是是使用新的interface类型作为类型参数而不是合集。和之前一样，你使用类型参数作为参数和返回类型。

3. 在main.go，在你已写完的代码下方，粘贴如下代码。

   ```go
   fmt.Printf("Generic Sums with Constraint: %v and %v\n",
       SumNumbers(ints),
       SumNumbers(floats))
   ```

   在这段代码里，你：

   - 每个map依次调用SumNumbers，并打印数值的总和。
   - 与上一节一样，你可以在调用泛型函数时省略类型参数（方括号中的类型名称）。Go编译器可以从其他参数中推断出类型参数。

### 运行代码

在main.go所在目录下，通过命令行运行代码

```shell
$ go run .
Non-Generic Sums: 46 and 62.97
Generic Sums: 46 and 62.97
Generic Sums, type parameters inferred: 46 and 62.97
Generic Sums with Constraint: 46 and 62.97
```

<h2 id="conclusion"> 总结 </h2>

完美结束！你刚才已经给你自己介绍了Go的泛型。

如果你想继续试验，你可以尝试用整数约束和浮点数约束来写Number interface，来允许更多的数字类型。

建议阅读的相关文章：

- [Go Tour](https://tour.golang.org/welcome/1) 是一个很好的，手把手教Go基础的介绍。
- 你可以在 [Effective Go](https://go.dev/doc/effective_go) 和 [How to write Go code](https://go.dev/doc/code) 中找到非常实用的GO的练习。

<h2 id="complete_code"> 完整代码 </h2>

你可以在Go playground运行这个代码。在playground只需要点击`Run`按钮即可。

```go
package main

import "fmt"

type Number interface {
    int64 | float64
}

func main() {
    // Initialize a map for the integer values
    ints := map[string]int64{
        "first": 34,
        "second": 12,
    }

    // Initialize a map for the float values
    floats := map[string]float64{
        "first": 35.98,
        "second": 26.99,
    }

    fmt.Printf("Non-Generic Sums: %v and %v\n",
        SumInts(ints),
        SumFloats(floats))

    fmt.Printf("Generic Sums: %v and %v\n",
        SumIntsOrFloats[string, int64](ints),
        SumIntsOrFloats[string, float64](floats))

    fmt.Printf("Generic Sums, type parameters inferred: %v and %v\n",
        SumIntsOrFloats(ints),
        SumIntsOrFloats(floats))

    fmt.Printf("Generic Sums with Constraint: %v and %v\n",
        SumNumbers(ints),
        SumNumbers(floats))
}

// SumInts adds together the values of m.
func SumInts(m map[string]int64) int64 {
    var s int64
    for _, v := range m {
        s += v
    }
    return s
}

// SumFloats adds together the values of m.
func SumFloats(m map[string]float64) float64 {
    var s float64
    for _, v := range m {
        s += v
    }
    return s
}

// SumIntsOrFloats sums the values of map m. It supports both floats and integers
// as map values.
func SumIntsOrFloats[K comparable, V int64 | float64](m map[K]V) V {
    var s V
    for _, v := range m {
        s += v
    }
    return s
}

// SumNumbers sums the values of map m. Its supports both integers
// and floats as map values.
func SumNumbers[K comparable, V Number](m map[K]V) V {
    var s V
    for _, v := range m {
        s += v
    }
    return s
}
```
