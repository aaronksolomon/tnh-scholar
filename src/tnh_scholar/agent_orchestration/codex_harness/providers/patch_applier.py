"""Patch application provider for Codex harness."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from tnh_scholar.agent_orchestration.codex_harness.models import PatchApplyResult
from tnh_scholar.agent_orchestration.codex_harness.protocols import PatchApplierProtocol


@dataclass(frozen=True)
class GitPatchApplier(PatchApplierProtocol):
    """Apply unified diff patches using git."""

    def apply(self, patch: str) -> PatchApplyResult:
        """Apply the patch to the workspace."""
        process = subprocess.run(
            ["git", "apply", "--whitespace=fix", "-"],
            input=patch,
            text=True,
            capture_output=True,
            check=False,
        )
        return PatchApplyResult(
            applied=process.returncode == 0,
            stdout=process.stdout,
            stderr=process.stderr,
        )
