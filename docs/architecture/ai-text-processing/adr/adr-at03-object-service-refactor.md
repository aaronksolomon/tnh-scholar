---
title: "ADR-AT03: AI Text Processing Object-Service Refactor"
description: "Three-tier refactor of ai_text_processing module for object-service compliance, GenAIService integration, and prompt system adoption"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: draft
created: "2025-12-07"
---

# ADR-AT03: AI Text Processing Object-Service Refactor

This ADR defines a comprehensive three-tier refactor of the `ai_text_processing` module to achieve object-service architecture compliance (ADR-OS01), integrate with GenAIService (ADR-A13), and adopt the new prompt system (ADR-PT04).

- **Status**: Draft
- **Date**: 2025-12-07
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Sonnet 4.5

## Context

The current `ai_text_processing` module (`src/tnh_scholar/ai_text_processing/`) suffers from architectural debt accumulated during rapid prototyping:

### Current Pain Points

1. **Mixed Concerns**: Business logic (text processing), transport (OpenAI API calls), and prompts intermingled in single files
2. **Tight Coupling**: Direct OpenAI SDK dependencies scattered throughout processors (`openai_process_interface.py`, `line_translator.py`, etc.)
3. **Legacy Prompts**: Hard-coded prompt strings in `prompts.py` instead of modular, versioned prompt templates
4. **No Protocol Contracts**: Missing adapter/port boundaries between domain and infrastructure layers
5. **Testability**: Difficult to test processors without mocking OpenAI SDK internals
6. **Configuration Sprawl**: Ad-hoc configuration handling, no clear precedence rules

### Architectural Vision

The refactor establishes three clear tiers:

```text
┌─────────────────────────────────────────────────────────────┐
│                   Tier 1: Object-Service                    │
│  (Domain models, protocols, adapters, mappers)              │
└────────────────┬────────────────────────┬───────────────────┘
                 │                        │
         ┌───────▼───────┐          ┌──────▼────────┐
         │ Tier 2: GenAI │          │ Tier 3:       │
         │ Service       │          │ Prompt System │
         │ (ADR-A13)     │          │ (ADR-PT04)    │
         └───────┬───────┘          └───────┬───────┘
                 │                          │
                 └──────────┬───────────────┘
                            │
                   ┌────────▼──────────┐
                   │  Transport Layer  │
                   │  (OpenAI SDK,     │
                   │   caching, etc.)  │
                   └───────────────────┘
```

### Design Drivers

1. **Separation of Concerns**: Domain logic isolated from transport and prompts
2. **Testability**: Protocol-based contracts enable comprehensive unit testing
3. **Flexibility**: Swap prompt systems, GenAI providers, or caching strategies without changing domain
4. **Consistency**: Align with object-service architecture used across TNH Scholar (ADR-OS01)
5. **Migration Path**: Incremental refactor without breaking existing functionality

## Decision

### Tier 1: Object-Service Compliance

#### 1.1 Domain Models

Refactor existing models to follow domain-driven design:

```python
# domain/models.py
from pydantic import BaseModel, Field
from enum import Enum

class ProcessingTask(str, Enum):
    """Text processing task types."""
    TRANSLATION = "translation"
    SECTIONING = "sectioning"
    SUMMARIZATION = "summarization"
    GENERAL = "general"

class TextProcessingRequest(BaseModel):
    """Domain request for text processing."""
    text_object: TextObject
    task: ProcessingTask
    target_language: str | None = None
    section_count: int | None = None
    custom_variables: dict[str, str] = Field(default_factory=dict)

class TextProcessingResult(BaseModel):
    """Domain result from text processing."""
    processed_text_object: TextObject
    metadata: ProcessingMetadata
    fingerprint: Fingerprint  # From ADR-PT04

class ProcessingMetadata(BaseModel):
    """Metadata about the processing operation."""
    task: ProcessingTask
    model_used: str
    prompt_key: str
    prompt_version: str
    token_usage: TokenUsage
    processing_time_ms: int
```

#### 1.2 Protocol Contracts

Define ports for external dependencies:

