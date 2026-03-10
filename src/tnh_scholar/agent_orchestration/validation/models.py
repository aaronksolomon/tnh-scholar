"""Typed models for the validation subsystem."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field


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
    run_directory: Path


class HarnessReport(BaseModel):
    """Minimal harness report needed by the kernel."""

    proposed_goldens: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Validation result exposed to the kernel."""

    termination: ValidationTermination
    harness_report: HarnessReport | None = None
    artifact_paths: list[Path] = Field(default_factory=list)
