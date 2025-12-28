---
title: "Quick Start Guide"
description: "TNH Scholar provides powerful text processing capabilities through several command-line tools. This guide will help you get started with the basic workflows."
owner: ""
author: ""
status: current
created: "2025-02-01"
---
# Quick Start Guide

TNH Scholar provides powerful text processing capabilities through several command-line tools. This guide will help you get started with the basic workflows.

## Initial Setup

After installation, run the setup tool:

```bash
tnh-setup
```

This creates necessary directories and downloads default prompts.

## Core Tools

TNH Scholar includes several specialized tools:

### tnh-gen (Current)

The unified GenAI-powered text processing CLI. This is the primary tool for AI-based text transformations.

**Quick Start**:

```bash
# List available prompts
tnh-gen list

# Translate Vietnamese text to English
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --var source_lang=vi \
  --var target_lang=en \
  --output-file teaching.en.md

# Get machine-readable output for scripts
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --var source_lang=vi \
  --var target_lang=en \
  --api > output.json
```

**Key Features**:

- Human-friendly output by default
- `--api` flag for JSON output (VS Code, scripts)
- Prompt discovery with `tnh-gen list`
- Hierarchical configuration system

For complete documentation, see [tnh-gen CLI Reference](/cli-reference/tnh-gen.md).

### audio-transcribe

Process and transcribe audio content:

```bash
# Transcribe from YouTube
audio-transcribe --yt_url "https://youtube.com/watch?v=example" --split --transcribe

# Process local audio
audio-transcribe -f recording.mp3 --split --transcribe
```

### ytt-fetch

Download YouTube transcripts:

```bash
# Get English transcript
ytt-fetch "https://youtube.com/watch?v=example" -l en -o transcript.txt
```

### nfmt

Format text file newlines:

```bash
# Normalize newlines in a file
nfmt input.txt > formatted.txt
```

## Common Workflows

### Text Processing with tnh-gen

```bash
# Discover available prompts
tnh-gen list

# Filter prompts by tag
tnh-gen list --tag translation

# Translate a teaching
tnh-gen run --prompt translate \
  --input-file vietnamese_teaching.md \
  --var source_lang=vi \
  --var target_lang=en \
  --output-file english_teaching.md

# Summarize a dharma talk
tnh-gen run --prompt summarize \
  --input-file long_talk.md \
  --var max_length=500 \
  --output-file summary.md

# Use variables from JSON file
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --vars translation_config.json \
  --output-file output.md
```

### Audio Processing

```bash
# Download and transcribe
audio-transcribe --yt_url "https://example.com/video" --split --transcribe

# Post-process transcription with tnh-gen
tnh-gen run --prompt punctuate \
  --input-file transcript.txt \
  --var language=vi \
  --output-file punctuated.txt
```

## Next Steps

- Review the [Prompt System](/user-guide/prompt-system.md) documentation
- Explore detailed [CLI documentation](/cli-reference/overview.md) for all available tools
- Check out example notebooks in the repository