```python
# domain/protocols.py
from typing import Protocol
from .models import TextProcessingRequest, TextProcessingResult

class TextProcessorPort(Protocol):
    """Port for text processing operations."""

    def process(self, request: TextProcessingRequest) -> TextProcessingResult:
        """Process text according to request."""
        ...

class GenAIPort(Protocol):
    """Port for GenAI service integration."""

    def render_and_execute(
        self,
        prompt_key: str,
        variables: dict[str, str],
        model: str | None = None
    ) -> tuple[str, Fingerprint]:
        """Render prompt and execute via GenAI service."""
        ...

class PromptCatalogPort(Protocol):
    """Port for prompt discovery (ADR-PT04 integration)."""

    def get_prompt_for_task(self, task: ProcessingTask) -> str:
        """Get prompt key for processing task."""
        ...
```

#### 1.3 Adapters

Implement adapters to external systems:

```python
# adapters/genai_adapter.py
from ..domain.protocols import GenAIPort
from tnh_scholar.gen_ai_service.services.genai_service import GenAIService
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter

class GenAIServiceAdapter(GenAIPort):
    """Adapter for GenAIService integration."""

    def __init__(
        self,
        genai_service: GenAIService,
        prompts_adapter: PromptsAdapter
    ):
        self._genai = genai_service
        self._prompts = prompts_adapter

    def render_and_execute(
        self,
        prompt_key: str,
        variables: dict[str, str],
        model: str | None = None
    ) -> tuple[str, Fingerprint]:
        """Render prompt via PromptsAdapter, execute via GenAIService."""

        # 1. Render prompt
        rendered, fingerprint = self._prompts.render(
            RenderRequest(
                instruction_key=prompt_key,
                variables=variables,
                user_input=variables.get("input_text", "")
            )
        )

        # 2. Execute via GenAI
        response = self._genai.execute(
            messages=rendered.messages,
            model=model or rendered.model,
            response_format=rendered.response_format
        )

        return response.content, fingerprint
```

#### 1.4 Mappers

Pure mapping functions between layers:

```python
# mappers/text_processing_mapper.py
from ..domain.models import TextProcessingRequest, ProcessingTask
from tnh_scholar.ai_text_processing.text_object import TextObject

class TextProcessingMapper:
    """Maps between domain models and external representations."""

    @staticmethod
    def to_processing_request(
        text_object: TextObject,
        task: ProcessingTask,
        **kwargs
    ) -> TextProcessingRequest:
        """Map TextObject to domain request."""
        return TextProcessingRequest(
            text_object=text_object,
            task=task,
            **kwargs
        )

    @staticmethod
    def to_prompt_variables(
        request: TextProcessingRequest
    ) -> dict[str, str]:
        """Map domain request to prompt variables."""
        variables = {
            "input_text": request.text_object.get_text(),
            **request.custom_variables
        }

        if request.target_language:
            variables["target_language"] = request.target_language
        if request.section_count:
            variables["section_count"] = str(request.section_count)

        return variables
```

### Tier 2: GenAIService Integration

Replace direct OpenAI SDK calls with GenAIService:

#### 2.1 Remove Direct OpenAI Dependencies

**Before (current):**

```python
# openai_process_interface.py (LEGACY)
import openai

def process_with_openai(prompt: str, text: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt + text}]
    )
    return response.choices[0].message.content
```

**After (refactored):**

```python
# services/text_processor_service.py
from ..domain.protocols import GenAIPort, TextProcessorPort
from ..domain.models import TextProcessingRequest, TextProcessingResult

class TextProcessorService(TextProcessorPort):
    """Service for text processing operations."""

    def __init__(self, genai: GenAIPort, prompt_catalog: PromptCatalogPort):
        self._genai = genai
        self._prompts = prompt_catalog

    def process(self, request: TextProcessingRequest) -> TextProcessingResult:
        """Process text via GenAI service."""

        # 1. Get prompt key for task
        prompt_key = self._prompts.get_prompt_for_task(request.task)

        # 2. Map request to variables
        variables = TextProcessingMapper.to_prompt_variables(request)

        # 3. Execute via GenAI adapter
        result_text, fingerprint = self._genai.render_and_execute(
            prompt_key=prompt_key,
            variables=variables
        )

        # 4. Build result
        return self._build_result(request, result_text, fingerprint)
```

#### 2.2 Dependency Injection

