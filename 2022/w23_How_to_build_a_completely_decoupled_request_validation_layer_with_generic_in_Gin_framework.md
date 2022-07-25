- 原文地址：https://albertgao.xyz/2022/07/22/how-to-have-a-completely-decoupled-request-validation-layer-in-gin-framework/
- 原文作者：albertgao
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w23_How_to_build_a_completely_decoupled_request_validation_layer_with_generic_in_Gin_framework.md
- 译者：[Jancd](https://github.com/Jancd)
- 校对：[]()

# How to build a completely decoupled request validation layer with generic in Gin framework

Request validation is the probably the most boring but critical layer of any web framework. Today I will show you how to do it right in [gin framework](https://github.com/gin-gonic/gin) in golang.

## 1. Goal
[Gin](https://github.com/gin-gonic/gin) integrates with [validator](https://github.com/go-playground/validator) to do the request validation. The terms is [Model binding and validation](https://github.com/gin-gonic/gin#model-binding-and-validation). We will rely on this heavily to achieve our goal.

Our goal here is:

>To build an abstraction, so the request validation is completely decoupled from the request handler, for example, in your normal gin handler function, you can just get the value from path parameters / query string / json body and start using them as granted.

## 2. How we do it now

Let’s start with a simple json body

```go
type CreateUserHttpBody struct {
    Birthday string `json:"birthday" binding:"required,datetime=01/02"`
	Timezone string `json:"timezone" binding:"omitempty,timezone"`
}

func CreateUser(c *gin.Context) {
    var httpBody HttpBody

    if err := c.ShouldBindJSON(&httpBody); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    // from here we can use the httpBody as it must has the correct
}
```

For the above example, anything incorrect from the request body leads to a bad request response. It’s fine for this simple case, but not fine if you have dozens of endpoints to build. This `validate-and-400-if-invalid pattern will be repeated over and over`. Can we make it better?

## 3. What is a better abstraction

The above logic would be the same for different use cases, the only thing that would change is the type of the http body. so, can we have a generic middleware to handle this, so we can just enjoy the value in the handler function? Something like this:

Let’s say you want to validate the json body with the above CreateUserHttpBody struct.

You can validate it when registering the handler function.

```go
router.POST("/user",
    ValidateJsonBody[CreateUserHttpBody](),
    rs.CreateUser,
)
```

Notice we only apply the validation for this very /user POST endpoint, gin supports route level middleware.

Then in your function, you can just get it like this:

```go
func CreateUser(c *gin.Context) {
    httpBody := GetJsonBody[CreateUserHttpBody]()

    // the below statement will print the birthday and timezone when receives valid request
    fmt.Println(httpBody.Birthday, httpBody.Timezone)
}
```

Look the above code, the interesting part is, when you hit the line `fmt.Println(httpBody.Birthday, httpBody.Timezone)`, that means the request is valid, and the `httpBody.Birthday` and `httpBody.Timezone` MUST be both valid and available to use.

If the request is invalid, it would be blocked by the `ValidateJsonBody[CreateUserHttpBody]()` and the client will receive a 400 response.

It almost like `declarative validation`. where you just describe your validation requirement in the `CreateUserHttpBody` struct, and anything else just happens!

## 4. A review for the simple 3 steps:

- We declare the request validation in the struct `CreateUserHttpBody`
- We put a `ValidateJsonBody[CreateUserHttpBody]()` middleware in `router.POST` before the actual handler function to do the validation.
- In the handler function, we just get the validated request body from `httpBody := GetJsonBody[CreateUserHttpBody]()`

## 5. How we do this

Let’s first create the ValidateJsonBody function, how? Remember we said in section 2 that This validate-and-400-if-invalid pattern will be repeated over and over.? The only thing that is not change is the type, and that leads us to the concept of generic.

```go
func ValidateJsonBody[BodyType any]() {
    return func(c *gin.Context) {
        var body BodyType

        err := c.ShouldBindJSON(&body)
        if err != nil {
            c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
            return
        }

        c.Set("jsonBody", value)

        c.Next()
    }
}
```

We created the function `ValidateJsonBody`, it receive the `BodyType` which can be an arbitrary type you pass to it. In the body, we just write a normal gin middleware, we declare the variable, and do the validation, if invalid request, we return 400. Otherwise, we set the parsed value to the gin context with the key `jsonBody`.

>In our example, `ValidateJsonBody[CreateUserHttpBody]()`, `CreateUserHttpBody` is the generic type that will be received.

Now let’s implement the GetJsonBody function, this is the easy part.

```go
func GetJsonBody[BodyType any](c *gin.Context) BodyType {
	return c.MustGet("jsonBody").(BodyType)
}
```

We use the `c.MustGet` from gin, to retrieve the value from gin context, and cast its type to the generic type. This `MustGet` will `panic` if no value, but in our case, it won’t happen, since we already set it in the ValidateJsonBody middleware.

>In our example, `httpBody := GetJsonBody[CreateUserHttpBody]()`, `CreateUserHttpBody` is the generic type that will be received.

## 6. Can we do better

As above, we did it, a completely decoupled request validation layer. But can we do better? Yes! What can we do?

- To implement the `ValidateRequestParam()` and `ValidateQueryString()`, but this is too easy with the knowledge above, I will leave it to you. :)
- We decouple the actual business logic (the part that is consuming the validated request information) from the handler function. But I will leave it to another blog. :)

## 7. End

Hope it helps :)

Enjoy :)

Thanks for reading!