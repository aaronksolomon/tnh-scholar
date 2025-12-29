---
title: "Development Documentation"
description: "Landing page for contributor guides, design principles, and engineering practices for TNH Scholar."
owner: ""
author: ""
status: current
created: "2025-12-03"
---
# Development Documentation

This directory contains documentation for developers contributing to TNH Scholar.

## Contents

- **[contributing-prototype-phase.md](/development/contributing-prototype-phase.md)** - Contributing guidelines for the prototype phase
- **[design-principles.md](/development/design-principles.md)** - Core design principles and patterns
- **[fine-tuning-strategy.md](/development/fine-tuning-strategy.md)** - Strategy for fine-tuning AI models
- **[git-workflow.md](/development/git-workflow.md)** - Safe git practices and workflow guidelines
- **[human-ai-software-engineering-principles.md](/development/human-ai-software-engineering-principles.md)** - Principles for human-AI collaborative development
- **[improvements-initial-structure.md](/development/improvements-initial-structure.md)** - Initial structural improvements and refactoring notes
- **[style-guide.md](/development/style-guide.md)** - Code style guide and conventions
- **[system-design.md](/development/system-design.md)** - Overall system design and architecture

## Important: Rapid Prototype Phase (0.x)

**TNH Scholar is in rapid prototype phase.** Breaking changes may occur in ANY 0.x release (including patches). See [ADR-PP01: Rapid Prototype Versioning](/architecture/project-policies/adr/adr-pp01-rapid-prototype-versioning.md) for full policy.

**Key Implications for Contributors:**

- No backward compatibility guarantees during 0.x
- Breaking changes acceptable in patch releases (0.1.3 → 0.1.4)
- When refactoring core systems, update ALL dependents in same PR
- No compatibility shims or legacy code maintenance
- Clean breaks over gradual migrations

## Getting Started as a Contributor

1. **Set up your development environment** - See [`DEV_SETUP.md`](/project/repo-root/dev-setup-guide.md) for Python, Poetry, and dependency installation
2. Read [contributing-prototype-phase.md](/development/contributing-prototype-phase.md) for contribution guidelines
3. **Understand versioning policy** - Review [ADR-PP01](/architecture/project-policies/adr/adr-pp01-rapid-prototype-versioning.md) for breaking change expectations
4. Review [design-principles.md](/development/design-principles.md) to understand our approach
5. Follow the [style-guide.md](/development/style-guide.md) for code consistency

## Development Philosophy

TNH Scholar embraces human-AI collaborative development. See [human-ai-software-engineering-principles.md](/development/human-ai-software-engineering-principles.md) for our approach to working with AI assistants.

## Related Documentation

- [Project Vision & Philosophy](/project/vision.md) - Project goals and philosophy
- [Architecture](/architecture/overview.md) - Technical architecture documentation
- [Docs Operations](/docs-ops/markdown-standards.md) - Documentation standards and templates
