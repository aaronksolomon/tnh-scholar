# TNH Scholar

TNH Scholar is an AI-driven project designed to explore, query, process and translate the teachings of Thich Nhat Hanh and the Plum Village community. The project provides tools for practitioners and scholars to engage with mindfulness and spiritual wisdom through natural language processing and machine learning models.

## Features

Currently TNH Scholar is in a rapid prototyping phase. It currently provides several utility-like command-line tools for text and audio processing, built around a flexible pattern-based approach to text processing. Patterns are customizable templates that guide AI-powered text operations, allowing for consistent and adaptable processing across different types of content.

- **audio-transcribe**: Process and transcribe audio files, with support for YouTube downloads
- **tnh-fab**: Text processing and formatting tool with capabilities for:
  - Adding/correcting punctuation
  - Identifying logical sections
  - Performing line-based translation
  - Applying custom text processing patterns
- **ytt-fetch**: Utility for downloading YouTube video transcripts
- **nfmt**: Tool for formatting newlines in text files
- **tnh-setup**: Configuration and pattern setup utility

## Installation

### From PyPI (CLI usage)

Install using pip:

```bash
pip install tnh-scholar
```

After installation, run the setup tool:

```bash
tnh-setup
```

### Prerequisites

- Python 3.12.4
- OpenAI API credentials (required for AI tools)
- Google Vision credentials (for OCR development and testing)
- pip package manager

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

### Development setup (from source)

If you plan to contribute or run the full test suite, follow the pyenv + Poetry workflow described in [DEV_SETUP.md](DEV_SETUP.md).  
The short version:

1. Install `pyenv` and `Python 3.12.4`.
2. Install Poetry and enable in-project virtual environments:  
   `poetry config virtualenvs.in-project true`
3. Clone this repository and run the provided Make targets:

```bash
make setup        # runtime dependencies only
make setup-dev    # runtime + dev dependencies (recommended)
```

Common development commands (run from the repo root):

```bash
make test         # or: poetry run pytest
make lint         # poetry run ruff check .
make format       # poetry run ruff format .
poetry run mypy src/
```

For step-by-step instructions, troubleshooting tips, and CI guidance, see [DEV_SETUP.md](DEV_SETUP.md).

## Quick Start

### Set Up OpenAI Credentials

```bash
export OPENAI_API_KEY="your-api-key"
```

### Transcribe Audio from YouTube

```bash
audio-transcribe --yt_url "https://youtube.com/watch?v=example" --split --transcribe
```

### Process Text with TNH-FAB

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

### Download Video Transcripts

```bash
ytt-fetch "https://youtube.com/watch?v=example" -l en -o transcript.txt
```

## Documentation

Comprehensive documentation is available at:

- [Online Documentation](https://aaronksolomon.github.io/tnh-scholar/)
- [GitHub Repository](https://github.com/aaronksolomon/tnh-scholar)

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to set up the environment, run tests, and open pull requests.

## License

This project is licensed under the [GPL-3.0 License](LICENSE).

## Development Status

TNH Scholar is currently in alpha stage (v0.1.3). While the core functionality is relatively stable, the API and features will change continuously with development.

## Support

For bug reports and feature requests, please use our [GitHub Issue Tracker](https://github.com/aaronksolomon/tnh-scholar/issues).

For questions about using TNH Scholar, please consult our [documentation](https://aaronksolomon.github.io/tnh-scholar/) or open a discussion on GitHub.
