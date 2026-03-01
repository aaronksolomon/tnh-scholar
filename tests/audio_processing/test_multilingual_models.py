from pathlib import Path

import pytest
from pydantic import ValidationError

from tnh_scholar.audio_processing.multilingual_models import (
    MultilingualTranscriptionRequest,
    TranscriptionProvider,
)


def test_multilingual_request_defaults_to_whisper() -> None:
    request = MultilingualTranscriptionRequest(audio_file=Path("sample.mp3"))

    assert request.provider is TranscriptionProvider.WHISPER
    assert request.skip_translation is False


def test_multilingual_request_rejects_invalid_caption_width() -> None:
    with pytest.raises(ValidationError):
        MultilingualTranscriptionRequest(
            audio_file=Path("sample.mp3"),
            chars_per_caption=0,
        )
