"""Kernel state models."""

from __future__ import annotations

from dataclasses import dataclass, field

from tnh_scholar.agent_orchestration.kernel.models import GateOutcome


@dataclass(frozen=True)
class KernelState:
    """Immutable runtime state."""

    current_step_id: str
    pending_golden_gate: bool = False
    trace: list[str] = field(default_factory=list)

    def advance(self, step_id: str, next_step_id: str, pending_gate: bool | None = None) -> "KernelState":
        """Advance state immutably."""
        new_pending = self.pending_golden_gate if pending_gate is None else pending_gate
        return KernelState(
            current_step_id=next_step_id,
            pending_golden_gate=new_pending,
            trace=[*self.trace, f"{step_id}->{next_step_id}"],
        )

    def log_text(self) -> str:
        """Render trace text."""
        return "\n".join(self.trace)

    def with_pending_gate(self) -> "KernelState":
        """Return a state with pending golden-gate approval."""
        return KernelState(
            current_step_id=self.current_step_id,
            pending_golden_gate=True,
            trace=[*self.trace],
        )

    def pending_gate_after_outcome(self, outcome: GateOutcome) -> bool:
        """Return pending gate state after one gate decision."""
        if self.pending_golden_gate and outcome in {
            GateOutcome.gate_approved,
            GateOutcome.gate_rejected,
            GateOutcome.gate_timed_out,
        }:
            return False
        return self.pending_golden_gate
