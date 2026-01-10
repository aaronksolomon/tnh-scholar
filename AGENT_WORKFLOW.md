---
title: "Agent Development Workflow"
description: "Dual-agent workflow for TNH Scholar development - task discovery through post-merge cleanup."
owner: ""
author: "aaronksolomon, Claude Sonnet 4.5"
status: current
created: "2025-12-28"
updated: "2026-01-01"
---
# Agent Development Workflow

**Agent Abbreviations:** CC = Claude Code, CO = Codex

**Workflow Type:** Iterative loop. **Exit conditions**: All CI green, docs updated, merged → next task. **Continue**: Issues discovered → restart from Step 1. **Blocked**: External dependency → document in TODO.md.

**Single-agent mode:** If only one agent available, that agent performs both roles (design + implementation). User must carefully review all work due to reduced independent validation.

## Role Definitions

**CC (Claude Code)**: Design-focused mindset

**CO (Codex)**: Implementation-focused mindset

**IMPORTANT:** User is 'glue' between agents and will share results of each action with the other agents. It can be helpful to keep this in mind when reporting on work completed.

---

## 1. Task Discovery

**Who:** CO
**Action:** If user request is explicit, treat it as the task. Otherwise review `TODO.md` to identify next task (priority order or most appropriate based on context).

**Output:** Task description and scope identified.

---

## 2. Initial Design

**Who:** CC
**Prerequisites:** Task scope clear from Discovery phase.

**Decision Tree:**

| Task Type | Action |
|-----------|--------|
| **Simple design** (single component/feature) | Draft single ADR using `docs/docs-ops/adr-template.md` |
| **Complex design** (large module, strategic direction, multiple sub-components) | Draft strategy ADR with sub-ADR roadmap |
| **Bug fix or patch** | Ask CC + CO: Does this require architectural re-evaluation? If YES → draft ADR addendum or decimal sub-ADR. If NO → skip to Implementation. |

**Requirements:**

- Reference `docs/docs-ops/adr-template.md` for ADR structure
- Follow object-service pattern (ADR-OS01) for GenAI code
- Observe all constraints in `AGENTS.md` (typing, config taxonomy, etc.)
- Review all related ADRs and project documentation that bear on scope of work.

**Output:** ADR draft in `proposed` status OR task ready for implementation (no ADR needed).

---

## 3. Design Review

**Who:** CC + CO (independent reviews), then User (final approval)
**Prerequisites:** ADR drafted OR architectural concerns raised during bug fix analysis.

**Process:**

1. **Agent Reviews (Independent)**
   - CC reviews ADR against:
     - Design principles (`docs/development/design-principles.md`)
     - Style guide (`docs/development/style-guide.md`)
     - Relevant existing ADRs
     - Architectural patterns (Object-Service, etc.)
   - CO reviews ADR against:
     - Implementation feasibility
     - Current codebase patterns
     - Technical complexity and risks
     - Testing strategy
   - **Single-agent mode**: Review sequentially from both perspectives:
     1. First pass: Design principles and patterns (CC mindset)
     2. Second pass: Implementation feasibility (CO mindset)
     3. Compare findings for conflicts or gaps

2. **Issue Resolution**
   - CC/CO identify and repair issues in ADR
   - **If blocking issues discovered:**
     - Add to `TODO.md` as blocking issue
     - **RESTART workflow from step 1** (blocking issue becomes new priority)
   - **If issue requires full redesign:**
     - Mark ADR as `superseded` or `rejected` (per ADR template)
     - Create new ADR (or restart design from scratch)
     - **RESTART workflow from step 1** with the new design task
   - **If issue requires blocking research:**
     - Create a research task in `TODO.md` with explicit questions
     - Pause design until research completes
     - **RESTART workflow from step 1** after research
   - **If non-blocking issues discovered:**
     - Document in ADR "Future Considerations"
     - Add to `TODO.md` under appropriate section
   - Make corrections/fixes as needed, iterate until agents agree

3. **User Review**
   - CC and CO present findings to user
   - User reviews ADR and agent feedback
   - User may request additional changes → return to step 2
   - User provides final approval or rejection

4. **Status Update (User-Authorized)**
   - **When user gives green light:**
     - CC updates ADR status: `proposed` → `accepted`
     - Update ADR `updated` date in frontmatter
     - Commit ADR status change
   - **If user rejects:**
     - Mark ADR as `rejected` with rationale
     - Return to step 1 if redesign needed

**Output:** ADR in `accepted` status (ready for implementation) OR `rejected` status (restart design).

---

## 4. Implementation

**Who:** CO (primary), CC (oversight)
**Prerequisites:** ADR accepted OR simple task scope confirmed.

### 4.1 Start Implementation

- **If ADR exists:** Move status `accepted` → `wip` at implementation start
- CO implements feature/fix (may require multiple iterations for large scope)
- CO develops tests concurrently with implementation:
  - Aim for 100% coverage of critical paths (subjective judgment)
  - Use TDD where applicable: write failing tests → implement → refactor
  - Coverage is qualitative, not numerical - focus on edge cases and integration points
- CO runs tests after each iteration

### 4.2 Handle Mid-Implementation Issues

**Architectural changes discovered:**

- **Small change:** CC creates addendum to current WIP ADR
- **Large change:** CC drafts decimal sub-ADR (e.g., ADR-XX.1)

**Out-of-scope issues discovered:**

- **Significant issue:**
  - Create GitHub issue
  - Add to `TODO.md` with appropriate priority
- **Small issue:**
  - Note in `TODO.md` under relevant section, OR
  - Add inline `# TODO:` comment in `.py` file
