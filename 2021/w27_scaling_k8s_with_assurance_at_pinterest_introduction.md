# Scaling Kubernetes with Assurance at Pinterest

* 原文地址：https://medium.com/pinterest-engineering/building-a-kubernetes-platform-at-pinterest-fb3d9571c948
* 原文作者：`pinterest-engineering`
* 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w27_scaling_k8s_with_assurance_at_pinterest_introduction.md
- 译者：[咔叽咔叽](https:/github.com/watermeloooo)

## Introduction

It has been more than a year since we shared our [Kubernetes Journey at Pinterest](https://medium.com/pinterest-engineering/building-a-kubernetes-platform-at-pinterest-fb3d9571c948). Since then, we have delivered many features to facilitate customer adoption, ensure reliability and scalability, and build up operational experience and best practices.

In general, Kubernetes platform users gave positive feedback. Based on our user survey, the top three benefits shared by our users are reducing the burden of managing compute resources, better resource and failure isolation, and more flexible capacity management.

By the end of 2020, we orchestrated **35K+ pods** with **2500+ nodes** in our Kubernetes clusters — supporting a wide range of Pinterest businesses — and the organic growth is still rocket high.

## 2020 in a Short Story

As user adoption grows, the variety and number of workloads increases. It requires the Kubernetes platform to be more scalable in order to catch up with the increasing load from workload management, pods scheduling and placement, and node allocation and deallocation. As more business critical workloads onboard the Kubernetes platform, the expectations on platform reliability naturally rise to a new level.

Platform-wide outage did happen. In early 2020, one of our clusters experienced a sudden spike of pods creation (~3x above planned capacity), causing the cluster autocalor to bring up 900 nodes to accommodate the demand. The [kube-apiserver](https://kubernetes.io/docs/concepts/overview/components/#kube-apiserver) started to first experience latency spikes and increased error rate, and then get Out of Memory (OOM) killed due to resource limit. The unbound retry from Kubelets resulted in a 7x jump on kube-apiserver load. The burst of writes caused [etcd](https://etcd.io/) to reach its total data size limit and start rejecting all write requests, and the platform lost availability in terms of workload management. In order to mitigate the incident, we had to perform etcd operations like compacting old revisions, defragmenting excessive spaces, and disabling alarms to recover it. In addition, we had to temporarily scale up Kubernetes master nodes that host kube-apiserver and etcd to reduce resource constraint.

![](https://miro.medium.com/max/700/0*HdAKrJV53QBeelLF)

Later in 2020, one of the infra components had a bug in kube-apiserver integration that generated a spike of expensive queries (listing all pods and nodes) to kube-apiserver. This caused the Kubernetes master node resource usage spikes, and kube-apiserver entered OOMKilled status. Luckily the problematic component was discovered and rolled back shortly afterwards. But during the incident, the platform performance suffered from degrationation, including delayed workload execution and stale status serving.

![](https://miro.medium.com/max/700/0*1gigns-zIDLjz6M7)

## Getting Ready for Scale

We continue to reflect on our platform governance, resilience, and operability throughout our journey, especially when incidents happen and hit hard on our weakest spots. With a nimble team of limited engineering resources, we had to dig deep to find out root causes, identify low hanging fruits, and prioritize solutions based on return vs. cost. Our strategy for dealing with the complex Kubernetes ecosystem is to try our best to minimize divergence from what’s provided by the community and contribute back to the community, but never rule out the option of writing our own in house components.

![](https://miro.medium.com/max/700/0*ARhaNPp-Jl33ZVcN)

## Governance

### Resource Quota Enforcement

Kubernetes already provides [resource quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) management to ensure no namespace can request or occupy **unbounded** resources in most dimensions: pods, cpu, memory, etc. As our previous incident mentioned, a surge of pod creation in a single namespace could overload kube-apiserver and cause cascading failure. It is key to have resource usage bounded in every namespace in order to ensure stability.

One challenge we faced is that enforcing resource quota in every namespace implicitly requires all pods and containers to have [resource requests and limits](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#requests-and-limits) specified. In Pinterest Kubernetes platform, workloads in different namespaces are owned by different teams for different projects, and platform users configure their workload via Pinterest CRD. We achieved that by adding default resource requests and limits for all pods and containers in the CRD transformation layer. In addition, we also rejected any pod specification without resource requests and limits in the CRD validation layer.

Another challenge we overcame was to streamline quota management across teams and organizations. To safely enable resource quota enforcement, we look at historical resource usage, add 20% headroom on top of peak value, and set it as the initial value for resource quota for every project. We created a cron job to monitor quota usage and send business hour alerts to project owning teams if their project usage is approaching a certain limit. This encourages project owners to do a better job of capacity planning and request a resource quota change. The resource quota change gets manually reviewed and automatically deployed after sign-off.

### Client Access Enforcement

We enforce all KubeAPI clients to follow the best practices Kubernetes already provides:

### Controller Framework

[Controller framework](https://github.com/operator-framework) provides a shareable cache for optimizing read operations, which leverages [informer-reflector-cache architecture](https://godoc.org/k8s.io/client-go/informers). **Informers** are set up to list and watch objects of interest from the kube-apiserver. **Reflector** reflects object changes to the underlying **Cache** and propagates out watched events to event handlers. Multiple components inside the same controller can register event handlers for OnCreate, OnUpdate, and OnDelete events from Informers and fetch objects from Cache instead of Kube-apiserver directly. Therefore, it reduces the chance of making unnecessary and redundant calls.

![](https://miro.medium.com/max/700/0*fC8_ET2XZJQvEkjz)

### Rate Limiting

Kubernetes API clients are usually shared among different controllers, and API calls are made from different threads. Kubernetes ships its API client along with a [token bucket rate limiter](https://en.wikipedia.org/wiki/Token_bucket) that supports configurable QPS and bursts. API calls that burst beyond threshold will be throttled so that a single controller will not jam the kube-apiserver bandwidth.

### Shared Cache

In addition to the kube-apiserver built-in cache that comes with the controller framework, we added another informer based write through cache layer in the platform API. This is to prevent unnecessary read calls hard hitting the kube-apiserver. The server side cache reuse also avoided thick clients in application code.

For kube-apiserver access **from applications**, we enforce all requests to go through the platform API to leverage shared care and assign security identity for access control and flow control. For kube-apiserver access from **workload controllers**, we enforce that all controllers implement based on control framework with rate limiting.

## Resilience

### Hardening Kubelet

One key reason why Kubernetes’ control plane entered cascading failure is that the legacy reflector implementation had **unbounded** retry when handling errors. Such imperfections can be exaggerated, especially when the API server is OOMKilled, which can easily cause a synchronization of reflectors across the cluster.

To resolve this issue, we worked very closely with the community by reporting [issues](https://github.com/kubernetes/kubernetes/issues/87794), discussing solutions, and finally getting PRs ([1](https://github.com/kubernetes/kubernetes/pull/87829), [2](https://github.com/kubernetes/kubernetes/pull/87795)) reviewed and merged. The idea is to add exponential backoff with jitter reflector’s ListWatch retry logic, so the kubelet and other controllers will not try to hammer the kube-apiserver upon kube-apiserver overload and request failures. This resilience improvement is useful in general, but we found it critical on the kubelet side as the number of nodes and pods increases in the Kubernetes cluster.

### Tuning Concurrent Requests

The more nodes we manage, the faster workloads are created and destroyed, and the larger the API call QPS server needs to handle. We first increased the maximum concurrent API call settings for both mutating and non-mutating operations based on estimated workloads. These two settings will enforce that the amount of API calls processed doesn’t exceed the configured number and therefore keeps CPU and memory consumption of kube-apiserver at a certain threshold.

Inside Kubernetes’s chain of API request handling, every request will pass a group of filters as the very first step. The filter chain is where max inflight API calls are enforced. For API calls burst to more than the configured threshold, a ‘too many requests” (429) response will be returned to clients to trigger proper retries. As future work, we plan to investigate more on [EventRateLimit features](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#eventratelimit) with more fine-grained admission control and provide better quality of services.

### Caching More Histories

Watch cache is a mechanism inside kube-apiserver that caches past events of each type of resource in a ring buffer in order to serve watch calls from a particular version with best effort. The larger the caches are, the more events can be retained in the server and are more likely to seamlessly serve event streams to clients in case of connection broken. Given this fact, we also improved the target RAM size of kube-apiserver, which internally is finally transferred to the watch cache capacity based on heuristics for serving more robust event streams. Kube-apiserver provides [more detailed ways](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/) to configure fine grained watch cache size, which can be further leveraged for specific caching requirements.

![](https://miro.medium.com/max/700/0*kIBn-GVvX_nQbLCS)

## Operability

### Observability

Aiming to reduce incident detection and mitigation time, we devote efforts continuously to improve observability of Kubernetes control planes. The challenge is to balance failure coverage and signal sensitivity. For existing Kubernetes metrics, we triage and pick important ones to monitor and/or alert so we can more proactively identify issues. In addition, we instrument kube-apiserver to cover more detailed areas in order to quickly narrow down the root cause. Finally, we tune alert statistics and thresholds to reduce noise and false alarms.

At a high level, we monitor kube-apiserver load by looking at QPS and concurrent requests, error rate, and request latency. We can breakdown the traffic by resource types, request verbs, and associated service accounts. For expensive traffic like listing, we also measure request payload by object counts and bytes size, since they can easily overload kube-apiserver even with small QPS. Lastly we monitor etcd watch events processing QPS and delayed processing count as important server performance indicators.

![](https://miro.medium.com/max/700/0*T7Rvvb--VHS0MKog)

### Debuggability

In order to better understand the Kubernetes control plane performance and resource consumption, we also built etcd data storage analysis tool using [boltdb](https://github.com/etcd-io/bbolt) library and [flamegraph](https://github.com/brendangregg/FlameGraph) to visualize data storage breakdown. The results of data storage analysis provide insights for platform users to optimize usage.

![](https://miro.medium.com/max/700/0*xOhDMF51YIh3g5aa)

In addition, we enabled golang profiling [pprof](https://blog.golang.org/pprof) and visualized heap memory footprint. We were able to quickly identify the most resource intensive code paths and request patterns, e.g. transforming response objects upon list resource calls. Another big caveat we found as part of kube-apiserver OOM investigation is that [page cache](https://www.kernel.org/doc/Documentation/cgroup-v1/memory.txt) used by kube-apiserver is counted towards a cgroup’s memory limit, and anonymous memory usage can steal page cache usage for the same cgroup. So even if kube-apiserver only has 20GB heap memory usage, the entire cgroup can see 200GB memory usage hitting the limit. While the current kernel default setting is not to proactively reclaim assigned pages for efficient re-use, we are currently looking at setup monitoring based on memory.stat file and force cgroup to reclaim as many pages reclaimed as possible if memory usage is approaching limit.

![](https://miro.medium.com/max/700/0*gj8_6QhwUjpIagms)

## Conclusion

With our governance, resilience, and operability efforts, we are able to significantly reduce sudden usage surges of compute resources, control plane bandwidth, and ensure the stability and performance of the whole platform. The kube-apiserver QPS (mostly read) is reduced by 90% after optimization rollout (as graph shown below), which makes kube-apiserver usage more stable, efficient, and robust. The deep knowledge of Kubernetes’ internals and additional insights we gained will enable the team to do a better job of system operation and cluster maintenance.

![](https://miro.medium.com/max/700/0*h_rpg23ZQ1mcU8EN)

Figure 9: Kube-apiserver QPS Reduction After Optimization Rollout

Here are some key takeaways that can hopefully help your next journey of solving Kubernetes scalability and reliability problem:

1.  Diagnose problems to get at their **root causes**. Focus on the “what is” before deciding “what to do about it.” The first step of solving problems is to understand what the bottleneck is and why. If you get to the root cause, you are halfway to the solution.
2.  It is almost always worthwhile to first look into **small incremental improvements** rather than immediately commit to radical architecture change. This is important, especially when you have a nimble team.
3.  Make **data-driven** decisions when you plan or prioritize the investigation and fixes. The right telemetry can help make better decisions on what to focus and optimize first.
4.  Critical infrastructure components should be designed with resilience in mind. Distributed systems are subject to failures, and it is best to **always prepare for the worst**. Correct guardrails can help prevent cascading failures and minimize the blast radius.

## Looking Forward

### Federation

As our scale grows steadily, single cluster architecture has become insufficient in supporting the increasing amount of workloads that try to onboard. After ensuring an efficient and robust single cluster environment, enabling our compute platform to scale horizontally is our next milestone moving forward. By leveraging a federation framework, we aim at plugging new clusters into the environment with minimum operation overhead while keeping the planform interface steady to end users. Our federated cluster environment is currently under development, and we look forward to the additional possibilities it opens up once productized.

### Capacity Planning

Our current approach of resource quota enforcement is a simplified and reactive way of capacity planning. As we onboard user workloads and system components, the platform dynamics change and project level or cluster wide capacity limit could be out of date. We want to explore proactive capacity planning with forecasting based on historical data, growth trajectory, and a sophisticated capacity model that can cover not only resource quota but also API quota. We expect more proactive and accurate capacity planning can prevent the platform from over-committing and under-delivering.

## Acknowledgements

Many engineers at Pinterest helped scale the Kubernetes platform to catch up with business growth. Besides the Cloud Runtime team — June Liu, Harry Zhang, Suli Xu, Ming Zong, and Quentin Miao who worked hard to achieve the scalable and stable compute platform as we have for today, Balaji Narayanan, Roberto Alcala and Rodrigo Menezes who lead our Site Reliability Engineering (SRE) effort, have worked together on ensuring the solid foundation of the compute platform. Kalim Moghul and Ryan Albrecht who lead the Capacity Engineering effort, have contributed to the project identity management and system level profiling. Cedric Staub and Jeremy Krach, who lead the Security Engineering effort, have maintained a high standard such that our workloads can run securely in a multi-tenanted platform. Lastly, our platform users Dinghang Yu, Karthik Anantha Padmanabhan, Petro Saviuk, Michael Benedict, Jasmine Qin, and many others, provided a lot of useful feedback, requirements, and worked with us to make the sustainable business growth happen.