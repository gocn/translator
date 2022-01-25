# Large stream processing in Golang with minimal memory usage

- 原文地址：https://engineering.be.com.vn/large-stream-processing-in-golang-with-minimal-memory-usage-c1f90c9bf4ce
- 原文作者：Tài Chí
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w04_Large_stream_processing_in_Golang_with_minimal_memory_usage.md
- 译者：[haoheipi](https://github.com/haoheipi)
- 校对：[ ]( )

Being a member of the Platform team of my company, I have been playing around with many use cases of file handling like handling a universal file uploading center, processing mailing attachments, processing and exporting large files. In the old days, the work has been a lot easier because we are fully controlling a whole server. We can just write to a file that is persistent on servers’ disks, and the resources are much larger for the job. On those days, your codebase is launched on smaller size handling units, like pods. The resources are only virtually allocated and usually limited in many cases, you should be aware of how to use them efficiently. The gracefully handling and OOM termination may be a big problem for those who have already familiar with the free usage of memory.

In my opinion, Reader and Writer are the most crucial parts of Golang. It’s the vital supporter for goroutine and concurrent handling, and the key to the lean and well performance of go programming. Therefore, in order to master the Go programming language, you should be able to manipulate go buffers and goroutines in an elegant and graceful way. In this article, I will discuss the problems I encountered while handling the file stream from satellite client to centralized file uploader, before uploading them to cloud storage engine.

## Multipart file forwarding

In Golang, if you search for anything like reader handling, you should go through something like this.

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

It’s usual to see something like this in your code because many practices over the internet have used this. Since the first time using Reader, I indeed have also used to, too. But, it may deal a lot of damage to your memory usage if you overused it, which significantly the amount of data you can process.

Typically the data you have read is in a predefined format, which means after you read it, you must also pass it to another data processor return do your job. One alternative you can come across is using `io.Copy`:

```golang
r := strings.NewReader("some io.Reader stream to be read\n")
if _, err := io.Copy(os.Stdout, r); err != nil {
  log.Fatal(err)
}
// The data have been copied from Reader r to Stdout
```

Copy is a convenient operation as we won’t need to read the data before writing it to another text process. However, be cautious because it can be another pitfall that you won’t want to step into. It was written in the official document:

> Copy copies from src to dst until either EOF is reached on src or an error occurs. It returns the number of bytes copied and the first error encountered while copying, if any. — go offical docs

With the file offline processing, you can open a buffered writer and fully copy the reader without worrying about the effects. However, the Copy operation will continuously copy your data to your Writer until your Reader drains out. That is an uncontrollable process. If you cannot process your writer as fast as the operation, it will quickly drain out your buffering resources. In addition, handling discard and revoking the allocation of buffers is also a hard thing to consider.

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

There, `io.Pipe` comes to the rescue.

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

Pipe provides a writer and a reader. The read and write operation from both the provided, is synchronous. Write to the writer blocks until previously written data has been fully consumed, with to internal buffering. You can fully control how the data is read and written. The data throughput now depends on how your processor reads the text, and how fast the writer renews its data.

I used it for my file forwarder via microservices, and it worked like a charm. The data is copied and transferred with minimal memory usage. Pipe and Copy created a perfect combo with the intended blocking write provided by Pipe.

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

That actually is how our files traveled between services before the file reached the final destination at the file uploading service. The file stream can be loaded locally via os.Open(), or can be from another request via multipart reader.

## Prefetch and compensate file stream
At our centralized file uploading service, we used the cloud engine for storage, and its API accepts a reader that provides the file raw data. Besides that, we also need to identify the uploaded content type, to determine whether to drop it as the type is not allowed or to classify to available buckets. However, the read operation is irreversible, we must find a way to read the minimum amount of sniff bytes for the mime-type detector while keeping the raw data stream for the latter process.

One viable solution is using `io.TeeReader`, which will write the data to another writer what it read from the reader. The most common use case of `TeeReader` is to clone a stream into a new one, serving the reader while keeping the stream undamaged.

```golang
var r io.Reader = strings.NewReader("some io.Reader stream to be read\n")
var buf = bytes.NewBufferString("")
r = io.TeeReader(r, buf)
// Everything read from r will be copied to buf.
_, _ = io.ReadAtLeast(r, mimeType, 512)
// Continue to copy the stream to write it to buf, to use buf in the following operation
io.Copy(io.Discard, r)
```

But the problem is if you are running it synchronously before passing it to the GCP file handler, it will end up copying all the data to your prepared buffer. One available option is to use the Pipe again to manipulate its no-buffer native. There another problem came as the TeeReader requires the writing process to be complete before the reading process can be complete, while the Pipe requires the opposite.

In the end, we came up with a customized prefetch reader, that was specifically designed to handle that case.

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

With this reader, you can prefetch a number of sniff bytes for handling, then create a new nested reader with the compensation bytes for the following operation.

## Conclusion
Those are how the problem emerged when I’m dealing with my jobs. Manipulating those readers and writers is hard but worth the try as it contains so much fun. I hope you can learn a way to deal with variant problems related to them and have a further good time playing with Go.