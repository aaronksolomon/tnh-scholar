---
title: "TNH Scholar Object & Service Design Blueprint"
description: "*A practical, opinionated blueprint for the overall direction for design, implementation, and evolution of complex objects and API-backed services across the TNH Scholar suite. It presents the big picture first, then the fine details, and ends with boilerplate templates you can copy‑paste to sketch new systems.*"
owner: ""
status: processing
created: "2025-11-15"
---
# TNH Scholar Object & Service Design Blueprint

*A practical, opinionated blueprint for the overall direction for design, implementation, and evolution of complex objects and API-backed services across the TNH Scholar suite. It presents the big picture first, then the fine details, and ends with boilerplate templates you can copy‑paste to sketch new systems.*

---

## 0. Big Picture (at a glance)

**Goal:** ship reliable features fast by separating concerns and keeping boundaries explicit.

```text
Application Layer (CLI, notebooks, web)
  └─ Orchestrators (thin): <Feature>Processor, ResultWriter
        ▲           
        │ domain objects / protocols
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

### One‑line contracts

- **Config at init**, **Params per call**, **Response envelope** always.
- Service protocol is tiny: `start()`, `get_response()`, `generate()`.
- Adapter maps API shapes → canonical domain shapes.

---

## 1. Core Concepts & Naming

- **Config** (`ThingConfig`): construction‑time settings; stable; immutable.
- **Params** (`ThingParams`): per‑call inputs; vary run‑to‑run.
- **Policy** (`DomainPolicy`, `ServicePolicy`): opinionated behavior toggles.
- **Context** (`ExecutionContext`): ephemeral runtime state (optional, pipelines only).
- **Response** (`ThingResponse`): discriminated union (status + diagnostics + provenance + *optional* Result).
- **Result** (`ThingResult`): canonical success payload embedded in Response.
- **Client**: pure transport/HTTP.
- **Adapter**: transport → domain mapping.
- **Service**: composes Client + Adapter; implements protocol.
- **Processor**: thin façade for apps; wires persistence & small conveniences.

> **Rule of thumb**  
> Wire behavior → Client.  
> Canonical data shape → Adapter/Service.  
> Usage intent → Params/Policy.  
> Long‑lived configuration → Config.

---

## 2. Configuration Taxonomy (stubs)

```python
# config/policy.py
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

class DomainPolicy(BaseModel):
    """Domain concerns about how the app wants to use the service."""
    completion_mode: Literal["snapshot", "wait"] = "wait"
    deadline_s: Optional[float] = None
    allow_partials: bool = True

class ServicePolicy(BaseModel):
    """Adapter/service‑side normalization and mapping decisions."""
    default_label: str = "DEFAULT"
    normalize_case: bool = True
    min_unit_size: int = 0

class TransportConfig(BaseModel):
    """Pure transport/HTTP configuration; only the client sees this."""
    base_url: str
    api_key: str = Field(repr=False)
    connect_timeout_s: float = 10
    read_timeout_s: float = 30
    max_retries: int = 5
    backoff_base_s: float = 0.5
    backoff_max_s: float = 8.0
    rate_limit_rps: float = 5.0

    @classmethod
    def from_env(cls) -> "TransportConfig":
        import os
        return cls(
            base_url=os.environ.get("VENDOR_BASE_URL", ""),
            api_key=os.environ.get("VENDOR_API_KEY", ""),
        )
```

---

## 3. Canonical Domain Envelope (generic)

```python
# domain/models.py
from __future__ import annotations
from typing import Any, Optional, Literal, List
from pydantic import BaseModel

class Provenance(BaseModel):
    backend: str                    # e.g., "pyannote", "assemblyai", "openai"
    model: Optional[str] = None
    job_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    schema_version: str = "1.0"
    params: dict = {}

class Envelope(BaseModel):
    status: Literal["pending", "running", "succeeded", "failed", "timeout"]
    result: Optional[Any] = None        # feature‑specific; present only on success
    error: Optional[str] = None
    diagnostics: dict = {}              # curated, not a dump
    provenance: Provenance

    def succeeded(self) -> bool:
        return self.status == "succeeded"
```

### Invariants

- `result` only when `status == "succeeded"`.
- `error` only for `failed`.
- `provenance.job_id` should be set when available (embed at transport boundary).

---

## 4. Service Protocol & Boilerplate

```python
# domain/service.py
from __future__ import annotations
from pathlib import Path
from typing import Optional, Protocol
from pydantic import BaseModel
from .models import Envelope

