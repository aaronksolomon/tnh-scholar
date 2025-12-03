# Architecture Documentation

This directory contains technical architecture documentation, design documents, and Architecture Decision Records (ADRs) for TNH Scholar.

## Organization

Architecture documentation is organized by subsystem/domain:

- **[ai-text-processing/](ai-text-processing/)** - Text object system and AI text processing
- **[configuration/](configuration/)** - Configuration management system
- **[docs-system/](docs-system/)** - Documentation system architecture
- **[gen-ai-service/](gen-ai-service/)** - GenAI service architecture and interfaces
- **[jvb-viewer/](jvb-viewer/)** - JVB (Jataka Vietnamese Bilingual) viewer
- **[knowledge-base/](knowledge-base/)** - Knowledge base architecture
- **[metadata/](metadata/)** - Metadata systems and JSON-LD
- **[object-service/](object-service/)** - Core object service architecture
- **[prompt-system/](prompt-system/)** - Prompt system and pattern catalog
- **[setup-tnh/](setup-tnh/)** - Setup tool architecture
- **[tnh-fab/](tnh-fab/)** - TNH Fabrication tool design
- **[transcription/](transcription/)** - Audio transcription and diarization
- **[ui-ux/](ui-ux/)** - User interface and experience design
- **[utilities/](utilities/)** - Utility functions and tools
- **[video-processing/](video-processing/)** - Video processing pipeline
- **[ytt-fetch/](ytt-fetch/)** - YouTube transcript fetching

## Document Types

Each subsystem directory may contain:

- **adr/** - Architecture Decision Records documenting key decisions
- **design/** - Design documents with detailed specifications
- **archive/** - Historical documents and superseded designs

## Reading Architecture Docs

1. Start with **overview.md** (if present) for high-level concepts
2. Check **adr/** for decision rationale and context
3. Review **design/** for detailed implementation specifications

## Contributing

When adding architecture documentation:
- Place in appropriate subsystem directory
- Use ADR template from [../docs-ops/adr-template.md](../docs-ops/adr-template.md)
- Follow naming conventions: `adr-XX##-description.md` for ADRs
