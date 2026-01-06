#!/usr/bin/env python
# audio_transcribe.py
"""
CLI tool for downloading audio (YouTube or local), and transcribing to text.

Usage:
    audio-transcribe [OPTIONS]

    e.g. audio-transcribe \
        --yt_url https://www.youtube.com/watch?v=EXAMPLE \
        --output_dir ./processed \
        --service whisper \
        --model whisper-1
"""

# TODO for production-readiness:
# - Check that all `assert` statements are failsafe only and explicit error handling with informative 
#   exceptions has happened upstream.
# - Add granular error handling and logging for file and network operations (YouTube download, file I/O).
# - Implement retry logic for network-dependent steps (e.g., YouTube downloads).
# - Ensure temporary files are cleaned up if the process fails midway.
# - Add checks and error handling for disk space and file permissions when writing outputs.
# - Log errors and print user-friendly messages to stderr in the CLI; consider returning appropriate exit 
#   codes.
# - Add input sanitization for file paths and URLs, especially before passing to subprocesses.
# - Warn the user if multiple input sources (yt_url, yt_url_csv, file_) are provided simultaneously.
# - Add progress reporting for long-running operations (downloads, transcriptions).
# - Consider a plugin/registry pattern for supporting additional transcription services.
# - Ensure all exceptions are logged with stack traces for debugging.
# - Add unit tests for all major code paths.



import logging
import tempfile
from pathlib import Path

import click
from dotenv import load_dotenv
from pydantic import ValidationError

from tnh_scholar import TNH_LOG_DIR
from tnh_scholar.audio_processing import DiarizationConfig
from tnh_scholar.logging_config import get_child_logger, setup_logging
from tnh_scholar.utils import TimeMs, ensure_directory_exists
from tnh_scholar.video_processing import DLPDownloader, get_youtube_urls_from_csv

from .config import AudioTranscribeConfig, MultipleAudioSourceError, NoAudioSourceError
from .convert_video import convert_video_to_audio
from .transcription_pipeline import TranscriptionPipeline
from .version_check import check_ytd_version

load_dotenv()
setup_logging(log_filepath=TNH_LOG_DIR / "audio_transcribe.log", log_level=logging.INFO)
logger = get_child_logger(__name__)

DEFAULT_OUTPUT_PATH = "./audio_transcriptions/transcript.txt"
DEFAULT_TEMP_DIR = tempfile.gettempdir()
DEFAULT_SERVICE = "whisper"
DEFAULT_MODEL = "whisper-1"
DEFAULT_RESPONSE_FORMAT = "text"
DEFAULT_CHUNK_DURATION = 120
DEFAULT_MIN_CHUNK = 10
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}



