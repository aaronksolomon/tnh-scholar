---
title: "ADR-MD02: Metadata Infrastructure Object-Service Integration"
description: "Defines metadata system's role as foundational infrastructure in the object-service architecture, establishing patterns for cross-layer usage and ensuring compliance with design principles."
owner: ""
author: "Aaron Solomon, Claude Sonnet 4.5"
status: current
created: "2025-12-07"
---

# ADR-MD02: Metadata Infrastructure Object-Service Integration

Establishes metadata system (`tnh_scholar.metadata`) as foundational cross-cutting infrastructure that supports the object-service architecture (ADR-OS01) while maintaining design principle compliance.

- **Status**: Accepted
- **Date**: 2025-12-07
- **Authors**: Aaron Solomon, Claude Sonnet 4.5
- **Related**: [ADR-MD01](/architecture/metadata/adr/adr-md01-json-ld-metadata.md), [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md), [ADR-PT04](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)

---

## Context

### Discovery

During implementation of ADR-PT04 (Prompt System Refactor), we discovered that:

1. **Metadata already exists**: `tnh_scholar.metadata` provides `Metadata`, `Frontmatter`, and `ProcessMetadata`
2. **Duplication was occurring**: Services were reimplementing YAML frontmatter parsing
3. **Broader pattern identified**: ALL .md files in TNH Scholar (prompts, corpus, derivatives, docs) use metadata frontmatter
4. **Self-reflexive design**: TNH Scholar operates on its own metadata-bearing artifacts

### Architectural Questions

1. **Is metadata a service?** No—it's foundational infrastructure with no external dependencies
2. **Does it need ports/adapters?** No—pure utility classes used across all layers
3. **How does it fit object-service architecture?** Cross-cutting concern, available to all layers
4. **Should services reuse or reimplement?** ALWAYS reuse; metadata is foundational

### Object-Service Compliance Assessment

**Current implementation** ([src/tnh_scholar/metadata/metadata.py](https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/metadata/metadata.py)):

✅ **Compliant aspects**:
- Strong typing (`Metadata`, `ProcessMetadata` are typed classes)
- Pure functions (no side effects in `Frontmatter.extract()`)
- JSON serialization via `Metadata.to_dict()` (type-safe)
- Type processors for `Path`, `datetime` conversion

❌ **Non-compliant aspects**:
- No transport/domain separation
- Mixes file I/O with domain logic in `Frontmatter.extract_from_file()`
- Logging in utility code
- No mapper pattern for domain schema validation

---

## Decision

### 1. Metadata System Role

**Metadata is FOUNDATIONAL INFRASTRUCTURE**, not a service:

- **Available everywhere**: All layers (domain, service, adapter, mapper, transport) can import
- **No protocols/ports**: Pure utility classes with no abstraction needed
- **Cross-cutting concern**: Supports object-service architecture without being one
- **Self-reflexive enabler**: System can reason about its own artifacts

### 2. Integration Patterns with Object-Service Layers

#### Pattern 1: Mappers Use Frontmatter for .md Files

**Rule**: Never reimplement YAML frontmatter parsing; always use `Frontmatter.extract()`.

```python
# ✅ CORRECT: mappers/prompt_mapper.py
from tnh_scholar.metadata import Frontmatter

class PromptMapper:
    def to_domain_prompt(self, file_content: str) -> Prompt:
        # Use shared infrastructure
        metadata_obj, body = Frontmatter.extract(file_content)

        # Validate against domain schema
        prompt_metadata = PromptMetadata.model_validate(metadata_obj.to_dict())

        return Prompt(metadata=prompt_metadata, template=body)
```

```python
# ❌ WRONG: Don't reimplement
def _parse_frontmatter(content: str) -> dict:
    # Reinventing the wheel
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    return yaml.safe_load(match[1])  # Duplication!
```

**Benefits**:
- Consistent frontmatter handling across all .md files
- JSON-LD support (ADR-MD01) available when needed
- BOM handling, whitespace normalization already implemented
- Future enhancements benefit all consumers

#### Pattern 2: Domain Models Use Metadata for Flexible Fields

