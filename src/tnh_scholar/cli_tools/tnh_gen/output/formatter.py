from __future__ import annotations

import json
from typing import Any, Iterable

import yaml

from tnh_scholar.cli_tools.tnh_gen.state import ListOutputFormat, OutputFormat


def render_output(payload: Any, fmt: OutputFormat | ListOutputFormat) -> str:
    if fmt == OutputFormat.json or fmt == ListOutputFormat.json:
        return json.dumps(payload, indent=2)
    if fmt == OutputFormat.yaml or fmt == ListOutputFormat.yaml:
        return yaml.safe_dump(payload, sort_keys=False)
    if fmt in (OutputFormat.text, ListOutputFormat.text):
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, indent=2)
    if fmt == ListOutputFormat.table:
        if isinstance(payload, str):
            return payload
        raise ValueError("Table formatting requires structured prompt data")
    raise ValueError(f"Unsupported format: {fmt}")


def format_table(headers: list[str], rows: Iterable[list[str]]) -> str:
    data = [headers, *list(rows)]
    widths = [max(len(row[idx]) for row in data) for idx in range(len(headers))]
    lines = []
    for row in data:
        padded = [cell.ljust(widths[idx]) for idx, cell in enumerate(row)]
        lines.append("  ".join(padded))
    return "\n".join(lines)
