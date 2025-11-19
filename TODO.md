# TNH Scholar TODO List

> **Last Updated**: 2025-11-16
> **Version**: 0.1.3 (Alpha)
> **Status**: Active Development - Quick Wins Phase

---

## Priority Roadmap

This section organizes work into three priority levels based on criticality for production readiness.

### Priority 1: Critical Path to Beta

**Goal**: Remove blockers to production readiness. These items must be completed before beta release.

**Status**: 3/5 Complete ✅

#### 1. ✅ Add pytest to CI

- **Status**: COMPLETED
- **Location**: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- **What**: Tests now run in CI with coverage reporting
- **Command**: `pytest --maxfail=1 --cov=tnh_scholar --cov-report=term-missing`

#### 2. ✅ Fix Packaging Issues

- **Status**: COMPLETED
- **Location**: [pyproject.toml](pyproject.toml)
- **What**:
  - ✅ Runtime dependencies declared (pydantic-settings, python-json-logger, tenacity)
  - ✅ Python version pinned to 3.12.4
  - ⚠️ Pattern directory import issue still pending (see Configuration & Data Layout below)

#### 3. ✅ Remove Library sys.exit() Calls

- **Status**: COMPLETED
- **Location**: [gen_ai_service/infra/issue_handler.py](src/tnh_scholar/gen_ai_service/infra/issue_handler.py)
- **What**: Library code now raises ConfigurationError by default
- **Test**: [tests/gen_ai_service/test_service.py::test_missing_api_key_raises_configuration_error](tests/gen_ai_service/test_service.py)

#### 4. 🚧 Implement Core Stubs

- **Status**: IN PROGRESS - Needs Implementation
- **Priority**: HIGH
- **Tasks**:
  - [ ] [config/params_policy.py](src/tnh_scholar/gen_ai_service/config/params_policy.py): Implement actual policy logic (currently pass-through)
    - Policy precedence: call hint → prompt metadata → defaults
    - Cache Settings instead of re-instantiating per call
  - [ ] [routing/model_router.py](src/tnh_scholar/gen_ai_service/routing/model_router.py): Implement model selection logic (currently echoes input)
    - Intent-based routing
    - Provider capability mapping
  - [ ] [safety/safety_gate.py](src/tnh_scholar/gen_ai_service/safety/safety_gate.py): Implement content safety (currently placeholder)
    - Pre-submission content checks
    - Post-completion validation
  - [ ] [mappers/completion_mapper.py](src/tnh_scholar/gen_ai_service/mappers/completion_mapper.py): Surface provider error bodies
    - Structured error propagation
    - Don't just raise ValueError on non-OK status

#### 5. 🚧 Unify OpenAI Clients

- **Status**: PHASE 1 COMPLETE ✅ (5/6 phases remaining)
- **Priority**: HIGH
- **ADR**: [ADR-A13: Legacy Client Migration](docs/design/gen-ai-service/ADR-A13-legacy-client-migration.md)
- **Plan**: [Migration Plan](docs/design/gen-ai-service/MIGRATION-PLAN.md)
- **Problem**: Two implementations causing code divergence (legacy client now removed)
  - **Modern**: [gen_ai_service/providers/openai_client.py](src/tnh_scholar/gen_ai_service/providers/openai_client.py) - typed, retrying
  - **Legacy**: `openai_interface/` – removed as of Phase 6
- **Phase 1: Utilities & Adapters** ✅ COMPLETE
  - [x] Create [token_utils.py](src/tnh_scholar/gen_ai_service/utils/token_utils.py) - token counting
  - [x] Create [response_utils.py](src/tnh_scholar/gen_ai_service/utils/response_utils.py) - response extraction
  - [x] Create [simple_completion.py](src/tnh_scholar/gen_ai_service/adapters/simple_completion.py) - migration adapter
  - [x] Add comprehensive tests (33 new tests)
  - [x] Fix hard-coded literals (use policy dataclass)
- **Phase 2-6: Migration**
  - [x] Phase 2: Migrate core modules (ai_text_processing, journal_processing)
  - [x] Phase 3: Migrate CLI tools
  - [x] Phase 4: Migrate tests
  - [x] Phase 5: Update notebooks
  - [x] Phase 6: Delete legacy code (openai_interface/)

---

### Priority 2: Beta Quality

**Goal**: Improve maintainability, user experience, and code quality for beta release.

#### 6. 🚧 Expand Test Coverage

- **Status**: NOT STARTED
- **Current Coverage**: ~5% (4 test modules)
- **Target**: 50%+ for gen_ai_service
- **Tasks**:
  - [ ] GenAI service flows: prompt rendering, policy resolution, provider adapters
  - [ ] CLI integration tests (option parsing, environment validation)
  - [ ] Configuration loading edge cases
  - [ ] Error handling scenarios
  - [ ] Pattern catalog validation

#### 7. 🚧 Consolidate Environment Loading

- **Status**: NOT STARTED
- **Problem**: Multiple modules call `load_dotenv()` at import time
  - [ai_text_processing/prompts.py](src/tnh_scholar/ai_text_processing/prompts.py)
  - [audio_processing/diarization/pyannote_client.py](src/tnh_scholar/audio_processing/diarization/pyannote_client.py)
