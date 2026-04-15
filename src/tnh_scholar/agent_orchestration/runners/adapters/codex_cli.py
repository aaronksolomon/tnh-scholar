"""Codex CLI maintained runner adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from tnh_scholar.agent_orchestration.execution import (
    CliExecutableInvocation,
    ExecutionRequest,
    ExecutionResult,
    InheritParentEnvironmentPolicy,
    SubprocessExecutionService,
)
from tnh_scholar.agent_orchestration.execution_policy import (
    ApprovalPosture,
    ExecutionPosture,
)
from tnh_scholar.agent_orchestration.runners.adapters._shared import (
    build_transcript_artifact,
    resolve_executable_path,
    to_runner_termination,
)
from tnh_scholar.agent_orchestration.runners.models import (
    AdapterCapabilities,
    RunnerCaptureFormat,
    RunnerInvocationMetadata,
    RunnerInvocationMode,
    RunnerResult,
    RunnerTaskRequest,
    RunnerTextArtifact,
)
from tnh_scholar.agent_orchestration.runners.protocols import RunnerAdapterProtocol
from tnh_scholar.agent_orchestration.shared_enums import AgentFamily, RunnerTermination


@dataclass(frozen=True)
class CodexCliInvocationMapper:
    """Build execution requests for maintained Codex CLI runs."""

    executable: Path
    model_name: str = "gpt-5.2-codex"
    response_filename: str = "codex-last-message.txt"

    def map(self, request: RunnerTaskRequest) -> tuple[ExecutionRequest, Path]:
        """Map one runner request into a trusted execution request."""
        self._validate_policy(request)
        response_path = request.working_directory / self.response_filename
        return (
            ExecutionRequest(
                invocation=CliExecutableInvocation(
                    executable=self.executable,
                    arguments=self._arguments_for(request, response_path),
                ),
                working_directory=request.working_directory,
                environment_policy=InheritParentEnvironmentPolicy(),
            ),
            response_path,
        )

    def _validate_policy(self, request: RunnerTaskRequest) -> None:
        policy = request.requested_policy
        if policy.network_posture is not None:
            raise ValueError("Codex CLI adapter does not support native network posture controls.")
        if policy.allowed_paths not in (None, ()):
            raise ValueError("Codex CLI adapter does not support native allowed_paths constraints.")
        if policy.forbidden_paths:
            raise ValueError("Codex CLI adapter does not support native forbidden_paths constraints.")
        if policy.forbidden_operations:
            raise ValueError(
                "Codex CLI adapter does not support native forbidden_operations constraints."
            )
        if policy.approval_posture == ApprovalPosture.bounded_auto_approve:
            raise ValueError(
                "Codex CLI adapter does not support native bounded_auto_approve controls."
            )

    def _arguments_for(self, request: RunnerTaskRequest, response_path: Path) -> tuple[str, ...]:
        return (
            "exec",
            "--json",
            "--ephemeral",
            "--output-last-message",
            str(response_path),
            "--sandbox",
            self._sandbox_mode(request),
            "-m",
            self.model_name,
            request.rendered_task_text,
        )

    def _sandbox_mode(self, request: RunnerTaskRequest) -> str:
        match request.requested_policy.execution_posture:
            case ExecutionPosture.workspace_write:
                return "workspace-write"
            case None | ExecutionPosture.read_only:
                return "read-only"
            case _:
                raise ValueError(
                    "Unsupported execution posture for Codex CLI: "
                    f"{request.requested_policy.execution_posture!r}"
                )


@dataclass(frozen=True)
class CodexCliOutputNormalizer:
    """Normalize Codex CLI execution results into maintained runner results."""

    def normalize(
        self,
        *,
        request: RunnerTaskRequest,
        execution_result: ExecutionResult,
        response_path: Path,
        command: tuple[str, ...],
        started_at: datetime,
        ended_at: datetime,
    ) -> RunnerResult:
        """Normalize one execution result."""
        termination = to_runner_termination(execution_result.termination)
        transcript = self._transcript(execution_result.stdout_text)
        final_response = self._final_response(response_path)
        if execution_result.termination.value == "completed":
            termination = self._validate_required_artifacts(termination, transcript, final_response)
        return RunnerResult(
            termination=termination,
            metadata=self._metadata(request, command, execution_result, termination, started_at, ended_at),
            transcript=transcript,
            final_response=final_response,
        )

    def _metadata(
        self,
        request: RunnerTaskRequest,
        command: tuple[str, ...],
        execution_result: ExecutionResult,
        termination: RunnerTermination,
        started_at: datetime,
        ended_at: datetime,
    ) -> RunnerInvocationMetadata:
        return RunnerInvocationMetadata(
            agent_family=request.agent_family,
            invocation_mode=RunnerInvocationMode.codex_exec,
            command=command,
            working_directory=request.working_directory,
            prompt_reference=request.prompt_reference,
            started_at=started_at,
            ended_at=ended_at,
            exit_code=execution_result.exit_code,
            termination=termination,
            capture_format=RunnerCaptureFormat.ndjson,
        )

    def _validate_required_artifacts(
        self,
        termination: RunnerTermination,
        transcript: RunnerTextArtifact | None,
        final_response: RunnerTextArtifact | None,
    ) -> RunnerTermination:
        if transcript is None or final_response is None:
            return RunnerTermination.error
        return termination

    def _transcript(self, stdout_text: str) -> RunnerTextArtifact | None:
        return build_transcript_artifact(stdout_text)

    def _final_response(self, response_path: Path) -> RunnerTextArtifact | None:
        if not response_path.exists():
            return None
        content = response_path.read_text(encoding="utf-8").strip()
        if not content:
            return None
        return RunnerTextArtifact(
            filename="final_response.txt",
            content=f"{content}\n",
            media_type="text/plain",
        )


@dataclass(frozen=True)
class CodexCliRunnerAdapter(RunnerAdapterProtocol):
    """Execute maintained headless Codex CLI runs."""

    execution_service: SubprocessExecutionService
    executable: Path | None = None
    model_name: str = "gpt-5.2-codex"

    def agent_family(self) -> AgentFamily:
        """Return the maintained family served by this adapter."""
        return AgentFamily.codex_cli

    def capabilities(self) -> AdapterCapabilities:
        """Return the native capabilities for Codex CLI."""
        return AdapterCapabilities(
            agent_family=self.agent_family(),
            supports_workspace_write=True,
            supports_read_only=True,
            supports_structured_event_stream=True,
            supports_final_response_file=True,
            supports_native_approval_controls=False,
        )

    def run(self, request: RunnerTaskRequest) -> RunnerResult:
        """Execute one Codex CLI request."""
        executable = resolve_executable_path(self.executable, "codex")
        mapper = CodexCliInvocationMapper(executable=executable, model_name=self.model_name)
        started_at = datetime.now(timezone.utc)
        execution_request, response_path = mapper.map(request)
        execution_result = self.execution_service.run(execution_request)
        ended_at = datetime.now(timezone.utc)
        command = (str(executable), *execution_request.invocation.arguments)
        return CodexCliOutputNormalizer().normalize(
            request=request,
            execution_result=execution_result,
            response_path=response_path,
            command=command,
            started_at=started_at,
            ended_at=ended_at,
        )
