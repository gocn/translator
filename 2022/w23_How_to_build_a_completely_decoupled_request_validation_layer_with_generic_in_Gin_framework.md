- 原文地址：https://albertgao.xyz/2022/07/22/how-to-have-a-completely-decoupled-request-validation-layer-in-gin-framework/
- 原文作者：albertgao
- 本文永久链接：https://github.com/gocn/translator/blob/master/2022/w23_How_to_build_a_completely_decoupled_request_validation_layer_with_generic_in_Gin_framework.md
- 译者：[Jancd](https://github.com/Jancd)
- 校对：[pseudoyu](https://github.com/pseudoyu)

# 如何在 Gin 框架中使用泛型构建完全解耦的请求验证层

请求验证可能是任何 Web 框架中最无聊但最关键的中间层。今天，我将展示在 golang 中的 [gin 框架](https://github.com/gin-gonic/gin) 中（使用泛型）的正确实践。

## 1. 目标

[Gin](https://github.com/gin-gonic/gin) 与 [validator](https://github.com/go-playground/validator) 库集成以进行请求验证，即 [模型绑定与验证](https://github.com/gin-gonic/gin#model-binding-and-validation)。我们将在很大程度上依靠这一点来实现我们的目标。

我们的目标是：

>构建一个抽象，通过这个抽象使得请求验证与请求处理程序完全解耦，例如，在您的常规 gin 的 handler 函数中，你只需从路径参数/query 字符串 / json body 中获取值并开始使用它们。

## 2. 如何实现

让我们从一个简单的 json body 开始

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

对于上面的示例，请求 body 中任何有问题的请求都会导致错误响应。这种简单的情况很好处理，但如果你有几十个类似的端点要处理，那就是一个很重复冗余的工作了。这种 `validate-and-400-if-invalid 模式将一遍又一遍地重复`。还有更好的处理办法么？

## 3. 什么是更好的抽象

对于不同的用例，上述逻辑是相同的，唯一会改变的是 http body 的类型。那么，我们可以使用一个泛型中间件来处理这个逻辑，那样我们就可以只关心 handler 函数中的值。如下：

假设我们想使用上述 `CreateUserHttpBody` 结构体验证 json body。

我们可以在注册 handler 函数时对其进行验证。

```go
router.POST("/user",
    ValidateJsonBody[CreateUserHttpBody](),
    rs.CreateUser,
)
```

>请注意，我们只对这个 `/user POST` 端点应用验证，gin 支持路由级中间件。

然后在你的函数中，你可以像这样使用它：

```go
func CreateUser(c *gin.Context) {
    httpBody := GetJsonBody[CreateUserHttpBody]()

    // the below statement will print the birthday and timezone when receives valid request
    fmt.Println(httpBody.Birthday, httpBody.Timezone)
}
```

看上面的代码，有趣的是，当运行到 `fmt.Println(httpBody.Birthday, httpBody.Timezone)` 这行时，意味着请求是有效的，并且 `httpBody.Birthday` 和 `httpBody.Timezone` 必须是合法且可供使用的。

如果请求无效，它将被 `ValidateJsonBody[CreateUserHttpBody]()` 拦截并返回，客户端将收到 http code 400 响应。

它几乎就像“声明式验证”，我们只需在 `CreateUserHttpBody` 结构中描述需要的验证要求，而不再需要更多别的操作！

## 4. 简单的 3 个步骤的回顾：

- 我们在 `CreateUserHttpBody` 结构体中声明请求验证
- 我们在 `router.POST` 中增加了一个 `ValidateJsonBody[CreateUserHttpBody]()` 中间件，在实际处理业务函数之前进行验证。
- 在 handler 函数中，我们只是从 `httpBody := GetJsonBody[CreateUserHttpBody]()` 中获取通过验证的请求body

## 5. 如何实现

我们先创建 `ValidateJsonBody` 方法，怎么实现？还记得我们在第 2 节中说过，这种 ``validate-and-400-if-invalid 模式将一遍又一遍地重复``。唯一不变的是类型，这就把我们引向了泛型的概念。

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

我们创建了 `ValidateJsonBody` 方法，它接收 `BodyType`，它可以是你传递给它的任意类型。在正文中，我们只是编写了一个普通的 gin 中间件，我们声明了变量，并进行了验证，如果请求无效，我们返回 400。否则，我们将解析后的值设置为 gin 上下文，key 为 `jsonBody`。

>在我们的示例中，`ValidateJsonBody[CreateUserHttpBody]()`，`CreateUserHttpBody` 是将被接收的泛型类型。

现在我们来实现 `GetJsonBody` 方法，这是最简单的部分。

```go
func GetJsonBody[BodyType any](c *gin.Context) BodyType {
	return c.MustGet("jsonBody").(BodyType)
}
```

我们使用 gin 中的 `c.MustGet` 从 gin context 中检索值，并将其类型转换为泛型类型。如果没有值，这个 `MustGet` 将发生 `panic`，但在我们的例子中，它不会发生，因为我们已经在 `ValidateJsonBody` 中间件中设置了它。

>在我们的示例中，`httpBody := GetJsonBody[CreateUserHttpBody]()`，`CreateUserHttpBody` 是将被接收的泛型类型。

## 6. 还能再优化么？

如上所述，我们实现了一个完全解耦的请求验证层。但我们可以做得更好吗？是的！我们还能做什么呢？

- 我们可以实现 `ValidateRequestParam()` 和 `ValidateQueryString()`，但是有了上面的知识，这容易实现的，读者可以自行思考。
- 我们将实际业务逻辑（使用经过验证的请求信息的部分）与 handler 函数解耦。但我会把它写在另一个博客文章中。

## 7. 结语

希望这个文章对你有所启发，感谢阅读:)
