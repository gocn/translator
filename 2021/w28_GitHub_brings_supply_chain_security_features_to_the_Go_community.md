# GitHub brings supply chain security features to the Go community

* 原文地址：https://github.blog/2021-07-22-github-supply-chain-security-features-go-community/
* 原文作者：[William Bartholomew](https://github.blog/author/iamwillbar/)
* 本文永久链接：https://github.com/gocn/translator/blob/master/2021/w27_scaling_k8s_with_assurance_at_pinterest_introduction.md

- 译者：[朱亚光](https://github.com/zhuyaguang)
- 校对：

The global Go community embraced GitHub from the beginning—both as a place to collaborate on code and a place to publish packages—leading to Go becoming one of the top 15 programming languages on GitHub today. We’re excited to announce that GitHub’s supply chain security features are now available for Go modules, which will help the Go community discover, report, and prevent security vulnerabilities.

> _Go was created, in part, to address the problem of managing dependencies in large-scale software. GitHub is the most popular host for open-source Go modules. The features announced today will help not just GitHub users but anyone who depends on GitHub-hosted modules. We are thrilled that GitHub is investing in improvements that benefit the entire Go ecosystem, and we look forward to more collaborations with them in the future._
> 
> – Steve Francia, Product Lead: Go Language @ Google

Go modules were introduced in 2019 to make dependency management easier and version information more explicit, and according to the [Go Developer Survey 2020](https://blog.golang.org/survey2020-results) have gained near-universal adoption. Below, I’ll walk you through how each of GitHub’s supply chain security features works with Go modules to improve security for the Go community.

## [Advisories](https://github.blog/2021-07-22-github-supply-chain-security-features-go-community/#advisories)

GitHub’s Advisory Database is an open database of security advisories focused on high quality, actionable vulnerability information for developers. It’s licensed under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/), so the data can be used anywhere.

So far, we’ve published [over 150 existing Go advisories](https://github.com/advisories?query=ecosystem%3Ago), and this number is growing every day as we curate existing vulnerabilities and triage newly discovered ones.

![Screenshot of advisory database](https://github.blog/wp-content/uploads/2021/07/GitHub-Supply-Chain-Security_fig-1-Advisory-Database.png?w=1024&resize=1024%2C458)

If you’re a Go module maintainer, you can use Security Advisories for coordinated disclosure of vulnerabilities. You can collaborate with vulnerability reporters, such as security researchers, to privately discuss and fix vulnerabilities before announcing them publicly. Security Advisories also make it easy for you to request a [Common Vulnerabilities and Exposures](https://cve.mitre.org/) (CVE) identification number for your advisories and to publish them to the [National Vulnerability Database](https://nvd.nist.gov/) (NVD).

![Screenshot of user requesting CVE](https://github.blog/wp-content/uploads/2021/07/GitHub-Supply-Chain-Security_fig-2-CVE-request.png?w=1024&resize=1024%2C518)

## [Dependency graph](https://github.blog/2021-07-22-github-supply-chain-security-features-go-community/#dependency-graph)

GitHub’s dependency graph analyzes a repository’s `go.mod` files to understand the repository’s dependencies. Along with security advisories, the dependency graph provides the information needed to alert developers to vulnerable dependencies. To view a repository’s detected dependencies, select the repository’s **Insights** tab, then select **Dependency graph** from the sidebar on the left.

![Screenshot of GitHub UI with Dependency graph selected](https://github.blog/wp-content/uploads/2021/07/GitHub-Supply-Chain-Security_fig-3-dependency-graph.png?w=1024&resize=1024%2C378)

The dependency graph is enabled by default for public repositories, but you must enable it [for private repositories](https://docs.github.com/en/code-security/getting-started/securing-your-repository#managing-the-dependency-graph). If the dependency graph for your public repository hasn’t already been populated, it will be soon. If you can’t wait you can trigger the update by pushing a change to your `go.mod` file.

To help prevent new vulnerabilities from being introduced, you can use [dependency review](https://docs.github.com/en/github/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/reviewing-dependency-changes-in-a-pull-request#about-dependency-review) to see the impact of changes to your `go.mod` files when reviewing pull requests.

![Screenshot of dependency review](https://github.blog/wp-content/uploads/2021/07/GitHub-Supply-Chain-Security_fig-4-dependency-review.png?w=1024&resize=1024%2C357)

## [Dependabot alerts](https://github.blog/2021-07-22-github-supply-chain-security-features-go-community/#dependabot-alerts)

Dependabot alerts notify you when new vulnerabilities are discovered in Go modules you’re already using. You can use our [new notification configuration](https://docs.github.com/en/code-security/supply-chain-security/managing-vulnerabilities-in-your-projects-dependencies/configuring-notifications-for-vulnerable-dependencies) to fine-tune which notifications you receive.

![Screenshot of a Dependabot alert](https://github.blog/wp-content/uploads/2021/07/GitHub-Supply-Chain-Security_fig-5-Dependabot-alerts.png?w=1024&resize=1024%2C297)

## [Dependabot security updates](https://github.blog/2021-07-22-github-supply-chain-security-features-go-community/#dependabot-security-updates)

What’s better than being alerted to a vulnerable dependency? Getting a pull request that automatically upgrades your vulnerable Go modules to a version without the vulnerability! That’s exactly what Dependabot security updates do.

We’ve found that repositories that automatically generate pull requests to update vulnerable dependencies patch their software [40% faster](https://octoverse.github.com/static/github-octoverse-2020-security-report.pdf) than those who don’t.

![Screenshot of an automated Dependabot pull request for a security update](https://github.blog/wp-content/uploads/2021/07/GitHub-Go-Supply-Chain-Security_fig-6-Dependabot-updates.png?w=1024&resize=1024%2C637)

## [Get started and learn more](https://github.blog/2021-07-22-github-supply-chain-security-features-go-community/#get-started-and-learn-more)

Get started today by [securing your Go repository](https://docs.github.com/en/code-security/getting-started/securing-your-repository), or learn more about each of GitHub’s supply chain security features:

-   [Security advisories](https://docs.github.com/en/code-security/security-advisories/about-github-security-advisories)
-   [Dependency graph](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph)
-   [Dependabot alerts](https://docs.github.com/en/code-security/supply-chain-security/managing-vulnerabilities-in-your-projects-dependencies/about-alerts-for-vulnerable-dependencies)
-   [Dependabot security updates](https://docs.github.com/en/code-security/supply-chain-security/managing-vulnerabilities-in-your-projects-dependencies/about-dependabot-security-updates)