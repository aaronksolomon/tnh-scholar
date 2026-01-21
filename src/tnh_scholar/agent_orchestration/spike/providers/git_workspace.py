"""Git workspace capture provider for the spike."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.spike.models import GitStatusSnapshot
from tnh_scholar.agent_orchestration.spike.protocols import WorkspaceCaptureProtocol


@dataclass(frozen=True)
class GitWorkspaceCapture(WorkspaceCaptureProtocol):
    """Capture git workspace state and manage work branches."""

    def repo_root(self) -> Path:
        output = self._run_git(["rev-parse", "--show-toplevel"])
        return Path(output.strip())

    def current_branch(self) -> str:
        output = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        return output.strip()

    def create_work_branch(self, branch_name: str) -> None:
        self._run_git(["checkout", "-b", branch_name])

    def checkout_branch(self, branch_name: str) -> None:
        self._run_git(["checkout", branch_name])

    def delete_branch(self, branch_name: str) -> None:
        self._run_git(["branch", "-D", branch_name])

    def reset_hard(self) -> None:
        self._run_git(["reset", "--hard"])

    def capture_status(self) -> GitStatusSnapshot:
        branch = self.current_branch()
        lines = self._status_lines()
        staged, unstaged = self._count_changes(lines)
        is_clean = len(lines) == 0
        return GitStatusSnapshot(
            branch=branch,
            is_clean=is_clean,
            staged=staged,
            unstaged=unstaged,
            lines=lines,
        )

    def capture_diff(self) -> str:
        return self._run_git(["diff"])

    def _status_lines(self) -> list[str]:
        output = self._run_git(["status", "--porcelain"])
        return [line for line in output.splitlines() if line.strip()]

    def _count_changes(self, lines: list[str]) -> tuple[int, int]:
        staged = 0
        unstaged = 0
        for line in lines:
            if len(line) < 2:
                continue
            if line[0] != " ":
                staged += 1
            if line[1] != " ":
                unstaged += 1
        return staged, unstaged

    def _run_git(self, args: list[str]) -> str:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
