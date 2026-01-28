---
title: "Codex Harness Spike Findings"
description: "Comprehensive findings from the Codex API harness spike - constraints, learnings, and recommendations"
owner: "aaronksolomon"
author: "Claude Opus 4.5"
status: "draft"
created: "2026-01-25"
updated: "2026-01-25"
---

# Codex Harness Spike Findings

## Executive Summary

The Codex harness spike revealed fundamental constraints in driving GPT-Codex models via the Responses API for agentic coding tasks. While tool execution worked correctly, **the model consistently fails to produce final structured output after tool-calling rounds**, blocking reliable automation.

**Key Finding**: The VS Code Codex extension likely uses client-side orchestration and summary synthesis rather than expecting the model to self-summarize. Replicating this behavior requires architectural changes beyond simple prompt engineering.

**Recommendation**: Suspend Codex harness development. The approach requires either (a) significant investment in client-side orchestration matching VS Code extension behavior, or (b) waiting for Responses API improvements. Neither is justified for the current bootstrap goal.

---

## Context

### Spike Objectives

Per ADR-OA03.2, the Codex runner aims to:

1. Invoke GPT-Codex models headlessly via the Responses API
2. Provide tool access (read_file, search_repo, list_files, apply_patch, run_tests)
3. Capture structured output (patch, rationale, risk_flags, status)
4. Enable automated code implementation tasks

### What Was Built

- **Harness CLI**: `tnh-codex-harness run --task "..."` — Typer-based CLI for single-shot execution
- **Tool Surface**: 5 tools implemented with JSON Schema definitions
- **Tool Execution**: Working providers for file read, directory listing, ripgrep search, git patch apply, shell test runner
- **Artifact Capture**: Request/response JSON, parsed output, patch files, stdout/stderr logs
- **Run Tracking**: Timestamped run directories under `.tnh-codex/runs/`

### Test Matrix

| Test Case | Result | Notes |
|-----------|--------|-------|
| Tool definitions accepted | ✅ Pass | Strict mode schemas work |
| read_file execution | ✅ Pass | File content returned |
| search_repo execution | ✅ Pass | Ripgrep matches returned |
| list_files execution | ✅ Pass | Directory entries returned |
| apply_patch execution | ✅ Pass | Git apply works |
| Final JSON output | ❌ Fail | Model stops after tool calls |
| Multi-round tool loop | ⚠️ Partial | Rounds execute, no final output |

---

## Findings

### Finding 1: No Final Text Output After Tool Rounds

**Observation**: When tools are available, the model enters a tool-calling loop and stops before emitting a final text response. The API returns `status: completed`, but the output array contains only:

1. `reasoning` blocks (encrypted/empty)
2. `function_call` blocks (the tool invocation)

There is no `message` type with `output_text` content.

**Evidence** (from run `20260123-212325`):

```json
{
  "output": [
    { "type": "reasoning", "content": null },
    { "type": "function_call", "name": "apply_patch", "arguments": "..." }
  ],
  "status": "completed"
}
```

The `response.txt` artifact is empty because `_extract_text()` found no message content.

**Impact**: The harness cannot parse structured output, so runs are marked `blocked`.

### Finding 2: Responses API Parameter Limitations

**Observation**: Several expected API parameters are rejected or ignored:

| Parameter | Expected Behavior | Actual Behavior |
|-----------|------------------|-----------------|
| `response_format` | Enforce JSON schema | Not supported on Responses API |
| `temperature` | Control sampling | Rejected (set to 1.0 regardless) |
| `tool_choice: none` | Force text output | Not available to prevent tool calls |

**Impact**: Cannot enforce structured output via API parameters. Must rely on prompt engineering alone.

### Finding 3: VS Code Extension Uses Different Architecture

**Observation**: The VS Code Codex extension produces structured summaries like:

```
Added a new AGENTLOG entry...

Details:
- Updated AGENTLOG.md with a full session entry
- Created codex-harness-e2e-report.md

2 files changed +115 -0
```

