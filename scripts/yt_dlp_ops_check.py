import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tnh_scholar.video_processing.ops_check import OpsCheckConfig, OpsCheckRunner
from tnh_scholar.video_processing.video_processing import DLPDownloader


@dataclass(frozen=True)
class OpsRunConfig:
    repo_root: Path
    log_path: Path
    urls_path: Path
    url_limit: int | None
    output_dir: Path


def _build_config() -> OpsRunConfig:
    repo_root = Path(__file__).resolve().parents[1]
    log_path = repo_root / "logs" / "yt_dlp_ops_check.log"
    urls_path = Path(os.environ.get("TNH_YT_URLS_PATH", "tests/fixtures/yt_dlp/validation_urls.txt"))
    url_limit = _parse_limit(os.environ.get("TNH_YT_URL_LIMIT"))
    output_dir = Path(os.environ.get("TNH_YT_OUTPUT_DIR", "tmp/yt_dlp_ops"))
    return OpsRunConfig(
        repo_root=repo_root,
        log_path=log_path,
        urls_path=urls_path,
        url_limit=url_limit,
        output_dir=repo_root / output_dir,
    )


def _parse_limit(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        limit = int(value)
    except ValueError:
        return None
    return limit if limit > 0 else None


def _run_ops(config: OpsRunConfig) -> tuple[int, str]:
    runner = OpsCheckRunner(
        downloader=DLPDownloader(),
        config=OpsCheckConfig(
            urls_path=config.urls_path,
            url_limit=config.url_limit,
            output_dir=config.output_dir,
        ),
    )
    report = runner.run()
    output = _format_report(report)
    return (0 if report.ok() else 1, output)


def _format_report(report) -> str:
    lines = [
        f"successes={report.successes}",
        f"failures={len(report.failures)}",
    ]
    lines.extend(
        f"failure_url={failure.url} reason={failure.reason}"
        for failure in report.failures
    )
    return "\n".join(lines)


def _append_log(log_path: Path, output: str) -> None:
    timestamp = datetime.now().isoformat()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n[{timestamp}] yt-dlp ops check\n")
        handle.write(output)
        handle.write("\n")


def main() -> None:
    config = _build_config()
    try:
        exit_code, output = _run_ops(config)
    except Exception as exc:  # noqa: BLE001 - ops script should capture failures
        exit_code = 1
        output = f"error={exc}"
    _append_log(config.log_path, output)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
