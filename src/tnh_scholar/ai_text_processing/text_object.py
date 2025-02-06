from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    NamedTuple,
    Optional,
)

from pydantic import BaseModel, Field

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.text_processing import NumberedText

logger = get_child_logger(__name__)

# Core models
class SectionRange(NamedTuple):
    """Represents the line range of a section."""
    start: int  # Start line (inclusive)
    end: int    # End line (Exclusive)
    
class SectionEntry(NamedTuple):
    """Represents a section with its content during iteration."""
    number: int         # Logical Section number (1 based index)
    title: str          # Section title 
    content: str        # Section content
    range: SectionRange # Section range

class LogicalSection(BaseModel):
    """
    Represents a contextually meaningful segment of a larger text.
    
    Sections should preserve natural breaks in content 
    (e.g., explicit section markers, topic shifts, argument development, narrative progression) 
    while staying within specified size limits in order to create chunks suitable for AI processing.
    """
    start_line: int = Field(
        ..., 
        description="Starting line number that begins this logical segment"
    )
    title: str = Field(
        ...,
        description="Descriptive title of section's key content"
    )

# This represents the serializable state of a TextObject
class TextObjectInfo(BaseModel):
    """Serializable information about a text and its sections."""
    source_file: Optional[Path] = None  # Original text file path
    language: str
    sections: List[LogicalSection]
    metadata: Dict[str, Any]
            
class TextObjectResponse(BaseModel):
    """Text Object for dividing large texts into AI-processable segments while
    maintaining broader document context."""
    document_summary: str = Field(
        ...,
        description="Concise, comprehensive overview of the text's content and purpose"
    )
    document_metadata: str = Field(
        ...,
        description="Available Dublin Core standard metadata in human-readable format"
    )
    key_concepts: str = Field(
        ...,
        description="Important terms, ideas, or references that appear throughout the text"
    )
    narrative_context: str = Field(
        ...,
        description="Concise overview of how the text develops or progresses as a whole"
    )
    language: str = Field(..., description="ISO 639-1 language code")
    sections: List[LogicalSection]

class TextObject:
    """Core text management with implicit section boundaries."""
    def __init__(self, 
             content: 'NumberedText', 
             language: str, 
             sections: List[LogicalSection],
             metadata: Optional[Dict[str, Any]] = None):
        """
        Create a TextObject with required content and sections.
        
        Args:
            content: Text content as NumberedText
            language: ISO language code
            sections: List of sections (must contain at least one)
            metadata: Optional metadata dictionary
        """
        self.content = content
        self.language = language
        self.sections = sections
        self._metadata = metadata or {}
        self._ranges: List[SectionRange] = self._calculate_ranges()
        
        self.validate_sections()
        logger.debug(f"TextObject ranges: {self._ranges}")
        
    
    def __iter__(self) -> Iterator[SectionEntry]:
        """Iterate through sections, yielding full section information."""
        if not self._ranges:
            self._calculate_ranges()
            
        for i, (section, range) in enumerate(zip(self.sections, self._ranges)):
            content = self.get_section_content(i)
            yield SectionEntry(
                number=i+1,
                title=section.title,
                range=range,
                content=content
            )
            
    def _calculate_ranges(self) -> List[SectionRange]:
        """Calculate and cache the line ranges for all sections."""
        ranges = []
        for i, section in enumerate(self.sections):
            start = section.start_line
            # End is either the next section's start, or the last line +1 (exclusive endpoints)
            end = (self.sections[i + 1].start_line  
                  if i < self.section_count - 1 
                  else self.last_line + 1)
            ranges.append(SectionRange(start, end))
        return ranges
            
    @classmethod
    def from_response(cls, response: TextObjectResponse, content: 'NumberedText') -> 'TextObject':
        """Create TextObject from AI response format."""
        obj = cls(content=content, language=response.language, sections=response.sections)
        
        # Store metadata from response (basic for PoC)
        obj._metadata = {
            "ai_summary": response.document_summary,
            "ai_metadata": response.document_metadata,
            "ai_concepts": response.key_concepts,
            "ai_context": response.narrative_context
        }
        return obj

    def validate_sections(self) -> None:
        """Basic validation of section integrity."""
        if not self.sections:
            raise ValueError("TextObject must have at least one section")
            
        # Check section ordering and bounds
        for i, section in enumerate(self.sections):
            if section.start_line < 1:
                logger.warning(f"Section {i}: start line must be >= 1")
                section.start_line = 1
            if section.start_line > self.content.size:
                logger.warning(f"Section {i}: start line exceeds text length")
                section.start_line = self.content.size
            if i > 0 and section.start_line <= self.sections[i-1].start_line:
                logger.warning(f"Section {i}: non-sequential start line")
                section.start_line = self.sections[i-1].start_line + 1

    def get_section_content(self, index: int) -> str:
        """Get content for a section using cached ranges."""            
        if index < 0 or index >= len(self.sections):
            raise IndexError("Section index out of range")
            
        sect_range = self._ranges[index]
        return self.content.get_segment(sect_range.start, sect_range.end)  
        
    def export_info(self, source_file: Optional[Path] = None) -> TextObjectInfo:
        """Export serializable state."""
        if source_file:
            source_file = source_file.resolve() # use absolute path for info
            
        return TextObjectInfo(
            source_file=source_file,
            language=self.language,
            sections=self.sections,
            metadata=self.metadata
        )
        
    @classmethod
    def from_info(cls, info: TextObjectInfo, content: 'NumberedText') -> 'TextObject':
        """Create TextObject from info and content."""
        return cls(content=content, 
                   language=info.language, 
                   sections=info.sections, 
                   metadata=info.metadata)
    
    @classmethod
    def from_section_file(
        cls, 
        section_file: Path, 
        content: Optional[NumberedText] = None
        ) -> 'TextObject':
        """
        Create TextObject from a section info file, loading content from source_file.
        
        Args:
            section_file: Path to JSON file containing TextObjectInfo
            content: Optional content in case no content file is found.
            
        Returns:
            TextObject instance
            
        Raises:
            ValueError: If source_file is missing from section info
            FileNotFoundError: If either section_file or source_file not found
        """
        # Check section file exists
        if not section_file.exists():
            raise FileNotFoundError(f"Section file not found: {section_file}")
            
        # Load and parse section info
        info = TextObjectInfo.model_validate_json(section_file.read_text())
        
        if not content:  # passed content always takes precedence over source_file
            # check if source file exists
            if not info.source_file:
                raise ValueError(f"No content available: no source_file specified "
                                 f"in section info: {section_file}")
            
            source_path = Path(info.source_file)
            if not source_path.exists():
                raise FileNotFoundError(
                    f"No content available: Source file not found: {source_path}"
                    )
            
            # Load content into NumberedText
            content = NumberedText(source_path.read_text())
        
        # Create TextObject
        return cls.from_info(info, content)
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Access to metadata dictionary."""
        return self._metadata.copy()  # Return copy to prevent direct modification
    
    @property
    def section_count(self) -> int:
        return len(self.sections)
    
    @property
    def last_line(self) -> int:
        return self.content.size
    
    