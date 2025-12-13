#!/usr/bin/env python
"""
TNH-FAB Command Line Interface

Part of the THICH NHAT HANH SCHOLAR (TNH_SCHOLAR) project.
A rapid prototype implementation of the TNH-FAB command-line tool
for Open AI based text processing.
Provides core functionality for text punctuation, sectioning,
translation, and general processing.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Generator, Optional

import click
from click import Context, UsageError
from dotenv import load_dotenv

# Default pattern directory as specified
from tnh_scholar import TNH_DEFAULT_PATTERN_DIR
from tnh_scholar.ai_text_processing import (
    Prompt,
    PromptCatalog,
    TextObject,
    find_sections,
    process_text,
    process_text_by_paragraphs,
    process_text_by_sections,
    translate_text_by_lines,
)
from tnh_scholar.ai_text_processing.ai_text_processing import ProcessedSection
from tnh_scholar.cli_tools.utils import run_or_fail
from tnh_scholar.logging_config import get_child_logger, setup_logging
from tnh_scholar.metadata.metadata import Frontmatter
from tnh_scholar.utils.validate import check_openai_env

DEFAULT_SECTION_PATTERN = "default_section"
DEFAULT_TRANSLATE_PATTERN = "default_line_translate"

logger = get_child_logger(__name__)


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
        self.pattern_manager = PromptCatalog(pattern_dir)


pass_config = click.make_pass_decorator(TNHFabConfig, ensure=True)


def gen_text_input(ctx: Context, input_file: Optional[Path]) -> TextObject:
    """Read input from file or stdin."""
    if input_file:
        return TextObject.load(input_file)
    if not sys.stdin.isatty():
        return TextObject.from_str(sys.stdin.read())
    raise UsageError("No input provided")


def get_pattern(pattern_manager: PromptCatalog, pattern_name: str) -> Prompt:
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
        return pattern_manager.load(pattern_name)
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

    ⚠️  DEPRECATION WARNING: tnh-fab is deprecated and will be removed in a future release.
    Please migrate to tnh-gen, which provides the same functionality with improved
    architecture and VS Code integration. See the migration guide at:
    https://aaronksolomon.github.io/tnh-scholar/architecture/tnh-gen/

    CORE COMMANDS: punctuate, section, translate, process

    To Get help on any command and see its options:

    tnh-fab [COMMAND] --help

    Provides specialized processing for multi-lingual Dharma content.

    Offers functionalities for punctuation, sectioning, line-based translation,
    and general text processing based on predefined patterns.
    Input text can be provided either via a file or standard input.
    """
    config = ctx.ensure_object(TNHFabConfig)

    # Print deprecation warning unless quiet mode is enabled
    if not quiet:
        click.echo(
            click.style(
                "\n⚠️  DEPRECATION WARNING: tnh-fab is deprecated and will be moved to tnh-gen.\n"
                "   This tool will be removed in a future release. Please plan to migrate to tnh-gen.\n"
                "   See: https://aaronksolomon.github.io/tnh-scholar/architecture/tnh-gen/\n",
                fg="yellow",
                bold=True,
            ),
            err=True,
        )

    if not check_openai_env():
        raise click.ClickException("Missing OpenAI Credentials.")

    config.verbose = verbose
    config.debug = debug
    config.quiet = quiet

    if not quiet:
        if debug:
            setup_logging(log_level=logging.DEBUG)
        else:
            setup_logging(log_level=logging.INFO)


@tnh_fab.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path), required=False)
@click.option("-l", "--language", help="[DEPRECATED] Source language code")
@click.option("-y", "--style", help="[DEPRECATED] Punctuation style")
@click.option("-c", "--review-count", type=int, help="[DEPRECATED] Number of review passes")
@click.option("-p", "--pattern", help="[DEPRECATED] Pattern name for punctuation")
def punctuate(
    input_file: Optional[Path],
    language: Optional[str],
    style: Optional[str],
    review_count: Optional[int],
    pattern: Optional[str],
):
    """[DEPRECATED] Punctuation command is deprecated."""
    click.echo(
        "\nDEPRECATED: The 'punctuate' command is deprecated.\n"
        "Please use: tnh-fab process -p <punctuation_pattern>\n\n"
        "Example:\n"
        "  tnh-fab process -p default_punctuate input.txt\n"
    )
    sys.exit(1)


