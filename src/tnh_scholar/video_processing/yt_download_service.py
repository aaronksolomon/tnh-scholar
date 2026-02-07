from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tnh_scholar.metadata import Metadata
from tnh_scholar.video_processing.video_processing import (
    VideoAudio,
    VideoFile,
    VideoTranscript,
    YTDownloader,
)


@dataclass(frozen=True)
class YTDownloadService:
    """Service wrapper for YouTube download operations.

    Notes:
        Keeps Object-Service protocol alignment; behavior is delegated for now.
    """

    downloader: YTDownloader

    def fetch_transcript(
        self,
        url: str,
        lang: str = "en",
        output_path: Optional[Path] = None,
    ) -> VideoTranscript:
        """Fetch a transcript via the configured downloader."""
        return self.downloader.get_transcript(url, lang=lang, output_path=output_path)

    def fetch_metadata(self, url: str) -> Metadata:
        """Fetch metadata via the configured downloader."""
        return self.downloader.get_metadata(url)

    def fetch_audio(
        self,
        url: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> VideoAudio:
        """Fetch audio via the configured downloader."""
        return self.downloader.get_audio(
            url,
            start=start,
            end=end,
            output_path=output_path,
        )

    def fetch_video(
        self,
        url: str,
        quality: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> VideoFile:
        """Fetch video via the configured downloader."""
        return self.downloader.get_video(
            url,
            quality=quality,
            output_path=output_path,
        )
