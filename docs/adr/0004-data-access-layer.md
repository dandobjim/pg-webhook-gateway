---
status: proposed
date: 2026-10-27
decision-makers: Daniel Doblas Jiménez
---

# Use explicit SQL with psycopg 3 (async) behind repository interfaces

## Context and Problem Statement

The gateway uses PostgreSQL as its queue (ADR-0001) and performs the delivery
fan-out inside the ingest transaction (ADR-0003). Its critical queries are
PostgreSQL-specific and latency-sensitive:

- ingest: idempotent event insert (`ON CONFLICT`) plus a multi-row insert of
  deliveries in one transaction;
- dispatcher: batch claim with `UPDATE ... WHERE id IN (SELECT ... FOR UPDATE
  SKIP LOCKED LIMIT n) RETURNING ...`, and finalisation guarded by a lease token;
- reaper: recovery of expired leases.

The Management API adds simpler CRUD queries with optional filters and cursor
pagination. Migrations are already managed with Alembic.

Which data access layer and driver should the services use so that critical
queries stay explicit, fast and measurable, while the rest of the code remains
maintainable and safe from SQL injection?

## Decision Drivers

- Full control and visibility of the SQL on the hot paths (claim, outbox).
- Performance: low per-query overhead, measurable in step 9 benchmarks.
- Async support compatible with FastAPI and the asyncio dispatcher.
- Static typing of query results (pyright/mypy in CI).
- Ecosystem: connection pooling, OpenTelemetry instrumentation, testcontainers.
- Maintainability of dynamic queries (filters, pagination) without string
  concatenation.

## Considered Options

- Explicit SQL with psycopg 3 (async)
- Explicit SQL with asyncpg
- SQLAlchemy 2.0 Core (async) on top of psycopg 3 or asyncpg
- SQLAlchemy 2.0 ORM (async)

## Decision Outcome

Chosen option: "Explicit SQL with psycopg 3 (async)", because the critical
queries are PostgreSQL-specific and must be written, reviewed and profiled as
SQL anyway; psycopg 3 provides native async, a standard DB-API interface, typed
row factories, pipeline mode and safe query composition, with no abstraction
layer between the code and the measured query.

Implementation rules:

- All SQL lives in repository modules (`db/repositories/`); API handlers and the
  dispatcher depend on repository interfaces, never on the driver.
- Parameters are always bound by the driver; dynamic identifiers or clauses are
  built only with `psycopg.sql` composition. String formatting of SQL is
  forbidden and checked by a linter rule.
- Rows are mapped to typed domain objects with row factories.
- Connections come from `psycopg_pool.AsyncConnectionPool`, sized per process
  and configured with explicit acquisition and statement timeouts.
- Alembic remains the migration tool, running its own synchronous engine;
  application code does not depend on SQLAlchemy.

### Consequences

- Good, because every hot-path query is visible as plain SQL, so `EXPLAIN
  ANALYZE` and `pg_stat_statements` output map directly to the code.
- Good, because there is a single mental model (SQL) for queries and no ORM
  session state, lazy loading or implicit transactions.
- Good, because the repository interface allows swapping the driver (asyncpg)
  for a benchmark without touching business logic.
- Bad, because there is more boilerplate for CRUD and row mapping than with a
  query builder.
- Bad, because dynamic queries (Management API filters, cursor pagination) must
  be composed carefully with `psycopg.sql`.
- Bad, because the schema is described twice: in Alembic migrations and in the
  SQL/row types; drift is caught only by integration tests.
- Neutral, because Alembic still brings SQLAlchemy as a development dependency.

### Confirmation

- Integration tests run every repository against PostgreSQL 18 in
  testcontainers; no SQLite or mocked driver.
- A CI check fails if SQL is built with f-strings or `%` formatting outside
  `psycopg.sql`.
- Step 9 benchmark: ingest and claim throughput measured with psycopg 3 and,
  as an experiment, with asyncpg behind the same repository interface; results
  recorded in `docs/benchmarks.md`.

### Revisit when

- The step 9 benchmark shows the driver is a significant share of ingest or
  claim latency and asyncpg removes it, or
- the Management API grows enough dynamic querying that hand-written
  composition becomes a recurring source of bugs (then reconsider SQLAlchemy
  Core for that API only).

## Pros and Cons of the Options

### Explicit SQL with psycopg 3 (async)

- Good, because it is natively async and implements DB-API 2.0.
- Good, because it ships type hints and typed row factories.
- Good, because pipeline mode and `COPY` support efficient bulk writes.
- Good, because OpenTelemetry provides an official instrumentation package.
- Bad, because it requires manual row mapping and query composition.

### Explicit SQL with asyncpg

- Good, because it is designed for asyncio and uses the binary protocol, usually
  with lower per-query overhead.
- Good, because it includes a built-in connection pool.
- Bad, because its API is non-standard (no DB-API), which couples the code to
  the driver.
- Bad, because type information relies on third-party stubs.
- Bad, because its prepared-statement cache needs explicit configuration behind
  transaction-pooling proxies such as PgBouncer.

### SQLAlchemy 2.0 Core (async)

- Good, because it composes dynamic queries safely and expresses
  `ON CONFLICT`, `FOR UPDATE SKIP LOCKED` and `RETURNING` through the
  PostgreSQL dialect.
- Good, because migrations and queries can share one table metadata
  definition, reducing schema drift.
- Good, because the underlying driver (psycopg 3 or asyncpg) can be switched by
  configuration.
- Bad, because it adds an abstraction layer and per-query overhead on the hot
  paths.
- Bad, because complex PostgreSQL-specific queries are harder to read than the
  equivalent SQL, and the emitted SQL must still be inspected to profile it.

### SQLAlchemy 2.0 ORM (async)

- Good, because it minimises CRUD boilerplate.
- Bad, because unit-of-work, identity map and lazy loading add implicit
  behaviour that is hard to reason about in queue-style concurrent workloads.
- Bad, because it adds the highest overhead and hides the SQL that this project
  aims to measure and document.