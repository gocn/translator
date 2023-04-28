# Don't write clean code, write CRISP code

I'm sure we're all in favour of "clean code", but it's one of those motherhood-and-apple-pie things that no one can reasonably disagree with. Who wants to write *dirty* code, unless maybe it's for a porn site?

The problem, of course, is that few of us can agree on what "clean code" *means*, and how to get there. A rule like "methods should only do one thing" looks great on a T-shirt, but it's not so easy to apply in practice. What counts as "one thing"?

Over a lifetime of programming that began with a ZX81 and hasn't quite ended yet, I've found a few *principles* enduringly useful. Principles are more flexible than rules, and might be more widely applicable.

I think good programs should be Correct, Readable, Idiomatic, Simple, and Performant. So here are my five rules for CRISP code in Go: they're not necessarily in order of importance, except for the first one, but it makes a nice backronym.

## Correct

Your code may have lots of other wonderful things to be said for it, but if it's not *correct*, they don't really matter. And, indeed, if we're willing to give up correctness, we can presumably obtain any other attribute fairly easily.

>*Correctness is the prime quality. If a system does not do what it is supposed to do, everything else about it—whether it is fast, has a nice user interface—matters little. But this is easier said than done.*
>*—Bertrand Meyer, Object-Oriented Software Construction*
It might seem obvious and not worth saying, but if incorrect code exists, and I think it does, then surely it *is* worth saying, because apparently someone didn't get the memo.

What does it mean for code to be correct, actually? The straightforward answer is "it does what the writer intended", but even that's not quite right, because I might have *intended* the wrong thing! For example, I might write a prime number generator while labouring under the erroneous impression that all odd numbers are prime. In this case, my code might produce the odd integers, as I requested, but still not be correct.

