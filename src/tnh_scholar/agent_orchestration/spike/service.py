"""Spike run orchestration service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import partial
from pathlib import Path

from tnh_scholar.agent_orchestration.spike.models import (
    AgentRunResult,
    GitStatusSnapshot,
    RunArtifactPaths,
    RunEvent,
    RunEventType,
    RunMetadata,
    SpikeConfig,
    SpikeParams,
    SpikePolicy,
    SpikePreflightError,
    TerminationReason,
)
from tnh_scholar.agent_orchestration.spike.protocols import (
    AgentCommandBuilderProtocol,
    AgentRunnerProtocol,
    ArtifactWriterProtocol,
    ClockProtocol,
    EventWriterFactoryProtocol,
    EventWriterProtocol,
    PromptHandlerProtocol,
    RunIdGeneratorProtocol,
    WorkspaceCaptureProtocol,
)


@dataclass(frozen=True)
class SpikeRunService:
    """Orchestrate a single spike run."""

    clock: ClockProtocol
    run_id_generator: RunIdGeneratorProtocol
    agent_runner: AgentRunnerProtocol
    workspace: WorkspaceCaptureProtocol
    artifact_writer: ArtifactWriterProtocol
    event_writer_factory: EventWriterFactoryProtocol
    command_builder: AgentCommandBuilderProtocol
    prompt_handler: PromptHandlerProtocol

    def run(self, params: SpikeParams, *, config: SpikeConfig, policy: SpikePolicy) -> RunMetadata:
        context = self._init_context(params, config)
        self._preflight_sandbox_root(context, params, config)
        self._preflight_clean_workspace(context, params)
        git_pre = self._prepare_workspace(context, params)
        run_result = self._execute_agent(context, params, policy)
        git_post = self._capture_post(context, params)
        metadata = self._persist_metadata(context, params, git_pre, git_post, run_result)
        self._finalize_workspace(context.base_branch, context.work_branch, policy, run_result.termination_reason)
        return metadata

    def _build_artifact_paths(self, run_dir: Path) -> RunArtifactPaths:
        return RunArtifactPaths(
            transcript_raw=run_dir / "transcript.raw.log",
            transcript_normalized=run_dir / "transcript.md",
            stdout_log=run_dir / "stdout.log",
            stderr_log=run_dir / "stderr.log",
            git_pre=run_dir / "git_pre.json",
            git_post=run_dir / "git_post.json",
            diff_patch=run_dir / "diff.patch",
            run_metadata=run_dir / "run.json",
            events=run_dir / "events.ndjson",
        )

    def _resolve_work_branch(self, params: SpikeParams, config: SpikeConfig, run_id: str) -> str:
        if params.work_branch:
            return params.work_branch
        return f"{config.work_branch_prefix}/{run_id}"

    def _write_event(
        self,
        writer: EventWriterProtocol,
        run_id: str,
        event_type: RunEventType,
        agent: str,
        work_branch: str,
        *,
        artifact_paths: list[Path] | None = None,
        reason: str | None = None,
        exit_code: int | None = None,
        message: str | None = None,
    ) -> None:
        event = self._build_event(
            run_id,
            event_type,
            agent,
            work_branch,
            artifact_paths,
            reason,
            exit_code,
            message,
        )
        writer.write_event(event)

    def _build_event(
        self,
        run_id: str,
        event_type: RunEventType,
        agent: str,
        work_branch: str,
        artifact_paths: list[Path] | None,
        reason: str | None,
        exit_code: int | None,
        message: str | None,
    ) -> RunEvent:
        return RunEvent(
            run_id=run_id,
            timestamp=self.clock.now(),
            event_type=event_type,
            agent=agent,
            work_branch=work_branch,
            artifact_paths=artifact_paths or [],
            reason=reason,
            exit_code=exit_code,
            message=message,
        )

    def _write_snapshot(self, path: Path, snapshot: GitStatusSnapshot) -> None:
        self.artifact_writer.write_text(path, snapshot.model_dump_json(indent=2))

    def _write_transcripts(self, paths: RunArtifactPaths, result: AgentRunResult) -> None:
        self.artifact_writer.write_bytes(paths.transcript_raw, result.transcript_raw)
        self.artifact_writer.write_text(paths.transcript_normalized, result.transcript_text)
        self.artifact_writer.write_text(paths.stdout_log, result.stdout_text or "")
        self.artifact_writer.write_text(paths.stderr_log, result.stderr_text or "")

    def _build_metadata(
        self,
        *,
        run_id: str,
        params: SpikeParams,
        work_branch: str,
        artifact_paths: RunArtifactPaths,
        git_pre: GitStatusSnapshot,
        git_post: GitStatusSnapshot,
        termination: TerminationReason,
        exit_code: int | None,
        started_at: datetime,
    ) -> RunMetadata:
        return RunMetadata(
            run_id=run_id,
            started_at=started_at,
            ended_at=self.clock.now(),
            agent=params.agent,
            task=params.task,
            prompt_id=params.prompt_id,
            work_branch=work_branch,
            exit_code=exit_code,
            termination_reason=termination,
            artifact_paths=artifact_paths,
            git_pre_summary=git_pre,
            git_post_summary=git_post,
        )

    def _write_completion_event(
        self,
        writer,
        run_id: str,
        agent: str,
        work_branch: str,
        termination: TerminationReason,
        exit_code: int | None,
    ) -> None:
        event_type = self._completion_event_type(termination)
        reason = termination.value
        self._write_event(
            writer,
            run_id,
            event_type,
            agent,
            work_branch,
            reason=reason,
            exit_code=exit_code,
        )

    def _completion_event_type(self, termination: TerminationReason) -> RunEventType:
        if termination != TerminationReason.completed:
            return RunEventType.run_blocked
        return RunEventType.run_completed

    def _finalize_workspace(
        self,
        base_branch: str,
        work_branch: str,
        policy: SpikePolicy,
        termination: TerminationReason,
    ) -> None:
        if termination != TerminationReason.completed and policy.cleanup_on_failure:
            self.workspace.reset_hard()
        self.workspace.checkout_branch(base_branch)
        if termination != TerminationReason.completed and policy.cleanup_on_failure:
            self.workspace.delete_branch(work_branch)

    def _init_context(self, params: SpikeParams, config: SpikeConfig) -> RunContext:
        now = self.clock.now()
        run_id = self.run_id_generator.next_id(now=now)
        run_dir = self.artifact_writer.ensure_run_dir(run_id)
        artifact_paths = self._build_artifact_paths(run_dir)
        event_writer = self.event_writer_factory.create(artifact_paths.events)
        base_branch = self.workspace.current_branch()
        work_branch = self._resolve_work_branch(params, config, run_id)
        self._write_event(event_writer, run_id, RunEventType.run_started, params.agent, work_branch)
        return RunContext(
            run_id=run_id,
            started_at=now,
            artifact_paths=artifact_paths,
            event_writer=event_writer,
            base_branch=base_branch,
            work_branch=work_branch,
        )

    def _prepare_workspace(self, context: RunContext, params: SpikeParams) -> GitStatusSnapshot:
        self.workspace.create_work_branch(context.work_branch)
        git_pre = self.workspace.capture_status()
        self._write_snapshot(context.artifact_paths.git_pre, git_pre)
        self._write_event(
            context.event_writer,
            context.run_id,
            RunEventType.workspace_captured_pre,
            params.agent,
            context.work_branch,
            artifact_paths=[context.artifact_paths.git_pre],
        )
        return git_pre

    def _preflight_clean_workspace(self, context: RunContext, params: SpikeParams) -> None:
        status = self.workspace.capture_status()
        if status.is_clean:
            return
        message = self._worktree_guidance_message()
        self._write_event(
            context.event_writer,
            context.run_id,
            RunEventType.run_blocked,
            params.agent,
            context.work_branch,
            reason="dirty_worktree",
            message=message,
        )
        raise SpikePreflightError(message)

    def _worktree_guidance_message(self) -> str:
        return (
            "Spike preflight failed: worktree is not clean. "
            "Run the spike from a dedicated git worktree, e.g. "
            "`git worktree add ../tnh-scholar-sandbox` then run the CLI there."
        )

    def _preflight_sandbox_root(self, context: RunContext, params: SpikeParams, config: SpikeConfig) -> None:
        repo_root = self.workspace.repo_root()
        expected_root = self._expected_sandbox_root(repo_root, config)
        if repo_root == expected_root:
            return
        message = self._sandbox_root_message(repo_root, expected_root)
        self._write_event(
            context.event_writer,
            context.run_id,
            RunEventType.run_blocked,
            params.agent,
            context.work_branch,
            reason="sandbox_root_mismatch",
            message=message,
        )
        raise SpikePreflightError(message)

    def _expected_sandbox_root(self, repo_root: Path, config: SpikeConfig) -> Path:
        if config.sandbox_root is not None:
            return config.sandbox_root
        return repo_root.parent / f"{repo_root.name}-sandbox"

    def _sandbox_root_message(self, repo_root: Path, expected_root: Path) -> str:
        return (
            "Spike preflight failed: repo root does not match sandbox root. "
            f"repo_root={repo_root}, expected={expected_root}. "
            "Create or use the sandbox worktree and run the spike there."
        )

    def _execute_agent(
        self, context: RunContext, params: SpikeParams, policy: SpikePolicy
    ) -> AgentRunResult:
        command = self.command_builder.build(params)
        self._write_event(
            context.event_writer,
            context.run_id,
            RunEventType.agent_started,
            params.agent,
            context.work_branch,
        )
        on_heartbeat = partial(self._emit_heartbeat, context, params)
        on_output = partial(self._emit_agent_output, context, params, policy)
        run_result = self.agent_runner.run(
            command=command,
            timeout_seconds=params.timeout_seconds,
            idle_timeout_seconds=params.idle_timeout_seconds,
            heartbeat_interval_seconds=params.heartbeat_interval_seconds,
            prompt_handler=self.prompt_handler,
            on_heartbeat=on_heartbeat,
            on_output=on_output,
        )
        self._write_transcripts(context.artifact_paths, run_result)
        return run_result

    def _capture_post(self, context: RunContext, params: SpikeParams) -> GitStatusSnapshot:
        git_post = self.workspace.capture_status()
        diff = self.workspace.capture_diff()
        self._write_snapshot(context.artifact_paths.git_post, git_post)
        self.artifact_writer.write_text(context.artifact_paths.diff_patch, diff)
        self._write_post_events(context, params)
        return git_post

    def _write_post_events(self, context: RunContext, params: SpikeParams) -> None:
        self._write_event(
            context.event_writer,
            context.run_id,
            RunEventType.workspace_captured_post,
            params.agent,
            context.work_branch,
            artifact_paths=[context.artifact_paths.git_post],
        )
        self._write_event(
            context.event_writer,
            context.run_id,
            RunEventType.diff_emitted,
            params.agent,
            context.work_branch,
            artifact_paths=[context.artifact_paths.diff_patch],
        )

    def _emit_heartbeat(self, context: RunContext, params: SpikeParams) -> None:
        self._write_event(
            context.event_writer,
            context.run_id,
            RunEventType.heartbeat,
            params.agent,
            context.work_branch,
        )

    def _emit_agent_output(
        self,
        context: RunContext,
        params: SpikeParams,
        policy: SpikePolicy,
        text: str,
    ) -> None:
        message = self._truncate_output(text, policy.output_event_max_chars)
        if not message:
            return
        self._write_event(
            context.event_writer,
            context.run_id,
            RunEventType.agent_output,
            params.agent,
            context.work_branch,
            message=message,
        )

    def _truncate_output(self, text: str, max_chars: int) -> str:
        if max_chars <= 0:
            return ""
        if len(text) <= max_chars:
            return text
        return text[:max_chars]

    def _persist_metadata(
        self,
        context: RunContext,
        params: SpikeParams,
        git_pre: GitStatusSnapshot,
        git_post: GitStatusSnapshot,
        run_result: AgentRunResult,
    ) -> RunMetadata:
        metadata = self._build_metadata(
            run_id=context.run_id,
            params=params,
            work_branch=context.work_branch,
            artifact_paths=context.artifact_paths,
            git_pre=git_pre,
            git_post=git_post,
            termination=run_result.termination_reason,
            exit_code=run_result.exit_code,
            started_at=context.started_at,
        )
        self.artifact_writer.write_json(context.artifact_paths.run_metadata, metadata)
        self._write_completion_event(
            context.event_writer,
            context.run_id,
            params.agent,
            context.work_branch,
            run_result.termination_reason,
            run_result.exit_code,
        )
        return metadata


@dataclass(frozen=True)
class RunContext:
    """Context for a single spike run."""

    run_id: str
    started_at: datetime
    artifact_paths: RunArtifactPaths
    event_writer: EventWriterProtocol
    base_branch: str
    work_branch: str