- **Tasks**:
  - [ ] Create single startup hook for dotenv loading
  - [ ] Use Pydantic Settings consistently
  - [ ] Pass configuration objects instead of `os.getenv()` calls
  - [ ] Remove import-time side effects

#### 8. 🚧 Clean Up CLI Tool Versions

- **Status**: NOT STARTED
- **Location**: [cli_tools/audio_transcribe/](src/tnh_scholar/cli_tools/audio_transcribe/)
- **Tasks**:
  - [x] Remove [audio_transcribe0.py](src/tnh_scholar/cli_tools/audio_transcribe/audio_transcribe0.py)
  - [x] Remove audio_transcribe1.py
  - [x] Remove audio_transcribe2.py
  - [x] Keep only current version
  - [ ] Create shared utilities (argument parsing, environment validation, logging)

#### 9. 🚧 Update Documentation

- **Status**: NOT STARTED
- **Tasks**:
  - [ ] Update [README.md](README.md) to highlight Gen AI Service architecture
  - [ ] Deprecate outdated CLI examples (punctuate command)
  - [ ] Add practical user guides for new features
  - [ ] Create architecture overview document
  - [ ] Document pattern/prompt authoring schema
  - [ ] Sync mkdocs.yaml with current implementation

#### 10. 🚧 Type System Improvements

