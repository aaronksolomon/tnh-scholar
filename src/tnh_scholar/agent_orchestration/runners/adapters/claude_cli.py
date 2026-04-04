"""Claude CLI maintained runner adapter."""

from __future__ import annotations

import json
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
class ClaudeCliInvocationMapper:
    """Build execution requests for maintained Claude CLI runs."""

    executable: Path

    def map(self, request: RunnerTaskRequest) -> ExecutionRequest:
        """Map one runner request into a trusted execution request."""
        self._validate_policy(request)
        arguments = self._arguments_for(request)
        return ExecutionRequest(
            invocation=CliExecutableInvocation(executable=self.executable, arguments=arguments),
            working_directory=request.working_directory,
            environment_policy=InheritParentEnvironmentPolicy(),
        )

    def _validate_policy(self, request: RunnerTaskRequest) -> None:
        policy = request.requested_policy
        match policy.execution_posture:
            case None | ExecutionPosture.workspace_write:
                pass
            case ExecutionPosture.read_only:
                raise ValueError("Claude CLI adapter cannot guarantee read_only execution posture.")
            case _:
                raise ValueError(
                    f"Unsupported execution posture for Claude CLI: {policy.execution_posture!r}"
                )
        if policy.network_posture is not None:
            raise ValueError("Claude CLI adapter does not support native network posture controls.")
        if policy.allowed_paths not in (None, ()):
            raise ValueError("Claude CLI adapter does not support native allowed_paths constraints.")
        if policy.forbidden_paths:
            raise ValueError("Claude CLI adapter does not support native forbidden_paths constraints.")
        if policy.forbidden_operations:
            raise ValueError(
                "Claude CLI adapter does not support native forbidden_operations constraints."
            )

    def _arguments_for(self, request: RunnerTaskRequest) -> tuple[str, ...]:
        return (
            "--print",
            "--output-format",
            "stream-json",
            "--permission-mode",
            self._permission_mode(request),
            request.rendered_task_text,
        )

    def _permission_mode(self, request: RunnerTaskRequest) -> str:
        match request.requested_policy.approval_posture:
            case None | ApprovalPosture.fail_on_prompt | ApprovalPosture.deny_interactive:
                return "dontAsk"
            case ApprovalPosture.bounded_auto_approve:
                return "acceptEdits"
            case _:
                raise ValueError(
                    "Unsupported approval posture for Claude CLI: "
                    f"{request.requested_policy.approval_posture!r}"
                )


@dataclass(frozen=True)
class ClaudeCliOutputNormalizer:
    """Normalize Claude CLI execution results into maintained runner results."""

    def normalize(
        self,
        *,
        request: RunnerTaskRequest,
        execution_result: ExecutionResult,
        command: tuple[str, ...],
        started_at: datetime,
        ended_at: datetime,
    ) -> RunnerResult:
        """Normalize one execution result."""
        termination = to_runner_termination(execution_result.termination)
        transcript = self._transcript(execution_result.stdout_text)
        final_response = self._final_response(execution_result.stdout_text)
        if execution_result.termination.value == "completed" and transcript is None:
            termination = RunnerTermination.error
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
            invocation_mode=RunnerInvocationMode.claude_print,
            command=command,
            working_directory=request.working_directory,
            prompt_reference=request.prompt_reference,
            started_at=started_at,
            ended_at=ended_at,
            exit_code=execution_result.exit_code,
            termination=termination,
            capture_format=RunnerCaptureFormat.ndjson,
        )

    def _transcript(self, stdout_text: str) -> RunnerTextArtifact | None:
        return build_transcript_artifact(stdout_text)

    def _final_response(self, stdout_text: str) -> RunnerTextArtifact | None:
        content = self._extract_final_response(stdout_text)
        if content is None:
            return None
        return RunnerTextArtifact(
            filename="final_response.txt",
            content=f"{content}\n",
            media_type="text/plain",
        )

    def _extract_final_response(self, stdout_text: str) -> str | None:
        parsed = [self._extract_text_candidate(line) for line in stdout_text.splitlines() if line.strip()]
        for candidate in reversed(parsed):
            if candidate:
                return candidate
        return None

    def _extract_text_candidate(self, line: str) -> str | None:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None
        return self._extract_from_payload(payload)

    def _extract_from_payload(self, payload: object) -> str | None:
        if not isinstance(payload, dict):
            return None
        if not self._is_final_response_payload(payload):
            return None
        for key in ("text", "result", "content"):
            candidate = payload.get(key)
            rendered = self._render_candidate(candidate)
            if rendered:
                return rendered
        return None

    def _is_final_response_payload(self, payload: dict[str, object]) -> bool:
        payload_type = payload.get("type")
        if payload_type in {"assistant", "assistant_message", "message", "result", "complete"}:
            return True
        message = payload.get("message")
        if isinstance(message, dict) and message.get("role") == "assistant":
            return True
        return False

    def _render_candidate(self, value: object) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for key in ("text", "output", "summary"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
        return None


@dataclass(frozen=True)
class ClaudeCliRunnerAdapter(RunnerAdapterProtocol):
    """Execute maintained headless Claude CLI runs."""

    execution_service: SubprocessExecutionService
    executable: Path | None = None

    def agent_family(self) -> AgentFamily:
        """Return the maintained family served by this adapter."""
        return AgentFamily.claude_cli

    def capabilities(self) -> AdapterCapabilities:
        """Return the native capabilities for Claude CLI."""
        return AdapterCapabilities(
            agent_family=self.agent_family(),
            supports_workspace_write=True,
            supports_read_only=False,
            supports_structured_event_stream=True,
            supports_final_response_file=False,
            supports_native_approval_controls=True,
        )

    def run(self, request: RunnerTaskRequest) -> RunnerResult:
        """Execute one Claude CLI request."""
        executable = resolve_executable_path(self.executable, "claude")
        mapper = ClaudeCliInvocationMapper(executable=executable)
        started_at = datetime.now(timezone.utc)
        execution_request = mapper.map(request)
        execution_result = self.execution_service.run(execution_request)
        ended_at = datetime.now(timezone.utc)
        command = (str(executable), *execution_request.invocation.arguments)
        return ClaudeCliOutputNormalizer().normalize(
            request=request,
            execution_result=execution_result,
            command=command,
            started_at=started_at,
            ended_at=ended_at,
        )
