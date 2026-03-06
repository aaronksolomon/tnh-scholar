"""Run id helpers shared by orchestration components."""

from __future__ import annotations

from datetime import datetime


def strftime_run_id(now: datetime, format_string: str) -> str:
    """Return run id generated from timestamp and format."""
    return now.strftime(format_string)