A good suite of [tests](https://bitfieldconsulting.com/golang/tdd), again like apple pie, is something just about everyone would love to have, even if they'd prefer that someone else does the hard work to produce it. And tests are a necessary, though not sufficient, part of any good program. No doubt there are some correct programs that don't have tests, but who knows which ones they are?

A well-written test expresses what the programmer thinks the code should do under a given set of circumstances, and running it should give us a certain level of confidence about whether it actually does or not. Tests themselves can be incorrect, though.

This is one reason why we need to be very suspicious and sceptical of any given test. What does it look like it says? Does it *actually* say that? Is it the right thing to say? If it verifies the program's result against some expected result, is the *expectation* correct? If the test claims to cover some particular section of code, does it actually *test* the behaviour of that code in all important ways, or does it merely cause it to be executed?

Not having tests is a terrible situation to be in, but it's actually slightly preferable to having tests that don't work. A malfunctioning or insufficient test may give us false confidence in code that *also* happens to be incorrect.

Therefore, once you've written your tests, read them all again extremely carefully, with an adversarial eye. Programmers are incurable optimists: we always think our code will work, despite much evidence to the contrary. Instead, we should assume that if there can *be* a bug, then there *is* a bug. [Humility](https://bitfieldconsulting.com/golang/tao-of-go) isn't a virtue often associated with software engineers, but it's certainly something that good test writers know all about.

Even the most thoroughly tested code should not be assumed to be correct. It should be assumed to be incorrect. It almost certainly is.

## Readable

Again, this might sound like something that doesn't need saying: who's arguing for *unreadable* code? Not me, but there seems to be a lot of it around, all the same. It's not that anyone deliberately sets out to write unreadable code, of course; it just ends up that way because we mistakenly prioritise other virtues over readability.

[Performance](https://bitfieldconsulting.com/golang/slower) is one such virtue, and there are cases where performance genuinely matters. Not as many as you might think, though: computers are pretty fast these days, and since most of what they do is in the service of us humans, they can usually afford to take their time about it.

So, while readability isn't *quite* as important as correctness, it's more important than anything else. Readability, as Churchill said of courage, is rightly esteemed the first of qualities, because it is the quality which guarantees all others.

What is it that *makes* code readable, or not? I don't think "readability" is something that you can add to your code: I think it's what you're left with when you've taken *away* all the things that make it hard to understand.

For example, a poorly-chosen variable name can put a bump in the reader's path. Using different names for the same thing, or the same name for different things, is confusing. An unnecessary function call, added purely to satisfy some rule like "methods should be less than 10 lines", breaks the reader's flow. It's like reading an article and coming across an unfamiliar word: should you pause to look it up, and risk losing the train of thought, or struggle on and try to infer the meaning from context?

The best way to make any code more readable is, oddly enough, to start by *reading it*. But I mean something special by that. I don't mean scrolling hurriedly through pages and pages of code, glancing and skimming to get a sense of what's happening. That *is* a useful skill, but for other tasks.

Instead, we need to read code in a careful, sequential, *intentional* way. We need to begin at the beginning, and go on till we come to the end. If it's not clear *where* the program begins, then that's the first thing we need to fix.

As we follow the thread of execution of the program, we need to read each line carefully and then try to answer two questions about it:

1. What does it say?
2. What does it mean?
For example, consider the following line:

```plain
requests++
```
What it *says* is clear: it increases the value of some numeric variable `requests` by one. What's not so easy to work out is what that *means*. What is being counted in the `requests` variable? Why is it being incremented? What significance does that have? Where did `requests` get its current value? What *is* its current value? When and where will that value be checked? Is there some *maximum* value? What happens when we reach it? And so on.
There may be perfectly good answers to all these questions, but that's not the point. The point is, can the *reader* answer them just by looking at the code? If not, what can we do to provide the answers, or make them easier to find? By reading our own code as though we were new to it, we see it with fresh eyes and discover the parts that need more cognitive effort to follow.

Reading code in this kind of careful, analytical way is one of the best ways to [really learn](https://bitfieldconsulting.com/golang/how) to write code.

## Idiomatic

I don't think this is quite the right word: I'd prefer "conventional", but again that doesn't fit with the *CRISP* backronym. Still, when people say "such and such is idiomatic", what they really mean is "this is the conventional way to do it."

Conventions are useful: there are lots of possible ways to lay out the driving controls for a car, for example, and the one we're used to isn't demonstrably optimal. It's just the one we're used to. There's no law stopping a car manufacturer from arranging the pedals differently, but they don't, in practice. Even if there were some *ergonomic* benefit, it wouldn't be worth the *cognitive* cost to users.

Similarly, I think there's great value in using conventional *names* for things: in an HTTP handler, the request pointer is always called `r` and the response writer `w`. If there's a universal convention, it's worth following. You'll also have local and personal conventions. In my code, an arbitrary `bytes.Buffer` is always named `buf`, the compared values in my tests are always named `want` and `got`, and so on.

`err` is a good example of a universal convention: Go programmers always use this name to refer to an arbitrary error value. While we wouldn't usually re-use variable names within the same function, we do re-use `err` for all the various errors that there can be throughout the function. It's a mistake to try to avoid this by creating variant names like `err2`, `err3`, and so on.

Why? Because it requires a tiny bit more cognitive effort from the reader. If you see `err`, your mind glides right over it with perfect understanding. If you see some other name, your mind has to stop to resolve the puzzle. I call these tiny roadblocks *cognitive microaggressions*. Each may be so tiny that its individual effect is negligible, yet they soon pile up, and if there are enough of them, they can make a heap of trouble.

As you write each line of code, you should be thinking "How much effort does it take to understand this? Could I reduce that somehow?" The secret of great software engineering is doing a lot of little things well. Picking the right names, organising code in a logical fashion, having one idea per line of code: all these go towards cumulatively making your code readable and pleasant to work with.

How do you learn what's idiomatic and conventional? By reading other people's programs, in the same careful and intentional way that we read our own. You can't write a good novel if you've never *read* a novel, and the same applies to programs. (It's a good idea to read one or two carefully-chosen [books on programming](https://bitfieldconsulting.com/books) too, though this is less important.)

Code found in the wild is of variable quality, and you should make sure to sample as wide a range as you can. It's just as useful to read bad programs as good ones, though for different reasons. You'll find mistakes even in good programs, and when you do, you'll have learned something. But the most useful thing of all to learn is *what everybody does*.

## Simple

Ah, [simplicity](https://bitfieldconsulting.com/golang/tao-of-go). Is there any more slippery and troublesome concept? Everyone thinks they know simplicity when they see it, but oddly enough no two people can agree on what "simple" means in practice.

As Rich Hickey has pointed out, [simple isn't the same as easy](https://www.youtube.com/watch?v=LKtk3HCgTa8). "Easy" is familiar, low-effort, the thing we reach for without thinking. That usually results in "complex", so getting it from there to "simple" can take a good deal of effort and thought.

One aspect of simplicity is *directness*: it does what it says on the tin. It doesn't have weird and unexpected side effects, or conflate several unrelated things. Directness is inversely related to brevity: instead of one short, but complex, function, write three simple, but similar functions.

This is one reason people find it hard to write simple code: we're all terrified of repeating ourselves. The *Don't Repeat Yourself* principle is so ingrained that we even use it as a verb: "we need to DRY up this function" (as Calvin reminds us, [verbing weirds language](https://www.gocomics.com/calvinandhobbes/1993/01/25)).

But there's nothing wrong with repetition in itself. I say again, there's nothing wrong with repetition *in itself*: a task we do many times is probably an important one. And if we find ourselves creating new abstractions to no purpose other than avoiding repetition, then we've gone wrong somewhere. We're making the program more complex, not more simple.

That leads us to another aspect of simplicity: *frugality*. Doing a lot with a little. A package that does one thing is simpler than one that does ten things. The fewer functions there are, and the shallower the call stack, the simpler the program. That might result in some *long* functions, and that's okay. All due respect to Uncle Bob, but a function should be as long as it needs to be. Adding unnecessary complexity *only* to reduce the length of a function is a good example of a blindly-applied rule defeating common sense.

Simplicity, as Alan Perlis observed, does not precede complexity, but follows it. In other words, don't try to *write* simple programs: write the program first, *then* make it simple. Read the code and ask what it says, then ask yourself if you can find a simpler way to write the same thing.

Another place you can find simplicity is in *naturalness*. Any given language has its own [Tao](https://bitfieldconsulting.com/golang/tao-of-go), its own natural forms and structures, and working *with* them generally gets better results than working against them. For example, you can try to use Go as though it were Java, or Python, or Clojure, and there's nothing wrong with those languages, but it's simpler to write Go programs in Go, and the results are better.

## Performant

You might think it strange that I've listed this one last. Isn't practically everything you hear or read about programming related to performance in some way? Yes, it is. But I don't think that's necessarily because performance is *important* so much as that it's easy to talk about. What can be measured is what will be maximised, and it's easy to measure performance: you can use a stopwatch. It's much harder to quantify things like simplicity, or even correctness.

But if the code *isn't* correct, who cares how fast it runs? To put it another way, we can make a given function arbitrarily efficient if it doesn't have to be correct. Similarly, if it's not simple, we will waste far more *programmer* time on understanding it than we could ever have shaved off the CPU time it takes. And programmers are more expensive to run, per hour, than any CPU. Doesn't it make sense to optimise for the limiting resource?

As I've said before, [performance doesn't matter](https://bitfieldconsulting.com/golang/slower) for the vast majority of programs. When it does, the best solution isn't usually to make your code harder to read. The saying "slow is smooth, and smooth is fast" applies here. If you tangle up your program in hopeless complexity to save a couple of microseconds off some loop, great, but that's the last optimisation anyone will ever make to it. Attempting to speed up complex code is usually counterproductive, because if you can't understand it, you can't optimise it. On the other hand, it's easy to speed up a simple program when you have to.

Nevertheless, we should be aware of the performance implications of the choices we make, even if we don't let them push us around. If we didn't need this task doing *fairly* quickly, we wouldn't have given it to a computer. Another way to think about it is that an efficient program can _do_ more in a given time, even if the actual time taken is irrelevant.

To be fair, even an inefficient program will run pretty fast: the inside of a computer is dumb as hell, as Richard Feynman observed, but it goes like mad. That's not to say that we can afford to *waste* time, because computation multiplied by time equals energy, and we are heating up our planet at an already ludicrously unsustainable rate. It would be a shame if we ended up emitting a few extra megatons of carbon just because we made a clumsy choice of data structure.

The idea of "mechanical sympathy" is helpful to bear in mind when you're programming. It means that you have some understanding of how the *machine* works, fundamentally, and you take care not to abuse it or get in its way. For example, if you don't know what *memory* is, how can you write efficient programs?

I often see code that blithely slurps entire data files into memory, then proceeds to actually *process* them just a few bytes at a time. I learned to program on a machine with 1K of memory, or about a thousand words: it wouldn't be enough to hold this article, for example.

I'm writing this, some years later, on a machine with about 16 *million* words of memory, and the words themselves are eight times bigger, so does that mean we can now relax and use as much memory as we want to? No, because the *tasks* have also got bigger.

For one thing, the more data you're schlepping around the system, the longer it takes. For another, however big your Kubernetes cluster, it still consists of physical machines with fixed, finite memory, and no container can use more than the total RAM of a single node. So look after your bytes, and the gigabytes will look after themselves.

## Takeaways

* Anyone who has a foolproof software engineering methodology to sell you is a charlatan, especially if the methodology has a neat backronym.
* Always define your terms to avoid unfortunate misunderstandings: words like "clean", "simple", and "readable" sound great, but, like "freedom", "justice", or "equality", they mean different things to different people.
* Distrust neat slogans like "clean code", "functions should do one thing", or "don't repeat yourself": if you can ever pin them down to a precise meaning, they always turn out to be false.
* Correctness trumps everything else, even readability; this is so obvious we need to remind ourselves of it constantly.
* Tests can only prove that the code does what the test writer thought it should, and most of the time they don't even prove that.
* A faulty or insufficient test is much worse than no test at all, because it *looks* like you have tests.
* All software has bugs, and they fall into two categories: the ones you've found so far, and the ones you haven't.
* Everyone approves of "readability", but disagrees violently about what makes code more or less readable.
* In fact, making programs readable consists largely of finding and removing instances of *unreadability*.
* You may know what the code *says*, but can you tell what it *means*?
* Originality is delightful, except in programming.
* Keep looking for and removing cognitive microaggressions in your code, until you can't find any more, then look a bit harder.
* To become competent, write lots of code; to become a master, *read* lots of code.
* Simple isn't the same as easy.
* _Do_ repeat yourself, when it helps clarity by avoiding unnecessary abstractions.
* First write the program, then make it simple.
* Flow with the Go: work with the language, not against it.
* Optimisation is usually unnecessary, or even counterproductive: don't waste time to save time.
* Your program will likely be fast enough anyway: the inside of a computer is dumb as hell, but it goes like mad.
* Time is infinite, but space is finite, so take every opportunity to trade off speed against memory.
* It's easy to scale your program's speed (run it on more computers), but hard to scale its memory footprint (you can only get so much RAM in a box).
* Look after the bytes, and the gigabytes will look after themselves.
* If you can't be clean, be CRISP.

