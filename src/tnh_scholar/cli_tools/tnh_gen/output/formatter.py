from __future__ import annotations

import json
from typing import Any, Iterable

import yaml

from tnh_scholar.cli_tools.tnh_gen.state import ListOutputFormat, OutputFormat


def render_output(payload: Any, fmt: OutputFormat | ListOutputFormat) -> str:
    """Serialize payload to the requested output format.

    Args:
        payload: Data to serialize.
        fmt: Output format enum selection.

    Returns:
        Serialized string representation for CLI display.

    Raises:
        ValueError: If the requested format is unsupported.
    """
    if fmt in [OutputFormat.json, ListOutputFormat.json]:
        return json.dumps(payload, indent=2)
    if fmt in [OutputFormat.yaml, ListOutputFormat.yaml]:
        return yaml.safe_dump(payload, sort_keys=False)
    if fmt in (OutputFormat.text, ListOutputFormat.text):
        return payload if isinstance(payload, str) else json.dumps(payload, indent=2)
    if fmt == ListOutputFormat.table:
        if isinstance(payload, str):
            return payload
        raise ValueError("Table formatting requires structured prompt data")
    raise ValueError(f"Unsupported format: {fmt}")


def format_table(headers: list[str], rows: Iterable[list[str]]) -> str:
    """Render a simple fixed-width table for CLI display.

    Args:
        headers: Column headers.
        rows: Row data to render.

    Returns:
        Rendered table string.
    """
    data = [headers, *list(rows)]
    widths = [max(len(row[idx]) for row in data) for idx in range(len(headers))]
    lines = []
    for row in data:
        padded = [cell.ljust(widths[idx]) for idx, cell in enumerate(row)]
        lines.append("  ".join(padded))
    return "\n".join(lines)
