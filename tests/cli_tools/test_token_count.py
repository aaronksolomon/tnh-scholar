from __future__ import annotations

from click.testing import CliRunner

from tnh_scholar.cli_tools.token_count.token_count import token_count_cli


def test_token_count_cli_reads_file(monkeypatch, tmp_path):
    runner = CliRunner()
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("hello world", encoding="utf-8")

    monkeypatch.setattr(
        "tnh_scholar.cli_tools.token_count.token_count.token_count",
        lambda text: 42,
    )

    result = runner.invoke(token_count_cli, [str(sample_file)])

    assert result.exit_code == 0
    assert result.output.strip() == "42"
