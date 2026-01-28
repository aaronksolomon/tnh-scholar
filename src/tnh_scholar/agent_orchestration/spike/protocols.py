"""Protocol definitions for the Phase 0 spike."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Protocol

from tnh_scholar.agent_orchestration.spike.models import (
    AgentRunResult,
    CommandFilterDecision,
    CommandPromptMatch,
    GitStatusSnapshot,
    PromptHandlingOutcome,
    RunEvent,
    RunMetadata,
    SpikeParams,
)


class ClockProtocol(Protocol):
    """Abstraction for time sourcing."""

    def now(self) -> datetime:
        """Return the current timestamp."""


class RunIdGeneratorProtocol(Protocol):
    """Generate run identifiers."""

    def next_id(self, *, now: datetime) -> str:
        """Return a new run id."""


class CommandFilterProtocol(Protocol):
    """Evaluate whether a command should be blocked."""

    def evaluate(self, command: str) -> CommandFilterDecision:
        """Return a decision for the provided command."""


class CommandPromptParserProtocol(Protocol):
    """Parse command confirmation prompts."""

    def parse(self, text: str) -> CommandPromptMatch | None:
        """Parse a prompt from text, if present."""


class PromptHandlerProtocol(Protocol):
    """Handle confirmation prompts from agent output."""

    def handle_output(self, text: str) -> PromptHandlingOutcome:
        """Process output text and return handling instructions."""


class AgentRunnerProtocol(Protocol):
    """Run an agent command and capture output."""

    def run(
        self,
        *,
        command: list[str],
        timeout_seconds: int,
        idle_timeout_seconds: int,
        heartbeat_interval_seconds: int,
        prompt_handler: PromptHandlerProtocol,
        on_heartbeat: Callable[[], None] | None,
        on_output: Callable[[str], None] | None,
    ) -> AgentRunResult:
        """Execute the agent command."""


class WorkspaceCaptureProtocol(Protocol):
    """Capture git workspace details."""

    def repo_root(self) -> Path:
        """Return the repo root path."""

    def current_branch(self) -> str:
        """Return the current branch name."""

    def create_work_branch(self, branch_name: str) -> None:
        """Create and checkout a work branch."""

    def checkout_branch(self, branch_name: str) -> None:
        """Checkout the specified branch."""

    def delete_branch(self, branch_name: str) -> None:
        """Delete a branch."""

    def reset_hard(self) -> None:
        """Reset the current worktree to HEAD."""

    def capture_status(self) -> GitStatusSnapshot:
        """Capture git status snapshot."""

    def capture_diff(self) -> str:
        """Capture unified diff for the worktree."""


class ArtifactWriterProtocol(Protocol):
    """Persist run artifacts to disk."""

    def ensure_run_dir(self, run_id: str) -> Path:
        """Ensure the run directory exists and return it."""

    def write_text(self, path: Path, content: str) -> None:
        """Write text content to a file."""

    def write_bytes(self, path: Path, content: bytes) -> None:
        """Write bytes content to a file."""

    def write_json(self, path: Path, payload: RunMetadata) -> None:
        """Write JSON content to a file."""


class EventWriterProtocol(Protocol):
    """Write NDJSON event streams."""

    def write_event(self, event: RunEvent) -> None:
        """Write a single event."""


class EventWriterFactoryProtocol(Protocol):
    """Create event writers for runs."""

    def create(self, events_path: Path) -> EventWriterProtocol:
        """Create an event writer for the given path."""


class AgentCommandBuilderProtocol(Protocol):
    """Build agent command line invocation."""

    def build(self, params: SpikeParams) -> list[str]:
        """Build a command for the agent."""
