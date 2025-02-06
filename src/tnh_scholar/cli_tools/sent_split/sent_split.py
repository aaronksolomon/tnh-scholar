#!/usr/bin/env python
"""
Simple CLI tool for sentence splitting.

This module provides a command line interface for splitting text into sentences.
Uses NLTK for robust sentence tokenization. Reads from stdin and writes to stdout
by default, with optional file input/output.
"""

import sys
from pathlib import Path
from typing import Optional, TextIO

import click
import nltk
from nltk.tokenize import sent_tokenize

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

def process_text(text: str, newline: bool = True) -> str:
    """Split text into sentences using NLTK."""
    ensure_nltk_data()
    sentences = sent_tokenize(text)
    return "\n".join(sentences) if newline else " ".join(sentences)

@click.command()
@click.argument('input_file', type=click.File('r'), required=False)
@click.option('-o', '--output', type=click.File('w'),
              help='Output file (default: stdout)')
@click.option('-s', '--space', is_flag=True,
              help='Separate sentences with spaces instead of newlines')
def sent_split(input_file: Optional[TextIO],
               output: Optional[TextIO],
               space: bool) -> None:
    """Split text into sentences using NLTK's sentence tokenizer.
    
    Reads from stdin if no input file is specified.
    Writes to stdout if no output file is specified.
    """
    try:
        # Read from file or stdin
        input_text = input_file.read() if input_file else sys.stdin.read()
        
        # Process the text
        result = process_text(input_text, newline=not space)
        
        # Write to file or stdout
        output_file = output or sys.stdout
        output_file.write(result)
        
        if output:
            click.echo(f"Output written to: {output.name}")

    except Exception as e:
        click.echo(f"Error processing text: {e}", err=True)
        sys.exit(1)

def main():
    sent_split()

if __name__ == '__main__':
    main()