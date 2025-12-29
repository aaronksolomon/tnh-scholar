---
title: "Markdown Standards"
description: "House style, linting, and structure requirements for TNH Scholar documentation."
owner: ""
author: ""
status: current
created: "2025-02-27"
---
# Markdown Standards

A consistent Markdown style keeps the documentation easy to navigate, parse, and automate. This guide defines the contract that every `.md` file in TNH Scholar must follow.

## File & Directory Naming

- Use **lowercase kebab-case** (`example-file-name.md`) for all filenames and directories. Avoid spaces and CamelCase.
- Prefer descriptive names that communicate the document scope (e.g., `architecture-system-overview.md`, not `overview.md`).
- Historical files that still use legacy names may remain until the archive migration, but new or renamed files must conform.
- Subdirectory landings: use `index.md` as the folder entry page; use `overview.md` for curated summaries within that folder. Avoid `README.md` in subdirectories (MkDocs doesn’t treat it as an entry page).

## Required Front Matter

All Markdown files must start with YAML front matter so the doc tooling can build the global index (initial state example):

```yaml
---
title: "Human-readable Title"
description: "One-sentence summary"
owner: ""
author: ""
status: draft
created: "YYYY-MM-DD"
---
```

- `title` and `description` should match the real content (not just repeat headings).
- `owner` may remain blank while we have a single maintainer but should be populated when an area gains ownership.
- `author` records provenance (person, tool, or AI agent responsible for the initial version of the document). Use a short identifier or comma-separated list when multiple authors collaborate.
- `status` tracks document lifecycle. See status values below.
- `created` reflects the original commit date when possible (auto-filled by tooling).
- `auto_generated` (boolean) indicates whether the file is machine-generated. When `true`, only `current`, `archived`, `deprecated`, or `superseded` statuses are allowed.
- `updated` date of change, added if file is updated.
- **Prompt Template Exception**: files in `patterns/` (soon living under `docs/prompt-templates/`) use a prompt-specific front matter schema that includes runtime variables and other metadata. Continue using that specialized format until the Prompt Template standard is finalized (TBD); do **not** remodel those files to the generic doc front matter without an explicit migration plan.

### Document Status Values

**Universal status values** (apply to all Markdown documents):

- `proposed` = early RFC/discussion stage
- `draft` = initial iteration pending approval
- `wip` = actively being revised (expected to change)
- `current` = approved baseline for active use (guides, references, documentation)
- `deprecated` = still valid but being phased out
- `superseded` = replaced by newer version (see link in doc)
- `archived` = historical reference only

**ADR-specific status values** (only for Architecture Decision Records):

- `accepted` = decision approved, ready for implementation
- `implemented` = decision has been executed/completed
- `rejected` = proposed but not approved

**Status lifecycle flows:**

**ADRs:**

```text
proposed → accepted → [wip] → implemented → [superseded/archived]
    ↓
  rejected
```

**Guides/References/Documentation:**

```text
draft/proposed → current → [deprecated] → [superseded/archived]
    ↓
  wip (if major revision)
```

**Key distinction**: ADRs track decisions over time (use `accepted`/`implemented`), while guides track content validity (use `current`/`deprecated`). ADRs never use `current`; regular docs never use `accepted`/`implemented`.

**Auto-generated file constraint**: Files with `auto_generated: true` may only use `current`, `archived`, `deprecated`, or `superseded` status. Manual lifecycle states (`proposed`, `draft`, `wip`, `accepted`, `implemented`, `rejected`) are invalid for generated content.

## Heading & Summary Rules

- Immediately after front matter, include a `# Title` heading that **exactly matches** the YAML `title` field (character-for-character, including punctuation and capitalization).
- Follow the heading with a one-sentence or single-paragraph description that orients the reader. This description should expand on or clarify the `description` field from front matter. ADRs and reference docs must comply even if they also list metadata (Status, Date, Owner) right after the summary.
- Use hierarchical headings (`##`, `###`, etc.) without skipping levels. Avoid deep nesting beyond `####`.
- **Validation**: A linting script (`scripts/validate_titles.py`) will verify YAML `title` matches `# Heading` exactly. CI will warn (but not fail) on mismatches until all legacy docs are updated.

## ADR Format

- Store ADRs under module directories such as `docs/architecture/<module>/adr/` (legacy ADRs move there during the restructure).
- File naming convention: `adr-<modulecode><number>-<descriptor>.md`, all lowercase, hyphen-separated (e.g., `adr-dd01-docs-reorg-strat.md`, `adr-kb02-knowledge-store.md`). Strategy ADRs append `-strat` to the descriptor (`adr-dd01-docs-reorg-strat.md`) so higher-level directional docs are easy to spot.
- **Decimal ADR Convention** (added 2025-12-12): Related or supporting ADRs use decimal notation:
  - `adr-at03-object-service-refactor.md` (main ADR)
  - `adr-at03.1-transition-plan.md` (transition strategy)
  - `adr-at03.2-implementation-guide.md` (implementation details)
  - Decimal ADRs must include `parent_adr` and optionally `type` in frontmatter (see template)
  - Benefits: Clear hierarchy, namespace flexibility, maintains traceability without namespace cramping
- The visible title in the Markdown file must use uppercase module codes, e.g., `# ADR-DD01: Documentation System Reorganization Strategy`. A simple lowercase-to-uppercase transform keeps filenames and titles aligned.
- Each ADR uses the same front matter and heading rules as any other doc.
- After the introductory paragraph, list metadata bullets:

