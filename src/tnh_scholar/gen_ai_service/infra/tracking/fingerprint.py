"""
Deterministic hashing utilities for pattern provenance (V1).

Algorithm summary
-----------------
- All digests are SHA-256 of UTF-8 bytes and returned as "sha256:<hex>".
- Variables are canonicalized to JSON with:
  * dict keys sorted (sort_keys=True)
  * compact separators (",", ":")
  * ensure_ascii=False (preserve non-ASCII)
- Canonicalization coercions (recursive):
  * Path           -> str(path)
  * Enum           -> enum.value
  * datetime/date/time -> ISO-8601 string (UTC if applicable; naive preserved)
  * set            -> sorted list
  * bytes          -> str(obj)  (V1 rule for "custom objects" -> str(obj))
  * other objects  -> str(obj)  (V1 rule)
- Hash sources:
  * pattern bytes: exact on-disk template bytes (including front-matter)
  * vars: canonicalized JSON bytes of variables
  * user prompt: UTF-8 bytes of the raw string
"""

from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum
from hashlib import sha256
from json import dumps
from pathlib import Path
from typing import Any, Mapping

RenderVars = Mapping[str, Any]

__all__ = [
    "sha256_bytes",
    "hash_user_string",
    "hash_vars",
    "hash_prompt_bytes",
]


def sha256_bytes(b: bytes) -> str:
    """
    Return a SHA-256 digest string for raw bytes, prefixed with the algorithm.
    Example: "sha256:4a...ff"
    """
    return f"sha256:{sha256(b).hexdigest()}"


def hash_prompt_bytes(b: bytes) -> str:
    """
    Fingerprint over the exact template file bytes (including front-matter).
    """
    return sha256_bytes(b)


def hash_user_string(s: str) -> str:
    """
    Fingerprint over the raw user prompt string (UTF-8 encoded).
    """
    return sha256_bytes(s.encode("utf-8"))


def hash_vars(d: RenderVars) -> str:
    """
    Fingerprint over canonicalized variables.
    """
    canonical_bytes = _to_json_canonical_bytes(_coerce(d))
    return sha256_bytes(canonical_bytes)


# ---------- internal helpers ----------

def _coerce(x: Any) -> Any:
    """
    Recursively coerce values to JSON-encodable canonical forms.

    Rules (V1):
    - Mapping        -> dict with coerced keys (as str) and values; keys will be sorted at dump time
    - Sequence       -> list of coerced elements (tuples become lists)
    - Set            -> sorted list of coerced elements (stringified for consistent ordering)
    - Path           -> str(path)
    - Enum           -> enum.value
    - datetime/date/time -> ISO-8601 string
    - bytes          -> str(obj)
    - Other non-JSON types -> str(obj)
    """
    # Use isinstance checks instead of structural pattern matching. Some
    # typing objects (e.g. typing.Mapping) are not real classes and cause
    # `TypeError: called match pattern must be a class` when used in `case`.
    from collections.abc import Mapping as _Mapping

    if isinstance(x, _Mapping):
        # keys must be JSON-serializable; coerce to str for stability
        return {str(k): _coerce(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_coerce(v) for v in x]
    if isinstance(x, set):
        coerced = [_coerce(v) for v in x]
        return sorted(coerced, key=_stable_key)
    if isinstance(x, Path):
        return str(x)
    if isinstance(x, Enum):
        return x.value
    if isinstance(x, (datetime, date, time)):
        return x.isoformat()
    if isinstance(x, (bytes, bytearray, memoryview)):
        return str(x)
    return x if x is None or isinstance(x, (str, int, float, bool)) else str(x)


def _stable_key(v: Any) -> str:
    """
    Convert a value to a deterministic string key for ordering in sets.
    The value is dumped with the same JSON canonicalization used for hashing.
    """
    return _to_json_canonical_str(_coerce(v))


def _to_json_canonical_bytes(obj: Any) -> bytes:
    """
    Dump to canonical JSON bytes according to ADR rules.
    """
    s = dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def _to_json_canonical_str(obj: Any) -> str:
    """
    Dump to canonical JSON string according to ADR rules.
    """
    return dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
