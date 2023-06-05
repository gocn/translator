# Build your Golang package docs locally

Previewing the HTML of your go docs from localhost

## Writing Golang docs

For my recent focus on [eBPF](https://bpfdeploy.io/), I've been needing to write more than I ever have before. This also means composing [docs](https://mdaverde.com/posts/hot-reloading-cargo-docs) for variety of ecosystems. While certain tools vary in friction for writers to do their jobs, this post is for a workflow I currently have set up for writing Golang docs.

### `godoc` has been deprecated

Similar to my Rust setup, I wanted to see a rendering of my module docs as they would on [pkg.go.dev](https://pkg.go.dev/) **locally** before publishing. This was [possible](https://stackoverflow.com/a/13530336/1879774) with `godoc` but it's been [deprecated](https://github.com/golang/go/issues/49212) since then with no official solution.

The recommendation now is to point users to [pkgsite](https://github.com/golang/pkgsite/tree/master/cmd/pkgsite) (the tool used to render pkg.go.dev) but it's left as an [exercise to the user](https://github.com/golang/go/issues/40371) on exactly what the setup should be.

So let's do the exercise.

## `pkgsite` cmd

[golang/pkgsite](https://github.com/golang/pkgsite) hosts the cli pkg.go.dev uses for docs rendering. The comments of the `pkgsite` cmd are [concise](https://github.com/golang/pkgsite/blob/master/cmd/pkgsite/main.go#L5) but can get us started:

```
// Pkgsite extracts and generates documentation for Go programs.
// It runs as a web server and presents the documentation as a
// web page.
//
// To install, run `go install ./cmd/pkgsite` from the pkgsite repo root.
```

We'll use this to set up a local server version of pkg.go.dev that contains the documentation rendering functionality for Golang packages. So let's install it. The recommendation I've seen elsewhere is to locally clone this repo, build it and install it somewhere in your `$PATH` but this `go install` should just work:

```
$ go install golang.org/x/pkgsite/cmd/pkgsite@latest
```

Once we have it installed, it should be as easy as running it where our go package repo lives:

```
$ cd /path/to/go/pkg
$ pkgsite
2022/06/16 10:13:55 Info: Listening on addr http://localhost:8080
```

You can customize the bound port with `-http localhost:3030`

Opening up the localhost site will show you a page similar to pkg.go.dev with the search bar and everything. Of course, you won't see any packages if you search because we're rendering just the local package (although there are flags to change this).

### Your local docs

Now, similar to pkg.go.dev, you can check your local module's documentation by appending the module path from your `go.mod` to the url:

`http://localhost:8080/my/local/module/path`

And that's it. You can now see the docs you wrote for your module in web form. With just that `pkgsite` install you can now preview what the docs for your Go project will look like before publishing.

Yet, can we push it further? I don't want to have to manually save the file, kill the server, start it again and refresh the page between thoughts. I want to just have a browser tab open rendering the page as I type from my text editor.

## Hot reload

For this, we'll need a couple of more tools. One that watches when our Go files change and another to communicate to our browser when to reload. Ideally, there would be a _single_ tool to do this (maybe even one day we can have `pkgsite` come with this functionality built in...). If you're from the frontend JavaScript world, this is table stakes and it usually comes with the framework's tooling. Now we'll work for it.

My tool of choice for file watching is [nodemon](https://nodemon.io/). It does its job well and lets me configure it when I need to (and we'll need to). At first, I wanted to find a Go-based file watcher but I couldn't find any that could do what I wanted. I even tried to shoehorn [cosmtrek/air](https://github.com/cosmtrek/air) into this, but didn't work out.

Now that we have a file watcher, we'll want to tell the browser when to reload the page. We'll use [browser-sync](https://browsersync.io/) for this.

### Terminal commands

Here are the key commands we'll use. Open up a new terminal for each process or just background one of them:

```
$ browser-sync start --proxy "localhost:8080"
[Browsersync] Proxying: http://localhost:8080
[Browsersync] Access URLs:
 --------------------------------------
       Local: http://localhost:3000
    External: http://192.168.1.227:3000
 --------------------------------------
          UI: http://localhost:3001
 UI External: http://localhost:3001
 --------------------------------------
```

The reason we need to set up this proxy is because we need an automatic way to communicate to the browser that something has changed. To do this, `browser-sync` injects a bit of javascript into our requests that listens to a signal as to when to reload.

```
$ nodemon --signal SIGTERM --watch my-mod.go --exec "browser-sync reload && pkgsite ."
[nodemon] 2.0.16
[nodemon] to restart at any time, enter `rs`
[nodemon] watching path(s): my-mod.go
[nodemon] starting `browser-sync reload && pkgsite .`
```

And this is how we create that signal. `nodemon` watches `my-mod.go` for file changes and auto-restarts the `pkgsite` process while sending a signal to `browser-sync`.

## Conclusion

With both of these running in parallel, you should now have automated documentation reloading. I can now write my [go doc](https://go.dev/doc/comment) comments in my text editor, save the file and see the tab reload.

There are less excuses to not write now but the developer experience could still be better. Obviously besides just the pain of setting this up, the reloading is slower than necessary. We shouldn't have to wait for the entire process to start and then wait again for it to render my local module before seeing it in my browser tab.

Perhaps by the time you read this article, that [pkgsite issue](https://github.com/golang/go/issues/40371) will be resolved and more doc-focused tooling will exist. Or maybe I'll have a free weekend and send some PRs.