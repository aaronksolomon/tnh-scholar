---
title: "AGENTS.md"
description: "Critical context for code agents working on TNH Scholar."
owner: ""
author: "aaronksolomon, Claude Sonnet 4.5"
status: current
created: "2025-12-07"
updated: "2026-04-26"
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
- Branch and worktree removal require explicit user approval plus a non-loss check: verify merged state or another retained reference before deleting anything
- `git branch -D` is allowed only with explicit user approval plus the same non-loss check used for any branch deletion
- Forbidden entirely (user-only, never AI): `reset --hard/soft/mixed`, `push --force`, `clean -fd`, `checkout -- .`, `restore` with destructive flags, `filter-branch`
- NEVER stash untracked files; commit them to a temp branch if needed
- Commit `poetry.lock` when dependency changes require it

## Workflow

Core commands:

```bash
make branch-preflight
make diff-size
make pr-check
make ci-check
poetry install --with local
poetry run sourcery review <paths> 2>&1
```

Docs-only changes: run `make docs-build` only before PR creation or when the user explicitly requests docs validation. If it passes, push directly to `main` (no PR required during rapid-prototype phase). Do not create new indexes or edit auto generated indexes. Indexes are auto built.

High-level operating stance:
- For higher-order workflow questions, multi-agent coordination, or delegation judgment, see `AGENT_WORKFLOW.md`
- Agent roles are not fixed; use the lightest workflow that is honest about risk
- Validation is local-first; use focused checks for focused changes and broader local validation for higher-risk work
- Treat PR CI as advisory fast signal; use `full-ci` when extra GitHub-side confidence is warranted
- For complex, multi-step, or mission-critical work, agents should consider scoped task distribution or independent review via subagents/assistant agents when available
- Native subagents are preferred when the runtime supports them; repo-local assistant CLIs such as `codex-assistant` and `claude-assistant` are valid bounded-review or bounded-implementation tools when their output can be captured and reviewed
- Delegation should stay scoped and useful: do not offload immediate blocking judgment blindly, and do not treat delegated output as a substitute for final engineering review
- Merge and release judgment remain human-owned; agents inform engineering decisions, they do not replace them

Default PR flow:
- `main -> feat/<slice> -> PR -> merge`
- Run `make branch-preflight` before starting new work
- Run `make diff-size` on an existing branch:
  - before substantial new work
  - before creating a commit
  - before opening a PR
- If branch diff is `>=120k` chars, assess whether to stop and prepare a PR-ready slice
- If branch diff is `>=140k` chars, avoid adding more substantial scope on that branch unless the user explicitly approves exceeding the review-size target
- Do not open a PR from a branch whose intended changes are still partly uncommitted; commit or intentionally separate that work first
- Open a normal PR by default; use a draft PR only when the user explicitly asks for draft status or the work is intentionally not review-ready
- Run `make pr-check` before opening a PR
- Preferred diff size: `<120k` chars
- Caution: `120k-150k`
- Split required: `>=150k`
- Run the changed-file checks suggested by `make pr-check`
- Run `make ci-check` before PR creation
- Do not run `git add`/`git commit` or other index-writing git operations in parallel; `.git/index.lock` races can scramble commit boundaries
- Update `CHANGELOG.md` for substantive changes; update `TODO.md` only when roadmap, priorities, or task status changed
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
