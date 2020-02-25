# Advanced Go Concurrency

- 原文地址：https://encore.dev/blog/advanced-go-concurrency
- 原文作者：[André Eriksson](https://encore.dev/blog)
- 译文出处：https://encore.dev/blog
- 本文永久链接：https://github.com/gocn/translator/blob/master/2020/w1_advanced_go_concurrency.md
- 译者：[咔叽咔叽](https://github.com/watermelo)
- 校对者：

If you’ve used Go for a while you’re probably aware of some of the basic Go concurrency primitives:

*   The `go` keyword for spawning goroutines
*   Channels, for communicating between goroutines
*   The `context` package for propagating cancellation
*   The `sync` and `sync/atomic` packages for lower-level primitives such as mutexes and atomic memory access

These language features and packages combine to provide a very rich set of tools for building concurrent applications. What you might not have discovered yet is a set of higher-level concurrency primitives available in the “extended standard library” available at [golang.org/x/sync](https://pkg.go.dev/golang.org/x/sync). We’ll be taking a look at these in this article.

## Package singleflight

As the [package documentation](https://pkg.go.dev/golang.org/x/sync/singleflight?tab=doc) states, this package provides a duplicate function call suppression mechanism.

This package is extremely useful for cases where you are doing something computationally expensive (or just slow, like network access) in response to user activity. For example, let’s say you have a database with weather information per city and you want to expose this as an API. In some cases you might have multiple users ask for the weather for the same city at the same time.

When that happens, wouldn’t it be great if you could just query the database, and then share the result to all the waiting requests? That’s exactly what the `singleflight` package does!

To use it, create a `singleflight.Group` somewhere. It needs to be shared across all the requests to work correctly. Then wrap the slow or expensive operation in a call to `group.Do(key, fn)`. Multiple concurrent requests for the same `key` will only call `fn` once, and the result will be returned to all callers once `fn` returns.

Here’s how it looks in practice:

```go
package weather

type Info struct {
    TempC, TempF int // temperature in Celsius and Farenheit
    Conditions string // "sunny", "snowing", etc
}

var group singleflight.Group

func City(city string) (*Info, error) {
    results, err, _ := group.Do(city, func() (interface{}, error) {
        info, err := fetchWeatherFromDB(city) // slow operation
        return info, err
    })
    if err != nil {
        return nil, fmt.Errorf("weather.City %s: %w", city, err)
    }
    return results.(*Info), nil
}
```

Note that the closure we pass to `group.Do` must return `(interface{}, error)` to work with the Go type system. The third return value from `group.Do`, which is ignored in the example above, indicates whether the result was shared between multiple callers or not. 

To see a more complete example, check out the code in the [Encore Playground](https://play.encore.dev/663hvcGbpq-rtw).

## Package errgroup

Another invaluable package is the [errgroup package](https://pkg.go.dev/golang.org/x/sync/errgroup?tab=doc). It is best described as a `sync.WaitGroup` but where the tasks return errors that are propagated back to the waiter.

This package is useful when you have multiple operations that you want to wait for, but you also want to determine if they all completed successfully.
For example, to build on the weather example from above, let’s say you want to lookup the weather for multiple cities at once, and fail if any of the lookups fails.

Start by defining an `errgroup.Group`, and use the `group.Go(fn func() error)` method for each city.
This method spawns a goroutine to run the task. When you’ve spawned all the tasks you want, use
`group.Wait()` to wait for them to complete. Note that this method returns an `error`, unlike `sync.WaitGroup`’s equivalent. The error is `nil` if and only if all the tasks returned a `nil` error.

In practice it looks like this:

```go
func Cities(cities ...string) ([]*Info, error) {
    var g errgroup.Group
    var mu sync.Mutex
    res := make([]*Info, len(cities)) // res[i] corresponds to cities[i]

    for i, city := range cities {
        i, city := i, city // create locals for closure below
        g.Go(func() error {
            info, err := City(city)
            mu.Lock()
            res[i] = info
            mu.Unlock()
            return err
        })
    }
    if err := g.Wait(); err != nil {
        return nil, err
    }
    return res, nil
}
```

Here we are allocating an slice of results so that each goroutine can write to its own index. While the above code is safe even without the `mu` mutex, since each goroutine is writing to its own entry in the slice, we use one anyway in case the code is changed over time.

## Bounded concurrency

The code above will lookup weather information for all the given cities concurrently.
That’s fine when the number of cities is small, but can cause performance issues if the number of cities is massive. In those cases it’s useful to introduce _bounded concurrency_.

Go makes it really easy to create bounded concurrency with the use of [semaphores](https://www.guru99.com/semaphore-in-operating-system.html). A semaphore is a concurrency primitive that you might have come across if you studied Computer Science, but if not, don’t worry. You can use semaphores for several purposes, but we’re just going to use them to keep track of how many tasks are running, and to block until there is room for another task to start.

In Go we can accomplish this through a clever use of channels! If we want to allow up to 10 tasks to run at once, we create a channel with space for 10 items: `semaphore := make(chan struct{}, 10)`. You can picture this as a pipe that can fit 10 balls.

To start a new task, blocking if too many tasks are already running, we simply attempt to send a value on the channel: `semaphore <- struct{}{}`. This is analogous to trying to push another ball into the pipe. If the pipe is full, it waits until there is room.

When a task completes, mark it as such by taking a value out of the channel: `<-semaphore`. This is analogous to pulling a ball out at the other end of the pipe, which leaves room for another ball to be pushed in (another task started).

And that’s it! Our modified `Cities` looks like this:

```go
func Cities(cities ...string) ([]*Info, error) {
    var g errgroup.Group
    var mu sync.Mutex
    res := make([]*Info, len(cities)) // res[i] corresponds to cities[i]
    sem := make(chan struct{}, 10)
    for i, city := range cities {
        i, city := i, city // create locals for closure below
        sem <- struct{}{}
        g.Go(func() error {
            info, err := City(city)
            mu.Lock()
            res[i] = info
            mu.Unlock()
            <-sem
            return err
        })
    }
    if err := g.Wait(); err != nil {
        return nil, err
    }
    return res, nil
}
```

### Weighted bounded concurrency

And finally, sometimes you want bounded concurrency, but not all tasks are equally expensive.
In that case the amount of resources we’ll consume will vary drastically depending on the distribution
of cheap and expensive tasks and how they happen to start.

A better solution for this use case is to use _weighted bounded concurrency_. How this works is simple: instead of reasoning about the number of tasks we want to run concurrently, we come up with a “cost” for every task and acquire and release that cost from a semaphore.

We can’t model this with channels any longer since we need the whole cost acquired and released at once.
Fortunately the “extended standard library” comes to our rescue once more! The [golang.org/x/sync/sempahore](https://pkg.go.dev/golang.org/x/sync@v0.0.0-20190911185100-cd5d95a43a6e/semaphore?tab=doc) package provides a weighted semaphore implementation exactly for this purpose.

The `sem <- struct{}{}` operation is called “Acquire” and the `<-sem` operation is called “Release”.
You will note that the `semaphore.Acquire` method returns an error; that is because it can be used
with the `context` package to abort the operation early. For the purpose of this example we will ignore it.

The weather lookup example is realistically too simple to warrant a weighted semaphore,
but for the sake of simplicity let’s pretend the cost varies with the length of the city name.
Then we arrive at the following:

```go
func Cities(cities ...string) ([]*Info, error) {
    ctx := context.TODO() // replace with a real context
    var g errgroup.Group
    var mu sync.Mutex
    res := make([]*Info, len(cities)) // res[i] corresponds to cities[i]
    sem := semaphore.NewWeighted(100) // 100 chars processed concurrently
    for i, city := range cities {
        i, city := i, city // create locals for closure below
        cost := int64(len(city))
        if err := sem.Acquire(ctx, cost); err != nil {
            break
        }
        g.Go(func() error {
            info, err := City(city)
            mu.Lock()
            res[i] = info
            mu.Unlock()
            sem.Release(cost)
            return err
        })
    }
    if err := g.Wait(); err != nil {
        return nil, err
    } else if err := ctx.Err(); err != nil {
        return nil, err
    }
    return res, nil
}
```

## Conclusion

The above examples show how easy it is to add concurrency to a Go program, and then fine-tune it based on your needs.