# AGENTLOG

This file captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. It provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

See AGENTLOG_TEMPLATE.md for structure and format.

**Archive**: Older sessions are archived in [`archive/agentlogs/`](archive/agentlogs/) with a summary index at [`archive/agentlogs/archive-index.md`](archive/agentlogs/archive-index.md).

**Ordering**: Append new records at the end (chronological order from least to most recent).

---

## 2026-01-02 12:35 PST VS Code Extension Skeleton

**Agent**: Codex (GPT-5)
**Chat Reference**: vscode-extension-wip
**Human Collaborator**: aaronksolomon

### Context

Begin initial VS Code extension development after ADR-VSC02 accepted and moved to WIP. Establish minimal walking skeleton per ADR with temp-config and CLI contract.

### Key Decisions

- **Temp config per call**: Extension writes a per-invocation config JSON and passes `--config` to `tnh-gen` (non-persistent).
- **Object-service structure**: Extension uses protocol interfaces and service classes to align with ADR-OS01.

### Work Completed

- [x] Added VS Code extension scaffold with commands and configuration (files: `vscode-extension/tnh-scholar/package.json`, `vscode-extension/tnh-scholar/tsconfig.json`)
- [x] Implemented CLI adapter, config manager, editor/file services, and prompt runner (files: `vscode-extension/tnh-scholar/src/extension.ts`, `vscode-extension/tnh-scholar/src/services/*.ts`)
- [x] Documented API payload contracts and config handling in ADRs; set ADR-VSC02 to WIP (files: `docs/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md`)

### Discoveries & Insights

- **CLI success payloads already typed**: `tnh-gen` success payloads are defined in `src/tnh_scholar/cli_tools/tnh_gen/types.py:120`, enabling direct TS mapping.

### Files Modified/Created

- `docs/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md`: WIP status + CF01/OS01 constraints + config/contract details
- `docs/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md`: Addendum documenting success payloads and `--config`
- `vscode-extension/tnh-scholar/package.json`: Created - extension manifest
- `vscode-extension/tnh-scholar/tsconfig.json`: Created - TypeScript config
- `vscode-extension/tnh-scholar/src/extension.ts`: Created - activation + command wiring
- `vscode-extension/tnh-scholar/src/models/*.ts`: Created - API payload + settings models
- `vscode-extension/tnh-scholar/src/protocols/extension_protocols.ts`: Created - extension protocols
- `vscode-extension/tnh-scholar/src/services/*.ts`: Created - CLI adapter, config manager, editor/file services, prompt runner

### Next Steps

- [ ] Run TypeScript compile for the extension scaffold
- [ ] Add minimal smoke tests for CLI adapter and config resolution
- [ ] Wire dev instructions for running the extension locally

### Open Questions

- Should prompt optional variables be collected in v0.1.0 or deferred?

### References

- ADR-VSC02, ADR-TG01, ADR-CF01, ADR-OS01

---

## 2026-01-02 12:55 PST VS Code Extension Unit Tests

**Agent**: Codex (GPT-5)
**Chat Reference**: vscode-extension-wip
**Human Collaborator**: aaronksolomon

### Context

User requested unit tests before VS Code extension integration tests.

### Key Decisions

- **Unit tests first**: Added minimal tests for CLI arg building and output path utilities using Node's built-in test runner.
- **Extract pure helpers**: Introduced `CliArgsBuilder` and `path_utils` for testable logic without VS Code host dependencies.

### Work Completed

- [x] Added CLI args builder service and tests (files: `vscode-extension/tnh-scholar/src/services/cli_args_builder.ts`, `vscode-extension/tnh-scholar/src/test/cli_args_builder.test.ts`)
- [x] Added path utils and tests; wired into file service (files: `vscode-extension/tnh-scholar/src/utils/path_utils.ts`, `vscode-extension/tnh-scholar/src/test/path_utils.test.ts`, `vscode-extension/tnh-scholar/src/services/file_service.ts`)
- [x] Added test script and ts-node dependency (file: `vscode-extension/tnh-scholar/package.json`)

