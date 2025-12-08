"""Construction-time configuration models for prompt catalog and transports."""

from pathlib import Path

from pydantic import BaseModel


class PromptCatalogConfig(BaseModel):
    """Configuration for building a prompt catalog."""

    repository_path: Path
    enable_git_refresh: bool = True
    cache_ttl_s: int = 300
    validation_on_load: bool = True


class GitTransportConfig(BaseModel):
    """Git transport layer configuration."""

    repository_path: Path
    auto_pull: bool = False
    pull_timeout_s: float = 30.0
    default_branch: str = "main"

