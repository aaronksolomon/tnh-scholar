---
key: section_by_break
name: Section by Break
version: "1.0"
description: Divides text transcript into sections based on existing structural breaks
role: sectioning
required_variables:
  - source_language
  - document_metadata
optional_variables:
  - target_section_count
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: document_metadata
    required: true
    strictness: strict
  - name: target_section_count
    required: false
    strictness: loose
tags:
  - sectioning
  - transcript
  - metadata
  - structure
default_model: gpt-5.4
output_contract:
  mode: json
  schema_ref: tnh.sectioning.section_by_break.v1
output_mode: json
safety_level: safe
schema_version: "1.0"
---

Divide the numbered transcript into approximately {{ target_section_count or "a sensible number of" }} sections, using existing structural breaks when possible.

Known metadata:
{{ document_metadata }}

Requirements:
- Input lines are `NUM:LINE`.
- Prefer structural cues over thematic interpretation.
- Do not break sections mid-sentence when avoidable.
- Smaller sections are preferable to overly large ones.
- Section start lines must be strictly increasing.
- The first section must start at line 1.
- Each next section must start exactly one line after the previous section ends.
- The final section must end at the final input line.
- Return sections in order.

Also produce:
- a concise summary in {{ source_language }}
- Dublin Core metadata in YAML with English field names and values in {{ source_language }}
- key concepts in {{ source_language }}
- narrative context in {{ source_language }}

Return the exact response format expected by the caller.
