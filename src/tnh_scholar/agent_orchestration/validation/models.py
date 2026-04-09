"""Typed models for the validation subsystem."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.execution.models import (
    EnvironmentPolicy,
    ExecutionOutputCapturePolicy,
)


class ValidationTermination(str, Enum):
    """Validation outcomes exposed to the kernel."""

    completed = "completed"
    error = "error"
    killed_timeout = "killed_timeout"
    killed_idle = "killed_idle"
    killed_policy = "killed_policy"


class BuiltinValidatorId(str, Enum):
    """Trusted builtin validator identifiers."""

    tests = "tests"
    lint = "lint"
    typecheck = "typecheck"


class GeneratedHarnessValidatorId(str, Enum):
    """Trusted generated harness validator identifiers."""

    generated_harness = "generated_harness"


class BackendFamily(str, Enum):
    """Maintained harness backend families."""

    script = "script"
    cli = "cli"
    web = "web"


class BuiltinValidationSpec(BaseModel):
    """Kernel-facing builtin validator spec."""

    kind: Literal["builtin"] = "builtin"
    name: BuiltinValidatorId


class HarnessValidationSpec(BaseModel):
    """Kernel-facing generated harness validator spec."""

    kind: Literal["harness"] = "harness"
    name: GeneratedHarnessValidatorId
    artifacts: list[str] = Field(default_factory=list)
    timeout_seconds: int | None = None
    may_propose_goldens: bool = False


ValidationSpec = Annotated[
    BuiltinValidationSpec | HarnessValidationSpec,
    Field(discriminator="kind"),
]


class ValidationStepRequest(BaseModel):
    """Kernel-facing validation step request."""

    validators: list[ValidationSpec]
    working_directory: Path


class HarnessReport(BaseModel):
    """Minimal harness report needed by the kernel."""

    proposed_goldens: list[str] = Field(default_factory=list)


class ValidationTextArtifact(BaseModel):
    """Normalized text artifact returned by validation execution."""

    filename: str
    content: str
    media_type: str


class ValidationCapturedArtifact(BaseModel):
    """Captured harness artifact awaiting canonical persistence."""

    source_path: Path
    relative_path: Path
    media_type: str = "application/octet-stream"


class HarnessBackendRequest(BaseModel):
    """Backend-neutral harness execution request."""

    backend_family: BackendFamily
    executable: Path
    entrypoint: Path | None = None
    arguments: tuple[str, ...] = Field(default_factory=tuple)
    working_directory: Path
    artifact_patterns: tuple[str, ...] = Field(default_factory=tuple)
    timeout_seconds: int | None = None
    environment_policy: EnvironmentPolicy
    output_capture_policy: ExecutionOutputCapturePolicy = Field(
        default_factory=ExecutionOutputCapturePolicy
    )


class HarnessBackendResult(BaseModel):
    """Normalized harness backend result."""

    termination: ValidationTermination
    harness_report: HarnessReport | None = None
    stdout_artifact: ValidationTextArtifact | None = None
    stderr_artifact: ValidationTextArtifact | None = None
    captured_artifacts: list[ValidationCapturedArtifact] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Validation result exposed to the kernel."""

    termination: ValidationTermination
    harness_report: HarnessReport | None = None
    stdout_artifact: ValidationTextArtifact | None = None
    stderr_artifact: ValidationTextArtifact | None = None
    captured_artifacts: list[ValidationCapturedArtifact] = Field(default_factory=list)
