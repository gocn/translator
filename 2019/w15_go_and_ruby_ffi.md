原文地址：https://c7.se/go-and-ruby-ffi/

# go 和 Ruby-FFI
如何用 go 写一个可以被 Ruby-FFI 加载的共享库。 

随着 [Go 1.5](https://golang.org/doc/go1.5) 的发布，我们有了新的构建模式（buildmode）c-shared，这个模式能让我们构建出 [Ruby-FFI](https://github.com/ffi/ffi) 可以加载的共享库。（当然，可以是其他任何可以加载共享库的语言，不单单是 ruby）

## 本文灵感
[Filippo Valsorda](https://twitter.com/filosottile) 已经写了一个非常好的文章 [《在 Go 1.5 中构建 Python 模块》](https://blog.filippo.io/building-python-modules-with-go-1-5/)，但我想用 Ruby ，而不是 Python。 

## 要求
需要已经安装了 [Go](http://golang.org/) 和 [Ruby](https://www.ruby-lang.org/) 哦。（这篇文章中，我用的是 Go 1.5 和 Ruby 2.2.3）

## 开始吧
我们的库文件要实现的是“复杂任务”，两个整型数求和，并返回结果。  
打开编辑器，开始敲上代码吧。

libsum.go
```go
package main

import "C"
//export add
func add(a, b int) int {
  return a + b
}
func main(){}
```
> 注意：只有通过 cgo `//export` 注释的函数才是可被调用的。除了 main 包外的，都会被忽略。

## 构建共享库
我们现在可以准备使用 `c-shared` 构建模式（buildmode） 来构建共享库了：
```bash
go build -buildmode=c-shared -o libsum.so libsum.go
```

## 使用 Ruby-FFI 载入 libsum.so
我们讨论的 Ruby-FFI 到底是什么？
> Ruby-FFI 是一个 Ruby 的扩展，我们可以通过编程方式载入动态库，绑定函数，并在 Ruby 代码中调用这些函数。

真棒！  
安装 `ffi` gem:
```bash
$ gem install ffi
Fetching: ffi-1.9.10.gem (100%)
Building native extensions.  This could take a while...
Successfully installed ffi-1.9.10
1 gem installed
```
现在我们可以使用 libsum.so 了
```ruby
require 'ffi'

module Sum
  extend FFI:Library
  ffi_lib './libsum.so'
  attatch_function :add, %i[int int], :int
end

puts Sum.add(15, 27) #=> 42
``` 
真棒，瞅瞅！  
桥豆麻袋，那内存管理呢？  
在 FFI wiki 中，有 [内存管理](https://github.com/ffi/ffi/wiki/Core-Concepts#memory-management) 的章节。
你可能还想读一读 [C? Go? Cgo!](https://blog.golang.org/c-go-cgo)。

## 奖励环节：直接从 [Crystal](http://crystal-lang.org/) 绑定（无需 FFI）
```ruby
@[Link(ldflags: "-L. -lsum")]
lib Sum
  fun add(a : Int32, b : Int32) : Int32
end

puts Sum.add(15, 27) #=> 42
```