@tnh_fab.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path), required=False)
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
    default=DEFAULT_SECTION_PATTERN,
    help=f"Pattern name for section analysis (default: '{DEFAULT_SECTION_PATTERN}')",
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
    input_text = run_or_fail("Unable to read input", lambda: gen_text_input(click, input_file))  # type: ignore
    section_pattern = get_pattern(config.pattern_manager, pattern)

    text_object = run_or_fail(
        "Sectioning failed",
        lambda: find_sections(
            input_text,
            section_pattern=section_pattern,
            section_count=num_sections,
            review_count=review_count,
        ),
    )
    # For prototype, just output the JSON representation
    info = text_object.export_info(input_file)
    click.echo(info.model_dump_json(indent=2))


@tnh_fab.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path), required=False)
@click.option("-l", "--language", help="Source language code. Auto-detected if not specified.")
@click.option("-r", "--target", default="en", help="Target language code (default: 'en')")
@click.option("-y", "--style", help="Translation style (e.g., 'American Dharma Teaching')")
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
    default=DEFAULT_TRANSLATE_PATTERN,
    help=f"Pattern name for translation (default: '{DEFAULT_TRANSLATE_PATTERN}')",
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

    This command performs intelligent translation that maintains
    line number correspondence between source and translated text.
    It uses surrounding context to improve translation
    accuracy and consistency, particularly important for texts
    where terminology and context are crucial.

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
    text_obj = run_or_fail("Unable to read input", lambda: gen_text_input(click, input_file))  # type: ignore
    translation_pattern = get_pattern(config.pattern_manager, pattern)

    text_obj.update_metadata(source_file=input_file)

    text_obj = run_or_fail(
        "Translation failed",
        lambda: translate_text_by_lines(
            text_obj,
            source_language=language,
            target_language=target,
            pattern=translation_pattern,
            style=style,
            context_lines=context_lines,
            segment_size=segment_size,
        ),
    )
    click.echo(text_obj)


@tnh_fab.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path), required=False)
@click.option("-p", "--pattern", required=True, help="Pattern name for processing")
@click.option(
    "-s",
    "--section",
    type=click.Path(exists=True, path_type=Path),
    help="Process using sections from JSON file.",
)
@click.option("-a", "--auto", is_flag=True, help="Automatically generate and process by sections.")
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
    auto: bool,
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
            - Uses sections from a JSON file
            - Processes each section according to pattern

        \b
        3. Paragraph Mode (-g):
            - Treats each line/paragraph as a separate unit
            - Useful for simpler processing tasks
            - More memory efficient for large files

        \b
        3. Auto Section Mode (-a):
            - Automatically sections the input file
            - Processes by section

    \b
    Notes:
        - Required pattern must exist in pattern directory
        - Template values can customize pattern behavior

    """
    text_obj = run_or_fail("Unable to read input", lambda: gen_text_input(click, input_file))  # type: ignore

    process_pattern = get_pattern(config.pattern_manager, pattern)

    template_dict: Dict[str, str] = {}

    if paragraph:
        result = run_or_fail(
            "Paragraph processing failed",
            lambda: process_text_by_paragraphs(text_obj, template_dict, pattern=process_pattern),
        )
        export_processed_sections(result, text_obj)
    elif section is not None:  # Section mode (either file or auto-generate)
        text_obj = run_or_fail(
            "Failed to read sections", lambda: TextObject.from_section_file(section, text_obj.content)
        )

        result = run_or_fail(
            "Section processing failed",
            lambda: process_text_by_sections(text_obj, template_dict, pattern=process_pattern),
        )
        export_processed_sections(result, text_obj)
    elif auto:
        # Auto-generate sections
        default_section_pattern = get_pattern(config.pattern_manager, DEFAULT_SECTION_PATTERN)
        text_obj = run_or_fail(
            "Sectioning failed", lambda: find_sections(text_obj, section_pattern=default_section_pattern)
        )

        result = run_or_fail(
            "Section processing failed",
            lambda: process_text_by_sections(text_obj, template_dict, pattern=process_pattern),
        )
        export_processed_sections(result, text_obj)

    else:
        result = run_or_fail(
            "Processing failed",
            lambda: process_text(text_obj, pattern=process_pattern, template_dict=template_dict),
        )
        click.echo(result)


def export_processed_sections(
    section_result: Generator[ProcessedSection, None, None], text_obj: TextObject
) -> None:
    click.echo(f"{Frontmatter.generate(text_obj.metadata)}")
    for processed_section in section_result:
        click.echo(processed_section.processed_str)
        click.echo("\n")  # newline separated output.


def main():
    """Entry point for TNH-FAB CLI tool."""
    tnh_fab()


if __name__ == "__main__":
    main()
