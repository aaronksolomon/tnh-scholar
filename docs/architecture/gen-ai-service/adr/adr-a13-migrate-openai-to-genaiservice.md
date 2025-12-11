---
title: "ADR-A13: Migrate All OpenAI Interactions to GenAIService"
description: "Retires the legacy OpenAI client and standardizes every caller on the typed GenAI Service pipeline."
owner: ""
author: "Aaron Solomon, Claude AI (Sonnet 4.5)"
status: current
created: "2025-11-17"
---
# ADR-A13: Migrate All OpenAI Interactions to GenAIService

Consolidates all OpenAI usage onto GenAI Service to eliminate the brittle legacy singleton client and keep parity.

**Status:** Proposed
**Date:** 2025-11-16
**Author:** Aaron Solomon with Claude AI (Sonnet 4.5)
**Supersedes:** Legacy openai_interface module usage

## Context

TNH Scholar currently has two parallel implementations for OpenAI interactions:

1. **Legacy System** (`openai_interface/`):
   - Singleton pattern with global state
   - Direct OpenAI SDK calls
   - Import-time `load_dotenv()` side effects
   - Used by: ai_text_processing, audio_processing, journal_processing, CLI tools
   - ~27KB monolithic openai_interface.py file
   - Batch processing support (run_oa_batch_jobs.py)
   - Token counting utilities

2. **Modern System** (`gen_ai_service/`):
   - Object-Service pattern (ADR-A01)
   - Typed domain models with Pydantic
   - Provider abstraction layer
   - Provenance tracking and fingerprinting
   - Retry logic with tenacity
   - Proper exception handling
   - Currently used only in tests

This duplication creates several problems:

**Code Divergence**: Bug fixes and improvements must be applied to both systems, leading to inconsistency and maintenance burden.

**Configuration Complexity**: Two different configuration approaches (singleton with env vars vs. Pydantic Settings) create confusion and potential bugs.

**Limited Extensibility**: Legacy code is tightly coupled to OpenAI, making multi-provider support (Anthropic, etc.) difficult.

**Testing Challenges**: Singleton pattern makes unit testing harder; need to mock global state.

**Architectural Inconsistency**: New features use GenAIService while existing features use legacy client, creating a fragmented codebase.

## Decision

**We will migrate all OpenAI interactions to use GenAIService as the exclusive interface for LLM provider calls.**

This migration will:

1. **Establish GenAIService as the Single Point of Entry** for all LLM interactions
2. **Delete the legacy openai_interface module** entirely after migration
3. **Update all consumers** (ai_text_processing, audio_processing, CLI tools) to use GenAIService
4. **Preserve essential functionality** (batch processing, token counting) by implementing adapters or utilities within gen_ai_service
5. **Maintain no backward compatibility** - this is a breaking change requiring all callsites to update

### Architectural Principle

**All consumers must go through GenAIService, not use openai_client directly.**

This creates maximum flexibility for:
- Multi-provider routing
- Policy application
- Safety filtering
- Provenance tracking
- Retry/fallback logic
- Future enhancements

## Implementation Plan

### Phase 1: Preparation & Groundwork

**Objective**: Ensure GenAIService has feature parity with legacy system

#### 1.1 Add Missing Utilities to gen_ai_service

**Location**: `src/tnh_scholar/gen_ai_service/utils/`

- [ ] **Token counting utilities**
  - Extract from `openai_interface.token_count()`
  - Use tiktoken with model-specific encodings
  - Support batch token counting for lists
  - File: `gen_ai_service/utils/token_utils.py`

- [ ] **Response extraction helpers**
  - Equivalent to `get_completion_content()`, `get_completion_object()`
  - Extract text from CompletionEnvelope
  - Extract structured objects from responses
  - File: `gen_ai_service/utils/response_utils.py`

#### 1.2 Implement Batch Processing Support

**Location**: `src/tnh_scholar/gen_ai_service/batch/`

The legacy system supports OpenAI Batch API via `run_single_batch()` and `run_oa_batch_jobs.py`. We need equivalent functionality.

**Options**:

**Option A**: Implement within GenAIService
- Add `batch_generate()` method to GenAIService
- Create `BatchRequest` and `BatchResponse` domain models
- Manage batch job lifecycle (submit, poll, retrieve)
- PRO: Unified interface, better abstraction
- CON: More initial implementation work

