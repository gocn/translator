# 定位并修复 Go 中的内存泄漏

- 原文地址：https://dev.to/googlecloud/finding-and-fixing-memory-leaks-in-go-1k1h
- 原文作者：Tyler Bui-Palsulich
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w42_Finding_and_fixing_memory_leaks_in_Go.md
- 译者：[Fivezh](https://github.com/fivezh)
- 校对：[](.)

这篇文章回顾了我是如何发现内存泄漏、如何修复它、如何修复 `Google` 中的 `Go` 示例代码中的类似问题，以及我们是如何改进我们的基础库防止未来再次发生这种情况。

[`Google` 云的 `Go` 的客户端基础库](https://github.com/googleapis/google-cloud-go)通常在底层使用 `gRPC` 来连接 `Google` 云的接口。当你创建一个客户端时，库会初始化一个与该 接口的连接，然后让这个连接保持打开状态，直到你在该客户端上调用 `Close` 操作。

```golang
client, err := api.NewClient()
// Check err.
defer client.Close()
```

客户端并发地使用是安全的，所以应该在使用完之前保留同一个客户端。但是，如果在应该关闭客户端的时候而没有关闭，会发生什么呢？

你会得到一个内存泄漏：底层连接从未被释放过。

------

`Google` 有一堆的 `GitHub` 自动化机器人，帮助管理数以百计的 `GitHub` 仓库。我们的一些机器人通过[云上运行的](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/go)上的[Go 服务](https://github.com/googleapis/repo-automation-bots/tree/main/serverless-scheduler-proxy)代理它们的请求。我们的内存使用情况看起来就是典型的锯齿状内存泄漏情况。

!["容器内存使用率" 显示先稳定增长、继而下跌至0](../static/images/2021_w42/1dmpo6x8cky6t9dsqsex.png)

我通过在程序中添加 `pprof.Index` 开始调试：

```golang
mux.HandleFunc("/debug/pprof/", pprof.Index)
```

[`pprof`](https://pkg.go.dev/net/http/pprof) 提供运行时的分析数据，比如内存使用量。访问 `Go` 官方博客中的 [分析 `Go` 程序](https://blog.golang.org/pprof) 获取更多信息.

然后，我在本地构建并启动了该服务：

```sh
$ go build
$ PROJECT_ID=my-project PORT=8080 ./serverless-scheduler-proxy
```

然后，我向这个服务发送了一些构造的请求：

```sh
for i in {1..5}; do
curl --header "Content-Type: application/json" --request POST --data '{"name": "HelloHTTP", "type": "testing", "location": "us-central1"}' localhost:8080/v0/cron
echo " -- $i"
done
```

具体的负载和路径是针对我们服务的，与本文无关。
为了获取一个关于内存使用情况的基线数据，我收集了一些初始的 `pprof` 数据。

```sh
curl http://localhost:8080/debug/pprof/heap > heap.0.pprof
```

通过检查输出的结果，可以看到一些内存的使用情况，但并没有发现徒增的问题（这很好！因为我们刚刚启动服务！）。

```sh
$ go tool pprof heap.0.pprof
File: serverless-scheduler-proxy
Type: inuse_space
Time: May 4, 2021 at 9:33am (EDT)
Entering interactive mode (type "help" for commands, "o" for options)
(pprof) top10
Showing nodes accounting for 2129.67kB, 100% of 2129.67kB total
Showing top 10 nodes out of 30
      flat  flat%   sum%        cum   cum%
 1089.33kB 51.15% 51.15%  1089.33kB 51.15%  google.golang.org/grpc/internal/transport.newBufWriter (inline)
  528.17kB 24.80% 75.95%   528.17kB 24.80%  bufio.NewReaderSize (inline)
  512.17kB 24.05%   100%   512.17kB 24.05%  google.golang.org/grpc/metadata.Join
         0     0%   100%   512.17kB 24.05%  cloud.google.com/go/secretmanager/apiv1.(*Client).AccessSecretVersion
         0     0%   100%   512.17kB 24.05%  cloud.google.com/go/secretmanager/apiv1.(*Client).AccessSecretVersion.func1
         0     0%   100%   512.17kB 24.05%  github.com/googleapis/gax-go/v2.Invoke
         0     0%   100%   512.17kB 24.05%  github.com/googleapis/gax-go/v2.invoke
         0     0%   100%   512.17kB 24.05%  google.golang.org/genproto/googleapis/cloud/secretmanager/v1.(*secretManagerServiceClient).AccessSecretVersion
         0     0%   100%   512.17kB 24.05%  google.golang.org/grpc.(*ClientConn).Invoke
         0     0%   100%  1617.50kB 75.95%  google.golang.org/grpc.(*addrConn).createTransport
```

接下来继续向服务发送一批请求，看看我们是否会出现（1）重现前面的内存泄漏，（2）确定泄漏是什么。

发送 500 个请求：

```sh
for i in {1..500}; do
curl --header "Content-Type: application/json" --request POST --data '{"name": "HelloHTTP", "type": "testing", "location": "us-central1"}' localhost:8080/v0/cron
echo " -- $i"
done
```

收集并分析更多的 `pprof` 数据：

```sh
$ curl http://localhost:8080/debug/pprof/heap > heap.6.pprof
$ go tool pprof heap.6.pprof
File: serverless-scheduler-proxy
Type: inuse_space
Time: May 4, 2021 at 9:50am (EDT)
Entering interactive mode (type "help" for commands, "o" for options)
(pprof) top10
Showing nodes accounting for 94.74MB, 94.49% of 100.26MB total
Dropped 26 nodes (cum <= 0.50MB)
Showing top 10 nodes out of 101
      flat  flat%   sum%        cum   cum%
   51.59MB 51.46% 51.46%    51.59MB 51.46%  google.golang.org/grpc/internal/transport.newBufWriter
   19.60MB 19.55% 71.01%    19.60MB 19.55%  bufio.NewReaderSize
    6.02MB  6.01% 77.02%     6.02MB  6.01%  bytes.makeSlice
    4.51MB  4.50% 81.52%    10.53MB 10.51%  crypto/tls.(*Conn).readHandshake
       4MB  3.99% 85.51%     4.50MB  4.49%  crypto/x509.parseCertificate
       3MB  2.99% 88.51%        3MB  2.99%  crypto/tls.Client
    2.50MB  2.49% 91.00%     2.50MB  2.49%  golang.org/x/net/http2/hpack.(*headerFieldTable).addEntry
    1.50MB  1.50% 92.50%     1.50MB  1.50%  google.golang.org/grpc/internal/grpcsync.NewEvent
       1MB     1% 93.50%        1MB     1%  runtime.malg
       1MB     1% 94.49%        1MB     1%  encoding/json.(*decodeState).literalStore
```

`google.golang.org/grpc/internal/transport.newBufWriter`很明显占用了大量的内存! 这就是内存泄漏与什么有关的第一个迹象：gRPC。结合源码，我们唯一使用 `gRPC` 的地方是[Google 云秘钥管理部分](https://cloud.google.com/secret-manager/docs/quickstart)。

```golang
client, err := secretmanager.NewClient(ctx) 
if err != nil { 
    return nil, fmt.Errorf("failed to create secretmanager client: %v", err) 
}
```

我们从未调用过`client.Close()`，并且在每个请求中都创建了一个`Client`! 所以，我添加了一个`Close`调用，问题就解决了。

```golang
defer client.Close()
```

我提交了这个修复, 它 [自动部署完成后](https://cloud.google.com/build/docs/deploying-builds/deploy-cloud-run), 毛刺显现立即消失了!

!["Container memory utilization" showing the sawtooth pattern at the start then dropping to a consistently flat line near 0.](../static/images/2021_w42/z46xksxzus3aluo3cu4k.png)

哇呜! 🎉🎉🎉

------

大约在同一时间，一个用户在我们的[云上的 Go 实例代码库](https://github.com/GoogleCloudPlatform/golang-samples)上提出了一个问题，其中包含了[cloud.google.com](https://cloud.google.com/)上文档的大部分 `Go` 示例程序。该用户注意到我们在其中一个程序中忘记了 `client.Close()` 关闭客户端!

我看到同样的事情出现过几次，所以我决定调查整个仓库。

我从粗略估计有多少受影响的文件开始。使用 `grep` 命令，我们可以得到一个包含 `NewClient` 风格调用的所有文件的列表，然后把这个列表传递给另一个 `grep` 调用，只列出*不*包含`Close`的文件，同时忽略测试文件。

```sh
$ grep -L Close $(grep -El 'New[^(]*Client' **/*.go) | grep -v test
```

> 译者注：列出包含`New[^(]*Client`，但不包含`Close`的所有 go 文件

哇呜! 总共有 207 个文件，而整个 [GoogleCloudPlatform/golang-samples](https://github.com/GoogleCloudPlatform/golang-samples) 仓库中有大约 1300 个 `.go` 文件.

鉴于问题的规模，我认为一些简单的自动化会[很值得](https://xkcd.com/1205/)。我不想写一个完整的 `Go` 程序来编辑这些文件，所以我选择用 `Bash` 脚本。

```sh
$ grep -L Close $(grep -El 'New[^(]*Client' **/*.go) | grep -v test | xargs sed -i '/New[^(]*Client/,/}/s/}/}\ndefer client.Close()/'
```

它是完美的吗？不，但它在工作量上能给我省好多事？是的!

第一部分（直到 `test`）与上面完全一样 -- 获得所有可能受影响的文件的列表（那些创建了 `Client` 但从未调用 `Close` 的文件）。

然后，我把这个文件列表传给 `sed` 进行实际编辑。`xargs` 调用传递的命令，`stdin` 的每一行都作为参数传递给特定的命令。

为了理解 `sed` 命令，看看 `golang-samples` 仓库中的示例程序通常是什么样子（省略导入和客户端初始化后）会很有帮助。

```golang
// accessSecretVersion accesses the payload for the given secret version if one
// exists. The version can be a version number as a string (e.g. "5") or an
// alias (e.g. "latest").
func accessSecretVersion(w io.Writer, name string) error {
    // name := "projects/my-project/secrets/my-secret/versions/5"
    // name := "projects/my-project/secrets/my-secret/versions/latest"
    // Create the client.
    ctx := context.Background()
    client, err := secretmanager.NewClient(ctx)
    if err != nil {
        return fmt.Errorf("failed to create secretmanager client: %v", err)
    }
    // ...
}
```

在高层次上，我们初始化客户端并检查是否有错误。每当你检查错误时，都有一个闭合的大括号（`}`）。我使用这些信息来确定如何自动编辑。

不过，`sed` 命令仍然是个麻烦。

```sh
sed -i '/New[^(]*Client/,/}/s/}/}\ndefer client.Close()/'
```

`-i` 参数表明是原地编辑并替换文件。对此我是没问题，因为如果搞砸了，`git` 可以救我。

接下来，我使用 `s` 命令在检查错误时的关闭大括号（`}`）之后插入 `defer client.Close()`。

但是，我不想替换*每一个`}`，我只想替换调用 `NewClient` *后的*第一个。要做到这一点，你可以给一个让 `sed` 去搜索[*地址范围*](https://www.gnu.org/software/sed/manual/html_node/Addresses.html)。

地址范围可以包括开始和结束模式，以便在应用接下来的任何命令之前进行匹配。在这个例子中，开始是 `/New[^(]*Client/`，匹配 `NewClient` 类型的调用，结束（用`,`分隔）是`/}/`，匹配下一个大括号。这意味着我们的搜索和替换将只适用于对 `NewClient` 的调用和结尾的大括号之间。

通过了解上面的错误处理模式，`if err != nil` 条件的结束括号正是我们要插入 `Close` 调用的地方。

------

一旦自动编辑了所有的文件，运行 `goimports` 来修复格式化。然后，检查了每个编辑过的文件，确保它做了正确的事情。

- 在服务器应用程序中，我们是应该真正关闭客户端，还是应该为未来的请求保留它？
- 客户端的名字实际上是 `client`，还是别的什么？
- 是否有更多的客户端需要 `Close`？

一旦完成这些，我留下了[180 个编辑的文件](https://github.com/GoogleCloudPlatform/golang-samples/pull/2080)

------

最后的任务是努力使用户不再发生这种情况。我们想到了几种方法：

1. 更好的示例程序。
2. 更好的 `GoDoc`。我们更新了我们的库生成器，在生成的库中加入了一个注释，说当你用完后要 `Close` 客户端。参见https://github.com/googleapis/google-cloud-go/issues/3031。
3. 更好的基础库。有什么办法可以让我们自动 `Close` 客户？Finalizer 方法？有什么想法我们可以做得更好吗？请在https://github.com/googleapis/google-cloud-go/issues/4498 上告诉我们。

希望你能学到一些关于 `Go`、内存泄漏、`pprof`、 `gRPC` 和 `Bash` 的知识。我很想听听你关于你所发现的内存泄露的故事，以及你是如何解决这些问题的! 如果你对我们的[代码库](https://github.com/googleapis/google-cloud-go)或[示例程序](https://github.com/GoogleCloudPlatform/golang-samples)有什么想法，欢迎提交问题让我们知道。
