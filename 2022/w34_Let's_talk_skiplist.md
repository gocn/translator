# Let's talk SkipList
- 原文地址：https://ketansingh.me/posts/lets-talk-skiplist/
- 原文作者：ketansingh
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w34_Let's_talk_skiplist.md
- 译者：[haoheipi](https://github.com/haoheipi)
- 校对：[]()

## Background

SkipLists often come up when discussing “obscure” data-structures but in reality they are not that obscure, in fact many of the production grade softwares actively use them. In this post I’ll try to go into SkipLists by describing how to make a toy implementation, potential optimizations and real world use cases of them. So what are SkipLists anyway? Well, SkipList are referential data structures inspired from linked list and binary trees. They are collection of sort linked list arranged in different levels, where levels are designed in such a way that it allows skipping nodes to get a logarithmic complexity when searching for the keys later. They are alternative to binary trees and even in some cases the legendary B-Tree, in fact last level of SkipList looks somewhat like a B+Tree. SkipLists perform very well with random write heavy workloads where ordered storage or fast lookup is required. Construction of level(s) is probabilistic in nature, thus these lists can be vulnerable to becoming unbalanced if underlying random algorithm isn’t uniform enough. These are also typically a lot easier to implement compared to HashMaps and Trees which make them ideal for an alternative choice specially if only in memory lookup is required. Why would you wanna use SkipLists? For one, lookup, deletion and insertion has logarithmic complexity. Secondly these are relatively very easy to implement as you don’t need to take care of rebalancing tree (as with RB Trees, AVL Trees, B+Trees) or container resizing (as with HashMaps). Thirdly, thread safe implementation is also not too complex, there are lock and lock-free concurrent implemetations out there and memory footprint is generally low when compared to other ordered collection.

Let’s try to take a peek at SkipList with a diagram.

![](../static/images/2022/w34_Let's_talk_skiplist/1.png)

This diagram essentially represents a collection of linked list data-structure organized in sorted order of the keys. There are different levels, which contain subset of elements from previous level in sorted order. This might depend on implementation but usually there are no multiple copies of same node but it’s just a way to represent same node across different levels. For example in the diagram, `Node 5` which is present in all 3 levels connects to `Node 24, Node 15, Node 7` . It may appear that it has multiple copies but it’s the same node with multiple connections for different levels.


# Toy Implementation

For the implementation, I’ll be using Go with generics because I have been wanting to use them for a while now and there’s no better use case than having a generic type safe collection. Using generic often requires constraints or traits (as rustaceans say) and I couldn’t find the constraints to enforce order in the standard library so I used [golang.org/x/exp/constraints](https://pkg.go.dev/golang.org/x/exp/constraints) package which gives us `Ordered` constraint which will give us a way to compare and keep them sorted them in our SkipList.

## Structures

Let’s define a struct to store key and value for the individual node

```golang
type Record[K constraints.Ordered, V any] struct {  
   Key   K  
   Value V  
}
```

Then the Node itself

```golang
type SkipNode[K constraints.Ordered, V any] struct {  
   record  *Record[K, V]  
   forward []*SkipNode[K, V]  
}
```

Note that `forward[i]` represents next member of the list at `i th` level. In the above diagram, for example, `forward[0]` for `Node 5` will have pointer to `Node 7`, `forward[1]` to `Node 15` and `forward[2]` to `Node 24`

Once we have these structs, we can define constructor functions to help us quickly build the struct

```golang
func NewRecord[K constraints.Ordered, V any](key K, value V) *Record[K, V] {  
   return &Record[K, V]{  
      Key:   key,  
      Value: value,  
   }  
}  

func NewSkipNode[K constraints.Ordered, V any](key K, value V, level int) *SkipNode[K, V] {  
   return &SkipNode[K, V]{  
      record:  NewRecord(key, value),  
      forward: make([]*SkipNode[K, V], level+1),  
   }  
}
```

Finally, we can write the SkipList struct as following

```golang
type SkipList[K constraints.Ordered, V any] struct {  
   head  *SkipNode[K, V]  
   level int  
   size  int  
}
```

We need head node which is basically a “dummy node” to help us maintain connection to the rest of the SkipList, `size` is the number of elements in the SkipList and the `levels` is the number of levels in the current SkipList which will be used later for `Insert` and `Find` operations. Finally to construct the SkipList, we can write the function as following

```golang
func NewSkipList[K constraints.Ordered, V any]() *SkipList[K, V] {  
   return &SkipList[K, V]{  
      head:  NewSkipNode[K, V](new(K), new(V), 0),  
      level: -1,  
      size:  0,  
   }  
}
```

## Find Operation

Find operation is the core algorithm for almost every operation involved with SkipList. It’s pretty much like a binary search but in linked list, as we hit the “roadblock” in our search, we start looking for a level below, skipping bunch of nodes and taking advantage of ordered and leveled structure of SkipList. Algorithm can be summarized as following

- Start looking for your key from the top level of the SkipList.
- Keep moving forward in the same level as long as key is smaller than what you’re looking for.
- If you happen to find the key, return it’s value.
- If next key is bigger than your target key then start looking in the level below.

```golang
func (s *SkipList[K, V]) Find(key K) (V, bool) {  
   x := s.head  
  
   for i := s.level; i >= 0; i-- {  
  
      for {  
         if x.forward[i] == nil || x.forward[i].record.Key > key {  
            break  
         } else if x.forward[i].record.Key == key {  
            return x.forward[i].record.Value, true  
         } else {  
            x = x.forward[i]  
         }  
      }  
   }  
  
   return *new(V), false    
}
```

Visually we can imagine something like following happening while looking for a key

![](../static/images/2022/w34_Let's_talk_skiplist/2.gif)

## Insert Operation

To perform the insert to the SkipList, we need couple of “helper” methods. First one is the which figures out the level for the new node. In our implementation we’re using naive probabilistic approach which is using random function to choose levels, where probability of level is `2^(-L+1)`. This works for the most part and is very simple to implement but it’s efficiency depends on how good the random function is. It may very well always choose level 0. Ideally what we want from the SkipList is to have half the number of nodes than level below it to take the full advantage of the binary search.

```golang
func (s *SkipList[K, V]) getRandomLevel() int {  
   level := 0  
   for rand.Int31()%2 == 0 {  
      level += 1  
   }  
   return level  
}  
```

Second one is `adjustLevel`, this method takes care of increasing the SkipList head’s forward pointer array size to be able to hold pointer for new levels, in case new node’s level is going to be greater than what SkipList currently contains. We don’t really care what Key Value we store in head node’s records, this the reason why I am just storing the zero value in there by `*new(K), *new(V)`. I can also store nil pointers but this will do.

```golang
func (s *SkipList[K, V]) adjustLevel(level int) {  
   temp := s.head.forward  
   
   s.head = NewSkipNode(*new(K), *new(V), level)
   s.level = level  
   
   copy(s.head.forward, temp)  
}
```

Insertion build up on what we described before for “helper” methods and Find operation. It can be summarized in following steps

- Assign a level to the new node
- Resize the SkipList’s head to be able to store points for the assigned level
- Start looking for the appropriate place for the new node at each level by comparing keys and at the same time start building “next” pointer array for the new node. Do it as you travel further down the levels.
- Update the pointers to insert the new node at the correct position.

```golang
func (s *SkipList[K, V]) Insert(key K, value V) {   
   newLevel := s.getRandomLevel()  
  
   if newLevel > s.level {  
      s.adjustLevel(newLevel)  
   }  
  
   newNode := NewSkipNode[K, V](key, value, newLevel)  
   updates := make([]*SkipNode[K, V], newLevel+1)  
   x := s.head  
  
   for i := s.level; i >= 0; i-- {  
      for x.forward[i] != nil && x.forward[i].record.Key < key {  
         x = x.forward[i]  
      }  
      updates[i] = x  
   }  
  
   for i := 0; i <= newLevel; i++ {  
      newNode.forward[i] = updates[i].forward[i]  
      updates[i].forward[i] = newNode  
   }
   
   s.size += 1
}
```

Visually we can imagine something like following happening while looking for a key

![](../static/images/2022/w34_Let's_talk_skiplist/3.gif)

## Delete Operation

Delete operation is very similar to find operation, you just keep removing references as you find your keys across the different levels.

```golang
func (s *SkipList[K, V]) Delete(key K) {  
  
   x := s.head  
  
   for i := s.level; i >= 0; i-- {  
      for {  
         if x.forward[i] == nil || x.forward[i].record.Key > key {  
            break  
         } else if x.forward[i].record.Key == key {  
            x.forward[i] = x.forward[i].forward[i]  
         } else {  
            x = x.forward[i]  
         }  
      }  
   }  
}
```

Visually we can imagine deletion as following.

![](../static/images/2022/w34_Let's_talk_skiplist/4.gif)


# Improving performance

## Memory Access

SkipList like linked list or binary tree are not cache friendly. Most modern CPU tries to predict which memory is going to be used in the future. Most common [algorithm](https://en.wikipedia.org/wiki/Cache_prefetching) is that it assumes program is going to ask for big chunk of contiguous data (like an array) so it tries to load contiguous memory blocks into the cache lines as predicted, but linked list nodes are not necessarily contiguous which will cause [trashing in the CPU cache](https://en.wikipedia.org/wiki/Thrashing_(computer_science)) because only few blocks would be relevant, rest of the space would be wasted as the next node can be in completely different chunk of memory. Arrays fit best in L1 cache but with linked list there’s no guarantee that next node will fit into that or even L2 or L3 which is dependent on how good is memory allocator.

If we look at the latency numbers in the following diagram, it gives us clear picture how bad performance can be with if there’s too frequent cache miss. This implies accessing different nodes in a list can be upto 100-200x times slow compared to accessing next element in an array.

![](../static/images/2022/w34_Let's_talk_skiplist/5.png)

## Using a shared memory allocator

Bane of the problem with SkipLists or LinkedList in general is the memory access pattern which is cache unfriendly. Let’s take a look on how efficient allocation can help us improve the performance.

![](../static/images/2022/w34_Let's_talk_skiplist/6.png)

Memory allocation can take 3 forms which can be seen in above diagram

(1) Is when allocator assigns randomly spread blocks of memory. (2) Is when allocator assigns blocks of memory which are contiguous but not necessary in correct order of list pointers. (3) Is when allocator assigns blocks of memory which are contiguous and in line with the list access pattern.

There’s a good chance that memory allocated for naive implementation might look like something like (1) which basically represents chunks of memory spread all over the place. Any access to next node of the List is going to be cache unfriendly. If we’re using a memory pool or a shared allocator we can have something like (2). All the memory for the nodes can be allocated from a dedicated block of memory. This increases the data cache hit rate and TLB cache hit rate. (3) is what we want in ideal situation but then implementation can be very complicated specially with delete operation.

Some programming languages make it easy to replace the memory allocator like C++ and Rust, This however is tricky with Go. This can be done with [manual memory management](https://dgraph.io/blog/post/manual-memory-management-golang-jemalloc/) and using a custom memory pool.

## Using unrolled SkipList

![](../static/images/2022/w34_Let's_talk_skiplist/7.png

Unrolled SkipList is one which stores multiple elements in each node. Unrolling is designed to give a better cache performance which can depend on the size of the objects which are accessed. These variants can “waste” extra space as each node allocates memory for the array which may not be occupied all the time. Delete operation can be tricky as it creates “gaps” in the node array. Searching is very similar to skip list, and when a candidate is found, the array is searched through linear search. To insert, you push to the array. If no excessive space is available, the insertion happens by adding a new SkipList node.

## Keeping track of elements at each levels

I talked briefly about this while describing one of the helper methods. In my implementation level determination is pretty much non-deterministic and based on probabilties but problem is that, if there’s a bad random function there’s a good chance we end up creating unbalanced SkipList. Unbalanced meaning, one of the levels having too many nodes than ideally required. So in order to make search performance as fast as possible, a smart implementation should ensure that a level has only half the elements of the previous level. Which allows best “skipping” while looking up a key. Ofcourse actively balancing can degrade the insert and delete performance so there needs to be a proper balance.


# SkipList in the wild

SkipLists are not very common when compared to say balanced trees or hashtables but once in a while you do run into them. Personally I have seen them only at the following places but I am pretty sure this is just anecdotal and if you look you can find it at more common places.

## RocksDB

RocksDB is an embeddable persistent key-value store for fast storage. RocksDB can also be the foundation for a client-server database, one of the most popular database using it these days is CockroachDB. RocksDB is built on [LevelDB](https://code.google.com/p/leveldb/) to be scalable to run on servers with multicore CPU, to efficiently use fast storage, to support IO-bound, in-memory and write-once workloads. Internally, RocksDB uses LSM Trees for storage and implementation needs a Memtable to store sorted keys in the memory before it’s flushed into the disk in the form of SST files. One of the implemtation of Memtable in RocksDB is done by SkipList in RocksDB. New writes always insert data to memtable, and reads has to query memtable before reading from SST files, because data in memtable is newer.

Skiplist-based memtable provides general good performance to both read and write, random access and sequential scan. Besides, it provides some other useful features that other memtable implementations don’t currently support, like [Concurrent Insert](https://github.com/facebook/rocksdb/wiki/MemTable#concurrent-insert) and [Insert with Hint](https://github.com/facebook/rocksdb/wiki/MemTable#insert-with-hint).

## Redis SortedSet

Redis Sorted Sets are similar to Sets with the feature that members are stored with user defined values. [To quote Antirez](https://news.ycombinator.com/item?id=1171423), it was chosen over balanced trees because

> 1. They are not very memory intensive. It’s up to you basically. Changing parameters about the probability of a node to have a given number of levels will make then less memory intensive than btrees.
> 2. A sorted set is often target of many ZRANGE or ZREVRANGE operations, that is, traversing the skip list as a linked list. With this operation the cache locality of skip lists is at least as good as with other kind of balanced trees.
> 3. They are simpler to implement, debug, and so forth. For instance thanks to the skip list simplicity I received a patch (already in Redis master) with augmented skip lists implementing ZRANK in O(log(N)). It required little changes to the code.

## MuQSS Linux Scheduler

Con Kolivas maintains a series of scheduler patch sets that he has tuned considerably over the years for his own use, focusing primarily on latency reduction for a better desktop experience. [In early October 2016](http://ck-hack.blogspot.my/2016/10/muqss-multiple-queue-skiplist-scheduler.html), Kolivas updated the design of his popular desktop scheduler patch set, which he renamed MuQSS. MuQSS is CPU Scheduler with multiple run queues, one per CPU. Instead of linked lists, the queues have been implemented as skip lists. Kolivas’s implementation is a custom skip list for his scheduler.


# References

- https://johnysswlab.com/the-quest-for-the-fastest-linked-list/
- https://dgraph.io/blog/post/manual-memory-management-golang-jemalloc/
- https://github.com/facebook/rocksdb/wiki/MemTable#concurrent-insert
- https://www.igvita.com/2012/02/06/sstable-and-log-structured-storage-leveldb/
- https://www.cockroachlabs.com/docs/stable/architecture/storage-layer.html
- https://vldb.org/pvldb/vol9/p1389-srinivasan.pdf
- https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.170.719&rep=rep1&type=pdf
- https://15721.courses.cs.cmu.edu/spring2018/papers/08-oltpindexes1/skiplists-done-right2016.pdf
- https://15721.courses.cs.cmu.edu/spring2018/papers/08-oltpindexes1/pugh-skiplists-cacm1990.pdf
- https://github.com/dai-shi/excalidraw-claymate
- https://lwn.net/Articles/720227/
