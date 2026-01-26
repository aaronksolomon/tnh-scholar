"""Test runner provider for Codex harness."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from tnh_scholar.agent_orchestration.codex_harness.models import TestRunResult
from tnh_scholar.agent_orchestration.codex_harness.protocols import TestRunnerProtocol


@dataclass(frozen=True)
class ShellTestRunner(TestRunnerProtocol):
    """Run test commands via the shell."""

    def run(self, command: str, timeout_seconds: int) -> TestRunResult:
        """Execute a test command and capture results."""
        try:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
            return TestRunResult(
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            return TestRunResult(
                exit_code=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "Test command timed out.",
            )
