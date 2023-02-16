# Ristretto 简介： 一个高性能GO缓存

- 原文地址：[Introducing Ristretto: A High-Performance Go Cache](https://dgraph.io/blog/post/introducing-ristretto-high-perf-go-cache/)
- 原文作者：[Dmitry Filimonov](https://github.com/petethepig)
- 本文永久链接：[Ristretto 简介： 一个高性能GO缓存](https://github.com/gocn/translator/blob/master/2023/w05_Introducing%20Ristretto%20A%20High-Performance%20Go%20Cache%20-%20Dgraph%20Blog.md)
- 译者：[784909593](https://github.com/784909593)
- 校对：[b8kings0ga](https://github.com/b8kings0ga)

**这个博客登上了 Golang [subreddit](https://www.reddit.com/r/golang/comments/d6taoq/introducing_ristretto_a_highperformance_go_cache/) 的顶部，并且在 [Hacker News](https://news.ycombinator.com/item?id=21023949) 的trending上排在前十位。 一定要在那里参与讨论，并通过给我们一个 [star](https://github.com/dgraph-io/dgraph)，表达对我们的喜欢。**

经过六个月的研发，我们自豪的宣布**缓存 [Ristretto](https://github.com/dgraph-io/ristretto)：一个高性能、并发、可设置内存上限的 Go 缓存**的初始版本。他是抗争用、扩展性好、提供稳定的高命中率。


### 前言

这一切都始于 [Dgraph](https://github.com/dgraph-io/dgraph) 中需要一个可设置内存上限的、并发的 Go 缓存。我们四处寻找解决方案，但是没有找到一个合适的。然后我们尝试使用分片 map，通过分片驱逐来释放内存，这导致了我们的内存问题。然后我们重新利用了 Groupcache 的 [LRU](https://github.com/golang/groupcache/blob/master/lru/lru.go), 用互斥锁保证线程安全。使用了一年之后，我们注意到缓存存在严重的争用问题。一个 [commit](https://github.com/dgraph-io/dgraph/commit/b9990f4619b64615c2c18bb7627d198b4397109c) 删除了该缓存，使我们的查询延迟显著改善了 5-10 倍。**本质上，我们的缓存正在减慢我们的速度!**

我们得出的结论是，Go 中的并发缓存库已经坏了，必须修复。 在三月, 我们写了一篇关于 [Go 中的缓存状态](https://blog.dgraph.io/post/caching-in-go/), 提到数据库和系统需要一个智能的、可设置内存上限的缓存的问题，它可以扩展到 Go 程序所处的多线程环境。特别的，我们将这些设置为缓存的要求：

1.  并发的；
2.  缓存命中率高；
3.  Memory-bounded (限制为可配置的最大内存使用量)；
4.  随着核数和协程数量的增加而扩展；
5.  在非随机key访问(例如 Zipf)分布下很好的扩展；

发布了[博客文章](https://blog.dgraph.io/post/caching-in-go/)之后，我们组建了一个团队来解决其中提到的挑战，并创建了一个值得与非 Go 语言缓存实现进行比较的 Go 缓存库。特别的，[Caffeine](https://github.com/ben-manes/caffeine) 这是一个基于 Java 8 的高性能、近乎最优的缓存库。许多基于 Java 8 的数据库都在使用它, 比如 Cassandra，HBase，和 Neo4j。[这里](http://highscalability.com/blog/2016/1/25/design-of-a-modern-cache.html)有一篇关于 Caffeine 设计的文章。

### Ristretto: Better Half of Espresso

从那以后我们[阅读](https://dgraph.io/blog/refs/bp_wrapper.pdf)[了](https://dgraph.io/blog/refs/Adaptive%20Software%20Cache%20Management.pdf)[文献](https://dgraph.io/blog/refs/TinyLFU%20-%20A%20Highly%20Efficient%20Cache%20Admission%20Policy.pdf), 广泛的测试了实现 ，并讨论了在写一个缓存库时需要考虑的每一个变量。 今天，我们自豪的宣布他已经准备好供更广泛的 Go 社区使用和实验。

在我们开始讲解 [Ristretto](https://github.com/dgraph-io/ristretto) 的设计之前, 这有一个代码片段展示了如何使用它：

```
func main() {
cache, err := ristretto.NewCache(&ristretto.Config{
NumCounters: 1e7,     // key 跟踪频率为（10M）
MaxCost:     1 << 30, // 缓存的最大成本 (1GB)。
BufferItems: 64,      // 每个 Get buffer的 key 数。
})
if err != nil {
panic(err)
}

cache.Set("key", "value", 1) // set a value
// 等待值通过 buffer
time.Sleep(10 * time.Millisecond)

value, found := cache.Get("key")
if !found {
panic("missing value")
}
fmt.Println(value)
cache.Del("key")
}
```

#### 指导原则

[Ristretto](https://github.com/dgraph-io/ristretto) 建立在三个指导原则之上：

1.  快速访问；
2.  高并发和抗争用；
3.  可设置内存上限；

在这篇博文中，我们将讨论这三个原则以及我们如何在 Ristretto 中实现它们。

### 快速访问

尽管我们喜欢 Go 和它对功能的固执己见，但一些 Go 的设计决策阻止我们榨取我们想要的所有性能。最值得注意的是 Go 的并发模型。由于对 CSP 的关注，大多数其他形式的原子操作被忽略了。这使得难以实现在缓存库中有用的无锁结构。例如, Go [不](https://groups.google.com/d/msg/golang-nuts/M9kF6Tdh2Vo/3tLSFYYOGgAJ)提供 thread-local 存储.

缓存的核心是一个 hash map 和关于进入和出去的规则。如果 hash map 表现不佳，那么整个缓存将受到影响。 与 Java 不同, Go 没有无锁的并发 hashmap。相反，Go 的线程安全是必须通过显式获取互斥锁来达到。

我们尝试了多种实现方式（使用 Ristretto 中的`store`接口），发现`sync.Map`在读取密集型工作负载方面表现良好，但在写入工作负载方面表现不佳。考虑没有 thread-local 存储，**我们发现使用分片的互斥锁包装的 Go map具有最佳的整体性能。** 特别是，我们选择使用 256 个分片，以确保即使在 64 核服务器上也能表现良好。

使用基于分片的方法，我们还需要找到一种快速方法来计算 key 应该进入哪个分片。这个要求和对 key 太长消耗太多内存的担忧，导致我们对 key 使用 `uint64`，而不是存储整个 key。理由是我们需要在多个地方使用 key 的哈希值，并且在入口处执行一次允许我们重用该哈希值，避免任何更多的计算。

**为了生成快速 hash，我们从 Go Runtime 借用了 [runtime.memhash](https://github.com/dgraph-io/ristretto/blob/master/z/rtutil.go#L42-L44)** 该函数使用汇编代码快速生成哈希。 请注意，这个 hash 有一个随机化器，每当进程启动时都会初始化，这意味着相同的key不会在下一次进程运行时生成相同的哈希。 但是，这对于非持久缓存来说没问题。 在我们的[实验](https://github.com/dgraph-io/ristretto/blob/master/z/rtutil_test.go#L11-L44), 我们发现它可以在 10ns 内散列 64 字节的 key。

```
BenchmarkMemHash-32 200000000 8.88 ns/op
BenchmarkFarm-32    100000000 17.9 ns/op
BenchmarkSip-32      30000000 41.1 ns/op
BenchmarkFnv-32      20000000 70.6 ns/op
```

然后，我们不仅将此 hash 用作被存储的 key，而且还用于确定 key 应该进入的分片。_这个确实引入了 key 冲突的机会，这是我们计划稍后处理的事情。_

### 并发和抗争用

实现高命中率需要管理有关缓存中，存在的内容以及缓存中应该存在的内容的元数据。当跨 goroutine 平衡缓存的性能和可扩展性时，这变得非常困难。
幸运的是，有一篇名为 BP-Wrapper 的[论文](https://dgraph.io/blog/refs/bp_wrapper.pdf)写了一个系统框架，可以使任何替换算法几乎无锁争用。本文介绍了两种缓解争用的方法：预取和批处理。我们只使用批处理。

批处理的工作方式与您想象的差不多。**我们不是为每个元数据变化获取互斥锁，而是等待 ring buffer 填满，然后再获取互斥锁并处理变化。**如论文中所述，这大大降低了争用，而且开销很小。

我们将此方法用于缓存的所有 `Gets` 和 `Sets`。

#### Gets

当然，所有对缓存的 Get 操作都会立即得到服务。困难的部分是捕获 Get，因此我们可以跟踪 key 访问。 在 LRU 缓存中，通常将 key 放在链表的头部。在我们基于 LFU 的缓存中，我们需要增加一个 item 的命中计数器。这两个操作都需要对缓存全局结构进行线程安全访问。[BP-Wrapper](https://dgraph.io/blog/refs/bp_wrapper.pdf) 建议使用批处理来处理命中计数器增量，但问题是我们如何在不获取另一个锁的情况下实现此批处理过程。

这听起来像是 Go chan 的完美用例，事实确实如此。不幸的是，chan 的吞吐量性能阻止了我们使用它们。**相反，我们设计了一种巧妙的方法使用 `sync.Pool` 来实现条带化的有损 [ring buffers](https://github.com/dgraph-io/ristretto/blob/master/ring.go#L99-L104)**，这些缓冲区具有出色的性能并且几乎没有数据丢失。

存储在 pool 中的任何 item 都可能随时自动删除，[不另行](https://golang.org/pkg/sync/#Pool)通知。_这引入了一个级别的有损行为。_ Pool 中的每个 item 实际上都是一批 key。当批次填满时，它会被推送到一个 chan。chan 大小故意保持较小，以避免消耗太多 CPU 周期来处理它。 如果 chan 已满，则丢弃该批次。_这引入了二级有损行为。_ 一个 goroutine 从内部 chan 中获取这批数据并处理这些 key，更新它们的命中计数器。

```
AddToLossyBuffer(key):
  stripe := b.pool.Get().(*ringStripe)
  stripe.Push(key)
  b.pool.Put(stripe)

一旦 buffer 填满，push 到 chan:
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

使用 `sync.Pool` 比其他任何东西（slice、携带互斥锁等）的性能都好，主要是由于 thread-local 存储的内部使用，_这是 Go 用户无法从公共 API 获得的东西。_

#### Sets

Set buffer 的要求与 Get 略有不同。在 Gets 中，我们缓冲 key，只有在 buffer 填满后才处理它们。 在 Sets 中，我们希望尽快处理 key。**因此，我们使用一个 chan 来捕获 Set，如果 chan 已满则将它们丢掉以避免争用。**几个后台 goroutine 从 chan 中挑选 set 并处理 set。

与 Gets 一样，此方法旨在优化抗争用性。 但是，有一些注意事项，如下所述。

```
select {
case c.setBuf <- &item{key: hash, val: val, cost: cost}:
    return true
default:
    // 丢弃 set 操作并避免阻塞
    c.stats.Add(dropSets, hash, 1)
    return false
}
```

#### 注意事项

[Ristretto](https://github.com/dgraph-io/ristretto) 中的 Set 进入 buffer 排队，控制权返回给调用者，然后将 buffer 应用于缓存。这有两个副作用：

1.  **无法保证会应用 Set 操作** 它可以立即删除以避免争用，也可以稍后被策略拒绝。
2.  即使应用了 Set，在调用返回给用户后也可能需要几毫秒。用数据库术语来说，它是一个 _最终的一致性_ 模型。

但是，如果缓存中已存在密钥，则 Set 将立即更新该密钥。这是为了避免缓存的 key 保存过时的值。


#### 抗争用

**Ristretto 针对抗争用进行了优化。**这在高并发负载下表现非常好，正如我们将在下面的吞吐量基准测试中看到的那样。但是，它会丢失一些元数据以换取更好的吞吐量性能。

有趣的是，由于密钥访问分布的性质，信息丢失不会影响我们的命中率性能。 如果我们确实丢失了元数据，它通常会均匀丢失，而密钥访问分布仍然是不均匀的。 因此，我们仍然实现了高命中率，并且命中率下降很小，如下图所示。

![Ristretto 命中率下降](https://dgraph.io/blog/images/rt-hit-degrade.svg?sanitize=true)

### 可设置内存上限

#### Key 成本

_无限大的缓存实际上是不可能的。_ 缓存的大小必须有界。许多缓存库会将缓存大小视为元素的数量。我们发现这种方法 _很幼稚_。当然，它适用于值大小相同的工作负载。然而，大多数工作负载具有可变大小的值。一个值可能需要几个字节，另一个可能需要几千字节，还有一个需要几兆字节。将它们视为具有相同的内存成本是不现实的。

**在 [Ristretto](https://github.com/dgraph-io/ristretto) 中, 我们将成本附加到每个 key-value** 用户可以在调用 Set 时指定该成本是多少。我们将此成本计入缓存的 MaxCost。 当缓存满负荷运行时，一个 _重_ 的 item 可能会取代许多 _轻_ 的item。 这种机制很好，因为它适用于所有不同的工作负载，包括每个 key-value 成本为 1 的朴素方法。

#### 通过 TinyLFU 的准入策略

> ”我们应该让什么进入缓存？“

显然，我们的目标是让比当前 item 更 _“有价值”_ 的新 item 进入。 但是，如果您考虑跟踪相关 item 的与 _“价值”_ 问题有关的信息所需的开销（延迟和内存），这将成为一个挑战。

尽管这是一个有据可查的提高命中率的策略，但大多数 Go 缓存库根本没有准入策略。事实上，许多 LRU 驱逐实现都假定最新的密钥是最有价值的。

此外，大多数 Go 缓存库使用纯 LRU 或 LRU 的近似值作为它们的驱逐策略。尽管 LRU 近似的质量很高，但某些工作负载更适合 LFU 逐出策略。 我们在使用各种跟踪的基准测试中发现了这种情况。

对于我们的准入政策，我们看了一篇引人入胜的新论文名为 **[TinyLFU](https://dgraph.io/blog/refs/TinyLFU%20-%20A%20Highly%20Efficient%20Cache%20Admission%20Policy.pdf): 一个高效的缓存准入策略** 在非常高的层次上，TinyLFU 提供了三种方法：

-   Increment(key uint64)
-   Estimate(key uint64) int (referred as ɛ)
-   Reset

该[论文](https://dgraph.io/blog/refs/TinyLFU%20-%20A%20Highly%20Efficient%20Cache%20Admission%20Policy.pdf)对其进行了最好的解释，但 TinyLFU 是一种与逐出无关的准入策略，旨在以极少的内存开销提高命中率。主要思想是**只有当新 item 的估计值高于被驱逐 item 的估计值时，才允许新 item 进入。**我们使用 [Count-Min](https://en.wikipedia.org/wiki/Count%E2%80%93min_sketch) 在 [Ristretto](https://github.com/dgraph-io/ristretto) 中实现了 TinyLFU。它使用 4 位计数器来估算 item (ɛ) 的访问频率。每个 key 的这种小成本，使我们能够跟踪比使用普通的频率 map，更大的全局 key 空间里的样本。

TinyLFU 还通过`重置`功能维护 key 访问的新近度。每 N 个 key 递增后，计数器减半。因此，一个很久没有出现的 key，其计数器将被重置为零；为最近出现的 key 铺平道路。

#### 通过采样 LFU 的驱逐策略

当缓存达到容量时，每个传入的 key 都应替换缓存中存在的一个或多个 key。 不仅如此，**传入 key 的 ε 应该高于被驱逐 key 的 ε。**为了找到一个 ε 低的 key，我们使用 Go map 迭代提供的自然[随机性](https://blog.golang.org/go-maps-in-action)来选择key样本并循环，在它们之上找到具有最低ε的key。

然后我们将这个 key 的 ɛ 与传入的 key 进行比较。如果传入的 key 具有更高的 ε，则该 key 将被逐出（_驱逐策略_）。否则，传入的 key 将被拒绝（_准入策略_）。重复此机制，直到传入 key 的成本可以放入缓存中。因此，一个传入的 key 可能取代一个以上的 key。_注意，传入 key 的成本在选择驱逐 key 时不起作用。_

**使用这种方法，在各种工作负载下，命中率与精确 LFU 策略的误差在 1% 以内。** 这意味着我们在同一个包中获得了准入策略、保守内存使用和较低争用的好处。

```
// 准入和驱逐算法的片段
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

在我们将新 key 放入 TinyLFU 之前，[Ristretto](https://github.com/dgraph-io/ristretto) 使用布隆过滤器首先检查该 key 是否曾被见过。只有当该 key 已经存在于布隆过滤器中时，它才会被插入到 TinyLFU 中。这是为了避免 TinyLFU 被那些不被多次看到的长尾 key 所 _污染_。

在计算一个 key 的 ε 时，如果 item 包含在 bloom filter 中，它的频率估计就是 TinyLFU 的 Estimate 加一。在 TinyLFU`重置`期间，布隆过滤器也被清除。

### Metrics

虽然是可选的，但了解缓存的行为方式是很重要的。我们希望确保跟踪与缓存相关的指标不仅是可能的，而且这样做的开销足够低，可以打开并保持。

除了命中和未命中，Ristretto 还追踪一些指标，如添加、更新和逐出的 key 及其成本，set 操作被丢弃或拒绝，以及 get 操作丢弃或保留的次数。所有这些数字有助于了解各种工作负载下的缓存行为，并且为了进一步优化铺平道路。

我们最初为这些使用原子计数器。然而，开销是巨大的。我们把原因缩小到 [False Sharing](https://dzone.com/articles/false-sharing)。考虑多核系统，其中不同的原子计数器(每个 8 字节)位于统一 cache line（通常为 64 字节）。任何更新改变计数器，都会导致其他计数器被标记 _无效_。这会强制为持有该缓存的所有其他核心重新加载缓存，从而在 cache line 上产生写入争用。

**为了实现可扩展性，我们确保每个原子计数器完全占据一个完整的 cache line。**所以，每个核在不同的 cache line 上工作。Ristretto 通过为每个 metric 分配 256 个 uint64 来使用它，在每个活动的 uint64 之间留下 9 个未使用的 uint 64。为了避免额外的计算，重用 key hash 值去决定要增加哪个 uint64。

```
Add:
valp := p.all[t]
// 通过在两个将递增的原子计数器之间填充至少 64 字节的空间来避免 false sharing。
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

读取指标时，会读取全部的 uint64 并求和，以获取最新的数字。**使用这种方法，metrics 跟踪只对缓存性能添加 10% 左右的开销。**

### Benchmarks

现在你了解了 [Ristretto](https://github.com/dgraph-io/ristretto) 中存在的各种各样的机制，让我们看看与其他流行的 Go 缓存相比的命中率和吞吐量 benchmark。

#### 命中率

命中率是使用 Damian Gryski 的 [cachetest](https://github.com/dgraph-io/benchmarks/blob/master/cachebench/cache_bench_test.go) 和我们自己的 benchmarking [套件](https://github.com/dgraph-io/benchmarks/tree/master/cachebench)测量的. 两个程序的命中率数字相同，但我们添加了读取某些 trace 格式 (特别是 LIRS and ARC)以及 CSV 输出的功能，以便于绘制图表。如果你想编写自己的 benchmark 或者添加一种 trace 格式，请查看 [sim](https://github.com/dgraph-io/ristretto/tree/master/sim) 包。

为了更好地了解改进空间，**我们添加了一个理论上[最佳的](https://en.wikipedia.org/wiki/Page_replacement_algorithm#The_theoretically_optimal_page_replacement_algorithm)缓存实现, 它使用未来的知识来驱逐在其的整个生命周期内命中次数最少的.** 注意这是一个能预见未来的 LFU 驱逐策略，其他能预见未来的策略可能用 LRU。 根据工作负载，LFU 或 LRU 可能更适合，但我们发现能预见未来的 LFU 对于与 [Ristretto](https://github.com/dgraph-io/ristretto) 的 Sampled LFU 进行比较很有用。

##### 查找

这个 trace 被描述为“由大型商业搜索引擎发起的磁盘读取访问，以响应各种网络搜索请求”

![命中率: 查找](https://dgraph.io/blog/images/rt-hit-search.svg?sanitize=true)

##### 数据库

这个 trace 被描述为“在一个商业数据库上，一个商业网站正运行一个ERP应用，一个数据库服务运行在上面“

![命中率: 商业数据库](https://dgraph.io/blog/images/rt-hit-db.svg?sanitize=true)

##### 循环

这个 trace 演示了循环访问模式。我们不能在此和后续的 benchmark 中包括 Fastcache、Freecache 或 Bigcache 实现，因为它们具有会影响结果的最低容量要求。一些跟踪文件很小并且需要小容量来进行性能测量。

![命中率: Loop](https://dgraph.io/blog/images/rt-hit-loop.svg?sanitize=true)

##### CODASYL

这个 trace 被描述为”在一小时内引用 CODASYL 数据库。“ 请注意与这里的其他库相比 [Ristretto](https://github.com/dgraph-io/ristretto) 的性能受到影响。 这是因为 LFU 逐出策略不适合此工作负载。

![命中率: CODASYL](https://dgraph.io/blog/images/rt-hit-codasyl.svg?sanitize=true)

#### 吞吐量

吞吐量是使用与[上一篇](https://blog.dgraph.io/post/caching-in-go/)博文[相同程序](https://github.com/dgraph-io/benchmarks/blob/master/cachebench/cache_bench_test.go)测量的，该程序会生成大量 key，并根据设置的工作负载在 Get 和 Set 的 goroutine 之间交替。

所有吞吐量基准测试均在具有 16gb RAM 的英特尔酷睿 i7-8700K (3.7GHz) 上运行。

##### 混合: 25% Writes, 75% Reads

![混合工作负载](https://dgraph.io/blog/images/rt-thr-mixed.svg?sanitize=true)

##### 读取: 100% Reads

![读工作负载](https://dgraph.io/blog/images/rt-thr-read.svg?sanitize=true)

##### 写入: 100% Writes

![写工作负载](https://dgraph.io/blog/images/rt-thr-write.svg?sanitize=true)

### 未来的改进

正如您可能已经在 CODASYL benchmark 中注意到的那样，[Ristretto](https://github.com/dgraph-io/ristretto) 的性能在 LRU 繁重的工作负载中受到影响. 然而，对于大多数工作负载，我们的 Sampled LFU 策略表现相当好。这个问题就变成了“**我们怎么能两全其美**”

在一篇名为 _Adaptive Software Cache Management_ 的[论文](https://dgraph.io/blog/refs/Adaptive%20Software%20Cache%20Management.pdf) , 探讨了这个确切的问题. 这个基本思想是在主缓存片段之前放置一个 LRU 窗口，并且使用爬山（hill-climbing）技术自适应地调整该窗口的大小以最大化命中率。Caffeine 已经通过[这个](https://github.com/ben-manes/caffeine/wiki/Design#adaptivity)看到了[重大](https://github.com/ben-manes/caffeine/wiki/Efficiency#adaptivity)的结果。我们相信 Ristretto 将来也能从中收益。

### 特别感谢

我们诚挚的感谢 [Ben Manes](https://github.com/ben-manes)。他的知识深度和专注,、无私的分享是我们取得任何进步的重要隐私，我们很荣幸能与他就缓存的所有方面进行对话。没有他的指导、支持和我们内部 Slack 频道 _[99.9%](https://en.wikipedia.org/wiki/High_availability#%22Nines%22)_ 的可用性，Ristretto 是不可能的。

我们还要感谢 [Damian Gryski](https://twitter.com/dgryski) 在对 Ristretto 进行基准测试和编写参考 [TinyLFU](https://github.com/dgryski/go-tinylfu) 实现方面提供的帮助。

## 结论

我们的目标是让缓存库与 Caffeine 竞争。虽然没有完全实现, 但我们确实通过使用其他人可以学习的一些新技术，创造了比目前Go世界中大多数其他人[**更好**](https://en.wikipedia.org/wiki/Ristretto)的东西。
在 Dgraph 中使用此缓存的一些初步实验看起来很有希望。并且我们希望将 [Ristretto](https://github.com/dgraph-io/ristretto) 整合到 [Dgraph](https://github.com/dgraph-io/dgraph) 和 [Badger](https://github.com/dgraph-io/badger) 在接下来的几个月里. 一定要[查看它](https://github.com/dgraph-io/ristretto)，也许可以使用 Ristretto 来加快您的工作负载。
