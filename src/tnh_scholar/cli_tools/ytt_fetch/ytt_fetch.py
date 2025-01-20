#!/usr/bin/env python
"""
Simple CLI tool for retrieving video transcripts.

This module provides a command line interface for downloading video transcripts
in specified languages. It uses yt-dlp for video info extraction.
"""

import sys
from pathlib import Path
from typing import Optional

import click
import yt_dlp

from tnh_scholar.utils.file_utils import write_text_to_file
from tnh_scholar.video_processing import TranscriptNotFoundError, get_transcript


@click.command()
@click.argument("url")
@click.option(
    "-l", "--lang", default="en", help="Language code for transcript (default: en)"
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Save transcript text to file instead of printing",
)
def ytt_fetch(url: str, lang: str, output: Optional[str]) -> None:
    """
    Youtube Transcript Fetch: Retrieve and save transcript for a Youtube video using yt-dlp.
    """

    try:
        transcript_text = get_transcript(url, lang)

    except TranscriptNotFoundError as e:
        click.echo(e, err=True)
        sys.exit(1)
    except yt_dlp.utils.DownloadError as e:
        click.echo(f"Failed to extract video transcript: {e}", err=True)
        sys.exit(1)

    try:
        if output:
            output_path = Path(output)
            write_text_to_file(output_path, transcript_text, overwrite=True)
            click.echo(f"Transcript written to: {output_path}")
        else:
            click.echo(transcript_text)

    except FileNotFoundError as e:
        click.echo(f"File not found error: {e}", err=True)
        sys.exit(1)
    except (IOError, OSError) as e:
        click.echo(f"Error writing transcript to file: {e}", err=True)
        sys.exit(1)
    except TypeError as e:
        click.echo(f"Unexpected type error: {e}", err=True)
        sys.exit(1)


def main():
    ytt_fetch()


if __name__ == "__main__":
    main()
