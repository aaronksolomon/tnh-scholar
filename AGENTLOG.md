# AGENTLOG

This file captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. It provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

See [AGENTLOG_TEMPLATE.md](AGENTLOG_TEMPLATE.md) for structure and format.

**Archive**: Older sessions are archived in [`archive/agentlogs/`](archive/agentlogs/) with a summary index at [`archive/agentlogs/archive-index.md`](archive/agentlogs/archive-index.md).
Archived previous active log: [`archive/agentlogs/AGENTLOG-03-28-26.md`](archive/agentlogs/AGENTLOG-03-28-26.md).

**Ordering**: Append new records at the end (chronological order from least to most recent).

---

## [2026-03-28 20:53 PDT] OA04.3 Run-Artifact Contract First Coding Pass

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: oa04-pr-series-build-sequence
**Human Collaborator**: phapman

### Context
Started the OA04 contract-family implementation sequence from `main` after the OA04 ADR set was locked down and the TODO plan was updated. The first coding slice targeted PR-2, `feat/oa04.3-run-artifact-contract`, with scope limited to the maintained run-artifact contract/store layer and only the minimum kernel compatibility updates required by that contract.

### Key Decisions
- **Start with PR-2, not PR-1**: PR-1 was already effectively represented by the docs-only OA04 acceptance commit on `main`, so coding began with the first implementation slice in TODO order.
- **Keep PR-2 scoped to contract/store work**: expand `run_artifacts/` and add only the minimum kernel compatibility needed for richer metadata/event persistence, while deferring manifest-writing and fuller provenance assembly to PR-3.
- **Treat ADR-OA04.3 as authoritative for `artifacts_root`**: persist the configured parent run-artifact directory, not the per-run `artifacts/` subtree.
- **Preserve typed schema tokens**: keep uppercase `Opcode` values because they are the canonical OA04 workflow DSL tokens, while runtime status enums remain lowercase.
- **Narrow the persistence boundary**: remove arbitrary write methods from the maintained run-artifact protocol and keep canonical persistence role-based.

### Work Completed
- [x] Reviewed repo-local agent instructions, OS01 architecture guidance, design principles, style guide, OA04 ADR set, TODO implementation plan, system-design context, and recent AGENTLOG continuity before coding (files: `AGENTS.md`, `docs/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md`, `docs/development/design-principles.md`, `docs/development/style-guide.md`, `docs/architecture/agent-orchestration/adr/adr-oa04*.md`, `TODO.md`, `docs/architecture/agent-orchestration/system-design.md`, `AGENTLOG.md`)
- [x] Created the implementation branch for the first OA04.3 code slice (branch: `feat/oa04.3-run-artifact-contract`)
- [x] Expanded maintained run-artifact domain models for OA04.3, including canonical artifact roles, event types, evidence summaries, step artifact entries, manifests, and richer run metadata (files: `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`)
- [x] Expanded the maintained run-artifact protocol and filesystem store for step directories, final-state persistence, manifest persistence, and role-based text/JSON artifact writing (files: `src/tnh_scholar/agent_orchestration/run_artifacts/protocols.py`, `src/tnh_scholar/agent_orchestration/run_artifacts/filesystem_store.py`, `src/tnh_scholar/agent_orchestration/run_artifacts/__init__.py`)
- [x] Updated the maintained kernel only where required for the new contract, including richer run metadata, canonical event records, typed `Opcode.stop` usage, and removal of the prior `STOP_STEP_ID` module constant (files: `src/tnh_scholar/agent_orchestration/kernel/enums.py`, `src/tnh_scholar/agent_orchestration/kernel/models.py`, `src/tnh_scholar/agent_orchestration/kernel/service.py`, `src/tnh_scholar/agent_orchestration/kernel/catalog.py`, `src/tnh_scholar/agent_orchestration/kernel/validator.py`, `src/tnh_scholar/agent_orchestration/kernel/__init__.py`)
- [x] Added focused OA04.3 run-artifact contract tests and updated maintained OA07 kernel tests for the new event shape and role-based artifact writing (files: `tests/agent_orchestration/test_run_artifacts_contract.py`, `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`)
- [x] Performed a review/fix pass after independent feedback, tightening `artifacts_root`, typed contract fields, and the run-artifact persistence boundary without expanding into PR-3 scope.

