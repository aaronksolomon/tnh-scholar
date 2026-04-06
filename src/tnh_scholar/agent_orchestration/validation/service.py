"""Validation service built on the execution subsystem."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.execution import (
    CliExecutableInvocation,
    ExecutionRequest,
    ExplicitEnvironmentPolicy,
    SubprocessExecutionService,
)
from tnh_scholar.agent_orchestration.validation.models import (
    BackendFamily,
    BuiltinValidationSpec,
    BuiltinValidatorId,
    GeneratedHarnessValidatorId,
    HarnessBackendRequest,
    HarnessBackendResult,
    HarnessReport,
    HarnessValidationSpec,
    ValidationResult,
    ValidationSpec,
    ValidationStepRequest,
    ValidationTermination,
    ValidationTextArtifact,
)
from tnh_scholar.agent_orchestration.validation.protocols import (
    HarnessBackendProtocol,
    HarnessBackendResolverProtocol,
    ValidationServiceProtocol,
    ValidatorResolverProtocol,
)
from tnh_scholar.agent_orchestration.validation.termination import (
    merge_validation_termination,
    to_validation_termination,
)


class BuiltinCommandEntry(BaseModel):
    """Trusted builtin command mapping."""

    name: BuiltinValidatorId
    executable: Path
    arguments: tuple[str, ...] = Field(default_factory=tuple)


@dataclass(frozen=True)
class StaticValidatorResolver(ValidatorResolverProtocol):
    """Resolve trusted builtin validators into execution requests."""

    entries: list[BuiltinCommandEntry]

    def resolve(self, spec: BuiltinValidationSpec, run_directory: Path) -> ExecutionRequest:
        """Resolve one builtin validation spec."""
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


@dataclass(frozen=True)
class StaticHarnessBackendResolver(HarnessBackendResolverProtocol):
    """Resolve trusted harness validators into backend requests."""

    harness_script_name: str = "generated_harness.py"
    harness_report_name: str = "harness_report.json"

    def resolve(self, spec: HarnessValidationSpec, run_directory: Path) -> HarnessBackendRequest:
        """Resolve one harness validation spec."""
        match spec.name:
            case GeneratedHarnessValidatorId.generated_harness:
                return HarnessBackendRequest(
                    backend_family=BackendFamily.script,
                    executable=Path(sys.executable),
                    entrypoint=run_directory / self.harness_script_name,
                    arguments=("--report", self.harness_report_name),
                    working_directory=run_directory,
                    artifact_patterns=tuple(spec.artifacts),
                    timeout_seconds=spec.timeout_seconds,
                    environment_policy=ExplicitEnvironmentPolicy(values={}),
                )
        raise ValueError(f"Unsupported harness validator: {spec.name.value}")


@dataclass(frozen=True)
class HarnessBackendRegistry:
    """Resolve maintained backend implementations by family."""

    script_backend: HarnessBackendProtocol

    def resolve(self, family: BackendFamily) -> HarnessBackendProtocol:
        """Resolve one backend implementation."""
        match family:
            case BackendFamily.script:
                return self.script_backend
            case BackendFamily.cli | BackendFamily.web:
                raise ValueError(f"Harness backend not implemented: {family.value}")


@dataclass(frozen=True)
class ValidationService(ValidationServiceProtocol):
    """Execute validation steps using the execution subsystem."""

    resolver: ValidatorResolverProtocol
    execution_service: SubprocessExecutionService
    harness_resolver: HarnessBackendResolverProtocol
    backend_registry: HarnessBackendRegistry

    def run(self, request: ValidationStepRequest) -> ValidationResult:
        """Execute all validators in a step."""
        return self._run_all_validators(request.validators, request.run_directory)

    def _run_all_validators(
        self,
        validators: list[ValidationSpec],
        run_directory: Path,
    ) -> ValidationResult:
        aggregate = ValidationResult(termination=ValidationTermination.completed)
        for spec in validators:
            aggregate = self._merge_result(
                current=aggregate,
                new_value=self._run_validator(spec, run_directory),
            )
        return aggregate

    def _run_validator(
        self,
        spec: ValidationSpec,
        run_directory: Path,
    ) -> HarnessBackendResult:
        if isinstance(spec, BuiltinValidationSpec):
            return self._run_builtin_validator(spec, run_directory)
        return self._run_harness_validator(spec, run_directory)

    def _run_builtin_validator(
        self,
        spec: BuiltinValidationSpec,
        run_directory: Path,
    ) -> HarnessBackendResult:
        execution_request = self.resolver.resolve(spec, run_directory)
        execution_result = self.execution_service.run(execution_request)
        return HarnessBackendResult(termination=to_validation_termination(execution_result.termination))

    def _run_harness_validator(
        self,
        spec: HarnessValidationSpec,
        run_directory: Path,
    ) -> HarnessBackendResult:
        backend_request = self.harness_resolver.resolve(spec, run_directory)
        backend = self.backend_registry.resolve(backend_request.backend_family)
        return backend.run(backend_request)

    def _merge_result(
        self,
        *,
        current: ValidationResult,
        new_value: HarnessBackendResult,
    ) -> ValidationResult:
        return ValidationResult(
            termination=merge_validation_termination(current.termination, new_value.termination),
            harness_report=self._merge_report(current.harness_report, new_value.harness_report),
            stdout_artifact=self._merge_text_artifact(
                current=current.stdout_artifact,
                new_value=new_value.stdout_artifact,
                fallback_filename="validation_stdout.txt",
            ),
            stderr_artifact=self._merge_text_artifact(
                current=current.stderr_artifact,
                new_value=new_value.stderr_artifact,
                fallback_filename="validation_stderr.txt",
            ),
            captured_artifacts=[*current.captured_artifacts, *new_value.captured_artifacts],
        )

    def _merge_report(
        self,
        current: HarnessReport | None,
        new_value: HarnessReport | None,
    ) -> HarnessReport | None:
        if new_value is None:
            return current
        if current is None:
            return new_value
        merged_goldens = tuple(dict.fromkeys([*current.proposed_goldens, *new_value.proposed_goldens]))
        return HarnessReport(proposed_goldens=list(merged_goldens))

    def _merge_text_artifact(
        self,
        *,
        current: ValidationTextArtifact | None,
        new_value: ValidationTextArtifact | None,
        fallback_filename: str,
    ) -> ValidationTextArtifact | None:
        if new_value is None:
            return current
        if current is None:
            return new_value
        if current.media_type != new_value.media_type:
            raise ValueError("Validation text artifacts must share a media type.")
        combined = self._join_text(current.content, new_value.content)
        return ValidationTextArtifact(
            filename=fallback_filename,
            content=combined,
            media_type=current.media_type,
        )

    def _join_text(self, current: str, new_value: str) -> str:
        if not current:
            return new_value
        if not new_value:
            return current
        if current.endswith("\n"):
            return f"{current}{new_value}"
        return f"{current}\n{new_value}"