class FeatureParams(BaseModel):
    """API‑facing parameters (safe subset)."""
    pass

class FeatureService(Protocol):
    def start(self, input_path: Path, params: Optional[FeatureParams] = None) -> str: ...
    def get_response(self, job_id: str, *, wait_until_complete: bool = False) -> Envelope: ...
    def generate(self, input_path: Path, params: Optional[FeatureParams] = None,
                 *, wait_until_complete: bool = True) -> Envelope: ...
```

---

## 5. Transport Client & Job Poller (skeleton)

```python
# transport/client.py
from __future__ import annotations
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from ..config.policy import TransportConfig

class JobStatusResponse(BaseModel):
    status: str            # "pending" | "running" | "succeeded" | "failed"
    job_id: str            # embed job_id for propagation
    elapsed_s: float = 0.0
    payload: dict = {}     # raw vendor payload (optional)
    error: Optional[str] = None

class VendorClient:
    def __init__(self, cfg: TransportConfig):
        self.cfg = cfg

    def upload(self, path: Path) -> str:
        # TODO: implement
        return "media_123"

    def start(self, media_id: str, params: dict | None = None) -> str:
        # TODO: implement
        return "job_abc"

    def job_status(self, job_id: str) -> JobStatusResponse:
        # TODO: implement
        return JobStatusResponse(status="running", job_id=job_id)

    def poll_until_done(self, job_id: str, deadline_s: float | None = None) -> JobStatusResponse:
        import time
        backoff = 0.5
        start = time.time()
        while True:
            jsr = self.job_status(job_id)
            if jsr.status in {"succeeded", "failed"}:  # vendor may also return "timeout"
                return jsr
            if deadline_s and (time.time() - start) > deadline_s:
                return JobStatusResponse(status="timeout", job_id=job_id, elapsed_s=time.time()-start)
            time.sleep(backoff)
            backoff = min(backoff * 1.6, self.cfg.backoff_max_s)
```

---

## 6. Adapter (transport → domain) Boilerplate

```python
# mapping/adapter.py
from __future__ import annotations
from typing import Optional
from ..domain.models import Envelope, Provenance
from ..transport.client import JobStatusResponse

class VendorAdapter:
    def __init__(self, backend_name: str = "vendor", model_name: Optional[str] = None):
        self.backend = backend_name
        self.model = model_name

    def to_envelope(self, jsr: JobStatusResponse) -> Envelope:
        prov = Provenance(
            backend=self.backend,
            model=self.model,
            job_id=jsr.job_id,
            params={},
        )
        status = jsr.status
        if status == "succeeded":
            return Envelope(status="succeeded", result=self._map_result(jsr), provenance=prov)
        if status == "failed":
            return Envelope(status="failed", error=jsr.error or "vendor failed", provenance=prov)
        if status == "timeout":
            return Envelope(status="timeout", diagnostics={"elapsed_s": jsr.elapsed_s}, provenance=prov)
        # pending/running
        return Envelope(status=status, diagnostics={"elapsed_s": jsr.elapsed_s}, provenance=prov)

    def _map_result(self, jsr: JobStatusResponse):
        # TODO: convert payload → domain result for your feature
        return jsr.payload
```

---

## 7. Concrete Service (composition) Boilerplate

```python
# service/vendor_service.py
from __future__ import annotations
from pathlib import Path
from typing import Optional
from ..config.policy import DomainPolicy, TransportConfig
from ..domain.models import Envelope
from ..domain.service import FeatureParams, FeatureService
from ..mapping.adapter import VendorAdapter
from ..transport.client import VendorClient

class VendorService(FeatureService):
    def __init__(self, transport: TransportConfig, *, policy: DomainPolicy | None = None):
        self.client = VendorClient(transport)
        self.adapter = VendorAdapter(backend_name="vendor")
        self.policy = policy or DomainPolicy()

    def start(self, input_path: Path, params: Optional[FeatureParams] = None) -> str:
        media_id = self.client.upload(input_path)
        return self.client.start(media_id, params.dict() if params else None)

    def get_response(self, job_id: str, *, wait_until_complete: bool = False) -> Envelope:
        if wait_until_complete or self.policy.completion_mode == "wait":
            jsr = self.client.poll_until_done(job_id, deadline_s=self.policy.deadline_s)
        else:
            jsr = self.client.job_status(job_id)
        return self.adapter.to_envelope(jsr)

    def generate(self, input_path: Path, params: Optional[FeatureParams] = None, *, wait_until_complete: bool = True) -> Envelope:
        job_id = self.start(input_path, params)
        return self.get_response(job_id, wait_until_complete=wait_until_complete)
