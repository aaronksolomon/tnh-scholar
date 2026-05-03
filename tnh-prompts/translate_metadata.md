---
key: translate_metadata
name: Translate Metadata
version: "1.0"
description: Translates YAML metadata fields and values to target language
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
  - metadata
  - yaml
default_variables:
  target_language: English
default_model: gpt-4o-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Translate the YAML metadata into {{ target_language }}.

Requirements:
- Preserve valid YAML structure exactly.
- Translate field names and values when appropriate.
- Do not add, omit, summarize, or explain anything.

Output only the YAML.
