# An overview of memory management in Go
- 原文地址：https://medium.com/safetycultureengineering/an-overview-of-memory-management-in-go-9a72ec7c76a8
- 原文作者： `Scott Gangemi`
- 本文永久链接： https://github.com/gocn/translator/blob/master/2021/w21_An_overview_of_memory_management_in_Go.md
- 译者：[haoheipi](https:/github.com/haoheipi)
- 校对：[]()

As programs run they write objects to memory. At some point these objects should be removed when they’re not needed anymore. This process is called **memory management**. This article aims to give an overview of memory management, and then dive deeper into how this is implemented in Go by using a garbage collector. Go has seen many changes to its memory management over the years, and will most likely see more in the future. If you’re reading this and you’re using a version of Go later than 1.16, some of this information may be outdated.

## Manual Memory Management

In a language like C the programmer will call a function such as `malloc` or `calloc` to write an object to memory. These functions return a pointer to the location of that object in heap memory. When this object is not needed anymore, the programmer calls the `free` function to use this chunk of memory again. This method of memory management is called **explicit deallocation** and is quite powerful. It gives the programmer greater control over the memory in use, which allows for some types of easier optimisation, particularly in low memory environments. However, it leads to two types of programming errors.

One, calling `free` prematurely which creates a **dangling pointer**. Dangling pointers are pointers that no longer point to valid objects in memory. This is bad because the program expects a defined value to live at a pointer. When this pointer is later accessed there’s no guarantee of what value exists at that location in memory. There may be nothing there, or some other value entirely. Two, failing to free memory at all. If the programmer forgets to free an object they may face a **memory leak** as memory fills up with more and more objects. This can lead to the program slowing down or crashing if it runs out of memory. Unpredictable bugs can be introduced into a program when memory has to be explicitly managed.

## Automatic Memory Management

This is why languages like Go offer **automatic dynamic memory management**, or more simply, **garbage collection**. Languages with garbage collection offer benefits like:

- increased security
- better portability across operating systems
- less code to write
- runtime verification of code
- bounds checking of arrays

Garbage collection has a performance overhead, but it isn’t as much as is often assumed. The tradeoff is that a programmer can focus on the business logic of their program and ensure it is fit for purpose, instead of worrying about managing memory.

A running program will store objects in two memory locations, the _heap_ and the _stack_. Garbage collection operates on the heap, not the stack. The stack is a LIFO data structure that stores function values. Calling another function from within a function pushes a new _frame_ onto the stack, which will contain the values of that function and so on. When the called function returns, its stack frame is popped off the stack. You might be familiar with the stack from when you’re debugging a crashed program. Most language compilers will return a stack trace to aid in debugging, which displays the functions that have been called leading up to that point.

