# 云原生的解决方案 - CNCF 之路
```
原文
While discussing on Digital Transformation and modern application development Cloud-Native is a term which frequently comes in. But what does it actually means to be cloud-native? This blog is all about giving a good understanding of the cloud-native approach and the ways to achieve it in the CNCF way.
```
在讨论数字改革和新一代应用程序开发时，云原生 (Cloud-Native) 是一个经常出现的术语。但云原生事实上意味着什么呢？ 本博客旨在深入了解云原生方法以及以CNCF方式实现它的方法。

```
Michael Dell once said that “the cloud isn’t a place, it’s a way of doing IT”. He was right, and the same can be said of cloud-native.
```
Dell 公司的老板说：“云不是一个设施，它是为了实现IT化之路”。他是对的，云原生的定义也是如此。

```
Cloud-native is an approach to building and running applications that exploit the advantages of the cloud computing delivery model. Cloud-native is about how applications are created and deployed, not where. … It’s appropriate for both public and private clouds.
```

云原生是一种构建和运行应用程序的方法，可利用云计算交付模型的优势。 云原生是关于如何创建和部署应用程序，不关心在哪....它适用于公共云和私有云。

```
Cloud native architectures take full advantage of on-demand delivery, global deployment, elasticity, and higher-level services. They enable huge improvements in developer productivity, business agility, scalability, availability, utilization, and cost savings.
```

云原生架构充分利用按需交付，全局部署，弹性和更高级别的服务。 它们可以显着提高开发人员的工作效率，业务灵活性，可扩展性，可用性，利用率和节约成本。

```
CNCF (Cloud native computing foundation)

Google has been using containers for many years and they led the Kubernetes project which is a leading container orchestration platform. But alone they can’t really change the broad perspective in the industry around modern applications. So there was a huge need for industry leaders to come together and solve the major problems facing the modern approach. In order to achieve this broader vision, Google donated kubernetes to the Cloud Native foundation and this lead to the birth of CNCF in 2015.
```

