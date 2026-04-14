---
title: "VS Code 1.110 Agent Features Research"
description: "Research findings from VS Code February 2026 release — UI patterns and systems relevant to tnh-conductor"
owner: "aaronksolomon"
author: "Claude Opus 4.5"
status: reference
created: "2026-03-08"
---
# VS Code 1.110 Agent Features Research

Research findings from VS Code v1.110 (February 2026) release notes analysis. Captures UI patterns, architectural ideas, and potential integration points relevant to tnh-conductor development.

**Date**: 2026-03-08
**Source**: https://code.visualstudio.com/updates/v1_110
**Context**: Evaluating VS Code agent capabilities for potential reuse, inspiration, or future integration (Phase 6)

---

## Executive Summary

VS Code's agent features require **GitHub Copilot subscription** and are designed for **single-agent IDE assistance**, not multi-agent workflow orchestration. There is no direct code reuse opportunity, but several UI patterns and architectural concepts are worth noting for tnh-conductor's Phase 6 (VS Code Integration).

**Key finding**: VS Code cannot currently coordinate workflows between Claude Code and Codex. Each operates as an isolated tool with no shared context, handoff protocol, or unified provenance. This gap is precisely what tnh-conductor addresses.

---

## Coverage Gap Analysis

| Capability | VS Code Copilot | tnh-conductor |
|------------|-----------------|---------------|
| Single-agent chat/execution | ✅ Yes | ✅ Yes |
| Multi-agent coordination | ❌ No | ✅ Core design goal |
| Cross-agent context sharing | ❌ No | ✅ Provenance ledger |
| Transcript capture | ❌ Session-internal only | ✅ Full PTY/stdout to artifacts |
| Workspace diff capture | ❌ No | ✅ Pre/post git diff |
| Dual-channel validation | ❌ No | ✅ Transcript vs workspace consistency |
| Policy enforcement | ❌ Basic tool restrictions | ✅ Allowed/forbidden paths, post-hoc diff |
| Semantic status classification | ❌ No | ✅ Planner evaluation |
| Human review gates | ❌ No | ✅ Daily journal, blocking gates |
| Workflow definition (YAML) | ❌ No (skills are simpler) | ✅ Opcode sequences |
| Git branch isolation | ❌ No | ✅ Work-branch per run |
| Rollback semantics | ❌ No | ✅ Git-based rollback |
| Provenance/audit trail | ❌ No | ✅ tnh-gen ledger |

---

## Pricing/Access Model

| Component | Access Model |
|-----------|--------------|
| VS Code editor | Free |
| Agent mode, chat, skills, hooks | GitHub Copilot subscription ($10-19/mo) |
| Claude Code CLI | Anthropic API key (pay-per-use) or Claude Pro |
| Codex CLI | OpenAI API key (pay-per-use) |

All VS Code 1.110 agent features (Agent Debug Panel, `/create-*` commands, plugins, session forking) require Copilot subscription.

---

## UI Patterns Worth Studying

### 1. Agent Debug Panel (Preview)

**What it does**: Real-time visibility into chat sessions with event tracking and visual hierarchy charts. Shows how customizations are loaded and applied.

**Relevance to OA**: Maps to our dual-channel output visualization needs:
- Event stream display (transcript channel)
- Hierarchy visualization (workflow step nesting)
- Customization loading (prompt/policy application)

**Ideas for tnh-conductor Phase 6**:
- Real-time event stream panel showing kernel events
- Visual hierarchy of workflow → step → agent invocation
- "Customizations loaded" equivalent showing which prompts/policies are active

**Limitation**: Currently local sessions only — no remote/background agent visibility.

### 2. Session Memory & Context Compaction

**What it does**: Plans persist across context compaction via `/compact` command. Users can provide custom guidance for what to preserve during compaction.

**Relevance to OA**: Validates our Planner design:
- Stateless Planner with explicit provenance window (last K steps)
- Bounded context fed as structured inputs, not "memory"
- User-guided summarization parallels our "provenance window" concept

**Ideas for tnh-conductor**:
- Expose similar "compaction" for long-running workflows
- Allow human-guided prioritization of what context to preserve
- UI for visualizing what's in the current provenance window

### 3. Session Forking (`/fork`)

**What it does**: Creates independent sessions inheriting conversation history. Can fork from specific checkpoints.

**Relevance to OA**: Maps to workflow branching concepts:
- Fork from any provenance checkpoint
- Explore alternative approaches without losing original path
- Compare outcomes across forked workflows

**Ideas for tnh-conductor**:
- Workflow fork capability from any recorded step
- "What-if" exploration: re-run from checkpoint with different prompts
- Diff view comparing forked workflow outcomes

### 4. Customization Generation (`/create-*`)

**What it does**: Generate reusable artifacts from conversations:
- `/create-prompt` → reusable prompt files
- `/create-skill` → multi-step workflows
- `/create-agent` → specialized personas
- `/create-hook` → lifecycle automation

**Relevance to OA**: Parallels our prompt library concept:
- Prompt artifacts generated from successful runs
- Skills ≈ workflow templates
- Agents ≈ capability profiles for routing

