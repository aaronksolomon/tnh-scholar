"""Typed fixtures for runtime status contracts."""

from datetime import UTC, datetime

import pytest

from tnh_scholar.cli_tools.tnh_gen.run_status.models import RunStatusMetadata
from tnh_scholar.gen_ai_service.models.domain import (
    CompletionEnvelope,
    CompletionOutcomeStatus,
    CompletionResult,
    Fingerprint,
    Provenance,
)


@pytest.fixture
def metadata() -> RunStatusMetadata:
    return RunStatusMetadata(trace_id="trace-test", prompt_key="daily", input_file_name="input.txt")


@pytest.fixture
def envelope() -> CompletionEnvelope:
    now = datetime.now(UTC)
    return CompletionEnvelope(
        outcome=CompletionOutcomeStatus.SUCCEEDED,
        result=CompletionResult(
            text="generated text", usage=None, model="resolved-model", provider="openai", finish_reason="stop"
        ),
        provenance=Provenance(
            provider="openai",
            model="resolved-model",
            started_at=now,
            finished_at=now,
            attempt_count=1,
            fingerprint=Fingerprint(
                prompt_key="daily",
                prompt_name="Daily",
                prompt_base_path=".",
                prompt_content_hash="prompt",
                variables_hash="vars",
                user_string_hash="input",
            ),
        ),
    )
