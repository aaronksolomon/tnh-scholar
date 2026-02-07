from dataclasses import dataclass
from enum import Enum


class YTPreflightSeverity(str, Enum):
    WARNING = "warning"


@dataclass(frozen=True)
class YTPreflightItem:
    """Structured preflight warning item for yt-dlp runtime checks."""

    code: str
    message: str
    severity: YTPreflightSeverity = YTPreflightSeverity.WARNING


@dataclass(frozen=True)
class YTPreflightReport:
    """Aggregated preflight report."""

    items: tuple[YTPreflightItem, ...]

    def has_items(self) -> bool:
        """Return True when preflight items exist."""
        return bool(self.items)
