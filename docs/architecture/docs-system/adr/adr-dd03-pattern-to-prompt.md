---
title: "ADR-DD03: Pattern to Prompt Terminology Standardization"
description: "Standardizes documentation terminology from 'Pattern' to 'Prompt' to align with industry conventions and gen-ai-service refactoring."
owner: ""
author: "Claude Sonnet 4.5"
status: proposed
created: "2025-11-28"
---
# ADR-DD03: Pattern to Prompt Terminology Standardization

Standardizes TNH Scholar documentation to use "Prompt" terminology instead of "Pattern" to align with industry conventions, match the refactored gen-ai-service architecture (Prompt/PromptCatalog), and improve clarity for external stakeholders.

- **Filename**: `adr-dd03-pattern-prompt-terminology.md`
- **Heading**: `# ADR-DD03: Pattern to Prompt Terminology Standardization`
- **Status**: Proposed
- **Date**: 2025-11-28
- **Author**: Claude Sonnet 4.5
- **Owner**: Documentation Working Group

## Context

TNH Scholar historically used "Pattern" to refer to engineered prompts for AI text processing. This terminology emerged from early prototyping and emphasized the engineering pattern aspect of reusable prompt structures. However, several factors now warrant standardizing on "Prompt":

1. **Industry Alignment**: The broader AI/LLM community uses "Prompt", "Prompt Engineering", and "Prompt Catalog" as standard terminology. External stakeholders (Parallax Press, potential users) expect this language.

2. **gen-ai-service Refactoring**: The core `gen-ai-service` module has been refactored to use `Prompt` and `PromptCatalog` classes, aligning with common practice. Code now uses modern terminology.

3. **Mixed Terminology Confusion**: Current docs contain mixed usage:
   - Some files use "Pattern" (legacy)
   - Some use "PromptTemplate" (transitional)
   - Some use "Prompt/PromptTemplate" or "Pattern/PromptTemplate" (hedging)
   - This creates cognitive overhead and suggests inconsistency

4. **Deprecated Code Base**: Many modules still using "Pattern" terminology are already marked for deprecation/deletion (e.g., old tnh-fab implementations). Updating code is out of scope; focusing on docs provides immediate clarity.

5. **Documentation Reorganization Timing**: The docs-reorg branch (ADR-DD01, ADR-DD02) provides a natural checkpoint to standardize terminology before merging and starting new work (VS Code integration, gen-ai-service ADRs).

**Scope Note**: This ADR focuses on **documentation only**. Code refactoring is tracked separately and many legacy modules are scheduled for deletion.

## Decision

Standardize all documentation to use **"Prompt"** as the primary term, with the following guidelines:

### Primary Terminology

- **Use "Prompt"** when referring to engineered text inputs for AI models
- **Use "Prompt Catalog"** when referring to collections/repositories of prompts
- **Use "Prompt Engineering"** when discussing the practice of designing prompts
- **Use "PromptTemplate"** only in technical contexts where referring to the actual class/data structure name

### Handling Historical References

1. **High-Level User-Facing Docs** (index.md, getting-started/, user-guide/, README):
   - Replace "Pattern" → "Prompt" throughout
   - Add a one-time explanatory note in a Glossary or FAQ section:
     > **Historical Note**: Earlier versions of TNH Scholar referred to prompts as "Patterns" to emphasize their engineering pattern nature. This terminology has been updated to align with industry standards. References to "Pattern" in older documentation or archived materials should be read as "Prompt".

2. **Architecture/Design Docs** (architecture/, development/):
   - Update to "Prompt" in current/active ADRs and design documents
   - In historical/archived docs: Add a callout at the top noting the terminology shift, but preserve original text for historical accuracy
   - Example callout:
     ```markdown
     > **Note**: This document uses historical "Pattern" terminology. In current TNH Scholar documentation, "Pattern" has been replaced with "Prompt".
     ```

3. **CLI Documentation** (cli/):
   - Update to "Prompt" in all descriptions and examples
   - Note where CLI commands still use `pattern` flags/arguments (due to legacy code) with explanation:
     > **Note**: The `--pattern` flag is retained for backwards compatibility. It refers to prompts.

4. **Code Comments & Docstrings**: Out of scope for this ADR (tracked separately)

### Execution Plan

**Phase 1: High-Priority Docs** (Complete before docs-reorg merge)
- [ ] Update `docs/index.md` and add concise historical terminology note near top
- [ ] Update `README.md`
- [ ] Update `docs/getting-started/*.md`
- [ ] Update `docs/user-guide/patterns.md` → rename to `prompts.md`
- [ ] Update current ADRs in `docs/architecture/*/adr/` that are still relevant
- [ ] Rename `docs/architecture/prompt-system/` → `prompt-system/` and update nav

