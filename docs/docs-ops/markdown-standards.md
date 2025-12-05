---
title: "Markdown Standards"
description: "House style, linting, and structure requirements for TNH Scholar documentation."
owner: ""
author: ""
status: processing
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

All Markdown files must start with YAML front matter so the doc tooling can build the global index:

```yaml
---
title: "Human-readable Title"
description: "One-sentence summary"
owner: ""
author: ""
status: processing
created: "YYYY-MM-DD"
---
```

- `title` and `description` should match the real content (not just repeat headings).
- `owner` may remain blank while we have a single maintainer but should be populated when an area gains ownership.
- `author` records provenance (person, tool, or AI agent responsible for the initial version of the document). Use a short identifier or comma-separated list when multiple authors collaborate.
- `status` tracks lifecycle (`processing`, `draft`, `current`, `archived`, etc.).
- `created` reflects the original commit date when possible (auto-filled by tooling).
- **Prompt Template Exception**: files in `patterns/` (soon living under `docs/prompt-templates/`) use a prompt-specific front matter schema that includes runtime variables and other metadata. Continue using that specialized format until the Prompt Template standard is finalized (TBD); do **not** remodel those files to the generic doc front matter without an explicit migration plan.

## Heading & Summary Rules

- Immediately after front matter, include a `# Title` heading that **exactly matches** the YAML `title` field (character-for-character, including punctuation and capitalization).
- Follow the heading with a one-sentence or single-paragraph description that orients the reader. This description should expand on or clarify the `description` field from front matter. ADRs and reference docs must comply even if they also list metadata (Status, Date, Owner) right after the summary.
- Use hierarchical headings (`##`, `###`, etc.) without skipping levels. Avoid deep nesting beyond `####`.
- **Validation**: A linting script (`scripts/validate_titles.py`) will verify YAML `title` matches `# Heading` exactly. CI will warn (but not fail) on mismatches until all legacy docs are updated.

## ADR Format

- Store ADRs under module directories such as `docs/architecture/<module>/adr/` (legacy ADRs move there during the restructure).
- File naming convention: `adr-<modulecode><number>-<descriptor>.md`, all lowercase, hyphen-separated (e.g., `adr-dd01-docs-reorg-strat.md``adr-kb02-knowledge-store.md`). Strategy ADRs append `-strat` to the descriptor (`adr-dd01-docs-reorg-strat.md`) so higher-level directional docs are easy to spot.
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
- Prefer relative links (`[Getting Started](/getting-started/installation.md)`) over absolute URLs inside the repo.
- Tables should include header separators (`| --- |`) so markdownlint can validate alignment.
- When embedding lists, keep them short and use parallel grammar. Use numbered lists only when order matters.
- Reference other documents via their kebab-case paths (matching the naming rule).
- **Directory links**: MkDocs resolves pages, not bare folders. Do not link to a directory path (`[Architecture](architecture/)`). Instead:
  - Link to a specific page (e.g., `[Architecture Overview](architecture/overview.md)`), or
  - Add an `index.md` in that directory and link to it (`architecture/index.md`).
  - `README.md` inside a folder is *not* treated as a landing page by MkDocs; prefer `index.md` for folder entry points.

## Linting & Automation

- We standardize on [`markdownlint`](https://github.com/DavidAnson/markdownlint). Add a `.markdownlint.json` configuration (future task) and run `npx markdownlint '**/*.md'` (or the Make target) locally.
- CI must run markdownlint alongside MkDocs builds; documentation PRs fail if lint errors remain.
- Documentation tooling (e.g., `documentation_index.md`) assumes compliant front matter and headings—if a file deviates, the generator will flag it. Regenerate the index with `scripts/generate_doc_index.py`; the script writes `auto_generated: true` into the front matter so downstream tooling knows not to edit it manually.
- The repo-wide `.markdownlint.json` disables MD025 ("multiple top-level headings") and MD013 (line length) because front matter + title duplication and long tables are intentional.

## Exceptions & Legacy Content

- During the archive migration, some historical files may temporarily violate the standards. Tag them with `status: historical` and move them under `docs/archive/`.
- When editing legacy docs, clean up the formatting to meet the standard where practical instead of propagating exceptions.

Following these standards keeps the documentation approachable for humans and structured for the automation we depend on.
