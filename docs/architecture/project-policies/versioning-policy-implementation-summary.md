---
title: "Versioning Policy Documentation Additions"
description: "Summary of documentation updates to clarify rapid prototype versioning policy"
status: complete
created: "2025-12-06"
---
# Versioning Policy Documentation Additions

This document summarizes the documentation updates made to clarify TNH Scholar's rapid prototype versioning policy across key developer-facing files.

## Background

[ADR-PP01](adr/adr-pp01-rapid-prototype-versioning.md) (Rapid Prototype Versioning Policy) establishes that breaking changes are acceptable in ANY 0.x release, including patch versions. This enables fast iteration and architectural improvements (e.g., [ADR-PT04](../prompt-system/adr/adr-pt04-prompt-system-refactor.md) prompt system refactor).

This deviates from typical semver expectations where 0.x patch bumps avoid breaking changes. To prevent confusion, we've documented this policy explicitly across all key entry points where developers encounter the project.

## Files Updated

### 1. [README.md](/README.md)

**Section**: Project Status

**Added**:

- Explicit "rapid prototype phase" designation
- Versioning notice callout box explaining breaking change policy
- Link to VERSIONING.md for full policy

**Impact**: First point of contact for all users and contributors

### 2. [CONTRIBUTING.md](/CONTRIBUTING.md)

**Section**: New section "Versioning & Breaking Changes" (§2)

**Added**:

- Clear statement that breaking changes are expected and acceptable
- Guidance for contributors: update dependents immediately
- Link to VERSIONING.md
- Renumbered subsequent sections (3-6)

**Impact**: Sets expectations for contributors making breaking changes

### 3. [VERSIONING.md](/VERSIONING.md) - NEW FILE

**Created**: Comprehensive versioning policy document

**Contents**:

- Rapid prototype phase (0.x) policy
  - Core principles (breaking changes acceptable, force refactors, immediate removal)
  - Why rapid prototype versioning (benefits over strict semver)
  - Version numbering scheme
  - Examples of acceptable breaking changes
  - User impact and communication
- Post-prototype phase (1.0+) policy
  - Transition to semantic versioning
  - Pre-1.0 checklist
- FAQ section
- Related documentation links

**Impact**: Canonical reference for versioning policy

### 4. [release_checklist.md](/release_checklist.md)

**Added**:

- Frontmatter update timestamp
- Note at top linking to VERSIONING.md
- Breaking changes reminder in CHANGELOG step
- New checklist item: "If breaking changes: update migration guides/ADRs"
- Organized into Pre-Release, Release, Post-Release sections
- Added: "Highlight breaking changes" in GitHub release notes

**Impact**: Ensures breaking changes are properly documented in releases

### 5. [docs/development/contributing-prototype-phase.md](/docs/development/contributing-prototype-phase.md)

**Section**: New section "Rapid Prototype Versioning Policy" (at top)

**Added**:

- IMPORTANT callout explaining breaking change policy
- Bullet points summarizing key principles
- Link to VERSIONING.md

**Impact**: Reinforces policy in developer-focused contributing guide

## Key Messages Across All Files

### Consistent Messaging

All updated files communicate:

1. **"Breaking changes acceptable in ANY 0.x release"** - including patches
2. **"No backward compatibility guarantees during 0.x"**
3. **"Force refactors in dependents"** - no dual API support
4. **"See VERSIONING.md for complete policy"** - single source of truth

### Rationale Provided

VERSIONING.md explains:

- **Why**: Fast iteration > compatibility during prototyping
- **What**: Specific examples of acceptable breaking changes
- **How**: Operational guidelines for contributors
- **When**: 1.0.0 transition to strict semver

## Coverage Analysis

### Where Policy Is Now Documented

| Location | Audience | Coverage |
|----------|----------|----------|
| README.md | All users | High-level notice |
| CONTRIBUTING.md | Contributors | Policy + guidelines |
| VERSIONING.md | All | Complete policy |
| release_checklist.md | Maintainers | Process integration |
| contributing-prototype-phase.md | Developers | Reinforcement |

### Entry Points Covered

✅ **pip install users**: README.md (first thing they read)
✅ **GitHub visitors**: README.md (rendered on repo home)
✅ **Contributors**: CONTRIBUTING.md + contributing-prototype-phase.md
✅ **Release managers**: release_checklist.md
✅ **Architects/designers**: VERSIONING.md (detailed rationale)

### Additional Locations Considered

**Not Updated** (but could add if needed):

- `DEV_SETUP.md` - Could add brief note, but less critical (focuses on environment setup)
- `docs/getting-started/*` - User-facing, less relevant (users already see README)
- `pyproject.toml` - No natural place for prose; classifiers already show "Alpha"
- GitHub issue/PR templates - Could add reminder, but contributors already see CONTRIBUTING.md

## Recommendations

### Immediate

✅ **Complete** - All critical entry points updated

### Future (Before 1.0)

1. **Add to DEV_SETUP.md** if developers report confusion
2. **Create GitHub PR template** with versioning policy reminder
3. **Add to release notes template** for consistent messaging
4. **Consider GitHub Actions bot** to flag PRs with breaking changes

### 1.0 Transition

When releasing 1.0.0:

- [ ] Update all references to "rapid prototype phase" → "stable release"
- [ ] Update VERSIONING.md to mark 0.x policy as historical
- [ ] Update README.md to remove versioning warning
- [ ] Add semver badge to README
- [ ] Update CONTRIBUTING.md to remove breaking change guidance

## Testing

### Verification Steps

To verify policy is discoverable:

1. **New user flow**: README → VERSIONING.md ✅
2. **Contributor flow**: CONTRIBUTING.md → VERSIONING.md ✅
3. **Release flow**: release_checklist.md → VERSIONING.md ✅
4. **GitHub browse**: Visible in root README ✅

### User Scenarios

| Scenario | Finds Policy? | Path |
|----------|---------------|------|
| Install from PyPI, check README | ✅ Yes | README.md § Project Status |
| Browse GitHub repo | ✅ Yes | README.md (rendered) |
| Want to contribute | ✅ Yes | CONTRIBUTING.md § 2 |
| Create PR with breaking change | ✅ Yes | CONTRIBUTING.md + review |
| Release new version | ✅ Yes | release_checklist.md note |
| Understand rationale | ✅ Yes | VERSIONING.md (linked everywhere) |

## Related Work

This documentation work directly supports:

- [ADR-PP01](adr/adr-pp01-rapid-prototype-versioning.md) - Rapid prototype versioning policy
- [ADR-PT04](../prompt-system/adr/adr-pt04-prompt-system-refactor.md) - Prompt system refactor with breaking changes
- [ADR-OS01](../object-service/adr/adr-os01-object-service-architecture-v3.md) - Object-service architecture (breaking refactors needed)
- Future rapid prototype refactors during 0.x phase

## Conclusion

The rapid prototype versioning policy is now:

- ✅ **Discoverable** at all key entry points
- ✅ **Comprehensive** with detailed rationale
- ✅ **Consistent** across all files
- ✅ **Actionable** with clear guidelines for contributors
- ✅ **Linked** to single source of truth (VERSIONING.md)

Developers encountering TNH Scholar will understand:

1. Breaking changes are expected during 0.x
2. Why this approach is taken (fast iteration)
3. How to handle breaking changes (force refactors)
4. Where to find complete policy (VERSIONING.md)

---

**Files Modified**: 5
**Files Created**: 2 (VERSIONING.md, this summary)
**Total Documentation Pages**: 7