class AudioTranscribeApp:
    """
    Main application class for audio transcription CLI.
    Organizes configuration, source resolution, and pipeline execution. All
    runtime options are supplied via a validated `AudioTranscribeConfig`.
    """
    def __init__(self, config: AudioTranscribeConfig) -> None:
        """
        Args:
            config: Validated AudioTranscribeConfig instance.
        """
        self.config = config
        self.yt_url = config.yt_url
        self.yt_url_csv = config.yt_url_csv
        self.file_ = config.file_
        self.output_path = Path(config.output)
        self.keep_artifacts = config.keep_artifacts
        # Use output directory for all artifacts if keep_artifacts is True, else use system temp
        if self.keep_artifacts:
            self.temp_dir = self.output_path.parent
        else:
            self.temp_dir = Path(tempfile.mkdtemp(dir=DEFAULT_TEMP_DIR))
        self.service = config.service
        self.model = config.model
        self.language = config.language
        self.response_format = config.response_format
        self.chunk_duration = TimeMs.from_seconds(config.chunk_duration)
        self.min_chunk = TimeMs.from_seconds(config.min_chunk)
        self.start_time = config.start_time
        self.end_time = config.end_time
        self.prompt = config.prompt
        ensure_directory_exists(self.output_path.parent)
        ensure_directory_exists(self.temp_dir)
        self.audio_file: Path = self._resolve_audio_source()
        self.transcription_options: dict = self._build_transcription_options()
        self.diarization_config = self._build_diarization_config()

    def run(self) -> None:
        """
        Run the transcription pipeline and print results, or just download audio if no_transcribe is set.
        """
        if self.config.no_transcribe:
            self._echo_settings()
            click.echo("\n[Download Only Mode]")
            click.echo(f"Downloaded audio file: {self.audio_file}")
            return
        pipeline = TranscriptionPipeline(
            audio_file=self.audio_file,
            output_dir=self.temp_dir,
            diarization_config=self.diarization_config,
            transcriber=self.service,
            transcription_options=self.transcription_options,
        )
        self._echo_settings()
        transcripts: list[str] = pipeline.run()
        self._write_transcript(transcripts)
        self._print_transcripts(transcripts)
        self._cleanup_temp_dir()

    def _cleanup_temp_dir(self) -> None:
        """
        Remove temp directory if not keeping artifacts.
        """
        if not self.keep_artifacts and self.temp_dir and self.temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {self.temp_dir} ({e})")

    def _write_transcript(self, transcripts: list[str]) -> None:
        """
        Write the full transcript to the output file.

        Args:
            transcripts: List of transcript strings.
        """
        with open(self.output_path, "w", encoding="utf-8") as f:
            for chunk in transcripts:
                f.write(chunk.strip() + "\n\n")

    def _echo_settings(self) -> None:
        """
        Display all runtime settings except transcription_options and diarization_config.
        """
        click.echo("\n[Settings]")
        click.echo(f"  YouTube URL:         {self.yt_url}")
        click.echo(f"  YouTube CSV:         {self.yt_url_csv}")
        click.echo(f"  File:                {self.file_}")
        click.echo(f"  Output Path:         {self.output_path}")
        click.echo(f"  Temp Directory:      {self.temp_dir}")
        click.echo(f"  Service:             {self.service}")
        click.echo(f"  Model:               {self.model}")
        click.echo(f"  Language:            {self.language}")
        click.echo(f"  Response Format:     {self.response_format}")
        click.echo(f"  Chunk Duration:      {self.chunk_duration.to_seconds()} sec")
        click.echo(f"  Min Chunk:           {self.min_chunk.to_seconds()} sec")
        click.echo(f"  Start Time:          {self.start_time}")
        click.echo(f"  End Time:            {self.end_time}")
        click.echo(f"  Audio File:          {self.audio_file}")
        click.echo(f"  Prompt:              '{self.prompt}'")
        
     
    def _resolve_audio_source(self) -> Path:
        """
        Resolve and return the audio file to transcribe.

        Returns:
            Path: Path to the resolved audio file.
        Raises:
            FileNotFoundError: If no audio input is found.
            RuntimeError: If youtube-dl version check fails.
        """
        click.echo("[Resolving/Downloading Audio Source ...]")
        if self.yt_url_csv:
            self._set_yt_url_from_csv()
        if self.yt_url:
            return self._get_audio_from_youtube()
        if self.file_:
            return self._get_audio_from_file()
        logger.error("No audio input found.")
        raise FileNotFoundError("No audio input found.")

    def _set_yt_url_from_csv(self) -> None:
        """
        Set the YouTube URL from the first entry in the CSV file.
        """
        assert self.yt_url_csv
        urls: list[str] = get_youtube_urls_from_csv(Path(self.yt_url_csv))
        self.yt_url = urls[0] if urls else None

    def _get_audio_from_youtube(self) -> Path:
        """
        Download and return the audio file from YouTube.

        Raises:
            click.ClickException: If yt-dlp is not installed or unavailable.
        """
        if not check_ytd_version():
            logger.error("yt-dlp is not available. Cannot download from YouTube.")
            raise click.ClickException(
                "yt-dlp is missing or outdated. Update with: poetry update yt-dlp"
            )

        dl = DLPDownloader()

        assert self.yt_url
        url_metadata = dl.get_metadata(self.yt_url)
        default_name = dl.get_default_filename_stem(url_metadata)
        download_path: Path = self.temp_dir / default_name
        download_file: Path = download_path.with_suffix(".mp3")
        if not download_file.exists():
            return self._extract_yt_audio(dl, download_path)
        click.echo(f"Re-using existing downloaded audio file: {download_file}")
        return download_file

    def _extract_yt_audio(self, dl, download_path):
        video_data = dl.get_audio(
                self.yt_url,
                start=self.start_time,
                output_path=download_path,
            )
        if not video_data or not video_data.filepath:
            raise FileNotFoundError("Failed to download or locate audio file.")
        return Path(video_data.filepath)
    
    def _get_audio_from_file(self) -> Path:
        """
        Return the audio file path, converting video if needed.
        """
        assert self.file_
        audio_file: Path = Path(self.file_)
        if audio_file.suffix.lower() in VIDEO_EXTENSIONS:
            logger.info(f"Detected video file: {audio_file}. Auto-converting to mp3 ...")
            return convert_video_to_audio(audio_file, self.temp_dir)
        return audio_file

    def _build_transcription_options(self) -> dict:
        """
        Build transcription options dictionary for the pipeline.

        Returns:
            dict: Transcription options for the pipeline.
        """
        options: dict = {
            "model": self.model,
            "language": self.language,
            "response_format": self.response_format,
            "prompt": self.prompt,
        }
        if self.service == "whisper" and self.response_format != "text":
            options["timestamp_granularities"] = ["word"]
        return options

    def _build_diarization_config(self) -> DiarizationConfig:
        """
        Build DiarizationConfig for chunking and language settings.

        Returns:
            DiarizationConfig: Configuration for diarization and chunking.
        """
        from tnh_scholar.audio_processing.diarization.config import (
            ChunkConfig,
            DiarizationConfig,
            LanguageConfig,
            SpeakerConfig,
        )
        return DiarizationConfig(
            chunk=ChunkConfig(
                target_duration=self.chunk_duration,
                min_duration=self.min_chunk,
            ),
            speaker=SpeakerConfig(single_speaker=True),
            language=LanguageConfig(default_language=self.language),
        )

    def _print_transcripts(self, transcripts: list[str]) -> None:
        """
        Print each transcript chunk to stdout.

        Args:
            transcripts: List of transcript strings.
        """
        for i, text in enumerate(transcripts, 1):
            print(f"\n--- Transcript chunk {i} ---\n{text}\n")

