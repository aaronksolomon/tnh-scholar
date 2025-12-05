---
title: "ADR-DD01: Documentation System Reorganization Strategy"
description: "Rebuilds the documentation architecture with new directories, automation, and Prompt terminology."
owner: ""
author: "Codex (GPT-5)"
status: accepted
created: "2024-11-09"
---
# ADR-DD01: Documentation System Reorganization Strategy

Defines the new documentation hierarchy, automation tooling, and naming standards for TNH Scholar.

- **Status**: Accepted
- **Date**: 2024-11-09
- **Owner**: Documentation Working Group (initially Codex + maintainers)

## Context

The documentation footprint for TNH Scholar has grown organically:

- `docs/index.md` and `README.md` describe the project at a high level but omit the current architecture, roadmap, or research context and still lean on the legacy "Pattern" terminology.
- End-user docs (`docs/getting-started`, `docs/user-guide`, `docs/cli`, `docs/api`) only cover a subset of the available tools and do not reflect the latest CLI surface, Prompt design, or evaluation workflows.
- Developer and architecture materials are split between `docs/development`, a large unindexed `docs/design` tree containing numerous ADRs, and `docs/docs-design` (the original documentation plan). Most of this content never appears in `mkdocs.yaml`, so the published site hides the majority of design history.
- Research work (`docs/research/**`) mixes current experiments with exploratory transcripts without indicating recency or ownership.
- There is no standard place for "doc ops" guidance (style guide, review checklists, roadmap), and the README is not a comprehensive introduction to TNH Scholar’s goals, structure, design principles, or contribution opportunities.

