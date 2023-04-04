- 原文地址：https://medium.com/wesionary-team/building-basic-event-scheduler-in-go-134c19f77f84
- 原文作者：Dipesh Dulal
- 本文永久链接：https://github.com/gocn/translator/blob/master/2023/w15_Building_Basic_Event_Scheduler_in_Go.md
- 译者：[lsj1342](https://github.com/lsj1342)
- 校对：[cvley](https://github.com/cvley)

## Go构建基础的事件调度器
![](https://github.com/gocn/translator/raw/master/static/images/2023/w15_Building_Basic_Event_Scheduler_in_Go//1_gBs7tyig8N5eeHNMOwIG8w.webp)

当我们需要在一段时间后的特定时间或间隔运行任务时，我们需要使用任务调度系统;来运行任务：例如发送电子邮件、推送通知、午夜关闭账户、清算表等

在本文中，我们将构建一个基本的事件调度程序，使用数据库作为持久层来调度事件在特定时间段运行，这将使我们了解事件调度系统的工作原理。基本的工作机制是；

每当我们需要调度事件时，计划作业就会添加到数据库中以在特定时间运行。另一个任务始终定期运行以检查某些任务是否已从数据库中过期，如果在数据库中发现已过期任务（轮询）则运行。

![Implementation Details](https://github.com/gocn/translator/raw/master/static/images/2023/w15_Building_Basic_Event_Scheduler_in_Go/1_WVOKKAJBbWlmOL2dEgOCOQ.png)



让我们从创建用于存储事件的数据库（在 postgresql 中）开始。

```sql
CREATE TABLE IF NOT EXISTS "public"."jobs" (     
   "id"      SERIAL PRIMARY KEY,     
   "name"    varchar(50) NOT NULL,     
   "payload" text,     
   "runAt"   TIMESTAMP NOT NULL    
)
```

现在，我们来定义数据结构；

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

还需要定义 `Scheduler` 结构，用于调度事件和运行侦听器。
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

在第 8 行到第 13 行中，我们通过将sql.DB实例和初始侦听器传递给调度程序来创建新的调度程序。

现在，我们实现调度函数，并将我们的事件插入到 `jobs` 表中；
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

在 `AddListener` 函数中，我们为事件分配监听函数。

我们已经首先完成了添加 `jobs` 表。现在需要从数据库中获取已经过期的作业，执行然后删除它们。

下面的函数实现显示了我们如何检查表中的过期事件并将事件序列化到 `Event` 结构中。
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

第二步是调用从数据库中找到的已注册事件侦听器，如下所示；
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

在这里，我们正在检查是否有绑定的事件函数，如果找到正在调用事件的监听器函数。第 6 行到第 9 行将从数据库中删除事件，以便在下次轮询数据库时不会再找到。

最后一步是（轮询）检查某个事件是否在给定时间间隔内过期。对于间隔运行的任务，我们使用 `time` 库的 `ticker` 函数，该函数将提供一个通道，该通道在提供的间隔内接收新的 `tick`。
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

在第 7 行和第 10 行中，我们检查上下文是否已关闭或 `ticker`通道是否正在接收新的 `tick`。在 11 行接收到 `tick` 后，我们检查到期事件，然后调用所有事件的侦听器函数。

下面是实际在文件中定义的所有函数，`main.go`  如下所示；
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

在第 13 行到第 16 行中，我们将侦听函数绑定到事件 `SendEmail` 和 `PayBills`上，以便在发生新事件时调用这些函数。

在 22行 和 32 到 37 行中，我们添加了中断信号(os.Interrupt)通道，当程序中发生中断时，我们执行 19 行中的上下文取消函数。

从第 26 行到第 30 行，我们定义事件调度程序、运行轮询函数并将在一分钟后运行 `SendEmail` ，两分钟后运行 `PayBills`。

程序的输出将如下所示；
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

从输出中，我们可以看到 `SendEmail` 在一分钟后触发，事件 `PayBills` 在第二分钟后触发。

通过这种方式，我们构建了一个基本的事件调度系统，它将在一定时间间隔后调度事件。

这个例子只展示了事件调度程度的基本实现，并未覆盖诸如：如果两个轮询间隔之间发生重叠，如何处理，如何不使用轮询等。我们可以使用 `rabbitmq`，`kafka` 等完成一个最终严谨的事件调度程度。
