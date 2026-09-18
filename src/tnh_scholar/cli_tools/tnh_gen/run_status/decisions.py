"""Map existing command errors and service outcomes to runtime decisions."""

from enum import Enum

from tnh_scholar.cli_tools.tnh_gen.errors import ExitCode, map_exception
from tnh_scholar.cli_tools.tnh_gen.run_status.models import (
    RunFailure,
    RunOutcome,
    RunStage,
    TerminalDecision,
)
from tnh_scholar.gen_ai_service.models.domain import (
    CompletionEnvelope,
    CompletionOutcomeStatus,
    FailureReason,
)
from tnh_scholar.gen_ai_service.models.errors import SafetyBlocked


class StatusFailureCode(str, Enum):
    """Command-level codes absent from the service failure vocabulary."""

    INTERRUPTED = "INTERRUPTED"
    COMPLETION_FAILED = "COMPLETION_FAILED"
    SAFETY_BUDGET_BLOCKED = "SAFETY_BUDGET_BLOCKED"


def exception_failure(exc: Exception, stage: RunStage) -> RunFailure:
    """Use the same class-based code as the existing CLI error payload."""
    code = exc.__class__.__name__.upper()[:128]
    if (
        isinstance(exc, SafetyBlocked)
        and exc.blocked_reason == "budget"
        and exc.estimated_cost is not None
        and exc.max_dollars is not None
    ):
        code = StatusFailureCode.SAFETY_BUDGET_BLOCKED.value
    return RunFailure(origin_stage=stage, code=code)


def exception_decision(exc: Exception, stage: RunStage) -> TerminalDecision:
    """Capture an exception before control passes to diagnostic rendering."""
    exit_code = map_exception(exc)
    if (
        isinstance(exc, SafetyBlocked)
        and exc.blocked_reason == "budget"
        and exc.estimated_cost is not None
        and exc.max_dollars is not None
    ):
        exit_code = ExitCode.POLICY_ERROR
    return TerminalDecision(
        outcome=RunOutcome.FAILED, exit_code=int(exit_code), failure=exception_failure(exc, stage)
    )


def envelope_decision(envelope: CompletionEnvelope) -> TerminalDecision:
    """Classify failed envelopes at the generation boundary, before rendering."""
    if envelope.outcome is not CompletionOutcomeStatus.FAILED:
        return TerminalDecision()
    reason = envelope.failure.reason if envelope.failure else None
    code = reason.value.upper() if reason else StatusFailureCode.COMPLETION_FAILED.value
    exit_code = (
        ExitCode.FORMAT_ERROR
        if reason is FailureReason.CONTRACT_VALIDATION_FAILED
        else ExitCode.PROVIDER_ERROR
    )
    return TerminalDecision(
        outcome=RunOutcome.FAILED,
        exit_code=int(exit_code),
        failure=RunFailure(origin_stage=RunStage.GENERATING, code=code),
    )


def cancelled_decision(stage: RunStage) -> TerminalDecision:
    """Typer/Click translates an uncaught KeyboardInterrupt into abort exit 1."""
    return TerminalDecision(
        outcome=RunOutcome.CANCELLED,
        exit_code=1,
        failure=RunFailure(origin_stage=stage, code=StatusFailureCode.INTERRUPTED.value),
    )
