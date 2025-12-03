---
title: "GenAI Service — Design Strategy"
description: "Strategy for unifying GenAI Service capabilities, personas, and phased releases."
owner: ""
author: ""
status: processing
created: "2025-11-15"
---
# GenAI Service — Design Strategy

Strategy for unifying GenAI Service capabilities, personas, and phased releases.

**Status:** Accepted
**Date** 9-30-2025
**Audience:** TNH Scholar core developers  
**Doc type:** Strategy (pre-ADR)  
**Related:** ADR-P02 Pattern & PatternCatalog (artifact vs service), Object-Service Blueprint, Human-AI Coding Principles

---

## 1) Purpose

Create a **modular, observable, policy-aware GenAI Service** that:

- Powers **single-message** text workflows now (translation, summarization, extraction),
- Adds **image-assisted** prompts (vision-in) as a first-class option,
- Establishes **stable domain shapes** and **provider-agnostic seams** to later support Anthropic and others,
- Enforces **budget, safety, and determinism** (via PatternCatalog + fingerprinting),
- Is small enough to ship immediately, yet extensible to streaming, batching, A/B routing, and tools.

---

## 2) Scope (v1)

- **In scope**
  - Single request → single response (text or JSON text); optional image attachments
  - Model controls (temp/top_p/max_tokens), caps (max_dollars, max_tokens)
  - **PatternCatalog** integration (template resolution, fingerprint)
  - Policy gates (pre/post), redacted structured logging, basic metrics & usage accounting
  - Provider abstraction (OpenAIAdapter v1; AnthropicAdapter skeleton)

- **Out of scope (for v1)**
  - Conversation memory, RAG orchestration, tool/function calling flows
  - Long-running batch runners; complex schedulers
  - Multi-provider federation/ensembles (kept as seam)

---

## 3) Design Principles

1. **Object Service**: single public entry point (`generate`) with strict, typed domain models.  
2. **Transport vs Domain**: domain is pure and immutable; adapters handle all wire formats.  
3. **Determinism**: render with **PatternCatalog** + **PatternFingerprint** for reproducibility & cache keys.  
4. **Policy-first**: cost/time guards, safety scans, JSON validation before/after provider calls.  
5. **Provider-agnostic by construction**: a `ProviderClient` protocol + adapters per vendor.  
6. **Observability by default**: correlation IDs, structured logs, metrics; redact at the boundary.  
7. **Walking skeleton**: ship minimal viable flow; evolve behind stable interfaces.  
8. **Testability**: pure helpers, narrow adapters, golden prompt snapshots, contract tests.

## 3.1) Configuration Taxonomy (Config vs Params vs Policy)

To align with the Object-Service Blueprint and avoid parameter soup, split concerns explicitly (ADR-A08 will formalize details):

- **Config** (construction-time, stable): credentials, timeouts, price table, default routing.
- **Params** (per-call inputs): pattern reference, variables, images.
- **Policy** (behavioral toggles): budgets, output mode, model behavior caps, media limits.

```python
# ai_service/config.py
class GenAIServiceConfig(BaseModel):
    api_key: str
    organization_id: Optional[str] = None
    base_url: Optional[str] = None
    default_timeout_s: float = 60.0
    price_table_version: str = "v1"

# ai_service/domain.py
class CompletionParams(BaseModel):
    temperature: float = 0.2
    top_p: float = 1.0
    max_output_tokens: int = 1024
    output_mode: Literal["text", "json"] = "text"
    model_hint: Optional[str] = None

class CompletionRequest(BaseModel):
    pattern: PatternRef
    variables: dict[str, Any]
    images: list[MediaAttachment] = []
    params: CompletionParams
```

---

## 4) High-Level Architecture

```plaintext
app (callers)
│
▼
GenAIService (Application / Orchestrator)
├─ PatternCatalog (resolve+render+fingerprint)   ← ADR-002
├─ SafetyGate (pre/post checks)
├─ ModelRouter (intent → provider+model)
├─ RateLimiter & RetryPolicy
├─ UsageAccounting
├─ Tracer & Metrics
└─ ProviderClient (protocol)
    ├─ OpenAIAdapter (v1)
    └─ AnthropicAdapter (skeleton)

```

Transport boundary:
CompletionRequest (domain) ──render + policy──▶ ProviderRequest (transport) ──▶ ProviderClient

**Domain Models (immutables):**

- `PatternRef` (id/version), `RenderedPattern` (text, metadata, fingerprint)  
- `MediaAttachment` (Path/bytes, mime, dims)  
- `ModelHint` (name, temperature, max_output_tokens, top_p)  
- `SafetyPolicy` (max_input_chars, max_dollars, allow_image, redact_logs)  
- `CompletionRequest` (patternRef/variables or direct text, images, model hint, output mode)  
- `CompletionResult` (text/json_obj, model, usage, latency_ms, warnings, correlation_id)  
- `ProviderRequest` / `ProviderResponse` (transport-layer normalized shapes)

