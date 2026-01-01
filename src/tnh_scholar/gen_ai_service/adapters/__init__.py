"""Adapters for easier migration from legacy interfaces."""

from typing import Any


def simple_completion(*args: Any, **kwargs: Any) -> Any:
    """Lazy wrapper to avoid import-time circular dependencies."""
    from .simple_completion import simple_completion as _simple_completion

    return _simple_completion(*args, **kwargs)


__all__ = ["simple_completion"]
