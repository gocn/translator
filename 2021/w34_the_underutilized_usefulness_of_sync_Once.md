# Go sync.Once 的妙用

如果你曾用过 Go 中的 goroutines，你也许会遇到几个并发原语言，如 `sync.Mutex`, `sync.WaitGroup` 或是 `sync.Map`，但是你听说过 `sync.Once` 么？

也许你听说过，那 go 文档是怎么描述它的呢？

> Once 是只执行一个操作的对象。 

听起来很简单，它有什么用处呢？

由于某些原因，`sync.Once` 的用法并没有很好的文档记录。在第一个`.Do`中的操作执行完成前，将一直处于等待状态，这使得在执行较昂贵的操作（通常缓存在`map`中）时非常有用。

## 原生缓存方式

假设你有一个热门的网站，但它的后端 API 访问不是很快，因此你决定将 API 结果通过 map 缓存在内存中。以下是一个基本的解决方案：

```go
package main

type QueryClient struct {
    cache map[string][]byte
    mutex *sync.Mutex
}

func (c *QueryClient) DoQuery(name string) []byte {
    // Check if the result is already cached.
    c.mutex.Lock()
    if cached, found := c.cache[name]; found {
        c.mutex.Unlock()
        return cached, nil
    }
    c.mutex.Unlock()

    // Make the request if it's uncached.
    resp, err := http.Get("https://upstream.api/?query=" + url.QueryEscape(name))
    // Error handling and resp.Body.Close omitted for brevity.
    result, err := ioutil.ReadAll(resp)

    // Store the result in the cache.
    c.mutex.Lock()
    c.cache[name] = result
    c.mutex.Unlock()

    return result
}
```

看起来不错，对吧？

然而，如果有两个 `DoQuery` 同时进行调用会发生什么呢？竞争。两方都会检测到缓存占用，并且都会向 `upstream.api` 执行不必要的 HTTP 请求，但只需要一方完成。

## 不美观但更好的缓存方式

我并没有进行统计，但我认为大家解决这个问题的另外一种方式是使用通道、上下文或互斥锁。在这个例子中，可以将上文代码转换为：

```go
package main

type CacheEntry struct {
    data []byte
    wait <-chan struct{}
}

type QueryClient struct {
    cache map[string]*CacheEntry
    mutex *sync.Mutex
}

func (c *QueryClient) DoQuery(name string) []byte {
    // Check if the operation has already been started.
    c.mutex.Lock()
    if cached, found := c.cache[name]; found {
        c.mutex.Unlock()
        // Wait for it to complete.
        <-cached.wait
        return cached.data, nil
    }

    entry := &CacheEntry{
        data: result,
        wait: make(chan struct{}),
    }
    c.cache[name] = entry
    c.mutex.Unlock()

    // Make the request if it's uncached.
    resp, err := http.Get("https://upstream.api/?query=" + url.QueryEscape(name))
    // Error handling and resp.Body.Close omitted for brevity
    entry.data, err = ioutil.ReadAll(resp)

    // Signal that the operation is complete, receiving on closed channels
    // returns immediately.
    close(entry.wait)

    return entry.data
}
```

这种方案不错，但代码的可读性受到了很大影响。`cached.wait` 进行了哪些操作并不是很清晰，在不同情况下的操作流也并不直观。

## 使用 `sync.Once`

我们来尝试一下使用 `sync.Once` 方案： 

```go
package main

type CacheEntry struct {
    data []byte
    once *sync.Once
}

type QueryClient struct {
    cache map[string]*CacheEntry
    mutex *sync.Mutex
}

func (c *QueryClient) DoQuery(name string) []byte {
    c.mutex.Lock()
    entry, found := c.cache[name]
    if !found {
        // Create a new entry if one does not exist already.
        entry = &CacheEntry{
            once: new(sync.Once),
        }
        c.cache[name] = entry
    }
    c.mutex.Unlock()

    // Now when we invoke `.Do`, if there is an on-going simultaneous operation,
    // it will block until it has completed (and `entry.data` is populated).
    // Or if the operation has already completed once before,
    // this call is a no-op and doesn't block.
    entry.once.Do(func() {
        resp, err := http.Get("https://upstream.api/?query=" + url.QueryEscape(name))
        // Error handling and resp.Body.Close omitted for brevity
        entry.data, err = ioutil.ReadAll(resp)
    })

    return entry.data
}
```

以上就是 `sync.Once` 的方案，和之前的示例很相似，但现在更容易理解（至少在我看来）。只有一个返回值，且代码自上而下，非常直观，而不必像之前一样对 `entry.wait` 通道进行阅读和理解。

## 进一步阅读/其他注意事项

另一个类似于 `sync.Once` 的机制是 [golang.org/x/sync/singleflight](https://pkg.go.dev/golang.org/x/sync/singleflight)。`singleflight` 只会删除正在进行中的请求中的重复请求（即不会持久化缓存），但与 `sync.Once` 相比，`singleflight` 通过上下文实现起来可能更简洁（通过使用 `select` 和 `ctx.Done()`），并且在生产环境中，可以通过上下文取消这一点很重要。`singleflight` 实现的模式和 `sync.Once` 十分接近，但如果 map 中存有值，则会提前返回。

[ianlancetaylor](https://github.com/golang/go/issues/25312#issuecomment-387800105) 建议结合上下文使用 `sync.Once`，方式如下：

```go
c := make(chan bool, 1)
go func() {
    once.Do(f)
    c <- true
}()
select {
case <-c:
case <-ctxt.Done():
    return
}
```