### Discoveries & Insights
- **PR-1 is effectively landed already**: the accepted OA04 ADR family and TODO sequencing are already on `main`, so the first meaningful implementation branch is the OA04.3 contract/store slice.
- **`artifacts_root` semantics are easy to misread**: the ADR defines it as the configured parent root (for example `.tnh/run/`), while step artifacts still belong under the per-run `artifacts/` subtree.
- **Typed enum reuse across subsystems can create import cycles**: sharing kernel enums with run-artifact models required extracting them into a small dedicated `kernel/enums.py` module to preserve strong typing cleanly.
- **Uppercase opcode values are intentional schema tokens**: they mirror the OA04 workflow document syntax and should not be normalized to match lowercase runtime status enums.

### Files Modified/Created
- `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`: Expanded OA04.3 run metadata, event, artifact, evidence, and manifest models.
- `src/tnh_scholar/agent_orchestration/run_artifacts/protocols.py`: Reworked maintained artifact-store protocol toward canonical role-based persistence.
- `src/tnh_scholar/agent_orchestration/run_artifacts/filesystem_store.py`: Implemented run root/artifact directory separation, final-state persistence, manifest writing, and canonical artifact writes.
- `src/tnh_scholar/agent_orchestration/run_artifacts/__init__.py`: Exported maintained run-artifact surface including the store protocol.
- `src/tnh_scholar/agent_orchestration/kernel/enums.py`: New shared enum module for kernel schema/runtime enums.
- `src/tnh_scholar/agent_orchestration/kernel/models.py`: Removed local enum definitions and `STOP_STEP_ID`; retained typed workflow models against shared enums.
- `src/tnh_scholar/agent_orchestration/kernel/service.py`: Updated run metadata/event persistence and final-state writing for the maintained OA04.3 contract.
- `src/tnh_scholar/agent_orchestration/kernel/catalog.py`: Updated STOP handling to use typed opcode value and tightened route typing.
- `src/tnh_scholar/agent_orchestration/kernel/validator.py`: Updated STOP handling to use typed opcode value.
- `src/tnh_scholar/agent_orchestration/kernel/__init__.py`: Re-exported shared kernel enums cleanly after enum extraction.
- `tests/agent_orchestration/test_run_artifacts_contract.py`: Added direct OA04.3 contract coverage including final-state persistence and BaseModel JSON artifact handling.
- `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`: Updated maintained kernel tests for richer event records and role-based artifact writes.

### Validation Performed
- `poetry run pytest tests/agent_orchestration/test_run_artifacts_contract.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py -q`
- `poetry run ruff check src/tnh_scholar/agent_orchestration/kernel src/tnh_scholar/agent_orchestration/run_artifacts tests/agent_orchestration/test_run_artifacts_contract.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py`
- `poetry run mypy src/tnh_scholar/agent_orchestration/kernel src/tnh_scholar/agent_orchestration/run_artifacts tests/agent_orchestration/test_run_artifacts_contract.py`

### Next Steps
- [ ] Review the current OA04.3 branch diff for any remaining PR-2 scope cleanup before commit.
- [ ] Commit the OA04.3 run-artifact contract slice on `feat/oa04.3-run-artifact-contract`.
- [ ] Begin PR-3 kernel provenance integration only after the PR-2 contract/store slice is considered stable.

### Open Questions
- None in the current OA04.3 contract/store slice after the `artifacts_root` and opcode-style clarifications.

### References
- [docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md](docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- [docs/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md](docs/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md)
- [docs/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md](docs/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
- [TODO.md](TODO.md)

---
