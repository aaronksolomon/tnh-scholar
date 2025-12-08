---
title: "Project Policies"
description: "Cross-cutting architectural policies and decisions affecting the entire TNH Scholar codebase"
owner: "TNH Scholar Architecture Working Group"
author: ""
status: active
created: "2025-12-06"
---
# Project Policies

Cross-cutting architectural policies and decisions affecting the entire TNH Scholar codebase.

## Overview

This directory contains Architecture Decision Records (ADRs) and policy documents for project-wide concerns that span multiple subsystems. Unlike feature-specific ADRs (GenAI, prompt system, etc.), these policies establish patterns and principles that apply across the entire codebase.

## Scope

**Project Policies cover:**
- Versioning and release strategies
- Testing and quality standards (future)
- CI/CD architecture (future)
- Cross-cutting design patterns (future)
- Repository organization (future)

**Not covered here:**
- Feature-specific architecture (see [architecture/](/architecture/index.md) subdirectories)
- Code style (see [development/style-guide.md](/development/style-guide.md))
- Documentation standards (see [docs-system/](/architecture/docs-system/index.md))

## Current Policies

### Versioning & Releases

- **[ADR-PP01: Rapid Prototype Versioning Policy](adr/adr-pp01-rapid-prototype-versioning.md)** - Establishes versioning policy for 0.x releases, allowing breaking changes in any release to enable fast iteration
- **[Implementation Summary](versioning-policy-implementation-summary.md)** - Documentation updates implementing ADR-PP01

**Status**: Active (0.x phase)
**Key Principle**: Breaking changes acceptable in ANY 0.x release to prioritize architectural consistency

See [VERSIONING.md](/project/repo-root/versioning.md) for user-facing policy documentation.

## Future Policies (Planned)

### Testing Strategy (Planned)

- Project-wide testing standards
- Coverage requirements
- Test infrastructure patterns
- Integration test strategies

### CI/CD Architecture (Planned)

- Build pipeline design
- Release automation
- Deployment strategies
- Quality gates

### Monorepo vs Multi-repo (Planned)

- Repository organization strategy
- Package boundaries
- Versioning across packages

## Related Documentation

- [VERSIONING.md](/project/repo-root/versioning.md) - User-facing versioning policy
- [CONTRIBUTING.md](/project/repo-root/contributing-root.md) - Contribution guidelines
- [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md) - Object-service architecture (cross-cutting pattern)
- [Architecture Overview](/architecture/overview.md) - High-level architecture

## Contributing

Project policies are decided by the Architecture Working Group with input from maintainers and contributors. To propose a new policy:

1. Open a GitHub issue with `[Policy Proposal]` prefix
2. Discuss approach with maintainers
3. Draft ADR using [ADR template](/docs-ops/adr-template.md)
4. Submit PR for review

---

**Last Updated**: 2025-12-06
**Active Policies**: 1 (ADR-PP01)
**Status**: Rapid Prototype Phase (0.x)
