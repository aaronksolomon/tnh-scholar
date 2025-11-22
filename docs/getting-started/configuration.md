---
title: "Configuration"
description: "TNH Scholar requires some initial configuration to function properly. This guide covers the essential configuration steps and options."
owner: ""
author: ""
status: processing
created: "2025-02-01"
---
# Configuration

TNH Scholar requires some initial configuration to function properly. This guide covers the essential configuration steps and options.

## Environment Setup

### OpenAI API Key

TNH Scholar's AI functionality requires an OpenAI API key. To configure this:

1. Obtain an API key from [OpenAI's platform](https://platform.openai.com/api-keys)
2. Set the environment variable:

   ```bash
   # Linux/Mac
   export OPENAI_API_KEY='your-api-key-here'
   
   # Windows
   set OPENAI_API_KEY=your-api-key-here
   ```

In development configuration (where you have downloaded the tnh-scholar repository) you can also use a `.env` file in your project directory:

```bash
OPENAI_API_KEY=your-api-key-here
```

### Directory Structure

TNH Scholar creates and uses the following directory structure:

```plaintext
~/.config/tnh_scholar/
├── patterns/         # Pattern storage
└── logs/            # Log files
```

## Pattern Configuration

### Pattern Directory

Patterns can be stored in:

1. Default location: `~/.config/tnh_scholar/patterns/`
2. Custom location specified by `TNH_PATTERN_DIR` environment variable

To use a custom pattern directory:

```bash
export TNH_PATTERN_DIR=/path/to/patterns
```

### Default Patterns

The system includes several default patterns:

- default_punctuate.md
- default_section.md
- default_line_translation.md
- default_xml_format.md
- default_xml_paragraph_format.md

These can be downloaded during setup or manually added later.

## Configuration File

The system looks for configuration in this order:

1. Command line arguments
2. Environment variables
3. Project-level config: `./.tnh-fab.yaml`
4. User-level config: `~/.config/tnh_scholar/tnh-fab/config.yaml`

Example configuration file:

```yaml
defaults:
  language: auto
  output_format: txt
  
punctuate:
  pattern: default_punctuate
  style: APA
  review_count: 3
  
section:
  pattern: default_section
  review_count: 3
  
translate:
  pattern: default_line_translation
  target_language: en
  style: "American Dharma Teaching"
  context_lines: 3
  review_count: 3
  
process:
  wrap_document: true
  
patterns:
  path: ~/.config/tnh_scholar/patterns
  
logging:
  level: INFO
  file: ~/.tnh-fab.log
```

## Initial Setup

The `tnh-setup` command automates configuration:

```bash
# Full setup
tnh-setup

# Skip specific steps
tnh-setup --skip-env        # Skip API key check
tnh-setup --skip-patterns   # Skip pattern download
```

This will:

1. Create necessary directories
2. Offer to download default patterns
3. Check for OpenAI API key
4. Set up basic configuration