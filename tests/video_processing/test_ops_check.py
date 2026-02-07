from dataclasses import dataclass
from pathlib import Path

import pytest

from tnh_scholar.metadata import Metadata
from tnh_scholar.video_processing.ops_check import (
    OpsCheckConfig,
    OpsCheckRunner,
)
from tnh_scholar.video_processing.video_processing import VideoAudio


@dataclass
class StubDownloader:
    audio_bytes: bytes

    def get_metadata(self, url: str) -> Metadata:
        return Metadata({"id": "x", "title": url})

    def get_audio(self, url: str, output_path: Path, **kwargs) -> VideoAudio:
        output_path.write_bytes(self.audio_bytes)
        return VideoAudio(metadata=Metadata({"id": "x", "title": url}), filepath=output_path)


def _write_urls(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_ops_check_success(tmp_path: Path) -> None:
    urls_path = tmp_path / "urls.txt"
    _write_urls(urls_path, "https://example.com\n")

    config = OpsCheckConfig(
        urls_path=urls_path,
        url_limit=None,
        output_dir=tmp_path / "out",
    )
    runner = OpsCheckRunner(downloader=StubDownloader(audio_bytes=b"data"), config=config)

    report = runner.run()
    assert report.ok() is True
    assert report.successes == 1
    assert report.failures == ()


def test_ops_check_failure(tmp_path: Path) -> None:
    urls_path = tmp_path / "urls.txt"
    _write_urls(urls_path, "https://example.com\n")

    @dataclass
    class FailingDownloader:
        def get_metadata(self, url: str) -> Metadata:
            raise RuntimeError("metadata failed")

    config = OpsCheckConfig(
        urls_path=urls_path,
        url_limit=None,
        output_dir=tmp_path / "out",
    )
    runner = OpsCheckRunner(downloader=FailingDownloader(), config=config)

    report = runner.run()
    assert report.ok() is False
    assert report.successes == 0
    assert len(report.failures) == 1


def test_ops_check_url_limit(tmp_path: Path) -> None:
    urls_path = tmp_path / "urls.txt"
    _write_urls(urls_path, "u1\nu2\n")

    config = OpsCheckConfig(
        urls_path=urls_path,
        url_limit=1,
        output_dir=tmp_path / "out",
    )
    runner = OpsCheckRunner(downloader=StubDownloader(audio_bytes=b"data"), config=config)

    report = runner.run()
    assert report.successes == 1
    assert report.ok() is True


def test_ops_check_empty_urls(tmp_path: Path) -> None:
    urls_path = tmp_path / "urls.txt"
    _write_urls(urls_path, "# comment\n\n")

    config = OpsCheckConfig(
        urls_path=urls_path,
        url_limit=None,
        output_dir=tmp_path / "out",
    )
    runner = OpsCheckRunner(downloader=StubDownloader(audio_bytes=b"data"), config=config)

    with pytest.raises(ValueError):
        runner.run()
