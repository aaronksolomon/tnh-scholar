#!/opt/anaconda3/envs/tnh-scholar/bin/python

import argparse
import os
import sys
from pathlib import Path

from video_processing import (
    detect_boundaries,
    download_audio_yt,
    get_youtube_urls_from_csv,
    process_audio_chunks,
    split_audio_at_boundaries,
)

from src.tnh_scholar.logging_config import get_child_logger, setup_logging

setup_logging(log_filepath="transcription.log")
logger = get_child_logger("yt_transcribe")

# Parameters
DEFAULT_OUTPUT_DIR = "./video_transcriptions"
DEFAULT_CHUNK_DURATION_S = 10 * 60  # in seconds. 10 minute default duration
DEFAULT_CHUNK_DURATION_MS = 10 * 60 * 1000  # in miliseconds. 10m
DEFAULT_PROMPT = (
    "Dharma, Deer Park, Thay, Thich Nhat Hanh, Bodhicitta, Bodhisattva, Mahayana"
)
EXPECTED_ENV = "tnh-scholar"


def check_conda_env():
    active_env = os.environ.get("CONDA_DEFAULT_ENV")
    if active_env != EXPECTED_ENV:
        logger.warning(
            f"WARNING: The active conda environment is '{active_env}', but '{EXPECTED_ENV}' is required. "
            "Please activate the correct environment."
        )
        # Optionally exit the script
        sys.exit(1)


# Call the check early in the script
check_conda_env()


def transcribe_youtube_videos(
    urls: list[str],
    output_base_dir: Path,
    max_chunk_duration: int = DEFAULT_CHUNK_DURATION_S,
    start: str = None,
    translate=False,
):
    """
    Full pipeline for transcribing a list of YouTube videos.

    Args:
        urls (list[str]): List of YouTube video URLs.
        output_base_dir (Path): Base directory for storing output.
        max_chunk_duration (int): Maximum duration for audio chunks in seconds (default is 10 minutes).
    """
    output_base_dir.mkdir(parents=True, exist_ok=True)

    for url in urls:
        try:
            logger.info(f"Processing video: {url}")

            # Step 1: Download audio
            logger.info("Downloading audio...")
            tmp_audio_file = download_audio_yt(url, output_base_dir, start_time=start)
            logger.info(f"Downloaded audio file: {tmp_audio_file}")

            # Prepare directories for chunks and outputs
            video_name = (
                tmp_audio_file.stem
            )  # Use the stem of the audio file (title without extension)
            video_output_dir = output_base_dir / video_name
            chunks_dir = video_output_dir / "chunks"
            chunks_dir.mkdir(parents=True, exist_ok=True)

            # Create the video directory and move the audio file into it
            video_output_dir.mkdir(parents=True, exist_ok=True)
            audio_file = video_output_dir / tmp_audio_file.name

            try:
                tmp_audio_file.rename(
                    audio_file
                )  # Move the audio file to the video directory
                logger.info(f"Moved audio file to: {audio_file}")
            except Exception as e:
                logger.error(f"Failed to move audio file to {video_output_dir}: {e}")
                # Ensure the code gracefully handles issues here, reassigning to the original tmp path.
                audio_file = tmp_audio_file

            # Step 2: Detect boundaries
            logger.info("Detecting boundaries...")
            boundaries = detect_boundaries(audio_file)
            logger.info("Boundaries generated.")

            # Step 3: Split audio into chunks
            logger.info("Splitting audio into chunks...")
            split_audio_at_boundaries(
                audio_file=audio_file,
                boundaries=boundaries,
                output_dir=chunks_dir,
                max_duration=max_chunk_duration,
            )
            logger.info(f"Audio chunks saved to: {chunks_dir}")

            # Step 4: Transcribe audio chunks
            logger.info("Transcribing audio chunks...")
            transcript_file = video_output_dir / f"{video_name}.txt"
            jsonl_file = video_output_dir / f"{video_name}.jsonl"
            process_audio_chunks(
                directory=chunks_dir,
                output_file=transcript_file,
                jsonl_file=jsonl_file,
                prompt=DEFAULT_PROMPT,
                translate=translate,
            )
            logger.info(f"Transcription completed for {url}")
            logger.info(f"Transcript saved to: {transcript_file}")
            logger.info(f"Raw transcription data saved to: {jsonl_file}")

        except Exception as e:
            logger.error(f"Failed to process video {url}: {e}")


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Transcribe YouTube videos from a URL or a file containing URLs."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--file",
        type=str,
        help="Path to the file containing YouTube URLs (newline-separated).",
    )
    group.add_argument(
        "--url", type=str, help="Single YouTube video URL to transcribe."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save transcriptions and processed audio (default: ./video_transcriptions).",
    )
    parser.add_argument(
        "--max_chunk_duration",
        type=int,
        default=DEFAULT_CHUNK_DURATION_S,
        help="Maximum duration for audio chunks in miliseconds (default: 10 minutes).",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start time for the video (format: HH:MM:SS). The transcription will begin from this time.",
    )
    parser.add_argument(
        "-translate",
        action="store_true",
        help="If set, the transcription will include translation.",
    )

    args = parser.parse_args()

    video_urls = []

    # Handle input source
    if args.file:
        url_file = Path(args.file)
        video_urls = get_youtube_urls_from_csv(url_file)
        if not video_urls:
            logger.error("No valid URLs found in the file.")
            sys.exit(1)
    elif args.url:
        video_urls = [args.url]

    # Process the videos
    output_directory = Path(args.output_dir)
    transcribe_youtube_videos(
        video_urls,
        output_directory,
        args.max_chunk_duration,
        args.start,
        translate=args.translate,
    )