**Rule**: Replace `Dict[str, Any]` with `Metadata` for type-safe, JSON-serializable metadata storage.

```python
# ✅ CORRECT: domain/models.py
from tnh_scholar.metadata import Metadata

class DocumentResult(BaseModel):
    content: str
    metadata: Metadata  # JSON-serializable, dict-like

class TranslationResult(BaseModel):
    text: str
    source_metadata: Metadata
    output_metadata: Metadata
```

**Benefits**:
- Type safety (`Metadata` ensures JSON-serializable values)
- Auto-conversion (`Path` → `str`, `datetime` → ISO format)
- Dict-like interface (familiar `|`, `[]` operators)
- Explicit serialization (`to_dict()`, `to_yaml()`)

#### Pattern 3: Services Track Provenance with ProcessMetadata

**Rule**: Use `ProcessMetadata` to record transformation steps in multi-stage pipelines.

```python
# ✅ CORRECT: services/translation_service.py
from tnh_scholar.metadata import ProcessMetadata, Metadata

class TranslationService:
    def translate(self, doc: Document) -> Document:
        result = self._translate_content(doc)

        # Track transformation
        result.metadata.add_process_info(
            ProcessMetadata(
                step="translation",
                processor="genai_service",
                tool="gpt-4o",
                source_lang=doc.metadata.get("language"),
                target_lang="en",
                timestamp=datetime.now(),  # Auto-converted to ISO
            )
        )

        return result
```

**Benefits**:
- Automatic provenance chain (stored in `tnh_metadata_process` field)
- Supports semantic queries (JSON-LD compatible)
- Reproducibility (track exact tools/versions used)
- Self-reflexive operations (system can analyze its own transformations)

#### Pattern 4: Mappers Separate Infrastructure from Domain Validation

**Rule**: Mappers use `Frontmatter` (infrastructure), then validate with domain schemas (Pydantic models).

```python
# ✅ CORRECT: Two-step process
class CorpusMapper:
    def to_domain_document(self, file_content: str) -> CorpusDocument:
        # Step 1: Infrastructure (Frontmatter parsing)
        metadata_obj, body = Frontmatter.extract(file_content)

        # Step 2: Domain validation (Pydantic schema)
        corpus_metadata = CorpusMetadata.model_validate(metadata_obj.to_dict())

        return CorpusDocument(metadata=corpus_metadata, content=body)
```

**Why separate?**
- **Infrastructure concern**: YAML parsing, BOM handling, whitespace
- **Domain concern**: Required fields, business rules, semantic validation
- **Separation of concerns**: Metadata module doesn't know about domain schemas
- **Reusability**: Same Frontmatter code works for prompts, corpus, derivatives

---

## 3. Object-Service Architecture Modifications

### Updated Layer Model with Metadata

```
┌──────────────────────────────────────────────────────────┐
│  Foundational Infrastructure (Cross-Cutting)             │
│  • tnh_scholar.metadata (Metadata, Frontmatter, Process) │
│  • Available to ALL layers below                         │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
    ┌────────────────────────────────────────────┐
    │  Application Layer                         │
    │  • CLI, notebooks, web, Streamlit          │
    └────────────────────────────────────────────┘
                           │
                           ▼
    ┌────────────────────────────────────────────┐
    │  Service Layer                             │
    │  • Orchestrators (use ProcessMetadata)     │
    └────────────────────────────────────────────┘
                           │
                           ▼
    ┌────────────────────────────────────────────┐
    │  Adapter + Mapper Layer                    │
    │  • Mappers use Frontmatter.extract()       │
    │  • Adapters use Metadata for flexible data │
    └────────────────────────────────────────────┘
                           │
                           ▼
    ┌────────────────────────────────────────────┐
    │  Transport Layer                           │
    │  • Uses Metadata.to_dict() for JSON        │
    └────────────────────────────────────────────┘
```

### Metadata as "Horizontal" Infrastructure

Unlike services (which flow vertically: Application → Service → Adapter → Transport), metadata is **horizontal**—available at every layer:

| Layer | Metadata Usage |
|-------|----------------|
| **Application** | Display metadata in UIs, format for users |
| **Service** | Track provenance with `ProcessMetadata` |
| **Adapter** | Store flexible provider-specific data in `Metadata` |
| **Mapper** | Parse .md files with `Frontmatter.extract()` |
| **Transport** | Serialize with `Metadata.to_dict()` for JSON |

---

## 4. Compliance Improvements Needed

### Issue 1: File I/O Mixed with Domain Logic

**Current** ([metadata/metadata.py:262-264](https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/metadata/metadata.py#L262-L264)):

```python
class Frontmatter:
    @classmethod
    def extract_from_file(cls, file: Path) -> tuple[Metadata, str]:
        text_str = read_str_from_file(file)  # ❌ File I/O in domain utility
        return cls.extract(text_str)
```

**Recommendation**: Mark as adapter-level helper, or move to separate `FrontmatterFileAdapter`:

```python
# Option A: Keep but document as adapter-level
class Frontmatter:
    """Pure frontmatter parsing (no I/O)."""

    @staticmethod
    def extract(content: str) -> tuple[Metadata, str]:
        """Extract frontmatter from string (pure function)."""
        ...

    @classmethod
    def extract_from_file(cls, file: Path) -> tuple[Metadata, str]:
        """ADAPTER-LEVEL: Convenience for file-based workflows.

        Note: This method performs I/O. For pure parsing, use extract().
        Services should inject file content via transport layer.
        """
        text_str = read_str_from_file(file)
        return cls.extract(text_str)
```

```python
# Option B: Separate adapter (stricter compliance)
# adapters/frontmatter_file_adapter.py
class FrontmatterFileAdapter:
    """Adapter for reading frontmatter from files."""

    def __init__(self, transport: FileTransport):
        self._transport = transport

    def extract_from_file(self, file: Path) -> tuple[Metadata, str]:
        content = self._transport.read_text(file)
        return Frontmatter.extract(content)
```

**Decision**: Keep Option A for rapid prototype phase; document as adapter-level helper. Consider Option B post-1.0 if strict layer separation becomes critical.

### Issue 2: Logging in Utility Code

**Current** ([metadata/metadata.py:22-36](https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/metadata/metadata.py#L22-L36)):

```python
def safe_yaml_load(yaml_str: str, *, context: str = "unknown") -> dict:
    try:
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            logger.warning(...)  # ❌ Side effect in utility function
            return {}
    except ScannerError as e:
        logger.error(...)  # ❌ Side effect
    except yaml.YAMLError as e:
        logger.error(...)  # ❌ Side effect
    return {}
```

**Recommendation**: Raise typed exceptions; let callers decide logging strategy:

```python
# metadata/errors.py (new file)
class MetadataError(Exception):
    """Base error for metadata operations."""
    pass

class FrontmatterParseError(MetadataError):
    """YAML frontmatter parsing failed."""
    pass

class InvalidMetadataError(MetadataError):
    """Metadata not a valid dict."""
    pass

# metadata/metadata.py
def safe_yaml_load(yaml_str: str, *, context: str = "unknown") -> dict:
    """Parse YAML string to dict.

    Raises:
        FrontmatterParseError: If YAML parsing fails
        InvalidMetadataError: If result is not a dict
    """
    try:
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            raise InvalidMetadataError(
                f"YAML in [{context}] is not a dict, got {type(data)}"
            )
        return data
    except yaml.ScannerError as e:
        raise FrontmatterParseError(
            f"YAML scanner error in [{context}]: {e}"
        ) from e
    except yaml.YAMLError as e:
        raise FrontmatterParseError(
            f"YAML error in [{context}]: {e}"
        ) from e
```

**Benefits**:
- Pure functions (no side effects)
- Callers choose logging strategy (service layer logs, transport retries, etc.)
- Typed errors enable better error handling
- Testable without mocking loggers

**Decision**: Implement for 0.2.0; track in TODO as "Metadata error handling improvements".

---

## 5. Design Principles Summary

### When to Use Metadata Infrastructure

| Scenario | Use Metadata? | Pattern |
|----------|---------------|---------|
| Parsing .md files with frontmatter | ✅ YES | `Frontmatter.extract()` in mappers |
| Flexible metadata storage | ✅ YES | `Metadata` instead of `Dict[str, Any]` |
| Tracking transformation provenance | ✅ YES | `ProcessMetadata` in services |
| Service-to-service data contracts | ❌ NO | Use Pydantic domain models |
| Provider-specific vendor data | ✅ YES | `Metadata` for flexible fields |
| Strict business rules validation | ❌ NO | Use Pydantic schemas (validate after `Frontmatter.extract()`) |

### Metadata vs. Pydantic Models

**Use `Metadata` when**:
- Schema is flexible (user-supplied, vendor-specific)
- Need dict-like operations (`|`, `[]`, iteration)
- JSON serialization is primary concern
- Provenance tracking with `ProcessMetadata`

**Use Pydantic models when**:
- Schema is well-defined (domain objects)
- Need strict validation (required fields, types)
- Want IDE autocomplete and type checking
- Encoding business rules

**Use both when** (common pattern):
```python
class DocumentResult(BaseModel):
    """Domain model with strict validation."""
    id: str
    content: str
    language: str  # Strict field

    # Flexible metadata for extensions
    custom_metadata: Metadata = Metadata()
```

---

## Consequences

### Positive

1. **No duplication**: Services reuse frontmatter parsing instead of reimplementing
2. **Consistent behavior**: All .md files parsed the same way (prompts, corpus, docs)
3. **Type safety**: `Metadata` ensures JSON-serializable values (no serialization surprises)
4. **Future-ready**: JSON-LD support (ADR-MD01) available when needed
5. **Provenance tracking**: `ProcessMetadata` enables reproducible transformations
6. **Self-reflexive**: System can operate on its own metadata-bearing artifacts
7. **Object-service aligned**: Clear patterns for metadata usage in each layer

### Negative

1. **Mixed concerns (current)**: `Frontmatter.extract_from_file()` has I/O, needs documentation
2. **Logging side effects (current)**: `safe_yaml_load()` logs instead of raising exceptions
3. **Learning curve**: Developers must understand when to use `Metadata` vs Pydantic

### Risks

1. **Temptation to expand**: Metadata should stay simple; avoid adding service-specific logic
2. **Over-use**: Don't use `Metadata` for everything; Pydantic models better for strict schemas

---

## Implementation Plan

### Phase 1: Documentation (Immediate - 0.1.4)

- [x] Document metadata role in ADR-OS01 (Section 3.3)
- [x] Create ADR-MD02 (this document)
- [x] Update ADR-PT04 addendum with as-built notes
- [ ] Add usage examples to metadata module docstrings

### Phase 2: API Cleanup (0.2.0)

- [ ] Document `Frontmatter.extract_from_file()` as adapter-level helper
- [ ] Refactor `safe_yaml_load()` to raise typed exceptions (remove logging)
- [ ] Create `metadata/errors.py` with `MetadataError` hierarchy
- [ ] Update tests to catch typed exceptions

### Phase 3: Broader Adoption (0.3.0+)

- [ ] Audit codebase for `Dict[str, Any]` usage → replace with `Metadata` where appropriate
- [ ] Add `ProcessMetadata` to translation/transcription pipelines
- [ ] Enable JSON-LD semantic queries in knowledge base (future)

---

## Open Questions

1. **Should `Metadata` support nested validation?** Currently shallow; consider recursive validation for nested dicts/lists
2. **JSON-LD activation?** When to fully enable schema.org vocabularies (deferred to knowledge base implementation)
3. **Metadata versioning?** Should `Metadata` track schema versions for migrations?

---

## References

- [ADR-MD01: JSON-LD Metadata Strategy](/architecture/metadata/adr/adr-md01-json-ld-metadata.md)
- [ADR-OS01: Object-Service Architecture V3](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)
- [ADR-PT04: Prompt System Refactor](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)
- [src/tnh_scholar/metadata/metadata.py](https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/metadata/metadata.py)

---

**Approval**: Accepted 2025-12-07 (Aaron Solomon)
