"""Shared kernel enums used across orchestration contracts."""

from __future__ import annotations

from enum import Enum

from tnh_scholar.agent_orchestration.shared_enums import AgentFamily, RunnerTermination


class Opcode(str, Enum):
    """Kernel opcode names.

    Values intentionally mirror the accepted OA04 workflow schema tokens.
    """

    run_agent = "RUN_AGENT"
    run_validation = "RUN_VALIDATION"
    evaluate = "EVALUATE"
    gate = "GATE"
    rollback = "ROLLBACK"
    stop = "STOP"


class MechanicalOutcome(str, Enum):
    """Mechanical outcomes used for kernel routing."""

    completed = "completed"
    error = "error"
    killed_timeout = "killed_timeout"
    killed_idle = "killed_idle"
    killed_policy = "killed_policy"


class PlannerStatus(str, Enum):
    """Semantic planner statuses."""

    success = "success"
    partial = "partial"
    blocked = "blocked"
    unsafe = "unsafe"
    needs_human = "needs_human"


class GateOutcome(str, Enum):
    """Human gate outcomes."""

    gate_approved = "gate_approved"
    gate_rejected = "gate_rejected"
    gate_timed_out = "gate_timed_out"


__all__ = [
    "AgentFamily",
    "GateOutcome",
    "MechanicalOutcome",
    "Opcode",
    "PlannerStatus",
    "RunnerTermination",
]
