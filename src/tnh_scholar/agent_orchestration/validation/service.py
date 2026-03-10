"""Validation service built on the execution subsystem."""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.execution import (
    CliExecutableInvocation,
    ExecutionRequest,
    ExecutionTermination,
    ExplicitEnvironmentPolicy,
    PythonScriptInvocation,
    SubprocessExecutionService,
    TimeoutPolicy,
)
from tnh_scholar.agent_orchestration.validation.models import (
    BuiltinValidationSpec,
    BuiltinValidatorId,
    GeneratedHarnessValidatorId,
    HarnessReport,
    HarnessValidationSpec,
    ValidationResult,
    ValidationSpec,
    ValidationStepRequest,
    ValidationTermination,
)
from tnh_scholar.agent_orchestration.validation.protocols import (
    ValidationServiceProtocol,
    ValidatorResolverProtocol,
)


class BuiltinCommandEntry(BaseModel):
    """Trusted builtin command mapping."""

    name: BuiltinValidatorId
    executable: Path
    arguments: tuple[str, ...] = Field(default_factory=tuple)


@dataclass(frozen=True)
class StaticValidatorResolver(ValidatorResolverProtocol):
    """Resolve trusted validation specs into execution requests."""

    entries: list[BuiltinCommandEntry]
    harness_script_name: str = "generated_harness.py"
    harness_report_name: str = "harness_report.json"

    def resolve(self, spec: ValidationSpec, run_directory: Path) -> ExecutionRequest:
        """Resolve a validation spec."""
        if isinstance(spec, BuiltinValidationSpec):
            return self._resolve_builtin(spec, run_directory)
        return self._resolve_harness(spec, run_directory)

    def _resolve_builtin(
        self,
        spec: BuiltinValidationSpec,
        run_directory: Path,
    ) -> ExecutionRequest:
        for entry in self.entries:
            if entry.name == spec.name:
                return ExecutionRequest(
                    invocation=CliExecutableInvocation(
                        executable=entry.executable,
                        arguments=entry.arguments,
                    ),
                    working_directory=run_directory,
                    environment_policy=ExplicitEnvironmentPolicy(values={}),
                )
        raise ValueError(f"Unknown builtin validator: {spec.name.value}")

    def _resolve_harness(
        self,
        spec: HarnessValidationSpec,
        run_directory: Path,
    ) -> ExecutionRequest:
        match spec.name:
            case GeneratedHarnessValidatorId.generated_harness:
                return ExecutionRequest(
                    invocation=PythonScriptInvocation(
                        interpreter=Path(sys.executable),
                        script_path=run_directory / self.harness_script_name,
                        arguments=("--report", self.harness_report_name),
                    ),
                    working_directory=run_directory,
                    environment_policy=ExplicitEnvironmentPolicy(values={}),
                    timeout_policy=TimeoutPolicy(wall_clock_seconds=spec.timeout_seconds),
                )
        raise ValueError(f"Unsupported harness validator: {spec.name.value}")


@dataclass(frozen=True)
class HarnessReportLoader:
    """Load and normalize harness reports."""

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
class ValidationService(ValidationServiceProtocol):
    """Execute validation steps using the execution subsystem."""

    resolver: ValidatorResolverProtocol
    execution_service: SubprocessExecutionService
    report_loader: HarnessReportLoader
    artifacts_subdir: str = "validation_artifacts"

    def run(self, request: ValidationStepRequest) -> ValidationResult:
        """Execute all validators in a step."""
        termination = ValidationTermination.completed
        report = None
        artifact_paths: list[Path] = []
        for spec in request.validators:
            execution_request = self.resolver.resolve(spec, request.run_directory)
            execution_result = self.execution_service.run(execution_request)
            termination = self._merge_termination(
                termination,
                self._to_validation_termination(execution_result.termination),
            )
            artifact_paths.extend(self._capture_artifacts(request.run_directory, spec))
            latest_report, report_termination = self._load_report(request.run_directory)
            termination = self._merge_termination(termination, report_termination)
            if latest_report is not None:
                report = latest_report
        return ValidationResult(
            termination=termination,
            harness_report=report,
            artifact_paths=artifact_paths,
        )

    def _to_validation_termination(
        self,
        termination: ExecutionTermination,
    ) -> ValidationTermination:
        match termination:
            case ExecutionTermination.completed:
                return ValidationTermination.completed
            case ExecutionTermination.non_zero_exit | ExecutionTermination.startup_failure:
                return ValidationTermination.error
            case ExecutionTermination.wall_clock_timeout:
                return ValidationTermination.killed_timeout
            case ExecutionTermination.idle_timeout:
                return ValidationTermination.killed_idle
            case ExecutionTermination.policy_kill:
                return ValidationTermination.killed_policy
        raise ValueError(f"Unsupported execution termination: {termination.value}")

    def _merge_termination(
        self,
        current: ValidationTermination,
        new_value: ValidationTermination,
    ) -> ValidationTermination:
        return max(current, new_value, key=self._termination_rank)

    def _termination_rank(self, value: ValidationTermination) -> int:
        match value:
            case ValidationTermination.completed:
                return 0
            case ValidationTermination.error:
                return 1
            case ValidationTermination.killed_policy:
                return 2
            case ValidationTermination.killed_idle:
                return 3
            case ValidationTermination.killed_timeout:
                return 4
        raise ValueError(f"Unsupported validation termination: {value}")

    def _load_report(
        self,
        run_directory: Path,
    ) -> tuple[HarnessReport | None, ValidationTermination]:
        try:
            return self.report_loader.load(run_directory), ValidationTermination.completed
        except ValueError:
            return None, ValidationTermination.error

    def _capture_artifacts(self, run_directory: Path, spec: ValidationSpec) -> list[Path]:
        if not isinstance(spec, HarnessValidationSpec):
            return []
        root = run_directory / self.artifacts_subdir
        captured: list[Path] = []
        for pattern in spec.artifacts:
            for path in run_directory.glob(pattern):
                if not path.is_file():
                    continue
                relative = path.relative_to(run_directory)
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
                captured.append(destination)
        return captured
