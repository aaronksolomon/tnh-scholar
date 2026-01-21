"""Tests for the spike command filter."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tnh_scholar.agent_orchestration.spike.adapters.command_filter import RegexCommandFilter
from tnh_scholar.agent_orchestration.spike.models import (
    AgentRunResult,
    CommandFilterDecision,
    GitStatusSnapshot,
    RunEventType,
    SpikeConfig,
    SpikeParams,
    SpikePolicy,
    SpikePreflightError,
    TerminationReason,
)
from tnh_scholar.agent_orchestration.spike.policy import default_spike_policy
from tnh_scholar.agent_orchestration.spike.service import SpikeRunService


@pytest.mark.parametrize(
    ("command", "blocked"),
    [
        ("rm -rf ./tmp", True),
        ("rm -r docs", True),
        ("git reset --hard", True),
        ("git clean -fd", True),
        ("git clean -fdx", True),
        ("git checkout -- src/file.py", True),
        ("git restore --worktree src/file.py", True),
        ("git restore --staged src/file.py", True),
        ("git branch -D work/test", True),
        ("git rebase main", True),
        ("git merge main", True),
        ("git push --force", True),
        ("git push --force-with-lease", True),
        ("git commit -m \"msg\"", True),
        ("git push origin main", True),
        ("mv .git/HEAD /tmp/HEAD", True),
        ("cp .git/config /tmp/config", True),
        ("curl https://example.com", True),
        ("wget https://example.com", True),
        ("ssh user@host", True),
        ("scp file user@host:/tmp", True),
        ("rsync -av src/ dest/", True),
        ("pip install requests", True),
        ("poetry install", True),
        ("npm install", True),
        ("brew install jq", True),
        ("ls -la", False),
        ("git status", False),
    ],
)
def test_command_filter_patterns(command: str, blocked: bool) -> None:
    policy = default_spike_policy()
    command_filter = RegexCommandFilter(patterns=tuple(policy.blocked_command_patterns))
    decision = command_filter.evaluate(command)
    assert decision.blocked is blocked


def test_preflight_blocks_dirty_workspace() -> None:
    dirty_status = GitStatusSnapshot(
        branch="work/test",
        is_clean=False,
        staged=0,
        unstaged=1,
        lines=[" M README.md"],
    )
    service = SpikeRunService(
        clock=_FakeClock(),
        run_id_generator=_FakeRunIdGenerator(),
        agent_runner=_FakeAgentRunner(),
        workspace=_FakeWorkspace(dirty_status, Path("/tmp/tnh-scholar-sandbox")),
        artifact_writer=_FakeArtifactWriter(),
        event_writer_factory=_FakeEventWriterFactory(),
        command_builder=_FakeCommandBuilder(),
        prompt_handler=_FakePromptHandler(),
    )
    params = SpikeParams(agent="claude-code", task="noop")
    config = SpikeConfig(
        runs_root=Path("/tmp"),
        work_branch_prefix="work",
        sandbox_root=Path("/tmp/tnh-scholar-sandbox"),
    )
    policy = SpikePolicy()
    with pytest.raises(SpikePreflightError):
        service.run(params, config=config, policy=policy)
    assert service.event_writer_factory.writer is not None
    events = service.event_writer_factory.writer.events
    assert events
    assert events[-1].event_type == RunEventType.run_blocked
    assert events[-1].reason == "dirty_worktree"


def test_preflight_blocks_wrong_sandbox_root() -> None:
    clean_status = GitStatusSnapshot(
        branch="work/test",
        is_clean=True,
        staged=0,
        unstaged=0,
        lines=[],
    )
    service = SpikeRunService(
        clock=_FakeClock(),
        run_id_generator=_FakeRunIdGenerator(),
        agent_runner=_FakeAgentRunner(),
        workspace=_FakeWorkspace(clean_status, Path("/tmp/tnh-scholar")),
        artifact_writer=_FakeArtifactWriter(),
        event_writer_factory=_FakeEventWriterFactory(),
        command_builder=_FakeCommandBuilder(),
        prompt_handler=_FakePromptHandler(),
    )
    params = SpikeParams(agent="claude-code", task="noop")
    config = SpikeConfig(
        runs_root=Path("/tmp"),
        work_branch_prefix="work",
        sandbox_root=Path("/tmp/tnh-scholar-sandbox"),
    )
    policy = SpikePolicy()
    with pytest.raises(SpikePreflightError):
        service.run(params, config=config, policy=policy)
    assert service.event_writer_factory.writer is not None
    events = service.event_writer_factory.writer.events
    assert events[-1].event_type == RunEventType.run_blocked
    assert events[-1].reason == "sandbox_root_mismatch"


@dataclass(frozen=True)
class _FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 1, 20, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _FakeRunIdGenerator:
    def next_id(self, *, now: datetime) -> str:
        return "run-1"


@dataclass(frozen=True)
class _FakeAgentRunner:
    def run(
        self,
        *,
        command: list[str],
        timeout_seconds: int,
        idle_timeout_seconds: int,
        heartbeat_interval_seconds: int,
        prompt_handler,
        on_heartbeat,
        on_output,
    ) -> AgentRunResult:
        return AgentRunResult(
            exit_code=0,
            termination_reason=TerminationReason.completed,
            transcript_raw=b"",
            transcript_text="",
            command_decision=None,
        )


@dataclass(frozen=True)
class _FakeWorkspace:
    status: GitStatusSnapshot
    root: Path

    def repo_root(self) -> Path:
        return self.root

    def current_branch(self) -> str:
        return self.status.branch

    def create_work_branch(self, branch_name: str) -> None:
        raise AssertionError("preflight should block before branch creation")

    def checkout_branch(self, branch_name: str) -> None:
        raise AssertionError("preflight should block before checkout")

    def delete_branch(self, branch_name: str) -> None:
        raise AssertionError("preflight should block before delete")

    def reset_hard(self) -> None:
        raise AssertionError("preflight should block before reset")

    def capture_status(self) -> GitStatusSnapshot:
        return self.status

    def capture_diff(self) -> str:
        return ""


@dataclass(frozen=True)
class _FakeArtifactWriter:
    def ensure_run_dir(self, run_id: str) -> Path:
        return Path("/tmp")

    def write_text(self, path: Path, content: str) -> None:
        return None

    def write_bytes(self, path: Path, content: bytes) -> None:
        return None

    def write_json(self, path: Path, payload) -> None:
        return None


@dataclass
class _FakeEventWriter:
    events: list

    def write_event(self, event) -> None:
        self.events.append(event)


@dataclass
class _FakeEventWriterFactory:
    writer: _FakeEventWriter | None = None

    def create(self, events_path: Path):
        self.writer = _FakeEventWriter(events=[])
        return self.writer


@dataclass(frozen=True)
class _FakeCommandBuilder:
    def build(self, params: SpikeParams) -> list[str]:
        return ["true"]


@dataclass(frozen=True)
class _FakePromptHandler:
    def handle_output(self, text: str):
        return CommandFilterDecision(command="noop", blocked=False)
