---
title: "Installation"
description: "Install instructions for TNH Scholar, a Python package for text processing and analysis, using `pip`."
owner: ""
author: ""
status: current
created: "2025-02-01"
---
# Installation

Install instructions for TNH Scholar, a Python package for text processing and analysis, using `pip`.

Simple install:

```bash
pip install tnh-scholar
```

## System Requirements

- Python 3.12.4
- OpenAI API key for AI-powered features
- Git (for prompt version control)

## Installation Options

### Basic Installation

For basic usage:

```bash
pip install tnh-scholar
tnh-setup  # Configure default prompts and directories
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
   - Download default prompts
   - Set up initial configuration

## Verification

Verify your installation:

```bash
tnh-gen version
```

You should see output like:

```text
tnh-gen 0.2.2 (tnh-scholar 0.2.2)
Python 3.12.4 on darwin
```

Test the CLI:

```bash
# List available prompts
tnh-gen list

# Show help for all commands
tnh-gen --help
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
