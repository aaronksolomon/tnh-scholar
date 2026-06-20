---
title: "ADR-TG05: Run Progress Reporting"
description: "Spinner and elapsed-time status on stderr during tnh-gen run invocations."
owner: "aaronksolomon"
author: "aaronksolomon, Claude Sonnet 4.6"
status: accepted
created: "2026-06-20"
---

# ADR-TG05: Run Progress Reporting

Add a spinner and elapsed-time status line on `stderr` during `tnh-gen run` so that human operators can confirm the process is alive while a model call is in flight.

- **Filename**: `adr-tg05-run-progress-reporting.md`
- **Status**: Accepted
- **Date**: 2026-06-20
- **Authors**: aaronksolomon, Claude Sonnet 4.6
- **Owner**: aaronksolomon

---

## ADR Editing Policy

ADR is `accepted`. **Do not edit** Context, Decision, or Consequences sections — append addendums only.

---

## Context

`tnh-gen run` is completely silent while a model call is in flight — typically 10–30 seconds for clean or translate prompts, longer for sectioning. Operators have no indication that the process is alive and resort to pressing Enter, killing and retrying, or watching resource monitors. This is the highest-impact, lowest-effort UX improvement identified in the May 2026 walkthrough ([tnh-gen UX Directions — May 2026](/architecture/tnh-gen/notes/tnh-gen-ux-directions-2026-05.md), item 3).

The `run` pipeline has two phases where time is spent:

1. **Prep** — `_prepare_run_context()`: config load, service init, catalog introspection. Fast in practice (<1 s), but occasionally slower on cold catalog scan.
2. **Generate** — `context.service.generate()`: synchronous LLM API call, blocking main thread for the duration.

Both phases share the same need: confirm aliveness. A single progress indicator covering both is correct.

The project already depends on `rich` (v13.9.4), which provides `Console.status()` — a context manager that renders a spinner using `Live(transient=True)` and cleans up the line on exit. `rich` auto-detects terminal capabilities; when stderr is not a TTY it emits no escape codes.

`--api` mode requires a clean, machine-parseable `stdout`. Any status output must go exclusively to `stderr` and must be completely suppressed in `--api` and `--quiet` modes so machine consumers see no interleaved noise.

---

## Decision

### Module

Introduce `src/tnh_scholar/cli_tools/tnh_gen/output/progress.py` as a standalone module in the existing `output/` package. No changes to `output/__init__.py` are required; callers import directly.

### Public interface

```python
@contextmanager
def run_progress(
    prompt_key: str,
    input_file: Path,
    *,
    quiet: bool = False,
    api: bool = False,
    no_color: bool = False,
) -> Iterator[None]:
    ...
```

`run_progress` is a context manager. Entering it may start a spinner on `stderr`; exiting it always cleans up cleanly regardless of exception state.

### Suppression rules

`run_progress` is a no-op — yields immediately with no side effects — when any of the following are true:

- `quiet=True` (`--quiet` flag)
- `api=True` (`--api` flag)
- `sys.stderr.isatty()` is `False` (piped or redirected stderr)

### Display format

When active, the status line on `stderr` reads:

```
⠙ [tnh-gen] {prompt_key} ← {filename}  [0:15]
```

Where `⠙` is the animated dots spinner rendered by `rich`. The elapsed time field ticks in whole seconds. On context exit the entire line is cleared (rich transient behavior).

### Implementation mechanics

A background daemon thread updates the elapsed-time portion of the status text once per second via `Status.update()`. The main thread remains unblocked and performs the model call. The thread is stopped via a `threading.Event` in the `finally` clause, so cleanup is guaranteed on both normal exit and exception propagation.

```
run_progress context entered
│
├── rich Console(stderr=True) opened
├── console.status() Live context started → spinner visible
├── background thread: tick elapsed time every 1 s via status.update()
│
│   [main thread blocked on service.generate()]
│
├── main thread returns or raises
├── finally: stop_event.set() → thread exits within 1 s → thread.join()
└── console.status() context exits → spinner line cleared (transient)
```

### Integration point

In `run_prompt()` (`commands/run.py`), wrap `_prepare_run_context()` and `_execute_prompt()` together:

```python
with run_progress(prompt, input_file, quiet=ctx.quiet, api=ctx.api, no_color=ctx.no_color):
    context = _prepare_run_context(...)
    envelope, payload = _execute_prompt(context)

_emit_run_output(context, envelope, payload, ctx.api)
```

The progress context exits before any output is emitted. Exceptions raised inside propagate normally through the `with` block to the existing `except` handlers in `run_prompt()`.

### Dependencies

No new dependencies. `rich` (already required), `threading` and `time` (stdlib).

---

## Consequences

**Positive**

- Operators receive immediate confirmation the process is alive; elapsed time lets them calibrate patience.
- Zero noise in `--api` and `--quiet` modes — machine consumers are unaffected.
- No changes to domain layer, service contracts, or output payload format.
- Spinner line is fully cleared on exit; subsequent `typer.echo(err=True)` messages (e.g., "Wrote output to …") are unaffected.
- Clean separation: progress is entirely contained in `output/progress.py`.

**Negative**

- A background thread is introduced for the duration of the run. It is a daemon thread and is always joined in `finally`, so there is no resource leak, but any threading interaction with rich's `Live` requires that other stderr writes during the spinner are avoided. Current call paths do not write to stderr during the generate phase, so this is not an immediate risk.
- If a future code path emits to `sys.stderr` (e.g., via `logging` handlers that target stderr) while the spinner is active, interleaved output can cause visual glitches. This should be managed by ensuring progress suppression or log routing if needed.

---

## Alternatives Considered

**`tqdm`-based spinner** — `tqdm` is already in the project (`progress_utils.py`) but that utility writes to `stdout`, is not integrated with the tnh-gen context flags, and carries more boilerplate for a simple spinner. Rich is a cleaner fit given it is already a direct dependency.

**Single status line without live elapsed time** — `console.status()` alone (static text) would suffice to show the process is alive. A live elapsed counter was included because it is the specific operator ask from the UX review, adds negligible complexity, and has real diagnostic value (operators can judge whether to abort).

**`typer.echo` heartbeat (no rich)** — Periodic newline or dot to stderr from the background thread, without any ANSI control. Simpler but leaves a trail of dots/newlines that cannot be cleaned up, and conflicts with structured output if the operator captures stderr.

**Rich `Progress` bar** — `rich.progress.Progress` supports multiple task bars and percentage fills. Overkill for a single synchronous call where total duration is unknown.

---

## Open Questions

- **Future: budget pre-flight line** — UX item 6 (display active budget limit before run) could be surfaced as an initial `typer.echo(err=True)` line just before the progress context is entered. That is a separate change with no dependency on this ADR.
- **Future: phase labels** — If prep time becomes significant (e.g., cold catalog scan on a large prompt directory), a `status.update()` call at the boundary between prep and generate phases could give finer-grained feedback. No change to the interface is required.

---

## As-Built Notes & Addendums

*None yet.*
