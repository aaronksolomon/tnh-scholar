import logging

import pytest

from tnh_scholar.cli_tools.audio_transcribe.audio_transcribe import (
    _normalize_transcript_texts,
)


def test_normalize_transcript_texts_accepts_string_entries() -> None:
    transcripts = [" first chunk ", "second chunk"]

    assert _normalize_transcript_texts(transcripts) == [
        "first chunk",
        "second chunk",
    ]


def test_normalize_transcript_texts_extracts_structured_entries(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transcripts = [
        {"chunk": None, "transcript": " first chunk ", "error": None},
        {"chunk": None, "transcript": None, "error": "upstream timeout"},
        {"chunk": None, "transcript": "second chunk", "error": None},
    ]

    with caplog.at_level(logging.WARNING):
        result = _normalize_transcript_texts(transcripts)

    assert result == ["first chunk", "second chunk"]
    assert "Skipping failed transcript chunk: upstream timeout" in caplog.text


def test_normalize_transcript_texts_warns_for_missing_error_details(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transcripts = [{"chunk": None, "transcript": None, "error": None}]

    with caplog.at_level(logging.WARNING):
        result = _normalize_transcript_texts(transcripts)

    assert result == []
    assert "Skipping failed transcript chunk without error details" in caplog.text


def test_normalize_transcript_texts_warns_for_non_string_transcript_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transcripts = [{"chunk": None, "transcript": 123, "error": None}]

    with caplog.at_level(logging.WARNING):
        result = _normalize_transcript_texts(transcripts)

    assert result == []
    assert "Skipping transcript entry with non-string text: int" in caplog.text


def test_normalize_transcript_texts_warns_for_unsupported_entries(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transcripts = [123]

    with caplog.at_level(logging.WARNING):
        result = _normalize_transcript_texts(transcripts)

    assert result == []
    assert "Skipping unsupported transcript entry type: int" in caplog.text
