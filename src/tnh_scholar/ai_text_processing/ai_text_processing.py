# AI based text processing routines and classes

# external package imports
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Generator, List, Optional, Pattern, Tuple, Type, Union

from dotenv import load_dotenv

from tnh_scholar.ai_text_processing.lang import get_language_name
from tnh_scholar.ai_text_processing.patterns import Pattern, PatternManager
from tnh_scholar.ai_text_processing.response_format import LogicalSection, TextObject

# internal package imports
from tnh_scholar.ai_text_processing.typing import ResponseFormat
from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.openai_interface import token_count
from tnh_scholar.text_processing import (
    NumberedText,
)

from .openai_process_interface import openai_process_text

logger = get_child_logger(__name__)

from tnh_scholar import TNH_DEFAULT_PATTERN_DIR

# Constants
DEFAULT_MIN_SECTION_COUNT = 3
DEFAULT_SECTION_TOKEN_SIZE = 650
DEFAULT_SECTION_RESULT_MAX_SIZE = 4000
SECTION_SEGMENT_SIZE_WARNING_LIMIT = 5
DEFAULT_REVIEW_COUNT = 5
DEFAULT_SECTION_PATTERN = "default_section"
DEFAULT_PUNCTUATE_PATTERN = "default_punctuate"
DEFAULT_PUNCTUATE_STYLE = "APA"
DEFAULT_XML_FORMAT_PATTERN = "default_xml_format"
DEFAULT_PARAGRAPH_FORMAT_PATTERN = "default_xml_paragraph_format"
DEFAULT_PUNCTUATE_MODEL = "gpt-4o"
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_TRANSLATE_SEGMENT_SIZE = 20
DEFAULT_TRANSLATE_STYLE = "'American Dharma Teaching'"
DEFAULT_TRANSLATION_PATTERN = "default_line_translation"
DEFAULT_TRANSLATE_CONTEXT_LINES = 3
DEFAULT_TRANSLATION_TARGET_TOKENS = 650
DEFAULT_TARGET_LANGUAGE = "English"
DEFAULT_SECTION_RANGE_VAR = 2
TRANSCRIPT_SEGMENT_MARKER = "TRANSCRIPT_SEGMENT"
PRECEDING_CONTEXT_MARKER = "PRECEDING_CONTEXT"
FOLLOWING_CONTEXT_MARKER = "FOLLOWING_CONTEXT"



