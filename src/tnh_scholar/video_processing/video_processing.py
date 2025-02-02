"""
video_processing.py
"""

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from xml.etree.ElementTree import ParseError

import yt_dlp

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import sanitize_filename
from tnh_scholar.utils.file_utils import write_text_to_file

logger = get_child_logger(__name__)

# Core yt-dlp configuration constants
BASE_YDL_OPTIONS = {
    "quiet": True,
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

TEMP_FILENAME_FORMAT = "%(id)s"

class VideoProcessingError(Exception):
    """Base exception for video processing errors."""
    pass

class TranscriptError(VideoProcessingError):
    """Raised for transcript-related errors."""
    pass

class DownloadError(VideoProcessingError):
    """Raised for download-related errors."""
    pass

@dataclass 
class VideoResource:
    """Base class for all video resources."""
    metadata: Dict[str, Any]
    filepath: Optional[Path] = None

class VideoTranscript(VideoResource): 
    pass

class VideoAudio(VideoResource): 
    pass 

class VideoMetadata(VideoResource): 
    pass

class YTDownloader:
    """Abstract base class for YouTube content retrieval."""
    
    def get_transcript(
        self, 
        url: str, 
        lang: str = "en", 
        output_path: Optional[Path] = None) -> VideoTranscript:
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
        output_path: Optional[Path] = None,
        write: bool = True,
        ) -> VideoMetadata:
        """Retrieve video metadata only."""
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
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or BASE_YDL_OPTIONS
        
    def get_metadata(
        self,
        url: str, 
        output_path: Optional[Path] = None,
        write: bool = True,
    ) -> VideoMetadata:
        """
        Get metadata for a YouTube video. 
        Save to JSON file if Write is specified.
        """
        temp_path = Path.cwd() / f"{TEMP_FILENAME_FORMAT}.info.json"
        options = DEFAULT_METADATA_OPTIONS | self.config  | {
            "outtmpl": str(temp_path),
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            if info := ydl.extract_info(url):
                metadata = self._extract_metadata(info)
                
                filepath = None
                
                if write:
                    # Use prepare_filename to get yt-dlp filename.  
                    # For info extraction only, without download
                    # yt-dlp, uses full path with extension.
                    filepath = Path(ydl.prepare_filename(info))
                    write_text_to_file(filepath, json.dumps(metadata, indent=2)) 
                    filepath = self._convert_filename(filepath, info, output_path)
                
                return VideoMetadata(
                        metadata=metadata,
                        filepath=filepath,
                    )
                
            else:
                logger.error(f"Unable to download metadata for {url}.")
                raise DownloadError("No info returned.")
    
    def get_transcript(
        self,
        url: str,
        lang: str = "en",
        output_path: Optional[Path] = None,
    ) -> VideoTranscript:
        """Downloads video transcript in TTML format.

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
        options = DEFAULT_TRANSCRIPT_OPTIONS | self.config |{
            "skip_download": True,
            "subtitleslangs": [lang],
            "outtmpl": str(temp_path),
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            if info := ydl.extract_info(url):
                metadata = self._extract_metadata(info)
                filepath = Path(ydl.prepare_filename(info)).with_suffix(f".{lang}.ttml")
                filepath = self._convert_filename(filepath, info, output_path)
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
        
        if start:
            options["postprocessor_args"].extend(["-ss", start])
            logger.debug(f"Postprocessor start time set to: {start}")
            
        if end:
            options["postprocessor_args"].extend(["-to", end])
            logger.debug(f"Postprocessor end time set to: {end}")

        with yt_dlp.YoutubeDL(options) as ydl:
            if info := ydl.extract_info(url, download=True):
                metadata = self._extract_metadata(info)
                filepath = Path(ydl.prepare_filename(info)).with_suffix(".mp3")
                filepath = self._convert_filename(filepath, info, output_path)
                return VideoAudio(metadata=metadata, filepath=filepath)
            else:
                logger.error("Info not found.")
                raise DownloadError(f"Unable to download {url}.")
            
    def _extract_metadata(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standard metadata fields from yt-dlp info."""
        return {k: info.get(k) for k in DEFAULT_METADATA_FIELDS if k in info}
    
    def _show_info(self, info: Dict[str, Any]) -> None:
        """debug routine for displaying info."""
        for k in info:
            if data := str(info.get(k)):
                if len(data) < 200:
                    print(f"{k}: {data}")
                else:
                    print(f"{k}: {data[:200]} ...")
                  
    def _get_default_filename(self, info: Dict[str, Any]) -> str:
        """
        Generate the object download filename
        """
        video_id = str(info.get('id'))
        sanitized_title = sanitize_filename(str(info.get('title')))
        return f"{sanitized_title}_{video_id}"
    
    def get_default_export_name(self, url) -> str:
        video_data = self.get_metadata(url, write=False)
        info = video_data.metadata
        return self._get_default_filename(info)
        
    def _convert_filename(
        self, 
        temp_path: Path,
        info: Dict[str, Any], 
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
        video_id = str(info.get('id'))
        assert video_id in str(temp_path)  # Must have video_id in actual path.
        assert temp_path.suffix  # Actual path must have suffix.

        if not output_path:
            new_filename = self._get_default_filename(info)
            new_path = Path(str(temp_path).replace(video_id, new_filename))
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
    