- **Blocking issue:**
  - Mark in `TODO.md` as blocking current work
  - **RESTART workflow from step 1**

### 4.3 Logging

- CO logs each change round in `AGENTLOG.md` (incremental updates)

**Output:** Feature/fix implemented with tests passing.

---

## 5. Review, Correct, Finalize

**Who:** CC (review), CO (corrections)

### 5.1 Code Review

**CC Actions:**

1. Review all changes against ADR requirements (if ADR exists)
2. Run Sourcery on all modified `.py` files:

   ```bash
   poetry install --with local
   poetry run sourcery review --check <changed-files.py>
   ```

3. Summarize issues found

**CO Actions:**

- Fix issues identified by CC review + Sourcery
- Log corrections in `AGENTLOG.md`

### 5.2 CI Validation

**CC Action:** Run full CI check:

```bash
make ci-check
```

**CO Action:** Repair ALL issues until checks pass:

- ✅ No typing errors (`poetry run mypy`)
- ✅ No Sourcery issues
- ✅ No documentation issues (`make docs-verify`)
- ✅ All tests passing (`make test`)

### 5.3 Documentation Review

**CC Actions:**

1. Assess documentation needs:
   - Migration plans (breaking changes)
   - Feature descriptions (new capabilities)
   - CLI reference updates (command changes)
   - Usage guides (new workflows)

2. Create documentation as needed following `docs/docs-ops/markdown-standards.md`

**Output:** All CI checks green, documentation complete.

---

## 6. Commit & PR

**Who:** CC
**Prerequisites:** All CI checks passing, documentation complete.

### 6.1 Branch Management

- Create feature branch if not already open
- Branch naming: `feat/<feature>`, `fix/<issue>`, `docs/<topic>`

### 6.2 Commit Organization

- Organize commits logically (conventional commits format)
- **Ensure docs (.md files) have YAML frontmatter** with provenance (see ADR-TG01, markdown-standards.md)
- **WAIT for user approval** before committing (user reviews changes in VS Code)
- After commits, update tracking files:
  - `CHANGELOG.md` (add `## [Unreleased]` section)
  - `TODO.md` (mark completed tasks)
  - Commit tracking updates: `chore: Update CHANGELOG and TODO for <feature>`

### 6.3 Pull Request

**For features (not simple patches/fixes):**

- Create PR with `gh pr create`
- Include ADR reference in PR description
- **WAIT for user review and signoff**

**User actions:**

- Reviews PR
- Approves changes
- Requests CC to merge

**CC actions (on user request):**

- Merge PR to main

**Output:** Changes merged to main OR committed directly (simple fixes).

---

## 7. Post-Merge Cleanup

**Who:** CC
**Prerequisites:** PR merged OR commits pushed to main.

**Actions (in order):**

1. **Delete working branch** (if PR was merged from feature branch)

2. **ADR Status Updates**
   - Standard ADRs: `accepted` → `implemented` (or `wip` → `implemented` if marked during work)
   - Strategy ADRs: Keep in `accepted` status
   - See ADR template for full status lifecycle: `proposed` → `accepted` → [`wip`] → `implemented`

3. **Archive AGENTLOG** (after feature PR merge only)
   - Archive to `archive/agentlogs/AGENTLOG-[MM-DD-YY].md`
   - Update `archive/agentlogs/archive-index.md` with summary
   - Reset `AGENTLOG.md` to template
   - **Skip for**: Hotfixes, patches, chores, routine changes

4. **Update CHANGELOG.md**
   - Move `## [Unreleased]` items to versioned section (if release)
   - Ensure all changes documented

5. **Update TODO.md**
   - Mark completed tasks with `✅` or `[x]`
   - Remove obsolete tasks
   - Update status indicators
   - Update `updated` date in frontmatter

**Output:** Repository documentation synchronized with code changes.

---

## 8. Hotfix Workflow (Direct to Main)

**Who:** CC
**When:** Critical bug or issue requiring immediate patch to main (bypasses PR process).

**Prerequisites:**

- Issue identified that requires hotfix (security vulnerability, critical bug, broken build)
- User approval to proceed with hotfix workflow

**Process:**

1. **Identify and confirm hotfix needed**
   - Verify issue severity warrants direct-to-main patch
   - Get user confirmation to proceed

2. **Implement fix**
   - Make minimal changes to resolve critical issue
   - Add/update tests to verify fix
   - Run tests: `make test`

3. **Validation (ALL must pass)**
   - ✅ Run `make ci-check` - all checks green
   - ✅ Run `poetry run mypy` on changed files - no type errors
   - ✅ Run `poetry run sourcery review --check` on changed files - no issues
   - ✅ Run `make docs-verify` if docs changed - no warnings
   - ✅ All tests passing

4. **Documentation**
   - Update `AGENTLOG.md` with hotfix details
   - Update `CHANGELOG.md` under `## [Unreleased]` → `### Fixed`
   - Update `TODO.md` to mark issue resolved

5. **Commit and push**
   - **WAIT for user approval** before committing
   - Create commit: `fix: <brief description of hotfix>`
   - Commit tracking updates: `chore: Update CHANGELOG and AGENTLOG for hotfix`
   - Push directly to main

**Output:** Critical fix deployed to main with all validation passing and documentation updated.

---

## Workflow Exit Conditions

**Complete:** All steps finished, documentation updated, ready for next task → return to step 1.

**Blocked:** Issue discovered that prevents progress → document in `TODO.md`, restart from step 1 with blocking issue as new task.