**Phase 2: Architecture & Design Docs** (Begin before merge, complete post-merge)
- [ ] Add historical callouts to archived/legacy design documents
- [ ] Update `docs/development/*.md` as they're actively edited
- [ ] Update architecture design documents with Pattern→Prompt terminology
- [ ] Update `docs/cli/*.md` CLI documentation (many commands deprecated/scheduled for removal)

**Phase 3: Search & Replace Validation** (Post-merge)
- [ ] Use `rg -i "pattern" docs/` to find remaining instances
- [ ] Manual review each occurrence for context-appropriateness
- [ ] Update navigation labels in `docs/nav.md` if needed

### Files Requiring Immediate Update (Phase 1)

Based on grep analysis, prioritize these files:

```
docs/index.md
docs/getting-started/quick-start.md
docs/getting-started/installation.md
docs/getting-started/configuration.md
docs/user-guide/patterns.md
docs/user-guide/overview.md
docs/user-guide/best-practices.md
docs/cli/overview.md
docs/cli/tnh-fab.md
docs/architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md (update references)
docs/architecture/docs-system/adr/adr-dd02-main-content-nav.md (update references)
```

## Consequences

### Positive

- **Clarity for External Stakeholders**: Parallax Press, new contributors, and users encounter familiar terminology
- **Alignment with Code**: Documentation matches the refactored gen-ai-service architecture
- **Reduced Cognitive Load**: Single consistent term across all current documentation
- **Professional Presentation**: Industry-standard language improves credibility
- **Future-Proof**: New ADRs (VS Code integration, gen-ai-service work) start with consistent terminology

### Negative

- **Historical Document Context Loss**: Archived docs may feel inconsistent unless callouts are added
- **One-Time Effort**: Requires systematic search-replace and manual review across ~65 files
- **CLI Flag Confusion**: Some CLI commands still use `--pattern` flags (legacy code); requires explanation in docs
- **Link/Navigation Updates**: May need to rename files/directories (e.g., `patterns.md` → `prompts.md`, `architecture/prompt-system/` → `architecture/prompt-system/`)

### Mitigation

- Add clear historical note in glossary/FAQ
- Use callouts in archived docs to preserve context
- Document CLI flag mismatches explicitly
- Phase the work: high-priority user-facing docs first, lower-priority archives later

## Alternatives Considered

### Alternative 1: Keep "Pattern" Throughout

**Rejected**: Misaligns with industry standards, confuses external stakeholders, and diverges from refactored code (gen-ai-service uses Prompt/PromptCatalog).

### Alternative 2: Use "PromptTemplate" as Primary Term

**Rejected**: "PromptTemplate" is more verbose and primarily a technical class name. "Prompt" is the user-facing concept. Use "PromptTemplate" only in technical contexts where referring to the class/structure.

### Alternative 3: Dual Terminology (Pattern/Prompt)

**Rejected**: Already tried this (Pattern/PromptTemplate hedging in docs). Creates confusion and suggests uncertainty. Pick one standard term.

### Alternative 4: Defer Until Code Refactoring Complete

**Rejected**: Deprecated code modules are scheduled for deletion, not refactoring. Documentation benefits are immediate and don't require code changes. Waiting blocks clarity improvements.

## Open Questions

### Resolved During ADR Review

1. **Directory Renaming**: Should `docs/architecture/prompt-system/` be renamed to `docs/architecture/prompt-system/`?
   - **Decision**: ✅ Yes, rename in Phase 1 (pre-merge) to ensure consistency

2. **User Guide File Renaming**: Should `docs/user-guide/patterns.md` be renamed to `prompts.md`?
   - **Decision**: ✅ Yes, rename in Phase 1 to match nav labels; update nav.md and internal links accordingly

3. **CLI Command Documentation**: How to handle CLI tools that still use `--pattern` flags?
   - **Decision**: ✅ Move to Phase 2/3 (post-merge) as many CLI tools are deprecated, scheduled for refactoring, or removal

4. **Glossary Location**: Where should the historical terminology note live?
   - **Decision**: ✅ Add brief, concise note to `docs/index.md` relatively high up (near top of document) to prevent confusion with legacy docs; defer full glossary to future work

### Remaining Open Questions

None - all decisions resolved during review.

## References

- [ADR-DD01: Documentation System Reorganization Strategy](/architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md) - References Pattern→PromptTemplate rename
- [ADR-DD02: Documentation Main Content and Navigation Strategy](/architecture/docs-system/adr/adr-dd02-main-content-nav.md)
- [gen-ai-service Refactoring ADRs](/architecture/gen-ai-service/adr/adr-a12-prompt-system-fingerprinting-v1.md) - Modern Prompt/PromptCatalog architecture
- TODO #9: Documentation Reorganization - Part 3b includes Pattern→PromptTemplate rename task
