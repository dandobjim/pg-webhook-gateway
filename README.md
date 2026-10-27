# pg-webhook-gateway

[![CI](https://github.com/dandobjim/pg-webhook-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/dandobjim/pg-webhook-gateway/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/dandobjim/pg-webhook-gateway/branch/main/graph/badge.svg)](https://codecov.io/gh/dandobjim/pg-webhook-gateway)
[![Python](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

Reliable webhook delivery gateway in Python: Postgres-backed queue with SKIP LOCKED leases, at-least-once delivery, Standard Webhooks signatures, retries with jitter, DLQ and replay.

<!-- Describe the problem this project solves, who it is for and how it fits in a bigger system. -->

## Features

<!-- List the main capabilities. Keep each bullet short and user-facing. -->

- Feature one
- Feature two

## Quickstart

Requirements: Python >= 3.14, [uv](https://docs.astral.sh/uv/) and Docker (with Compose).

```bash
git clone https://github.com/dandobjim/pg-webhook-gateway.git
cd pg-webhook-gateway
uv sync
cp .env.example .env                           # local settings (git-ignored)
docker compose up -d                           # PostgreSQL 18, data in ./postgres-data
uv run --env-file .env alembic upgrade head    # apply migrations
```

```python
import app

print(app.__version__)
```

## Configuration

Project and tool settings live in [`pyproject.toml`](pyproject.toml): dependencies, Ruff, mypy, pytest and coverage.

Runtime settings come from environment variables. Copy [`.env.example`](.env.example) to `.env` (git-ignored) and load it with `uv run --env-file .env ...`; Docker Compose reads `.env` automatically.

| Variable            | Description                                            | Default (`.env.example`)                                        |
| ------------------- | ------------------------------------------------------ | --------------------------------------------------------------- |
| `DATABASE_URL`      | Async SQLAlchemy URL (asyncpg) used by app and Alembic | `postgresql+asyncpg://webhooks:webhooks@localhost:5432/webhooks` |
| `POSTGRES_USER`     | User created by the Postgres container                 | `webhooks`                                                      |
| `POSTGRES_PASSWORD` | Password for that user                                 | `webhooks`                                                      |
| `POSTGRES_DB`       | Database created by the Postgres container             | `webhooks`                                                      |
| `POSTGRES_PORT`     | Host port mapped to the container's 5432               | `5432`                                                          |
| `LOG_LEVEL`         | Application log level                                  | `INFO`                                                          |

PostgreSQL is both the store and the queue (see [ADR-0001](docs/adr/0001-postgres-vs-redis-kafka.md)): the gateway talks to it asynchronously through SQLAlchemy's asyncio extension and the [asyncpg](https://github.com/MagicStack/asyncpg) driver, and workers claim deliveries with `FOR UPDATE SKIP LOCKED`.

## Development

```bash
uv sync                      # create .venv and install the project + dev tools
uv run pre-commit install    # run checks automatically on every commit
```

**Commit `uv.lock`.** CI installs with `--locked`, so it fails if the lockfile is missing or out of sync with `pyproject.toml` (the `uv-lock` pre-commit hook keeps it updated locally).

| Task                     | Command                             |
| ------------------------ | ----------------------------------- |
| Lint                     | `uv run ruff check .`               |
| Lint and autofix         | `uv run ruff check --fix .`         |
| Format                   | `uv run ruff format .`              |
| Type check (strict)      | `uv run mypy`                       |
| Run all pre-commit hooks | `uv run pre-commit run --all-files` |
| Update hook versions     | `uv run pre-commit autoupdate`      |
| Add a dependency         | `uv add <package>`                  |
| Add a dev dependency     | `uv add --dev <package>`            |

### Database

A local PostgreSQL 18 runs from [`docker-compose.yml`](docker-compose.yml). Its data lives in `./postgres-data` (bind mount, git-ignored), so it survives `docker compose down`. Migrations are managed with [Alembic](https://alembic.sqlalchemy.org/) in async mode ([`alembic/env.py`](alembic/env.py)) and read `DATABASE_URL`; generated revisions are formatted with Ruff automatically.

| Task                        | Command                                                         |
| --------------------------- | --------------------------------------------------------------- |
| Start Postgres              | `docker compose up -d`                                          |
| Stop Postgres (keeps data)  | `docker compose down`                                           |
| Follow logs                 | `docker compose logs -f postgres`                               |
| Open a `psql` shell         | `docker compose exec postgres psql -U webhooks -d webhooks`     |
| Create a migration          | `uv run --env-file .env alembic revision -m "describe change"` |
| Autogenerate from models    | `uv run --env-file .env alembic revision --autogenerate -m "…"` |
| Apply migrations            | `uv run --env-file .env alembic upgrade head`                   |
| Revert last migration       | `uv run --env-file .env alembic downgrade -1`                   |
| Show current revision       | `uv run --env-file .env alembic current`                        |
| Reset the database (wipes!) | `docker compose down && rm -rf postgres-data`                   |

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming, commit conventions and the PR checklist.

## Testing

| Task                       | Command                           |
| -------------------------- | --------------------------------- |
| Run tests with coverage    | `uv run pytest`                   |
| HTML coverage report       | `uv run pytest --cov-report=html` |
| Run a single test          | `uv run pytest tests/path.py::test_name` |

Tests fail if coverage drops below **80%** (`[tool.coverage.report] fail_under` in `pyproject.toml`).

GitHub Actions runs on every push to `main` and on every pull request:

- **Lint**: all pre-commit hooks (ruff check, ruff format, mypy in strict mode, file hygiene).
- **Test**: `pytest` on every supported Python version (3.14–3.14); coverage is uploaded to [Codecov](https://codecov.io/gh/dandobjim/pg-webhook-gateway).

Actions are pinned to commit SHAs and [Dependabot](.github/dependabot.yml) opens weekly PRs to update actions, Python dependencies and pre-commit hooks.

## Architecture

Significant design decisions are recorded as [Architecture Decision Records](docs/adr/README.md) using the [MADR](https://adr.github.io/madr/) format.

```
pg-webhook-gateway/
├── .github/                # CI workflow, Dependabot, PR template
├── alembic/                # async migration environment and revisions
├── docs/adr/               # architecture decision records
├── src/app/ # package source code
├── tests/                  # pytest test suite
├── .env.example            # sample local settings (copy to .env)
├── alembic.ini             # Alembic configuration
├── docker-compose.yml      # local PostgreSQL 18 (data in ./postgres-data)
└── pyproject.toml          # metadata, dependencies and tool configuration
```

```mermaid
flowchart LR
    producer["Producer<br/>(tenant service)"]
    tenant["Tenant developer"]
    operator["Platform operator"]

    subgraph gateway["pg-webhook-gateway"]
        direction LR
        api["Ingest API<br/>FastAPI"]
        mgmt["Management API<br/>endpoints, subscriptions,<br/>secrets, replay"]
        opsapi["Operator API (internal)<br/>tenants, API keys,<br/>incidents"]
        dispatcher["Dispatcher<br/>asyncio workers"]
        reaper["Reaper<br/>expired lease recovery"]
    end

    db[("PostgreSQL<br/>events · deliveries ·<br/>delivery_attempts")]
    subscribers["Subscriber endpoints"]

    subgraph observability["Observability"]
        direction TB
        otel["OpenTelemetry Collector"]
        prom["Prometheus"]
        tempo["Tempo"]
        grafana["Grafana"]
    end

    producer -->|"POST /v1/events<br/>API key + Idempotency-Key"| api
    api -->|"single transaction:<br/>event + deliveries (outbox)"| db
    tenant -->|"/v1/...<br/>tenant API key"| mgmt
    operator -->|"/internal/v1/...<br/>operator credential"| opsapi
    mgmt -->|"own resources:<br/>CRUD + replay dead deliveries"| db
    opsapi -->|"cross-tenant:<br/>tenants, keys, replay, purge"| db
    dispatcher -->|"claim batch<br/>FOR UPDATE SKIP LOCKED + lease"| db
    dispatcher -->|"HTTPS POST<br/>Standard Webhooks signature"| subscribers
    dispatcher -->|"finalize with lease token"| db
    reaper -->|"expired leases → retrying"| db

    api -.->|traces, metrics| otel
    dispatcher -.->|traces, metrics| otel
    otel --> prom
    otel --> tempo
    prom --> grafana
    tempo --> grafana
```

### Database schema

The schema is created by the Alembic revisions in [`alembic/versions/`](alembic/versions/), applied in this order: tenants and API keys, endpoints and subscriptions, events and deliveries, audit log. Primary keys are `uuidv7()` (native in PostgreSQL 18 and time-ordered) except for the two append-only logs, which use `bigint` identity columns.

```mermaid
erDiagram
    tenants ||--o{ api_keys : "authenticates with"
    tenants ||--o{ endpoints : owns
    tenants ||--o{ events : ingests
    tenants |o--o{ audit_log : "scopes (null = platform-wide)"
    endpoints ||--o{ subscriptions : "listens via (cascade)"
    endpoints ||--o{ deliveries : receives
    events ||--o{ deliveries : "fans out to (cascade)"
    deliveries ||--o{ delivery_attempts : "records (cascade)"

    tenants {
        uuid id PK
        text name
        text status "active | suspended"
        integer ingest_rate_limit_per_sec "> 0, default 100"
        timestamptz created_at
        timestamptz updated_at
    }
    api_keys {
        uuid id PK
        uuid tenant_id FK
        text name
        text prefix UK "visible part, used for lookup"
        bytea key_hash "sha256(full key), 32 bytes"
        text_array scopes "default {events:write}"
        timestamptz expires_at "nullable"
        timestamptz revoked_at "nullable"
        timestamptz last_used_at "updated at most once per minute"
        timestamptz created_at
    }
    endpoints {
        uuid id PK "UK (id, tenant_id)"
        uuid tenant_id FK
        text url
        text description "nullable"
        text status "active | disabled | deleted"
        text disabled_reason "manual | gone_410 | failing | operator"
        timestamptz disabled_at "nullable"
        bytea secret_ciphertext "signing secret, encrypted"
        bytea previous_secret_ciphertext "set during rotation"
        timestamptz previous_secret_expires_at "set during rotation"
        smallint secret_key_version "which KEK encrypted the secrets"
        smallint max_concurrency "1..100, default 10"
        timestamptz created_at
        timestamptz updated_at
    }
    subscriptions {
        uuid id PK
        uuid tenant_id FK "with endpoint_id"
        uuid endpoint_id FK "UK (endpoint_id, event_type)"
        text event_type "* or invoice.paid style"
        timestamptz created_at
    }
    events {
        uuid id PK "sent as webhook-id; UK (id, tenant_id)"
        uuid tenant_id FK "UK (tenant_id, idempotency_key)"
        text event_type "dot-delimited [a-zA-Z0-9_]"
        bytea payload "<= 256 KiB"
        text idempotency_key "1..255 chars"
        bytea request_fingerprint "32 bytes"
        text traceparent "W3C trace context, nullable"
        timestamptz created_at
    }
    deliveries {
        uuid id PK
        uuid tenant_id FK
        uuid event_id FK "UK (event_id, endpoint_id)"
        uuid endpoint_id FK
        text status "pending | in_flight | retrying | delivered | dead"
        smallint attempt_count ">= 0"
        timestamptz next_attempt_at "when the dispatcher may claim it"
        timestamptz locked_until "lease expiry, in_flight only"
        uuid lease_token "lease owner, in_flight only"
        smallint last_status_code "nullable"
        text last_error "nullable"
        timestamptz delivered_at "set iff delivered"
        timestamptz created_at
        timestamptz updated_at
    }
    delivery_attempts {
        bigint id PK "identity"
        uuid delivery_id FK "UK (delivery_id, attempt_number)"
        smallint attempt_number ">= 1"
        timestamptz started_at
        integer duration_ms ">= 0"
        text outcome "success | http_error | timeout | ..."
        smallint status_code "nullable"
        text response_excerpt "first 1 KB of the body"
        text error_message "nullable"
    }
    audit_log {
        bigint id PK "identity"
        timestamptz occurred_at
        text actor_type "operator | tenant | system"
        text actor_id
        uuid tenant_id FK "nullable"
        text action "e.g. delivery.replayed"
        text target_type
        text target_id
        jsonb details "default {}"
    }
```

How to read it:

- **Tenant isolation is enforced by the database.** `endpoints` and `events` expose a `UNIQUE (id, tenant_id)` key, and `subscriptions` and `deliveries` reference it with composite foreign keys `(endpoint_id, tenant_id)` / `(event_id, tenant_id)`. A delivery can't link an event of tenant A to an endpoint of tenant B.
- **Ingest is idempotent.** `UNIQUE (tenant_id, idempotency_key)` on `events` rejects replays of the same request, and `request_fingerprint` (a 32-byte hash of the request) lets ingest detect a key reused with a different body.
- **Fan-out:** one `deliveries` row per matching (event, endpoint), and `UNIQUE (event_id, endpoint_id)` makes duplicates impossible. Subscriptions match an exact `event_type` or `*`.
- **Delivery lifecycle:** `pending → in_flight → delivered`, or `→ retrying → in_flight → …` until it is `dead` (DLQ). CHECK constraints keep the state consistent: `lease_token` and `locked_until` are set **only** while `in_flight`, and `delivered_at` **only** when `delivered`. Every HTTP try is appended to `delivery_attempts`.
- **Hot-path indexes:** `deliveries_ready_idx` (partial, `pending`/`retrying` by `next_attempt_at`) serves the dispatcher's `FOR UPDATE SKIP LOCKED` claim; `deliveries_leased_idx` (partial, `in_flight` by `locked_until`) serves the reaper; `deliveries_tenant_idx` serves `GET /v1/deliveries?status=dead`.
- **Cascades:** deleting an event (retention, via `events_retention_idx`) removes its deliveries and their attempts. Endpoints are soft-deleted (`status = 'deleted'`), so their deliveries are kept for history.
- **Endpoint invariants:** `disabled_reason` is set if and only if `status = 'disabled'`, and `previous_secret_*` are both set or both null (the zero-downtime secret rotation window).

## Project docs

- [CONTRIBUTING.md](CONTRIBUTING.md): how to set up, branch, commit and open PRs
- [CHANGELOG.md](CHANGELOG.md): notable changes per release
- [SECURITY.md](SECURITY.md): how to report vulnerabilities

This project was generated with [Copier](https://copier.readthedocs.io/). Pull in template updates with `uvx copier update`.

## License

Distributed under the [MIT License](LICENSE). © 2026 Daniel Doblas Jimenez
