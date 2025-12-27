---
title: "ADR-A15: Thread Safety and Rate Limiting"
description: "Implements thread-safe GenAIService operations and provider-aware rate limiting for concurrent and batch processing scenarios."
owner: ""
author: ""
status: proposed
created: "2025-12-23"
---
# ADR-A15: Thread Safety and Rate Limiting

Implements thread-safe GenAIService operations and provider-aware rate limiting for concurrent and batch processing scenarios.

**Status:** Proposed
**Date:** 2025-12-23
**Related:** [ADR-A01: Object-Service GenAI](/architecture/gen-ai-service/adr/adr-a01-object-service-genai.md), [ADR-A09: V1 Simplified Implementation](/architecture/gen-ai-service/adr/adr-a09-v1-simplified.md), [ADR-A14: File-Based Registry System](/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md)
**Issue:** [#22](https://github.com/aaronksolomon/tnh-scholar/issues/22)

---

## Context

The current GenAIService implementation (V1) is not thread-safe and lacks rate limiting. This blocks critical production use cases:

1. **Concurrent/Parallel Processing**: Batch document processing, pipeline parallelization
2. **Rate Limit Compliance**: Avoiding API throttling and 429 errors in high-throughput scenarios
3. **Resource Efficiency**: Safe sharing of service instances across threads/workers

### Current Issues

**Thread Safety Gaps:**

1. **Shared Retry State** (`openai_client.py:35`)
   - Single `Retrying` instance stored in `self._retry_caller`
   - Mutated on each `generate()` call (lines 45-54)
   - Tenacity's `Retrying` is not designed for concurrent reuse
   - **Impact**: Concurrent calls can trample each other's retry state and backoff timings

2. **Unprotected Cache** (`prompt_system/transport/cache.py:24-53`)
   - `InMemoryCacheTransport` uses plain `dict` with TTL
   - No locking on read/write operations
   - **Impact**: Race conditions, cache corruption, unpredictable eviction

**Rate Limiting Gap:**

- No implementation despite architectural plan (design-strategy.md:104, ADR-A14)
- OpenAI enforces RPM (Requests Per Minute) and TPM (Tokens Per Minute) limits
- Limits vary by tier: Tier 1 ~500 RPM, Tier 2+ ~5000 RPM
- Without tracking, batch jobs risk cascading 429 errors and exponential backoff delays

### Performance Analysis

**Per-Instance Overhead** (tested):
- GenAIService instantiation: <1ms, ~few KB memory
- Dominated by network I/O (100-500ms per request)
- **Conclusion**: Per-instance pattern is viable for 20-100 concurrent calls

**Rate Limit Risk**:
- 20-30 concurrent calls: No risk even on Tier 1
- 100+ concurrent calls: Requires rate limiting on Tier 1 accounts
- Tier 2+ accounts: Rate limiting recommended for predictable performance

---

## Decision

Implement **thread-safe service operations** and **provider-aware rate limiting** in two phases:

### Phase 1: Thread Safety (Quick Win)

Enable safe concurrent usage through isolated retry state and locked cache access.

**Changes:**

1. **Per-Call Retry Objects** (`openai_client.py`)
   - Move `_create_retry_caller()` invocation from `__init__` to `generate()`
   - Remove `self._retry_caller` instance variable
   - Each request gets fresh retry state (no shared mutation)

2. **Thread-Safe Cache** (`prompt_system/transport/cache.py`)
   - Add `threading.Lock` to `InMemoryCacheTransport`
   - Wrap all dict operations (`get`, `set`, `invalidate`, `clear`) with lock
   - Preserve existing API (backward compatible)

3. **Documentation & Testing**
   - Add docstring warnings about concurrency patterns
   - Add integration test: concurrent `generate()` calls with shared instance
   - Document per-instance pattern as safe alternative

### Phase 2: Rate Limiting (Production Hardening)

Implement provider-aware rate limiting with configurable limits and token tracking.

**Architecture:**

```python
# gen_ai_service/infra/rate_limiter.py
class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter.

    Tracks both requests/minute (RPM) and tokens/minute (TPM)
    for OpenAI API compliance.
    """
    def __init__(
        self,
        requests_per_minute: int,
        tokens_per_minute: int,
        provider: str = "openai",
    ):
        self.rpm_capacity = requests_per_minute
        self.tpm_capacity = tokens_per_minute
        self.rpm_tokens = requests_per_minute
        self.tpm_tokens = tokens_per_minute
        self.rpm_refill_rate = requests_per_minute / 60.0
        self.tpm_refill_rate = tokens_per_minute / 60.0
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, estimated_tokens: int = 1) -> bool:
        """Attempt to acquire permits for request + estimated tokens.

        Returns:
            True if permits acquired, False if rate limit would be exceeded
        """
        with self._lock:
            self._refill()
            if self.rpm_tokens >= 1 and self.tpm_tokens >= estimated_tokens:
                self.rpm_tokens -= 1
                self.tpm_tokens -= estimated_tokens
                return True
            return False

    def _refill(self):
        """Refill token buckets based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.rpm_tokens = min(
            self.rpm_capacity,
            self.rpm_tokens + elapsed * self.rpm_refill_rate
        )
        self.tpm_tokens = min(
            self.tpm_capacity,
            self.tpm_tokens + elapsed * self.tpm_refill_rate
        )
        self.last_refill = now
```

**Integration:**

1. **Registry Configuration** (extends ADR-A14)
   - Add rate limit tiers to `runtime_assets/registries/providers/openai.jsonc`
   - Support tier detection via API or manual configuration

   ```jsonc
   {
     "rate_limits": {
       "tier_1": {"rpm": 500, "tpm": 200000},
       "tier_2": {"rpm": 5000, "tpm": 2000000}
     }
   }
   ```

2. **Service Integration** (`service.py`)
   ```python
   class GenAIService:
       def __init__(self, settings: GenAISettings | None = None):
           # ... existing init ...

           # Optional rate limiter (enabled via settings)
           if settings.enable_rate_limiting:
               tier_config = self._load_rate_limit_config(settings.rate_limit_tier)
               self.rate_limiter = TokenBucketRateLimiter(
                   requests_per_minute=tier_config.rpm,
                   tokens_per_minute=tier_config.tpm,
               )
           else:
               self.rate_limiter = None

       def generate(self, request: RenderRequest) -> CompletionEnvelope:
           # Pre-flight rate limit check
           if self.rate_limiter:
               estimated_tokens = self._estimate_tokens(request)
               while not self.rate_limiter.acquire(estimated_tokens):
                   # Blocking mode: wait and retry
                   # Alternative: raise RateLimitError for caller control
                   time.sleep(0.1)

           # ... existing generate logic ...
   ```

3. **Settings Configuration** (`config/settings.py`)
   ```python
   class GenAISettings(BaseSettings):
       # ... existing settings ...

       # Rate limiting (optional, disabled by default for V1 compatibility)
       enable_rate_limiting: bool = False
       rate_limit_tier: str = "tier_1"  # or "tier_2", "tier_3", etc.
       rate_limit_mode: Literal["blocking", "error"] = "blocking"
   ```

---

## Implementation Plan

### Phase 1: Thread Safety (1-2 hours)

1. **Fix Retry State** (30 min)
   - [ ] Modify `OpenAIClient.generate()` to create fresh retry caller
   - [ ] Remove `self._retry_caller` from `__init__`
   - [ ] Add docstring note about thread safety

2. **Thread-Safe Cache** (30 min)
   - [ ] Add `threading.Lock` to `InMemoryCacheTransport.__init__`
   - [ ] Wrap all cache operations with lock context
   - [ ] Verify no deadlock scenarios

3. **Testing** (30 min)
   - [ ] Add `tests/gen_ai_service/test_concurrency.py`
   - [ ] Test: 20 concurrent `generate()` calls with shared instance
   - [ ] Test: Cache race conditions (concurrent get/set on same key)
   - [ ] Test: Retry state isolation (concurrent calls don't interfere)

### Phase 2: Rate Limiting (2-4 hours)

1. **Rate Limiter Implementation** (1 hour)
   - [ ] Create `gen_ai_service/infra/rate_limiter.py`
   - [ ] Implement `TokenBucketRateLimiter` class
   - [ ] Add unit tests (token refill, acquire logic, thread safety)

2. **Registry Integration** (1 hour)
   - [ ] Extend `openai.jsonc` with rate limit tiers
   - [ ] Add tier detection logic or manual config
   - [ ] Update `RegistryLoader` (from ADR-A14)

3. **Service Integration** (1 hour)
   - [ ] Add settings for rate limiting (`enable_rate_limiting`, `rate_limit_tier`)
   - [ ] Integrate limiter into `GenAIService.generate()`
   - [ ] Add token estimation helper (or reuse existing token utils)

4. **Testing & Documentation** (1 hour)
   - [ ] Add rate limit integration tests
   - [ ] Test blocking vs error modes
   - [ ] Document rate limiting configuration in user guide
   - [ ] Update ADR with acceptance criteria

---

## Configuration Examples

**Basic Usage (Thread-Safe, No Rate Limiting):**
```python
# Safe for concurrent use after Phase 1
service = GenAIService()

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(service.generate, req) for req in requests]
    results = [f.result() for f in futures]
```

**With Rate Limiting (Phase 2):**
```python
# .env or settings
ENABLE_RATE_LIMITING=true
RATE_LIMIT_TIER=tier_1  # 500 RPM, 200K TPM

service = GenAIService()  # Auto-loads rate limiter
# Concurrent calls automatically throttled to stay within limits
```

**Per-Instance Pattern (Always Safe):**
```python
# Alternative: separate instance per worker (minimal overhead)
def worker(requests):
    service = GenAIService()  # <1ms overhead
    return [service.generate(req) for req in requests]

with ProcessPoolExecutor() as executor:
    results = executor.map(worker, batched_requests)
```

---

## Consequences

### Positive

- **Enables Concurrent Processing**: Batch pipelines can safely parallelize GenAI calls
- **Rate Limit Compliance**: Automatic throttling prevents API errors and costs
- **Backward Compatible**: Phase 1 changes are internal; existing code unaffected
- **Configurable**: Rate limiting opt-in preserves V1 simplicity
- **Well-Tested Pattern**: Token bucket is standard for rate limiting

### Negative

- **Blocking Overhead**: Default blocking mode adds latency when rate limited (alternative: error mode)
- **Memory**: Rate limiter adds ~100 bytes per service instance (negligible)
- **Complexity**: Additional configuration surface (mitigated by sensible defaults)

### Neutral

- **Per-Instance Pattern Remains Valid**: Still recommended for process-based parallelism
- **OpenAI SDK Retry**: Built-in retry logic still handles transient 429s

---

## Alternatives Considered

### 1. Document Per-Instance Pattern Only (No Code Changes)

**Pros**: Zero implementation cost, already safe
**Cons**:
- Doesn't address shared instance use cases (common in web services)
- Cache still has race conditions
- No rate limit protection

**Decision**: Rejected. Phase 1 fixes are trivial and eliminate subtle bugs.

### 2. External Rate Limiter (Redis, etc.)

**Pros**: Shared across processes, persistent
**Cons**:
- Requires infrastructure (Redis server)
- Adds latency (network round-trip)
- Overkill for single-process/thread scenarios

**Decision**: Deferred to V3. In-process limiter sufficient for V2.

### 3. Async/Await Concurrency Model

**Pros**: Better concurrency scaling, native Python async
**Cons**:
- Large refactor (entire service + OpenAI SDK integration)
- Breaking change for callers
- Not needed for current use cases (20-100 concurrent calls)

**Decision**: Deferred. Threading model adequate for current scale.

---

## Acceptance Criteria

### Phase 1 (Thread Safety)
- [ ] No shared mutable state in retry logic
- [ ] Cache operations are atomic and lock-protected
- [ ] Integration test passes: 20+ concurrent `generate()` calls
- [ ] Documentation warns about concurrency patterns
- [ ] No performance regression on single-threaded usage

### Phase 2 (Rate Limiting)
- [ ] `TokenBucketRateLimiter` correctly enforces RPM and TPM limits
- [ ] Rate limiter is thread-safe (tested under concurrent load)
- [ ] Integration with Settings and registry system (ADR-A14)
- [ ] Configurable modes: blocking vs error
- [ ] Documentation includes rate limiting setup and examples
- [ ] Graceful behavior when limits approached (no cascading failures)

---

## References

- [GenAI Service Design Strategy](/architecture/gen-ai-service/design/genai-service-design-strategy.md) - Original architecture
- [ADR-A01: Object-Service GenAI](/architecture/gen-ai-service/adr/adr-a01-object-service-genai.md) - Service pattern
- [ADR-A09: V1 Simplified Implementation](/architecture/gen-ai-service/adr/adr-a09-v1-simplified.md) - Current implementation
- [ADR-A14: File-Based Registry System](/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md) - Rate limit config source
- [OpenAI Rate Limits Documentation](https://platform.openai.com/docs/guides/rate-limits)
- [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)
- [GitHub Issue #22](https://github.com/aaronksolomon/tnh-scholar/issues/22)

---

## Appendix: Code Locations

**Files to Modify (Phase 1):**
- `src/tnh_scholar/gen_ai_service/providers/openai_client.py` - Retry state fix
- `src/tnh_scholar/prompt_system/transport/cache.py` - Thread-safe cache
- `src/tnh_scholar/gen_ai_service/service.py` - Docstrings
- `tests/gen_ai_service/test_concurrency.py` - New test file

**Files to Create (Phase 2):**
- `src/tnh_scholar/gen_ai_service/infra/rate_limiter.py` - Rate limiter implementation
- `runtime_assets/registries/providers/openai.jsonc` - Rate limit tiers (extend existing)

**Files to Update (Phase 2):**
- `src/tnh_scholar/gen_ai_service/config/settings.py` - Rate limit settings
- `src/tnh_scholar/gen_ai_service/service.py` - Rate limiter integration
- `docs/user-guide/configuration.md` - Rate limiting documentation
