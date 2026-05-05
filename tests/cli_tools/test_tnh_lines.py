from pathlib import Path

from typer.testing import CliRunner

from tnh_scholar.cli_tools.tnh_lines import tnh_lines

runner = CliRunner(mix_stderr=False)


def test_tnh_lines_number_command_writes_numbered_output(tmp_path: Path):
    input_file = tmp_path / "plain.txt"
    output_file = tmp_path / "numbered.txt"
    input_file.write_text("alpha\nbeta\n", encoding="utf-8")

    result = runner.invoke(
        tnh_lines.app,
        ["number", str(input_file), str(output_file)],
    )

    assert result.exit_code == 0, result.output
    assert output_file.read_text(encoding="utf-8") == "1:alpha\n2:beta"


def test_tnh_lines_unnumber_command_overwrites_by_default(tmp_path: Path):
    input_file = tmp_path / "numbered.txt"
    output_file = tmp_path / "plain.txt"
    input_file.write_text("1:alpha\n2:beta", encoding="utf-8")
    output_file.write_text("stale", encoding="utf-8")

    result = runner.invoke(
        tnh_lines.app,
        ["unnumber", str(input_file), str(output_file)],
    )

    assert result.exit_code == 0, result.output
    assert output_file.read_text(encoding="utf-8") == "alpha\nbeta"


def test_tnh_lines_number_command_respects_no_clobber(tmp_path: Path):
    input_file = tmp_path / "plain.txt"
    output_file = tmp_path / "numbered.txt"
    input_file.write_text("alpha\nbeta\n", encoding="utf-8")
    output_file.write_text("existing", encoding="utf-8")

    result = runner.invoke(
        tnh_lines.app,
        ["number", str(input_file), str(output_file), "--no-clobber"],
    )

    assert result.exit_code != 0
    assert output_file.read_text(encoding="utf-8") == "existing"
