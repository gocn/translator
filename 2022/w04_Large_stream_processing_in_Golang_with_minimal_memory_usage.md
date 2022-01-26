# Golang 在大规模流处理场景下的最小化内存使用

- 原文地址：https://engineering.be.com.vn/large-stream-processing-in-golang-with-minimal-memory-usage-c1f90c9bf4ce
- 原文作者：Tài Chí
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w04_Large_stream_processing_in_Golang_with_minimal_memory_usage.md
- 译者：[haoheipi](https://github.com/haoheipi)
- 校对：[ ]( )

作为公司平台团队的一员，我接触了很多文件处理的场景，比如管理一个通用文件上传中心服务，处理邮件附件，处理和导出大文件。在过去，这项工作要容易得多，因为我们可以完全支配整个服务器。我们可以写入一个文件让它持久化在服务器磁盘上，尽管这个作业所需的资源是非常多的。而现在，你的代码库是在更小的处理单元上发布的，比如 pods 。它的资源是虚拟分配的，并且在许多情况下是有限的，所以你需要知道如何有效地使用它们。实现优雅的处理和解决 OOM 退出问题也许对于那些已经熟悉自由地使用内存的人来说是一个大麻烦。

在我看来，`Reader` 和 `Writer` 是 Golang 最重要的部分。它给 goroutine 和并发处理提供了重要支持，是 Go 编程模型精简且具有良好性能的关键。因此，为了更进一步掌握 Go 编程语言，你应该能够优雅地操作 go buffers 和 goroutines。在本文中，我将讨论在文件上传到云存储引擎之前，处理从卫星客户端的文件流到中央文件上传器时遇到的问题。

## Multipart 文件转发

在 Golang，如果你搜索任何类似 `reader` 操作，你应该得到过下面这些内容：

```golang
r := strings.NewReader("Go is a general-purpose language designed with systems 
programming in mind.")
b, err := ioutil.ReadAll(r)
if err != nil {
   log.Fatal(err)
}
// Playing with your loaded bytes
fmt.Printf("%s", b)
```

在你的代码中看到这样的东西是很常见的，因为在互联网上的许多实践都使用了这种方法。自从我第一次使用 `Reader`，我也确实习惯了这样用。但是，如果你过度使用它，可能会对内存使用造成很大的损耗，这将极大地影响你可以处理的数据量。

典型场景当你读取的数据是已经预定义好格式的，这意味着在你读取它之后，还必须将它传递给另一个数据处理器再返回你的工作。你可能会使用的一种选择是 `io.Copy`:

```golang
r := strings.NewReader("some io.Reader stream to be read\n")
if _, err := io.Copy(os.Stdout, r); err != nil {
  log.Fatal(err)
}
// The data have been copied from Reader r to Stdout
```

`Copy` 是一种非常方便的操作，因为在将数据写入另一个文本进程之前，我们不需要读取数据。然而要小心的是这可能会导致你落入一个不想踏入的陷阱。官方文件中写道:

> 从 src 复制副本到 dst，直到在 src 上到达 EOF 或发生错误。它返回复制的字节数和复制时遇到的第一个错误(如果有的话)。 --- Go 官方文档

在文件离线处理时，你可以打开一个带缓冲的 `writer` 然后完全复制 `reader` 中内容，并且不用担心任何其他影响。然而，`Copy` 操作将持续地将数据复制到 `Writer`，直到 `Reader` 读完数据。但这是一个无法控制的过程，如果你处理 `writer` 中数据的速度不能与复制操作一样快，那么它将很快耗尽你的缓冲区资源。此外，选择丢弃或者撤销缓冲区分配也是一件很难考虑的事情。

```golang
buf := new(bytes.Buffer)
writer := multipart.NewWriter(buf)
defer writer.Close()
part, err := writer.CreateFormFile("file", "textFile.txt")
if err != nil {
   return err
}
file, err := os.Open(name)
if err != nil {
   return err
}
defer file.Close()
if _, err = io.Copy(part, file); err != nil {
   return err
}
http.Post(url, writer.FormDataContentType(), buf)
```

这里 `io.Pipe` 就出现来解决这类问题。

```golang
r, w := io.Pipe()
go func() {
   fmt.Fprint(w, "some io.Reader stream to be read\n")
   w.Close()
}()
if _, err := io.Copy(os.Stdout, r); err != nil {
   log.Fatal(err)
}
```

`Pipe` 提供一对 `writer` 和 `reader`，并且读写操作都是同步的。利用内部缓冲机制，直到之前写入的数据被完全消耗掉才能写到一个新的 `writer` 数据快。这样你就可以完全控制如何读取和写入数据。现在，数据吞吐量取决于处理器读取文本的方式，以及 `writer` 更新数据的速度。

我用它来做我的微服务文件转发器，实际工作效果非常好。能够以最小的内存使用量来复制和传输数据。有着 `Pipe` 提供的写阻塞功能 ，`Pipe` 和 `Copy` 就形成了一个完美的组合。

```golang
r, w := io.Pipe()
m := multipart.NewWriter(w)
go func() {
   defer w.Close()
   defer m.Close()
   part, err := m.CreateFormFile("file", "textFile.txt")
   if err != nil {
      return
   }
   file, err := os.Open(name)
   if err != nil {
      return
   }
   defer file.Close()
   if _, err = io.Copy(part, file); err != nil {
      return
   }
}()
http.Post(url, m.FormDataContentType(), r)
```

在文件到达文件上传服务的最终目的地之前，这实际上就是我们的文件在各个服务之间传输的方式。文件流可以通过 `os.Open()` 在本地加载，也可以通过 `multipart reader` 从其他请求中加载。

# 预取和补偿文件流
在我们的中央文件上传服务中，我们使用云引擎进行存储，它的 API 接受一个提供文件原始数据的 `reader`。除此之外，我们还需要识别上传的内容类型，以确定是否将其删除，还是将其分类到可用的 bucket 中。但是，读取操作是不可逆的，我们必须找到一种方法，为类型检测器读取最小长度的嗅探字节，同时也需要为后一个过程保留原始数据流。

一个可行的解决方案是使用 `io.TeeReader`，它会将从 `reader` 读取的数据写入另一个 `writer` 中。`TeeReader` 最常见的用例是将一个流克隆成一个新的流，在保持流不被破坏的情况下为 `reader` 提供服务。

```golang
var r io.Reader = strings.NewReader("some io.Reader stream to be read\n")
var buf = bytes.NewBufferString("")
r = io.TeeReader(r, buf)
// Everything read from r will be copied to buf.
_, _ = io.ReadAtLeast(r, mimeType, 512)
// Continue to copy the stream to write it to buf, to use buf in the following operation
io.Copy(io.Discard, r)
```

但问题是，如果在将其传递给 GCP 文件处理程序之前同步运行它，它最终还是会将所有数据复制到准备好的缓冲区。一个可行的方法是再次使用 `Pipe` 来操作它，达到无本地缓存效果。但另一个问题是，`TeeReader` 要求在完成读取过程之前必须完成写入过程，而 `Pipe` 则相反。

所以最后我们设计了一个定制化的预取 `reader`，专门用来处理这种情况。

```golang
package services

import (
   "fmt"
   "io"
)

type prefetchReader struct {
   reader   io.Reader
   prefetch []byte
   size     int
}

func newPrefetchReader(reader io.Reader, prefetch []byte) *prefetchReader {
   return &prefetchReader{
      reader:   reader,
      prefetch: prefetch,
   }
}

func (r *prefetchReader) Read(p []byte) (n int, err error) {
   if len(p) == 0 {
      return 0, fmt.Errorf("empty buffer")
   }
   defer func() {
      r.size += n
   }()
   if len(r.prefetch) > 0 {
      if len(p) >= len(r.prefetch) {
         copy(p, r.prefetch)
         n := len(r.prefetch)
         r.prefetch = nil
         return n, nil
      } else {
         copy(p, r.prefetch[:len(p)])
         r.prefetch = r.prefetch[len(p):]
         return len(p), nil
      }
   }
   return r.reader.Read(p)
}
```

使用这个 `reader`，你可以预取一些嗅探字节以进行处理，然后使用补偿字节创建一个新的嵌套 `reader` 用于后面的操作。

## 结论
这就是我在工作中遇到的问题。操作这些 `readers` 和 `writers` 是非常麻烦的，但还是非常值得一试，因为这其中包含了很多乐趣。我希望你能学习到一种处理与它们相关的各种问题的方法，并能有一个更好的 Go 使用体验。