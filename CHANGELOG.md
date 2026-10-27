# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Add entries under [Unreleased], creating only the subsections you need:
Added, Changed, Deprecated, Removed, Fixed, Security.
On release, rename [Unreleased] to [X.Y.Z] - YYYY-MM-DD, tag vX.Y.Z and
add compare links at the bottom.
-->

## [Unreleased]

### Added

- ADR-0003 performing the delivery fan-out inside the ingest transaction, so
  an accepted event never exists without its deliveries.
- ADR-0004 (proposed) using explicit SQL with async psycopg 3 behind
  repository interfaces for the latency-sensitive queue queries.
- FastAPI application skeleton with a root welcome endpoint, runnable through
  the `fastapi` CLI entrypoint configured in `pyproject.toml`.
- Typed application settings with pydantic-settings, read from the environment
  or `.env` (`DATABASE_URL`, pool size, max overflow, SQL echo).
- Async database engine created on application startup and disposed on
  shutdown, with a request-scoped session dependency for route handlers.
- `/api/v1/healthz` liveness probe and `/api/v1/readyz` readiness probe;
  readiness runs `SELECT 1` and answers 503 when Postgres is unreachable.

### Changed

- Renamed the import package from `pg_webhook_gateway` to `app`; the
  distribution name `pg-webhook-gateway` is unchanged.

## [0.2.0] - 2026-10-23

### Added

- ADR-0002 adopting the Standard Webhooks v1.0.0 specification (HMAC-SHA256
  `v1` scheme) for signing deliveries, covering spoofing, tampering, replay,
  duplicate deliveries and zero-downtime secret rotation.
- Functional and non-functional requirements document with stable IDs that
  ADRs, issues and tests can reference.
- Local PostgreSQL 18 via Docker Compose, with data persisted in a
  git-ignored `postgres-data/` directory and settings loaded from `.env`
  (see `.env.example`).
- Async database stack (SQLAlchemy asyncio + asyncpg) and Alembic migrations
  running in async mode, configured through `DATABASE_URL`; generated
  revisions are linted and formatted with Ruff automatically.
- Initial database schema as Alembic migrations: tenants and API keys,
  endpoints and subscriptions, events, deliveries and delivery attempts, and
  an audit log. Tenant isolation is enforced with composite foreign keys, and
  partial indexes back the dispatcher claim and the expired-lease reaper.
- Database schema ER diagram in the README, with notes on tenant isolation,
  idempotent ingest, fan-out and the delivery lifecycle.

### Changed

- Architecture diagram now separates the public tenant Management API from the
  internal platform Operator API, reflecting their different audiences,
  permissions and exposure.

## [0.1.0] - 2026-10-20

### Added

- Initial project scaffold with the package layout for the API, database,
  dispatcher, domain, observability and security modules.
- Architecture overview diagram in the README.
- ADR-0001 documenting the choice of Postgres over Redis Streams and Kafka as
  the queue.

[Unreleased]: https://github.com/dandobjim/pg-webhook-gateway/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/dandobjim/pg-webhook-gateway/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dandobjim/pg-webhook-gateway/releases/tag/v0.1.0
