---
title: "ADR-A08: Configuration / Parameters / Policy Taxonomy"
description: "Establishes the Config/Params/Policy taxonomy for GenAI Service to prevent parameter soup and clarify ownership."
owner: ""
author: "Aaron Solomon, GPT-5.0"
status: processing
created: "2025-11-15"
---
# ADR-A08: Configuration / Parameters / Policy Taxonomy

Defines distinct Config, Params, and Policy layers so GenAI Service stays composable and avoids parameter soup.

**Status:** Accepted
**Date:** 2025-10-05  
**Author:** Aaron Solomon, ChatGPT (GPT-5)  
**Linked Docs:** ADR-A01 (Object-Service Domain Design), ADR-A09 (Simplified Implementation Pathway)

---

## Context

This ADR defines the taxonomy and separation of **Config**, **Params**, and **Policy** within the `GenAIService` ecosystem. The intent is to maintain clear ownership boundaries, composability, and extendability across providers and environments while preserving simplicity for the early prototype.

The taxonomy follows the principles defined in the *Object-Service Design Blueprint* and *GenAI Service Strategy*, where domain purity and flexibility are prioritized over short-term expediency.

---

## Motivation

The original OpenAI interface used many keyword arguments, mixing runtime options, environment setup, and behavioral constraints. This violated the *parameter soup* antipattern.  
The refactor introduces explicit objects representing distinct layers of control:

- **Config** → Construction-time, environment and provider-level constants  
- **Params** → Per-call, user- or system-provided input for specific invocations  
- **Policy** → Behavioral and safety rules governing all operations  

This separation improves clarity, traceability, and testability while making future provider additions (Anthropic, Gemini, etc.) straightforward.

---

## Taxonomy Overview

| Layer | Description | Lifecycle | Example Fields | Owner |
|-------|--------------|------------|----------------|--------|
| **Config** | Stable construction-time constants and credentials. | Static | `api_key`, `base_url`, `timeout_s`, `default_model`, `price_table` | System |
| **Params** | Per-call adjustable execution inputs. | Ephemeral | `pattern_ref`, `variables`, `images`, `temperature`, `max_output_tokens`, `output_mode`, `model_hint` | Consumer / Caller |
| **Policy** | Behavioral rules governing service operation. | Persistent / Runtime | `BudgetPolicy`, `MediaPolicy`, `SecurityConfig`, `RetryPolicy` | System / Admin |

---

## Relationships

```plaintext
CompletionRequest
 ├── Params (runtime, from caller)
 ├── (no Policy field on request in v1)
 └── Config/Policy applied inside GenAIService
```

- **Params** define what is being asked.
- **Policy** defines how it may be executed.
- **Config** defines where and with what limits.

---

## V1 Implementation Scope

The following subset is implemented in v1 per ADR-A09 (Simplified Pathway):

### Config (GenAIServiceConfig)

```python
class GenAIServiceConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-5o-mini"
    default_timeout_s: float = 60.0
    max_dollars: float = 0.10
```

- Minimal; supports only OpenAI.
- Future: provider registry, dynamic pricing, and per-model metadata.

---

### Params (CompletionParams)

```python
class CompletionParams(BaseModel):
    temperature: float = 0.2
    top_p: float = 1.0
    max_output_tokens: int = 1024
    output_mode: Literal["text", "json"] = "text"
    model_hint: Optional[str] = None
```

- **Note:** Request-scoped inputs (`pattern`, `variables`, `images`) belong on `CompletionRequest`, not in `CompletionParams`. This enforces domain purity and avoids parameter soup per the Human‑Agent Coding Principles.

---

### Policy (CompletionPolicy)

```python
class BudgetPolicy(BaseModel):
    max_dollars: float = 0.10
    fail_on_budget_exceeded: bool = True

class MediaPolicy(BaseModel):
    allow_images: bool = True
    max_image_size_mb: int = 10

class RetryPolicy(BaseModel):
    max_attempts: int = 2
    backoff_ms: int = 250

class SecurityConfig(BaseModel):
    redact_pii: bool = False
    max_input_chars: int = 150_000

class CompletionPolicy(BaseModel):
    budget: BudgetPolicy = BudgetPolicy()
    media: MediaPolicy = MediaPolicy()
    retry: RetryPolicy = RetryPolicy()
    security: SecurityConfig = SecurityConfig()
```

---

## Ownership and Precedence Rules

| Layer | Can be Overridden By | Notes |
|--------|----------------------|-------|
| Config | System only | Reconstructed when environment or provider changes |
| Params | Caller or PatternCatalog | Pattern defaults are overridden by direct input |
| Policy | Admin or System Context | Not mutable at call site (injected by service) |

---

### V1 Decisions & Deferrals

- System message handling deferred: PatternCatalog may later render `system_text`, but v1 renders `user_text` only.  
- Fingerprinting scope: hooks and comments only in v1 (observability), no cache lookup yet.  
- Pricing: use a static, good‑enough price table in config; move to dynamic registry later.  
- Policy ownership: service‑level only in v1; per‑request overrides deferred to v2.

---

## Future Directions (Beyond v1)

1. **Dynamic Provider Discovery** — `GenAIServiceConfig` loads from environment or registry (multi-provider).  
2. **Hierarchical Policies** — Service-level defaults → Project-level overrides → Call-level exceptions.  
3. **Runtime Introspection** — Query `GenAIService` for effective config/policy summary.  
4. **Extensible Params** — Support embeddings, fine-tuning, RAG context injection.  
5. **Externalized Policy Registry** — Optional YAML- or DB-backed runtime policies.

---

## Consequences

### Benefits

- Eliminates “parameter soup.”  
- Makes routing, logging, and safety composable.  
- Simplifies dependency injection and testing.  
- Supports lightweight migration to other providers.

### Drawbacks

- Adds minor verbosity for simple one-off calls.  
- Requires schema evolution management for backward compatibility.

---

## Status & Next Steps

- **Status:** Proposed for v1 implementation.  
- **Next Steps:**  
  1. Integrate with `GenAIService` skeleton.  
  2. Validate via functional test notebook.  
  3. Refine during `ADR-A09` walking skeleton build.
