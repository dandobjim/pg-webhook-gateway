---
status: accepted
date: 2026-10-27
decision-makers: Daniel Doblas Jiménez
---

# Perform delivery fan-out inside the ingest transaction

## Context and Problem Statement

Every accepted event must produce one `deliveries` row per matching active
subscription. ADR-0001 chose PostgreSQL as the queue so that the event and its
deliveries can be written atomically (transactional outbox).

The fan-out can run inside the `POST /v1/events` transaction or in a dedicated
worker that expands stored events asynchronously. Fan-out size grows with the
number of subscriptions: a tenant with 50 subscriptions to one event type writes
51 rows per request. Where should the fan-out run so that the ingest p99 SLO
(see `docs/requirements.md`) is met without weakening delivery guarantees?

In both options, HTTP delivery is performed by the Dispatcher, never by the
ingest path.

## Decision Drivers

- Atomicity: an accepted event must never exist without its deliveries.
- Ingest latency: p99 of `POST /v1/events` within the SLO.
- Operational complexity: number of components to deploy, monitor and recover.
- Unambiguous subscription semantics: which subscriptions receive an event.

## Considered Options

- Fan-out inside the ingest transaction
- Dedicated fan-out worker

## Decision Outcome

Chosen option: "Fan-out inside the ingest transaction", because it is the only
option that guarantees atomicity without extra recovery machinery, it keeps
subscription semantics unambiguous, and the expected fan-out size (tens of rows,
inserted with a single multi-row statement) does not threaten the ingest SLO.

### Consequences

- Good, because events and deliveries are committed atomically; no recovery
  logic is needed for partially fanned-out events.
- Good, because deliveries are visible to the Dispatcher as soon as the request
  returns, with no additional end-to-end delay.
- Good, because there is one queue and one claiming mechanism to operate.
- Bad, because ingest latency grows linearly with the number of matching
  subscriptions.
- Bad, because a tenant with an unusually large fan-out increases transaction
  duration and lock time on the ingest path.
- Neutral, because the event payload is stored once regardless of fan-out size.

### Confirmation

- Integration test: a failure forced while inserting deliveries rolls back the
  event.
- Benchmark: ingest p99 measured with 1, 10, 50 and 200 matching
  subscriptions, recorded in `docs/benchmarks.md`.

### Revisit when

- Ingest p99 exceeds the SLO in the step 9 benchmarks, or
- a single event type exceeds the documented maximum of matching subscriptions.

## Pros and Cons of the Options

### Fan-out inside the ingest transaction

The API inserts the event and all its deliveries in one transaction, using a
single multi-row insert for the deliveries.

- Good, because atomicity is provided by PostgreSQL.
- Good, because subscriptions are resolved at acceptance time, which is easy to
  explain to users.
- Good, because no additional component is required.
- Bad, because write amplification is on the latency-critical path.

### Dedicated fan-out worker

The API stores only the event. A separate worker claims unexpanded events and
creates their deliveries.

- Good, because ingest latency is independent of fan-out size.
- Good, because fan-out throughput can be scaled independently of the API.
- Bad, because it requires a second claimable queue (state column, leases,
  `SKIP LOCKED`), duplicating the Dispatcher's claiming logic.
- Bad, because a crash between claim and completion requires an idempotent
  fan-out, enforced by a unique constraint on `(event_id, subscription_id)`.
- Bad, because subscriptions are resolved at fan-out time, so subscriptions
  created or removed after acceptance change who receives the event.
- Bad, because total writes increase (an extra update per event to mark it as
  expanded) and end-to-end delivery latency gains a new component (fan-out lag)
  that must be monitored.