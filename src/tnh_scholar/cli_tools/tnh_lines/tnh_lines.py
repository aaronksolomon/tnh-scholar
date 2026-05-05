from __future__ import annotations

from pathlib import Path

import typer

from tnh_scholar.text_processing.numbered_text import NumberedText
from tnh_scholar.utils.file_utils import write_str_to_file

app = typer.Typer(
    name="tnh-lines",
    help="Prepare numbered text for sectioning workflows and convert it back to plain text.",
    add_completion=False,
    no_args_is_help=True,
)


def _write_output(output_file: Path, text: str, *, overwrite: bool) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    write_str_to_file(output_file, text, overwrite=overwrite)


@app.command("number")
def number_command(
    input_file: Path = typer.Argument(..., help="Plain text source file."),
    output_file: Path = typer.Argument(..., help="Numbered output path."),
    start: int = typer.Option(1, "--start", help="Starting line number."),
    separator: str = typer.Option(":", "--separator", help="Line-number separator."),
    no_clobber: bool = typer.Option(
        False,
        "--no-clobber",
        help="Fail if the output file already exists.",
    ),
) -> None:
    """Write numbered text in N:LINE format."""
    document = NumberedText.from_file(input_file, start=start, separator=separator)
    _write_output(output_file, document.numbered_content, overwrite=not no_clobber)


@app.command("unnumber")
def unnumber_command(
    input_file: Path = typer.Argument(..., help="Numbered source file."),
    output_file: Path = typer.Argument(..., help="Plain-text output path."),
    no_clobber: bool = typer.Option(
        False,
        "--no-clobber",
        help="Fail if the output file already exists.",
    ),
) -> None:
    """Strip numbering and write plain text."""
    document = NumberedText.from_file(input_file)
    _write_output(output_file, document.content, overwrite=not no_clobber)


def main() -> None:
    """Dispatch execution to the Typer application."""
    app()


if __name__ == "__main__":
    main()