**Option B**: Create separate BatchService
- Standalone service for batch operations
- Still uses GenAIService internally for individual items
- PRO: Separation of concerns, clearer responsibilities
- CON: Another service to manage

**Option C**: Adapter pattern
- Create `LegacyBatchAdapter` that wraps GenAIService
- Maintains similar interface to `run_single_batch()`
- PRO: Easier migration, minimal refactoring
- CON: Less clean architecture

**Decision**: Use **Option A** (implement within GenAIService)
- Better long-term architecture
- Batch is a core LLM interaction pattern
- Allows for future multi-provider batch support

**Implementation**:
```python
# gen_ai_service/service.py
def batch_generate(
    self,
    requests: List[RenderRequest],
    batch_params: Optional[BatchParams] = None
) -> BatchResult:
    """Submit batch of requests to provider's batch API."""
    # Create batch job
    # Poll for completion
    # Return results with provenance
```

#### 1.3 Create Migration Adapters

**Location**: `src/tnh_scholar/gen_ai_service/adapters/`

To ease migration, create adapters that provide legacy-like interfaces backed by GenAIService:

**File**: `gen_ai_service/adapters/simple_completion.py`
```python
def simple_completion(
    system_message: str,
    user_message: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    response_format: Optional[Type[BaseModel]] = None,
) -> Union[str, BaseModel]:
    """
    Simple completion interface for easier migration.

    Wraps GenAIService.generate() with a simpler API.
    """
    # Create GenAIService
    # Build RenderRequest
    # Call generate()
    # Extract and return result
```

This allows gradual migration with minimal disruption.

### Phase 2: Migrate Core Modules

**Objective**: Update core text processing and audio processing modules

#### 2.1 Migrate ai_text_processing/openai_process_interface.py

**Current dependencies**:
```python
from tnh_scholar.openai_interface import (
    get_completion_content,
    get_completion_object,
    run_immediate_completion_simple,
    run_single_batch,
    token_count,
)
```

**Migration strategy**:
1. Replace with GenAIService import
2. Update `openai_process_text()` to use GenAIService
3. Use simple_completion adapter initially, then refactor to proper RenderRequest

**Files to update**:
- `ai_text_processing/openai_process_interface.py`
- `ai_text_processing/ai_text_processing.py` (imports token_count)

#### 2.2 Migrate audio_processing

**Files to update**:
***Removed***
- `audio_processing/transcription_legacy.py`

**Note**: This appears to be legacy code (filename suggests it). Evaluate if it should be deleted instead of migrated.

#### 2.3 Migrate journal_processing

**Files to update**:
- `journal_processing/journal_process.py` (28KB - largest consumer)

**Strategy**:
- This is a large file with complex processing
- Create specialized prompts in pattern catalog
- Break into smaller functions using GenAIService
- Consider refactoring as part of Priority 3 task (monolithic module refactoring)

### Phase 3: Migrate CLI Tools

**Objective**: Update all CLI tools to use GenAIService

#### 3.1 Migrate token-count CLI

**File**: `cli_tools/token_count/token_count.py`

**Current**: Uses `openai_interface.token_count()`
**Update**: Use `gen_ai_service/utils/token_utils.py`

Simple utility migration.

#### 3.2 Update other CLI tools

**Verify usage**: Check if any other CLI tools import openai_interface
- Most CLI tools currently use legacy ai_text_processing
- They'll automatically use GenAIService once ai_text_processing is migrated
- No direct updates needed

### Phase 4: Update Tests

**Objective**: Migrate or delete legacy tests

#### 4.1 Migrate useful tests

**File**: `tests/openai_interface/test_openai_interface.py`

**Strategy**:
- Review 19 existing tests
- Migrate valuable test cases to test GenAIService equivalents
- Focus on behavior, not implementation
- Add to `tests/gen_ai_service/`

#### 4.2 Delete obsolete tests

Tests tightly coupled to singleton pattern or internal implementation details can be deleted.

### Phase 5: Handle Notebooks

**Objective**: Update or document notebook status

**Files**:
- `notebooks/ai_text_processing/section_processing_tests.ipynb`
- `notebooks/video_processing/postprocessing_english.ipynb`
- `notebooks/video_processing/postprocessing_viet.ipynb`

**Strategy**:
- Add migration notice at top of each notebook
- Either update to use GenAIService or mark as legacy/archived
- Consider moving to `notebooks/legacy/` directory

### Phase 6: Deletion & Cleanup

