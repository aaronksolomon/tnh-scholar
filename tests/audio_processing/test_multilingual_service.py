from __future__ import annotations

import logging
import wave
from io import BytesIO
from pathlib import Path

from tnh_scholar.audio_processing.audio_slice_utils import resolve_audio_format
from tnh_scholar.audio_processing.diarization.models import DiarizedSegment
from tnh_scholar.audio_processing.language_utils import normalize_language_code
from tnh_scholar.audio_processing.multilingual_models import (
    ArtifactRetention,
    LanguageDetectionResult,
    MultilingualTranscriptionRequest,
    SegmentTranscriptionRequest,
    SegmentTranscriptionResult,
    SpeakerLanguageBlock,
    TranscriptionProvider,
)
from tnh_scholar.audio_processing.multilingual_service import (
    MultilingualTranscriptionService,
    PassThroughSubtitleMergeService,
    ProviderBackedSegmentTranscriptionService,
    SrtSegmentTranslationService,
)
from tnh_scholar.utils import TimeMs


class FakeTranscriptionService:
    def __init__(self) -> None:
        self.requests: list[SegmentTranscriptionRequest] = []

    def transcribe_segment(self, request: SegmentTranscriptionRequest) -> SegmentTranscriptionResult:
        self.requests.append(request)
        body = "HELLO" if request.source_language == "en" else "XIN CHAO"
        return SegmentTranscriptionResult(
            provider=request.provider,
            source_language=request.source_language,
            target_language=request.target_language,
            source_srt=(f"1\n00:00:00,000 --> 00:00:00,500\n{body}\n"),
        )


class FakeTranslationService:
    def translate_segment(
        self,
        result: SegmentTranscriptionResult,
    ) -> SegmentTranscriptionResult:
        if result.source_language == "en":
            return result.model_copy(
                update={
                    "translated_srt": result.source_srt,
                    "translation_skipped": True,
                }
            )
        return result.model_copy(
            update={
                "translated_srt": ("1\n00:00:00,000 --> 00:00:00,500\nHELLO FROM VI\n"),
                "translation_skipped": False,
            }
        )


class RecordingTranslationService:
    def __init__(self) -> None:
        self.seen_languages: list[str | None] = []

    def translate_segment(
        self,
        result: SegmentTranscriptionResult,
    ) -> SegmentTranscriptionResult:
        self.seen_languages.append(result.source_language)
        if result.source_language == "en":
            return result.model_copy(
                update={
                    "translated_srt": result.source_srt,
                    "translation_skipped": True,
                }
            )
        if result.source_language is None:
            return result.model_copy(
                update={
                    "translated_srt": ("1\n00:00:00,000 --> 00:00:00,500\nFALLBACK ENGLISH\n"),
                    "translation_skipped": False,
                }
            )
        return result.model_copy(
            update={
                "translated_srt": (f"1\n00:00:00,000 --> 00:00:00,500\nEN:{result.source_language}\n"),
                "translation_skipped": False,
            }
        )


class FailureAwareTranslationService:
    def __init__(self) -> None:
        self.error_messages: list[str | None] = []

    def translate_segment(
        self,
        result: SegmentTranscriptionResult,
    ) -> SegmentTranscriptionResult:
        self.error_messages.append(result.error_message)
        if result.error_message is not None:
            return result.model_copy(
                update={
                    "translated_srt": result.source_srt,
                    "translation_skipped": True,
                }
            )
        return result.model_copy(
            update={
                "translated_srt": ("1\n00:00:00,000 --> 00:00:00,500\nTRANSLATED OK\n"),
                "translation_skipped": False,
            }
        )


class FakeSegmentationService:
    def build_blocks(
        self,
        _request: MultilingualTranscriptionRequest,
    ) -> list[SpeakerLanguageBlock]:
        return [
            SpeakerLanguageBlock(
                speaker_label="SPEAKER_00",
                start_ms=0,
                end_ms=500,
                detection=LanguageDetectionResult(
                    language_code="en",
                    confidence=1.0,
                    detector_source="test",
                ),
            ),
            SpeakerLanguageBlock(
                speaker_label="SPEAKER_01",
                start_ms=1000,
                end_ms=1500,
                detection=LanguageDetectionResult(
                    language_code="vi",
                    confidence=1.0,
                    detector_source="test",
                ),
            ),
        ]


