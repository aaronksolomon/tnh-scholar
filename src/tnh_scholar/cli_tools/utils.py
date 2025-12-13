from __future__ import annotations

from typing import Callable, NoReturn, TypeVar

import click

from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)

T = TypeVar("T")


def handle_cli_exception(message: str, exc: Exception) -> NoReturn:
    """Convert unexpected errors to Click-friendly messages."""
    if isinstance(exc, click.ClickException):
        raise exc

    logger.debug(message, exc_info=exc)
    raise click.ClickException(f"{message}: {exc}") from exc


def run_or_fail(message: str, operation: Callable[[], T]) -> T:
    """
    Execute an operation and re-raise failures as Click exceptions to avoid stack traces.
    """
    try:
        return operation()
    except Exception as exc:  # pragma: no cover - handled by wrapper
        handle_cli_exception(message, exc)
