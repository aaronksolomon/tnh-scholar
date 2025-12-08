---
title: "TNH Scholar Versioning Policy"
description: "Versioning policy for TNH Scholar during rapid prototype phase (0.x) and post-1.0 stable releases"
status: active
created: "2025-12-06"
---
# TNH Scholar Versioning Policy

TNH Scholar uses different versioning strategies depending on project maturity.

## Rapid Prototype Phase (0.x) - Current

**Status**: Active (currently v0.1.4)

### Core Principles

During the **0.x release series**, TNH Scholar follows **rapid prototype versioning** that prioritizes architectural consistency and fast iteration over backward compatibility:

1. **Breaking changes are acceptable in ANY 0.x release**
   - Minor version bumps (0.1.x → 0.2.0) MAY include breaking changes
   - Patch version bumps (0.1.3 → 0.1.4) MAY include breaking changes
   - No backward compatibility guarantees

2. **Force refactors in dependent code**
   - When core systems change (e.g., prompt system, GenAI service), all dependent modules MUST be updated
   - No dual API support or compatibility shims
   - Breaking changes push all code forward

3. **Immediate deprecation and removal**
   - Legacy APIs are removed immediately when replaced
   - No deprecation timeline during 0.x
   - Example: `TNH_PATTERN_DIR` → `TNH_PROMPT_DIR` (removed immediately, no migration period)

### Why Rapid Prototype Versioning?

**Problem with strict semver during prototyping:**
- Maintaining backward compatibility across major architectural changes creates technical debt
- Compatibility shims slow down iteration and create dual-system complexity
- Developer time spent on migration paths instead of core features

**Benefits of rapid prototype versioning:**
- Architectural improvements can be implemented immediately
- All code stays consistent with latest patterns
- Faster iteration cycles
- Clearer codebase without legacy cruft

### Version Number Scheme (0.x)

We use `MAJOR.MINOR.PATCH` notation, but with different semantics than semver:

- **0.MINOR.PATCH** format (e.g., 0.1.4, 0.2.0)
- **MINOR bump** (0.1.x → 0.2.0): Significant feature additions or major refactors (may break APIs)
- **PATCH bump** (0.1.3 → 0.1.4): Bug fixes, small features, or internal refactors (may break APIs)
- **MAJOR stays at 0** until stable release

**Key Difference from Semver**: PATCH bumps can include breaking changes during 0.x.

### What We Provide

Even though we don't guarantee compatibility, we provide:

1. **Migration guides** for major architectural changes (e.g., ADR-PT04)
2. **Clear documentation** of breaking changes in CHANGELOG
3. **Comprehensive test suites** to validate changes
4. **ADRs (Architecture Decision Records)** explaining major changes

### Examples

**Acceptable in 0.1.3 → 0.1.4 (patch):**
- ✅ Remove `ai_text_processing/prompts.py` entirely
- ✅ Change import paths from `tnh_scholar.ai_text_processing.prompts` to `tnh_scholar.prompt_system`
- ✅ Remove `TNH_PATTERN_DIR` environment variable support
- ✅ Change CLI flags from `--pattern` to `--prompt`
- ✅ Refactor GenAI service adapter interfaces

**Acceptable in 0.1.x → 0.2.0 (minor):**
- ✅ Major architecture refactor (e.g., prompt system → object-service compliance)
- ✅ Complete rewrite of subsystems
- ✅ New CLI tools or major feature additions
- ✅ All of the above PLUS large-scale changes

### User Impact & Communication

**For Users (pip install tnh-scholar):**
- Expect breaking changes in ANY 0.x update
- Pin to specific version if stability needed: `pip install tnh-scholar==0.1.4`
- Review CHANGELOG before upgrading
- Migration guides provided for major changes

**For Contributors:**
- When making breaking changes, update all dependent code in the same PR
- Document breaking changes in PR description and CHANGELOG
- Update tests to reflect new APIs
- No need to maintain backward compatibility during 0.x

## Post-Prototype Phase (1.0+) - Future

**Status**: Not yet active (target: TBD)

### Transition to Semantic Versioning

Once TNH Scholar reaches **1.0.0**, we will adopt **strict semantic versioning** (semver):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR** (1.x.x → 2.0.0): Breaking changes, backward-incompatible API changes
- **MINOR** (1.2.x → 1.3.0): New features, backward-compatible additions
- **PATCH** (1.2.3 → 1.2.4): Bug fixes, backward-compatible fixes only

### What Changes at 1.0?

1. **Stability commitment**: Public APIs will not break without major version bump
2. **Deprecation policy**: Deprecated features maintained for at least one major version
3. **Migration guides**: Clear upgrade paths for breaking changes
4. **LTS consideration**: Possible long-term support for major versions

### Pre-1.0 Checklist

Before releasing 1.0.0, we must:

- [ ] Complete core architecture stabilization (prompt system, GenAI service, transcription)
- [ ] Finalize public API surface
- [ ] Comprehensive test coverage (>80%)
- [ ] Complete documentation for all public APIs
- [ ] Security review
- [ ] Performance benchmarking
- [ ] Production usage validation

## Version History

| Version | Date | Type | Notes |
|---------|------|------|-------|
| 0.1.4 | 2025-01 | Patch | Test patches, build fixes |
| 0.1.3 | 2024-12 | Patch | Alpha release |
| ... | ... | ... | Earlier versions |

## Related Documentation

- [CHANGELOG.md](CHANGELOG.md) - Detailed version history
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [release_checklist.md](release_checklist.md) - Release process
- [ADR-PT04](docs/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md) - Example breaking change (prompt system refactor)

## FAQ

### Q: Why not follow standard semver during 0.x?

**A**: Standard semver allows breaking changes in 0.x minor bumps (0.1.0 → 0.2.0), but typically discourages them in patches (0.1.1 → 0.1.2). However, this still creates pressure to maintain compatibility, slowing down architectural improvements. Our explicit rapid prototype policy makes it clear that ANY 0.x change may break, allowing maximum iteration speed.

### Q: How is this different from "0.x means unstable" in semver?

**A**: Semver states "0.x is for initial development, anything may change." We make this explicit and add operational guidelines:
- Force dependent refactors (no compatibility shims)
- Immediate deprecation and removal
- Breaking changes acceptable in patches, not just minors

### Q: When will 1.0 be released?

**A**: When core architecture is stable, public APIs are finalized, and the project is production-ready. No specific timeline yet. Follow [GitHub milestones](https://github.com/aaronksolomon/tnh-scholar/milestones) for progress.

### Q: How do I avoid breaking changes?

**A**: Pin to a specific version: `pip install tnh-scholar==0.1.4`. Review CHANGELOG before upgrading.

### Q: What if I'm building on top of TNH Scholar?

**A**: During 0.x, expect to update your code when upgrading. Consider:
- Pin to specific version until 1.0
- Subscribe to release notifications
- Review ADRs for architectural changes
- Contribute to design discussions to influence stable APIs

---

**Last Updated**: 2025-12-06
**Current Version**: 0.1.4
**Current Phase**: Rapid Prototype (0.x)
