---
title: "TNH-Gen CLI Architecture"
description: "Unified command-line interface for TNH Scholar GenAI operations"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: 
created: "2025-12-07"
auto_generated: false
---

# TNH-Gen CLI Architecture

The `tnh-gen` CLI is TNH Scholar's unified command-line interface for GenAI-powered text processing operations. It replaces the legacy `tnh-fab` tool with a modern, object-service compliant architecture.

## Purpose

`tnh-gen` provides:

- **Prompt Discovery**: Browse and search available prompts with rich metadata
- **Text Processing**: Execute AI-powered transformations (translation, sectioning, summarization, etc.)
- **Configuration Management**: Hierarchical configuration with clear precedence rules
- **VS Code Integration**: Stable CLI contract for editor extension consumption
- **Batch Operations**: Process multiple files with consistent provenance tracking

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                        tnh-gen CLI                          │
│  (Typer-based, JSON output, stable interface)               │
└────────────────┬────────────────────────┬───────────────────┘
                 │                        │
         ┌───────▼───────┐          ┌──────▼────────┐
         │ Prompt System │          │ AI Text       │
         │ (ADR-PT04)    │          │ Processing    │
         │               │          │ (ADR-AT03)    │
         └───────┬───────┘          └───────┬───────┘
                 │                          │
                 └──────────┬───────────────┘
                            │
                   ┌────────▼──────────┐
                   │  GenAI Service    │
                   │  (ADR-A13)        │
                   └───────────────────┘
```

## ADR Series

### Core ADRs

- **[ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)** - Command structure, error handling, configuration
- **[ADR-TG02: Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)** - CLI ↔ prompt system integration

### Related ADRs

- **[ADR-AT03: AI Text Processing Refactor](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)** - 3-tier refactor (object-service, GenAI, prompts)
- **[ADR-PT04: Prompt System Refactor](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)** - New prompt system architecture
- **[ADR-VSC02: VS Code Extension](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md)** - VS Code integration strategy

## Migration from tnh-fab

The `tnh-gen` CLI supersedes the legacy `tnh-fab` tool:

| Aspect | tnh-fab (Legacy) | tnh-gen (Current) |
|--------|------------------|-------------------|
| Architecture | Monolithic, mixed concerns | Object-service compliant |
| Prompt System | Legacy `ai_text_processing.prompts` | New `prompt_system` (ADR-PT04) |
| GenAI Integration | Direct OpenAI calls | GenAIService (ADR-A13) |
| Configuration | Ad-hoc, `TNH_PATTERN_DIR` | Hierarchical, `TNH_PROMPT_DIR` |
| VS Code Support | None | First-class citizen |

## Status

- **Current Phase**: ADR drafting
- **Implementation**: Blocked pending ADR-AT03 (ai_text_processing refactor)
- **Active CLI**: `tnh-fab` (legacy, to be deprecated)

## Command Overview

```bash
# List available prompts with metadata
tnh-gen list [--tag TAG] [--search QUERY]

# Execute a prompt with variables
tnh-gen run --prompt KEY --input-file PATH [--var KEY=VALUE]

# Manage configuration
tnh-gen config show|get|set [KEY] [VALUE]

# Show version information
tnh-gen version
```

See ADR-TG01 for complete command specification.

## Key Design Principles

1. **Stable Interface**: CLI contract remains stable for VS Code and scripting consumption
2. **Structured Output**: JSON-formatted responses for programmatic parsing
3. **Clear Errors**: Descriptive error messages with actionable suggestions
4. **Provenance First**: All outputs include generation metadata and fingerprints
5. **Configuration Precedence**: CLI flags > workspace > user > environment > defaults

## References

### Documentation

- User Guide: tnh-gen CLI (planned)
- [Getting Started: Quick Start Guide](/getting-started/quick-start-guide.md)

### Related Architecture

- [Prompt System Overview](/architecture/prompt-system/prompt-system-architecture.md)
- [GenAI Service Strategy](/architecture/gen-ai-service/index.md)
- [Object-Service Architecture](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)

---

## Historical References

<details>
<summary>📚 View superseded design documents (maintainers/contributors)</summary>

**Note**: These documents are archived and excluded from the published documentation. They provide historical context for the current design.

### Legacy tnh-fab Design Documents

Legacy `tnh-fab` design documents are archived for historical reference. These documents informed the `tnh-gen` design but are superseded by the ADR-TG series.

- **[tnh-fab CLI Specification](/architecture/tnh-gen/design/archive/tnh-fab-cli-spec.md)** (2024)
  *Status*: Superseded by [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)
- **[tnh-fab Design Document](/architecture/tnh-gen/design/archive/tnh-fab-design-document.md)** (2024)
  *Status*: Superseded by ADR-TG series

</details>

---

*Last Updated: 2025-12-11*