@click.command()
@click.option(
    "-y", "--yt_url", type=str,
    help="Single YouTube URL."
)
@click.option(
    "-v", "--yt_url_csv", type=click.Path(exists=True),
    help="CSV file with multiple YouTube URLs in first column."
)
@click.option(
    "-f", "--file", "file_", type=click.Path(exists=True),
    help="Path to a local audio file."
)
@click.option(
    "-o", "--output", type=click.Path(), default=DEFAULT_OUTPUT_PATH,
    help="Path to the output transcript file."
)
    # Removed temp_dir option, now handled by keep_artifacts only
@click.option(
    "-s", "--service", type=click.Choice(["whisper", "assemblyai"]), default=DEFAULT_SERVICE,
    help="Transcription service to use."
)
@click.option(
    "-m", "--model", type=str, default=DEFAULT_MODEL,
    help="Model to use for transcription (for OpenAI only)."
)
@click.option(
    "-l", "--language", type=str, default="en",
    help="Language code (e.g., 'en', 'vi')."
)
@click.option(
    "-r", "--response_format", type=str, default=DEFAULT_RESPONSE_FORMAT,
    help="Response format for Whisper (default: text)."
)
@click.option(
    "--chunk_duration", type=int, default=DEFAULT_CHUNK_DURATION,
    help="Chunk duration in seconds (default: 7 minutes)."
)
@click.option(
    "--min_chunk", type=int, default=DEFAULT_MIN_CHUNK,
    help="Minimum chunk duration in seconds."
)
@click.option(
    "--start_time", type=str,
    help="Start time offset for the input media (HH:MM:SS)."
)
@click.option(
    "--end_time", type=str,
    help="End time offset for the input media (HH:MM:SS)."
)
@click.option(
    "--prompt", type=str, default="",
    help="Prompt or keywords to guide the transcription."
)
@click.option(
    "-n", "--no_transcribe", is_flag=True, default=False,
    help="Download YouTube audio to mp3 only, do not transcribe. Requires --yt_url or --yt_url_csv."
)
@click.option(
    "-k", "--keep_artifacts", is_flag=True, default=False,
    help="Keep all intermediate artifacts in the output directory instead of using a system temp directory."
)
def audio_transcribe(**kwargs):
    """
    CLI entry point for audio transcription.
    """
    try:
        config = AudioTranscribeConfig(**kwargs)
    except NoAudioSourceError as e:
        print(f"\n[INPUT ERROR] {e}", flush=True)
        raise SystemExit(1) from e
    except MultipleAudioSourceError as e:
        print(f"\n[INPUT ERROR] {e}", flush=True)
        raise SystemExit(1) from e
    except ValidationError as e:
        print("\n[CONFIG VALIDATION ERROR]\n", e, flush=True)
        raise SystemExit(1) from e
    app = AudioTranscribeApp(config)
    app.run()

def main():
    audio_transcribe()

if __name__ == "__main__":
    main()
    
