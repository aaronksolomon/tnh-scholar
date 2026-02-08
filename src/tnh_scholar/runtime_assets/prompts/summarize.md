---
key: summarize
name: Summarize
version: "1.0.0"
description: "Summarize the input text in concise bullet points."
task_type: "summarize"
required_variables: []
optional_variables:
  - input_text
default_variables: {}
tags:
  - builtin
  - summary
---
You are a helpful assistant. Summarize the following text in 3-5 concise bullet points.

Text:
{{ input_text }}
