New in Go 1.20: wrapping multiple errors

- 原文地址：https://lukas.zapletalovi.com/posts/2022/wrapping-multiple-errors/
- 原文作者：Lukáš Zapletal
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w50_Wrapping_multiple_errors
- 译者：[haoheipi](https://github.com/haoheipi)
- 校对：

Go 1.20, which is expected to be released in February 2023, comes with a small change that can possibly improve error handling in applications which heavily use error wrapping. Let’s take a look how it looks, but first, short recap of what error wrapping is. Feel free to skip to “New in Go 1.20” section down below for the news.

Errors in Go are values which implements a very simple interface:

```
type error interface {
    Error() string
}
```

Error types can be anything, from `string` itself to `int`, but very often they are `struct` types. This example is from the standard library:

```
type err struct {
    s string
}

func (e *err) Error() string {
    return e.s
}
```

To check an error in Go, you simply compare a value (in this case an `int` value):

```
if err == io.EOF {
    // ...
}
```

The second common thing is to check error’s type, that is little bit more code to write tho:

```
if nerr, ok := err.(net.Error) {
    // ... (use nerr which is a net.Error)
}
```

In the example above, the type assertion tests the `err` value for type `net.Error` creating a new variable `nerr` which can be used in the if statement. Errors in Go are simple to understand, simple to use use and efficient.

## Error wrapping

Now, starting from Go 1.13, wrapping was introduced. Wrapping allows to embed errors into other errors, just like wrapping exceptions in other languages. This is very useful: a function that encounters “record not found” error can add more context information to the message like “unknown user: record not found”.

The interesting idea behind error wrapping design in Go is that the contract does not care about error types, structure or how they are created. What only matters is the unwrapping procedure and conversion to string because that is what is needed. It is very simple then: error types with unwrapping support must implement `Unwrap() error` method. There is no (named) interface in the standard library to show you since interfaces are implemented implicitly and there is no need to have one. Let`s write one just for the purpose of this post:

```
type WrappedError interface {
    Unwrap() error
}
```

Let’s take a look how wrapped errors are implemented in the Go standard library (package fmt actually):

```
type wrapError struct {
    msg string
    err error
}

func (e *wrapError) Error() string {
    return e.msg
}

func (e *wrapError) Unwrap() error {
    return e.err
}
```

Since errors are types which implement `Error() string` and there is nothing wrong saying that errors in Go actually are “strings” in the end, a good mechanism of creating these strings is needed. This is where function `fmt.Errorf` from standard library comes into play:

```
var RecordNotFoundErr = errors.New("not found")
const name, id = "lzap", 13

werr := fmt.Errorf("unknown user %q (id %d): %w", name, id, recordNotFoundErr)

fmt.Println(werr.Error())
```

A special format verb `%w`, which can be only used once per call (more about this later), is meant for error arguments. Other than that, the function works similar to `fmt.Printf` function. The example above prints this:

```
unknown user "lzap" (id 13): not found
```

As you can see, wrapped errors are essentially a linked list. To unwrap an error use `errors.Unwrap` function which will return `nil` for the last error value in the list. To check for error type or value, the whole list needs to be walked which is not very practical for each error check. Luckily, there are two helper functions to do that.

To check for a value in wrapped errors list:

```
if errors.Is(err, RecordNotFoundErr) {
    // ...
}
```

To check for a specific type (a network error from the standard library in this case):

```
var nerr *net.Error
if errors.As(err, &nerr) {
    // ... (use nerr which is a *net.Error)
}
```

That summarizes error wrapping in Go 1.13 and later.

## New in Go 1.20

Let’s take a look what is actually new in Go 1.20 starting with function `errors.Join` which wraps list of errors via variadic arguments:

```
err1 := errors.New("err1")
err2 := errors.New("err2")

err := errors.Join(err1, err2)

fmt.Println(err)
```

This function can be useful for joining errors together when amount of errors is not known in advance. A good example would be gathering errors from goroutines. It is worth mentioning that the function concatenates errors from the list with newline characters. The above snippet prints:

```
err1
err2
```

This could be a problem for many applications or (logging) libraries which expects errors to be very often just strings without newline characters. Luckily, another change in Go 1.20 changes behavior of `fmt.Errorf`: the function now accepts multiple `%w` format specifiers:

```
err1 := errors.New("err1")
err2 := errors.New("err2")

err := fmt.Errorf("%w + %w", err1, err2)

fmt.Println(err)
```

What would previously result as a malformed format string now correctly prints:

```
err1 + err2
```

How this is possible when wrapped errors implements `Unwrap() error?` It turns out that there is a new mechanism in Go 1.20 standard library: an error type implementing `Unwrap() []error` function can wrap multiple errors instead of just one. Let’s take a look how this is implemented in the library:

```
type joinError struct {
    errs []error
}

func (e *joinError) Error() string {
    // concatenate errors with a new line character
}

func (e *joinError) Unwrap() []error {
    return e.errs
}
```

A theoretical interface, which does not exists in the standard library, looks like this:

```
type MultiWrappedError interface {
    Unwrap() []error
}
```

Since Go does not allow method overloading, each type can either implement `Unwrap() error` or `Unwrap() []error`, but not both. Remember when I mentioned that wrapped errors are essentially a linked list? Types which implement the former (the newly introduced) method actually form a linked tree and functions `errors.Is` and `errors.As` work the same, except now they need to traverse tree instead of list. According to documentation, the implementation performs pre-order, depth-first traversal.

That is really all that Go 1.20 brings to the table, it may seem like a small change, but it allows new ways how to handle errors efficiently and cleanly. Before I show a real-world example, let me summarize the new features:

- New `Unwrap []error` function contract allowing traversing through tree of errors.
- New `errors.Join` function which is a handy function to join two error string values (with a newline).
- Existing functions `errors.Is` and `errors.As` updated to work both on list and tree of errors.
- Existing function `fmt.Errorf` now accepts multiple `%w` format verbs.

## In practice

So it’s all great, but how can you leverage this in practice? In a small REST API microservice, we do all error handling through `errors.New` and `fmt.Errorf` wrapping various errors from DAO package (database), REST clients (other backend services) and other packages. The return HTTP status code should be either 2xx, 4xx or 5xx depending on the error status to follow the best REST API practices. One way to achieve this is to unwrap errors in the main HTTP handler and find out which kind of error is it.

However, with the multiple error wrapping, it is now possible to wrap both the root cause (e.g. database returning “no records found”) and also preferred HTTP code to return to the user (404 in this case). A working example could look like this:

```
package main

import (
	"errors"
	"fmt"
)

// common HTTP status codes
var NotFoundHTTPCode = errors.New("404")
var UnauthorizedHTTPCode = errors.New("401")

// database errors
var RecordNotFoundErr = errors.New("DB: record not found")
var AffectedRecordsMismatchErr = errors.New("DB: affected records mismatch")

// HTTP client errors
var ResourceNotFoundErr = errors.New("HTTP client: resource not found")
var ResourceUnauthorizedErr = errors.New("HTTP client: unauthorized")

// application errors (the new feature)
var UserNotFoundErr = fmt.Errorf("user not found: %w (%w)",
    RecordNotFoundErr, NotFoundHTTPCode)
var OtherResourceUnauthorizedErr = fmt.Errorf("unauthorized call: %w (%w)",
    ResourceUnauthorizedErr, UnauthorizedHTTPCode)

func handleError(err error) {
	if errors.Is(err, NotFoundHTTPCode) {
		fmt.Println("Will return 404")
	} else if errors.Is(err, UnauthorizedHTTPCode) {
		fmt.Println("Will return 401")
	} else {
		fmt.Println("Will return 500")
	}
	fmt.Println(err.Error())
}

func main() {
	handleError(UserNotFoundErr)
	handleError(OtherResourceUnauthorizedErr)
}
```

This will print:

```
Will return 404
user not found: DB: record not found (404)
Will return 401
unauthorized to call other service: HTTP client: unauthorized (401)
```

What may not look obvious from such artificial code snippet is that errors declarations are typically spread across many packages and it is not easy to keep track of all possible errors ensuring the required HTTP status codes. In this approach, all application-level wrapping errors declared in a single place also have HTTP codes wrapped inside them.

Note this was previously not possible in Go 1.19 or older because the `fmt.Errorf` function would only wrap the first error. The code does compile on 1.19 and does not even generate runtime panic, it won’t work however.

Obviously, the common HTTP status codes could easily be a new error type (based on `int` type) so the actual code could be easily extracted via `errors.As`, but I want to keep the example simple.

Feel free to play around with the code on Go Playground. Make sure to use “dev branch” or 1.20+ version of Go.

## Existing applications

When implementing the new feature into your application, beware of `errors.Unwrap` function. For error types that has `Unwrap() []error` it always returns `nil`:

```
err1 := errors.New("err1")
err2 := errors.New("err2")

err := errors.Join(err1, err2)
unwrapped := errors.Unwrap(err)

fmt.Println(unwrapped)
```

This prints `nil` and it is expected because of the Go 1.X compatibility promise. Just make sure to review unwrapping code when you introduce multiple wrapped errors. Luckily, most of error checking in typical Go code is done using `errors.Is` and `errors.As`.

Error wrapping is not the ultimate solution for all error handling in Go. It provides a clean approach to handle errors in typical Go applications tho and it might actually be all you need for simple application.

