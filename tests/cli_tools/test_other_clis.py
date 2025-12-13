from __future__ import annotations

import importlib

from click.testing import CliRunner

nfmt_module = importlib.import_module("tnh_scholar.cli_tools.nfmt.nfmt")
srt_translate_module = importlib.import_module("tnh_scholar.cli_tools.srt_translate.srt_translate")
sent_split_module = importlib.import_module("tnh_scholar.cli_tools.sent_split.sent_split")
from tnh_scholar.cli_tools.json_to_srt.json_to_srt import JsonlToSrtConverter, json_to_srt
from tnh_scholar.cli_tools.nfmt.nfmt import nfmt
from tnh_scholar.cli_tools.sent_split.sent_split import sent_split
from tnh_scholar.cli_tools.srt_translate.srt_translate import SrtTranslator, srt_translate
from tnh_scholar.cli_tools.token_count.token_count import token_count_cli


def test_nfmt_happy_path():
    runner = CliRunner()
    result = runner.invoke(nfmt, [], input="a\n\n\nb\n")

    assert result.exit_code == 0
    assert result.output == "a\n\nb\n\n"


def test_nfmt_failure(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(
        nfmt_module, "normalize_newlines", lambda *_: (_ for _ in ()).throw(ValueError("bad"))
    )

    result = runner.invoke(nfmt, [], input="text")

    assert result.exit_code == 1
    assert "Normalization failed" in result.output


def test_token_count_happy_path(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("tnh_scholar.cli_tools.token_count.token_count.token_count", lambda text: 7)

    result = runner.invoke(token_count_cli, [], input="hello")

    assert result.exit_code == 0
    assert result.output.strip() == "7"


def test_token_count_failure(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(
        "tnh_scholar.cli_tools.token_count.token_count.token_count",
        lambda text: (_ for _ in ()).throw(RuntimeError("count failed")),
    )

    result = runner.invoke(token_count_cli, [], input="hello")

    assert result.exit_code == 1
    assert "Token count failed" in result.output


def test_json_to_srt_happy_path(monkeypatch):
    runner = CliRunner()

    called = {"value": False}

    def _convert(self, input_file, output):
        called["value"] = True
        return None

    monkeypatch.setattr(JsonlToSrtConverter, "convert", _convert)

    result = runner.invoke(json_to_srt, [], input='{"text": "hi"}\n')

    assert result.exit_code == 0
    assert called["value"] is True


def test_json_to_srt_failure(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(
        JsonlToSrtConverter, "convert", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    result = runner.invoke(json_to_srt, [], input="{}")

    assert result.exit_code == 1
    assert "Error processing file" in result.output


def test_srt_translate_happy_path(monkeypatch, tmp_path):
    runner = CliRunner()
    input_file = tmp_path / "sample.srt"
    input_file.write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8")

    monkeypatch.setattr(srt_translate_module, "set_pattern", lambda pattern: object())
    monkeypatch.setattr(
        SrtTranslator,
        "translate_and_save",
        lambda self, input_path, output_path: output_path.write_text("ok", encoding="utf-8"),
    )

    result = runner.invoke(
        srt_translate,
        [str(input_file)],
    )

    assert result.exit_code == 0
    assert (tmp_path / "sample_en.srt").read_text(encoding="utf-8") == "ok"


def test_srt_translate_failure(monkeypatch, tmp_path):
    runner = CliRunner()
    input_file = tmp_path / "sample.srt"
    input_file.write_text("content", encoding="utf-8")

    monkeypatch.setattr(srt_translate_module, "set_pattern", lambda pattern: object())
    monkeypatch.setattr(
        SrtTranslator,
        "translate_and_save",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail")),
    )

    result = runner.invoke(
        srt_translate,
        [str(input_file)],
    )

    assert result.exit_code == 1
    assert "Error translating SRT" in result.output


def test_sent_split_happy_path(monkeypatch):
    runner = CliRunner()

    class DummyResult:
        def __init__(self):
            self.text_object = self
            self.stats = {"sentence_count": 2}

        def __str__(self):
            return "first\nsecond"

    monkeypatch.setattr(sent_split_module, "split_text", lambda *a, **k: DummyResult())
    monkeypatch.setattr(sent_split_module, "ensure_nltk_data", lambda *a, **k: None)

    result = runner.invoke(sent_split, [], input="First. Second.")

    assert result.exit_code == 0
    assert "first\nsecond" in result.output


def test_sent_split_failure(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(
        sent_split_module,
        "split_text",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("split fail")),
    )
    monkeypatch.setattr(sent_split_module, "ensure_nltk_data", lambda *a, **k: None)

    result = runner.invoke(sent_split, [], input="Text.")

    assert result.exit_code == 1
    assert "Error processing text" in result.output
