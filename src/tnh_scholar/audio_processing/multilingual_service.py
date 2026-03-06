from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Callable, cast

from tnh_scholar.ai_text_processing import get_pattern
from tnh_scholar.audio_processing.audio_slice_utils import (
    resolve_audio_format,
    slice_audio_bytes,
)
from tnh_scholar.audio_processing.diarization.config import DiarizationConfig
from tnh_scholar.audio_processing.diarization.models import (
    AugDiarizedSegment,
    DiarizedSegment,
    SpeakerBlock,
)
from tnh_scholar.audio_processing.diarization.pyannote_diarize import diarize
from tnh_scholar.audio_processing.diarization.schemas import DiarizationSucceeded
from tnh_scholar.audio_processing.diarization.strategies.language_probe import (
    LanguageProbe,
    WhisperLanguageDetector,
)
from tnh_scholar.audio_processing.diarization.strategies.speaker_blocker import (
    group_speaker_blocks,
)
from tnh_scholar.audio_processing.language_utils import normalize_language_code
from tnh_scholar.audio_processing.multilingual_models import (
    ArtifactRetention,
    LanguageDetectionResult,
    MergedSubtitleArtifact,
    MultilingualTranscriptionRequest,
    SegmentTranscriptionRequest,
    SegmentTranscriptionResult,
    SpeakerLanguageBlock,
)
from tnh_scholar.audio_processing.multilingual_protocols import (
    LanguageSegmentationServiceProtocol,
    SegmentTranscriptionServiceProtocol,
    SegmentTranslationServiceProtocol,
    SubtitleMergeServiceProtocol,
)
from tnh_scholar.audio_processing.timed_object.timed_text import Granularity, TimedText
from tnh_scholar.audio_processing.transcription.srt_processor import SRTProcessor
from tnh_scholar.audio_processing.transcription.transcription_service import (
    TranscriptionServiceFactory,
)
from tnh_scholar.cli_tools.srt_translate.srt_translate import SrtTranslator
from tnh_scholar.logging_config import get_logger
from tnh_scholar.metadata.metadata import Frontmatter, Metadata
from tnh_scholar.utils import TimeMs
from tnh_scholar.utils import TNHAudioSegment as AudioSegment

logger = get_logger(__name__)


class ProviderBackedSegmentTranscriptionService(SegmentTranscriptionServiceProtocol):
    """Bridge to the existing provider transcription services."""

    def transcribe_segment(
        self,
        request: SegmentTranscriptionRequest,
    ) -> SegmentTranscriptionResult:
        service = self._create_service(request)
        source_srt = service.transcribe_to_format(
            request.audio_file,
            format_type="srt",
            transcription_options=self._build_options(request),
            format_options={"chars_per_caption": request.chars_per_caption},
        )
        return SegmentTranscriptionResult(
            provider=request.provider,
            source_language=request.source_language,
            target_language=request.target_language,
            source_srt=source_srt,
        )

    def _create_service(self, request: SegmentTranscriptionRequest) -> Any:
        service_kwargs: dict[str, Any] = {}
        if request.transcription_model is not None:
            service_kwargs["model"] = request.transcription_model
        return TranscriptionServiceFactory.create_service(
            provider=request.provider.value,
            **service_kwargs,
        )

    def _build_options(self, request: SegmentTranscriptionRequest) -> dict[str, Any] | None:
        options: dict[str, Any] = {}
        normalized_language = normalize_language_code(request.source_language)
        if normalized_language is not None:
            options["language"] = normalized_language
        if isinstance(request.audio_file, BytesIO):
            options["file_extension"] = request.audio_file_extension or "wav"
        if not options:
            return None
        return options


