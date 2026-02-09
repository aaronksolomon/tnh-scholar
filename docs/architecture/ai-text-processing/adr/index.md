---
title: "Adr"
description: "Table of contents for architecture/ai-text-processing/adr"
owner: ""
author: ""
status: processing
created: "2026-02-09"
auto_generated: true
---

# Adr

**Table of Contents**:

<!-- To manually edit this file, update the front matter and keep `auto_generated: true` to allow regeneration. -->

**[ADR-AT01: AI Text Processing Pipeline Redesign](adr-at01-ai-text-processing.md)** - Defines the modular TextObject pipeline, metadata handling, and configuration strategy for AI processing.

**[ADR-AT02: TextObject Architecture Decision Records](adr-at02-sectioning-textobject.md)** - Captures the historical TextObject design comparisons and links to the original/new design documents.

**[ADR-AT03: Minimal AI Text Processing Refactor for tnh-gen](adr-at03-object-service-refactor.md)** - Focused refactor of ai_text_processing module to support tnh-gen CLI release: TextObject robustness, GenAI Service integration, and basic prompt system adoption

**[ADR-AT03.1: AT03→AT04 Transition Plan](adr-at03.1-transition-plan.md)** - Phased transition strategy: minimal refactor (AT03) for tnh-gen release, followed by comprehensive platform (AT04)

**[ADR-AT03.2: NumberedText Section Boundary Validation](adr-at03.2-numberedtext-validation.md)** - Adds robust validation, coverage reporting, and gap/overlap detection to NumberedText to support reliable sectioning in ai_text_processing

**[ADR-AT03.3: TextObject Robustness and Metadata Management](adr-at03.3-textobject-robustness.md)** - Fixes metadata propagation bugs, enhances section validation, and adds merge strategies to TextObject for reliable ai_text_processing workflows

**[ADR-AT04: AI Text Processing Platform Strategy](adr-at04-ai-text-processing-platform-strat.md)** - Platform architecture for extensible, evaluation-driven text processing with strategy polymorphism and context fidelity

---

*This file auto-generated.*
