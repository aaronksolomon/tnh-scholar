---
key: release_consistency_review
name: Release Consistency Review
version: "1.0"
description: "Review a bundle of high-level project docs for release-facing consistency and produce concrete recommended changes."
task_type: analysis
required_variables: []
optional_variables: []
tags:
  - release
  - docs
  - consistency
  - review
default_model: gpt-5.4
output_mode: text
safety_level: safe
schema_version: "1.0"
---

# Release Consistency Review

## Task

Review the provided high-level documentation bundle for release-facing consistency.

Focus on:

- version and release framing consistency
- alignment between README and higher-level project/development docs
- user-facing status claims that appear stale, confusing, or contradictory
- terminology consistency
- command/example consistency when high-level docs mention concrete workflows

Do not rewrite the docs.
Do not propose broad architecture changes.
Do not comment on style unless it affects clarity or consistency.

## Output

Output markdown with exactly these sections:

### Top Findings

- 5 to 10 bullets max
- each bullet must name the file and the concrete issue
- prioritize highest-value release-facing inconsistencies first

### Recommended Changes

- provide concrete recommended edits
- each bullet must include:
  - file path
  - section or heading when possible
  - a short recommended change in plain language

### Lower Priority Notes

- optional
- only include items worth tracking later

### Overall Assessment

- 1 short paragraph
- say whether the docs are broadly release-ready or still noticeably inconsistent

Constraints:

- be concise
- be concrete
- no nested bullets
- no code fences
