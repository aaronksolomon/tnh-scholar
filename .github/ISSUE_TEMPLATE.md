# Issue Template for TNH Scholar (Agents)

> Use for GitHub issues via `gh issue create` or tracking design/bugs.

---

## Issue Title
[Concise description]

---

## Type
- [ ] Bug
- [ ] Feature
- [ ] Architectural issue
- [ ] Technical debt
- [ ] Documentation

---

## Context (User-Facing)
**What happens**:  
[Concrete behavior]

**Expected**:  
[Desired behavior]

**Impact**:  
Severity: [Critical/High/Medium/Low]  
Affected use cases: [List]  
Workarounds: [None/Manual/Other]

---

## Discovery + Repro
**Discovered via**: [Testing/Usage/Review/VS Code test]  
**Reproducible**: [Always/Intermittent/Env-specific]

```
Minimal repro (command, code, or scenario)
```

---

## Technical Analysis
**Location(s)**: [`src/.../file.py:line`]  
**Root cause**: [Core issue]  
**Why it happens**: [Design/architecture reason]

**Flow (optional)**:
```
Input → Step → Output (what is missing/broken)
```

**Affected modules**:
- [ ] cli_tools/tnh_gen/
- [ ] gen_ai_service/
- [ ] ai_text_processing/
- [ ] metadata/
- [ ] prompt_system/
- [ ] vscode-extension/
- [ ] Other: ___________

**Existing infrastructure to reuse**: [Classes/utils]

---

## Architectural Considerations (if applicable)
**Concern areas**:
- [ ] Metadata strategy
- [ ] Data flow between components
- [ ] Type system/domain modeling
- [ ] Configuration management
- [ ] Provenance/traceability
- [ ] Object-service compliance
- [ ] Other: ___________

**Open questions**:
1. [Question]
2. [Question]

**Cross-cutting impacts**: [Metadata conflicts, downstream effects, etc.]

---

## Solution Options
### Option A (Tactical)
Approach: [Short fix]  
Pros: [Benefits]  
Cons: [Risks]  
Complexity: [Low/Medium/High]

### Option B (Strategic)
Approach: [Design-level fix]  
Requires: [ADR / refactor / integration]  
Pros: [Benefits]  
Cons: [Risks]  
Complexity: [Medium/High/Very High]

### Option C (Optional)
[Alternative if needed]

---

## Recommendation
**Proposed path**:
1. Immediate: [Mitigation if critical]
2. Phase 1: [Tactical]
3. Phase 2: [Strategic/ADR]

**Open questions**:
- [ ] Question 1
- [ ] Question 2

---

## Related Work
**ADRs**:
- [ADR-XX: Title](/architecture/category/adr/adr-xx-title.md)

**Docs/Refs**:
- [Doc section to update]
- [Prior art/internal utilities]
- [External precedent/spec]

---

## Acceptance Criteria
- [ ] [Testable outcome 1]
- [ ] [Testable outcome 2]
- [ ] Docs updated
- [ ] Tests added/updated
