---
title: "tnh-fab"
description: "## Overview"
owner: ""
status: processing
created: "2025-01-19"
---
# tnh-fab

## Overview

`tnh-fab` is a specialized command-line tool, part of the Thich Nhat Hanh Scholar Project.
`tnh-fab` can process multilingual texts using AI 'patterns'.
It is originally developed to work with processing Dharma-based materials such as talks by Thich Nhat Hanh.

It provides functionality for:

- Adding/correcting punctuation
- Identifying logical sections
- Performing line-based translation
- Applying custom text processing patterns

## Installation

```bash
pip install tnh-scholar
```

## Basic Usage

```bash
tnh-fab [COMMAND] [OPTIONS] [INPUT_FILE]
```

Input can be provided either as a file or through standard input (stdin).

Global options:

```bash
-v, --verbose        Enable detailed logging
--debug             Enable debug output
--quiet             Suppress all non-error output
```

## Commands

### 1. Punctuate

Adds or corrects punctuation based on language-specific rules.

Basic usage:

```bash
tnh-fab punctuate [OPTIONS] [INPUT_FILE]
```

Options:

```plaintext
-l, --language      Source language code (auto-detected if not specified)
-y, --style         Punctuation style (default: 'APA')
-c, --review-count  Number of review passes (default: 3)
-p, --pattern       Pattern name (default: 'default_punctuate')
```

Examples:

```bash
# Basic punctuation of a file
tnh-fab punctuate input.txt

# Punctuate Vietnamese text with specific style
tnh-fab punctuate -l vi -y "Modern" vietnamese_text.txt

# Process from stdin with extra review passes
cat unpunctuated.txt | tnh-fab punctuate -c 5

# Use custom pattern with specific language
tnh-fab punctuate -p dharma_punctuation -l en text.txt
```

### 2. Section

Analyzes text and divides it into logical sections.

Basic usage:

```bash
tnh-fab section [OPTIONS] [INPUT_FILE]
```

Options:

```plaintext
-l, --language      Source language code (auto-detected if not specified)
-n, --num-sections  Target number of sections (auto-calculated if not specified)
-c, --review-count  Number of review passes (default: 3)
-p, --pattern       Pattern name (default: 'default_section')
```

Examples:

```bash
# Auto-detect sections
tnh-fab section dharma_talk.txt

# Create specific number of sections
tnh-fab section -n 5 long_text.txt

# Section Vietnamese text with custom pattern
tnh-fab section -l vi -p vn_section_pattern text.txt

# Process from stdin and save to file
cat text.txt | tnh-fab section > sections.json
```

### 3. Translate

Performs line-by-line translation while maintaining structure.

Basic usage:

```bash
tnh-fab translate [OPTIONS] [INPUT_FILE]
```

Options:

```plaintext
-l, --language       Source language code (auto-detected if not specified)
-r, --target         Target language code (default: 'en')
-y, --style          Translation style
--context-lines      Number of context lines (default: 3)
--segment-size       Lines per translation segment (auto-calculated if not specified)
-p, --pattern        Pattern name (default: 'default_line_translation')
```

Examples:

```bash
# Basic Vietnamese to English translation
tnh-fab translate -l vi vietnamese_text.txt

# Translation with specific style
tnh-fab translate -l vi -y "American Dharma Teaching" text.txt

# French translation with increased context
tnh-fab translate -l vi -r fr --context-lines 5 text.txt

# Custom segment size and pattern
tnh-fab translate --segment-size 20 -p custom_translation text.txt
```

### 4. Process

Applies custom pattern-based processing with flexible structuring.

Basic usage:

```bash
tnh-fab process -p PATTERN [OPTIONS] [INPUT_FILE]
```

Options:

```plaintext
-p, --pattern     Pattern name (required)
-s, --section     Process using sections from JSON file
-g, --paragraph   Process text by paragraphs
-t, --template    YAML file with template values
```

Examples:

```bash
# Basic processing with pattern
tnh-fab process -p format_xml input.txt

# Process using sections from file
tnh-fab process -p format_xml -s sections.json input.txt

# Process by paragraphs
tnh-fab process -p format_xml -g long_text.txt

# Process with template values
tnh-fab process -p format_xml -t template.yaml input.txt
```

## Advanced Usage Examples

### Pipeline Processing

#### 1. Punctuate, section, and process

```bash
cat raw_text.txt | \
tnh-fab punctuate -l vi | \
tnh-fab section -n 5 | \
tnh-fab process -p format_xml > final_output.xml
```

#### 2. Section and translate

```bash
tnh-fab section input.txt > sections.json
tnh-fab translate -l vi -s sections.json input.txt > translated.txt
```

#### 3. Complete processing pipeline

```bash
cat vietnamese_text.txt | \
tnh-fab punctuate -l vi -y "Modern" | \
tnh-fab section --num-sections 10 | \
tnh-fab translate -r en --context-lines 5 | \
tnh-fab process -p format_xml > final_output.xml
```

## Pattern System

Patterns are stored in the pattern directory (default or specified by TNH_PATTERN_DIR environment variable). Each command uses specific default patterns that can be overridden using the -p option.

For information about creating custom patterns, please refer to the pattern documentation.