"""Shared user-facing prompt setup descriptions."""

from __future__ import annotations

from dataclasses import dataclass

from tnh_scholar.configuration.context import PromptDirectoryNames


@dataclass(frozen=True)
class PromptSetupDisplay:
    """Human-readable prompt setup descriptions for setup commands."""

    @classmethod
    def repo_workspace(cls) -> str:
        return f"{PromptDirectoryNames.workspace()}/ (repo-local default)"

    @classmethod
    def bundled_prompts(cls) -> str:
        return "built-in prompts bundled with the package"
