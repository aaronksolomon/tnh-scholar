# Archive Directory

This directory contains deprecated and historical documentation files preserved for maintainer and developer reference. These files are **excluded from the documentation build** and not intended for end users or researchers.

## Purpose

Archive directories throughout the docs tree store:

- **Deprecated documentation** – superseded by newer versions
- **Historical design documents** – early explorations that informed current architecture
- **Legacy ADRs** – replaced or consolidated Architecture Decision Records
- **Obsolete research artifacts** – experimental work with historical value

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

Archive files when:

1. Content replaced by newer documentation
2. Design decisions superseded by new ADRs
3. Research no longer relevant but has historical value
4. Reference needed but shouldn't appear in active docs

## Best Practices

- **Add context** – note why the file was archived
- **Update references** – remove links from active documentation
- **Preserve metadata** – keep original frontmatter and dates
- **Consider deletion** – delete files with no historical value

Archive directories can exist anywhere in the `docs/` tree, keeping deprecated content close to related active documentation.
