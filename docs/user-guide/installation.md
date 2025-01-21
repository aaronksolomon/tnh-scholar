# Installation

TNH Scholar can be installed using pip:

```bash
pip install tnh-scholar
```

## Prerequisites

- Python 3.12.4 or higher
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

