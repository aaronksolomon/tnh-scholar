---
title: "ADR-MD01: Adoption of JSON-LD for Metadata Management"
description: "Chooses JSON-LD as the canonical metadata format to capture provenance, relationships, and future semantic queries."
owner: ""
author: ""
status: current
created: "2025-02-01"
---
# ADR-MD01: Adoption of JSON-LD for Metadata Management

Commits to JSON-LD metadata so provenance, multilingual transformations, and semantic relationships stay queryable.

- **Status**: Proposed
- **Date**: 2025-01-30

### Context

TNH Scholar needs a robust metadata management system to track content through various processing stages, particularly for multilingual content processing and human-AI collaborative workflows. The system must support both embedded metadata in text files and associated metadata for binary files, while enabling future expansion to database storage.

Two primary approaches were considered:

1. Simple YAML frontmatter with basic key-value pairs
2. JSON-LD based metadata using semantic web standards

The initial inclination was toward YAML frontmatter for its simplicity and readability. However, deeper analysis revealed that JSON-LD's semantic capabilities align well with TNH Scholar's document processing and provenance tracking needs.

### Decision Drivers

1. Need to track content transformations through multiple processing stages
2. Requirement to maintain clear provenance for AI-assisted translations
3. Future requirements for web-based interfaces showing processing history
4. Importance of standardized metadata for content management
5. Value of semantic relationships in understanding content connections
6. Long-term extensibility requirements

### Decision

We will adopt JSON-LD as TNH Scholar's primary metadata format, implemented through a phased approach:

Phase 1: File-based Storage

- Embedded JSON-LD in text files using frontmatter
- Sidecar JSON-LD files for binary content
- Basic metadata validation and processing through pyld

Phase 2: Enhanced Processing

- Expanded semantic relationships
- Improved validation
- Training data extraction capabilities

Phase 3: Database Integration

- Central metadata storage
- Unified querying
- Maintained backward compatibility with file-based storage

### Technical Implementation

Initial implementation will center on a Frontmatter class handling JSON-LD:

```python
class Frontmatter:
    """Handles JSON-LD frontmatter embedding and extraction."""
    
    SCHEMA_ORG = "https://schema.org/"
    DC_CONTEXT = "http://purl.org/dc/elements/1.1/"
    
    @staticmethod
    def extract(content: str) -> Tuple[Dict[str, Any], str]:
        """Extract JSON-LD frontmatter and content from text."""
        
    @staticmethod
    def embed(metadata: Dict[str, Any], content: str) -> str:
        """Embed metadata as JSON-LD frontmatter."""
        
    @staticmethod
    def validate_jsonld(metadata: Dict[str, Any]) -> bool:
        """Validate if the metadata is valid JSON-LD."""
```

### Example Usage

Document processing workflow metadata:

```javascript
{
  "@context": "https://schema.org/",
  "@type": "Translation",
  "@id": "translation_123_revised",
  "translationOf": {"@id": "transcript_123_raw"},
  "basedOn": {"@id": "translation_123_draft"},
  "sourceLanguage": "vi",
  "targetLanguage": "en",
  "processingStage": "human_revised",
  "revisor": "John Doe",
  "revisionDate": "2024-01-30"
}
```

### Consequences

#### Positive

1. Rich semantic relationships between content
2. Standard vocabularies through schema.org and Dublin Core
3. Strong support for content provenance tracking
4. Better foundation for future web interfaces
5. Industry-standard metadata format
6. Enhanced machine readability for AI processing

#### Negative

1. Increased complexity compared to YAML
2. Steeper learning curve for contributors
3. Additional dependency on pyld library
4. More complex validation requirements

#### Neutral

1. Changes to existing metadata handling required
2. Need for migration strategy from current formats
3. Documentation requirements for JSON-LD usage

### Alternative Approaches Considered

#### Simple YAML Frontmatter

```yaml
type: translation
id: translation_123
source_id: transcript_123
language: vi
target_language: en
```

While simpler, this approach lacks semantic richness and standardization.

#### Custom Metadata Format

Creating a custom format was rejected due to:

- Reinventing existing solutions
- Lack of standardization
- Limited tool support

### Implementation Strategy

1. Initial Phase

- Implement basic JSON-LD frontmatter handling
- Focus on core metadata fields
- Simple validation

2. Enhancement Phase

- Add semantic relationship support
- Improve validation
- Develop migration tools

3. Integration Phase

- Database integration
- Advanced querying
- Web interface support

### Notes

This decision prioritizes long-term system capabilities over short-term simplicity. The initial complexity investment is justified by:

1. Enhanced content relationship tracking
2. Better support for human-AI workflow management
3. Improved potential for web interface development
4. Standard compliance for potential interoperability

### Related Documents

- TNH Scholar System Design (system-design.md)
- Pattern System Documentation (patterns.md)
- Text Processing Documentation

The semantic capabilities of JSON-LD align particularly well with TNH Scholar's vision for cyclical learning and content processing improvements as outlined in the system architecture document.

Here's the ADR documentation for the metadata implementation:

## ADR 002: Metadata Implementation Strategy

02-01-2025

### Status

Accepted

### Context

TNH Scholar needs a flexible metadata storage solution during its rapid prototyping phase. The system currently uses `Dict[str, Any]` throughout for metadata storage, but requires a more controlled yet still flexible approach that:

1. Maintains JSON serializability for AI pipeline integration
2. Preserves dict-like operations (especially the | operator for combining metadata)
3. Allows schema flexibility during prototyping
4. Provides clear extension points for future structure

Two main approaches were considered:

1. Type alias: `Metadata = Dict[str, Any]`
2. Custom class implementing MutableMapping

### Decision Drivers

1. Need for JSON serializability in AI pipelines
2. Heavy use of dict union operations (|) in existing code
3. Requirement for maximum flexibility during prototyping
4. Future extensibility requirements
5. Minimal overhead during development

### Decision

Implement a custom `Metadata` class using `MutableMapping` that provides dict-like behavior while ensuring JSON serializability:

```python
from collections.abc import MutableMapping
from typing import Any, Dict, Optional, Union, Iterator, Mapping

JsonValue = Union[str, int, float, bool, list, dict, None]

class Metadata(MutableMapping):
    """
    Flexible metadata container that behaves exactly like a dict while ensuring
    JSON serializability. Designed for AI processing pipelines where schema
    flexibility is prioritized over structure.
    """
    def __init__(self, data: Optional[Union[Dict[str, JsonValue], 'Metadata']] = None) -> None:
        self._data: Dict[str, JsonValue] = {}
        if data is not None:
            self.update(data._data if isinstance(data, Metadata) else data)

    # [Core implementation as shown above...]
```

This implementation was chosen over a simple type alias because it provides:

- JSON serializability guarantees
- Full dict-like behavior including all operators
- Clear extension points for future enhancements
- Type safety for JSON values
- Explicit serialization methods

### Consequences

#### Positive

1. Ensures metadata remains JSON-serializable
2. Maintains all dict operations including | operator
3. Makes metadata objects self-identifying
4. Provides clear path for adding validation/structure later
5. Explicit serialization methods improve code clarity

#### Negative

1. Slightly more complex than simple type alias
2. Need to implement and maintain custom class
3. Must ensure all dict operations are properly supported
4. Minor performance overhead compared to raw dict

#### Neutral

1. Changes required to existing Dict[str, Any] usage
2. Need to document class behavior and limitations
3. May need to add features as dict usage patterns emerge

### Alternative Approaches Considered

#### Type Alias

```python
Metadata = Dict[str, Any]
```

Rejected because it provides no guarantees about JSON serializability and no extension points for future enhancements.

#### Pydantic Model

Rejected as too structured for current prototyping needs.

#### attrs/dataclasses

- Python's built-in dataclass or attrs library
- Offers strong typing and validation
- Rejected as requiring too rigid structure for current needs

#### jsonschema/JSON Schema

- Provides flexible schema validation
- Rejected as overkill for current metadata needs
- Could be considered for future validation requirements

#### Existing Metadata Libraries

- `python-metadata`: Dedicated metadata handling
- `metadatastore`: Scientific metadata management
- `dublin-core-metadata`: Dublin Core implementation
- All rejected as adding unnecessary complexity during prototyping

#### Related Project Approaches

Examined metadata handling in:

- Documentation tools (Sphinx, mkdocs, pelican)
- Git metadata systems
- Python package metadata

Found these approaches either too specialized or too complex for current needs

