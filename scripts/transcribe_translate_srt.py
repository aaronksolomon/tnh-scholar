from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.audio_processing.multilingual_models import (
    MultilingualTranscriptionRequest,
    TranscriptionProvider,
)
from tnh_scholar.audio_processing.multilingual_service import (
    MultilingualTranscriptionService,
)
from tnh_scholar.logging_config import setup_logging


@dataclass(frozen=True)
class SubtitleWorkflowDefaults:
    provider: TranscriptionProvider = TranscriptionProvider.WHISPER
    target_language: str = "en"
    chars_per_caption: int = 42


@dataclass(frozen=True)
class SubtitleWorkflowConfig:
    audio_file: Path
    source_srt_output: Path
    translated_srt_output: Path | None
    provider: TranscriptionProvider
    source_language: str | None
    target_language: str
    transcription_model: str | None
    translation_model: str | None
    translation_pattern: str | None
    metadata_file: Path | None
    chars_per_caption: int
    debug: bool


class SubtitleWorkflow:
    """Prototype workflow for direct SRT transcription and optional translation."""

    def __init__(self, config: SubtitleWorkflowConfig) -> None:
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._service = MultilingualTranscriptionService()

    def run(self) -> None:
        self._validate_input()
        artifact = self._service.generate_subtitles(self._build_request())
        self._write_text(self._config.source_srt_output, artifact.source_srt)
        self._write_translated_output(artifact.final_english_srt)

    def _validate_input(self) -> None:
        if not self._config.audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {self._config.audio_file}")
        if not self._config.audio_file.is_file():
            raise FileNotFoundError(f"Audio path is not a file: {self._config.audio_file}")

    def _build_request(self) -> MultilingualTranscriptionRequest:
        return MultilingualTranscriptionRequest(
            audio_file=self._config.audio_file,
            provider=self._config.provider,
            source_language=self._config.source_language,
            target_language=self._config.target_language,
            transcription_model=self._config.transcription_model,
            translation_model=self._config.translation_model,
            translation_pattern=self._config.translation_pattern,
            metadata_file=self._config.metadata_file,
            chars_per_caption=self._config.chars_per_caption,
            skip_translation=self._config.translated_srt_output is None,
        )

    def _write_text(self, output_path: Path, content: str) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        self._logger.info("Wrote subtitle output to %s", output_path)

    def _write_translated_output(self, translated_srt: str) -> None:
        if self._config.translated_srt_output is None:
            return
        self._write_text(self._config.translated_srt_output, translated_srt)


class SubtitleWorkflowCli:
    """Argument parsing and config construction for the workflow prototype."""

    def __init__(self) -> None:
        self._defaults = SubtitleWorkflowDefaults()

    def run(self) -> None:
        config = self._build_config(self._parse_args())
        self._configure_logging(config.debug)
        workflow = SubtitleWorkflow(config)
        workflow.run()

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Generate a source SRT and optional translated SRT from a local audio file.",
        )
        parser.add_argument("audio_file", type=Path, help="Path to a local audio file.")
        parser.add_argument(
            "--provider",
            choices=[provider.value for provider in TranscriptionProvider],
            default=self._defaults.provider.value,
            help="Transcription backend.",
        )
        parser.add_argument(
            "--source-language",
            help="Source language code. Omit for multilingual or auto-detect behavior.",
        )
        parser.add_argument(
            "--target-language",
            default=self._defaults.target_language,
            help="Target language code for translated SRT output.",
        )
        parser.add_argument(
            "--transcription-model",
            help="Optional transcription model override (for example: whisper-1).",
        )
        parser.add_argument(
            "--translation-model",
            help="Optional translation model override.",
        )
        parser.add_argument(
            "--translation-pattern",
            help="Optional TNH Scholar translation pattern name.",
        )
        parser.add_argument(
            "--metadata-file",
            type=Path,
            help="Optional file with YAML front matter for translation context.",
        )
        parser.add_argument(
            "--chars-per-caption",
            type=int,
            default=self._defaults.chars_per_caption,
            help="Caption width hint passed to provider-native SRT generation.",
        )
        parser.add_argument(
            "--source-srt-output",
            type=Path,
            help="Output path for the source-language SRT.",
        )
        parser.add_argument(
            "--translated-srt-output",
            type=Path,
            help="Output path for the translated SRT.",
        )
        parser.add_argument(
            "--skip-translation",
            action="store_true",
            help="Only generate the source-language SRT.",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging.",
        )
        return parser.parse_args()

    def _build_config(self, args: argparse.Namespace) -> SubtitleWorkflowConfig:
        audio_file = args.audio_file.resolve()
        source_srt_output = args.source_srt_output or audio_file.with_suffix(".srt")
        translated_srt_output = self._build_translated_output(args, source_srt_output)
        return SubtitleWorkflowConfig(
            audio_file=audio_file,
            source_srt_output=source_srt_output,
            translated_srt_output=translated_srt_output,
            provider=TranscriptionProvider(args.provider),
            source_language=args.source_language,
            target_language=args.target_language,
            transcription_model=args.transcription_model,
            translation_model=args.translation_model,
            translation_pattern=args.translation_pattern,
            metadata_file=args.metadata_file.resolve() if args.metadata_file else None,
            chars_per_caption=args.chars_per_caption,
            debug=args.debug,
        )

    def _build_translated_output(
        self,
        args: argparse.Namespace,
        source_srt_output: Path,
    ) -> Path | None:
        if args.skip_translation:
            return None
        if args.translated_srt_output is not None:
            return args.translated_srt_output
        return source_srt_output.with_stem(f"{source_srt_output.stem}_{args.target_language}")

    def _configure_logging(self, debug: bool) -> None:
        log_level = logging.DEBUG if debug else logging.INFO
        setup_logging(log_level=log_level)


def main() -> None:
    cli = SubtitleWorkflowCli()
    cli.run()


if __name__ == "__main__":
    main()
