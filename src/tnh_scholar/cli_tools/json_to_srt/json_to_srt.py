#!/usr/bin/env python
"""
Simple CLI tool for converting JSONL transcription files to SRT format.

This module provides a command line interface for transforming JSONL
transcription files (from audio-transcribe) into SRT subtitle format.
Handles chunked transcriptions with proper timestamp accumulation.
"""

import json
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, TextIO, Tuple

import click

from tnh_scholar.cli_tools.utils import run_or_fail
from tnh_scholar.logging_config import get_child_logger, setup_logging
from tnh_scholar.utils.file_utils import write_str_to_file

setup_logging()
logger = get_child_logger(__name__)


class JsonlToSrtConverter:
    """Converts JSONL transcription files from audio-transcribe to SRT format."""

    def __init__(self):
        """Initialize converter state."""
        self.entry_index = 1
        self.accumulated_time = 0.0

    def format_timestamp(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = round(td.microseconds / 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def parse_jsonl_line(self, line: str) -> Dict:
        """Parse a single JSONL line into a dictionary."""
        try:
            return json.loads(line.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSONL line: {e}")
            return {}

    def build_srt_entry(self, index: int, start: float, end: float, text: str) -> str:
        """Format a single SRT entry."""
        start_str = self.format_timestamp(start)
        end_str = self.format_timestamp(end)
        return f"{index}\n{start_str} --> {end_str}\n{text}\n"

    def extract_segment_data(self, segment: Dict) -> Tuple[float, float, str]:
        """Extract timestamp and text data from a segment."""
        start = segment.get("start", 0) + self.accumulated_time
        end = segment.get("end", 0) + self.accumulated_time
        text = segment.get("text", "").strip()
        return start, end, text

    def process_segment(self, segment: Dict) -> Optional[str]:
        """Process a single segment into SRT format."""
        start, end, text = self.extract_segment_data(segment)

        if not text:
            return None

        entry = self.build_srt_entry(self.entry_index, start, end, text)
        self.entry_index += 1
        return entry

    def process_segments_list(self, segments_list: List[Dict]) -> List[str]:
        """Process a list of segments into SRT entries."""
        entries = []

        for segment in segments_list:
            if entry := self.process_segment(segment):
                entries.append(entry)

        return entries

    def get_segments_from_data(self, data: Dict) -> List[Dict]:
        """Extract segments from a data object."""
        return data.get("segments", [])

    def read_input_lines(self, input_file: TextIO) -> List[str]:
        """Read and filter input lines from file."""
        return [line.strip() for line in input_file if line.strip()]

    def process_jsonl_line(self, line: str) -> List[str]:
        """Process a single JSONL line into SRT entries."""
        data = self.parse_jsonl_line(line)
        if not data:
            return []

        # Extract duration for accumulation
        chunk_duration = data.get("duration", 0.0)

        segments = self.get_segments_from_data(data)
        entries = self.process_segments_list(segments)

        # Update accumulated time after processing this chunk
        self.accumulated_time += chunk_duration
        return entries

    def process_jsonl_content(self, lines: List[str]) -> str:
        """Process all JSONL content into SRT format."""
        all_entries = []

        for line in lines:
            entries = self.process_jsonl_line(line)
            all_entries.extend(entries)

        return "\n".join(all_entries)

    def handle_output(self, srt_content: str, output_file: Optional[Path]) -> None:
        """Write SRT content to file or stdout."""
        if output_file:
            write_str_to_file(output_file, srt_content, overwrite=True)
            logger.info(f"SRT content written to {output_file}")
        else:
            click.echo(srt_content)

    def convert(self, input_file: TextIO, output_file: Optional[Path] = None) -> str:
        """
        Convert a JSONL transcription file to SRT format.

        Args:
            input_file: JSONL transcription file to parse
            output_file: Optional output file path

        Returns:
            str: SRT formatted content
        """
        input_lines = self.read_input_lines(input_file)
        srt_content = self.process_jsonl_content(input_lines)
        self.handle_output(srt_content, output_file)
        return srt_content


@click.command()
@click.argument("input_file", type=click.File("r"), default="-")
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output file (default: stdout)")
def json_to_srt(input_file: TextIO, output: Optional[Path] = None) -> None:
    """
    Convert JSONL transcription files to SRT subtitle format.

    Reads from stdin if no INPUT_FILE is specified.
    Writes to stdout if no output file is specified.
    """

    def _convert() -> None:
        converter = JsonlToSrtConverter()
        converter.convert(input_file, output)

    run_or_fail("Error processing file", _convert)


def main():
    """Entry point for the jsonl-to-srt CLI tool."""
    json_to_srt()


if __name__ == "__main__":
    main()