Configure dependencies via factory:

```python
# config/factory.py
from tnh_scholar.gen_ai_service.services.genai_service import GenAIService
from tnh_scholar.prompt_system.adapters.git_catalog_adapter import GitPromptCatalog
from ..adapters.genai_adapter import GenAIServiceAdapter
from ..services.text_processor_service import TextProcessorService

def create_text_processor() -> TextProcessorService:
    """Factory for creating configured text processor."""

    # 1. Initialize GenAI service
    genai_service = GenAIService.from_config(GenAIConfig.from_env())

    # 2. Initialize prompt system
    prompt_catalog = GitPromptCatalog.from_config(
        PromptCatalogConfig.from_env()
    )
    prompts_adapter = PromptsAdapter(
        catalog=prompt_catalog,
        renderer=PromptRenderer(...),
        validator=PromptValidator()
    )

    # 3. Build adapters
    genai_adapter = GenAIServiceAdapter(genai_service, prompts_adapter)
    prompt_catalog_adapter = PromptCatalogAdapter(prompts_adapter)

    # 4. Return service
    return TextProcessorService(genai_adapter, prompt_catalog_adapter)
```

### Tier 3: Prompt System Integration

Migrate from `prompts.py` hard-coded strings to modular prompt system:

#### 3.1 Migrate Legacy Prompts

**Before (current):**

```python
# prompts.py (LEGACY)
TRANSLATION_PROMPT = """
Translate the following text to {target_language}:

{input_text}
"""

SECTIONING_PROMPT = """
Divide the following text into {section_count} logical sections:

{input_text}
"""
```

**After (migrated to prompt system):**

```bash
# prompts/translation.md
---
name: translation
version: 1.0
description: Translate text to target language
task_type: translation
required_variables: [input_text, target_language]
optional_variables: []
default_model: gpt-4
output_mode: text
tags: [translation, text-processing]
---

Translate the following text to {{target_language}}:

{{input_text}}
```

```bash
# prompts/sectioning.md
---
name: sectioning
version: 1.0
description: Divide text into logical sections
task_type: sectioning
required_variables: [input_text, section_count]
optional_variables: []
default_model: gpt-4
output_mode: json
response_format: sectioning_response
tags: [sectioning, text-processing]
---

Divide the following text into {{section_count}} logical sections:

{{input_text}}
```

#### 3.2 Prompt Catalog Adapter

Map processing tasks to prompt keys:

```python
# adapters/prompt_catalog_adapter.py
from ..domain.protocols import PromptCatalogPort
from ..domain.models import ProcessingTask

class PromptCatalogAdapter(PromptCatalogPort):
    """Adapter for prompt system integration."""

    # Task → Prompt Key mapping
    TASK_PROMPT_MAP = {
        ProcessingTask.TRANSLATION: "translation",
        ProcessingTask.SECTIONING: "sectioning",
        ProcessingTask.SUMMARIZATION: "summarization",
        ProcessingTask.GENERAL: "general_processing"
    }

    def __init__(self, prompts_adapter: PromptsAdapter):
        self._prompts = prompts_adapter

    def get_prompt_for_task(self, task: ProcessingTask) -> str:
        """Get prompt key for processing task."""
        prompt_key = self.TASK_PROMPT_MAP.get(task)
        if not prompt_key:
            raise ValueError(f"No prompt configured for task: {task}")

        # Validate prompt exists
        try:
            self._prompts.introspect(prompt_key)
        except PromptNotFoundError:
            raise ValueError(f"Prompt not found: {prompt_key}")

        return prompt_key
```

### Migration Strategy

#### Phase 1: Object-Service Foundation (Week 1-2)

1. Create `domain/` directory with models and protocols
2. Implement mappers (pure functions, easy to test)
3. Add unit tests for domain layer (no I/O dependencies)
4. **Deliverable**: Domain models pass all tests

#### Phase 2: GenAI Integration (Week 2-3)

1. Implement `GenAIServiceAdapter` using existing GenAIService
2. Replace `openai_process_interface.py` calls with adapter
3. Add integration tests with mocked GenAI responses
4. **Deliverable**: All processors use GenAIService, no direct OpenAI calls

#### Phase 3: Prompt System Integration (Week 3-4)

