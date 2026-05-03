---
key: translate_json
name: Translate JSON
version: "1.0"
description: Translates JSON schema field strings while preserving exact structure
task_type: translation
role: translation
required_variables:
  - target_language
optional_variables: []
inputs:
  - name: target_language
    required: true
    strictness: strict
tags:
  - translation
  - json
  - data
default_variables:
  target_language: English
default_model: gpt-4o-mini
output_contract:
  mode: json
  schema_ref: tnh.translation.translate_json.v1
output_mode: json
safety_level: safe
schema_version: "1.0"
---

Translate the JSON schema text into {{ target_language }}.

Requirements:
- Preserve valid JSON structure exactly.
- Translate only human-readable field strings.
- Do not translate filenames or identifiers that should remain stable.
- Do not add, omit, or wrap anything.

Output only the raw JSON.
