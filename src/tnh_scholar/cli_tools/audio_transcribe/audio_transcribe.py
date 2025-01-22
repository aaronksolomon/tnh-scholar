#!/usr/bin/env python
# audio_transcribe.py
"""
This module provides a command line interface for handling audio transcription tasks.
It can optionally:
 - Download audio from a YouTube URL.
 - Split existing audio into chunks.
 - Transcribe audio chunks to text.

Usage Example:
    # Download, split, and transcribe from a single YouTube URL
    audio-transcribe \
        --yt_download \
        --yt_process_url "https://www.youtube.com/watch?v=EXAMPLE" \
        --split \
        --transcribe \
        --output_dir ./processed \
        --prompt "Dharma, Deer Park..."

In a production environment, this CLI tool would be installed as part of the `tnh-scholar` package.
"""
import os

from dotenv import load_dotenv

os.environ["KMP_WARNINGS"] = (
    "0"  # Turn off known info message about nested levels for OMP that arises from torch.
         # Must turn this off before imports that use OMP in order to have effect.
)

import logging
import sys
from pathlib import Path

import click

from tnh_scholar import TNH_CLI_TOOLS_DIR, TNH_PROJECT_ROOT_DIR, TNH_LOG_DIR
from tnh_scholar.logging_config import get_child_logger, setup_logging

# --- Setup logging early ---
setup_logging(log_filepath=TNH_LOG_DIR / "audio_transcribe.log", log_level=logging.INFO)
logger = get_child_logger("audio_transcribe")

from tnh_scholar.audio_processing import (
    process_audio_chunks,
    process_audio_file,
    split_audio,
)
from tnh_scholar.utils import ensure_directory_exists, get_user_confirmation
from tnh_scholar.video_processing import (
    download_audio_yt,
    get_video_download_path_yt,
    get_youtube_urls_from_csv,
)

from .environment import check_env
from .validate import validate_inputs
from .version_check import check_ytd_version

# Settings
DEFAULT_CHUNK_DURATION_MIN = 7
DEFAULT_CHUNK_DURATION_SEC = DEFAULT_CHUNK_DURATION_MIN * 60
REQUIREMENTS_PATH = (
    TNH_CLI_TOOLS_DIR / "audio_transcribe" / "environment" / "requirements.txt"
)
RE_DOWNLOAD_CONFIRMATION_STR = "An mp3 file corresponding to {url} already exists in the output path:\n\t{output_dir}.\nSKIP download ([Y]/n)?"
DEFAULT_OUTPUT_DIR = "./audio_transcriptions"
DEFAULT_PROMPT = (
    "Dharma, Deer Park, Thay, Thich Nhat Hanh, Bodhicitta, Bodhisattva, Mahayana"
)

load_dotenv()
if not check_env():
    sys.exit(1)  # missing environment setting cause immediate failure (prototype stage)
    
        
