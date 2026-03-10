"""Typed models for the execution subsystem."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ExecutionTermination(str, Enum):
    """Mechanical subprocess outcomes."""

    completed = "completed"
    non_zero_exit = "non_zero_exit"
    wall_clock_timeout = "wall_clock_timeout"
    idle_timeout = "idle_timeout"
    policy_kill = "policy_kill"
    startup_failure = "startup_failure"


class OutputEncoding(str, Enum):
    """Output decoding policy."""

    text = "text"


class ExecutionOutputCapturePolicy(BaseModel):
    """How process output should be captured."""

    capture_stdout: bool = True
    capture_stderr: bool = True
    encoding: OutputEncoding = OutputEncoding.text


class TimeoutPolicy(BaseModel):
    """Execution timeout settings.

    ``idle_seconds`` is reserved for future streaming/idleness enforcement.
    The current subprocess service only enforces wall-clock timeouts.
    """

    wall_clock_seconds: int | None = Field(
        default=None,
        description="Maximum wall-clock runtime in seconds before termination.",
    )
    idle_seconds: int | None = Field(
        default=None,
        description=(
            "Maximum allowed idle time in seconds before termination. "
            "Reserved for future enforcement in the subprocess service."
        ),
    )


class InheritParentEnvironmentPolicy(BaseModel):
    """Inherit parent environment with optional overrides."""

    kind: Literal["inherit_parent"] = "inherit_parent"
    overrides: dict[str, str] = Field(default_factory=dict)


class ExplicitEnvironmentPolicy(BaseModel):
    """Use an explicit allowlisted environment."""

    kind: Literal["explicit"] = "explicit"
    values: dict[str, str] = Field(default_factory=dict)


class IsolatedEnvironmentPolicy(BaseModel):
    """Start from an empty environment and allowlist values."""

    kind: Literal["isolated"] = "isolated"
    allowlist: dict[str, str] = Field(default_factory=dict)


EnvironmentPolicy = Annotated[
    InheritParentEnvironmentPolicy | ExplicitEnvironmentPolicy | IsolatedEnvironmentPolicy,
    Field(discriminator="kind"),
]


class CliExecutableInvocation(BaseModel):
    """Invoke a concrete executable with typed arguments."""

    family: Literal["cli_executable"] = "cli_executable"
    executable: Path
    arguments: tuple[str, ...] = ()


class PythonScriptInvocation(BaseModel):
    """Invoke a Python script using a specific interpreter."""

    family: Literal["python_script"] = "python_script"
    interpreter: Path
    script_path: Path
    arguments: tuple[str, ...] = ()


Invocation = Annotated[
    CliExecutableInvocation | PythonScriptInvocation,
    Field(discriminator="family"),
]


class ExecutionRequest(BaseModel):
    """Trusted execution request."""

    invocation: Invocation
    working_directory: Path
    environment_policy: EnvironmentPolicy
    timeout_policy: TimeoutPolicy = Field(default_factory=TimeoutPolicy)
    output_capture_policy: ExecutionOutputCapturePolicy = Field(
        default_factory=ExecutionOutputCapturePolicy
    )


class ExecutionResult(BaseModel):
    """Low-level subprocess result."""

    termination: ExecutionTermination
    exit_code: int | None = None
    stdout_text: str = ""
    stderr_text: str = ""
    timed_out: bool = False
    failure_message: str | None = None