### Discoveries & Insights

- **VS Code module dependency**: Tests avoid VS Code runtime by isolating pure helpers.

### Files Modified/Created

- `vscode-extension/tnh-scholar/src/services/cli_args_builder.ts`: Created - build CLI args
- `vscode-extension/tnh-scholar/src/utils/path_utils.ts`: Created - prompt key sanitization + output path
- `vscode-extension/tnh-scholar/src/services/cli_adapter.ts`: Use args builder
- `vscode-extension/tnh-scholar/src/services/file_service.ts`: Use path utils
- `vscode-extension/tnh-scholar/src/test/cli_args_builder.test.ts`: Created
- `vscode-extension/tnh-scholar/src/test/path_utils.test.ts`: Created
- `vscode-extension/tnh-scholar/package.json`: Add test script + ts-node dev dependency

### Next Steps

- [ ] Run `npm install` in `vscode-extension/tnh-scholar`
- [ ] Run `npm test` in `vscode-extension/tnh-scholar`
- [ ] Add VS Code extension integration tests

### Open Questions

- Should we add a small wrapper to mock `vscode` for more unit tests (config_manager/editor_service)?

### References

- ADR-VSC02

---

## 2026-01-02 13:15 PST VS Code Integration Test Harness

**Agent**: Codex (GPT-5)
**Chat Reference**: vscode-extension-wip
**Human Collaborator**: aaronksolomon

### Context

User requested integration tests after unit tests; add VS Code extension test harness (test-electron + Mocha).

### Key Decisions

- **Integration tests via test-electron**: Use @vscode/test-electron with Mocha test runner for extension-host tests.
- **Minimal smoke test**: Verify command registration on activation before deeper CLI flow tests.

### Work Completed

- [x] Added VS Code integration test harness (files: `vscode-extension/tnh-scholar/src/test/runTest.ts`, `vscode-extension/tnh-scholar/src/test/suite/index.ts`)
- [x] Added command registration smoke test (file: `vscode-extension/tnh-scholar/src/test/suite/extension.test.ts`)
- [x] Added integration test dependencies and scripts (file: `vscode-extension/tnh-scholar/package.json`)
- [x] Updated TS compiler types for Mocha (file: `vscode-extension/tnh-scholar/tsconfig.json`)

### Discoveries & Insights

- **Extension ID**: Tests target `tnh-scholar.tnh-scholar` based on package.json publisher/name.

### Files Modified/Created

- `vscode-extension/tnh-scholar/src/test/runTest.ts`: Created - test-electron launcher
- `vscode-extension/tnh-scholar/src/test/suite/index.ts`: Created - Mocha test loader
- `vscode-extension/tnh-scholar/src/test/suite/extension.test.ts`: Created - command registration test
- `vscode-extension/tnh-scholar/package.json`: Add test:integration script + deps
- `vscode-extension/tnh-scholar/tsconfig.json`: Add mocha types

### Next Steps

- [ ] Run `npm install` in `vscode-extension/tnh-scholar`
- [ ] Run `npm run test:integration` in `vscode-extension/tnh-scholar`
- [ ] Add CLI adapter integration test with a mock tnh-gen executable

### Open Questions

- Should we add a fixture workspace for integration tests (sample prompt catalog)?

### References

- ADR-VSC02

---

## 2026-01-03 00:55 PST VS Code Extension Test Coverage

**Agent**: Codex (GPT-5)
**Chat Reference**: vscode-extension-wip
**Human Collaborator**: aaronksolomon

### Context

User asked to address review notes about test coverage: add CLI adapter unit tests and a broader integration test.

### Key Decisions

- **ExecRunner injection**: Added an injectable execution runner to `TnhGenCliAdapter` for deterministic unit testing.
- **Refresh catalog IT**: Added a CLI-path integration test using a mock `tnh-gen` script to validate the config path and command wiring.