**Ideas for tnh-conductor**:
- "Promote to library" action: successful ad-hoc prompt → versioned prompt artifact
- Learn workflow patterns from transcript analysis
- Generate capability profiles from observed agent behavior

### 5. Explore Subagent Architecture

**What it does**: Dedicated read-only agent for codebase research using fast models (Haiku 4.5, Gemini 3 Flash). Configurable model via `chat.exploreAgent.defaultModel`.

**Relevance to OA**: Validates our agent positioning in ADR-OA03:
- Separation of exploration (Claude Code) vs execution (Codex)
- Fast/cheap models for research, capable models for implementation
- Explicit agent capability routing

**Ideas for tnh-conductor**:
- Formalize "explore mode" vs "execute mode" in runner contracts
- Model selection based on task classification
- Cost-aware routing (use cheaper models for triage/exploration)

### 6. Auto-Approval Commands

**What it does**: Toggle global auto-approve via `/autoApprove` and `/disableAutoApprove` slash commands.

**Relevance to OA**: Maps to our policy enforcement model:
- Runtime policy adjustment without restart
- Explicit opt-in to reduced oversight for bounded tasks

**Ideas for tnh-conductor**:
- Per-run policy override (more permissive for trusted workflows)
- "Auto-approve within policy bounds" mode
- Clear UI indication when operating in reduced-oversight mode

---

## Extension/Integration APIs

### Chat Session Item Controller

New APIs for extension authors:
- `ChatSessionItemControllerNewItemHandler` for URI specification
- `ChatSessionProviderOptions.newSessionOptions` for session defaults
- Optimized for large session numbers

**Relevance**: If we build VS Code integration, these APIs would be entry points for:
- Custom session types representing workflow runs
- Provenance-linked session items
- Custom UI for tnh-conductor workflows within VS Code

### Agent Plugins (Experimental)

Prepackaged bundles containing skills, commands, agents, MCP servers, and hooks. Installable from Extensions view.

**Relevance**: Potential distribution mechanism for tnh-conductor VS Code integration:
- Package conductor CLI + prompts + workflows as plugin
- MCP server for provenance queries
- Custom commands for workflow operations

**Caution**: Experimental feature — API stability uncertain.

---

## Browser Automation Tools (Experimental)

New agent tools for browser interaction:
- Navigation: `openBrowserPage`, `navigatePage`
- Content reading: `readPage`, `screenshotPage`
- Interaction: `clickElement`, `hoverElement`, `typeInPage`, `runPlaywrightCode`

**Potential OA use cases**:
- Verification workflows: confirm documentation renders correctly
- Integration testing: verify web UI changes
- Screenshot capture for visual diff in review journal

**Caution**: Experimental, agents operating browsers autonomously carries risk.

---

## Architectural Convergence

VS Code's agent architecture is converging toward patterns already present in tnh-conductor design:

| Pattern | VS Code 1.110 | tnh-conductor |
|---------|---------------|---------------|
| Explore vs Execute agents | Explore Subagent (read-only, fast model) | Claude Code (explore) vs Codex (execute) |
| Bounded context windows | Session memory + compaction | Provenance window (last K steps) |
| Workflow branching | Session forking | Work-branch isolation, checkpoint rollback |
| Artifact generation | `/create-*` commands | Prompt library versioning |
| Policy runtime control | Auto-approve commands | RunPolicy, post-hoc diff enforcement |

This suggests our architectural choices align with industry direction, even though VS Code's implementation serves different goals (IDE assistance vs auditable orchestration).

---

## Non-Relevant Features (For Completeness)

These VS Code 1.110 features were reviewed but deemed not directly relevant to OA work:

- **Custom thinking phrases**: Cosmetic chat customization
- **Collapsible terminal output**: UI polish
- **Kitty graphics protocol**: Terminal image rendering
- **Ghostty external terminal**: macOS/Linux terminal option
- **JavaScript/TypeScript setting unification**: Language-specific
- **Next edit suggestions**: Code completion enhancement

---

## Recommendations

### Short-term (Current OA Work)

1. **No direct reuse opportunity** — VS Code agent features are Copilot-integrated, not extractable
2. **Continue independent development** — tnh-conductor addresses gaps VS Code doesn't cover
3. **Document patterns** — Use VS Code's UI patterns as reference for future visualization

### Medium-term (Phase 6 Planning)

1. **Monitor Agent Plugins API** — If it stabilizes, consider packaging conductor as VS Code plugin
2. **Study Agent Debug Panel** — Model our provenance visualization on their event/hierarchy display
3. **Consider Chat Session APIs** — Entry point for custom workflow sessions in VS Code

### Long-term (Post-MVP)

1. **Evaluate Copilot integration** — Could tnh-conductor orchestrate Copilot as another runner?
2. **MCP server potential** — Expose provenance queries via MCP for VS Code consumption
3. **Unified UI** — VS Code extension providing workflow control surface over tnh-conductor

---

## References

- VS Code February 2026 Release Notes: https://code.visualstudio.com/updates/v1_110
- ADR-OA01: Agent Orchestration Strategy
- ADR-OA03: Agent Runner Architecture
- ADR-OA07: MVP Runtime Architecture Strategy

---

*Research document — not an ADR. Captures findings for future reference.*
