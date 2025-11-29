from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Iterator,
    List,
    Literal,
    NamedTuple,
    Optional,
    Self,
    TypeAlias,
    Union,
)

from pydantic import BaseModel, Field

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.metadata.metadata import Frontmatter, Metadata, ProcessMetadata
from tnh_scholar.text_processing import NumberedText
from tnh_scholar.utils.file_utils import read_str_from_file, write_str_to_file
from tnh_scholar.utils.lang import get_language_code_from_text

logger = get_child_logger(__name__)

class StorageFormat(Enum):
    TEXT = "text"
    JSON = "json"
    
StorageFormatType: TypeAlias = Union[StorageFormat, Literal["text", "json"]]

@dataclass(frozen=True)
class LoadConfig:
    """Configuration for loading a TextObject.
    
    Attributes:
        format: Storage format of the input file
        source_str: Optional source content as string
        source_file: Optional path to source content file
        
    Note:
        For JSON format, exactly one of source_str or source_file may be provided.
        Both fields are ignored for TEXT format.
    """
    format: StorageFormat = StorageFormat.TEXT
    source_str: Optional[str] = None
    source_file: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration."""
        valid_source = (
            (self.source_str is None) ^ (self.source_file is None)
        )
        if self.format == StorageFormat.JSON and not valid_source:
            raise ValueError(
                "Either source_str or source_file (not both) "
                "must be set for JSON format."
            )
    
    def get_source_text(self) -> Optional[str]:
        """Get source content as text if provided."""
        if self.source_file is not None:
            return read_str_from_file(self.source_file)
        return self.source_str
    
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
    (explicit section markers, topic shifts, argument development, narrative progression) 
    while staying within specified size limits in order to create chunks suitable for AI processing.
    """  # noqa: E501
    start_line: int = Field(
        ..., 
        description="Starting line number that begins this logical segment"
    )
    title: str = Field(
        ...,
        description="Descriptive title of section's key content"
    )

            
class AIResponse(BaseModel):
    """Class for dividing large texts into AI-processable segments while
    maintaining broader document context."""
    document_summary: str = Field(
        ...,
        description="Concise, comprehensive overview of the text's content and purpose"
    )
    document_metadata: str = Field(
        ...,
        description="Available Dublin Core standard metadata in human-readable YAML format" # noqa: E501
    )
    key_concepts: str = Field(
        ...,
        description="Important terms, ideas, or references that appear throughout the text"  # noqa: E501
    )
    narrative_context: str = Field(
        ...,
        description="Concise overview of how the text develops or progresses as a whole"
    )
    language: str = Field(..., description="ISO 639-1 language code")
    sections: List[LogicalSection]
    
@dataclass
class SectionObject:
    """Represents a section of text with metadata."""
    title: str
    section_range: SectionRange
    metadata: Optional[Metadata] 

    @classmethod
    def from_logical_section(
        cls, 
        logical_section: LogicalSection, 
        end_line: int, 
        metadata: Optional[Metadata] = None
        ) -> "SectionObject":
        """Create a SectionObject from a LogicalSection model."""
        return cls(
            title=logical_section.title,
            section_range = SectionRange(logical_section.start_line, end_line),
            metadata = metadata 
        )

# This represents the serializable state of a TextObject
class TextObjectInfo(BaseModel):
    """Serializable information about a text and its sections."""
    source_file: Optional[Path] = None  # Original text file path
    language: str
    sections: List[SectionObject]
    metadata: Metadata
    
    def model_post_init(self, __context: Any) -> None:
        """Ensure metadata is always a Metadata instance after initialization."""
        if isinstance(self.metadata, dict):
            self.metadata = Metadata(self.metadata)
        elif not isinstance(self.metadata, Metadata):
            raise ValueError(f"Unexpected type for metadata: {type(self.metadata)}")