**Objective**: Remove legacy code and update documentation

#### 6.1 Delete openai_interface module

Once all migrations are complete:
```bash
rm -rf src/tnh_scholar/openai_interface/
```

**Files to delete**:
- `openai_interface/openai_interface.py` (27KB)
- `openai_interface/run_oa_batch_jobs.py`
- `openai_interface/__init__.py`
- `openai_interface/gpt_batch_files/` (if present)
- `tests/openai_interface/`

#### 6.2 Update imports

Search for any remaining imports:
```bash
grep -r "from tnh_scholar.openai_interface" src/
grep -r "import.*openai_interface" src/
```

Ensure all are removed.

#### 6.3 Update documentation

- Update README.md to mention only GenAIService
- Update architecture docs
- Create migration guide for any external users

## Implementation Checklist

### Phase 1: Preparation ✅ / 🚧 / ⬜

- [ ] Create `gen_ai_service/utils/token_utils.py`
  - [ ] Implement `token_count(text, model)`
  - [ ] Implement `token_count_messages(messages, model)`
  - [ ] Implement `token_count_file(path, model)`
  - [ ] Add tests

- [ ] Create `gen_ai_service/utils/response_utils.py`
  - [ ] Implement `extract_text(envelope: CompletionEnvelope) -> str`
  - [ ] Implement `extract_object(envelope: CompletionEnvelope) -> BaseModel`
  - [ ] Add tests

- [ ] Create `gen_ai_service/batch/`
  - [ ] Define `BatchRequest`, `BatchResponse`, `BatchParams` models
  - [ ] Implement `GenAIService.batch_generate()`
  - [ ] Add batch job polling logic
  - [ ] Add tests for batch processing

- [ ] Create `gen_ai_service/adapters/simple_completion.py`
  - [ ] Implement `simple_completion()` function
  - [ ] Implement `batch_completion()` function
  - [ ] Add tests

- [ ] Update documentation
  - [ ] Document new utilities
  - [ ] Create migration guide draft
  - [ ] Add examples

### Phase 2: Core Modules ⬜

- [ ] Migrate `ai_text_processing/openai_process_interface.py`
  - [ ] Update imports
  - [ ] Refactor `openai_process_text()` to use GenAIService
  - [ ] Update tests
  - [ ] Verify all callsites work

- [ ] Migrate `ai_text_processing/ai_text_processing.py`
  - [ ] Update token_count imports
  - [ ] Verify ProcessedSection and related classes work
  - [ ] Run integration tests

    - [x] Evaluate `audio_processing/transcription_legacy.py` (deleted)
  - [ ] Decide: migrate or delete?
  - [ ] If migrate: update to use GenAIService
  - [ ] If delete: remove file and references

- [ ] Migrate `journal_processing/journal_process.py`
  - [ ] Audit current usage patterns
  - [ ] Create necessary prompts in pattern catalog
  - [ ] Update to use GenAIService
  - [ ] Consider refactoring (large file)
  - [ ] Add tests

### Phase 3: CLI Tools ⬜

- [ ] Migrate `cli_tools/token_count/token_count.py`
  - [ ] Update imports to use token_utils
  - [ ] Test CLI command
  - [ ] Update CLI documentation

- [ ] Audit other CLI tools
  - [ ] Verify no direct openai_interface usage
  - [ ] Test end-to-end workflows

### Phase 4: Tests ⬜

- [ ] Review `tests/openai_interface/test_openai_interface.py`
  - [ ] Identify valuable test cases
  - [ ] Migrate to `tests/gen_ai_service/`
  - [ ] Rewrite using GenAIService

- [ ] Add new tests
  - [ ] Test migration adapters
  - [ ] Test batch processing
  - [ ] Test token utilities

### Phase 5: Notebooks ⬜

- [ ] Update `notebooks/ai_text_processing/section_processing_tests.ipynb`
- [ ] Update `notebooks/video_processing/postprocessing_english.ipynb`
- [ ] Update `notebooks/video_processing/postprocessing_viet.ipynb`
- [ ] Consider creating `notebooks/legacy/` directory

### Phase 6: Deletion & Cleanup ⬜

- [ ] Final verification
  - [ ] Search for any remaining openai_interface imports
  - [ ] Run full test suite
  - [ ] Test all CLI tools end-to-end

- [ ] Delete legacy code
  - [ ] Delete `src/tnh_scholar/openai_interface/`
  - [ ] Delete `tests/openai_interface/`
  - [ ] Update .gitignore if needed

