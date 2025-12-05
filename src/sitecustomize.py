"""Project-wide Python startup configuration."""
from __future__ import annotations

import warnings

TARGET_MODULES = (
    r"mkdocstrings.*",
    r"mkdocstrings_handlers.*",
    r"mkdocs_autorefs.*",
)


def _install_filters() -> None:
    for module_pattern in TARGET_MODULES:
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            module=module_pattern,
        )


_install_filters()
_original_simplefilter = warnings.simplefilter


def _simplefilter_with_reinstall(
    action,
    category=Warning,
    lineno: int = 0,
    append: bool = False,
):
    _original_simplefilter(action, category=category, lineno=lineno, append=append)
    _install_filters()


warnings.simplefilter = _simplefilter_with_reinstall
