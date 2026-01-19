# AGENTLOG Archive: 2026-01-17 to 2026-01-19

Archived from main AGENTLOG.md on 2026-01-19.

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

---
## 2026-01-19

### Summary
- Removed legacy `tnh-fab` CLI implementation/tests and updated docs/tooling references to `tnh-gen`.
- Repointed `TNH_PROMPT_DIR` to `prompts/`, updated VS Code repo detection settings, and removed the stray `patterns/` directory.
- Repaired the `prompts/` nested repo by recloning `tnh-prompts` and overlaying local prompt files; confirmed it is a standalone git repo.

### Changes Made
- **Code/packaging**: Removed `src/tnh_scholar/cli_tools/tnh_fab/*`, `tests/cli_tools/test_tnh_fab.py`, and the `tnh-fab` script entry in `pyproject.toml`; updated CLI docs in `src/tnh_scholar/cli_tools/__init__.py` and `src/tnh_scholar/__init__.py`.
- **Docs**: Updated references to tnh-fab across user/CLI/architecture docs and simplified examples; refreshed `project_directory_tree.txt` and `src_directory_tree.txt`.
- **Env/config**: Updated `.env` `TNH_PROMPT_DIR` to `.../prompts`; set `.vscode/settings.json` `git.autoRepositoryDetection` to `subFolders` and `git.repositoryScanMaxDepth` to `2`.
- **Prompt repo migration**: Cloned `https://github.com/aaronksolomon/tnh-prompts` into `prompts/`, overlaid local prompt files, and removed the old `patterns/` directory. Backups saved under `/tmp/tnh-prompts-backup-20260118-2128` and `/tmp/tnh-prompts-current-20260119-1514`.