- [ ] Update documentation
  - [ ] Update README.md
  - [ ] Update architecture docs
  - [ ] Create MIGRATION.md guide
  - [ ] Update CHANGELOG.md

- [ ] Update TODO.md
  - [ ] Mark task #5 as complete
  - [ ] Update progress summary

## Benefits

1. **Single Source of Truth**: All LLM interactions go through one well-designed service
2. **Better Testability**: No singletons, proper dependency injection
3. **Multi-Provider Ready**: GenAIService already has provider abstraction
4. **Provenance & Observability**: All completions tracked with metadata
5. **Type Safety**: Pydantic models throughout
6. **Better Error Handling**: Structured exceptions vs. string errors
7. **No Global State**: All configuration passed explicitly
8. **Retry Logic**: Built-in retry with exponential backoff
9. **Easier Maintenance**: Single codebase to maintain
10. **Future-Proof**: Architecture supports upcoming features (safety, routing, caching)

## Risks & Mitigation

### Risk 1: Breaking Changes

**Impact**: Existing code will break
**Mitigation**:
- Provide migration adapters for smooth transition
- Document all changes thoroughly
- Migrate incrementally with tests at each step

### Risk 2: Batch Processing Complexity

**Impact**: Batch API integration is non-trivial
**Mitigation**:
- Start with simple batch implementation
- Test thoroughly with small batches
- Document limitations clearly
- Consider async patterns for better UX

### Risk 3: Performance Differences

**Impact**: New code might have different performance characteristics
**Mitigation**:
- Benchmark before/after
- Monitor token usage and costs
- Profile slow operations
- Optimize hot paths

### Risk 4: Missing Features

**Impact**: Legacy system might have features we haven't identified
**Mitigation**:
- Thorough code audit before deletion
- Keep legacy code in git history
- Document all legacy functionality
- Create feature parity checklist

## Timeline Estimate

**Phase 1 (Preparation)**: 2-3 days
- Utilities and adapters are straightforward
- Batch processing needs careful design

**Phase 2 (Core Modules)**: 3-4 days
- journal_process.py is complex (28KB)
- Need to create prompts in catalog
- Thorough testing required

**Phase 3 (CLI Tools)**: 1 day
- Mostly indirect through ai_text_processing
- Simple utility migration

**Phase 4 (Tests)**: 1-2 days
- Migrate valuable tests
- Add new coverage

**Phase 5 (Notebooks)**: 1 day
- Update or document

**Phase 6 (Cleanup)**: 1 day
- Verification and documentation

**Total**: ~9-13 days of focused work

Can be done incrementally while maintaining working system.

## Success Criteria

- [ ] All uses of `openai_interface` removed from src/
- [ ] All uses of `openai_interface` removed from tests/
- [ ] `openai_interface/` directory deleted
- [ ] All CLI tools working with GenAIService
- [ ] All tests passing
- [ ] Test coverage maintained or improved
- [ ] Documentation updated
- [ ] No regression in functionality
- [ ] Performance acceptable (within 10% of legacy)
- [ ] Migration guide written

## Related ADRs

- [ADR-A01: Object-Service Pattern](/architecture/gen-ai-service/adr/adr-a01-object-service-genai.md) - Architectural foundation
- [ADR-A02: Pattern Catalog V1](/architecture/gen-ai-service/adr/adr-a02-patterncatalog-integration-v1.md) - Prompt management
- [ADR-A08: Config Params Policy](/architecture/gen-ai-service/adr/adr-a08-config-params-policy-taxonomy.md) - Configuration approach
- [ADR-A09: V1 Simplified](/architecture/gen-ai-service/adr/adr-a09-v1-simplified.md) - Current implementation

## References

- Legacy implementation: `src/tnh_scholar/openai_interface/openai_interface.py`
- Modern implementation: `src/tnh_scholar/gen_ai_service/service.py`
- Provider abstraction: `src/tnh_scholar/gen_ai_service/providers/`
- Existing tests: `tests/gen_ai_service/test_service.py`

## Notes

This is a significant refactoring but sets the foundation for:
- Multi-provider support (Anthropic, etc.)
- Advanced features (caching, routing, safety)
- Better observability and debugging
- Cleaner, more maintainable codebase

The investment in proper migration now will pay dividends as we add new LLM providers and capabilities.
