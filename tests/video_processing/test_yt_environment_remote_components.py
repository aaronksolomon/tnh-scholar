from pathlib import Path

import pytest

from tnh_scholar.video_processing.yt_environment import YTDLPEnvironmentInspector


def _write_config(home: Path, content: str) -> Path:
    config_path = home / ".config" / "yt-dlp" / "config"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content, encoding="utf-8")
    return config_path


def test_remote_components_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_config(tmp_path, "--js-runtimes node:/usr/bin/node\n")
    inspector = YTDLPEnvironmentInspector()
    report = inspector.inspect_report()
    codes = {item.code for item in report.items}
    assert "missing_remote_components" in codes
    assert inspector.has_remote_components() is False


def test_remote_components_present(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_config(tmp_path, "--remote-components ejs:github\n")
    inspector = YTDLPEnvironmentInspector()
    report = inspector.inspect_report()
    codes = {item.code for item in report.items}
    assert "missing_remote_components" not in codes
    assert inspector.has_remote_components() is True
