import csv
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict
from xml.etree.ElementTree import ParseError

import yt_dlp

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import read_str_from_file

logger = get_child_logger(__name__)

# Configuration Constants
DEFAULT_TRANSCRIPT_DIR = Path.home() / ".yt_dlp_transcripts"

# Core yt-dlp options
BASE_YDL_OPTIONS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "socket_timeout": 30,
    "retries": 3,
    "ignoreerrors": True,
    "logger": logger,
}

AUDIO_DOWNLOAD_OPTIONS = BASE_YDL_OPTIONS | {
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "noplaylist": True,
}

TRANSCRIPT_OPTIONS = BASE_YDL_OPTIONS | {
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitlesformat": "ttml",
}

# Default metadata fields to collect
DEFAULT_METADATA_FIELDS = [
    "id",
    "title",
    "description",
    "duration",
    "upload_date",
    "uploader",
    "channel_url",
    "webpage_url",
    "original_url",
    "channel",
    "language",
    "categories",
    "tags",
]

# Return Types
@dataclass
class VideoMetadata:
    """Base class for video operations containing common metadata."""
    metadata: Dict[str, Any]

@dataclass
class VideoTranscript(VideoMetadata):
    """Result of transcript operations."""
    content: str

@dataclass
class VideoDownload(VideoMetadata):
    """Result of download operations."""
    filepath: Path

class SubtitleTrack(TypedDict):
    """Type definition for a subtitle track entry."""
    url: str
    ext: str
    name: str

class VideoInfo(TypedDict):
    """Type definition for relevant video info fields."""
    subtitles: Dict[str, List[SubtitleTrack]]
    automatic_captions: Dict[str, List[SubtitleTrack]]

class TranscriptNotFoundError(Exception):
    """Raised when no transcript is available for the requested language."""
    def __init__(self, video_url: str, language: str) -> None:
        self.video_url = video_url
        self.language = language
        message = f"No transcript found for {self.video_url} \
                    in language {self.language}."
        super().__init__(message)

