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

![Implementation Details](https://miro.medium.com/max/1122/1*WVOKKAJBbWlmOL2dEgOCOQ.png)



Let’s start by creating database schema (in postgresql) that we will use to store our events.

```sql
CREATE TABLE IF NOT EXISTS "public"."jobs" (     
   "id"      SERIAL PRIMARY KEY,     
   "name"    varchar(50) NOT NULL,     
   "payload" text,     
   "runAt"   TIMESTAMP NOT NULL    
)
```

Now, let’s define data structure for;

-   `Event` : 调度事件
-   `Listeners` : 事件监听器列表
-   `ListenFunc:` 触发事件时调用的函数

```go
// Listeners has attached event listeners
type Listeners map[string]ListenFunc

// ListenFunc function that listens to events
type ListenFunc func(string)

// Event structure
type Event struct {
	ID      uint
	Name    string
	Payload string
}
```

Also define `Scheduler` struct that we will use to schedule events and run the listeners.
```go
// Scheduler data structure
type Scheduler struct {
	db        *sql.DB
	listeners Listeners
}

// NewScheduler creates a new scheduler
func NewScheduler(db *sql.DB, listeners Listeners) Scheduler {
	return Scheduler{
		db:        db,
		listeners: listeners,
	}
}
```

In line #8 to #13, we are creating new scheduler by passing `sql.DB` instance and initial listeners to the scheduler.

Now, we need to add schedule function implementation that will insert our event into `jobs` table which is shown below;
```go
// Schedule sechedules the provided events
func (s Scheduler) Schedule(event string, payload string, runAt time.Time) {
	log.Print("🚀 Scheduling event ", event, " to run at ", runAt)
	_, err := s.db.Exec(`INSERT INTO "public"."jobs" ("name", "payload", "runAt") VALUES ($1, $2, $3)`, event, payload, runAt)
	if err != nil {
		log.Print("schedule insert error: ", err)
	}
}

// AddListener adds the listener function to Listeners
func (s Scheduler) AddListener(event string, listenFunc ListenFunc) {
	s.listeners[event] = listenFunc
}
```

Here, in `AddListener` function we are simply assigning listener function to event name.

We have completed first part of puzzle adding to the job table. We now need to get the jobs that have been expired from the database, execute and then delete them.

The function implementation below shows how we can check for the expired events in the table and serializing the event into our `Event` struct.
```go
// checkDueEvents checks and returns due events
func (s Scheduler) checkDueEvents() []Event {
	events := []Event{}
	rows, err := s.db.Query(`SELECT "id", "name", "payload" FROM "public"."jobs" WHERE "runAt" < $1`, time.Now())
	if err != nil {
		log.Print("💀 error: ", err)
		return nil
	}
	for rows.Next() {
		evt := Event{}
		rows.Scan(&evt.ID, &evt.Name, &evt.Payload)
		events = append(events, evt)
	}
	return events
}
```

Second part of the puzzle is calling the registered event listeners found from the database as shown below;
```go
// callListeners calls the event listener of provided event
func (s Scheduler) callListeners(event Event) {
	eventFn, ok := s.listeners[event.Name]
	if ok {
		go eventFn(event.Payload)
		_, err := s.db.Exec(`DELETE FROM "public"."jobs" WHERE "id" = $1`, event.ID)
		if err != nil {
			log.Print("💀 error: ", err)
		}
	} else {
		log.Print("💀 error: couldn't find event listeners attached to ", event.Name)
	}

}
```

Here, we are checking if there is event function attached, and if found we are calling the event listener function. Line #6 to #9 deletes the job from database so that the listener is not found another time when polling the database.

Now, the final part is (polling) to check if some event has been expired in the given interval. For running tasks in interval we are using ticker function of `time` library that will give a channel which receives a new tick in provided interval.
```go
// CheckEventsInInterval checks the event in given interval
func (s Scheduler) CheckEventsInInterval(ctx context.Context, duration time.Duration) {
	ticker := time.NewTicker(duration)
	go func() {
		for {
			select {
			case <-ctx.Done():
				ticker.Stop()
				return
			case <-ticker.C:
				log.Println("⏰ Ticks Received...")
				events := s.checkDueEvents()
				for _, e := range events {
					s.callListeners(e)
				}
			}

		}
	}()
}
```

In line #7 and #10, we are checking if context is closed or ticker channel is receiving the ticks. Upon receiving ticks in #11, we check for due events and then for all the events we call the listeners.

The next part is the actually use all the functions that we defined previously in `main.go` file as shown below;
```go
package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"time"

	"github.com/dipeshdulal/event-scheduling/customevents"
)

var eventListeners = Listeners{
	"SendEmail": customevents.SendEmail,
	"PayBills":  customevents.PayBills,
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())

	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)

	db := initDBConnection()

	scheduler := NewScheduler(db, eventListeners)
	scheduler.CheckEventsInInterval(ctx, time.Minute)

	scheduler.Schedule("SendEmail", "mail: nilkantha.dipesh@gmail.com", time.Now().Add(1*time.Minute))
	scheduler.Schedule("PayBills", "paybills: $4,000 bill", time.Now().Add(2*time.Minute))

	go func() {
		for range interrupt {
			log.Println("\n❌ Interrupt received closing...")
			cancel()
		}
	}()

	<-ctx.Done()
}
```

In line #13 to #16, we are attaching event listeners to the event name `SendEmail` and `PayBills` so that, these functions will be called when new event has occurred.

In line #22 and #32 to #37, we are attaching interrupt channel with `os.Interrupt` and when interrupt occurs in the program we cancel the context provided in #19.

From line #26 to #30, we are defining event scheduler, running polling function and scheduling the event `SendEmail` to run after a minute and `PayBills` to run after two minute.

The output of the given program will look like;
```

2021/01/16 11:58:49 💾 Seeding database with table...
2021/01/16 11:58:49 🚀 Scheduling event SendEmail to run at 2021-01-16 11:59:49.344904505 +0545 +0545 m=+60.004623549
2021/01/16 11:58:49 🚀 Scheduling event PayBills to run at 2021-01-16 12:00:49.34773798 +0545 +0545 m=+120.007457039
2021/01/16 11:59:49 ⏰ Ticks Received...
2021/01/16 11:59:49 📨 Sending email with data:  mail: nilkantha.dipesh@gmail.com
2021/01/16 12:00:49 ⏰ Ticks Received...
2021/01/16 12:01:49 ⏰ Ticks Received...
2021/01/16 12:01:49 💲 Pay me a bill:  paybills: $4,000 bill
2021/01/16 12:02:49 ⏰ Ticks Received...
2021/01/16 12:03:49 ⏰ Ticks Received...
^C2021/01/16 12:03:57 
❌ Interrupt received closing...
```

From the output, we can see that the event `SendEmail` was triggered after a minute and event `PayBills` after second minute.

In this way, we built a basic event scheduling system that will schedule events after certain time interval. Full example for this code can be found at:

This example only shows basic implementation of event scheduling which doesn’t cover things like; how to handle if overlap that occurs between two polling interval, how to not use polling, etc. We can use rabbitmq , kafka etc for some serious event scheduling that might scale eventually.
