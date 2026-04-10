"""Maintained application-layer bootstrap service for headless orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

from tnh_scholar.agent_orchestration.app.factory import (
    BootstrapKernelBundle,
    BootstrapKernelFactory,
    BootstrapKernelFactoryProtocol,
)
from tnh_scholar.agent_orchestration.app.models import (
    HeadlessBootstrapConfig,
    HeadlessBootstrapParams,
    HeadlessBootstrapResult,
)
from tnh_scholar.agent_orchestration.kernel.adapters.workflow_loader import YamlWorkflowLoader
from tnh_scholar.agent_orchestration.kernel.enums import Opcode
from tnh_scholar.agent_orchestration.kernel.models import WorkflowDefinition


@dataclass(frozen=True)
class HeadlessBootstrapService:
    """Load one workflow and run the maintained kernel end to end."""

    config: HeadlessBootstrapConfig
    workflow_loader: YamlWorkflowLoader = field(default_factory=YamlWorkflowLoader)
    kernel_factory: BootstrapKernelFactoryProtocol | None = None

    def run(self, params: HeadlessBootstrapParams) -> HeadlessBootstrapResult:
        """Execute one maintained headless bootstrap run."""
        workflow = self.workflow_loader.load(params.workflow_path)
        self._validate_bootstrap_workflow(workflow)
        bundle = self._kernel_bundle()
        run_result = bundle.kernel_service.run(workflow, self.config.storage.runs_root)
        return HeadlessBootstrapResult(
            run_id=run_result.run_id,
            workflow_id=run_result.workflow_id,
            status=run_result.status.value,
            run_directory=run_result.run_directory,
            metadata_path=run_result.metadata_path,
            final_state_path=run_result.final_state_path,
            workspace_context=bundle.workspace_service.current_context(),
        )

    def _kernel_bundle(self) -> BootstrapKernelBundle:
        factory = self.kernel_factory
        if factory is None:
            factory = BootstrapKernelFactory(config=self.config)
        return factory.build()

    def _validate_bootstrap_workflow(self, workflow: WorkflowDefinition) -> None:
        unsupported = [
            str(step.opcode)
            for step in workflow.steps
            if step.opcode in {Opcode.evaluate, Opcode.gate}
        ]
        if unsupported:
            joined = ", ".join(unsupported)
            raise ValueError(
                "Maintained headless bootstrap does not support semantic control steps yet: "
                f"{joined}."
            )