The current effort (TODO #9) should reorganize the documentation without losing information, surface up-to-date guidance, archive historical material appropriately, and ensure the MkDocs site mirrors the on-disk structure. It must also accommodate the ongoing rename from **Pattern** to **Prompt** (e.g., `docs/user-guide/patterns.md`, `docs/design/pattern/*`, `docs/cli/tnh-fab.md`, etc.).

## Decision

Adopt a documentation architecture that is source-of-truth in the repository, entirely reflected in MkDocs navigation, and explicit about currency vs. history.

1. **Unify the directory layout.**
   - Replace the current mix of `design/`, `development/`, `docs-design/`, and `research/` subtrees with a single hierarchy:

     ```plaintext
     docs/
       index.md                    # mirrors README, includes vision + orientation
       overview/                   # mission, roadmap, release notes, glossary
       getting-started/            # install, quick start, configuration
       user-guide/                 # workflows, Prompt usage, best practices
       cli-reference/              # per-command auto-generated docs
       prompt-templates/           # Prompt catalog, conventions, metadata schema
       api-reference/              # mkdocstrings output + integration guides
       architecture/               # system design, component deep-dives, ADRs
         adr/                      # numbered ADRs (inc. migrated legacy files)
       development/                # contributing, dev setup, testing, coding standards
       research/                   # active experiments + summaries
       docs-ops/                   # documentation roadmap, maintenance plan, style guide
       archive/                    # frozen historical docs (design prototypes, transcripts, etc.)
     ```

     Each folder gains an `index.md` that frames its content and links to authoritative children. Legacy directories (e.g., `docs/design/tnh-fab/...`) move into either `architecture/adr/` or `archive/design/tnh-fab/` depending on relevance.

2. **Enforce README ↔ site parity.**
   - Expand `README.md` into a full project introduction (vision, goals, architecture snapshot, CLI summary, development status, research focus, and where to contribute) and keep it synchronized with `docs/index.md`.
   - Include the documentation map (nav overview + major directories) so newcomers know where to look.

3. **Adopt Prompt terminology.**
   - Rename `docs/user-guide/patterns.md` to `user-guide/prompt-templates.md` (mirrored in MkDocs nav and CLI docs).
   - Update all references in docs (and eventually CLI/API text) to use Prompt nomenclature while acknowledging the historical Pattern term in the archive.

4. **Surface everything through MkDocs.**
   - Restructure `mkdocs.yaml` to follow the physical layout above, ensuring no Markdown lives outside the published nav.
   - Use nested sections (Material tabs) to distinguish current vs. archival content, with clear "Historical" banners and metadata.

5. **Introduce doc automation + QA.**
   - Add a `scripts/docs/` toolkit with:
     - `generate_cli_docs.py` – runs each Click/Typer command (`tnh-fab --help`, etc.) and produces Markdown in `docs/cli-reference`.
     - `generate_prompt_template_catalog.py` – inspects `patterns/` (soon `prompt_templates/`) and builds a catalog page (name, intent, inputs, outputs, maturity).
     - `sync_readme.py` – verifies that README sections map to `docs/index.md` and fails CI if they diverge.
   - Extend MkDocs with `mkdocstrings` (already configured) for API coverage and consider `mkdocs-gen-files` + `mkdocs-literate-nav` (or Material `navigation.instant`) to keep nav synchronized automatically.
   - Add CI jobs (`make docs-verify`) to run `mkdocs build`, automated link checking, and template generation.

6. **Document gaps + backlog.**
   - Produce a living checklist in `docs/docs-ops/roadmap.md` describing missing or stale topics (see below).
   - Attach ownership metadata (module owner, last reviewed) at the top of each page.

7. **Codify Markdown + indexing standards.**
   - Generate `documentation_index.md` at the repo root (and mirrored at `docs/docs-ops/documentation_index.md`) from front matter metadata so contributors can quickly locate any doc without digging into directories. The document index is treated as a build artifact and regenerated whenever docs change (`scripts/generate_doc_index.py` handles this and marks the files with `auto_generated: true`).
   - Publish `docs/docs-ops/markdown-standards.md` to define file naming (lowercase kebab-case, hyphen-separated, no spaces), required YAML front matter (now including an `author` provenance field), mandated `# Title` + single-paragraph description, link styles, and lint expectations. ADR filenames follow `adr-<modulecode><number>-<descriptor>.md` (e.g., `adr-dd01-docs-reorg.md`).
   - Adopt `markdownlint` (GitHub: DavidAnson/markdownlint) in CI/Make targets to enforce the standard automatically. `.markdownlint.json` disables MD025/MD013 to account for YAML-title duplication and long architecture tables; CI now runs `npx markdownlint '**/*.md'`.
   - Provide an ADR template (`docs/docs-ops/adr-template.md`) that applies the standard (front matter + `# Title` heading + one-sentence summary) while accommodating ADR metadata (Status, Date, Owner, Author). Also require module-specific storage: `docs/architecture/<module>/adr/ADR-<module-code><number>.md`, where the module code is one to four lowercase letters (e.g., `adr-a01`, `adr-kb02`, `ADR-dd01`) to keep the catalog navigable.
   - Update existing ADRs/docs over time to conform to the standards; new docs must comply immediately.

## Implementation Plan

1. **Inventory and tagging (Week 1).**
   - Tag each existing Markdown file as `current`, `needs-update`, or `historical`.
   - Capture metadata (owner, last review date) in YAML front matter.
   - Identify Pattern→Prompt rename scope via `rg` (currently 300+ hits).

2. **Filesystem reorganization (Week 1–2).**
   - Create the target directory structure.
   - Move files into their new homes, inserting shim `index.md` pages where necessary.
   - Preserve original filenames in `archive/` for traceability and add cross-links from the new canonical documents.

3. **Terminology + README sweep (Week 2).**
   - Update README and `docs/index.md` with the comprehensive intro, project structure, research focus, and contribution pointers.
   - Rename `Pattern` to `Prompt` (docs + nav). Retain a glossary entry describing the rename.

4. **MkDocs + automation (Week 2–3).**
   - Rewrite `mkdocs.yaml` nav to mirror the new hierarchy.
   - Add doc-generation scripts and hook them into `make docs`.
   - Configure CI to run `mkdocs build` plus the generators (ensuring docs stay up to date).

5. **Historical archiving + discoverability (Week 3).**
   - Move legacy ADRs/prototypes into `docs/archive/**` with short summaries in their parent section pointing users to the archive.
   - Build an archive index (chronological table with tags, e.g., `design`, `research`, `ops`).

6. **Gap-filling sprint planning (Week 3+).**
   - Use the backlog below to create GitHub issues and assign owners.
   - Track documentation coverage in `docs/docs-ops/roadmap.md`.

## Documentation Backlog (initial)

1. **Prompt Catalog + Standards.**
   - Naming conventions, metadata schema, versioning, testing strategy, migration guide from Patterns.
2. **Workflow Playbooks.**
   - End-to-end tutorials for research tasks (e.g., transcription → translation → Prompt evaluation).
3. **Evaluation + Benchmarking.**
   - How to run `evaluation/` scripts, metrics definitions, sample datasets.
4. **Knowledge Infrastructure.**
   - Vector store design, metadata extraction pipeline, ingestion policies.
5. **Deployment / Operations.**
   - Release checklist integration, environment promotion strategy, secrets management.
6. **Research Summaries.**
   - Digestible summaries of `docs/research/*` experiments with conclusions and follow-up work.
7. **Documentation Ops.**
   - Style guide, doc PR checklist, automation instructions, label taxonomy.

## Consequences

- **Positive**
  - Every document has a clear home and appears in the published site.
  - README + docs/index become authoritative onboarding material.
  - Historical context remains accessible but separated from current guidance.
  - Automation keeps CLI/API docs and template catalogs in sync with the codebase.
  - Terminology alignment reduces confusion during the Pattern→Prompt migration.

- **Negative / Risks**
  - Short-term churn as files move; open PRs may require rebase assistance.
  - Automation scripts add maintenance burden and require CI resources.
  - Contributors must learn the new structure; requires communication + contributor guide updates.

## Open Questions & Decisions

1. **Nav automation** – adopt `mkdocs-literate-nav` once directories encode archival status (e.g., `archive/`, `architecture/adr/`). We'll author explicit `index.md` files but let literate-nav derive most of the hierarchy to keep nav and filesystem in sync automatically.
2. **Research storage** – keep curated summaries in `docs/research/` but move bulky/raw transcripts to external storage (S3 or knowledge base). Each summary page links to the raw artifacts so we avoid bloating Git while retaining traceability.
3. **Single README** – maintain one `README.md` as the universal entry point with early persona routing (user/developer/researcher). Each docs section gets a robust `index.md` that continues the onboarding for that persona.
4. **Review cadence** – tie required documentation reviews to the release/CI pipeline instead of calendar schedules. Major version bumps (e.g., `0.x → 1.0`, `1.15 → 2.0`) must run a docs verification job that fails if key sections lack updates/acknowledgement. Smaller releases can reuse the automation but only warn on drift.

Approval of this ADR green-lights the restructuring work for TODO #9 and provides a concrete blueprint for subsequent documentation updates.

---

## As-Built Notes & Addendums

### Addendum 2025-12-03: CLI Documentation Consolidation

**Context**: During implementation, the planned separation of `docs/cli/` (guide material) and `docs/cli-reference/` (auto-generated reference docs) proved confusing and redundant. The existing content was already reference documentation (per-command pages like `tnh-fab.md`, `audio-transcribe.md`), not guide material.

**Decision**:

1. **Consolidated all CLI documentation** into single `docs/cli-reference/` directory containing:
   - Overview and guide material ([overview.md](/cli-reference/overview.md))
   - Per-command reference documentation (individual command pages)
2. **Removed** auto-generated CLI reference stubs and generation infrastructure
3. **Deferred** comprehensive CLI reference generation (TODO #17) until after CLI refactor (blocked by TODO #8)
4. **Renamed** `docs/cli/` to `docs/cli-reference/` to accurately reflect content type

**Rationale**:

- The CLI structure is scheduled for overhaul, making current auto-generated stubs low-value
- Placeholder documentation with minimal content ("run --help for help") doesn't serve users
- Directory name `cli-reference` accurately describes the reference-style content
- Single location reduces navigation complexity and maintenance burden
- Aligns with actual as-built directory structure

**Implementation Changes**:

- Removed auto-generated `docs/cli-reference/` stub files (2025-12-03)
- Removed `scripts/generate_cli_docs.py` from MkDocs build pipeline
- Renamed `docs/cli/` to `docs/cli-reference/`
- Updated navigation scripts with consolidated `cli-reference` directory:
  - `scripts/generate_mkdocs_nav.py`
  - `scripts/generate_subdir_indexes.py`
- Created TODO #17 to track comprehensive CLI reference generation post-refactor

**Updated Directory Structure**:

```plaintext
docs/
  cli-reference/              # CLI overview + per-command reference (consolidated)
  api/                        # API reference
  project/                    # Project meta-docs
  community/                  # Community resources
```

**References**:

- TODO #17: Comprehensive CLI Reference Documentation
- TODO #8: Clean Up CLI Tool Versions (blocks CLI reference work)

---

### Addendum 2025-12-04: Absolute Link Strategy

**Context**: During documentation reorganization, the team initially used relative links (e.g., `../../../cli-reference/overview.md`). With the deep hierarchical structure (`docs/architecture/*/adr/`, `docs/architecture/*/design/`), relative links became unwieldy, error-prone, and generated MkDocs warnings about absolute paths.

**Decision**:

1. **Enable MkDocs 1.6+ absolute link validation** in `mkdocs.yaml`:

   ```yaml
   validation:
     links:
       absolute_links: relative_to_docs
   ```

2. **Standardize on absolute links** for all internal documentation cross-references:
   - Use `/cli-reference/overview.md` instead of `../../../cli-reference/overview.md`
   - Links starting with `/` are interpreted relative to `docs/` directory
   - MkDocs validates absolute links and converts them to proper relative links in HTML output

3. **Convert all existing relative links to absolute format** (TODO #18)

**Rationale**:

- **Clearer intent**: `/architecture/docs-system/adr/...` immediately shows destination vs calculating `../../../` depth
- **Easier refactoring**: Search/replace `/old/path/file.md` → `/new/path/file.md` works across all docs; relative links require different updates per source location
- **Automation friendly**: Doc generation scripts construct absolute paths easily without calculating relative paths from each source file
- **Less error-prone**: No manual counting of `../` levels in deep hierarchies
- **Better for complex structures**: Multi-level architecture organization makes relative links unreadable

**Implementation**:

- Added `validation.links.absolute_links: relative_to_docs` to mkdocs.yaml (2025-12-04)
- Converted links in this ADR to absolute format
- Created TODO #18 for systematic conversion across all documentation

**Impact**:

- Eliminates MkDocs warnings about absolute links
- Improves documentation maintainability for future reorganizations
- Makes link targets immediately clear to readers and automation
- No functional change: MkDocs converts absolute links to relative in HTML output

**References**:

- TODO #18: Convert Documentation Links to Absolute Paths
- [MkDocs 1.6 Release Notes](https://www.mkdocs.org/about/release-notes/#version-16-2024-06-10)

---

## Addendum 3: Auto-Generated Documentation Index System (2025-12-05)

**Context**:

The original ADR specified a manually-maintained Documentation Map section in `/docs/index.md`. As the documentation grew, maintaining this static list became error-prone and duplicated information available from filesystem scanning.

**Decision**:

Implemented a dual-format auto-generated documentation index system:

1. **`documentation_index.md`** (comprehensive reference):
   - Searchable table format with Title, Description, Created date, and Path
   - Organized by category sections (Getting Started, Architecture, CLI Reference, etc.)
   - Generated from frontmatter metadata via `scripts/generate_doc_index.py`

2. **`documentation_map.md`** (browsable navigation):
   - Clean hierarchical list format matching the original static Documentation Map
   - Same category organization as documentation_index.md
   - Auto-appended to `/docs/index.md` during build via `scripts/append_doc_map_to_index.py`

**Implementation**:

- Created `scripts/generate_doc_index.py` - scans docs/ directory, extracts frontmatter, generates both files
- Created `scripts/append_doc_map_to_index.py` - injects documentation_map.md content into index.md at build time
- Added both scripts to mkdocs.yaml gen-files plugin
- Excluded `documentation_map.md` from navigation (mkdocs.yaml exclude_docs) since it's embedded in index.md
- Respects existing EXCLUDE_PATTERNS to avoid indexing draft/archived files
- Filters out subdirectory `index.md` files from documentation_map.md (navigation landing pages that clutter the browsable list)

**Benefits**:

- **Single source of truth**: Documentation structure derived from filesystem and frontmatter
- **Always in sync**: Regenerated on every `mkdocs build` or `mkdocs serve`
- **Two complementary formats**:
  - Browsable map for quick navigation on landing page
  - Comprehensive searchable index with metadata for reference
- **Zero maintenance**: No manual updates needed when adding/removing docs
- **Landing page friendly**: Documentation Map visible on index.md without clicking

**Migration from original ADR**:

- Original: Manually-maintained static Documentation Map in index.md
- Now: Auto-generated from filesystem, appended at build time
- Static map in source index.md remains as fallback but is replaced in built site

**References**:

- `/scripts/generate_doc_index.py` - Main index generation script
- `/scripts/append_doc_map_to_index.py` - Build-time index.md augmentation
- `/docs/documentation_index.md` - Auto-generated comprehensive reference
- `/docs/documentation_map.md` - Auto-generated hierarchical navigation (excluded from site nav)
