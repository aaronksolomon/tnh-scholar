---
title: "ADR-TG07: Shared Provider Rate Limits Across CLI Invocations"
description: "Propose atomic local quota coordination and provider-header discovery for concurrent tnh-gen processes."
owner: "aaronksolomon"
author: "Codex"
status: proposed
created: "2026-10-13"
---
# ADR-TG07: Shared Provider Rate Limits Across CLI Invocations

- **Status**: Proposed
- **Date**: 2026-10-13
- **Related**: [ADR-A15](/architecture/gen-ai-service/adr/adr-a15-thread-safety-rate-limiting.md), [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md), [ADR-TG06](/architecture/tnh-gen/adr/adr-tg06-runtime-status-events.md)

## Context

Paragraph-by-paragraph grammar editing launches concurrent `tnh-gen` processes.
An instance-local limiter cannot coordinate them or survive a new invocation.
The workflow's shared thread limiter only coordinates one runner process.

ADR-A15 already proposes thread safety and provider-aware limiting; it remains
proposed and its roadmap item is paused. This recommendation extends that work
to independent CLI processes. Current `infra/rate_limit.py` is a placeholder;
`OpenAIClient` has retries but does not expose provider quota headers to a
shared coordinator (`src/tnh_scholar/gen_ai_service/infra/rate_limit.py:1`,
`src/tnh_scholar/gen_ai_service/providers/openai_client.py:59`).

OpenAI supplies limits, remaining capacity, and reset times in response
headers. Limits apply to organizations/projects and can be shared by models;
they are not a fixed per-user concurrency count. Discover them from ordinary
API responses rather than assume an account-tier lookup endpoint exists.
See [official rate-limit guidance](https://developers.openai.com/api/docs/guides/rate-limits).

## Proposed decision

1. **Shared state:** use a SQLite coordinator under the resolved TNH user root
   (`state/provider-rate-limits.sqlite3`) so invocations and worktrees on one
   machine share atomic request/token reservations. A log is optional audit
   output, not the coordination mechanism. Keep transactions short and never
   hold a database lock during a network request or sleep.
2. **Architecture:** define typed Pydantic quota observations, reservations,
   and decisions, with a domain `RateLimitCoordinator` Protocol and a SQLite
   infrastructure adapter. Provider transports capture headers; bidirectional
   mappers normalize them. Enforce admission around each actual transport
   attempt, so retries count too. CLI presentation stays in the application
   layer; other GenAIService callers reuse the same policy.
3. **Scope:** key quota buckets by provider, nonsecret organization/project or
   configured account scope, and provider quota group. Honor overlapping
   organization/project constraints and known shared model groups. Do not use
   API keys as stored identifiers or assume different keys imply different
   quotas. Use conservative grouping when the scope cannot be inferred.
4. **Discovery:** persist normalized `x-ratelimit-limit-*`, remaining/reset
   headers, project-token headers when supplied, and `Retry-After`. Include
   observation time, request correlation, and freshness. Bootstrap missing
   observations with conservative configured caps; user caps may lower learned
   limits. Registry tiers are hints, not authoritative account state.
5. **Admission:** atomically reserve request and estimated token capacity before
   sending; pace starts and wait outside transactions. Reconcile responses
   with outstanding reservations conservatively: out-of-order headers must not
   replenish capacity prematurely. A cancellation before sending releases its
   reservation; sent or uncertain attempts retain it until the applicable
   reset/expiry. Expired observations revert to bootstrap policy, not unlimited
   capacity. Persist no prompts, outputs, credentials, or raw header dumps.
6. **Retries and observability:** use one bounded retry controller, disabling
   opaque SDK retries or integrating each attempt into admission. Honor valid
   `Retry-After`; use jittered backoff otherwise. Distinguish throttling from
   exhausted quota/billing errors. Expose typed wait/limit diagnostics without
   polluting result stdout. Respect cancellation and an overall deadline.

## Consequences

Separate invocations coordinate automatically and learn actual provider limits.
SQLite adds local state, schema migration, and crash/clock recovery requirements.
Traffic from other machines remains outside local reservations, so header
reconciliation and configured headroom still matter. This does not promise
perfect prediction of provider throttling.

## Alternatives

- **Append-only log or unlocked JSON:** insufficient atomic admission semantics.
- **Per-process buckets:** retain the current cross-invocation gap.
- **Redis/shared service:** a future adapter for multi-host coordination; unnecessary
  for the initial local CLI implementation.

## Acceptance and follow-up

Test independent processes contending for one quota; overlapping quota groups;
missing/stale/out-of-order headers; retries; cancellation; crash recovery;
clock changes; and store failures. A missing/corrupt store must not silently
disable coordination. Keep configuration in Settings → Config → Params → Policy.
Resolve reservation leases, freshness defaults, and scope identification in
the implementation design. This draft is a feature recommendation; ADR-A15's
existing implementation work remains separately tracked.
