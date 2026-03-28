---
title: "AGENTS.md"
description: "Critical context for code agents working on TNH Scholar."
owner: ""
author: "aaronksolomon, Claude Sonnet 4.5"
status: current
created: "2025-12-07"
updated: "2026-03-25"
---
# AGENTS.md

Agent brief for TNH Scholar. Keep this file terse. For rationale, recovery, and detailed git mechanics, see [docs/development/git-workflow.md](docs/development/git-workflow.md).

## Read First

- [docs/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md](docs/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)
- [docs/development/design-principles.md](docs/development/design-principles.md)
- [docs/development/style-guide.md](docs/development/style-guide.md)

## Architecture

ADR-OS01 is mandatory for GenAI code:

```text
Domain Layer:    Protocols (abstract), Service orchestrators
Infrastructure:  Adapters (SDK↔domain), Transport clients
```

Rules:

- Strong typing with Pydantic models
- No dict/literal sprawl in app logic
- Bi-directional mappers for type translation
- Config taxonomy: Settings -> Config -> Params -> Policy
- Config-at-init, params-per-call
- New behavior should trigger structural review, not patch growth

## Coding Rules

- Python 3.12.4, PEP 8, Google docstrings
- Absolute imports only
- Prefer `Protocol`; use `ABC` only for shared mixins
- No module-level constants; use `@dataclass(frozen=True)` or `str` `Enum`
- Early returns; use `match`/`case` for 3+ conditions
- Functions target `<=20` LOC; cyclomatic complexity target `<=9`
- Favor encapsulation, composition, and extraction over procedural sprawl

## Doc Rules

- Source refs: `` `src/file.py:42` ``
- Doc cross-refs: absolute paths from `/docs`
- Repo-root docs: use generated docs paths such as `/project/repo-root/repo-readme.md` or `/project/repo-root/versioning.md`
- Markdown files: kebab-case, YAML front matter, absolute links only

## Git Rules

- Versioning is `0.x`: breaking changes are allowed; prefer clean breaks
- Pre-commit hooks are disabled: `core.hookspath=/dev/null`
- `git rebase` and `git push --force-with-lease` require full confirmation protocol: explain the operation, show exact commands, state consequences and risks, explain recovery, then wait for explicit "yes"
- Forbidden entirely (user-only, never AI): `reset --hard/soft/mixed`, `push --force`, `branch -D`, `clean -fd`, `checkout -- .`, `restore` with destructive flags, `filter-branch`
- NEVER stash untracked files; commit them to a temp branch if needed
- Commit `poetry.lock` when dependency changes require it

## Workflow

Core commands:

```bash
make pr-check
make ci-check
poetry install --with local
poetry run sourcery review <paths> 2>&1
```

Default PR flow:
- `main -> feat/<slice> -> PR -> merge`
- Run `make pr-check` before opening a PR
- Preferred diff size: `<120k` chars
- Caution: `120k-150k`
- Split required: `>=150k`
- Run the changed-file checks suggested by `make pr-check`
- Run `make ci-check` before PR creation
- Update `CHANGELOG.md` and `TODO.md` after commits, before push
- Stacked PRs/worktrees are optional, only for true dependency chains
- Sourcery GitHub review still requires normal PR/human review after PR creation

## Repo-Specific Rules

1. Breaking changes are fine in `0.x`
2. Object-service is mandatory for GenAI code
3. Pydantic typing is required
4. ADRs are append-only; add addendums, do not rewrite decisions
5. ADR status lifecycle matters; see [docs/docs-ops/adr-template.md](docs/docs-ops/adr-template.md) for template and lifecycle rules
6. After a merged substantive PR, append an entry to `AGENTLOG.md` (format: `AGENTLOG_TEMPLATE.md`). When the file grows large: copy to `archive/agentlogs/AGENTLOG-[MM-DD-YY].md`, add a one-line summary to `archive/agentlogs/archive-index.md`, then reset `AGENTLOG.md` to an empty log with an archive reference line

## Docs and Context

- Design/docs work: use [docs/docs-ops/adr-template.md](docs/docs-ops/adr-template.md)
- System context: [docs/development/system-design.md](docs/development/system-design.md)
- Architecture map: [docs/architecture/overview.md](docs/architecture/overview.md)
- Active priorities: `TODO.md`
- Recent session continuity: `AGENTLOG.md`
