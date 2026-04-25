from importlib import import_module

import pytest

audio_transcribe_module = import_module(
    "tnh_scholar.cli_tools.audio_transcribe.audio_transcribe"
)


def _capture_warning_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> list[str]:
    """Capture warning messages sent through the module logger."""
    warning_messages: list[str] = []

    def _fake_warning(message: str, *args: object) -> None:
        if args:
            warning_messages.append(message % args)
            return
        warning_messages.append(message)

    monkeypatch.setattr(audio_transcribe_module.logger, "warning", _fake_warning)
    return warning_messages


def test_normalize_transcript_texts_accepts_string_entries() -> None:
    transcripts = [" first chunk ", "second chunk"]

    assert audio_transcribe_module._normalize_transcript_texts(transcripts) == [
        "first chunk",
        "second chunk",
    ]


def test_normalize_transcript_texts_extracts_structured_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transcripts = [
        {"chunk": None, "transcript": " first chunk ", "error": None},
        {"chunk": None, "transcript": None, "error": "upstream timeout"},
        {"chunk": None, "transcript": "second chunk", "error": None},
    ]

    warning_messages = _capture_warning_messages(monkeypatch)
    result = audio_transcribe_module._normalize_transcript_texts(transcripts)

    assert result == ["first chunk", "second chunk"]
    assert "Skipping failed transcript chunk: upstream timeout" in warning_messages


def test_normalize_transcript_texts_warns_for_missing_error_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transcripts = [{"chunk": None, "transcript": None, "error": None}]

    warning_messages = _capture_warning_messages(monkeypatch)
    result = audio_transcribe_module._normalize_transcript_texts(transcripts)

    assert result == []
    assert any(
        message.startswith("Skipping failed transcript chunk without error details")
        for message in warning_messages
    )


def test_normalize_transcript_texts_warns_for_non_string_transcript_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transcripts = [{"chunk": None, "transcript": 123, "error": None}]

    warning_messages = _capture_warning_messages(monkeypatch)
    result = audio_transcribe_module._normalize_transcript_texts(transcripts)

    assert result == []
    assert "Skipping transcript entry with non-string text: int" in warning_messages


def test_normalize_transcript_texts_warns_for_unsupported_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transcripts = [123]

    warning_messages = _capture_warning_messages(monkeypatch)
    result = audio_transcribe_module._normalize_transcript_texts(transcripts)

    assert result == []
    assert "Skipping unsupported transcript entry type: int" in warning_messages
