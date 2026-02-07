from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from tnh_scholar.video_processing.video_processing import VideoAudio, YTDownloader


@dataclass(frozen=True)
class OpsCheckConfig:
    urls_path: Path
    url_limit: int | None
    output_dir: Path


@dataclass(frozen=True)
class OpsCheckFailure:
    url: str
    reason: str


@dataclass(frozen=True)
class OpsCheckReport:
    successes: int
    failures: tuple[OpsCheckFailure, ...]

    def ok(self) -> bool:
        return not self.failures


class OpsCheckRunner:
    def __init__(self, downloader: YTDownloader, config: OpsCheckConfig) -> None:
        self._downloader = downloader
        self._config = config

    def run(self) -> OpsCheckReport:
        urls = self._load_urls(self._config.urls_path)
        urls = self._limit_urls(urls, self._config.url_limit)
        self._config.output_dir.mkdir(parents=True, exist_ok=True)
        failures: list[OpsCheckFailure] = []
        successes = 0
        for index, url in enumerate(urls):
            result = self._check_url(url, index)
            if result is None:
                successes += 1
            else:
                failures.append(result)
        return OpsCheckReport(successes=successes, failures=tuple(failures))

    def _load_urls(self, path: Path) -> list[str]:
        lines = path.read_text(encoding="utf-8").splitlines()
        urls = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
        if not urls:
            raise ValueError(f"No URLs found in {path}")
        return urls

    def _limit_urls(self, urls: list[str], limit: int | None) -> list[str]:
        return urls if limit is None else urls[: max(limit, 0)]

    def _check_url(self, url: str, index: int) -> OpsCheckFailure | None:
        try:
            self._downloader.get_metadata(url)
            audio = self._download_audio(url, index)
            self._validate_audio(audio)
            self._cleanup_audio(audio)
            return None
        except Exception as exc:  # noqa: BLE001 - live ops check must capture all failures
            return OpsCheckFailure(url=url, reason=str(exc))

    def _download_audio(self, url: str, index: int) -> VideoAudio:
        filename = f"ops_audio_{index}.mp3"
        output_path = self._config.output_dir / filename
        return self._downloader.get_audio(url, output_path=output_path)

    def _validate_audio(self, audio: VideoAudio) -> None:
        if audio.filepath is None:
            raise ValueError("Audio download returned no file path")
        if not audio.filepath.exists():
            raise FileNotFoundError(f"Audio file missing: {audio.filepath}")
        if audio.filepath.stat().st_size <= 0:
            raise ValueError(f"Audio file empty: {audio.filepath}")

    def _cleanup_audio(self, audio: VideoAudio) -> None:
        if audio.filepath and audio.filepath.exists():
            audio.filepath.unlink()
