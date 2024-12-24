import yt_dlp
from pathlib import Path
from pydub import AudioSegment
from openai import OpenAI
from openai.types.audio.transcription_verbose import TranscriptionVerbose
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import whisper
import logging
from typing import List, Dict, Any
import json
import csv
import warnings
from tnh_scholar.logging_config import get_child_logger

MIN_SILENCE_LENGTH = 1000 # 1 second in ms, for splitting on silence
SILENCE_DBFS_THRESHOLD = -30    # Silence threshold in dBFS
MAX_DURATION_MS = 10 * 60 * 1000  # Max chunk length in milliseconds, 10m
MAX_DURATION_S = 10 * 60 # Max chunk length in seconds, 10m
SEEK_LENGTH = 100 # miliseconds. for silence detection, the scan interval
TOKEN_BUFFER = 500   # additional tokens to request as a buffer when parsing text.

# from tnh_scholar.gpt_processing import (
#     run_transcription_speech, 
#     token_count, 
#     run_immediate_completion_simple, 
#     run_single_batch, 
#     get_completion_content, 
#     get_completion_object
# )

from tnh_scholar.utils import get_user_confirmation

# from tnh_scholar.text_processing import get_text_from_file, write_text_to_file

logger = get_child_logger("video_processing")

def get_youtube_urls_from_csv(file_path: Path) -> List[str]:
    """
    Reads a CSV file containing YouTube URLs and titles, logs the titles, 
    and returns a list of URLs.

    Args:
        file_path (Path): Path to the CSV file containing YouTube URLs and titles.

    Returns:
        List[str]: List of YouTube URLs.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the CSV file is improperly formatted.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    urls = []
    
    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        if "url" not in reader.fieldnames or "title" not in reader.fieldnames:
            logger.error("CSV file must contain 'url' and 'title' columns.")
            raise ValueError("CSV file must contain 'url' and 'title' columns.")
        
        for row in reader:
            url = row["url"]
            title = row["title"]
            urls.append(url)
            logger.info(f"Found video title: {title}")
    
    return urls

def get_video_download_path_yt(output_dir: Path, url: str) -> str:
    """
    Extracts the video title using yt-dlp.
    
    Args:
        url (str): The YouTube URL.
    
    Returns:
        str: The title of the video.
    """
    ydl_opts = {
        'quiet': True,  # Suppress output
        'skip_download': True,  # Don't download, just fetch metadata
        'outtmpl': str(output_dir / '%(title)s.%(ext)s')
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)  # Extract metadata without downloading
        filepath = ydl.prepare_filename(info)

    download_path = Path(filepath).with_suffix('.mp3') # ensure mp3 format for audio downloads.
    return download_path

def download_audio_yt(url: str, output_dir: Path, start_time: str = None, prompt_overwrite=True) -> Path:
    """
    Downloads audio from a YouTube video using yt_dlp.YoutubeDL, with an optional start time.

    Args:
        url (str): URL of the YouTube video.
        output_dir (Path): Directory to save the downloaded audio file.
        start_time (str): Optional start time (e.g., '00:01:30' for 1 minute 30 seconds).

    Returns:
        Path: Path to the downloaded audio file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'postprocessor_args': [],
        'noplaylist': True,
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
    }

    # Add start time to the FFmpeg postprocessor if provided
    if start_time:
        ydl_opts['postprocessor_args'].extend(['-ss', start_time])
        logger.info(f"Postprocessor start time set to: {start_time}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)  # Extract metadata without downloading
        filename = ydl.prepare_filename(info)
        return Path(filename).with_suffix('.mp3')