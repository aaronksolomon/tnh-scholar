---
title: "Object-Service Design Overview"
description: "High-level overview of TNH Scholar's layered architecture for complex objects and API-backed services."
owner: ""
author: ""
status: processing
created: "2025-11-29"
---
# Object-Service Design Overview

High-level overview of TNH Scholar's layered architecture for complex objects and API-backed services.

## Purpose

This document provides a high-level introduction to the Object-Service design pattern used throughout TNH Scholar. For complete architectural details, see [ADR-OS01: Object-Service Design Architecture V3](adr/adr-os01-object-service-architecture-v3.md).

## Core Principle

**Goal**: Ship reliable, composable features fast by separating concerns and keeping boundaries explicit.

## Architectural Layers

```text
Application Layer (CLI, notebooks, web, Streamlit)
  └─ Orchestrators (thin): <Feature>Processor, ResultWriter
        ▲
        │ domain objects / protocols
        │
Domain Service Layer
  └─ <Feature>Service (Protocol-based orchestrator)
     └─ ProviderClient (impl: OpenAIClient, PyannoteClient, etc.)
        └─ RequestMapper (bi-directional: domain ↔ transport)
           └─ TransportClient (HTTP, polling, streaming)
        ▲
        │ transport models (anti-corruption boundary)
        │
Transport Layer
  └─ VendorClient  (upload/start/status/poll, retries, rate-limit)
     JobPoller     (backoff, jitter, deadline)
```

## Key Design Contracts

1. **Config at init, Params per call, Response envelope always**
2. **Service protocol is minimal**: `start()`, `get_response()`, `generate()` for async jobs; `generate()` or `run()` for sync
3. **Adapter maps API shapes** → canonical domain shapes (bi-directional)
4. **All payloads use strong typing** (Pydantic or dataclass models)
5. **No literals or untyped dicts** in application logic

## Primary Benefits

- **Separation of Concerns**: Domain logic isolated from API transport details
- **Testability**: Each layer can be tested independently with clear interfaces
- **Flexibility**: Swap providers without changing application code
- **Type Safety**: Strong typing throughout prevents runtime errors
- **Maintainability**: Clear boundaries make refactoring safer

## Core Services

Current TNH Scholar services following this architecture:

- **GenAIService**: AI text processing with OpenAI/Anthropic providers
- **TranscriptionService**: Audio transcription with Whisper/AssemblyAI providers
- **DiarizationService**: Speaker diarization with Pyannote provider

Future services planned:

- **PromptCatalogService**: Enhanced prompt management
- **EmbeddingService**: Text embeddings for semantic search
- **VectorStoreService**: Vector database integration

## Implementation Status

See [object-service-implementation-status.md](object-service-implementation-status.md) for current gaps, resolved items, and planned work.

## Related Documentation

- [ADR-OS01: Object-Service Design Architecture V3](adr/adr-os01-object-service-architecture-v3.md) - Complete architectural specification
- [Implementation Status](object-service-implementation-status.md) - Gaps analysis and progress
- [Design Principles](/development/design-principles.md) - General design philosophy
- [Conceptual Architecture](/project/conceptual-architecture.md) - High-level system model

## Quick Reference

### Service Protocol Example

```python
from typing import Protocol

class TextProcessingService(Protocol):
    """Protocol for text processing services."""

    def generate(
        self,
        request: ProcessingRequest
    ) -> ProcessingResponse:
        """Process text and return result."""
        ...
```

### Adapter Pattern Example

```python
class OpenAIAdapter:
    """Maps domain models to/from OpenAI API."""

    def to_api_request(
        self,
        domain_request: ProcessingRequest
    ) -> OpenAICompletionRequest:
        """Map domain request to OpenAI format."""
        ...

    def from_api_response(
        self,
        api_response: OpenAICompletion
    ) -> ProcessingResponse:
        """Map OpenAI response to domain format."""
        ...
```

For complete examples, templates, and detailed patterns, see [ADR-OS01](adr/adr-os01-object-service-architecture-v3.md).
