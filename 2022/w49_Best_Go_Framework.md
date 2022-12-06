# The Best Go framework: no framework?

- 原文地址：https://threedots.tech/post/best-go-framework/
- 原文作者：Robert Laszczak
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w49_Best_Go_Framework.md
- 译者：[b8kings0ga](https://github.com/b8kings0ga)
- 校对：


While writing this blog and leading Go teams for a couple of years, the most common question I heard from beginners was “What framework should I use?”. One of the worst things you can do in Go is follow an approach from other programming languages.

Other languages have established, “default” frameworks. Java has Spring, Python has Django and Flask, Ruby has Rails, C# has ASP.NET, Node has Express, and PHP has Symfony and Laravel. Go is different: there is no default framework.

What’s even more interesting, many suggest you shouldn’t use a framework at all. Are they insane?

![p1](../static/images/2022/w49_Best_Go_Framework/p1.png)

## The Philosophy of Go
Go frameworks exist, but none provides a feature set like frameworks from other languages. This won’t change soon.

You may think that it’s because the Go ecosystem is younger. But there is a more important factor. Go is built around the Unix Philosophy that says:

> * Write programs that do one thing and do it well.
> * Write programs to work together.
> * Write programs to handle text streams because that is a universal interface.


This philosophy originated from Ken Thompson, the designer of the B programming language (a precursor of C) and also… Go!

In practice, the Unix philosophy favors building small independent pieces of software that do one thing well rather than big chunks that do everything. You may have seen it in your terminal. For example: cat example.txt | sort | uniq. cat reads the text from the file, sort sorts the lines, and uniq removes the duplicates. All commands are independent and do one thing. It comes directly from the Unix philosophy. Thanks to such design, you can independently develop much smaller, autonomous commands.

In Go, the Unix philosophy is visible in the standard library. The best examples are the most widespread interfaces: the io.Reader and the io.Writer. The best libraries follow this philosophy as well.

Frameworks are designed against this philosophy. Often, they try to cover all possible use cases within one framework. They are not designed to work with other tools and often can’t be reused. It means that it’s not possible to transfer development efforts to other non-compatible frameworks. If the framework adoption is low (or it just dies), all the effort is lost.

## What is important for you

Every technical decision has tradeoffs. You need to choose tradeoffs that make more sense for you and your project.

Some approaches make sense when you work on a one-weekend proof of concept and throw it away (you will, right?). In that case, the most critical factor is how quick you can finish it. But if you work on a project that will last a long time and you build it with multiple people, the impact of that decision is tremendous.

For most projects, the most important parameters are:

* how fast can you start the project,
* how fast will you be able to develop this project in the long term,
* how flexible for future changes the project will be (it’s strongly connected with the previous point).

Let’s start assessing our decisions.

## Time saving

One of the biggest promises given by frameworks is time saving. You run one command, and you get a fully functional project. Frameworks usually provide an opinionated structure of the project, and it helps if you don’t know how to do it. But as with most other technical decisions, it’s not free.

With time, when the project grows, you’ll quickly hit the framework’s wall of conventions and limitations. The framework’s author requirements were likely different from yours. The decision taken by the framework creator may work nicely for simple CRUD applications but may not handle more complex scenarios. It’s easy to quickly lose all your time saved on the project bootstrap just to fight with one framework limitation. Over time, it can lead to a lot of frustration in your team.

A couple of years ago, I worked in a company that initially started with one Go framework (I’ll skip the name of the framework). The company was growing and creating new services. With time, we started to feel more pain when we wanted to support more complex use cases. It was also a source of severe bugs. Unfortunately, getting rid of the framework wasn’t easy.

At one point, some framework components became unmaintained and incompatible with the rest of the ecosystem. We were forced to get rid of it. The framework has already become very tightly coupled to the entire system. Removing it from tens of services was a non-trivial task. It required a cross-team initiative that took multiple person-months and a few incidents to get rid of. Even if the project was successful in the end, I didn’t see it in such a way. All the time spent could be used in a much better way if someone took a different decision earlier. The entire project would not be needed. It’s not surprising that many companies suffer from the lack of trust in the development team.

It’s a great example how such a small decision can become a costly rescue project after a couple of years.

![p2](../static/images/2022/w49_Best_Go_Framework/p2.png)


## Maintainability of the project

Measuring the maintainability of projects is a controversial topic — it’s hard to compare two projects. Some people say that frameworks are great and they don’t feel the pain of using them. For others, frameworks can be the biggest nightmare in the long term. Some projects are much more challenging than others. Many people think that fighting with the framework is just a part of the job. That’s why it’s hard to objectively measure the impact of frameworks on the project’s maintainability.

Fortunately, we can help ourselves understand it with a bit of science. More precisely, with the excellent Accelerate: The Science of Lean Software and DevOps book based on scientific research. The book is focused on finding the characteristics of the best and worst-performing teams. What’s important for us, one of the most significant factors for good performance is loosely-coupled architecture.

The teams I led often asked me how to know if our architecture is loosely coupled. One of the simplest ways is ensuring that it’s easy to replace or delete parts of your application. If it’s hard to remove parts of your application, your application is tightly coupled. Touching one thing stars a domino effect of changes in different places.

Why is the loosely coupled architecture that important? Let’s admit it. We are humans, and even after the best research, we make mistakes. When you choose the wrong framework or library, it should be easy to replace it without rewriting the entire project. If we want to save time, we should think what helps in the long term, not only at the beginning of the project.

Consider a scenario when you want to remove the framework entirely. Will it require a lot of code rewrites? Can it be done on multiple services independently? If not, you could put some effort to separate the framework from your core logic. But it requires sacrificing the “time-saving” it gives in the first place.

## The alternative? Building services without a framework
You may feel that building your services without a framework will take ages. Especially if you are coming from other programming languages. I understand that. I had the same feeling a couple of years ago when I started writing in Go. It was an unjustified fear. Not using a framework doesn’t mean that you will need to build everything yourself. There are many proven libraries that provide the functionality you need.

You need to put a bit more effort into research. You’re reading this, so you’re already doing that! Even a couple hours of research are nothing in the entire project’s lifetime. You’ll also get that time back very soon thanks to the flexibility it gives you.

What should you do if you decide not to use a framework? The biggest blocker at the beginning may be how you build a service. The easiest way is to start by putting everything into one file. You can start simple, defer some decisions, and evolve your project with time.

It’s helpful to have example projects you can use as a reference. You can take a look at the project I used for my Let’s build event-driven application in 15 minutes with Watermill presentation at GoRemoteFest – github.com/roblaszczak/goremotefest-livecoding. This example needed just two external libraries to make it functional.

Feel free to clone this repository and adopt to your needs. I’m sure this example doesn’t have all libraries required by your project. To help you with more specific use-cases, next week, we will release an article with a list of Go libraries you can use to build your Go services. We have been using them for a couple of years. We’ll also explain why we use those libraries and how to know if a similar library is good or bad.

![p3](../static/images/2022/w49_Best_Go_Framework/p3.png)

When your project becomes more complex, and you already know how your libraries work together, you can start to refactor it. In the end, you may not need most of the framework features that seemed critical. Thanks to that, you can end up with a simpler project and less research.

If you are looking for a reference on how more advanced projects can look like, you should check Wild Workouts – our fully functional example Go project. We released a +200 pages free e-book describing how we built that application.

## Summary

Deciding how you build services is not where you should take shortcuts. Making a wrong decision may have a very negative impact on your time in the long term. It negatively affects your team’s velocity and, more importantly, morale.

After making a wrong decision, you can quickly fall into the sunk cost fallacy trap. Instead of becoming heroes who solve problems they created, we should avoid creating them.

After that article’s lecture, you should know each way’s tradeoffs and implications. You can now make a responsible decision. I hope this article will help avoid at least one company a couple-man-months painful refactoring project.

Do you have any framework horror stories (even from a different programming language)? Let us know in the comments!