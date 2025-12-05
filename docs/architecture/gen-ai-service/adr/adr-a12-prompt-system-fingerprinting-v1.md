---
title: "ADR-A12: Prompt System & Fingerprinting Architecture (V1)"
description: "Replaces the Pattern Catalog adapter with a Prompt-first design that yields domain objects plus fingerprints."
owner: ""
author: ""
status: processing
created: "2025-02-04"
---
# ADR-A12: Prompt System & Fingerprinting Architecture (V1)

Renames Patterns to Prompts and adds fingerprinted domain objects so GenAIService can track provenance cleanly.

- **Status**: Accepted
- **Date**: 2025-02-04
- **Supersedes**: ADR-A02 – Pattern Catalog V1
- **Related**: ADR-P03 (Prompt rename), ADR-A01 (Object-Service Blueprint), ADR-A11 (Model Parameters)

---

## 1. Context

The GenAIService originally adopted a *Pattern Catalog* abstraction (ADR-A02), built around an `patterns.py` system, part of the TNH Scholar suite, from the AI Text Processing module. During implementation, two major issues emerged:

1. **Terminology friction** — the industry-standard term is *Prompt*, and the name “Pattern” conflicted with Python’s regular expression `Pattern` class and caused ambiguity.
2. **Structural mismatch** — ADR-A02 required the adapter to produce `RenderedPrompt + Provenance`.  
   However, provenance is a *domain* concern and should not be constructed inside the adapter, which sits at the boundary between external prompt files and domain objects.
3. **Lack of a clean identity model** — The system needed a domain-level representation of “what was rendered?” for traceability, hashing, and future reproducibility.

During refactoring, the project adopted `prompts.py` as the new API-facing module and rebuilt the adapter using modern conventions. This raised the need for a new ADR that defines the correct architectural shape for Prompt Catalog integration and Fingerprinting.

This ADR replaces ADR-A02 completely.

---

## 2. Decision

### 2.1 Rename “Pattern” to “Prompt” everywhere

- `patterns.py` → `prompts.py`  
- `Pattern` → `Prompt`  
- `PatternCatalog` → `PromptCatalog`  
- `patterns_adapter.py` → `prompts_adapter.py`  
- All public APIs, internal adapters, and domain mapping use the term **Prompt**.

This aligns with industry standards and removes ambiguity with Python’s built‑in regex `Pattern` type.

### 2.2 Adapter returns **pure domain objects** only

The adapter is the boundary between:

- the external prompt disk/API system (`prompts.py`), and
- internal domain structures (`RenderedPrompt`, `Fingerprint`).

Therefore:

```python
PromptsAdapter.render(key, request)  
    → (RenderedPrompt, Fingerprint)
```

The adapter **MUST NOT** construct Provenance.  
It only maps the prompt definition to domain structures and calculates the fingerprint.

### 2.3 Introduce a domain value object: **Fingerprint**

Fingerprint is now a **first-class domain model** located in `domain.py`. It describes *exactly what was rendered* and is the identity anchor for provenance.

```python
class Fingerprint(BaseModel):
    schema_version: Literal["fp-1"] = "fp-1"
    prompt_key: str
    prompt_name: str
    prompt_base_path: str
    prompt_content_hash: str
    variables_hash: str
    user_string_hash: str
```

Properties:

- `schema_version` supports future evolution.
- Tracks prompt location, name, and content hashes.
- Includes template variable hash and user string hash.
- Immutable and serializable.

The adapter constructs this object.  
The domain and service layers treat it as opaque identity metadata.

### 2.4 Move **Provenance construction** into `GenAIService`

Provenance belongs to the business layer. It is constructed *after* the provider call completes, because it must include execution details (provider, model, retry count, timestamps, etc.).

`Provenance` lives in `domain.py` and now includes a Fingerprint:

```python
class Provenance(BaseModel):
    provider: str
    model: str
    sdk_version: str | None = None
    started_at: datetime
    finished_at: datetime
    attempt_count: int = 1
    fingerprint: Fingerprint
```