class MixedRoutingSegmentationService:
    def build_blocks(
        self,
        _request: MultilingualTranscriptionRequest,
    ) -> list[SpeakerLanguageBlock]:
        return [
            SpeakerLanguageBlock(
                speaker_label="SPEAKER_00",
                start_ms=0,
                end_ms=500,
                detection=LanguageDetectionResult(
                    language_code="en",
                    confidence=1.0,
                    detector_source="test",
                ),
            ),
            SpeakerLanguageBlock(
                speaker_label="SPEAKER_01",
                start_ms=600,
                end_ms=1100,
                detection=LanguageDetectionResult(
                    language_code="vi",
                    confidence=1.0,
                    detector_source="test",
                ),
            ),
            SpeakerLanguageBlock(
                speaker_label="SPEAKER_02",
                start_ms=1200,
                end_ms=1700,
                detection=LanguageDetectionResult(
                    language_code=None,
                    confidence=0.0,
                    detector_source="test",
                    is_reliable=False,
                ),
                is_uncertain=True,
            ),
        ]


class PartialFailureTranscriptionService:
    def __init__(self) -> None:
        self.calls = 0

    def transcribe_segment(
        self,
        request: SegmentTranscriptionRequest,
    ) -> SegmentTranscriptionResult:
        self.calls += 1
        if self.calls == 1:
            return SegmentTranscriptionResult(
                provider=request.provider,
                source_language=request.source_language,
                target_language=request.target_language,
                source_srt=("1\n00:00:00,000 --> 00:00:00,500\nFIRST BLOCK\n"),
            )
        return SegmentTranscriptionResult(
            provider=request.provider,
            source_language=request.source_language,
            target_language=request.target_language,
            source_srt=("1\n00:00:00,000 --> 00:00:00,500\ntranscription unavailable\n"),
            error_message="mock transcription failure",
        )


class InvalidSrtFailureTranscriptionService:
    def __init__(self) -> None:
        self.calls = 0

    def transcribe_segment(
        self,
        request: SegmentTranscriptionRequest,
    ) -> SegmentTranscriptionResult:
        self.calls += 1
        if self.calls == 1:
            return SegmentTranscriptionResult(
                provider=request.provider,
                source_language=request.source_language,
                target_language=request.target_language,
                source_srt=("1\n00:00:00,000 --> 00:00:00,500\nVALID BLOCK\n"),
            )
        return SegmentTranscriptionResult(
            provider=request.provider,
            source_language=request.source_language,
            target_language=request.target_language,
            source_srt="not a valid srt payload",
            error_message="upstream returned malformed subtitle content",
        )


def _write_silent_wav(path: Path, duration_ms: int = 2000) -> None:
    frame_rate = 16000
    frame_count = int(frame_rate * (duration_ms / 1000))
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(frame_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count)


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