class TextObject:
    """
    Manages text content with section organization and metadata tracking.
    
    TextObject serves as the core container for text processing, providing:
    - Line-numbered text content management
    - Language identification
    - Section organization and access
    - Metadata tracking including incorporated processing stages
    
    The class allows for section boundaries through line numbering,
    allowing sections to be defined by start lines without explicit end lines.
    Subsequent sections implicitly end where the next section begins.
    SectionObjects are utilized to represent sections.
    
    Attributes:
        num_text: Line-numbered text content manager
        language: ISO 639-1 language code for the text content
        _sections: Internal list of text sections with boundaries
        _metadata: Processing and content metadata container
        
    Example:
        >>> content = NumberedText("Line 1\\nLine 2\\nLine 3")
        >>> obj = TextObject(content, language="en")
    """
    num_text: NumberedText 
    language: str 
    _sections: List[SectionObject]
    _metadata: Metadata
    
    def __init__(self, 
        num_text: NumberedText, 
        language: Optional[str] = None, 
        sections: Optional[List[SectionObject]] = None,
        metadata: Optional[Metadata] = None):
        """
        Initialize a TextObject with content and optional organizing components.
        
        Args:
            num_text: Text content with line numbering
            language: ISO 639-1 language code. If None, auto-detected from content
            sections: Initial sections defining text organization. If None, 
                      text is considered un-sectioned.
            metadata: Initial metadata. If None, creates empty metadata container
            
        Note:
            Until sections are established, section-based methods will raise a value
            error if called.
        """
        self.num_text = num_text
        self.language = language or get_language_code_from_text(num_text.content)
        self._sections = sections or []
        self._metadata = metadata or Metadata()
        
        if sections:
            self.validate_sections()
        
    
    def __iter__(self) -> Iterator[SectionEntry]:
        """Iterate through sections, yielding full section information."""
        if not self._sections:
            raise ValueError("No Sections available.")
        
        for i, section in enumerate(self._sections):
            content = self.num_text.get_segment(
                section.section_range.start, 
                section.section_range.end
            )
            yield SectionEntry(
                number=i+1,
                title=section.title,
                range=section.section_range,
                content=content
            )
    
    def __str__(self) -> str:
        return Frontmatter.embed(self.metadata, self.content)

    @staticmethod
    def _build_section_objects(
        logical_sections: List[LogicalSection], 
        last_line: int,
        metadata: Optional[Metadata] = None
    ) -> List[SectionObject]:
        """Convert LogicalSections to SectionObjects with proper ranges."""
        section_objects = []
        
        for i, section in enumerate(logical_sections):
            # For each section, end is either next section's start or last line + 1
            end_line = (logical_sections[i + 1].start_line 
                    if i < len(logical_sections) - 1 
                    else last_line + 1)
            
            section_objects.append(
                SectionObject.from_logical_section(section, end_line, metadata)
            )
            
        return section_objects
    
    @classmethod
    def from_str(
        cls,
        text: str,
        language: Optional[str] = None,
        sections: Optional[List[SectionObject]] = None,
        metadata: Optional[Metadata] = None
    ) -> 'TextObject':
        """
        Create a TextObject from a string, extracting any frontmatter.
        
        Args:
            text: Input text string, potentially containing frontmatter
            language: ISO language code
            sections: List of section objects
            metadata: Optional base metadata to merge with frontmatter
        
        Returns:
            TextObject instance with combined metadata
        """
        # Extract any frontmatter and merge with provided metadata
        frontmatter_metadata, content = Frontmatter.extract(text)
        
        # Create NumberedText from content without frontmatter
        numbered_text = NumberedText(content)
        
        obj = cls(
            num_text=numbered_text,
            language=language,
            sections=sections,
            metadata=frontmatter_metadata
        )
        if metadata:
            obj.merge_metadata(metadata)
            
        return obj
        
        
    @classmethod
    def from_response(
        cls, 
        response: AIResponse,
        existing_metadata: Metadata,
        num_text: 'NumberedText'
    ) -> 'TextObject':
        """Create TextObject from AI response format."""
        # Create metadata from response
        ai_metadata = response.document_metadata
        new_metadata = Metadata({
            "ai_summary": response.document_summary,
            "ai_concepts": response.key_concepts,
            "ai_context": response.narrative_context
        })
        
        # Convert LogicalSections to SectionObjects
        sections = cls._build_section_objects(
            response.sections, 
            num_text.size,
        )
        
        text = cls(
            num_text=num_text,
            language=response.language,
            sections=sections,
            metadata=existing_metadata
        )
        text.merge_metadata(new_metadata)
        text.merge_metadata(Metadata.from_yaml(ai_metadata))
        return text

    def merge_metadata(self, new_metadata: Metadata, override=False) -> None:
        """
        Merge new metadata with existing metadata.
        
        For now, performs simple dict-like union (|=) but can be extended 
        to handle more complex merging logic in the future (e.g., merging 
        nested structures, handling conflicts, merging arrays).
        
        Args:
        new_metadata: Metadata to merge with existing metadata
        override: If True, new_metadata values override existing values
                            If False, existing values are preserved
        """
        # Currently using simple dict union
        # Future implementations might handle:
        # - Deep merging of nested structures
        # - Special handling of specific fields
        # - Array/list merging strategies
        # - Conflict resolution
        # - Metadata versioning
        if not new_metadata:
            return
        
        if override:
            self._metadata |= new_metadata  # new overrides existing
        else:
            self._metadata = new_metadata | self._metadata # existing values preserved

        logger.debug("Merging new metadata into TextObject")

    def update_metadata(self, **kwargs) -> None:
        """Update metadata with new key-value pairs."""
        new_metadata = Metadata(kwargs)
        self.merge_metadata(new_metadata)
    
    def validate_sections(self) -> None:
        """Basic validation of section integrity."""
        if not self._sections:
            raise ValueError("No sections set.")
            
        # Check section ordering and bounds
        for i, section in enumerate(self._sections):
            if section.section_range.start < 1:
                logger.warning(f"Section {i}: start line must be >= 1")
            if section.section_range.start > self.num_text.size:
                logger.warning(f"Section {i}: start line exceeds text length")
            if i > 0 and \
                section.section_range.start <= self._sections[i-1].section_range.start:
                logger.warning(f"Section {i}: non-sequential start line")

    def get_section_content(self, index: int) -> str:     
        if not self._sections:
            raise ValueError("No Sections available.")
        """Get content for a section."""            
        if index < 0 or index >= len(self._sections):
            raise IndexError("Section index out of range")
                
        section = self._sections[index]
        return self.num_text.get_segment(
            section.section_range.start, 
            section.section_range.end
        )
        
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
    def from_info(
        cls, 
        info: TextObjectInfo, 
        metadata: Metadata, 
        num_text: 'NumberedText'
        ) -> 'TextObject':
        """Create TextObject from info and content."""
        text_obj = cls(
            num_text=num_text, 
            language=info.language, 
            sections=info.sections, 
            metadata=info.metadata
            )
        
        text_obj.merge_metadata(metadata)
        return text_obj
    
    @classmethod
    def from_text_file(
        cls,
        file: Path
    ) -> 'TextObject':
        text_str = read_str_from_file(file)
        return cls.from_str(text_str)
            
    @classmethod
    def from_section_file(
        cls, 
        section_file: Path, 
        source: Optional[str] = None
        ) -> 'TextObject':
        """
        Create TextObject from a section info file, loading content from source_file.
        Metadata is extracted from the source_file or from content.
        
        Args:
            section_file: Path to JSON file containing TextObjectInfo
            source: Optional source string in case no source file is found.
            
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
        info = TextObjectInfo.model_validate_json(read_str_from_file(section_file))
        
        if not source:  # passed content always takes precedence over source_file
            # check if source file exists
            if not info.source_file:
                raise ValueError(f"No content available: no source_file specified "
                                 f"in section info: {section_file}")
            
            source_path = Path(info.source_file)
            if not source_path.exists():
                raise FileNotFoundError(
                    f"No content available: Source file not found: {source_path}"
                    )
            
            # Load source from path
            source = read_str_from_file(source_path)
        
        metadata, content = Frontmatter.extract(source)
        
        # Create TextObject
        return cls.from_info(info=info, 
                             metadata=metadata, 
                             num_text=NumberedText(content)
                             )
    
    def save(
        self,
        path: Path,
        output_format: StorageFormatType = StorageFormat.TEXT,
        source_file: Optional[Path] = None,
        pretty: bool = True
        ) -> None:
        """
        Save TextObject to file in specified format.
        
        Args:
            path: Output file path
            output_format: "text" for full content+metadata or "json" for serialized state
            source_file: Optional source file to record in metadata
            pretty: For JSON output, whether to pretty print
        """
        if isinstance(output_format, str):
            output_format = StorageFormat(output_format)
            
        if output_format == StorageFormat.TEXT:
            # Full text output with metadata as frontmatter
            write_str_to_file(path, str(self))
            
        elif output_format == StorageFormat.JSON:
            # Export serializable state
            info = self.export_info(source_file)
            json_str = info.model_dump_json(indent=2 if pretty else None)
            write_str_to_file(path, json_str)
            
    @classmethod
    def load(
        cls,
        path: Path,
        config: Optional[LoadConfig] = None
    ) -> 'TextObject':
        """
        Load TextObject from file with optional configuration.
        
        Args:
            path: Input file path
            config: Optional loading configuration. If not provided,
                loads directly from text file.
                
        Returns:
            TextObject instance
                
        Usage:
            # Load from text file with frontmatter
            obj = TextObject.load(Path("content.txt"))
                
            # Load state from JSON with source content string
            config = LoadConfig(
                format=StorageFormat.JSON,
                source_content="Text content..."
            )
            obj = TextObject.load(Path("state.json"), config)
            
            # Load state from JSON with source content file
            config = LoadConfig(
                format=StorageFormat.JSON,
                source_content=Path("content.txt")
            )
            obj = TextObject.load(Path("state.json"), config)
        """
        # Use default config if none provided
        config = config or LoadConfig()
                
        if config.format == StorageFormat.TEXT:
            return cls.from_text_file(path)
                
        elif config.format == StorageFormat.JSON:
            return cls.from_section_file(path, source=config.get_source_text())
        
        else:
            raise ValueError("Unknown load configuration format.")
    
    def transform(
        self,
        data_str: Optional[str] = None,
        language: Optional[str] = None, 
        metadata: Optional[Metadata] = None,
        process_metadata: Optional[ProcessMetadata] = None,
        sections: Optional[List[SectionObject]] = None
    ) -> Self:
        """Update TextObject content and metadata in place.
        
        Optionally modifies the object's content, language, and adds process tracking.
        Process history is maintained in metadata.
        
        Args:
            data_str: New text content
            language: New language code  
            metadata: Metadata to merge into the object
            process_metadata: Identifier and details for the process performed
            sections: Optional replacement list of sections
        """
        # Update potentially changed elements
        if data_str:
            self.num_text = NumberedText(data_str)
        if language:
            self.language = language
        if metadata:
            self.merge_metadata(metadata)
        if process_metadata:    
            self._metadata.add_process_info(process_metadata)
        if sections:
            self._sections = sections
        
        return self
    
    @property
    def metadata(self) -> Metadata:
        """Access to metadata dictionary."""
        return self._metadata  
    
    @property
    def section_count(self) -> int:
        return len(self._sections) if self._sections else 0
    
    @property
    def last_line_num(self) -> int:
        return self.num_text.size
    
    @property
    def sections(self) -> List[SectionObject]:
        """Access to sections list."""
        return self._sections or []
    
    @property
    def content(self) -> str:
        return self.num_text.content
    
    @property
    def metadata_str(self) -> str:
        return self.metadata.to_yaml()
    
    @property
    def numbered_content(self) -> str:
        return self.num_text.numbered_content
