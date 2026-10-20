---
name: google-docstrings
description: >
  Google-style docstrings for Python modules, classes, functions and methods,
  enforced by ruff (pydocstyle, convention = "google"). Trigger: when writing or
  documenting Python code ("documentá", "docstring", "document this method").
---

# Google-style Docstrings

All public modules, classes, functions and methods in `src/` get a Google-style
docstring in **English**. Ruff enforces it (`D` rules, `convention = "google"`);
tests are exempt.

## Core rules

1. Triple double quotes `"""`. Summary on the first line, right after the quotes.
2. Summary: one line, imperative mood ("Return", "Acquire", not "Returns"), ends
   with a period, ≤ 88 chars.
3. Blank line between summary and the rest.
4. **No types** in `Args:` / `Returns:` — signatures are fully typed (mypy strict).
   The docstring explains MEANING, constraints and units, not types.
5. Section order: `Args:`, `Returns:` / `Yields:`, `Raises:`, `Example:` /
   `Examples:`, `Note:`. Omit empty sections.
6. Section items indented 4 spaces; continuation lines indented 4 more.
7. Document behavior that is not obvious: side effects, idempotency, concurrency,
   transactions, timeouts, units (seconds, ms).
8. Don't restate the code. `get_id() -> "Get the id."` adds nothing; skip extended
   description when the summary says it all.

## Function

```python
def compute_backoff(attempt: int, base: float = 1.0, cap: float = 300.0) -> float:
    """Compute the retry delay using exponential backoff with full jitter.

    Args:
        attempt: Zero-based delivery attempt number.
        base: Base delay in seconds for the first retry.
        cap: Maximum delay in seconds.

    Returns:
        Delay in seconds, uniformly distributed in ``[0, min(cap, base * 2**attempt)]``.

    Raises:
        ValueError: If ``attempt`` is negative.

    Examples:
        >>> 0.0 <= compute_backoff(3) <= 8.0
        True
    """
```

## Async function

Document it as a regular function; mention I/O and transactional behavior.

```python
async def acquire_leases(
    conn: AsyncConnection, limit: int, ttl: float
) -> list[Delivery]:
    """Lease up to ``limit`` pending deliveries for this worker.

    Uses ``SELECT ... FOR UPDATE SKIP LOCKED`` so concurrent workers never lease
    the same row.

    Args:
        conn: Open connection; the lease is committed before returning.
        limit: Maximum number of deliveries to lease.
        ttl: Lease duration in seconds before the row becomes visible again.

    Returns:
        Leased deliveries, oldest first. Empty if nothing is due.
    """
```

## Generator

Use `Yields:` instead of `Returns:`.

```python
def iter_batches(items: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    """Split ``items`` into consecutive batches.

    Args:
        items: Items to split.
        size: Maximum batch size; must be positive.

    Yields:
        Consecutive slices of at most ``size`` items.
    """
```

## Class

Class docstring documents the class AND the `__init__` arguments (`D107` is ignored,
so `__init__` needs no docstring). Public attributes go in `Attributes:`.

```python
class WebhookSigner:
    """Sign payloads following the Standard Webhooks specification.

    Args:
        secret: Base64-encoded signing secret, with optional ``whsec_`` prefix.

    Attributes:
        key_id: Identifier of the secret, sent in the ``webhook-id`` header.
    """

    def __init__(self, secret: str) -> None: ...
```

Dataclasses / Pydantic models: list fields under `Attributes:`.

## Method

Same as functions; never document `self` / `cls`.

```python
    def sign(self, msg_id: str, timestamp: int, payload: bytes) -> str:
        """Return the ``webhook-signature`` header value for a payload.

        Args:
            msg_id: Unique message identifier.
            timestamp: Unix timestamp in seconds.
            payload: Raw request body exactly as sent.

        Returns:
            Signature in the form ``v1,<base64>``.
        """
```

## Property

Summary is a noun phrase describing the value; no `Returns:` section.

```python
    @property
    def is_expired(self) -> bool:
        """Whether the lease TTL has elapsed."""
```

## Protocol / abstract method

Describe the CONTRACT every implementation must honor.

```python
class DeliveryRepository(Protocol):
    """Persistence port for webhook deliveries."""

    async def mark_failed(self, delivery_id: UUID, error: str) -> None:
        """Record a failed attempt and schedule the next retry or move to the DLQ.

        Implementations must be idempotent for the same ``delivery_id`` and attempt.

        Args:
            delivery_id: Delivery to update.
            error: Human-readable failure reason, truncated by the implementation.
        """
```

## Module

First statement of the file; one summary line, optional description.

```python
"""Postgres-backed delivery queue with SKIP LOCKED leases."""
```

`__init__.py` packages also get a one-line module docstring.

## Checklist

- [ ] English, imperative summary ending with a period
- [ ] Sections in order, no types repeated from the signature
- [ ] `Raises:` lists every exception intentionally raised
- [ ] `__init__` args documented in the class docstring
- [ ] Doctest examples (`>>>`) are correct if present
- [ ] `uv run ruff check <file>` passes (suggest it to the user; don't run builds)
