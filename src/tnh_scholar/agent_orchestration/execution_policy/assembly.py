"""Execution policy assembly helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.execution_policy.models import (
    ApprovalPosture,
    EffectiveExecutionPolicy,
    ExecutionPolicySettings,
    ExecutionPosture,
    NetworkPosture,
    PolicySummary,
    PolicyViolation,
    PolicyViolationClass,
    RequestedExecutionPolicy,
)


class ExecutionPolicyAssemblyError(ValueError):
    """Raised when execution policy references cannot be assembled."""


@dataclass(frozen=True)
class ExecutionPolicyAssembler:
    """Derive requested and effective policy records."""

    def assemble(
        self,
        *,
        settings: ExecutionPolicySettings,
        workflow_policy_ref: str | None = None,
        step_policy_ref: str | None = None,
        runtime_overrides: RequestedExecutionPolicy | None = None,
    ) -> PolicySummary:
        workflow_policy = self._resolve_reference(settings, workflow_policy_ref)
        step_policy = self._resolve_reference(settings, step_policy_ref)
        requested = self._merge_policies(settings.default_policy, workflow_policy, step_policy)
        applied_overrides = self._merge_policies(settings.runtime_overrides, runtime_overrides)
        effective = self._derive_effective_policy(requested, applied_overrides)
        notes = self._build_notes(step_policy_ref, workflow_policy_ref, applied_overrides)
        return PolicySummary(
            requested_policy=requested,
            effective_policy=effective,
            runtime_overrides=applied_overrides if self._has_policy_content(applied_overrides) else None,
            violations=self._derive_violations(requested, effective),
            enforcement_notes=notes,
        )

    def _resolve_reference(
        self,
        settings: ExecutionPolicySettings,
        policy_ref: str | None,
    ) -> RequestedExecutionPolicy | None:
        if policy_ref is None:
            return None
        if policy_ref not in settings.named_policies:
            raise ExecutionPolicyAssemblyError(f"Unknown policy reference: {policy_ref}")
        return settings.named_policies[policy_ref].model_copy(update={"policy_reference": policy_ref})

    def _merge_policies(
        self,
        *policies: RequestedExecutionPolicy | None,
    ) -> RequestedExecutionPolicy:
        merged = RequestedExecutionPolicy()
        for policy in policies:
            if policy is None:
                continue
            merged = RequestedExecutionPolicy(
                policy_reference=policy.policy_reference or merged.policy_reference,
                execution_posture=policy.execution_posture or merged.execution_posture,
                network_posture=policy.network_posture or merged.network_posture,
                approval_posture=policy.approval_posture or merged.approval_posture,
                allowed_paths=(
                    merged.allowed_paths if policy.allowed_paths is None else policy.allowed_paths
                ),
                forbidden_paths=self._merge_paths(merged.forbidden_paths, policy.forbidden_paths),
                forbidden_operations=self._merge_strings(
                    merged.forbidden_operations,
                    policy.forbidden_operations,
                ),
            )
        return merged

    def _derive_effective_policy(
        self,
        requested: RequestedExecutionPolicy,
        runtime_overrides: RequestedExecutionPolicy,
    ) -> EffectiveExecutionPolicy:
        return EffectiveExecutionPolicy(
            policy_reference=requested.policy_reference,
            execution_posture=self._tighten_execution_posture(
                requested.execution_posture,
                runtime_overrides.execution_posture,
            ),
            network_posture=self._tighten_network_posture(
                requested.network_posture,
                runtime_overrides.network_posture,
            ),
            approval_posture=self._tighten_approval_posture(
                requested.approval_posture,
                runtime_overrides.approval_posture,
            ),
            allowed_paths=self._tighten_allowed_paths(
                requested.allowed_paths or (),
                runtime_overrides.allowed_paths,
            ),
            forbidden_paths=self._merge_paths(
                requested.forbidden_paths,
                runtime_overrides.forbidden_paths,
            ),
            forbidden_operations=self._merge_strings(
                requested.forbidden_operations,
                runtime_overrides.forbidden_operations,
            ),
        )

    def _build_notes(
        self,
        step_policy_ref: str | None,
        workflow_policy_ref: str | None,
        runtime_overrides: RequestedExecutionPolicy,
    ) -> tuple[str, ...]:
        notes: list[str] = []
        if workflow_policy_ref is not None:
            notes.append(f"workflow_policy={workflow_policy_ref}")
        if step_policy_ref is not None:
            notes.append(f"step_policy={step_policy_ref}")
        if self._has_policy_content(runtime_overrides):
            notes.append("runtime_overrides_applied")
        return tuple(notes)

    def _tighten_execution_posture(
        self,
        requested: ExecutionPosture | None,
        override: ExecutionPosture | None,
    ) -> ExecutionPosture:
        postures = [value for value in (requested, override) if value is not None]
        if not postures:
            return ExecutionPosture.read_only
        if ExecutionPosture.read_only in postures:
            return ExecutionPosture.read_only
        return ExecutionPosture.workspace_write

    def _tighten_network_posture(
        self,
        requested: NetworkPosture | None,
        override: NetworkPosture | None,
    ) -> NetworkPosture:
        postures = [value for value in (requested, override) if value is not None]
        if not postures:
            return NetworkPosture.deny
        return NetworkPosture.deny if NetworkPosture.deny in postures else NetworkPosture.allow

    def _tighten_approval_posture(
        self,
        requested: ApprovalPosture | None,
        override: ApprovalPosture | None,
    ) -> ApprovalPosture:
        ranking = {
            ApprovalPosture.fail_on_prompt: 0,
            ApprovalPosture.deny_interactive: 1,
            ApprovalPosture.bounded_auto_approve: 2,
        }
        postures = [value for value in (requested, override) if value is not None]
        if not postures:
            return ApprovalPosture.fail_on_prompt
        return min(postures, key=ranking.__getitem__)

    def _tighten_allowed_paths(
        self,
        requested: tuple[Path, ...],
        override: tuple[Path, ...] | None,
    ) -> tuple[Path, ...]:
        if override is None:
            return requested
        if requested:
            shared = [path for path in requested if path in override]
            return tuple(shared)
        return override

    def _derive_violations(
        self,
        requested: RequestedExecutionPolicy,
        effective: EffectiveExecutionPolicy,
    ) -> tuple[PolicyViolation, ...]:
        violations: list[PolicyViolation] = []
        if (
            effective.execution_posture == ExecutionPosture.workspace_write
            and requested.allowed_paths == ()
        ):
            violations.append(
                PolicyViolation(
                    violation_class=PolicyViolationClass.forbidden_path,
                    message="Workspace-write policy cannot use an empty allowed_paths scope.",
                )
            )
        return tuple(violations)

    def _merge_paths(
        self,
        left: tuple[Path, ...],
        right: tuple[Path, ...],
    ) -> tuple[Path, ...]:
        merged: list[Path] = []
        for path in (*left, *right):
            if path not in merged:
                merged.append(path)
        return tuple(merged)

    def _merge_strings(
        self,
        left: tuple[str, ...],
        right: tuple[str, ...],
    ) -> tuple[str, ...]:
        merged: list[str] = []
        for value in (*left, *right):
            if value not in merged:
                merged.append(value)
        return tuple(merged)

    def _has_policy_content(self, policy: RequestedExecutionPolicy) -> bool:
        return any(
            (
                policy.policy_reference is not None,
                policy.execution_posture is not None,
                policy.network_posture is not None,
                policy.approval_posture is not None,
                policy.allowed_paths is not None,
                bool(policy.forbidden_paths),
                bool(policy.forbidden_operations),
            )
        )
