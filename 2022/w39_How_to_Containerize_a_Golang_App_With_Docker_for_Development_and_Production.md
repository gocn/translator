- 原文地址：https://bartlomiejmika.com/posts/2022/how-to-containerize-a-golang-app-with-docker-for-development-and-production/
- 原文作者：**Bartlomiej Mika**
- 本文永久链接：
- 译者：[朱亚光](https://github.com/zhuyaguang)
- 校对：

# How to Containerize a Golang App With Docker for Development and Production

![Docker](https://bartlomiejmika.com/img/2022/07/ian-taylor-jOqJbvo1P9g-unsplash.jpg) Photo by [Ian Taylor](https://unsplash.com/@carrier_lost) on [Unsplash](https://unsplash.com/photos/jOqJbvo1P9g).

Do you want to write a **Golang** app which is containerized with **Docker**? The purpose of this article is to help you quickly get your Golang App containerized for **development** (with hot-reload) and **production** purposes.

## Before you begin

Please install [Docker Desktop](https://www.docker.com/get-started/) before proceeding any further. Once installed, start the desktop app and if it works you are ready to begin.

Also I am assuming you have a `$GOPATH` directory where you put your Golang source code you are working on. Mien will be: `~/go/src/github.com/bartmika`.

## … but if I am unfamiliar with Docker?

Don’t worry! Docker is a mature toolset which has been around long enough for there to be plenty of great educational resources to help you learn. I recommend the following as it helped me:

Checkout another article I wrote which will help you learn the basics:

-   [**Docker Learning Resources for Absolute Beginners Programming With Golang**](https://bartlomiejmika.com/post/2021/docker-learning-resources-for-absolute-beginners-programming-with-golang/)

## Golang and Docker for Development with Hot Reloading

In this section you’ll learn how to setup your Golang app for local development on your machine. The purpose of a development container is to hold all the dependencies (ex: Third-Party Packages like [GORM](https://gorm.io/index.html)), infrastructure (ex: Database, Memory Cache, etc) and your code in manner that assist and improves your development.

1. Create our app repo.

   ```shell
   mkdir mullberry-backend
   cd mullberry-backend
   go mod init github.com/bartmika/mullberry-backend
   ```

2. Every time you want to add a dependency you would shutdown the current running container and install the dependencies. Install our dependencies as follows:

   ```shell
   go get github.com/labstack/echo/v4
   go get github.com/labstack/echo/v4/middleware@v4.7.2
   ```

3. Hold on, you need to have Golang installed locally? What’s the point of the container then? [This Stackoverflow](https://stackoverflow.com/a/71297861) user explains it best in a discussion of setting up a `Dockerfile` for development purposes:

   > \[It\] is great for when you want to package your app into a container, ready for deployment. It’s not so good for development where you want to have the source outside the container and have the running container react to changes in the source.\*

   So in essence, if you are OK with this limitation then proceed onwards!

4. Create a `main.go` file in the root of your project then copy and paste the following into it:

   ```go
   package main
   
   import (
   "net/http"
   "os"
   
   "github.com/labstack/echo/v4"
   "github.com/labstack/echo/v4/middleware"
   )
   
   func main() {
   
   e := echo.New()
   
   e.Use(middleware.Logger())
   e.Use(middleware.Recover())
   
   e.GET("/", func(c echo.Context) error {
   return c.HTML(http.StatusOK, "Hello, Docker! <3")
   })
   
   e.GET("/ping", func(c echo.Context) error {
   return c.JSON(http.StatusOK, struct{ Status string }{Status: "OK"})
   })
   
   httpPort := os.Getenv("HTTP_PORT")
   if httpPort == "" {
   httpPort = "8080"
   }
   
   e.Logger.Fatal(e.Start(":" + httpPort))
   }
   ```

   Please note, the above code was copied from [“Build your Go image”](https://docs.docker.com/language/golang/build-images/) via their Docker Documentation.

5. Before creating anything docker related, create a `.dockerignore` file and copy and paste the following contents:

   ```shell
   bin
   .dockerignore
   Dockerfile
   docker-compose.yml
   dev.Dockerfile
   dev.docker-compose.yml
   .env
   ```

   What is a `.dockerignore` file? In essence it’s similar to `.gitignore` in which certain files / folders will not be saved to the docker container and image.

6. Create the `dev.Dockerfile` file and copy and paste the following contents into it.

   ```dockerfile
   FROM golang:1.18
   
   # Copy application data into image
   COPY . /go/src/bartmika/mullberry-backend
   WORKDIR /go/src/bartmika/mullberry-backend
   
   COPY go.mod ./
   COPY go.sum ./
   RUN go mod download
   
   # Copy only `.go` files, if you want all files to be copied then replace `with `COPY . .` for the code below.
   COPY *.go .
   
   # Install our third-party application for hot-reloading capability.
   RUN ["go", "get", "github.com/githubnemo/CompileDaemon"]
   RUN ["go", "install", "github.com/githubnemo/CompileDaemon"]
   
   ENTRYPOINT CompileDaemon -polling -log-prefix=false -build="go build ." -command="./mullberry-backend" -directory="./"
   ```

   If you read the comments above, you’ll notice the usage of [`CompileDaemon`](https://github.com/githubnemo/CompileDaemon), whats that? In essence this is your hot-reloader! It watches your `.go` files in a directory and invokes `go build` if a file changed. So for example, you open this project in `Atom` IDE, make a change to the `main.go` file and click _Save_, then [`CompileDaemon`](https://github.com/githubnemo/CompileDaemon) will rebuild your Go app in the container so you see the latest build!

7. Create our `dev.docker-compose.yml` file:

   ```yaml
   version: '3.6'
   
   services:
       api:
           container_name: mullberry-backend
           image: mullberry-backend
           ports:
               - 8000:8080
           volumes:
               - ./:/go/src/bartmika/mullberry-backend
   build:
           dockerfile: dev.Dockerfile
   ```

   Wait, why am I using the `dev.` prefix to these Docker file names? The reason why is because I want to distinguish the Docker files for either the **production** and **development** purposes.

8. In your terminal, start the development environment with the following command:

   ```shell
   $ docker-compose -f dev.docker-compose.yml up
   ```

9. Confirm we can access it.

   ```shell
   $ curl localhost:8000/
   ```

10. You should see the following output in your terminal:

    ```sh
    Hello, Docker! <3   
    ```

    If you see this, congratulations you are ready to start developing! If you’d like to learn more, feel free and checkout the [“Build your Go image”](https://docs.docker.com/language/golang/build-images/) article via their Docker Documentation.

## Golang and Docker for Production

The purpose of this section is to get your Golang app containerized and ready to be run in a production environment.

### Option 1: Single stage

The easiest setup is a _single stage build_. The problem with this build is that your Docker image will be _huge_!

To begin, create a `Dockerfile` in your project root folder and copy and paste the following into it:

```dockerfile
FROM golang:1.18

# Copy application data into image
COPY . /go/src/bartmika/mullberry-backend
WORKDIR /go/src/bartmika/mullberry-backend

COPY go.mod ./
COPY go.sum ./
RUN go mod download

# Copy only `.go` files, if you want all files to be copied then replace `with `COPY . .` for the code below.
COPY *.go .

# Build our application.
RUN go build -o ./bin/mullberry-backend


EXPOSE 8080

# Run the application.
CMD ["./bin/mullberry-backend"]
```

Then run `up` and you should see it working:

```shell
$ docker-compose up
```

### Option 2: Multi-stage

A more complicated setup called a _multi-stage build_ grants of disk space savings. The idea is you want to build your Golang app in one container and then move it into another more minimal container thus leaving behind the disk space heavy container.

If you want to give this a try, create a `Dockerfile` in your project root folder and copy and paste the following into it:

```dockerfile
##
## Build
##
FROM golang:1.18-alpine as dev-env

# Copy application data into image
COPY . /go/src/bartmika/mullberry-backend
WORKDIR /go/src/bartmika/mullberry-backend

COPY go.mod ./
COPY go.sum ./
RUN go mod download

# Copy only `.go` files, if you want all files to be copied then replace `with `COPY . .` for the code below.
COPY *.go .

# Build our application.
# RUN go build -o /go/src/bartmika/mullberry-backend/bin/mullberry-backend
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -gcflags "all=-N -l" -o /server

##
## Deploy
##
FROM alpine:latest
RUN mkdir /data

COPY --from=dev-env /server ./
CMD ["./server"]
```

Then run `up` and you should see it working:

```shell
$ docker-compose up
```

