# Agent Orchestration - EXPERIMENTAL

**Status:** Paused (as of 2026-01-27)

**Reason:** Evaluating Codex interface build costs and alternative approaches

This module contains spike/exploratory code from Phase 0 protocol work (ADR-OA02). The code is **non-operational** and preserved for reference only.

## Contents

- `spike/` - Phase 0 conductor spike (Claude Code PTY automation exploration)
- `codex_harness/` - Codex API harness spike (suspended due to API limitations)

## Related Documentation

- Design docs: `docs/architecture/agent-orchestration/`
- ADRs: `docs/architecture/agent-orchestration/adr/`
- Spike findings: `docs/architecture/agent-orchestration/notes/`
- Spike report: `SPIKE_REPORT.md` (repo root)

## Resuming Work

If work resumes on agent orchestration:

1. Review ADR-OA02 and ADR-OA03 addendums for pause context
2. Update ADR statuses from `paused` to `wip`
3. Uncomment CLI entry points in `pyproject.toml`
4. Remove this EXPERIMENTAL.md marker
