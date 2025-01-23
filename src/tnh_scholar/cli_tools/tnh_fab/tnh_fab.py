#!/usr/bin/env python
"""
TNH-FAB Command Line Interface

Part of the THICH NHAT HANH SCHOLAR (TNH_SCHOLAR) project.
A rapid prototype implementation of the TNH-FAB command-line tool for Open AI based text processing.
Provides core functionality for text punctuation, sectioning, translation, and processing.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import click
from click import Context
from dotenv import load_dotenv

from tnh_scholar.utils.validate import check_openai_env
from tnh_scholar.ai_text_processing import (
    Pattern,
    PatternManager,
    TextObject,
    find_sections,
    process_text,
    process_text_by_paragraphs,
    process_text_by_sections,
    punctuate_text,
    translate_text_by_lines,
)
from tnh_scholar.logging_config import get_child_logger, setup_logging

DEFAULT_SECTION_PATTERN = "default_section"

logger = get_child_logger(__name__)

# Default pattern directory as specified
from tnh_scholar import TNH_DEFAULT_PATTERN_DIR

class TNHFabConfig:
    """Holds configuration for the TNH-FAB CLI tool."""

    def __init__(self):
        self.verbose: bool = False
        self.debug: bool = False
        self.quiet: bool = False
        # Initialize pattern manager with directory set in .env file or default.

        load_dotenv()
        
        if pattern_path_name := os.getenv("TNH_PATTERN_DIR"):
            pattern_dir = Path(pattern_path_name)
            logger.debug(f"pattern dir: {pattern_path_name}")
        else:
            pattern_dir = TNH_DEFAULT_PATTERN_DIR

        pattern_dir.mkdir(parents=True, exist_ok=True)
        self.pattern_manager = PatternManager(pattern_dir)

pass_config = click.make_pass_decorator(TNHFabConfig, ensure=True)

def read_input(ctx: Context, input_file: Optional[Path]) -> str:
    """Read input from file or stdin."""
    if input_file:
        return input_file.read_text()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    ctx.fail("No input provided")

def get_pattern(pattern_manager: PatternManager, pattern_name: str) -> Pattern:
    """
    Get pattern from the pattern manager.

    Args:
        pattern_manager: Initialized PatternManager instance
        pattern_name: Name of the pattern to load

    Returns:
        Pattern: Loaded pattern object

    Raises:
        click.ClickException: If pattern cannot be loaded
    """
    try:
        return pattern_manager.load_pattern(pattern_name)
    except FileNotFoundError as e:
        raise click.ClickException(
            f"Pattern '{pattern_name}' not found in {pattern_manager.base_path}"
        ) from e
    except Exception as e:
        raise click.ClickException(f"Error loading pattern: {e}") from e


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable detailed logging. (NOT implemented)")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.option("--quiet", is_flag=True, help="Suppress all non-error output")
@click.pass_context
def tnh_fab(ctx: Context, verbose: bool, debug: bool, quiet: bool):
    """TNH-FAB: Thich Nhat Hanh Scholar Text processing command-line tool.

    CORE COMMANDS: punctuate, section, translate, process

    To Get help on any command and see its options:

    tnh-fab [COMMAND] --help

    Provides specialized processing for multi-lingual Dharma content.

    Offers functionalities for punctuation, sectioning, line-based translation,
    and general text processing based on predefined patterns.
    Input text can be provided either via a file or standard input.
    """        
    config = ctx.ensure_object(TNHFabConfig)
    
    if not check_openai_env():
        
        ctx.fail("Missing OpenAI Credentials.")
        
    config.verbose = verbose
    config.debug = debug
    config.quiet = quiet

    if not quiet:
        if debug:
            setup_logging(log_level=logging.DEBUG)
        else:
            setup_logging(log_level=logging.INFO)


@tnh_fab.command()
@click.argument(
    "input_file", type=click.Path(exists=True, path_type=Path), required=False
)
@click.option(
    "-l",
    "--language",
    help="Source language code (e.g., 'en', 'vi'). Auto-detected if not specified.",
)
@click.option(
    "-y", "--style", default="APA", help="Punctuation style to apply (default: 'APA')"
)
@click.option(
    "-c",
    "--review-count",
    type=int,
    default=3,
    help="Number of review passes (default: 3)",
)
@click.option(
    "-p",
    "--pattern",
    default="default_punctuate",
    help="Pattern name for punctuation rules (default: 'default_punctuate')",
)
@pass_config
def punctuate(
    config: TNHFabConfig,
    input_file: Optional[Path],
    language: Optional[str],
    style: str,
    review_count: int,
    pattern: str,
):
    """Add punctuation and structure to text based on language-specific rules.

    This command processes input text to add or correct punctuation, spacing, and basic
    structural elements. It is particularly useful for texts that lack proper punctuation
    or need standardization.


    Examples:

        \b
        # Process a file using default settings
        $ tnh-fab punctuate input.txt

        \b
        # Process Vietnamese text with custom style
        $ tnh-fab punctuate -l vi -y "Modern" input.txt

        \b
        # Process from stdin with increased review passes
        $ cat input.txt | tnh-fab punctuate -c 5

    """
    text = read_input(click, input_file)  # type: ignore
    punctuate_pattern = get_pattern(config.pattern_manager, pattern)
    result = punctuate_text(
        text,
        source_language=language,
        punctuate_pattern=punctuate_pattern,
        template_dict={"style_convention": style, "review_count": review_count},
    )
    click.echo(result)


@tnh_fab.command()
@click.argument(
    "input_file", type=click.Path(exists=True, path_type=Path), required=False
)
@click.option(
    "-l",
    "--language",
    help="Source language code (e.g., 'en', 'vi'). Auto-detected if not specified.",
)
@click.option(
    "-n",
    "--num-sections",
    type=int,
    help="Target number of sections (auto-calculated if not specified)",
)
@click.option(
    "-c",
    "--review-count",
    type=int,
    default=3,
    help="Number of review passes (default: 3)",
)
@click.option(
    "-p",
    "--pattern",
    default="default_section",
    help="Pattern name for section analysis (default: 'default_section')",
)
@pass_config
def section(
    config: TNHFabConfig,
    input_file: Optional[Path],
    language: Optional[str],
    num_sections: Optional[int],
    review_count: int,
    pattern: str,
):
    """Analyze and divide text into logical sections based on content.

    This command processes the input text to identify coherent sections based on content
    analysis. It generates a structured representation of the text with sections that
    maintain logical continuity. Each section includes metadata such as title and line
    range.

    Examples:

        \b
        # Auto-detect sections in a file
        $ tnh-fab section input.txt

        \b
        # Specify desired number of sections
        $ tnh-fab section -n 5 input.txt

        \b
        # Process Vietnamese text with custom pattern
        $ tnh-fab section -l vi -p custom_section_pattern input.txt

        \b
        # Section text from stdin with increased review
        $ cat input.txt | tnh-fab section -c 5

    \b
    Output Format:
        JSON object containing:
        - language: Detected or specified language code
        - sections: Array of section objects, each with:
            - title: Section title in original language
            - start_line: Starting line number (inclusive)
            - end_line: Ending line number (inclusive)
    """
    text = read_input(click, input_file)  # type: ignore
    section_pattern = get_pattern(config.pattern_manager, pattern)
    result = find_sections(
        text,
        source_language=language,
        section_pattern=section_pattern,
        section_count=num_sections,
        review_count=review_count,
    )
    # For prototype, just output the JSON representation
    click.echo(result.model_dump_json(indent=2))


@tnh_fab.command()
@click.argument(
    "input_file", type=click.Path(exists=True, path_type=Path), required=False
)
@click.option(
    "-l", "--language", help="Source language code. Auto-detected if not specified."
)
@click.option(
    "-r", "--target", default="en", help="Target language code (default: 'en')"
)
@click.option(
    "-y", "--style", help="Translation style (e.g., 'American Dharma Teaching')"
)
@click.option(
    "--context-lines",
    type=int,
    default=3,
    help="Number of context lines to consider (default: 3)",
)
@click.option(
    "--segment-size",
    type=int,
    help="Lines per translation segment (auto-calculated if not specified)",
)
@click.option(
    "-p",
    "--pattern",
    default="default_line_translation",
    help="Pattern name for translation (default: 'default_line_translation')",
)
@pass_config
def translate(
    config: TNHFabConfig,
    input_file: Optional[Path],
    language: Optional[str],
    target: str,
    style: Optional[str],
    context_lines: int,
    segment_size: Optional[int],
    pattern: str,
):
    """Translate text while preserving line numbers and contextual understanding.

    This command performs intelligent translation that maintains line number correspondence
    between source and translated text. It uses surrounding context to improve translation
    accuracy and consistency, particularly important for Buddhist texts where terminology
    and context are crucial.

    Examples:

        \b
        # Translate Vietnamese text to English
        $ tnh-fab translate -l vi input.txt

        \b
        # Translate to French with specific style
        $ tnh-fab translate -l vi -r fr -y "Formal" input.txt

        \b
        # Translate with increased context
        $ tnh-fab translate --context-lines 5 input.txt

        \b
        # Translate using custom segment size
        $ tnh-fab translate --segment-size 10 input.txt

    \b
    Notes:
        - Line numbers are preserved in the output
        - Context lines are used to improve translation accuracy
        - Segment size affects processing speed and memory usage
    """
    text = read_input(click, input_file)  # type: ignore
    translation_pattern = get_pattern(config.pattern_manager, pattern)
    result = translate_text_by_lines(
        text,
        source_language=language,
        target_language=target,
        pattern=translation_pattern,
        style=style,
        context_lines=context_lines,
        segment_size=segment_size,
    )
    click.echo(result)


@tnh_fab.command()
@click.argument(
    "input_file", type=click.Path(exists=True, path_type=Path), required=False
)
@click.option("-p", "--pattern", required=True, help="Pattern name for processing")
@click.option(
    "-s",
    "--section",
    type=click.Path(exists=True, path_type=Path),
    help="Process using sections from JSON file, or auto-generate if no file provided",
)
@click.option("-g", "--paragraph", is_flag=True, help="Process text by paragraphs")
@click.option(
    "-t",
    "--template",
    type=click.Path(exists=True, path_type=Path),
    help="YAML file containing template values",
)
@pass_config
def process(
    config: TNHFabConfig,
    input_file: Optional[Path],
    pattern: str,
    section: Optional[Path],
    paragraph: bool,
    template: Optional[Path],
):
    """Apply custom pattern-based processing to text with flexible structuring options.

    This command provides flexible text processing using customizable patterns. It can
    process text either by sections (defined in a JSON file or auto-detected), by
    paragraphs, or can be used to process a text as a whole (this is the default).
    This is particularly useful for formatting, restructuring, or applying
    consistent transformations to text.

    Examples:

        \b
        # Process using a specific pattern
        $ tnh-fab process -p format_xml input.txt

        \b
        # Process using paragraph mode
        $ tnh-fab process -p format_xml -g input.txt

        \b
        # Process with custom sections
        $ tnh-fab process -p format_xml -s sections.json input.txt

        \b
        # Process with template values
        $ tnh-fab process -p format_xml -t template.yaml input.txt


    Processing Modes:

        \b
        1. Single Input Mode (default)
            - Processes entire input.

        \b
        2. Section Mode (-s):
            - Uses sections from JSON file if provided (-s)
            - If no section file is provided, sections are auto-generated.
            - Processes each section according to pattern

        \b
        3. Paragraph Mode (-g):
            - Treats each line/paragraph as a separate unit
            - Useful for simpler processing tasks
            - More memory efficient for large files

    \b
    Notes:
        - Required pattern must exist in pattern directory
        - Template values can customize pattern behavior

    """
    text = read_input(click, input_file)  # type: ignore
    process_pattern = get_pattern(config.pattern_manager, pattern)

    template_dict: Dict[str, str] = {}

    if paragraph:
        result = process_text_by_paragraphs(
            text, template_dict, pattern=process_pattern
        )
        for processed in result:
            click.echo(processed)
    elif section is not None:  # Section mode (either file or auto-generate)
        if isinstance(section, Path):  # Section file provided
            sections_json = Path(section).read_text()
            text_obj = TextObject.model_validate_json(sections_json)

        else:  # Auto-generate sections
            default_section_pattern = get_pattern(
                config.pattern_manager, DEFAULT_SECTION_PATTERN
            )
            text_obj = find_sections(text, section_pattern=default_section_pattern)

        result = process_text_by_sections(
            text, text_obj, template_dict, pattern=process_pattern
        )
        for processed_section in result:
            click.echo(processed_section.processed_text)
    else:
        result = process_text(
            text, pattern=process_pattern, template_dict=template_dict
        )
        click.echo(result)


def main():
    """Entry point for TNH-FAB CLI tool."""
    tnh_fab()


if __name__ == "__main__":
    main()