```markdown
- **Status**: Proposed
- **Date**: 2025-02-27
- **Owner**: Documentation Working Group
- **Author**: Codex (GPT-5)
```

- Organize ADRs under module-specific folders (`docs/architecture/<module>/adr/ADR-<code>.md`). Module codes can be one to four uppercase characters (e.g., `ADR-A01`, `ADR-KB01`, `ADR-DD01`) to keep numbering human-readable while signaling the owning subsystem.

- Standard sections: `## Context`, `## Decision`, `## Consequences`, `## Open Questions`. Add `## Alternatives Considered` if helpful.
- A reusable template lives in `docs/docs-ops/adr-template.md`.

## Content Guidelines

- Use fenced code blocks with language hints (\```bash, \```python, \```yaml, etc.).
- **Link formatting**:
  - **Use absolute links only** for internal documentation references. Absolute links are relative to the MkDocs root (`/docs` directory).
  - Example: `/architecture/overview.md` (resolves to `docs/architecture/overview.md` in the repository).
  - Example: `/architecture/docs-system/adr/adr-dd01-docs-reorg-strat.md` (resolves to `docs/architecture/docs-system/adr/adr-dd01-docs-reorg-strat.md`).
  - **Never use** relative links like `../architecture/overview.md` or paths that include `/docs/` in the link itself.
  - Always use absolute links starting with `/` not relative links to avoid broken references when files are moved or reorganized.
  - For external URLs, use full absolute URLs (e.g., `https://example.com`).
- **Repository root file references**:
  - When drafting documentation that links to tracked repository root files (e.g., `README.md`, `CONTRIBUTING.md`, `VERSIONING.md`), **always link to the generated copies** under `/project/repo-root/<name>.md`.
  - Example: Link to `/project/repo-root/versioning.md` instead of `/VERSIONING.md` to match MkDocs target paths and avoid later rewrites.
  - These generated files are created by `scripts/sync_root_docs.py` from the repository root originals.
- **Adding new repository root files**:
  - If adding a new file to the repository root that should be surfaced in the documentation (e.g., `VERSIONING.md`), you **must update** `scripts/sync_root_docs.py`:
    1. Add the filename to the `ROOT_DOCS` tuple (lines 64-72).
    2. Add a mapping entry to `ROOT_DOC_DEST_MAP` (lines 74-82) that specifies the kebab-case destination filename.
  - This ensures the file is automatically synced to `/docs/project/repo-root/` during the MkDocs build process.
- Tables should include header separators (`| --- |`) so markdownlint can validate alignment.
- When embedding lists, keep them short and use parallel grammar. Use numbered lists only when order matters.
- Reference other documents via their kebab-case paths (matching the naming rule).
- **Directory links**: MkDocs resolves pages, not bare folders. Do not link to a directory path (`[Architecture](/architecture/index.md)`). Instead:
  - Link to a specific page (e.g., `[Architecture Overview](/architecture/overview.md)`), or
  - Add an `index.md` in that directory and link to it (`/architecture/index.md`).
  - `README.md` inside a folder is *not* treated as a landing page by MkDocs; prefer `index.md` for folder entry points.

## Linting & Automation

- We standardize on [`markdownlint`](https://github.com/DavidAnson/markdownlint). Add a `.markdownlint.json` configuration (future task) and run `npx markdownlint '**/*.md'` (or the Make target) locally.
- CI must run markdownlint alongside MkDocs builds; documentation PRs fail if lint errors remain.
- Documentation tooling (e.g., `documentation_index.md`) assumes compliant front matter and headings—if a file deviates, the generator will flag it. Regenerate the index with `scripts/generate_doc_index.py`; the script writes `auto_generated: true` into the front matter so downstream tooling knows not to edit it manually.
- The repo-wide `.markdownlint.json` disables MD025 ("multiple top-level headings") and MD013 (line length) because front matter + title duplication and long tables are intentional.

## Historical References Pattern

When documenting superseded designs, archived ADRs, or earlier explorations, use the "Historical References" pattern to provide progressive disclosure of archived content:

```markdown
---

## Historical References

<details>
<summary>📚 View superseded design documents (maintainers/contributors)</summary>

**Note**: These documents are archived and excluded from the published documentation. They provide historical context for the current design.

### Superseded ADRs

- **[ADR-XX: Title](<docs-absolute-path>/archive/adr/adr-xx-title.md)** (YYYY-MM-DD)
  *Status*: Superseded by [ADR-YY](/path/to/current-adr.md)

### Earlier Design Explorations

- **[Design Doc Title](<docs-absolute-path>/archive/design-doc.md)** (YYYY-MM-DD)
  *Status*: Replaced by [Current Doc](/path/to/current-doc.md)

</details>
```

**When to use**:

- Current ADR supersedes archived ADRs
- Design documents replace earlier explorations
- Implementation supersedes prototypes
- Providing historical context adds value for contributors

**Benefits**:

- Archive links work in GitHub/IDE even when excluded from MkDocs build
- `<details>` tags render in both MkDocs and GitHub
- Progressive disclosure keeps published docs clean for users
- Maintainers can access historical context via repository

**See also**: [ADR-DD01 Addendum 4: Archive Linking Pattern](/architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md#addendum-4-archive-linking-pattern-2025-12-11)

## Exceptions & Legacy Content

- During the archive migration, some historical files may temporarily violate the standards. Tag them with `status: historical` and move them under `docs/archive/`.
- When editing legacy docs, clean up the formatting to meet the standard where practical instead of propagating exceptions.

Following these standards keeps the documentation approachable for humans and structured for the automation we depend on.
