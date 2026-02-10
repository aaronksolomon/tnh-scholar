"""Time helpers shared by orchestration components."""

from __future__ import annotations

from datetime import datetime, timezone


def local_now() -> datetime:
    """Return current local timestamp."""
    return datetime.now()


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)
