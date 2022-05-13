# Writing a simple in-memory key-value Database in Go

[flashdb]: ../static/images/2022/w17_Writing_a_simple_in-memory_key-value_Database_in_Go/flashdb.png
![flashdb][flashdb]
<center style="font-size:14px;color:#C0C0C0;text-decoration">flashdb</center>

We've used databases and have worked on a variety of them, right from Postgres to Redis to Prometheus. I've spent a lot of time reading through the source code of some of these databases. And for those curious few like me who would be interested in learning how to build one, this book aims to document the process.

[GitHub - arriqaaq/flashdb: FlashDB is an embeddable, in-memory key/value database in Go (with Redis like commands)](https://github.com/arriqaaq/flashdb)

## In-Memory Database

In-memory databases are purpose-built databases that rely primarily on memory for data storage, in contrast to databases that store data on disk or SSDs. In-memory data stores are designed to enable minimal response times by eliminating the need to access disks. An in-memory database keeps all data in the main memory or RAM of a computer. A traditional database retrieves data from disk drives.Because all data is stored and managed exclusively in main memory, In-memory databases are more volatile than traditional databases because data is lost when there is a loss of power or the computer’s RAM crashes. In-memory databases can persist data on disks by storing each operation in a log or by taking snapshots.

## Expectations

The aim is to build a simple, fast, embeddable and persistent key/value database in Go that can

- Supports Redis like data structures: `string`,  `hash`, `set`, `zset`.
- Has low latency and high throughput.
- Support transaction, ACID semantics.
- [Durable append-only file](https://github.com/arriqaaq/flashdb#append-only-file) format for persistence.
- Option to evict old items with an [expiration](https://github.com/arriqaaq/flashdb#data-expiration) TTL.

## Getting Started

The aim was to build a very simple KV (key/value) store so that it is easy to for everyone to understand and implement. There are quite a few embedded key/value stores available in Go. Here are a few to list:

- [BadgerDB](https://github.com/dgraph-io/badger) - BadgerDB is an embeddable, persistent, simple and fast key-value (KV) database written in pure Go. It's meant to be a performant alternative to non-Go-based key-value stores like RocksDB.
- [BoltDB](https://github.com/boltdb/bolt) - BoltDB is a B+ tree based embedded key/value database for Go.
- [BuntDB](https://github.com/tidwall/buntdb) - BuntDB is an embeddable, in-memory key/value database for Go with custom indexing and geospatial support
- [go-memdb](https://github.com/hashicorp/go-memdb) - Golang in-memory database built on immutable radix trees
- [nutsdb](https://github.com/xujiajun/nutsdb) - A disk-backed key-value store

It is easier read than done. It is possible to understand the internals reading going through the huge codebases, but that becomes a starting hurdle for many. [NutsDB](https://github.com/xujiajun/nutsdb) was one of the first ones I read 2-3 years back which was simple and easy to read.

Hence, FlashDB is made of composable libraries that are easy to understand. The idea is to bridge the learning for anyone new on how to build a simple ACID database.

## Architecture

[flashdb]: ../static/images/2022/w17_Writing_a_simple_in-memory_key-value_Database_in_Go/flashdb.png
![flashdb][flashdb]
<center style="font-size:14px;color:#C0C0C0;text-decoration">flashdb</center>

The architecture is simple. FlashDB supports a variety of Redis commands. Redis is not a plain key-value store, it is actually a data structures server, supporting different kinds of values. Under the hood, Redis implements various types using the following data structures:

### Strings

The Redis String type is the simplest type of value you can associate with a Redis key. Since Redis keys are strings, when we use the string type as a value too, we are mapping a string to another string. This is implemented using an [Adaptive Radix Tree](https://github.com/arriqaaq/art) (ART) so that scans could be done easily.

- [String](https://github.com/arriqaaq/skiplist)

### Hashes

While hashes are handy to represent objects, actually the number of fields you can put inside a hash has no practical limits (other than available memory), so you can use hashes in many different ways inside your application. This is implemented using a very simple HashMap data structure.

- [Hash](https://github.com/arriqaaq/hash)

### Sets

Redis Sets are unordered collections of strings. It's also possible to do a number of other operations against sets like testing if a given element already exists, performing the intersection, union or difference between multiple sets, and so forth. This is also implemented using a simple HashMap data structure.

- [Set](https://github.com/arriqaaq/set)

### Sorted sets

Sorted sets are a data type which is similar to a mix between a Set and a Hash. Like sets, sorted sets are composed of unique, non-repeating string elements, so in some sense a sorted set is a set as well.

However while elements inside sets are not ordered, every element in a sorted set is associated with a floating point value, called the score (this is why the type is also similar to a hash, since every element is mapped to a value).

This is implemented using a slightly modified skiplist than the one used for strings.

- [ZSet](https://github.com/arriqaaq/zset)

## Persistence

Though there are many persistence mechanisms, I chose a simple append-only log design because it is easier to implement and understand. **AOF** (Append Only File) logs every write operation received by the server, that will be played again at server startup, reconstructing the original dataset. Commands are logged using the same format as the API protocol itself, in an append-only fashion. FlashDB is able to handle multiple segments of the log in the background when it gets too big. This is implemented based on [wal](https://github.com/tidwall/wal)

- [Append Only Log](https://github.com/arriqaaq/aol)

## Conclusion

So that is it. Using the five simple libraries above, [FlashDB](https://github.com/arriqaaq/flashdb) was made. It has transaction and ACID support, which is easy to understand. But I hope this serves as a useful tutorial to anyone interested in learning how to make a database.

[GitHub - arriqaaq/flashdb: FlashDB is an embeddable, in-memory key/value database in Go (with Redis like commands)](https://github.com/arriqaaq/flashdb)

## Talks

I recently spoke about this in the Golang meetup, here is the slide deck.

[https://www.canva.com/design/DAE8sGRyC2o/ZCuCaezQ6dYA0Oq24QxjUQ/view?utm_content=DAE8sGRyC2o&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink](https://www.canva.com/design/DAE8sGRyC2o/ZCuCaezQ6dYA0Oq24QxjUQ/view?utm_content=DAE8sGRyC2o&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink)