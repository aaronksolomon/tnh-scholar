from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Literal, NamedTuple, Optional, TypeAlias, Union

from pydantic import BaseModel, Field, model_validator

from tnh_scholar.exceptions import MetadataConflictError, ValidationError
from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.metadata.metadata import Frontmatter, Metadata, ProcessMetadata
from tnh_scholar.text_processing import NumberedText
from tnh_scholar.text_processing.numbered_text import SectionValidationError
from tnh_scholar.utils.file_utils import read_str_from_file, write_str_to_file
from tnh_scholar.utils.lang import get_language_code_from_text

logger = get_child_logger(__name__)


class StorageFormat(Enum):
    TEXT = "text"
    JSON = "json"


StorageFormatType: TypeAlias = Union[StorageFormat, Literal["text", "json"]]


class MergeStrategy(Enum):
    """Strategy for merging metadata."""

    PRESERVE = "preserve"
    UPDATE = "update"
    DEEP_MERGE = "deep"
    FAIL_ON_CONFLICT = "fail"


class _MetadataMerger:
    """Encapsulates metadata merge strategies and provenance handling.

    This helper class implements the strategy pattern for metadata merging,
    keeping merge logic modular and testable. Each merge strategy is isolated
    in its own method for clarity and maintainability.

    Attributes:
        target: The base Metadata instance to merge into
        incoming: The new Metadata to merge from
    """

    def __init__(self, target: Metadata, incoming: Metadata) -> None:
        self.target = target
        self.incoming = incoming

    def merge(self, strategy: MergeStrategy) -> None:
        match strategy:
            case MergeStrategy.PRESERVE:
                self._preserve()
            case MergeStrategy.UPDATE:
                self._update()
            case MergeStrategy.DEEP_MERGE:
                self._deep_merge()
            case MergeStrategy.FAIL_ON_CONFLICT:
                self._fail_on_conflict()
            case _:
                raise ValueError(f"Unknown merge strategy: {strategy}")

    def add_provenance(self, source: str, strategy: MergeStrategy) -> None:
        provenance = self.target.get("_provenance", [])
        if not isinstance(provenance, list):
            provenance = []
        provenance.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "source": source,
                "strategy": strategy.value,
                "keys_added": list(self.incoming.keys()),
            }
        )
        self.target["_provenance"] = provenance
        # NOTE: Provenance is intentionally unbounded for this interim implementation to unblock tnh-gen.
        # Future work should consider capping or deduplicating provenance entries to avoid unbounded growth.

    def _preserve(self) -> None:
        for key, value in self.incoming.items():
            if key not in self.target:
                self.target[key] = value

    def _update(self) -> None:
        self.target.update(self.incoming)

    def _deep_merge(self) -> None:
        merged_dict = self._deep_merge_dicts(self.target._data, self.incoming._data)
        self.target._data = merged_dict

    def _fail_on_conflict(self) -> None:
        if conflicts := set(self.target.keys()) & set(self.incoming.keys()):
            raise MetadataConflictError(f"Metadata key conflicts: {sorted(conflicts)}")
        self.target.update(self.incoming)

    @staticmethod
    def _deep_merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge dictionaries with list append semantics."""
        result = base.copy()
        for key, value in update.items():
            if key not in result:
                result[key] = value
            elif isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = _MetadataMerger._deep_merge_dicts(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                result[key] = result[key] + value
            else:
                result[key] = value
        return result


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
        """Validate LoadConfig constraints.

        Ensures exactly one source is provided for JSON format using XOR logic.

        Raises:
            ValueError: If JSON format specified without exactly one source
        """
        valid_source = (self.source_str is None) ^ (self.source_file is None)
        if self.format == StorageFormat.JSON and not valid_source:
            raise ValueError("Either source_str or source_file (not both) must be set for JSON format.")

    def get_source_text(self) -> Optional[str]:
        """Get source content as text.

        Reads from source_file if provided, otherwise returns source_str.

        Returns:
            Source text content, or None if neither source is set

        Note:
            This method is primarily used internally by TextObject.load()
            for JSON format loading.
        """
        if self.source_file is not None:
            return str(read_str_from_file(self.source_file))
        return self.source_str


# Core models
class SectionRange(NamedTuple):
    """Represents the line range of a section."""

    start: int  # Start line (inclusive)
    end: int  # End line (Exclusive)


class SectionEntry(NamedTuple):
    """Represents a section with its content during iteration."""

    number: int  # Logical Section number (1 based index)
    title: str  # Section title
    content: str  # Section content
    range: SectionRange  # Section range


class LogicalSection(BaseModel):
    """
    Represents a contextually meaningful segment of a larger text.

    Sections should preserve natural breaks in content
    (explicit section markers, topic shifts, argument development, narrative progression)
    while staying within specified size limits in order to create chunks suitable for AI processing.
    """  # noqa: E501

    start_line: int = Field(..., description="Starting line number that begins this logical segment")
    title: str = Field(..., description="Descriptive title of section's key content")


class AIResponse(BaseModel):
    """Class for dividing large texts into AI-processable segments while
    maintaining broader document context."""

    document_summary: str = Field(
        ..., description="Concise, comprehensive overview of the text's content and purpose"
    )
    document_metadata: str = Field(
        ...,
        description="Available Dublin Core standard metadata in human-readable YAML format",  # noqa: E501
    )
    key_concepts: str = Field(
        ...,
        description="Important terms, ideas, or references that appear throughout the text",  # noqa: E501
    )
    narrative_context: str = Field(
        ..., description="Concise overview of how the text develops or progresses as a whole"
    )
    language: str = Field(..., description="ISO 639-1 language code")
    sections: List[LogicalSection]


@dataclass
class SectionObject:
    """Represents a section of text with computed boundaries and optional metadata.

    SectionObject is used internally by TextObject to track section ranges.
    Unlike LogicalSection (which only has start_line), SectionObject includes
    the computed end boundary.

    Attributes:
        title: Descriptive title of the section
        section_range: Line range (start inclusive, end exclusive)
        metadata: Optional section-specific metadata
    """

    title: str
    section_range: SectionRange
    metadata: Optional[Metadata]

    @classmethod
    def from_logical_section(
        cls, logical_section: LogicalSection, end_line: int, metadata: Optional[Metadata] = None
    ) -> "SectionObject":
        """Create a SectionObject from a LogicalSection with computed end boundary.

        Args:
            logical_section: AI-generated section with start_line and title
            end_line: Computed end boundary (exclusive)
            metadata: Optional metadata for this section

        Returns:
            SectionObject with complete range information
        """
        return cls(
            title=logical_section.title,
            section_range=SectionRange(logical_section.start_line, end_line),
            metadata=metadata,
        )


# This represents the serializable state of a TextObject
class TextObjectInfo(BaseModel):
    """Serializable information about a text and its sections."""

    source_file: Optional[Path] = None  # Original text file path
    language: str
    sections: List[SectionObject]
    metadata: Metadata

    @model_validator(mode="before")
    @classmethod
    def _coerce_metadata(cls, data: Any) -> Any:
        """Coerce raw dict to Metadata instance before Pydantic validation.

        This pre-validator ensures metadata is always a Metadata instance,
        avoiding post-initialization mutation and enabling proper method access
        (to_yaml, add_process_info, etc.).

        Args:
            data: Raw input data dict

        Returns:
            Data with metadata coerced to Metadata instance if needed
        """
        if isinstance(data, dict) and "metadata" in data and isinstance(data["metadata"], dict):
            data = {**data, "metadata": Metadata(data["metadata"])}
        return data

    def model_post_init(self, __context: Any) -> None:
        """Ensure metadata is always a Metadata instance after initialization."""
        if isinstance(self.metadata, dict):
            object.__setattr__(self, "metadata", Metadata(self.metadata))
        elif not isinstance(self.metadata, Metadata):
            raise ValueError(f"Unexpected type for metadata: {type(self.metadata)}")


class SectionBoundaryError(ValidationError):
    """Raised when section boundaries have gaps, overlaps, or out-of-bounds errors.

    Attributes:
        errors: List of SectionValidationError instances from NumberedText
        coverage_report: Coverage statistics (coverage_pct, gaps, overlaps)
    """

    def __init__(
        self,
        errors: List[SectionValidationError],
        coverage_report: Dict[str, Any],
    ):
        self.errors = errors
        self.coverage_report = coverage_report

        # Build human-readable message
        message = (
            f"Section validation failed with {len(errors)} error(s):\n"
            + "\n".join(f"  - {err.message}" for err in errors)
            + f"\n\nCoverage: {coverage_report.get('coverage_pct', 0):.1f}% "
            + f"({coverage_report.get('covered_lines', 0)}/"
            f"{coverage_report.get('total_lines', 0)} lines)"
        )
        if coverage_report.get("gaps"):
            gap_ranges = [f"{start}-{end}" for start, end in coverage_report["gaps"]]
            message += f"\nGaps at lines: {', '.join(gap_ranges)}"
        if coverage_report.get("overlaps"):
            overlap_count = sum(len(o["lines"]) for o in coverage_report["overlaps"])
            message += f"\nOverlapping lines: {overlap_count}"

        # Call TnhScholarError with structured context
        super().__init__(
            message=message,
            context={
                "error_count": len(errors),
                "errors": [
                    {
                        "type": err.error_type,
                        "section_index": err.section_index,
                        "expected_start": err.expected_start,
                        "actual_start": err.actual_start,
                        "message": err.message,
                    }
                    for err in errors
                ],
                "coverage_report": coverage_report,
            },
        )


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
        sections: List of text sections with boundaries
        metadata: Processing and content metadata container

    Example:
        >>> content = NumberedText("Line 1\\nLine 2\\nLine 3")
        >>> obj = TextObject(content, language="en")
    """

    def __init__(
        self,
        num_text: NumberedText,
        language: Optional[str] = None,
        sections: Optional[List[SectionObject]] = None,
        metadata: Optional[Metadata] = None,
        validate_on_init: bool = True,
    ):
        self.num_text = num_text
        self.language = language or get_language_code_from_text(num_text.content)
        self.sections = sections or []
        self.metadata = metadata or Metadata()
        if validate_on_init and self.sections:
            self.validate_sections()

    def __iter__(self) -> Iterator[SectionEntry]:  # type: ignore[override]
        """Iterate through sections, yielding full section information.

        Note: Pydantic BaseModel defines __iter__ for dict-like iteration over fields.
        We override it here for domain-specific section iteration. The type: ignore
        is intentional as we're providing a different iteration interface.
        """
        if not self.sections:
            raise ValueError("No Sections available.")

        for i, section in enumerate(self.sections):
            content = self.num_text.get_segment(section.section_range.start, section.section_range.end)
            yield SectionEntry(
                number=i + 1, title=section.title, range=section.section_range, content=content
            )

    def __str__(self) -> str:
        # Include metadata as frontmatter to preserve provenance/context when serialized.
        return str(Frontmatter.embed(self.metadata, self.content))

    @staticmethod
    def _build_section_objects(
        logical_sections: List[LogicalSection], last_line: int, metadata: Optional[Metadata] = None
    ) -> List[SectionObject]:
        """Convert LogicalSections to SectionObjects with computed end boundaries.

        Each section's end line is computed as the start of the next section,
        or last_line + 1 for the final section. This ensures contiguous coverage.

        Args:
            logical_sections: List of LogicalSection models from AI response
            last_line: Last line number in the text (for final section boundary)
            metadata: Optional metadata to attach to each section

        Returns:
            List of SectionObjects with computed ranges
        """
        section_objects = []

        for i, section in enumerate(logical_sections):
            # For each section, end is either next section's start or last line + 1
            end_line = logical_sections[i + 1].start_line if i < len(logical_sections) - 1 else last_line + 1

            section_objects.append(SectionObject.from_logical_section(section, end_line, metadata))

        return section_objects

    @classmethod
    def from_str(
        cls,
        text: str,
        language: Optional[str] = None,
        sections: Optional[List[SectionObject]] = None,
        metadata: Optional[Metadata] = None,
    ) -> "TextObject":
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

        obj = cls(num_text=numbered_text, language=language, sections=sections, metadata=frontmatter_metadata)
        if metadata:
            obj.merge_metadata(metadata)

        return obj

    @classmethod
    def from_response(
        cls, response: AIResponse, existing_metadata: Metadata, num_text: "NumberedText"
    ) -> "TextObject":
        """Create TextObject from AI response with section boundaries and metadata.

        Extracts sections, language, and metadata from an AI-generated response
        (e.g., from sectioning or translation processing).

        Args:
            response: AIResponse model containing sections and metadata
            existing_metadata: Base metadata to start with
            num_text: NumberedText instance with the text content

        Returns:
            TextObject with sections and merged metadata from AI response

        Note:
            Merges metadata in order: existing → ai_summary/concepts/context → document_metadata
        """
        # Create metadata from response
        ai_metadata = response.document_metadata
        new_metadata = Metadata(
            {
                "ai_summary": response.document_summary,
                "ai_concepts": response.key_concepts,
                "ai_context": response.narrative_context,
            }
        )

        # Convert LogicalSections to SectionObjects
        sections = cls._build_section_objects(
            response.sections,
            num_text.size,
        )

        text = cls(
            num_text=num_text, language=response.language, sections=sections, metadata=existing_metadata
        )
        text.merge_metadata(new_metadata)
        text.merge_metadata(Metadata.from_yaml(ai_metadata))
        return text

    def merge_metadata(
        self,
        new_metadata: Metadata,
        strategy: MergeStrategy = MergeStrategy.PRESERVE,
        source: Optional[str] = None,
    ) -> None:
        """Merge metadata with explicit strategy and optional provenance tracking."""
        if new_metadata is None:
            return

        merger = _MetadataMerger(self.metadata, new_metadata)
        merger.merge(strategy)
        if source:
            merger.add_provenance(source, strategy)

        logger.debug(
            "Merged metadata using %s strategy: %s keys",
            strategy.value,
            len(new_metadata),
        )

    def merge_metadata_legacy(
        self,
        new_metadata: Metadata,
        override: bool = False,
    ) -> None:
        """Deprecated legacy merge interface that maps to MergeStrategy."""
        import warnings

        warnings.warn(
            "merge_metadata(override=...) is deprecated. "
            "Use merge_metadata(strategy=MergeStrategy.UPDATE) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        strategy = MergeStrategy.UPDATE if override else MergeStrategy.PRESERVE
        self.merge_metadata(new_metadata, strategy=strategy)

    def update_metadata(self, **kwargs: Any) -> None:
        """Update metadata with new key-value pairs using PRESERVE strategy.

        Convenience method for adding metadata without overriding existing keys.

        Args:
            **kwargs: Key-value pairs to add to metadata

        Example:
            >>> obj.update_metadata(author="Thich Nhat Hanh", year=2020)
        """
        new_metadata = Metadata(kwargs)
        self.merge_metadata(new_metadata)

    def validate_sections(
        self,
        raise_on_error: bool = True,
    ) -> List[SectionValidationError]:
        """Validate section integrity using NumberedText boundary checks."""
        if not self.sections:
            raise ValueError("No sections set.")

        start_lines = [section.section_range.start for section in self.sections]
        if errors := self.num_text.validate_section_boundaries(start_lines):
            if raise_on_error:
                coverage_report = self.num_text.get_coverage_report(start_lines)
                raise SectionBoundaryError(errors, coverage_report)
            return list(errors)

        return []

    def get_section_content(self, index: int) -> str:
        """Get content for a section by index.

        Args:
            index: Zero-based section index

        Returns:
            Section content as string

        Raises:
            ValueError: If no sections are available
            IndexError: If index is out of range

        Example:
            >>> obj = TextObject(num_text, sections=[...])
            >>> content = obj.get_section_content(0)  # First section
        """
        if not self.sections:
            raise ValueError("No Sections available.")
        if index < 0 or index >= len(self.sections):
            raise IndexError("Section index out of range")

        section = self.sections[index]
        return str(self.num_text.get_segment(section.section_range.start, section.section_range.end))

    def export_info(self, source_file: Optional[Path] = None) -> TextObjectInfo:
        """Export serializable state for persistence.

        Args:
            source_file: Optional path to source file to record in metadata

        Returns:
            TextObjectInfo instance containing serializable state

        Note:
            If source_file is provided, it will be resolved to an absolute path.
        """
        if source_file:
            source_file = source_file.resolve()  # use absolute path for info

        return TextObjectInfo(
            source_file=source_file,
            language=self.language or "unknown",  # Guaranteed by validator but type system doesn't know
            sections=self.sections,
            metadata=self.metadata,
        )

    @classmethod
    def from_info(cls, info: TextObjectInfo, metadata: Metadata, num_text: "NumberedText") -> "TextObject":
        """Create TextObject from serialized info and content.

        Args:
            info: Serialized TextObjectInfo with section and language data
            metadata: Base metadata to merge into the object
            num_text: NumberedText instance with the actual content

        Returns:
            TextObject instance with combined info and metadata

        Example:
            >>> info = TextObjectInfo.model_validate_json(json_str)
            >>> text = read_str_from_file(info.source_file)
            >>> obj = TextObject.from_info(info, Metadata(), NumberedText(text))
        """
        text_obj = cls(
            num_text=num_text, language=info.language, sections=info.sections, metadata=info.metadata
        )

        text_obj.merge_metadata(metadata)
        return text_obj

    @classmethod
    def from_text_file(cls, file: Path) -> "TextObject":
        """Create TextObject from a text file.

        Reads the file and extracts any frontmatter metadata.

        Args:
            file: Path to text file

        Returns:
            TextObject instance with extracted content and metadata

        Example:
            >>> obj = TextObject.from_text_file(Path("document.txt"))
        """
        text_str = read_str_from_file(file)
        return cls.from_str(text_str)

    @classmethod
    def from_section_file(cls, section_file: Path, source: Optional[str] = None) -> "TextObject":
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
                raise ValueError(
                    f"No content available: no source_file specified in section info: {section_file}"
                )

            source_path = Path(info.source_file)
            if not source_path.exists():
                raise FileNotFoundError(f"No content available: Source file not found: {source_path}")

            # Load source from path
            source = read_str_from_file(source_path)

        metadata, content = Frontmatter.extract(source)

        # Create TextObject
        return cls.from_info(info=info, metadata=metadata, num_text=NumberedText(content))

    def save(
        self,
        path: Path,
        output_format: StorageFormatType = StorageFormat.TEXT,
        source_file: Optional[Path] = None,
        pretty: bool = True,
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
            try:
                output_format = StorageFormat(output_format)
            except ValueError as e:
                raise ValueError(
                    f"Invalid output_format '{output_format}'. "
                    f"Valid options are: {[fmt.value for fmt in StorageFormat]}"
                ) from e

        if output_format == StorageFormat.TEXT:
            # Full text output with metadata as frontmatter
            write_str_to_file(path, str(self))

        elif output_format == StorageFormat.JSON:
            # Export serializable state
            info = self.export_info(source_file)
            json_str = info.model_dump_json(indent=2 if pretty else None)
            write_str_to_file(path, json_str)

        else:
            raise ValueError(f"Unknown output_format: {output_format}")

    @classmethod
    def load(cls, path: Path, config: Optional[LoadConfig] = None) -> "TextObject":
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
                source_str="Text content..."
            )
            obj = TextObject.load(Path("state.json"), config)

            # Load state from JSON with source content file
            config = LoadConfig(
                format=StorageFormat.JSON,
                source_file=Path("content.txt")
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
        sections: Optional[List[SectionObject]] = None,
    ) -> "TextObject":
        """
        Return a **new** TextObject with requested changes; does not mutate the original.

        Args:
            data_str: Optional new text content
            language: Optional new language code
            metadata: Metadata to merge into the new object
            process_metadata: Identifier/details for the process performed
            sections: Optional replacement list of sections
        """
        new_num_text = NumberedText(data_str) if data_str is not None else self.num_text
        new_language = language or self.language
        new_sections = deepcopy(sections) if sections is not None else deepcopy(self.sections)
        new_metadata = deepcopy(self.metadata)
        if metadata:
            merger = _MetadataMerger(new_metadata, metadata)
            merger.merge(MergeStrategy.UPDATE)
        if process_metadata:
            new_metadata.add_process_info(process_metadata)

        return TextObject(
            num_text=new_num_text,
            language=new_language,
            sections=new_sections,
            metadata=new_metadata,
        )

    @property
    def section_count(self) -> int:
        """Get the total number of sections.

        Returns:
            Number of sections, or 0 if no sections defined
        """
        return len(self.sections) if self.sections else 0

    @property
    def last_line_num(self) -> int:
        """Get the last line number in the text.

        Returns:
            Last line number (1-based indexing)
        """
        return int(self.num_text.size)

    @property
    def content(self) -> str:
        """Get the raw text content without line numbers.

        Returns:
            Plain text content as string
        """
        return str(self.num_text.content)

    @property
    def metadata_str(self) -> str:
        """Get metadata as YAML-formatted string.

        Returns:
            YAML representation of metadata

        Example:
            >>> print(obj.metadata_str)
            author: Thich Nhat Hanh
            language: en
        """
        return str(self.metadata.to_yaml())

    @property
    def numbered_content(self) -> str:
        """Get text content with line numbers prefixed.

        Returns:
            Text with line numbers in format "  1 | line content"

        Example:
            >>> print(obj.numbered_content)
              1 | First line
              2 | Second line
        """
        return str(self.num_text.numbered_content)
