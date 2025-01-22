# Installation

TNH Scholar can be installed using pip:

```bash
pip install tnh-scholar
```

The project configuration can then setup using:
```bash
tnh-setup
```

`tnh-setup` prompts to download default patterns.

NOTE: You must have OpenAI API credentials to use the AI tools.
The environment variable OPENAI_API_KEY must be set to your API key.

## Prerequisites

- Python 3.12.4
- pip package manager

## Development Installation

For development work, clone the repository and install in editable mode with development dependencies:

```bash
git clone https://github.com/aaronksolomon/tnh-scholar.git
cd tnh-scholar
pip install -e ".[dev]"
```

## Optional Dependencies

TNH Scholar has several optional dependency groups:

- OCR functionality: `pip install "tnh-scholar[ocr]"`
- GUI tools: `pip install "tnh-scholar[gui]"`
- Query capabilities: `pip install "tnh-scholar[query]"`
- Development tools: `pip install "tnh-scholar[dev]"`

