# TNH Scholar TODO List

## Package API Definition

**Priority**: Low (Code Quality)  
**Status**: Deferred during prototyping

### Description

Implement `__all__` declarations to define public APIs and resolve F401 warnings.

### Tasks

- [ ] Review and document all intended public exports
- [ ] Implement `__all__` in key `__init__.py` files:
  - [ ] src/tnh_scholar/ai_text_processing/**init**.py
  - [ ] [Additional **init**.py files to be identified]
- [ ] Verify exports match documentation
- [ ] Update package documentation to reflect public API

## Type System Improvements

### High Priority (Pre-Beta)

#### Install Missing Type Stubs

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

## Implementation Strategy

### Phase 1: Core Type Safety

- [ ] Focus on high-priority items affecting core functionality
- [ ] Implement type checking in CI pipeline
- [ ] Document type decisions

### Phase 2: Beta Preparation

- [ ] Address medium-priority items
- [ ] Set up pre-commit type checking hooks
- [ ] Update documentation with type information

### Phase 3: Post-Beta Cleanup

- [ ] Handle low-priority type improvements
- [ ] Implement stricter type checking settings
- [ ] Full type coverage audit

## Typing Guidelines

### Standards

- [ ] Use explicit types over Any
- [ ] Create type aliases for complex types
- [ ] Document typing decisions
- [ ] Implement consistent Optional handling

### Quality Metrics

Current Status:

- Total Type Errors: 58
- Affected Files: 16
- Files Checked: 62

### References

- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Type Checking Best Practices](https://mypy.readthedocs.io/en/stable/common_issues.html)

---

## Additional Cleanup Recommendations

High Priority

Packaging & dependencies: pyproject.toml:13-80 pins Python to exactly 3.12.4 and omits runtime packages that are imported throughout the codebase (pydantic_settings in src/tnh_scholar/gen_ai_service/config/settings.py:15-61, python-json-logger in src/tnh_scholar/logging_config.py:176-184, tenacity in src/tnh_scholar/gen_ai_service/providers/openai_client.py:1-63 and src/tnh_scholar/audio_processing/diarization/pyannote_client.py:20-138). Add those dependencies, relax the Python requirement to a compatible range, and move to a locked workflow (Poetry or pip-compile) so CI/dev shells all agree on versions.

Configuration & data layout: src/tnh_scholar/__init__.py:53-69 raises FileNotFoundError during import when the expected repo layout is missing, yet Settings.prompt_dir still defaults to that path (src/tnh_scholar/gen_ai_service/config/settings.py:51-61). Package the pattern assets or make them optional resources, move directory checks into CLI entry points, and ensure installed wheels don’t fail just because patterns/ isn’t beside site-packages.

Fail-fast strategy: GenAIService.__init__ calls IssueHandler.no_api_key with exit_on_fail=True, which prints to stderr and terminates the interpreter (src/tnh_scholar/gen_ai_service/service.py:36-48, src/tnh_scholar/gen_ai_service/infra/issue_handler.py:61-89). Replace sys.exit with typed exceptions so libraries/tests can catch configuration errors, and add richer error context (missing prompt dir, missing policy file, etc.).

Environment/secrets loading: multiple modules call load_dotenv() at import time (src/tnh_scholar/openai_interface/openai_interface.py:55-66, src/tnh_scholar/ai_text_processing/prompts.py:971-984, src/tnh_scholar/audio_processing/diarization/pyannote_client.py:27-50), which both hits the filesystem repeatedly and couples library imports to .env files. Consolidate dotenv loading into a single startup hook or rely entirely on BaseSettings, and pass configuration objects instead of accessing os.getenv everywhere.

GenAI policy/router skeletons: apply_policy is a stub that re-instantiates Settings per call (src/tnh_scholar/gen_ai_service/config/params_policy.py:25-47), select_provider_and_model just echoes its input (src/tnh_scholar/gen_ai_service/routing/model_router.py:1-15), and provider_to_completion raises ValueError on any non-OK status without surfacing the provider error body (src/tnh_scholar/gen_ai_service/mappers/completion_mapper.py:1-35). Implement actual policy precedence (call hint vs prompt metadata vs defaults), caching, provider routing, and structured error propagation before trying to support additional providers.

OpenAI client duplication: the gen-ai stack uses a typed, retrying client (src/tnh_scholar/gen_ai_service/providers/openai_client.py:1-100) while legacy tooling uses a singleton with global state (src/tnh_scholar/openai_interface/openai_interface.py:1-200). Unify on one adapter (ideally the typed one), port CLIs/text pipelines to it, and delete the redundant code to avoid hotfixes diverging.

Prompt catalog safety: the adapter never handles missing keys or invalid front-matter beyond throwing whatever PromptCatalog.load raises (src/tnh_scholar/gen_ai_service/pattern_catalog/adapters/prompts_adapter.py:33-115), while the singleton LocalPromptManager lazily loads directories without validation (src/tnh_scholar/ai_text_processing/prompts.py:931-984). Add manifest validation, caching, and clearer error messages (unknown prompt, hash mismatch) before shipping anything that relies on this data.

Testing & CI: Only four test modules exist—two target the legacy OpenAI helper and one targets NumberedText (tests/openai_interface/test_openai_interface.py:1-200, tests/text_processing/test_numbered_text.py:1-200)—and the GitHub workflow never invokes pytest (.github/workflows/ci.yml:29-44). Build a regression suite for GenAI service flows (prompt rendering, policy resolution, provider adapters), CLI option parsing, and config loading; then run pytest --maxfail=1 --cov inside CI alongside lint/type checks.

Medium Priority

Refactor monolithic prompt tooling: src/tnh_scholar/ai_text_processing/prompts.py:1-988 combines git metadata, locking, file I/O, Jinja environments, and singleton access in one module. Break it into smaller units (prompt model, repository manager, git/lock helpers), add docstrings/tests for each, and document the front-matter schema so contributors know how to author prompts.
Improve NumberedText ergonomics: the constructor raises for content=None even though it is typed as optional, and tests duplicate imports and placeholder comments (src/tnh_scholar/text_processing/numbered_text.py:144-217, tests/text_processing/test_numbered_text.py:1-200). Decide whether empty content should mean “no lines yet,” add file-based round-trip tests, and trim the redundant pytest boilerplate.

Consolidate CLI implementations: three generations of audio-transcribe code live side-by-side (src/tnh_scholar/cli_tools/audio_transcribe/audio_transcribe0.py:1-70, audio_transcribe1.py, audio_transcribe2.py), all with their own config and dotenv handling. Redesign the CLI package with shared utilities (argument parsing, environment validation, logging) and delete deprecated entry points to reduce maintenance burden.

Logging system scope: src/tnh_scholar/logging_config.py:158-219 already implements color/json/queue logging, but modules still call setup_logging individually (see src/tnh_scholar/cli_tools/audio_transcribe/audio_transcribe0.py:33-67). Define a single application bootstrap (maybe a helper in tnh_scholar.cli_tools.common) that initializes logging once per process, and document how library modules should obtain loggers (get_logger only).

Documentation vs implementation drift: mkdocs.yaml:1-53 references CLI and design docs that are out of date with the gen-ai service, while README.md still focuses on the legacy tooling. Draft a doc re-org plan (architecture overview, GenAI pattern catalog, CLI how-tos) and add docstring templates so modules like service.py and openai_adapter.py stay synchronized with docs.
Type-checking debt: TODO.md and mypy_errors.txt track unresolved typing work, but pyproject.toml keeps mypy in a permissive mode. Once missing dependencies are added, iterate through the TODO list, enable stricter flags module-by-module, and enforce mypy (and maybe ruff --select=ANN) via pre-commit hooks.

Low Priority

Repo hygiene: Generated artifacts (build/, dist/, site/, root __pycache__/) and diagnostic outputs (current_pip_freeze.txt, mypy_errors.txt, project_directory_tree.txt) live in the repo (project_directory_tree.txt:1-80). Add them to .gitignore, document how to regenerate directory trees, and rely on release pipelines to build wheels/docs.

Notebook & research management: the notebooks/ and docs/research/ trees contain exploratory work that’s valuable but not curated. Adopt a naming/linting convention (e.g., keep reproducible notebooks in notebooks/experiments, publish vetted analyses to docs/research via nbconvert) and archive obsolete notebooks elsewhere.

Developer workflow polish: provide a Makefile/justfile or Poetry scripts for common ops (lint, type-check, test, docs, format), add pre-commit configs for Black/Ruff/Mypy, and create contribution templates that reference the new workflow (see CONTRIBUTING.md and release_checklist.md for seed content).

Natural next steps: (1) choose and configure Poetry/pip-compile, update pyproject, and clean the git tree; (2) refactor the configuration/prompt stack so GenAI service can run without hard crashes; (3) stand up CI tests covering the new behavior before iterating on CLI and doc cleanup.
