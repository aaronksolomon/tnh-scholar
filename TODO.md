# TNH Scholar TODO List

## Package API Definition
**Priority**: Low (Code Quality)  
**Status**: Deferred during prototyping

### Description
Implement `__all__` declarations to define public APIs and resolve F401 warnings.

### Tasks
- [ ] Review and document all intended public exports
- [ ] Implement `__all__` in key `__init__.py` files:
  - [ ] src/tnh_scholar/ai_text_processing/__init__.py
  - [ ] [Additional __init__.py files to be identified]
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