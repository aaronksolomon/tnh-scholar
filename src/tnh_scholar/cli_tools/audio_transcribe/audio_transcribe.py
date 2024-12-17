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
import src.logging_config as logging_config
from src.logging_config import setup_logging, get_child_logger
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
from environment import (
    check_env
)

# Settings
DEFAULT_CHUNK_DURATION = 7 * 60 # 7 minutes
PROJECT_PATH = Path("../../../tnh-scholar")
REQUIREMENTS_PATH = Path("./environment/requirements.txt")

def validate_inputs(
    is_download: bool,
    yt_url: str | None,
    yt_url_list: Path | None,
    audio: Path | None,
    split: bool,
    transcribe: bool,
    chunk_dir: Path | None,
    no_chunks: bool,
    silence_boundaries: bool,
    whisper_boundaries: bool
) -> None:
    """
    Validate the CLI inputs to ensure logical consistency given all the flags.

    Conditions & Requirements:
    1. At least one action (yt_download, split, transcribe) should be requested. 
       Otherwise, nothing is done, so raise an error.

    2. If yt_download is True:
       - Must specify either yt_process_url OR yt_process_url_list (not both, not none).

    3. If yt_download is False:
       - If split is requested, we need a local audio file (since no download will occur).
       - If transcribe is requested without split and without yt_download:
         - If no_chunks = False, we must have chunk_dir to read existing chunks.
         - If no_chunks = True, we must have a local audio file (direct transcription) or previously downloaded file
           (but since yt_download=False, previously downloaded file scenario doesn't apply here,
           so effectively we need local audio in that scenario).

    4. no_chunks flag:
       - If no_chunks = True, we are doing direct transcription on entire audio without chunking.
         - Cannot use split if no_chunks = True. (Mutually exclusive)
         - chunk_dir is irrelevant if no_chunks = True; since we don't split into chunks, 
           requiring a chunk_dir doesn't make sense. If provided, it's not useful, but let's allow it silently 
           or raise an error for clarity. It's safer to raise an error to prevent user confusion.
       
    5. Boundaries flags (silence_boundaries, whisper_boundaries):
       - These flags control how splitting is done.
       - If split = False, these are irrelevant. Not necessarily an error, but could be a no-op. 
         For robustness, raise an error if user specifies these without split, to avoid confusion.
       - If split = True and no_chunks = True, that’s contradictory already, so no need for boundary logic there.
       - If split = True, exactly one method should be chosen: 
         If both silence_boundaries and whisper_boundaries are True simultaneously or both are False simultaneously, 
         we need a clear default or raise an error. By the code snippet logic, whisper_boundaries is default True 
         if not stated otherwise. To keep it robust:
           - If both are True, raise error. 
           - If both are False, that means user explicitly turned them off or never turned on whisper. 
             The code snippet sets whisper_boundaries True by default. If user sets it False somehow, 
             we can then default to silence. Just ensure at run-time we have a deterministic method:
             If both are False, we can default to whisper or silence. Let's default to whisper if no flags given.
             However, given the code snippet, whisper_boundaries has a default of True. 
             If the user sets whisper_boundaries to False and also does not set silence_boundaries, 
             then no method is chosen. Let's then raise an error if both ended up False to avoid ambiguity.

    Raises:
        ValueError: If the input arguments are not logically consistent.
    """

    # 1. Check that we have at least one action
    if not (is_download or split or transcribe):
        raise ValueError("No actions requested. At least one of --yt_download, --split, --transcribe, or --full must be set.")

    # 2. Validate YouTube download logic
    if is_download:
        if yt_url and yt_url_list:
            raise ValueError("Both --yt_process_url and --yt_process_url_list provided. Only one allowed.")
        if not yt_url and not yt_url_list:
            raise ValueError("When --yt_download is specified, you must provide --yt_process_url or --yt_process_url_list.")

    # 3. Logic when no YouTube download:
    if not is_download:
        # If splitting but no download, need an audio file
        if split and audio is None:
            raise ValueError("Splitting requested but no audio file provided and no YouTube download source available.")
        
        # If transcribing but not splitting or downloading:
        # Check no_chunks scenario:
        if transcribe and not split:
            if no_chunks:
                # Direct transcription, need an audio file
                if audio is None:
                    raise ValueError("Transcription requested with no_chunks=True but no audio file provided.")
            else:
                # no_chunks=False, we need chunks from chunk_dir
                if chunk_dir is None:
                    raise ValueError("Transcription requested without splitting or downloading and no_chunks=False. Must provide --chunk_dir with pre-split chunks.")

    # 4. no_chunks flag validation:
    # no_chunks and split are mutually exclusive
    if no_chunks and split:
        raise ValueError("Cannot use --no_chunks and --split together. Choose one option.")
    # If no_chunks and chunk_dir provided, it doesn't make sense since we won't use chunks at all.
    if no_chunks and chunk_dir is not None:
        raise ValueError("Cannot specify --chunk_dir when --no_chunks is set.")

    # 5. Boundaries flags:
    # If splitting is not requested but boundaries flags are set, it's meaningless. 
    # The code snippet defaults whisper_boundaries to True, so if user tries to turn it off and sets silence?
    # We'll require that boundaries only matter if split is True.
    if not split and (silence_boundaries or whisper_boundaries):
        raise ValueError("Boundary detection flags given but splitting is not requested. Remove these flags or enable --split.")
        
    # If split is True, we must have a consistent boundary method:
    if split:
        # If both whisper and silence are somehow True:
        if silence_boundaries and whisper_boundaries:
            raise ValueError("Cannot use both --silence_boundaries and --whisper_boundaries simultaneously.")
        
        # If both are False:
        # Given the original snippet, whisper_boundaries is True by default. 
        # For the sake of robustness, let's say if user sets both off, we can't proceed:
        if not silence_boundaries and not whisper_boundaries:
            raise ValueError("No boundary method selected for splitting. Enable either whisper or silence boundaries.")

    # If we got here, inputs are logically consistent.

