# Go 🐿 应用程序安全和 AppSec 自动化变得简单

- [原文链接](https://awkwardferny.medium.com/go-application-security-and-appsec-automation-made-easy-36bd2f3d520b)
- 原文作者：Fernando Diaz
- [本文永久链接](https://github.com/gocn/translator/blob/master/static/images/2023/w03-Go-Application-Security-and-Appsec-Automation-Made-Easy/w03-Go-Application-Security-and-Appsec-Automation-Made-Easy.md)
- 译者：[司镜233](https://github.com/sijing233)
- 校对：

在云应用程序领域，Go是最流行的语言之一了，Kubernetes大部分的内容都是Go构建的。

但即便如此，根据[Nautilus2022云原生威胁报告](https://info.aquasec.com/cloud-native-threat-report-2022)表明：具有恶意的个人或组织，也增加了更多目标和方式，包括CI/CD的环境、容易收到攻击的Kubernets部署、应用程序。

随着时间的推移，针对Kubernets的攻击次数、攻击手段不断增加。根据[AquaSec]((https://www.aquasec.com/) )的观察显示：以Kubernets为目标的恶意攻击数量，从2020年的9%，增加到2021年的19%，增加了10%。这也说明，保护我们Golang应用程序的安全，越来越重要。

在这篇文章中，我将用不同的方法，扫描应用程序源代码的漏洞。以及，如何将安全扫描器，集成到GitLab等CI/CD平台中。我将提供一份我创建的，不安全的微服务的真实示例。





## 先决条件

- 基本了解Go编程语言
- Git基础知识
- 基本了解应用程序的安全性
- Gitlab账户（免费）
- Go 1.19+ 

```
$ go versiongo version go1.19.1 darwin/amd64
```



# 安全扫描器



在推送代码之前，或是将代码部署到生产级环境之前，运行安全扫描器，检测并修复漏洞。我将介绍如何用Go，使用各种不同的安全扫描器：[GoSec](](https://github.com/securego/gosec))、[GoVulnCheck](https://go.dev/blog/vuln)、[Fuzz](](https://go.dev/security/fuzz/))



首先，我们可以开始设置一个适当的GOPATH，添加GOPATH/bin到我们的PATH，并且git clone [不安全]((https://gitlab.com/awkwardferny/insecure-microservice))的微服务代码，可以在[此处](https://go.dev/doc/tutorial/compile-install)找到有关路径的详细信息。

```shell
# 设置合适的 GOPATH
$ export GOPATH=/path/to/your/go/projects

# 添加合适的 GOPATH bin 目录到你的 PATH
$ export PATH=$PATH:$GOPATH/bin

# 进入到你的 GOPATH
$ cd $GOPATH

# 创建正确的目录结构
$ mkdir -p src/gitlab.com/awkwardferny

# clone 我们用于测试扫描的应用程序
$ git clone git@gitlab.com:awkwardferny/insecure-microservice.git src/gitlab.com/awkwardferny/insecure-microservice

# 进入应用程序根目录
$ cd src/gitlab.com/awkwardferny/insecure-microservice
```

现在，我们已经正确设置了路径，并且已经clone了应用程序，我们可以开始运行我们的安全扫描器了。

# GoSec(源代码分析)

我们将介绍的第一个安全扫描器是[GoSec](https://github.com/securego/gosec)。它是一种流行的Go安全扫描器，可以扫描应用程序的源代码和依赖项，检查到漏洞。它通过将您的源代码与一组规则进行模式匹配来工作。

如果Go模块打开(e.g.`GO111MODULE=on`) ，或者明确下载依赖项(`go get -d`)，GoSec还可以自动扫描您的应用程序依赖项，来检查漏洞。现在，让我们在不安全的微服务上运行GoSec：

```shell
# 安装GoSec
$ go install github.com/securego/gosec/v2/cmd/gosec@latest

# 运行GoSec
$ gosec ./...
```

扫描运行后，我们可以查看发现的漏洞：

```shell
G404 (CWE-338): Use of weak random number generator (math/rand instead of crypto/rand) (Confidence: MEDIUM, Severity: HIGH) #使用弱随机数生成器(math/rand，而不是crypto/rand) (置信度：中等，严重性：高)
G114 (CWE): Use of net/http serve function that has no support for setting timeouts (Confidence: HIGH, Severity: MEDIUM) # 使用不支持设置超市的net/http服务功能（置信度：高，严重度：中）
G104 (CWE-703): Errors unhandled. (Confidence: HIGH, Severity: LOW)
G104 (CWE-703): Errors unhandled. (Confidence: HIGH, Severity: LOW)
G104 (CWE-703): Errors unhandled. (Confidence: HIGH, Severity: LOW)
G104 (CWE-703): Errors unhandled. (Confidence: HIGH, Severity: LOW)
```



这些漏洞表明我们的应用程序，有很多未捕获的异常：没有设置超时、使用了弱随机生成数。扫描返回规则出发、常见弱点枚举（CWE）、置信度、严重性和受影响的代码行。

在典型的开发人员工作流中，发现漏洞后，开发人员可以检查CWE，获取改进提示，对受影响的代码进行代码更改，然后重新运行扫描程序，以检查解决方案。应该运行回归测试，以确保我们的应用程序逻辑仍然健全。



# Govulncheck（源代码分析）

接下来是Govulncheck！Govulncheck是一个针对源代码，和应用程序依赖项的安全扫描器。Go安全团队正在积极开发它，并且在几个方面，与GoSec不同：

首先，它由[Go漏洞数据库]((https://vuln.go.dev/))支持。

其次，它只显示您的代码，实际调用的漏洞。这会减少“噪音”，并且让您知道哪些漏洞实际影响了您的应用程序。

下面是[Govulncheck]((https://go.dev/blog/vuln))的架构图，显示了它的*数据源、漏洞数据库、工具和集成。*



![img](../static/images/2023/w03-Go-Application-Security-and-Appsec-Automation-Made-Easy/image-20230111155421980.png)

现在，让我们试一试！

```
# 安装 govulncheck
$ go install golang.org/x/vuln/cmd/govulncheck@latest

# 运行 govulncheck
$ govulncheck ./...
```

After the scanner has run, let’s take a look at its findings:

```shell
Vulnerability #1: GO-2020-0016

An attacker can construct a series of bytes such that calling Reader. Read on the bytes could cause an infinite loop. If parsing user supplied input, this may be used as a denial of service vector.
# 攻击者可以构造一系列字节，以便调用 Reader。读取字节可能会导致无限循环。如果解析用户提供的输入，这可能会用作拒绝服务向量。

Call stacks in your code:
internal/logic/logic.go:63:8: gitlab.com/awkwardferny/insecure-microservice/internal/logic.insecure calls github.com/ulikunitz/xz.Reader.Read

Found in: github.com/ulikunitz/xz@v0.5.7
Fixed in: github.com/ulikunitz/xz@v0.5.8
More info: https://pkg.go.dev/vuln/GO-2020-0016
```



您可以看到扫描器，向我们提供了漏洞规则参考、说明、受影响的代码行、漏洞依赖项、解决方案以及附加信息的链接。因为我在我的应用程序中使用***github.com/ulikunitz/xz@v0.5.7作为*依赖*项并调用***xz.Reader.Read，所以我的应用程序容易受到[DDoS](https://www.cloudflare.com/learning/ddos/what-is-a-ddos-attack/)攻击。这个漏洞是由Go 漏洞数据库中的[GO-2020-016规则检测到的。](https://github.com/golang/vulndb/blob/master/data/reports/GO-2020-0016.yaml)

在典型的工作流程中，开发人员会更新依赖版本，然后重新运行扫描器以及*单元*和*功能*测试，以确保应用程序不会中断。



# Fuzz（模糊测试）

最后我们将进行模糊测试。模糊测试，是将随机格式**错误的数据**输入应用程序，看是否有安全的问题或错误的写法。Go 有一个名为[fuzz](https://go.dev/security/fuzz/)的本地模糊测试库。

[Fuzz](https://go.dev/security/fuzz/)执行***基于覆盖的***模糊测试，其编写类似于*单元测试*，并在应用程序功能上执行。他们擅长发现您在自己的*单元测试*中可能遗漏的边缘案例/错误。让我们看看下面这个模糊测试示例：

```go
func FuzzAdd(f *testing.F) {
  f.Add("1", "2")
  f.Fuzz(func(t *testing.T, a string, b string) {
    result, err := add(a, b)
    if err != nil {
      t.Errorf(fmt.Sprintf("error: %v", err))
    }    intA, _ := strconv.Atoi(a)
    intB, _ := strconv.Atoi(b)
    expected := intA + intB    if result != expected {
      t.Errorf(fmt.Sprintf("expected %v, got %v", expected, result))
    }
  })
}

func add(a string, b string) (c int, e error) {
  intA, err := strconv.Atoi(a)
  if err != nil {
    return 0, nil
  }  intB, err := strconv.Atoi(b)
  if err != nil {
    return 0, nil
  }  return (intA + intB), nil
}
```



我们可以看到 `FuzzAdd() `的编写类似于单元测试。我们通过添加`f.Fuzz(func(t \*testing.T, a string, b string)`来启用模糊测试，它调用`add( a string, b string )`函数，为变量`a`和`b`提供随机数据。然后，将它和预期值结果，进行比较。

`add()`函数，简单地将2 个字符串转换为整数，然后将它们相加并返回结果。

`FuzzAdd ()`测试可以使用[种子数据](https://go.dev/security/fuzz/#glos-seed-corpus)`f.Add("1", “2”),`正确运行，但是当存在格式错误或随机数据时会发生什么情况？让我们运行模糊测试并找出：

```
# 运行 fuzz 测试
$ go test ./internal/logic -fuzz FuzzAdd
```

我们可以看到扫描仪检测到一个错误：

```shell
--- FAIL: FuzzAdd (0.10s)
    --- FAIL: FuzzAdd (0.00s)
        logic_test.go:44: expected 1, got 0
    
    Failing input written to testdata/fuzz/FuzzAdd/9f4dc959af0a73c061c4b4185e9fdb9e5dbfc854cccce7bf9199f0f5556c42a9
    To re-run:
    go test -run=FuzzAdd/9f4dc959af0a73c061c4b4185e9fdb9e5dbfc854cccce7bf9199f0f5556c42a9
FAIL
```

导致这个错误，是因为传递了字母A，而不是可以转换为整数的字符串。Fuzz还在testdata目录下，生成了一个种子语料库，可以用来再次测试这个特定的故障。

解决这个问题的一个方式，是在add()函数中，简单地返回err，而不是nil。并期望在FuzzAdd()中，返回非整数可转换字符串的错误。

我们还可以考虑，仅将整数值设置为0，并记录错误。如下所示，这仅仅取决于，我们要实现的目标。

```go
func add(a string, b string) (c int, e error) {
  intA, err := strconv.Atoi(a)
  if err != nil {
    // change value to 0 if error is thrown
    intA = 0
    // TODO: Log the error (err)  
  }intB, err := strconv.Atoi(b)
  if err != nil {
    // change value to 0 if error is thrown
    intB = 0
    // TODO: Log the error (err)
  }  return (intA + intB), nil
}
```

有关模糊测试的更多高级用法，请查看 [Go模糊测试教程](https://go.dev/doc/tutorial/fuzz).





# 使用GitLab实现自动化扫描

如果可以自动运行安全扫描器来搜索Go应用程序中的漏洞，这样我们就可以在每次推送代码时，在功能分支上运行扫描器。

这会在代码投入生产之前，解决安全问题，并且不必在每次更改代码时，都手动运行扫描程序，从而节省了我们的时间。

这些扫描器，可以通过在GitLab中，创建CI/CD管道来实现自动化。管道可以在每次将代码推送到分支时，自动运行这些扫描。我们将查看[GitLab CI yaml](https://gitlab.com/awkwardferny/insecure-microservice/-/blob/master/.gitlab-ci.yml)，它在下面生成了一个CI/CD管道。



首先，我们看到的是，将按照提供的顺序，在管道中运行的阶段：

```
stages:
  - build
  - test
```

The **build** stage makes sure the application even builds before proceeding. If you’ve containerized your application, in this stage you would ideally also test if a container image can be built as well:

构建阶段，确保是在构建应用程序之前。如果您已经容器化了您的应用程序，那么在这个阶段，您最好也测试一下，是否可以构建容器镜像：

```
build:
  image: golang:alpine
  stage: build
  script:
    - go mod download
    - go build .
```

然后**测试阶段**，将运行*单元测试、模糊测试*，以及在本博客中描述的*安全扫描器*。还安装了运行这些流程的适当依赖项。

我们可以在**fuzz**下看到，我们有一个**artifact**指令，其中包含了一个在作业失败时，运行的**path**，这样做，是为了让我们可以[下载](https://docs.gitlab.com/ee/ci/pipelines/job_artifacts.html#download-job-artifacts) 种子语料库在本地运行：



```
unit:
  image: golang:alpine
  stage: test
  script:
    - apk update
    - apk add g++ git
    - go test -v ./...

gosec:
  image: golang:alpine
  stage: test
  script:
    - apk update
    - apk add g++ git
    - go install github.com/securego/gosec/v2/cmd/gosec@latest
    - gosec ./...

go-vuln-check:
  image: golang:alpine
  stage: test
  script:
    - apk update
    - apk add g++ git
    - go install golang.org/x/vuln/cmd/govulncheck@latest
    - govulncheck ./...

fuzz:
  image: golang:alpine
  stage: test
  script:
    - apk update
    - apk add g++ git
    - go test ./internal/logic -fuzz FuzzAdd -fuzztime 50s
  artifacts:
    paths:
      - internal/logic/testdata/*
    when: on_failure
```

[GitLab CI yaml](https://gitlab.com/awkwardferny/insecure-microservice/-/blob/master/.gitlab-ci.yml)中，描述的所有内容，生成以下的管道，我们可以在其中看到**fuzz、gosec、govulncheck**全部失败，表明我们的代码中，检测到漏洞和错误。

![img](../static/images/2023/w03-Go-Application-Security-and-Appsec-Automation-Made-Easy/1_2E0sq-gDjk5s1HoxlM740w.png)



如果点击一个测试，我们可以看到我们工作的输出。例如，当单机**govulncheck**作业时，我们会看到以下内容：



![img](../static/images/2023/w03-Go-Application-Security-and-Appsec-Automation-Made-Easy/1_5B2fV6vh8sdPPx1rb8wo4g.png)



这就是将单元测试、模糊测试和安全扫描器，集成到CI/CD管道中的方法。这让生活变的更轻松，并且无需每次都手动运行所有内容。

# 代码审查和安全编码实践

最后但同样重要的是，为了增强应用程序安全性，您应该始终执行*代码审查*。这很重要，因为其他人可以找到您可能遗漏的问题。扫描器可能会发现漏洞，但它们无法检测到不正确的逻辑。

[安全编码实践](https://github.com/OWASP/Go-SCP)由[开放 Web 应用程序安全项目 (OWASP](https://owasp.org/) ) 提供。应审查这些做法，以便在代码审查中提供有关增强安全性的重要反馈。

这些安全编码实践的一些示例包括[数据库安全](https://github.com/OWASP/Go-SCP/tree/master/src/database-security)、[输出编码](https://github.com/OWASP/Go-SCP/tree/master/src/output-encoding)、[错误处理和日志记录](https://github.com/OWASP/Go-SCP/blob/master/src/error-handling-logging/logging.md)等等。

# 其他注意事项

# **职责分离**

另一种减少不安全代码进入生产环境的方法是强制[职责*分离*](https://www.totem.tech/cmmc-separation-of-duties/#:~:text=Continuing with NIST definitions, separation,privilege to perpetrate damaging fraud.)。职责分离的意思是，开发人员只能访问其工作所必需的部分。这方面的一些例子是：

- 不允许开发人员合并他们自己的提交
- 如果发现漏洞，需要安全团队或团队领导的***批准\***
- 不允许开发人员禁用安全扫描
- 实现[CODEOWNERS](https://docs.gitlab.com/ee/user/project/code_owners.html)功能

# **其他攻击媒介**

应用程序的其他方面可能容易受到攻击，这些方面不是应用程序源代码的一部分。这方面的一些例子包括：

- 容器镜像
- 其他语言的应用依赖
- 限制性许可
- 正在运行的应用程序/服务器中的配置

这些项目可以通过*额外的安全扫描器*以及*实施安全策略*和*提供有关配置的审查*来修复。我在日常工作中使用 GitLab Ultimate 安全[策略](https://docs.gitlab.com/ee/user/application_security/policies/)和[扫描器](https://docs.gitlab.com/ee/user/application_security/configuration/#security-testing)

# **安全态势的可见性**

另一件需要考虑的事情是您对应用程序[*安全*](https://csrc.nist.gov/glossary/term/security_posture#:~:text=Definition(s)%3A,react as the situation changes.)状况的可见性。您应该了解哪些项目具有最令人担忧的漏洞以及针对这些漏洞正在采取的措施。



仪表板类型的视图将是理想的，这样您就可以有效地分类和管理漏洞，引导您找到应该首先解决的问题。

好了，Go 🐿 应用程序安全和 AppSec 自动化变得简单！感谢阅读，希望您喜欢这篇文章。

