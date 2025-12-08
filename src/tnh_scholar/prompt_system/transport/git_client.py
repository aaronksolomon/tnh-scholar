"""Git transport client for prompt files."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config.prompt_catalog_config import GitTransportConfig
from ..mappers.prompt_mapper import PromptMapper
from ..transport.models import GitRefreshResponse, PromptFileRequest, PromptFileResponse


class GitTransportClient:
    """Minimal git transport operations."""

    def __init__(self, config: GitTransportConfig, mapper: PromptMapper):
        self._config = config
        self._mapper = mapper

    def get_current_commit(self) -> str:
        return (
            self._run_git(["rev-parse", "HEAD"], cwd=self._config.repository_path)
            .strip()
        )

    def pull_latest(self) -> GitRefreshResponse:
        if not self._config.auto_pull:
            return GitRefreshResponse(
                current_commit=self.get_current_commit(),
                branch=self._current_branch(),
                changed_files=[],
                refreshed_at=self._now_iso(),
            )
        self._run_git(
            ["pull"],
            cwd=self._config.repository_path,
            timeout=self._config.pull_timeout_s,
        )
        return GitRefreshResponse(
            current_commit=self.get_current_commit(),
            branch=self._current_branch(),
            changed_files=self._changed_files(),
            refreshed_at=self._now_iso(),
        )

    def read_file_at_commit(self, request: PromptFileRequest) -> PromptFileResponse:
        if request.commit_sha:
            spec = f"{request.commit_sha}:{request.path}"
            content = self._run_git(
                ["show", spec], cwd=self._config.repository_path
            )
        else:
            content = request.path.read_text(encoding="utf-8")

        metadata_raw, _ = self._mapper._split_frontmatter(content)
        return PromptFileResponse(
            content=content,
            metadata_raw=metadata_raw,
            file_hash=self._hash_content(content),
            loaded_at=self._now_iso(),
        )

    def list_files(self, pattern: str = "**/*.md") -> list[Path]:
        return sorted(self._config.repository_path.glob(pattern))

    def _current_branch(self) -> str:
        return (
            self._run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=self._config.repository_path)
            .strip()
        )

    def _changed_files(self) -> list[str]:
        try:
            output = self._run_git(
                ["diff", "--name-only", "HEAD@{1}", "HEAD"],
                cwd=self._config.repository_path,
            )
            return [line for line in output.splitlines() if line]
        except RuntimeError:
            return []

    def _run_git(self, args: list[str], cwd: Path, timeout: float | None = None) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout

    def _hash_content(self, content: str) -> str:
        import hashlib

        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _now_iso(self) -> str:
        import datetime as dt

        return dt.datetime.now(dt.timezone.utc).isoformat()
