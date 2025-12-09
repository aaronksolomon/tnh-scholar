---
title: "ADR-PP01: Rapid Prototype Versioning Policy"
description: "Establishes versioning policy for TNH Scholar during 0.x releases, allowing breaking changes in any release to enable fast iteration and architectural improvements."
owner: "TNH Scholar Architecture Working Group"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: accepted
created: "2025-12-06"
---
# ADR-PP01: Rapid Prototype Versioning Policy

Establish versioning policy for TNH Scholar during rapid prototype phase (0.x) that prioritizes architectural consistency and fast iteration over backward compatibility.

- **Status**: Accepted
- **Date**: 2025-12-06
- **Owner**: TNH Scholar Architecture Working Group
- **Authors**: Aaron Solomon, Claude Sonnet 4.5
- **Related**: [ADR-PT04](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md), [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md), [VERSIONING.md](/project/repo-root/versioning.md)

---

## Context

### Problem

TNH Scholar is in rapid prototype phase (0.x) where architectural patterns are still evolving. Recent work includes:
- Object-service architecture refactors ([ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md))
- Prompt system refactor ([ADR-PT04](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md))
- GenAI service improvements
- Transport layer isolations

**Challenge**: Standard semantic versioning (semver) creates pressure to maintain backward compatibility, slowing architectural improvements:
- Compatibility shims accumulate technical debt
- Dual API support increases maintenance burden
- Developer time spent on migration paths instead of core features
- Inconsistent codebase with old and new patterns coexisting

### Current State

- Version: 0.1.4 (alpha)
- Standard semver interpretation: "0.x is unstable, anything may change"
- In practice: Unclear expectations on when breaking changes are acceptable
- Result: Hesitation to make needed architectural improvements

### Use Case: ADR-PT04 Prompt System Refactor

The prompt system refactor requires:
- ✅ Remove `ai_text_processing/prompts.py` entirely
- ✅ Change imports: `tnh_scholar.ai_text_processing.prompts` → `tnh_scholar.prompt_system`
- ✅ Remove `TNH_PATTERN_DIR` environment variable
- ✅ Change CLI flags: `--pattern` → `--prompt`
- ✅ Refactor GenAI service adapter interfaces

**Question**: Can we ship this in 0.1.4 → 0.1.5 (patch), or must we wait for 0.2.0 (minor)?

Standard semver for 0.x says "maybe," but unclear. We need explicit policy.

---

## Decision

### Rapid Prototype Versioning for 0.x Releases

During **0.x releases only**, TNH Scholar adopts **rapid prototype versioning** with the following principles:

#### 1. Breaking Changes Acceptable in ANY 0.x Release

- **Minor bumps** (0.1.x → 0.2.0): MAY include breaking changes
- **Patch bumps** (0.1.3 → 0.1.4): MAY include breaking changes
- No distinction between patch and minor for breaking change policy

**Rationale**: During prototyping, architectural consistency matters more than stability. Delaying breaking changes to minor bumps creates artificial constraints.

#### 2. No Backward Compatibility Guarantees

- No compatibility shims maintained
- No dual API support
- Legacy code removed immediately when replaced
- Example: `TNH_PATTERN_DIR` removed entirely, no migration period

**Rationale**: Shims and dual systems create technical debt and slow iteration. Clean breaks keep codebase consistent.

#### 3. Force Refactors in Dependent Code

- When core systems change, ALL dependent modules MUST be updated in same PR/release
- No gradual migration strategies
- All code pushed forward to latest patterns

**Rationale**: Ensures entire codebase stays architecturally consistent. Prevents fragmentation.

#### 4. Clear Communication & Documentation

While not guaranteeing compatibility, we provide:
- Migration guides for major architectural changes (ADRs)
- Breaking changes documented in CHANGELOG
- Comprehensive test suites to validate changes
- ADRs explaining architectural decisions

**Rationale**: Developers need context even without compatibility guarantees.

### Version Numbering Scheme (0.x)

Use `MAJOR.MINOR.PATCH` notation with 0.x semantics:

- **MAJOR**: Stays at 0 during prototype phase
- **MINOR bump** (0.1.x → 0.2.0): Significant feature additions or major refactors (may break)
- **PATCH bump** (0.1.3 → 0.1.4): Bug fixes, small features, or refactors (may break)

**Key Difference from Semver**: Both PATCH and MINOR bumps can include breaking changes.

### Transition to Semver at 1.0.0

When releasing 1.0.0 (post-prototype):
- Adopt **strict semantic versioning**
- MAJOR = breaking changes only
- MINOR = new features, backward-compatible
- PATCH = bug fixes, backward-compatible
- Deprecation policy with migration periods

---

## Implementation

### Documentation Updates

Created/updated the following files:
1. ✅ [VERSIONING.md](/project/repo-root/versioning.md) - Comprehensive policy document (single source of truth)
2. ✅ [README.md](/project/repo-root/repo-readme.md) - Project Status section with versioning notice
3. ✅ [CONTRIBUTING.md](/project/repo-root/contributing-root.md) - New section "Versioning & Breaking Changes"
4. ✅ [release_checklist.md](/project/repo-root/release_checklist.md) - Breaking change documentation reminders
5. ✅ [contributing-prototype-phase.md](/development/contributing-prototype-phase.md) - Policy callout

See [implementation summary](/architecture/project-policies/versioning-policy-implementation-summary.md) for details.

