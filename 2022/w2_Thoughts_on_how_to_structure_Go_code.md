# Thoughts on how to structure Go code
***
- 原文地址：https://changelog.com/posts/on-go-application-structure
- 原文作者：Jon Calhoun
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[]()
***
App structure is complicated.

Good app structure improves the developer experience. It can help you isolate what they are working on without needing to keep the entire codebase in your head. A well structured app can help prevent bugs by decoupling components and making it easier to write useful tests.

A poorly structured application can do the opposite; it can make testing harder, it can make it challenging to find relevant code, and it can introduce needless complexity and verbosity that slows you down with no real benefits.

That last bit is important - using a structure that is far more complex than needed can actually hurt a project more than help it.

What I’m writing here likely isn’t news to anyone. Programmers are taught very early on about the importance of organizing their code. Whether it is naming variables and functions, or naming and organizing files, this is a topic covered early in nearly every programming course.

All of this begs the question - why is it so damn hard to figure out how to structure Go code?

### Organizing by context

In a past Q&A episode of Go Time we were asked about structuring Go applications and Peter Bourgon responded with the following:

> A lot of languages have this (I guess) convention of all of the project structures being roughly the same, for the same type of project… Like, if you’re doing a web service in Ruby, you’re gonna have this layout, and the packages are gonna be named after the architectural patterns you’re using. MVC, for example; controllers etc. But in Go, that’s not really what we do. We have package and project structures that are basically reflective of the domain of the thing we’re implementing. Not of the patterns we use, not of the scaffolding, but of the specific types and entities in the domain of the project that we’re working in.
> 
> **So it is always idiomatically different from project to project, by definition.** What makes sense in one doesn’t make sense in another. Not to say it’s the only way to do things, but this is what we tend to do… And so yeah, there’s no answer, and that kind of truth about what is idiomatic in the language is extremely confusing for a lot of people, and it may be the wrong choice as a result… I don’t know, but I think that’s the main point.
> 
> [Peter Bourgon](https://twitter.com/peterbourgon) on [Go Time #147](https://changelog.com/gotime/147#transcript-185). Emphasis added by me.

Most successful Go applications are, by and large, not structured in a way that can be copy/pasted from project to project. That is, we can’t take the general folder structure and copy it over to a new application and expect it to work, because the new application will very likely have a unique set of contexts to work from.

Rather than looking for a template to copy, the best way to start is to think about the contexts of your application. To help you understand what I mean, let’s try to walk through how we might structure the web application used to host my Go courses.

![A screenshot of Jon's Go courses dashboard](https://github.com/gocn/translator/raw/master/static/images/2022/w2_Thoughts_on_how_to_structure_Go_code/courses-app-screenshot.png)

_Background info: My Go courses application is a website where students enroll in courses and view individual lessons from the course. Most lessons have a video component, links to the code used in the lesson, and other related info. If you have ever used any video course website you should have a general idea of what it looks like, but if you want to dig a bit further you can sign up for [Gophercises](https://gophercises.com/) for free._

At this point I’m pretty familiar with the needs of the application, but I’m going to try to walk you through my thought process when I originally started creating the application, as that is the state you will often be starting from.

Getting started, there are two main contexts I want to consider:

1.  The student context.
2.  The admin/teacher context.

The student context is what most people will be familiar with. In this context users sign into an account, view a dashboard with courses they have access to, and can then navigate down to individual lessons in the course.

The admin context is a bit different, and most people won’t see it. As an admin we are less worried about consuming courses, and more concerned with managing them. We will need to be able to add a new lesson to a course, to update videos for existing lessons, and more. In addition to being able to manage courses, the admin context will also entail managing users, purchases, and refunds.

To create this separation, my repo will start with two packages:

```
admin/
  ... (some go files here)
student/
  ... (some go files here)
```

By separating these two packages, I am able to define entities differently in each context. For instance, a `Lesson` from a student’s perspective mostly consisted of URLs to resources, and it has user-specific information like a `CompletedAt` field indicating when/if that particular user completed the lesson.

```
package student

type Lesson struct {
  Name         string 
  Video        string 
                      
  SourceCode   string 
  CompletedAt  *time.Time 
                          
  
}
```

Meanwhile, the admin `Lesson` type doesn’t have a `CompletedAt` field because that doesn’t make sense in this context. That information is only relevant in the context of a signed in user viewing a course, not as an admin managing a course’s contents.

Instead, the admin Lesson type will provide access to fields like `Requirement`, which will be used to determine if a user has access to content. Other fields will look a bit different as well; rather than a URL to the video, the `Video` field might instead be information about where the video is hosted, as this is how admins will update the content.

```
package admin


type Lesson struct {
  Name string
  
  
  Video struct {
    Provider string 
    ExternalID string
  }
  
  SourceCode struct {
    Provider string 
    Repo     string 
    Branch   string 
  }
  
  
  
  
  
  
  Requirement string
}
```

I am opting to go this route because I believe these two contexts will vary enough to justify the separation, but I also suspect that neither will grow to be large enough to justify any further organization.

Could I organize this code differently? Absolutely!

One way I might change the structure is by separating it further. For instance, some of the code that made its way into the `admin` package relates to managing users, while other pieces of code related to managing courses. It would have been pretty easy to split that into two contexts. Alternatively, I could pull all of the code related to authentication - signing up, changing your password, etc - and placed that into an `auth` package.

Rather than overthinking it, I find it more useful to pick something that looks like a reasonably good fit and to adapt as needed.

### Packages as layers

Another way to break up an app is by dependency. Ben Johnson discusses this a good bit at [gobeyond.dev](https://www.gobeyond.dev/), specifically in the article [Packages as layers, not groups](https://www.gobeyond.dev/packages-as-layers/). The concept is very similar to the [hexagonal architecture](https://www.youtube.com/watch?v=oL6JBUk6tj0&t=1614s) mentioned by Kat Zien in her GopherCon talk, “How Do You Structure Your Go Apps.”

At a high level, the idea is that we have a core domain where we define our resources and the services we use to interact with them.

```
package app

type Lesson struct {
  ID string
  Name string
  
}

type LessonStore interface {
  Create(*Lesson) error
  QueryByPermissions(...Permission) ([]Lesson, error)
  
}
```

Using types like `Lesson` and interfaces like `LessonStore` we can code up a complete application. We can’t run our program without an implementation of the `LessonStore`, but we can write all of the core logic without worrying about how it is implemented.

When we are ready to implement an interface like the `LessonStore` we add a new layer to our application. In this case it would likely be in the form of an `sql` package.

```
package sql

type LessonStore struct {
  db *sql.DB
}

func Create(l *Lesson) error {
  
}

func QueryByPermissions(perms ...Permission) ([]Lesson, error) {
  
}
```

_If you want to read more about this strategy, I highly recommend you check out Ben’s writing at [https://www.gobeyond.dev/](https://www.gobeyond.dev/)._

The package by layers approach may seem wildly different than what I opted for with my Go courses, but it is actually much easier to mix-n-match these strategies than it first appears. For instance, if we treat `admin` and `student` each as a domain where resources and services are defined, we can use the package by layers approach to implement those services. Below is an example of this using the `admin` package domain and the `sql` package which has an implementation of the `admin.LessonStore`.

```
package admin

type Lesson struct {
  
}

type LessonStore interface {
  Create(*Lesson) error
  
}
```

```
package sql

import "github.com/joncalhoun/my-app/admin"

type AdminLessonStore struct { ... }

func (ls *AdminLessonStore) Create(lesson *admin.Lesson) error { ... }
```

Is that the correct choice for the application? I don’t know.

Using interfaces like this definitely makes it easier to test smaller pieces of code, but that only matters if it provides real benefits. Otherwise we end up writing interfaces, decoupling code, and creating new packages with no real benefit. Basically, we are creating busywork for ourselves.

### The only wrong decision is no decision

Going beyond these structures, there are countless other ways to structure (or not structure) code that can make sense depending on the context. I have experimented with using a flat structure - one single package - on a number of projects, and I am still shocked at how well that works. When I first started writing Go code I used MVC almost exclusively. Not only does this work better than the community as a whole might lead you to believe, but it allowed me to get past that decision paralysis caused by not knowing how to structure my application, and thus, not knowing where to even start.

In the same Q&A Go Time episode where we were asked how to structure Go code, Mat Ryer expressed the upside to not having one set way to structure code:

> I think it can be quite liberating though to say that there isn’t really a way to do it, which also means you can’t really do it wrong. It’s what fits for your case.
> 
> [Mat Ryer](https://twitter.com/matryer) on [Go Time #147](https://changelog.com/gotime/147#transcript-186)

Now that I have plenty of experience using Go, I fully agree with Mat. It IS liberating being able to decide what structure fits each application. I love that there isn’t a set way to do things, nor is there really a wrong way. Despite feeling that way now, I also recall being quite frustrated at not having concrete examples to work from when I was less experienced.

The truth is, deciding what structure fits your situation is nearly impossible without some experience, yet it feels like we are forced to make that decision before we can gain any experience. It is a catch-22 that stops us before we even get started.

Rather than giving up, I opted to just use what I knew - MVC. This allowed me to write code, to get something working, and to learn from those mistakes. Over time I started to understand other ways of structuring code, and my applications resembled MVC less and less, but it was a very incremental process. I suspect if I had forced myself to get the app structure right immediately, I wouldn’t have succeeded at all. At best I would have succeeded after a great deal of frustration.

It is absolutely true that MVC will never provide as much clarity as an app structure tailored to the project. It is equally true that discovering the ideal app structure for a project isn’t a realistic goal for someone with little to no experience structuring Go code. It takes practice, experimenting, and refactoring to get right. MVC is simple and approachable. It is a reasonable starting point when we don’t have enough experience or context to come up with something better.

### Summing up

As I said at the beginning of this article, good app structure is meant to improve the developer experience. It is meant to help you organize your code in a way that makes sense to you. It isn’t meant to leave newcomers paralyzed and unsure how to proceed.

If you find yourself stuck and unsure how to proceed, ask yourself what is more productive - remaining stuck, or picking any app structure and giving it a try?

With the former nothing gets done. With the latter, even if you get it wrong you can learn from the experience, and do better the next time. That sounds far better than never starting.

___

