---
key: section_by_break
name: Section by Break
version: "1.0"
description: Divides text transcript into sections based on existing structural breaks
task_type: sectioning
role: sectioning
required_variables:
  - source_language
  - section_count
  - metadata
optional_variables:
  - field_language
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: section_count
    required: true
    strictness: strict
  - name: metadata
    required: true
    strictness: strict
  - name: field_language
    required: false
    strictness: loose
tags:
  - sectioning
  - transcript
  - metadata
  - structure
default_variables:
  field_language: English
default_model: gpt-4o
output_contract:
  mode: json
  schema_ref: tnh.sectioning.section_by_break.v1
output_mode: json
safety_level: safe
schema_version: "1.0"
---

Divide the numbered transcript into approximately {{ section_count }} sections, using existing structural breaks when possible.

Known metadata:
{{ metadata }}

Requirements:
- Input lines are `NUM:LINE`.
- Prefer structural cues over thematic interpretation.
- Do not break sections mid-sentence when avoidable.
- Smaller sections are preferable to overly large ones.
- Section start lines must be strictly increasing.
- Return sections in order.

Also produce:
- a concise summary in {{ source_language }}
- Dublin Core metadata in YAML with field names in {{ field_language }} and values in {{ source_language }}
- key concepts in {{ source_language }}
- narrative context in {{ source_language }}

Return the exact response format expected by the caller.