This summary is **not from the model** — it's synthesized by the extension from observed tool calls.

**Evidence**:
- The extension shows "steps" (inspecting, planning, editing) that are UI states, not API outputs
- File change counts (`+115 -0`) are computed from git diff, not model output
- The "Undo" action implies client-side state tracking

**Architectural Insight**: The VS Code extension is an **orchestrator** that:
1. Tracks all tool calls made by the model
2. Applies changes directly to the workspace
3. Synthesizes summaries from its own observation of what changed
4. Maintains conversation state across turns

This is fundamentally different from expecting the model to produce a final summary.

### Finding 4: VS Code Extension Uses External App Server (2026-01-26)

**Observation**: VS Code output channel logs reveal the extension communicates with an external "app server" via notifications:

```text
Received app server notification: codex/event/agent_message_content_delta
Received app server notification: item/agentMessage/delta
Received app server notification: codex/event/item_completed
Received app server notification: codex/event/agent_message
Received app server notification: codex/event/token_count
Received app server notification: thread/tokenUsage/updated
Received app server notification: codex/event/task_complete
Received app server notification: turn/completed
```

**Architectural Insight**: The VS Code Codex extension is **not** driving the API directly. It connects to an OpenAI-hosted **app server** that:
- Manages the agentic loop (`turn/completed`, `task_complete`)
- Streams content deltas (`agent_message_content_delta`)
- Tracks token usage (`tokenUsage/updated`)
- Handles MCP (Model Context Protocol) requests

This is a **proprietary orchestration layer** not available via public API.

**Implications**:
1. Replicating VS Code behavior would require building our own orchestrator
2. The "app server" likely handles the tool loop and summary synthesis
3. Public API access provides raw model capabilities, not the orchestrated experience

### Finding 5: Cost and Feedback Loop Implications

**Observation**: Each API call incurs token costs. Without the VS Code extension's UI feedback loop, the harness provides no interactive iteration.

**Run cost example** (from `20260123-212325`):
- Input tokens: 14,574
- Output tokens: 195
- Total: 14,769 tokens
- At typical Codex pricing: ~$0.15-0.30 per run

For iterative development, costs compound quickly without the value-add of VS Code's interactive session.

---

## Root Cause Analysis

### Why the Model Doesn't Produce Final Output

The Responses API treats tool calls as valid "outputs." From the model's perspective:

1. Receive task
2. Use tools to gather information
3. Call `apply_patch` to make changes
4. **Done** — the tool call *is* the output

The model doesn't distinguish between "I made changes via tools" and "I should now summarize what I did." The ADR assumption that Codex would emit a post-tool JSON summary is not supported by the API's behavior.

### Comparison to Claude Code Runner (OA03.1)

| Aspect | Claude Code (OA03.1) | Codex (OA03.2) |
|--------|---------------------|----------------|
| Output capture | CLI stdout (natural) | API response (requires schema) |
| Tool execution | Filesystem-native | Tool-mediated |
| Summary | Inherent in response | **Not produced** |
| State tracking | None needed | Client must track |

Claude Code's `--print` mode forces text output to stdout. The harness captures this naturally. Codex has no equivalent forcing mechanism.

---

## Options Considered

### Option A: Prompt Engineering

**Approach**: Add explicit "after completing tools, respond with JSON summary" instructions.

**Tested**: The system prompt already includes:
> "Return ONLY JSON with keys: patch, rationale, risk_flags, open_questions, status"

**Result**: Ineffective. The model treats tool calls as completion.

### Option B: Forced Final Turn

**Approach**: After tool loop exhausts, send a final message with `tool_choice: none` (if supported) demanding JSON output.

**Status**: Not implemented. Requires API support for disabling tools on specific turns, which may not exist.

### Option C: Client-Side Synthesis (VS Code Model)