@click.command()
@click.option(
    "-s", "--split", is_flag=True, help="Split downloaded/local audio into chunks."
)
@click.option("-t", "--transcribe", is_flag=True, help="Transcribe the audio chunks.")
@click.option("-y", "--yt_url", type=str, help="Single YouTube URL to process.")
@click.option(
    "-v",
    "--yt_url_csv",
    type=click.Path(exists=True),
    help="A CSV File containing multiple YouTube URLs. The first column of the file must be the URL and Second column a start time (if specified).",
)
@click.option(
    "-f", "--file", type=click.Path(exists=True), help="Path to a local audio file."
)
@click.option(
    "-c",
    "--chunk_dir",
    type=click.Path(),
    help="Directory for pre-existing chunks or where to store new chunks.",
)
@click.option(
    "-o",
    "--output_dir",
    type=click.Path(),
    default=DEFAULT_OUTPUT_DIR,
    help=f"Base output directory. DEFAULT: '{DEFAULT_OUTPUT_DIR}' ",
)
@click.option(
    "-d",
    "--chunk_duration",
    type=int,
    default=DEFAULT_CHUNK_DURATION_SEC,
    help=f"Max chunk duration in seconds (default: {DEFAULT_CHUNK_DURATION_MIN} minutes).",
)
@click.option(
    "-x",
    "--no_chunks",
    is_flag=True,
    help="Run transcription directly on the audio files source(s). WARNING: for files > 10 minutes in Length, the Open AI transcription API may fail.",
)
@click.option(
    "-b",
    "--start",
    "start_time",
    type=str,
    help="Start time (beginning) offset for the input media (HH:MM:SS).",
)
@click.option(
    "-a",
    "--translate",
    is_flag=True,
    help="Include translation in the transcription if set.",
)
@click.option(
    "-p",
    "--prompt",
    type=str,
    default=DEFAULT_PROMPT,
    help="Prompt or keywords to guide the transcription.",
)
@click.option(
    "-i",
    "--silence_boundaries",
    is_flag=True,
    help="Use silence detection to split audio file(s)",
)
@click.option(
    "-w",
    "--whisper_boundaries",
    is_flag=True,
    help="(DEFAULT) Use a whisper based model to audio at sentence boundaries.",
)
@click.option(
    "-l",
    "--language",
    type=str,
    help="The two letter language code. e.g. 'vi' for Vietnamese. Used for splitting only. DEFAULT: English ('en').",
)
def audio_transcribe(
    split: bool,
    transcribe: bool,
    yt_url: str | None,
    yt_url_csv: str | None,
    file: str | None,
    chunk_dir: str | None,
    output_dir: str,
    chunk_duration: int,
    no_chunks: bool,
    start_time: str | None,
    translate: bool,
    prompt: str,
    silence_boundaries: bool,
    whisper_boundaries: bool,
    language: str | None,
) -> None:
    """
    Entry point for the audio transcription pipeline.
    Depending on the provided flags and arguments, it can download audio from YouTube,
    split the audio into chunks, and/or transcribe the chunks.

    Steps are:

    1. Download (if requested)

    2. Split (if requested)

    3. Transcribe (if requested)
    """
        
    check_ytd_version()  # Do a version check on startup. Version issues can cause yt-dlp to fail.

    logger.info("Starting audio transcription pipeline...")

    # initial parameter processing
    if not split and not transcribe:  # if neither set, we assume both.
        split = True
        transcribe = True

    is_download = bool(yt_url or yt_url_csv)
    if not language:
        language = "en"

    # default logic for splitting boundaries
    if not whisper_boundaries and not silence_boundaries:
        whisper_boundaries = True

    try:
        # Validate input arguments
        audio_file: Path | None = Path(file) if file else None
        chunk_directory: Path | None = Path(chunk_dir) if chunk_dir else None
        out_dir = Path(output_dir)

        validate_inputs(
            is_download=is_download,
            yt_url=yt_url,
            yt_url_list=Path(yt_url_csv) if yt_url_csv else None,
            audio_file=audio_file,
            split=split,
            transcribe=transcribe,
            chunk_dir=chunk_directory,
            no_chunks=no_chunks,
            silence_boundaries=silence_boundaries,
            whisper_boundaries=whisper_boundaries,
        )

        # Determine the list of URLs if we are downloading from YouTube
        urls: list[str] = []
        if yt_url_csv:
            if is_download:
                urls = get_youtube_urls_from_csv(Path(yt_url_csv))
        elif yt_url:
            if is_download:
                urls = [yt_url]

        # If we are downloading from YouTube, handle that
        downloaded_files: list[Path] = []
        if is_download:
            for url in urls:
                download_path = get_video_download_path_yt(out_dir, url)
                if download_path.exists():
                    if get_user_confirmation(
                        RE_DOWNLOAD_CONFIRMATION_STR.format(url=url, output_dir=out_dir)
                    ):
                        logger.info(f"Skipping download for {url}.")
                    else:
                        logger.info(f"Re-downloading {url}:")
                        download_path = download_audio_yt(
                            url, out_dir, start_time=start_time
                        )
                        logger.info(f"Successfully downloaded {url} to {download_path}")
                else:
                    logger.info(f"Downloading from YouTube: {url}")
                    ensure_directory_exists(out_dir)
                    download_path = download_audio_yt(
                        url, out_dir, start_time=start_time
                    )
                    logger.info(f"Successfully downloaded {url} to {download_path}")

                downloaded_files.append(download_path)

        # If we have a local audio file specified (no yt_download), treat that as our input
        if audio_file and not is_download:
            downloaded_files = [audio_file]

        # If splitting is requested, split either the downloaded files or the provided audio
        if split:
            for audio_file in downloaded_files:
                audio_name = audio_file.stem
                audio_output_dir = out_dir / audio_name
                ensure_directory_exists(audio_output_dir)
                chunk_output_dir = chunk_directory or audio_output_dir / "chunks"
                ensure_directory_exists(chunk_output_dir)

                logger.info(f"Splitting audio into chunks for {audio_file}")

                if (
                    not whisper_boundaries
                    and not silence_boundaries
                    or not silence_boundaries
                ):
                    detection_method = "whisper"
                else:
                    detection_method = "silence"
                split_audio(
                    audio_file=audio_file,
                    method=detection_method,
                    output_dir=chunk_output_dir,
                    max_duration=chunk_duration,
                    language=language,
                )

        # If transcribe is requested, we must have a chunk directory to transcribe from
        if transcribe:
            for audio_file in downloaded_files:
                audio_name = audio_file.stem
                audio_output_dir = out_dir / audio_name
                transcript_file = audio_output_dir / f"{audio_name}.txt"
                if no_chunks:
                    jsonl_file = audio_output_dir / f"{audio_name}.jsonl"
                    logger.info(
                        f"Transcribing {audio_name} directly without chunking..."
                    )
                    process_audio_file(
                        audio_file=audio_file,
                        output_file=transcript_file,
                        jsonl_file=jsonl_file,
                        prompt=prompt,
                        translate=translate,
                    )

                else:
                    chunk_output_dir = chunk_directory or audio_output_dir / "chunks"
                    jsonl_file = audio_output_dir / f"{audio_name}.jsonl"
                    logger.info(f"Transcribing chunks from {chunk_output_dir}")
                    process_audio_chunks(
                        directory=chunk_output_dir,
                        output_file=transcript_file,
                        jsonl_file=jsonl_file,
                        prompt=prompt,
                        translate=translate,
                    )

        logger.info("Audio transcription pipeline completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.debug("traceback info", exc_info=True)
        sys.exit(1)


def main():
    """Entry point for AUDIO-TRANSCRIBE CLI tool."""
    audio_transcribe()


if __name__ == "__main__":
    main()
