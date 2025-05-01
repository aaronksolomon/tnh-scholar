#!/usr/bin/env python
"""
Simple CLI tool for converting JSONL transcription files to SRT format.

This module provides a command line interface for transforming JSONL
transcription files (from audio-transcribe) into SRT subtitle format.
"""

import json
import sys
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Tuple

import click

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import write_str_to_file

logger = get_child_logger(__name__)

def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = round(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def parse_jsonl_line(line: str) -> Dict:
    """Parse a single JSONL line into a dictionary."""
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSONL line: {e}")
        return {}

def format_srt_entry(index: int, start: float, end: float, text: str) -> str:
    """Format a single SRT entry."""
    start_str = format_timestamp(start)
    end_str = format_timestamp(end)
    return f"{index}\n{start_str} --> {end_str}\n{text}\n"

def extract_segment_data(segment: Dict) -> Tuple[float, float, str]:
    """Extract timestamp and text data from a segment."""
    start = segment.get("start", 0)
    end = segment.get("end", 0)
    text = segment.get("text", "").strip()
    return start, end, text

def process_segment(segment: Dict, entry_index: int) -> Tuple[str, int]:
    """Process a single segment into SRT format."""
    start, end, text = extract_segment_data(segment)
    
    if not text:
        return "", entry_index
        
    entry = format_srt_entry(entry_index, start, end, text)
    return entry, entry_index + 1

def process_segments_list(segments_list: List[Dict], 
                          entry_index: int) -> Tuple[List[str], int]:
    """Process a list of segments into SRT entries."""
    entries = []
    
    for segment in segments_list:
        entry, entry_index = process_segment(segment, entry_index)
        if entry:
            entries.append(entry)
            
    return entries, entry_index

def get_segments_from_data(data: Dict) -> List[Dict]:
    """Extract segments from a data object."""
    return data["segments"] if "segments" in data else []

def read_input_lines(input_file: TextIO) -> List[str]:
    """Read and filter input lines from file."""
    return [line.strip() for line in input_file if line.strip()]

def process_jsonl_line(line: str, entry_index: int) -> Tuple[List[str], int]:
    """Process a single JSONL line into SRT entries."""
    data = parse_jsonl_line(line)
    if not data:
        return [], entry_index
        
    segments = get_segments_from_data(data)
    return process_segments_list(segments, entry_index)

def process_jsonl_content(lines: List[str]) -> str:
    """Process all JSONL content into SRT format."""
    all_entries = []
    entry_index = 1
    accumulated_time = 0.0  # Track total duration of processed chunks
    
    for line in lines:
        entries, entry_index, chunk_duration = process_jsonl_line(
            line, entry_index, accumulated_time)
        all_entries.extend(entries)
        
        # Add this chunk's duration to accumulated time
        accumulated_time += chunk_duration  
    
    return "\n".join(all_entries)

def handle_output(srt_content: str, output_file: Optional[Path]) -> None:
    """Write SRT content to file or stdout."""
    if output_file:
        write_str_to_file(output_file, srt_content)
        logger.info(f"SRT content written to {output_file}")
    else:
        click.echo(srt_content)

def convert_to_srt(input_file: TextIO, output_file: Optional[Path] = None) -> str:
    """
    Convert a JSONL transcription file to SRT format.
    
    Args:
        input_file: JSONL transcription file to parse
        output_file: Optional output file path
        
    Returns:
        str: SRT formatted content
    """
    input_lines = read_input_lines(input_file)
    srt_content = process_jsonl_content(input_lines)
    handle_output(srt_content, output_file)
    return srt_content

@click.command()
@click.argument("input_file", type=click.File("r"), default="-")
@click.option(
    "-o", 
    "--output", 
    type=click.Path(path_type=Path), 
    help="Output file (default: stdout)"
)
def json_to_srt(input_file: TextIO, output: Optional[Path] = None) -> None:
    """
    Convert JSONL transcription files to SRT subtitle format.
    
    Reads from stdin if no INPUT_FILE is specified.
    Writes to stdout if no output file is specified.
    """
    try:
        convert_to_srt(input_file, output)
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        sys.exit(1)

def main():
    """Entry point for the jsonl-to-srt CLI tool."""
    json_to_srt()

if __name__ == "__main__":
    main()