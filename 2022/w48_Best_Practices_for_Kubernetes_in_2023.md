# Best Practices for Kubernetes in 2023


- 原文地址：https://myhistoryfeed.medium.com/best-practices-for-kubernetes-in-2023-bd0aaada1f72
- 原文作者：MyHistoryFeed
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[]()
***

![Kubernetes](https://miro.medium.com/max/1024/0*JDVk89SkkXugCfZH)

As a container orchestration platform, Kubernetes (K8s) offers numerous advantages. K8s, for example, is big on automation. This includes workload discovery, self-healing, and containerized application scaling.

However, Kubernetes isn’t always ready for production after a few tweaks.

This guide shares critical Kubernetes best practices that you should implement right away to improve your K8s security, performance, and costs.

![Practices](https://miro.medium.com/max/1400/0*6AEPn08Te6lX8513.jpg)

## 1. Keep Up With The Most Stable

The general rule is to update your K8s to the most recent stable version. It will most likely already be patched for any security or performance issues. There will almost certainly be more community-based or vendor-provided support available as well. Finally, the K8s best practice allows you to avoid security, performance, and cost anomalies that could jeopardize your service delivery.

## 2. Lint Your Manifests

Perhaps you find YAML difficult to use. Then you can use yamllint, which can handle multiple documents in a single file.

There are also Kubernetes-specific linters available:

You can lint your manifests and follow best practices with kube-score.  
Kubeval will also lint your manifests. However, it only checks for validity.  
The dry-run option on kubectl in Kubernetes 1.13 allows Kubernetes to inspect but not apply your manifests. This feature allows you to validate your YAML files for K8s.

## 3. Versioning Config Files Is Your Friend

Store all config files, such as deployment, services, and ingress ones in a version control system. GitHub is the most popular, open-source, and distributed version control platform for that, but others include GitLab, BitBucket, and SourceForge.

Doing this before pushing your code to a cluster enables you to track source code changes and who made them. Whenever necessary, you can quickly roll back the change, re-create, or restore your cluster to ensure stability and security.

## 4. A Git Workflow Is The Way To Go

GitOps, or Git-based workflow, is an excellent model for automating all tasks, including CI/CD pipelines, with Git serving as the single source of truth. A GitOps framework can assist you in the following ways, in addition to increasing productivity:

1.  Accelerate deployments
2.  Enhance error tracking
3.  Automate your CI/CD workflows.

Finally, using the GitOps approach simplifies cluster management and speeds up app development.

## 5. Take Advantage Of Declarative YAML Files

Write declarative YAML files instead of using imperative kubectl commands like kubectl run. Then, using the kubectl apply command, you can add them to your cluster. A declarative approach allows you to specify the desired state, and Kubernetes will figure out how to get there.

All of your objects, as well as your code, can be stored and versioned in YAML files. If something goes wrong, you can easily roll back deployments by restoring an earlier YAML file and reapplying it. Furthermore, this model ensures that your team can see the cluster’s current status as well as changes made to it over time.

## 6. Say What You Want With Resource Requests And Caps

Millicores are typically used for CPUs and mebibytes or megabytes for memory when defining CPU and memory limits for either requests or limits. Containers will not run in a pod if a resource request exceeds the limit you specify.

When resources are scarce, production clusters may fail in the absence of resource limits and requests. Excess resources can be consumed by pods in a cluster, increasing your Kubernetes costs. Furthermore, if pods consume too much CPU or memory and the scheduler is unable to add new pods, nodes can crash.

## 7. Couple Pods To Deployments, ReplicaSets, And Jobs

As much as possible, avoid using naked pods. Naked pods cannot be rescheduled in the event of a node failure because they are not bound to a Deployment or ReplicaSet.

A deployment achieves two goals:

1.  Creates a ReplicaSet to keep the desired number of pods.
2.  Defines a replacement strategy for pods, such as a RollingUpdate.

Unless you have a strict restart Policy: Never use cases, deploying is almost always more efficient than creating pods directly.

## 8. Clearly Label Your K8s Resources

Labels are key/value pairs that help you identify the characteristics of a specific resource in Kubernetes clusters. Labels also allow you to filter and select objects with kubectl, allowing you to quickly identify objects based on a specific characteristic.

Even if you don’t think you’ll use them right away, labeling your objects is a good idea. Also, use as many descriptive labels as possible to differentiate between the resources that your team will be working on. Objects can be labeled by owner, version, instance, component, managed by, project, team, confidentiality level, compliance aspects, and other criteria.

## 9. Run Liveness Probes (After This Other Probe)

Liveness probes check the health of long-lived pods on a regular basis, preventing Kubernetes from routing traffic to unhealthy ones. Kubernetes (kubelet default policy) restarts pods that fail a health check, ensuring your app’s availability.

The probe sends a ping to the pod to see if it receives a response. No response indicates that your app is not running on that pod, causing the probe to launch a new pod and run the application there.

Another point. You must first run a startup probe, a third type of probe that alerts K8s when a pod’s startup sequence is complete. If a pod’s startup probe is incomplete, the liveness and readiness probes do not target it.

## 10. Namespaces Simplify Resource Management

Namespaces assist your team in logically partitioning a cluster into sub-clusters. This is especially useful when you want to share a Kubernetes cluster among multiple projects or teams at the same time. Namespaces allow development, testing, and production teams to collaborate within the same cluster without overwriting or interfering with each other’s projects.

Kubernetes ships with three namespaces: default, kube-system, and kube-public. A cluster can support multiple namespaces that are logically separate but can communicate with one another.

## 11. Keep It Stateless

Stateless apps are generally easier to manage than stateful apps, though this is changing as Kubernetes Operators gain popularity.

A stateless backend eliminates the need for teams new to Kubernetes to maintain long-running connections that limit scalability.

Stateless apps also make it easier to migrate and scale on demand.

Just one more thing. Keeping workloads stateless allows you to use spot instances.

Here’s the deal. One disadvantage of using Spots Instances is that providers such as AWS and Azure frequently require the cheap compute resources to be returned on short notice, which can disrupt your workload. You can circumvent this issue by making your application stateless.

## 12. Establish Your Network Policies

A network policy in Kubernetes specifies which traffic is allowed and which is not. It’s similar to putting firewalls between pods in a Kubernetes cluster. Regardless of how traffic moves between pods in your environment, it will only be permitted if your network policies allow it.

You must define authorized connections and specify which pods the policy should apply to before you can create a network policy. This filters out any traffic that does not meet your criteria.

You can find various examples of Kubernetes Network Policies and sample YAML files in this repository.

## 13. Set Up Role Based Access Controls

Consider this:

RedHat discovered the following in a survey of over 300 DevOps professionals in 2022:

-   For 55% of respondents, security concerns delayed application release.
-   In terms of continuing to use Kubernetes and containers, 59% cited security as a major impediment.
-   31% said a security breach resulted in revenue or customer loss.
-   Almost all of them (94%) had at least one Kubernetes security incident in the previous year.

![Kubernetes Adoption, Security, and Market Trends](https://miro.medium.com/max/1400/1*adz0_UmrIqCPJID4eVi6ew.png)

You can use RBAC to specify which users have access to which Kubernetes resources, such as which clusters they can access, who can make changes, and to what extent they can make changes.

RBAC permissions can be configured in two ways:

-   If you want to set permissions for a non-namespaces resource, use **ClusterRole**.  
    •Namespaced Kubernetes resource **by Role**

## 14. Firewall Your Kubernetes Environment

Another significant Kubernetes security best practice.

Set up a firewall in front of the cluster to limit external requests from reaching the API server, in addition to network policies to control internal traffic within your cluster. This can be accomplished through the use of regular or port firewall rules.

Additionally, make sure that IP addresses are whitelisted and that open ports are restricted.

## 15. Smaller Images Are More Ideal

Make your images small and layered. The smaller the image, the faster the build and the less storage space required. An image’s size can be significantly reduced by efficiently layering it. By starting from scratch, you can optimize your images.

How?

Use multiple FROM statements in a single Dockerfile if you need many different components. The setup will lift each layer from the deployed container based on the FROM command.

The feature generates sections, each referring to a different base image. The resulting Docker container is smaller because it no longer includes previous layers, only the components you require.

## See you in my next post!

## Best Articles Of The Month:

-   [Top 10 DevOps Trends to keep an Eye on 2023!](https://myhistoryfeed.medium.com/top-10-devops-trends-to-keep-an-eye-on-in-2023-247971ad4a26)
-   [5 Top Kubernetes Monitoring Tools You’ve Probably Haven’t Used](https://myhistoryfeed.medium.com/5-top-kubernetes-monitoring-tools-youve-probably-haven-t-used-2a149f264288)
-   [You Should Know this Kubernetes Terminologies!](https://myhistoryfeed.medium.com/you-should-know-these-kubernetes-terminologies-b6451bceae1e)
