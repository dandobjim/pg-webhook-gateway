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
import pg_webhook_gateway

print(pg_webhook_gateway.__version__)
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
├── src/pg_webhook_gateway/ # package source code
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

## Project docs

- [CONTRIBUTING.md](CONTRIBUTING.md): how to set up, branch, commit and open PRs
- [CHANGELOG.md](CHANGELOG.md): notable changes per release
- [SECURITY.md](SECURITY.md): how to report vulnerabilities

This project was generated with [Copier](https://copier.readthedocs.io/). Pull in template updates with `uvx copier update`.

## License

Distributed under the [MIT License](LICENSE). © 2026 Daniel Doblas Jimenez