```

---

## 8. Processor (thin orchestrator) & Ports

```python
# app/processor.py
from __future__ import annotations
from pathlib import Path
from typing import Optional, Protocol
from ..domain.models import Envelope

class ResultWriter(Protocol):
    def write(self, path: Path, response: Envelope) -> Path: ...

class FileResultWriter:
    def write(self, path: Path, response: Envelope) -> Path:
        from tnh_scholar.utils.file_utils import ensure_directory_exists, write_str_to_file
        ensure_directory_exists(path.parent)
        write_str_to_file(path, response.model_dump_json(indent=2), overwrite=True)
        return path

class FeatureProcessor:
    def __init__(self, service, output_path: Optional[Path] = None, writer: Optional[ResultWriter] = None):
        self.service = service
        self.output_path = output_path
        self.writer = writer or FileResultWriter()
        self._last: Optional[Envelope] = None
        self._last_job_id: Optional[str] = None

    def start(self, input_path: Path, params) -> str:
        job_id = self.service.start(input_path, params)
        self._last_job_id = job_id
        return job_id

    def get_response(self, job_id: Optional[str] = None, *, wait_until_complete: bool = False) -> Envelope:
        jid = job_id or self._last_job_id
        if not jid:
            raise ValueError("No job_id available. Call start() first or pass a job_id.")
        self._last = self.service.get_response(jid, wait_until_complete=wait_until_complete)
        return self._last

    def generate(self, input_path: Path, params, *, wait_until_complete: bool = True) -> Envelope:
        self._last = self.service.generate(input_path, params, wait_until_complete=wait_until_complete)
        return self._last

    def export(self, path: Path | None = None, response: Envelope | None = None) -> Path:
        resp = response or self._last
        if resp is None:
            raise ValueError("No response to export. Run generate() or get_response() first.")
        out = path or self.output_path
        if out is None:
            raise ValueError("No output path provided.")
        return self.writer.write(out, resp)
```

---

## 9. Diagnostics & Observability (curated)

- **Structured logs** with `job_id`, input hash, request_ids.
- **Metrics**: latency p50/p95, error rate by class, retries, timeouts, queue vs run time.
- **Tracing**: spans for upload/start/poll; propagate correlation IDs.
- **Provenance**: always fill backend, model, params, timestamps; include `schema_version` for evolution.
- **Diagnostics**: keep concise and purposeful (e.g., `{ "elapsed_s": 12.4, "retries": 1 }`).

---

## 10. Error Model & Resilience

- Map remote errors to `failed` envelopes (no catch‑all handlers in services).
- **Retries**: idempotent calls only; exponential backoff + jitter; classify retryable errors.
- **Timeouts & Deadlines**: enforce at client (read/connect) and at poller (absolute deadline).
- **Rate limiting**: client‑side token bucket; honor `Retry‑After`.
- **Circuit breaker**: open after N consecutive failures; half‑open probes.
- **Idempotency keys**: for start endpoints when supported.

---

## 11. Factory Helpers & Defaults

- `TransportConfig.from_env()` to bootstrap quickly.
- `ServiceFactory.from_env()` (small helper) to wire a default client+adapter.
- Allow dict inputs in notebooks/CLI and coerce to Pydantic via `ThingParams(**d)`.
- Prefer immutable Configs (frozen models) and explicit per‑call Params.

---

## 12. Checklists

### Design Kickoff

- [ ] Identify domain Result shape and invariants.
- [ ] Define Response envelope (status, error, diagnostics, provenance).
- [ ] Split knobs into Config vs Params vs Policy.
- [ ] Decide success criteria, partials policy, and deadlines.

### Implementation

- [ ] Client happy path (upload/start/status) with timeouts.
- [ ] Adapter success mapping with golden fixture.
- [ ] Service `generate()` end‑to‑end (no retries yet).
- [ ] Processor + ResultWriter wired.

### Hardening

- [ ] Retries/backoff/jitter; classify retryable errors.
- [ ] Poller deadlines; snapshot vs wait flows.
- [ ] Observability: logs, metrics, traces, provenance.
- [ ] Contract tests against real API (skipped on PR, nightly allowed).

### Pre‑merge

- [ ] Unit tests: success, failure, timeout, retries, mapping.
- [ ] Docs updated (this blueprint + ADR if needed).

---

## 13. Anti‑patterns to Avoid

- **Parameter soup**: 12 kwargs on every call → use Params/Config objects.
- **Fat client returns domain** (if you plan reuse elsewhere) → prefer Service + Adapter.
- **Orchestrators doing HTTP** → violates separation; move to Client.
- **Mutable Config** shared across threads → make Configs immutable and thread‑safe.
- **Diagnostics dumping** raw payloads → curate; log correlation IDs instead.

---

## 14. Example: Applying to Diarization (thumbnail)

```python
# Diarization flavors
class DiarizationParams(FeatureParams):
    language: str | None = None
    model_hint: str | None = None

