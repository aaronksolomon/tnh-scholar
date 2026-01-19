# AGENTLOG

This file captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. It provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

See AGENTLOG_TEMPLATE.md for structure and format.

**Archive**: Older sessions are archived in [`archive/agentlogs/`](archive/agentlogs/) with a summary index at [`archive/agentlogs/archive-index.md`](archive/agentlogs/archive-index.md).

**Ordering**: Append new records at the end (chronological order from least to most recent).

---
## 2026-01-17

### Summary
- Renamed repo prompt templates directory to `prompts/`, updated default prompt dir/env var wiring to `TNH_PROMPT_DIR`, and aligned CLI/tooling/tests/docs.
- Ran targeted GenAI service tests via `poetry run pytest` for prompt-dir changes; all passed.
- Removed obsolete `gen_ai_service/runtime_assets/patterns` scaffolding and .keep files after confirming no ADR references.
- Verified GenAI ADRs only reference runtime registry/policy assets, not prompt assets under gen_ai_service.

---
## 2026-01-18

### Summary
- Reviewed patterns→prompts restructuring work completed on 2026-01-17
- Applied minor consistency fixes to complete the terminology migration

### Changes Made
- **tnh-setup CLI flag rename**: Changed `--skip-patterns` to `--skip-prompts` in `src/tnh_scholar/cli_tools/tnh_setup/tnh_setup.py`
- **Comment update**: Updated comment in `src/tnh_scholar/cli_tools/tnh_fab/tnh_fab.py` from "Default pattern directory" to "Default prompt directory"
- **Documentation updates**: Updated `--skip-patterns` → `--skip-prompts` in:
  - `docs/cli-reference/tnh-setup.md`
  - `docs/getting-started/configuration.md`

### Review Notes
The patterns→prompts migration is now complete with consistent terminology across:
- Core constants (`TNH_DEFAULT_PROMPT_DIR`)
- Environment variables (`TNH_PROMPT_DIR`)
- CLI flags (`--skip-prompts`)
- Function names (`download_prompts()`)
- Documentation

**Breaking change noted**: `TNH_PATTERN_DIR` env var no longer accepted in `GenAISettings` - users with existing `.env` files using this variable will silently fall back to defaults. Consider documenting in release notes.
