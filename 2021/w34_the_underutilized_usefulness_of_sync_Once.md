# The underutilized usefulness of sync.Once

 If you've ever used goroutines in Go, you've probably come across a couple of concurrency primitives. Probably `sync.Mutex`, `sync.WaitGroup` and maybe `sync.Map`, but have you heard of `sync.Once`?

 Maybe you have, but what does the [godoc say about it](https://pkg.go.dev/sync#Once)?

 > Once is an object that will perform exactly one action.

 Sounds simple enough, what's so useful about it then?

 Well for some reason this isn't particularly well documented, but a `sync.Once` will wait until the execution inside the first `.Do` completes. This makes it incredibly useful when performing relatively expensive operations that you would typically cache in a map.

 ## Naive caching

 Say for example you have a popular website that hits a backend API that isn't particularly fast, so you decide to cache API results in-memory with a map. A naive solution might look like this:

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

 Looks good, right?

 Well what happens if there are two calls to `DoQuery` that happen simultaneously? The calls would race, neither would see the cache is populated, and both would perform the HTTP request to `upstream.api` unnecessarily, when only one would need to complete it.

 ## Ugly but better caching

 I don't have statistics on this, but one way I would imagine people solving this is by using channels, contexts or mutexes. For example you could turn this into:

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

 That's good and all but the code's readability has taken a hit. It's not immediately clear what's going on with `cached.wait` and the flow of operations under different situations is not very intuitive.

 ## Applying `sync.Once`

 Let's try to apply `sync.Once` to this instead:

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

 That's it. This achieves the same as the previous example, but is now much easier to understand (at least in my opinion). There is only a single return, and the code flows intuitively from top to bottom without having to read and understand what's going on with the `entry.wait` channel as before.

 ## Further reading/additional considerations

 Another mechanism similar to `sync.Once` is [golang.org/x/sync/singleflight](https://pkg.go.dev/golang.org/x/sync/singleflight). However `singleflight` only deduplicates requests that are in-flight (i.e. doesn't cache persistently). `singleflight` however may be cleaner to implement with contexts compared to `sync.Once` (through the use of a `select` and `ctx.Done()`), in production environments this may be important as to be able to cancel out with a context. The pattern with `singleflight` is quite similar to `sync.Once` but you would early return if a value is present inside the map.

 [ianlancetaylor](https://github.com/golang/go/issues/25312#issuecomment-387800105) suggested the following pattern to use `sync.Once` with contexts:

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