class SrtSegmentTranslationService(SegmentTranslationServiceProtocol):
    """Translate generated SRT content using the existing SRT translator."""

    def __init__(
        self,
        target_language: str,
        skip_translation: bool = False,
        model: str | None = None,
        pattern_name: str | None = None,
        metadata_file: Path | None = None,
    ) -> None:
        self._target_language = target_language
        self._skip_translation = skip_translation
        self._model = model
        self._pattern_name = pattern_name
        self._metadata_file = metadata_file

    def translate_segment(
        self,
        result: SegmentTranscriptionResult,
    ) -> SegmentTranscriptionResult:
        if result.error_message is not None or not result.source_srt.strip():
            return result.model_copy(
                update={
                    "translated_srt": result.source_srt,
                    "translation_skipped": True,
                }
            )
        if self._should_skip_translation(result):
            return result.model_copy(
                update={
                    "translated_srt": result.source_srt,
                    "translation_skipped": True,
                }
            )
        translator = self._build_translator(result.source_language)
        translated_srt = translator.translate_srt(result.source_srt)
        return result.model_copy(
            update={
                "translated_srt": translated_srt,
                "translation_skipped": False,
            }
        )

    def _should_skip_translation(self, result: SegmentTranscriptionResult) -> bool:
        if self._skip_translation:
            return True
        source_language = normalize_language_code(result.source_language)
        if source_language is None:
            return False
        return source_language == normalize_language_code(self._target_language)

    def _build_translator(self, source_language: str | None) -> SrtTranslator:
        return SrtTranslator(
            source_language=normalize_language_code(source_language),
            target_language=self._target_language,
            pattern=self._load_pattern(),
            model=self._model,
            metadata=self._load_metadata(),
        )

    def _load_pattern(self) -> Any:
        return get_pattern(self._pattern_name) if self._pattern_name is not None else None

    def _load_metadata(self) -> Metadata | None:
        if self._metadata_file is None:
            return None
        metadata, _ = Frontmatter.extract_from_file(self._metadata_file)
        return metadata


class SpeakerBlockLanguageSegmentationService(LanguageSegmentationServiceProtocol):
    """Build language-tagged speaker blocks from diarized segments."""

    def __init__(
        self,
        diarization_config: DiarizationConfig | None = None,
        detector: WhisperLanguageDetector | None = None,
    ) -> None:
        self._config = diarization_config or DiarizationConfig()
        self._probe = LanguageProbe(
            self._config,
            detector or WhisperLanguageDetector(),
        )

    def build_blocks(
        self,
        request: MultilingualTranscriptionRequest,
    ) -> list[SpeakerLanguageBlock]:
        segments = self._resolve_segments(request)
        if not segments:
            return []
        grouped_blocks = group_speaker_blocks(segments, self._config)
        if request.source_language is not None:
            return [
                self._build_fixed_language_block(block, request.source_language)
                for block in grouped_blocks
            ]
        base_audio = AudioSegment.from_file(request.audio_file)
        return [self._build_detected_block(block, base_audio) for block in grouped_blocks]

    def _resolve_segments(
        self,
        request: MultilingualTranscriptionRequest,
    ) -> list[DiarizedSegment]:
        if request.diarization_segments is not None:
            return list(request.diarization_segments)
        if not request.use_speaker_blocks:
            return []
        response = diarize(request.audio_file)
        if isinstance(response, DiarizationSucceeded):
            return list(response.result.segments)
        raise RuntimeError("Speaker-block mode requested, but diarization did not succeed.")

    def _build_fixed_language_block(
        self,
        block: SpeakerBlock,
        language_code: str,
    ) -> SpeakerLanguageBlock:
        return self._build_block(
            block,
            language_code,
            detector_source="request",
            confidence=1.0,
            is_reliable=True,
            is_uncertain=False,
        )

    def _build_detected_block(
        self,
        block: SpeakerBlock,
        base_audio: AudioSegment,
    ) -> SpeakerLanguageBlock:
        block_audio = base_audio[int(block.start):int(block.end)]
        language_code = self._probe_language(block, block_audio)
        is_uncertain = language_code is None
        return self._build_block(
            block,
            language_code,
            detector_source="whisper-probe",
            confidence=0.0 if is_uncertain else 0.75,
            is_reliable=not is_uncertain,
            is_uncertain=is_uncertain,
        )

    def _build_block(
        self,
        block: SpeakerBlock,
        language_code: str | None,
        *,
        detector_source: str,
        confidence: float,
        is_reliable: bool,
        is_uncertain: bool,
    ) -> SpeakerLanguageBlock:
        return SpeakerLanguageBlock(
            speaker_label=block.speaker,
            start_ms=int(block.start),
            end_ms=int(block.end),
            detection=LanguageDetectionResult(
                language_code=language_code,
                confidence=confidence,
                detector_source=detector_source,
                is_reliable=is_reliable,
            ),
            is_uncertain=is_uncertain,
        )

    def _probe_language(
        self,
        block: SpeakerBlock,
        block_audio: AudioSegment,
    ) -> str | None:
        probe_segment = AugDiarizedSegment(
            speaker=block.speaker,
            start=TimeMs(block.start),
            end=TimeMs(block.end),
            audio_map_start=None,
            gap_before=None,
            spacing_time=None,
            gap_before_new=False,
            spacing_time_new=TimeMs(0),
            audio=block_audio,
        )
        language = str(self._probe.segment_language(probe_segment))
        if language == "unknown":
            return None
        return normalize_language_code(language)