### Work Completed

- [x] Added CLI adapter unit tests (files: `vscode-extension/tnh-scholar/src/test/cli_adapter.test.ts`)
- [x] Added integration test for refresh command with mock CLI (file: `vscode-extension/tnh-scholar/src/test/suite/refresh_catalog.test.ts`)
- [x] Refactored CLI adapter to accept ExecRunner injection (file: `vscode-extension/tnh-scholar/src/services/cli_adapter.ts`)

### Discoveries & Insights

- **Mock CLI scripts**: A simple bash stub is sufficient for list-only integration tests.

### Files Modified/Created

- `vscode-extension/tnh-scholar/src/services/cli_adapter.ts`: Add ExecRunner injection
- `vscode-extension/tnh-scholar/src/test/cli_adapter.test.ts`: Created
- `vscode-extension/tnh-scholar/src/test/suite/refresh_catalog.test.ts`: Created

### Next Steps

- [ ] Re-run unit tests and integration tests to confirm new coverage
- [ ] Add a full workflow IT once UI inputs can be mocked

### Open Questions

- Should we add a dedicated mock CLI fixture script for reuse across tests?

### References

- ADR-VSC02

---

## 2026-01-03 01:10 PST Separate Unit vs Integration Tests

**Agent**: Codex (GPT-5)
**Chat Reference**: vscode-extension-wip
**Human Collaborator**: aaronksolomon

### Context

Unit test run failed because integration tests imported the VS Code runtime. Needed to separate unit and integration suites.

### Key Decisions

- **Split test folders**: Unit tests live in `src/test/unit`, integration tests in `src/test/integration`.
- **Unit test script**: `npm test` only runs unit tests.

### Work Completed

- [x] Moved tests into unit/integration folders (files: `vscode-extension/tnh-scholar/src/test/unit/*.test.ts`, `vscode-extension/tnh-scholar/src/test/integration/*.test.ts`)
- [x] Updated integration test loader path (file: `vscode-extension/tnh-scholar/src/test/suite/index.ts`)
- [x] Updated unit test script to exclude VS Code tests (file: `vscode-extension/tnh-scholar/package.json`)

### Files Modified/Created

- `vscode-extension/tnh-scholar/src/test/unit/cli_args_builder.test.ts`: Moved
- `vscode-extension/tnh-scholar/src/test/unit/path_utils.test.ts`: Moved
- `vscode-extension/tnh-scholar/src/test/unit/cli_adapter.test.ts`: Moved
- `vscode-extension/tnh-scholar/src/test/integration/extension.test.ts`: Moved
- `vscode-extension/tnh-scholar/src/test/integration/refresh_catalog.test.ts`: Moved
- `vscode-extension/tnh-scholar/src/test/suite/index.ts`: Point to integration tests
- `vscode-extension/tnh-scholar/package.json`: Unit tests only

### Next Steps

- [ ] Re-run `npm test` and `npm run test:integration`

### References

- ADR-VSC02

---

## 2026-01-03 19:05 PST Audio Transcribe Hotfixes + Dependency Wiring

**Agent**: Codex (GPT-5)
**Chat Reference**: audio-transcribe-hotfix-assemblyai
**Human Collaborator**: phapman

### Context

Audio-transcribe failures surfaced after diarization refactors and missing dependencies. Needed a hotfix to restore CLI reliability with AssemblyAI.

### Key Decisions

- **AssemblyAI required**: Promote `assemblyai` and `pysrt` to core deps to match runtime expectations.
- **Provider-aware pipeline**: Skip pyannote diarization for AssemblyAI to avoid unnecessary uploads.
- **Resilient SDK options**: Filter/normalize CLI options to match AssemblyAI SDK constraints.

### Work Completed

- [x] Accept pyannote status payload aliases and default outcome for Pydantic validation (file: `src/tnh_scholar/audio_processing/diarization/schemas.py`)
- [x] Fix diarization success match and reduce log payload size (file: `src/tnh_scholar/cli_tools/audio_transcribe/transcription_pipeline.py`)
- [x] Skip diarization for AssemblyAI and transcribe full audio (file: `src/tnh_scholar/cli_tools/audio_transcribe/transcription_pipeline.py`)
- [x] Improve transcription factory lazy import handling for AssemblyAI (file: `src/tnh_scholar/audio_processing/transcription/transcription_service.py`)
- [x] Normalize AssemblyAI options (drop unsupported keys, map language, disable language_detection when language_code set) (file: `src/tnh_scholar/audio_processing/transcription/assemblyai_service.py`)
- [x] Add minimal tests for diarization payloads, pipeline provider routing, and AssemblyAI option normalization (files: `tests/audio_processing/diarization/test_schemas.py`, `tests/cli_tools/test_audio_transcribe_pipeline.py`, `tests/audio_processing/transcription/test_assemblyai_service_options.py`, `tests/audio_processing/transcription/test_transcription_service_factory.py`)
- [x] Add required deps and update Makefile target (files: `pyproject.toml`, `Makefile`)

### Discoveries & Insights

- AssemblyAI SDK rejects `language_detection` when `language_code` is present; must disable it.

### Files Modified/Created

- `src/tnh_scholar/audio_processing/diarization/schemas.py`
- `src/tnh_scholar/cli_tools/audio_transcribe/transcription_pipeline.py`
- `src/tnh_scholar/audio_processing/transcription/transcription_service.py`
- `src/tnh_scholar/audio_processing/transcription/assemblyai_service.py`
- `pyproject.toml`
- `Makefile`
- `tests/audio_processing/diarization/test_schemas.py`
- `tests/cli_tools/test_audio_transcribe_pipeline.py`
- `tests/audio_processing/transcription/test_assemblyai_service_options.py`
- `tests/audio_processing/transcription/test_transcription_service_factory.py`

### Next Steps

- [ ] Run targeted audio-transcribe smoke test with AssemblyAI after install

## 2026-01-05 21:24 PST Prompt Frontmatter + Token Counting Registry Fallback

**Agent**: Codex (GPT-5)
**Chat Reference**: simple-punctuate-frontmatter-token-count
**Human Collaborator**: phapman

### Context

`tnh-gen run` surfaced prompt frontmatter validation errors and a token-count warning for `gpt-5-mini`.

### Key Decisions

- **Normalize prompt metadata**: Coerce missing/invalid frontmatter fields to safe defaults with warnings instead of failing.
- **Registry-aware token encoding**: Use the model registry to pick a sensible encoding when tiktoken lacks the model.

### Work Completed

- [x] Normalized prompt frontmatter loading to default missing required variables and defaults with warnings (file: `src/tnh_scholar/prompt_system/mappers/prompt_mapper.py`)
- [x] Fixed `simple_punctuate` frontmatter required variables list (file: `patterns/simple_punctuate.md`)
- [x] Added prompt mapper coverage for missing required variables (file: `tests/prompt_system/test_catalog_adapters.py`)
- [x] Added registry-based encoding fallback for token counting (file: `src/tnh_scholar/gen_ai_service/utils/token_utils.py`)
- [x] Added token counting test for GPT-5 registry encoding resolution (file: `tests/gen_ai_service/utils/test_token_utils.py`)

### Discoveries & Insights

- Token counting warnings came from tiktoken model mapping, not prompt execution.

### Files Modified/Created

- `src/tnh_scholar/prompt_system/mappers/prompt_mapper.py`: Normalize metadata fields with warnings
- `patterns/simple_punctuate.md`: Required variables set to empty list
- `tests/prompt_system/test_catalog_adapters.py`: Add missing required variables normalization test
- `src/tnh_scholar/gen_ai_service/utils/token_utils.py`: Registry-aware encoding fallback
- `tests/gen_ai_service/utils/test_token_utils.py`: Add GPT-5 token count warning regression test

