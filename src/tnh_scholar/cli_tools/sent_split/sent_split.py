#!/usr/bin/env python
"""
Simple CLI tool for sentence splitting.

This module provides a command line interface for splitting text into sentences.
Uses NLTK for robust sentence tokenization. Reads from stdin and writes to stdout
by default, with optional file input/output.
"""

#!/usr/bin/env python
import sys
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import click
import nltk
from attr import dataclass
from nltk.tokenize import sent_tokenize
from pydantic import BaseModel

from tnh_scholar.ai_text_processing import TextObject
from tnh_scholar.cli_tools.utils import run_or_fail
from tnh_scholar.metadata import ProcessMetadata
from tnh_scholar.utils.file_utils import read_str_from_file, write_str_to_file


class SplitConfig(BaseModel):
    separator: Literal["space", "newline"] = "newline"
    nltk_tokenizer: str = "punkt"


@dataclass
class SplitResult:
    text_object: TextObject
    stats: Dict[str, Any] = {}


class SplitIOData(BaseModel):
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    content: Optional[str] = None

    @classmethod
    def from_io(cls, input_file: Optional[Path], output: Optional[Path]) -> "SplitIOData":
        return cls(input_path=input_file, output_path=output)

    def get_input_content(self) -> str:
        if self.content is not None:
            return self.content
        return read_str_from_file(self.input_path) if self.input_path else sys.stdin.read()

    def write_output(self, result: SplitResult) -> None:
        text = result.text_object
        output_str = str(text)
        if self.output_path:
            write_str_to_file(self.output_path, output_str)
            click.echo(f"Output written to: {self.output_path.name}")
            click.echo(f"Split into {result.stats['sentence_count']} sentences.")
        else:
            click.echo(output_str)


def ensure_nltk_data(config: SplitConfig) -> None:
    try:
        nltk.data.find(f"tokenizers/{config.nltk_tokenizer}")
    except LookupError:
        try:
            nltk.download(config.nltk_tokenizer, quiet=True)
            nltk.data.find(f"tokenizers/{config.nltk_tokenizer}")
        except Exception as e:
            raise RuntimeError(
                f"Failed to download required NLTK data. "
                f"Please run 'python -m nltk.downloader {config.nltk_tokenizer}' "
                f"to install manually. Error: {e}"
            ) from e


def split_text(text: TextObject, config: SplitConfig, io_data: SplitIOData) -> SplitResult:
    ensure_nltk_data(config)
    sentences = sent_tokenize(text.content)

    separator = "\n" if config.separator == "newline" else " "
    new_content = separator.join(sentences)

    text.transform(
        data_str=new_content,
        process_metadata=ProcessMetadata(
            step="split_text",
            processor="NLTK",
            tool="sent-split",
            source_file=io_data.input_path or None,
        ),
    )

    return SplitResult(text_object=text, stats={"sentence_count": len(sentences)})


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path), required=False)
@click.option(
    "-o", "--output", type=click.Path(path_type=Path), required=False, help="Output file (default: stdout)"
)
@click.option("-s", "--space", is_flag=True, help="Separate sentences with spaces instead of newlines")
def sent_split(input_file: Optional[Path], output: Optional[Path], space: bool) -> None:
    def _run_split() -> None:
        io_data = SplitIOData.from_io(input_file, output)
        config = SplitConfig(separator="space" if space else "newline")

        input_text = io_data.get_input_content()
        text = TextObject.from_str(input_text)

        result = split_text(text, config, io_data)
        io_data.write_output(result)

    run_or_fail("Error processing text", _run_split)


def main():
    sent_split()


if __name__ == "__main__":
    main()