class LocalPatternManager:
    """
    A simple singleton implementation of PatternManager that ensures only one instance
    is created and reused throughout the application lifecycle.

    This class wraps the PatternManager to provide efficient pattern loading by
    maintaining a single reusable instance.

    Attributes:
        _instance (Optional[SingletonPatternManager]): The singleton instance
        _pattern_manager (Optional[PatternManager]): The wrapped PatternManager instance
    """

    _instance: Optional["LocalPatternManager"] = None

    def __new__(cls) -> "LocalPatternManager":
        """
        Create or return the singleton instance.

        Returns:
            SingletonPatternManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pattern_manager = None
        return cls._instance

    @property
    def pattern_manager(self) -> "PatternManager":
        """
        Lazy initialization of the PatternManager instance.

        Returns:
            PatternManager: The wrapped PatternManager instance

        Raises:
            RuntimeError: If PATTERN_REPO is not properly configured
        """
        if self._pattern_manager is None:  # type: ignore
            try:
                load_dotenv()
                if pattern_path_name := os.getenv("TNH_PATTERN_DIR"):
                    pattern_dir = Path(pattern_path_name)
                    logger.debug(f"pattern dir: {pattern_path_name}")
                else:
                    pattern_dir = TNH_DEFAULT_PATTERN_DIR
                self._pattern_manager = PatternManager(pattern_dir)
            except ImportError as err:
                raise RuntimeError(
                    "Failed to initialize PatternManager. Ensure pattern_manager "
                    f"module and PATTERN_REPO are properly configured: {err}"
                ) from err
        return self._pattern_manager


@dataclass
class ProcessedSection:
    """Represents a processed section of text with its metadata."""

    title: str
    original_text: str
    processed_text: str
    start_line: int
    end_line: int
    metadata: Dict = field(default_factory=dict)


class TextProcessor(ABC):
    """Abstract base class for text processors that can return Pydantic objects."""

    @abstractmethod
    def process_text(
        self,
        text: str,
        instructions: str,
        response_format: Optional[Type[ResponseFormat]] = None,
        **kwargs,
    ) -> Union[str, ResponseFormat]:
        """
        Process text according to instructions.

        Args:
            text: Input text to process
            instructions: Processing instructions
            response_object: Optional Pydantic class for structured output
            **kwargs: Additional processing parameters

        Returns:
            Either string or Pydantic model instance based on response_model
        """
        pass


class OpenAIProcessor(TextProcessor):
    """OpenAI-based text processor implementation."""

    def __init__(self, model: Optional[str] = None, max_tokens: int = 0):
        if not model:
            model = DEFAULT_OPENAI_MODEL
        self.model = model
        self.max_tokens = max_tokens

    def process_text(
        self,
        text: str,
        instructions: str,
        response_format: Optional[Type[ResponseFormat]] = None,
        max_tokens: int = 0,
        **kwargs,
    ) -> Union[str, ResponseFormat]:
        """Process text using OpenAI API with optional structured output."""

        if max_tokens == 0 and self.max_tokens > 0:
            max_tokens = self.max_tokens

        return openai_process_text(
            text,
            instructions,
            model=self.model,
            max_tokens=max_tokens,
            response_format=response_format,
            **kwargs,
        )


class TextPunctuator:
    def __init__(
        self,
        processor: TextProcessor,
        punctuate_pattern: Pattern,
        source_language: Optional[str] = None,
        review_count: int = DEFAULT_REVIEW_COUNT,
        style_convention=DEFAULT_PUNCTUATE_STYLE,
    ):
        """
        Initialize punctuation generator.

        Args:
            text_punctuator: Implementation of TextProcessor
            punctuate_pattern: Pattern object containing punctuation instructions
            section_count: Target number of sections
            review_count: Number of review passes
        """

        self.source_language = source_language
        self.processor = processor
        self.punctuate_pattern = punctuate_pattern
        self.review_count = review_count
        self.style_convention = style_convention

    def punctuate_text(
        self,
        text: str,
        source_language: Optional[str] = None,
        template_dict: Optional[Dict] = None,
    ) -> str:
        """
        punctuate a text based on a pattern and source language.
        """

        if not source_language:
            if self.source_language:
                source_language = self.source_language
            else:
                source_language = get_language_name(text)

        template_values = {
            "source_language": source_language,
            "review_count": self.review_count,
            "style_convention": self.style_convention,
        }

        if template_dict:
            template_values |= template_dict

        logger.info("Punctuating text...")
        punctuate_instructions = self.punctuate_pattern.apply_template(template_values)
        text = self.processor.process_text(text, punctuate_instructions)
        logger.info("Punctuation completed.")

        # normalize newline spacing to two newline (default) between lines and return
        # commented out to allow pattern to dictate newlines.
        # return normalize_newlines(text)
        return text


def punctuate_text(
    text,
    source_language: Optional[str] = None,
    punctuate_pattern: Optional[Pattern] = None,
    punctuate_model: Optional[str] = None,
    template_dict: Optional[Dict] = None,
) -> str:

    if not punctuate_model:
        punctuate_model = DEFAULT_PUNCTUATE_MODEL

    if not punctuate_pattern:
        punctuate_pattern = get_default_pattern(DEFAULT_PUNCTUATE_PATTERN)

    punctuator = TextPunctuator(
        processor=OpenAIProcessor(punctuate_model),
        source_language=source_language,
        punctuate_pattern=punctuate_pattern,
    )

    return punctuator.punctuate_text(
        text, source_language=source_language, template_dict=template_dict
    )


class LineTranslator:
    """Translates text line by line while maintaining line numbers and context."""

    def __init__(
        self,
        processor: TextProcessor,
        pattern: Pattern,
        review_count: int = DEFAULT_REVIEW_COUNT,
        style: str = DEFAULT_TRANSLATE_STYLE,
        context_lines: int = DEFAULT_TRANSLATE_CONTEXT_LINES,  # Number of context lines before/after
    ):
        """
        Initialize line translator.

        Args:
            processor: Implementation of TextProcessor
            pattern: Pattern object containing translation instructions
            review_count: Number of review passes
            style: Translation style to apply
            context_lines: Number of context lines to include before/after
        """
        self.processor = processor
        self.pattern = pattern
        self.review_count = review_count
        self.style = style
        self.context_lines = context_lines

    def translate_segment(
        self,
        num_text: NumberedText,
        start_line: int,
        end_line: int,
        source_language: Optional[str] = None,
        target_language: Optional[str] = DEFAULT_TARGET_LANGUAGE,
        template_dict: Optional[Dict] = None,
    ) -> str:
        """
        Translate a segment of text with context.

        Args:
            text: Full text to extract segment from
            start_line: Starting line number of segment
            end_line: Ending line number of segment
            source_language: Source language code
            target_language: Target language code (default: English)
            template_dict: Optional additional template values

        Returns:
            Translated text segment with line numbers preserved
        """

        # Extract main segment and context
        lines = num_text.numbered_lines

        # Calculate context ranges
        preceding_start = max(1, start_line - self.context_lines)  # lines start on 1.
        following_end = min(num_text.end + 1, end_line + self.context_lines)

        # Extract context and segment
        preceding_context = num_text.get_numbered_segment(preceding_start, start_line)
        transcript_segment = num_text.get_numbered_segment(start_line, end_line)
        following_context = num_text.get_numbered_segment(end_line, following_end)

        # build input text
        translation_input = self._build_translation_input(
            preceding_context, transcript_segment, following_context
        )

        # Prepare template values
        template_values = {
            "source_language": source_language,
            "target_language": target_language,
            "review_count": self.review_count,
            "style": self.style,
        }

        if template_dict:
            template_values |= template_dict

        # Get and apply translation instructions
        logger.info(f"Translating segment (lines {start_line}-{end_line})")
        translate_instructions = self.pattern.apply_template(template_values)

        if start_line <= 1:
            logger.debug(
                f"Translate instructions (first segment):\n{translate_instructions}"
            )

        logger.debug(f"Translation input:\n{translation_input}")

        return self.processor.process_text(translation_input, translate_instructions)

    def _build_translation_input(
        self, preceding_context: str, transcript_segment: str, following_context: str
    ) -> str:
        """
        Build input text in required XML-style format.

        Args:
            preceding_context: Context lines before segment
            transcript_segment: Main segment to translate
            following_context: Context lines after segment

        Returns:
            Formatted input text
        """
        parts = []

        # Add preceding context if exists
        if preceding_context:
            parts.extend(
                [
                    PRECEDING_CONTEXT_MARKER,
                    preceding_context,
                    PRECEDING_CONTEXT_MARKER,
                    "",
                ]
            )

        # Add main segment (always required)
        parts.extend(
            [
                TRANSCRIPT_SEGMENT_MARKER,
                transcript_segment,
                TRANSCRIPT_SEGMENT_MARKER,
                "",
            ]
        )

        # Add following context if exists
        if following_context:
            parts.extend(
                [
                    FOLLOWING_CONTEXT_MARKER,
                    following_context,
                    FOLLOWING_CONTEXT_MARKER,
                    "",
                ]
            )

        return "\n".join(parts)

    def translate_text(
        self,
        text: str,
        segment_size: Optional[int] = None,  # Number of lines per segment
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
        template_dict: Optional[Dict] = None,
    ) -> str:
        """
        Translate entire text in segments while maintaining line continuity.

        Args:
            text: Text to translate
            segment_size: Number of lines per translation segment
            source_language: Source language code
            target_language: Target language code (default: English)
            template_dict: Optional additional template values

        Returns:
            Complete translated text with line numbers preserved
        """

        # Auto-detect language if not specified
        if not source_language:
            source_language = get_language_name(text)

        # Convert text to numbered lines
        num_text = NumberedText(text)
        total_lines = num_text.size

        if not segment_size:
            segment_size = _calculate_segment_size(
                num_text, DEFAULT_TRANSLATION_TARGET_TOKENS
            )

        translated_segments = []

        logger.debug(
            f"Total lines to translate: {total_lines} | Translation segment size: {segment_size}."
        )
        # Process text in segments using segment iteration
        for start_idx, end_idx in num_text.iter_segments(
            segment_size, segment_size // 5
        ):
            translated_segment = self.translate_segment(
                num_text,
                start_idx,
                end_idx,
                source_language,
                target_language,
                template_dict,
            )

            # validate the translated segment
            translated_content = self._extract_content(translated_segment)
            self._validate_segment(translated_content, start_idx, end_idx)

            translated_segments.append(translated_content)

        return "\n".join(translated_segments)

    def _extract_content(self, segment: str) -> str:
        segment = segment.strip()  # remove any filling whitespace
        if segment.startswith(TRANSCRIPT_SEGMENT_MARKER) and segment.endswith(
            TRANSCRIPT_SEGMENT_MARKER
        ):
            return segment[
                len(TRANSCRIPT_SEGMENT_MARKER) : -len(TRANSCRIPT_SEGMENT_MARKER)
            ].strip()
        logger.warning("Translated segment missing transcript_segment tags")
        return segment

    def _validate_segment(
        self, translated_content: str, start_index: int, end_index: int
    ) -> None:
        """
        Validate translated segment format, content, and line number sequence.
        Issues warnings for validation issues rather than raising errors.

        Args:
            translated_segment: Translated text to validate
            start_idx: the staring index of the range (inclusive)
            end_line: then ending index of the range (exclusive)

        Returns:
            str: Content with segment tags removed
        """

        # Validate lines

        lines = translated_content.splitlines()
        line_numbers = []

        start_line = start_index  # inclusive start
        end_line = end_index - 1  # exclusive end

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if ":" not in line:
                logger.warning(f"Invalid line format: {line}")
                continue

            try:
                line_num = int(line[: line.index(":")])
                if line_num < 0:
                    logger.warning(f"Invalid line number: {line}")
                    continue
                line_numbers.append(line_num)
            except ValueError:
                logger.warning(f"Line number parsing failed: {line}")
                continue

        # Validate sequence
        if not line_numbers:
            logger.warning("No valid line numbers found")
        else:
            if line_numbers[0] != start_line:
                logger.warning(
                    f"First line number {line_numbers[0]} doesn't match expected {start_line}"
                )

            if line_numbers[-1] != end_line:
                logger.warning(
                    f"Last line number {line_numbers[-1]} doesn't match expected {end_line}"
                )

            expected = set(range(start_line, end_line + 1))
            if missing := expected - set(line_numbers):
                logger.warning(f"Missing line numbers in sequence: {missing}")

        logger.debug(f"Validated {len(lines)} lines from {start_line} to {end_line}")


def _calculate_segment_size(num_text: NumberedText, target_segment_tokens: int) -> int:
    """
    Calculate segment size (in number of lines) based on average tokens per line
    to reach a total of target_segment_tokens for the segment.

    Args:
        num_text: Collection of numbered lines as NumberedText
        target_segment_tokens: Desired token count per segment

    Returns:
        int: Recommended number of lines per segment

    Example:
    """
    text = num_text.content
    tokens = token_count(text)
    # Calculate average tokens per line
    avg_tokens_per_line = tokens / num_text.size
    logger.debug(f"Average tokens per line: {avg_tokens_per_line}")

    return max(1, round(target_segment_tokens / avg_tokens_per_line))


def translate_text_by_lines(
    text,
    source_language: Optional[str] = None,
    target_language: Optional[str] = None,
    pattern: Optional[Pattern] = None,
    model: Optional[str] = None,
    style: Optional[str] = None,
    segment_size: Optional[int] = None,
    context_lines: Optional[int] = None,
    review_count: Optional[int] = None,
    template_dict: Optional[Dict] = None,
) -> str:

    if pattern is None:
        pattern = get_default_pattern(DEFAULT_TRANSLATION_PATTERN)

    translator = LineTranslator(
        processor=OpenAIProcessor(model),
        pattern=pattern,
        style=style or DEFAULT_TRANSLATE_STYLE,
        context_lines=context_lines or DEFAULT_TRANSLATE_CONTEXT_LINES,
        review_count=review_count or DEFAULT_REVIEW_COUNT,
    )

    return translator.translate_text(
        text,
        source_language=source_language,
        target_language=target_language,
        segment_size=segment_size,
        template_dict=template_dict,
    )


class SectionParser:
    """Generates structured section breakdowns of text content."""

    def __init__(
        self,
        section_scanner: TextProcessor,
        section_pattern: Pattern,
        review_count: int = DEFAULT_REVIEW_COUNT,
    ):
        """
        Initialize section generator.

        Args:
            processor: Implementation of TextProcessor
            pattern: Pattern object containing section generation instructions
            max_tokens: Maximum tokens for response
            section_count: Target number of sections
            review_count: Number of review passes
        """
        self.section_scanner = section_scanner
        self.section_pattern = section_pattern
        self.review_count = review_count

    def find_sections(
        self,
        text: str,
        source_language: Optional[str] = None,
        section_count_target: Optional[int] = None,
        segment_size_target: Optional[int] = None,
        template_dict: Optional[Dict[str, str]] = None,
    ) -> TextObject:
        """
        Generate section breakdown of input text. The text must be split up by newlines.

        Args:
            text: Input text to process
            source_language: ISO 639-1 language code, or None for autodetection
            section_count_target: the target for the number of sections to find
            segment_size_target: the target for the number of lines per section
                (if section_count_target is specified, this value will be set to generate correct segments)
            template_dict: Optional additional template variables

        Returns:
            TextObject containing section breakdown

        Raises:
            ValidationError: If response doesn't match TextObject schema
        """

        # Prepare numbered text, each line is numbered
        num_text = NumberedText(text)

        if num_text.size < SECTION_SEGMENT_SIZE_WARNING_LIMIT:
            logger.warning(
                f"find_sections: Text has only {num_text.size} lines. This may lead to unexpected sectioning results."
            )

        # Get language if not specified
        if not source_language:
            source_language = get_language_name(text)

        # determine section count if not specified
        if not section_count_target:
            segment_size_target, section_count_target = self._get_section_count_info(
                text
            )
        elif not segment_size_target:
            segment_size_target = round(num_text.size / section_count_target)

        section_count_range = self._get_section_count_range(section_count_target)

        # Prepare template variables
        template_values = {
            "source_language": source_language,
            "section_count": section_count_range,
            "line_count": segment_size_target,
            "review_count": self.review_count,
        }

        if template_dict:
            template_values |= template_dict

        # Get and apply processing instructions
        instructions = self.section_pattern.apply_template(template_values)
        logger.debug(f"Finding sections with pattern instructions:\n {instructions}")

        logger.info(
            f"Finding sections for {source_language} text "
            f"(target sections: {section_count_target})"
        )

        # Process text with structured output
        try:
            result = self.section_scanner.process_text(
                str(num_text), instructions, response_format=TextObject
            )

            # Validate section coverage
            self._validate_sections(result.sections, num_text.size)

            return result

        except Exception as e:
            logger.error(f"Section generation failed: {e}")
            raise

    def _get_section_count_info(self, text: str) -> Tuple[int, int]:
        num_text = NumberedText(text)
        segment_size = _calculate_segment_size(num_text, DEFAULT_SECTION_TOKEN_SIZE)
        section_count_target = round(num_text.size / segment_size)
        return segment_size, section_count_target

    def _get_section_count_range(
        self,
        section_count_target: int,
        section_range_var: int = DEFAULT_SECTION_RANGE_VAR,
    ) -> str:
        low = max(1, section_count_target - section_range_var)
        high = section_count_target + section_range_var
        return f"{low}-{high}"

    def _validate_sections(
        self, sections: List[LogicalSection], total_lines: int
    ) -> None:
        """
        Validate section line coverage and ordering. Issues warnings for validation problems
        instead of raising errors.

        Args:
            sections: List of generated sections
            text: Original text
        """

        covered_lines = set()
        last_end = -1

        for section in sections:
            # Check line ordering
            if section.start_line <= last_end:
                logger.warning(
                    f"Section lines should be sequential but found overlap: "
                    f"section starting at {section.start_line} begins before or at "
                    f"previous section end {last_end}"
                )

            # Track line coverage
            section_lines = set(range(section.start_line, section.end_line + 1))
            if section_lines & covered_lines:
                logger.warning(
                    f"Found overlapping lines in section '{section.title_en}'. "
                    f"Each line should belong to exactly one section."
                )
            covered_lines.update(section_lines)

            last_end = section.end_line

        # Check complete coverage
        expected_lines = set(range(1, total_lines + 1))
        if covered_lines != expected_lines:
            missing = sorted(list(expected_lines - covered_lines))
            logger.warning(
                f"Not all lines are covered by sections. "
                f"Missing line numbers: {missing}"
            )


def find_sections(
    text: str,
    source_language: Optional[str] = None,
    section_pattern: Optional[Pattern] = None,
    section_model: Optional[str] = None,
    max_tokens: int = DEFAULT_SECTION_RESULT_MAX_SIZE,
    section_count: Optional[int] = None,
    review_count: int = DEFAULT_REVIEW_COUNT,
    template_dict: Optional[Dict[str, str]] = None,
) -> TextObject:
    """
    High-level function for generating text sections.

    Args:
        text: Input text
        source_language: ISO 639-1 language code
        pattern: Optional custom pattern (uses default if None)
        model: Optional model identifier
        max_tokens: Maximum tokens for response
        section_count: Target number of sections
        review_count: Number of review passes
        template_dict: Optional additional template variables

    Returns:
        TextObject containing section breakdown
    """
    if section_pattern is None:
        section_pattern = get_default_pattern(DEFAULT_SECTION_PATTERN)
        logger.debug(f"Using default section pattern: {DEFAULT_SECTION_PATTERN}.")

    if source_language is None:
        source_language = get_language_name(text)

    section_scanner = OpenAIProcessor(model=section_model, max_tokens=max_tokens)
    parser = SectionParser(
        section_scanner=section_scanner,
        section_pattern=section_pattern,
        review_count=review_count,
    )

    return parser.find_sections(
        text,
        source_language=source_language,
        section_count_target=section_count,
        template_dict=template_dict,
    )


class SectionProcessor:
    """Handles section-based XML text processing with configurable output handling."""

    def __init__(
        self,
        processor: TextProcessor,
        pattern: Pattern,
        template_dict: Dict,
        wrap_in_document: bool = True,
    ):
        """
        Initialize the XML section processor.

        Args:
            processor: Implementation of TextProcessor to use
            pattern: Pattern object containing processing instructions
            template_dict: Dictionary for template substitution
            wrap_in_document: Whether to wrap output in <document> tags
        """
        self.processor = processor
        self.pattern = pattern
        self.template_dict = template_dict
        self.wrap_in_document = wrap_in_document

    def process_sections(
        self,
        transcript: str,
        text_object: TextObject,
    ) -> Generator[ProcessedSection, None, None]:
        """
        Process transcript sections and yield results one section at a time.

        Args:
            transcript: Text to process
            text_object: Object containing section definitions

        Yields:
            ProcessedSection: One processed section at a time, containing:
                - title: Section title (English or original language)
                - original_text: Raw text segment
                - processed_text: Processed text content
                - start_line: Starting line number
                - end_line: Ending line number
        """
        numbered_transcript = NumberedText(transcript)
        sections = text_object.sections

        logger.info(
            f"Processing {len(sections)} sections with pattern: {self.pattern.name}"
        )

        for i, section in enumerate(sections, 1):
            logger.info(f"Processing section {i}, '{section.title}':")

            # Get text segment for section
            text_segment = numbered_transcript.get_segment(
                section.start_line, end=section.end_line
            )

            # Prepare template variables
            template_values = {
                "section_title": section.title,
                "source_language": text_object.language,
                "review_count": DEFAULT_REVIEW_COUNT,
            }

            if self.template_dict:
                template_values |= self.template_dict

            # Get and apply processing instructions
            instructions = self.pattern.apply_template(template_values)
            if i <= 1:
                logger.debug(f"Process instructions (first section):\n{instructions}")
            processed_text = self.processor.process_text(text_segment, instructions)

            yield ProcessedSection(
                title=section.title,
                original_text=text_segment,
                processed_text=processed_text,
                start_line=section.start_line,
                end_line=section.end_line,
            )

    def process_paragraphs(
        self,
        transcript: str,
    ) -> Generator[str, None, None]:
        """
        Process transcript by paragraphs (as sections) where paragraphs are assumed to be given as newline separated.

        Args:
            transcript: Text to process

        Returns:
            Generator of lines

        Yields:
            Processed lines as strings
        """
        numbered_transcript = NumberedText(transcript)

        logger.info(f"Processing lines as paragraphs with pattern: {self.pattern.name}")

        for i, line in numbered_transcript:

            # If line is empty or whitespace, continue
            if not line.strip():
                continue

            # Otherwise get and apply processing instructions
            instructions = self.pattern.apply_template(self.template_dict)

            if i <= 1:
                logger.debug(f"Process instructions (first paragraph):\n{instructions}")
            yield self.processor.process_text(line, instructions)


class GeneralProcessor:
    def __init__(
        self,
        processor: TextProcessor,
        pattern: Pattern,
        source_language: Optional[str] = None,
        review_count: int = DEFAULT_REVIEW_COUNT,
    ):
        """
        Initialize punctuation generator.

        Args:
            text_punctuator: Implementation of TextProcessor
            punctuate_pattern: Pattern object containing punctuation instructions
            section_count: Target number of sections
            review_count: Number of review passes
        """

        self.source_language = source_language
        self.processor = processor
        self.pattern = pattern
        self.review_count = review_count

    def process_text(
        self,
        text: str,
        source_language: Optional[str] = None,
        template_dict: Optional[Dict] = None,
    ) -> str:
        """
        process a text based on a pattern and source language.
        """

        if not source_language:
            if self.source_language:
                source_language = self.source_language
            else:
                source_language = get_language_name(text)

        template_values = {
            "source_language": source_language,
            "review_count": self.review_count,
        }

        if template_dict:
            template_values |= template_dict

        logger.info("Processing text...")
        instructions = self.pattern.apply_template(template_values)

        logger.debug(f"Process instructions:\n{instructions}")

        text = self.processor.process_text(text, instructions)
        logger.info("Processing completed.")

        # normalize newline spacing to two newline between lines and return
        # commented out to allow pattern to dictate newlines:
        # return normalize_newlines(text)
        return text


def process_text(
    text: str,
    pattern: Pattern,
    source_language: Optional[str] = None,
    model: Optional[str] = None,
    template_dict: Optional[Dict] = None,
) -> str:

    if not model:
        model = DEFAULT_OPENAI_MODEL

    processor = GeneralProcessor(
        processor=OpenAIProcessor(model),
        source_language=source_language,
        pattern=pattern,
    )

    return processor.process_text(
        text, source_language=source_language, template_dict=template_dict
    )


def process_text_by_sections(
    transcript: str,
    text_object: TextObject,
    template_dict: Dict,
    pattern: Optional[Pattern] = None,
    model: Optional[str] = None,
) -> Generator[ProcessedSection, None, None]:
    """
    High-level function for processing text sections with configurable output handling.

    Args:
        transcript: Text to process
        text_object: Object containing section definitions
        pattern: Pattern object containing processing instructions
        template_dict: Dictionary for template substitution
        model: Optional model identifier for processor

    Returns:
        Generator for ProcessedSections
    """
    processor = OpenAIProcessor(model)

    if not pattern:
        pattern = get_default_pattern(DEFAULT_XML_FORMAT_PATTERN)

    section_processor = SectionProcessor(processor, pattern, template_dict)

    return section_processor.process_sections(
        transcript,
        text_object,
    )


def process_text_by_paragraphs(
    transcript: str,
    template_dict: Dict[str, str],
    pattern: Optional[Pattern] = None,
    model: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    High-level function for processing text paragraphs. Assumes paragraphs are separated by newlines.
    Uses DEFAULT_XML_FORMAT_PATTERN as default pattern for text processing.

    Args:
        transcript: Text to process
        pattern: Pattern object containing processing instructions
        template_dict: Dictionary for template substitution
        model: Optional model identifier for processor


    Returns:
        Generator for ProcessedSections
    """
    processor = OpenAIProcessor(model)

    if not pattern:
        pattern = get_default_pattern(DEFAULT_PARAGRAPH_FORMAT_PATTERN)

    section_processor = SectionProcessor(processor, pattern, template_dict)

    return section_processor.process_paragraphs(transcript)


def get_default_pattern(name: str) -> Pattern:
    """
    Get a pattern by name using the singleton PatternManager.

    This is a more efficient version that reuses a single PatternManager instance.

    Args:
        name: Name of the pattern to load

    Returns:
        The loaded pattern

    Raises:
        ValueError: If pattern name is invalid
        FileNotFoundError: If pattern file doesn't exist
    """
    return LocalPatternManager().pattern_manager.load_pattern(name)
