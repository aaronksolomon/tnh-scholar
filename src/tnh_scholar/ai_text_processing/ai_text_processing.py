# AI based text processing routines and classes

# external package imports
from pathlib import Path
from typing import List, Dict
import logging
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Generator, List, Optional, Pattern, Union
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Type, TypeVar, List, Optional, Tuple
from pydantic import BaseModel, Field

# internal package imports
from tnh_scholar.text_processing import bracket_lines, unbracket_lines, lines_from_bracketed_text
from tnh_scholar.text_processing import get_text_from_file, write_text_to_file
from tnh_scholar.utils import iterate_subdir, load_json_into_model, save_model_to_json
from tnh_scholar.ai_text_processing.lang import get_language
from tnh_scholar.ai_text_processing.response_format import TextObject, Section
from tnh_scholar.ai_text_processing.patterns import Pattern, PatternManager

from .openai_process_interface import openai_process_text
from tnh_scholar.logging_config import get_child_logger
logger = get_child_logger(__name__)

from tnh_scholar import PATTERN_REPO

# Constants
DEFAULT_SECTION_TOKENS = 4000
DEFAULT_SECTION_COUNT = 5
DEFAULT_REVIEW_COUNT = 3
DEFAULT_SECTION_PATTERN = "default_generate_sections"
DEFAULT_PUNCTUATE_PATTERN = "default_punctuate"
DEFAULT_PUNCTUATE_STYLE = "APA"
DEFAULT_XML_FORMAT_PATTERN = "default_xml_format_section"
DEFAULT_PUNCTUATE_MODEL = "gpt-4o-mini"
DEFAULT_SECTION_MODEL = "gpt-4o"

ResponseFormat = TypeVar('ResponseFormat', bound=BaseModel)

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
        **kwargs
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
        self.model = model
        self.max_tokens = max_tokens

    def process_text(
        self,
        text: str,
        instructions: str,
        response_format: Optional[Type[ResponseFormat]] = None,
        max_tokens: int = 0,
        **kwargs
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
            **kwargs
        )

class TextPunctuator:
    def __init__(
        self,
        text_punctuator: TextProcessor,
        punctuate_pattern: Pattern,
        review_count: int = DEFAULT_REVIEW_COUNT,
        style_convention = DEFAULT_PUNCTUATE_STYLE
    ):
        """
        Initialize punctuation generator.
        
        Args:
            text_punctuator: Implementation of TextProcessor
            punctuate_pattern: Pattern object containing punctuation instructions
            section_count: Target number of sections
            review_count: Number of review passes
        """

        self.text_punctuator = text_punctuator
        self.punctuate_pattern = punctuate_pattern
        self.review_count = review_count
        self.style_convention = style_convention
        
    def punctuate_text(
        self,  
        text: str,
        source_language: str = None,
        template_dict: Optional[Dict] = None
    ) -> str:
        """
        punctuate a text based on a pattern and source language.
        """
        
        if not source_language:
            source_language = get_language(text, return_format='name')
            
        template_values = {
            "source_language": source_language,
            "review_count": self.review_count,
            "style_convention": DEFAULT_PUNCTUATE_STYLE
        }
        
        if template_dict:
            template_values |= template_dict
            
        logger.info("Punctuating text...")
        punctuate_instructions = self.punctuate_pattern.apply_template(template_values)
        text = self.text_punctuator.process_text(
            text,
            punctuate_instructions
        )
        logger.info("Punctuation completed.")
        
        return text    
        
        
