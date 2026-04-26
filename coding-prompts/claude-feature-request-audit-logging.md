---
title: "Claude Feature Request Audit Logging"
description: "Concise product-facing prompt for a Claude Code audit logging feature request."
owner: ""
author: "OpenAI GPT-5 Codex"
status: current
created: "2026-04-24"
updated: "2026-04-25"
model_family: "claude"
source: "tmp/claude-code-feature-request-audit-logging.md"
copied: "2026-04-24"
---

# Claude Code audit logging feature request

Objective: draft a concise product-facing feature request for opt-in Claude Code audit logging.

Context:
- a prior destructive git incident could be recovered from reflog but not fully reconstructed because the exact command history was unavailable
- similar community incidents have raised the same need for command-level auditability

Requirements:
- propose opt-in local audit logging for shell commands and file operations
- keep the design privacy-preserving: metadata only, no file contents or command output
- use simple local JSONL streams
- include minimal settings for enablement, retention, and log scope
- explain why this helps incident forensics, debugging, and compliance

Suggested design:
- `~/.claude/audit/file-operations.jsonl`
- `~/.claude/audit/shell-commands.jsonl`
- per-entry fields such as timestamp, session id, operation or command, cwd or path, exit code, duration, and small structural metadata

Constraints:
- opt-in, not default-on
- local storage only
- rotation / retention support
- no sensitive payload capture

Deliverable:
- concise summary
- proposed log schema
- example settings block
- open questions or product tradeoffs
