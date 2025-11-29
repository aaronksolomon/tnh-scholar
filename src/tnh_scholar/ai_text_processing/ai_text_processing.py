# AI based text processing routines and classes

# external package imports
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, Optional, Tuple, Type, cast

from pydantic import BaseModel

from tnh_scholar.gen_ai_service.utils.token_utils import token_count
from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.metadata.metadata import ProcessMetadata
from tnh_scholar.text_processing import (
    NumberedText,
)
from tnh_scholar.utils.lang import (
    get_language_from_code,
)

from .openai_process_interface import openai_process_text
from .prompts import LocalPromptManager, Prompt
from .text_object import AIResponse, TextObject

# internal package imports
from .typing import ProcessorResult

logger = get_child_logger(__name__)

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
DEFAULT_SECTION_RANGE_VAR = 2

@dataclass
class ProcessedSection:
    """Represents a processed section of text with its metadata."""
    title: str
    original_str: str
    processed_str: str
    metadata: Dict = field(default_factory=dict)

class TextProcessor(ABC):
    """Abstract base class for text processors that can return Pydantic objects."""
    @abstractmethod
    def process_text(
        self,
        input_str: str,
        instructions: str,
        response_format: Optional[Type[BaseModel]] = None,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Process text according to instructions.

        Args:
            input_str: Input text to process
            instructions: Processing instructions
            response_format: Optional Pydantic class for structured output
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
        input_str: str,
        instructions: str,
        response_format: Optional[Type[BaseModel]] = None,
        max_tokens: int = 0,
        **kwargs: Any,
    ) -> ProcessorResult:
        """Process text using OpenAI API with optional structured output."""

        if max_tokens == 0 and self.max_tokens > 0:
            max_tokens = self.max_tokens

        return openai_process_text(
            input_str,
            instructions,
            model=self.model,
            max_tokens=max_tokens,
            response_format=response_format,
            **kwargs,
        )

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


