---
title: "srt-translate"
description: "Translate SRT subtitle files while preserving timecodes, using TNH Scholar translation patterns."
owner: ""
author: "Codex"
status: current
created: "2025-12-10"
---
# srt-translate

Translate an SRT subtitle file from one language to another while keeping timecodes intact. Supports selecting a translation pattern and model, and writing the result to a new SRT file.

## Usage

```bash
srt-translate [OPTIONS] INPUT_FILE
```

## Options

- `-o, --output PATH` — Output file path (default: `<input>-<lang>.srt`).
- `-s, --source-language TEXT` — Source language code (auto-detected if omitted).
- `-t, --target-language TEXT` — Target language code (default: `en`).
- `-m, --model TEXT` — Optional model name to use for translation.
- `-p, --pattern TEXT` — Optional translation pattern name.
- `-g, --debug` — Enable debug logging.
- `-d, --metadata PATH` — Path to YAML front matter providing translation context.

## Examples

```bash
# Translate to English with defaults
srt-translate talk.srt

# Translate to French with a specific pattern and model
srt-translate talk.srt --target-language fr --pattern line_translate --model gpt-4o

# Write to a custom path and enable debug logging
srt-translate talk.srt --output translated.srt --debug
```
