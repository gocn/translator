# 用 golang 实现 Serverless 服务

* 原文地址：https://ewanvalentine.io/how-im-writing-serverless-services-in-golang-these-days/
* 原文作者：`EwanValentine`
* 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w26_How_I'm_writing_Serverless_Services_in_Golang_these_days.md
- 译者：[Jancd](https://github.com/Jancd)


## Introduction

I’ve been programming with Go for almost 5 years now, and it’s been almost as long since I first created a Lambda function. This article will cover what I’ve learnt over the past few years, writing serverless Go microservices.

The stack I use mostly is AWS, therefore some elements of this article will be AWS specific, however most of the concepts should translate into other cloud providers.

## Project Structure

The way I structure more complex projects, tend to follow the suggested Go project structure, and Uncle Bobs clean architecture.

This may seem overkill for the size of the example I've given (a single CRUD like application), but hopefully you can mentally extrapolate from this to a larger example, where you can hopefully see the value.

The aim is to make the architeture modular and pluggable, using carefully designed interfaces, possibly Go's strongest feature besides concurrency.

First up, a look at the general layout.

/internal
My internal directory, I use for code I don’t want to expose to the outside world, or at least signal to other users of this codebase, that the contents of this folder are, well… as the name suggests, internal.

I use this for code used to connect to external services or databases for example.

/pkg
I use the pkg directory to house code which can be reused across the project, and can be safely used in other projects if needed. Although, if you’re writing code for services, as opposed to libraries, external use is less of a concern.

## Splitting code by domain

I generally, at least in services which have multiple concerns, try to split code by domain. So if I have a service which has posts and comments, I will keep all the code specific to those domains together in a sub-package. Leaving pkg and internal for shared functionality, which isn’t specific to a particular domain.

There’s no hard or fast rule when it comes to structuring your serverless application, the approaches of outlined above tend to work for me for bigger services. But for a service with a couple of functions for example, you might find this overkill. Remember, it's perfectly okay to just have everything in your project root if you think that's all that's needed. Many projects start off in a single main.go file and grow as needed. My example demonstrates how you might want to structure a bigger, more formalised project.

## Architecture

When structuring my Serverless projects, I try to follow the approaches outlined in Uncle Bob’s infamous ‘Clean Architecture’ book. Again, this isn’t a must, but it does outline some good core principles which I’ve found to make my code easier to test, easier to run locally, and more resilient to change.

The key thing is to treat concepts such as ‘http’, ‘lambda’, your cache, your database etc, all as minor details, shielded away from your business logic. Your code is split up into a set of well defined concepts:

## Entities

An entity is a type, in the case of Go a struct, which communicates the shape of the business problem. So for example a comment type, which may have a user id, a timestamp, and a text field. This entity is then used to represent the data stored within the datastore, but marshalling datastore queries to and from this entity struct.

Entity example:

```go
// User -
type User struct {
	ID    string `json:"id"`
	Email string `json:"email" validate:"email,required"`
	Name  string `json:"name" validate:"required,gte=1,lte=50"`
	Age   uint32 `json:"age" validate:"required,gte=0,lte=130"`
}
```

## Repositories

A repository is a fairly familiar concept in many frameworks and languages. A repository is a common set of methods interfacing a certain datastore technology. This means that switching datastores, is a case of writing a new repository which satisfies those same methods. Using interfaces, this makes it easy to switch around datastores/database technologies.

Create user repository example:

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

## Services

Services are code abstractions around calls to external services, or other services within your ecosystem. Or they can represent an internal concept which groups a few blocks together. In my example, I use a service to encapsulate a domain, which can then be plugged into our deliveries with all of its required configuration already set-up.

### Use cases

Use cases represent your core business logic, it should call services and repositories, deal with entities and return generic data types. In other words, your business logic should not be aware of the underlying database technology, because you’re using a repository. Your business logic shouldn’t be aware of the transport type, your use case could be called via a web server, a command line interface, a lambda function, etc. Because you just return the generic data type from your use case, you can call this using anything. This gives you a lot of flexibility, in order to call your use case, you need a delivery.

In our example, we have a generic user entity, we do some validation on it, and pass it to the repository to be saved. In more complex examples, you might need to call a number of repositories and services here.

Create user use case example:

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

## Deliveries

A delivery is a type which interfaces a protocol or user interface in some sense. So a command line interface, http request etc. The delivery just takes the data from the request body, arguments, or whatever, converts them into a generic data type, and passes it to the correct use case. Which will then return some data, to be marshalled into a json response, etc, etc.

The sum of all these parts, means that it’s very simple to switch around your datastore, or the method of calling your business logic. The aim is always to protect business logic from minor details such as external technologies and underlying technologies.

Create user Lambda:

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

## Testing

The architeture outlined above makes things very easy to test. I tend to write tests for each use case. I use Go’s simple approach to dependency injection, using interfaces, to switch the datastore to a mock version.

Because the use case takes generic data types, we don’t need to mock calling a lambda function within our tests, which keeps our tests clean and focussed on just the business logic also.

In terms of tooling and libraries, I try to keep it mostly standard library. However a few libraries and tools I’ve found to be useful timesavers, especially for repetitive patterns such as assertions and generating dummy implementations.

https://github.com/stretchr/testify
https://github.com/golang/mock

A lot of people frown upon using tools for testing, and using external libraries etc, but I think it’s worth being pragmatic, I found I ended up manually doing the job of go mock and testify when I tried being 100% standard library, and that wasn’t worth the time or the effort. I recommend carefully assessing and using tools that genuinely save you time and are of a high quality.

### Integration Testing

I sometimes like to write some light integration tests which can run in CI environments, which are less about the business logic and more about things having the correct access and connectivity etc. In my example, I’ve written some integration tests as part of my Lambda delivery. In my Cloudformation script, I also include an integration DynamoDB table.

Example integration test:

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

## Routing

If I’m writing RESTful endpoints, utilising HTTP verbs on resources, you can combine a resource into a single endpoint, using the HTTP verb to route to the correct use case. As shown below:

Example:

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

As you can see, I use HTTP verbs to route to the correct handler of a resource, for routes with multiple endpoints using the same verb, I use the presence of a path argument or not to differentiate further. This covers basic CRUD operations perfectly.

## Logging

For logging, I’ve found it’s crucially important to use structured logging, as opposed to just logging our strings to stdout. Structured logging is just a term for logging in a predictable way. In JSON for example. This means you can store and perform analysis more readily on your logs. Storing them to Kibana for example, an indexing on certain fields. In AWS for example, you can just Cloudwatch Insights, which will pick up on JSON fields, and allow you to perform rich search queries, with a SQL like syntax. Having some form of structured logging, opens up a lot of opportunities for visibility and diving deeper into your services behaviours. It makes debugging a breeze combined with good tooling.

For Go applications, I tend to use Logrus, but more recently I’ve been playing around with a great library brought out by Uber, called Zap.

## Tracing

There are lots of great tracing tools out there, especially for Go. Such as: Jaeger, Zipkin etc. However, as we’re using AWS in these examples, we’re going to take a look at AWS X-Ray. X-Ray integrates directly into most of the main AWS Services, the bread and butter services, such as API Gateway, Lambda, SQS, and several more. Which means it’s perfect for serverless use-cases.

The serverless framework itself makes this process incredibly easy, you simply include the following in your serverless.yml file:

```yaml
provider:
  tracing:
    apiGateway: true
    lambda: true
```

Which enables tracing for your API Gateway, and your Lambdas functions. You can use the X-Ray SDK to add further tracing to other services, using their instrumentation tools.

To add the instrumentation to track other AWS services, you simply wrap the client of that service, in the xray instrumentation.

```go
xray.Configure(xray.Config{LogLevel: "trace"})
xray.AWS(ddb.Client)
```

Then, when interacting with supported AWS services, make sure you use 'with context', for example:

```go
result, err := r.session.GetItemWithContext(ctx, input)
```

The context being the one passed into your Lambda handler, it'll be automatically connected end to end, and you'll be able to view your traces in the X-Ray UI.

![](https://ewanvalentine.io/content/images/2019/09/Screenshot-2019-09-03-at-13.28.06.png)

## Running locally

In other languages, such as nodejs, there are plugins to emulate the behaviour of serverless gateway (serverless-offline), but due to the compiled nature of Go, that becomes tricky, and to my knowledge, no such alternative exists for Go at this time. If there is… please do let me know!

But, because we’ve architected our service to decouple the runtime from the business logic, we can easily write a new delivery type, which we can use to spin up locally.

Instead of compiling our service with the lambda entrypoint, we utilise a basic web server, found in the cmd directory. Which exposes all of our http deliveries. In summary, with very little effort, we can create new ways of interacting with our data and our business logic.

## Infrastructure

Like most people using AWS, I tend to just use Cloudformation, although sometimes it’s easy to feel as though you’re a YAML developer, it’s a powerful, yet verbose tool in your arsenal. But there are very good alternatives at your disposal, such as terraform.

However, with Serverless, which generates cloudformation under the hood, Cloudformation generally feels like a better fit. Especially as you can include Cloudformation along with your serverless config.

There are exceptions to this however. For example, I used to put DynamoDB configurations in my Serverless config. Until I went to delete and recreate a serverless stack one day and I was warned I’d be deleting all the data in my DynamoDB table. Of course! After that fright, I now make sure to define my DynamoDB, or anything dealing with data that could be lost if a table was dropped, in separate cloudformation stack files. You lose the easy of being able to generate all of your tables with a serverless up command. But you gain some extra safety and assurance.

Other services which are generally stateless however, can be defined in your serverless.yml safely.

## Databases 

Serverless has huge implications in terms of the type of database you choose. The key thing to note about the serverless architecture is its concurrency capabilities, and statelessness. Which are both benefits, of course. However, this can become a burden on traditional databases, which tend to use some form of connection pooling in order to manage the load to a database. Connection pooling is inherently stateful. So this works fine on a long-running process, such as a webserver. However, your Lambda functions being stateless, have no concept of a connection pool, it has to create a fresh connection each time. Which means you can face very quickly hit connection limits to your database.

In the my early forays into serverless architecture, I was using a hosted MongoDB server, it was a managed instance, so I thought I didn't have to worry too much about scaling etc. However, we kept running out of RAM, we scaled the instance up a few times, but that was only a temporary fix, we were also massively overpowered for the relatively small amount of data we were dealing with. We kept hitting connection limits, and running out of RAM. It turns out, the high concurrency and lack of connection pooling meant connections were being spawned by the thousands and not being properly closed again, connections were leaking. After reviewing and patching all of the code to explicitly handle closing connections, we were still seeing issues during bursts of traffic.

There are ways to mitigate this, for example, creating a long-running process betwixt your cloud functions and your database, which handles connection pooling and returns results. You can also add caching to this layer to lessen the load of your database. This layer can become pretty thin and light-weight, but it's added complexity for sure.

The second solution is to use a serverless database, for example DynamoDB, or Cloud Datastore. However these come with limitations also. They're new, and have different APIs. If you come from a SQL background, you're adopting an entirely new, NoSQL database query syntax. There are alternavtives to this problem emerging, for example Aurora, which is a serverless SQL wrapper. Which lets you use a MySQL, or PostgresSQL flavoured database instance, exposing a serverless friendly query connection. This only offers restricted versions of each though, so you need to consider this as well.

## Deployments

Typically I have a deployment pipeline for each service, which is triggered by GitHub webhook events, such as merging into master.

I tend to use AWS Code Pipeline and Code Build, it’s already integrated into the AWS stack, and ships with everything you need to deploy Lambdas. It’s also pretty lightweight configuration wise. I ship the cloudformation for the pipeline along with my service. Another good option is CircleCI which offers a free trial.

## Service Discovery

As you build out more and more services, you find use cases where you might need to communicate between services. You may have some services in Fargate, some in Lambda, etc. One issue I had architecting on serverless technologies, and AWS services, is that it’s tricky to communicate between all of these different services and protocols, and it’s tricky to find the location of each service without using ARNs. So this is where, in a typical microservice architecture, you’d use service discovery.

Service discovery allows you to register the location of services, with a user friendly name, so that you can find other services by name. AWS provides a Serverless offering for this, called Cloudmap. I use Cloudmap to register the ARNs of my functions. I also wrote a series of libraries to abstract the process of calling other functions, and locating other services.

Example calling a Lambda function using our service discovery framework:

```go
d := discover.NewDiscovery(
  discover.SetFunction(function.NewLambdaAdapter(client),
)

d.Request("my-namespace.users->create-user", types.Request{
  Body: []byte("{ \"hello\": \"world\" }"),
}, opts)
```

Under the hood, this finds the service with the namespace of my-namespace, the users service, and calls the create-user function as part of that service from Cloudmap. Cloudmap returns the ARN with some additional metadata, including its type, in this case a function. Because we instantiated this library using the Lambda adapter for functions (which is also the default), it then uses the Lambda SDK to call that Lambda function.

From your codes point of view, it doesn't care where it is, or what it is, it can intuitively infer how to handle that interaction, protecting your code from the details of Lambda.

## Conclusion

I’m still learning every day, and in all probability, my approach will change several more times in the next year or so. The approaches and tools I’ve outlined aren’t foolproof, but it’s a solid start.

The most important lesson I hope you take away from this, however, is protecting your business logic from the sea of AWS services and technologies. Treat Lambda as an unimportant detail, treat DynamoDB as an unimportant detail. The important parts are your use cases, which should encapsulate your business logic, and should not be aware of your database, or your delivery mechanism, etc.

One thing I've noticed, it feels much easier to architect distributed systems with Docker and Kubernetes for example; there are design patterns and primatives that are clearly defined and well understood. I still think this is missing or incomplete with serverless as a concept, largely driven by the plethora of services and the differences between cloud platforms offerings. With Kubernetes, docker is docker, you can take a unified approach.

But we can achieve the same with serverless architectures, using careful abstractions, and understanding how the same patterns we see in traditional architectures, can apply to serverless.

Example repo: https://github.com/EwanValentine/serverless-api-example
