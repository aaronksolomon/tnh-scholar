---
title: "Installation"
description: "TNH Scholar--Python package for text processing and analysis. Install it using pip:"
owner: ""
author: ""
status: processing
created: "2025-02-01"
---
# Installation

TNH Scholar--Python package for text processing and analysis. Install it using pip:

```bash
pip install tnh-scholar
```

## System Requirements

- Python 3.12.4
- OpenAI API key for AI-powered features
- Git (for pattern version control)

## Installation Options

### Basic Installation

For basic usage:

```bash
pip install tnh-scholar
tnh-setup  # Configure default patterns and directories
```

### Feature-Specific Installation

Install optional components based on your needs:

- OCR capabilities: `pip install "tnh-scholar[ocr]"`
- GUI tools: `pip install "tnh-scholar[gui]"`
- Query features: `pip install "tnh-scholar[query]"`
- Development tools: `pip install "tnh-scholar[dev]"`

## Configuration

1. Set your OpenAI API key:

   ```bash
   export OPENAI_API_KEY='your-api-key'
   ```

   Or add it to your .env file.

2. Run the setup tool:

   ```bash
   tnh-setup
   ```

   This will:
   - Create the configuration directory (~/.config/tnh-scholar)
   - Download default patterns
   - Set up initial configuration

## Verification

Verify your installation:

```bash
tnh-fab --help
```

## Common Issues

1. Missing API Key
   If you see authentication errors, ensure OPENAI_API_KEY is set correctly.

2. Python Version Mismatch
   TNH Scholar requires Python 3.12.4 exactly. Check your version:

   ```bash
   python --version
   ```

For troubleshooting, see our [GitHub Issues](https://github.com/aaronksolomon/tnh-scholar/issues).