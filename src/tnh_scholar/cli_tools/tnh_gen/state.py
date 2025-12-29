from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from tnh_scholar.cli_tools.tnh_gen.factory import ServiceFactory


class OutputFormat(str, Enum):
    """Supported output formats for primary CLI commands."""

    json = "json"
    yaml = "yaml"
    text = "text"


class ListOutputFormat(str, Enum):
    """Output formats available for prompt listing."""

    json = "json"
    yaml = "yaml"
    text = "text"
    table = "table"


@dataclass
class CLIContext:
    """Holds shared CLI state populated by the Typer callback."""

    config_path: Path | None = None
    output_format: OutputFormat | None = None
    api: bool = False
    quiet: bool = False
    no_color: bool = False
    service_factory: "ServiceFactory | None" = None


def _create_default_factory() -> "ServiceFactory":
    """Lazy factory creation to avoid circular imports."""
    from tnh_scholar.cli_tools.tnh_gen.factory import DefaultServiceFactory

    return DefaultServiceFactory()


ctx = CLIContext()
