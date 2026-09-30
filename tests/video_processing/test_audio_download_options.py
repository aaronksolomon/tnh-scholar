from pathlib import Path
from typing import Any, Callable, cast

import pytest
from yt_dlp.utils import DownloadError

from tnh_scholar.video_processing import video_processing
from tnh_scholar.video_processing.video_processing import DLPDownloader


def test_audio_download_uses_bounded_range_and_strict_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeYoutubeDL:
        def __init__(self, options: dict[str, object]) -> None:
            captured.update(options)

        def __enter__(self) -> "FakeYoutubeDL":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def extract_info(self, url: str, download: bool) -> dict[str, str]:
            Path("temp_x.mp3").write_bytes(b"audio")
            return {"id": "x", "title": "Example"}

        def prepare_filename(self, info: dict[str, str]) -> str:
            return "temp_x"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(video_processing.yt_dlp, "YoutubeDL", FakeYoutubeDL)

    DLPDownloader().get_audio("https://example.com", end="15", output_path=tmp_path / "sample.mp3")

    assert captured["ignoreerrors"] is False
    assert captured["force_keyframes_at_cuts"] is True
    range_selector = cast(Callable[[dict[str, Any], Any], Any], captured["download_ranges"])
    ranges = range_selector({"duration": 60}, None)
    assert list(ranges) == [{"start_time": 0.0, "end_time": 15.0}]


def test_audio_download_preserves_ytdlp_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingYoutubeDL:
        def __init__(self, options: dict[str, object]) -> None:
            pass

        def __enter__(self) -> "FailingYoutubeDL":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def extract_info(self, url: str, download: bool) -> None:
            raise DownloadError("HTTP Error 403: Forbidden")

    monkeypatch.setattr(video_processing.yt_dlp, "YoutubeDL", FailingYoutubeDL)

    with pytest.raises(DownloadError, match="HTTP Error 403"):
        DLPDownloader().get_audio("https://example.com", output_path=Path("sample.mp3"))
