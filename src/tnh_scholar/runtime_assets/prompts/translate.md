---
key: translate
name: Translate
version: "1.0.0"
description: "Translate input text between languages."
task_type: "translate"
required_variables:
  - source_language
  - target_language
optional_variables:
  - input_text
default_variables: {}
tags:
  - builtin
  - translate
---
Translate the following text from {{ source_language }} to {{ target_language }}.

Text:
{{ input_text }}
