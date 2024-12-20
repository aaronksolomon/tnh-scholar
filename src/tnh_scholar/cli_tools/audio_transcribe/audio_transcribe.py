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

import sys
from pathlib import Path
import click
import logging
import tnh_scholar.logging_config as logging_config
from tnh_scholar.logging_config import setup_logging, get_child_logger
from tnh_scholar import PROJECT_ROOT_DIR, LOG_DIR, CLI_TOOLS_DIR

# --- Setup logging early ---
setup_logging(log_filepath=LOG_DIR / "audio_transcribe.log", log_level=logging.DEBUG)
logger = get_child_logger("audio_transcribe")

from tnh_scholar.video_processing import (
    get_youtube_urls_from_csv, 
    download_audio_yt,
)
from tnh_scholar.audio_processing import (
    split_audio, 
    process_audio_chunks,
    process_audio_file
)
from tnh_scholar.utils import (
    ensure_directory_exists
)
from .environment import check_env
from .validate import validate_inputs

# Settings
DEFAULT_CHUNK_DURATION = 7 * 60 # 7 minutes
REQUIREMENTS_PATH = CLI_TOOLS_DIR / "audio_transcribe" / "environment" / "requirements.txt"

check_env(PROJECT_ROOT_DIR, REQUIREMENTS_PATH)

@click.command()
@click.option('--full', is_flag=True, help='Perform full pipeline: split and transcribe.')
@click.option('--split', is_flag=True, help='Split downloaded/local audio into chunks.')
@click.option('--transcribe', is_flag=True, help='Transcribe the audio chunks.')
@click.option('--yt_url', type=str, help='Single YouTube URL to process.')
@click.option('--yt_url_cvs', type=click.Path(exists=True), help='A CSV File containing multiple YouTube URLs. The first column of the file must be the URL and Second column a start time (if specified).')
@click.option('--audio', type=click.Path(exists=True), help='Path to a local audio file.')
@click.option('--chunk_dir', type=click.Path(), help='Directory for pre-existing chunks or where to store new chunks.')
@click.option('--output_dir', type=click.Path(), default='./video_transcriptions', help='Base output directory.')
@click.option('--chunk_duration', type=int, default=DEFAULT_CHUNK_DURATION, help='Max chunk duration in seconds (default: 10 minutes).')
@click.option('--no_chunks', is_flag=True, help='Run transcription directly on the audio files source(s). WARNING: for files > 10 minutes in Length, the Open AI transcription API may fail.')
@click.option('--start_time', type=str, help='Start time offset for the input media (HH:MM:SS).')
@click.option('--translate', is_flag=True, help='Include translation in the transcription if set.')
@click.option('--prompt', type=str, default="Dharma, Deer Park, Thay, Thich Nhat Hanh, Bodhicitta, Bodhisattva, Mahayana",
              help='Prompt or keywords to guide the transcription.')
@click.option('--silence_boundaries', is_flag=False, help='Use silence detection to split audio file(s)')
@click.option('--whisper_boundaries', is_flag=True, help='Use a whisper based model to audio at sentence boundaries.')

def main(
    full: bool,
    split: bool,
    transcribe: bool,
    yt_url: str | None,
    yt_url_csv: str | None,
    audio: str | None,
    chunk_dir: str | None,
    output_dir: str,
    chunk_duration: int,
    no_chunks: bool,
    start_time: str | None,
    translate: bool,
    prompt: str,
    silence_boundaries: bool,
    whisper_boundaries: bool
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
    logger.info("Starting audio transcription pipeline...")

    if full:
        split = True
        transcribe = True

    if yt_url or yt_url_csv:
        is_download = True
    else:
        is_download = False

    try:
        # Validate input arguments
        audio_file: Path | None = Path(audio) if audio else None
        chunk_directory: Path | None = Path(chunk_dir) if chunk_dir else None
        out_dir = Path(output_dir)
        
        validate_inputs(
            is_download=is_download,
            yt_url=yt_url,
            yt_url_list=Path(yt_url_csv) if yt_url_csv else None,
            audio=audio_file,
            split=split,
            transcribe=transcribe,
            chunk_dir=chunk_directory,
            no_chunks=no_chunks,
            silence_boundaries=silence_boundaries,
            whisper_boundaries=whisper_boundaries
        )

        # Determine the list of URLs if we are downloading from YouTube
        urls: list[str] = []
        if is_download and yt_url_csv:
            urls = get_youtube_urls_from_csv(Path(yt_url_csv))
        elif is_download and yt_url:
            urls = [yt_url]

        # If we are downloading from YouTube, handle that
        downloaded_files: list[Path] = []
        if is_download:
            for url in urls:
                logger.info(f"Downloading from YouTube: {url}")
                ensure_directory_exists(out_dir)
                downloaded_file = download_audio_yt(url, out_dir, start_time=start_time)
                downloaded_files.append(downloaded_file)

        # If we have a local audio file specified (no yt_download), treat that as our input
        if audio_file and not is_download:
            downloaded_files = [audio_file]

        # If splitting is requested, split either the downloaded files or the provided audio
        if split:
            for afile in downloaded_files:
                audio_name = afile.stem
                audio_output_dir = out_dir / audio_name
                ensure_directory_exists(audio_output_dir)
                chunk_output_dir = chunk_directory if chunk_directory else (audio_output_dir / "chunks")
                ensure_directory_exists(chunk_output_dir)
                
                logger.info(f"Splitting audio into chunks for {afile}")

                detection_method = "whisper" if whisper_boundaries else "silence"
                split_audio(
                    audio_file=afile,
                    method=detection_method,
                    output_dir=chunk_output_dir,
                    max_duration=chunk_duration
                )

        # If transcribe is requested, we must have a chunk directory to transcribe from
        if transcribe:
            if no_chunks:
                 for afile in downloaded_files:
                    audio_name = afile.stem
                    audio_output_dir = out_dir / audio_name
                    transcript_file = audio_output_dir / f"{audio_name}.txt"
                    jsonl_file = audio_output_dir / f"{audio_name}.jsonl"
                    logger.info(f"Transcribing {audio_name} directly without chunking...")
                    process_audio_file(
                        audio_file=afile,
                        output_file=transcript_file, 
                        jsonl_file=jsonl_file, 
                        prompt=prompt, 
                        translate=translate)

            else:
                for afile in downloaded_files:
                    audio_name = afile.stem
                    audio_output_dir = out_dir / audio_name
                    transcript_file = audio_output_dir / f"{audio_name}.txt"
                    chunk_output_dir = chunk_directory if chunk_directory else (audio_output_dir / "chunks")
                    jsonl_file = audio_output_dir / f"{audio_name}.jsonl"
                    logger.info(f"Transcribing chunks from {chunk_output_dir}")
                    process_audio_chunks(
                        directory=chunk_output_dir,
                        output_file=transcript_file,
                        jsonl_file=jsonl_file,
                        prompt=prompt,
                        translate=translate
                    )

        logger.info("Audio transcription pipeline completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.deubug(f"traceback info", exc_info=True)
        sys.exit(1)