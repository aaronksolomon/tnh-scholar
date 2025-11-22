---
title: "Object-Service Design Blueprint: Critical Gaps & Clarifications"
description: "Checklist of open design questions that must be resolved for the Object-Service blueprint to ship."
owner: ""
author: ""
status: processing
created: "2025-11-15"
---
# Object-Service Design Blueprint: Critical Gaps & Clarifications

Checklist of open design questions that must be resolved for the Object-Service blueprint to ship.

**Purpose:** Checklist of items needed to make the blueprint fully actionable for implementation  
**Status:** Work in Progress  
**Date:** 2025-10-24

---

## Priority 1: Critical Gaps (Must Address)

### 1. Complete Runnable Example

**Status:** ❌ Not Addressed

**What's Missing:**

- End-to-end working example showing all layers integrated
- Actual runnable file with imports, initialization, and execution
- Both sync (GenAI) and async (diarization) full implementations
- How to bootstrap the application from scratch

**Required Deliverable:**

- `examples/complete_genai_example.py` - Full working GenAI service
- `examples/complete_diarization_example.py` - Full working async service
- `examples/README.md` - How to run the examples

---

### 2. Dependency Management & Environment

**Status:** ❌ Not Addressed

**What's Missing:**

- No `pyproject.toml` or `requirements.txt` specification
- Which versions of libraries? (Pydantic v1 vs v2? OpenAI SDK version?)
- Python version requirements
- Development dependencies (pytest versions, type checkers)

**Required Deliverable:**

- `pyproject.toml` with all dependencies and versions
- Minimum Python version specified
- Dev dependencies section
- Optional dependencies per provider

**Questions to Resolve:**

- Use Poetry, pip-tools, or plain requirements.txt?
- Pydantic v2 only or support v1 compatibility?
- Pin exact versions or use ranges?

---

### 3. Configuration Loading Flow

**Status:** ❌ Not Addressed

**What's Missing:**

- How Settings cascade: env vars → .env → defaults
- Validation errors: what happens when API keys missing?
- Multiple environment support (dev/staging/prod)
- Secrets management (vault, AWS Secrets Manager?)

**Required Deliverable:**

- Complete Settings loading logic with error handling
- Example `.env.example` file
- Documentation on configuration precedence
- Error messages for misconfiguration

**Questions to Resolve:**

- Required vs optional API keys (fail fast or lazy validation)?
- Support for multiple .env files (.env.local, .env.production)?
- Config validation at startup or on first use?

---

### 4. Error Handling Implementation Details

**Status:** ❌ Not Addressed

**What's Missing:**

- Retry logic: exponential backoff with jitter concrete implementation
- Circuit breaker pattern for failing providers?
- Fallback strategies when primary provider fails?
- Error propagation through layers (when to catch, when to re-raise?)
- Logging of errors vs user-facing error messages

**Required Deliverable:**

- Complete retry decorator or class
- Circuit breaker implementation
- Error handling examples for each layer
- Error message guidelines (internal vs external)

**Questions to Resolve:**

- Use tenacity library or custom retry logic?
- Circuit breaker per-provider or per-endpoint?
- How many retries before giving up?
- Should we expose provider errors to users?

---

### 5. Async/Await Patterns

**Status:** ❌ Not Addressed

**What's Missing:**

- When to use `async def` vs regular `def`?
- How to structure async adapters vs sync adapters?
- Event loop management
- Mixing sync and async code (running sync code in async context)

**Required Deliverable:**

- Guidelines for async protocol design
- Example async adapter implementation
- Pattern for sync-to-async bridging
- Event loop best practices

**Questions to Resolve:**

- Support both sync and async variants of each protocol?
- Use asyncio.run() or manage loop explicitly?
- How to handle blocking SDK calls in async context?

---

### 6. Resource Management

**Status:** ❌ Not Addressed

**What's Missing:**

- Connection pooling for HTTP clients
- When to create/close clients (per-request vs singleton?)
- Resource limits (max concurrent requests)
- Memory management for large files/responses

