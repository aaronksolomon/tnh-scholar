---
title: "Quick Start Guide"
description: "TNH Scholar provides powerful text processing capabilities through several command-line tools. This guide will help you get started with the basic workflows."
owner: ""
author: ""
status: processing
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

### tnh-fab

The main text processing tool, providing functions for:

- Text punctuation and formatting
- Section analysis
- Translation
- Prompt-based processing

Example usage:

```bash
# Add punctuation to text
tnh-fab punctuate input.txt > punctuated.txt

# Translate Vietnamese text to English
tnh-fab translate -l vi input.txt > translated.txt
```

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

### Text Processing Pipeline

```bash
# Complete processing pipeline
cat input.txt | \
tnh-fab punctuate | \
tnh-fab section | \
tnh-fab translate -l vi | \
tnh-fab process -p format_xml > output.xml
```

### Audio Processing

```bash
# Download and transcribe
audio-transcribe --yt_url "https://example.com/video" --split --transcribe

# Post-process transcription
tnh-fab punctuate transcript.txt | \
tnh-fab section > processed.txt
```

## Next Steps

- Review the [Prompt System](/user-guide/prompt-system.md) documentation
- Explore detailed [CLI documentation](/cli-reference/overview.md) for all available tools
- Check out example notebooks in the repository
