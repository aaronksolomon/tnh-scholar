---
title: "OpenAI Interface Migration Plan"
description: "Step-by-step plan for migrating from the legacy `openai_interface` module to the typed GenAI Service."
owner: ""
author: ""
status: processing
created: "2025-11-17"
---
# OpenAI Interface Migration Plan

Step-by-step plan for migrating from the legacy `openai_interface` module to the typed GenAI Service.

**Status**: Phase 1 Complete - Utilities Ready
**ADR**: [ADR-A13: Legacy Client Migration](../adr/adr-a13-legacy-client-migration.md)
**Goal**: Delete `openai_interface/` module, use `GenAIService` exclusively

---

## Why Migrate?

| Legacy System | Modern System (GenAIService) |
|--------------|------------------------------|
| Singleton with global state | Dependency injection |
| No type safety | Full Pydantic validation |
| OpenAI-only | Multi-provider ready |
| No provenance tracking | Full metadata & fingerprinting |
| Basic retry | Exponential backoff with tenacity |
| Scattered error handling | Structured exceptions |
| Import-time side effects | Clean initialization |

---

## Quick Start: What Changes?

### Before (Legacy)

```python
from tnh_scholar.openai_interface import (
    run_immediate_completion_simple,
    get_completion_content,
    token_count,
)

# Call with simple params
completion = run_immediate_completion_simple(
    system_message="You are a helpful assistant",
    user_message="Translate this text",
    max_tokens=1000,
)
text = get_completion_content(completion)
tokens = token_count(text)
```

### After (Modern)

```python
from tnh_scholar.gen_ai_service import GenAIService
from tnh_scholar.gen_ai_service.models.domain import RenderRequest, Message
from tnh_scholar.gen_ai_service.utils.token_utils import token_count
from tnh_scholar.gen_ai_service.utils.response_utils import extract_text

# Initialize service
service = GenAIService()

# Create request
request = RenderRequest(
    instruction_key="translate",  # Reference to prompt in catalog
    user_input="Translate this text",
    intent="translation",
)

# Generate completion
envelope = service.generate(request)

# Extract results
text = extract_text(envelope)
tokens = token_count(text)
```

### Migration Adapter (Temporary)

```python
from tnh_scholar.gen_ai_service.adapters.simple_completion import simple_completion

# Easier transition - similar interface to legacy
text = simple_completion(
    system_message="You are a helpful assistant",
    user_message="Translate this text",
    max_tokens=1000,
)
```

---

## File Impact Analysis

### Legacy Module (Removed) ✅

```plaintext
src/tnh_scholar/openai_interface/      ❌ removed
tests/openai_interface/               ❌ removed
```

### Need Migration 🔄

**High Priority** (Core functionality):

- `ai_text_processing/openai_process_interface.py` - Main interface layer
- `ai_text_processing/ai_text_processing.py` - Uses token_count
- `journal_processing/journal_process.py` - Large consumer (28KB)

**Medium Priority** (CLI Tools):

- `cli_tools/token_count/token_count.py` - Simple utility

**Low Priority**:

- (Completed) Removed `audio_processing/transcription_legacy.py`

**Documentation**:

- `notebooks/ai_text_processing/section_processing_tests.ipynb`
- `notebooks/video_processing/postprocessing_english.ipynb`
- `notebooks/video_processing/postprocessing_viet.ipynb`

---

## Migration Phases

### ✅ Phase 0: Quick Wins (Already Done)

- [x] GenAIService implemented
- [x] OpenAI provider adapter working
- [x] Basic tests passing
- [x] Provenance tracking functional

### 🚧 Phase 1: Preparation (2-3 days)

**Create missing utilities in gen_ai_service:**

```python
# gen_ai_service/utils/token_utils.py
def token_count(text: str, model: str = "gpt-4o") -> int
def token_count_messages(messages: List[Message], model: str) -> int
def token_count_file(path: Path, model: str) -> int

# gen_ai_service/utils/response_utils.py
def extract_text(envelope: CompletionEnvelope) -> str
def extract_object(envelope: CompletionEnvelope) -> BaseModel

# gen_ai_service/adapters/simple_completion.py
def simple_completion(
    system_message: str,
    user_message: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    response_format: Optional[Type[BaseModel]] = None,
) -> Union[str, BaseModel]
```

**Implement batch processing:**

```python
# gen_ai_service/batch/
@dataclass
class BatchParams:
    poll_interval: int = 60
    max_wait_time: int = 3600

class GenAIService:
    def batch_generate(
        self,
        requests: List[RenderRequest],
        batch_params: Optional[BatchParams] = None
    ) -> BatchResult:
        """Submit batch requests to provider's batch API."""
```

**Deliverables:**

- [ ] Token utilities with tests
- [ ] Response utilities with tests
- [ ] Simple completion adapter with tests
- [ ] Batch processing with tests

### 🚧 Phase 2: Core Modules (3-4 days)

**Migrate ai_text_processing:**

1. Update `openai_process_interface.py`:

   ```python
   # OLD
   from tnh_scholar.openai_interface import run_immediate_completion_simple

   # NEW
   from tnh_scholar.gen_ai_service.adapters.simple_completion import simple_completion
   ```

2. Update `ai_text_processing.py`:

   ```python
   # OLD
   from tnh_scholar.openai_interface import token_count

   # NEW
   from tnh_scholar.gen_ai_service.utils.token_utils import token_count
   ```

