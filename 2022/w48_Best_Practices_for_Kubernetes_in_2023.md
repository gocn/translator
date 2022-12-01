# 2023 年 Kubernetes 最佳实践


- 原文地址：https://myhistoryfeed.medium.com/best-practices-for-kubernetes-in-2023-bd0aaada1f72
- 原文作者：MyHistoryFeed
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[cvley](https://github.com/cvley)
***

![Kubernetes](https://github.com/gocn/translator/raw/master/static/images/2022/w48_Best_Practices_for_Kubernetes/0*JDVk89SkkXugCfZH)

作为容器编排平台，Kubernetes（K8s）具有诸多优势。例如，K8s 在工作负载发现、自我修复和应用容器化扩展等方面具备很强的自动化。

然而，在经过一些调整后，Kubernetes 并不总是适用于生产环境。

本文向您分享了一些重要的 Kubernetes 最佳实践，以提高您的 K8s 安全性、性能和成本。

![Practices](https://github.com/gocn/translator/raw/master/static/images/2022/w48_Best_Practices_for_Kubernetes/0*6AEPn08Te6lX8513.webp)

## 1. 保持最稳定版本

一般是将您的 K8s 更新到最新的稳定版本。此版本很可能已经针对任何安全或性能问题进行了修补。基本上也会有更多基于社区版本或供应商提供的支持。最后，K8s 最佳实践可以让您避免出现一些可能危及服务交付的安全、性能和成本异常。

## 2. 整理清单

也许您发现 YAML 很难用。那么你可以使用 yamllint，它可以在一个文件中处理多个文档。

此外也有 Kubernetes 特定的 linters 可用：

- 您可以使用 kube-score 整理您的清单并遵循最佳实践。
- Kubeval 也会检查你的清单。但是，它只检查有效性。
- Kubernetes 1.13 中 kubectl 的 dry-run 选项允许 Kubernetes 检查但不应用您的清单。此功能将验证 K8s 的 YAML 文件。

## 3. 管理好版本控制配置文件

将所有配置文件（例如 deployment、services 和 ingress）存储在版本控制系统中。GitHub 是目前最流行的开源分布式版本控制平台，其他平台还包括 GitLab、BitBucket 和 SourceForge。

在将您的代码推送到集群之前执行此操作，使您能够跟踪源代码变更以及谁进行了变更。必要时，您可以快速回滚变更、重新创建或恢复集群，以确保稳定性和安全性。

## 4. Git 工作流

GitOps 或基于 Git 的工作流，是一个用于自动化所有任务的优秀模型，包括 CI/CD 管道。除了提高生产力之外，GitOps 框架还可以通过以下方式为您提供帮助：

1.  加速部署
2.  增强错误跟踪能力
3.  CI/CD 流程自动化

总之，使用 GitOps 方法可以简化集群管理并加快应用程序开发。

## 5. 利用声明式 YAML 文件

编写声明式的 YAML 文件，而不是使用诸如 kubectl run 等命令。之后，使用 kubectl apply 命令，您可以将它们添加到集群中。声明式方法允许您指定所需的状态， Kubernetes 也能够处理。

所有对象以及代码都可以存储在 YAML 文件中并进行版本控制。如果出现问题，您可以通过恢复较早的 YAML 文件并重新应用它来实现轻松回滚。此外，此模式可确保您的团队可以看到集群的当前状态，以及从时间线上看到对其所做的更改。

## 6. 指定资源请求和限制

当定义 CPU 和内存的资源限制和请求时，毫核通常用于CPU，兆字节用户内存。需要注意的是，容器运行时会禁止容器使用超出所设置资源限制的资源。

当资源稀缺时，生产集群可能会在没有资源限制和请求的情况下失败。集群中的 Pod 可能会消耗过多的资源，从而增加您的 Kubernetes 成本。此外，如果 pod 消耗太多 CPU 或内存并且调度程序无法添加新的 pod，节点可能会崩溃。

## 7. 将 Pods 与Deployments, ReplicaSets, 和 Jobs绑定

尽可能不要使用独立的 Pod（即未绑定到 ReplicaSet 或 Deployment 的 Pod）。 如果节点发生故障，将不会重新调度这些独立的 Pod。

deployment 能够实现两个目标：

1.  创建一个 ReplicaSet 来确保预期个数的 Pod 始终可用
2.  指定替换 Pod 的策略，例如 RollingUpdate

除了一些显式的 restartPolicy: Never 场景外，Deployment 通常比直接创建 Pod 要好得多。

## 8. 清晰标记 K8s 资源

标签是可帮助您识别 Kubernetes 集群中资源特性的键/值对。标签还允许您使用 kubectl 过滤和选择对象，让您可以根据特定特征快速识别对象。

即使您认为您当前不会使用它们，给您的对象贴上标签也是极好的。此外，尽可能多地使用描述性标签来区分您的团队将使用的资源。对象可以按所有者、版本、实例、组件、管理者、项目、团队、保密级别、合规性和其他标准进行标记。

## 9. 运行存活探测（在其他探测之后）

存活探测定期检查 pod 的健康状况，防止 Kubernetes 将流量路由到不健康的 pod。Kubernetes（kubelet 默认策略）会重启未通过健康检查的 pod，确保应用程序的可用性。

探针向 pod 发送 ping 以查看是否能收到响应。无响应则表示您的应用程序未在该 pod 上运行，进而启动新的 pod 并在那里运行应用程序。

还有一点。您必须先运行启动探测，这是第三种类型的探测，它会在 pod 的启动阶段完成时向 K8s 发出警报。如果 pod 的启动探测不完整，则 存活探针 和 就绪态探针 也不会再去探测。

## 10. 通过命名空间简化资源管理

命名空间可帮助您的团队在逻辑上将一个集群划分为多个子集群。当您想同时在多个项目或团队之间共享 Kubernetes 集群时，这尤其有用。命名空间允许开发、测试和生产团队在同一集群内协作，而不会覆盖或干扰彼此的项目。

Kubernetes 附带三个命名空间：default、kube-system 和 kube-public。一个集群可以支持多个逻辑上独立但可以相互通信的命名空间。

## 11. 保持无状态

无状态应用程序通常比有状态应用程序更易于管理，尽管随着 Kubernetes Operators 越来越受欢迎，这种情况正在发生变化。

对于不熟悉 Kubernetes 的团队来说，无状态后端消除了维持长期连接的可扩展性限制。

无状态应用程序还可以更轻松地按需迁移和扩展。

更重要的是，保持工作负载无状态，您就可以使用临时实例。

使用临时实例的一个缺点是 AWS 和 Azure 等提供商经常需要您在短时间内返还这些廉价的计算资源，这可能会中断您的工作负载。您可以通过使您的应用程序无状态来规避此问题。

## 12. 建立网络策略

Kubernetes 中的网络策略指的是哪些流量被允许，哪些不被允许。这类似于在 Kubernetes 集群中的 pod 之间放置防火墙。无论流量如何在您环境中的 pod 之间流动，只有在您的网络策略认可的情况下流量才会被允许。

在创建网络策略之前，您必须定义授权连接并指定该策略应用于哪些 pod。这能帮助您过滤掉任何不符合条件的流量。

您可以在[此](https://kubernetes.io/zh-cn/docs/concepts/services-networking/network-policies/)找到 Kubernetes 网络策略的各种示例和示例 YAML 文件。

## 13. 设置基于角色的访问控制

先看以下数据：

RedHat 在 2022 年对 300 多名 DevOps 专业人员的调查中发现了以下内容：

-   对于 55% 的受访者来说，安全问题会延后应用程序发布。
-   在持续使用 Kubernetes 和容器方面，59% 的人认为安全是主要障碍。
-   31% 表示安全漏洞导致了收入或客户流失。
-   几乎所有人 (94%) 在前一年至少发生过一次 Kubernetes 安全事件。

![Kubernetes Adoption, Security, and Market Trends](https://github.com/gocn/translator/raw/master/static/images/2022/w48_Best_Practices_for_Kubernetes/1*adz0_UmrIqCPJID4eVi6ew.webp)

您可以使用 RBAC 指定哪些用户可以访问哪些 Kubernetes 资源，例如他们可以访问哪些集群、谁可以进行更改以及他们可以更改到什么程度。

可以通过两种方式配置 RBAC 权限：

-   如果你希望定义集群范围的角色，应该使用 **ClusterRole**。
-   如果你希望在名字空间内定义角色，应该使用 **by Role**。

## 14. 为 Kubernetes 环境设置防火墙

这是另外一种重要的 Kubernetes 安全最佳实践。

在集群前面设置防火墙以限制外部请求到达 API 服务器，此外还设置网络策略来控制集群内的内部流量。可以通过使用常规或端口防火墙规则来完成。

此外，需要确保 IP 地址已列入白名单并且设置开放端口限制。

## 15. 镜像越小越好

使您的镜像小而分层。因为镜像越小，构建速度越快，所需的存储空间也越少。通过有效地分层可以显着减小图像的大小。从此之后，您可以通过一些手段来优化镜像。

如果做呢？

如果您需要许多不同的组件，请在单个 Dockerfile 中使用多个 FROM 语句。该设置将根据 FROM 命令从已部署的容器中提取每一层。

在生成阶段，每个部分都引用不同的基本镜像。这样生成的 Docker 容器更小，因为它不再包含前面的层，只包含您需要的组件。

## 在我的下一篇文章中见！

## 本月最佳文章：

-   [2023 年值得关注的 10 大 DevOps 趋势！](https://myhistoryfeed.medium.com/top-10-devops-trends-to-keep-an-eye-on-in-2023-247971ad4a26)
-   [您可能没有使用过的 5 个顶级 Kubernetes 监控工具](https://myhistoryfeed.medium.com/5-top-kubernetes-monitoring-tools-youve-probably-haven-t-used-2a149f264288)
-   [你应该知道这个 Kubernetes 术语！](https://myhistoryfeed.medium.com/you-should-know-these-kubernetes-terminologies-b6451bceae1e)
