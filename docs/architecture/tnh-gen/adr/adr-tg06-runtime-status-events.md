---
title: "ADR-TG06: Runtime Status Events for tnh-gen run"
description: "Typed application events for terminal feedback and agent-readable runtime status, with explicit failure attribution."
owner: "aaronksolomon"
author: "OpenAI Codex"
status: accepted
created: "2026-06-20"
updated: "2026-09-15"
---

# ADR-TG06: Runtime Status Events for tnh-gen run

Provide typed runtime events for human operators and agents running `tnh-gen`, including outside the repository, while preserving the result-output contract.

- **Status**: Accepted — approved by the maintainer on 2026-09-15; implementation pending
- **Date**: 2026-06-20
- **Authors**: OpenAI Codex
- **Owner**: aaronksolomon

## ADR Editing Policy

This ADR is accepted. Preserve the Context, Decision, and Consequences sections; record subsequent design changes through addendums. Implementation remains pending.

## Context

`tnh-gen` is already used for production tasks, including work outside the repository and invocations by agents. Operators need to know whether a process is alive, which operation is active, whether generation succeeded, and whether requested output was delivered.

[ADR-TG05](/architecture/tnh-gen/adr/adr-tg05-run-progress-reporting.md) introduced `run_progress(...)` around preparation and generation. It shows a Rich spinner and elapsed time on stderr, but is disabled for non-TTY callers, `--api`, and `--quiet`. It exposes no reusable status contract. [Issue #55](https://github.com/aaronksolomon/tnh-scholar/issues/55) also records the difficulty of distinguishing useful diagnostics from routine stderr chatter in agent-driven runs.

The initial TG06 draft retained those visibility gaps by limiting V1 to terminal rendering. This revision includes an explicit JSONL event file so agents can observe a run without scraping a terminal or parsing mixed stderr output.

Two current orchestration boundaries require care:

- `context.service.generate(...)` includes prompt rendering, routing, safety checks, provider execution, and result validation. Entering that call does not prove provider dispatch occurred.
- Failed completion envelopes are currently rendered inside `_emit_run_output()`. The place where a failure is rendered is not necessarily where it originated.

Per [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md), terminal presentation and CLI sink selection stay in the application layer. This does not prohibit typed service telemetry in general; V1 simply needs no new service observer contract.

## Decision

### 1. Own run status in the CLI application layer

Introduce `src/tnh_scholar/cli_tools/tnh_gen/run_status/` with separate responsibilities:

- `models.py`: immutable Pydantic metadata, event, and failure models; typed enums.
- `policy.py`: typed sink selection and heartbeat configuration resolved once at invocation.
- `sink.py`: `RunStatusSink` protocol with `open()`, `emit(event)`, and `close()` methods.
- `sinks/`: no-op, Rich terminal, and JSONL file implementations.
- `emitter.py`: event construction, sequencing, timing, serialization of concurrent emissions, and sink lifecycle.

`run.py` owns orchestration transitions and outcome classification. It calls emitter methods rather than constructing event payloads. The emitter owns heartbeat scheduling. Rich animation remains private to the terminal sink.

The GenAI service, adapters, and transport clients must not import this CLI package or call its sinks. No provider callbacks or retry instrumentation are introduced. Existing typed envelopes and exceptions supply the facts the CLI can observe.

### 2. Define a versioned event contract

`RunStatusMetadata` is immutable for an invocation and includes:

- `trace_id`: the existing CLI invocation identifier, reused in result and error payloads.
- `prompt_key`, `input_file_name`, optional `output_file_name`.
- `api_mode`, `quiet`, optional `requested_model`.

Create metadata before preparation; configuration and service failures must still be correlatable. Actual provider/model values are optional event fields populated only when available from service results. Requested and resolved model identities must remain distinct.

Each immutable `RunStatusEvent` includes:

| Field | Contract |
| --- | --- |
| `schema_version` | `1.0` for V1; breaking wire changes require a new major version. |
| `sequence` | Positive integer, starting at 1 and increasing across all events for this invocation. |
| `event_type` | `stage_started`, `heartbeat`, or `terminal`. |
| `stage` | Current CLI-owned stage when the event is emitted. |
| `timestamp` | UTC wall-clock timestamp with explicit timezone. |
| `elapsed_ms` | Nonnegative monotonic elapsed time since invocation status tracking began. |
| `stage_elapsed_ms` | Nonnegative monotonic elapsed time since the current stage began. |
| `metadata` | The invocation metadata above. |
| `message` | Bounded presentation text; consumers branch on typed fields, not this text. |
| `outcome` | Terminal-only: `completed`, `failed`, or `cancelled`. |
| `exit_code` | Terminal-only: the intended process exit code, using existing CLI mappings. |
| `failure` | Optional typed primary failure record with `origin_stage` and stable `code`. |
| `reporting_failure` | Optional typed secondary failure while rendering an already-known failure. |
| `model`, `provider` | Optional resolved identities when known; never inferred from a CLI override. |

`RunFailure` carries an origin stage and code, with an optional bounded, sanitized summary. Reuse existing domain reasons and CLI error codes through one mapper; do not invent codes at each call site. Use typed event variants or model validation to enforce terminal-only fields and valid outcome/failure combinations. Completed events have no failure; failed events require one. Cancellation records its origin stage with an interruption code.

No arbitrary `details: dict[str, Any]`, prompt contents, input text, output text, credentials, or raw exception dumps belong in status events. Filenames and prompt keys are operational metadata and may still be sensitive; the caller controls where the event file is stored. This is a status contract, not a full reproducibility manifest.

### 3. Use stages that describe observable work

| Stage | Meaning |
| --- | --- |
| `starting` | Command callback accepted, trace ID created, status initialized; includes command-level option validation. |
| `preparing_run` | Configuration, service construction, catalog lookup, input reading, and variable preparation. |
| `generating` | Request assembly, service invocation, and outcome/payload interpretation. |
| `emitting_output` | Requested artifact writes, warnings, result/error rendering, and stdout emission. |

Use `generating`, not `calling_provider`: the CLI cannot observe the dispatch boundary within the service. Safety blocking or schema validation failure can therefore correctly originate in `generating` without implying that a paid request occurred.

Stages express current activity. Outcomes express how the invocation ended. Do not add `failed` or `completed` as stages.

Argument-parser failures before the command callback begins are outside this lifecycle. Status initialization failures are reported through the existing CLI error path; no event file is promised if it could not be opened.

### 4. Preserve the origin of failures independently of rendering

Introduce a typed CLI terminal-decision model separate from the current stage. It stores the primary outcome, failure origin/code, and intended exit code. It is not a replacement for the GenAI completion envelope or public API result payload.

Classify a returned failed completion envelope immediately after generation, before entering `emitting_output`. Capture exceptions at the operation boundary where they arise, before moving to error rendering. Keep this primary failure fixed while diagnostics are rendered.

| Scenario | Terminal event stage | Primary failure origin | Outcome |
| --- | --- | --- | --- |
| Preparation fails; error rendering succeeds | `emitting_output` | `preparing_run` | `failed` |
| Safety blocks generation; error rendering succeeds | `emitting_output` | `generating` | `failed` |
| Service returns a failed envelope; error rendering succeeds | `emitting_output` | `generating` | `failed` |
| Generation succeeds; output file, sidecar, or stdout write fails | `emitting_output` | `emitting_output` | `failed` |
| Generation fails; rendering that error also fails | `emitting_output` | `generating` | `failed`, with secondary `reporting_failure` |
| User interrupts during generation | `generating` unless subsequent rendering begins | `generating` | `cancelled` |

If error rendering itself fails after a primary failure is known, retain the primary failure and its exit code; attach the secondary failure separately. Do not overwrite the original cause with an output error. If output fails after successful generation, output failure becomes the primary cause under the existing CLI exception mapping.

Refactor `_emit_run_output()` so outcome classification and process-exit selection belong to orchestration rather than being hidden in rendering. Rendering may still raise I/O errors. A renderer's `typer.Exit` must not be used to infer the failure origin.

No automatic provider retry or replay follows a reporting failure. Partial output may already exist; the status contract does not imply rollback or atomic writes.

### 5. Finalize after output, with bounded cleanup

The success path is:

1. Open selected sinks and emit `starting`.
2. Emit preparation and generation transitions around their operations.
3. Classify the service outcome while still in `generating`.
4. Emit `emitting_output`, stop transient Rich rendering, and perform requested output/error rendering. Keep the JSONL sink active.
5. Flush result stdout and finish requested file/sidecar writes before deciding `completed`.
6. Stop and join the heartbeat worker, emit one terminal event, then close remaining sinks.

The failure path captures its primary decision before rendering diagnostics, then follows the same finalization ownership. Use context-manager/finally cleanup; cleanup errors must not replace the task's original exception or outcome. Terminal emission is idempotent, and no heartbeat or stage event follows it. Sink closure is also idempotent; stopping Rich early must not close the JSONL sink.

Catch interruption at the CLI lifecycle boundary to attempt a `cancelled` event and cleanup, then preserve existing interruption/exit behavior. Do not swallow `KeyboardInterrupt` or convert it into ordinary provider failure. A hard kill, default signal termination, process crash, or failed event sink may prevent a terminal record. V1 adds no new signal-handling framework.

A completed event means the command finished its requested output operations, not that downstream consumers read stdout or that files survived a power loss. Consumers combine events with process exit status. EOF or a missing terminal event alone is not success and is not sufficient grounds to repeat a paid request.

### 6. Provide explicit machine status without changing stdout

Add `tnh-gen run --status-file PATH` for a UTF-8 JSONL event file. This is the V1 opt-in control; no shared logging setup or implicit status-file creation is required.

| Invocation | Rich stderr status | JSONL event file |
| --- | --- | --- |
| Human mode with stderr TTY | Enabled | Only when explicitly requested |
| Non-TTY human mode | Disabled | Only when explicitly requested |
| `--api` | Disabled | Only when explicitly requested |
| `--quiet` | Disabled | Still enabled when explicitly requested |

`--quiet` suppresses human status, not an explicitly requested machine artifact. `--no-color` affects terminal rendering only. Existing result and error behavior remains unchanged; this ADR does not redefine all CLI warning suppression.

Stdout remains exclusively the result/error payload channel. Status events never go to stdout or through a logging handler that might target stdout. Stderr remains diagnostic text, not a structured event stream. Agents use the dedicated file and do not need to parse warnings.

Paths resolve against the caller's working directory and require no repository checkout. The parent directory must already exist. Create the file exclusively: reject an existing destination, including symlinks, without truncating or appending. Reject collisions with invocation inputs and requested output/provenance destinations before any provider work. Callers choose a fresh path per invocation and own retention.

Write one complete JSON object plus newline per record and flush each record for live readers. No `fsync` durability guarantee is required. Readers consume complete lines, tolerate an incomplete final line after abnormal termination, ignore unknown additive fields, and reject unsupported major schema versions. Sequence numbers order events even if the wall clock moves.

### 7. Define heartbeat and sink-failure policy

Use a 10-second heartbeat interval in a typed configuration supplied at initialization, injectable for tests. V1 need not expose another CLI flag. Emit a heartbeat when an active stage has produced no event for that interval. It repeats current stage and elapsed times without implying stage completion or provider progress.

Use one serialized emission path for stage, heartbeat, and terminal records. Protect state transitions and sequence assignment so a heartbeat cannot carry stale stage metadata or follow a terminal event. Avoid an unbounded event queue; disable a failed sink rather than accumulating undeliverable records.

Sink failures have explicit semantics:

- If an explicitly requested file cannot open or accept its initial event, fail before preparation/generation through the existing CLI error contract.
- After initialization, a sink write/flush/close failure disables that sink and emits at most one bounded diagnostic on stderr. It does not alter the task outcome, mask an existing failure, cancel generation, or trigger a retry. Continue any other functioning sinks.
- Rich initialization/rendering failure is nonfatal; disable terminal status and continue the task.
- File I/O stays local and synchronous in V1; arbitrary slow network filesystems are not promised bounded write latency. Prefer local storage for live supervision.

Best-effort delivery means an observer can lose status while the underlying task succeeds. Exit status and result artifacts remain authoritative. Consumers must handle a truncated event history and must not treat heartbeat absence as proof that a remote request failed.

### 8. Keep V1 bounded and retire the direct spinner path

Implement typed events, emitter lifecycle, Rich rendering, and the explicit JSONL file as one `tnh-gen run` slice before the conductor review/revision loop. This is a current production-operability need, not a dependency on a future conductor event framework.

Remove `output/progress.py` or retain only a private Rich helper behind the sink. After implementation, append an addendum to [ADR-TG05](/architecture/tnh-gen/adr/adr-tg05-run-progress-reporting.md) identifying TG06 as the replacement for direct spinner orchestration.

Defer provider retry instrumentation, service observers, shared logging adoption, automatic output persistence, artifact indexing/retention, dashboards, and cross-CLI event unification. An explicit event file does not commit the project to those systems.

## Consequences

**Positive**

- Humans and agents gain useful runtime visibility, including from external working directories.
- Typed stages, heartbeats, and terminal outcomes preserve machine-output purity.
- Failure attribution survives transitions into diagnostic rendering.
- Output failure cannot be mislabeled as successful completion merely because generation succeeded.
- Sink-specific behavior remains separate from application orchestration and GenAI services.

**Negative**

- More modules, lifecycle state, and concurrency tests than the existing spinner helper.
- Explicit event files require caller-managed paths, observation, and retention.
- Coarse stages and local heartbeats cannot diagnose remote provider progress or retries.
- Best-effort status delivery cannot prove success after abnormal termination or guarantee recovery of generated content.

## Alternatives Considered

- **Rich-only V1**: Leaves agent and non-TTY production runs without useful status, despite a typed internal contract.
- **Direct stage messages on stderr**: Adds mixed diagnostic chatter without a reliable machine contract.
- **JSONL on stderr**: Existing warnings and diagnostics share that stream. A clean dedicated file avoids a broader stderr redesign.
- **Shared logging for both status and diagnostics**: Couples runtime reporting to handler configuration and potential stdout contamination.
- **Status hooks throughout the GenAI service**: Unnecessary for the observable CLI stages; defer a typed service observer until internal milestones are required.
- **Infer failure from the current stage at exit**: Misattributes a failed generation envelope to the output-rendering stage.

## Open Questions — Deferred Beyond V1

- How should provider retries and polling milestones be exposed through a typed service observer?
- Should future shared logging be enabled by CLI flag, configuration, or an application default?
- What retention, discovery, or indexing policy should apply if run artifacts become automatic?
- Which event concepts should eventually be shared with `tnh-conductor` and other CLIs?

These questions do not block V1. Non-TTY defaults, API/quiet behavior, explicit event files, heartbeat semantics, and failure-origin rules are decided above.

## Implementation Scope and Acceptance

Implement the package, CLI option, typed terminal-decision mapping, sink lifecycle, and orchestration refactor. Update CLI documentation and append the TG05 implementation addendum when behavior lands. Acceptance records the approved design, not completed implementation.

Focused tests must cover:

- API stdout remains one valid result/error payload with no status bytes; explicit event files work with `--api` and `--quiet`.
- TTY selection, no-color behavior, and silent non-TTY defaults.
- Fresh-file creation, path collisions, missing parent directories, and initialization failure before any service invocation.
- Stage order, schema validation, shared trace ID, sequence order, UTC timestamps, and monotonic timing with an injected clock.
- Heartbeats during a blocked fake service call and absence of heartbeats after terminal emission.
- Preparation exceptions, safety blocking, returned failed envelopes, successful generation followed by output failure, and secondary error-rendering failures.
- Exactly one terminal decision/event when delivery succeeds, correct primary origin and exit code, cancellation, and cleanup on all paths.
- Result stdout flush and file/sidecar completion before a completed event; stopped Rich rendering before output diagnostics.
- Sink failures during open, emit, flush, and close; no masked task failure, duplicated service call, or unbounded queue.
- Event visibility to a live reader before command completion; truncated-file handling without false success.
- A real subprocess from a temporary directory outside the checkout, using captured stdout/stderr, explicit prompt/input paths, an event file, and a controlled provider fixture without paid calls.

The acceptance criterion is that an agent outside the repository can observe startup, current stage, elapsed time, and terminal outcome without scraping a spinner or corrupting the result payload.

## Historical References

- [ADR-TG05: Run Progress Reporting](/architecture/tnh-gen/adr/adr-tg05-run-progress-reporting.md): narrow terminal-feedback predecessor.
- [tnh-gen UX Directions and Issues — May 2026](/architecture/tnh-gen/notes/tnh-gen-ux-directions-2026-05.md): production observations motivating liveness feedback.
- [Issue #55: Agent/script ergonomics](https://github.com/aaronksolomon/tnh-scholar/issues/55): predictable controls and output for delegated use.


## Addendum 2026-09-17: V1 Implementation on Feature Branch

**Status**: Implemented on `feat/tnh-gen-runtime-status-events`; review and merge pending.

The `run_status` package now owns typed events, sink policy, sequence/timing,
heartbeats, and terminal decisions. `run.py` classifies the service envelope before
constructing or rendering its output payload. Rendering no longer selects the
process exit code. Primary failure origin is retained if later rendering fails.

`--status-file` uses exclusive creation and flushes complete JSONL records. Rich
rendering stops before output while the file sink remains active. Heartbeat and
terminal emission share serialized state, and the worker stops before terminal
emission. Failed status sinks are retired without retrying generation. Failure
records contain codes and stages only; optional free-text summaries are omitted.

Cancellation follows Typer/Click's existing keyboard-interrupt abort behavior
(exit 1), records `cancelled` when possible, and propagates the interruption.
Other process termination retains best-effort cleanup without inventing a terminal
success. Event readers accept additive V1 minor versions and unknown fields while
rejecting unsupported major versions.

Tests cover event/schema invariants, primary and secondary failure attribution,
sink failures, output flushing, path protection, API/quiet selection, and live
observation from an actual subprocess outside the checkout using a controlled
service fixture. No provider calls are made by these tests.