### Communication Strategy

**For Users (pip install tnh-scholar):**
- Prominent notice in README
- CHANGELOG documents all breaking changes
- Pin to specific version if stability needed: `pip install tnh-scholar==0.1.4`

**For Contributors:**
- CONTRIBUTING.md sets expectations
- When making breaking changes: update dependents in same PR
- No need to maintain backward compatibility during 0.x

**For Release Managers:**
- release_checklist.md includes breaking change checks
- GitHub release notes highlight breaking changes

---

## Consequences

### Positive

- ✅ **Faster iteration**: Architectural improvements can be implemented immediately
- ✅ **Consistent codebase**: All code follows latest patterns, no legacy cruft
- ✅ **Simpler maintenance**: No compatibility shims or dual APIs
- ✅ **Clear expectations**: Developers know breaking changes are normal during 0.x
- ✅ **Better architecture**: Can refactor toward object-service compliance without hesitation

### Negative

- ❌ **User disruption**: Updates may break existing code
- ❌ **Migration burden**: Users must update code when upgrading
- ❌ **Perception risk**: May deter users seeking stability
- ❌ **Documentation overhead**: Each breaking change needs clear communication

### Mitigations

- Clear documentation of breaking changes in CHANGELOG
- Migration guides (ADRs) for major architectural changes
- Version pinning guidance for users needing stability
- Comprehensive test suites to validate changes
- Explicit communication: "0.x = rapid prototype, expect breaking changes"

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Users pin to old versions, miss improvements | Medium | Medium | Clear upgrade guides, compelling features |
| Breaking changes poorly documented | Low | High | release_checklist.md enforces documentation |
| Perception as "unstable project" | Medium | Medium | Explicit 0.x = prototype messaging |
| Contributors forget to update dependents | Low | Medium | PR reviews, CI tests catch breakage |

---

## Examples

### Acceptable in 0.1.4 → 0.1.5 (Patch Bump)

✅ Remove `ai_text_processing/prompts.py` entirely
✅ Change import paths
✅ Remove `TNH_PATTERN_DIR` environment variable
✅ Change CLI flags `--pattern` → `--prompt`
✅ Refactor GenAI service adapter interfaces

### Acceptable in 0.1.x → 0.2.0 (Minor Bump)

✅ All of the above PLUS:
✅ Major architecture refactor (e.g., prompt system → object-service)
✅ Complete rewrite of subsystems
✅ New CLI tools or major features

### NOT Acceptable (Never)

❌ Breaking changes without documentation
❌ Breaking changes without updating dependents
❌ Breaking changes without test updates

---

## Alternatives Considered

### Alternative 1: Strict Semver for 0.x

**Rejected**: Standard semver allows breaking changes in 0.x minors but discourages in patches. This still creates pressure to batch changes, slowing iteration.

### Alternative 2: Trunk-Based Development Without Releases

**Rejected**: Need versioned releases for PyPI distribution and user communication.

### Alternative 3: Maintain Compatibility Shims

**Rejected**: Creates technical debt and dual-system complexity. Violates rapid prototype principle.

### Alternative 4: Wait Until 1.0 for All Breaking Changes

**Rejected**: Would delay critical architectural improvements by months/years. Not viable for rapid prototyping.

---

## Success Metrics

### Short Term (0.x phase)

- ✅ Breaking changes documented in CHANGELOG (100%)
- ✅ Dependent code updated in same release (100%)
- ✅ No compatibility shims added
- ✅ Test suites pass after breaking changes (100%)

### Long Term (1.0 transition)

- Stable public API surface defined
- Comprehensive documentation
- Production usage validation
- >80% test coverage
- Security review complete

---

## Related Documentation

- [VERSIONING.md](/project/repo-root/versioning.md) - Complete versioning policy
- [ADR-PT04](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md) - Example breaking change (prompt system)
- [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md) - Architecture requiring breaking refactors
- [Implementation Summary](/architecture/project-policies/versioning-policy-implementation-summary.md) - Documentation updates

---

## Approval

- **Architecture Team**: Accepted 2025-12-06
- **Maintainers**: Accepted 2025-12-06
- **Implementation**: Complete (documentation updated)

---

## Appendix: FAQ

### Q: Why not follow standard semver during 0.x?

**A**: Standard semver says "0.x is for initial development, anything may change" but doesn't provide operational guidelines. We make expectations explicit:
- Force dependent refactors (no compatibility shims)
- Immediate deprecation and removal
- Breaking changes acceptable in patches, not just minors

### Q: When will 1.0 be released?

**A**: When core architecture is stable, public APIs are finalized, and the project is production-ready. No specific timeline. Follow [GitHub milestones](https://github.com/aaronksolomon/tnh-scholar/milestones).

### Q: How do I avoid breaking changes?

**A**: Pin to a specific version: `pip install tnh-scholar==0.1.4`. Review CHANGELOG before upgrading.

### Q: What if I'm building on top of TNH Scholar?

**A**: During 0.x, expect to update your code when upgrading. Consider:
- Pin to specific version until 1.0
- Subscribe to release notifications
- Review ADRs for architectural changes
- Contribute to design discussions

---

**Last Updated**: 2025-12-06
**Current Version**: 0.1.4
**Current Phase**: Rapid Prototype (0.x)
**Next Review**: Before 1.0.0 release
