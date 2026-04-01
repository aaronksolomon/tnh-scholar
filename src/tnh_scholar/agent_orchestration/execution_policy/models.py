"""Typed models for maintained execution policy contracts."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class ExecutionPosture(str, Enum):
    """Filesystem execution posture."""

    read_only = "read_only"
    workspace_write = "workspace_write"


class NetworkPosture(str, Enum):
    """Network posture."""

    deny = "deny"
    allow = "allow"


class ApprovalPosture(str, Enum):
    """Interactive approval posture."""

    fail_on_prompt = "fail_on_prompt"
    deny_interactive = "deny_interactive"
    bounded_auto_approve = "bounded_auto_approve"


class PolicyViolationClass(str, Enum):
    """Stable policy violation classes."""

    native_policy_block = "native_policy_block"
    forbidden_path = "forbidden_path"
    forbidden_operation = "forbidden_operation"
    interactive_prompt_violation = "interactive_prompt_violation"
    network_violation = "network_violation"
    protected_branch_violation = "protected_branch_violation"


class RequestedExecutionPolicy(BaseModel):
    """Policy intent requested by the control plane."""

    policy_reference: str | None = None
    execution_posture: ExecutionPosture | None = None
    network_posture: NetworkPosture | None = None
    approval_posture: ApprovalPosture | None = None
    allowed_paths: tuple[Path, ...] | None = None
    forbidden_paths: tuple[Path, ...] = Field(default_factory=tuple)
    forbidden_operations: tuple[str, ...] = Field(default_factory=tuple)


class EffectiveExecutionPolicy(BaseModel):
    """Concrete enforced policy after derivation."""

    policy_reference: str | None = None
    execution_posture: ExecutionPosture = ExecutionPosture.read_only
    network_posture: NetworkPosture = NetworkPosture.deny
    approval_posture: ApprovalPosture = ApprovalPosture.fail_on_prompt
    allowed_paths: tuple[Path, ...] = Field(default_factory=tuple)
    forbidden_paths: tuple[Path, ...] = Field(default_factory=tuple)
    forbidden_operations: tuple[str, ...] = Field(default_factory=tuple)


class PolicyViolation(BaseModel):
    """One concrete policy violation."""

    violation_class: PolicyViolationClass
    message: str
    path: Path | None = None
    operation: str | None = None
    hard_violation: bool = True


class PolicySummary(BaseModel):
    """Canonical persisted policy record for one executed step."""

    requested_policy: RequestedExecutionPolicy
    effective_policy: EffectiveExecutionPolicy
    runtime_overrides: RequestedExecutionPolicy | None = None
    capability_notes: tuple[str, ...] = Field(default_factory=tuple)
    violations: tuple[PolicyViolation, ...] = Field(default_factory=tuple)
    enforcement_notes: tuple[str, ...] = Field(default_factory=tuple)


class ExecutionPolicySettings(BaseModel):
    """System-level execution policy defaults and named references."""

    default_policy: RequestedExecutionPolicy = Field(default_factory=RequestedExecutionPolicy)
    named_policies: dict[str, RequestedExecutionPolicy] = Field(default_factory=dict)
    runtime_overrides: RequestedExecutionPolicy = Field(default_factory=RequestedExecutionPolicy)