class PassThroughSubtitleMergeService(SubtitleMergeServiceProtocol):
    """Merge segment SRTs into a single artifact."""

    def __init__(self, artifact_retention: ArtifactRetention) -> None:
        self._artifact_retention = artifact_retention
        self._srt_processor = SRTProcessor()

    def merge(
        self,
        results: list[SegmentTranscriptionResult],
    ) -> MergedSubtitleArtifact:
        if not results:
            raise ValueError("At least one segment result is required for merge.")
        source_srt = self._merge_srt_content(results, translated=False)
        final_english_srt = self._merge_srt_content(results, translated=True)
        first_result = results[0]
        return MergedSubtitleArtifact(
            provider=first_result.provider,
            source_language=self._resolve_source_language(results),
            target_language=first_result.target_language,
            source_srt=source_srt,
            final_english_srt=final_english_srt,
            artifact_retention=self._artifact_retention,
        )

    def _merge_srt_content(
        self,
        results: list[SegmentTranscriptionResult],
        *,
        translated: bool,
    ) -> str:
        timed_texts = [
            self._build_shifted_timed_text(result, translated=translated)
            for result in results
        ]
        combined = self._srt_processor.combine(timed_texts)
        return str(self._srt_processor.generate(combined))

    def _build_shifted_timed_text(
        self,
        result: SegmentTranscriptionResult,
        *,
        translated: bool,
    ) -> TimedText:
        srt_content = self._select_srt(result, translated=translated)
        timed_text = self._parse_srt_content(result, srt_content)
        if not timed_text.segments:
            return timed_text
        return self._srt_processor.shift_timestamps(timed_text, result.segment_start_ms)

    def _parse_srt_content(
        self,
        result: SegmentTranscriptionResult,
        srt_content: str,
    ) -> TimedText:
        try:
            return self._srt_processor.parse(srt_content)
        except ValueError as exc:
            if result.error_message is not None:
                logger.warning(
                    "Skipping malformed failed subtitle block at %sms: %s",
                    result.segment_start_ms,
                    exc,
                    extra={
                        "provider": result.provider.value,
                        "source_language": result.source_language,
                        "target_language": result.target_language,
                        "segment_start_ms": result.segment_start_ms,
                        "translation_skipped": result.translation_skipped,
                        "error_message": result.error_message,
                    },
                )
                return TimedText(segments=[], granularity=Granularity.SEGMENT)
            raise

    def _select_srt(
        self,
        result: SegmentTranscriptionResult,
        *,
        translated: bool,
    ) -> str:
        if translated and result.translated_srt is not None:
            return str(result.translated_srt)
        return str(result.source_srt)

    def _resolve_source_language(
        self,
        results: list[SegmentTranscriptionResult],
    ) -> str | None:
        languages = {
            result.source_language
            for result in results
            if result.source_language is not None
        }
        if len(languages) == 1:
            return cast(str, next(iter(languages)))
        return None


