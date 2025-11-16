# API Integration Blueprint (Generic)

*A practical, layered blueprint for designing professional‑grade modules that talk to web APIs—cleanly, testably, and safely. Examples reference a "diarizer" service, but the patterns are generic.*

---

## 1 Executive Summary

Robust API integrations succeed when **domain**, **service**, and **transport** concerns are kept sharply separated, interactions are constrained through **small protocols**, and **failures are first‑class citizens** (explicit envelopes, retries, idempotency, and observability).

This document provides:

- A **layered architecture** that generalizes across diarization, transcription, payments, etc.
- A **configuration taxonomy** (domain vs. service vs. transport) so options don’t leak across layers.
- A **contract & envelope design** that scales to partials, failures, and future extensions.
- A **testing & observability plan** to keep things reliable as you evolve.

---

## 2 Layered Architecture (Ports & Adapters)

```text
Application Layer (CLI, notebooks, web)
  └─ Orchestrators (thin): <Feature>Processor, ResultWriter
        ▲           
        │ domain models / protocols
        │
Domain Service Layer
  └─ <Feature>Service (Protocol)
     └─ VendorService (impl)  ── uses ──> VendorAdapter (transport → domain)
                                       └─> VendorClient (HTTP, polling)
        ▲
        │ transport models (anti‑corruption boundary)
        │
Transport Layer
  └─ VendorClient  (upload/start/status/poll, retries, rate‑limit)
     JobPoller     (backoff, jitter, deadline)
```

### Key principles

- The **client** knows HTTP, not domain.
- The **service** composes client + adapter to return **domain envelopes**.
- The **processor** calls the service via a small **protocol**, persists results, and stays dumb.

---

## 3 Configuration Taxonomy

Keep configuration in three buckets so concerns don’t leak across layers. Below are **lightweight generic stubs** you can drop into any project.

```python
# config/policy.py
from typing import Literal, Optional
from pydantic import BaseModel

# 3.1 Domain Policy (app‑level)
class DomainPolicy(BaseModel):
    """Domain concerns about how the app wants to use the service.

    Example fields:
      - completion_mode: whether to return a snapshot immediately or wait
      - deadline_s: absolute deadline for the operation (UI or workflow driven)
      - allow_partials: OK to return partial results on timeout?
    """
    completion_mode: Literal["snapshot", "wait"] = "wait"
    deadline_s: Optional[float] = None
    allow_partials: bool = True


# 3.2 Service Policy (mapping/normalization)
class ServicePolicy(BaseModel):
    """Adapter/service‑side decisions about canonical shape and normalization.

    Example fields for a diarizer:
      - default_speaker_label
      - single_speaker
      - min_segment_ms
    For other domains, swap in relevant normalization knobs.
    """
    # Example defaults (customize per domain)
    default_label: str = "DEFAULT"
    normalize_case: bool = True
    min_unit_size: int = 0  # e.g., min segment/token length, ms/characters/etc.


# 3.3 Transport Config (HTTP concerns)
class TransportConfig(BaseModel):
    """Pure transport/HTTP configuration; only the client sees this.

    Applies across vendors: timeouts, retries, backoff, rate limiting, auth.
    """
    base_url: str
    api_key: str
    connect_timeout_s: float = 10
    read_timeout_s: float = 30
    max_retries: int = 5
    backoff_base_s: float = 0.5
    backoff_max_s: float = 8.0
    rate_limit_rps: float = 5.0
```

> **Rule of thumb**
>
> - If it’s about *wire behavior* → **TransportConfig**
> - If it’s about *domain semantics* → **DomainPolicy**
> - If it’s about *shape of your canonical data* → **ServicePolicy**

---

## 4 Canonical Domain Envelope (Generic)

Below is a generic envelope; specialize the payload for your feature (e.g., `segments` for diarization, `transcript` for ASR, `charges` for payments).

```python
# domain/models.py
from typing import Optional, Literal, Any
from pydantic import BaseModel

class Provenance(BaseModel):
    backend: str              # e.g., "pyannote", "assemblyai", "stripe"
    model: Optional[str] = None
    job_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    params: dict = {}

class Envelope(BaseModel):
    status: Literal["pending","running","succeeded","failed","timeout"]
    payload: Optional[Any] = None        # feature‑specific object; None unless succeeded
    error: Optional[str] = None
    diagnostics: dict = {}
    provenance: Provenance
```

### Invariants

- `payload` present **only** when `status == "succeeded"`.
- `error` only for `failed`.
- `provenance.job_id` should be set when available (embed `job_id` at the transport boundary).

---

