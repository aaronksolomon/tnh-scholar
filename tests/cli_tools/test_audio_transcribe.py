import logging
from importlib import import_module

import pytest

audio_transcribe_module = import_module(
    "tnh_scholar.cli_tools.audio_transcribe.audio_transcribe"
)


def test_normalize_transcript_texts_accepts_string_entries() -> None:
    transcripts = [" first chunk ", "second chunk"]

    assert audio_transcribe_module._normalize_transcript_texts(transcripts) == [
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

    caplog.set_level(logging.WARNING, logger=audio_transcribe_module.logger.name)
    result = audio_transcribe_module._normalize_transcript_texts(transcripts)

    assert result == ["first chunk", "second chunk"]
    assert any(
        "Skipping failed transcript chunk: upstream timeout" in record.message
        for record in caplog.records
    )


def test_normalize_transcript_texts_warns_for_missing_error_details(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transcripts = [{"chunk": None, "transcript": None, "error": None}]

    caplog.set_level(logging.WARNING, logger=audio_transcribe_module.logger.name)
    result = audio_transcribe_module._normalize_transcript_texts(transcripts)

    assert result == []
    assert any(
        "Skipping failed transcript chunk without error details" in record.message
        for record in caplog.records
    )


def test_normalize_transcript_texts_warns_for_non_string_transcript_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transcripts = [{"chunk": None, "transcript": 123, "error": None}]

    caplog.set_level(logging.WARNING, logger=audio_transcribe_module.logger.name)
    result = audio_transcribe_module._normalize_transcript_texts(transcripts)

    assert result == []
    assert any(
        "Skipping transcript entry with non-string text: int" in record.message
        for record in caplog.records
    )


def test_normalize_transcript_texts_warns_for_unsupported_entries(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transcripts = [123]

    caplog.set_level(logging.WARNING, logger=audio_transcribe_module.logger.name)
    result = audio_transcribe_module._normalize_transcript_texts(transcripts)

    assert result == []
    assert any(
        "Skipping unsupported transcript entry type: int" in record.message
        for record in caplog.records
    )
