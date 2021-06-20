# Functional programming in Go with generics

Date: [May 25, 2021  19:00:00](#)

Functional programming is an increasing popular programming paradigm with many languages building or already supporting it. Go already supports some of these features such as first-class and higher order functions and enabling functional programming.

One key feature that’s been missing from Go is generics. Without this feature, functional Go libraries and applications are forced down one of two paths: type safe + use-case specific or type-unsafe + use-case agnostic. With the upcoming release of Go 1.18 in early 2022, [generics are expected to be added to the language](https://blog.golang.org/generics-proposal) which will enable new sorts of functional programming solutions in Go.

In this article, I’ll cover some [background on functional programming](#Background), survey functional programming landscape today in Go, and discuss features planned for Go 1.18 and how they could enable functional programming.

## Background

### What is functional programming?

Functional programming as defined by [Wikipedia](https://en.wikipedia.org/wiki/Functional_programming) is:

> programming paradigm where programs are constructed by applying and composing functions.

In more concrete terms, there’s a few key characteristics to functional programming:

*   **pure functions** - a function that when called with the same input always returns the same output with no shared state, mutable data, or side effects
*   **immutable data** - data is never reassigned or changed after creation
*   **function composition** - combining multiple functions together to apply logic to data
*   **declarative over imperative** - express _what_ the function must do without defining _how_ to achieve it

For more detailed information on Functional Programming, have a look at these two great articles that describe it at length with examples: [What is Functional Programming?](https://medium.com/javascript-scene/master-the-javascript-interview-what-is-functional-programming-7f218c68b3a0) and [Functional Go](https://medium.com/@geisonfgfg/functional-go-bc116f4c96a4)

### What are the benefits of functional programming?

Functional programming imposes some patterns on developers that improve code quality. These quality improvements are not exclusive to functional programming but are “free” benefits.

*   **testability** - testing pure functions is simpler because the function will never produce effects outside of it’s scope (e.g. console output, database writes) and will always produce predictable output
*   **expressiveness** - functional language/library primitives being declarative can be more effective at expressing the original intent of code albeit with the overhead cost of learning those primitives
*   **understandability** - reading and understanding a pure function with no side effects, global state, or mutation is subjectively easier

As many developers know from experience and as Robert C. Martin stated in [_Clean Code_](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882):

> Indeed, the ratio of time spent reading versus writing is well over 10 to 1. We are constantly reading old code as part of the effort to write new code. …\[Therefore,\] making it easy to read makes it easier to write.

These benefits can be highly impactful depending on the team’s experience with or willingness to learn functional programming. On the opposite end, functional programming can be a drag on inexperienced teams without enough time to invest in learning or large legacy codebases where it could introduce context switching or significant rework without delivering proportional value.

## Functional Programming in Go today

Go is not a functional language but it does offer a set of features which allow for functional programming. There’s a sizeable number of open source Go libraries available that provide functional feature sets. As we will discuss, the omission of generics has guided these libraries to make one of two tradeoffs.

### Language Features

Language support for functional programming lies on a spectrum ranging from functional paradigm only (e.g. Haskell) to multi-paradigm + first-class support (e.g. Scala, Elixir) to multi-paradigm + partial support (e.g. Javascript, Go). In the latter category of languages, functional programming is typically supported through the use of community created libraries that replicate some or all of the features in the standard libraries of the former two.

Go being in the last category does offer these features which enable functional programming:

| Language Feature                                             | Support |
| ------------------------------------------------------------ | ------- |
| [first-class functions + higher order functions](https://golangbot.com/first-class-functions/) | ✓       |
| [closures](https://tour.golang.org/moretypes/25)             | ✓       |
| [generics](https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md) | ✓†      |
| [tail call optimization](https://github.com/golang/go/issues/22624) | ✗       |
| [variadic functions](https://gobyexample.com/variadic-functions) + [variadic type parameters](https://en.wikipedia.org/wiki/Variadic_template) | ✗       |
| [currying](https://blog.bitsrc.io/understanding-currying-in-javascript-ceb2188c339) | ✗       |

† available in Go 1.18 (early 2022)

### Existing Libraries

In the Go ecosystem, there’s already exist many functional programming libraries that vary in popularity, features, and ergonomics. Due to the omission of generics, they’ve all had to make one of two design choices:

1.  **type safe + use-case specific** - libraries that chose this approach implemented a design that is type safe but only capable of handling certain pre-defined types. Without being able to use custom types or structs, the variety of problems these libraries can be applied to is limited.
    *   For example, `func UniqString(data []string) []string` and `func UniqInt(data []int) []int` are both type safe but only work on the pre-defined types
2.  **type unsafe + use-case agnostic** - libraries that chose this approach implemented a design that is not type safe but can be applied to any use case. These libraries work with custom types and structs but with the tradeoff that [type assertions](https://tour.golang.org/methods/15) must be used which exposes the application to the risk of a runtime panic if improperly implemented.
    *   For example, a generic unique function might have this signature: `func Uniq(data interface{}) interface{}`

These two design choices present two similarly unappealing options: limited utility or runtime panic risk. The easiest and perhaps most common option is to not use a functional programming library with Go and stick with an imperative style.

## Functional Go with Generics

On March 19th 2021, the [design proposal](https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md) for generics was accepted and slated for release as part of Go 1.18. With the addition of generics, functional programming libraries no longer need to make tradeoff between usefulness and type safety.

### Experimenting with Go 1.18

The go development team released a [go 1.18 playground](https://go2goplay.golang.org/) where anyone can try running go with generics. There’s also an experimental compiler that implements a minimal set of features available [on a branch](https://github.com/golang/go/tree/dev.go2go) of the go repository. Both of these options are great for playing around with generics in Go 1.18.

### Exploring a use-case

Earlier, the unique function was described with the two possible design approaches. With generics, this could be revised to `func Uniq[T](data []T) []T` and called with any type such as `Uniq[string any](data []string) []string` or `Uniq[MyStruct any](data []MyStruct) []MyStruct`. Taking this concept further, below is a concrete example that demonstrate how functional primitives can be used to solve real problems with Go 1.18 generics.

#### Background

A common use case in the web world is HTTP request-response where JSON data is returned from an API and it commonly will need to be transformed into something usable by the consuming application.

#### Problem & Input Data

Consider this response from an API that returns users, their points, and fiends:

```
[
  {
    "id": "6096abc445dbb831decde62f",
    "index": 0,
    "isActive": true,
    "isVerified": false,
    "user": {
      "points": 7521,
      "name": {
        "first": "Ramirez",
        "last": "Gillespie"
      },
      "friends": [
        {
          "id": "6096abc46573cedd17fb0201",
          "name": "Crawford Arnold"
        },
        ...
      ],
      "company": "SEALOUD"
    },
    "level": "gold",
    "email": "ramirez.gillespie@sealoud.com",
    "text": "Consequat pariatur aliquip pariatur mollit mollit cillum sint. Elit est nisi velit cillum. Ex mollit dolor qui velit Lorem proident ullamco magna velit nulla qui. Elit duis non ad laborum ullamco irure nulla culpa. Proident culpa esse deserunt minim sint nisi duis culpa nostrud in incididunt ad. Amet qui laborum deserunt proident adipisicing exercitation quis.",
    "created_at": "Saturday, August 3, 2019 8:12 AM",
    "greeting": "Hello, Ramirez! You have 9 unread messages.",
    "favoriteFruit": "banana"
  },
  ...
]
```

Let’s say the goal was to get the top users by points in each level. We’ll examine what the solution could look like with both functional and imperative styles next.

#### Imperative

```
// imperative
func getTopUsers(posts []Post) []UserLevelPoints {

	postsByLevel := map[string]Post{}
	userLevelPoints := make([]UserLevelPoints, 0)

	for _, post := range posts {

		// Set post for group when group does not already exist
		if _, ok := postsByLevel[post.Level]; !ok {
			postsByLevel[post.Level] = post
			continue
		}

		// Replace post for group if points are higher for current post
		if postsByLevel[post.Level].User.Points < post.User.Points {
			postsByLevel[post.Level] = post
		}
	}

	// Summarize user from post
	for _, post := range postsByLevel {
		userLevelPoints = append(userLevelPoints, UserLevelPoints{
			FirstName:   post.User.Name.First,
			LastName:    post.User.Name.Last,
			Level:       post.Level,
			Points:      post.User.Points,
			FriendCount: len(post.User.Friends),
		})
	}

	return userLevelPoints

}

posts, _ := getPosts("data.json")
topUsers := getTopUsers(posts)

fmt.Printf("%+v\n", topUsers)
// [{FirstName:Ferguson LastName:Bryant Level:gold Points:9294 FriendCount:3} {FirstName:Ava LastName:Becker Level:silver Points:9797 FriendCount:2} {FirstName:Hahn LastName:Olsen Level:bronze Points:9534 FriendCount:2}]
```

[Full source for example](https://github.com/achannarasappa/pneumatic/blob/main/examples/imperative-transformation/main.go2)

#### Functional

```
// functional
var getTopUser = Compose3[[]Post, []Post, Post, UserLevelPoints](
	// Sort users by points
	SortBy(func (prevPost Post, nextPost Post) bool {
		return prevPost.User.Points > nextPost.User.Points
	}),
	// Get top user by points
	Head[Post],
	// Summarize user from post
	func(post Post) UserLevelPoints {
		return UserLevelPoints{
			FirstName:   post.User.Name.First,
			LastName:    post.User.Name.Last,
			Level:       post.Level,
			Points:      post.User.Points,
			FriendCount: len(post.User.Friends),
		}
	},
)

var getTopUsers = Compose3[[]Post, map[string][]Post, [][]Post, []UserLevelPoints](
	// Group posts by level
	GroupBy(func (v Post) string { return v.Level }),
	// Covert map to values only
	Values[[]Post, string],
	// Iterate over each nested group of posts
	Map(getTopUser),
)

posts, _ := getPosts("data.json")
topUsers := getTopUsers(posts)

fmt.Printf("%+v\n", topUsers)
// [{FirstName:Ferguson LastName:Bryant Level:gold Points:9294 FriendCount:3} {FirstName:Ava LastName:Becker Level:silver Points:9797 FriendCount:2} {FirstName:Hahn LastName:Olsen Level:bronze Points:9534 FriendCount:2}]
```

[Full source for example](https://github.com/achannarasappa/pneumatic/blob/main/examples/functional-pipeline/main.go2)

Some features to call outs in the above examples:

1.  The imperative implementation is valid Go 1.16 (latest version at time of writing) syntax while the functional implementation is only valid when compiled with Go 1.18 (go2go)
2.  Generic functions with type parameters in the functional example (e.g. `Compose3`, `Head`, etc) are only supported with Go 1.18
3.  Both implementations use differing logic to solve the same problem that best suit each respective style
4.  The imperative implementation is likely computationally more efficient than a functional one that uses eager evaluation (i.e. [pneumatic](https://github.com/achannarasappa/pneumatic) in this example)

### Experimenting with a Go 1.18 functional library

In the above examples, the two use cases use the go2go compiler and a Go 1.18 library called [pneumatic](https://github.com/achannarasappa/pneumatic) which provides common functional primitives similar to those found in [Ramda](https://ramdajs.com/) (JavaScript), [Elixir’s standard library](https://hexdocs.pm/elixir/api-reference.html#content), and others. Given the go2go compiler’s limited feature set, pneumatic should only be used for experimental purposes as of the writing of this article but the long term vision is evolve it into general purpose functional Go library as the Go 1.18 compiler matures. Have a look at the [pneumatic readme](https://github.com/achannarasappa/pneumatic/blob/main/README.md) for instructions on how to set it up and start playing with functional programming in Go 1.18.

## Conclusion

The addition of generics to Go will open up new sorts of solutions, approaches, and paradigms with better functional programming support being one of them. With the growing popularity of functional programming, better functional programming support and the resulting possibilities have the potential to bring in developers that may have not otherwise considered learning Go and expand the community - a net positive in my view. It will be exciting to see how the Go community and ecosystem evolves over time with the addition of generics and the new solutions it enables.

## References

*   Go functional library survey
    *   [go-funk](https://github.com/thoas/go-funk) \[2.5k stars, type-safe or generic, active\]
    *   [go-underscore](https://github.com/tobyhede/go-underscore) \[1.2k stars, generic, abandoned\]
    *   [gubrak](https://github.com/novalagung/gubrak) \[336 stars, generic, active\]
    *   [fpGo](https://github.com/TeaEntityLab/fpGo) \[167 stars, generic, active\]
    *   [functional-go](https://github.com/logic-building/functional-go) \[92 stars, type-safe, active\]
*   Articles
    *   [The past, present, and future of Go generics](https://blog.logrocket.com/past-present-future-go-generics/)
