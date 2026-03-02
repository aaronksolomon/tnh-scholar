from __future__ import annotations

from types import MappingProxyType
from typing import Callable, Mapping

__all__ = [
    "ArtifactRetention",
    "DiarizationConfig",
    "MultilingualTranscriptionRequest",
    "MultilingualTranscriptionService",
    "TranscriptionProvider",
    "detect_nonsilent",
    "detect_whisper_boundaries",
    "split_audio",
    "split_audio_at_boundaries",
]


def _load_audio_legacy_export(name: str):
    from . import audio_legacy

    return getattr(audio_legacy, name)


def _load_multilingual_export(name: str):
    if name == "MultilingualTranscriptionService":
        from tnh_scholar.audio_processing.multilingual_service import (
            MultilingualTranscriptionService,
        )

        return MultilingualTranscriptionService
    from . import multilingual_models

    return getattr(multilingual_models, name)


def _load_diarization_config():
    from tnh_scholar.audio_processing.diarization.config import DiarizationConfig

    return DiarizationConfig


_LOADERS: Mapping[str, Callable[[], object]] = {
    "detect_nonsilent": lambda: _load_audio_legacy_export("detect_nonsilent"),
    "detect_whisper_boundaries": lambda: _load_audio_legacy_export("detect_whisper_boundaries"),
    "split_audio": lambda: _load_audio_legacy_export("split_audio"),
    "split_audio_at_boundaries": lambda: _load_audio_legacy_export("split_audio_at_boundaries"),
    "ArtifactRetention": lambda: _load_multilingual_export("ArtifactRetention"),
    "MultilingualTranscriptionRequest": lambda: _load_multilingual_export(
        "MultilingualTranscriptionRequest"
    ),
    "TranscriptionProvider": lambda: _load_multilingual_export("TranscriptionProvider"),
    "MultilingualTranscriptionService": lambda: _load_multilingual_export(
        "MultilingualTranscriptionService"
    ),
    "DiarizationConfig": _load_diarization_config,
}
_LOADERS = MappingProxyType(_LOADERS)


def __getattr__(name: str):
    """Lazily expose audio processing exports to avoid heavy import side effects."""
    loader = _LOADERS.get(name)
    if loader is None:
        raise AttributeError(f"module 'tnh_scholar.audio_processing' has no attribute {name!r}")
    return loader()
