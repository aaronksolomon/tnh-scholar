"""Tests for response extraction utilities."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import BaseModel

from tnh_scholar.gen_ai_service.models.domain import (
    CompletionEnvelope,
    CompletionResult,
    Fingerprint,
    Provenance,
    Usage,
)
from tnh_scholar.gen_ai_service.models.transport import FinishReason
from tnh_scholar.gen_ai_service.utils.response_utils import (
    extract_finish_reason,
    extract_object,
    extract_provenance,
    extract_text,
    extract_usage,
    is_successful,
)


class SampleModel(BaseModel):
    """Sample Pydantic model for testing."""
    name: str
    value: int


def _create_test_envelope(text: str = "Test response") -> CompletionEnvelope:
    """Helper to create a test envelope."""
    return CompletionEnvelope(
        result=CompletionResult(
            text=text,
            usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            model="gpt-4o",
            provider="openai",
        ),
        provenance=Provenance(
            provider="openai",
            model="gpt-4o",
            sdk_version="2.5.0",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            finished_at=datetime(2025, 1, 1, 12, 0, 5),
            attempt_count=1,
            fingerprint=Fingerprint(
                prompt_key="test",
                prompt_name="test_prompt",
                prompt_base_path="/test/path",
                prompt_content_hash="abc123",
                variables_hash="def456",
                user_string_hash="ghi789",
            ),
        ),
        policy_applied={},
        warnings=[],
    )


def test_extract_text():
    """Test extracting text from envelope."""
    envelope = _create_test_envelope("Hello, world!")

    text = extract_text(envelope)
    assert text == "Hello, world!"


def test_extract_text_no_result():
    """Test extracting text when envelope has no result."""
    envelope = CompletionEnvelope.model_construct(
        result=None,
        provenance=None,
        policy_applied={},
        warnings=[],
    )

    with pytest.raises(ValueError, match="has no result"):
        extract_text(envelope)


def test_extract_text_no_content():
    """Test extracting text when result has no text."""
    envelope = _create_test_envelope()
    envelope.result.text = None

    with pytest.raises(ValueError, match="has no text content"):
        extract_text(envelope)


def test_extract_object_not_supported_by_default():
    """Structured outputs should raise clear error when unavailable."""
    envelope = _create_test_envelope()

    with pytest.raises(ValueError, match="Structured outputs are not yet supported"):
        extract_object(envelope)


def test_extract_object_with_type_check():
    """Test extracting object when parsed payload is manually provided."""
    envelope = _create_test_envelope()
    object.__setattr__(envelope.result, "parsed", SampleModel(name="test", value=42))

    obj = extract_object(envelope, model_class=SampleModel)
    assert isinstance(obj, SampleModel)


def test_extract_object_wrong_type():
    """Test extracting object with wrong type raises error."""
    class OtherModel(BaseModel):
        foo: str

    envelope = _create_test_envelope()
    object.__setattr__(envelope.result, "parsed", SampleModel(name="test", value=42))

    with pytest.raises(TypeError, match="Expected object of type"):
        extract_object(envelope, model_class=OtherModel)


def test_extract_usage():
    """Test extracting token usage."""
    envelope = _create_test_envelope()

    usage = extract_usage(envelope)

    assert usage["tokens_in"] == 10
    assert usage["tokens_out"] == 5
    assert usage["total_tokens"] == 15


def test_extract_usage_no_usage():
    """Test extracting usage when none exists."""
    envelope = _create_test_envelope()
    envelope.result.usage = None

    usage = extract_usage(envelope)

    assert usage["tokens_in"] == 0
    assert usage["tokens_out"] == 0
    assert usage["total_tokens"] == 0


def test_extract_provenance():
    """Test extracting provenance metadata."""
    envelope = _create_test_envelope()

    prov = extract_provenance(envelope)

    assert prov["provider"] == "openai"
    assert prov["model"] == "gpt-4o"
    assert prov["attempt_count"] == 1
    assert prov["duration_seconds"] == 5.0  # 5 second duration

    # Check fingerprint included
    assert "fingerprint" in prov
    assert prov["fingerprint"]["prompt_key"] == "test"


def test_extract_provenance_no_provenance():
    """Test extracting provenance when none exists."""
    envelope = CompletionEnvelope.model_construct(
        result=_create_test_envelope().result,
        provenance=None,
        policy_applied={},
        warnings=[],
    )

    prov = extract_provenance(envelope)
    assert prov == {}


def test_extract_finish_reason():
    """Test extracting finish reason when field is present."""
    envelope = _create_test_envelope()
    object.__setattr__(envelope.result, "finish_reason", FinishReason.STOP)

    reason = extract_finish_reason(envelope)
    assert reason == "stop"


def test_extract_finish_reason_none():
    """Test extracting finish reason when none exists."""
    envelope = _create_test_envelope()

    reason = extract_finish_reason(envelope)
    assert reason is None


def test_is_successful_with_text():
    """Test checking success with text result."""
    envelope = _create_test_envelope("Success!")

    assert is_successful(envelope) is True


def test_is_successful_with_object():
    """Test checking success with structured object."""
    envelope = _create_test_envelope()
    envelope.result.text = None
    object.__setattr__(envelope.result, "parsed", SampleModel(name="test", value=42))

    assert is_successful(envelope) is True


def test_is_successful_no_result():
    """Test checking success when no result."""
    envelope = CompletionEnvelope.model_construct(
        result=None,
        provenance=None,
        policy_applied={},
        warnings=[],
    )

    assert is_successful(envelope) is False


def test_is_successful_no_content():
    """Test checking success when result has no content."""
    envelope = _create_test_envelope()
    envelope.result.text = None
    # No parsed either

    assert is_successful(envelope) is False