**Required Deliverable:**

- Client lifecycle management pattern
- Connection pool configuration
- Resource limit examples
- Memory-efficient file handling

**Questions to Resolve:**

- Use context managers for all clients?
- Share connection pools across services?
- Max concurrent requests per provider?
- Streaming vs buffering for large responses?

---

## Priority 2: Important Clarifications (Should Address)

### 7. Logging Strategy

**Status:** ❌ Not Addressed

**What's Missing:**

- Structured logging format
- What to log at each layer (domain vs transport)
- PII handling in logs
- Log levels for different scenarios
- Correlation IDs for tracing requests

**Required Deliverable:**

- Logging configuration example
- Logger setup per module
- PII redaction utilities
- Correlation ID propagation pattern

**Questions to Resolve:**

- Use Python logging, structlog, or loguru?
- JSON logs in production?
- Log sampling for high-volume operations?

---

### 8. Testing Infrastructure

**Status:** ❌ Not Addressed

**What's Missing:**

- How to create test fixtures for each protocol
- Mock vs real API testing strategy
- VCR/cassette pattern for recording HTTP interactions
- How to test polling logic without waiting
- Coverage expectations

**Required Deliverable:**

- Base test fixtures for each protocol type
- Mock provider implementations
- Example VCR tests (if using)
- Fast polling tests (time mocking)
- Coverage target (80%? 90%?)

**Questions to Resolve:**

- Use pytest-vcr or responses library?
- Run integration tests in CI?
- Separate unit/integration test commands?

---

### 9. Type Checking & Validation

**Status:** ❌ Not Addressed

**What's Missing:**

- When to use `mypy --strict`?
- Runtime validation patterns with Pydantic
- Optional vs required fields strategy
- Custom validators examples

**Required Deliverable:**

- mypy configuration
- Type checking guidelines
- Pydantic validator examples
- Type stub handling for untyped libraries

**Questions to Resolve:**

- Require 100% type coverage?
- Use Pydantic v2 validators or v1 style?
- Type check tests as well?

---

### 10. Serialization & Persistence

**Status:** ❌ Not Addressed

**What's Missing:**

- How to serialize Envelopes for storage?
- JSON encoding of complex types (datetime, Path, etc.)
- Database schema if persisting results
- File format for storing provenance

**Required Deliverable:**

- Envelope serialization utilities
- JSON encoder for custom types
- Example persistence layer
- Schema migration strategy

**Questions to Resolve:**

- Store as JSON, pickle, or other format?
- Database or filesystem storage?
- Compress large payloads?
- Retention policy for old results?

---

### 11. Rate Limiting Implementation

**Status:** ❌ Not Addressed

**What's Missing:**

- Config has `rate_limit_rps` but no implementation
- Token bucket vs leaky bucket algorithm?
- Per-provider limits vs global limits
- Queue management when rate limited

**Required Deliverable:**

- Rate limiter implementation
- Configuration per provider
- Queue/backpressure handling
- Rate limit exceeded error handling

**Questions to Resolve:**

- Use existing library (aiolimiter, ratelimit) or custom?
- Client-side rate limiting only or server-enforced?
- How to handle burst traffic?

---

### 12. Timeout Handling

**Status:** ❌ Not Addressed

**What's Missing:**

- Connect timeout vs read timeout vs total timeout
- How timeouts propagate through layers
- Graceful degradation vs hard failure
- Deadline propagation in nested calls

**Required Deliverable:**

- Timeout configuration examples
- Deadline propagation pattern
- Timeout error handling
- Partial result handling on timeout

**Questions to Resolve:**

- Default timeout values per operation type?
- User-configurable timeouts?
- What happens to in-flight requests on timeout?

---

## Priority 3: Nice to Have (Consider Adding)

### 13. Performance Patterns

**Status:** ❌ Not Addressed

**What's Missing:**

- Caching strategies (where, when, invalidation)
- Batch request optimization
- Streaming response handling
- Memory-efficient processing of large files

