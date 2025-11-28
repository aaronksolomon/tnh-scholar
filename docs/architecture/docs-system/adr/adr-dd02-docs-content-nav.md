---
title: "ADR-DD02: Documentation Main Content and Navigation Strategy"
description: "Defines content architecture, sync mechanisms, and navigation patterns for README.md, docs/index.md, and filesystem-driven documentation."
owner: ""
author: "Claude (Sonnet 4.5)"
status: approved
created: "2025-11-23"
---
# ADR-DD02: Documentation Main Content and Navigation Strategy

Establishes how README.md and docs/index.md relate, defines content inclusion patterns, and specifies navigation automation with mkdocs-literate-nav.

- **Status**: Proposed
- **Date**: 2025-11-23
- **Owner**: Documentation Working Group
- **Supersedes**: None
- **Related**: [ADR-DD01: Documentation System Reorganization Strategy](adr-dd01-docs-reorg-strat.md)

## Context

Following ADR-DD01's filesystem reorganization and literate-nav adoption (TODO #9, Part 4e complete), we now have:

- **README.md**: Rich user-facing content with Vision & Goals, Features, Quick Start, Installation, and Documentation Structure overview
- **docs/index.md**: Auto-generated sparse documentation map—just a flat list of all documents by section
- **Navigation**: Filesystem-driven via `generate_mkdocs_nav.py` producing `docs-nav.md` for mkdocs-literate-nav
- **Build automation**: Scripts for CLI docs generation, doc-index generation, and README sync verification

### Current Problems

1. **Content Divergence**: README.md has substantial onboarding content (vision, features, quick start) that doesn't appear in docs/index.md. Newcomers arriving at the published documentation site see only a file listing, not the compelling project introduction.

2. **Document Purpose Confusion**: Both documents serve entry points but target different contexts:
   - README.md: GitHub repository landing page, must be immediately actionable
   - docs/index.md: MkDocs site home, should orient users to the full documentation landscape

3. **Maintenance Burden**: No clear strategy for what content belongs where, when duplication is acceptable, or how to keep critical sections synchronized.

4. **Navigation Clarity**: Auto-generated `docs-nav.md` works well for filesystem traversal but lacks curation—no persona-based entry points, no workflow-oriented groupings, no "start here" guidance.

5. **Content Reusability**: Complex sections (installation steps, development setup, pattern system overview) appear in multiple places with manual duplication and drift risk.

### Design Constraints

- **Filesystem-driven navigation is non-negotiable** (ADR-DD01 decision): Documentation structure must mirror `docs/` tree with literate-nav auto-generation
- **README.md must remain editable**: Cannot become a pure build artifact—GitHub display requires direct file readability
- **CI verification**: Must detect when critical content drifts between README and documentation
- **Incremental adoption**: Solution must work with current tooling (mkdocs-literate-nav, mkdocs-gen-files) without major architectural changes
- **Contributor accessibility**: Documentation workflow should be obvious to new contributors without deep tooling knowledge

## Decision

Adopt a **Progressive Enhancement** content strategy with phase-based implementation:

### 1. Content Architecture

#### README.md: Concise Project Gateway

README.md serves as the **GitHub repository landing page** and remains hand-maintained. It provides:

