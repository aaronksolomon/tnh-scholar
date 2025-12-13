from __future__ import annotations

import importlib
import io

from click.testing import CliRunner

from tnh_scholar.cli_tools.tnh_fab import tnh_fab
from tnh_scholar.cli_tools.tnh_fab.tnh_fab import PromptCatalog

tnh_fab_module = importlib.import_module("tnh_scholar.cli_tools.tnh_fab.tnh_fab")


def test_missing_openai_credentials_exits_cleanly(monkeypatch, tmp_path):
    runner = CliRunner()

    monkeypatch.setattr(tnh_fab_module, "check_openai_env", lambda: False)

    sample = tmp_path / "input.txt"
    sample.write_text("content", encoding="utf-8")

    result = runner.invoke(tnh_fab, ["--quiet", "section", str(sample)])

    assert result.exit_code == 1
    assert "Missing OpenAI Credentials." in result.output
    assert "Traceback" not in result.output


def test_section_requires_input_when_no_stdin(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(tnh_fab_module, "check_openai_env", lambda: True)

    stdin = io.StringIO("")
    monkeypatch.setattr(stdin, "isatty", lambda: True)
    monkeypatch.setattr(tnh_fab_module.sys, "stdin", stdin)

    result = runner.invoke(tnh_fab, ["--quiet", "section"])

    assert result.exit_code == 1
    assert "Unable to read input" in result.output
    assert "Traceback" not in result.output


def test_translate_reports_missing_pattern(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(tnh_fab_module, "check_openai_env", lambda: True)

    def _raise_file_not_found(self, pattern_name):
        raise FileNotFoundError(pattern_name)

    monkeypatch.setattr(PromptCatalog, "load", _raise_file_not_found)

    result = runner.invoke(
        tnh_fab,
        ["--quiet", "translate", "--pattern", "missing"],
        input="text to translate",
    )

    assert result.exit_code == 1
    assert "Pattern 'missing' not found" in result.output
    assert "Traceback" not in result.output


def test_process_handles_invalid_section_file(monkeypatch, tmp_path):
    runner = CliRunner()

    monkeypatch.setattr(tnh_fab_module, "check_openai_env", lambda: True)
    monkeypatch.setattr(PromptCatalog, "load", lambda self, name: object())

    invalid_section_file = tmp_path / "sections.json"
    invalid_section_file.write_text("{ invalid json", encoding="utf-8")

    result = runner.invoke(
        tnh_fab,
        ["--quiet", "process", "-p", "format_xml", "-s", str(invalid_section_file)],
        input="content body",
    )

    assert result.exit_code == 1
    assert "Failed to read sections" in result.output
    assert "Traceback" not in result.output


def test_section_happy_path(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(tnh_fab_module, "check_openai_env", lambda: True)
    monkeypatch.setattr(PromptCatalog, "load", lambda self, name: object())

    class DummyInfo:
        def model_dump_json(self, indent=None):
            return '{"ok": true}'

    class DummyText:
        def export_info(self, input_file):
            return DummyInfo()

    monkeypatch.setattr(tnh_fab_module, "find_sections", lambda *args, **kwargs: DummyText())

    result = runner.invoke(tnh_fab, ["--quiet", "section"], input="abc")

    assert result.exit_code == 0
    assert '{"ok": true}' in result.output


def test_translate_happy_path(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(tnh_fab_module, "check_openai_env", lambda: True)
    monkeypatch.setattr(PromptCatalog, "load", lambda self, name: object())
    monkeypatch.setattr(tnh_fab_module, "translate_text_by_lines", lambda *a, **k: "translated")

    result = runner.invoke(tnh_fab, ["--quiet", "translate"], input="abc")

    assert result.exit_code == 0
    assert "translated" in result.output


def test_process_happy_path(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(tnh_fab_module, "check_openai_env", lambda: True)
    monkeypatch.setattr(PromptCatalog, "load", lambda self, name: object())
    monkeypatch.setattr(tnh_fab_module, "process_text", lambda *a, **k: "processed")

    result = runner.invoke(tnh_fab, ["--quiet", "process", "-p", "format_xml"], input="abc")

    assert result.exit_code == 0
    assert "processed" in result.output