**Required Deliverable:**

- Caching layer examples
- Batch processing utilities
- Streaming adapter pattern
- Large file handling guide

---

### 14. Security Considerations

**Status:** ❌ Not Addressed

**What's Missing:**

- API key rotation strategy
- Input sanitization
- Output validation (prevent injection)
- Rate limiting to prevent abuse

**Required Deliverable:**

- Security checklist
- Input validation examples
- API key rotation procedure
- Abuse prevention guidelines

---

### 15. Monitoring & Metrics

**Status:** ❌ Not Addressed

**What's Missing:**

- Which metrics to track (latency, cost, errors)
- Prometheus exposition format example
- Health check endpoints
- Alerting thresholds

**Required Deliverable:**

- Metrics collection layer
- Prometheus exporter example
- Health check implementation
- Alerting rule examples

---

### 16. Documentation Standards

**Status:** ❌ Not Addressed

**What's Missing:**

- Docstring format (Google, NumPy, or reStructuredText?)
- Type annotation requirements
- README structure for each module
- API documentation generation (Sphinx?)

**Required Deliverable:**

- Documentation style guide
- Example module documentation
- API doc generation setup
- Contribution guidelines

---

### 17. Development Workflow

**Status:** ❌ Not Addressed

**What's Missing:**

- How to run locally for development
- Hot reload setup
- Debug configuration
- Pre-commit hooks (formatting, linting)

**Required Deliverable:**

- Development setup guide
- IDE configuration examples
- Pre-commit hook configuration
- Debugging tips and tools

---

### 18. Deployment

**Status:** ❌ Not Addressed

**What's Missing:**

- Docker container structure
- Environment variable injection
- Health checks and readiness probes
- Scaling considerations

**Required Deliverable:**

- Dockerfile
- docker-compose.yml for local dev
- Kubernetes manifests (if applicable)
- Deployment checklist

---

### 19. Migration Patterns

**Status:** ❌ Not Addressed

**What's Missing:**

- How to handle schema changes
- Backward compatibility strategy
- Data migration scripts
- API versioning (if exposing HTTP API)

**Required Deliverable:**

- Migration guide
- Schema versioning strategy
- Backward compatibility testing
- Breaking change protocol

---

### 20. Protocol Extension Examples

**Status:** ❌ Not Addressed

**What's Missing:**

- How to add a new provider (step-by-step)
- How to add a new service following the pattern
- Common pitfalls and how to avoid them

**Required Deliverable:**

- Provider implementation guide
- Service implementation guide
- Troubleshooting guide
- Checklist for new implementations

---

## Specific Open Questions

### Mapper Pattern

- Should mappers be stateless functions or stateful classes?
- When to choose each approach?
- Should mappers handle validation or just transformation?

### Protocol vs ABC

- Concrete guidance on when structural typing isn't enough
- When to use ABC for enforcement vs Protocol for flexibility
- How to document Protocol requirements?

### Error Granularity

- Should `ProviderError` have subclasses per error type or per provider?
- How fine-grained should error classification be?
- Standard error codes across providers?

### Streaming Support

- How to handle streaming responses in the protocol?
- Sync vs async streaming
- Backpressure handling

### Testing Mocks

- Should mocks live in test files or reusable fixtures?
- Shared mock implementations across test suites?
- How to keep mocks in sync with real implementations?

### Policy Precedence

- When policies conflict, exact resolution algorithm?
- How to detect and warn about conflicts?
- Should policy conflicts be errors or warnings?

---

## Work Plan Template

For each item above, the completion checklist should include:

- [ ] Design decision documented
- [ ] Implementation completed
- [ ] Example code provided
- [ ] Tests written
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Merged to main branch

---

## Notes

- Items marked ❌ need to be addressed
- Items marked ✅ are complete
- Items marked ⚠️ are partially complete
- Priority 1 items should be completed before Priority 2
- Priority 2 items should be completed before Priority 3
