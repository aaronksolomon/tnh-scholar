"""Service orchestrator for the Codex harness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tnh_scholar.agent_orchestration.codex_harness.adapters.output_parser import CodexOutputParser
from tnh_scholar.agent_orchestration.codex_harness.models import (
    CodexMessage,
    CodexOutputStatus,
    CodexRequest,
    CodexRunArtifacts,
    CodexRunConfig,
    CodexRunMetadata,
    CodexRunParams,
    CodexRunStatus,
    CodexStructuredOutput,
)
from tnh_scholar.agent_orchestration.codex_harness.protocols import (
    ArtifactWriterProtocol,
    ClockProtocol,
    PatchApplierProtocol,
    ResponsesClientProtocol,
    RunIdGeneratorProtocol,
    ToolRegistryProtocol,
    TestRunnerProtocol,
)
from tnh_scholar.logging_config import get_logger


@dataclass(frozen=True)
class CodexHarnessService:
    """Coordinate Codex harness execution and artifacts."""

    clock: ClockProtocol
    run_id_generator: RunIdGeneratorProtocol
    responses_client: ResponsesClientProtocol
    artifact_writer: ArtifactWriterProtocol
    output_parser: CodexOutputParser
    patch_applier: PatchApplierProtocol
    test_runner: TestRunnerProtocol
    tool_registry: ToolRegistryProtocol

    def run(self, params: CodexRunParams, config: CodexRunConfig) -> CodexRunMetadata:
        """Execute a Codex harness run."""
        logger = get_logger(__name__)
        context = self._initialize_run(params, config)
        response_text = self._capture_response(context)
        output = self._parse_output(context, response_text)
        if output is None:
            logger.error("codex-harness-parse-failed")
            return self._write_blocked(context, response_text.text)
        patch_applied = self._apply_patch_if_needed(output, params, context.artifacts)
        test_exit_code = self._run_tests_if_needed(params, context.artifacts)
        status = self._resolve_run_status(output, params, patch_applied)
        metadata = self._build_success_metadata(
            context,
            output,
            patch_applied,
            test_exit_code,
            status,
        )
        self.artifact_writer.write_json(context.artifacts.run_metadata, metadata)
        return metadata

    def _initialize_run(self, params: CodexRunParams, config: CodexRunConfig) -> "_RunContext":
        started = self.clock.now()
        run_id = self.run_id_generator.next_id(now=started)
        run_dir = self.artifact_writer.ensure_run_dir(run_id)
        artifacts = self._build_artifacts(run_dir)
        request = self._build_request(params, config)
        self.artifact_writer.write_json(artifacts.request_json, request)
        return _RunContext(run_id=run_id, started=started, request=request, artifacts=artifacts)

    def _build_request(self, params: CodexRunParams, config: CodexRunConfig) -> CodexRequest:
        messages = []
        if params.system_prompt:
            messages.append(CodexMessage(role="system", content=params.system_prompt))
        messages.append(CodexMessage(role="user", content=params.task))
        return CodexRequest(
            model=config.model,
            messages=messages,
            max_output_tokens=params.max_output_tokens,
            temperature=params.temperature,
            max_tool_rounds=params.max_tool_rounds,
        )

    def _build_artifacts(self, run_dir) -> CodexRunArtifacts:
        return CodexRunArtifacts(
            run_metadata=run_dir / "run.json",
            request_json=run_dir / "request.json",
            response_json=run_dir / "response.json",
            response_text=run_dir / "response.txt",
            output_json=run_dir / "output.json",
            patch_diff=run_dir / "diff.patch",
            stdout_log=run_dir / "stdout.log",
            stderr_log=run_dir / "stderr.log",
        )

    def _capture_response(self, context: "_RunContext"):
        response_text = self.responses_client.run(context.request, self.tool_registry)
        self.artifact_writer.write_text(context.artifacts.response_json, response_text.raw_payload)
        self.artifact_writer.write_text(context.artifacts.response_text, response_text.text)
        return response_text

    def _parse_output(self, context: "_RunContext", response_text) -> CodexStructuredOutput | None:
        try:
            output = self.output_parser.parse(response_text.text)
        except ValueError:
            return None
        self.artifact_writer.write_json(context.artifacts.output_json, output)
        return output

    def _build_success_metadata(
        self,
        context: "_RunContext",
        output: CodexStructuredOutput,
        patch_applied: bool,
        test_exit_code: int | None,
        status: CodexRunStatus,
    ) -> CodexRunMetadata:
        ended = self.clock.now()
        return CodexRunMetadata(
            run_id=context.run_id,
            started_at=context.started,
            ended_at=ended,
            model=context.request.model,
            status=status,
            output_status=output.status,
            artifacts=context.artifacts,
            patch_applied=patch_applied,
            test_exit_code=test_exit_code,
        )

    def _write_failure(self, context: "_RunContext", message: str) -> CodexRunMetadata:
        ended = self.clock.now()
        metadata = CodexRunMetadata(
            run_id=context.run_id,
            started_at=context.started,
            ended_at=ended,
            model=context.request.model,
            status=CodexRunStatus.failed,
            artifacts=context.artifacts,
            error_message=message,
        )
        self.artifact_writer.write_json(context.artifacts.run_metadata, metadata)
        return metadata

    def _write_blocked(self, context: "_RunContext", raw_text: str) -> CodexRunMetadata:
        ended = self.clock.now()
        output = CodexStructuredOutput(
            patch=None,
            rationale="Structured output missing or invalid.",
            risk_flags=["missing_structured_output"],
            open_questions=[raw_text] if raw_text else [],
            status=CodexOutputStatus.blocked,
        )
        self.artifact_writer.write_json(context.artifacts.output_json, output)
        metadata = CodexRunMetadata(
            run_id=context.run_id,
            started_at=context.started,
            ended_at=ended,
            model=context.request.model,
            status=CodexRunStatus.blocked,
            output_status=output.status,
            artifacts=context.artifacts,
            error_message="Structured output missing or invalid.",
        )
        self.artifact_writer.write_json(context.artifacts.run_metadata, metadata)
        return metadata

    def _apply_patch_if_needed(
        self,
        output: CodexStructuredOutput,
        params: CodexRunParams,
        artifacts: CodexRunArtifacts,
    ) -> bool:
        if output.patch is None:
            return False
        self.artifact_writer.write_text(artifacts.patch_diff, output.patch)
        if not params.apply_patch:
            return False
        result = self.patch_applier.apply(output.patch)
        if result.stdout:
            self.artifact_writer.write_text(artifacts.stdout_log, result.stdout)
        if result.stderr:
            self.artifact_writer.write_text(artifacts.stderr_log, result.stderr)
        return result.applied

    def _run_tests_if_needed(self, params: CodexRunParams, artifacts: CodexRunArtifacts) -> int | None:
        if params.run_tests_command is None:
            return None
        result = self.test_runner.run(params.run_tests_command, params.timeout_seconds)
        self.artifact_writer.write_text(artifacts.stdout_log, result.stdout)
        self.artifact_writer.write_text(artifacts.stderr_log, result.stderr)
        return result.exit_code

    def _resolve_run_status(
        self,
        output: CodexStructuredOutput,
        params: CodexRunParams,
        patch_applied: bool,
    ) -> CodexRunStatus:
        if output.status == CodexOutputStatus.blocked:
            return CodexRunStatus.blocked
        if output.patch and params.apply_patch and not patch_applied:
            return CodexRunStatus.failed
        return CodexRunStatus.completed


@dataclass(frozen=True)
class _RunContext:
    run_id: str
    started: datetime
    request: CodexRequest
    artifacts: CodexRunArtifacts
