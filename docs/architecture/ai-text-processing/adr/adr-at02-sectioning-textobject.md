---
title: "ADR-AT02: TextObject Architecture Decision Records"
description: "Captures the historical TextObject design comparisons and links to the original/new design documents."
owner: ""
author: ""
status: archived
created: "2025-02-01"
---
# ADR-AT02: TextObject Architecture Decision Records

Summarizes the historical TextObject designs and the documents preserved for reference.

- **Status**: Accepted
- **Date**: 2025-02-01

### Context

During documentation efforts, we created a "greenfield" design document for TextObject without fully accounting for the existing implementation. This resulted in having both an as-built design and a potential alternative design that suggests simplifications.

### Decision

We will maintain three documents:

1. `design/textobject-original-design.md` - Documents the original implementation
2. `design/textobject-new-design.md` - Records the simpler new design
3. This ADR file - Explains the context and tracks future decisions

### Consequences

- Clear separation between actual and planned future designs
- Preserved thinking about potential simplifications
- Minimal documentation overhead by keeping related docs focused

## ADR 002: Current TextObject Implementation Design

### Status

Accepted

### Context

The TextObject system was implemented to provide structured text handling with explicit section boundaries and metadata support.

### Decision

Key design points of current implementation:

1. Sections have explicit start_line and end_line
2. LogicalSection uses Pydantic BaseModel
3. Metadata follows Dublin Core standards
4. Strong integration with NumberedText for line management
5. ISO 639-1 language codes used but not strictly validated

### Consequences

- More explicit section control but higher validation complexity
- Clear contract through Pydantic models
- Flexible metadata handling

## ADR 003: New TextObject Design Consideration

### Status

Accepted

### Context

During documentation, a simpler design was conceived that would reduce complexity through implicit section boundaries. Additionally section metadata and contextual data could be added to convey/preserve important information for users and for AI assistants.

### Decision

Key points of alternative design:

