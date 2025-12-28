---
title: "Archive Directory"
description: "Archived CLI reference documentation preserved for maintainer reference and excluded from the published site."
owner: "Documentation Working Group"
author: ""
status: archived
created: "2025-12-28"
---
# Archive Directory

This directory contains deprecated CLI reference documentation preserved for maintainer and developer reference. These files are **excluded from the documentation build** and not intended for end users.

## Purpose

This archive directory stores:

- **Deprecated CLI tools** – Documentation for tools superseded by newer versions
- **Legacy command references** – Historical documentation for migrated commands
- **Historical user guides** – Early documentation that informed current guides

## Not in Documentation Build

All `archive/` directories are excluded from the MkDocs build:

```yaml
exclude_docs: |
  **/archive/**
```

Archived files will **not** appear in:

- Published documentation site
- Navigation menus
- Search results
- Documentation index

## When to Archive

Archive CLI reference files when:

1. Tool replaced by newer version (e.g., tnh-fab → tnh-gen)
2. Commands deprecated and removed from active toolset
3. Documentation superseded by comprehensive rewrites
4. Reference needed for migration but shouldn't appear in active docs

## Archived Files

### tnh-fab.md

Legacy CLI tool documentation. Superseded by:
- [tnh-gen CLI Reference](/cli-reference/tnh-gen.md)
- [TNH-Gen Architecture](/architecture/tnh-gen/index.md)

**Archived**: 2025-12-28
**Reason**: Tool deprecated in v0.2.2, replaced by tnh-gen
**Migration Guide**: See [TNH-Gen Architecture](/architecture/tnh-gen/index.md)

## Best Practices

- **Add archive notice** – Update frontmatter with `status: archived`
- **Note replacement** – Link to superseding documentation
- **Preserve metadata** – Keep original frontmatter and dates
- **Reference in migration docs** – Link from active docs when relevant

Archive directories can exist anywhere in the `docs/` tree, keeping deprecated content close to related active documentation.
