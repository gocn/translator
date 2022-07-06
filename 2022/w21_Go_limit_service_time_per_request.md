# Go limit service time per request

In this problem, you are given a video processing service with a freemium tier. Everyone will be given 10 seconds of free processing time. If you are not a paying user, the service will kill your process after 10 seconds.

There are two variations for this problem. You can limit every 10 seconds for every request or limit 10 seconds for every user accumulated.

This article will discuss the first one, limiting every request to 10 seconds.

## Solution

![w21_01](../static/images/2022/w21_Go_limit_service_time_per_request/w21_Go_limit_service_time_per_request_01.png)



This implementation will block a request if a user is not premium after 10 seconds.

## Key takeaways

### How to time out code

You can use the following pattern when you need to limit how long operations take in Go.

```go
// This code is taken from the book 
// Learning Go by Jon Bodner.
func timeLimit() (int, error) {
    var result int
    var err error

    done := make(chan struct{})

    go func() {
        result, err = doSomeWork()
        close(done)
    }

    select {
        case <-done:
            return result, err
        case <-time.After(2 * time.Second):
            return 0, errors.New("Timed out")
    }
}

```

You will see many variations of the above pattern when you want to limit or time out code in Golang.

In this pattern, I use:

1. `time.After`  function that sends the current time to a channel after a specific duration has elapsed.

2. `select`  statement behavior, where it will block until one of its cases can run. And it will choose one at random if multiple cases can run.   

This is the pattern I utilize to solve this problem. The only difference is that I wrap the select block inside a for loop, which I will explain later.

### Goroutine are not actually being killed with this time our pattern

If you exit `timeLimit` before the goroutine finishes processing, the goroutine continues to run. You just choose not to do anything with the result that it (eventually) returns.

If you want to stop work in a goroutine that you are no longer wish to wait for its completion, use context cancellation. But that will be the topic of another article.

### Select statement behavior

The `select` statement lets a goroutine wait on several communication operations. A `select` statement without a `default` statement blocks until one of its cases can run.

In this problem, you need to wrap the `select` statement inside a for-loop because once you receive a message from the timer, you might need to wait for the process to finish.

```go
func HandleRequest(process func(), u *User) bool {
    ...
    for {
        select {
            case <-done:
                return true
            case <-time.After(time.Second * 10):
                if !u.IsPremium {
                    return false
                }
        }
    }
    ...
```

When `time.After` sends a message to the channel, you need to check if the user is premium or not. If the user is premium, you need to continue the process until it is finished. By putting the select statement inside a for-loop, you execute the `select` statement once again and wait until the `done` channel has been written before the function returns.