from pathlib import Path

import pytest

from tnh_scholar.metadata import Metadata
from tnh_scholar.video_processing import DLPDownloader, VideoProcessingError


def test_convert_filename_renames_to_title(tmp_path: Path) -> None:
    downloader = DLPDownloader()
    metadata = Metadata({"id": "abc123", "title": "Sample Title"})

    temp_path = tmp_path / "temp_abc123.mp3"
    temp_path.write_text("data", encoding="utf-8")

    new_path = downloader._convert_filename(temp_path, metadata, output_path=None)
    assert new_path.exists()
    assert new_path.name.startswith("sample_title")
    assert new_path.suffix == ".mp3"


def test_convert_filename_requires_id_in_temp_path(tmp_path: Path) -> None:
    downloader = DLPDownloader()
    metadata = Metadata({"id": "abc123", "title": "Sample Title"})

    temp_path = tmp_path / "temp_other.mp3"
    temp_path.write_text("data", encoding="utf-8")

    with pytest.raises(VideoProcessingError):
        downloader._convert_filename(temp_path, metadata, output_path=None)
