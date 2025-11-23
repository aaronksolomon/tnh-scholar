---
title: "TNH Scholar"
description: "Comprehensive documentation for TNH Scholar, an AI-driven project exploring and processing the teachings of Thich Nhat Hanh and the Plum Village community."
owner: ""
author: ""
status: processing
created: "2025-01-19"
---

# TNH Scholar Documentation

Welcome to the TNH Scholar documentation. Here you'll find everything you need to get started, understand the tools, and contribute to the project.

TNH Scholar is an AI-driven project designed to explore, query, process and translate the teachings of Thich Nhat Hanh and the Plum Village community. The project provides tools for practitioners and scholars to engage with mindfulness and spiritual wisdom through natural language processing and machine learning models.

## Vision & Goals

TNH Scholar aims to make the profound teachings of Thich Nhat Hanh and the Plum Village tradition more accessible and discoverable through modern AI techniques. By combining natural language processing, machine learning, and careful curation, we create pathways for practitioners and scholars to:

- Extract and organize key insights from dharma talks and written teachings
- Translate teachings across languages with cultural sensitivity
- Discover connections between topics and teachings
- Process audio recordings and transcripts into structured, searchable formats
- Engage with the tradition through both programmatic and interactive tools

## Features

TNH Scholar provides several utility-like command-line tools for text and audio processing, built around a flexible pattern-based approach to text processing:

**Core Tools:**

- **audio-transcribe** – Process and transcribe audio files with speaker detection
- **tnh-fab** – Text processing and formatting tool for punctuation, translation, and pattern-based operations
- **ytt-fetch** – Utility for downloading and preparing YouTube video transcripts
- **nfmt** – Tool for formatting and normalizing newlines in text files
- **token-count** – Count tokens in text files for LLM planning
- **tnh-setup** – Configuration and pattern setup utility

**Pattern System:**

Patterns are customizable templates that guide AI-powered text operations, enabling consistent and adaptable processing across different types of content.

See the [CLI Reference](/cli-reference/) for complete documentation of all tools.

## Quick Start

### Installation

**From PyPI:**

```bash
pip install tnh-scholar
tnh-setup
```

**From Source (Development):**

See [Getting Started: Installation](/getting-started/installation/) for detailed instructions.

### Set Up Credentials

```bash
export OPENAI_API_KEY="your-api-key"
```

### First Steps

1. Try [Getting Started: Quick Start](/getting-started/quick-start/) for example commands
2. Explore [CLI Reference](/cli-reference/) for tool documentation
3. Learn about [Patterns](/user-guide/patterns/) for advanced text processing

## Documentation Overview

TNH Scholar documentation is organized into these main sections:

- **Getting Started** – [Installation](/getting-started/installation/), [Quick Start](/getting-started/quick-start/), [Configuration](/getting-started/configuration/)
- **CLI Reference** – Complete reference for all [command-line tools](/cli-reference/)
- **User Guide** – [Usage guides](/user-guide/), [patterns](/user-guide/patterns/), workflows
- **API Reference** – [Python API](/api/) for programmatic use
- **Architecture** – [System design](/architecture/), [design decisions](/architecture/adr/), [roadmap](/docs-ops/roadmap/)
- **Development** – [Development setup](/development/setup/), [contributing guide](/development/contributing/)
- **Research** – [Research notes](/research/), background, experiments

### By Role

**I'm a User** → Start with [Installation](/getting-started/installation/) → [Quick Start](/getting-started/quick-start/) → [CLI Reference](/cli-reference/)

**I'm a Developer** → [Development Setup](/development/setup/) → [API Reference](/api/) → [Contributing](/development/contributing/)

**I'm a Researcher** → [Research Notes](/research/) → [Architecture](/architecture/) → [Roadmap](/docs-ops/roadmap/)

## Contributing

We welcome contributions from practitioners, developers, and scholars. See the [Contributing Guide](/development/contributing/) for details on:

- Setting up your development environment
- Running tests and quality checks
- Opening pull requests
- Code style and conventions

## Development

### Common Commands

```bash
make setup        # Install runtime dependencies
make setup-dev    # Install dev dependencies
make test         # Run tests
make lint         # Check code style
make format       # Format code
make docs         # Build documentation
```

See [Development Setup](/development/setup/) for full instructions.

## Project Status

TNH Scholar is in **alpha stage** (v0.1.3). The core functionality is relatively stable, but the API and features will change with development. See the [Roadmap](/docs-ops/roadmap/) for upcoming work.

## Support & Community

- **Questions**: Consult this [documentation](/), or use [GitHub Discussions](https://github.com/aaronksolomon/tnh-scholar/discussions)
- **Bug Reports**: [GitHub Issue Tracker](https://github.com/aaronksolomon/tnh-scholar/issues)
- **Contribute**: See [Contributing Guide](/development/contributing/)

## License

This project is licensed under the [GPL-3.0 License](/license/).

---

**Next Steps**: [Get Started](/getting-started/installation/) | [Explore Tools](/cli-reference/) | [Read More](https://github.com/aaronksolomon/tnh-scholar)
