---
title: "ADR-A09: V1 Simplified Implementation Pathway"
description: "Defines the minimum viable GenAI Service implementation that preserves architectural seams while shipping quickly."
owner: ""
author: "Aaron Solomon, GPT-5.0"
status: processing
created: "2025-11-15"
---
# ADR-A09: V1 Simplified Implementation Pathway

Outlines the pared-down GenAI Service build that keeps public seams intact but stubs complex internals for faster delivery.

**Status:** Accepted  
**Date:** 2025-10-05  
**Author:** Aaron Solomon, ChatGPT (GPT‑5)  
**Linked Docs:** [GenAI Service — Design Strategy (v0.2)](../design/genai-service-strategy.md), [ADR‑A01 (Domain & Object Service)](adr-a01-domain-service.md)

---

## Purpose

This ADR captures the **simplified implementation pathway** for the first working release of the `GenAIService`. It preserves the architectural intent and interfaces of the strategy document but scales back complexity to achieve a **usable prototype quickly**. The goal is to reach a point where the system can “work on itself” via VS Code integration for AI‑assisted development.

---

## Guiding Principles

- Preserve all seams (router, safety, observability, policy) but stub or simplify internal logic.  
- Prioritize usability, determinism, and end‑to‑end working flow over completeness.  
- Keep the public shapes and interfaces stable for future ADRs.

---

## Simplification Overview

| Subsystem | Simplified for v1 | Deferred / Full in Future |
|------------|------------------|----------------------------|
| **Routing** | Single provider (`OpenAIAdapter`); model selected by Pattern `model_hint` if available, otherwise falls back to default (`gpt-4o-mini`). | Capability filtering, multi-provider, latency/budget heuristics |
| **Params / Policy** | Keep `temperature`, `max_output_tokens`, `output_mode`, and `max_dollars`. Use constants for other fields. | Full taxonomy ADR‑A08 (ownership, precedence, defaults) |
| **Preflight** | Use fixed constants: `MAX_INPUT_CHARS`, naive token estimator (`len(text)/3`), `MAX_CONTEXT_TOKENS=128k`, `MAX_DOLLARS`. | Model‑aware tokenizers and price tables |
| **Images** | Support basic JPEG/PNG via `Path`; generic handling (no image count limit, simple type validation). | Byte uploads, EXIF stripping, type registry |
| **JSON mode** | Prompt for JSON; `json.loads` parse; warn on failure. | Schema validation, structured field coercion |
| **Observability** | Single log line with `{cid, pattern_id, model, latency_ms, dollars}`; ULID correlation only. | Metrics registry, retention, structured tracing |
| **Errors** | Implement `PolicyError`, `TransportError`, `FormatError`. | Extended error taxonomy, redaction, retries w/ jitter |
| **Retries** | One retry on 429/5xx, 250 ms backoff. | Configurable policy, exponential/jitter, rate limiting |
| **PatternCatalog** | Only `render()` and `introspect()` returning `{task_kind, default_model_hint, output_mode}`. | Linting, forbidden tokens, metadata schema |
| **ProviderRequest** | Minimal fields: text, images, model, temperature, max_output_tokens, output_mode, correlation_id. | System messages, raw response, full transport |
| **Convenience API** | Add `openai_generate()` helper to simplify testing and notebook/extension use. | None—core UX improvement |

Convenience API definition suggestion:

```python
# ai_service/convenience.py
def openai_generate(pattern_name: str, variables: dict[str, Any], *, temperature: float = 0.2, max_tokens: int = 1024, images: list[Path] | None = None) -> str:
    service = GenAIService.from_env()  # factory to be added later
    req = CompletionRequest(
        pattern=PatternRef(id=pattern_name),
        variables=variables,
        images=[MediaAttachment(path=p, mime="image/jpeg") for p in (images or [])],
        params=CompletionParams(temperature=temperature, max_output_tokens=max_tokens),
    )
    resp = service.generate(req)
    if resp.status != "succeeded" or not resp.result:
        raise RuntimeError(f"Generation failed: {resp.error}")
    return resp.result.text
```

---

## Definition of Done (Prototype Ready)

1. `GenAIService.generate()` works end‑to‑end for:
   - Text → Text (translation, summarization)
   - Text + Image → Text (vision‑in)
2. Constants enforce budget, context, and size limits.
3. OpenAIAdapter functional; AnthropicAdapter skeleton compiles.
4. JSON mode yields `warnings=["json‑parse‑failed"]` when needed.
5. Correlation ID and basic structured log emitted.
6. `openai_generate()` convenience API available for direct IDE/extension use and rapid testing.

---

## Development Milestones

1. Skeleton compile pass: domain + provider base + OpenAI adapter.  
2. Pattern render + fingerprint (example pattern).  
3. Generate() text flow + log + usage.  
4. Add image support (Path).  
5. Add JSON mode.  
6. Add budget/context guards.  
7. Add simple_generate().  
8. Add Anthropic skeleton.

---

## Rationale

This approach enables a **walking, testable skeleton** within minimal engineering effort.  
It allows for immediate integration with VS Code extensions and the PatternCatalog system, creating an environment where AI agents can progressively enhance their own supporting infrastructure.

- Service-level policy only in v1; no per-request overrides.  
- Fingerprinting used for observability hooks only, no caching yet.  
- Static price table in config; dynamic pricing registry deferred.

---

## Status & Next Steps

- Review for approval by TNH Scholar core devs.  
- Upon acceptance, this ADR governs the immediate implementation sequence for `GenAIService v1`.  
- Follow‑ups:  
  - ADR‑A04 (Routing Rules & Guardrails)  
  - ADR‑A08 (Config/Params/Policy taxonomy) *complete*

---
