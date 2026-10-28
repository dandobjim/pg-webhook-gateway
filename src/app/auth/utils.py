"""API key generation and hashing helpers.

Keys have the form ``pwg_<env>_<key_id>_<secret>``. The ``pwg_<env>_<key_id>`` part
is the public prefix stored in ``api_keys.prefix`` for lookup; only the SHA-256
digest of the full key is persisted, in ``api_keys.key_hash``.
"""

import hashlib
import re
import secrets
import string

BASE62 = string.ascii_letters + string.digits
KEY_RE = re.compile(r"(?P<prefix>pwg_(?:live|test)_[A-Za-z0-9]{12})_[A-Za-z0-9]{40}")


def _rand(n: int) -> str:
    """Return a cryptographically secure random base62 string of length ``n``."""
    return "".join(secrets.choice(BASE62) for _ in range(n))


def hash_key(full_key: str) -> bytes:
    """Return the SHA-256 digest of ``full_key``, as stored in ``api_keys.key_hash``.

    Args:
        full_key: Plaintext key, including its prefix.

    Returns:
        The 32-byte raw digest.
    """
    return hashlib.sha256(full_key.encode()).digest()


def generate_key(env: str = "live") -> tuple[str, str, bytes]:
    """Generate a new API key with its lookup prefix and hash.

    The full key is only available at creation time; callers must show it to the
    user once and persist just the prefix and the hash.

    Args:
        env: Key environment, ``"live"`` or ``"test"``. Not validated; any other
            value yields a key that does not match ``KEY_RE``.

    Returns:
        A ``(full_key, prefix, key_hash)`` tuple, where ``full_key`` is the
        plaintext key handed to the client, ``prefix`` is ``pwg_<env>_<key_id>``
        and ``key_hash`` is the SHA-256 digest of ``full_key``.
    """
    prefix = f"pwg_{env}_{_rand(12)}"
    full_key = f"{prefix}_{_rand(40)}"
    return full_key, prefix, hash_key(full_key)