def test_translation_service_skips_for_normalized_language_names() -> None:
    service = SrtSegmentTranslationService(target_language="en")
    result = SegmentTranscriptionResult(
        provider=TranscriptionProvider.WHISPER,
        source_language="English",
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


def test_translation_service_skips_when_result_has_error_message() -> None:
    service = SrtSegmentTranslationService(target_language="en")
    result = SegmentTranscriptionResult(
        provider=TranscriptionProvider.WHISPER,
        source_language="vi",
        target_language="en",
        source_srt="1\n00:00:00,000 --> 00:00:00,500\n[error]\n",
        error_message="upstream failed",
    )

    translated = service.translate_segment(result)

    assert translated.translation_skipped is True
    assert translated.translated_srt == result.source_srt


def test_merge_service_requires_results() -> None:
    service = PassThroughSubtitleMergeService(ArtifactRetention.MINIMAL)

    try:
        service.merge([])
    except ValueError as exc:
        assert str(exc) == "At least one segment result is required for merge."
    else:
        raise AssertionError("Expected merge to reject empty results.")


def test_merge_service_shifts_and_combines_segment_srts() -> None:
    service = PassThroughSubtitleMergeService(ArtifactRetention.MINIMAL)
    first = SegmentTranscriptionResult(
        provider=TranscriptionProvider.WHISPER,
        segment_start_ms=0,
        source_language="en",
        target_language="en",
        source_srt="1\n00:00:00,000 --> 00:00:00,300\nONE\n",
        translated_srt="1\n00:00:00,000 --> 00:00:00,300\nONE\n",
    )
    second = SegmentTranscriptionResult(
        provider=TranscriptionProvider.WHISPER,
        segment_start_ms=1000,
        source_language="vi",
        target_language="en",
        source_srt="1\n00:00:00,000 --> 00:00:00,300\nHAI\n",
        translated_srt="1\n00:00:00,000 --> 00:00:00,300\nTWO\n",
    )

    artifact = service.merge([first, second])

    assert "00:00:01,000 --> 00:00:01,300" in artifact.final_english_srt
    assert "TWO" in artifact.final_english_srt
    assert "HAI" in artifact.source_srt
    assert artifact.source_language is None


def test_provider_backed_transcription_normalizes_empty_language() -> None:
    service = ProviderBackedSegmentTranscriptionService()
    request = SegmentTranscriptionRequest(
        audio_file=Path("sample.mp3"),
        provider=TranscriptionProvider.WHISPER,
        source_language="",
    )

    options = service._build_options(request)

    assert options is None


def test_provider_backed_transcription_adds_file_extension_for_bytesio() -> None:
    service = ProviderBackedSegmentTranscriptionService()
    request = SegmentTranscriptionRequest(
        audio_file=BytesIO(b"fake-audio"),
        audio_file_extension="mp3",
        provider=TranscriptionProvider.WHISPER,
        source_language="vi",
    )

    options = service._build_options(request)

    assert options == {"language": "vi", "file_extension": "mp3"}


def test_provider_backed_transcription_normalizes_language_names() -> None:
    service = ProviderBackedSegmentTranscriptionService()
    request = SegmentTranscriptionRequest(
        audio_file=BytesIO(b"fake-audio"),
        audio_file_extension="wav",
        provider=TranscriptionProvider.WHISPER,
        source_language="Vietnamese",
    )

    options = service._build_options(request)

    assert options == {"language": "vi", "file_extension": "wav"}


def test_normalize_language_code_maps_common_aliases() -> None:
    assert normalize_language_code("English") == "en"
    assert normalize_language_code("vi-VN") == "vi"
    assert normalize_language_code(" Cantonese ") == "zh"
    assert normalize_language_code("") is None


def test_resolve_audio_format_defaults_to_wav_without_suffix() -> None:
    assert resolve_audio_format(Path("sample")) == "wav"
    assert resolve_audio_format(Path("sample.MP3")) == "mp3"


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
    assert "XIN CHAO" in artifact.source_srt
    assert "HELLO FROM VI" in artifact.final_english_srt
    assert artifact.artifact_retention is ArtifactRetention.DEBUG


def test_multilingual_service_routes_speaker_blocks_and_merges(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    transcription_service = FakeTranscriptionService()
    service = MultilingualTranscriptionService(
        transcription_service=transcription_service,
        segmentation_service=FakeSegmentationService(),
        translation_service_factory=lambda _request: FakeTranslationService(),
    )
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        provider=TranscriptionProvider.WHISPER,
        target_language="en",
        use_speaker_blocks=True,
    )

    artifact = service.generate_subtitles(request)

    assert len(transcription_service.requests) == 2
    assert isinstance(transcription_service.requests[0].audio_file, BytesIO)
    assert "00:00:01,000 --> 00:00:01,500" in artifact.final_english_srt
    assert "HELLO FROM VI" in artifact.final_english_srt
    assert "XIN CHAO" in artifact.source_srt


def test_multilingual_service_uses_precomputed_diarization_segments(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    transcription_service = FakeTranscriptionService()
    diarization_segments = [
        DiarizedSegment(
            speaker="SPEAKER_00",
            start=TimeMs(0),
            end=TimeMs(500),
            audio_map_start=None,
            gap_before=None,
            spacing_time=None,
        ),
        DiarizedSegment(
            speaker="SPEAKER_00",
            start=TimeMs(600),
            end=TimeMs(900),
            audio_map_start=None,
            gap_before=None,
            spacing_time=None,
        ),
    ]
    service = MultilingualTranscriptionService(
        transcription_service=transcription_service,
        translation_service_factory=lambda _request: FakeTranslationService(),
    )
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        source_language="en",
        diarization_segments=diarization_segments,
    )

    artifact = service.generate_subtitles(request)

    assert len(transcription_service.requests) == 1
    assert artifact.source_language == "en"
    assert "HELLO" in artifact.final_english_srt


def test_multilingual_service_routes_translation_by_language(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    transcription_service = FakeTranscriptionService()
    translation_service = RecordingTranslationService()
    service = MultilingualTranscriptionService(
        transcription_service=transcription_service,
        segmentation_service=MixedRoutingSegmentationService(),
        translation_service_factory=lambda _request: translation_service,
    )
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        provider=TranscriptionProvider.WHISPER,
        target_language="en",
        use_speaker_blocks=True,
    )

    artifact = service.generate_subtitles(request)

    assert translation_service.seen_languages == ["en", "vi", None]
    assert "HELLO" in artifact.final_english_srt
    assert "EN:vi" in artifact.final_english_srt
    assert "FALLBACK ENGLISH" in artifact.final_english_srt
    assert "XIN CHAO" in artifact.source_srt


def test_multilingual_service_preserves_block_order_in_merged_output(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    service = MultilingualTranscriptionService(
        transcription_service=FakeTranscriptionService(),
        segmentation_service=MixedRoutingSegmentationService(),
        translation_service_factory=lambda _request: RecordingTranslationService(),
    )
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        provider=TranscriptionProvider.WHISPER,
        target_language="en",
        use_speaker_blocks=True,
    )

    artifact = service.generate_subtitles(request)

    english_index = artifact.final_english_srt.index("HELLO")
    vi_index = artifact.final_english_srt.index("EN:vi")
    fallback_index = artifact.final_english_srt.index("FALLBACK ENGLISH")

    assert english_index < vi_index < fallback_index
    assert "00:00:00,600 --> 00:00:01,100" in artifact.final_english_srt
    assert "00:00:01,200 --> 00:00:01,700" in artifact.final_english_srt


def test_multilingual_service_preserves_partial_failure_blocks_in_merge(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    translation_service = FailureAwareTranslationService()
    service = MultilingualTranscriptionService(
        transcription_service=PartialFailureTranscriptionService(),
        segmentation_service=FakeSegmentationService(),
        translation_service_factory=lambda _request: translation_service,
    )
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        provider=TranscriptionProvider.WHISPER,
        target_language="en",
        use_speaker_blocks=True,
    )

    artifact = service.generate_subtitles(request)

    assert translation_service.error_messages == [None, "mock transcription failure"]
    assert "TRANSLATED OK" in artifact.final_english_srt
    assert "transcription unavailable" in artifact.final_english_srt
    assert "transcription unavailable" in artifact.source_srt


def test_multilingual_service_skips_malformed_failed_block_during_merge(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    translation_service = FailureAwareTranslationService()
    service = MultilingualTranscriptionService(
        transcription_service=InvalidSrtFailureTranscriptionService(),
        segmentation_service=FakeSegmentationService(),
        translation_service_factory=lambda _request: translation_service,
    )
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        provider=TranscriptionProvider.WHISPER,
        target_language="en",
        use_speaker_blocks=True,
    )

    artifact = service.generate_subtitles(request)

    assert translation_service.error_messages == [None, "upstream returned malformed subtitle content"]
    assert "TRANSLATED OK" in artifact.final_english_srt
    assert "not a valid srt payload" not in artifact.final_english_srt
    assert "VALID BLOCK" in artifact.source_srt


def test_multilingual_service_logs_when_skipping_malformed_failed_block(
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    service = MultilingualTranscriptionService(
        transcription_service=InvalidSrtFailureTranscriptionService(),
        segmentation_service=FakeSegmentationService(),
        translation_service_factory=lambda _request: FailureAwareTranslationService(),
    )
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        provider=TranscriptionProvider.WHISPER,
        target_language="en",
        use_speaker_blocks=True,
    )

    logger_name = "tnh.tnh_scholar.audio_processing.multilingual_service"
    target_logger = logging.getLogger(logger_name)
    records: list[logging.LogRecord] = []

    class _CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _CaptureHandler(level=logging.WARNING)
    previous_level = target_logger.level
    target_logger.addHandler(handler)
    target_logger.setLevel(logging.WARNING)
    try:
        service.generate_subtitles(request)
    finally:
        target_logger.removeHandler(handler)
        target_logger.setLevel(previous_level)

    warning_record = next(
        record
        for record in records
        if "Skipping malformed failed subtitle block at 1000ms" in record.getMessage()
    )
    assert getattr(warning_record, "provider") == "whisper"
    assert getattr(warning_record, "source_language") == "vi"
    assert getattr(warning_record, "target_language") == "en"
    assert getattr(warning_record, "segment_start_ms") == 1000
    assert getattr(warning_record, "translation_skipped") is True
    assert getattr(warning_record, "error_message") == "upstream returned malformed subtitle content"
