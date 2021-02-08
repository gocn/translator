# Go 1.16 即将到来的函数：ReadDir 和 DirEntry

- 原文地址：https://benhoyt.com/writings/go-readdir/
- 原文作者：Ben Hoyt
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w6_coming_in_go_1.16_readdir_and_direntry.md
- 译者：[cvley](https://github.com/cvley)
- 校对：[guzzsek](https://github.com/guzzsek)

2021年1月

作为Python中的 [`os.scandir`](https://docs.python.org/3/library/os.html#os.scandir) 和  [PEP 471](https://www.python.org/dev/peps/pep-0471/) （`scandir`的首次提案）的主要作者，我很开心看到将在2021年2月下旬发布的Go 1.16版本中将增加类似的函数。

在Go中，这个函数叫做 [`os.ReadDir`](https://tip.golang.org/pkg/os/#ReadDir)，是在去年九月提出的[提案](https://github.com/golang/go/issues/41467) 。在100多个评论和对设计进行多次细微调整后，Russ Cox 在10月[提交了对应的代码](https://github.com/golang/go/commit/a4ede9f9a6254360d39d0f45aec133c355ac6b2a)。 这次提交也包含了一个不感知文件系统的版本，是位于新的[`io/fs`](https://tip.golang.org/pkg/io/fs/) 包中 [`fs.ReadDir`](https://tip.golang.org/pkg/io/fs/#ReadDir)的函数。

## 为什么需要ReadDir？

简短的答案是：性能。

当调用读取文件夹路径的系统函数时，操作系统一般会返回文件名_和_它的类型（在Windows下，还包括如文件大小和最后修改时间等的stat信息）。然而，原始版本的Go和Python接口会丢掉这些额外信息，这就需要在读取每个路径时再多调用一个`stat`。系统调用的[性能较差](https://stackoverflow.com/a/6424772/68707) ，`stat` 可能从磁盘、或至少从磁盘缓存读取信息。

在循环遍历目录树时，你需要知道一个路径是文件还是文件夹，这样才可以知道循环遍历的方式。因此即使一个简单的目录树遍历，也需要读取文件夹路径并获取每个路径的`stat`信息。但如果使用操作系统提供的文件类型信息，就可以避免那些`stat`系统调用，同时遍历目录的速度也将提高几倍（在网络文件系统上甚至可以快十几倍）。具体信息可以参考Python版本的[基准测试](https://github.com/benhoyt/scandir#benchmarks)。

不幸的是，两种语言中读取文件夹的最初实现都不是最优的设计，不使用额外的系统调用`stat`就无法获取类型信息：Python中的[`os.listdir`](https://docs.python.org/3/library/os.html#os.listdir)和Go中的 [`ioutil.ReadDir`](https://golang.org/pkg/io/ioutil/#ReadDir) 。

我在2012年首次想到Python的`scandir`背后的原理，并为2015年发布的Python 3.5实现了这个函数（[从这里可以了解更多这个过程的信息](https://benhoyt.com/writings/scandir/)）。此后这个函数不断地被改进完善：比如，增加`with`控制语句和文件描述符的支持。

对于Go语言，除了基于Python版本的经验提出[一些](https://github.com/golang/go/issues/41467#issuecomment-694603286)改进[建议](https://github.com/golang/go/issues/41467#issuecomment-697937162)的[评论](https://github.com/golang/go/issues/41188#issuecomment-686720957)外，我没有参与这个提案或实现。

## Python vs Go

我们看下新的“读取文件夹”的接口，尤其关注下它们在Python和Go中有多么的相似。

在Python中调用`os.scandir(path)`，会返回一个`os.DirEntry`的迭代器，如下所示：

```
class DirEntry:
    # This entry's filename.
    name: str

    # This entry's full path: os.path.join(scandir_path, entry.name).
    path: str

    # Return inode or file ID for this entry.
    def inode(self) -> int: ...

    # Return True if this entry is a directory.
    def is_dir(self, follow_symlinks=True) -> bool: ...

    # Return True if this entry is a regular file.
    def is_file(self, follow_symlinks=True) -> bool: ...

    # Return True if this entry is a symbolic link.
    def is_symlink(self) -> bool: ...

    # Return stat information for this entry.
    def stat(self, follow_symlinks=True) -> stat_result: ...
```

访问`name`和`path`属性将不会抛出异常，但根据操作系统和文件系统，以及路径是否为符号链接，方法的调用可能会抛出`OSError`异常。比如，在Linux下，`stat`总是会进行一次系统调用，因此可能会抛出异常，但`is_X`的方法一般不会这样。

在Go语言中，调用`os.ReadDir(path)`，将会返回一个`os.DirEntry`对象的切片，如下所示：

```
type DirEntry interface {
    // Returns the name of this entry's file (or subdirectory).
    Name() string

    // Reports whether the entry describes a directory.
    IsDir() bool

    // Returns the type bits for the entry (a subset of FileMode).
    Type() FileMode

    // Returns the FileInfo (stat information) for this entry.
    Info() (FileInfo, error)
}
```

尽管在真正的Go风格下，Go版本更加简单，但你一眼就可以看出二者之间多么相似。实际上，如果重新来写Python的`scandir`，我很可能会选择一个更简单的接口——尤其是要去掉`follow_symlinks`参数，不让它默认跟随处理符号链接。

下面是一个使用`os.scandir`的例子——一个循环计算文件夹及其子文件夹中文件的总大小的函数：

```
def get_tree_size(path):
    total = 0
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                total += get_tree_size(entry.path)
            else:
                total += entry.stat(follow_symlinks=False).st_size
    return total
```

在Go中（一旦1.16发布），对应的函数如下所示：

```
func GetTreeSize(path string) (int64, error) {
    entries, err := os.ReadDir(path)
    if err != nil {
        return 0, err
    }
    var total int64
    for _, entry := range entries {
        if entry.IsDir() {
            size, err := GetTreeSize(filepath.Join(path, entry.Name()))
            if err != nil {
                return 0, err
            }
            total += size
        } else {
            info, err := entry.Info()
            if err != nil {
                return 0, err
            }
            total += info.Size()
        }
    }
    return total, nil
}
```

高级结构很相似，当然有人可能会说：“看，Go的错误处理多么繁琐！”没错——Python代码非常简洁。在简短脚本的情况下这没有问题，而这也是Python的优势。

然而，在生产环境的代码中，或者在一个频繁使用的命令行工具库中，捕获stat调用的错误会更好，进而可以忽略权限错误或者记录日志。Go代码可以明确看到错误发生的情况，可以让你轻松添加日志或者打印的错误信息更好。

## 更高级的目录树遍历

另外，两个语言都有更高级的循环遍历目录的函数。在Python中，它是[`os.walk`](https://docs.python.org/3/library/os.html#os.walk)。Python中`scandir`的美妙之处在于`os.walk`的签名无需改变，因此所有`os.walk`的用户（有非常多）都可以自动得到加速。

比如，使用`os.walk`打印文件夹下所有非点的路径：

```
def list_non_dot(path):
    paths = []
    for root, dirs, files in os.walk(path):
        # Modify dirs to skip directories starting with '.'
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.startswith('.'):
                continue
            paths.append(os.path.join(root, f))
    return sorted(paths)
```

从Python3.5开始，`os.walk`底层使用`scandir`代替`listdir`，根据操作系统和文件系统，这可以显著提升1.5到20倍的速度。

Go （pre-1.16版本）语言中有一个相似的函数， [`filepath.Walk`](https://golang.org/pkg/path/filepath/#Walk)，但不幸的是 [`FileInfo`](https://golang.org/pkg/os/#FileInfo) 接口的设计无法支持各种方法调用时的错误报告。正如我们所知，有时函数会进行系统调用——比如，像`Size`这样的统计信息在Linux下总是需要一次系统调用。因此在Go语言中，这些方法需要返回错误（在Python中它们会抛出异常）。

是否要尝试去掉错误处理的逻辑来重复使用 `FileInfo` 接口，这样现有代码就可以显著提速。实际上，Russ Cox提出一个提案 [issue 41188](https://github.com/golang/go/issues/41188)就是这个思路（提供了一些数据来表明这个想法并不像听起来那么不靠谱）。然而，`stat` 确实会返回错误，因此像文件大小这样潜在的属性应该在错误时返回0。这样对应的结果是，要把这个逻辑嵌入到现有的API中，需要大量需要推动改动的地方，最后Russ[确认](https://github.com/golang/go/issues/41188#issuecomment-694596908) 无法就此达成共识，并提出 `DirEntry` 接口。

这表明，为了获得性能提升， `filepath.Walk` 的调用需要改成 [`filepath.WalkDir`](https://tip.golang.org/pkg/path/filepath/#WalkDir) ——尽管非常相似，但遍历函数的参数是`DirEntry` 而不是 `FileInfo`。

下面的代码是Go版本的使用现有`filepath.Walk `函数的`list_non_dot` ：

```
func ListNonDot(path string) ([]string, error) {
    var paths []string
    err := filepath.Walk(path, func(p string, info os.FileInfo,
                                    err error) error {
        if strings.HasPrefix(info.Name(), ".") {
            if info.IsDir() {
                return filepath.SkipDir
            }
            return err
        }
        if !info.IsDir() {
            paths = append(paths, p)
        }
        return err
    })
    return paths, err
}
```

当然，在Go 1.16中这段代码也可以运行，但如果你想得到性能收益就需要做少许修改——在上面的代码中仅需要把 `Walk` 替换为 `WalkDir`，并把 `os.FileInfo` 替换成 `os.DirEntry`：

```
    err := filepath.WalkDir(path, func(p string, info os.DirEntry,
```

对于这么修改的价值，在我的Linux home文件夹下运行第一个函数，在缓存后花费约580ms。使用Go 1.16中的新版本花费约370ms——差不多快了1.5倍。差异并不大，但也是有意义的——在网络文件系统和Windows下将会得到更多的加速效果。

## 总结

新的`ReadDir` API易于使用，通过 `fs.ReadDir`可以便捷地集成新的文件系统。相比于加速现有的`Walk`调用，你所需要替换成`WalkDir`的改动微不足道。

API 的设计非常难。跨平台、操作系统相关的API设计更加困难。希望你在设计下一个编程语言的标准库时可以设计正确！ :-)

无论如何，我很开心可以看到Go对于文件夹读取的支持将不在落后——或者说_努力_紧追——Python。
