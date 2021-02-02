# Coming in Go 1.16: ReadDir and DirEntry

- 原文地址：https://benhoyt.com/writings/go-readdir/
- 原文作者：Ben Hoyt
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w6_coming_in_go_1.16_readdir_and_direntry.md
- 译者：[cvley](https://github.com/cvley)
- 校对：[](https://github.com/)

January 2021

As the primary author of Python’s [`os.scandir`](https://docs.python.org/3/library/os.html#os.scandir) function and [PEP 471](https://www.python.org/dev/peps/pep-0471/) (the original proposal for `scandir`), I was very happy to see that Go is adding something similar in Go 1.16, which is coming out in late February 2021.

In Go it will be called [`os.ReadDir`](https://tip.golang.org/pkg/os/#ReadDir), and was [proposed](https://github.com/golang/go/issues/41467) last September. After more than 100 comments and several tweaks to the design, it was [committed](https://github.com/golang/go/commit/a4ede9f9a6254360d39d0f45aec133c355ac6b2a) by Russ Cox in October. A file system-agnostic version is also included in the new [`io/fs`](https://tip.golang.org/pkg/io/fs/) package as [`fs.ReadDir`](https://tip.golang.org/pkg/io/fs/#ReadDir).

## Why is ReadDir needed?

The short answer is: performance.

When you call the system functions to read directory entries, the OS typically returns the file name _and_ its type (and on Windows, stat information such as file size and last modified time). However, the original Go and Python interfaces threw away this extra information, requiring you to make an additional `stat` call per entry. System calls [aren’t cheap](https://stackoverflow.com/a/6424772/68707) to begin with, and `stat` may read from disk, or at least the disk cache.

When recursively walking a directory tree, you need to know whether an entry is a file or directory so you know whether to recurse in. So even a simple directory tree traversal required reading the directory entries _and_ `stat`\-ing each entry. But if you use the file type information the OS provides, you can avoid those `stat` calls and traverse a directory several times as fast (even dozens of times as fast on network file systems). See some [benchmarks](https://github.com/benhoyt/scandir#benchmarks) for the Python version.

Both languages, unfortunately, started with a non-optimal design for reading directories that didn’t allow you to access the type information without extra calls to `stat`: [`os.listdir`](https://docs.python.org/3/library/os.html#os.listdir) in Python, and [`ioutil.ReadDir`](https://golang.org/pkg/io/ioutil/#ReadDir) in Go.

I first came up with the idea behind Python’s `scandir` in 2012, and implemented it for Python 3.5, which came out in 2015 ([read more about that process](https://benhoyt.com/writings/scandir/)). It’s been improved and added to since: for example, `with` statement handling and file descriptor support.

For Go, I didn’t have anything to do with the proposal or implementation, apart from a [couple](https://github.com/golang/go/issues/41467#issuecomment-694603286) [of](https://github.com/golang/go/issues/41467#issuecomment-697937162) [comments](https://github.com/golang/go/issues/41188#issuecomment-686720957) suggesting improvements based on my experience with the Python version.

## Python vs Go

Let’s have a look at the new “read directory” interfaces, particularly how similar they are in Python and Go.

In Python you call `os.scandir(path)`, and it returns an iterator of `os.DirEntry` objects, which are as follows:

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
    

Accessing the `name` and `path` attributes will never raise exceptions, but the method calls may raise `OSError`, depending on operating system and file system, and whether the entry is a symbolic link or not. For example, on Linux, `stat` always performs a system call, and hence may raise an exception, but the `is_X` methods usually do not.

In Go you call `os.ReadDir(path)`, and it returns a slice of `os.DirEntry` objects, which look like this:

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
    

You can see the similarities right away, though in true Go fashion, the Go version is somewhat simpler. In fact, if I were doing Python’s `scandir` again, I’d probably push for a slightly simpler interface – in particular, getting rid of the `follow_symlinks` parameter and making it not follow symbolic links by default.

Here’s an example that uses `os.scandir` – a function that calculates the total size of the files in a directory and its subdirectories, recursively:

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

In Go (once 1.16 comes out) it would look like this:

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

A similar high-level structure, though of course someone’s going to say, “see, look how much boilerplate Go’s error handling introduces!” And that’s true – the Python code is very neat. In a little script that would be fine, and that’s where Python excels.

However, in production code, or in a hardened command-line utility, you’d want to catch errors around the stat call, and perhaps ignore permission errors, or log them. The Go code makes explicit the fact that errors can occur, and would easily allow you to add logging or nicer error messages.

## Higher-level tree walking

In addition, both languages have higher-level functions for recursively walking a directory tree. In Python, that’s [`os.walk`](https://docs.python.org/3/library/os.html#os.walk). The beauty of `scandir` in Python is that the signature of `os.walk` didn’t need to change, so all existing users of `os.walk` (of which there are many) got the speed-up automatically.

For example, to print all the non-dot file paths in a directory tree using `os.walk`:

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
    

As of Python 3.5, where `os.walk` uses `scandir` instead of `listdir` under the hood, this will magically be from 1.5 to 20 times as fast, depending on operating system and file system.

Go (pre-1.16) has a similar function, [`filepath.Walk`](https://golang.org/pkg/path/filepath/#Walk), but unfortunately the [`FileInfo`](https://golang.org/pkg/os/#FileInfo) interface wasn’t designed to allow errors to be reported from its various method calls. As we’ve seen, these can sometimes perform system calls – for example, the stat information like `Size` will always require a system call on Linux. So in Go, the methods need to return an error (in Python they raise an exception).

Is was tempting to wave error handling away to try to reuse the `FileInfo` interface, so that existing code would get a magical speed-up. In fact, [issue 41188](https://github.com/golang/go/issues/41188) is a proposal from Russ Cox suggesting just that (with some [data](https://github.com/golang/go/issues/41188#issuecomment-690879673) to show that it’s not as terrible an idea as it sounds). However, `stat` can and does return errors, so there was potential for things like a file size being returned as 0 on error. As a result, there was significant push-back against trying to wedge it into the existing API, and Russ eventually [acknowledged](https://github.com/golang/go/issues/41188#issuecomment-694596908) the lack of consensus and proposed the `DirEntry` interface instead.

What this means is that, to get the performance gain, `filepath.Walk` calls need to be changed to [`filepath.WalkDir`](https://tip.golang.org/pkg/path/filepath/#WalkDir) – very similar, but the walk function receives a `DirEntry` instead of a `FileInfo`.

Here’s what a Go version of `list_non_dot` would look like with the existing `filepath.Walk` function:

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

This will keep working in Go 1.16, of course, but if you want the performance benefits you’ll have to make some very small changes – in this case just changing `Walk` to `WalkDir`, and changing `os.FileInfo` to `os.DirEntry`:

```
    err := filepath.WalkDir(path, func(p string, info os.DirEntry,
```

For what it’s worth, running the first function on my home directory on Linux, once cached, takes about 580ms. The new version using Go 1.16 takes about 370ms – roughly 1.5x as fast. Not a huge difference, but worth it – and you get much larger speed-ups on networked file systems and on Windows.

## Summary

The new `ReadDir` API is easy to use, and integrates nicely with the new file system interface via `fs.ReadDir`. And to speed up your existing `Walk` calls, the tweaks you’ll need to make to switch to `WalkDir` are trivial.

API design is hard. Cross-platform, OS-related API design is even harder. Be sure to get this right when designing your next programming language’s standard library! :-)

In any case, I’m glad that Go’s support for reading directories will no longer be lagging behind – or _walking_ behind – Python.
