# Agent Session Log

This file captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. It provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

*See AGENTLOG_TEMPLATE.md for template.*

---

## Session History (Most Recent First)

<!-- Add new sessions here following the template format -->

## 2026-01-01 11:30 PST JSONC Parser Hardening + Tests

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: "jsonc-parser-hardening"
**Human Collaborator**: phapman

### Context
User requested Sourcery comment fixes, targeted tests for JSONC parsing, and full test run.

### Key Decisions
- **Stateful parsing**: Replaced regex-based trailing comma removal with a string-aware scan.
- **Strict error handling**: Unterminated block comments or strings now raise errors with line/column.
- **Test resilience**: Token count comparison tolerates fallback encoding.

### Work Completed
- [x] Refactored JSONC parser to use a tracked scan state with safe comment and comma handling (file: `src/tnh_scholar/gen_ai_service/adapters/registry/jsonc_parser.py`)
- [x] Added JSONC parser tests for comment tokens inside strings, unterminated comments, and trailing commas (file: `tests/gen_ai_service/adapters/registry/test_jsonc_parser.py`)
- [x] Adjusted token count model comparison test to tolerate fallback encoding (file: `tests/gen_ai_service/utils/test_token_utils.py`)
- [x] Ran full test suite (`make test`)

### Files Modified/Created
- `src/tnh_scholar/gen_ai_service/adapters/registry/jsonc_parser.py`: Added stateful scanning, line/column tracking, and strict error handling.
- `tests/gen_ai_service/adapters/registry/test_jsonc_parser.py`: New JSONC parser tests.
- `tests/gen_ai_service/utils/test_token_utils.py`: Token count comparison now accounts for fallback encoding.

### Tests
- `make test`

## 2026-01-01 11:05 PST ADR-A14 Implementation: Test Fix + Doc Sync

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: "adr-a14-implementation"
**Human Collaborator**: phapman

### Context
User requested full test run and documentation updates after registry/staleness changes.

### Key Decisions
- **Registry-backed test model**: Swapped to an existing registry model (`gpt-5-mini`) to avoid stale test fixtures.
- **ADR alignment**: Documented staleness settings fields and corrected ADR-A14 addendum link.

### Work Completed
- [x] Updated GPT-5 family token util test to use a registry-backed model (file: `tests/gen_ai_service/utils/test_token_utils.py`)
- [x] Documented staleness settings fields and fixed ADR-A14.1 link (file: `docs/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md`)
- [x] Ran full test suite (`make test`)

### Files Modified/Created
- `tests/gen_ai_service/utils/test_token_utils.py`: Adjusted model name to `gpt-5-mini`.
- `docs/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md`: Added staleness settings note and corrected addendum link.

### Tests
- `make test`

## 2026-01-01 10:50 PST ADR-A14 Implementation: Registry Tiers & Tests

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: "adr-a14-implementation"
**Human Collaborator**: phapman

### Context
User requested test runs and adjustments for pricing tiers, including parser fixes and schema updates.

### Key Decisions
- **Tiered Pricing Support**: Registry models and schema updated to support pricing tiers and tier metadata.
- **Robust JSONC Parsing**: Comment stripping updated to respect string literals (e.g., URLs).

### Work Completed
- [x] Fixed JSONC parser to avoid stripping comment markers inside strings and added missing regex import (files: `src/tnh_scholar/gen_ai_service/adapters/registry/jsonc_parser.py`)
- [x] Added tier-aware pricing flow in safety gate and aligned registry tests (files: `src/tnh_scholar/gen_ai_service/safety/safety_gate.py`, `tests/gen_ai_service/test_registry_loader.py`)
- [x] Extended registry schema and sample registry with pricing tier metadata (files: `src/tnh_scholar/runtime_assets/registries/providers/schema.json`, `src/tnh_scholar/runtime_assets/registries/providers/openai.jsonc`)
- [x] Added focused tier metadata test (files: `tests/gen_ai_service/test_registry_tier_metadata.py`)
- [x] Hardened token_utils to fall back when tiktoken cannot fetch encodings (files: `src/tnh_scholar/gen_ai_service/utils/token_utils.py`)
- [x] Added ProviderRegistry `$schema` alias handling for JSONC schema references (files: `src/tnh_scholar/gen_ai_service/models/registry.py`)

