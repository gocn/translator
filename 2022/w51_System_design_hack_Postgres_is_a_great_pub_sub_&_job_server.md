**If you need a publish/subscribe or job server at any point in your project, try using Postgres. It'll give you lots of data integrity and performance guarantees, and it doesn't require you or your team learning any new technology.**

If you're making any project of sufficient complexity, you'll need a [publish/subscribe](https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern) server to process events. This article will introduce you to Postgres, explain the alternatives, and walk you through an example use case of pub/sub and its solution.

**Postgres is an amazing relational database**

If you aren't too familiar with [Postgres](https://www.postgresql.org/), it's a feature-packed relational database that many companies use as a traditional central data store. By storing your "users" table in Postgres, you can immediately scale to 100 columns and a row for every living person.

It's possible to scale Postgres to storing a billion 1KB rows entirely in memory - This means you could quickly run queries against the full name of everyone on the planet on commodity hardware and with little fine-tuning.

I'm not going to belabor the point that something called "PostgresSQL" is a good SQL database. I'll show you a more interesting use case for it where we combine a few features to turn Postgres into a powerful pubsub / job server.

**Postgres makes a great persistent pubsub server**

If you do enough system design, you'll inevitably need to solve a problem with [publish/subscribe architecture](https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern). We hit it quickly at [webapp.io](https://webapp.io/) - we needed to keep the viewers of a test run's page and the [github](https://github.com/) API notified about a run as it progressed.

For your pub/sub server, you have a lot of options:

- [Kafka](https://kafka.apache.org/)
- [RabbitMQ](https://www.rabbitmq.com/)
- [Redis PUB/SUB](https://redis.io/topics/pubsub)
- A [vendor](https://aws.amazon.com/sqs/) [locked](https://cloud.google.com/pubsub/docs/overview) [cloud](https://docs.microsoft.com/en-us/azure/event-grid/) [provider](https://docs.microsoft.com/en-us/azure/event-grid/) [solution](https://docs.microsoft.com/en-us/azure/service-bus-messaging/)
- Postgres?
  There are very few use cases where you'd need a dedicated pub/sub server like Kafka. Postgres can [easily handle 10,000 insertions per second](https://severalnines.com/blog/benchmarking-postgresql-performance), and it can be tuned to even higher numbers. It's rarely a mistake to start with Postgres and then switch out the most performance critical parts of your system when the time comes.

### Pub/sub + atomic operations ⇒ no job server necessary.

In the list above, I skipped things similar to pub/sub servers called "job queues" - they only let one "subscriber" watch for new "events" at a time, and keep a queue of unprocessed events:

- [Celery](http://www.celeryproject.org/)
- [Gearman](http://gearman.org/)
  It turns out that Postgres generally supersedes job servers as well. You can have your workers "watch" the "new events" channel and try to claim a job whenever a new one is pushed. As a bonus, Postgres lets other services watch the status of the events with no added complexity.

### Our use case: CI runs processed by sequential workers

At webapp.io, we run "test runs", which start by cloning a repository, and then running some user specified tests. There are microservices that do various initialization steps for the test run, and additional microservices (such as the websocket gateway) that need to listen to the status of the runs.

![How a test run is processed at webapp.io](../static/images/2022/w51_System_design_hack_Postgres_is_a_great_pub_sub_&_job_server/run-flow.svg "How a test run is processed at webapp.io")

An instance of an API server creates a run by inserting a row into the "Runs" row of a Postgres table:

```plain
CREATE TYPE ci_job_status AS ENUM ('new', 'initializing', 'initialized', 'running', 'success', 'error');

CREATE TABLE ci_jobs(
	id SERIAL,
	repository varchar(256),
	status ci_job_status,
	status_change_time timestamp
);

/*on API call*/
INSERT INTO ci_job_status(repository, status, status_change_time) VALUES ('https://github.com/colinchartier/layerci-color-test', 'new', NOW());
```

How do the workers worker "claim" a job? By setting the job status atomically:

```plain
UPDATE ci_jobs SET status='initializing'
WHERE id = (
  SELECT id
  FROM ci_jobs
  WHERE status='new'
  ORDER BY id
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
RETURNING *;
```

Finally, we can use a trigger and a channel to notify the workers that there might be new work available:

```plain
CREATE OR REPLACE FUNCTION ci_jobs_status_notify()
	RETURNS trigger AS
$$
BEGIN
	PERFORM pg_notify('ci_jobs_status_channel', NEW.id::text);
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE TRIGGER ci_jobs_status
	AFTER INSERT OR UPDATE OF status
	ON ci_jobs
	FOR EACH ROW
EXECUTE PROCEDURE ci_jobs_status_notify();
```

All the workers have to do is "listen" on this status channel and try to claim a job whenever a job's status changes:

```plain
tryPickupJob := make(chan interface{})
//equivalent to 'LISTEN ci_jobs_status_channel;'
listener.Listen("ci_jobs_status_channel")
go func() {
  for event := range listener.Notify {
    select {
    case tryPickupJob <- true:
    }
  }
  close(tryPickupJob)
}

for job := range tryPickupJob {
  //try to "claim" a job
}
```

When we combine these elements, we get something like the following:
![queue-system](../static/images/2022/w51_System_design_hack_Postgres_is_a_great_pub_sub_&_job_server/queue-system.svg)
This architecture scales to many sequential workers processing the job in a row, all you need is a "processing" state and a "processed" state for each worker. For webapp.io that looks like: new, initializing, initialized, running, complete.

It also allows other services to watch the `ci_jobs_status_channel` - Our websocket gateway for the /run page and github notification services simply watch the channel and notify any relevant parties of the published events.

## Other benefits of using Postgres for Pub/Sub

There are also a bunch of other benefits to using postgres instead of something like Redis Pub/Sub:

- Many SQL users will already have Postgres installed for use as a database, so there are no extra setup costs for using it for pub/sub.
- As a database, Postgres has very good persistence guarantees - It's easy to query "dead" jobs with, e.g., `SELECT * FROM ci_jobs WHERE status='initializing' AND NOW() - status_change_time > '1 hour'::interval` to handle workers crashing or hanging.
- Since jobs are defined in SQL, it's easy to generate graphql and protobuf representations of them (i.e., to provide APIs that checks the run status.)
- It's easy to have multiple watchers of status changes, you can have other services use the same "LISTEN ci_jobs_status_channel"
- Postgres has very good language support, with bindings for most popular languages. This is a stark difference from most other pub/sub servers.
- You can also run complicated SQL queries on things that are still in your "work queues" to give highly tailored API endpoints to your users.

## Conclusion

If you need a publish/subscribe or job server at any point in your project, it's not a bad idea to start by using Postgres. It'll give you lots of data integrity and performance guarantees, and it doesn't require you or your team learning any new technology.