> ![](../static/images/w21_An_overview_of_memory_management_in_Go/figure1.png)
Stacks can have values “pushed” onto the top, or “popped” from the top in a LIFO (last in, first out) fashion. [Image from Wikipedia.](https://en.wikipedia.org/wiki/Stack_(abstract_data_type))

In contrast, the heap contains values that are referenced outside of a function. For example, statically defined constants at the start of a program, or more complex objects, like Go structs. When the programmer defines an object that gets placed on the heap, the needed amount of memory is allocated and a pointer to it is returned. The heap is a graph where objects are represented as nodes which are referred to in code or by other objects in the heap. As a program runs, the heap will continue to grow as objects are added unless the heap is cleaned up.

>![](../static/images/w21_An_overview_of_memory_management_in_Go/figure2.png)
The heap starts from the roots and grows as more object are added.

## Garbage Collection in Go

Go [prefers to allocate memory on the stack](https://groups.google.com/g/golang-nuts/c/KJiyv2mV2pU/m/wdBUH1mHCAAJ?pli=1), so most memory allocations will end up there. This means that Go has a stack per goroutine and when possible Go will allocate variables to this stack. The Go compiler attempts to prove that a variable is not needed outside of the function by performing **escape analysis** to see if an object “escapes” the function. If the compiler can determine a variables [lifetime](https://www.memorymanagement.org/glossary/l.html#term-lifetime), it will be allocated to a stack. However, if the variable’s lifetime is unclear it will be allocated on the heap. Generally if a Go program has a pointer to an object then that object is stored on the heap. Take a look at this sample code:

```go
type myStruct struct {
  value int
}
var testStruct = myStruct{value: 0}
func addTwoNumbers(a int, b int) int {
  return a + b
}
func myFunction() {
  testVar1 := 123
  testVar2 := 456
  testStruct.value = addTwoNumbers(testVar1, testVar2)
}
func someOtherFunction() {
  // some other code
  myFunction()
  // some more code
}
```

For the purposes of this example, let’s imagine this is part of a running program because if this was the whole program the Go compiler would optimise this by allocating the variables into stacks. When the program runs:

1. `testStruct` is defined and placed on the heap in an available block of memory.
2. `myFunction` is executed and allocated a stack while the function is being executed. `testVar1` and `testVar2` are both stored on this stack.
3. When `addTwoNumbers` is called a new stack frame is pushed onto the stack with the two function arguments.
4. When `addTwoNumbers` finishes execution, it’s result is returned to myFunction and the stack frame for `addTwoNumbers` is popped off the stack as it’s no longer needed.
5. The pointer to `testStruct` is followed to the location on the heap containing it and the `value` field is updated.
6. `myFunction` exits and the stack created for it is cleaned up. The value for testStruct stays on the heap until garbage collection occurs.

`testStruct` is now on the heap and without analysis, the Go runtime doesn’t know if it’s still needed. To do this, Go relies on a garbage collector. Garbage collectors have two key parts, a **mutator** and a **collector**. The collector executes garbage collection logic and finds objects that should have their memory freed. The mutator executes application code and allocates new objects to the heap. It also updates existing objects on the heap as the program runs, which includes making some objects unreachable when they’re no longer needed.

>![](../static/images/w21_An_overview_of_memory_management_in_Go/figure3.png)
The object at the bottom has become unreachable due to changes made by the mutator. It should be cleaned up by the garbage collector.

## The implementation of Go’s garbage collector

Go’s garbage collector is a **non-generational concurrent**, **tri-color mark and sweep garbage collector**. Let’s break these terms down.

The [generational hypothesis](https://www.memorymanagement.org/glossary/g.html#term-generational-hypothesis) assumes that short lived objects, like temporary variables, are reclaimed most often. Thus, a generational garbage collector focuses on recently allocated objects. However, as mentioned before, compiler optimisations allow the Go compiler to allocate objects with a known lifetime to the stack. [This means fewer objects will be on the heap, so fewer objects will be garbage collected](https://groups.google.com/g/golang-nuts/c/KJiyv2mV2pU/m/wdBUH1mHCAAJ). This means that a generational garbage collector is not necessary in Go. So, Go uses a non-generational garbage collector. [Concurrent means that the collector runs at the same time as mutator threads](https://github.com/golang/go/blob/master/src/runtime/mgc.go#L7). Therefore, Go uses a non-generational concurrent garbage collector. Mark and sweep is the type of garbage collector and tri-color is the algorithm used to implement this

A mark and sweep garbage collector has two phases, unsurprisingly named **mark** and **sweep**. In the mark phase the collector traverses the heap and marks objects that are no longer needed. The follow-up sweep phase removes these objects. Mark and sweep is an indirect algorithm, as it marks live objects, and removes everything else.

>![](../static/images/w21_An_overview_of_memory_management_in_Go/figure4.gif)
A visualisation of a mark and sweep collector, [borrowed from here](https://spin.atomicobject.com/2014/09/03/visualizing-garbage-collection-algorithms/). There’s visualisations of other kinds of garbage collectors too if you’re interested.

[Go implements this in a few steps](https://github.com/golang/go/blob/master/src/runtime/mgc.go#L24):

Go has all goroutines reach a garbage collection safe point with a process called **stop the world**. This temporarily stops the program from running and turns a **write barrier** on to maintain data integrity on the heap. This allows for concurrency by allowing goroutines and the collector to run simultaneously.

Once all goroutines have the write barrier turned on, the Go runtime **starts the world** and has workers perform the garbage collection work.

Marking is implemented by using a **tri-color algorithm**. When marking begins, all objects are white except for the root objects which are grey. Roots are an object that all other heap objects come from, and are instantiated as part of running the program. The garbage collector begins marking by scanning stacks, globals and heap pointers to understand what is in use. When scanning a stack, the worker stops the goroutine and marks all found objects grey by traversing downwards from the roots. It then resumes the goroutine.

The grey objects are then enqueued to be turned black, which indicates that they’re still in use. Once all grey objects have been turned black, the collector will stop the world again and clean up all the white nodes that are no longer needed. The program can now continue running until it needs to clean up more memory again.

>![](../static/images/w21_An_overview_of_memory_management_in_Go/figure5.gif)
[This diagram from Wikipedia makes it a bit easier to understand](https://en.wikipedia.org/wiki/Tracing_garbage_collection#Tri-color_marking). The colours are a bit confusing, but white objects are light-grey, grey objects are yellow, and black objects are blue.

This process is initiated again once the program has allocated extra memory proportional to the memory in use. The `GOGC` environment variable determines this, and is set to 100 by default. [The Go source code describes this as:](https://github.com/golang/go/blob/master/src/runtime/mgc.go#L112)

> *If GOGC=100 and we’re using 4M, we’ll GC again when we get to 8M (this mark is tracked in next_gc variable). This keeps the GC cost in linear proportion to the allocation cost. Adjusting GOGC just changes the linear constant (and also the amount of extra memory used).*

Go’s garbage collector improves your efficiency by abstracting memory management into the runtime and is one part of what enables Go to be so performant. Go has built in tooling to allow you to optimise how garbage collection occurs in your program that you can investigate if you’re interested. For now, I hope you learnt a bit more about how garbage collection works and how it’s implemented in Go.

## References

- [Garbage Collection in Go: Part 1](https://www.ardanlabs.com/blog/2018/12/garbage-collection-in-go-part1-semantics.html)

- [Getting to Go: The Journey of Go’s Garbage Collector](https://blog.golang.org/ismmkeynote)

- [Go: How Does the Garbage Collector Mark the Memory?](https://medium.com/a-journey-with-go/go-how-does-the-garbage-collector-mark-the-memory-72cfc12c6976)

- [Golang: Cost of using the heap](https://medium.com/invalid-memory/golang-cost-of-using-the-heap-e70363469754)

- [Golang FAQ](https://golang.org/doc/faq#stack_or_heap)

- [Google Groups discussion, comment by Ian Lance Taylor](https://groups.google.com/g/golang-nuts/c/KJiyv2mV2pU/m/wdBUH1mHCAAJ)

- [Implementing memory management with Golang’s garbage collector](https://hub.packtpub.com/implementing-memory-management-with-golang-garbage-collector/)

- [Memory Management Reference](https://www.memorymanagement.org/)

- [Stack (abstract data type)](https://en.wikipedia.org/wiki/Stack_(abstract_data_type))

- [The Garbage Collection Handbook](https://gchandbook.org/)

- [Tracing garbage collection: Tri-color marking](https://en.wikipedia.org/wiki/Tracing_garbage_collection#Tri-color_marking)