### Next Steps

- [ ] Run `pytest tests/prompt_system/test_catalog_adapters.py tests/gen_ai_service/utils/test_token_utils.py`

---

## 2026-01-07 22:40 PST Diagnostics Command

**Agent**: Codex (GPT-5)
**Chat Reference**: vscode-extension-wip
**Human Collaborator**: aaronksolomon

### Context

User requested a diagnostics command to validate CLI discovery, error messages, and temp config behavior.

### Key Decisions

- **Diagnostics command**: Added a command that logs resolved settings, temp config content, and CLI version info to the Output channel.

### Work Completed

- [x] Added diagnostics service and command wiring (files: `vscode-extension/tnh-scholar/src/services/diagnostics_service.ts`, `vscode-extension/tnh-scholar/src/extension.ts`, `vscode-extension/tnh-scholar/package.json`)
- [x] Added diagnostics protocol interface (file: `vscode-extension/tnh-scholar/src/protocols/extension_protocols.ts`)

### Files Modified/Created

- `vscode-extension/tnh-scholar/src/services/diagnostics_service.ts`: Created
- `vscode-extension/tnh-scholar/src/extension.ts`: Register diagnostics command
- `vscode-extension/tnh-scholar/src/protocols/extension_protocols.ts`: Add DiagnosticsProtocol
- `vscode-extension/tnh-scholar/package.json`: Add command + activation

### Next Steps

- [ ] Run `TNH Scholar: Show Diagnostics` in VS Code and review output

### References

- ADR-VSC02

---

## 2026-01-07 23:10 PST VS Code Extension Validation

**Agent**: Codex (GPT-5)
**Chat Reference**: vscode-extension-wip
**Human Collaborator**: aaronksolomon

### Context

Recorded testing and validation results for the VS Code extension harness and diagnostics.

### Work Completed

- [x] Ran unit tests (`npm test`) after separating unit/integration suites
- [x] Ran integration tests (`npm run test:integration`) with test-electron and confirmed smoke + refresh tests passing
- [x] Validated diagnostics output for cliPath resolution, temp config creation, and tnh-gen version reporting

### Discoveries & Insights

- **VS Code download cache**: test-electron reused cached VS Code build; IPC path warning resolved with shorter user-data dirs
- **Diagnostics confirms config flow**: temp config writes and `tnh-gen --api --config ... version` are working

### References

- ADR-VSC02

---

## 2026-01-08 00:20 PST VS Code Extension Refinements

**Agent**: Codex (GPT-5)
**Chat Reference**: vscode-extension-wip
**Human Collaborator**: aaronksolomon

### Context

Follow-up refinements to support diagnostics and testing workflows for the VS Code extension.

### Key Decisions

- **Session vars addendum**: Documented session defaults and session vars file behavior in ADR-VSC02.
- **Optional variables**: Added optional-variable prompt flow with skip behavior for v0.1.0.

### Work Completed

- [x] Added ADR-VSC02 addendum for session defaults and session vars files (files: `docs/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md`)
- [x] Implemented optional-variable prompting in editor service and prompt runner (files: `vscode-extension/tnh-scholar/src/services/editor_service.ts`, `vscode-extension/tnh-scholar/src/services/prompt_runner.ts`)
- [x] Shortened VS Code test IPC paths for faster shutdown (file: `vscode-extension/tnh-scholar/src/test/runTest.ts`)
- [x] Added pipx refresh + build-all Makefile targets (file: `Makefile`)

### Files Modified/Created

- `docs/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md`: Addendum for session defaults
- `vscode-extension/tnh-scholar/src/services/editor_service.ts`: Optional variable prompts
- `vscode-extension/tnh-scholar/src/services/prompt_runner.ts`: Merge required + optional variables
- `vscode-extension/tnh-scholar/src/test/runTest.ts`: Shorter user-data and extensions paths
- `Makefile`: Add `pipx-refresh` and `build-all` targets

