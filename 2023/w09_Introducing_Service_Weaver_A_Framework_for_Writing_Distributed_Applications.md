### Service Weaver : 一个用于编写分布式应用的框架

- 原文地址：[Introducing Service Weaver: A Framework for Writing Distributed Applications | Google Open Source Blog (googleblog.com)](https://opensource.googleblog.com/2023/03/introducing-service-weaver-framework-for-writing-distributed-applications.html)
- 原文作者：Srdjan Petrovic and Garv Sawhney
- 本文永久链接：[translator/w09_Introducing_Service_Weaver_A_Framework_for_Writing_Distributed_Applications.md at master · gocn/translator (github.com)](https://github.com/gocn/translator/blob/master/2023/w09_Introducing_Service_Weaver_A_Framework_for_Writing_Distributed_Applications.md)
- 译者：[zxmfke](https://github.com/zxmfke)
- 校对：

我们很高兴地介绍 Service Weaver，**这是一个用于构建和部署分布式应用程序的开源框架**。Service Weaver 允许您将应用程序编写为一个**模块化**的单体应用，并将其部署为一组微服务。

更具体地说，Service Weaver 由两个核心部分组成：

1. 一组编程库，让你只需要使用原生数据结构和方法调用，就可以将应用程序编写为单个**模块化**二进制文件。
2. 一组部署程序，允许您配置应用程序的运行时拓扑，并将其部署为一组微服务，可以在本地或您选择的云上进行部署。

![Flow chart of Service Weaver Programming Libraries from development to execution, moving four modules labeled A through D from application across a level of microservices to deployers labeled Desktop, Google Cloud, and Other Cloud](C:\Users\zhengxm\Documents\notes\翻译\Introducing Service Weaver A Framework for Writing Distributed Applications\1.png)

通过将编写应用程序的过程与 runtime 考虑因素（例如如何将应用程序拆分为微服务、使用哪些数据序列化格式以及如何发现服务）分离，Service Weaver 旨在提高分布式应用程序开发速度和性能。

### 构建 Service Weaver 的动机

在编写基于微服务的应用程序时，我们发现维护多个不同的微服务二进制文件，以及它们各自的配置文件、网络端点和可序列化数据格式，会显著降低我们的开发速度。

更重要的是，**微服务严重影响了我们进行跨二进制更改的能力**。这使我们不得不在每个二进制文件中标记新功能，小心地更替我们的数据格式，并保持对我们的推出流程的深入了解(这意味着我们需要非常熟悉我们的应用程序部署流程)。最后，预先确定特定数量的微服务有效地冻结了我们的 API；它们变得如此难以更改，以至于把所有更改都挤进现有的 API 中比修改它们更容易。

因此，我们希望有一个单一的单体二进制文件来使用。单体二进制文件易于编写：它们只使用原生的语言类型和方法调用。它们也易于更新：只需编辑源代码并重新部署即可。它们易于在本地或虚拟机中运行：只需执行二进制文件即可。

**Service Weaver 是具有单体应用程序的开发速度，同时也具备微服务的可扩展性、安全性和容错性，是两者之间最佳结合的一个框架。**

## Service Weaver 概览

Service Weaver 的核心思想是其“**模块式单体应用**”模型。您可以编写一个单一的二进制文件，只使用语言原生的数据结构和方法调用。您可以将二进制文件组织为一组模块，称为“**组件**”，这些组件是编程语言的原生类型。例如，以下是使用 Service Weaver 编写的 Go 语言应用程序。它由一个 main() 函数和一个 Adder 组件组成：

```go
type Adder interface { 
    Add(context.Context, int, int) (int, error)
} 
type adder struct{ 
    weaver.Implements[Adder]
}
func (adder) Add(_ context.Context, x, y int) (int, error) {
  return x + y, nil
}

func main() {
  ctx := context.Background()
  root := weaver.Init(ctx)
  adder, err := weaver.Get[Adder](root)
  sum, err := adder.Add(ctx, 1, 2)
}
```

运行上述应用程序时，您可以进行微不足道的配置选择，即将 Adder 组件与 main() 函数放在一起还是分开放置。当 Adder 组件是独立的时，Service Weaver 框架会自动将 Add 调用转换为远程 RPC；否则，Add 调用仍然是本地方法调用。

要对上述应用程序进行更改，例如向 Add 方法添加无限数量的参数，您只需要更改 Add 的签名，更改其调用位置，然后重新部署应用程序。Service Weaver 确保新版本的 main() 仅与新版本的 Adder 通信，而不管它们是否共存。这种行为，结合使用语言原生的数据结构和方法调用，使您可以专注于编写应用程序逻辑，而不必担心部署拓扑和服务间通信（例如，在代码中没有 protos、stubs 或 RPC 通道）。

当运行应用程序时，Service Weaver 允许您在任何地方运行它——在您的本地桌面环境、本地机架或云上——而不需要更改应用程序代码。这种可移植性是通过 Service Weaver 框架内置的明确关注点分离实现的。在一端，我们有编程框架，用于应用程序开发。在另一端，我们有各种“**部署器**”实现，每个实现针对一种部署环境。

![Flow chart depicting Service Weaver Libraries deployer implementations across three separate platforms in one single iteration](C:\Users\zhengxm\Documents\notes\翻译\Introducing Service Weaver A Framework for Writing Distributed Applications\2.png)

这种关注点分离使您可以通过 go run .在本地单个进程中运行应用程序；或通过 weaver gke deploy 在 Google Cloud 上运行；或在其他平台上启用和运行它。在所有这些情况下，您都可以获得相同的应用程序行为，而无需修改或重新编译应用程序。

## Service Weaver v0.1 包括什么?

- 用于编写应用程序的[Go 核心库](https://github.com/ServiceWeaver/weaver)。
- 用于在本地或 GKE 上运行应用程序的一些部署器，如[本地部署器](https://github.com/ServiceWeaver/weaver/tree/main/cmd/weaver)或[GKE 部署器](https://github.com/ServiceWeaver/weaver-gke)。
- 一组 API，允许您为任何其他平台编写自己的部署器。

所有库都在 Apache 2.0 许可下发布。请注意，在发布 v1.0 版本之前，**我们可能会引入破坏性更改**。

## 入门指南和参与方式

虽然 Service Weaver 仍处于早期开发阶段，但我们希望邀请您使用它并分享您的反馈、想法和贡献。

使用 Service Weaver 的最简单方法是遵循我们网站上的[逐步说明](https://serviceweaver.dev/docs.html#step-by-step-tutorial)。如果您想做出贡献，请遵循我们的[贡献者指南](https://github.com/ServiceWeaver/weaver/blob/main/CONTRIBUTING.md)。如果要发布问题或直接联系团队，请使用 Service Weaver 的[邮件列表](https://groups.google.com/g/serviceweaver)。

请关注 Service Weaver [博客](https://serviceweaver.dev/blog/)以获取最新消息、更新和未来活动的详细信息。

## 更多资源

- 访问我们的网站[serviceweaver.dev](https://serviceweaver.dev/)，获取有关该项目的最新信息，例如入门指南、教程和博客文章。
- 访问我们在 GitHub 上的其中一个 Service Weaver [代码库](https://github.com/orgs/ServiceWeaver/repositories)。

*By Srdjan Petrovic and Garv Sawhney,  仅代表 Service Weaver team*
