---
title: "ADR-DD03: Phase 1 Execution Punch List"
description: "Pre-merge checklist to complete Pattern→Prompt terminology updates and related navigation changes."
owner: "Documentation Working Group"
author: "Codex (GPT-5)"
status: wip
created: "2025-11-28"
updated: "2025-12-11"
---
# ADR-DD03: Phase 1 Execution Punch List

Task list for completing the Pattern→Prompt terminology sweep and directory/nav updates ahead of merging the documentation reorg.

- **Status**: In Progress
- **Date**: 2025-11-28
- **Owner**: Documentation Working Group
- **Author**: Codex (GPT-5)
- **Goal**: Complete Pattern→Prompt terminology updates before docs-reorg merge

## Phase 1 Tasks (Pre-Merge)

### 1. Add Historical Terminology Note
- [ ] Add concise note to `docs/index.md` near top explaining Pattern→Prompt shift
- Location: After vision/intro, before main navigation sections
- Keep brief (2-3 sentences max)

### 2. Core Documentation Updates

#### README.md
- [ ] Search for "pattern" references (case-insensitive)
- [ ] Update to "prompt" where referring to AI prompts
- [ ] Review and verify changes

#### docs/index.md
- [ ] Update Pattern→Prompt references
- [ ] Update "Pattern/PromptTemplate" → "Prompt"
- [ ] Verify navigation links

#### docs/getting-started/
- [ ] `quick-start.md` - Pattern→Prompt
- [ ] `installation.md` - Pattern→Prompt
- [ ] `configuration.md` - Pattern→Prompt

#### docs/user-guide/
- [ ] Rename `patterns.md` → `prompts.md`
- [ ] Update content: Pattern→Prompt
- [ ] `overview.md` - Pattern→Prompt
- [ ] `best-practices.md` - Pattern→Prompt

### 3. Architecture Documentation

#### Directory Renaming
- [ ] Rename `docs/architecture/prompt-system/` → `prompt-system/`
- [ ] Update all internal links pointing to pattern-system/
- [ ] Update nav.md references

#### ADR Updates
- [ ] `adr-dd01-docs-reorg-strat.md` - Update Pattern→Prompt references
- [ ] `adr-dd02-docs-content-nav.md` - Update Pattern→Prompt references
- [ ] Review `docs/architecture/prompt-system/adr/` ADRs for consistency

### 4. Navigation & Links
- [ ] Update `docs/nav.md` - Pattern→Prompt labels
- [ ] Search for broken links after directory rename: `rg "pattern-system" docs/`
- [ ] Update `docs/documentation_index.md` if auto-generated content needs refresh

### 5. Verification
- [ ] Run `rg -i "pattern(?!s\\.md)" docs/index.md docs/README.md docs/getting-started/ docs/user-guide/` to find remaining instances
- [ ] Manual review of changes
- [ ] Test mkdocs build: `make docs`
- [ ] Verify navigation works correctly

### 6. Commit & Documentation
- [ ] Commit terminology updates with clear message
- [ ] Update CHANGELOG.md with ADR-DD03 Phase 1 completion
- [ ] Update AGENTLOG.md with session details
- [ ] Update TODO #9 with terminology work completion

## Files to Update (Quick Reference)

```
docs/index.md
README.md
docs/getting-started/quick-start.md
docs/getting-started/installation.md
docs/getting-started/configuration.md
docs/user-guide/patterns.md → prompts.md
docs/user-guide/overview.md
docs/user-guide/best-practices.md
docs/architecture/prompt-system/ → prompt-system/
docs/architecture/docs-system/adr/adr-dd01-docs-reorg-strat.md
docs/architecture/docs-system/adr/adr-dd02-docs-content-nav.md
docs/nav.md
```

## Search Commands for Validation

```bash
# Find all "pattern" references in Phase 1 files
rg -i "pattern" docs/index.md docs/getting-started/ docs/user-guide/

# Find references to old directory name
rg "pattern-system" docs/

# Find Pattern/PromptTemplate hedging
rg "Pattern/Prompt" docs/
```

## Notes
- Keep "pattern" when referring to software design patterns (non-prompt contexts)
- Preserve historical callouts in archived documents
- CLI documentation (docs/cli/) deferred to Phase 2