class SectionParser:
    """Generates structured section breakdowns of text content."""

    def __init__(
        self,
        section_scanner: TextProcessor,
        section_pattern: Prompt,
        review_count: int = DEFAULT_REVIEW_COUNT,
    ):
        """
        Initialize section generator.

        Args:
            section_scanner: Text processor used to extract sections
            section_pattern: Pattern object containing section generation instructions
            review_count: Number of review passes
        """
        self.section_scanner = section_scanner
        self.section_pattern = section_pattern
        self.review_count = review_count

    def find_sections(
        self,
        text: TextObject,
        section_count_target: Optional[int] = None,
        segment_size_target: Optional[int] = None,
        template_dict: Optional[Dict[str, str]] = None,
    ) -> TextObject:
        """
        Generate section breakdown of input text. The text must be split up by newlines.

        Args:
            text: Input TextObject to process
            section_count_target: the target for the number of sections to find
            segment_size_target: the target for the number of lines per section
                (if section_count_target is specified, 
                this value will be set to generate correct segments)
            template_dict: Optional additional template variables

        Returns:
            TextObject containing section breakdown
        """

        # Prepare numbered text, each line is numbered
        num_text = text.num_text

        if num_text.size < SECTION_SEGMENT_SIZE_WARNING_LIMIT:
            logger.warning(
                f"find_sections: Text has only {num_text.size} lines. "
                "This may lead to unexpected sectioning results."
            )

        # Get language if not specified
        source_language = get_language_from_code(text.language)

        # determine section count if not specified
        if not section_count_target:
            segment_size_target, section_count_target = self._get_section_count_info(
                text.content
            )
        elif not segment_size_target:
            segment_size_target = round(num_text.size / section_count_target)

        section_count_range = self._get_section_count_range(section_count_target)

        current_metadata = text.metadata
        
        # Prepare template variables
        template_values = {
            "metadata": current_metadata.to_yaml(),
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
        result = self.section_scanner.process_text(
            num_text.numbered_content, instructions, response_format=AIResponse
        )
        
        ai_response = cast(AIResponse, result)
        text_result = TextObject.from_response(ai_response, current_metadata, num_text)

        logger.info(f"Generated {text_result.section_count} sections.")
        
        return text_result

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

def find_sections(
    text: TextObject,
    source_language: Optional[str] = None,
    section_pattern: Optional[Prompt] = None,
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
        section_pattern: Optional custom pattern (uses default if None)
        section_model: Optional model identifier
        max_tokens: Maximum tokens for response
        section_count: Target number of sections
        review_count: Number of review passes
        template_dict: Optional additional template variables

    Returns:
        TextObject containing section breakdown
    """
    if section_pattern is None:
        section_pattern = get_pattern(DEFAULT_SECTION_PATTERN)
        logger.debug(f"Using default section pattern: {DEFAULT_SECTION_PATTERN}.")

    section_scanner = OpenAIProcessor(model=section_model, max_tokens=max_tokens)
    parser = SectionParser(
        section_scanner=section_scanner,
        section_pattern=section_pattern,
        review_count=review_count,
    )
    
    process_metadata = ProcessMetadata(
            step="find_sections",
            processor="SectionProcessor", 
            source_language=source_language,
            pattern=section_pattern.name,
            model=section_model,
            section_count=section_count,
            review_count=review_count,
            template_dict=template_dict,
        )

    result_text = parser.find_sections(
        text,
        section_count_target=section_count,
        template_dict=template_dict,
    )
    result_text.transform(process_metadata=process_metadata)
    return result_text

class SectionProcessor:
    """Handles section-based XML text processing with configurable output handling."""

    def __init__(
        self,
        processor: TextProcessor,
        pattern: Prompt,
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
        text_object: TextObject,
    ) -> Generator[ProcessedSection, None, None]:
        """
        Process transcript sections and yield results one section at a time.

        Args:
            text_object: Object containing section definitions

        Yields:
            ProcessedSection: One processed section at a time, containing:
                - title: Section title (English or original language)
                - original_text: Raw text segment
                - processed_text: Processed text content
                - start_line: Starting line number
        """
        # numbered_transcript = NumberedText(transcript) 
        # transcript is now stored in the TextObject
        sections = text_object.sections

        logger.info(
            f"Processing {len(sections)} sections with pattern: {self.pattern.name}"
        )

        for section_entry in text_object:
            logger.info(f"Processing section {section_entry.number} "
                        f"'{section_entry.title}':")

            # Get text segment for section
            text_segment = section_entry.content

            # Prepare template variables
            template_values = {
                "metadata": text_object.metadata.to_yaml(),
                "section_title": section_entry.title,
                "source_language": get_language_from_code(text_object.language),
                "review_count": DEFAULT_REVIEW_COUNT,
            }

            if self.template_dict:
                template_values |= self.template_dict

            # Get and apply processing instructions
            instructions = self.pattern.apply_template(template_values)
            processed_str = self.processor.process_text(text_segment, instructions)

            yield ProcessedSection(
                title=section_entry.title,
                original_str=text_segment,
                processed_str=processed_str,
            )

    def process_paragraphs(
        self,
        text: TextObject,
    ) -> Generator[ProcessedSection, None, None]:
        """
        Process transcript by paragraphs (as sections), yielding ProcessedSection objects.
        Paragraphs are assumed to be given as newline separated.

        Args:
            text: TextObject to process

        Yields:
            ProcessedSection: One processed paragraph at a time, containing:
                - title: Paragraph number (e.g., 'Paragraph 1')
                - original_str: Raw paragraph text
                - processed_str: Processed paragraph text
                - metadata: Optional metadata dict
        """
        num_text = text.num_text

        logger.info(f"Processing lines as paragraphs with pattern: {self.pattern.name}")

        for i, line in num_text:
            # If line is empty or whitespace, continue
            if not line.strip():
                continue

            instructions = self.pattern.apply_template(self.template_dict)

            if i <= 1:
                logger.debug(f"Process instructions (first paragraph):\n{instructions}")

            processed_str = self.processor.process_text(line, instructions)
            yield ProcessedSection(
                title=f"Paragraph {i}",
                original_str=line,
                processed_str=processed_str,
                metadata={"paragraph_number": i}
            )


class GeneralProcessor:
    def __init__(
        self,
        processor: TextProcessor,
        pattern: Prompt,
        source_language: Optional[str] = None,
        review_count: int = DEFAULT_REVIEW_COUNT,
    ):
        """
        Initialize general processor.

        Args:
            processor: Implementation of TextProcessor
            pattern: Pattern object containing processing instructions
            source_language: ISO code for the source language
            review_count: Number of review passes
        """

        self.source_language = source_language
        self.processor = processor
        self.pattern = pattern
        self.review_count = review_count

    def process_text(
        self,
        text: TextObject,
        template_dict: Optional[Dict] = None,
    ) -> str:
        """
        process a text based on a pattern and source language.
        """

        source_language = get_language_from_code(text.language)
        
        template_values = {
            "metadata": text.metadata_str,
            "source_language": source_language,
            "review_count": self.review_count,
        }

        if template_dict:
            template_values |= template_dict

        logger.info("Processing text...")
        instructions = self.pattern.apply_template(template_values)

        logger.debug(f"Process instructions:\n{instructions}")

        result = self.processor.process_text(text.content, instructions)
        
        logger.info("Processing completed.")

        # normalize newline spacing to two newline between lines and return
        # commented out to allow pattern to dictate newlines:
        # return normalize_newlines(text)
        return result

def process_text(
    text: TextObject,
    pattern: Prompt,
    source_language: Optional[str] = None,
    model: Optional[str] = None,
    template_dict: Optional[Dict] = None,
) -> TextObject:

    if not model:
        model = DEFAULT_OPENAI_MODEL

    processor = GeneralProcessor(
        processor=OpenAIProcessor(model),
        source_language=source_language,
        pattern=pattern,
    )

    process_metadata = ProcessMetadata(
            step="process_text",
            processor="GeneralProcessor",
            pattern=pattern.name,
            model=model,
            template_dict=template_dict,
        )
    
    result = processor.process_text(
        text, template_dict=template_dict
    )
    text.transform(data_str=result, process_metadata=process_metadata)
    return text
    
def process_text_by_sections(
    text_object: TextObject,
    template_dict: Dict,
    pattern: Prompt,
    model: Optional[str] = None,
) -> Generator[ProcessedSection, None, None]:
    """
    High-level function for processing text sections with configurable output handling.

    Args:
        text_object: Object containing section definitions
        pattern: Pattern object containing processing instructions
        template_dict: Dictionary for template substitution
        model: Optional model identifier for processor

    Returns:
        Generator for ProcessedSections
    """
    processor = OpenAIProcessor(model)

    section_processor = SectionProcessor(processor, pattern, template_dict)

    process_metadata = ProcessMetadata(
            step="process_text_by_sections",
            processor="SectionProcessor",
            pattern=pattern.name,
            model=model,
            template_dict=template_dict,
        )
    result = section_processor.process_sections(text_object)
    
    text_object.transform(process_metadata=process_metadata)
    
    return result

def process_text_by_paragraphs(
    text: TextObject,
    template_dict: Dict[str, str],
    pattern: Optional[Prompt] = None,
    model: Optional[str] = None,
) -> Generator[ProcessedSection, None, None]:
    """
    High-level function for processing text paragraphs, yielding ProcessedSection objects.
    Assumes paragraphs are separated by newlines.
    Uses DEFAULT_XML_FORMAT_PATTERN as default pattern for text processing.

    Args:
        text: TextObject to process
        template_dict: Dictionary for template substitution
        pattern: Pattern object containing processing instructions
        model: Optional model identifier for processor

    Returns:
        Generator for ProcessedSection objects (one per paragraph)
    """
    processor = OpenAIProcessor(model)

    if not pattern:
        pattern = get_pattern(DEFAULT_PARAGRAPH_FORMAT_PATTERN)

    section_processor = SectionProcessor(processor, pattern, template_dict)

    process_metadata = ProcessMetadata(
        step="process_text_by_paragraphs",
        processor="SectionProcessor",
        pattern=pattern.name,
        model=model,
        template_dict=template_dict,
    )

    result = section_processor.process_paragraphs(text)

    text.transform(process_metadata=process_metadata)

    return result

def get_pattern(name: str) -> Prompt:
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
    return LocalPromptManager().get_prompt(name)
