# Understanding defer in Go
- 原文地址：https://www.digitalocean.com/community/tutorials/understanding-defer-in-go
- 原文作者：Gopher Guides
- 本文永久链接：https://github.com/gocn/translator/blob/master/2019/w43_understanding_defer_in_go.md
- 译者：lsj1342
- 校对者：

### Introduction

Go has many of the common control-flow keywords found in other programming languages such as `if`, `switch`, `for`, etc. One keyword that isn’t found in most other programming languages is `defer`, and though it’s less common you’ll quickly see how useful it can be in your programs.

One of the primary uses of a `defer` statement is for cleaning up resources, such as open files, network connections, and [database handles](https://en.wikipedia.org/wiki/Handle_(computing)). When your program is finished with these resources, it’s important to close them to avoid exhausting the program’s limits and to allow other programs access to those resources. `defer` makes our code cleaner and less error prone by keeping the calls to close the file/resource in proximity to the open call.

In this article we will learn how to properly use the `defer` statement for cleaning up resources as well as several common mistakes that are made when using `defer`.

What is a `defer` Statement
---------------------------

A `defer` statement adds the [function](https://www.digitalocean.com/community/tutorials/how-to-define-and-call-functions-in-go) call following the `defer` keyword onto a stack. All of the calls on that stack are called when the function in which they were added returns. Because the calls are placed on a stack, they are called in last-in-first-out order.

Let’s look at how `defer` works by printing out some text:

main.go

```plain
package main

import "fmt"

func main() {
    defer fmt.Println("Bye")
    fmt.Println("Hi")
}


```

In the `main` function, we have two statements. The first statement starts with the `defer` keyword, followed by a `print` statement that prints out `Bye`. The next line prints out `Hi`.

If we run the program, we will see the following output:

```plain
Output

Hi
Bye


```

Notice that `Hi` was printed first. This is because any statement that is preceded by the `defer` keyword isn’t invoked until the end of the function in which `defer` was used.

Let’s take another look at the program, and this time we’ll add some comments to help illustrate what is happening:

main.go

```plain
package main

import "fmt"

func main() {
    // defer statement is executed, and places
    // fmt.Println("Bye") on a list to be executed prior to the function returning
    defer fmt.Println("Bye")

    // The next line is executed immediately
    fmt.Println("Hi")

    // fmt.Println*("Bye") is now invoked, as we are at the end of the function scope
}


```

The key to understanding `defer` is that when the `defer` statement is executed, the arguments to the deferred function are evaluated immediately. When a `defer` executes, it places the statement following it on a list to be invoked prior to the function returning.

Although this code illustrates the order in which `defer` would be run, it’s not a typical way it would be used when writing a Go program. It’s more likely we are using `defer` to clean up a resource, such as a file handle. Let’s look at how to do that next.

Using `defer` to Clean Up Resources
-----------------------------------

Using `defer` to clean up resources is very common in Go. Let’s first look at a program that writes a string to a file but does not use `defer` to handle the resource clean-up:

main.go

```plain
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

In this program, there is a function called `write` that will first attempt to create a file. If it has an error, it will return the error and exit the function. Next, it tries to write the string `This is a readme file` to the specified file. If it receives an error, it will return the error and exit the function. Then, the function will try to close the file and release the resource back to the system. Finally the function returns `nil` to signify that the function executed without error.

Although this code works, there is a subtle bug. If the call to `io.WriteString` fails, the function will return without closing the file and releasing the resource back to the system.

We could fix the problem by adding another `file.Close()` statement, which is how you would likely solve this in a language without `defer`:

main.go

```plain
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

Now even if the call to `io.WriteString` fails, we will still close the file. While this was a relatively easy bug to spot and fix, with a more complicated function, it may have been missed.

Instead of adding the second call to `file.Close()`, we can use a `defer` statement to ensure that regardless of which branches are taken during execution, we always call `Close()`.

Here’s the version that uses the `defer` keyword:

main.go

```plain
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

This time we added the line of code: `defer file.Close()`. This tells the compiler that it should execute the `file.Close` prior to exiting the function `write`.

We have now ensured that even if we add more code and create another branch that exits the function in the future, we will always clean up and close the file.

However, we have introduced yet another bug by adding the defer. We are no longer checking the potential error that can be returned from the `Close` method. This is because when we use `defer`, there is no way to communicate any return value back to our function.

In Go, it is considered a safe and accepted practice to call `Close()` more than once without affecting the behavior of your program. If `Close()` is going to return an error, it will do so the first time it is called. This allows us to call it explicitly in the successful path of execution in our function.

Let’s look at how we can both `defer` the call to `Close`, and still report on an error if we encounter one.

main.go

```plain
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

The only change in this program is the last line in which we return `file.Close()`. If the call to `Close` results in an error, this will now be returned as expected to the calling function. Keep in mind that our `defer file.Close()` statement is also going to run after the `return` statement. This means that `file.Close()` is potentially called twice. While this isn’t ideal, it is an acceptable practice as it should not create any side effects to your program.

If, however, we receive an error earlier in the function, such as when we call `WriteString`, the function will return that error, and will also try to call `file.Close` because it was deferred. Although `file.Close` may (and likely will) return an error as well, it is no longer something we care about as we received an error that is more likely to tell us what went wrong to begin with.

So far, we have seen how we can use a single `defer` to ensure that we clean up our resources properly. Next we will see how we can use multiple `defer` statements for cleaning up more than one resource.

Multiple `defer` Statements
---------------------------

It is normal to have more than one `defer` statement in a function. Let’s create a program that only has `defer` statements in it to see what happens when we introduce multiple defers:

main.go

```plain
package main

import "fmt"

func main() {
    defer fmt.Println("one")
    defer fmt.Println("two")
    defer fmt.Println("three")
}


```

If we run the program, we will receive the following output:

```plain
Output

three
two
one


```

Notice that the order is the opposite in which we called the `defer` statements. This is because each deferred statement that is called is stacked on top of the previous one, and then called in reverse when the function exits scope (_Last In, First Out_).

You can have as many deferred calls as needed in a function, but it is important to remember they will all be called in the opposite order they were executed.

Now that we understand the order in which multiple defers will execute, let’s see how we would use multiple defers to clean up multiple resources. We’ll create a program that opens a file, writes to it, then opens it again to copy the contents to another file.

main.go

```plain
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

We added a new function called `fileCopy`. In this function, we first open up our source file that we are going to copy from. We check to see if we received an error opening the file. If so, we `return` the error and exit the function. Otherwise, we `defer` the closing of the source file we just opened.

Next we create the destination file. Again, we check to see if we received an error creating the file. If so, we `return` that error and exit the function. Otherwise, we also `defer` the `Close()` for the destination file. We now have two `defer` functions that will be called when the function exits its scope.

Now that we have both files open, we will `Copy()` the data from the source file to the destination file. If that is successful, we will attempt to close both files. If we receive an error trying to close either file, we will `return` the error and exit function scope.

Notice that we explicitly call `Close()` for each file, even though the `defer` will also call `Close()`. This is to ensure that if there is an error closing a file, we report the error. It also ensures that if for any reason the function exits early with an error, for instance if we failed to copy between the two files, that each file will still try to close properly from the deferred calls.

Conclusion
----------

In this article we learned about the `defer` statement, and how it can be used to ensure that we properly clean up system resources in our program. Properly cleaning up system resources will make your program use less memory and perform better. To learn more about where `defer` is used, read the article on Handling Panics, or explore our entire [How To Code in Go series](https://www.digitalocean.com/community/tutorial_series/how-to-code-in-go).