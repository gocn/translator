- 原文地址：https://medium.com/wesionary-team/building-basic-event-scheduler-in-go-134c19f77f84
- 原文作者：Dipesh Dulal
- 本文永久链接：https://github.com/gocn/translator/blob/master/2021/
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[]()

## Building Basic Event Scheduler in Go
![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*gBs7tyig8N5eeHNMOwIG8w.png)

When we need to run a task after certain period of time, at a given time, on intervals etc, we need to use task scheduling system that is responsible for running tasks like; sending emails, push notifications, closing accounts at midnight, clearing tables etc.

In this story, we will build basic event scheduler that can schedule event to run after certain period of time using database as a persisting layer that will give us some understanding how event scheduling system might work. The basic working mechanism is that;

Whenever we need to schedule the event, the scheduled job is added to database to run at given time. Another task is always running periodically to check if some task has been expired from database and run the event if found expired in the database (polling).

![](https://miro.medium.com/max/1122/1*WVOKKAJBbWlmOL2dEgOCOQ.png)

Implementation Details

Let’s start by creating database schema (in postgresql) that we will use to store our events.

CREATE TABLE IF NOT EXISTS "public"."jobs" (     
   "id"      SERIAL PRIMARY KEY,     
   "name"    varchar(50) NOT NULL,     
   "payload" text,     
   "runAt"   TIMESTAMP NOT NULL    
)

Now, let’s define data structure for;

-   `Event` : That we schedule
-   `Listeners` : List of event listeners and
-   `ListenFunc:` The function to be called when event is fired.

Also define `Scheduler` struct that we will use to schedule events and run the listeners.

In line #8 to #13, we are creating new scheduler by passing `sql.DB` instance and initial listeners to the scheduler.

Now, we need to add schedule function implementation that will insert our event into `jobs` table which is shown below;

Here, in `AddListener` function we are simply assigning listener function to event name.

We have completed first part of puzzle adding to the job table. We now need to get the jobs that have been expired from the database, execute and then delete them.

The function implementation below shows how we can check for the expired events in the table and serializing the event into our `Event` struct.

Second part of the puzzle is calling the registered event listeners found from the database as shown below;

Here, we are checking if there is event function attached, and if found we are calling the event listener function. Line #6 to #9 deletes the job from database so that the listener is not found another time when polling the database.

Now, the final part is (polling) to check if some event has been expired in the given interval. For running tasks in interval we are using ticker function of `time` library that will give a channel which receives a new tick in provided interval.

In line #7 and #10, we are checking if context is closed or ticker channel is receiving the ticks. Upon receiving ticks in #11, we check for due events and then for all the events we call the listeners.

The next part is the actually use all the functions that we defined previously in `main.go` file as shown below;

In line #13 to #16, we are attaching event listeners to the event name `SendEmail` and `PayBills` so that, these functions will be called when new event has occurred.

In line #22 and #32 to #37, we are attaching interrupt channel with `os.Interrupt` and when interrupt occurs in the program we cancel the context provided in #19.

From line #26 to #30, we are defining event scheduler, running polling function and scheduling the event `SendEmail` to run after a minute and `PayBills` to run after two minute.

The output of the given program will look like;

From the output, we can see that the event `SendEmail` was triggered after a minute and event `PayBills` after second minute.

In this way, we built a basic event scheduling system that will schedule events after certain time interval. Full example for this code can be found at:
