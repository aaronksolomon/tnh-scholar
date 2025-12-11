# Documentation Archive Linking Pattern

## Summary

Implement a consistent pattern for linking to archived documentation that preserves developer/maintainer access while keeping the published documentation clean for users and researchers.

## Background

- Archive directories (`**/archive/**`) are excluded from the MkDocs build
- Many active documents reference archived ADRs and design documents
- Developers need access to historical context; users should not be confused by deprecated content
- Current state: Direct links to archived docs cause MkDocs warnings and broken links in published site

## Proposed Solution

Use collapsible "Historical References" sections at the end of relevant documents to provide progressive disclosure of archived content.

### Pattern Template

```markdown
---

## Historical References

<details>
<summary>📚 View superseded design documents (maintainers/contributors)</summary>

**Note**: These documents are archived and excluded from the published documentation. They provide historical context for the current design.

### Superseded ADRs

- **[ADR-XX: Title](../archive/adr/adr-xx-title.md)** (YYYY-MM-DD)
  *Status*: Superseded by [ADR-YY](/path/to/current-adr.md)

### Earlier Design Explorations

- **[Design Doc Title](../archive/design-doc.md)** (YYYY-MM-DD)
  *Status*: Replaced by [Current Doc](/path/to/current-doc.md)

</details>
```

## Tasks

### 1. Documentation

- [ ] Create ADR addendum to ADR-DD01 documenting this pattern
- [ ] Add pattern to style guide (`docs/development/style-guide.md`)
- [ ] Document when to use Historical References sections

### 2. Archive READMEs

- [ ] Copy `docs/archive/README.md` to:
  - [ ] `docs/architecture/prompt-system/archive/README.md`
  - [ ] `docs/architecture/tnh-gen/design/archive/README.md`
  - [ ] Any other archive directories discovered

### 3. Add Historical References Sections

Audit and update documents that currently link to archived content:

- [ ] `docs/index.md` - Remove direct archive links, add Historical References
- [ ] `docs/architecture/prompt-system/prompt-system-architecture.md`
- [ ] Other architecture docs as identified

### 4. Cleanup

- [ ] Regenerate `documentation_index.md` after changes
- [ ] Verify MkDocs build with `--strict` passes
- [ ] Check no broken links to archive content in published site

## Acceptance Criteria

1. ✅ All `archive/` directories have README.md files
2. ✅ No direct links to archived docs in active documentation (except within Historical References sections)
3. ✅ MkDocs build passes with no warnings about excluded archive files
4. ✅ Pattern documented in ADR and style guide
5. ✅ Developers can access archived docs via repository/IDE
6. ✅ Published docs are clean for users

## Notes

- Archive links work in GitHub/IDE even when excluded from published docs
- `<details>` tags render in both MkDocs and GitHub
- Historical References sections are collapsible by default (progressive disclosure)