### Implementation Strategy

1. Initial Implementation
   - Create Metadata class with full dict behavior
   - Ensure JSON value type constraints
   - Add basic serialization methods

2. Migration
   - Replace Dict[str, Any] usage with Metadata class
   - Update existing metadata handling code
   - Document any behavioral differences

3. Future Considerations
   - Potential addition of schema validation
   - Integration with Dublin Core standards
   - Enhanced metadata merging strategies

### Notes

This decision prioritizes flexibility and simplicity during prototyping while ensuring basic guarantees about metadata structure and behavior. The implementation can evolve toward more structured approaches as requirements solidify.

The design specifically supports AI pipeline integration by maintaining JSON compatibility while providing full dict-like operations for easy metadata manipulation.

### Related Documents

- ADR 001: Adoption of JSON-LD for Metadata Management
- TNH Scholar System Design (system-design.md)
- Pattern System Documentation (patterns.md)

Yes, good points about the deeper validation needs and potential extensibility. Let's draft an ADR to document these considerations:


## ADR 003: Metadata Validation and Serialization Strategy

02-23-2024

### Status
Proposed - Prototyping Phase

### Context
The TNH Scholar system needs flexible metadata handling that balances immediate prototyping needs with potential future requirements. Current implementation using JsonValue typing provides basic type safety but has several limitations and considerations that need to be documented.

Key Issues:
1. Recursive Validation
   - Current JsonValue validation is shallow
   - Nested dictionaries may contain non-serializable objects
   - List contents are not validated

2. Object Serialization
   - Some objects may have valid serialization methods
   - Current approach limited to primitive JSON types
   - No standard interface for serializable objects

3. Type Processing
   - Current processing happens at initialization
   - No validation on subsequent updates
   - Limited to predefined type processors

### Current Implementation (Prototype Phase)

```python
JsonValue = Union[str, int, float, bool, list, dict, None]

class Metadata(MutableMapping):
    _type_processors = {
        Path: lambda p: str(p.resolve()),
        datetime: lambda d: d.isoformat(),
    }
    
    def __init__(self, data: Optional[Union[Dict[str, Any], 'Metadata']] = None):
        self._data: Dict[str, JsonValue] = {}
        if data is not None:
            raw_data = data._data if isinstance(data, Metadata) else data
            processed_data = {
                k: self._process_value(v) for k, v in raw_data.items()
            }
            self.update(processed_data)
```

### Future Considerations

1. Deep Validation

   ```python
   def validate_json_value(value: Any, path: str = "") -> bool:
       if isinstance(value, dict):
           return all(
               validate_json_value(v, f"{path}.{k}") 
               for k, v in value.items()
           )
       if isinstance(value, list):
           return all(
               validate_json_value(v, f"{path}[{i}]") 
               for i, v in enumerate(value)
           )
       return isinstance(value, (str, int, float, bool, type(None)))
   ```

2. Serializable Interface

   ```python
   class Serializable(Protocol):
       def to_dict(self) -> Dict[str, JsonValue]: ...
       
   class Metadata(MutableMapping):
       def _process_value(self, value: Any) -> JsonValue:
           if isinstance(value, Serializable):
               return value.to_dict()
           # existing processing...
   ```

3. Update Validation

   ```python
   def __setitem__(self, key: str, value: Any) -> None:
       self._data[key] = self._process_value(value)
   ```

### Decision

For the prototyping phase:

1. Keep current shallow validation
2. Document known limitations
3. Use type processors for common cases
4. Accept some type safety compromises for flexibility

### Consequences

Positive:

- Simple, workable implementation for prototyping
- Clear path for future enhancement
- Basic type safety for common cases
- Flexible enough for rapid development

Negative:

- Incomplete validation
- Potential for invalid nested data
- No standardized object serialization
- Some type safety compromises

### Future Directions

1. Validation Options:
   - Full recursive validation
   - Schema-based validation
   - Custom validation rules

2. Serialization Enhancement:
   - Standard serialization protocol
   - Custom serializers registry
   - Validation hooks

3. Type Processing:
   - Extended type processor registry
   - Custom processor registration
   - Update validation

### Notes

This design purposefully favors flexibility and simplicity during prototyping while documenting paths for future enhancement. The current implementation acknowledges and accepts certain limitations in favor of development velocity.
