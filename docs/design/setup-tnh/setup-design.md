# minimal but extensible setup tool for the prototyping phase

Core Requirements:

1. Configuration directory setup (~/.config/tnh_scholar)
2. Basic .env file for API keys
3. Pattern directory preparation
4. Simple validation checks

## high-level design structure (iteration 1)

```plaintext
tnh-setup/
├── __init__.py
├── setup.py           # Main CLI entry point
├── config.py          # Configuration handling
├── patterns.py        # Pattern management 
└── validators.py      # Basic validation

Key Functions:
1. Directory Setup
   - Create ~/.config/tnh_scholar
   - Create patterns subdirectory
   - Create logs subdirectory

2. Environment Setup
   - Create/update .env file
   - Basic OpenAI key validation
   - (Optional) Google Cloud key setup

3. Pattern Setup
   - Create patterns directory
   - Minimal set of default patterns
   - (Future) Pattern repository integration

4. Validation
   - Check directory permissions
   - Verify API key format
   - Test pattern loading
```

For prototyping, suggested implementation these core functions:

1. Directory creation
2. Basic .env file with OpenAI key
3. Pattern directory preparation
4. Simple CLI interface

## high-level design structure (iteration 2)

```plaintext
TNH-SETUP TOOL DESIGN

1. Core Functions

   - Create config directory (~/.config/tnh_scholar)

   - Set up OpenAI API key in .env

   - Optional pattern download

2. User Flow

   A. Config Directory

      - Create ~/.config/tnh_scholar

      - Create logs subdirectory

   B. Environment Setup 

      - Prompt for OpenAI API key

      - Create/update .env file

   C. Pattern Setup (Optional)

      - Show confirmation message:

        "Public pattern files (markdown templates) will be downloaded from:

         https://github.com/aaronksolomon/patterns 

         and installed to: ~/.config/tnh_scholar/patterns"

      - If confirmed, download and extract patterns

3. Command Line Interface

   tnh-setup [OPTIONS]

   Options:

   --skip-env        Skip API key setup

   --skip-patterns   Skip pattern download

4. Files Structure

   setup/

   ├── init.py

   ├── setup.py      # Main CLI tool

   └── download.py   # Pattern download function

5. Dependencies

   - click

   - requests

   - python-dotenv

```