## 5 Protocols (Small, Stable, Swappable)

```python
# domain/service.py
from pathlib import Path
from typing import Optional, Protocol

class FeatureParams(BaseModel):
    """API‑facing parameters (safe subset for domain).
    Replace with e.g., DiarizationParams/TranscriptionParams, etc.
    """
    pass

class FeatureService(Protocol):
    def start(self, input_path: Path, params: Optional[FeatureParams] = None) -> str: ...
    def get_response(self, job_id: str, *, wait_until_complete: bool = False) -> Envelope: ...
    def generate(self, input_path: Path, params: Optional[FeatureParams] = None,
                 *, wait_until_complete: bool = True) -> Envelope: ...
```

Optionally define `ResultWriter` and `EventSink` protocols for persistence and observability.

---

## 6 Adapter Rules (Transport → Domain)

- Map **success** payloads to `payload` + `status="succeeded"`.
- Map **in‑progress** to `pending`/`running` with no payload.
- Map **timeout** to `timeout` (optionally with partials if supported).
- Map **API failures** to `failed` with structured `error`.
- Always fill `provenance` (backend/model/job_id/params/timestamps).

---

## 7 Long‑Running Jobs & Control Flow

- **start()** → returns `job_id` (also stored in transport objects and copied into `provenance`).
- **get_response(job_id, snapshot vs wait)** → domain envelope mirrors current or final state.
- **generate()** → one‑shot path: start + wait/snapshot.
- **Cancellation/Deadlines** → pass `DomainPolicy` to service; service enforces via poller.

---

## 8 Resilience Patterns

- **Retries**: idempotent calls only; exponential backoff + jitter; classify retryable errors.
- **Rate limiting**: client‑side token bucket; honor `Retry‑After`.
- **Timeouts & Deadlines**: both connect/read timeouts and absolute deadlines.
- **Circuit breaker**: open after N consecutive failures; half‑open probes.
- **Idempotency keys**: use when starts can accidentally duplicate jobs.

---

## 9 Observability

- **Structured logs** with `job_id`, input hash, request_ids.
- **Metrics**: p50/p95 latencies, error rate by class, retries, timeouts, queue vs run time.
- **Tracing**: spans for upload/start/poll; propagate correlation IDs.
- **Provenance** captured in the domain envelope.

---

## 10 Security & Privacy

- Secrets from env/secret manager; never log tokens.
- Minimize PII; redact logs; encrypt at rest.
- Validate hosts, enforce TLS, explicit timeouts (no hangs).

---

## 11 Testing Strategy

This represents the long term ideal strategy. In prototyping not all of this testing will be enacted.

- **Unit**: adapter mapping (golden fixtures), client retry/backoff (fake server), service logic (fake client+adapter).
- **Contract**: validate assumptions against real API in CI (nightly).
- **Record/Replay**: VCR‑style cassettes to stabilize tests.
- **Property‑based**: fuzz adapter with constrained transport payloads.
- **Load/Chaos**: slow responses, intermittent 500s, rate‑limit bursts.
- **Policy tests**: snapshot vs wait, deadlines, partials.

---

## 12 Versioning & Evolution

- Version the domain envelope (e.g., `provenance.schema_version`).
- Additive changes preferred; keep adapter tolerant of unknown transport fields.
- For breaking API changes, introduce a new service/adapter version and migrate gradually.

---

## 13 Walking Skeleton (Suggested Build Order)

1. Domain models (`Envelope`, `Provenance`, feature payload types).
2. Transport client with `job_status` and `start` (happy path).
3. Adapter (success path mapping).
4. Service (`generate()` success path).
5. Processor + `ResultWriter`.
6. Add timeouts/polling/retries.
7. Add failure/timeout mapping; enrich provenance.
8. Add metrics/logs; then broaden tests.

---

## 14 End‑to‑End Checklist

- [ ] Domain envelope has **status**, **payload**, **error**, **provenance**.
- [ ] Client implements **timeouts**, **retries**, **rate limiting**, **idempotency** where applicable.
- [ ] Adapter maps all transport outcomes to domain envelopes.
- [ ] Service honors `DomainPolicy` (`snapshot`/`wait`, deadlines, partials).
- [ ] Processor writes only via `ResultWriter`.
- [ ] Logs/metrics/traces include **job_id** and **input hash**.
- [ ] Tests cover success, timeout, failure, retries, mapping, policy.
- [ ] Configs are **separated** (domain vs service vs transport).
- [ ] `job_id` embedded in transport status objects (and copied to provenance).
- [ ] Provenance includes backend, model, params, timestamps.
