---
# Allowed values: proposed | rejected | accepted | deprecated | superseded by ADR-NNNN
status: accepted
# Date of the last update, YYYY-MM-DD
date: 2026-10-20
# People who own the decision
decision-makers: [ Daniel Doblas Jimenez ]
# People whose opinion was sought (two-way communication)
consulted: [ None ]
# People kept up to date on progress (one-way communication)
informed: [ Daniel Doblas Jimenez ]
---

# Postgres as a queue: use Postgres instead of Redis or Kafka for queueing

## Context and Problem Statement

There are a lot of tools in the market that can be used to implement a queue, but we want to keep the architecture
simple and avoid adding more moving parts. We want to use Postgres as a queue instead of Redis or Kafka.

## Decision Drivers

- **Reduce the amount of tools**: Same tool for everything (Postgres)
- **Simplicity**: Easier to manage and maintain with a single technology
- **Cost**: Avoid the cost of running additional services like Redis or Kafka
- **Performance**: Postgres can handle a high volume of messages and is suitable for our use case

## Considered Options

- Postgres as a queue
- Kafka
- Redis Streams

## Decision Outcome

Chosen option: "Postgres as a queue",
because it is the only option that meets the must-have driver of reducing the amount of tools and it scores best against
the drivers below.

### Consequences

- Good, because it reduces the amount of tools and simplifies the architecture
- Good, because it reduces the cost of running additional services
- Good, because it is suitable for our use case and can handle a high volume of messages
- Good, because it is easier to manage and maintain with a single technology
- Bad, because it may not be as performant as Kafka or Redis Streams for very high throughput use cases, but it is
  sufficient for our needs
- Bad, because it may not have the same level of features and capabilities as Kafka or Redis Streams, but it is
  sufficient for our needs
- Bad, because it may not be as widely adopted or have as large of a community as Kafka or Redis Streams, but it is
  sufficient for our needs

## Pros and Cons of the Options

### Postgres as a queue

Postgres can be used as a queue by using a table to store messages and using `FOR UPDATE SKIP LOCKED` with leases so
concurrent workers never claim the same row, giving at-least-once delivery without global ordering (consumers must be
idempotent; expired leases are retried). This approach is simple and easy to implement, and it allows us to use the same
database for both our application data and our queue.

- Good, because it reduces the amount of tools and simplifies the architecture
- Bad, because it may not be as performant as Kafka or Redis Streams for very high throughput use cases, but it is
  sufficient for our needs

#### Sources
- [SELECT – The Locking Clause (`FOR UPDATE`, `NOWAIT`, `SKIP LOCKED`)](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE)
- [Explicit Locking – Row-Level Locks](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS)
- [NOTIFY](https://www.postgresql.org/docs/current/sql-notify.html) / [LISTEN](https://www.postgresql.org/docs/current/sql-listen.html)
- [Routine Vacuuming (autovacuum and bloat)](https://www.postgresql.org/docs/current/routine-vacuuming.html)
- [Release notes 9.5 (introduction of `SKIP LOCKED`)](https://www.postgresql.org/docs/9.5/release-9-5.html)


### Kafka

Kafka is a distributed streaming platform that can be used as a queue.

- Good, because it is a distributed streaming platform that can be used as a queue. It is designed for high throughput and
  low latency, and it has a rich set of features for managing and processing messages.
- Bad, because it requires additional infrastructure and management, and it may be overkill for our use case.

#### Sources
- [KIP-932: Queues for Kafka (share groups)](https://cwiki.apache.org/confluence/display/KAFKA/KIP-932%3A+Queues+for+Kafka)
- [KIP-848: Next Generation of the Consumer Rebalance Protocol](https://cwiki.apache.org/confluence/display/KAFKA/KIP-848%3A+The+Next+Generation+of+the+Consumer+Rebalance+Protocol)
- [Official Kafka documentation](https://kafka.apache.org/documentation/)
- [Kafka – Design (persistence, consumers, delivery guarantees)](https://kafka.apache.org/documentation/#design)

### Redis Streams

Redis Streams is a data structure in Redis that can be used as a queue.

- Good, because it is designed for high performance and low latency
- Neutral, because it requires additional infrastructure and management
- Bad, because it may be overkill for our use case

#### Sources
- [Redis Streams](https://redis.io/docs/latest/develop/data-types/streams/)
- [XACK](https://redis.io/docs/latest/commands/xack/)
- [XACKDEL (Redis 8.2+)](https://redis.io/docs/latest/commands/xackdel/)
- [XNACK (Redis 8.8+)](https://redis.io/docs/latest/commands/xnack/)
- [Streaming with redis-py (official use case)](https://redis.io/docs/latest/develop/use-cases/streaming/redis-py/)
- [Redis Lists](https://redis.io/docs/latest/develop/data-types/lists/)
- [Pub/Sub](https://redis.io/docs/latest/develop/pubsub/)
- [Persistence (RDB / AOF)](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)
