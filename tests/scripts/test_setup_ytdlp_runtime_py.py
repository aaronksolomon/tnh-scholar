from dataclasses import dataclass
from pathlib import Path
import importlib.util
import sys

import pytest


def _load_runtime_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "setup_ytdlp_runtime.py"
    spec = importlib.util.spec_from_file_location("setup_ytdlp_runtime", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runtime = _load_runtime_module()


class FakeWhich:
    def __init__(self, initial: dict[str, str | None]) -> None:
        self._mapping = dict(initial)

    def __call__(self, name: str) -> str | None:
        return self._mapping.get(name)

    def set(self, name: str, value: str | None) -> None:
        self._mapping[name] = value


@dataclass
class FakeResult:
    returncode: int = 0


def test_install_js_runtime_existing() -> None:
    which = FakeWhich({"deno": "/usr/bin/deno"})
    setup = runtime.RuntimeSetup(runner=lambda *a, **k: FakeResult(), which=which, input_func=lambda _: "")
    detected, errors = setup.install_js_runtime(assume_yes=False, no_input=False)
    assert detected is not None
    assert detected.name == "deno"
    assert errors == []


def test_install_js_runtime_with_brew(monkeypatch: pytest.MonkeyPatch) -> None:
    which = FakeWhich({"brew": "/usr/bin/brew", "deno": None})

    def runner(cmd, check=False, **kwargs):
        if cmd[:2] == ["brew", "install"]:
            which.set("deno", "/usr/bin/deno")
        return FakeResult()

    setup = runtime.RuntimeSetup(runner=runner, which=which, input_func=lambda _: "y")
    detected, errors = setup.install_js_runtime(assume_yes=False, no_input=False)
    assert detected is not None
    assert errors == []


def test_install_js_runtime_missing_no_brew() -> None:
    which = FakeWhich({"deno": None, "node": None, "bun": None})
    setup = runtime.RuntimeSetup(runner=lambda *a, **k: FakeResult(), which=which, input_func=lambda _: "")
    detected, errors = setup.install_js_runtime(assume_yes=False, no_input=False)
    assert detected is None
    assert errors == ["JS runtime missing."]


def test_install_curl_cffi_current_env(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = runtime.RuntimeSetup(runner=lambda *a, **k: FakeResult(), which=lambda _: None, input_func=lambda _: "")
    monkeypatch.setattr(setup, "python_has_curl_cffi", lambda: True)
    errors = setup.install_curl_cffi(assume_yes=False, no_input=False)
    assert errors == []


def test_install_curl_cffi_pipx_env(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = runtime.RuntimeSetup(runner=lambda *a, **k: FakeResult(), which=lambda _: "/usr/bin/pipx", input_func=lambda _: "")
    monkeypatch.setattr(setup, "python_has_curl_cffi", lambda: False)
    monkeypatch.setattr(setup, "pipx_has_curl_cffi", lambda: True)
    errors = setup.install_curl_cffi(assume_yes=False, no_input=False)
    assert errors == []


def test_install_curl_cffi_declined(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = runtime.RuntimeSetup(runner=lambda *a, **k: FakeResult(), which=lambda _: None, input_func=lambda _: "n")
    monkeypatch.setattr(setup, "python_has_curl_cffi", lambda: False)
    monkeypatch.setattr(setup, "pipx_has_curl_cffi", lambda: False)
    errors = setup.install_curl_cffi(assume_yes=False, no_input=False)
    assert errors == ["curl_cffi not installed."]


def test_install_curl_cffi_pipx_missing_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    def runner(cmd, check=False, **kwargs):
        if cmd[:1] == ["pipx"]:
            raise FileNotFoundError("pipx")
        return FakeResult()

    setup = runtime.RuntimeSetup(runner=runner, which=lambda _: "/usr/bin/pipx", input_func=lambda _: "y")
    monkeypatch.setattr(setup, "python_has_curl_cffi", lambda: False)
    monkeypatch.setattr(setup, "pipx_has_curl_cffi", lambda: False)
    errors = setup.install_curl_cffi(assume_yes=True, no_input=False)
    assert errors == []


def test_write_config_with_impersonate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    setup = runtime.RuntimeSetup(runner=lambda *a, **k: FakeResult(), which=lambda _: None, input_func=lambda _: "")
    runtime_detection = runtime.RuntimeDetection(name="node", path=Path("/usr/bin/node"))
    curl_status = runtime.CurlCffiStatus(current_env=True, pipx_env=False)

    wrote, message = setup.write_config(runtime_detection, curl_status)
    assert wrote is True
    assert message is None

    config_path = tmp_path / ".config" / "yt-dlp" / "config"
    content = config_path.read_text(encoding="utf-8")
    assert "--js-runtimes node:/usr/bin/node" in content
    assert "--remote-components ejs:github" in content
    assert "--impersonate chrome" in content


def test_run_setup_success(monkeypatch: pytest.MonkeyPatch) -> None:
    @dataclass
    class FakeSetup:
        def install_js_runtime(self, assume_yes, no_input):
            return runtime.RuntimeDetection("deno", Path("/usr/bin/deno")), []

        def install_curl_cffi(self, assume_yes, no_input):
            return []

        def curl_status(self):
            return runtime.CurlCffiStatus(current_env=True, pipx_env=False)

        def write_config(self, runtime_detection, curl_status):
            return True, None

        def print_status(self, runtime_detection, curl_status):
            return None

    monkeypatch.setattr(runtime, "_build_setup", lambda: FakeSetup())
    result = runtime.run_setup(assume_yes=True, no_input=False)
    assert result.ok() is True
    assert result.config_written is True
