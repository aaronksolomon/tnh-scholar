# Agent Session Template

This file specifies the format for AGENTLOG files which captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. These provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

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

## Session History (Most Recent First)

---
