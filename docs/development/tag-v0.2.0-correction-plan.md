# v0.2.0 Tag Correction Plan

## Context

During recovery from the December 7-8, 2025 incident where branches were deleted
and work was orphaned, we discovered that the v0.2.0 tag points to commit 0d7d459
which does NOT include the prompt system implementation work.

The v0.2.0 tag was created during release prep BEFORE the actual work was merged.
The intended v0.2.0 release should include:

- Prompt system implementation (ADR-PT04) 
- Metadata infrastructure documentation (ADR-MD02)
- All work from PRs #11 and #12 (recovered in PR #13)

## Corrective Action

After PR #13 merges to main, we will:

1. Delete the incorrect v0.2.0 tag locally and remotely
2. Create new v0.2.0 tag at the correct commit (main after PR #13 merge)
3. Document this correction in the tag annotation

## Commands

```bash
# 1. Merge PR #13 (via GitHub UI or gh CLI)
gh pr merge 13 --merge

# 2. Update local main
git checkout main
git pull

# 3. Delete old v0.2.0 tag
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0

# 4. Create corrected v0.2.0 tag with documentation
git tag -a v0.2.0 -m "Release v0.2.0 (Corrected)

Release v0.2.0 with prompt system implementation and metadata infrastructure.

## Includes

- Prompt system package (ADR-PT04) - 22 source files, 6 test files
- Metadata infrastructure documentation (ADR-MD02)
- Project versioning policy (ADR-PP01)
- Git safety documentation and tooling
- All work from PRs #11, #12, #13

## Tag Correction Note

This tag was corrected on 2025-12-07 after recovery from branch deletion incident.

Original v0.2.0 tag (0d7d459) created during release prep but did not include
the prompt system work. This corrected tag points to the actual v0.2.0 release
including all intended features.

See docs/development/git-workflow.md for incident details and recovery process.

## References

- PR #13: Recovery of prompt system implementation
- ADR-PT04: Prompt System Refactor
- ADR-MD02: Metadata Infrastructure Integration
- Recovered from commit c6532f5 (orphaned 2025-12-07)

🤖 Generated with Claude Code
"

# 5. Push corrected tag
git push origin v0.2.0

# 6. Verify
git show v0.2.0 --stat | head -n 20
```

## Verification

After tag correction:
- v0.2.0 should point to main after PR #13 merge
- Tag annotation should document the correction
- `git ls-tree -r v0.2.0 --name-only | grep prompt_system` should find files

## Documentation

This correction is documented in:
- This file: /tmp/tag-correction-plan.md
- Git workflow guide: docs/development/git-workflow.md
- Tag annotation message (see above)
- CHANGELOG.md (should be updated with v0.2.0 actual contents)