class MultilingualTranscriptionService:
    """Provider-neutral entry point for the current multilingual MVP path."""

    def __init__(
        self,
        transcription_service: SegmentTranscriptionServiceProtocol | None = None,
        segmentation_service: LanguageSegmentationServiceProtocol | None = None,
        translation_service_factory: Callable[
            [MultilingualTranscriptionRequest],
            SegmentTranslationServiceProtocol,
        ]
        | None = None,
        merge_service_factory: Callable[
            [ArtifactRetention],
            SubtitleMergeServiceProtocol,
        ]
        | None = None,
    ) -> None:
        self._transcription_service = (
            transcription_service or ProviderBackedSegmentTranscriptionService()
        )
        self._segmentation_service = (
            segmentation_service or SpeakerBlockLanguageSegmentationService()
        )
        self._translation_service_factory = translation_service_factory
        self._merge_service_factory = merge_service_factory

    def generate_subtitles(
        self,
        request: MultilingualTranscriptionRequest,
    ) -> MergedSubtitleArtifact:
        if self._should_use_speaker_blocks(request):
            return self._generate_block_routed_subtitles(request)
        segment_request = self._build_segment_request(request)
        transcription_result = self._transcription_service.transcribe_segment(segment_request)
        translation_service = self._create_translation_service(request)
        translated_result = translation_service.translate_segment(transcription_result)
        merge_service = self._create_merge_service(request.artifact_retention)
        return merge_service.merge([translated_result])

    def _generate_block_routed_subtitles(
        self,
        request: MultilingualTranscriptionRequest,
    ) -> MergedSubtitleArtifact:
        blocks = self._segmentation_service.build_blocks(request)
        if not blocks:
            return self.generate_subtitles(request.model_copy(update={"use_speaker_blocks": False}))
        translation_service = self._create_translation_service(request)
        base_audio = AudioSegment.from_file(request.audio_file)
        results = [
            self._transcribe_block(request, block, translation_service, base_audio)
            for block in blocks
        ]
        merge_service = self._create_merge_service(request.artifact_retention)
        return merge_service.merge(results)

    def _transcribe_block(
        self,
        request: MultilingualTranscriptionRequest,
        block: SpeakerLanguageBlock,
        translation_service: SegmentTranslationServiceProtocol,
        base_audio: AudioSegment,
    ) -> SegmentTranscriptionResult:
        segment_request = SegmentTranscriptionRequest(
            audio_file=self._slice_audio(request.audio_file, block, base_audio),
            audio_file_extension=resolve_audio_format(request.audio_file),
            provider=request.provider,
            source_language=block.detection.language_code,
            target_language=request.target_language,
            transcription_model=request.transcription_model,
            chars_per_caption=request.chars_per_caption,
        )
        transcribed = self._transcription_service.transcribe_segment(segment_request)
        translated = translation_service.translate_segment(
            transcribed.model_copy(
                update={
                    "segment_start_ms": block.start_ms,
                    "source_language": block.detection.language_code,
                }
            )
        )
        return translated

    def _slice_audio(
        self,
        audio_file: Path,
        block: SpeakerLanguageBlock,
        base_audio: AudioSegment,
    ) -> Any:
        return slice_audio_bytes(base_audio, block.start_ms, block.end_ms, audio_file)

    def _should_use_speaker_blocks(
        self,
        request: MultilingualTranscriptionRequest,
    ) -> bool:
        return request.use_speaker_blocks or request.diarization_segments is not None

    def _build_segment_request(
        self,
        request: MultilingualTranscriptionRequest,
    ) -> SegmentTranscriptionRequest:
        return SegmentTranscriptionRequest(
            audio_file=request.audio_file,
            provider=request.provider,
            source_language=request.source_language,
            target_language=request.target_language,
            transcription_model=request.transcription_model,
            chars_per_caption=request.chars_per_caption,
        )

    def _create_translation_service(
        self,
        request: MultilingualTranscriptionRequest,
    ) -> SegmentTranslationServiceProtocol:
        if self._translation_service_factory is not None:
            return self._translation_service_factory(request)
        return SrtSegmentTranslationService(
            target_language=request.target_language,
            skip_translation=request.skip_translation,
            model=request.translation_model,
            pattern_name=request.translation_pattern,
            metadata_file=request.metadata_file,
        )

    def _create_merge_service(
        self,
        artifact_retention: ArtifactRetention,
    ) -> SubtitleMergeServiceProtocol:
        if self._merge_service_factory is not None:
            return self._merge_service_factory(artifact_retention)
        return PassThroughSubtitleMergeService(artifact_retention)
