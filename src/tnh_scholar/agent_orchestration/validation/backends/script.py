"""Script-based harness backend."""

from __future__ import annotations

import json
from dataclasses import dataclass
from mimetypes import guess_type
from pathlib import Path

from tnh_scholar.agent_orchestration.execution import (
    ExecutionRequest,
    PythonScriptInvocation,
    SubprocessExecutionService,
    TimeoutPolicy,
)
from tnh_scholar.agent_orchestration.validation.models import (
    HarnessBackendRequest,
    HarnessBackendResult,
    HarnessReport,
    ValidationCapturedArtifact,
    ValidationTermination,
    ValidationTextArtifact,
)
from tnh_scholar.agent_orchestration.validation.protocols import HarnessBackendProtocol
from tnh_scholar.agent_orchestration.validation.termination import (
    merge_validation_termination,
    to_validation_termination,
)


@dataclass(frozen=True)
class HarnessReportLoader:
    """Load and normalize script harness reports."""

    report_name: str = "harness_report.json"

    def load(self, run_directory: Path) -> HarnessReport | None:
        """Load a harness report if present."""
        path = run_directory / self.report_name
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid harness report JSON: {path}") from error
        return HarnessReport.model_validate(payload)


@dataclass(frozen=True)
class ScriptHarnessBackend(HarnessBackendProtocol):
    """Execute generated script harnesses via the execution subsystem."""

    execution_service: SubprocessExecutionService
    report_loader: HarnessReportLoader

    def run(self, request: HarnessBackendRequest) -> HarnessBackendResult:
        """Execute one script harness request."""
        script_path = self._required_entrypoint(request)
        execution_result = self.execution_service.run(
            ExecutionRequest(
                invocation=PythonScriptInvocation(
                    interpreter=request.executable,
                    script_path=script_path,
                    arguments=request.arguments,
                ),
                working_directory=request.working_directory,
                environment_policy=request.environment_policy,
                timeout_policy=TimeoutPolicy(wall_clock_seconds=request.timeout_seconds),
                output_capture_policy=request.output_capture_policy,
            )
        )
        captured_artifacts = self._capture_artifacts(
            run_directory=request.working_directory,
            patterns=request.artifact_patterns,
        )
        report, report_termination = self._load_report(request.working_directory)
        termination = merge_validation_termination(
            to_validation_termination(execution_result.termination),
            report_termination,
        )
        return HarnessBackendResult(
            termination=termination,
            harness_report=report,
            stdout_artifact=self._stdout_artifact(execution_result.stdout_text),
            stderr_artifact=self._stderr_artifact(execution_result.stderr_text),
            captured_artifacts=captured_artifacts,
        )

    def _required_entrypoint(self, request: HarnessBackendRequest) -> Path:
        if request.entrypoint is None:
            raise ValueError("Script backend requires an entrypoint.")
        return Path(request.entrypoint)

    def _capture_artifacts(
        self,
        run_directory: Path,
        patterns: tuple[str, ...],
    ) -> list[ValidationCapturedArtifact]:
        captured: list[ValidationCapturedArtifact] = []
        seen_relatives: set[Path] = set()
        for pattern in patterns:
            for path in run_directory.glob(pattern):
                if not path.is_file():
                    continue
                relative = path.relative_to(run_directory)
                if relative in seen_relatives:
                    continue
                seen_relatives.add(relative)
                captured.append(
                    ValidationCapturedArtifact(
                        source_path=path,
                        relative_path=relative,
                        media_type=self._media_type_for_path(path),
                    )
                )
        return captured

    def _load_report(
        self,
        run_directory: Path,
    ) -> tuple[HarnessReport | None, ValidationTermination]:
        try:
            return self.report_loader.load(run_directory), ValidationTermination.completed
        except ValueError:
            return None, ValidationTermination.error

    def _stdout_artifact(self, content: str) -> ValidationTextArtifact | None:
        if not content:
            return None
        return ValidationTextArtifact(
            filename="validation_stdout.txt",
            content=content,
            media_type="text/plain",
        )

    def _stderr_artifact(self, content: str) -> ValidationTextArtifact | None:
        if not content:
            return None
        return ValidationTextArtifact(
            filename="validation_stderr.txt",
            content=content,
            media_type="text/plain",
        )

    def _media_type_for_path(self, path: Path) -> str:
        media_type, _ = guess_type(path.name)
        if media_type is None:
            return "application/octet-stream"
        return media_type
