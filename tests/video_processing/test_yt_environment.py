from pathlib import Path

import pytest

from tnh_scholar.video_processing.yt_environment import JsRuntime, YTDLPEnvironmentInspector


def _write_config(home: Path, content: str) -> Path:
    config_path = home / ".config" / "yt-dlp" / "config"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content, encoding="utf-8")
    return config_path


def test_resolve_js_runtime_from_config_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runtime_path = tmp_path / "bin" / "node"
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_text("", encoding="utf-8")

    monkeypatch.setenv("HOME", str(tmp_path))
    _write_config(tmp_path, f"--js-runtimes node:{runtime_path}\n")

    inspector = YTDLPEnvironmentInspector()
    runtime = inspector.resolve_js_runtime()
    assert runtime == JsRuntime(name="node", path=runtime_path)


def test_resolve_js_runtime_from_config_name(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runtime_path = tmp_path / "bin" / "node"
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_text("", encoding="utf-8")
    runtime_path.chmod(0o755)

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", f"{runtime_path.parent}")
    _write_config(tmp_path, "--js-runtimes node\n")

    inspector = YTDLPEnvironmentInspector()
    runtime = inspector.resolve_js_runtime()
    assert runtime == JsRuntime(name="node", path=runtime_path)


def test_resolve_js_runtime_from_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runtime_path = tmp_path / "bin" / "deno"
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_text("", encoding="utf-8")
    runtime_path.chmod(0o755)

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", f"{runtime_path.parent}")

    inspector = YTDLPEnvironmentInspector()
    runtime = inspector.resolve_js_runtime()
    assert runtime == JsRuntime(name="deno", path=runtime_path)
