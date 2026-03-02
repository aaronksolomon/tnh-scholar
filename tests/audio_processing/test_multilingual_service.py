from pathlib import Path

from tnh_scholar.audio_processing.multilingual_models import (
    ArtifactRetention,
    MultilingualTranscriptionRequest,
    SegmentTranscriptionRequest,
    SegmentTranscriptionResult,
    TranscriptionProvider,
)
from tnh_scholar.audio_processing.multilingual_service import (
    MultilingualTranscriptionService,
    PassThroughSubtitleMergeService,
    ProviderBackedSegmentTranscriptionService,
    SrtSegmentTranslationService,
)


class FakeTranscriptionService:
    def transcribe_segment(self, request) -> SegmentTranscriptionResult:
        return SegmentTranscriptionResult(
            provider=request.provider,
            source_language=request.source_language,
            target_language=request.target_language,
            source_srt="SOURCE SRT",
        )


class FakeTranslationService:
    def translate_segment(
        self,
        result: SegmentTranscriptionResult,
    ) -> SegmentTranscriptionResult:
        return result.model_copy(
            update={
                "translated_srt": "TRANSLATED SRT",
                "translation_skipped": False,
            }
        )


def test_translation_service_skips_when_source_matches_target() -> None:
    service = SrtSegmentTranslationService(target_language="en")
    result = SegmentTranscriptionResult(
        provider=TranscriptionProvider.WHISPER,
        source_language="en",
        target_language="en",
        source_srt="ALREADY ENGLISH",
    )

    translated = service.translate_segment(result)

    assert translated.translation_skipped is True
    assert translated.translated_srt == "ALREADY ENGLISH"


def test_translation_service_skips_when_source_srt_is_empty() -> None:
    service = SrtSegmentTranslationService(target_language="en")
    result = SegmentTranscriptionResult(
        provider=TranscriptionProvider.WHISPER,
        source_language="vi",
        target_language="en",
        source_srt="   ",
    )

    translated = service.translate_segment(result)

    assert translated.translation_skipped is True
    assert translated.translated_srt == "   "


def test_merge_service_requires_results() -> None:
    service = PassThroughSubtitleMergeService(ArtifactRetention.MINIMAL)

    try:
        service.merge([])
    except ValueError as exc:
        assert str(exc) == "At least one segment result is required for merge."
    else:
        raise AssertionError("Expected merge to reject empty results.")


def test_provider_backed_transcription_normalizes_empty_language() -> None:
    service = ProviderBackedSegmentTranscriptionService()
    request = SegmentTranscriptionRequest(
        audio_file=Path("sample.mp3"),
        provider=TranscriptionProvider.WHISPER,
        source_language="",
    )

    options = service._build_options(request)

    assert options is None


def test_multilingual_service_uses_injected_collaborators() -> None:
    service = MultilingualTranscriptionService(
        transcription_service=FakeTranscriptionService(),
        translation_service_factory=lambda _request: FakeTranslationService(),
    )
    request = MultilingualTranscriptionRequest(
        audio_file=Path("sample.mp3"),
        provider=TranscriptionProvider.ASSEMBLYAI,
        source_language="vi",
        artifact_retention=ArtifactRetention.DEBUG,
    )

    artifact = service.generate_subtitles(request)

    assert artifact.provider is TranscriptionProvider.ASSEMBLYAI
    assert artifact.source_srt == "SOURCE SRT"
    assert artifact.final_english_srt == "TRANSLATED SRT"
    assert artifact.artifact_retention is ArtifactRetention.DEBUG