### 2.5 `provenance.py` becomes a helper/builder module

It now defines:

```python
def build_provenance(
    *,
    fingerprint: Fingerprint,
    provider: str,
    model: str,
    sdk_version: str | None,
    started_at: datetime,
    finished_at: datetime,
    attempt_count: int,
) -> Provenance:
    ...
```

This is the only approved way to construct a Provenance object.

### 2.6 Location of responsibilities

| Component | Responsibility |
|----------|----------------|
| `prompts.py` | Load/save Prompt objects from disk; provide template application. |
| `prompts_adapter.py` | Map external Prompt → RenderedPrompt + Fingerprint. No provenance. No provider logic. |
| `domain.py` | Define all domain models: RenderedPrompt, Fingerprint, Provenance, Message, Role, etc. |
| `provenance.py` | Builder for Provenance; no external API awareness. |
| `service.py` (GenAIService) | Orchestrates workflow, chooses model/provider, calls adapter, provider, and constructs final Provenance. |

### 2.7 Hashing implementation details (V1)

The following helper functions exist in `infra/tracking/fingerprint.py`:

```python
def hash_prompt_bytes(b: bytes) -> str: ...
def hash_vars(vars_dict: dict[str, Any]) -> str: ...
def hash_user_string(s: str) -> str: ...
```

The adapter must use these functions when building the Fingerprint.

---

## 3. Consequences

### 3.1 Cleaner boundary

The external prompt system is now isolated behind a single mapping layer.  
Domain code never touches Prompt objects, disk paths, or parsing.

### 3.2 Provenance is now domain-pure

Provenance now depends only on:

- domain objects,
- runtime execution data.

No external API leakage.

### 3.3 Fingerprinting is fully replaceable

Future fingerprinting strategies (commit hash, dataset ID, model parameters, etc.) can evolve without altering adapter signatures or provenance structures.

### 3.4 ADR-A02 superseded

The PatternCatalog architecture is no longer used and should not be referenced except for historical context.

---

## 4. Status of ADR-A02

ADR-A02 remains in the repository for historical reference but is now marked:

```plaintext
Status: Superseded by ADR-A12
```

---

## 5. Future Work

- ADR-P03 will document the `patterns.py → prompts.py` rename in the general codebase.
- A future ADR may refine Fingerprint schema or introduce reproducible “render bundles.”
- A later version may define a PromptCatalog indexing format or in-memory caching strategy.

---

## 6. Decision Summary (Implementation-Ready)

**Implement immediately:**

1. Add `Fingerprint` and revised `Provenance` to `domain.py`.
2. Update `PromptsAdapter.render()` to return `(RenderedPrompt, Fingerprint)`.
3. Move all provenance construction to `GenAIService`.
4. Update `provenance.py` to provide a pure builder.
5. Use the hashing utilities in `infra/tracking/fingerprint.py`.
6. Update all imports and method signatures accordingly.
7. Mark ADR-A02 as “Superseded.”

This defines the authoritative V1 architecture for Prompt + Fingerprinting inside the Gen AI Service.

## 7. Addendum: V1 Prompt Policy Scope

For the initial V1 walking skeleton:

- `apply_policy` is effectively a pass-through:
  - It uses only the `RenderRequest` intent and explicit model override,
    plus global/default settings.
  - It does **not** use prompt metadata such as `model_hint` or `default_params`.
- The PromptsAdapter returns only `(RenderedPrompt, Fingerprint)`; no additional
  prompt metadata is surfaced to the policy layer in V1.
- Prompt-aware policy (e.g., model selection or temperature tuned by prompt metadata)
  is explicitly deferred to a future ADR.

A later ADR (e.g Prompt Policy V1) will introduce either:

- a `RenderResult`/`PromptMeta` domain object, or
- a revised domain model,
to connect prompt metadata to policy decisions in a principled way.
