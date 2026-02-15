"""Shared helpers for resilient prompt body extraction."""

from __future__ import annotations

from typing import cast

from tnh_scholar.metadata.metadata import Frontmatter


def extract_best_effort_body(content: str) -> str:
    """Return prompt body even when frontmatter is missing or malformed."""
    cleaned = content.lstrip("\ufeff\n\r\t ")
    try:
        _, body = Frontmatter.extract(cleaned)
        if body:
            return cast(str, body).lstrip()
    except Exception:
        pass

    if cleaned.startswith("---"):
        parts = cleaned.split("---", 2)
        if len(parts) == 3:
            return parts[2].lstrip()
    return cleaned