---

## 5) Request Lifecycle (v1)

1. **Assemble Request**
   - Caller provides `PatternRef` + `variables` (preferred) *or* raw text (escape hatch),
   - Optional images as `MediaAttachment[]`,
   - `CompletionParams` (includes model override fields) + `BudgetPolicy`/`MediaPolicy`.

2. **Introspect + Render Pattern**
   - `PatternCatalog.introspect(id, version?) → PatternMeta`
   - `PatternCatalog.render(id, version?, variables) → RenderedPattern`
   - Compute `fingerprint = sha256(rendered_text + metadata)`

3. **Routing (select provider/model)**
   - `ModelRouter` chooses `(provider, model)` using precedence: **override → pattern default → global default**
   - Guardrail planning: ensure required capabilities (e.g., vision-in) are supported by the candidate.
   - Produce a short `RoutingDecision.reason` for diagnostics.

4. **Pre-Flight Safety & Policy (model-aware)**
   - Estimate tokens/cost **for the selected provider/model** via pricing tables; **fail fast** if `> max_dollars`
   - Enforce `SecurityConfig.max_input_chars`, required variables
   - Optional PII scrubbing for logs (never mutate payload)

5. **Build Provider Request & Call**
   - Build a **ProviderRequest** from rendered text + params/policy + routing decision via helper
   - Call `ProviderClient.generate(provider_request)` with retry policy (retry 429/5xx with jitter)

        ```python
            def _build_provider_request(self, req: CompletionRequest, rendered: RenderedPattern, routing: RoutingDecision) -> ProviderRequest:
                # v1 enforces a fixed temperature to improve determinism
                return ProviderRequest(
                    input_text=rendered.text,
                    images=req.images,
                    model=routing.model,
                    temperature=0.2,
                    max_output_tokens=req.params.max_output_tokens,
                    top_p=req.params.top_p,
                    output_mode=req.params.output_mode,
                    correlation_id=req.correlation_id or generate_ulid(),
                )
        ```

6. **Post-Flight**
   - Parse/validate output; for JSON mode, schema-validate
   - If JSON parse fails → return text + `warnings=["json-parse-failed"]`
   - Update usage accounting; log redacted trace; emit metrics

    The service uses an injected Observer to demarcate phases (render, route, call, parse). Timing is measured in the Observer; the service may read the provider-call span’s duration to populate result latency.

7. **Return**
   - `CompletionResponse` (status envelope) with `result`, `provenance`, `correlation_id`, usage, warnings

**Routing notes (v1):**

For v1 we keep routing deterministic and simple. Precedence is **consumer override → PatternMeta.default_model_hint → global default**. Two immediate guardrails are applied: (a) if images are present, chosen model must support vision-in; (b) if estimated tokens exceed model context, fail fast. Future work (ADR-A04) will add capability filtering, budget/latency heuristics, and optional fallbacks.

---

## 6) Provider Abstraction

```python
class ProviderRequest(BaseModel):
    input_text: str                  # Rendered prompt (post-pattern)
    images: list[MediaAttachment] = []
    model: str
    temperature: float
    max_output_tokens: int
    top_p: float
    output_mode: Literal["text", "json"] = "text"
    correlation_id: str
    system_text: Optional[str] = None  # System message population deferred in v1; PatternCatalog may emit `system_text` later.

class ProviderResponse(BaseModel):
    text: str
    usage: UsageInfo
    model: str
    finish_reason: Optional[str] = None
    raw_response: Optional[dict] = None

class ProviderClient(Protocol):
    def generate(self, request: ProviderRequest) -> ProviderResponse: ...
```

## 6a) Response Envelope

Adopt a standard status envelope so callers can uniformly handle success/failure and partials.

```python
class Envelope(BaseModel):
    status: Literal["pending", "running", "succeeded", "failed", "timeout"]
    error: Optional[str] = None
    diagnostics: dict[str, Any] = {}
    provenance: "Provenance"

class CompletionResult(BaseModel):
    text: str
    json_obj: Optional[dict] = None
    model: str
    usage: UsageInfo
    latency_ms: int
    warnings: list[str] = []

class CompletionResponse(Envelope):
    result: Optional[CompletionResult] = None  # Only present on success
```

---

## 7) PatternCatalog Integration

- Terminology: Patterns are the artifacts; PatternCatalog is the managing service (see ADR-002).
- Responsibilities
- `introspect(ref)` yields `PatternMeta` (task kind, default model hint, expected output mode)
- Pattern lookup (id → content, metadata), Jinja2 render with strict var checks
- Fingerprint (rendered_text + metadata) for cache keys and observability
- Optional template lint: length bounds, forbidden substrings, required headers
- Interfaces
- render(ref, variables) -> RenderedPattern
- introspect(ref) -> PatternMeta (task kind, default model caps, expected output mode)

