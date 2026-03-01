from __future__ import annotations

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


def __getattr__(name: str):
    """Lazily expose audio processing exports to avoid heavy import side effects."""
    if name in {
        "detect_nonsilent",
        "detect_whisper_boundaries",
        "split_audio",
        "split_audio_at_boundaries",
    }:
        return _load_audio_legacy_export(name)
    if name in {
        "ArtifactRetention",
        "MultilingualTranscriptionRequest",
        "TranscriptionProvider",
        "MultilingualTranscriptionService",
    }:
        return _load_multilingual_export(name)
    if name == "DiarizationConfig":
        from tnh_scholar.audio_processing.diarization.config import DiarizationConfig

        return DiarizationConfig
    raise AttributeError(f"module 'tnh_scholar.audio_processing' has no attribute {name!r}")


def _load_audio_legacy_export(name: str):
    from tnh_scholar.audio_processing import audio_legacy

    return getattr(audio_legacy, name)


def _load_multilingual_export(name: str):
    if name == "MultilingualTranscriptionService":
        from tnh_scholar.audio_processing.multilingual_service import (
            MultilingualTranscriptionService,
        )

        return MultilingualTranscriptionService
    from tnh_scholar.audio_processing import multilingual_models

    return getattr(multilingual_models, name)
