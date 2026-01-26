"""Protocol definitions for the Codex harness."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

from tnh_scholar.agent_orchestration.codex_harness.models import (
    CodexRequest,
    CodexResponseText,
    PatchApplyResult,
    TestRunResult,
)
from tnh_scholar.agent_orchestration.codex_harness.tools import ToolCall, ToolDefinition, ToolResult


class ClockProtocol(Protocol):
    """Abstraction for time sourcing."""

    def now(self) -> datetime:
        """Return the current timestamp."""


class RunIdGeneratorProtocol(Protocol):
    """Generate run identifiers."""

    def next_id(self, *, now: datetime) -> str:
        """Return a new run id."""


class ArtifactWriterProtocol(Protocol):
    """Persist run artifacts to disk."""

    def ensure_run_dir(self, run_id: str) -> Path:
        """Ensure the run directory exists and return it."""

    def write_text(self, path: Path, content: str) -> None:
        """Write text content to a file."""

    def write_json(self, path: Path, payload: object) -> None:
        """Write JSON content to a file."""


class ToolRegistryProtocol(Protocol):
    """Registry for tool definitions and execution."""

    def definitions(self) -> list[ToolDefinition]:
        """Return tool definitions."""

    def execute(self, call: ToolCall) -> ToolResult:
        """Execute tool call."""


class ResponsesClientProtocol(Protocol):
    """Call the OpenAI Responses API."""

    def run(self, request: CodexRequest, tool_registry: ToolRegistryProtocol) -> CodexResponseText:
        """Execute the request and return response text."""


class PatchApplierProtocol(Protocol):
    """Apply unified diff patches."""

    def apply(self, patch: str) -> PatchApplyResult:
        """Apply the patch to the workspace."""


class TestRunnerProtocol(Protocol):
    """Run test commands."""

    def run(self, command: str, timeout_seconds: int) -> TestRunResult:
        """Execute a test command and capture results."""


class ToolExecutorProtocol(Protocol):
    """Execute tool calls for the Codex harness."""

    def execute(self, call: ToolCall) -> ToolResult:
        """Execute the tool call and return output."""


class WorkspaceLocatorProtocol(Protocol):
    """Locate the repository root for tools."""

    def repo_root(self) -> Path:
        """Return the repository root."""


class SearcherProtocol(Protocol):
    """Search for text in the repository."""

    def search(self, query: str, root: Path) -> list[str]:
        """Return matching lines for the query."""
