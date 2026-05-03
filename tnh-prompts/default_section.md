---
key: default_section
name: Default Section
version: "1.0"
description: Divides text transcript into logical sections with metadata and Dublin Core fields
task_type: sectioning
role: sectioning
required_variables:
  - source_language
  - section_count
  - line_count
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
  - name: line_count
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
  - dublin-core
default_variables:
  field_language: English
default_model: gpt-4o
output_contract:
  mode: json
  schema_ref: tnh.sectioning.default_section.v1
output_mode: json
safety_level: safe
schema_version: "1.0"
---

Divide the numbered transcript into approximately {{ section_count }} coherent sections and generate document-level context.

Existing metadata:
{{ metadata }}

Requirements:
- The input format is `NUM:LINE`.
- Section start lines must be strictly increasing.
- Sections must be contiguous and cover the entire transcript.
- Prefer good sectioning over hitting the target count exactly.
- Use existing headings or structural cues when useful.
- A rough target is about {{ line_count }} lines per section.
- Write section titles in {{ source_language }}.

Also produce:
- a concise summary in {{ source_language }}
- Dublin Core metadata in YAML with field names in {{ field_language }} and values in {{ source_language }}
- key concepts in {{ source_language }}
- narrative context in {{ source_language }}

Return the exact response format expected by the caller.