class SectionParser:
    """Generates structured section breakdowns of text content."""
    
    def __init__(
        self,
        section_scanner: TextProcessor,
        section_pattern: Pattern,
        section_count: int = DEFAULT_SECTION_COUNT,
        review_count: int = DEFAULT_REVIEW_COUNT
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
        self.section_count = section_count
        self.review_count = review_count

    def find_sections(
        self,
        text: str,
        source_language: str = None,
        template_dict: Optional[Dict] = None
    ) -> TextObject:
        """
        Generate section breakdown of input text. The text must be split up by newlines.
        
        Args:
            text: Input text to process
            source_language: ISO 639-1 language code, or None for autodetection
            template_dict: Optional additional template variables
            
        Returns:
            TextObject containing section breakdown
            
        Raises:
            ValidationError: If response doesn't match TextObject schema
        """
           
        # Get language if needed
        if not source_language:
            source_language = get_language(text)
            
        # Prepare numbered text, each line is numbered
        bracketed_text = bracket_lines(text, number=True)

        # Prepare template variables
        template_values = {
            "source_language": source_language,
            "section_count": self.section_count,
            "review_count": self.review_count
        }
        
        if template_dict:
            template_values |= template_dict

        # Get and apply processing instructions
        instructions = self.section_pattern.apply_template(template_values)

        logger.info(f"Generating sections for {source_language} text "
                   f"(target sections: {self.section_count})")

        # Process text with structured output
        try:
            result = self.section_scanner.process_text(
                bracketed_text,
                instructions,
                response_format=TextObject
            )

            # Validate section coverage
            self._validate_sections(result.sections, bracketed_text)

            return result

        except Exception as e:
            logger.error(f"Section generation failed: {e}")
            raise
        
    

    def _validate_sections(self, sections: List[Section], text: str) -> None:
        """
        Validate section line coverage and ordering. Issues warnings for validation problems
        instead of raising errors.
        
        Args:
            sections: List of generated sections
            text: Original text
        """
        logger = logging.getLogger(__name__)
        total_lines = len(text.splitlines())
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
        
class XMLSectionProcessor:
    """Handles section-based XML text processing with configurable output handling."""
    
    def __init__(
        self,
        processor: TextProcessor,
        pattern: Pattern,
        template_dict: Dict,
        wrap_in_document: bool = True
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
        output_mode: str = "generator"
    ) -> Union[Generator[ProcessedSection, None, None], List[ProcessedSection], None]:
        """
        Process transcript sections and handle output according to specified mode.

        Args:
            transcript: Text to process
            section_object: Object containing section definitions
            output_mode: One of "generator", "list", or "none"

        Returns:
            Generator, List of ProcessedSection objects, or None based on output_mode

        Yields:
            ProcessedSection objects if output_mode is "generator"
        """
        bracketed_transcript = bracket_lines(transcript, number=True)
        sections = text_object.sections

        logger.info(f"Processing {len(sections)} sections with pattern: {self.pattern.name}")

        processed_sections = []

        for i, section in enumerate(sections, 1):
            
            is_english = section.language == 'en'

            if is_english:
                logger.info(f"Processing section {i}: '{section.title_en}'")
            else:
                logger.info(f"Processing section {i}: '{section.title_orig} / {section.title_en}")

            # Extract original text
            original_text = lines_from_bracketed_text(
                bracketed_transcript,
                start=section.start_line,
                end=section.end_line,
                keep_brackets=False
            )

            # Get and apply processing instructions
            instructions = self.pattern.apply_template(self.template_dict)
            processed_text = self.processor.process_text(original_text, instructions)

            # Create processed section object
            processed_section = ProcessedSection(
                title = section.title_en if is_english else section.title_orig,
                original_text=original_text,
                processed_text=processed_text,
                start_line=section.start_line,
                end_line=section.end_line
            )

            if output_mode == "generator":
                yield processed_section
            elif output_mode == "list":
                processed_sections.append(processed_section)

        return processed_sections if output_mode == "list" else None

    def write_to_file(
        self,
        output_file: Path,
        sections_generator: Generator[ProcessedSection, None, None]
    ) -> None:
        """
        Write processed sections to XML file.

        Args:
            output_file: Path to output file
            sections_generator: Generator of ProcessedSection objects
        """
        with open(output_file, 'w', encoding='utf-8') as file:
            if self.wrap_in_document:
                file.write("<document>\n")
                
            for section in sections_generator:
                file.write(f"<section title='{section.title}'>\n")
                file.write(section.processed_text)
                file.write("</section>\n")
                
            if self.wrap_in_document:
                file.write("</document>")

def punctuate_text(
    text, 
    source_language: str,
    punctuate_pattern: Optional[Pattern] = None,
    punctuate_model: Optional[str] = None,
    
    ):
    pass

def find_sections(
    text: str,
    source_language: str = None,
    section_pattern: Optional[Pattern] = None,
    section_model: Optional[str] = None,
    max_tokens: int = DEFAULT_SECTION_TOKENS,
    section_count: int = DEFAULT_SECTION_COUNT,
    review_count: int = DEFAULT_REVIEW_COUNT,
    template_dict: Optional[Dict] = None
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
        
    if source_language is None:
        source_language = get_language(text)
        
    section_scanner = OpenAIProcessor(model=section_model, max_tokens=max_tokens)
    parser = SectionParser(
        section_scanner=section_scanner,
        section_pattern=section_pattern,
        section_count=section_count,
        review_count=review_count
    )
    
    return parser.find_sections(text, source_language, template_dict)

def process_text_by_sections(
    transcript: str,
    text_object: TextObject,
    template_dict: Dict,
    pattern: Optional[Pattern] = None,
    output_file: Optional[Path] = None,
    model: Optional[str] = None,
    output_mode: str = "generator"
) -> Union[Generator[ProcessedSection, None, None], List[ProcessedSection], None]:
    """
    High-level function for processing text sections with configurable output handling.

    Args:
        transcript: Text to process
        text_object: Object containing section definitions
        pattern: Pattern object containing processing instructions
        template_dict: Dictionary for template substitution
        output_file: Optional path to output file
        model: Optional model identifier for processor
        output_mode: One of "generator", "list", or "none"

    Returns:
        Builder, List of ProcessedSection objects, or None based on output_mode
    """
    processor = OpenAIProcessor(model)
    
    if not pattern:
        pattern = get_default_pattern(DEFAULT_XML_FORMAT_PATTERN)
        
    section_processor = XMLSectionProcessor(processor, pattern, template_dict)
    
    sections_output = section_processor.process_sections(
        transcript, 
        text_object,
        output_mode
    )
    
    if output_file:
        if output_mode != "generator":
            sections_output = section_processor.process_sections(
                transcript,
                text_object,
                output_mode="generator"
            )
        section_processor.write_to_file(output_file, sections_output)
    
    return sections_output

def get_default_pattern(name: str):
    manager = PatternManager(PATTERN_REPO)
    
    return manager.load_pattern(name)



# def xml_process_text_by_sections(output_file: Path, 
#                                  transcript: str, 
#                                  section_object: Text,
#                                  pattern: Pattern, 
#                                  template_dict: Dict,
#                                  model: str = None) -> None:
#     """
#     Processes sections of a document by applying provided instructions
#     and writing the results to an output file.

#     Args:
#         output_file (Path): Path to the file where the processed sections will be written.
#         transcript (str): The transcript string
#         section_object: Object containing the sections to process. Each section should have 'start_line', 
#                         'end_line', and 'title' attributes.
#         instructions (str): Instructions for processing each section.

#     Example:
#         process_sections(
#             output_file="output.xml",
#             section_object=my_section_object,
#             instructions="Process section titled '{section_title}' carefully."
#         )
#     """
#     sections = section_object.sections
#     wrapped_transcript = wrap_lines(transcript, number=True)

#     logger.info(f"Sections to process: {len(sections)}")
#     logger.info(f"Section processing pattern: {pattern.name}")

#     with open(output_file, 'w', encoding='utf-8') as file:
#         file.write(output_file, "<document>")
#         for i, section in enumerate(sections):
#             logger.info(f"Processing section {i+1}: '{section.title}'...")

#             # Get original segment of text indicated by section lines
#             original_lines = lines_from_wrapped_text(
#                 wrapped_transcript,  
#                 start=section.start_line,
#                 end=section.end_line,
#                 keep_brackets=False
#             )

#             # Get processing instructions from pattern with template applied
#             section_instructions = pattern.apply_template(template_dict)

#             # Process lines through openai
#             processed_lines = openai_process_text(original_lines, section_instructions, batch=False)

#             # Write lines
#             file.write(processed_lines)

#         file.write(output_file, processed_lines)
#     file.write(output_file, "</document>")
