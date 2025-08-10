"""
video_processing.py
"""

import csv
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from xml.etree.ElementTree import ParseError

import yt_dlp

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.metadata import Metadata
from tnh_scholar.utils import sanitize_filename

# from tnh_scholar.utils.file_utils import write_text_to_file

logger = get_child_logger(__name__)

# Core yt-dlp configuration constants remain unchanged
BASE_YDL_OPTIONS = {
    "quiet": False,
    "no_warnings": True,
    "extract_flat": True,
    "socket_timeout": 30,
    "retries": 3,
    "ignoreerrors": True,
    "logger": logger,
}

DEFAULT_AUDIO_OPTIONS = BASE_YDL_OPTIONS | {
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

DEFAULT_TRANSCRIPT_OPTIONS = BASE_YDL_OPTIONS | {
    "skip_download": True,
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitlesformat": "ttml",
}

DEFAULT_METADATA_OPTIONS = BASE_YDL_OPTIONS | {
    "skip_download": True,
}

DEFAULT_VIDEO_OPTIONS = BASE_YDL_OPTIONS | {
    "format": "bestvideo+bestaudio/best",
    "merge_output_format": "mp4",
    "noplaylist": True,
}

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

TEMP_FILENAME_FORMAT = "temp_%(id)s"
TEMP_FILENAME_STR = "temp_{id}"

class VideoProcessingError(Exception):
    """Base exception for video processing errors."""
    pass

class TranscriptError(VideoProcessingError):
    """Raised for transcript-related errors."""
    pass

class DownloadError(VideoProcessingError):
    """Raised for download-related errors."""
    pass

class VideoDownloadError(VideoProcessingError):
    """Raised for video download-related errors."""
    pass

@dataclass 
class VideoResource:
    """Base class for all video resources."""
    metadata: Metadata
    filepath: Optional[Path] = None

class VideoTranscript(VideoResource): 
    pass

class VideoAudio(VideoResource): 
    pass 

class VideoFile(VideoResource):
    """Represents a downloaded video file and its metadata."""
    pass


class YTDownloader:
    """Abstract base class for YouTube content retrieval."""
    
    def get_transcript(
        self, 
        url: str, 
        lang: str = "en", 
        output_path: Optional[Path] = None
    ) -> VideoTranscript:
        """Retrieve video transcript with associated metadata."""
        raise NotImplementedError
        
    def get_audio(
        self, 
        url: str, 
        start: str,
        end: str,
        output_path: Optional[Path]
    ) -> VideoAudio:
        """Extract audio with associated metadata."""
        raise NotImplementedError
        
    def get_metadata(
        self, 
        url: str, 
    ) -> Metadata:
        """Retrieve video metadata only."""
        raise NotImplementedError

    def get_video(
        self,
        url: str,
        quality: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> VideoFile:
        """
        Download the full video with associated metadata.

        Args:
            url: YouTube video URL
            quality: yt-dlp format string (default: highest available)
            output_path: Optional output directory

        Returns:
            VideoFile containing video file path and metadata

        Raises:
            VideoDownloadError: If download fails
        """
        raise NotImplementedError

class DLPDownloader(YTDownloader):
    """
    yt-dlp based implementation of YouTube content retrieval.
    
    Assures temporary file export is in the form <ID>.<ext> 
    where ID is the YouTube video id, and ext is the appropriate
    extension.
    
    Renames the export file to be based on title and ID by
    default, or moves the export file to the specified output
    file with appropriate extension.
    """
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or BASE_YDL_OPTIONS
        
    def get_metadata(
        self,
        url: str,
    ) -> Metadata:
        """
        Get metadata for a YouTube video. 
        """
        options = DEFAULT_METADATA_OPTIONS | self.config
        with yt_dlp.YoutubeDL(options) as ydl:
            if info := ydl.extract_info(url):
                return self._extract_metadata(info)
            logger.error(f"Unable to download metadata for {url}.")
            raise DownloadError("No info returned.")
    
    def get_transcript(
        self,
        url: str,
        lang: str = "en",
        output_path: Optional[Path] = None,
    ) -> VideoTranscript:
        """
        Downloads video transcript in TTML format.

        Args:
            url: YouTube video URL
            lang: Language code for transcript (default: "en")
            output_path: Optional output directory (uses current dir if None)
        
        Returns:
            TranscriptResource containing TTML file path and metadata
            
        Raises:
            TranscriptError: If no transcript found for specified language
        """
        temp_path = Path.cwd() / TEMP_FILENAME_FORMAT
        options = DEFAULT_TRANSCRIPT_OPTIONS | self.config | {
            "skip_download": True,
            "subtitleslangs": [lang],
            "outtmpl": str(temp_path),
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            if info := ydl.extract_info(url):
                metadata = self._extract_metadata(info)
                filepath = Path(ydl.prepare_filename(info)).with_suffix(f".{lang}.ttml")
                filepath = self._convert_filename(filepath, metadata, output_path)
                return VideoTranscript(metadata=metadata, filepath=filepath)
            else:
                logger.error("Info not found.")
                raise TranscriptError(f"Transcript not downloaded for {url} in {lang}")
    
    def get_audio(
        self, 
        url: str, 
        start: Optional[str] = None,
        end: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> VideoAudio:
        """Download audio and get metadata for a YouTube video."""
        temp_path = Path.cwd() / TEMP_FILENAME_FORMAT
        options = DEFAULT_AUDIO_OPTIONS | self.config | {
            "outtmpl": str(temp_path)
        }

        self._add_start_stop_times(options, start, end)

        with yt_dlp.YoutubeDL(options) as ydl:
            if info := ydl.extract_info(url, download=True):
                metadata = self._extract_metadata(info)
                filepath = Path(ydl.prepare_filename(info)).with_suffix(".mp3")
                filepath = self._convert_filename(filepath, metadata, output_path)
                return VideoAudio(metadata=metadata, filepath=filepath)
            else:
                logger.error("Info not found.")
                raise DownloadError(f"Unable to download {url}.")
    
    def get_video(
        self,
        url: str,
        quality: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> VideoFile:
        """
        Download the full video with associated metadata.

        Args:
            url: YouTube video URL
            quality: yt-dlp format string (default: highest available)
            output_path: Optional output directory

        Returns:
            VideoFile containing video file path and metadata

        Raises:
            VideoDownloadError: If download fails
        """
        temp_path = Path.cwd() / TEMP_FILENAME_FORMAT
        video_options = DEFAULT_VIDEO_OPTIONS | self.config | {
            "outtmpl": str(temp_path)
        }
        if quality:
            video_options["format"] = quality

        with yt_dlp.YoutubeDL(video_options) as ydl:
            if info := ydl.extract_info(url, download=True):
                metadata = self._extract_metadata(info)
                ext = info.get("ext", "mp4")
                filepath = Path(ydl.prepare_filename(info)).with_suffix(f".{ext}")
                filepath = self._convert_filename(filepath, metadata, output_path)
                return VideoFile(metadata=metadata, filepath=filepath)
            else:
                logger.error("Info not found.")
                raise VideoDownloadError(f"Unable to download video for {url}.")
    
    #TODO this function is not affecting the start time of processing. 
    # find a fix or new implementation 
    # (pydub postprocessing after yt-dlp? keep yt-dlp minimal?)        
    def _add_start_stop_times(
        self, options: dict, start: Optional[str], end: Optional[str]) -> None:
        """
        Adds -ss and -to arguments for FFmpegExtractAudio via postprocessor_args dict.
        Modifies options in place.
        """
        if start or end:
            ppa_args = []
            if start:
                ppa_args.extend(["-ss", start])
                logger.debug(f"Added start time to postprocessor args: {start}")
            if end:
                ppa_args.extend(["-to", end])
                logger.debug(f"Added end time to postprocessor args: {end}")

            postprocessor_args = options.setdefault("postprocessor_args", {})
            
            postprocessor_args.setdefault("ExtractAudio", []).extend(ppa_args)

        logger.info(f"Updated options for postprocessor_args: "
                    f"{options.get('postprocessor_args')}")
            
    def _extract_metadata(self, info: dict) -> Metadata:
        """Extract standard metadata fields from yt-dlp info."""
        return Metadata.from_fields(info, DEFAULT_METADATA_FIELDS)
    
    def _show_info(self, info: Metadata) -> None:
        """Debug routine for displaying info."""
        for k in info:
            if data := str(info[k]):
                if len(data) < 200:
                    print(f"{k}: {data}")
                else:
                    print(f"{k}: {data[:200]} ...")
                  
    def get_default_filename_stem(self, metadata: Metadata) -> str:
        """Generate the object download filename."""
        # Expect both id and title in Youtube metadata
        assert metadata["id"]
        assert metadata["title"] 
        video_id = str(metadata["id"])
        sanitized_title = sanitize_filename(str(metadata["title"]))
        return f"{sanitized_title}_{video_id}"
    
    def get_default_export_name(self, url) -> str:
        """Get default export filename for a URL."""
        metadata = self.get_metadata(url)
        return self.get_default_filename_stem(metadata)
        
    def _convert_filename(
        self, 
        temp_path: Path,
        metadata: Metadata, 
        output_path: Optional[Path]
    ) -> Path:
        """
        Move/rename file from temp_path to output_path if specified.
        If output_path is not provided, a sanitized title and video ID are 
        used to create the new filename. This function is required because yt-dlp 
        is not consistent in its output file naming (across subtitles, audio, metadata)
        In this interface implementation we use a temp_path and TEMP_FILENAME_FORMAT to 
        specify the the temporary output to be the video_id followed by the correct 
        extension for all resources. This function then converts the temp_path
        to the appropriately named resource, using output_path if specified,
        or a default filename format ({sanitized_title}_{id}).
        """
        video_id = str(metadata["id"])
        if video_id not in str(temp_path):
            raise VideoProcessingError(f"Temporary path '{temp_path}' "
                                       "does not contain video ID '{video_id}'.")
        if not temp_path.suffix:
            raise VideoProcessingError(f"Temporary path '{temp_path}' "
                                       "does not have a file extension.")

        if not output_path:
            new_filename = self.get_default_filename_stem(metadata)
            new_path = Path(str(temp_path).replace(
                TEMP_FILENAME_STR.format(id=video_id), new_filename
                )
            )
            logger.debug(f"Renaming downloaded YT resource to: {new_path}")
            return temp_path.rename(new_path)

        if not output_path.suffix:
            output_path = output_path.with_suffix(temp_path.suffix)
            logger.info(f"Added extension {temp_path.suffix} to output path")
        elif output_path.suffix != temp_path.suffix:
            output_path = output_path.with_suffix(temp_path.suffix)
            logger.warning(f"Replaced output extension with {temp_path.suffix}")
        return temp_path.rename(output_path)

def extract_text_from_ttml(ttml_path: Path) -> str:
    """Extract plain text content from TTML file.

    Args:
        ttml_path: Path to TTML transcript file
        
    Returns:
        Plain text content with one sentence per line
        
    Raises:
        ValueError: If file doesn't exist or has invalid content
    """
    if not ttml_path.exists():
        raise ValueError(f"TTML file not found: {ttml_path}")

    ttml_str = ttml_path.read_text()
    if not ttml_str.strip():
        return ""

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

            if (reader.fieldnames is None 
                or "url" not in reader.fieldnames 
                or "title" not in reader.fieldnames
            ):
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