### Discoveries & Insights
- **Parser Greediness**: Naive `//` stripping breaks JSON strings with URLs; parser now handles string literals.
- **Network-Restricted Tiktoken**: Encoding downloads can fail offline; fallback keeps tests stable.

### Files Modified/Created
- `src/tnh_scholar/gen_ai_service/adapters/registry/jsonc_parser.py`: Improved JSONC comment handling and fixed imports.
- `src/tnh_scholar/gen_ai_service/safety/safety_gate.py`: Tier-aware pricing resolution.
- `src/tnh_scholar/gen_ai_service/utils/token_utils.py`: Fallback when tiktoken encoding fetch fails.
- `src/tnh_scholar/gen_ai_service/models/registry.py`: Added pricing tier metadata and `$schema` alias handling.
- `src/tnh_scholar/runtime_assets/registries/providers/schema.json`: Added pricing tier metadata schema.
- `src/tnh_scholar/runtime_assets/registries/providers/openai.jsonc`: Added tier metadata entries.
- `tests/gen_ai_service/test_registry_loader.py`: Updated for pricing tiers.
- `tests/gen_ai_service/test_registry_tier_metadata.py`: Added tier metadata test.

### Next Steps
- [ ] Consider adding tier metadata to other provider registries as they are added.

### Open Questions
- Should tier metadata be optional for providers, or required when `pricing_tier` is set?

### References
- /architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md
- /architecture/gen-ai-service/adr/adr-a14.1-registry-staleness-detection.md

## 2026-01-01 10:02 PST ADR-A14 Implementation Kickoff

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: "adr-a14-implementation"
**Human Collaborator**: phapman

### Context
User requested review and alignment of ADR-CF01 runtime context strategy and ADR-A14 registry design, then asked to begin implementing ADR-A14.

### Key Decisions
- **TNHContext-First Registry Discovery**: Registry loader resolves provider/override paths via TNHContext (workspace → user → built-in) per ADR-CF01.
- **No Protocol for V1**: Registry loader remains concrete with injected collaborators for parsing/merging; protocol abstraction deferred.
- **User-Facing Path Convention**: `tnh-scholar` used for user config directories; underscores reserved for Python package names.

### Work Completed
- [x] Aligned ADR-CF01 with user-facing naming, built-in asset migration notes, and ADR-PP01 breaking-change policy (files: `docs/architecture/configuration/adr/adr-cf01-runtime-context-strategy.md`)
- [x] Conformed ADR-A14 to TNHContext path strategy and layered precedence (files: `docs/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md`)
- [x] Added registry domain models, JSONC parsing, override merging, and loader wired to TNHContext (files: `src/tnh_scholar/gen_ai_service/models/registry.py`, `src/tnh_scholar/gen_ai_service/adapters/registry/jsonc_parser.py`, `src/tnh_scholar/gen_ai_service/adapters/registry/override_merger.py`, `src/tnh_scholar/gen_ai_service/config/registry.py`, `src/tnh_scholar/configuration/context.py`)
- [x] Added built-in registry assets and schema plus package include (files: `src/tnh_scholar/runtime_assets/registries/providers/openai.jsonc`, `src/tnh_scholar/runtime_assets/registries/providers/schema.json`, `src/tnh_scholar/runtime_assets/registries/.registry-metadata.json`, `pyproject.toml`)
- [x] Updated GenAIService integrations to read registry for capabilities, context limits, and pricing (files: `src/tnh_scholar/gen_ai_service/routing/model_router.py`, `src/tnh_scholar/gen_ai_service/safety/safety_gate.py`, `src/tnh_scholar/gen_ai_service/utils/token_utils.py`, `src/tnh_scholar/gen_ai_service/config/settings.py`)
- [x] Added registry loader tests (files: `tests/gen_ai_service/test_registry_loader.py`)
- [x] Added `platformdirs` dependency (files: `pyproject.toml`)

