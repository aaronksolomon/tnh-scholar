from pathlib import Path

import pytest

from tnh_scholar.video_processing.video_processing import DLPDownloader
from tnh_scholar.video_processing.yt_environment import JsRuntime


def test_runtime_options_added(monkeypatch: pytest.MonkeyPatch) -> None:
    downloader = DLPDownloader()
    runtime = JsRuntime(name="node", path=Path("/usr/local/bin/node"))
    monkeypatch.setattr(downloader._runtime_inspector, "resolve_js_runtime", lambda: runtime)
    monkeypatch.setattr(downloader._runtime_inspector, "has_remote_components", lambda: True)

    options = downloader._runtime_options()
    assert options == {
        "js_runtimes": {"node": {"path": "/usr/local/bin/node"}},
        "remote_components": ["ejs:github"],
    }