def get_youtube_urls_from_csv(file_path: Path) -> List[str]:
    """Reads YouTube URLs from a CSV file containing URLs and titles."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    urls = []
    try:
        with file_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None \
                or "url" not in reader.fieldnames \
                or "title" not in reader.fieldnames:
                logger.error("CSV file must contain 'url' and 'title' columns.")
                raise ValueError("CSV file must contain 'url' and 'title' columns.")

            for row in reader:
                urls.append(row["url"])
                logger.info(f"Found video title: {row['title']}")
    except Exception as e:
        logger.exception(f"Error processing CSV file: {e}")
        raise

    return urls

def get_video_download_path_yt(output_dir: Path, url: str) -> VideoDownload:
    """Get video metadata and expected download path."""
    options = AUDIO_DOWNLOAD_OPTIONS | {
        "skip_download": True,
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        if info := ydl.extract_info(url, download=False):
            filepath = Path(ydl.prepare_filename(info)).with_suffix(".mp3")
            metadata = _extract_metadata(info)
        else:
            logger.error(f"YT video download: unable to extract info for {url}")
            raise
        return VideoDownload(metadata=metadata, filepath=filepath)

def download_audio_yt(
    url: str, 
    output_dir: Path, 
    start_time: Optional[str] = None
) -> VideoDownload:
    """Downloads audio from YouTube URL with optional start time."""
    output_dir.mkdir(parents=True, exist_ok=True)

    options = AUDIO_DOWNLOAD_OPTIONS | {
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
    }

    if start_time:
        options["postprocessor_args"] = ["-ss", start_time]
        logger.info(f"Postprocessor start time set to: {start_time}")

    with yt_dlp.YoutubeDL(options) as ydl:
        if info := ydl.extract_info(url, download=True):
            filepath = Path(ydl.prepare_filename(info)).with_suffix(".mp3")
            metadata = _extract_metadata(info)
        else:
            logger.error(f"YT audio download: Unable to get info for {url}.")
            raise 
        return VideoDownload(metadata=metadata, filepath=filepath)

def get_transcript(
    url: str,
    lang: str = "en",
    download_dir: Path = DEFAULT_TRANSCRIPT_DIR,
    keep_transcript_file: bool = False,
) -> VideoTranscript:
    """Downloads and extracts transcript with metadata."""
    transcript_file = _download_yt_ttml(download_dir, url=url, lang=lang)
    text = read_str_from_file(transcript_file)

    if not keep_transcript_file:
        try:
            os.remove(transcript_file)
            logger.debug(f"Removed temporary transcript file: {transcript_file}")
        except OSError as e:
            logger.warning(
                f"Failed to remove temporary transcript file {transcript_file}: {e}"
                )

    content = _extract_ttml_text(text)

    # Get metadata
    options = BASE_YDL_OPTIONS | {"skip_download": True}
    with yt_dlp.YoutubeDL(options) as ydl:
        if info := ydl.extract_info(url, download=False):
            metadata = _extract_metadata(info)
        else:
            logger.error(f"YT get transcript: unable to get info for {url}.")
            raise
    return VideoTranscript(metadata=metadata, content=content)

def _download_yt_ttml(temp_storage_path: Path, url: str, lang: str = "en") -> Path:
    """Downloads video transcript in TTML format."""
    logger.info(f"Downloading TTML transcript for {url} in language '{lang}'")

    try:
        temp_storage_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create directory {temp_storage_path}: {e}")
        raise

    return _extract_ttml_from_youtube(url, lang, temp_storage_path)

def _extract_ttml_from_youtube(url: str, lang: str, temp_storage_path: Path) -> Path:
    """Extracts TTML data from YouTube."""
    options = TRANSCRIPT_OPTIONS | {
        "subtitleslangs": [lang],
        "outtmpl": str(temp_storage_path / "%(id)s.%(ext)s"),
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url)
        if not info:
            raise ValueError(f"Failed to retrieve video information for {url}")

        video_id = info["id"]
        if ttml_files := list(temp_storage_path.glob(f"{video_id}*.{lang}*.ttml")):
            return ttml_files[0]

        logger.error(f"Downloaded transcript file not found in {temp_storage_path}.")
        raise TranscriptNotFoundError(video_url=url, language=lang)

def _extract_ttml_text(ttml_str: str) -> str:
    """Extract raw text content from TTML format string."""
    if not isinstance(ttml_str, str):
        raise ValueError("Input must be a string")

    if not ttml_str.strip():
        raise ValueError("Input string cannot be empty")

    namespaces = {
        "tt": "http://www.w3.org/ns/ttml",
        "tts": "http://www.w3.org/ns/ttml#styling",
    }

    try:
        root = ET.fromstring(ttml_str)
        text_lines = []
        for p in root.findall(".//tt:p", namespaces):
            if p.text is not None:
                text_lines.append(p.text.strip())
            else:
                text_lines.append("")
                logger.debug("Found empty paragraph in TTML, preserving as blank line")

        logger.info(f"Extracted {len(text_lines)} lines of text from TTML")
        return "\n".join(text_lines)

    except ParseError as e:
        logger.error(f"Failed to parse XML content: {e}")
        raise
    
def _extract_metadata(
    info: Dict[str, Any], 
    fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
    """Extract specified metadata fields from yt-dlp info dictionary.
    
    Args:
        info: Raw info dictionary from yt-dlp
        fields: List of fields to extract. If None, uses DEFAULT_METADATA_FIELDS
        
    Returns:
        Dictionary containing only specified fields that exist in info
    """
    fields = fields or DEFAULT_METADATA_FIELDS
    return {k: info.get(k) for k in fields if k in info}

def get_video_metadata(url: str) -> VideoResult:
    """Get metadata for a YouTube video without downloading content.
    
    Args:
        url: YouTube video URL
        
    Returns:
        VideoResult with only metadata field populated
        
    Raises:
        yt_dlp.utils.DownloadError: If video info extraction fails
    """
    options = BASE_YDL_OPTIONS | {"skip_download": True}
    
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
        metadata = _extract_metadata(info)
        return VideoResult(metadata=metadata)