CNCF (Cloud native computing foundation)
Google 已经使用了很多年的容器技术，他们开发了 Kubernetes 项目，这是一个领先的容器编排平台。 但仅凭它们无法真正改变新一代应用广泛的应用场景。 因此，行业领导者迫切需要走到一起，解决现在面临的主要问题。 为了适配这一更广阔的应用场景，Google 将 kubernetes 捐赠给了 Cloud Native 基金会，这促成了2015年 CNCF 的诞生。
![1](https://cdn-images-1.medium.com/max/1200/1*S1V9R_C_rjLVlH3M8dyF-g.png)

```
Cloud Native computing foundation is created in the Linux foundation for building and managing platforms and solutions for modern application development. It really is a home for amazing projects that enable modern application development. CNCF defines cloud-native as “scalable applications” running in “modern dynamic environments” that use technologies such as containers, microservices, and declarative APIs. Kubernetes is the world’s most popular container-orchestration platform and the first CNCF project.
```

Cloud Native 基金会归属于 Linux 基金会名下，用于构建和管理新一代应用程序开发平台和解决方案。它是为了新一代应用程序开发组建的基金会。CNCF 将云原生定义为在“新一代动态环境”中运行的“可扩展应用程序”，这些应用程序使用容器，微服务和API声明等技术。 Kubernetes 是世界上最受欢迎的容器编排平台，也是 CNCF 的第一个项目。

```
The approch....
CNCF created a trail map to better understand the concept of Cloud native approach. In this article, we will be discussed based on this landscape. The newer version is available at https://landscape.cncf.io/
```

# The approch...
CNCF创建了一个步骤图，以更好地理解云原生方法的概念。 在本文中，我们将基于图中的服务进行讨论。 点击这个连接查看：[CNCF Landscape](https://landscape.cncf.io/)

```
The Cloud Native Trail Map is CNCF’s recommended path through the cloud-native landscape. This doesn’t define a specific path with which we can approach digital transformation rather there are many possible paths you can follow to align with this concept based on your business scenario. This is just a trail to simplify the journey to cloud-native.
```

Cloud Native 步骤图是 CNCF 推荐的步骤图去一览云原生中的组件。它并没有指定一条明确的路径，但是您可以根据业务场景选择进行数字化之路所要使用的组件， 这只是简化云原生之旅的一条线索。

```
Let's start discussing the steps defined in this trail map.
```
让我们开始讨论云原生化的步骤

# 1. 容器化
```
1. CONTAINERIZATION
You can’t do cloud-native without containerizing your application. It doesn’t matter what size the application is any type of application will do. A container is a standard unit of software that packages up the code and all its dependencies so the application runs quickly and reliably from one computing environment to another. Docker is the most preferred platform for containerization. A Docker container image is a lightweight, standalone, executable package of software that includes everything needed to run an application.
```

如果你不对应用程序进行容器化，则无法实现云原生。 应用程序的大小与任何类型的应用程序无关。 容器是一个标准的软件单元，它将代码及其所有依赖关系打包，以便应用程序快速适应多个计算环境。 Docker 是最受欢迎的容器化平台。 Docker 容器映像是一个轻量级，独立的可执行软件包，包含运行应用程序所需的所有内容。

```
2. CI/CD
Setup Continuous Integration/Continuous Delivery (CI/CD) so that changes to your source code automatically result in a new container being built, tested, and deployed to staging and eventually, perhaps, to production. Next thing we need to setup is automated rollouts, rollbacks as well as testing. There are a lot of platforms for CI/CD: Jenkins, VSTS, Azure DevOps, TeamCity, JFRog, Spinnaker, etc..
```
# 2. CI/CD
```
1. CONTAINERIZATION
You can’t do cloud-native without containerizing your application. It doesn’t matter what size the application is any type of application will do. A container is a standard unit of software that packages up the code and all its dependencies so the application runs quickly and reliably from one computing environment to another. Docker is the most preferred platform for containerization. A Docker container image is a lightweight, standalone, executable package of software that includes everything needed to run an application.
```
![2](https://cdn-images-1.medium.com/max/1600/1*qOno8YNzmwimlaL9j2fSbA.png)

设置持续集成/持续交付 (CI/CD) 在一个新的容器上构建代码，部署并测试，最终运行在生产环。接下来, 我们需要设置自动部署，回滚和测试。 CI/CD 有很多平台：Jenkins，VSTS，Azure DevOps，TeamCity，JFRog，Spinnaker 等。


# 3. 编排
```
3. ORCHESTRATION
Container orchestration is all about managing the lifecycles of containers, especially in large, dynamic environments. Software teams use container orchestration to control and automate many tasks. Kubernetes is the market-leading orchestration solution. There are other orchestrators like Docker swarm, Mesos, etc.. Helm Charts help you define, install, and upgrade even the most complex Kubernetes application.
```
![3](https://cdn-images-1.medium.com/max/1200/1*fw8YJnfF32dWsX_beQpWOw.png)

容器编排是指容器的生命周期管理，尤其是在大型动态环境中。 软件团队使用容器编排来控制和自动执行许多任务。 Kubernetes 是市场领先的容器编排解决方案。 还有其他容器编排解决方案，如 Docker swarm，Mesos 等. Helm Charts 可帮助您定义，安装和升级最复杂的 Kubernetes 应用程序。

# 4. 监控 & 分析
```
4. OBSERVABILITY & ANALYSIS
Kubernetes provides no native storage solution for log data, but you can integrate many existing logging solutions into your Kubernetes cluster. Kubernetes provides detailed information about an application’s resource usage at each of these levels. This information allows you to evaluate your application’s performance and where bottlenecks can be removed to improve overall performance.
```
![4](https://cdn-images-1.medium.com/max/1600/1*sbjPYNq76s9lR7D_FK4ltg.png)

Kubernetes 不提供日志数据的采集和本机存储解决方案，但您可以将许多现有的日志记采集决方案集成到 Kubernetes 集群中。 Kubernetes 提供一个应用使用资源的详细信息。通过这些信息，您可以评估应用程序的性能和如何消除瓶颈，从而提高整体性能。

```
Pick solutions for monitoring, logging, and tracing. Consider CNCF projects Prometheus for monitoring, Fluentd for logging and Jaeger for TracingFor tracing, look for an OpenTracing-compatible implementation like Jaeger.
```
挑选监控，日志和追踪的解决方案。CNCF 项目 Prometheus 用于监控集群，Fluentd 用于日志记录和 Jaeger 用于追踪，可以找到与 Jaeger 一样的 OpenTracing 兼容实现。


# 5. 服务网格
```
5. SERVER MESH
As its name says it’s all about connecting services, the discovery of services, health checking, routing and it is used to monitoring ingress from the internet. A service mesh also often has more complex operational requirements, like A/B testing, canary rollouts, rate limiting, access control, and end-to-end authentication.
```
![5](https://cdn-images-1.medium.com/max/1600/1*kUFBuGfjZSS-n-32CCjtwQ.png)
服务发现顾名思义就是连接服务，发现服务，健康检查，路由，它用于监控来自互联网的入口。 Server Mech 通常还具有更复杂的操作要求，如 A/B 测试，服务发现，速率限制，访问控制和端到端身份验证。

```
Istio provides behavioral insights and operational control over the service mesh as a whole, offering a complete solution to satisfy the diverse requirements of microservice applications. CoreDNS is a fast and flexible tool that is useful for service discovery. Envoy and Linkerd each enable service mesh architectures.
```
Server Mach 解决方案：Istio 作为一个整体提供对服务的行为洞察和操作控制，提供完整的解决方案以满足微服务应用程序的各种要求。CoreDNS 是一种快速而灵活的工具，可用于服务发现。 Envoy 和 Linkerd 也是 Server Mach 的解决方案。


# 6. NETWORKING AND POLICY
```
6. NETWORKING AND POLICY
It is really important to enable more flexible networking layers. To enable more flexible networking, use a CNI compliant network project like Calico, Flannel, or Weave Net. Open Policy Agent (OPA) is a general purpose policy engine with uses ranging from authorization and admission control to data filtering
```
使用更灵活的网络层非常重要。 要使用更灵活的网络，请使用符合 CNI 的网络项目，如 Calico，Flannel 或 Weave Net。开放策略代理 (OPA) 是一种通用策略引擎，其使用范围从授权和准入控制到数据过滤。

# 7. 分布式数据库
```
7. DISTRIBUTED DATABASE
A distributed database is a database in which not all storage devices are attached to a common processor. It may be stored in multiple computers, located in the same physical location; or may be dispersed over a network of interconnected computers.
```
分布式数据库是一个数据库，其中并非所有存储设备都连接到一个公共处理器。数据可以存储在位于同一物理位置的多台计算机中；或者可以分散在互连计算机的网络上。

![6](https://cdn-images-1.medium.com/max/1600/1*4OGiB3HHQZBFsALjaRb9pA.jpeg)

```
When you need more resiliency and scalability than you can get from a single database, Vitess is a good option for running MySQL at scale through sharding. Rook is a storage orchestrator that integrates a diverse set of storage solutions into Kubernetes. Serving as the “brain” of Kubernetes, etcd provides a reliable way to store data across a cluster of machine
```
当您需要比单节点数据库更具弹性和可伸缩性数据库时，Vitess 是一个很好的选择，它可以是你的 MySQL 具有可扩展性。 Rook 是一个存储协调器，它将各种存储解决方案集成Kubernetes 中 (译者注：Rook 是一个款云原生环境下的开源分布式存储编排系统)。 作为 Kubernetes的 “大脑”，etcd 提供了一种将数据存储在一组机器上的解决方案。

# 8. 通信
```
8. MESSAGING
When you need higher performance than JSON-REST, consider using gRPC or NATS. gRPC is a universal RPC framework. NATS is a multi-modal messaging system that includes request/reply, pub/sub and load balanced queues. It is also applicable and take care of much newer and use cases like IoT.
```
当您需要比 JSON-REST 更高的性能的消息中间件时，请考虑使用 gRPC 或NATS。 gRPC 是一个通用的 RPC 框架。 NATS 是一种多模式消息传递系统，包括 `request/reply`, `pub/sub` 和负载平衡队列。 它也适用于并处理更新的和物联网等用例。

# 9. 容器注册 & Runtimes
```
9. CONTAINER REGISTRY & RUNTIMES

Container Registry is a single place for your team to manage Docker images, perform vulnerability analysis, and decide who can access what with fine-grained access control. There are many container registries available in market docker hub, Azure Container registry, Harbor, Nexus registry, Amazon Elastic Container Registry and way more…
```
容器注册是您的团队管理Docker镜像，执行漏洞分析以及决定谁可以使用容器，细粒度的访问控制访问哪些内容。 Market Docker hub，Azure 容器注册中心，Harbour，Nexus 注册中心，Amazon Elastic Container Registry 以及更多方式提供了许多容器注册中心。

```
Container runtime containerd is available as a daemon for Linux and Windows. It manages the complete container lifecycle of its host system, from image transfer and storage to container execution and supervision to low-level storage to network attachments and beyond.
```
Container Runtime 是 Linux 和 Windows 的一个守护进程。它管理其主机系统的完整的容器生命周期，从图像传输和存储到容器执行和监督，再到低级存储，再到网络附件等。

# 10. 软件分发
```
10. SOFTWARE DISTRIBUTION
If you need to do secure software distribution, evaluate Notary, implementation of The Update Framework (TUF).
TUF provide a framework (a set of libraries, file formats, and utilities) that can be used to secure new and existing software update systems. The framework should enable applications to be secure from all known attacks on the software update process. It is not concerned with exposing information about what software is being updated (and thus what software the client may be running) or the contents of updates.
```
如果您需要安全的进行软件分发，请评估 Notary，关于实现更新框架（TUF）。

TUF提供了一个框架（一组 libraries，文件格式和实用程序），可用于保护新的和现有的软件更新系统。 该框架应该使应用程序能够抵御软件更新过程中的所有已知攻击。 它不关心是否暴漏有关正在更新的软件（以及客户端可能正在运行的软件）或更新内容的信息。

> “Cloud-native applications are specifically designed to run on cloud infrastructure, hence the term ‘native’. They are growing in popularity because they deliver benefits, which include: high availability and responsiveness, plus also strong resilience and flexibility through autonomous and self-healing capabilities, such as designing for failure,”
> CNCF democratize state-of-the-art patterns to make these innovations accessible for everyone.

> “Cloud-native application 专门设计用于在云基础架构上运行，因此称为 ”原生 (native)“ 。 它们越来越受欢迎，因为它们带来了好处，包括：高可用性和响应性，以及通过自主和自我修复功能的强大弹性和灵活性，例如：设计失败“
> CNCF使最先进的模式民主化，使每个人都可以获得这些创新。

[点击阅读原文](https://medium.com/@sonujose993/what-it-means-to-be-cloud-native-approach-the-cncf-way-9e8ab99d4923)