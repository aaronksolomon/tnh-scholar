import importlib.util

import pytest

from tnh_scholar.audio_processing.transcription.transcription_service import (
    TranscriptionServiceFactory,
)


def test_factory_missing_assemblyai_dependency() -> None:
    if importlib.util.find_spec("assemblyai") is not None:
        pytest.skip("assemblyai is installed; skipping missing-dependency test")

    with pytest.raises(ImportError, match="assemblyai package is not installed"):
        TranscriptionServiceFactory.create_service(provider="assemblyai")


def test_factory_creates_assemblyai_when_installed() -> None:
    if importlib.util.find_spec("assemblyai") is None:
        pytest.skip("assemblyai is not installed; skipping installed-provider test")

    service = TranscriptionServiceFactory.create_service(provider="assemblyai")

    assert service is not None
