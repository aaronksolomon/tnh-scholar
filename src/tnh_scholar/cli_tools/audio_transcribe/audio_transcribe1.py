#!/usr/bin/env python
# audio_transcribe.py
"""
CLI tool for downloading audio (YouTube or local), 
splitting into chunks, and transcribing.

Usage:
    audio-transcribe [OPTIONS]

    e.g. audio-transcribe \
        --yt_url https://www.youtube.com/watch?v=EXAMPLE \
        --split \
        --transcribe \
        --output_dir ./processed \
        --prompt "Some prompt"
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import click
from dotenv import load_dotenv

# External modules from tnh_scholar
from tnh_scholar import TNH_LOG_DIR
from tnh_scholar.audio_processing import (
    split_audio,
)
from tnh_scholar.audio_processing.transcription import get_transcription
from tnh_scholar.logging_config import get_child_logger, setup_logging
from tnh_scholar.metadata.metadata import Frontmatter, Metadata
from tnh_scholar.utils import ensure_directory_exists, get_user_confirmation
from tnh_scholar.utils.file_utils import write_str_to_file
from tnh_scholar.video_processing import (
    DLPDownloader,
    get_youtube_urls_from_csv,
)
from tnh_scholar.video_processing.video_processing import VideoAudio

from .version_check import check_ytd_version

# Turn off certain warnings
os.environ["KMP_WARNINGS"] = "0"

# --- Basic setup ---
load_dotenv()
setup_logging(log_filepath=TNH_LOG_DIR / "audio_transcribe.log", log_level=logging.INFO)
logger = get_child_logger(__name__)

DEFAULT_CHUNK_DURATION_MIN = 7
DEFAULT_CHUNK_DURATION_SEC = DEFAULT_CHUNK_DURATION_MIN * 60
DEFAULT_OUTPUT_DIR = "./audio_transcriptions"
DEFAULT_PROMPT = "Dharma, Deer Park, Thay, Thich Nhat Hanh"
RE_DOWNLOAD_CONFIRMATION_STR = (
    "An mp3 file for {url} already exists in {output_dir}.\nSKIP download ([Y]/n)?"
)

@dataclass
class AudioSource:
    """Configuration for the audio source (YouTube or local)."""
    yt_url: Optional[str] = None
    yt_url_csv: Optional[Path] = None
    audio_file: Optional[Path] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

@dataclass
class SplitAudio:
    file_path: Path
    metadata: Metadata
    is_chunked: bool = True    
    
@dataclass
class SplitConfig:
    """Configuration for splitting audio."""
    enabled: bool = True
    chunk_dir: Optional[Path] = None
    chunk_duration: int = DEFAULT_CHUNK_DURATION_SEC
    no_chunks: bool = False
    method: str = "whisper"  # or "silence"
    language: str = "en"

@dataclass
class TranscribeConfig:
    """Configuration for transcription."""
    enabled: bool = True
    translate: bool = False
    prompt: str = DEFAULT_PROMPT

@dataclass 
class AudioPipelineConfig:
    """Umbrella configuration for entire pipeline"""
    source: AudioSource
    split: SplitConfig 
    transcribe: TranscribeConfig
    output_dir: Path

class AudioPipeline:
    """Core pipeline implementation"""
    def __init__(self, config: AudioPipelineConfig):
        self.config = config
        
    def run(self) -> None:
        """Execute full pipeline"""
        audio_data = handle_audio_source(
            self.config.source, 
            self.config.output_dir
            )
        split_results = handle_split(
            audio_data, 
            self.config.split, 
            self.config.output_dir
            )
        handle_transcribe(
            split_results, 
            self.config.transcribe, 
            self.config.output_dir
            )

def handle_audio_source(
    source: AudioSource, 
    output_dir: Path
    ) -> List[VideoAudio]:
    """
    Gather or download audio files from YouTube or local source.
    Returns a list of audio file paths.
    """
    is_download = bool(source.yt_url or source.yt_url_csv)

    if is_download:
        check_ytd_version()

    # If CSV provided, gather multiple URLs
    if source.yt_url_csv and is_download:
        urls = get_youtube_urls_from_csv(source.yt_url_csv)
    elif source.yt_url and is_download:
        urls = [source.yt_url]
    else:
        urls = []

    # Download if needed
    if urls:
       return _download_urls(urls, source, output_dir)
        
    # If local file provided (and no YT download needed)
    if source.audio_file and not is_download:
        # Use a VideoAudio object with empty metadata
        return [VideoAudio(metadata=Metadata(), filepath=source.audio_file)]
    
    logger.error("No audio input found.")
    exit(1)

def _download_urls(urls, source, output_dir) -> List[VideoAudio]:
    
    # Set the downloader object
    dl = DLPDownloader()
    
    video_data_list: List[VideoAudio] = []

    for url in urls:
        url_metadata = dl.get_metadata(url)
        default_name = dl.get_default_filename_stem(url_metadata)
        download_path = output_dir / default_name    
    
        if download_path.exists():
            if get_user_confirmation(
                RE_DOWNLOAD_CONFIRMATION_STR.format(url=url, output_dir=output_dir)
            ):
                logger.info(f"Skipping download for {url}")
                video_data = VideoAudio(url_metadata, download_path)
                video_data_list.append(video_data)
                continue
            else:
                logger.info(f"Re-downloading {url}")
                
        ensure_directory_exists(output_dir)
        video_data = dl.get_audio(
            url,  
            start=source.start_time,
            output_path=download_path,
            )
        logger.info(f"Downloaded {url} to {download_path}")

        video_data_list.append(video_data)
        
    return video_data_list

def handle_split(
    audio_list: List[VideoAudio], 
    config: SplitConfig, 
    output_dir: Path
    ) -> List[SplitAudio]:
    """
    Split audio files into chunks if configured, returning a list of processed results.
    """
    if not config.enabled or config.no_chunks:
        # need to implement
        click.echo("not implemented!")
        exit(1)
        
        # should:
        # skip splitting if not configured or asked to avoid chunking
        # return audio_list  

    chunk_data: List[SplitAudio] = []

    for audio_data in audio_list:
        audio_file = audio_data.filepath
        assert audio_file is not None # must have real audio_files
        audio_name = audio_file.stem
        audio_output_dir = output_dir / audio_name
        chunk_output_dir = config.chunk_dir or (audio_output_dir / "chunks")
        ensure_directory_exists(audio_output_dir)

        logger.info(f"Splitting {audio_file} into chunks "
                    f"using '{config.method}' boundaries."
                    )

        split_audio(
            audio_file=audio_file,
            method=config.method,
            output_dir=chunk_output_dir,
            max_duration=config.chunk_duration,
            language=config.language,
        )

        # The chunk files are discovered externally.
        # Store the chunk dir for later use and
        # Return a list of all the chunk directories.
        chunk_data.append(
            SplitAudio(
                file_path=chunk_output_dir, 
                metadata=audio_data.metadata,
                is_chunked=True,
            )
        )

    return chunk_data

def handle_transcribe(
    audio_splits: List[SplitAudio], 
    config: TranscribeConfig, 
    output_dir: Path) -> None:
    """
    Transcribe audio directly (if no_chunks) or from chunk directories.
    """
    if not config.enabled:
        return

    # current implementation expects chunks
    
    for split in audio_splits:
        
        if split.is_chunked:
            # This is a directory with chunks
            audio_name = split_name(split)
            transcript_file = output_dir / audio_name / f"{audio_name}.txt"
            jsonl_file = output_dir / audio_name / f"{audio_name}.jsonl"
            logger.info(f"Transcribing chunk directory {split.file_path}")
            
            transcript = process_audio_chunks(
                chunk_dir=split.file_path,
                jsonl_file=jsonl_file,
                prompt=config.prompt,
                translate=config.translate,
            )
            
            metadata_transcript = Frontmatter.embed(split.metadata, transcript)
            write_str_to_file(transcript_file, metadata_transcript)
            
        else:
            click.echo("Single file processing not implemented!")
            exit(1)
            # This is a single audio file
            # audio_file = split
            # audio_name = audio_file.stem
            # transcript_file = output_dir / audio_name / f"{audio_name}.txt"
            # jsonl_file = output_dir / audio_name / f"{audio_name}.jsonl"
            # ensure_directory_exists(output_dir / audio_name)
            # logger.info(f"Transcribing audio file {audio_file}")
            # process_audio_file(
            #     audio_file=audio_file,
            #     output_file=transcript_file,
            #     jsonl_file=jsonl_file,
            #     prompt=config.prompt,
            #     translate=config.translate,
            # )

    logger.info("Transcription complete.")


def split_name(split):
    return split.file_path.parent.stem

def process_audio_file(
    audio_file: Path,
    output_file: Path,
    jsonl_file: Path,
    model: str = "whisper-1",
    prompt: str = "",
    translate: bool = False,
) -> None:
    """
    NEEDS REFACTOR!
    Processes a single audio file using OpenAI's transcription API,
    saves the transcription objects into a JSONL file.

    Args:
        audio_file (Path): Path to the the audio file for processing
        output_file (Path): Path to the output file to save the stitched transcription.
        jsonl_file (Path): Path to save the transcription objects as a JSONL file.
        model (str): The transcription model to use (default is "whisper-1").
        prompt (str): Optional prompt to provide context for better transcription.
        translate (bool): Optional flag to translate speech to English 
        (useful if the audio input is not English)
    Raises:
        FileNotFoundError: If no audio chunks are found in the directory.
    """

    # Ensure the output directory exists
    ensure_directory_exists(output_file.parent)
    ensure_directory_exists(jsonl_file.parent)

    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file {audio_file} not found.")
    else:
        logger.info(f"Audio file found: {audio_file}")

    # Open the JSONL file for writing
    with jsonl_file.open("w", encoding="utf-8") as jsonl_out:
        logger.info(f"Processing {audio_file.name}...")
        try:
            if translate:
                text = get_transcription(
                    audio_file, model, prompt, jsonl_out, mode="translate"
                )
            else:
                text = get_transcription(
                    audio_file, model, prompt, jsonl_out, mode="transcribe"
                )
        except Exception as e:
            logger.error(f"Error processing {audio_file.name}: {e}", exc_info=True)
            raise e

    # Write the stitched transcription to the output file
    with output_file.open("w", encoding="utf-8") as out_file:
        out_file.write(text)

    logger.info(f"Transcription saved to {output_file}")
    logger.info(f"Full transcript objects saved to {jsonl_file}")

def process_audio_chunks(
    chunk_dir: Path,
    jsonl_file: Path,
    model: str = "whisper-1",
    prompt: str = "",
    translate: bool = False,
) -> str:
    """
    Processes all audio chunks in a specified directory using OpenAI's transcription 
    API, saves the transcription objects into a JSONL file, and stitches the 
    transcriptions into a single text.

    Args:
        directory (Path): Path to the directory containing audio chunks.
        output_file (Path): Path to the output file to save the stitched transcription.
        jsonl_file (Path): Path to save the transcription objects as a JSONL file.
        model (str): The transcription model to use (default is "whisper-1").
        prompt (str): Optional prompt to provide context for better transcription.
        translate (bool): Optional flag to translate speech to English 
        (useful if the audio input is not English)
    Raises:
        FileNotFoundError: If no audio chunks are found in the directory.
    """

    # Ensure the jsonl output directory exists
    ensure_directory_exists(jsonl_file.parent)

    # Collect all audio chunks in the directory, sorting numerically by chunk number
    audio_files = sorted(
        chunk_dir.glob("*.mp3"),
        key=lambda f: int(f.stem.split("_")[1]),  # Extract the number from 'chunk_X'
    )

    if not audio_files:
        raise FileNotFoundError(f"No audio files found in the directory: {chunk_dir}")

    # log files to process:
    audio_file_names = [file.name for file in audio_files]  # get strings for logging
    audio_file_name_str = "\n\t".join(audio_file_names)
    audio_file_count = len(audio_file_names)
    logger.info(
        f"{audio_file_count} audio files found in {chunk_dir}:\n\t{audio_file_name_str}"
    )

    return generate_transcription(
        audio_files, jsonl_file, translate, model, prompt
    )
    

def generate_transcription(
    audio_files, 
    jsonl_file, 
    translate, 
    model, 
    prompt
    ) -> str:
    # save transcription data to JSONL file 
    
    stitched_transcription: List[str] = []
    
    with jsonl_file.open("w", encoding="utf-8") as jsonl_out:
        # Process each audio chunk
        for audio_file in audio_files:
            logger.info(f"Processing {audio_file.name}...")

            if translate:
                text = get_transcription(
                    audio_file, model, prompt, jsonl_out, mode="translate"
                )
            else:
                text = get_transcription(
                    audio_file, model, prompt, jsonl_out, mode="transcribe"
                )

            stitched_transcription.append(text)
    
    logger.info(f"Full transcript objects saved to {jsonl_file}")
    return "\n".join(stitched_transcription)
            
@click.command()
@click.option("-s", "--split", is_flag=True, help="Split audio into chunks.")
@click.option("-t", "--transcribe", is_flag=True, help="Transcribe the audio.")
@click.option("-y", "--yt_url", type=str, help="Single YouTube URL.")
@click.option(
    "-v",
    "--yt_url_csv",
    type=click.Path(exists=True),
    help="CSV file with multiple YouTube URLs in first column.",
)
@click.option(
    "-f", "--file", "file_", type=click.Path(exists=True), 
    help="Path to a local audio file."
)
@click.option(
    "-c",
    "--chunk_dir",
    type=click.Path(),
    help="Directory for new or existing audio chunks.",
)
@click.option(
    "-o",
    "--output_dir",
    type=click.Path(),
    default=DEFAULT_OUTPUT_DIR,
    help="Base output directory.",
)
@click.option(
    "-d",
    "--chunk_duration",
    type=int,
    default=DEFAULT_CHUNK_DURATION_SEC,
    help=(
        f"Max chunk duration in seconds. \n"
        f"(default: {DEFAULT_CHUNK_DURATION_MIN} minutes).",
    )
)
@click.option(
    "-x",
    "--no_chunks",
    is_flag=True,
    help="Transcribe entire audio without splitting into chunks.",
)
@click.option(
    "-b",
    "--start_time",
    type=str,
    help="Start time offset for the input media (HH:MM:SS).",
)
@click.option(
    "-a",
    "--translate",
    is_flag=True,
    help="Enable translation in the transcription if set.",
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
    help="Use silence detection to split audio file(s).",
)
@click.option(
    "-w",
    "--whisper_boundaries",
    is_flag=True,
    help="(DEFAULT) Use a whisper-based model to split audio at sentence boundaries.",
)
@click.option(
    "-l",
    "--language",
    type=str,
    default="en",
    help="Two-letter language code (e.g., 'vi'). Used for splitting.",
)
def audio_transcribe(
    split: bool,
    transcribe: bool,
    yt_url: Optional[str],
    yt_url_csv: Optional[str],
    file_: Optional[str],
    chunk_dir: Optional[str],
    output_dir: str,
    chunk_duration: int,
    no_chunks: bool,
    start_time: Optional[str],
    translate: bool,
    prompt: str,
    silence_boundaries: bool,
    whisper_boundaries: bool,
    language: str,
) -> None:
    """
    Main CLI entry point. Orchestrates the audio pipeline:
    1) Download or locate audio source,
    2) Split (optional),
    3) Transcribe (optional).
    """
    # If user didn't specify, default is do both
    if not split and not transcribe:
        split = True
        transcribe = True

    # Decide which method to use for splitting
    # Default to whisper if not specified
    method = "whisper"
    if silence_boundaries and not whisper_boundaries:
        method = "silence"

    # Build configuration objects
    source_config = AudioSource(
        yt_url=yt_url,
        yt_url_csv=Path(yt_url_csv) if yt_url_csv else None,
        audio_file=Path(file_) if file_ else None,
        start_time=start_time,
    )

    split_config = SplitConfig(
        enabled=split,
        chunk_dir=Path(chunk_dir) if chunk_dir else None,
        chunk_duration=chunk_duration,
        no_chunks=no_chunks,
        method=method,
        language=language,
    )

    transcribe_config = TranscribeConfig(
        enabled=transcribe,
        translate=translate,
        prompt=prompt,
    )

    config = AudioPipelineConfig(
        source=source_config,
        split=split_config,
        transcribe=transcribe_config,
        output_dir=Path(output_dir)
    )
    
    pipeline = AudioPipeline(config)
    pipeline.run()
    
    logger.info("Audio transcription pipeline completed.")

def main():
    audio_transcribe()

if __name__ == "__main__":
    main()


