import csv
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, TypedDict
from xml.etree.ElementTree import ParseError

import yt_dlp

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import read_str_from_file

logger = get_child_logger(__name__)

DEFAULT_TRANSCRIPT_DIR = Path.home() / ".yt_dlp_transcripts"

DEFAULT_TRANSCRIPT_OPTIONS = {
    "skip_download": True,
    "quiet": True,
    "no_warnings": True,
    # 'verbose': True,
    "extract_flat": True,
    "socket_timeout": 30,
    "retries": 3,
    "ignoreerrors": True,  # Continue on download errors
    "logger": logger,
}

class TranscriptNotFoundError(Exception):
    """Raised when no transcript is available for the requested language."""

    def __init__(
        self,
        video_url: str,
        language: str,
    ) -> None:
        """
        Initialize TranscriptNotFoundError.

        Args:
            video_url: URL of the video where transcript was not found
            language: Language code that was requested
        """
        self.video_url = video_url
        self.language = language

        message = (
            f"No transcript found for {self.video_url} in language {self.language}. "
        )
        super().__init__(message)


class SubtitleTrack(TypedDict):
    """Type definition for a subtitle track entry."""

    url: str
    ext: str
    name: str


class VideoInfo(TypedDict):
    """Type definition for relevant video info fields."""

    subtitles: Dict[str, List[SubtitleTrack]]
    automatic_captions: Dict[str, List[SubtitleTrack]]


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

    try:
        with file_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None or "url" not in reader.fieldnames or "title" not in reader.fieldnames:
                logger.error("CSV file must contain 'url' and 'title' columns.")
                raise ValueError("CSV file must contain 'url' and 'title' columns.")

            for row in reader:
                url = row["url"]
                title = row["title"]
                urls.append(url)
                logger.info(f"Found video title: {title}")
    except Exception as e:
        logger.exception(f"Error processing CSV file: {e}")
        raise

    return urls

def get_video_download_path_yt(output_dir: Path, url: str) -> Path:
    """
    Extracts the video title using yt-dlp.

    Args:
        url (str): The YouTube URL.

    Returns:
        str: The title of the video.
    """
    ydl_opts = {
        "quiet": True,  # Suppress output
        "skip_download": True,  # Don't download, just fetch metadata
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            url, download=False
        )  # Extract metadata without downloading
        filepath = ydl.prepare_filename(info)

    return Path(filepath).with_suffix(".mp3")

def download_audio_yt(
    url: str, output_dir: Path, start_time: Optional[str] = None, prompt_overwrite=True
) -> Path:
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
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "postprocessor_args": [],
        "noplaylist": True,
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
    }

    # Add start time to the FFmpeg postprocessor if provided
    if start_time:
        ydl_opts["postprocessor_args"].extend(["-ss", start_time])
        logger.info(f"Postprocessor start time set to: {start_time}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)  # Extract metadata and download
        filename = ydl.prepare_filename(info)
        return Path(filename).with_suffix(".mp3")


def get_transcript(
    url: str,
    lang: str = "en",
    download_dir: Path = DEFAULT_TRANSCRIPT_DIR,
    keep_transcript_file: bool = False,
) -> str:
    """Downloads and extracts the transcript for a given YouTube video URL.

    Retrieves the transcript file, extracts the text content, and returns the raw text.

    Args:
        url: The URL of the YouTube video.
        lang: The language code for the transcript (default: 'en').
        download_dir: The directory to download the transcript to.
        keep_transcript_file: Whether to keep the downloaded transcript file (default: False).

    Returns:
        The extracted transcript text.

    Raises:
        TranscriptNotFoundError: If no transcript is available in the specified language.
        yt_dlp.utils.DownloadError: If video info extraction or download fails.
        ValueError: If the downloaded transcript file is invalid or empty.
        ParseError: If XML parsing of the transcript fails.
    """

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

    return _extract_ttml_text(text)

def _download_yt_ttml(temp_storage_path: Path, url: str, lang: str = "en") -> Path:
    """
    Downloads video transcript in TTML format to specified path.

    Args:
        video_url: The URL of the video
        output_path: Directory where transcript will be saved
        lang: The desired language code

    Returns:
        Path to the downloaded TTML file

    Raises:
        TranscriptNotFoundError: If no transcript is available
    """

    logger.info(f"Downloading TTML transcript for {url} in language '{lang}'")

    try:
        temp_storage_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create directory {temp_storage_path}: {e}")
        raise

    return _extract_ttml_from_youtube(url, lang, temp_storage_path)

def _extract_ttml_from_youtube(url: str, lang: str, temp_storage_path: Path) -> Path:
    """Extracts TTML data from YouTube using yt-dlp."""

    options = {
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitlesformat": "ttml",
        "subtitleslangs": [lang],
        "outtmpl": str(temp_storage_path / "%(id)s.%(ext)s"),
        "progress_hooks": [],
    }
    options |= DEFAULT_TRANSCRIPT_OPTIONS

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url)

        if not info:
            raise ValueError(f"Failed to retrieve video information for {url}")

        video_id = info["id"]

        if ttml_files := list(temp_storage_path.glob(f"{video_id}*.{lang}*.ttml")):
            return ttml_files[0]

        raise TranscriptNotFoundError(video_url=url, language=lang)

def _extract_ttml_text(ttml_str: str) -> str:
    """
    Extract raw text content from TTML format string, preserving only the text content.

    Uses proper namespace handling for TTML XML parsing and extracts text from
    paragraph elements while maintaining line separation.

    Args:
        ttml_str: String containing TTML-formatted XML content

    Returns:
        String containing extracted text with line breaks between paragraphs

    Raises:
        ValueError: If input string is empty or not a string
        ParseError: If XML parsing fails due to malformed content
        DefusedParseError: If XML contains potentially malicious content
    """
    if not isinstance(ttml_str, str):
        raise ValueError("Input must be a string")

    if not ttml_str.strip():
        raise ValueError("Input string cannot be empty")

    # TTML namespace - used for proper XML parsing
    namespaces = {
        "tt": "http://www.w3.org/ns/ttml",
        "tts": "http://www.w3.org/ns/ttml#styling",
    }

    try:
        # Parse XML using proper namespace handling
        root = ET.fromstring(ttml_str)

        # Extract text from all paragraph elements
        # Note: TTML specification uses <p> elements for paragraph content
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

def get_transcript_info(video_url: str, lang: str = "en") -> str:
    """
    Retrieves the transcript URL for a video in the specified language.

    Args:
        video_url: The URL of the video
        lang: The desired language code

    Returns:
        URL of the transcript

    Raises:
        TranscriptNotFoundError: If no transcript is available in the specified language
        yt_dlp.utils.DownloadError: If video info extraction fails
    """
    options = {
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [lang],
        "skip_download": True,
        #    'verbose': True
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        # This may raise yt_dlp.utils.DownloadError which we let propagate
        info: VideoInfo = ydl.extract_info(video_url, download=False)  # type: ignore

        subtitles = info.get("subtitles", {})
        auto_subtitles = info.get("automatic_captions", {})

        # Log available subtitle information
        logger.debug("Available subtitles:")
        logger.debug(f"Manual subtitles: {list(subtitles.keys())}")
        logger.debug(f"Auto captions: {list(auto_subtitles.keys())}")

        if lang in subtitles:
            return subtitles[lang][0]["url"]
        elif lang in auto_subtitles:
            return auto_subtitles[lang][0]["url"]

        raise TranscriptNotFoundError(video_url=video_url, language=lang)