**Approach**: Don't expect the model to summarize. Track tool calls, synthesize `CodexStructuredOutput` from tool call history.

**Viability**: Technically feasible, but requires:
- Parsing `apply_patch` arguments as the "patch" artifact
- Inferring status from tool call patterns
- Generating rationale via a separate (cheaper) model call

**Complexity**: High. Essentially rebuilds VS Code extension orchestration logic.

### Option D: Different API Surface (TESTED 2026-01-26)

**Approach**: Use Chat Completions API with `response_format: json_schema` instead of Responses API.

**Tested**: Built `ChatCompletionsClient` with `--use-chat-completions` flag.

**Result**: **Failed** — GPT-Codex models are not supported on the Chat Completions endpoint.

```text
Error: "This is not a chat model and thus not supported in the v1/chat/completions endpoint."
Model: gpt-5.2-codex
```

**Implication**: GPT-Codex models are **Responses API only**. The Chat Completions path with `response_format: json_schema` cannot be used with Codex models. This eliminates Option D as a viable path.

### Option E: Wait for API Improvements

**Approach**: OpenAI may add forced-text-output mode or structured output support to Responses API.

**Status**: Unknown timeline.

---

## Recommendation

### Suspend Codex Harness Development

**Rationale**:

1. **Core assumption invalid**: ADR-OA03.2 assumes the model produces structured output after tool rounds. It doesn't.

2. **Workarounds are expensive**: Client-side synthesis (Option C) requires significant engineering to match VS Code extension behavior.

3. **Cost-benefit unfavorable**: Without VS Code's interactive loop, API costs accumulate without proportional productivity gain.

4. **Claude Code runner is tractable**: OA03.1 has a cleaner capture model (CLI stdout). It should be prioritized for near-term implementation tasks.

### Preserve the Work

The spike produced valuable artifacts:

- **Codex harness code**: Working tool execution, artifact capture, run tracking
- **Learnings**: Documented API behavior constraints
- **ADR validation**: Identified invalid assumptions before full implementation

This work can be resumed if:
- OpenAI adds forced-output mode to Responses API
- A business need justifies client-side orchestration investment
- Chat Completions API proves more suitable

### Update ADR-OA03.2

Add an addendum documenting:
- Spike findings
- Invalid assumptions
- Suspension rationale
- Conditions for resumption

---

## Appendix: Artifact Inventory

### Code Artifacts

| Path | Description |
|------|-------------|
| `src/tnh_scholar/agent_orchestration/codex_harness/` | Harness package |
| `src/tnh_scholar/agent_orchestration/codex_harness/service.py` | Orchestrator |
| `src/tnh_scholar/agent_orchestration/codex_harness/providers/` | Tool providers |
| `src/tnh_scholar/cli_tools/tnh_codex_harness/` | CLI entrypoint |
| `tests/agent_orchestration/test_codex_harness_tools.py` | Tool tests |

### Documentation Artifacts

| Path | Description |
|------|-------------|
| `docs/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md` | ADR (to be updated) |
| `docs/architecture/agent-orchestration/notes/codex-harness-e2e-report.md` | Initial test report |
| `docs/architecture/agent-orchestration/notes/codex-harness-spike-findings.md` | This document |

### Run Artifacts (in sandbox)

| Path | Description |
|------|-------------|
| `.tnh-codex/runs/<timestamp>/request.json` | API request payload |
| `.tnh-codex/runs/<timestamp>/response.json` | Raw API response |
| `.tnh-codex/runs/<timestamp>/response.txt` | Extracted text (usually empty) |
| `.tnh-codex/runs/<timestamp>/output.json` | Parsed structured output |
| `.tnh-codex/runs/<timestamp>/run.json` | Run metadata |

---

## References

- [ADR-OA03: Agent Runner Architecture](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md)
- [ADR-OA03.1: Claude Code Runner](/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md)
- [ADR-OA03.2: Codex Runner](/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