- **Status**: PARTIAL (see detailed section below)
- **Current**: 58 errors across 16 files
- **Tasks**: See [Type System Improvements](#type-system-improvements) section below

---

### Priority 3: Production Readiness

**Goal**: Long-term sustainability, advanced features, and production hardening.

#### 11. 🚧 Refactor Monolithic Modules

- **Status**: NOT STARTED
- **Targets**:
  - [ ] [ai_text_processing/prompts.py](src/tnh_scholar/ai_text_processing/prompts.py) (34KB)
    - Break into: prompt model, repository manager, git helpers, lock helpers
    - Add docstrings and tests for each unit
    - Document front-matter schema
  - [ ] [journal_processing/journal_process.py](src/tnh_scholar/journal_processing/journal_process.py) (28KB)
    - Identify focused units
    - Extract reusable components

#### 12. 🚧 Complete Provider Abstraction

- **Status**: NOT STARTED
- **Tasks**:
  - [ ] Implement [Anthropic adapter](src/tnh_scholar/gen_ai_service/providers/anthropic_adapter.py)
  - [ ] Add provider-specific error handling
  - [ ] Test fallback/retry across providers
  - [ ] Provider capability discovery
  - [ ] Multi-provider cost optimization

#### 13. 🚧 Knowledge Base Implementation

- **Status**: DESIGN COMPLETE
- **ADR**: [docs/design/knowledge-base/ADR-K01-preliminary-architectural-design.md](docs/design/knowledge-base/ADR-K01-preliminary-architectural-design.md)
- **Tasks**:
  - [ ] Implement Supabase integration
  - [ ] Vector search functionality
  - [ ] Query capabilities
  - [ ] Semantic similarity search

#### 14. 🚧 Developer Experience Improvements

- **Status**: NOT STARTED
- **Tasks**:
  - [ ] Add pre-commit hooks (Black, Ruff, MyPy)
  - [ ] Create Makefile/justfile for common tasks (lint, test, docs, format)
  - [ ] Add contribution templates
  - [ ] Improve CONTRIBUTING.md
  - [ ] Release automation
  - [ ] Changelog automation

#### 15. 🚧 Configuration & Data Layout

- **Status**: NOT STARTED
- **Priority**: HIGH (blocks pip install)
- **Problem**: [src/tnh_scholar/**init**.py](src/tnh_scholar/__init__.py) raises FileNotFoundError when repo layout missing
- **Tasks**:
  - [ ] Package pattern assets as resources
  - [ ] Make patterns directory optional
  - [ ] Move directory checks to CLI entry points only
  - [ ] Ensure installed wheels work without patterns/ directory

#### 16. 🚧 Prompt Catalog Safety

- **Status**: NOT STARTED
- **Priority**: MEDIUM
- **Problem**: Adapter doesn't handle missing keys or invalid front-matter gracefully
- **Tasks**:
  - [ ] Add manifest validation
  - [ ] Implement caching
  - [ ] Better error messages (unknown prompt, hash mismatch)
  - [ ] Front-matter validation
  - [ ] Document pattern schema

---

## Type System Improvements

**Current Status**:

- Total Type Errors: 58
- Affected Files: 16
- Files Checked: 62

### High Priority (Pre-Beta)

#### Install Missing Type Stubs ✅ COMPLETED

- [x] Install required type stub packages:
  - [x] types-PyYAML
  - [x] types-requests

#### Critical Type Errors

- [ ] Fix audio processing boundary type inconsistencies
  - [ ] Resolve return type mismatches in `audio_processing/audio.py`
  - [ ] Standardize Boundary type usage
- [ ] Fix core text processing type errors
  - [ ] Fix str vs list[str] return type in `bracket.py`
  - [ ] Resolve object extension error in `video_processing.py`
- [ ] Address function redefinitions in `run_oa_batch_jobs.py`:
  - [ ] Resolve `calculate_enqueued_tokens` redefinition
  - [ ] Fix `process_batch_files` redefinition
  - [ ] Fix `main` function redefinition

### Medium Priority (Beta Stage)

#### Add Missing Type Annotations

- [ ] Add variable type annotations:
  - [ ] `attributes_with_values` in clean_parse_tag.py
  - [ ] `current_page` in xml_processing.py
  - [ ] `covered_lines` in ai_text_processing.py
  - [ ] `seen_names` in patterns.py

#### Pattern System Type Improvements

- [ ] Fix Pattern class type issues:
  - [ ] Resolve `apply_template` attribute errors
  - [ ] Fix `name` attribute access issues
  - [ ] Standardize Pattern type definition

### Low Priority (Post-Beta)

#### General Type Improvements

- [ ] Clean up Any return types:
  - [ ] Properly type `getch` handling in user_io_utils.py
  - [ ] Type language code returns in lang.py
  - [ ] Remove Any returns in ai_text_processing.py
- [ ] Standardize type usage:
  - [ ] Implement consistent string formatting in patterns.py
  - [ ] Update callable type usage
  - [ ] Clean up type hints in openai_interface.py

### Implementation Strategy

#### Phase 1: Core Type Safety

- [ ] Focus on high-priority items affecting core functionality
- [x] Implement type checking in CI pipeline
- [ ] Document type decisions

#### Phase 2: Beta Preparation

- [ ] Address medium-priority items
- [ ] Set up pre-commit type checking hooks
- [ ] Update documentation with type information

#### Phase 3: Post-Beta Cleanup

- [ ] Handle low-priority type improvements
- [ ] Implement stricter type checking settings
- [ ] Full type coverage audit

### Typing Guidelines

**Standards**:

- [ ] Use explicit types over Any
- [ ] Create type aliases for complex types
- [ ] Document typing decisions
- [ ] Implement consistent Optional handling

**References**:

- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Type Checking Best Practices](https://mypy.readthedocs.io/en/stable/common_issues.html)

---

## Additional Tasks

### Medium Priority

#### Improve NumberedText Ergonomics

- **Location**: [text_processing/numbered_text.py](src/tnh_scholar/text_processing/numbered_text.py)
- **Problem**: Constructor raises for content=None even though typed as optional
- **Tasks**:
  - [ ] Decide whether empty content should mean "no lines yet"
  - [ ] Add file-based round-trip tests
  - [ ] Trim redundant pytest boilerplate in tests

#### Logging System Scope

- **Location**: [logging_config.py](src/tnh_scholar/logging_config.py)
- **Problem**: Modules call setup_logging individually
- **Tasks**:
  - [ ] Define single application bootstrap
  - [ ] Document logger acquisition pattern (get_logger only)
  - [ ] Create shared CLI bootstrap helper

### Low Priority

#### Package API Definition

- **Status**: Deferred during prototyping
- **Tasks**:
  - [ ] Review and document all intended public exports
  - [ ] Implement `__all__` in key `__init__.py` files
  - [ ] Verify exports match documentation

#### Repo Hygiene

- **Problem**: Generated artifacts in repo
- **Files**: build/, dist/, site/, current_pip_freeze.txt, mypy_errors.txt, project_directory_tree.txt
- **Tasks**:
  - [ ] Add to .gitignore
  - [ ] Document regeneration process
  - [ ] Rely on release pipelines for builds

#### Notebook & Research Management

- **Location**: notebooks/, docs/research/
- **Problem**: Valuable but not curated exploratory work
- **Tasks**:
  - [ ] Adopt naming/linting convention
  - [ ] Keep reproducible notebooks in notebooks/experiments
  - [ ] Publish vetted analyses to docs/research via nbconvert
  - [ ] Archive obsolete notebooks

---

## Progress Summary

**Quick Wins Completed (2025-11-16)**:

- ✅ Packaging & dependencies fixed
- ✅ CI pytest integration
- ✅ Library exception handling (removed sys.exit)

**Next Sprint Focus**:

- 🎯 Implement core stubs (policy, routing, safety)
- 🎯 Unify OpenAI clients
- 🎯 Expand test coverage to 50%+

**Beta Blockers**:

- Configuration & data layout (pattern directory)
- Core stub implementations
- OpenAI client unification

---

## Notes for Maintainers

### Test Running

```bash
# Run all tests with coverage
poetry run pytest --maxfail=1 --cov=tnh_scholar --cov-report=term-missing -v

# Run specific test file
poetry run pytest tests/gen_ai_service/test_service.py -v

# Run with coverage report
poetry run pytest --cov=tnh_scholar --cov-report=html
```

### Type Checking

```bash
# Check types
poetry run mypy src/

# Generate error report
poetry run mypy src/ > mypy_errors.txt
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Lint
poetry run ruff check src/

# Run all checks (as CI does)
poetry run black --check src/
poetry run mypy src/
poetry run ruff check src/
poetry run pytest --maxfail=1 --cov=tnh_scholar
```
