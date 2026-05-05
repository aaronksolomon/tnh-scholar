---
key: default_section
name: Default Section
version: "1.0"
description: Divides text transcript into logical sections with metadata and Dublin Core fields
role: sectioning
required_variables:
  - source_language
  - document_metadata
optional_variables:
  - target_section_count
  - target_lines_per_section
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
  - name: target_lines_per_section
    required: false
    strictness: loose
tags:
  - sectioning
  - transcript
  - metadata
  - dublin-core
default_model: gpt-5.4
output_contract:
  mode: json
  schema_ref: tnh.sectioning.default_section.v1
output_mode: json
safety_level: safe
schema_version: "1.0"
---

Divide the numbered transcript into approximately {{ target_section_count or "a sensible number of" }} coherent sections and generate document-level context.

Existing metadata:
{{ document_metadata }}

Requirements:
- The input format is `NUM:LINE`.
- Section start lines must be strictly increasing.
- Sections must be contiguous and cover the entire transcript, including blank lines.
- The first section must start at line 1.
- Each next section must start exactly one line after the previous section ends.
- The final section must end at the final input line.
- Prefer good sectioning over hitting the target count exactly.
- Use existing headings or structural cues when useful.
- A rough target is about {{ target_lines_per_section or "the target_section_count-derived average" }} lines per section.
- Write section titles in {{ source_language }}.

Also produce:
- a concise summary in {{ source_language }}
- Dublin Core metadata in YAML with English field names and values in {{ source_language }}
- key concepts in {{ source_language }}
- narrative context in {{ source_language }}

Return the exact response format expected by the caller.
