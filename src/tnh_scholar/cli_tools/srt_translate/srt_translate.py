#!/usr/bin/env python
"""
CLI tool for translating SRT subtitle files using tnh-scholar line translation.

This module provides a command line interface for translating SRT subtitle files
from one language to another while preserving timecodes and subtitle structure.
Uses the same translation engine as tnh-fab translate.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click

from tnh_scholar.ai_text_processing import TextObject, get_pattern
from tnh_scholar.ai_text_processing.line_translator import translate_text_by_lines
from tnh_scholar.ai_text_processing.prompts import Prompt
from tnh_scholar.cli_tools.utils import run_or_fail
from tnh_scholar.logging_config import get_child_logger, setup_logging
from tnh_scholar.metadata.metadata import Frontmatter, Metadata
from tnh_scholar.utils.file_utils import read_str_from_file, write_str_to_file

logger = get_child_logger(__name__)


class SrtEntry:
    """Represents a single subtitle entry from an SRT file."""

    def __init__(self, index: int, start_time: str, end_time: str, text: str):
        """Initialize subtitle entry with timing and text."""
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text.strip()

    def __str__(self) -> str:
        """Format entry as SRT text."""
        return f"{self.index}\n{self.start_time} --> {self.end_time}\n{self.text}\n"

    @property
    def line_key(self) -> str:
        """Generate a unique line key for this entry."""
        return f"{self.index}"


class SrtTranslator:
    """Translates SRT files while preserving timecodes."""

    def __init__(
        self,
        source_language: Optional[str] = None,
        target_language: str = "en",
        pattern: Optional[Prompt] = None,
        model: Optional[str] = None,
        metadata: Optional[Metadata] = None,
    ):
        """Initialize translator with language, model settings, and metadata."""
        self.source_language = source_language
        self.target_language = target_language
        self.pattern = pattern
        self.model = model
        self.metadata = metadata

    def parse_srt(self, content: str) -> List[SrtEntry]:
        """Parse SRT content into structured entries."""
        # Pattern matches: index, start time, end time, and multiline text
        pattern = r"(\d+)\r?\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\r?\n((?:.+(?:\r?\n))+)(?:\r?\n)?"  # noqa: E501
        matches = re.findall(pattern, content, re.MULTILINE)

        entries = []
        for match in matches:
            index = int(match[0])
            start_time = match[1]
            end_time = match[2]
            text = match[3].strip()
            entries.append(SrtEntry(index, start_time, end_time, text))

        logger.info(f"Parsed {len(entries)} subtitle entries")
        return entries

    def entries_to_numbered_text(self, entries: List[SrtEntry]) -> str:
        """Convert SRT entries to numbered text for TextObject."""
        lines = []
        lines.extend(f"{entry.text}" for entry in entries)
        return "\n".join(lines)

    def create_text_object(self, text: str) -> TextObject:
        """Create a TextObject from the extracted SRT text with metadata."""
        return TextObject.from_str(text, language=self.source_language, metadata=self.metadata)

    def translate_text_object(self, text_object: TextObject) -> TextObject:
        """Translate the TextObject using line translation."""
        text_obj = translate_text_by_lines(
            text_object,
            source_language=self.source_language,
            target_language=self.target_language,
            pattern=self.pattern,
            model=self.model,
        )
        logger.debug(f"Text generated: \n{text_obj}")
        return text_obj

    def extract_translated_lines(self, translated_object: TextObject) -> Dict[str, str]:
        """Extract translated lines from TextObject with line keys."""
        # Get the properly numbered content instead of raw content
        numbered_translation = translated_object.numbered_content
        logger.debug(f"Numbered translated text sample :\n{numbered_translation[:500]}...")

        # Pattern matches line numbers and their text,
        # accounting for the numbering format.
        # This depends on a consistent pattern for the lines.
        # This pattern will match the format like "1: Translated text"
        pattern = rf"(\d+){re.escape(translated_object.num_text.separator)}(.*)"

        translations = {}
        for line in numbered_translation.splitlines():
            if match := re.match(pattern, line):
                line_key = match[1]
                text = match[2].strip()
                translations[line_key] = text
                logger.debug(f"Found translation for key {line_key}: {text[:50]}...")

        logger.debug(f"Extracted {len(translations)} translations")
        return translations

    def update_entries_with_translations(
        self, entries: List[SrtEntry], translations: Dict[str, str]
    ) -> List[SrtEntry]:
        """Apply translations to original entries."""
        updated_entries = []
        for entry in entries:
            # Look up translation by line key
            if entry.line_key in translations:
                entry.text = translations[entry.line_key]
            updated_entries.append(entry)

        return updated_entries

    def format_srt(self, entries: List[SrtEntry]) -> str:
        """Format entries back to SRT content."""
        return "\n".join(str(entry) for entry in entries)

    def translate_srt(self, content: str) -> str:
        """Process SRT content through complete translation pipeline."""
        entries = self.parse_srt(content)
        numbered_text = self.entries_to_numbered_text(entries)
        text_object = self.create_text_object(numbered_text)

        logger.info(f"Translating from {self.source_language or 'auto-detected'} to {self.target_language}")
        translated_object = self.translate_text_object(text_object)

        translations = self.extract_translated_lines(translated_object)
        updated_entries = self.update_entries_with_translations(entries, translations)

        return self.format_srt(updated_entries)

    def translate_and_save(self, input_file: Path, output_path: Path):
        """Handles file reading, translation, and saving."""

        content = read_str_from_file(input_file)
        logger.info(f"Reading SRT file: {input_file}")

        translated_content = self.translate_srt(content)

        write_str_to_file(output_path, translated_content, overwrite=True)
        logger.info(f"Translated SRT written to: {output_path}")


def set_pattern(pattern: Optional[str]):
    pattern_obj = None
    if pattern:
        try:
            pattern_obj = get_pattern(pattern)
        except Exception as e:
            logger.error(f"Failed to load pattern '{pattern}': {e}")
            sys.exit(1)
    return pattern_obj


def set_output_path(input_file: Path, output: Optional[Path], target_language):
    if not output:
        lang_suffix = target_language
        return input_file.with_stem(f"{input_file.stem}_{lang_suffix}")
    return output


def load_metadata_from_file(metadata_file: Optional[Path]) -> Optional[Metadata]:
    """Load metadata from a file if provided."""
    if not metadata_file:
        return None

    try:
        metadata, _ = Frontmatter.extract_from_file(metadata_file)
        logger.info(f"Loaded metadata from {metadata_file}")
        return metadata
    except FileNotFoundError:
        logger.error(f"Metadata file not found: {metadata_file}")
        exit(1)
    except Exception as e:
        logger.error(f"Failed to load metadata from {metadata_file}: {e}")
        exit(1)


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output file path (default: adds language suffix to input filename)",
)
@click.option("-s", "--source-language", help="Source language code (auto-detected if not specified)")
@click.option("-t", "--target-language", default="en", help="Target language code (default: en)")
@click.option("-m", "--model", help="Optional model name to use for translation")
@click.option("-p", "--pattern", help="Optional translation pattern name")
@click.option("-g", "--debug", is_flag=True, help="Option to show debug output.")
@click.option(
    "-d",
    "--metadata",
    type=click.Path(exists=True, path_type=Path),
    help="Path to file with YAML metadata as frontmatter, providing translation context",
)
def srt_translate(
    input_file: Path,
    output: Optional[Path] = None,
    source_language: Optional[str] = None,
    target_language: str = "en",
    model: Optional[str] = None,
    pattern: Optional[str] = None,
    debug: Optional[bool] = False,
    metadata: Optional[Path] = None,
) -> None:
    """
    Translate SRT subtitle files from one language to another.

    INPUT_FILE is the path to the SRT file to translate.
    """

    if debug:
        setup_logging(log_level=logging.DEBUG)
    else:
        setup_logging()

    def _translate() -> None:
        output_path = set_output_path(input_file, output, target_language)
        pattern_obj = set_pattern(pattern)
        if metadata_obj := load_metadata_from_file(metadata):
            logger.info(f"Using metadata for translation context from: {metadata}")
        translator = SrtTranslator(
            source_language=source_language,
            target_language=target_language,
            pattern=pattern_obj,
            model=model,
            metadata=metadata_obj,
        )
        translator.translate_and_save(input_file, output_path)

    run_or_fail("Error translating SRT", _translate)


def main():
    """Entry point for the srt-translate CLI tool."""
    srt_translate()


if __name__ == "__main__":
    main()
