---
title: "ADR-A14.1: Registry Staleness Detection and User Warnings"
description: "Implements staleness detection for OpenAI pricing data with configurable warnings and CLI tooling"
type: "implementation-guide"
owner: "aaronksolomon"
author: "Aaron Solomon, Anthropic Claude Sonnet 4.5"
status: implemented
created: "2026-01-01"
parent_adr: "/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md"
---
# ADR-A14.1: Registry Staleness Detection and User Warnings

Extends ADR-A14 with robust staleness detection mechanisms to warn users when registry pricing data becomes outdated, preventing cost estimation errors and billing surprises.

- **Filename**: `adr-a14.1-registry-staleness-detection.md`
- **Heading**: `# ADR-A14.1: Registry Staleness Detection and User Warnings`
- **Status**: wip
- **Date**: 2026-01-01
- **Authors**: Aaron Solomon, Anthropic Claude Sonnet 4.5
- **Owner**: aaronksolomon
- **Parent ADR**: [ADR-A14: File-Based Registry System](/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md)

---

## Context

### Current State

As of 2026-01-01, the registry system (ADR-A14) is implemented with:

- ✅ Multi-tier pricing support (batch, flex, standard, priority)
- ✅ Manual pricing updates from OpenAI's pricing page
- ✅ `last_updated` timestamp in provider registry files
- ❌ **No staleness detection mechanism**
- ❌ **No user warnings for outdated data**
- ❌ **No CLI tooling for registry maintenance**

### Problem Statement

**OpenAI pricing changes frequently** (historical evidence: GPT-4o pricing changed 3x in 2024). Without staleness detection:

1. **Cost Estimation Drift**: Users unknowingly use outdated pricing, leading to budget overruns
2. **Batch Tier Adoption Blocker**: Users can't confidently switch to batch tier without current pricing
3. **Silent Data Decay**: Registry becomes stale over time with no visibility
4. **Manual Tracking Burden**: Maintainers must manually remember to check pricing updates

### ADR-A14 Original Specification

ADR-A14 Phase 3 (lines 883-961) specified:

```python
# scripts/update_registry.py --check-staleness
# Exit codes: 0 (OK), 1 (stale >90 days), 2 (validation error)
```

However, **no runtime detection mechanism** was specified, only a CLI tool.

### User Requirements

From project requirements and batch pricing adoption:

1. **Transparent Warnings**: Users must be informed when pricing may be inaccurate
2. **Configurable Thresholds**: Different projects have different staleness tolerances
3. **Non-Blocking**: Warnings shouldn't prevent application startup
4. **CI Integration**: Automated staleness checks in GitHub workflows
5. **Override Capability**: Users can silence warnings if intentionally using old data

---

## Decision

### Staleness Detection Architecture

Implement a **minimal staleness detection system** appropriate for rapid prototype phase:

1. **Runtime Warning System** (Default Enabled, Minimal Config)
2. **Future Enhancements** (Deferred to Post-Prototype)

### Runtime Warning System (V1 - Minimal)

**Location**: `src/tnh_scholar/gen_ai_service/config/registry.py`

**Behavior**:

- On first registry load, check `last_updated` timestamp
- If age > threshold, emit simple warning via logger
- Non-blocking: application continues normally
- **No per-session deduplication** (keeps implementation simple)

**Canonical source**: Use `last_updated` from the provider registry file (`providers/<provider>.jsonc`); ignore `.registry-metadata.json` for staleness checks.

**Configuration** (in `GenAISettings`, per ADR-CF01):

```python
# src/tnh_scholar/gen_ai_service/config/settings.py

class GenAISettings(BaseSettings):
    """Application-level settings."""

    # Registry staleness detection (minimal)
    registry_staleness_warn: bool = Field(
        default=True,
        description="Warn when registry pricing is stale"
    )

    registry_staleness_threshold_days: int = Field(
        default=90,
        ge=0,
        description="Warn if registry older than N days (0 = disable)"
    )
```

**Implementation**:

```python
# src/tnh_scholar/gen_ai_service/config/registry.py

class RegistryLoader:
    """Loads and caches provider registries from JSONC files."""

    def __init__(self, ...):
        self._settings = GenAISettings()  # Access user settings

    def get_provider(self, provider: str) -> ProviderRegistry:
        if cached := self._cache.get(provider):
            return cached

        registry = self._load_provider(provider)
        self._check_staleness(provider, registry)  # NEW: Check staleness
        self._cache.set(provider, registry)
        return registry

    def _check_staleness(self, provider: str, registry: ProviderRegistry) -> None:
        """Check registry staleness and warn user if configured.

        Simple implementation - warns every time, no session tracking.
        May result in duplicate warnings but keeps code simple for prototype.
        """
        # Skip if warnings disabled
        if not self._settings.registry_staleness_warn:
            return

        threshold = self._settings.registry_staleness_threshold_days
        if threshold == 0:
            return  # Disabled

        # Calculate age from provider registry file
        age_days = (date.today() - registry.last_updated).days

        if age_days > threshold:
            logger = logging.getLogger(__name__)
            message = (
                f"Registry pricing for '{provider}' is {age_days} days old "
                f"(threshold: {threshold} days). Pricing may be inaccurate. "
                f"Update recommended: {registry.source_url or 'manual update required'}"
            )
            logger.warning(message)
```

**User Experience**:

```python
# User code - automatic warning on registry load
from tnh_scholar.gen_ai_service.config.registry import get_model_info

# First call triggers warning if stale
model = get_model_info("openai", "gpt-4o")
# WARNING: Registry pricing for 'openai' is 120 days old (threshold: 90 days).
#          Pricing may be inaccurate. Update recommended: https://openai.com/api/pricing/

# Note: May warn multiple times per session (no deduplication in V1)
```

**Configuration Override**:

```bash
# Disable warnings via environment
export REGISTRY_STALENESS_WARN=false

# Adjust threshold
export REGISTRY_STALENESS_THRESHOLD_DAYS=30  # More aggressive

**Env naming note**: These environment variables map directly to `GenAISettings` fields
(`registry_staleness_warn`, `registry_staleness_threshold_days`) and are not prefixed
with `TNH_` to align with existing GenAI settings conventions.
```

---

## Future Enhancements (Post-Prototype)

The following features are intentionally deferred to keep the prototype implementation simple:

### Per-Session Warning Deduplication

**Motivation**: Prevent duplicate warnings when registry is accessed multiple times

**Implementation**: Track warned providers in `RegistryLoader` instance state

**Deferred because**:

- Adds state management complexity
- Singleton pattern makes testing harder
- Warnings are cheap (just logging)
- Prototype phase: simplicity > polish

---

### Rich CLI Maintenance Tool

**Motivation**: Advanced CLI with Rich formatting, multiple commands, table output

**Example commands**:

- `--check-staleness` with formatted tables
- `--validate` with detailed output
- `--info` with pricing display

**Deferred because**:

- Adds dependency on Rich library
- Complex formatting not needed for basic checks
- Manual registry updates are rare (quarterly at most)
- Can use simple Python script or direct file inspection

**Simple alternative for V1**: Basic Python script that prints plain text

---

### GitHub Workflow Automation

**Motivation**: Automated weekly checks, GitHub issue creation, smart deduplication

**Features**:

- Scheduled cron runs
- Auto-created issues with update instructions
- Issue deduplication (comment on existing vs. create new)

**Deferred because**:

- Significant CI/CD complexity for prototype phase
- Manual updates are manageable at current scale (single provider)
- GitHub Actions workflow can be added when needed
- Runtime warnings provide sufficient visibility for now

**Migration path**: When needed, resurrect the full workflow spec from this ADR's earlier versions

---

### Configurable Log Severity

**Motivation**: Allow users to set WARNING/INFO/ERROR/DEBUG levels

**Deferred because**:

- Additional configuration surface area
- Standard WARNING level works for all cases in prototype
- Adds minimal value (users can filter logs externally)
- Simplifies settings validation

**Simple alternative for V1**: Always use `WARNING` level

---

## Implementation Plan (Scaled Back)

### Phase 1: Minimal Runtime Warnings (1-2 days)

- [ ] Add basic staleness settings to `GenAISettings` (warn flag, threshold only)
- [ ] Implement simple `_check_staleness()` in `RegistryLoader` (no session tracking)
- [ ] Use standard `logger.warning()` (no structured logging extras)
- [ ] Unit tests for staleness detection logic with mocked dates
- [ ] Integration test confirming warnings appear