class DiarizationResult(BaseModel):
    segments: list[dict]  # speaker, t0, t1 (use a typed model in real code)

class DiarizationAdapter(VendorAdapter):
    def _map_result(self, jsr: JobStatusResponse) -> DiarizationResult:
        # convert vendor payload → segments
        return DiarizationResult(segments=jsr.payload.get("segments", []))
```

---

## 15. Evolution & Versioning

- Version the envelope (`schema_version`) and keep changes additive where possible.
- Be adapter‑tolerant to unknown transport fields.
- For breaking API shifts, add a new adapter/service and migrate gradually.

---

## 16. Glossary

- **Envelope**: response wrapper containing status, diagnostics, provenance, and optional result.
- **Policy**: opinionated settings that change behavior but not capability (e.g., wait vs snapshot).
- **Provenance**: metadata about how/when/with what the result was produced.
- **Anti‑corruption layer**: the adapter that converts vendor shapes to our domain shapes.

---

## 17. Appendix: File/Module Scaffold (cookie‑ready)

```text
<feature>/
  config/
    policy.py
  domain/
    models.py
    service.py
  transport/
    client.py
  mapping/
    adapter.py
  service/
    vendor_service.py
  app/
    processor.py
```

> Copy the stubs in this blueprint into the scaffold to start a new feature quickly.

---

## 18. Policy Evolution Strategy (robust & explicit)

*A potential strategy for evaluation.*

**Why this matters:** policy is where we encode TNH Scholar’s domain choices. These choices evolve as we learn. Make evolution safe, explicit, and observable.

### Principles

1. **Policy ≠ Config:** policies affect semantics; configs describe environment. Keep types separate.
2. **Additive first:** prefer adding new policy fields with sensible defaults over changing semantics of existing ones.
3. **Version the policy surface:** include `policy_version` in provenance (and optionally on the policy object itself).
4. **Document intent:** every policy field gets a one‑line rationale in code docstrings.
5. **Record used policy:** echo effective policy into `provenance.policy` on every response.

### Versioning

- Add `policy_version: str = "1.0"` to the policy model.
- Bump minor (`1.1`) for additive fields; bump major (`2.0`) for behavior changes.
- Store the version in `provenance.params["policy_version"]`.

### Migration patterns

1. **Expand → Contract**
   - Ship new policy fields with defaults that preserve old behavior.
   - Gather metrics; then flip defaults in a major version.
2. **Feature flags**
   - Use boolean or enum policy switches for new behaviors (e.g., `overlap_mode = "ignore|merge|separate"`).
3. **Policy profiles**
   - Provide named presets (e.g., `"dharma_talks"`, `"interviews"`) that resolve to concrete policy objects.
4. **Deprecation path**
   - Mark fields as deprecated in docstrings; log deprecation warnings in service when used; remove only after a major bump.

### Testing & governance

- **Golden tests** for policy variants: for each profile, snapshot the envelope shape.
- **Contract tests** to verify provenance always includes the policy version and effective values.
- **Review checklist** for policy PRs: rationale, defaults, migration notes, docstrings, provenance echo.

---

## 19. Interface Modalities & Integration Patterns (beyond polling APIs)

Design for a range of service shapes. Choose the smallest that fits; keep the envelope consistent.

### 19.1 Synchronous request/response (local or remote)

**When to use:** small/fast tasks; local libraries; remote endpoints with low latency.

- **Contract:** `run(params) -> Envelope` (no `start()`/`get_response()`).
- **Failure model:** exceptions for programmer errors; `failed` envelope for domain/remote errors.
- **Examples:** local Whisper inference; lightweight text cleaners.

### 19.2 Asynchronous jobs with polling

**When to use:** long‑running tasks without push callbacks.

- **Contract:** `start() -> job_id`, `get_response(job_id, wait|snapshot) -> Envelope`.
- **Failure model:** timeouts → `timeout` envelope (optionally partials); network errors retried.
- **Notes:** your existing diarization flow fits here.

### 19.3 Asynchronous jobs with webhooks/callbacks

**When to use:** vendor can push results; you control an HTTP endpoint.

- **Contract:** `start(callback_url) -> job_id`; callback sends transport payload; adapter maps to envelope.
- **Failure model:** at‑least‑once delivery; verify signatures; be idempotent.
- **Skeleton:**

```python
# app/webhooks.py
from fastapi import FastAPI, Request, HTTPException
app = FastAPI()