1. Migrate prompts from `prompts.py` to `prompts/` directory
2. Implement `PromptCatalogAdapter` with task mapping
3. Update processors to use prompt keys instead of hard-coded strings
4. Add prompt validation tests
5. **Deliverable**: All prompts loaded from prompt system

#### Phase 4: Cleanup & Deprecation (Week 4-5)

1. Mark legacy files (`prompts.py`, `openai_process_interface.py`) as deprecated
2. Update documentation with migration guide
3. Remove unused code after migration verification
4. **Deliverable**: Clean architecture, no legacy code paths

## Consequences

### Positive

- **Testability**: Protocol-based contracts enable comprehensive unit testing without external dependencies
- **Flexibility**: Swap GenAI providers, prompt systems, or caching without changing domain logic
- **Consistency**: Aligns with object-service architecture used across TNH Scholar
- **Maintainability**: Clear separation of concerns makes code easier to understand and modify
- **Reusability**: Domain models and protocols can be shared across other modules
- **Prompt Versioning**: Modular prompts enable A/B testing, rollback, and collaborative editing

### Negative

- **Migration Effort**: Significant refactor required across entire `ai_text_processing` module
- **Learning Curve**: Team must understand object-service patterns, adapters, and protocols
- **Abstraction Overhead**: More layers may slow initial feature development
- **Breaking Changes**: Existing consumers of `ai_text_processing` API must be updated

### Risks

- **Scope Creep**: Three-tier refactor is ambitious; risk of incomplete migration
- **Performance Regression**: Additional abstraction layers may introduce overhead (mitigated by profiling)
- **Coordination Complexity**: Requires coordinated work across GenAIService and prompt system teams

### Mitigation Strategies

1. **Incremental Migration**: Phase-based rollout allows early validation
2. **Backwards Compatibility**: Keep legacy code paths functional during migration
3. **Test Coverage**: Require 80%+ test coverage before deprecating legacy code
4. **Documentation**: Provide migration guide and examples for consumers

## Alternatives Considered

### Alternative 1: Partial Refactor (GenAI Only)

**Approach**: Integrate GenAIService but keep hard-coded prompts.

**Rejected**: Leaves technical debt in prompt management. Misses opportunity for full architectural alignment.

### Alternative 2: Big-Bang Refactor

**Approach**: Rewrite entire module in one PR.

**Rejected**: Too risky. Incremental migration allows early feedback and reduces blast radius.

### Alternative 3: Greenfield Rewrite

**Approach**: Build new `ai_text_processing_v2` module, deprecate old one.

**Rejected**: Increases maintenance burden (two modules). Migration path unclear for consumers.

## Open Questions

1. **Performance Impact**: What is the overhead of adapter/protocol layers? (Requires profiling)
2. **Prompt Versioning**: How do we handle prompt schema changes that break existing processors?
3. **Error Handling**: Should adapters map GenAI exceptions to domain-specific errors?
4. **Caching Strategy**: Where does response caching live—GenAI service or text processor layer?
5. **Legacy Code Removal**: When can we safely delete `prompts.py` and `openai_process_interface.py`?

## References

### Related ADRs

- **[ADR-OS01: Object-Service Architecture V3](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)** - Object-service pattern foundation
 - **[ADR-A13: GenAI Service](/architecture/gen-ai-service/adr/adr-a13-migrate-openai-to-genaiservice.md)** - GenAI service architecture
- **[ADR-PT04: Prompt System Refactor](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)** - New prompt system architecture
- **[ADR-AT01: AI Text Processing Pipeline](/architecture/ai-text-processing/adr/adr-at01-ai-text-processing.md)** - Original text processing design
- **[ADR-AT02: TextObject Architecture](/architecture/ai-text-processing/adr/adr-at02-sectioning-textobject.md)** - TextObject historical context
- **[ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)** - CLI integration patterns
- **[ADR-TG02: Prompt Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)** - CLI ↔ prompt system integration

### External Resources

- [Hexagonal Architecture (Ports & Adapters)](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Dependency Injection Patterns](https://www.martinfowler.com/articles/injection.html)

---

*This ADR defines the comprehensive refactor strategy that enables `tnh-gen` CLI implementation and modern prompt system adoption.*
