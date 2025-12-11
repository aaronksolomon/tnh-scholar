---
title: "ADR-PT03: Prompt System Current Status & Roadmap"
description: "Current as-built status of the TNH Scholar prompt system, documentation terminology standardization, and planned enhancements."
owner: ""
author: "Claude Sonnet 4.5"
status: proposed
created: "2025-11-29"
---
# ADR-PT03: Prompt System Current Status & Roadmap

Documents the current state of the TNH Scholar prompt system, recent documentation standardization work, and planned enhancements for VS Code integration and gen-ai-service upgrades.

- **Filename**: `adr-pt03-current-status-roadmap.md`
- **Heading**: `# ADR-PT03: Prompt System Current Status & Roadmap`
- **Status**: Proposed
- **Date**: 2025-11-29
- **Author**: Claude Sonnet 4.5
- **Owner**: TNH Scholar Architecture Working Group

## Purpose

This ADR provides a current snapshot of the prompt system architecture, terminology standardization efforts, and planned work. It serves as the primary entry point for understanding the prompt system's current state and future direction.

## Current System Status

### Implementation Overview

The TNH Scholar prompt system currently uses:

- **Git-based Storage**: Prompts stored as versioned text files in `~/.config/tnh_scholar/patterns/` (directory name retained for backwards compatibility)
- **Jinja2 Templates**: Prompts are Jinja2 templates rendered with context variables before AI processing
- **LocalPatternManager**: Singleton pattern manager providing global access to prompts (prototype phase; see historical notes in Core Pattern Architecture in Historical References)
- **CLI Integration**: Command-line tools (`tnh-fab`) use prompts via `--pattern` flag

### Key Components

1. **Pattern/Prompt Files**: Git-versioned Jinja2 templates
2. **PatternManager**: Manages prompt discovery, loading, and rendering
3. **LocalPatternManager**: Singleton wrapper for global access (prototype architecture)
4. **Prompt Templates**: Core prompts include sectioning, translation, punctuation, and custom processing

### Code Status

- **Core Implementation**: `src/tnh_scholar/ai_text_processing/` (uses legacy "pattern" terminology)
- **CLI Tools**: `src/tnh_scholar/cli_tools/tnh_fab/` (uses `--pattern` flag)
- **Configuration**: `TNH_PATTERN_DIR` environment variable (legacy naming)

**Note**: Code refactoring to use "Prompt" terminology is tracked separately. Many legacy modules are scheduled for deprecation/deletion as part of the gen-ai-service refactor and tnh-gen CLI redesign.

## Recent Work: Documentation Terminology Standardization

### ADR-DD03: Pattern→Prompt Terminology Shift

**Completed**: 2025-11-28 to 2025-11-29

All user-facing documentation has been updated to use "Prompt" instead of "Pattern" to align with:
- Industry standard terminology (Prompt Engineering, Prompt Catalog)
- Refactored gen-ai-service architecture (Prompt/PromptCatalog classes)
- External stakeholder expectations (Parallax Press, new users)

**Scope**: Documentation only (code refactoring tracked separately)

**Key Changes**:
- Updated docs/index.md, README.md, getting-started/, user-guide/
- Renamed `docs/user-guide/patterns.md` → `prompts.md`
- Renamed `docs/architecture/pattern-system/` → `prompt-system/`
- Added historical terminology note to docs/index.md explaining Pattern→Prompt shift
- Retained legacy naming for backwards compatibility: `TNH_PATTERN_DIR`, `--pattern` CLI flags

**Reference**: [ADR-DD03: Pattern to Prompt Terminology Standardization](/architecture/docs-system/adr/adr-dd03-pattern-to-prompt.md)

### Historical Context

Earlier architectural explorations (now archived) document the evolution from prototype singleton architecture toward production dependency-injection patterns (see Historical References).

## Planned Work & Roadmap

### 1. VS Code Integration Requirements

**Upcoming**: ADR-VSC02 (tnh-gen CLI implementation) will require prompt system enhancements:

- **Interactive Prompt Selection**: VS Code command palette integration for browsing/selecting prompts
- **Prompt Preview**: Real-time rendering of prompts with context variables
- **Custom Prompt Authoring**: In-editor prompt creation and testing workflow
- **Prompt Versioning UI**: Git integration for prompt history and diffs

**Dependencies**:
- Enhanced PromptCatalog with metadata queries
- Prompt validation and preview rendering
- Structured prompt metadata (task type, model constraints, variables)

**Status**: Requirements gathering phase; detailed ADR pending

**Reference**: [ADR-VSC01: VS Code Integration Strategy](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)

### 2. Gen-AI-Service Refactor Integration

**Planned**: Transition to modern Prompt/PromptCatalog architecture:

- Replace LocalPatternManager singleton with dependency-injected PromptCatalog
- Implement PromptFingerprint for reproducibility and caching
- Add structured prompt metadata (task type, model constraints, safety requirements)
- Support deterministic rendering and caching keyed by fingerprint
- Enable usage analytics (cost/latency tracking)

**Status**: Design phase; awaiting gen-ai-service ADRs

**Historical Reference**: Core Pattern Architecture outlined early dependency-injection transition ideas (see Historical References)

### 3. tnh-gen CLI Redesign

**Planned**: Refactor tnh-fab → tnh-gen with prompt-first architecture:

- Unified `tnh-gen` command with prompt-based subcommands
- Improved prompt discovery and selection UX
- Interactive prompt authoring workflow
- Better integration with VS Code extension

**Status**: Requirements phase; ADR pending

## Design Principles

Current prompt system design emphasizes:

1. **Simplicity**: Git-based storage, minimal abstractions
2. **Transparency**: Human-readable Jinja2 templates
3. **Versioning**: Git lineage for collaborative editing and reproducibility
4. **Flexibility**: Template-based customization with context variables

Future enhancements will preserve these principles while adding:
- Structured metadata for discoverability
- Reproducibility via fingerprinting
- Better tooling integration (VS Code, CLI)

## Migration Path

**Phase 1 (Completed)**: Documentation terminology standardization
- ✅ User-facing docs use "Prompt" terminology
- ✅ Historical note added to docs/index.md
- ✅ Legacy config/CLI naming documented

**Phase 2 (Upcoming)**: VS Code integration foundation
- Enhance PromptCatalog with metadata queries
- Implement prompt preview/rendering
- Add structured prompt metadata

**Phase 3 (Future)**: Production architecture transition
- Replace singleton with dependency injection (per ADR-PT01)
- Implement PromptFingerprint
- Add usage analytics and caching

**Phase 4 (Future)**: Code terminology updates
- Refactor code to use "Prompt" terminology
- Update CLI flags (with backwards compatibility)
- Deprecate legacy modules

## References

### Current Documentation
- [Prompt System User Guide](/user-guide/prompt-system.md)
- [Prompt System Overview](/getting-started/quick-start-guide.md)
- [Configuration Guide](/getting-started/configuration.md)

### Related ADRs
- [ADR-DD03: Pattern to Prompt Terminology Standardization](/architecture/docs-system/adr/adr-dd03-pattern-to-prompt.md) - Documentation terminology shift
- [ADR-VSC01: VS Code Integration Strategy](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md) - VS Code extension requirements

### Development Documentation
- Core Pattern Architecture (see Historical References) - Detailed architectural concepts using legacy "Pattern" terminology
- [System Design](/development/system-design.md) - High-level system architecture

## Historical References

<details>
<summary>📚 View superseded design documents (maintainers/contributors)</summary>

**Note**: This document is archived and excluded from the published documentation. It captures legacy terminology and architecture explorations.

- **[Core Pattern Architecture](/architecture/prompt-system/archive/core-pattern-architecture.md)** (2024)
  *Status*: Historical prompt/pattern architecture exploration superseded by ADR-PT03/ADR-PT04

</details>

## Status

**Current Phase**: Documentation standardization complete; VS Code integration requirements gathering

**Next Steps**:
1. Draft ADR-VSC02 (tnh-gen CLI implementation) with prompt system requirements
2. Begin gen-ai-service refactor ADRs with PromptCatalog design
3. Update development documentation with terminology notes (see ADR-DD03 Phase 2)
