原文地址：https://c7.se/go-and-ruby-ffi/

# Go and Ruby-FFI  
How to write a shared library in Go that can be loaded by Ruby-FFI.  
With the release of Go 1.5 we got access to a new buildmode called c-shared, which allows you to build shared libraries that Ruby-FFI can load. (Also, anything else that can load shared libraries)

## Inspiration
Filippo Valsorda has already written a very nice article on Building Python modules with Go 1.5 but I naturally wanted to use Ruby instead of Python.

## Requirements
You will need to have Go and Ruby installed. (I am using Go 1.5 and Ruby 2.2.3 in this article)

## Getting started  
Our library is going to perform the complicated task of adding up two integers, and then returning the resulting sum.

Break out your trusty editor and type in the following code:

libsum.go
```go
package main

import "C"

//export add
func add(a, b int) int {
  return a + b
}
func main() {}
```

> Note: The only callable symbols will be those functions exported using a cgo //export comment. Non-main packages are ignored.

## Building the shared library
We are now ready to use the c-shared buildmode in order to build the shared library:
```bash
go build -buildmode=c-shared -o libsum.so libsum.go
```
Using Ruby-FFI to load libsum.so  
So what is this Ruby-FFI thing you keep talking about?

Ruby-FFI is a ruby extension for programmatically loading dynamic libraries, binding functions within them, and calling those functions from Ruby code.

Ok, cool.

Install the ffi gem:
```bash
$ gem install ffi
Fetching: ffi-1.9.10.gem (100%)
Building native extensions.  This could take a while...
Successfully installed ffi-1.9.10
1 gem installed
```
Now you are ready to interface with libsum.so
require 'ffi'

```ruby
module Sum
  extend FFI::Library
  ffi_lib './libsum.so'
  attach_function :add, [:int, :int], :int
end

puts Sum.add(15, 27) #=> 42
```
Well, look at that!

Wait, what about memory management?  
There is a section on memory management in the FFI wiki.

You probably also want to read C? Go? Cgo!

## Bonus round: Binding directly from Crystal (No need for FFI)
```crystal
@[Link(ldflags: "-L. -lsum")]
lib Sum
  fun add(a : Int32, b : Int32) : Int32
end
puts Sum.add(15,27) #=> 42
```