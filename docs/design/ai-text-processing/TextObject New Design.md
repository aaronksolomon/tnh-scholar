# TextObject System Design Document

## 1. Overview and Purpose

The TextObject system manages the division of large texts into processable segments while maintaining contextual integrity. It serves two key purposes:

Primary Goal:

- Enable AI processing of large texts by breaking them into manageable chunks
- Preserve essential context across segmentation boundaries
- Provide rich contextual information to compensate for segmentation

Secondary Goal:

- Maintain structured metadata for human analysis and documentation
- Support standard metadata practices (Dublin Core)
- Enable systematic text processing workflows

## 2. Core Components

### 2.1 Response Format (API Layer)

The response format is optimized for AI interaction, emphasizing human-readable context:

```python
class LogicalSection(BaseModel):
    """Represents a contextually meaningful segment of a larger text.
    
    Sections should preserve natural breaks in content (e.g., explicit section markers, topic shifts,
    argument development, narrative progression) while staying within specified size limits 
    in order to create chunks suitable for AI processing."""
    start_line: int = Field(
        ..., 
        description="Starting line number that begins this logical segment"
    )
    title: str = Field(
        ...,
        description="Descriptive title of section's key content"
    )

class TextObjectResponse(BaseModel):
    """Format for dividing large texts into AI-processable segments while
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
```

Key Design Points:

- Separates document-level context into distinct conceptual units
- Uses human-readable format for metadata and context
- Maintains simple section structure for reliable AI processing

### 2.2 Internal Representation

The internal system uses a richer structure based on Dublin Core standards:

```python
class TextMetadata(BaseModel):
    """Rich metadata container following Dublin Core standards."""
    
    # Core Dublin Core elements with validation
    title: str
    creator: List[str]
    subject: List[str]
    description: str
    publisher: Optional[str] = None
    contributor: List[str] = Field(default_factory=list)
    date: Optional[str] = None
    type: str
    format: str
    identifier: Optional[str] = None
    source: Optional[str] = None
    language: str
    
    # Additional fields
    context: str = ""
    additional_info: Dict[str, Any] = Field(default_factory=dict)
    
    # Custom fields can be added through additional_info
    
    class Config:
        """Pydantic model configuration."""
        extra = 'allow'  # Allows additional fields beyond those specified
        
    def to_dublin_core(self) -> Dict[str, Any]:
        """Extract Dublin Core fields as dictionary."""
        return self.model_dump(
            exclude={'context', 'additional_info'},
            exclude_none=True
        )
```

## 3. Key Design Decisions

### 3.1 Dual-Layer Design

1. AI Interface Layer (TextObjectResponse)
   - Optimized for AI processing
   - Human-readable context
   - Simplified structure

2. Internal Layer (TextObject)
   - Strict validation
   - Structured metadata
   - Rich processing capabilities

### 3.2 Metadata Approach

1. AI Format
   - Narrative document summary
   - Human-readable metadata
   - Context and key concepts separated
   - Focus on information relevant for processing

2. Internal Format
   - Structured Dublin Core metadata
   - Additional context storage
   - Extensible design

### 3.3 Content Integration

Content management is delegated to NumberedText class:

- Clean separation of concerns
- Efficient text storage and access
- Section-aware interface

## 4. Existing implementation details

### 4.1 Section Access

```python
def get_section_content(self, index: int) -> str:
    """Retrieve content for specific section."""
    start = self.sections[index].start_line
    end = (self.sections[index + 1].start_line 
           if index < len(self.sections) - 1 
           else self.total_lines + 1)
    return self.content.get_segment(start, end)
```

### 4.2 Validation of TextObject

```python
def _validate(self) -> None:
    """Validate section integrity."""
    if not self.sections:
        raise ValueError("TextObject must have at least one section")
        
    # Validate section ordering
    for i, section in enumerate(self.sections):
        if section.start_line < 1:
            raise ValueError(f"Section {i}: start line must be >= 1")
        if section.start_line > self.total_lines:
            raise ValueError(f"Section {i}: start line exceeds text length")
        if i > 0 and section.start_line <= self.sections[i-1].start_line:
            raise ValueError(f"Section {i}: non-sequential start line")
```

## 6. Future Considerations

1. Performance Optimization
   - Index sections for faster access
   - Optimize metadata string parsing

2. Extended Functionality
   - Section manipulation (merge/split)
   - Advanced metadata querying
   - Enhanced validation rules

3. Integration Enhancements
   - Expanded AI context generation
   - Bulk processing capabilities

This validation strategy ensures data integrity while providing clear feedback for both programmatic and human review of processing results.