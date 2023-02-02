**This post made it to the top of Golang [subreddit](https://www.reddit.com/r/golang/comments/d6taoq/introducing_ristretto_a_highperformance_go_cache/) and is trending in top 10 on the front page of [Hacker News](https://news.ycombinator.com/item?id=21023949). Do engage in discussion there and show us love by giving us a [star](https://github.com/dgraph-io/dgraph).**

With over six months of research and development, we’re proud to announce the initial release of **[Ristretto](https://github.com/dgraph-io/ristretto): A High Performance, Concurrent, Memory-Bound Go cache.** It is contention-proof, scales well and provides consistently high hit-ratios.

You can now also watch the talk Manish gave at the latest Go Bangalore meetup!

<iframe width="560" height="315" src="https://www.youtube.com/embed/HzMZEsqXDec?enablejsapi=1&amp;origin=https://dgraph.io" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen="" data-lf-form-tracking-inspected-p1e024byr0q7gb6d="true" data-lf-yt-playback-inspected-p1e024byr0q7gb6d="true" data-lf-vimeo-playback-inspected-p1e024byr0q7gb6d="true"></iframe>

### Preface

It all started with needing a memory-bound, concurrent Go cache in [Dgraph](https://github.com/dgraph-io/dgraph). We looked around for a solution, but we couldn’t find a great one. We then tried using a sharded map, with shard eviction to release memory, which caused us memory issues. We then repurposed Groupcache’s [LRU](https://github.com/golang/groupcache/blob/master/lru/lru.go), using mutex locks for thread safety. After having it around for a year, we noticed that the cache suffered from severe contention. A [commit](https://github.com/dgraph-io/dgraph/commit/b9990f4619b64615c2c18bb7627d198b4397109c) to remove that cache caused our query latency to dramatically improve by 5-10x. **In essence, our cache was slowing us down!**

We concluded that the concurrent cache story in Go is broken and must be fixed. In March, we wrote about the [State of Caching in Go](https://blog.dgraph.io/post/caching-in-go/), mentioning the problem of databases and systems requiring a smart memory-bound cache which can scale to the multi-threaded environment Go programs find themselves in. In particular, we set these as the requirements for the cache:

1.  Concurrent
2.  High cache-hit ratio
3.  Memory-bounded (limit to configurable max memory usage)
4.  Scale well as the number of cores and goroutines increases
5.  Scale well under non-random key access distribution (e.g. Zipf).

After publishing the [blog post](https://blog.dgraph.io/post/caching-in-go/), we built a team to address the challenges mentioned therein and create a Go cache library worthy of being compared to non-Go cache implementations. In particular, [Caffeine](https://github.com/ben-manes/caffeine) which is a high performance, near-optimal caching library based on Java 8. It is being used by many Java-based databases, like Cassandra, HBase, and Neo4j. There’s an article about the design of Caffeine [here](http://highscalability.com/blog/2016/1/25/design-of-a-modern-cache.html).

### Ristretto: Better Half of Espresso

We have since [read](https://dgraph.io/blog/refs/bp_wrapper.pdf) [the](https://dgraph.io/blog/refs/Adaptive%20Software%20Cache%20Management.pdf) [literature](https://dgraph.io/blog/refs/TinyLFU%20-%20A%20Highly%20Efficient%20Cache%20Admission%20Policy.pdf), extensively tested implementations and discussed every variable there is to consider in writing a cache library. And today, we are proud to announce that it is ready for the wider Go community to use and experiment with.

Before we begin explaining the design of [Ristretto](https://github.com/dgraph-io/ristretto), here’s a code snippet which shows how to use it:

```
func main() {
cache, err := ristretto.NewCache(&ristretto.Config{
NumCounters: 1e7,     // Num keys to track frequency of (10M).
MaxCost:     1 << 30, // Maximum cost of cache (1GB).
BufferItems: 64,      // Number of keys per Get buffer.
})
if err != nil {
panic(err)
}

cache.Set("key", "value", 1) // set a value
// wait for value to pass through buffers
time.Sleep(10 * time.Millisecond)

value, found := cache.Get("key")
if !found {
panic("missing value")
}
fmt.Println(value)
cache.Del("key")
}
```

#### Guiding Principles

[Ristretto](https://github.com/dgraph-io/ristretto) is built on three guiding principles:

1.  Fast Accesses
2.  High Concurrency and Contention Resistance
3.  Memory Bounding.

In this blog post, we’ll discuss these three principles and how we achieved them in Ristretto.

### Fast Access

As much as we love Go and its opinionated stance on features, some of Go design decisions prevented us from squeezing out all the performance we wanted to. The most notable one is Go’s concurrency model. Due to the focus on CSP, most other forms of atomic operations have been neglected. This makes it hard to implement lock-free structures that would be useful in a cache library. For example, Go [does not](https://groups.google.com/d/msg/golang-nuts/M9kF6Tdh2Vo/3tLSFYYOGgAJ) provide thread-local storage.

At its core, a cache is a hash map with rules about what goes in and what goes out. If the hash map doesn’t perform well, then the whole cache will suffer. As opposed to Java, Go does not have a lockless concurrent hashmap. Instead, thread safety in Go is achieved via explicitly acquiring mutex locks.

We experimented with multiple implementations (using the `store` interface within Ristretto) and found `sync.Map` performs well for read-heavy workloads but deteriorates for write workloads. Considering there’s no thread-local storage, **we found the best overall performance with sharded mutex-wrapped Go maps.** In particular, we chose to use 256 shards to ensure that this would perform well even with a 64-core server.

With a shard based approach, we also needed to find a quick way to calculate which shard a key should go in. This requirement and the concern about long keys consuming too much memory led us to using `uint64` for keys, instead of storing the entire key. The rationale was that we’ll need the hash of the key in multiple places and doing it once at entry allowed us to reuse that hash, avoiding any more computation.

**To generate a fast hash, we borrowed [runtime.memhash](https://github.com/dgraph-io/ristretto/blob/master/z/rtutil.go#L42-L44) from Go Runtime.** This function uses assembly code to quickly generate a hash. Note that the hash has a randomizer that is initialized whenever the process starts, which means the same key would not generate the same hash on the next process run. But, that’s alright for a non-persistent cache. In our [experiments](https://github.com/dgraph-io/ristretto/blob/master/z/rtutil_test.go#L11-L44), we found that it can hash 64-byte keys in under 10ns.

```
BenchmarkMemHash-32 200000000 8.88 ns/op
BenchmarkFarm-32    100000000 17.9 ns/op
BenchmarkSip-32      30000000 41.1 ns/op
BenchmarkFnv-32      20000000 70.6 ns/op
```

We then used this hash as not only the stored key but also to figure out the shard the key should go into. _This does introduce a chance of key collision, that’s something we plan to deal with later._

### Concurrency and Contention Resistance

Achieving high hit ratios requires managing metadata about what’s present in the cache and what _should_ be present in the cache. This becomes very hard when balancing the performance and scalability of the cache across goroutines. Luckily, there’s a [paper](https://dgraph.io/blog/refs/bp_wrapper.pdf) called _BP-Wrapper_ written about a system framework making any replacement algorithms almost lock contention-free. The paper describes two ways to mitigate contention: _prefetching_ and _batching_. We only use batching.

Batching works pretty much how you’d think. **Rather than acquiring a mutex lock for every metadata mutation, we wait for a ring buffer to fill up before we acquire a mutex and process the mutations.** As described in the paper, this lowers contention considerably with little overhead.

We apply this method for all `Gets` and `Sets` to the cache.

#### Gets

All Gets to the cache are, of course, immediately serviced. The hard part is to capture the Get, so we can keep track of the key access. In an LRU cache, typically a key would be placed at the head of a linked list. In our LFU based cache, we need to increment an item’s hit counter. Both operations require thread-safe access to a cache global struct. [BP-Wrapper](https://dgraph.io/blog/refs/bp_wrapper.pdf) suggests using batching to process the hit counter increments, but the question is how do we implement this batching process, without acquiring yet another lock.

This might sound like a perfect use case of Go channels, and it is. Unfortunately, the throughput performance of channels prevented us from using them. **Instead, we devised a nifty way to use `sync.Pool` to implement striped, lossy [ring buffers](https://github.com/dgraph-io/ristretto/blob/master/ring.go#L99-L104)** that have great performance with little loss of data.

Any item stored in the Pool may be removed automatically at any time [without](https://golang.org/pkg/sync/#Pool) notification. _That introduces one level of lossy behavior._ Each item in Pool is effectively a batch of keys. When the batch fills up, it gets pushed to a channel. The channel size is deliberately kept small to avoid consuming too many CPU cycles to process it. If the channel is full, the batch is dropped. _This introduces a secondary level of lossy behavior._ A goroutine picks up this batch from the internal channel and processes the keys, updating their hit counter.

```
AddToLossyBuffer(key):
  stripe := b.pool.Get().(*ringStripe)
  stripe.Push(key)
  b.pool.Put(stripe)

Once buffer fills up, push to channel:
  select {
  case p.itemsCh <- keys:
      p.stats.Add(keepGets, keys[0], uint64(len(keys)))
      return true
  default:
      p.stats.Add(dropGets, keys[0], uint64(len(keys)))
      return false
  }

p.itemCh processing:
  func (p *tinyLFU) Push(keys []uint64) {
    for _, key := range keys {
      p.Increment(key)
    }
  }
```

The performance benefits of using a `sync.Pool` over anything else (slices, striped mutexes, etc.) are mostly due to the internal usage of thread-local storage, _something not available as a public API to Go users._

#### Sets

The requirements for Set buffer is slightly different from Get. In Gets, we buffer up the keys, only processing them once the buffer fills up. In Sets, we want to process the keys as soon as possible. **So, we use a channel to capture the Sets, dropping them on the floor if the channel is full to avoid contention.** A couple of background goroutines pick sets from the channel and process the Set.

This approach, as with Gets, is designed to optimize for contention resistance. But, comes with a few caveats, described below.

```
select {
case c.setBuf <- &item{key: hash, val: val, cost: cost}:
    return true
default:
    // drop the set and avoid blocking
    c.stats.Add(dropSets, hash, 1)
    return false
}
```

#### Caveats

Sets in [Ristretto](https://github.com/dgraph-io/ristretto) are queued into a buffer, control is returned back to the caller, and the buffer is then applied to the cache. This has two side-effects:

1.  **There is no guarantee that a set would be applied.** It could be dropped immediately to avoid contention or could be rejected later by the policy.
2.  Even if a Set gets applied, it might take a few milliseconds after the call has returned to the user. In database terms, it is an _eventual consistency_ model.

If however, a key is already present in the cache, Set would update the key immediately. This is to avoid a cached key holding a stale value.

#### Contention Resistance

**Ristretto is optimized for contention resistance.** This performs really well under heavy concurrent load, as we’ll see with throughput benchmarks below. However, it would lose some metadata in exchange for better throughput performance.

Interestingly, that information loss doesn’t hurt our hit ratio performance because of the nature of key access distributions. If we do lose metadata, it is generally lost uniformly while the key access distribution remains non-uniform. Therefore, we still achieve high hit ratios and the hit ratio degradation is small as shown by the following graph.

![Ristretto Hit Ratio Degradation](https://dgraph.io/blog/images/rt-hit-degrade.svg?sanitize=true)

### Memory Bounding

#### Key Cost

_An infinitely large cache is practically impossible._ A cache must be bounded in size. Many cache libraries would consider cache size to be the number of elements. We found that approach _naive_. Surely it works in a workload where values are of identical size. Most workloads, however, have variable-sized values. One value could cost a few bytes, another a few kilobytes and yet another, a few megabytes. Treating them as having the same memory cost isn’t realistic.

**In [Ristretto](https://github.com/dgraph-io/ristretto), we attach a cost to every key-value.** Users can specify what that cost is when calling Set. We count this cost against the MaxCost of the cache. When the cache is operating at capacity, a _heavy_ item could displace many _lightweight_ items. This mechanism is nice in that it works well for all different workloads, including the naive approach where each key-value costs 1.

#### Admission Policy via TinyLFU

> “What should we let into the cache?”

is answered by the admission policy. The goal, obviously, is to let in new items if they are more _“valuable”_ than the current items. However, this becomes a challenge if you consider the overhead (latency and memory) required to track relevant item information pertaining to the _“value”_ question.

Despite being a well-documented strategy for increasing hit ratios, most Go cache libraries have no admission policy at all. In fact, many LRU eviction implementations assume the latest key as the most valuable.

Moreover, most of the Go cache libraries use pure LRU or an approximation of LRU as their eviction policy. The quality of LRU approximation notwithstanding, some workloads are just better suited to LFU eviction policies. We’ve found this to be the case in our benchmarks using various traces.

For our admission policy, we looked at a new and fascinating paper called **[TinyLFU](https://dgraph.io/blog/refs/TinyLFU%20-%20A%20Highly%20Efficient%20Cache%20Admission%20Policy.pdf): A Highly Efficient Cache Admission Policy.** At a very high level, TinyLFU provides three methods:

-   Increment(key uint64)
-   Estimate(key uint64) int (referred as ɛ)
-   Reset

The [paper](https://dgraph.io/blog/refs/TinyLFU%20-%20A%20Highly%20Efficient%20Cache%20Admission%20Policy.pdf) explains it best, but TinyLFU is an eviction-agnostic admission policy designed to improve hit ratios with very little memory overhead. The main idea is to **only let in a new item if its estimate is higher than that of the item being evicted.** We implemented TinyLFU in [Ristretto](https://github.com/dgraph-io/ristretto) using a [Count-Min](https://en.wikipedia.org/wiki/Count%E2%80%93min_sketch) Sketch. It uses 4-bit counters to approximate the frequency of access for the item (ɛ). This small cost per key allows us to keep track of a much larger sample of the global keyspace, than would be possible using a normal key to frequency map.

TinyLFU also maintains the recency of key access by a `Reset` function. After N key increments, the counters get halved. So, a key that has not been seen for a while would have its counter get reset to zero; paving the way for more recently seen keys.

#### Eviction Policy via Sampled LFU

When the cache reaches capacity, every incoming key should displace one or more keys present in the cache. Not only that, **the ɛ of incoming key should be higher than the ɛ of key being evicted.** To find a key with low ɛ, we used the natural [randomness](https://blog.golang.org/go-maps-in-action) provided by Go map iteration to pick a sample of keys and loop over them to find a key with the lowest ɛ.

We then compare the ɛ of this key against the incoming key. If the incoming key has a higher ɛ, then this key gets evicted (_eviction policy_). Otherwise, the incoming key is rejected (_admission policy_). This mechanism is repeated until the incoming key’s cost can be fit into the cache. Thus, a single incoming key may displace more than one key. _Note that the cost of the incoming key does not play a factor in choosing the eviction keys._

**With this approach, the hit ratios are within 1% of the exact LFU policies for a variety of workloads.** This means we get the benefits of admission policy, conservative memory usage, and lower contention in the same little package.

```
// Snippet from the Admission and Eviction Algorithm
incHits := p.admit.Estimate(key)
for ; room < 0; room = p.evict.roomLeft(cost) {
    sample = p.evict.fillSample(sample)
    minKey, minHits, minId := uint64(0), int64(math.MaxInt64), 0
    for i, pair := range sample {
        if hits := p.admit.Estimate(pair.key); hits < minHits {
            minKey, minHits, minId = pair.key, hits, i
        }
    }
    if incHits < minHits {
        p.stats.Add(rejectSets, key, 1)
        return victims, false
    }
    p.evict.del(minKey)
    sample[minId] = sample[len(sample)-1]
    sample = sample[:len(sample)-1]
    victims = append(victims, minKey)
}
```

#### DoorKeeper

Before we place a new key in TinyLFU, [Ristretto](https://github.com/dgraph-io/ristretto) uses a bloom filter to first check if the key has been seen before. Only if the key is already present in the bloom filter, is it inserted into the TinyLFU. This is to avoid _polluting_ TinyLFU with a long tail of keys that are not seen more than once.

When calculating ɛ of a key, if the item is included in the bloom filter, its frequency is estimated to be the Estimate from TinyLFU plus one. During a `Reset` of TinyLFU, the bloom filter is also cleared out.

### Metrics

While optional, it is important to understand how a cache is behaving. We wanted to ensure that tracking metrics related to cache is not only possible, the overhead of doing so is low enough to be turned on and kept on.

Beyond hits and misses, Ristretto tracks metrics like keys and their cost being added, updated and evicted, sets being dropped or rejected, and gets being dropped or kept. All these numbers help understand the cache behavior on various workloads and pave way for further optimizations.

We initially used atomic counters for these. However, the overhead was significant. We narrowed the cause down to [False Sharing](https://dzone.com/articles/false-sharing). Consider a multi-core system, where different atomic counters (8-bytes each) fall in the same cache line (typically 64 bytes). Any update made to one of these counters, causes the others to be marked _invalid_. This forces a cache reload for all other cores holding that cache, thus creating a write contention on the cache line.

**To achieve scalability, we ensure that each atomic counter completely occupies a full cache line.** So, every core is working on a different cache line. Ristretto uses this by allocating 256 uint64s for each metric, leaving 9 unused uint64s between each active uint64. To avoid extra computation, the key hash is reused to determine which uint64 to increment.

```
Add:
valp := p.all[t]
// Avoid false sharing by padding at least 64 bytes of space between two
// atomic counters which would be incremented.
idx := (hash % 25) * 10
atomic.AddUint64(valp[idx], delta)

Read:
valp := p.all[t]
var total uint64
for i := range valp {
total += atomic.LoadUint64(valp[i])
}
return total
```

When reading the metric, all the uint64s are read and summed up to get the latest number. **With this approach, metrics tracking only adds around 10% overhead to the cache performance.**

### Benchmarks

Now that you understand the various mechanisms present in [Ristretto](https://github.com/dgraph-io/ristretto), let’s look at the Hit ratio and Throughput benchmarks compared to other popular Go caches.

#### Hit Ratios

Hit ratios were measured using Damian Gryski’s [cachetest](https://github.com/dgraph-io/benchmarks/blob/master/cachebench/cache_bench_test.go) along with our own benchmarking [suite](https://github.com/dgraph-io/benchmarks/tree/master/cachebench). The hit ratio numbers are the same across both utilities, but we added the ability to read certain trace formats (LIRS and ARC, specifically) as well as CSV output for easier graphing. If you want to write your own benchmarks or add a trace format, check out the [sim](https://github.com/dgraph-io/ristretto/tree/master/sim) package.

To get a better idea of the room for improvement, **we added a theoretically [optimal](https://en.wikipedia.org/wiki/Page_replacement_algorithm#The_theoretically_optimal_page_replacement_algorithm) cache implementation, which uses future knowledge to evict items with the least amount of hits over its entire lifetime.** Note that this is a clairvoyant LFU eviction policy, where other clairvoyant policies may use LRU. Depending on the workload, LFU or LRU may be better suited, but we found clairvoyant LFU useful for comparisons with [Ristretto](https://github.com/dgraph-io/ristretto)’s Sampled LFU.

##### Search

This trace is described as “disk read accesses initiated by a large commercial search engine in response to various web search requests.”

![Hit Ratios: Search](https://dgraph.io/blog/images/rt-hit-search.svg?sanitize=true)

##### Database

This trace is described as “a database server running at a commercial site running an ERP application on top of a commercial database.”

![Hit Ratios: Commercial DB](https://dgraph.io/blog/images/rt-hit-db.svg?sanitize=true)

##### Looping

This trace demonstrates a looping access pattern. We couldn’t include Fastcache, Freecache, or Bigcache implementations in this and the following benchmark because they have minimum capacity requirements that would skew the results. Some trace files are small and require small capacities for performance measurements.

![Hit Ratios: Loop](https://dgraph.io/blog/images/rt-hit-loop.svg?sanitize=true)

##### CODASYL

This trace is described as “references to a CODASYL database for a one hour period.” Note that [Ristretto](https://github.com/dgraph-io/ristretto)’s performance suffers in comparison to the others here. This is because of the LFU eviction policy being a bad fit for this workload.

![Hit Ratios: CODASYL](https://dgraph.io/blog/images/rt-hit-codasyl.svg?sanitize=true)

#### Throughput

Throughput was measured using the [same utility](https://github.com/dgraph-io/benchmarks/blob/master/cachebench/cache_bench_test.go) as the [previous](https://blog.dgraph.io/post/caching-in-go/) blog post, which generates a large number of keys and alternates between goroutines for Getting and Setting according to the workload.

All throughput benchmarks were ran on an Intel Core i7-8700K (3.7GHz) with 16gb of RAM.

##### Mixed: 25% Writes, 75% Reads

![Mixed Workload](https://dgraph.io/blog/images/rt-thr-mixed.svg?sanitize=true)

##### Read: 100% Reads

![Read Workload](https://dgraph.io/blog/images/rt-thr-read.svg?sanitize=true)

##### Write: 100% Writes

![Write Workload](https://dgraph.io/blog/images/rt-thr-write.svg?sanitize=true)

### Future Improvements

As you may have noticed in the CODASYL benchmarks, [Ristretto](https://github.com/dgraph-io/ristretto)’s performance suffers in LRU-heavy workloads. However, for most workloads, our Sampled LFU policy performs quite well. The question then becomes **“How can we get the best of both worlds?”**

In a [paper](https://dgraph.io/blog/refs/Adaptive%20Software%20Cache%20Management.pdf) called _Adaptive Software Cache Management_, this exact question is explored. The basic idea is placing an LRU “window” before the main cache segment, and adaptively sizing that window using hill-climbing techniques to maximize the hit ratio. Caffeine has already seen [great](https://github.com/ben-manes/caffeine/wiki/Efficiency#adaptivity) results by doing [this](https://github.com/ben-manes/caffeine/wiki/Design#adaptivity). Something we believe Ristretto can benefit from as well in the future.

### Special Thanks

We would like to sincerely thank [Ben Manes](https://github.com/ben-manes). His depth of knowledge and dedicated, selfless sharing has been a large factor in any progress we’ve made and we are honored to have had many conversations with him about all things caching. Ristretto would just not have been possible without his guidance, support and _[99.9%](https://en.wikipedia.org/wiki/High_availability#%22Nines%22)_ availability on our internal Slack channel.

We would also like to thank [Damian Gryski](https://twitter.com/dgryski) for his help with benchmarking Ristretto and writing a reference [TinyLFU](https://github.com/dgryski/go-tinylfu) implementation.

## Conclusion

We set out with the goal of making a cache library competitive with Caffeine. While not completely there, **we did create something significantly [better](https://en.wikipedia.org/wiki/Ristretto)** than most others in the Go world at the moment by using some new techniques that others can learn from.

Some initial experiments with using this cache in Dgraph are looking promising. And we hope to integrate [Ristretto](https://github.com/dgraph-io/ristretto) into both [Dgraph](https://github.com/dgraph-io/dgraph) and [Badger](https://github.com/dgraph-io/badger) in the upcoming months. Do [check it out](https://github.com/dgraph-io/ristretto) and perhaps use Ristretto to speed up your workloads!