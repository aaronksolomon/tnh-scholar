"""Composition helpers for the maintained headless bootstrap app layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tnh_scholar.agent_orchestration.app.models import HeadlessBootstrapConfig
from tnh_scholar.agent_orchestration.common.run_id import strftime_run_id
from tnh_scholar.agent_orchestration.common.time import utc_now
from tnh_scholar.agent_orchestration.execution import SubprocessExecutionService
from tnh_scholar.agent_orchestration.kernel import KernelRunService
from tnh_scholar.agent_orchestration.kernel.validator import WorkflowValidator
from tnh_scholar.agent_orchestration.run_artifacts import FilesystemRunArtifactStore
from tnh_scholar.agent_orchestration.runners import DelegatingRunnerService
from tnh_scholar.agent_orchestration.runners.adapters.claude_cli import ClaudeCliRunnerAdapter
from tnh_scholar.agent_orchestration.runners.adapters.codex_cli import CodexCliRunnerAdapter
from tnh_scholar.agent_orchestration.validation import (
    HarnessBackendRegistry,
    HarnessReportLoader,
    ScriptHarnessBackend,
    StaticHarnessBackendResolver,
    StaticValidatorResolver,
    ValidationService,
)
from tnh_scholar.agent_orchestration.workspace import GitWorktreeWorkspaceService


@dataclass(frozen=True)
class SystemClock:
    """System UTC clock for maintained headless bootstrap runs."""

    def now(self) -> datetime:
        """Return the current UTC timestamp."""
        return utc_now()


@dataclass(frozen=True)
class TimestampRunIdGenerator:
    """Generate compact timestamp run IDs for bootstrap runs."""

    def next_id(self, now: datetime) -> str:
        """Return a compact timestamp-based run ID."""
        return strftime_run_id(now, "%Y%m%dT%H%M%SZ")


@dataclass(frozen=True)
class BootstrapKernelBundle:
    """Maintained collaborators required for one headless bootstrap run."""

    kernel_service: KernelRunService
    workspace_service: GitWorktreeWorkspaceService


@dataclass(frozen=True)
class BootstrapKernelFactory:
    """Build the maintained kernel bundle for one headless bootstrap run."""

    config: HeadlessBootstrapConfig

    def build(self) -> BootstrapKernelBundle:
        """Return the fully assembled maintained kernel bundle."""
        execution_service = SubprocessExecutionService()
        workspace_service = GitWorktreeWorkspaceService(
            repo_root=self.config.repo_root,
            workspace_root=self.config.storage.workspace_root,
            base_ref=self.config.base_ref,
            branch_prefix=self.config.branch_prefix,
        )
        kernel_service = KernelRunService(
            clock=SystemClock(),
            run_id_generator=TimestampRunIdGenerator(),
            artifact_store=FilesystemRunArtifactStore(),
            workspace=workspace_service,
            runner_service=DelegatingRunnerService(
                adapters=(
                    CodexCliRunnerAdapter(
                        execution_service=execution_service,
                        executable=self.config.runner.codex_executable,
                    ),
                    ClaudeCliRunnerAdapter(
                        execution_service=execution_service,
                        executable=self.config.runner.claude_executable,
                    ),
                )
            ),
            validation_service=ValidationService(
                resolver=StaticValidatorResolver(
                    entries=list(self.config.validation.builtin_commands)
                ),
                execution_service=execution_service,
                harness_resolver=StaticHarnessBackendResolver(),
                backend_registry=HarnessBackendRegistry(
                    script_backend=ScriptHarnessBackend(
                        execution_service=execution_service,
                        report_loader=HarnessReportLoader(),
                    )
                ),
            ),
            planner_evaluator=_UnsupportedPlannerEvaluator(),
            gate_approver=_UnsupportedGateApprover(),
            workflow_validator=WorkflowValidator(),
            execution_policy_settings=self.config.policy.execution_policy_settings,
        )
        return BootstrapKernelBundle(
            kernel_service=kernel_service,
            workspace_service=workspace_service,
        )


@dataclass(frozen=True)
class _UnsupportedPlannerEvaluator:
    """Fail closed until the maintained evaluator surface is implemented."""

    def evaluate(self, step: object, run_directory: object) -> object:
        del step, run_directory
        raise NotImplementedError(
            "Maintained headless bootstrap does not yet support EVALUATE. "
            "Use workflows limited to RUN_AGENT, RUN_VALIDATION, ROLLBACK, and STOP."
        )


@dataclass(frozen=True)
class _UnsupportedGateApprover:
    """Fail closed until the maintained gate approval surface is implemented."""

    def decide(self, step: object, run_directory: object) -> object:
        del step, run_directory
        raise NotImplementedError(
            "Maintained headless bootstrap does not yet support GATE. "
            "Use workflows limited to RUN_AGENT, RUN_VALIDATION, ROLLBACK, and STOP."
        )