**Migrate journal_processing:**

This is the largest consumer (28KB file). Strategy:

- Create prompts in pattern catalog for journal operations
- Replace openai_interface calls with GenAIService
- Consider refactoring into smaller modules

**Deliverables:**

- [ ] ai_text_processing fully migrated
- [ ] journal_processing fully migrated
- [ ] All existing functionality working
- [ ] Tests updated and passing

### 🚧 Phase 3: CLI Tools (1 day)

**Migrate token-count:**

```python
# cli_tools/token_count/token_count.py

# OLD
from tnh_scholar.openai_interface import token_count_file

# NEW
from tnh_scholar.gen_ai_service.utils.token_utils import token_count_file
```

**Deliverables:**

- [ ] All CLI tools working
- [ ] End-to-end tests passing

### 🚧 Phase 4: Tests (1-2 days)

**Migrate valuable tests:**

- Review 19 tests in `tests/openai_interface/test_openai_interface.py`
- Port behavior tests to `tests/gen_ai_service/`
- Delete implementation-specific tests

**Add new tests:**

- Migration adapters
- Batch processing
- Token utilities
- Response utilities

**Deliverables:**

- [ ] Test coverage maintained or improved
- [ ] All tests passing

### 🚧 Phase 5: Notebooks (1 day)

**Update or archive:**

- Add migration notice to notebook headers
- Update to use GenAIService OR
- Move to `notebooks/legacy/` directory

**Deliverables:**

- [ ] Notebooks updated or documented

### 🚧 Phase 6: Deletion (1 day)

**Final verification:**

```bash
# Search for any remaining imports
grep -r "from tnh_scholar.openai_interface" src/
grep -r "import.*openai_interface" src/

# Should return nothing
```

**Delete legacy code:**

```bash
rm -rf src/tnh_scholar/openai_interface/
rm -rf tests/openai_interface/
```

**Update documentation:**

- README.md - remove legacy references
- Architecture docs
- Create MIGRATION.md guide for users
- Update CHANGELOG.md

**Deliverables:**

- [ ] openai_interface deleted
- [ ] All imports removed
- [ ] Documentation updated
- [ ] Full test suite passing

---

## Testing Strategy

### Unit Tests

- Test each new utility in isolation
- Mock GenAIService for adapter tests
- Test error cases

### Integration Tests

- Test ai_text_processing end-to-end
- Test journal_processing workflows
- Test CLI tools with real prompts

### Regression Tests

- Compare outputs before/after migration
- Verify token counts match
- Check response formats

### Performance Tests

- Benchmark key operations
- Monitor API call patterns
- Track token usage

---

## Rollback Plan

If migration fails:

1. **Git Tags**: Tag each phase completion

   ```bash
   git tag migration-phase-1-complete
   ```

2. **Feature Flags**: Use environment variable during transition

   ```python
   USE_LEGACY_CLIENT = os.getenv("TNH_USE_LEGACY_OPENAI", "false") == "true"
   ```

3. **Branching Strategy**:
   - Main work in `migration/unify-openai-client` branch
   - Merge phases incrementally
   - Can revert specific commits if needed

4. **Keep Legacy in Git History**:
   - Don't delete until migration 100% complete
   - Can cherry-pick from history if needed

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Coverage | ≥ Current (5%) | pytest --cov |
| Performance | Within 10% of legacy | Benchmark script |
| Token Usage | No increase | Monitor API costs |
| Error Rate | ≤ Legacy rate | Error tracking |
| Migration Complete | 100% | No legacy imports |

---

## Communication Plan

### Internal Team

- Announce migration start
- Daily progress updates
- Flag any blockers immediately

### External (if applicable)

- Migration guide in docs
- Deprecation warnings in code
- Version bump to indicate breaking change

---

## FAQ

**Q: Can I use GenAIService and legacy client together?**
A: During migration, yes. But the goal is to eliminate legacy entirely.

**Q: What if I need a feature that only exists in legacy?**
A: Document it in the ADR and implement in GenAIService before migrating that code.

**Q: Will this affect API costs?**
A: No. Same OpenAI calls, just better organized. May actually reduce costs due to better caching/retry logic.

**Q: What about batch processing?**
A: Will be implemented in Phase 1. May have different interface but same functionality.

**Q: Do I need to update my prompts?**
A: Possibly. Prompts should move to the pattern catalog for better management.

**Q: What if something breaks?**
A: Use git tags to roll back to last working phase. Report issues immediately.

---

## Next Steps

1. **Review ADR-A13** - Understand full context and rationale
2. **Estimate effort** - Confirm timeline for your specific modules
3. **Start Phase 1** - Create utilities and adapters
4. **Test incrementally** - Don't wait until end to test
5. **Document issues** - Track problems and solutions
6. **Celebrate** - Delete legacy code when done! 🎉

---

## Resources

- **Full ADR**: [ADR-A13-legacy-client-migration.md](../adr/adr-a13-legacy-client-migration.md)
- **GenAIService docs**: [ADR-A01-domain-service.md](../adr/adr-a01-domain-service.md)
- **Pattern Catalog**: [ADR-A02-pattern-catalog-v1.md](../adr/adr-a02-pattern-catalog-v1.md)
- **Example usage**: `tests/gen_ai_service/test_service.py`

---

**Questions or concerns?** Add them to the ADR or TODO.md for tracking.
