# 用 golang 实现 Serverless 服务

* 原文地址：https://ewanvalentine.io/how-im-writing-serverless-services-in-golang-these-days/
* 原文作者：`EwanValentine`
* 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w26_How_I'm_writing_Serverless_Services_in_Golang_these_days.md
- 译者：[Jancd](https://github.com/Jancd)，译者注：本文最好结合附录的代码仓库阅读理解

## 介绍

我已经用 go 编程将近 5 年了，同时我用 Lambda 函数到也有这么长时间了。本文将介绍我在过去几年中学到的知识，用 go 编写 serverless 微服务。

我主要使用的技术栈是 AWS 的，因此本文的某些内容将特定于 AWS，但是大多数概念在其他云提供商上是通用的。

## 项目结构

对于构建较为复杂项目，我倾向于遵循 go 项目结构的建议和 Bobs 提出的整洁架构。

这里没必要给出一个完整的示例（一个类似 CRUD 的应用程序），但希望你可以从这个小示例中借鉴经验，运用到更大的项目中。

整洁架构目的是使架构模块化和可插拔，使用精心设计的接口，这可能是 go 除了并发之外最强大的特性。

首先，看一下总体布局。

/internal
`/internal`目录，主要编写不想对外暴露的代码，或者向代码库的其他用户说明，这个文件夹的内容就是顾名思义的意思 - `internal`。

例如，我在这里编写连接到外部服务或数据库的代码。

/pkg
`pkg`目录用来存放可以在整个项目中重复使用的通用代码，同时它也可以在其他项目中安全地使用。不过，如果你正在为服务编写代码，而不是库，那应该考虑不放在这儿。

## 按照业务区分代码

通常，至少在有多个关注点的服务中，我会尝试按业务区分代码。假设我有一个有发布和评论的服务，我将把所有特定于这些业务的代码放在一个子包中。将 pkg 和 internal 留给共享功能，而不是特定于特定的业务。

在构建 serverless 应用程序时，并没有硬性或快速的规则，上面概述的方法往往适用于更大的服务。但是在这个示例中，对于一个具有两个函数的服务来说，你可能会发现这有点过分了。如果认为所有需要的东西都在项目根目录中，那么完全可以这样做。许多项目都以单一的 main.go 文件开始，并根据需求慢慢增长。我的示例演示了你可能希望如何构建一个更大、更正式的项目。

## 结构

在组织我的 Serverless 项目时，我试图遵循 Bob 那本臭名昭著的《干净的架构》一书中列出的方法。当然，这不是必须的，但它确实概括了一些好的核心原则，我发现这些原则可以使我的代码更容易测试，更容易本地运行，更有弹性地进行更改。

关键是要把诸如“http”、“lambda”、你的缓存、你的数据库等元素当作次要的细节，从你的业务逻辑中屏蔽掉。你的代码被分解成一组定义良好的概念：

## 实例

业务示例在 go 中会被定义为结构体，它表达业务问题具象。例如，comment 类型可能有一个用户 id、一个时间戳和一个文本字段。然后，该实体用于表示存储在数据存储中的数据，往返于此实例结构中的数据存储查询。

用户示例：

```go
// User -
type User struct {
	ID    string `json:"id"`
	Email string `json:"email" validate:"email,required"`
	Name  string `json:"name" validate:"required,gte=1,lte=50"`
	Age   uint32 `json:"age" validate:"required,gte=0,lte=130"`
}
```

## 存储层

在许多框架和语言中，存储层是一个相当熟悉的概念。存储层是一组连接特定数据存储技术的通用方法。这意味着切换数据存储，就是编写一个满足相同方法的新存储层。通过使用接口，可以轻松切换数据存储/数据库技术。

创建用户存储层示例：

```go
// Create a user
func (r *DynamoDBRepository) Create(ctx context.Context, user *User) error {
	item, err := dynamodbattribute.MarshalMap(user)
	if err != nil {
		return err
	}

	input := &dynamodb.PutItemInput{
		Item:      item,
		TableName: aws.String(r.tableName),
	}
	_, err = r.session.PutItemWithContext(ctx, input)
	return err
}
```

## 服务

服务是围绕外部服务或生态系统中的其他服务调用的代码抽象。或者它们可以代表一个内部概念，将几个块组合在一起。在我的示例中，我使用一个服务来封装一个业务，然后可以将其安排到已经设置好的所有所需配置的交付中。

### 用例

用例代表核心业务逻辑，它应该调用服务和存储层，处理实体并返回通用数据类型。换句话说，你的业务逻辑不应该知道底层数据库技术，因为你正在使用存储层。你的业务逻辑不应该知道传输类型，同时你的用例可以通过 web 服务器、命令行接口、lambda 函数等调用。因为你只是从用例返回泛型数据类型，所以可以使用任何东西调用它。这给了你很大的灵活性，为了调用用例，你需要一个交付。

在我们的示例中，我们有一个通用的用户实例，我们对它进行一些验证，并将其传递到存储层进行保存。在更复杂的示例中，你可能需要调用许多存储层和服务。

创建用户用例示范：

```go
// Create a single user
func (u *Usecase) Create(ctx context.Context, user *User) error {
	validate = validator.New()
	if err := validate.Struct(*user); err != nil {
		validationErrors := err.(validator.ValidationErrors)
		return validationErrors
	}

	user.ID = u.newID()
	if err := u.Repository.Create(ctx, user); err != nil {
		return errors.Wrap(err, "error creating new user")
	}

	return nil
}
```

## 交付

交付在某种意义上是一种接口协议或用户界面的类型。比如命令行界面，http 请求等等。传递只是从请求体、参数或其他内容中获取数据，将它们转换为通用数据类型，并将其传递给正确的用例。然后返回一些数据，将其编组为 json 响应，等等。

所有这些部分加起来，意味着在数据存储或调用业务逻辑的方法之间切换非常简单。其目的始终是保护业务逻辑不受外部技术和底层技术等次要细节的影响。

创建用户 Lambda:

```go
// Create a user
func (h *handler) Create(ctx context.Context, body []byte) (helpers.Response, error) {
	user := &users.User{}
	if err := json.Unmarshal(body, &user); err != nil {
		return helpers.Fail(err, http.StatusInternalServerError)
	}

	if err := h.usecase.Create(ctx, user); err != nil {
		return helpers.Fail(err, http.StatusInternalServerError)
	}

	return helpers.Success(user, http.StatusCreated)
}
```

## 测试

上面概述的架构使测试变得非常容易。我倾向于为每个用例编写测试。我使用 go 的简单依赖注入方法，使用接口将数据存储切换到模拟版本。

因为用例采用通用数据类型，所以我们不需要在测试中模拟调用 lambda 函数，这使我们的测试保持干净，并且只关注业务逻辑。

在工具和库方面，我尽量保持它主要使用标准库。然而，我发现有一些库和工具可以节省时间，特别是对于断言和生成虚拟实现这样的重复模式，如下：

https://github.com/stretchr/testify
https://github.com/golang/mock

很多人不赞成使用工具进行测试，并使用外部库等，但我认为值得是务实的，最后我发现我手工做的工作去模拟，证明当我试着使用标准库实现 100% 的测试覆盖所花的时间和精力是不值得的。我建议仔细评估和使用那些真正节省时间和高质量的工具。

### 集成测试

有时我喜欢编写一些能够在 CI 环境中运行的轻量级集成测试，这些测试与业务逻辑无关，而更多地关注的是如何获得正确的访问和连接等问题。在我的示例中，我编写了一些集成测试作为 Lambda 交付的一部分。在我的 Cloudformation 脚本中，我还包含了一个集成 DynamoDB 表。

集成测试实例：

```go
func TestCanCreate(t *testing.T) {
	ctx := context.Background()
	user := &users.User{}
	clear()
	h := setup()
	req := helpers.Request{
		HTTPMethod: "POST",
		Body:       validUser,
	}
	res, err := helpers.Router(h)(ctx, req)
	assert.NoError(t, err)

	err = json.Unmarshal([]byte(res.Body), &user)
	assert.NoError(t, err)
	assert.Equal(t, http.StatusCreated, res.StatusCode)
	assert.NotNil(t, user.ID)
	id = user.ID
}
```

## 路由

如下我正在编写 RESTful 端点，利用机器上的 HTTP verbs，你可以将资源合并到单个端点中，使用 HTTP verbs 路由到正确的用例。如下所示：

示例：

```go
func Router(handler handler) func(context.Context, Request) (Response, error) {
	return func(ctx context.Context, req Request) (Response, error) {

		// Add cancellation deadline to context
		ctx, cancel := context.WithTimeout(ctx, fiveSecondsTimeout)
		defer cancel()

		switch req.HTTPMethod {
		case "GET":
			id, ok := req.PathParameters["id"]
			if !ok {
				return handler.GetAll(ctx)
			}
			return handler.Get(ctx, id)

		case "POST":
			return handler.Create(ctx, []byte(req.Body))

		case "PUT":
			id, ok := req.PathParameters["id"]
			if !ok {
				return Response{}, errors.New("id parameter missing")
			}
			return handler.Update(ctx, id, []byte(req.Body))

		case "DELETE":
			id, ok := req.PathParameters["id"]
			if !ok {
				return Response{}, errors.New("id parameter missing")
			}
			return handler.Delete(ctx, id)

		default:
			return Response{}, errors.New("invalid method")
		}
	}
}
```

如你所见，我使用 HTTP verbs 来路由到资源的正确处理程序，对于使用相同谓词的多个端点的路由，我使用 path 参数或不使用 path 参数来进一步区分。这完美地涵盖了基本的 CRUD 操作。

## 日志

对于日志记录，我发现使用结构化日志记录至关重要，而不仅仅是将字符串记录到标准输出。结构化日志只是一个术语，用于以可预测的方式进行日志记录。比如 JSON。这意味着你可以更容易地在日志上存储和执行分析。例如，将它们存储到 Kibana，对某些字段的索引。例如，在 AWS 中，你可以只使用 Cloudwatch Insights，它将收集 JSON 字段，并允许你使用类似 SQL 的语法执行丰富的搜索查询。拥有某种形式的结构化日志，可以为你的服务行为提供大量可见性和深入挖掘的机会。它使调试与良好的工具结合起来变得轻而易举。

对于 go 应用程序，我倾向于使用 Logrus，但最近我一直在使用 Uber 推出的一个很棒的库 Zap。

## 追踪

市面上有很多很棒的跟踪工具，特别是 go，如:Jaeger， Zipkin 等。然而，当我们在这些例子中使用 AWS 时，我们将看一下 AWS X-Ray。X-Ray 直接集成到大多数主要的 AWS 服务，基本服务，如 API Gateway、Lambda、SQS 等。这意味着它非常适合 serverless 的用例。

serverless 框架本身使得这个过程非常容易，你只需在 serverless.yml 文件中添加 tracing 配置：

```yaml
provider:
  tracing:
    apiGateway: true
    lambda: true
```

它支持对 API 网关和 Lambdas 函数的跟踪，同时你可以使用 X-Ray SDK 向其他服务添加进一步的跟踪，使用它们的工具。

要添加跟踪其他 AWS 服务的检测，只需将该服务的客户端包装在 X-Ray 检测中。

```go
xray.Configure(xray.Config{LogLevel: "trace"})
xray.AWS(ddb.Client)
```

然后，在与支持的 AWS 服务交互时，确保使用“with context”，例如：

```go
result, err := r.session.GetItemWithContext(ctx, input)
```

上下文是传递到 Lambda 处理程序中的，它将自动端到端连接，并且你将能够在 X-Ray UI 中查看你的追踪记录。

![](https://ewanvalentine.io/content/images/2019/09/Screenshot-2019-09-03-at-13.28.06.png)

## 本地运行

在其他语言中，比如 nodejs，有一些插件可以模拟 serverless 网关 (serverless 离线) 的行为，但由于 go 的编译特性，这变得很棘手，据我所知，目前还不存在这样的替代方案。如果有……请告诉我！

但是，因为我们已经将服务的架构设计为将运行时与业务逻辑解耦，所以我们可以很容易地编写新的交付类型，我们可以使用它在本地启动。

我们不用 lambda 入口点来编译我们的服务，而是使用一个基本的 web 服务器，在 cmd 目录中。这暴露了我们所有的 http 交付。总之，只需花费很少的努力，我们就可以创建与数据和业务逻辑交互的新方法。

## 基础设施

像大多数使用 AWS 的人一样，我倾向于只使用 Cloudformation，尽管有时很容易觉得自己是 YAML 开发人员，但它是你的工具库中一个强大而冗长的工具。但也有很好的替代方案可供选择，比如 terraform。

然而，有了 Serverless， 特别是当你可以在你的 serverless 配置中包含 Cloudformation 时，cloudformation 通常感觉更适合。

然而，也有例外。 例如，我曾经将 DynamoDB 配置放在我的 serverless 配置中。直到有一天我删除并重新创建了一个 serverless 堆栈，并被警告我将删除 DynamoDB 表中的所有数据。当然！在那次惊吓之后，我现在确保在单独的 cloudformation 堆栈文件中定义我的 DynamoDB，或任何处理如果删除表可能会丢失的数据的内容。你失去了使用 serverless `up`命令生成所有表的容易性，但是你会获得一些额外的安全和保证。

然而，其他通常无状态的服务可以安全地在 serverless.yml 中定义。

## Databases 

就所选择的数据库类型而言，serverless 具有巨大的影响。关于 serverless 体系结构需要注意的关键是它的并发能力和无状态性。当然，这两个好处都有。但是，这可能会成为传统数据库的负担，因为传统数据库往往使用某种形式的连接池来管理数据库的负载。连接池本身就是有状态的。所以这在长期运行的进程上工作得很好，比如 web 服务器。但是，Lambda 函数是无状态的，没有连接池的概念，每次都必须创建一个新的连接。这意味着你可能很快就会遇到数据库的连接限制。

在我早期对 serverless 架构的尝试中，我使用了一个托管的 MongoDB 服务器，它是一个托管实例，所以我认为我不必太担心伸缩性等问题。然而，我们不断耗尽 RAM，我们将实例扩展了几次，但这只是一个临时的修复，我们也无法处理相对较少的数据。我们不断达到连接限制，并耗尽 RAM。事实证明，高并发性和缺乏连接池意味着数以千计的连接被生成，没有被正确地再次关闭，连接正在泄漏。在检查并修补了所有显式处理关闭连接的代码后，我们仍然在流量激增时看到问题。

有一些方法可以减轻这种情况，例如，在云函数和数据库之间创建一个长期运行的进程，它处理连接池并返回结果。还可以向这一层添加缓存，以减少数据库的负载。这一层可以变得非常薄和轻量级，但它无疑增加了复杂性。

第二种解决方案是使用 serverless 数据库，例如 DynamoDB 或云数据存储。然而，这些也有局限性。它们是新的，有不同的 api。如果你有 SQL 背景，你会采用一种全新的 NoSQL 数据库查询语法。对于这个问题，有其他的替代方案，例如 Aurora，它是一个 serverless 的 SQL 包装器。它允许你使用 MySQL 或 PostgresSQL 风格的数据库实例，公开一个 serverless 友好的查询连接。但这只提供了每个版本的限制版本，所以你也需要考虑这一点。

## Deployments

通常我有每个服务的部署 pipeline，这是由 GitHub 的 webhook 事件触发，如合并到 master。

我倾向于使用 AWS Code Pipeline 和 Code Build，它已经集成到 AWS 堆栈中，并且附带了部署 Lambdas 所需的一切。它也是非常轻量级的配置。我为 pipeline 运送云的形成随我的服务。另一个不错的选择是 CircleCI，它提供免费试用。

## 服务发现

当你构建越来越多的服务时，你会发现可能需要在服务之间进行通信的用例。你可以在 Fargate 和 Lambda 等地获得一些服务。我在 serverless 技术和 AWS 服务上遇到的一个问题是，在所有这些不同的服务和协议之间进行通信很棘手，而且在不使用 arn 的情况下查找每个服务的位置也很棘手。因此，在典型的微服务体系结构中，这就是需要使用服务发现的地方。

服务发现允许你用用户友好的名称注册服务的位置，这样你就可以通过名称找到其他服务。AWS 为此提供了一个名为 Cloudmap 的 serverless 产品。我使用 Cloudmap 注册我的函数的 arn。我还编写了一系列库来抽象调用其他函数和定位其他服务的过程。

使用我们的服务发现框架调用 Lambda 函数的示例：

```go
d := discover.NewDiscovery(
  discover.SetFunction(function.NewLambdaAdapter(client),
)

d.Request("my-namespace.users->create-user", types.Request{
  Body: []byte("{ \"hello\": \"world\" }"),
}, opts)
```

在底层，它找到名称空间为 my-namespace 的服务，即用户服务，并从 Cloudmap 调用创建用户函数作为该服务的一部分。Cloudmap 返回带有一些附加元数据的 ARN，包括它的类型，在本例中是一个函数。因为我们使用 Lambda 函数适配器（这也是默认的）实例化了这个库，所以它随后使用 Lambda SDK 调用该 Lambda 函数。

从代码的角度来看，它并不关心它在哪里，或者它是什么，它可以直观地推断出如何处理交互，保护代码不受 Lambda 细节的影响。

## 总结

我每天都在学习，而且很有可能，我的方法在接下来的一年左右会改变好几次。我列出的方法和工具并不是完美的，但它是一个很好的开始。

很重要的一点是，我希望你能记住：保护好你的业务逻辑免受 AWS 服务和技术的冲击。将 Lambda 视为不重要的细节，将 DynamoDB 视为不重要的细节，而重要的部分是你的用例。它应该封装你的业务逻辑，同时你的数据库、交付机制等等是不透明的。

我注意到一件事，比如用 Docker 和 Kubernetes 来构建分布式系统要容易得多，有一些设计模式和基本元素被清晰地定义和理解。我仍然认为“serverless”这个概念是缺失的或不完整的，主要是由过多的服务和云平台产品之间的差异所驱动。有了 Kubernetes， docker 只是 docker，你可以采取统一的方式。

但是我们可以通过使用谨慎的抽象，以及理解我们在传统体系结构中看到的相同模式如何应用于 serverless 体系结构来实现相同的目标。

示例仓库: https://github.com/EwanValentine/serverless-api-example