# --- Setup logging early ---
setup_logging(log_filename="audio_transcribe.log")
logger = get_child_logger("audio_transcribe")

check_env(PROJECT_PATH, REQUIREMENTS_PATH)

@click.command()
@click.option('--full', is_flag=True, help='Perform full pipeline: split and transcribe.')
@click.option('--split', is_flag=True, help='Split downloaded/local audio into chunks.')
@click.option('--transcribe', is_flag=True, help='Transcribe the audio chunks.')
@click.option('--yt_url', type=str, help='Single YouTube URL to process.')
@click.option('--yt_url_list', type=click.Path(exists=True), help='File containing multiple YouTube URLs.')
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
    yt_url_list: str | None,
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

    Args:
        yt_download (bool): If True, download audio from YouTube URLs.
        split (bool): If True, split audio into chunks.
        transcribe (bool): If True, transcribe the audio chunks.
        yt_process_url (str|None): A single YouTube URL to process.
        yt_process_url_list (str|None): Path to a file containing multiple YouTube URLs.
        audio (str|None): Path to a local audio file.
        chunk_dir (str|None): Directory to store or read pre-existing chunks.
        output_dir (str): Base output directory.
        chunk_duration (int): Max duration of each chunk in seconds.
        no_chunks (bool): If true, work with the audio file(s) as a single chunk
        start_time (str|None): Start time offset.
        translate (bool): Include translation if True.
        prompt (str): Prompt text to guide transcription.
        silence_boundaries (bool): Detection method for splitting chunks
        whisper_boundaries (bool): Detection method for splitting chunks (default)
    """
    logger.info("Starting audio transcription pipeline...")

    if full:
        split = True
        transcribe = True

    if yt_url or yt_url_list:
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
            yt_url_list=Path(yt_url_list) if yt_url_list else None,
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
        if is_download and yt_url_list:
            urls = get_youtube_urls_from_csv(Path(yt_url_list))
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