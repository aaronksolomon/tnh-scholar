"""Kernel state models."""

from __future__ import annotations

from dataclasses import dataclass, field


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
