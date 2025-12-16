from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class OutputFormat(str, Enum):
    json = "json"
    yaml = "yaml"
    text = "text"


class ListOutputFormat(str, Enum):
    json = "json"
    yaml = "yaml"
    text = "text"
    table = "table"


@dataclass
class CLIContext:
    """Holds shared CLI state populated by the Typer callback."""

    config_path: Path | None = None
    output_format: OutputFormat = OutputFormat.json
    verbose: bool = False
    quiet: bool = False
    no_color: bool = False


ctx = CLIContext()