### V1 implementation note — reuse existing TNH‑Scholar patterns

For V1 we will *wrap* the existing module `ai_text_processing.patterns` to provide the `PatternCatalog` API, avoiding a disruptive migration.

- Wrapper: `ai_service/patterns_adapter.py` exposes `render()` and `introspect()` by delegating to the current TNH‑Scholar pattern system.
- Mapping: existing pattern IDs and variable names are preserved; the adapter raises strict errors on missing variables.
- Fingerprint: compute `sha256(rendered_text + metadata_json)` in the adapter (non‑breaking to upstream code).
- Ownership: no changes to `ai_text_processing.patterns` in V1; a dedicated ADR will cover converging the two systems post‑V1.
- Test plan: golden renders compare adapter output to the legacy `ai_text_processing.patterns` output for a fixed set of patterns.

### Service flow using introspect

```python
pattern_meta = PatternCatalog.introspect(pattern_ref)
rendered = PatternCatalog.render(pattern_ref, variables)
fingerprint = sha256(rendered.text + rendered.metadata_json)

# Routing influenced by introspection
intent = pattern_meta.task_kind
provider, model = ModelRouter.select(intent, override=CompletionParams(...))

# Validate expected output mode from pattern vs request
assert pattern_meta.output_mode in ("text", "json")
```

---

## 8) Safety & Policy (split across Config/Policy/Params)

- Input size guard via `SecurityConfig.max_input_chars`
- Budget guard via `BudgetPolicy.max_dollars`
- Optional PII redaction for logs via `SecurityConfig.redact_pii`
- Media limits via `MediaPolicy` (count/MB), optional EXIF strip
- Post-flight:
  - Output JSON schema (when requested)
  - Optional content filters (basic profanity/PII detection for display surfaces)
- Error taxonomy:
  - PolicyError (budget/size/validation)
  - TransportError (HTTP/SDK)
  - ProviderError (non-retryable)
  - FormatError (JSON parsing/validation)

---

## 9) Observability

- Tracing: correlation_id (ULID), pattern_id, pattern_fingerprint, provider, model, attempts, latency
- Logging: single structured line per phase (render → policy → call → parse) with redaction
- Metrics:
- llm_calls_total{provider, model, intent, outcome}
- llm_latency_ms_bucket{provider, model, intent}
- llm_retries_total{provider, model}
- llm_dollars_total{provider, model}
- Usage accounting: prompt/completion tokens and $ per call + rolling window counters

**Provenance (aligned with tracing):**

```python
class Provenance(BaseModel):
    backend: str            # e.g., "openai"
    model: str
    correlation_id: str
    pattern_id: str
    pattern_fingerprint: str
    started_at: str
    completed_at: str
    schema_version: str = "1.0"
    # Optional (v1.1+): provider_request_id, routing_reason, retry_count, policy_version
```

## 9a) Observation Seam (Observer + Clock/Timer)

We establish an observation seam now so the service never performs low-level timing or unit conversions. The service emits phase events; an injected Observer (with a Clock/Timer) measures and records durations. Default implementations can be no-ops.

```python
from __future__ import annotations
from typing import Protocol, Any

class Clock(Protocol):
    def now_ms(self) -> int: ...  # monotonic milliseconds

class ObsSpan(Protocol):
    def __enter__(self) -> "ObsSpan": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    @property
    def duration_ms(self) -> int: ...

class Observer(Protocol):
    def phase(self, name: str, **fields: Any) -> ObsSpan: ...

class NoOpClock:
    def now_ms(self) -> int:  # placeholder monotonic clock
        return 0

class NoOpSpan:
    def __enter__(self) -> "NoOpSpan":
        return self
    def __exit__(self, exc_type, exc, tb) -> None:
        pass
    @property
    def duration_ms(self) -> int:
        return 0

class NoOpObserver:
    def phase(self, name: str, **fields: Any) -> ObsSpan:
        return NoOpSpan()
```

The concrete implementation (e.g., BasicObserver) can wrap time.perf_counter_ns() or OpenTelemetry without changing GenAIService.

---

## V1 Decisions & Deferrals

- System message handling deferred: PatternCatalog may later render `system_text`, but v1 renders `user_text` only.  
- Fingerprinting scope: hooks and comments only in v1 (observability), no cache lookup yet.  
- Pricing: use a static, good‑enough price table in config; move to dynamic registry later.  
- Policy ownership: service‑level only in v1; per‑request overrides deferred to v2.

---

## 10) Configuration

