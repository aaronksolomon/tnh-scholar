# Next Session Prompt: Documentation Reorganization Parts 3b–4d

## Context
You are continuing **TODO #9: Documentation Reorganization (ADR-DD01)** on the `docs-reorg` branch.

**What's complete** (as of commit ddfa441):
- ✅ Part 1: Inventory + Tagging (all Markdown catalogued with metadata)
- ✅ Part 2: Filesystem Reorg (target structure created, docs moved)
- ✅ Part 4b: Doc Generation Scripts (CLI docs, doc index, README sync tools + Makefile `docs` targets)

**What's next** (in this sequence order):

### 1. Part 3b: README + Docs Index Expansion (45 min)
Expand `README.md` and `docs/index.md` with comprehensive sections:
- Vision, quick start, installation, overview + navigation map, contributing, development, research, license
- Ensure major sections align between both files
- Run `sync_readme.py` to verify
- **File**: `README.md`, `docs/index.md`
- **Reference**: See NEXT_SESSION.md for detailed tasks

### 2. Part 4c: Add CI for Docs Builds (15 min)
Create GitHub Actions workflow to run `make docs-build` on every PR/push to docs-reorg.
- Add `.github/workflows/docs.yml` or extend existing `ci.yml`
- Fail on `mkdocs build` errors
- **File**: `.github/workflows/docs.yml` (or ci.yml)

### 3. Part 4d: Normalize Internal Links (20 min)
Fix broken-link warnings from MkDocs:
- Run `make docs-build` and capture warnings
- Fix relative paths, ADR cross-links, README refs (likely ~20 files)
- Re-test until `make docs-build` has no warnings
- **Files**: Various in `docs/` tree

## Key Constraints
- **Do NOT touch `patterns/` directory** – it's managed separately under TODO #16
- **Commit strategy**: Separate commits for 3b, 4c, and 4d (not combined)
- **Only modify `docs/` tree** (and `.github/workflows/`, Makefile, scripts/ if needed)

## Files to Read First
1. **NEXT_SESSION.md** (in repo root) – detailed task breakdown
2. **TODO.md** (lines 133–171) – full TODO #9 checkpoint
3. **ADR-DD01** (`docs/architecture/docs-design/adr/adr-dd01-docs-reorg-strat.md`) – master plan

## Testing Commands
```bash
# Verify doc generation works
make docs-generate

# Build site and check for broken links
make docs-build

# Validate README ↔ docs/index sync
make docs-verify
```

## Success Criteria
- README.md and docs/index.md are comprehensive and aligned
- `make docs-build` completes without warnings
- CI workflow is in place (or PR to add it created)
- 3 separate commits: Part 3b, Part 4c, Part 4d
- TODO.md updated to mark 3b, 4c, 4d ✅

## If Blocked
- Check NEXT_SESSION.md for detailed context
- Refer to ADR-DD01 for decision rationale
- Git log shows recent commits: 35b892e (Part 4b), 9676485 (TODO update), b04ed90 (TODO clarified), ddfa441 (NEXT_SESSION.md)