@app.post("/callbacks/vendor")
async def vendor_callback(req: Request):
    sig = req.headers.get("X-Vendor-Signature")
    body = await req.json()
    if not verify(sig, body):
        raise HTTPException(status_code=401)
    jsr = JobStatusResponse.model_validate({**body, "job_id": body.get("job_id")})
    env = adapter.to_envelope(jsr)
    save(env)  # persist; notify UI
    return {"ok": True}
```

### 19.4 Streaming (server‑sent events / WebSocket / gRPC)

**When to use:** incremental results (tokens, segments, progress).

- **Contract:** open stream → receive `Envelope` deltas or `Progress` events; final `Envelope` closes stream.
- **Failure model:** reconnect with resume tokens; dedupe by `event_id`.
- **Notes:** wrap stream events into mini‑envelopes to keep a consistent shape.

### 19.5 Message‑queue / Pub‑Sub integration

**When to use:** decouple producers/consumers; batch pipelines; fan‑out/fan‑in.

- **Contract:** publish `Params` + correlation IDs; consumers emit `Envelope`s on a result topic.
- **Failure model:** retries with DLQ; ensure idempotency via keys.

### 19.6 Batch pipelines (orchestration)

**When to use:** multi‑stage processing: diarize → chunk → transcribe → summarize.

- **Contract:** each stage returns an `Envelope`; orchestrator composes; pass along `provenance` and `policy`.
- **Failure model:** saga‑style compensation/skip policies; partial results acceptable per policy.

### 19.7 Pure data processors (no transport)

**When to use:** deterministic local transforms.

- **Contract:** `run(params) -> Envelope` or just `Result` + exceptions; envelopes still helpful for observability consistency.

### 19.8 Decision aid: which modality?

1. **Is the task fast (< 2s)?** Use synchronous.
2. **Long‑running and vendor can’t call back?** Async + polling.
3. **Vendor supports webhooks and you can host an endpoint?** Async + webhook.
4. **You need incremental UX?** Streaming.
5. **You need decoupling/scale?** MQ / Pub‑Sub.
6. **It’s a local library?** Synchronous or streaming.

---

## 20. Templates for other modalities

### 20.1 Streaming client loop (sketch)

```python
async def consume_stream(uri: str):
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"auth": token, "params": {...}}))
        async for msg in ws:
            evt = json.loads(msg)
            env = to_envelope(evt)  # mini‑envelopes or progress events
            handle(env)
```

### 20.2 MQ consumer (sketch)

```python
@mq.consume("transcribe.jobs")
def worker(msg):
    params = FeatureParams.model_validate(msg["params"])  # typed
    env = service.generate(Path(msg["input"]), params)
    mq.publish("transcribe.results", env.model_dump())
```

### 20.3 Webhook verification helper (sketch)

```python
import hmac, hashlib

def verify(signature: str, body: dict) -> bool:
    mac = hmac.new(SECRET, json.dumps(body).encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, mac)
```

---

## 21. Provenance integration tips

- Always record policy and policy version in `provenance.params`.
- Add `system_version` (git SHA/tag) for reproducibility.
- Store upstream IDs (job_id/request_id) and correlation IDs for cross‑system tracing.
- When combining stages, **aggregate provenance**: keep a list of stage‑level blocks.

---

## 22. Closing notes

This blueprint is **modality‑agnostic** and **policy‑forward**. Use the smallest viable integration pattern, keep envelopes consistent, and let policy express TNH Scholar’s domain decisions as they evolve. Persist provenance and you will be able to debug, reproduce, and explain results months or years later.