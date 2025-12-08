"""Transport models for prompt system I/O."""

from pathlib import Path

from pydantic import BaseModel


class PromptFileRequest(BaseModel):
    """Transport-level request to load a prompt file."""

    path: Path
    commit_sha: str | None = None


class PromptFileResponse(BaseModel):
    """Transport-level prompt file data."""

    content: str
    metadata_raw: dict
    file_hash: str
    loaded_at: str


class GitRefreshRequest(BaseModel):
    """Request to refresh git repository."""

    repository_path: Path
    target_ref: str | None = None


class GitRefreshResponse(BaseModel):
    """Git refresh operation result."""

    current_commit: str
    branch: str
    changed_files: list[str]
    refreshed_at: str

