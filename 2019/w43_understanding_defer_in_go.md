# 理解 Go 语言中的 defer  

- 原文地址：https://www.digitalocean.com/community/tutorials/understanding-defer-in-go
- 原文作者：Gopher Guides
- 本文永久链接：https://github.com/gocn/translator/blob/master/2019/w43_understanding_defer_in_go.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对者：[cvley](https://github.com/cvley)
---

![](../static/images/w43_understanding_defer_in_go/Go_TutorialIllo_Social.png)  

##  介绍  
Go 中有许多通用的流程控制关键词例如`if`，`switch`，`for`等等，这些在其他的编程语言中也是可以找到的。但有一个关键词是绝大多数编程语言所不拥有的——`defer`，尽管它并不通用，但是接下来你将会明白它在你的程序中是多么的实用。

`defer`语句最主要的用处之一就是清理资源，例如关闭打开的文件、网络连接和[数据库句柄](https://en.wikipedia.org/wiki/Handle_(computing))等。当你的程序用完这些资源后，请务必关闭它们，以免耗尽程序的资源限制，并允许其他程序访问这些资源。`defer`语句通过靠近打开文件/资源调用的位置这样的方式，使我们的代码更整洁，并且能够更少出错。

在这篇文章，我们将了解到如何恰当的使用`defer`语句来清理资源以及使用时会犯的一些常见错误。  

## 什么是`defer`语句  
`defer`语句将其之后的[函数](https://www.digitalocean.com/community/tutorials/how-to-define-and-call-functions-in-go)调用添加到堆栈上，当该语句所在的函数返回时，将执行堆栈中所有的函数调用。由于这些调用位于堆栈上，因此将按照后进先出的顺序进行调用。  

让我们通过`defer`打印一些文本来看看工作原理：

```go
package main

import "fmt"

func main() {
    defer fmt.Println("Bye")
    fmt.Println("Hi")
    }
```
在 main 函数中，有两个语句。第一条语句以`defer`关键字开头，后跟一条 print 语句打印`Bye`。下一行语句会打印出`Hi`。  
如果运行程序，将看到以下输出：  

```plain
Hi
Bye
```
可以看到，先打印的是`Hi`。这是因为以`defer`为前缀的语句直到该函数的末尾，才被调用。

让我们再来看一下该程序，这次我们添加来一些注释以帮助我们理解发生了什么。

```go
package main

import "fmt"

func main() {
    // defer语句执行，将fmt.Println("Bye")放在函数返回前要执行的列表上
    defer fmt.Println("Bye")

    // 下一行会立刻执行
    fmt.Println("Hi")

    // 在函数结尾处，调用fmt.Println*("Bye")
}
```
理解`defer`的关键在于，当执行`defer`语句时，会立刻检查`defer`后函数的参数，并将其后的语句放在函数返回时要调用的列表上。  
尽管此代码说明了`defer`运行的顺序，但这并不是编写 Go 程序时使用的典型方式。我们通常会使用`defer`来清理资源，例如文件句柄的关闭等。接下来让我们看看要如何做。  

## 使用`defer`清理资源  
在 Go 中使用`defer`来清理资源是非常普遍的。首先我们来看看一个将字符串写入文件但不使用`defer`清理资源的程序：

```go
package main

import (
    "io"
    "log"
    "os"
)

func main() {
    if err := write("readme.txt", "This is a readme file"); err != nil {
        log.Fatal("failed to write file:", err)
    }
}

func write(fileName string, text string) error {
    file, err := os.Create(fileName)
    if err != nil {
        return err
    }
    _, err = io.WriteString(file, text)
    if err != nil {
        return err
    }
    file.Close()
    return nil
}
```
在这个程序中，有一个叫做`write`的函数，此函数首先将会尝试创建文件，如果出现错误，那么将会返回错误并且退出函数。接下来将尝试将字符串“`This is a readme file`”写入指定的文件，如果出现错误，则返回错误并退出函数。然后，该函数将尝试关闭文件并将资源释放。最后，该函数返回`nil`以表明该函数已正确执行。  

尽管此代码能够执行，但存在一个细微的错误。如果调用`io.WriteString`失败，该函数将返回但并不会关闭文件将资源释放。  

我们仍然可以不添加`defer`来修复这个问题，只需再添加一条`file.Close()`语句：

```go
package main

import (
    "io"
    "log"
    "os"
)

func main() {
    if err := write("readme.txt", "This is a readme file"); err != nil {
        log.Fatal("failed to write file:", err)
    }
}

func write(fileName string, text string) error {
    file, err := os.Create(fileName)
    if err != nil {
        return err
    }
    _, err = io.WriteString(file, text)
    if err != nil {
        file.Close()
        return err
    }
    file.Close()
    return nil
}
```
这样，即使调用`io.WriteString`失败，我们仍然可以关闭文件。这是一个相对容易发现和修复的 bug，但是当函数更复杂时，我们很有可能会忽略。  

使用`defer`语句，我们可以不用添加两条`file.Close()`，就可以保证不论程序执行了哪个分支都可以关闭文件。  

下面是使用`defer`的版本：

```go
package main

import (
    "io"
    "log"
    "os"
)

func main() {
    if err := write("readme.txt", "This is a readme file"); err != nil {
        log.Fatal("failed to write file:", err)
    }
}

func write(fileName string, text string) error {
    file, err := os.Create(fileName)
    if err != nil {
        return err
    }
    defer file.Close()
    _, err = io.WriteString(file, text)
    if err != nil {
        return err
    }
    return nil
}
```
这次我们增加了一行代码：`defer file.Close()`，来告诉编译器在退出函数`write`之前应该执行`file.Close()`。  

现在已经可以确保，即使我们以后增加更多的代码或者创建更多的分支，都可以完成清理和关闭文件。  

然而，添加`defer`也会引入另一个 bug。我们从未检查`Close()`方法可能存在的潜在错误。这是因为当使用`defer`时，无法将任何返回值传递回我们的函数。  

在 Go 中，`Close()`多次调用而不影响程序的行为是被视为安全且可以接受的。如果`Close()`要返回错误，它会在第一次调用时返回。这样，我们可以在函数的成功执行路径中显式调用它。  

让我们看看如何既可以使用`defer`调用`Close()`，又可以在遇到错误时报告错误：

```go
package main

import (
    "io"
    "log"
    "os"
)

func main() {
    if err := write("readme.txt", "This is a readme file"); err != nil {
        log.Fatal("failed to write file:", err)
    }
}

func write(fileName string, text string) error {
    file, err := os.Create(fileName)
    if err != nil {
        return err
    }
    defer file.Close()
    _, err = io.WriteString(file, text)
    if err != nil {
        return err
    }

    return file.Close()
}
```
这个程序唯一改变的地方是在最后一行返回的是`file.Close()`,如果`Close()`导致了错误，那么会按我们的预期将错误返回给调用函数。同时我们注意到，`defer file Close()`语句将在`return`语句之后执行，这就意味着`file.Close()`将被调用两次。虽然这不是最理想的方法，但是这是可以接受的，因为它不会对程序产生任何副作用。  

但是，如果我们在函数中更早的收到了错误，比如在调用`WriteString`时，那么函数将会返回其导致的错误，同时因为`defer`，会再执行`file.Close()`。这样即使`file.Close()`会出错，但是它不再是我们关注的对象，它更有可能告诉我们问题的源头在哪里。

到目前为止，我们已经看到如何用`defer`来确保资源得以清理。接下来，将展示如何用多个`defer`来清理多个资源。  

## 多条`defer`语句  
在一个函数中有多条`defer`语句也是很常见的。让我们创建一个仅含`defer`语句的程序，来看看会发生什么事情：

```go
package main

import "fmt"

func main() {
    defer fmt.Println("one")
    defer fmt.Println("two")
    defer fmt.Println("three")
}
```
如果运行该程序，我们将收到以下输出：

```plain
three
two
one
```
可以看到，输出顺序与我们调用`defer`语句的顺序是相反的。这是因为在堆栈中，每个被调用的`defer`语句都会堆叠在前一个语句之上，然后在函数退出时反向调用（*后进先出*）。

你可以根据需要在函数中进行任意数量的`defer`调用，但是要记住，所有调用都将以与执行相反的顺序进行调用。

现在我们理解了多条`defer`语句执行的顺序，那么让我们看看如何使用多个`defer`来清理多个资源。我们将创建一个程序，该程序打开一个文件，对其进行写入，然后再次打开并将内容复制到另一个文件。

```go
package main

import (
    "fmt"
    "io"
    "log"
    "os"
)

func main() {
    if err := write("sample.txt", "This file contains some sample text."); err != nil {
        log.Fatal("failed to create file")
    }

    if err := fileCopy("sample.txt", "sample-copy.txt"); err != nil {
        log.Fatal("failed to copy file: %s")
    }
}

func write(fileName string, text string) error {
    file, err := os.Create(fileName)
    if err != nil {
        return err
    }
    defer file.Close()
    _, err = io.WriteString(file, text)
    if err != nil {
        return err
    }

    return file.Close()
}

func fileCopy(source string, destination string) error {
    src, err := os.Open(source)
    if err != nil {
        return err
    }
    defer src.Close()

    dst, err := os.Create(destination)
    if err != nil {
        return err
    }
    defer dst.Close()

    n, err := io.Copy(dst, src)
    if err != nil {
        return err
    }
    fmt.Printf("Copied %d bytes from %s to %s\n", n, source, destination)

    if err := src.Close(); err != nil {
        return err
    }

    return dst.Close()
}
```
我们添加了一个名为`fileCopy`的新函数。在此函数中，首先打开要复制的源文件，并检查是否在打开文件时收到错误。如果出错，`return`该错误并退出函数。否则，通过`defer`来关闭刚刚打开的源文件。

接下来，我们创建目标文件，同样检查是否在创建文件时收到错误。若出错，则`return`该错误并退出函数，否则，通过`defer`来关闭刚刚打开的目标文件。现在，函数中有两条`defer`语句，当函数退出其作用域时将被调用。

现在我们打开了两个文件，使用`Copy()`源文件的数据写入到目标文件。如果成功，我们将尝试关闭两个文件。如果在关闭任何一个文件时收到错误，将错误`return`并退出函数。

可以注意到，尽管`defer`语句将会调用`Close()`，我们还是显式调用了`Close()`，这是为了确保即使关闭文件时出错，我们仍可以捕捉到该错误并报告出来。这样的程序也能够确保无论出现了什么错误导致函数退出，都可以使文件得以正确的关闭。

## 总结  
在这篇文章中，我们了解到`defer`语句以及如何使用它来确保程序中的资源清理。正确清理系统资源将使你的程序使用更少的内存并获得更好的性能。要了解有关在何处`defer`使用的更多信息，请阅读有关 Handling Panics 的文章，或浏览[《How To Code in Go》](https://www.digitalocean.com/community/tutorial_series/how-to-code-in-go)系列。