### Phase 2: Documentation (1 day)

- [ ] Document configuration options in user guide
- [ ] Add "Manual Registry Update" procedure to docs
- [ ] Update ADR-A14 as-built notes with reference to this addendum

---

## Configuration Matrix (V1 Simplified)

### Recommended Configurations

| Use Case            | `warn`  | `threshold` | Rationale                                             |
| ------------------- | ------- | ----------- | ----------------------------------------------------- |
| **Production**      | `true`  | `90`        | Default, balanced (quarterly updates)                 |
| **Development**     | `true`  | `30`        | More aggressive staleness detection                   |
| **Offline/Testing** | `false` | `0`         | Disable warnings entirely                             |
| **Batch-Heavy**     | `true`  | `14`        | Critical for cost optimization (bi-weekly checks)     |

### Environment Variables

```bash
# Production (default)
REGISTRY_STALENESS_WARN=true
REGISTRY_STALENESS_THRESHOLD_DAYS=90

# Batch-optimized project (more aggressive)
REGISTRY_STALENESS_WARN=true
REGISTRY_STALENESS_THRESHOLD_DAYS=14

# Testing environment (warnings off)
REGISTRY_STALENESS_WARN=false
```

---

## Consequences

### Positive

1. **Proactive Awareness**: Users notified of stale data before cost impact
2. **Configurable Behavior**: Different projects can set appropriate thresholds
3. **Non-Blocking**: Warnings don't break applications
4. **Batch Tier Confidence**: Users can trust pricing when adopting batch API
5. **Future Automation**: ADR leaves room for CI workflows and issue tracking later
6. **Future Logging Enhancements**: Structured logging can be added post-prototype

### Negative

1. **Additional Complexity**: More configuration surface area (minimal: 2 settings)
2. **Potential Warning Fatigue**: Users may see duplicate warnings (no session deduplication)
3. **False Positives**: Registry may be "stale" but pricing unchanged
4. **Dependency on Manual Updates**: Still requires human intervention

### Mitigations

- **Warning Fatigue**: Simple `REGISTRY_STALENESS_WARN=false` to disable; warnings only on registry load (not frequent)
- **False Positives**: 90-day threshold provides buffer for stable pricing
- **Manual Updates**: Acceptable for prototype phase; future ADR could explore automation

---

## Alternatives Considered

### Alternative 1: Hard Block on Stale Registry

**Approach**: Raise exception and refuse to load registry if too old.

**Pros**: Forces immediate action, prevents silent errors

**Cons**: Breaking change, blocks development/testing, too aggressive

**Rejected**: Too disruptive for development workflows

### Alternative 2: Automatic Background Updates

**Approach**: Auto-fetch pricing from OpenAI on staleness detection.

**Pros**: Fully automated, no manual work

**Cons**:

- OpenAI has no pricing API (confirmed in ADR-A14 research)
- Web scraping unreliable and against ToS
- Security risk (auto-executing untrusted data)
- Violates "human-editable" principle

**Rejected**: Not feasible without official API

### Alternative 3: External Service Integration

**Approach**: Subscribe to third-party pricing update service (e.g., LLMPrices.dev).

**Pros**: Automated, covers multiple providers

**Cons**:

- External dependency risk
- Subscription cost
- Data accuracy not guaranteed
- Privacy concerns (exposing usage patterns)

**Deferred**: Consider for ADR-A14.2 if services mature

---

## Open Questions

1. **Threshold Tuning**: Is 90 days the right default? Should it vary by provider?
2. **Pricing Change API**: Should we monitor OpenAI announcements for pricing changes?
3. **Historical Pricing**: Should we maintain a pricing history for cost analysis?
4. **Multi-Provider**: How do thresholds work when different providers update at different rates?
5. **User Notifications**: Should we support email/Slack notifications beyond logging?

---

## References

- [ADR-A14: File-Based Registry System](/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md)
- [OpenAI Pricing Page](https://openai.com/api/pricing/)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Rich Console Documentation](https://rich.readthedocs.io/en/stable/console.html)
- [Typer CLI Framework](https://typer.tiangolo.com/)

---

## As-Built Notes

*This section will be populated during implementation. Never edit the original Context/Decision/Consequences sections - always append addenda here.*
