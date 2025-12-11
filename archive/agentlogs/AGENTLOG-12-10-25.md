# Agent Session Log

This file captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. It provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

One AGENTLOG file is intended to be kept per branch/dev/refactor/issue push, and archived on completion of work.

## Format Specification

Each entry must follow this structure:

```markdown
## [YYYY-MM-DD HH:MM TZ] Session Title

**Agent**: [Model/System descriptor] (e.g., Claude Sonnet 4.5, GPT-4, Custom Agent)
**Chat Reference**: [Session name/ID if applicable] (e.g., "docs-reorg-planning", PR #123)
**Human Collaborator**: [Name/identifier if different from repo owner]

### Context
Brief description of what prompted this session and relevant background.

### Key Decisions
- **Decision Title**: One-line summary of choice and rationale
- **Decision Title**: One-line summary of choice and rationale

### Work Completed
- [x] Task description (files: `path/to/file.py`, `path/to/other.md`)
- [x] Task description (files: `config.yaml`)

### Discoveries & Insights
- **Finding Title**: One-line description of insight or implication
- **Finding Title**: One-line description of insight or implication

### Files Modified/Created
- `path/to/file.py`: Description of changes
- `path/to/newfile.md`: Created - purpose

### Next Steps
- [ ] Follow-up task 1
- [ ] Follow-up task 2

### Open Questions
- Question 1 requiring human input or future exploration
- Question 2 requiring human input or future exploration

### References
- Links to relevant ADRs, issues, PRs, docs
---
```

### Field Guidelines

- **DateTime Format**: `YYYY-MM-DD HH:MM TZ` (e.g., `2025-11-23 14:30 UTC`)
- **Agent**: Include model name and version when known
- **Chat Reference**: Optional; use descriptive names for multi-session threads
- **Context**: 2-3 sentences max; link to ADRs/issues for details
- **Key Decisions**: **Title**: One-line summary (see ADRs for full rationale)
- **Work Completed**: Single-line task descriptions with file paths in parentheses
- **Discoveries**: **Title**: One-line insight or implication
- **Files Modified/Created**: Comprehensive list with single-line change descriptions
- **Next Steps**: Single-line immediate follow-ups (use `[ ]` for incomplete)
- **Open Questions**: Single-line questions/blockers/deferred decisions
- **References**: Links to ADRs, GitHub issues/PRs, external docs

---

## Branch work: gen-ai-core-stubs

## Session History (Most Recent on Top)

## [2025-01-07 15:45 UTC] Core stub implementation and hardening

**Agent**: Codex (GPT-5 based)
**Chat Reference**: core-stubs-merge-ready
**Human Collaborator**: phapman

### Context

Implement and harden GenAI core stubs (policy, routing, safety, mapper) per ADR-A08/A09/A11 with follow-up polish before merge.

### Key Decisions

- Default pricing moved into Settings (`price_per_1k_tokens`) while leaving registry extraction to ADR-A14 follow-up.
- Capability lookup made case-insensitive; structured fallback ignores provider until registry lands.
- Safety pre-check keeps collected warnings (no reset) and surfaces coercion/ignored content.

### Work Completed

- [x] Implemented policy precedence with settings cache, prompt metadata, and routing reason diagnostics (file: `src/tnh_scholar/gen_ai_service/config/params_policy.py`)
- [x] Added capability-aware routing with structured fallbacks and case-insensitive lookup (file: `src/tnh_scholar/gen_ai_service/routing/model_router.py`)
- [x] Safety gate: size/context/budget guards, content coercion warnings, pricing from settings, preserved warnings (file: `src/tnh_scholar/gen_ai_service/safety/safety_gate.py`)
- [x] Completion mapper: structured error propagation, `PolicyApplied` alias, null-safe error message (file: `src/tnh_scholar/gen_ai_service/mappers/completion_mapper.py`)
- [x] Settings: validator uses shared context limits, added TODOs for registry/pricing; hard-stop on missing API key in service (files: `src/tnh_scholar/gen_ai_service/config/settings.py`, `src/tnh_scholar/gen_ai_service/service.py`)
- [x] Expanded tests for policy precedence, router behavior, safety guards/warnings, post-check; updated TODOs and ADR links (files: `tests/gen_ai_service/test_policy_routing_safety.py`, `tests/gen_ai_service/test_completion_mapper.py`, `TODO.md`, `docs/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md`)

### Discoveries & Insights

- Token counting assumes iterable message content; non-string list coercion works, but true non-iterable content will still raise upstream (accepted for now).
- Routing diagnostics remain string-based; promoting a structured type for `policy_applied` will ripple and is deferred.

### Files Modified/Created

- `src/tnh_scholar/gen_ai_service/config/params_policy.py`: Policy precedence, docstrings, routing diagnostics.
- `src/tnh_scholar/gen_ai_service/routing/model_router.py`: Capability map, case-insensitive lookup, structured fallback, refined copy.
- `src/tnh_scholar/gen_ai_service/safety/safety_gate.py`: SafetyReport, warnings preserved, pricing from settings, docstrings.
- `src/tnh_scholar/gen_ai_service/mappers/completion_mapper.py`: PolicyApplied alias, error handling, docstrings.
- `src/tnh_scholar/gen_ai_service/config/settings.py`: Context-limit validator import, pricing setting, registry TODOs.
- `src/tnh_scholar/gen_ai_service/service.py`: Fail-fast on missing API key.
- `docs/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md`: Link fixes, “addenda” wording.
- `tests/gen_ai_service/test_policy_routing_safety.py`: Expanded coverage (policy, routing, safety, post_check).
- `tests/gen_ai_service/test_completion_mapper.py`: Updated timestamps, mapper tests.
- `TODO.md`: Marked completed high-priority items, added policy_applied typing follow-up.

### Next Steps

- [ ] Promote `policy_applied` to a shared domain type (`CompletionEnvelope`) for consistent typing.
- [ ] Implement registry-backed capabilities/pricing per ADR-A14 and refactor routing/safety to consume it.
- [ ] Consider structured routing diagnostics instead of strings.

### Open Questions

- Should non-iterable message content be rejected earlier in the pipeline vs. warning at safety gate?
- Preferred shape for policy diagnostics (typed model vs. dict) when promoting to domain?

### References

- ADR-A08, ADR-A09, ADR-A11, ADR-A14 (file-based registry system) ***