- **GenAIServiceConfig**: credentials (OpenAI/Anthropic), base URLs, default timeout, price table version
- **RoutingPolicy**: intent → (provider, model) mapping; guardrails
- **SecurityConfig**: redaction and input-size bounds
- **BudgetPolicy**: per-call or default budget caps
- Retry/backoff policy
- Secrets: env or Secret Manager; keys never logged; redact in traces.

---

## 11) Testing Strategy

- Unit (pure): Pattern rendering, fingerprint determinism, cost estimator, router decisions, safety gates
- Adapter (mocked): Wire payloads, error mapping, usage extraction
- Contract (opt-in live): Minimal smoke gated by RUN_LIVE=1
- Golden tests: Snapshot rendered prompts (hash), schema-valid JSON outputs for fixed seeds
- Property tests: Renderer never exceeds size limits; required vars enforced

---

## 12) Migration Plan (from openai_interface.py)

This project is in **0.x prototyping**. We will refactor callers to use `GenAIService.generate()` directly; **no backward compatibility shims** are required. Provenance fields (pattern id, fingerprint, correlation id) will be included from the start to enable future reproducibility, even though we do not aim to recreate results during early prototyping.

**PatternCatalog V1 migration**: The `PatternCatalog` used by `GenAIService` is a thin wrapper over the existing `ai_text_processing.patterns` module. Callers migrate to `GenAIService.generate()` without changing pattern IDs/variables; the adapter handles rendering, metadata, and fingerprinting.

---

## 13) Roadmap (post-v1)

- Streaming responses; token-level handlers
- Batch jobs with idempotency keys; resumable on failure
- A/B routing & canaries (per intent)
- Cache (pattern_fingerprint + variables + model) with TTL and budget heuristics
- Tool/function calling seam in domain layer
- Richer safety (semantic jailbreak detection, content classifiers)
- Multi-provider policy (price/perf aware router; automatic failover)

---

## 14) Deliverables (v1 Walking Skeleton)

- ai_service/domain.py: dataclasses (PatternRef, ModelHint, MediaAttachment, CompletionRequest/Result)
- ai_service/policy.py: SafetyPolicy, pre/post gates, pricing estimator
- ai_service/patterns_adapter.py: Thin wrapper around `ai_text_processing.patterns` exposing `PatternCatalog` (`render`, `introspect`, `fingerprint`).
- ai_service/patterns.py: Facade/typing for `PatternCatalog`; may later switch the backing implementation without affecting callers.
- ai_service/router.py: ModelRouter (intent → provider/model)
- ai_service/providers/base.py: ProviderClient protocol, ProviderRequest/ProviderResponse
- ai_service/providers/openai_adapter.py: concrete OpenAI adapter
- ai_service/service.py: GenAIService.generate() orchestration
- ai_service/obs.py: tracer, metrics, usage accounting
- tests/…: golden renders, adapter mocks, policy tests

---

## 15) Rationale & Trade-offs

- Why single entrypoint? Centralized policy/observability, simple testing.  
- Why fingerprint? Reproducibility, cache keys, transparent science.  
- Why strict shapes? Easier refactors, provider swaps, and property testing.  
- Why not tools/RAG now? Keeps v1 small, ships value, preserves clean seams.  
- Why ProviderRequest object? Eliminates parameter soup, creates a stable transport boundary to adapters.  
- Service-level policy ownership in v1; per-request deferred.
- Fingerprinting used for observability only in v1.  
- Static price table used initially; dynamic pricing planned.

---

## 16) Open / Existing Items for ADRs

- ADR-A01: Object-Service adoption & domain shapes  
- ADR-A02: PatternCatalog integration & fingerprinting semantics (ref ADR-002)  
- ADR-A03: Safety policy (limits, PII redaction, JSON schema validation)  
- ADR-A04: Model routing rules & provider guardrails  
- ADR-A05: Observability contract (logs/metrics/retention/redaction)  
- ADR-A06: Error taxonomy & retry/backoff policy  
- ADR-A07: Image attachment policy (limits, EXIF, mime support)  
- ADR-A08: Config vs Params vs Policy taxonomy (ownership, precedence, defaults)
- ADR-A09: V1 Simplified Implementation Pathway
- ADR-A10: Unify `ai_text_processing.patterns` with `PatternCatalog` (adapter → consolidation plan, deprecation policy)
- ADR-A11: Minor model and parameters fix

---

## 17) Acceptance for v1

- Deterministic prompt rendering via PatternCatalog + fingerprint  
- Policy gates enforce caps; clear error taxonomy  
- OpenAIAdapter returns normalized CompletionResponse (status envelope + result)  
- Observability: correlation IDs, structured logs, basic metrics  
- AnthropicAdapter skeleton builds cleanly (provider-agnostic seam proven)  

---
