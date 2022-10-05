# How To Create a Go Private Module With Docker

- 原文地址：https://medium.com/the-godev-corner/how-to-create-a-go-private-module-with-docker-b705e4d195c4
- 原文作者：Marvin Collins
- 本文永久链接：https:/github.com/gocn/translator/blob/master/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker.md
- 译者：[cvley](https://github.com/cvley)
- 校对：[]()

![](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_1.png)

## Introduction

Since the introduction of modules in Go 1.11, Go application dependency management has improved dramatically. We’ve seen fetching a module become easier with **GOPROXY,** better support for authentication requests, streamlined dependency versioning, and more.

But if you wanted to create your own module, where would you start?

The good news is that relatively speaking, public packages aren’t that much more difficult to create than private ones, and vice versa. But they are a bit _different._

> _👉_ Note: I’ll be using the terms Go package and Go module interchangeably throughout this article

Nevertheless, working with private Go module distributions on private platforms such as bitbucket, Gitlab, or Github is an invaluable skill to have whether you’re creating a personal project or want to keep proprietary logic “in-house.” So I figured it would be worthwhile to guide a few people through it.

As an added bonus, I’ll also be showing you how to develop a Go application using a Docker image — so buckle up, sit tight, and let’s get started.

## Short Preface

### By the end of this article, you’ll be able to:

\[Feel free to skip ahead to a specific section\]

1.  [Create a GitHub private repository](https://medium.com/the-godev-corner/how-to-create-a-go-private-module-with-docker-b705e4d195c4#2f67) (for your Go private module)
2.  [Setup and configure](https://medium.com/the-godev-corner/how-to-create-a-go-private-module-with-docker-b705e4d195c4#1a36) your Go private module
3.  [Use it locally and with Docker](https://medium.com/the-godev-corner/how-to-create-a-go-private-module-with-docker-b705e4d195c4#58d4)
4.  [Set authentication credentials](https://medium.com/the-godev-corner/how-to-create-a-go-private-module-with-docker-b705e4d195c4#21c3) for it
5.  [Establish a secure connection](https://medium.com/the-godev-corner/how-to-create-a-go-private-module-with-docker-b705e4d195c4#ee25) (using SSH) for it
6.  [Configure Docker](https://medium.com/the-godev-corner/how-to-create-a-go-private-module-with-docker-b705e4d195c4#d053) (and securely download it)
7.  And [build application Docker images](https://medium.com/the-godev-corner/how-to-create-a-go-private-module-with-docker-b705e4d195c4#d846) for it

### Prerequisites

- Go module knowledge  
  (Note: if you’re new to Go modules, I recommend you start with the [official documentation](https://github.com/golang/go/wiki/Modules#go-111-modules))
- Go 1.16+ installed
- Familiarity with Git

## Getting Started

First, we will create a GitHub private repository for a Go private module.

> \[To simply read along, feel free to jump to [this section](https://medium.com/the-godev-corner/how-to-create-a-go-private-module-with-docker-b705e4d195c4#1a36)\]

### Download sample project codebase

There is no need to write a sample Go module from scratch. So, feel free to head to the GitHub repository listed below and download the zip file of the project; yes, you read that correctly — no need to clone the repository, just download the zip file.

[### GitHub - marvinhosea/filter: Article Repo](https://github.com/marvinhosea/filter)

Click the code on the repository page to see a dropdown similar to this one. Go right ahead and click Download zip to download the codebase

![Two step visual process to download the required codebase](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_2.png)

Once the download is complete, extract the zip file to a folder. Before committing the codebase to a private GitHub repository, we must make one change. Open the extracted folder in your preferred IDE and edit the **go. mod** file to match your module name by replacing the username with your GitHub username, as shown below.

```golang
module github.com/username/go-filter

go 1.19

require golang.org/x/exp v0.0.0-20220722155223-a9213eeb770e // indirect
```

### Create GitHub private repository

We consider our private Github repository to be a private Go module distribution. So go to GitHub and create a new private repository, as shown below:

![Visual image of creating a new private repository within GitHub](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_3.png)

Creating a new private repository

Next, you’ll want to add our Go module files to the create newly created Github private repository.

- In the Go module project root directory, run the command below to git init the directory:

```
git init
```

> _👉_ We git add the files after git initializing the project; because we have git ignore already configured, there is nothing to worry about when running git add. Everything is shown below:

```
git add --all
```

- Now, if you look at the code base, you’ll notice that we have a simple test. Let’s run it before we commit our code to ensure that everything is working properly:

```
go test -v -cover ./...
```

- If done successfully, you should see something like this:

![Code showing the initial test being run in your Go private module](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_4.png)

Running the recommended test in your Go private module

- Now that the package is functioning properly, let’s add our git commit message:

> _👉_ Feel free to create your own

```
git commit -m 'first commit'
```

- Let’s now add our remote origin to the project:

```
git remote add origin git@github.com:username/private-filter.git
```

- Finally, run the command below to push our project to the remote repository:

```
git push -u origin main
```

If you refresh the project repository page on GitHub, you should see that the above command successfully transferred the code base and files from the local repository to the remote repository. That was all we needed.

## Working with Go private module

Go modules allow developers to add and manage dependencies, but private Go module distribution does not work out of the box; we must do some additional configuration to both Go and our setup.

After the changes, getting Go module dependencies will be similar to getting Go public modules with **go get** command. This will download Go modules from the public distribution mirrored at [proxy.golang.org](http://www.proxy.golang.org).

### Go private environment variable configuration

Because we’re working with Go modules, make sure **GO111MODULE** is enabled; if it isn’t, run this command:

```
export GO111MODULE=on
```

> _👉_ The location of the Go private modules distribution must be specified, which is the private Github repository in our case.

The environmental variable **GOPRIVATE** enables us to distribute Go private modules, and we can use this command to set the **GOPRIVATE** values:

```
go env -w GOPRIVATE=github.com/username/*
```

To set a Go environment variable, use **go env -w**. The preceding command informs Go of modules distribution source other than the Go public packages distribution. **github.com/username/\*** corresponds to your organization’s or personal private Go module distribution, which can also be Gitlab, Bitbucket, or other similar services.

> But what if we have multiple private modules?

In that case, we can use a comma to separate the module’s distribution source, as shown below.

```
go env -w GOPRIVATE=github.com/username/*,gitlab.com/username/*
```

> _👉_ We include the asterisk to allow any Go module in the distribution url.

We can also add the **GOPRIVATE** environment variable directly in the bashrc or zshrc file, but I’ll leave that to you to investigate further, or simply run the instructions below to add the **GOPRIVATE** environment variable.

```
export GOPRIVATE=github.com/username/*
```

> 👉 Setting GOPRIVATE does not interfere with the distribution of Go public modules.

To confirm that **GOPRIVATE** environment variable is set, run this command:

```
env | grep GOPRIVATE
```

And the output should be something similar to this:

```
GOPRIVATE=github.com/username/*
```

That’s all we need to do in Go to work with Go private modules. Let’s do the necessary configuration to allow Go tools to download Go private modules from private distribution.

### Setting credentials and Go private module access

In this section, we’ll look at how to use Go private modules locally and with Docker. To start, let’s go get our Go private module:

-   Navigate to your development directory and create a simple Go application. In my case, I’ll call it **go-private-example:**

```
mkdir go-private-example && cd go-private-example
```

> _👉_ The command above creates an empty directory and then navigates to that directory

-   Now, let’s add the go module to our simple Go application via our project’s root directory:

```
go mod init github.com/username/go-private-example
```

> _👉_ The preceding will generate a **go.mod** file that will track our dependencies.

- Next, within the root directory, create a **main.go** file and paste the content below into it:

```golang

package main

import "fmt"

func main(){
	fmt.Println("Go private module Example")
}
```

- Now that we have the package main and the main function, which concurrently serve as the entry point to our example program, let’s open the terminal and use **go get** to download our private Go module:

```
go get github.com/username/go-filter
```

If you run the instruction in your terminal, you’ll get the output below \[Go 1.19\]:

![Visual code depicting how to download the go private module using go get](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_5.png)

Using go get to download the private Go module

> _👉_ The error indicates that the Go tool attempted to access the Go private module but was unable to download it due to access denial, as we had not yet set the authentication credentials.

Let’s see what we can do next to solve this issue:

## Providing credentials

At this point, there’s a fork in the road and you could go one of two ways: use the ssh method (which is simpler and preferred) or use the .netrc method.

We’ll look at both just in case you’re interested, but we’ll start with using ssh.

> _💡_ Even if you have both options configured (i.e., ssh and .netrc), you will still be able to download private Go modules without issue.

### Using ssh

Git provides a global configuration file with an option called **insteadOf**, which tells git which URL to use instead of the default HTTPS URL. For example, instead of “[https://github.com/](https://github.com/)," use “ssh://[git@github.com](mailto:git@github.com)/.”

> _💡_When you have ssh configured and linked to your private Go module distribution, you’ll have a more secure connection.

Let’s configure our system to use ssh rather than HTTPS:

-   Navigate to the user’s home directory (**$HOME)**, open the **.gitconfig** file, and add this content at the end of the line:

```
...[url "ssh://git@github.com/"]   insteadOf = https://github.com/
```

This instructs git to use the ssh URL rather than the HTTPS URL.

> _👉_ This also works with Gitlab, Bitbucket, etc.

### Using .netrc file

> _💡_The **.netrc** file is located in the user’s home directory and is used to store credentials required for login without manual input. More information can be found [here](https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html).
> 
> Also, this method involves potentially leaving unencrypted credential on disk, so please proceed with caution

To begin, let’s navigate to the home directory (**$HOME)** and check if **the .netrc** file is available within the directory:

```
ls .netrc
```

- If the file is not available you will get the error below. Otherwise please skip this part and continue from the part where we add the file content.

```
No such file or directory
```

- Go ahead and create the file if it is not available by running:

```
touch .netrc
```

- As shown below, grant it permission 600:

```
sudo chmod 600 .netrc
```

- Now open the file, add the following content to the end, and close it:

```
machine github.com login username password accesstoken
```

Replace the **username** in the preceding line with your GitHub username, then generate your personal access token and replace it with the **accesstoken** in the preceding line. You can make a new access token [here](https://github.com/settings/tokens), assign only relevant scope to it, and then copy it.

> _💡_ Make sure to check the relevant scopes when creating the token. Keep your security in mind in case your token is compromised. And do not use your account password.

> What about Gitlab?

Just replace github.com URL with gitlab.com or bitbucket.com URL or other repository services.

Now, let’s try getting our Go private module one more time by repeating the following instructions:

```
go get github.com/username/go-filter
```

The output will be similar to this one:

![Visual code explaining how to get the Go private module](../static/images/2022/w42_How_To_Create_a_Go_Private_Module_With_Docker/go_private_module_with_docker_6.png)

Getting our Go private module one more time

As you can see, our package was downloaded and added to our project. To confirm, open the project in your preferred IDE and open the **go.mod** file. This is what the content should look like:

```golang
module github.com/username/go-private-example

go 1.19

require (
	github.com/username/go-filter v0.0.0-20220920084832-2774b2100989 // indirect
	golang.org/x/exp v0.0.0-20220916125017-b168a2c6b86b // indirect
)
```

This means that our Go private module has been added as a dependency, and we can now use it in our sample program with ease. Let’s update our program **main.go** file by copying the content below and replacing it with the previously added content:

```golang
package main

import (
	"fmt"
	"github.com/username/go-filter"
)

func main() {
	fmt.Println("Go private module Example")

	intArray1 := []int{1, 2, 3, 4, 5, 5}
	intArray2 := []int{0, 9, 45, 5}
	result := filter.Filter(intArray1, intArray2)
	fmt.Println(result)
}
```

Essentially, in the above program, we are passing two integer arrays to our private Go module’s filter function, which will combine the two arrays and filter out duplicate values. And if we run the program now, we will get the following result:

```
Go private module Example[1 2 3 4 5 0 9 45]marvinhosea8
```

> _👉_ This demonstrates that everything is operating as expected.

## What about Docker?

Ultimately, you will need to create a Docker image at some point. And to do so, we’ll look at how to configure Docker and the Docker-compose file to securely download our private Go module.

-   In our example project, create a Docker file by running this command:

```
touch Dockerfile
```

-   After you’ve created the Dockerfile, add the following content to it:

```
## Build
FROM golang:1.19-alpine AS build

LABEL maintainer="Marvin Hosea"

RUN apk add --no-cache git ca-certificates

ARG GITHUB_TOKEN
ENV CGO_ENABLED=0 GO111MODULE=on GOOS=linux TOKEN=$GITHUB_TOKEN

RUN go env -w GOPRIVATE=github.com/marvinhosea/*
## Or you could use ENV GOPRIVATE=github.com/username

RUN git config --global url."https://${TOKEN}:x-oauth-basic@github.com/".insteadOf "https://github.com/"
# Gitlab
# RUN git config  --global url."https://oauth2:${TOKEN}@gitlab.com".insteadOf "https://gitlab.com"


WORKDIR /app

COPY go.mod ./
COPY go.sum ./
RUN go mod download

COPY . .

RUN go build -installsuffix cgo -ldflags '-s -w' -o main ./...

## Deploy
FROM scratch as final

COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=build /app .

ENTRYPOINT ["./main"]
```

> _☝️_Because Docker is outside the scope of this article, I will only explain specific parts of the Dockerfile. Lines 8 and 9 are shown below:

```
ARG GITHUB_TOKENENV CGO_ENABLED=0 GO111MODULE=on GOOS=linux TOKEN=$GITHUB_TOKEN
```

We are defining an argument that will accept a value during the Docker image build.

> _💡_Due to security concerns, the argument is set dynamically. I cannot emphasize enough that your secret and tokens **should not** be hard coded in your Dockerfile.

We then pass the **GITHUB\_TOKEN** docker argument once we receive the **GITHUB\_TOKEN** environment variable value which is our Personal Access Token:

```
RUN go env -w GOPRIVATE=github.com/username/*
```

As previously stated, this command on line 11 will set the Go **GOPRIVATE** environment variable:

```
RUN git config --global url."https://${TOKEN}:x-oauth-basic@github.com/".insteadOf "https://github.com/"
```

Line 14 specifies how we will download our private Go modules and retrieve the environment variable using the Personal Access Token passed as **TOKEN**:

Before we begin, let’s create a **.env** file for our project.

- In the project root, create the **.env** file and add the following content:

```
GITHUB_USERNAME=username
GITHUB_TOKEN=PersonalAccessToken
```

After we’ve finished with the **.env**, let’s build our application Docker image by running the command below:

```
export $(egrep -v ‘^#’ .env | xargs) && docker build --build-arg GITHUB_TOKEN=${GITHUB_TOKEN} -t go-private-example .
```

On the above commands, we grab the values from our **.env** file and export them as environment variables with their values. Then we run Docker build to build the Docker image with arguments from the environment variables passed from the **.env** file.

After building the image we can run the Docker image by running this command:

```
docker run go-private-example
```

And the output should be as shown below:

```
Go private module Example [1 2 3 4 5 0 9 45]
```

### Using docker-compose

Create a **docker-compose.yml** file in the project’s root directory and fill it with the content:

```
services:
  app:
    container_name: go-private-example
    env_file:
      - .env
    build:
      dockerfile: Dockerfile
      args:
        - GITHUB_TOKEN=GITHUB_TOKEN
    image: go-private-example

    # other configuration
```

The docker-compose file is nearly identical to our Docker run instruction. Pass the environment file using the **env\_file** flag, and execute the docker-compose command as shown below:

```
docker compose up
```

The output should resemble this:

```
[+] Running 1/0
 ⠿ go-private-example  Warning: No resource found to remove
0.0s
[+] Running 2/2
 ⠿ Network go-private-example_default  Created
0.1s
 ⠿ Container go-private-example        Created
0.1s
Attaching to go-private-example
go-private-example  | Go private module Example
go-private-example  | [1 2 3 4 5 0 9 45]
go-private-example exited with code 0
```

Now you’ve got your own working Go private module!

## Conclusion

In this article, we looked at working with and publishing Go private modules. We also discussed how to configure our setup to download Go private modules with credentials and how to use private Go modules when building application Docker images.

> _💡_ I just want to reiterate — you should be cautious when configuring and using your Go private module distribution credentials to avoid exposing them, which is why they are labeled private.

In another upcoming article, I will discuss how to get started with Go module development. If you’re unfamiliar with Go module development or would like a quick, fun read, head on over when you have a chance.

I hope you’ve enjoyed this short tutorial. If you’d like to read more like this, please hit the 👏 icon below, or tell me in the comments how I can improve articles like this in the future.

## Reference

The article code base repositories are listed below:

[### GitHub — marvinhosea/go-private-example](https://github.com/marvinhosea/go-private-example)

[### GitHub — marvinhosea/filter: Article Repo](https://github.com/marvinhosea/filter)

_Disclosure: In accordance with Medium.com’s rules and guidelines, I publicly acknowledge financial compensation from_ [_UniDoc_](http://www.unidoc.io) _for this article. All thoughts, opinions, code, pictures, writing, etc. are those of my own._
