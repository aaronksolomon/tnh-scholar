---
title: "TNH Scholar"
description: "TNH Scholar is an AI-driven project designed to explore, query, process and translate the teachings of Thich Nhat Hanh and the Plum Village community. The project provides tools for practitioners and scholars to engage with mindfulness and spiritual wisdom through natural language processing and machine learning models."
owner: ""
author: ""
status: processing
created: "2024-10-21"
---

# TNH Scholar

TNH Scholar is an AI-driven project designed to explore, query, process and translate the teachings of Thich Nhat Hanh and the Plum Village community. The project provides tools for practitioners and scholars to engage with mindfulness and spiritual wisdom through natural language processing and machine learning models.

## Vision & Goals

TNH Scholar aims to make the profound teachings of Thich Nhat Hanh and the Plum Village tradition more accessible and discoverable through modern AI techniques. By combining natural language processing, machine learning, and careful curation, we create pathways for practitioners and scholars to:

- Extract and organize key insights from dharma talks and written teachings
- Translate teachings across languages with cultural sensitivity
- Discover connections between topics and teachings
- Process audio recordings and transcripts into structured, searchable formats
- Engage with the tradition through both programmatic and interactive tools

## Features

TNH Scholar is currently in active prototyping phase. It provides several utility-like command-line tools for text and audio processing, built around a flexible pattern-based approach to text processing:

**Core Tools:**

- **audio-transcribe**: Process and transcribe audio files with speaker detection, including support for YouTube downloads
- **tnh-fab**: Text processing and formatting tool with capabilities for:
  - Adding/correcting punctuation and formatting
  - Identifying and organizing logical sections
  - Performing line-based and full-text translation
  - Applying custom text processing patterns
- **ytt-fetch**: Utility for downloading and preparing YouTube video transcripts
- **nfmt**: Tool for formatting and normalizing newlines in text files
- **token-count**: Count tokens in text files for LLM planning
- **tnh-setup**: Configuration and pattern setup utility for initializing projects

**Pattern System:**

Patterns are customizable templates that guide AI-powered text operations, allowing for consistent and adaptable processing across different types of content. Built-in patterns include:
- Metadata extraction and tagging
- Section marking and organization
- Quote detection and formatting
- Reference formatting and validation

## Quick Start

### Installation

#### From PyPI (CLI usage)

Install using pip:

```bash
pip install tnh-scholar
```

After installation, run the setup tool:

```bash
tnh-setup
```

#### Prerequisites

- Python 3.12.4+
- OpenAI API credentials (required for AI tools)
- Google Vision credentials (for OCR development and testing)
- pip or Poetry package manager

#### Development setup (from source)

If you plan to contribute or run the full test suite, follow the pyenv + Poetry workflow described in [DEV_SETUP.md](DEV_SETUP.md).

The short version:

1. Install `pyenv` and `Python 3.12.4`
2. Install Poetry and enable in-project virtual environments:
   ```bash
   poetry config virtualenvs.in-project true
   ```
3. Clone this repository and run:
   ```bash
   make setup        # runtime dependencies only
   make setup-dev    # runtime + dev dependencies (recommended)
   ```

### Set Up OpenAI Credentials

```bash
export OPENAI_API_KEY="your-api-key"
```

### Example Usage

**Transcribe Audio from YouTube:**

```bash
audio-transcribe --yt_url "https://youtube.com/watch?v=example" --split --transcribe
```

**Process Text with TNH-FAB:**

```bash
# Add punctuation
tnh-fab punctuate input.txt > punctuated.txt

# Translate text
tnh-fab translate -l vi input.txt > translated.txt

# Process text using a specific pattern
tnh-fab process -p format_xml input.txt > formatted.xml

# Create sections using default sectioning pattern
tnh-fab section input.txt > sections.json
```

**Download Video Transcripts:**

```bash
ytt-fetch "https://youtube.com/watch?v=example" -l en -o transcript.txt
```

## Documentation Overview

Comprehensive documentation is available in multiple formats:

- **Online Documentation**: [aaronksolomon.github.io/tnh-scholar/](https://aaronksolomon.github.io/tnh-scholar/)
- **GitHub Repository**: [github.com/aaronksolomon/tnh-scholar](https://github.com/aaronksolomon/tnh-scholar)

### Documentation Structure

- **[Getting Started](docs/getting-started/)** – Installation, setup, and first steps
- **[CLI Reference](docs/cli-reference/)** – Complete command-line tool documentation
- **[User Guide](docs/user-guide/)** – Detailed usage guides, patterns, and workflows
- **[API Reference](docs/api/)** – Python API documentation for programmatic use
- **[Architecture](docs/architecture/)** – Design decisions, ADRs, and system overview
- **[Development](docs/development/)** – Contributing guidelines and development setup
- **[Research](docs/research/)** – Research notes, experiments, and background
- **[Documentation Operations](docs/docs-ops/)** – Documentation roadmap and maintenance

## Development

### Common Development Commands

Run from the repo root:

```bash
make test         # Run test suite (poetry run pytest)
make lint         # Check code style (poetry run ruff check .)
make format       # Format code (poetry run ruff format .)
make docs         # Generate and build documentation
poetry run mypy src/  # Run type checking
```

For detailed development instructions, troubleshooting, and CI guidance, see [DEV_SETUP.md](DEV_SETUP.md).

### Optional Dependencies

TNH Scholar offers several optional dependency groups:

```bash
# OCR functionality (development only)
pip install "tnh-scholar[ocr]"

# GUI tools (development only)
pip install "tnh-scholar[gui]"

# Query capabilities (development only)
pip install "tnh-scholar[query]"

# Development tools
pip install "tnh-scholar[dev]"
```

## Contributing

We welcome contributions from practitioners, developers, and scholars interested in making these teachings more accessible. Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Running tests and code quality checks
- Opening pull requests
- Code style and conventions

## Project Status

TNH Scholar is currently in **alpha stage** (v0.1.3). While the core functionality is relatively stable, the API and features will change continuously with development.

## Support & Community

- **Bug Reports & Feature Requests**: [GitHub Issue Tracker](https://github.com/aaronksolomon/tnh-scholar/issues)
- **Questions & Discussions**: [GitHub Discussions](https://github.com/aaronksolomon/tnh-scholar/discussions) or consult our [documentation](https://aaronksolomon.github.io/tnh-scholar/)

## License

This project is licensed under the [GPL-3.0 License](LICENSE).

---

**For more information, visit the [full documentation](https://aaronksolomon.github.io/tnh-scholar/) or explore the [source code](https://github.com/aaronksolomon/tnh-scholar).**
