from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from tnh_scholar.ai_text_processing import get_pattern
from tnh_scholar.audio_processing.multilingual_models import (
    ArtifactRetention,
    MergedSubtitleArtifact,
    MultilingualTranscriptionRequest,
    SegmentTranscriptionRequest,
    SegmentTranscriptionResult,
)
from tnh_scholar.audio_processing.multilingual_protocols import (
    SegmentTranscriptionServiceProtocol,
    SegmentTranslationServiceProtocol,
    SubtitleMergeServiceProtocol,
)
from tnh_scholar.audio_processing.transcription.transcription_service import (
    TranscriptionServiceFactory,
)
from tnh_scholar.cli_tools.srt_translate.srt_translate import SrtTranslator
from tnh_scholar.metadata.metadata import Frontmatter, Metadata


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
        if request.source_language is None:
            return None
        return {"language": request.source_language}


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
        if self._should_skip_translation(result):
            return result.model_copy(
                update={
                    "translated_srt": result.source_srt,
                    "translation_skipped": True,
                }
            )
        translator = self._build_translator(result.source_language)
        translated_srt = translator.translate_srt(result.source_srt)
        return result.model_copy(update={"translated_srt": translated_srt, "translation_skipped": False})

    def _should_skip_translation(self, result: SegmentTranscriptionResult) -> bool:
        if self._skip_translation:
            return True
        source_language = result.source_language
        if source_language is None:
            return False
        return source_language.lower() == self._target_language.lower()

    def _build_translator(self, source_language: str | None) -> SrtTranslator:
        return SrtTranslator(
            source_language=source_language,
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


class PassThroughSubtitleMergeService(SubtitleMergeServiceProtocol):
    """Current MVP merge service for single-result whole-file processing."""

    def __init__(self, artifact_retention: ArtifactRetention) -> None:
        self._artifact_retention = artifact_retention

    def merge(
        self,
        results: list[SegmentTranscriptionResult],
    ) -> MergedSubtitleArtifact:
        first_result = results[0]
        final_english_srt = self._select_final_srt(first_result)
        return MergedSubtitleArtifact(
            provider=first_result.provider,
            source_language=first_result.source_language,
            target_language=first_result.target_language,
            source_srt=first_result.source_srt,
            final_english_srt=final_english_srt,
            artifact_retention=self._artifact_retention,
        )

    def _select_final_srt(self, result: SegmentTranscriptionResult) -> str:
        if result.translated_srt is not None:
            return result.translated_srt
        return result.source_srt


class MultilingualTranscriptionService:
    """Provider-neutral entry point for the current multilingual MVP path."""

    def __init__(
        self,
        transcription_service: SegmentTranscriptionServiceProtocol | None = None,
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
        self._translation_service_factory = translation_service_factory
        self._merge_service_factory = merge_service_factory

    def generate_subtitles(
        self,
        request: MultilingualTranscriptionRequest,
    ) -> MergedSubtitleArtifact:
        segment_request = self._build_segment_request(request)
        transcription_result = self._transcription_service.transcribe_segment(segment_request)
        translation_service = self._create_translation_service(request)
        translated_result = translation_service.translate_segment(transcription_result)
        merge_service = self._create_merge_service(request.artifact_retention)
        return merge_service.merge([translated_result])

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
