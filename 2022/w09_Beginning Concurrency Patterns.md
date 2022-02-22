# Beginning Concurrency Patterns

- 原文地址：https://benjiv.com/beginning-concurrency-patterns/
- 原文作者：Benjamin Vesterby
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2022/w09_Beginning Concurrency Patterns.md
- 译者：[朱亚光](https://github.com/zhuyaguang)
- 校对：

![Cover image](https://benjiv.com/beginning-concurrency-patterns/images/cover.webp)

In this post I will cover some best practices for building concurrent applications in Go using basic concurrency patterns and native primitives. The patterns themselves are applicable to any language, but for these examples we will use Go.

Clone the repository for this post to follow along

```shell
git clone https://github.com/benjivesterby/may2021-triangle-meetup.git
```

[TOC]

## Pipeline Pattern

A pipeline pattern  [1](https://benjiv.com/beginning-concurrency-patterns/#fn:1) [2](https://benjiv.com/beginning-concurrency-patterns/#fn:2) consists of a number of stages that are connected by a series of channels. The first stage is the source of the data, the last stage is the sink of the data. A good example of this would be a data pipeline where the first step mines the data, the subsequent steps cleans the data, and the final step stores the sanitized data in a database.

![A diagram showing an example Pipeline](https://benjiv.com/beginning-concurrency-patterns/images/pipeline.webp) **Example Pipeline**

As the diagram shows, the first stage is the source of the data, the last stage is the sink of the data. Here is a code example showing the pipeline pattern in action.

```golang
// Example of a pipeline pattern
func main() {
  // Call each function passing the output of the previous function
  // as the input to the next function

  d := []data{
    // ... data ...
  }

  // Create the pipeline
  sink(sanitize(source(d)))
}

func source(in []data) <-chan data {
  out := make(chan data)

  go func(in []data) {
    defer close(out)

    for _, d := range data {
      // Load data into the front of the pipeline
      out <- d
    }
  }(in)

  return out
}

func sanitize(in <-chan data) <-chan data {
  out := make(chan data)

  go func(in <-chan data, out chan<-data) {
    defer close(out)
    for {
      d, ok := <- in
      if !ok {
        return
      }
      // ... Do some work

      // push the data out
      out <- d
    }
  }(in, out)

  return out
}

func sink(in <-chan data) {
  for {
    d, ok := <- in
    if !ok {
      return
    }
    // ... Process the sanitized data
  }
}

```



For an executable example of this pattern, see the [pipeline in the Github project for this post.](https://github.com/benjivesterby/may2021-triangle-meetup/blob/main/patterns/pipeline/main.go#L8) From the project root folder run the following command to execute the example pipeline.

```shell
go run patterns/pipeline/main.go
```

Built with a series of Go routines each routine uses a channel of data coming in, and one going out. Each routine is responsible for its own work and pushes the results to the next step in the pipeline. Using this pattern you can create pipelines of any size and complexity.



## Fan-Out Pattern

The Fan-Out pattern is a pattern that allows for a number of routines to consume data from a single source. This pattern is useful when you need to load balance a large amount of data processing across multiple routines.

For an executable example of this pattern, see the [fan-out in the Github project for this post.](https://github.com/benjivesterby/may2021-triangle-meetup/blob/f9b47be76a7675bcffe6fb65dfbd7ff63ffccd60/patterns/fanout/main.go#L8) From the project root folder run the following command to execute the example fan-out.

```shell
go run patterns/fanout/main.go
```



![A diagram showing an example Fan-Out](https://benjiv.com/beginning-concurrency-patterns/images/fanout.webp) **Example Fan-Out**

Here is an example of the fan-out pattern where data is being processed by a set of worker routines.

```go
// Example of a fan-out pattern for processing data in parallel
func main() {
  dataPipeline := make(chan data)

  // Create three worker routines
  go process(dataPipeline)
  go process(dataPipeline)
  go process(dataPipeline)

  // Load the data into the pipeline
  for _, d := range ReadData() {
    dataPipeline <- d
  }

  // Close the pipeline when all data has been read in
  // NOTE: This will immediately close the application regardless
  // of whether the workers have completed their processing.
  // See the section on Best Practices at the end of the post
  // for more information on how to handle this.
  close(dataPipeline)
}

func ReadData() []data {
  // ...
}

func process(in <-chan data) {
  for {
    d, ok := <- in
    if !ok {
      return
    }
    // ... Do some work
  }
}

```

In the example above the `process` function is called three times, each as its own routine. The `in` channel is passed to each routine and data is read off the channel by the `for` loop. The `in` channel is closed when the data is exhausted.

### Replicator Pattern

So we have seen parallel processing of data, but a fan-out pattern can also be used to replicate data across multiple routines.

```go
// Example of a fan-out replication pattern
func main() {
  dataPipeline := make(chan data)

  // Pass the write-only channels from the three proc calls to the fan-out
  go replicate(dataPipeline, proc1(), proc2(), proc3())

  // Load the data into the pipeline
  for _, d := range ReadData() {
    dataPipeline <- d
  }
}

func proc1() chan<- data {/* ... */}
func proc2() chan<- data {/* ... */}
func proc3() chan<- data {/* ... */}

func replicate(in <-chan data, outgoing ...chan<- data) {
  for {
    d, ok := <- in // Read from the input channel
    if !ok {
      return
    }
    
    // Replicate the data to each of the outgoing channels
    for _, out := range outgoing {
      out <- d
    }
  }
}

```



> When using the replicator pattern be mindful of the type of data. This is particularly important when using _**pointers**_ because the replicator is not copying the data, it is passing the pointer.

The above example shows a fan-out pattern where the `replicate` function is called with three channels through a variadic argument. The `in` channel provides the base data and it is copied to the outgoing channels.



### Type Fan-Out

The last fan-out pattern we will cover here is the [type fan-out pattern](https://github.com/benjivesterby/may2021-triangle-meetup/blob/f9b47be76a7675bcffe6fb65dfbd7ff63ffccd60/patterns/fanout/main.go#L82) . This is particularly useful when dealing with a channel of `interface{}` types. This pattern allows for data to be directed to appropriate processors based on the type of the data.

```go
// Example of a type fan-out pattern from the github project
// for this post
func TypeFan(in <-chan interface{}) (
  <-chan int,
  <-chan string,
  <-chan []byte,
  ) {
  ints := make(chan int)
  strings := make(chan string)
  bytes := make(chan []byte)

  go func(
    in <-chan interface{},
    ints chan<- int,
    strings chan<- string,
    bytes chan<- []byte,
    ) {
      defer close(ints)
      defer close(strings)
      defer close(bytes)

      for {
        data, ok := <-in
        if !ok {
          return
        }

        // Type Switch on the data coming in and
        // push the data to the appropriate channel
        switch value := data.(type) {
        case nil: // Special case in type switch
          // Do nothing
        case int:
          ints <- value
        case string:
          strings <- value
        case []byte:
          bytes <- value
        default:
          fmt.Printf("%T is an unsupported type", data)
        }
      }
  }(in, ints, strings, bytes)

  return ints, strings, bytes
}

```



This example shows how to accept a channel of empty interface (i.e. `interface{}`) and use a type-switch to determine which channel to send the data to.



## Fan-In / Consolidator Pattern

With a Fan-In pattern, data is read in from multiple channels and consolidated to a single channel as output data.[3](https://benjiv.com/beginning-concurrency-patterns/#fn:3) The Fan-In pattern is the opposite of the Fan-Out pattern.

For an executable example of this pattern, see the [fan-in in the Github project for this post.](https://github.com/benjivesterby/may2021-triangle-meetup/blob/f9b47be76a7675bcffe6fb65dfbd7ff63ffccd60/patterns/fanin/main.go#L10) From the project root folder run the following command to execute the example fan-in.

```shell
go run patterns/fanin/main.go
```



![A diagram showing an example Fan-In](https://benjiv.com/beginning-concurrency-patterns/images/fanin.webp) **Example Fan-In**

Here is an example of the fan-in pattern where data is being mined by a set of worker routines and it is all being funneled into a single channel.

```go
// Example of a fan-in pattern mining data in
// parallel, but processing it all synchronously
func main() {
  miner1 := mine()
  miner2 := mine()
  miner3 := mine()

  // Take miner data and consolidate it into a single channel
  out := consolidate(miner1, miner2, miner3)

  // Process the data
  for {
    data, ok := <- out
    if !ok {
      return
    }
    // ... Do some work
  }
}

func consolidate(miners ...<-chan data) <-chan data {
  out := make(chan data)

  // Iterate over the miners and start a routine for
  // consuming each one and merging them into the output
  for _, in := range miners {
    go func(in <-chan data, out chan<- data) {
      for {
        d, ok := <-in // Pull data from the miner
        if !ok {
          return
        }
        out <- d // Send the data to the output
      }
    }(in, out)
  }

  return out
}

func mine() <-chan data {
  out := make(chan data)

  go func() {
    // ... populate the channel with mined data
  }()

  return out
}

```



The above example utilizes the fan-in pattern to consolidate incoming data from a set of mock data miners.

## Combining and Nesting Patterns

Each of these patterns can be combined to create more complex patterns. This is incredibly useful since the majority of applications will not use just one concurrency pattern.

Here is an example of combining all the patterns into a request response life-cycle. In this example the data comes in from a single source, fans out to multiple pipelines, and then fans back into a single response to the user.

![A diagram showing an example of a request-response life-cycle](https://benjiv.com/beginning-concurrency-patterns/images/combo.webp)

When building applications I recommend building diagrams to help conceptualize the concurrent design elements. I really like [diagrams.net](https://diagrams.net/) for this. The process of building out these diagrams can help solidify the final product and make it easier to understand the design. Having the designs made as part of your process will also help sell the design to other engineers and leadership.

>   Use Go’s native concurrency primitives when possible

## Best Practices

While it is considered best practice to primarily use the Go concurrency primitives to manage concurrency in your Go applications, there are situations where it becomes necessary to use the `sync` package to help manage concurrency.

A good example of this is when you need to ensure that all routines are properly exited when implementing something like `io.Closer`. If, for example, your code spawns N routines and you want to ensure that all of them are properly exited when the `Close` method is called, you can use the `sync.WaitGroup` to wait for the routines that are still running to be closed.

The method for doing this is shown below.

```go
// Example of using a wait group to
// ensure all routines are properly exited
type mytype struct {
  ctx context.Context
  cancel context.CancelFunc
  wg sync.WaitGroup
  wgMu sync.Mutex
}

// DoSomething spawns a go routine
// every time it's called
func (t *mytype) DoSomething() {
  // Increment the waitgroup to ensure
  // Close properly blocks
  t.wgMu.Lock()
  t.wg.Add(1)
  t.wgMu.Unlock()

  go func() {
    // Decrement the waitgroup
    // when the routine exits
    defer t.wg.Done()

    // ... do something
  }()
}

func (t *mytype) Close() error {
  // Cancel the internal context
  t.cancel()

  // Wait for all routines to exit
  t.wgMu.Lock()
  t.wg.Wait()
  t.wgMu.Unlock()
  return nil
}

```

There are a couple of important elements in the code above. Firstly it uses a `sync.WaitGroup` to increment and decrement the number of routines that are running. Secondly it uses a `sync.Mutex` to ensure that only one routine is modifying the `sync.WaitGroup` at a time (a mutex is **not** necessary for the `.Wait()` method).

> [Click here to read a very thourough explanation of this by Leo Lara.](https://www.leolara.me/blog/closing_a_go_channel_written_by_several_goroutines/) [4](https://benjiv.com/beginning-concurrency-patterns/#fn:4)

For a functional example of a situation where using the `sync` package is necessary, see the [Plex library.](https://github.com/devnw/plex/blob/2d4f8fe223ab71f488d2d6f5e3dcfad77250d28d/stream.go#L121)

## Generics (COMING SOON!)

These patterns become much easier to use with the introduction of generics in `Go 1.18` which I will cover in an upcoming post.

___

1.  [Pipelines - Concurrency in Go by Katherine Cox-Buday - Page 100](https://www.oreilly.com/library/view/concurrency-in-go/9781491941294/)  [↩︎](https://benjiv.com/beginning-concurrency-patterns/#fnref:1)
    
2.  [Go Concurrency Patterns: Pipelines and cancellation](https://blog.golang.org/pipelines)  [↩︎](https://benjiv.com/beginning-concurrency-patterns/#fnref:2)
    
3.  [Multiplexing - Concurrency in Go by Katherine Cox-Buday - Page 117](https://www.oreilly.com/library/view/concurrency-in-go/9781491941294/)  [↩︎](https://benjiv.com/beginning-concurrency-patterns/#fnref:3)
    
4.  [Closing a Go channel written by several goroutines](https://www.leolara.me/blog/closing_a_go_channel_written_by_several_goroutines/)  [↩︎](https://benjiv.com/beginning-concurrency-patterns/#fnref:4)