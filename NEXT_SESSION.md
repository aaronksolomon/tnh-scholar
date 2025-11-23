# Next Session: Documentation Reorganization Part 3b → 4c → 4d

**Date**: 2025-11-22  
**Branch**: `docs-reorg`  
**Epic**: TODO #9 – Documentation Reorganization (ADR-DD01)  
**Status**: Parts 1–2 and 4b ✅ complete. Parts 3b/4c/4d ready to start.

---

## Summary: What's Done

### Part 1: Inventory + Tagging ✅
- Catalogued all Markdown files with metadata (owner, status, created date)
- Added YAML front matter standardization
- Generated `documentation_index.md` (auto-generated from metadata)

### Part 2: Filesystem Reorg ✅
- Created target directory structure: `overview/`, `getting-started/`, `user-guide/`, `cli-reference/`, `prompt-templates/`, `api-reference/`, `architecture/adr/`, `development/`, `research/`, `docs-ops/`, `archive/`
- Moved docs into new layout with stub `index.md` files
- Restructured `mkdocs.yaml` to filesystem-driven navigation + adopted `mkdocs-literate-nav`

### Part 4b: Doc Generation Scripts ✅
- Created `scripts/generate_cli_docs.py` – generates CLI reference stubs in `docs/cli-reference/`
- Created `scripts/sync_readme.py` – validates README ↔ docs/index.md sync
- Updated `scripts/generate_doc_index.py` to use glob instead of ripgrep (no external dependencies)
- Added Makefile targets: `make docs-generate`, `make docs-build`, `make docs-verify`, `make docs`
- Generated 9 CLI reference stubs (all CLI tools covered)
- **Commits**: 35b892e, 9676485

---

## Next: Immediate Sequence (3b → 4c → 4d)

### Part 3b: README + Docs Index Expansion (NEXT - ~45 min)
**Goal**: Make README and docs/index.md comprehensive, aligned, persona-routed.

**Current state**:
- README.md is minimal (legacy)
- docs/index.md has basic structure but lacks overview + context map
- `sync_readme.py` currently reports divergences (expected)

**Tasks**:
1. Expand README.md sections:
   - Introduction (vision, goals, core benefits)
   - Quick Start (install, first use)
   - Documentation Overview (with navigation map showing all sections)
   - Features (high-level)
   - Development (link to dev setup)
   - Contributing
   - Research
   - License
   
2. Align docs/index.md to match README outline but with deeper intro prose + section links

3. Run `poetry run python scripts/sync_readme.py` to verify alignment

4. **Commit**: "Part 3b: Expand README + docs/index with comprehensive overview and navigation map"

---

### Part 4c: Wire CI for Documentation (NEXT AFTER 3b - ~15 min)
**Goal**: Add GitHub Actions workflow to build and verify docs automatically.

**Tasks**:
1. Create `.github/workflows/docs.yml` (or add to existing ci.yml):
   - Run `make docs-build` on PRs/pushes to docs-reorg branch
   - Fail if `mkdocs build` errors
   - Optionally check broken links (optional: use `linkchecker` or skip for now)

2. Update `.github/workflows/ci.yml` to include `docs-verify` check

3. **Commit**: "Part 4c: Add CI workflow for documentation builds"

---

### Part 4d: Normalize Internal Documentation Links (~20 min)
**Goal**: Fix broken-link warnings from MkDocs build.

**Current issues** (from mkdocs.yaml):
- Absolute paths in cross-references (e.g., `docs/getting-started/quick-start.md` should be relative)
- ADR cross-links (e.g., linking to legacy `docs/design/` paths before they're archived)
- README/docs/index relative path inconsistencies

**Tasks**:
1. Run `poetry run mkdocs build` and capture any broken-link warnings
2. Scan `docs/` for common patterns:
   - `[link](docs/...)` → `[link](../...)`
   - `[link](documentation_index.md)` → fix relative path per location
   - ADR cross-references to moved files

3. Fix in batch (likely ~20 files)

4. **Commit**: "Part 4d: Normalize internal documentation links for MkDocs navigation"

---

## Key Context

### Important: Scope Boundary
**`patterns/` directory is OUT OF SCOPE** for this work. It contains PromptTemplate definitions (not documentation), and is managed separately under TODO #16 (Configuration & Data Layout). The earlier confusion was clarified in commits and ADR-DD01 scope section.

### Running Docs Commands
```bash
# Generate doc index + CLI stubs
make docs-generate

# Build full MkDocs site (includes generation)
make docs-build

# Build + verify README/docs sync
make docs-verify

# Full docs pipeline (all of above)
make docs
```

### Files to Watch
- `TODO.md` – line 151–158 for Part 4 status
- `docs/architecture/docs-design/adr/adr-dd01-docs-reorg-strat.md` – master plan
- `Makefile` – docs targets (lines 30–46)
- `scripts/generate_cli_docs.py`, `scripts/sync_readme.py`, `scripts/generate_doc_index.py` – automation tools

### GitHub Commits This Session
```
35b892e Part 4b: Add doc-generation scripts and Makefile docs targets
9676485 Update TODO: Mark Part 4b docs scripts complete, prep Part 4c
b04ed90 Clarify TODO #9 status and next sequence (Part 3b → 4c → 4d)
```

---

## After 4d: Parts 5+

Once the immediate sequence (3b/4c/4d) is done:
- **Part 5**: Historical Archive + Discoverability (move legacy ADRs to `docs/archive/`, create index)
- **Part 6**: Gap Filling + Backlog (populate `docs/docs-ops/roadmap.md`, open GitHub issues)
- **Part 7**: Outstanding Tasks (deprecate CLI examples, add user guides, architecture overview, Pattern→PromptTemplate rename across docs)

See TODO.md lines 159–171 for details.

---

## Quick Checklist for Next Session
- [ ] Expand README.md with full structure (intro, quick start, overview, contributing, etc.)
- [ ] Sync docs/index.md to match README sections
- [ ] Run `make docs-verify` and fix any sync issues
- [ ] Commit Part 3b
- [ ] Add CI workflow for docs building (Part 4c)
- [ ] Run `make docs-build` and collect broken-link warnings
- [ ] Fix internal links in docs/ (Part 4d)
- [ ] Commit Parts 4c + 4d
- [ ] Push branch & prepare for next epic (Part 5+)
