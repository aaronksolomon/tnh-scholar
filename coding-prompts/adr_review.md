---
key: adr_review
name: ADR Review
version: "1.0.0"
description: "Review a recent ADR set for implementation risks and ambiguities."
task_type: "architecture-review"
required_variables: []
optional_variables: []
default_variables: {}
tags:
  - golden
  - architecture
  - review
default_model: gpt-5.4
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Review the provided ADR material as if you were preparing to implement it.

Output requirements:
- Start with `Findings:`
- Provide 3 to 5 concise findings
- Each finding must include:
  - a short severity label in brackets: `[high]`, `[medium]`, or `[low]`
  - the specific concern
  - why it matters for implementation
- End with `Overall:` followed by one short sentence

Focus on:
- missing operational constraints
- ambiguity between ADR intent and implementable behavior
- rollback/workspace/provenance edge cases
- review or policy gaps that could cause unsafe automation

Do not summarize the whole ADR unless needed for a finding.