1. Sections defined only by start_line
2. End lines implicit (next section's start - 1)
3. Guaranteed contiguous coverage
4. Simplified validation
5. Addition of metadata and context fields
6. Separation of concerns for a TextObject (general representation) and TextObjectFormat (for API use).

This design is preserved for consideration in future refactoring.

### Consequences

- Would simplify section management
- Would require migration effort
- Trade-off between explicitness and simplicity

## ADR 004: TextObject Re-Design Decisions

### Status

Accepted

### Context

The TextObject new design specification proposes some significant changes from existing implementations, particularly around section handling, while some aspects of metadata and language handling need clarification for the prototype phase.

### Decisions

#### 1. Language Code Handling

- Language code validation (ISO 639-1 compliance) is deferred to production phase
- Prototype accepts any string value for language codes

#### 2. Metadata Requirements

- No minimum required metadata fields for prototype phase
- Will establish standard placeholder value for unset fields:
  - None for optional fields
  - Empty string for required strings
  - Empty lists for collections
- Metadata validation deferred to production phase

#### 3. NumberedText Integration

- TextObject maintains immutable reference to its NumberedText instance
- No modifications to line numbers allowed after TextObject creation

### Consequences

#### Positive

- Simpler section management through implicit end lines
- Reduced validation complexity
- Guaranteed contiguous sections by design
- Clear separation from current implementation for migration planning

#### Negative

- Will require migration from current dual start_line/end_line model
- Cannot explicitly represent gaps between sections (if that was ever needed)

#### Neutral

- Tools using TextObject will need to adapt to new section model
- May need transition period supporting both models

### Related

- Original TextObject.md design specification
- Current response_format.py implementation
- tnh-fab implementation requirements

## ADR 005: TextObject Metadata Management and Processing Pipeline

### Status

Proposed

### Context

The TextObject system needs to handle metadata consistently across different processing workflows while maintaining simplicity for the prototype phase. Two main workflows exist:

1. AI-based section generation and processing
2. Pattern-based section generation for large texts

Key challenges include:

- Consistent metadata handling across workflows
- Metadata extraction from various sources
- Maintaining processable sections with context
- Supporting very large texts
- Balancing simplicity with extensibility

### Decision

#### 1. Metadata Format and Storage

- Use YAML frontmatter as the standard metadata format
- Base metadata structure on Dublin Core standards
- Generate metadata only once at start of pipeline
- Store metadata separately from content body

#### 2. Metadata Processing Strategy

Simple, predictable process with clear precedence:

```plaintext
if YAML frontmatter exists:
    use existing metadata as authoritative
    run AI metadata extraction for validation
    if differences found:
        log warning showing differences
        retain existing metadata
else:
    if other metadata format detected:
        log warning about potential conflict
    extract head/tail sections
    generate metadata via AI processing
    add YAML frontmatter
```

#### 3. Minimal Metadata Requirements

Guarantee basic metadata fields:

- title
- description
- language
- date
- identifier

#### 4. Processing Pipeline Structure

Standard pipeline for all workflows:

```plaintext
Metadata Management → Text Analysis → Section Generation → Section Processing → Assembly
```

#### 5. Text Analysis Strategies for Investigation

Multiple approaches should be tested to determine optimal text analysis strategy. Key considerations include processing efficiency, metadata quality, and handling of different text structures.

##### Proposed Analysis Methods

1. Token-Based Approach
   - Define boundaries by token count
   - Consider GPT token encoding specifics
   - Test various token thresholds
   - Evaluate impact on metadata quality

2. Line-Based Approach
   - Use natural line breaks
   - Test fixed line counts vs. percentage
   - Consider paragraph boundaries
   - Evaluate handling of different line lengths

3. Size-Based Approach
   - Use file size for initial categorization
   - Test different size thresholds
   - Consider memory efficiency
   - Evaluate processing speed

4. Structural Approach
   - Detect document structure (headings, sections)
   - Use natural document divisions
   - Consider format-specific markers
   - Test robustness across document types

##### Testing Requirements

1. Metrics to Evaluate
   - Metadata extraction quality
   - Processing time
   - Token usage efficiency
   - Memory requirements
   - Accuracy across document types

2. Test Scenarios
   - Very small documents (< 1000 tokens)
   - Standard documents (1000-5000 tokens)
   - Large documents (5000-128,000 tokens)
   - Very large documents (>128,000 tokens)
   - Documents with varying structures
   - Multi-language documents

3. Success Criteria
   - Consistent metadata quality
   - Predictable performance
   - Resource efficiency
   - Reliable handling of edge cases

##### Implementation Note

Initial implementation should support multiple analysis strategies to facilitate testing and comparison. Results will inform the final strategy selection.

### Consequences

#### Positive

- Consistent metadata handling across system
- Simple, predictable metadata generation
- Clear separation of metadata and content
- Support for future extensions
- Leverages existing tools and standards
- Minimal complexity in prototype phase

#### Negative

- May need to refactor for more complex metadata needs
- Limited handling of non-YAML metadata
- Potential for metadata conflicts in some cases
- Head/tail analysis may miss important metadata

#### Neutral

- Single-pass metadata generation may require future revision
- Fixed head/tail sizes may need tuning
- Warning-only approach to metadata conflicts requires user attention

### Implementation Notes

#### Phase 1 (Current)

- Implement basic YAML frontmatter handling
- Basic Dublin Core metadata structure
- Simple head/tail AI analysis
- Warning system for metadata conflicts

#### Future Considerations

- Enhanced metadata extraction from various sources
- Metadata confidence tracking
- Metadata inheritance in sectioned documents
- Multiple metadata format support
- Streaming processing for very large texts

### Related Documents

- TextObject System Design Document
- Dublin Core Metadata Standard

## ADR 006: TextObject Metadata Generation and Storage

### Status

Accepted

### Context

TextObject needs to handle cases where input files lack YAML frontmatter metadata. The system needs a clean separation between metadata handling and TextObject's core functionality while maintaining simplicity during the prototype phase.

Key challenges:

- Safe handling of source files
- Clear default behavior
- Separation of metadata generation from validation
- Future extensibility for different metadata formats
- File permission and access issues

### Decision

Implement a separated metadata handling approach:

1. TextObject Responsibilities:

- Expect and validate YAML frontmatter only
- Issue warning if metadata missing
- Delegate to MetadataGenerator for generation
- Use standardized external metadata location

2. MetadataGenerator Component:

- Handle metadata extraction logic
- Manage file operations (save/modify)
- Support two storage modes:
  a. Save to separate file in tnh_metadata directory
  b. Modify source file in-place (with permission check)

3. Default Storage Structure:

```plaintext
working_dir/
├── source_file.txt
└── tnh_metadata/
    └── source_file_meta.txt
```

4. Prototype Phase Handling:

- Warning-only for non-YAML metadata formats
- Basic permission checking
- Simple metadata extraction
- No backup system required yet

### Consequences

Positive:

- Clear separation of concerns
- Original files preserved by default
- Simple, predictable behavior
- Easy to extend for future metadata formats
- Minimal complexity for prototype

Negative:

- Additional directory management needed
- Potential for metadata file/source file desync
- Extra file I/O operations

Neutral:

- External metadata files may need cleanup management
- Future sync mechanism may be needed
- May need to revisit backup strategy in production

### Related

- ADR 004: TextObject Re-Design Decisions
- ADR 005: TextObject Metadata Management and Processing Pipeline
- TextObject New Design specification

### Future Considerations

Interactive metadata handling could be implemented, allowing users to choose whether to modify files in place, save to external location, or use metadata only in memory. This would be particularly valuable when implementing GUI interfaces, providing explicit user control over metadata storage behavior while maintaining current automated pipeline capabilities through a mode parameter.