- **Project description**: 2-3 sentence elevator pitch
- **Vision & Goals**: Why the project exists, what problems it solves (4-6 bullet points)
- **Features**: High-level capabilities overview (Core Tools summary, Pattern System summary)
- **Quick Start**: Minimal install + first command (PyPI install, tnh-setup, example usage)
- **Documentation Overview**: Brief orientation + link to full docs site
- **Development**: Pointer to [DEV_SETUP.md](https://github.com/aaronksolomon/tnh-scholar/blob/main/DEV_SETUP.md) and [CONTRIBUTING.md](https://github.com/aaronksolomon/tnh-scholar/blob/main/CONTRIBUTING.md)
- **Project Status**: Current version, alpha/beta/stable designation
- **Support & Community**: Links to issues, discussions, documentation

README.md stays **concise** (target: readable in 2-3 scrolls, ~200-250 lines). Detailed content lives in the documentation site.

#### docs/index.md: Comprehensive Documentation Hub

docs/index.md serves as the **MkDocs site landing page** and becomes the primary onboarding experience. It provides:

- **Welcome Section**: Same project description as README (synchronized manually or via drift reporting)
- **Getting Started (Persona-Based)**: Curated entry points for different audiences:
  - **Practitioners**: Using the CLI tools for dharma talk processing and translation
  - **Developers**: Contributing code, running tests, understanding architecture
  - **Researchers**: Exploring the knowledge base, evaluation workflows, and experiments
- **Key Features**: Expanded from README with links to deep-dive documentation
- **Installation**: Embedded detailed steps (can reference `_includes/installation.md` in Phase 2)
- **Quick Reference**: Common commands, pattern examples, troubleshooting links
- **Architecture Overview**: High-level system design with links to ADRs
- **Contributing**: How to participate, testing, documentation contributions
- **Documentation Map**: Auto-generated section listing (repositioned to bottom, renamed "Complete Documentation Index")

docs/index.md is **comprehensive** (target: complete orientation for all personas, ~400-500 lines). It's the definitive "start here" page.

**Persona-based navigation is a key differentiator** from README.md—it helps users self-identify their path and find relevant documentation quickly.

#### Shared Content Strategy

**Phase 1 (Current - Simple Independence with Drift Reporting)**:
- Accept controlled duplication of introductory content (project description, vision, high-level features)
- README and docs/index.md are independently maintained
- Lightweight drift reporting script (`check_readme_docs_drift.py`) generates informational reports
- Non-blocking: reports written to local log file (`docs_sync_report.txt`) for review
- Manual sync decisions made during project check-ins based on drift reports

**Phase 2 (Planned - Selective Inclusion)**:
- Extract complex, frequently reused content to `docs/_includes/`:
  - `installation.md`: Detailed install steps (PyPI, prerequisites, dev setup)
  - `development.md`: Development environment configuration
  - `pattern-overview.md`: Pattern/PromptTemplate system introduction
- Use mkdocs snippets plugin (`--8<--` syntax) for transclusion
- Keep README independent; include shared content in docs/index.md and other docs

**Phase 3 (Future - Templated Assembly, if needed)**:
- If maintenance burden grows significantly, consider templating (Jinja2 via mkdocs-macros)
- Would allow generating both README and docs/index.md from structured content
- Defer this decision until Phase 2 proves insufficient

### 2. Navigation Strategy

#### Filesystem-Driven Navigation (Literate-Nav)

Continue current approach with refinements:

- **Auto-generation**: `generate_mkdocs_nav.py` produces `docs-nav.md` from `docs/` tree structure
- **Front matter titles**: Prefer YAML `title:` field over filename humanization (must match exactly per markdown standards)
- **Sort order**: Maintain curated top-level order in `TOP_LEVEL_ORDER` list
- **Index page handling**: Directory `index.md` becomes section landing page with overview + persona-appropriate navigation aids

Navigation file `docs-nav.md` is a **build artifact** (regenerated on every docs build).

#### Section Index Pages

Every top-level directory must have an `index.md` that provides:

- **Section purpose**: What this documentation covers
- **Target audience**: Who should read this section
- **Navigation aids**: Curated list of key documents (complement to auto-generated nav)
- **Prerequisites**: What to read first (if applicable)

Example structure for `docs/architecture/index.md`:

```markdown
---
title: "Architecture"
description: "System design, ADRs, and component deep-dives for TNH Scholar."
---
# Architecture

This section documents the design decisions, system architecture, and
component implementations for TNH Scholar.

## Getting Started
- **New to the codebase?** Start with [System Overview](system-overview.md)
- **Looking for decisions?** Browse [ADRs by topic](adr/index.md)
- **Need component details?** See subsystem design documents below

## Key Resources
- [ADR Index](adr/index.md) - All architectural decision records
- [GenAI Service](gen-ai-service/design/genai-service-strategy.md) - Core AI integration layer
- [Pattern System](pattern-system/adr/adr-pt02-pattern-catalog.md) - Prompt management architecture
- [Transcription Pipeline](transcription/design/diarization-system1.md) - Audio processing design

## Subsystems
- [AI Text Processing](ai-text-processing/) - Text transformation pipeline
- [Knowledge Base](knowledge-base/) - Vector search and metadata
- [Transcription](transcription/) - Audio-to-text with diarization
- [Video Processing](video-processing/) - YouTube integration
```

#### Documentation Map Integration

The auto-generated "Documentation Map" in docs/index.md (current behavior) is **retained** but **repositioned**:

- Move to bottom of docs/index.md (after Welcome, Getting Started (Persona-Based), Features, Installation, Quick Reference, Architecture Overview, Contributing)
- Rename to "Complete Documentation Index"
- Add introductory text: "Browse all documentation organized by topic. For persona-based entry points, see Getting Started above."

This ensures the landing page prioritizes **human-oriented navigation** (persona paths) over **exhaustive file listings** (auto-generated map).

### 3. Content Drift Monitoring (Phase 1 MVP)

#### Lightweight Drift Reporting

Instead of enforcing synchronization, Phase 1 uses **informational drift reporting**:

**Script**: `scripts/check_readme_docs_drift.py`

The script compares sections between README.md and docs/index.md by **dynamic heading detection**:

**Approach**:

- Extract **all** `## Section Name` headings from both files
- Compare sections with **matching titles** (case-sensitive)
- Warn on title mismatches (case, punctuation, spacing differences)
- Report sections that exist in one file but not the other

**Behavior**:

1. Extract all `## Level 2` sections from both files
2. Match sections by heading text (exact match)
3. For matched sections: generate unified diff if content differs
4. For unmatched sections: report "only in README" or "only in docs/index.md"
5. Warn on near-matches (e.g., "Quick Start" vs "Quick start" - case mismatch)
6. Write report to `docs_sync_report.txt` (gitignored)
7. Print report to console for CI visibility
8. **Always exit 0** (non-blocking, informational only)

**Report format**:

```text
================================================================================
README.md ↔ docs/index.md Drift Report
Generated: 2025-11-23 10:15:32
================================================================================

Matched Sections (compared):
✓ Vision & Goals: IDENTICAL
✗ Features: DIFFERS

--- README.md::Features
+++ docs/index.md::Features
@@ -1,5 +1,7 @@
 TNH Scholar provides several CLI tools:
 - audio-transcribe: Process audio files
+- tnh-fab: Text processing with patterns
 - ytt-fetch: Download YouTube transcripts

Sections only in README.md:
- Example Usage
- Development

Sections only in docs/index.md:
- Architecture Overview
- Contributing
- Complete Documentation Index

Title Mismatches (possible typos):
⚠ "Quick Start" (README) vs "Quick start" (docs/index.md) - case mismatch

⚠ DRIFT DETECTED - Review differences above
This is informational only - no action required unless intentional divergence.
================================================================================
```

#### Integration Points

**Makefile target**:

```makefile
.PHONY: docs-drift
docs-drift:
    @poetry run python scripts/check_readme_docs_drift.py

.PHONY: docs-verify
docs-verify: docs-drift
    @poetry run mkdocs build --strict
```

**CI workflow** (non-blocking):

```yaml
- name: Check documentation drift
  run: |
    python scripts/check_readme_docs_drift.py
    cat docs_sync_report.txt
  continue-on-error: true
```

**Gitignore**:

```gitignore
# Documentation drift reports (local review only)
docs_sync_report.txt
```

#### Usage Workflow

1. **During development**: Run `make docs-drift` to see current drift status
2. **Before commits**: Review `docs_sync_report.txt` locally
3. **In CI**: Drift report printed in logs (visible but doesn't fail build)
4. **At project check-ins**: Review accumulated drift, decide if manual sync warranted

#### Acceptable Divergence

The following divergences are **expected and acceptable**:

- **Depth**: README gives high-level overview; docs/index.md provides detailed explanation
- **Audience**: README targets newcomers; docs/index.md serves all personas
- **Navigation**: README links to docs site; docs/index.md embeds navigation aids
- **Examples**: README shows minimal quick-start; docs/index.md includes comprehensive examples

**No sync enforcement** - teams decide when alignment matters based on drift reports.

### 4. Content Inclusion Patterns (Future)

**Status**: Detailed design deferred to **ADR-DD03: Content Reuse and Inclusion Strategies**

Phase 1 accepts controlled duplication with drift monitoring. When duplication becomes burdensome, ADR-DD03 will define:

- **Inclusion hierarchy**: Markdown snippets (`docs/_includes/`), macros (`docs/_templates/`), and generation scripts
- **Tooling choices**: mkdocs snippets plugin, mkdocs-macros, mkdocs-gen-files integration
- **Naming conventions**: Underscore-prefixed directories for non-user-facing content
- **Migration strategy**: Moving duplicated content to shared locations

**Current approach** (Phase 1): Use generation scripts (Level 3) only for already-automated content (CLI docs, API reference, documentation index). No manual content inclusion yet.

### 5. Maintenance Workflows

#### Updating README.md

1. Edit README.md directly in repository root
2. Run `make docs-drift` to see if changes affect monitored sections
3. Review `docs_sync_report.txt` to assess drift
4. Decide if docs/index.md should be updated (no enforcement)

#### Updating docs/index.md

1. Edit docs/index.md directly in `docs/`
2. Run `make docs-drift` to check for drift in monitored sections
3. Review report and update README.md if appropriate
4. CI runs drift check but doesn't fail on drift (informational only)

#### Adding New Documentation

1. Create markdown file in appropriate `docs/` subdirectory
2. Add YAML front matter (title, description, owner, author, status)
3. Navigation updates **automatically** via literate-nav
4. If creating new top-level section, add to `TOP_LEVEL_ORDER` in `generate_mkdocs_nav.py`
5. Create section `index.md` with overview and navigation aids

#### Reorganizing Content

1. Move files using `git mv` to preserve history
2. Update internal links (CI link checker will catch broken references)
3. Navigation regenerates automatically
4. Update section index pages if section purpose changes
5. Run `make docs` to rebuild and verify

### 6. Implementation Phases

#### Phase 1: Simple Independence with Drift Reporting (Current Priority)

**Scope**: Complete TODO #9, Part 3b

- [x] ~~Enhance docs/index.md with persona-based Getting Started~~
- [ ] Implement `check_readme_docs_drift.py` script
- [ ] Add `docs-drift` target to Makefile
- [ ] Add `docs_sync_report.txt` to `.gitignore`
- [ ] Integrate drift reporting into CI (non-blocking)
- [ ] Create/update section index pages for all top-level directories
- [ ] Reposition auto-generated Documentation Map in docs/index.md

**Success Criteria**:
- docs/index.md provides comprehensive onboarding (400-500 lines)
- README.md stays concise (200-250 lines)
- Drift reporting runs in CI and generates local reports
- No CI failures from drift (informational only)
- All top-level sections have index.md with navigation aids

#### Phase 2: Content Inclusion Patterns (Future)

**Status**: Deferred to **ADR-DD03: Content Reuse and Inclusion Strategies**

**Trigger**: When 10+ instances of duplicated complex content (installation steps, development setup, etc.) cause maintenance burden.

**Approach Sketch**:

- Use mkdocs snippets plugin (`--8<--` syntax) for shared content in `docs/_includes/`
- Keep README.md independent; include shared sections in docs/index.md and other docs
- Document inclusion patterns in markdown standards

**Decision Point**: Revisit 6 months post-beta or when drift reporting shows repeated manual syncs of identical content.

#### Phase 3: Advanced Automation (Future, If Needed)

**Status**: Deferred to **ADR-DD04: Documentation Generation and Templating** (if Phase 2 proves insufficient)

**Trigger**: High-churn content causing frequent drift despite inclusion patterns.

**Approach Sketch**:

- Templated assembly using Jinja2 via mkdocs-macros
- Structured content storage (YAML/JSON) for frequently changing sections
- Generate both README.md and docs/index.md from templates

**Decision Point**: Only proceed if clear ROI demonstrated (e.g., weekly README/docs updates causing sync overhead).

## Alternatives Considered

1. **Templated Assembly (Full Jinja2)**: Rejected for Phase 1 due to build complexity and README becoming non-editable artifact. Deferred to Phase 3 if needed.

2. **README as Build Artifact**: Rejected because GitHub requires readable README in repository view. Generated files hurt discoverability.

3. **Single Unified Document**: Rejected because README and docs/index serve different contexts (GitHub vs. MkDocs site) and need different levels of detail.

4. **Manual Duplication Without Any Monitoring**: Rejected due to drift risk observed in current state (README and docs/index.md had diverged significantly). Lightweight drift reporting provides awareness without enforcement overhead.

5. **Shared Content Directory (No Templating)**: Considered for Phase 1 but deferred to Phase 2. Initial implementation keeps documents independent with drift reporting only.

6. **Enforced Synchronization with Markers**: Rejected for Phase 1 due to added complexity (marker management, CI failures on drift). Phase 1 prioritizes simplicity—drift reporting provides awareness without enforcement burden. Can revisit in Phase 2 if drift proves problematic.

## Consequences

### Positive

- **Clear ownership**: README and docs/index.md have distinct purposes and audiences
- **Flexibility**: Each document optimized for its context (GitHub vs. MkDocs site)
- **Safety net**: Sync verification prevents critical content drift while allowing intentional divergence
- **Incremental adoption**: Start simple (independent docs), add inclusion patterns only when needed
- **Contributor clarity**: Obvious where content lives, when to update both files, how to verify
- **Navigation automation**: Literate-nav keeps structure in sync with filesystem
- **Onboarding improvement**: docs/index.md becomes comprehensive entry point (not just file list)

### Negative / Risks

- **Controlled duplication**: Accept some redundancy between README intro and docs/index intro (mitigated by drift reporting for awareness)
- **Manual sync decisions**: Teams must review drift reports and decide when to sync (no enforcement)
- **Drift accumulation**: Without enforcement, documents could diverge significantly over time (mitigated by regular project check-in reviews)
- **Tooling dependency**: Relies on mkdocs-literate-nav, mkdocs-gen-files, and custom scripts (acceptable given ADR-DD01 commitment)
- **Phase 2 transition**: Moving to inclusion patterns requires coordination (defer until post-beta to minimize churn)

### Mitigation Strategies

1. **Document the workflow**: Clear instructions in `docs/docs-ops/markdown-standards.md` and CONTRIBUTING.md
2. **Regular reviews**: Include drift report in project check-in process
3. **Minimal monitoring surface**: Only track high-level sections (Vision, Features, Quick Start, Installation)
4. **Defer complexity**: Don't adopt inclusion patterns or sync enforcement until duplication causes real pain
5. **Template enforcement**: ADR template and standards prevent structural inconsistency

## Open Questions & Future Decisions

1. **Sync enforcement**: Should we enforce synchronization in CI or keep reporting-only? **Decision**: Start with reporting-only in Phase 1; add enforcement in Phase 2 only if drift becomes problematic.

2. **Documentation Map position**: Bottom of docs/index.md or separate page? **Decision**: Keep at bottom initially; move to dedicated `/documentation-index` page if docs/index.md exceeds 600 lines.

3. **Persona-based navigation**: Should literate-nav group docs by persona (User/Developer/Researcher) in addition to topic? **Decision**: Defer to Phase 2; current topic-based structure sufficient for ~100 docs.

4. **Section index automation**: Can section index pages be partially auto-generated? **Decision**: Keep hand-maintained for curation; auto-generation risks losing narrative flow.

5. **Link checking**: Should CI verify all internal markdown links? **Decision**: Yes, add to TODO #9, Part 4d (link normalization task).

## Approval & Tracking

- **TODO Reference**: TODO #9 (Documentation Reorganization, ADR-DD01), Part 3b
- **Implementation Tracking**: GitHub issues tagged `docs` + `adr-dd02`
- **Related ADRs**:
  - [ADR-DD01](adr-dd01-docs-reorg-strat.md): Documentation System Reorganization Strategy (accepted)
  - **ADR-DD03**: Content Reuse and Inclusion Strategies (future - Phase 2)
  - **ADR-DD04**: Documentation Generation and Templating (future - Phase 3, if needed)
- **Review Cycle**: Reassess Phase 2 transition 6 months post-beta or when 10+ instances of complex content duplication observed

Approval of this ADR completes the content architecture design for TODO #9, Part 3b, and provides a roadmap for incremental documentation improvements through beta and beyond.
