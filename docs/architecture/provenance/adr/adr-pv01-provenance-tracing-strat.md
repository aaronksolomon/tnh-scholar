---
title: "ADR-PV01: Provenance & Tracing Infrastructure Strategy"
description: "Establishes unified cross-cutting infrastructure for tracking data lineage, request tracing, and operation provenance across all TNH Scholar layers"
type: "strategy"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: proposed
created: "2025-12-19"
related_adrs: ["../metadata/adr/adr-md02-metadata-object-service-integration.md", "../object-service/adr/adr-os01-object-service-architecture-v3.md"]
---

# ADR-PV01: Provenance & Tracing Infrastructure Strategy

Establishes provenance and tracing as foundational cross-cutting infrastructure that provides unified patterns for tracking data lineage, request tracing, and operation provenance across all TNH Scholar layers.

- **Filename**: `adr-pv01-provenance-tracing-strat.md`
- **Heading**: `# ADR-PV01: Provenance & Tracing Infrastructure Strategy`
- **Status**: Proposed
- **Date**: 2025-12-19
- **Authors**: Aaron Solomon, Claude Sonnet 4.5
- **Related ADRs**:
  - [ADR-MD02: Metadata Infrastructure Object-Service Integration](/architecture/metadata/adr/adr-md02-metadata-object-service-integration.md)
  - [ADR-OS01: Object-Service Architecture V3](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip` status**: Coding has begun. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

**Rationale**: Once implementation begins, the original decision must be preserved for historical context.

---

## Context

### Discovery: Fragmented Provenance Concepts

During Sourcery code review of PR #21 (tnh-gen CLI), we identified a **correlation ID inconsistency**: two separate IDs were being generated for a single CLI invocation—one for CLI output and another for provenance headers in output files. This revealed a deeper architectural gap.

**Current state across TNH Scholar:**

1. **GenAI Service**: `Provenance` class (provider, model, timestamps, fingerprint)
2. **CLI Layer**: `correlation_id` (request tracing)
3. **Metadata Infrastructure**: `ProcessMetadata` (document processing history)
4. **Object-Service §12**: Mentions "correlation IDs" in provenance.params but no standard model

**Problem**: We're using **different terminologies and models** for essentially the same concept—tracking "where things came from"—across different operational scopes. There's no unified guidance on:

- Standard terminology (provenance vs correlation_id vs trace_id vs fingerprint)
- When to use which tracking mechanism
- How to propagate tracking data through call chains
- How to nest/aggregate provenance across multi-stage operations
- Storage and serialization patterns

### Architectural Questions

1. **Is provenance a service?** No—it's foundational infrastructure (like Metadata)
2. **Does it need ports/adapters?** No—pure data models used across all layers
3. **How does it fit object-service architecture?** Cross-cutting concern, available everywhere
4. **Should we standardize terminology?** Yes—prevents confusion and implementation errors
5. **Do we need layered models?** Yes—different scopes need different granularity

### Relationship to Existing Infrastructure

**Metadata (ADR-MD02)** provides:
- Frontmatter parsing for .md files
- `ProcessMetadata` for document transformations
- JSON-LD serialization

**Provenance/Tracing** extends this with:
- Request-level tracing (CLI invocations, API requests)
- Service-level provenance (AI generations, processing operations)
- Transport-level tracking (HTTP request IDs, retry counts)
- Aggregation patterns for multi-stage workflows

---

## Decision

### 1. Provenance System Role

**Provenance/Tracing is FOUNDATIONAL CROSS-CUTTING INFRASTRUCTURE**, similar to Metadata:

- **Available everywhere**: All layers (domain, service, adapter, mapper, transport) can import
- **No protocols/ports**: Pure data models with no abstraction needed
- **Cross-cutting concern**: Supports object-service architecture without being a service itself
- **Reproducibility enabler**: System can recreate results and trace operations

### 2. Unified Terminology

Establish standard terms to replace fragmented naming:

| **Term** | **Scope** | **Purpose** | **Example** |
|----------|-----------|-------------|-------------|
| **Trace ID** | Request/Invocation | Track single operation end-to-end | CLI command, API request, batch job |
| **Correlation ID** | *Alias for Trace ID* | (Legacy term, prefer "trace_id") | Same as trace_id |
| **Provenance** | Service Operation | Record how result was generated | AI generation, document processing |
| **Fingerprint** | Content Identity | Content-based hash for reproducibility | Prompt hash, input file hash |
| **Lineage** | Data Flow | Chain of transformations | Source → derivative artifacts |
| **Process Metadata** | Document Transformation | Metadata about processing operations | (Existing in metadata infrastructure) |

**Migration Path**:
- New code: use `trace_id`
- Existing `correlation_id`: acceptable as alias, gradually refactor
- Always use `provenance` for service-level result tracking

### 3. Layered Provenance Model

Define standard data models for different operational scopes:

#### Layer 1: Request Provenance (CLI/API Layer)

**Purpose**: Track individual operations through the system

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RequestProvenance:
    """Provenance for CLI commands, API requests, batch jobs."""
    trace_id: str  # Unique identifier for this operation
    operation: str  # e.g., "tnh-gen run", "api.generate", "batch.process"
    started_at: datetime
    finished_at: datetime | None = None
    user_context: dict[str, Any] | None = None  # User, environment, etc.
    service_provenance: list["ServiceProvenance"] = field(default_factory=list)
```

**Usage**:
- Generate `trace_id` once at operation entry point
- Propagate through all downstream calls
- Include in all outputs (stdout JSON, file headers, logs)

#### Layer 2: Service Provenance (GenAI/Processing Layer)

**Purpose**: Record how AI/processing results were generated

```python
@dataclass
class ServiceProvenance:
    """Provenance for AI generations, document processing, transformations."""
    provider: str  # "openai", "anthropic", "pyannote", "docprocessor"
    model: str | None = None  # Model name if applicable
    fingerprint: Fingerprint | None = None  # Content hash for reproducibility
    started_at: datetime
    finished_at: datetime
    attempt_count: int = 1
    parameters: dict[str, Any] = field(default_factory=dict)  # Effective params
    policy_version: str | None = None
    transport_provenance: "TransportProvenance | None" = None
```

**Usage**:
- Created by services (GenAIService, DocumentProcessor, etc.)
- Embedded in result envelopes
- Nested within RequestProvenance for full trace

#### Layer 3: Transport Provenance (HTTP/SDK Layer)

**Purpose**: Track external system interactions

```python
@dataclass
class TransportProvenance:
    """Provenance for HTTP requests, SDK calls, external APIs."""
    request_id: str | None = None  # Backend-provided request ID
    retry_count: int = 0
    backend_metadata: dict[str, Any] = field(default_factory=dict)
    sdk_version: str | None = None
```

**Usage**:
- Captured by adapters when calling external systems
- Nested within ServiceProvenance
- Aids debugging and cost tracking

#### Fingerprint Model (Content Identity)

```python
@dataclass
class Fingerprint:
    """Content-based identity for reproducibility."""
    content_hash: str  # Hash of primary input content
    variables_hash: str | None = None  # Hash of template variables
    algorithm: str = "sha256"  # Hash algorithm used
```

**Usage**:
- Generate for all deterministic inputs (prompts, templates, source files)
- Enables cache lookups and reproducibility verification

### 4. Propagation Rules

**Rule 1: Single Trace ID Per Operation**
- Generate trace_id at entry point (CLI command, API handler)
- Pass through all function calls via context or explicit parameter
- Never regenerate within the same operation

**Rule 2: Nesting for Multi-Stage Operations**
- RequestProvenance contains list of ServiceProvenance
- ServiceProvenance optionally contains TransportProvenance
- Preserve full chain for debugging and audit

**Rule 3: Aggregation for Pipelines**
- Multi-stage pipelines: maintain list of ServiceProvenance (one per stage)
- Each stage records its own provenance
- Top-level RequestProvenance aggregates all stages

**Rule 4: Propagation Through Object-Service Layers**
```
CLI/Application Layer:
  └─ Creates RequestProvenance with trace_id
       │
Service Layer:
  └─ Creates ServiceProvenance (embedded in result Envelope)
       │
Adapter Layer:
  └─ Propagates trace_id to transport, captures TransportProvenance
       │
Transport Layer:
  └─ Includes trace_id in HTTP headers (X-Trace-ID)
```

### 5. Storage & Serialization Patterns

#### File Headers (Human-Readable)

Use YAML frontmatter with `---` delimiters (consistent with TNH Scholar metadata patterns):

```yaml
---
# Provenance metadata (generated output)
trace_id: abc123def456
operation: tnh-gen run summarize-talk
provider: openai
model: gpt-4-turbo-2024-04-09
fingerprint: sha256:8f3e4d...
generated: 2025-12-19T10:30:45Z
---

[Generated content follows...]
```

**Rationale**: Maintains consistency with existing TNH Scholar patterns:

- Metadata infrastructure (ADR-MD01/MD02) uses YAML frontmatter
- All `.md` files in corpus use `---` delimiters
- Enables reuse of `Frontmatter.extract()` utilities
- Machine-parseable and human-readable

#### JSON Output (Machine-Readable)

```json
{
  "status": "succeeded",
  "result": {...},
  "provenance": {
    "trace_id": "abc123def456",
    "operation": "tnh-gen run summarize-talk",
    "started_at": "2025-12-19T10:30:42Z",
    "finished_at": "2025-12-19T10:30:45Z",
    "service_provenance": [
      {
        "provider": "openai",
        "model": "gpt-4-turbo-2024-04-09",
        "fingerprint": {
          "content_hash": "8f3e4d...",
          "algorithm": "sha256"
        },
        "parameters": {...},
        "attempt_count": 1
      }
    ]
  }
}
```

#### Database Schema (Future)

```sql
CREATE TABLE request_provenance (
    trace_id TEXT PRIMARY KEY,
    operation TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    user_context JSONB
);

CREATE TABLE service_provenance (
    id SERIAL PRIMARY KEY,
    trace_id TEXT REFERENCES request_provenance(trace_id),
    provider TEXT NOT NULL,
    model TEXT,
    fingerprint_hash TEXT,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP NOT NULL,
    parameters JSONB,
    policy_version TEXT
);
```

### 6. Integration with Existing Infrastructure

#### Relationship to Metadata (ADR-MD02)

**Metadata provides**:
- Frontmatter parsing (`Frontmatter.extract()`)
- `ProcessMetadata` for document transformations
- JSON-LD serialization

**Provenance extends**:
- Request tracing (trace_id)
- Service result provenance
- Cross-operation aggregation

**Integration Pattern**:
```python
from tnh_scholar.metadata import ProcessMetadata
from tnh_scholar.provenance import RequestProvenance, ServiceProvenance

# ProcessMetadata records transformation details
process_meta = ProcessMetadata(
    operation="summarize",
    version="1.0",
    parameters={"max_length": 500}
)

# ServiceProvenance records how AI generated result
service_prov = ServiceProvenance(
    provider="openai",
    model="gpt-4",
    parameters=process_meta.to_dict(),  # Link to ProcessMetadata
    fingerprint=Fingerprint(content_hash="...")
)

# RequestProvenance tracks full CLI operation
request_prov = RequestProvenance(
    trace_id="abc123",
    operation="tnh-gen run summarize",
    service_provenance=[service_prov]
)
```

#### Relationship to Object-Service Provenance (ADR-OS01 §12)

**ADR-OS01 §12.2 states**:
> Always record in `provenance.params`:
> - Upstream IDs (job_id/request_id) and correlation IDs

**ADR-PV01 standardizes this**:
- `trace_id` = standard correlation ID
- `ServiceProvenance.parameters` = effective params
- `TransportProvenance.request_id` = upstream IDs

**Migration**: Existing `Provenance` class in GenAI service becomes `ServiceProvenance` (backward compatible with alias)

### 7. Implementation Location

**New module**: `src/tnh_scholar/provenance/`

```
src/tnh_scholar/provenance/
  ├── __init__.py          # Export public models
  ├── models.py            # RequestProvenance, ServiceProvenance, etc.
  ├── fingerprint.py       # Fingerprint generation utilities
  └── serialization.py     # JSON, file header, JSON-LD serializers
```

**Available to all layers** (like metadata):
- Domain: Include in result models
- Service: Create ServiceProvenance
- Adapter: Capture TransportProvenance
- Transport: Propagate trace_id in HTTP headers
- CLI: Generate RequestProvenance

---

## Consequences

### Positive

1. **Unified Terminology**: Eliminates confusion between correlation_id, trace_id, provenance
2. **Consistent Tracking**: Standard patterns across CLI, service, transport layers
3. **Debuggability**: Trace_id links logs, errors, outputs for same operation
4. **Reproducibility**: Fingerprints + provenance enable result recreation
5. **Audit Trail**: Full lineage from request to result to output file
6. **Error Prevention**: Prevents bugs like duplicate correlation_id generation
7. **Cross-Layer Visibility**: Single trace_id flows through entire operation
8. **Standards Alignment**: Uses industry-standard terms (trace_id from OpenTelemetry/W3C)

### Negative

1. **Migration Effort**: Existing code uses `correlation_id` (low risk: alias acceptable)
2. **Storage Overhead**: Additional metadata in outputs and databases
3. **Complexity**: Developers must understand layered provenance model
4. **Learning Curve**: New team members need to learn provenance patterns

### Trade-offs

- **Verbosity vs Clarity**: More structured models increase boilerplate but improve clarity
- **Performance vs Traceability**: Provenance tracking adds minimal overhead for significant debugging value
- **Flexibility vs Standards**: Opinionated models constrain implementation but ensure consistency

---

## Alternatives Considered

### Alternative 1: Keep Current Fragmented Approach

**Rejected** because:
- Continues allowing bugs like duplicate correlation_id generation
- No guidance for developers on when to use which tracking mechanism
- Difficult to trace operations across layers

### Alternative 2: Single Flat Provenance Model

**Rejected** because:
- Different layers need different granularity
- Doesn't support nesting for multi-stage operations
- Mixes concerns (request tracing vs service provenance)

### Alternative 3: Use OpenTelemetry Directly

**Considered but deferred** because:
- OpenTelemetry is complex infrastructure (spans, traces, instrumentation)
- Our needs are simpler (data models, not distributed tracing infrastructure)
- Can adopt OpenTelemetry later and map our models to their schema
- **Future path**: Provenance models are compatible with OpenTelemetry semantic conventions

---

## Open Questions

**Note**: These questions will be addressed in supporting decimal ADRs (see Future Extensions below).

1. **JSON-LD Integration**: Should provenance use JSON-LD schema.org vocabulary? (Metadata does)
   - **Direction**: ADR-PV01.1 will define Schema.org mappings and integration patterns

2. **Fingerprint Algorithm**: Always SHA-256 or configurable per use case?
   - **Direction**: ADR-PV01.5 will specify pluggable algorithm interface with SHA-256 as default

3. **OpenTelemetry Compatibility**: How to map internal models to OTEL semantic conventions?
   - **Direction**: ADR-PV01.3 will provide compatibility mapping for future instrumentation

4. **Logging Integration**: How to inject trace_id into log messages and structured logging?
   - **Direction**: ADR-PV01.4 will define context injection and formatter patterns

5. **Testing Strategy**: How to test provenance propagation in integration tests?
   - **Direction**: ADR-PV01.2 will establish testing patterns and CI integration

6. **Provenance Compression**: For large pipelines, how to avoid verbose provenance chains?
   - **Future consideration**: May need summarization or sampling strategies

7. **Database Schema**: When to implement full provenance database?
   - **Future consideration**: Deferred until usage patterns emerge

8. **Backward Compatibility**: Timeline for migrating existing `correlation_id` to `trace_id`?
   - **Decision**: Gradual migration; `correlation_id` acceptable as alias during transition

---

## Implementation Plan

### Phase 1: Foundation (Immediate)

1. ✅ Create `src/tnh_scholar/provenance/` module
2. ✅ Define `RequestProvenance`, `ServiceProvenance`, `TransportProvenance` models
3. ✅ Define `Fingerprint` model
4. ✅ Add serialization utilities (JSON, file headers)
5. ✅ Update documentation with terminology standards

### Phase 2: CLI Integration (Next PR)

1. Refactor tnh-gen CLI to use `RequestProvenance` with `trace_id`
2. Update file header generation to use standard format
3. Add trace_id to all JSON outputs
4. Update error handling to include trace_id

### Phase 3: Service Integration (Subsequent PR)

1. Alias existing `Provenance` class to `ServiceProvenance`
2. Update GenAIService to use new model
3. Add fingerprint generation to prompt rendering
4. Nest ServiceProvenance within RequestProvenance in CLI

### Phase 4: Adapter & Transport (Future)

1. Add `TransportProvenance` capture in OpenAI adapter
2. Propagate trace_id in HTTP headers (X-Trace-ID)
3. Document adapter patterns for other services

---

## Future Extensions

The following decimal ADRs will provide detailed implementation guidance for specific aspects of the provenance infrastructure. These extend ADR-PV01 without modifying the core strategy decisions.

### ADR-PV01.1: JSON-LD Provenance Vocabulary

**Type**: `implementation-guide`
**Status**: Planned

**Scope**:

- Define Schema.org vocabulary mappings for provenance models
- Integration with existing metadata JSON-LD infrastructure (ADR-MD01/MD02)
- Serialization examples and templates
- Benefits: semantic web compatibility, dataset interoperability, advanced querying

**Key Decisions**:

- Map `RequestProvenance`, `ServiceProvenance`, `TransportProvenance` to Schema.org types
- Use `schema:Provenance`, `schema:Action`, `schema:SoftwareApplication` vocabulary
- Provide bidirectional conversion utilities (internal models ↔ JSON-LD)

### ADR-PV01.2: Provenance Testing Strategy

**Type**: `testing-strategy`
**Status**: Planned

**Scope**:

- Integration test patterns for trace_id propagation across layers
- Property-based tests for consistency (same trace_id in all outputs)
- Serialization/deserialization round-trip tests
- CI/CD integration and regression prevention

**Key Decisions**:

- Test trace_id flows: CLI → service → adapter → transport
- Verify provenance nesting in multi-stage operations
- Assert trace_id consistency in stdout JSON, file headers, logs
- Add provenance assertions to existing service tests

### ADR-PV01.3: OpenTelemetry Compatibility Mapping

**Type**: `design-detail`
**Status**: Planned

**Scope**:

- Mapping table: internal provenance models → OpenTelemetry semantic conventions
- Optional instrumentation layer for OTEL export
- Future migration path to full OTEL tracing
- Preserves investment in current models while enabling future observability

**Key Decisions**:

- Map `trace_id` → OTEL `trace_id` (W3C Trace Context format)
- Map `ServiceProvenance` → OTEL span attributes (provider, model, parameters)
- Map `TransportProvenance.request_id` → OTEL span/event attributes
- Provide serializer module for OTEL export (opt-in)

**Benefits**:

- Future-proofs provenance infrastructure
- Enables integration with OTEL-compatible tools (Jaeger, Zipkin, DataDog)
- No immediate migration required; gradual adoption path

### ADR-PV01.4: Logging & Observability Integration

**Type**: `implementation-guide`
**Status**: Planned

**Scope**:

- Context injection patterns for trace_id in log messages
- Structured logging formatter integration (JSON logs)
- Correlation between provenance and application logs
- Log aggregation and querying patterns

**Key Decisions**:

- Standardized logging context manager (`with trace_context(trace_id)`)
- Custom logging formatter that extracts trace_id from context
- Log message format: `[trace_id=abc123] Operation completed`
- Integration with Python `logging` module and structured loggers (e.g., structlog)

**Benefits**:

- Significantly enhances debugging (grep logs by trace_id)
- Links errors, warnings, and info messages to specific operations
- Enables log-based analysis and alerting

### ADR-PV01.5: Fingerprint Algorithms & Extensibility

**Type**: `design-detail`
**Status**: Planned

**Scope**:

- Pluggable fingerprint algorithm interface
- Default SHA-256 implementation
- Support for alternative algorithms (e.g., BLAKE3 for performance, MD5 for legacy)
- Algorithm selection based on data type or performance requirements

**Key Decisions**:

- Define `FingerprintAlgorithm` protocol with `hash(content: bytes) -> str` method
- Register algorithms in a factory or registry pattern
- Default to SHA-256 for security and compatibility
- Allow per-operation algorithm override via configuration

**Benefits**:

- Flexibility for different use cases (text, audio, images)
- Performance tuning for large datasets
- Future-proof for new hash algorithms

---

## As-Built Notes & Addendums

*Optional section for post-decision updates.*

---

## References

- [W3C Trace Context Specification](https://www.w3.org/TR/trace-context/) - Industry standard for trace propagation
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/) - Standard attribute naming
- [Schema.org Provenance Vocabulary](https://schema.org/Provenance) - JSON-LD provenance schema
- [PROV-DM: The PROV Data Model](https://www.w3.org/TR/prov-dm/) - W3C provenance standard
