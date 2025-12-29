# AGENTS.md  

CRITICAL CONTEXT FOR CODE AGENTS

> THIS DOCUMENT MUST REMAIN MINIMAL AND TERSE -> context window preserving

**TNH Scholar** - AI toolkit for Thích Nhất Hạnh teachings. Alpha v0.2.2, rapid prototype phase.

**Bootstrap Goal:** VS Code integration (tnh-gen CLI) enables AI-assisted dev of TNH Scholar itself—code agents accelerate the project.



## Architecture - Object-Service Pattern (MANDATORY)

**ADR-OS01** - Layered design for all GenAI code:

```
Domain Layer:    Protocols (abstract), Service orchestrators
Infrastructure:  Adapters (SDK↔domain), Transport clients
```

**Rules:**
- Strong typing (Pydantic models), NO dicts/literals in app logic
- Bi-directional mappers for type translation
- Config taxonomy: Settings (env) → Config (init) → Params (per-call) → Policy (behavior)
- Config-at-init, params-per-call pattern

**Example Structure:**
```
gen_ai_service/
  protocols.py    # GenAIServiceProtocol, PromptCatalogProtocol
  service.py      # Main orchestrator
  adapters/       # Provider implementations
  mappers/        # Type translation
  models/         # Domain models
  providers/      # Transport layer
```

## Key Constraints

**Versioning:** 0.x allows breaking changes in ANY release (patch/minor). No backward compat shims. Clean breaks preferred.

**Doc Links (CRITICAL):**
- Source refs: `` `src/file.py:42` `` (inline code, NOT markdown links)
- Doc cross-refs: `/architecture/adr/...` (absolute paths from `/docs`, NOT relative `../`)
- Prevents MkDocs warnings

**Pre-commit:** DISABLED (`core.hookspath=/dev/null`). No auto-stash concerns.

**Git Safety:** User approval required for destructive ops (reset, force push, rebase, branch delete).

## Design Standards (CRITICAL)

**Before any change:** Ask "Does this need a class?" Don't patch—refactor toward proper abstractions.

**Architectural discipline:**

- **Favor encapsulation over procedural sprawl** - New behavior → new class/protocol, NOT longer functions
- **Composition over ad-hoc helpers** - Assemble objects, don't chain functions
- **Extract collaborators early** - If logic grows, extract a typed service/strategy object
- **Single Responsibility** - One class/function, one concern. Refactor when dual-purpose detected
- **High cohesion, loose coupling** - Related data/behavior groups into classes; minimize cross-dependencies

**Anti-patterns to avoid:**

- Long functions (>20 LOC) - extract methods or introduce coordinator class
- Procedural scripts masquerading as modules - OOP-first mindset
- Feature additions without structural review - always assess if architecture needs evolution

**See:** [Design principles](/development/design-principles.md) for composition patterns, separation of concerns.

## Style & Conventions

**Python:** 3.12.4, PEP 8, Google docstrings. [Full style guide](/development/style-guide.md).

**Critical rules:**

- Absolute imports (`tnh_scholar.module`), NOT relative (`..module`)
- NO module-level constants—use `@dataclass(frozen=True)` or `str` Enum
- NO literals/dicts in app logic—Pydantic models, typed classes, enums only
- Early returns, `match`/`case` for 3+ conditions
- Functions ≤20 LOC, cyclomatic complexity ≤9
- `Protocol` for interfaces (no inheritance), `ABC` only for shared mixins

**Docs:** Kebab-case filenames, YAML front matter required, absolute links only. [Markdown standards](/docs-ops/markdown-standards.md).

## CLI Tools

**tnh-gen** (NEW, replaces tnh-fab):
- Typer-based, protocol-driven
- Dual modes: human (default), `--api` (JSON)
- Commands: `list`, `run`, `config`, `version`

Others: `audio-transcribe`, `ytt-fetch`, `token-count`, `nfmt`

## Dev Workflow