### Discoveries & Insights
- **Asset Packaging Gap**: `runtime_assets/` not present yet; ADR-CF01 notes current repo-root assets and planned migration.
- **Registry Path Clarity**: Workspace/user layering eliminates prior ambiguity around overrides and registry roots.

### Files Modified/Created
- `docs/architecture/configuration/adr/adr-cf01-runtime-context-strategy.md`: Clarified user path naming, asset migration notes, and ADR-PP01 breaking-change policy.
- `docs/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md`: Aligned registry discovery/precedence with TNHContext.
- `src/tnh_scholar/configuration/context.py`: Created TNHContext, discovery, and path resolution helpers.
- `src/tnh_scholar/gen_ai_service/config/registry.py`: Created registry loader and APIs.
- `src/tnh_scholar/gen_ai_service/models/registry.py`: Created registry Pydantic models and override schemas.
- `src/tnh_scholar/gen_ai_service/adapters/registry/jsonc_parser.py`: Created JSONC parser.
- `src/tnh_scholar/gen_ai_service/adapters/registry/override_merger.py`: Created override merge service.
- `src/tnh_scholar/runtime_assets/registries/providers/openai.jsonc`: Created initial provider registry.
- `src/tnh_scholar/runtime_assets/registries/providers/schema.json`: Added JSON schema.
- `src/tnh_scholar/runtime_assets/registries/.registry-metadata.json`: Added metadata stub.
- `src/tnh_scholar/gen_ai_service/routing/model_router.py`: Switched routing capability checks to registry.
- `src/tnh_scholar/gen_ai_service/safety/safety_gate.py`: Switched context/cost checks to registry pricing/limits.
- `src/tnh_scholar/gen_ai_service/utils/token_utils.py`: Switched context-limit resolution to registry lookup.
- `src/tnh_scholar/gen_ai_service/config/settings.py`: Removed hardcoded limits and pricing; validate via registry.
- `tests/gen_ai_service/test_registry_loader.py`: Added registry loader tests.
- `pyproject.toml`: Added `platformdirs` and runtime_assets include.

### Next Steps
- [ ] Update `poetry.lock` after adding `platformdirs`.
- [ ] Run targeted tests (`tests/gen_ai_service/test_registry_loader.py`, `tests/gen_ai_service/test_policy_routing_safety.py`).
- [ ] Confirm pricing and model data in `openai.jsonc`.

### Open Questions
- Should additional built-in assets (beyond `patterns/`) be migrated into `runtime_assets/` now or later?
- Do we want provider-specific override files in workspace/user layers to be optional for every provider by default?

### References
- /architecture/configuration/adr/adr-cf01-runtime-context-strategy.md
- /architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md
- /architecture/project-policies/adr/adr-pp01-rapid-prototype-versioning.md

---

## Archive

Previous agent session logs are archived in `archive/agentlogs/`:

- [AGENTLOG-12-31-25.md](archive/agentlogs/AGENTLOG-12-23-31.md) - 
- [AGENTLOG-12-23-25.md](archive/agentlogs/AGENTLOG-12-23-25.md) - Post-merge hotfix, tnh-gen legacy compatibility, architecture improvements
- [AGENTLOG-12-13-25.md](archive/agentlogs/AGENTLOG-12-13-25.md) - TextObject robustness, ADR-AT03 series implementation
- [AGENTLOG-12-11-25.md](archive/agentlogs/AGENTLOG-12-11-25.md) - tnh-fab deprecation, documentation updates
- [AGENTLOG-12-10-25.md](archive/agentlogs/AGENTLOG-12-10-25.md) - GenAI service implementation, test coverage
- [AGENTLOG-12-07-25.md](archive/agentlogs/AGENTLOG-12-07-25.md) - Early project work, architecture foundations