### Next Steps

- [ ] Complete full workflow integration test (run prompt end-to-end)
- [ ] Manual validation in VS Code with real prompts

### References

- ADR-VSC02

---


## 2026-01-07 19:15 PST VS Code Extension Walking Skeleton Completion

**Agent**: Claude Sonnet 4.5
**Chat Reference**: vscode-extension-commit-pr-workflow
**Human Collaborator**: phapman

### Context

VS Code extension walking skeleton completed and tested end-to-end. All three commands validated in live dev extension. Ready for commit sequence and PR creation per ADR-VSC01/VSC02.

### Key Decisions

- **Commit Organization**: Separate commits for feature (extension code), workspace improvements, docs/ADRs, and project tracking
- **ADR Status Update**: ADR-VSC02 moved from 'wip' to 'implemented'
- **TODO Update**: VS Code Extension Walking Skeleton marked as COMPLETED with all deliverables checked off
- **CHANGELOG Update**: Comprehensive entry documenting all extension capabilities and architecture components

### Work Completed

- [x] Committed VS Code extension implementation (vscode-extension/ directory, 24 files, 3138+ lines)
- [x] Committed workspace improvements (.github/ISSUE_TEMPLATE.md, poetry.toml, .gitignore updates)
- [x] Committed documentation updates (ADR-VSC02 status, ADR-TG01/TG02 addendums, supporting docs)
- [x] Updated CHANGELOG.md with VS Code extension completion details
- [x] Updated TODO.md marking extension walking skeleton as COMPLETED
- [x] Updated AGENTLOG.md with session summary
- [ ] Commit project tracking updates (CHANGELOG, TODO, AGENTLOG)
- [ ] Push to remote branch
- [ ] Create pull request with comprehensive summary

### Discoveries & Insights

- Extension demonstrates successful CLI-first architecture pattern
- CF01 ownership-based precedence working correctly in temp config approach
- All three endpoints (run prompt, refresh catalog, diagnostics) validated end-to-end
- TypeScript object-service pattern mirrors Python implementation effectively

### Files Modified/Created

**Extension Implementation** (Commit 1):
- `vscode-extension/tnh-scholar/`: Complete TypeScript extension (24 files)

**Workspace Improvements** (Commit 2):
- `.github/ISSUE_TEMPLATE.md`
- `poetry.toml`
- `.gitignore`

**Documentation Updates** (Commit 3):
- `docs/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md`
- `docs/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md`
- `docs/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md`
- `AGENTS.md`, `DEV_SETUP.md`, `README.md`
- `docs/documentation_index.md`, `docs/documentation_map.md`, `docs/index.md`

**Project Tracking** (Commit 4 - in progress):
- `CHANGELOG.md`
- `TODO.md`
- `AGENTLOG.md`

### Next Steps

- [ ] Complete project tracking commit
- [ ] Run pre-push validation (make ci-check, mypy)
- [ ] Push to origin/feat/vscode-extension-adrs
- [ ] Create PR with detailed summary covering all work

### References

- ADR-VSC01, ADR-VSC02, ADR-TG01, ADR-TG02

---

## 2026-01-09 12:31 PST Mypy Fixes in Transcription Pipeline

**Agent**: Codex (GPT-5)
**Chat Reference**: vscode-extension-wip
**Human Collaborator**: aaronksolomon

### Context
Addressed mypy issues in transcription pipeline (branch-only fixes requested).

### Work Completed
- [x] Aligned transcription return types and added explicit annotations (file: `src/tnh_scholar/cli_tools/audio_transcribe/transcription_pipeline.py`)
- [x] Renamed duplicated diarization response variable to avoid redefinition

### Files Modified/Created
- `src/tnh_scholar/cli_tools/audio_transcribe/transcription_pipeline.py`: Type annotations + return shape alignment

### References
- CI Fix List (audio_transcribe/transcription_pipeline.py)
---