```bash
make setup-dev    # pyenv 3.12.4 + poetry + dev deps (non-optional)
make test         # pytest
make lint         # ruff check
make format       # ruff format
poetry run mypy src/
make docs-verify  # MkDocs strict + validation
```

**CI/CD:** GitHub Actions, all deps non-optional, 210 tests passing.

## Prompt System

- Jinja2 templates in `~/.config/tnh_scholar/patterns/`
- Git-versioned, legacy "Pattern" → "Prompt" rename in progress
- Current: LocalPatternManager singleton (prototype)
- Future: DI PromptCatalog

## Source Structure

```
src/tnh_scholar/
  gen_ai_service/       # Object-service GenAI
  prompt_system/        # Jinja2 prompts
  ai_text_processing/   # Text pipelines
  cli_tools/            # CLI entry points
  audio_processing/     # Transcription
  utils/                # Shared
```

## Critical Gotchas

1. **Breaking changes OK in 0.x patches** - no compatibility guarantees
2. **Object-service mandatory** for GenAI code - no shortcuts
3. **Pydantic required** - strong typing, no dict/literal sprawl
4. **Commit poetry.lock** - always include lockfile changes
5. **ADRs append-only** - never edit decisions, add addendums
6. **ADR status lifecycle** - When implementing "accepted" ADRs, update status: `proposed` → `accepted` → `implemented`. Check code exists before marking TODO items as "in progress"

## Docs Structure

**Organized by purpose:**

```text
docs/
  architecture/        # ADRs by module (object-service, tnh-gen, etc)
  development/         # Dev guides, style, design principles
  cli-reference/       # Tool-specific comprehensive docs
  docs-ops/            # Meta: markdown standards, ADR templates
  project/             # Vision, principles, repo-root files
```

**Intentions:** MkDocs strict mode, auto-generated indexes, progressive disclosure (collapsible archive refs). All docs have YAML front matter (title, description, status, created).

**See:** [Development overview](/development/overview.md), [Markdown standards](/docs-ops/markdown-standards.md).

## Agent Task Types

**You'll be asked to do two kinds of work:**

1. **Design & Documentation** - Write ADRs, design docs, architecture analysis
   - Use ADR template: `docs/docs-ops/adr-template.md`
   - Start with high-level design: `docs/development/system-design.md` (cyclical AI processing architecture)
   - Review architecture map: `docs/architecture/overview.md` (subsystem directory guide)
   - Follow markdown standards for all doc creation

2. **Implementation** - Execute ADRs, implement features, refactor code
   - Read relevant ADR first (always linked or specified)
   - Follow object-service pattern for GenAI code (ADR-OS01)
   - Apply design standards (encapsulation, composition, extraction)
   - Update CHANGELOG.md, AGENTLOG.md, TODO.md after commits, before push

**For both:** Proactive architectural thinking. Don't patch—design properly, then implement.

## Critical Reading (Start Here)

**Must read (implementation):**

- `docs/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md` - **MANDATORY pattern for all GenAI code**
- `docs/development/design-principles.md` - Core design philosophy
- `docs/development/style-guide.md` - Python conventions

**Must read (design work):**

- `docs/development/system-design.md` - High-level cyclical AI architecture
- `docs/architecture/overview.md` - Subsystem map and architecture diagrams
- `docs/docs-ops/adr-template.md` - ADR structure and format

**Context:**

- `docs/development/overview.md` - Dev doc landing page
- `docs/cli-reference/tnh-gen.md` - tnh-gen comprehensive reference

## Current Branch Context (docs-testing/tnh-gen)

**Focus:** Documentation improvements - tnh-gen CLI reference (661 lines), surfaced versioning policy, fixed markdown validation, made dev deps non-optional.

---

**For session continuity:** Read ADR-OS01 (object-service pattern—MANDATORY), design-principles.md, style-guide.md. Strong types, no literals/dicts, absolute doc links, user confirms git destructive ops.
