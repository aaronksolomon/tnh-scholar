---
title: "TNH Scholar README"
description: "TNH Scholar is an AI-driven project designed to explore, query, process and translate the teachings of Thich Nhat Hanh and the Plum Village community. The project provides tools for practitioners and scholars to engage with mindfulness and spiritual wisdom through natural language processing and machine learning models."
owner: ""
author: ""
status: continuous update
created: "2024-10-21"
---

# TNH Scholar README

TNH Scholar is an AI-driven project designed to explore, query, process and translate the teachings of Thich Nhat Hanh and the Plum Village community. The project provides tools for practitioners and scholars to engage with mindfulness and spiritual wisdom through natural language processing and machine learning models.

## Vision & Goals

TNH Scholar aims to make the teachings of Thich Nhat Hanh and the Plum Village tradition more accessible and discoverable through modern AI techniques. By combining natural language processing, machine learning, and careful curation, we create pathways for practitioners and scholars to translate, search, organize, process and otherwise find meaningful connections among the body of teachings.

## Features

TNH Scholar is currently in active prototyping. Key capabilities:

- **Audio and transcript processing**: `audio-transcribe` with diarization and YouTube support
- **Text formatting and translation**: `tnh-gen` CLI (rename in flight; see [ADR-VSC01](docs/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md) and [ADR-VSC02](docs/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md)) for punctuation, translation, sectioning, and prompt-driven processing
- **Acquisition utilities**: `ytt-fetch` for transcripts; `token-count` and `nfmt` for prep and planning
- **Setup and configuration**: `tnh-setup` plus guided config in Getting Started
- **Prompt system**: See ADRs under [docs/architecture/prompt-system/index.md](docs/architecture/prompt-system/index.md) for decisions and roadmap

## Quick Start

### Installation (PyPI)

```bash
pip install tnh-scholar
tnh-setup
```

Prerequisites: Python 3.12.4+, OpenAI API key (CLI tools), Google Vision (optional OCR), pip or Poetry.

### Development setup (from source)

Follow [DEV_SETUP.md](DEV_SETUP.md) for the full workflow. Short version:

```bash
pyenv install 3.12.4
poetry config virtualenvs.in-project true
make setup        # runtime deps
make setup-dev    # runtime + dev deps (recommended)
```

### Set OpenAI credentials

```bash
export OPENAI_API_KEY="your-api-key"
```

### Example usage

**Transcribe Audio from YouTube:**

```bash
audio-transcribe --yt_url "https://youtube.com/watch?v=example" --split --transcribe
```

**Process Text with TNH-GEN (was previously tnh-fab: CLI refactor and rename in progress; see ADR-VSC01/VSC02):**

**Download Video Transcripts:**

```bash
ytt-fetch "https://youtube.com/watch?v=example" -l en -o transcript.txt
```

## Getting Started

- **Practitioners**: Install, configure credentials, and follow the [Quick Start Guide](docs/getting-started/quick-start-guide.md); workflows live in the [User Guide](docs/user-guide/overview.md).
- **Developers**: Set up via [DEV_SETUP.md](DEV_SETUP.md) and [Contributing](CONTRIBUTING.md); review [System Design](docs/development/system-design.md) and the [CLI docs](docs/cli-reference/index.md); run `make docs` to view locally.
  - **Project Philosophy & Vision**: Developers and researchers should review the conceptual foundations in `docs/project/vision.md`, `docs/project/philosophy.md`, `docs/project/principles.md`, and `docs/project/conceptual-architecture.md` to understand the system’s long-term direction and design intent.
- **Researchers**: Explore [Research](docs/research/index.md) for experiments and direction; see [Architecture](docs/architecture/index.md) for pipelines/ADRs (e.g., [ADR-K01](docs/architecture/knowledge-base/adr/adr-k01-kb-architecture-strategy.md)).

## Documentation Overview

Comprehensive documentation is available in multiple formats:

- **Online Documentation**: [aaronksolomon.github.io/tnh-scholar/](https://aaronksolomon.github.io/tnh-scholar/)
- **GitHub Repository**: [github.com/aaronksolomon/tnh-scholar](https://github.com/aaronksolomon/tnh-scholar)

### Documentation Structure

- **[Getting Started](docs/getting-started/index.md)** – Installation, setup, and first steps
- **[CLI Docs](docs/cli-reference/index.md)** – Command-line tool documentation
- **[User Guide](docs/user-guide/index.md)** – Detailed usage guides, prompts, and workflows
- **[API Reference](docs/api/index.md)** – Python API documentation for programmatic use
- **[Architecture](docs/architecture/index.md)** – Design decisions, ADRs, and system overview
- **[Development](docs/development/index.md)** – Contributing guidelines and development setup
- **[Research](docs/research/index.md)** – Research notes, experiments, and background
- **[Documentation Operations](docs/docs-ops/index.md)** – Documentation roadmap and maintenance

## Architecture Overview

- Documentation strategy: [ADR-DD01](docs/architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md) and [ADR-DD02](docs/architecture/docs-system/adr/adr-dd02-main-content-nav.md)
- GenAI, transcription, and prompt system ADRs live under [Architecture](docs/architecture/index.md) (see ADR-A*, ADR-TR*, ADR-PT*).
- System design references: [Object–Service Design](docs/architecture/object-service/object-service-design-overview.md) and [System Design](docs/development/system-design.md).

## Development

- Common commands: `make test`, `make lint`, `make format`, `make docs`, `poetry run mypy src/`
- Optional dependency groups (development only): `tnh-scholar[ocr]`, `tnh-scholar[gui]`, `tnh-scholar[query]`, `tnh-scholar[dev]`
- Troubleshooting and workflows: [DEV_SETUP.md](DEV_SETUP.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards, testing expectations, and PR workflow. We welcome contributions from practitioners, developers, and scholars.

## Project Status

TNH Scholar is currently in **alpha stage** (v0.1.3). Expect ongoing API and workflow changes during active development.

## Support & Community

- Bug reports & feature requests: [GitHub Issues](https://github.com/aaronksolomon/tnh-scholar/issues)
- Questions & discussions: [GitHub Discussions](https://github.com/aaronksolomon/tnh-scholar/discussions)

## Documentation Map

For an auto-generated list of every document (titles and metadata), see the [Documentation Index](docs/documentation_index.md).

## License

This project is licensed under the [GPL-3.0 License](LICENSE).

---

**For more information, visit the [full documentation](https://aaronksolomon.github.io/tnh-scholar/) or explore the [source code](https://github.com/aaronksolomon/tnh-scholar).**
