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

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.metadata import Frontmatter, Metadata
from tnh_scholar.metadata.metadata import ProcessMetadata
from tnh_scholar.utils.file_utils import write_str_to_file
from tnh_scholar.video_processing import (
    DLPDownloader,
    TranscriptError,
    extract_text_from_ttml,
)

logger = get_child_logger(__name__)

@click.command()
@click.argument("url")
@click.option(
    "-l", "--lang", default="en", help="Language code for transcript (default: en)"
)
@click.option(
    "-k", "--keep",
    is_flag=True,
    help="Keep downloaded datafile: TTML transcript."
)
@click.option(
    "-i", "--info",
    is_flag=True,
    help="Return only metadata in YAML frontmatter format." 
    )
@click.option(
    "-n", "--no-embed",
    is_flag=True,
    help="Do not embed metadata in transcript file."
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Save transcript text to file instead of printing.",
)
def ytt_fetch(
    url: str, 
    lang: str, 
    keep: bool, 
    info: bool,
    no_embed: bool,
    output: Optional[str]) -> None:
    """
    YouTube Transcript Fetch: Retrieve and 
    save transcripts for a Youtube video using yt-dlp.
    """

    dl = DLPDownloader()
    
    output_path = Path(output) if output else None
    
    if not info:  
        generate_transcript(dl, url, lang, keep, no_embed, output_path)
    else:
        generate_metadata(dl, url, keep, output_path)
            
def generate_metadata(
    dl: DLPDownloader, 
    url: str, 
    keep: bool,
    output_path: Optional[Path]
    ) -> None:
    metadata = dl.get_metadata(url)
    metadata_out = metadata.text_embed("") # Only metadata
    
    export_data(output_path, metadata_out)

def generate_transcript(
    dl: DLPDownloader, 
    url: str, 
    lang: str, 
    keep: bool, 
    no_embed: bool,
    output_path: Optional[Path]
    ) -> None:
    
    metadata, ttml_path = get_ttml_download(dl, url, lang, output_path)
    
    process_metadata = ProcessMetadata(
            step="generate_transcript",
            processor="DLPDownloader",
            tool="ytt-fetch"
            )
    if output_path:
        process_metadata.update(output_path=output_path)
        
    metadata.add_process_info(process_metadata)
            
    export_ttml_data(metadata, ttml_path, no_embed, output_path, keep)
     
def export_ttml_data(
    metadata: Metadata, 
    ttml_path: Optional[Path], 
    no_embed: bool, 
    output_path: Optional[Path], 
    keep: bool):
    try:
        # export transcript as text 
        if ttml_path:
            transcript_text = extract_text_from_ttml(ttml_path)
        else:
            click.echo("Transcript Error. No ttml file found.")
            sys.exit(1)
        
        if not no_embed:
            transcript_text = Frontmatter.embed(metadata, transcript_text)

        export_data(output_path, transcript_text)   
        cleanup_files(keep, ttml_path)

    except FileNotFoundError as e:
        click.echo(f"File not found error: {e}", err=True)
        sys.exit(1)
    except (IOError, OSError) as e:
        click.echo(f"Error writing transcript to file: {e}", err=True)
        sys.exit(1)
    except TypeError as e:
        click.echo(f"Type error: {e}", err=True)
        sys.exit(1)

def get_ttml_download(dl, url, lang, output_path):
    try:
        transcript_data = dl.get_transcript(url, lang, output_path)
        metadata = transcript_data.metadata
        ttml_path = transcript_data.filepath
            
    except TranscriptError as e:
        click.echo(f"Transcript error {e}", err=True)
        sys.exit(1)
    except yt_dlp.utils.DownloadError as e:
        click.echo(f"Failed to extract video transcript: {e}", err=True)
        sys.exit(1)   
        
    return metadata, ttml_path

def cleanup_files(keep: bool, filepath: Path) -> None:
    if not keep:
        filepath.unlink()
        logger.debug(f"Removed local data file: {filepath}")
        
def export_data(output_path, data):
    if output_path:
            write_str_to_file(output_path, data, overwrite=True)
            click.echo(f"Data written to: {output_path}")
    else:
        click.echo(data)
        
def main():
    ytt_fetch()

if __name__ == "__main__":
    main()
