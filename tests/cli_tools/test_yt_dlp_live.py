import os
import warnings
from pathlib import Path

import pytest

from tnh_scholar.video_processing import DLPDownloader
from tnh_scholar.video_processing.yt_environment import YTDLPEnvironmentInspector


def _load_urls(path: Path) -> list[str]:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def _cleanup_file(path: Path | None) -> None:
    if path and path.exists():
        path.unlink()


@pytest.mark.live_yt
def test_ytt_fetch_transcript_live() -> None:
    if os.environ.get("TNH_YT_LIVE_TESTS") != "1":
        pytest.skip("Set TNH_YT_LIVE_TESTS=1 to run live yt-dlp integration checks.")

    inspector = YTDLPEnvironmentInspector()
    report = inspector.inspect_report()
    if report.has_items():
        for item in report.items:
            warnings.warn(
                f"Preflight {item.severity.value}: {item.code}: {item.message}",
                UserWarning,
                stacklevel=2,
            )

    url_path = Path(
        os.environ.get("TNH_YT_URLS_PATH", "tests/fixtures/yt_dlp/validation_urls.txt")
    )
    urls = _load_urls(url_path)
    assert urls, f"Expected at least one URL in {url_path}"

    dl = DLPDownloader()
    failures = []

    limit_env = os.environ.get("TNH_YT_URL_LIMIT")
    limit = int(limit_env) if limit_env and limit_env.isdigit() else None
    for url in urls if limit is None else urls[:limit]:
        transcript_path = None
        try:
            result = dl.get_transcript(url, lang="en", output_path=None)
            transcript_path = result.filepath
            assert transcript_path and transcript_path.exists()
        except Exception as exc:  # noqa: BLE001 - collect all failures for batch run
            failures.append(f"{url}: {exc}")
        finally:
            _cleanup_file(transcript_path)

    if failures:
        pytest.fail("Live yt-dlp failures:\n" + "\n".join(failures))
