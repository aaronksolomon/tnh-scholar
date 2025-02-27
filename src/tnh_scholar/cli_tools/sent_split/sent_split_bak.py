#!/usr/bin/env python
"""
Simple CLI tool for sentence splitting.

This module provides a command line interface for splitting text into sentences.
Uses NLTK for robust sentence tokenization. Reads from stdin and writes to stdout
by default, with optional file input/output.
"""

import sys
from pathlib import Path
from typing import Optional

import click
import nltk
from nltk.tokenize import sent_tokenize

from tnh_scholar.ai_text_processing import TextObject
from tnh_scholar.metadata import ProcessMetadata
from tnh_scholar.utils.file_utils import (
    path_as_str,
    read_str_from_file,
    write_str_to_file,
)


# Download required NLTK data on first run
def ensure_nltk_data():
    """Ensure NLTK punkt tokenizer is available."""
    try:
        # Try to find the resource
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        # If not found, try downloading
        try:
            nltk.download('punkt', quiet=True)
            # Verify download
            nltk.data.find('tokenizers/punkt')
        except Exception as e:
            raise RuntimeError(
                "Failed to download required NLTK data. "
                "Please run 'python -m nltk.downloader punkt' "
                f"to install manually. Error: {e}"
            ) from e

def process_text(text: TextObject, newline: bool = True) -> None:
    """Split text into sentences using NLTK."""
    ensure_nltk_data()
    sentences = sent_tokenize(text.content)

    new_content = "\n".join(sentences) if newline else " ".join(sentences)
    text.transform(data_str=new_content)

@click.command()
@click.argument(
    "input_file", type=click.Path(exists=True, path_type=Path), required=False
    )
@click.option('-o', '--output', type=click.Path(path_type=Path), required=False,
              help='Output file (default: stdout)')
@click.option('-s', '--space', is_flag=True,
              help='Separate sentences with spaces instead of newlines')
def sent_split(input_file: Optional[Path],
               output: Optional[Path],
               space: bool) -> None:
    """Split text into sentences using NLTK's sentence tokenizer.
    
    Reads from stdin if no input file is specified.
    Writes to stdout if no output file is specified.
    """
    try:
        # Read from file or stdin
        input_text = read_str_from_file(input_file) if input_file else sys.stdin.read()
        
        # Process the text
        text = TextObject.from_str(input_text)
        process_text(text, newline=not space)
        
        process_metadata = ProcessMetadata(
            step="sentence-split",
            processor="NLTK", 
        )
        if input_file:
            process_metadata.update({"source_file": path_as_str(input_file)})
                
        text.transform(process_metadata=process_metadata)
        
        # Write to file or stdout
        if output:
            write_str_to_file(output, str(text))
        else:
            click.echo(text)
        
        if output:
            click.echo(f"Output written to: {output.name}")

    except Exception as e:
        click.echo(f"Error processing text: {e}", err=True)
        sys.exit(1)

def main():
    sent_split()

if __name__ == '__main__':
    main()