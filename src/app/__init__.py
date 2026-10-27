"""Reliable webhook delivery gateway backed by Postgres.

Postgres-backed queue with SKIP LOCKED leases, at-least-once delivery, Standard
Webhooks signatures, retries with jitter, DLQ and replay.
"""

from importlib.metadata import version

__version__ = version("pg-webhook-gateway")
