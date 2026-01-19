# AGENTLOG Archive Index

This index provides quick summaries of archived agent session logs.

**Current active log**: [`/AGENTLOG.md`](/AGENTLOG.md)

---

## 2026-01-19 - Patterns→Prompts Migration Complete

**File**: [`AGENTLOG-01-19-26.md`](AGENTLOG-01-19-26.md)

**Major Work**:
- Completed patterns→prompts terminology migration across codebase
- Renamed `patterns/` directory to `prompts/`, updated env vars (`TNH_PROMPT_DIR`)
- Removed legacy `tnh-fab` CLI (replaced by `tnh-gen`)
- Migrated prompt repo to standalone `tnh-prompts` git repository
- Updated all CLI flags, constants, documentation

**Breaking Changes**:
- `TNH_PATTERN_DIR` env var no longer accepted (use `TNH_PROMPT_DIR`)
- `tnh-fab` CLI removed (use `tnh-gen`)

---

## 2026-01-09 - VS Code Extension Walking Skeleton (v0.3.0 Release)

**File**: [`AGENTLOG-01-09-26.md`](AGENTLOG-01-09-26.md)

**Major Work**:
- Implemented VS Code extension walking skeleton per ADR-VSC02
- Three commands: Run Prompt on Active File, Refresh Prompt Catalog, Show Diagnostics
- TypeScript services: TnhGenCliAdapter, ConfigService, PromptService, EditorService, FileService
- Unit and integration test harness (node:test + test-electron)
- Audio transcribe hotfixes (AssemblyAI pipeline, diarization payloads)
- Prompt frontmatter normalization and token encoding fallback
- Released v0.3.0 to PyPI

**Key Decisions**:
- CLI-first architecture (extension calls tnh-gen subprocess)
- Temp config per invocation (non-persistent)
- Object-service structure in TypeScript mirroring Python patterns
- Session vars file for defaults persistence

---

## 2026-01-01 - ADR-A14 Registry System Implementation

**File**: [`AGENTLOG-01-01-26.md`](AGENTLOG-01-01-26.md)

**Major Work**:
- Implemented ADR-A14 file-based registry system (JSONC, multi-tier pricing, TNHContext)
- Implemented ADR-A14.1 staleness detection with configurable warnings
- Integrated registry into GenAI service layer (router, safety gate, token utils)
- Added comprehensive test coverage (264 tests passing)
- Fixed CI/docs builds (moved Sourcery to optional local group)
- Fixed mypy type errors (9 errors resolved)
- Created PR #24 and merged to main

**Key Decisions**:
- JSONC format for VS Code alignment
- Three-layer path resolution (workspace → user → built-in)
- Staleness detection with 90-day default threshold
- Sourcery in optional local group (platform-specific wheels)

---

## 2025-12-31 - JSONC Parser & Registry Tiers

**File**: [`AGENTLOG-12-31-25.md`](AGENTLOG-12-31-25.md)

**Major Work**:
- Hardened JSONC parser (stateful scanning, string-aware comment handling)
- Added pricing tier metadata support
- Fixed token count fallback for tiktoken unavailability
- Registry staleness detection implementation planning

---

## 2025-12-23 - GenAI Service Review & Thread Safety Planning

**File**: [`AGENTLOG-12-23-25.md`](AGENTLOG-12-23-25.md)

**Major Work**:
- Code review of GenAI service components (Grade: A-, 92/100)
- ADR-A15 thread safety and rate limiting design
- Registry system architecture planning (ADR-A14 draft)

---

## 2025-12-13 - Documentation Reorganization

**File**: [`AGENTLOG-12-13-25.md`](AGENTLOG-12-13-25.md)

**Major Work**:
- Major documentation restructuring per ADR-DD01/DD02
- Implemented progressive disclosure patterns
- Created collapsible navigation for archived content

---

## 2025-12-11 - AI Text Processing Refactor

**File**: [`AGENTLOG-12-11-25.md`](AGENTLOG-12-11-25.md)

**Major Work**:
- Object-service refactor for TextObject
- ADR-AT03 subseries implementation
- Metadata system improvements

---

## 2025-12-10 - Object-Service Architecture

**File**: [`AGENTLOG-12-10-25.md`](AGENTLOG-12-10-25.md)

**Major Work**:
- ADR-OS01 v3 object-service pattern establishment
- Foundational architecture decisions for GenAI service

---

## 2025-12-07 - Early Project Setup

**File**: [`AGENTLOG-12-07-25.md`](AGENTLOG-12-07-25.md)

**Major Work**:
- Initial project structure
- Early development workflow establishment
- Foundational tooling setup

---

**Note**: For detailed session logs, click the file links above. Each archive contains complete context, decisions, discoveries, and file changes for that period.
