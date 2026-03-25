PYTHON_VERSION = 3.12.4
POETRY        = poetry
LYCHEE        = lychee
PIPX          = pipx
PIPX_LOG_DIR  = $(HOME)/.local/pipx/logs
TNH_CLI_TOOLS = audio-transcribe tnh-gen ytt-fetch nfmt token-count tnh-setup tnh-tree sent-split json-srt srt-translate
SANDBOX_PATH ?= ../tnh-scholar-sandbox
SANDBOX_BRANCH ?= feat/agent-orchestration-sandbox
SANDBOX_SOURCE_REPO ?= .
PR_BASE ?= origin/main
PR_CHECK_ARGS ?=

.PHONY: setup setup-dev test lint format kernel docs docs-validate docs-generate docs-build docs-drift docs-verify codespell docs-quickcheck type-check release-check changelog-draft release-patch release-minor release-major release-commit release-tag release-publish release-full docs-links docs-links-apply ci-check pr-check pipx-refresh build-all update sync-sandbox ytdlp-runtime

setup:
	pyenv install -s $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION)
	$(POETRY) env use python
	$(POETRY) install

setup-dev:
	pyenv install -s $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION)
	$(POETRY) env use python
	$(POETRY) install
	$(POETRY) run python -m ipykernel install --user --name tnh-scholar --display-name "Python (tnh-scholar)"

ytdlp-runtime:
	$(POETRY) run python scripts/setup_ytdlp_runtime.py --yes

build-all:
	$(POETRY) self update
	$(POETRY) update yt-dlp
	$(POETRY) install
	$(MAKE) ytdlp-runtime
	$(MAKE) pipx-refresh
	$(MAKE) docs-build

update:
	$(POETRY) self update
	$(POETRY) update
	$(POETRY) install
	$(POETRY) build
	$(MAKE) pipx-build

sync-sandbox:
	./scripts/sync-sandbox.sh --sandbox $(SANDBOX_PATH) --source-repo $(SANDBOX_SOURCE_REPO)

pipx-build:
	@echo "Building pipx install for tnh-scholar (all CLI tools)..."
	PIPX_LOG_DIR=$(PIPX_LOG_DIR) $(PIPX) install --force --editable .
	@printf "CLI tools available via pipx:\n"
	@printf "  - %s\n" $(TNH_CLI_TOOLS)

pipx-refresh: pipx-build

test:
	$(POETRY) run pytest

lint:
	$(POETRY) run ruff check .

format:
	$(POETRY) run ruff format .

kernel:
	$(POETRY) run python -m ipykernel install --user --name tnh-scholar --display-name "Python (tnh-scholar)"

# Documentation targets
docs-validate:
	@echo "Validating markdown documentation"
	$(POETRY) run python scripts/validate_markdown.py || echo "⚠️  Validation warnings found (non-fatal)"

docs-generate: docs-validate
	@echo "Generating documentation artifacts..."
	$(POETRY) run python scripts/sync_root_docs.py
	$(POETRY) run python scripts/generate_index_md.py
	$(POETRY) run python scripts/generate_subdir_indexes.py
	$(POETRY) run python scripts/generate_doc_index.py
	$(POETRY) run python scripts/update_index_doc_map.py

docs-links:
	@echo "Auto-fixing unambiguous documentation links..."
	$(POETRY) run python scripts/verify_doc_links.py --apply

docs-links-apply:
	@echo "Auto-fixing unambiguous documentation links..."
	$(POETRY) run python scripts/verify_doc_links.py --apply

docs-build: docs-generate docs-links
	@echo "Building MkDocs site..."
	$(POETRY) run mkdocs build --strict

docs-drift:
	@echo "Checking README ↔ docs/index.md drift..."
	$(POETRY) run python scripts/check_readme_docs_drift.py

link-check:
	@echo "Running external link check..."
	$(POETRY) run md-dead-link-check

codespell:
	@echo "Running codespell..."
	$(POETRY) run codespell -q 3 -I .codespell-ignore.txt --skip="*.txt" README.md docs

docs-verify: docs-drift docs-build codespell
	@echo "Verifying documentation..."
	$(POETRY) run python scripts/sync_readme.py

docs: docs-verify
	@echo "Documentation build complete: site/"

docs-quickcheck: docs-generate
	@echo "Running docs quickcheck (strict build, links, spelling)..."
	$(MAKE) docs-links
	$(POETRY) run mkdocs build --strict
	$(MAKE) codespell

# Type checking
type-check:
	@echo "Running type checks..."
	$(POETRY) run mypy src/

# CI check - run all CI checks locally
ci-check:
	@echo "========================================="
	@echo "Running CI checks locally..."
	@echo "========================================="
	@echo ""
	@echo "📁 [1/6] Verifying directory trees..."
	@$(POETRY) run python scripts/generate_tree.py
	@if ! git diff --quiet -- project_directory_tree.txt src_directory_tree.txt; then \
		echo "⚠️  Directory tree drift detected:"; \
		git diff --stat -- project_directory_tree.txt src_directory_tree.txt; \
	else \
		echo "✅ Directory trees are up to date"; \
	fi
	@echo ""
	@echo "🔍 [2/6] Running ruff lint..."
	@$(POETRY) run ruff check . && echo "✅ Ruff lint passed" || echo "⚠️  Ruff lint found issues (non-blocking)"
	@echo ""
	@echo "✨ [3/6] Checking ruff format..."
	@$(POETRY) run ruff format --check . && echo "✅ Ruff format passed" || echo "⚠️  Ruff format check found issues (non-blocking)"
	@echo ""
	@echo "🔎 [4/6] Running type checks..."
	@$(POETRY) run mypy src/ && echo "✅ Type checking passed" || echo "⚠️  Type checking found issues (non-blocking)"
	@echo ""
	@echo "🧪 [5/6] Running tests..."
	@$(POETRY) run pytest --maxfail=1 --cov=tnh_scholar --cov-report=term-missing
	@echo ""
	@echo "📝 [6/6] Verifying README ↔ docs/index.md sync..."
	@$(POETRY) run python scripts/sync_readme.py && echo "✅ README sync verified"
	@echo ""
	@echo "========================================="
	@echo "✅ CI checks complete!"
	@echo "========================================="
	@echo ""
	@echo "Note: Markdown lint (npx markdownlint) requires Node.js and is not included."
	@echo "Run manually: npx markdownlint '**/*.md'"

pr-check:
	@echo "Evaluating PR readiness against $(PR_BASE)..."
	$(POETRY) run python scripts/pr_readiness.py --base $(PR_BASE) $(PR_CHECK_ARGS)

# Release management targets
# Set DRY_RUN=1 to preview commands without executing (e.g., make release-patch DRY_RUN=1)
DRY_RUN ?= 0

release-check: test type-check lint docs-verify
	@echo "✅ All quality checks passed - ready to release"

changelog-draft:
	@echo "📝 Generating CHANGELOG entry from git history..."
	@$(POETRY) run python scripts/generate_changelog_entry.py || echo "\n⚠️  Could not generate changelog (no previous tag?)\n   You'll need to write it manually."
	@echo "\n👆 Copy this to CHANGELOG.md and edit as needed"

release-patch:
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "🔍 DRY RUN MODE - No changes will be made"; \
		echo ""; \
		CURRENT=$$($(POETRY) version -s); \
		NEW=$$($(POETRY) version --dry-run patch 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | tail -1); \
		echo "🚀 Would bump patch version: $$CURRENT → $$NEW"; \
		echo ""; \
		echo "Commands that would run:"; \
		echo "  poetry version patch"; \
		echo "  sed -i.bak 's/> \*\*Version\*\*:.*/> **Version**: $$NEW (Alpha)/' TODO.md"; \
		echo ""; \
		echo "To execute: make release-patch"; \
	else \
		echo "🚀 Bumping patch version (0.x.Y -> 0.x.Y+1)..."; \
		$(POETRY) version patch; \
		$(MAKE) _release-update-files; \
	fi

release-minor:
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "🔍 DRY RUN MODE - No changes will be made"; \
		echo ""; \
		CURRENT=$$($(POETRY) version -s); \
		NEW=$$($(POETRY) version --dry-run minor 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | tail -1); \
		echo "🚀 Would bump minor version: $$CURRENT → $$NEW"; \
		echo ""; \
		echo "Commands that would run:"; \
		echo "  poetry version minor"; \
		echo "  sed -i.bak 's/> \*\*Version\*\*:.*/> **Version**: $$NEW (Alpha)/' TODO.md"; \
		echo ""; \
		echo "To execute: make release-minor"; \
	else \
		echo "🚀 Bumping minor version (0.X.y -> 0.X+1.0)..."; \
		$(POETRY) version minor; \
		$(MAKE) _release-update-files; \
	fi

release-major:
	@if [ "$(DRY_RUN)" = "1" ]; then \
		echo "🔍 DRY RUN MODE - No changes will be made"; \
		echo ""; \
		CURRENT=$$($(POETRY) version -s); \
		NEW=$$($(POETRY) version --dry-run major 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | tail -1); \
		echo "🚀 Would bump major version: $$CURRENT → $$NEW"; \
		echo ""; \
		echo "Commands that would run:"; \
		echo "  poetry version major"; \
		echo "  sed -i.bak 's/> \*\*Version\*\*:.*/> **Version**: $$NEW (Alpha)/' TODO.md"; \
		echo ""; \
		echo "To execute: make release-major"; \
	else \
		echo "🚀 Bumping major version (X.y.z -> X+1.0.0)..."; \
		$(POETRY) version major; \
		$(MAKE) _release-update-files; \
	fi

_release-update-files:
	@VERSION=$$($(POETRY) version -s); \
	echo "📝 Updating version to $$VERSION in TODO.md..."; \
	if grep -q "> \*\*Version\*\*:" TODO.md; then \
		sed -i.bak "s/> \*\*Version\*\*:.*/> **Version**: $$VERSION (Alpha)/" TODO.md && rm -f TODO.md.bak; \
	else \
		echo "⚠️  Version marker not found in TODO.md"; \
	fi; \
	echo "📝 Updating version to $$VERSION in __init__.py..."; \
	$(POETRY) run python scripts/update_version.py; \
	echo "✅ Version updated to $$VERSION in all files"; \
	echo ""; \
	echo "Next steps:"; \
	echo "  1. Run 'make changelog-draft' to generate CHANGELOG entry"; \
	echo "  2. Edit CHANGELOG.md with the generated content"; \
	echo "  3. Run 'make release-commit' to commit changes"; \
	echo "  4. Run 'make release-tag' to tag and push"; \
	echo "  5. Run 'make release-publish' to publish to PyPI and create GitHub release"

release-commit:
	@VERSION=$$($(POETRY) version -s); \
	if [ "$(DRY_RUN)" = "1" ]; then \
		echo "🔍 DRY RUN MODE - No changes will be made"; \
		echo ""; \
		echo "📝 Would commit version $$VERSION"; \
		echo ""; \
		echo "Files that would be staged:"; \
		echo "  - pyproject.toml"; \
		echo "  - TODO.md"; \
		echo "  - src/tnh_scholar/__init__.py"; \
		echo "  - CHANGELOG.md"; \
		echo "  - poetry.lock"; \
		echo ""; \
		echo "Commit message:"; \
		echo "  chore: Bump version to $$VERSION"; \
		echo ""; \
		echo "  - Update version in pyproject.toml"; \
		echo "  - Update TODO.md version header"; \
		echo "  - Update __init__.py __version__"; \
		echo "  - Add $$VERSION release notes to CHANGELOG.md"; \
		echo ""; \
		echo "  🤖 Generated with Claude Code"; \
		echo ""; \
		echo "  Co-Authored-By: Claude <noreply@anthropic.com>"; \
		echo ""; \
		echo "To execute: make release-commit"; \
	else \
		echo "📝 Committing version $$VERSION..."; \
		git add pyproject.toml TODO.md src/tnh_scholar/__init__.py CHANGELOG.md poetry.lock; \
		git commit -m "chore: Bump version to $$VERSION" \
			-m "" \
			-m "- Update version in pyproject.toml" \
			-m "- Update TODO.md version header" \
			-m "- Update __init__.py __version__" \
			-m "- Add $$VERSION release notes to CHANGELOG.md" \
			-m "" \
			-m "🤖 Generated with Claude Code" \
			-m "" \
			-m "Co-Authored-By: Claude <noreply@anthropic.com>"; \
		echo "✅ Release committed"; \
		echo ""; \
		echo "Next: Run 'make release-tag' to tag and push"; \
	fi

release-tag:
	@VERSION=$$($(POETRY) version -s); \
	BRANCH=$$(git branch --show-current); \
	if [ "$(DRY_RUN)" = "1" ]; then \
		echo "🔍 DRY RUN MODE - No changes will be made"; \
		echo ""; \
		echo "🏷️  Would create and push tag v$$VERSION"; \
		echo ""; \
		echo "Commands that would run:"; \
		echo "  git tag -a v$$VERSION -m 'Release v$$VERSION...'"; \
		echo "  git push origin $$BRANCH"; \
		echo "  git push origin v$$VERSION"; \
		echo ""; \
		echo "Tag message:"; \
		echo "  Release v$$VERSION"; \
		echo ""; \
		echo "  See CHANGELOG.md for full details."; \
		echo ""; \
		echo "  🤖 Generated with Claude Code"; \
		echo ""; \
		echo "  Co-Authored-By: Claude <noreply@anthropic.com>"; \
		echo ""; \
		echo "To execute: make release-tag"; \
	else \
		echo "🏷️  Tagging version v$$VERSION..."; \
		git tag -a "v$$VERSION" -m "Release v$$VERSION" \
			-m "" \
			-m "See CHANGELOG.md for full details." \
			-m "" \
			-m "🤖 Generated with Claude Code" \
			-m "" \
			-m "Co-Authored-By: Claude <noreply@anthropic.com>"; \
		echo "📤 Pushing branch and tag..."; \
		git push origin $$BRANCH; \
		git push origin "v$$VERSION"; \
		echo "✅ Tagged and pushed v$$VERSION"; \
		echo ""; \
		echo "Next: Run 'make release-publish' to publish to PyPI"; \
	fi

release-publish:
	@VERSION=$$($(POETRY) version -s); \
	if [ "$(DRY_RUN)" = "1" ]; then \
		echo "🔍 DRY RUN MODE - No changes will be made"; \
		echo ""; \
		echo "📦 Would build and publish package v$$VERSION to PyPI and GitHub"; \
		echo ""; \
		echo "Commands that would run:"; \
		echo "  python scripts/prepare_pypi_readme.py  # Strip YAML frontmatter"; \
		echo "  poetry build"; \
		echo "  poetry publish"; \
		echo "  python scripts/prepare_pypi_readme.py --restore  # Restore original"; \
		echo "  gh release create v$$VERSION --title 'Release v$$VERSION' --notes-file CHANGELOG.md"; \
		echo ""; \
		echo "Files that would be created:"; \
		echo "  - dist/tnh_scholar-$$VERSION-py3-none-any.whl"; \
		echo "  - dist/tnh_scholar-$$VERSION.tar.gz"; \
		echo ""; \
		echo "To execute: make release-publish"; \
	else \
		if ! command -v gh >/dev/null 2>&1; then \
			echo "❌ GitHub CLI (gh) not found. Please install it and ensure it's on your PATH before running release-publish." >&2; \
			exit 1; \
		fi; \
		if ! gh auth status >/dev/null 2>&1; then \
			echo "❌ GitHub CLI (gh) is not authenticated. Please run 'gh auth login' before running release-publish." >&2; \
			exit 1; \
		fi; \
		echo "📝 Preparing README for PyPI (stripping YAML frontmatter)..."; \
		$(POETRY) run python scripts/prepare_pypi_readme.py; \
		echo ""; \
		echo "📦 Building package..."; \
		$(POETRY) build; \
		echo ""; \
		echo "📤 Publishing to PyPI..."; \
		$(POETRY) publish; \
		echo ""; \
		echo "📝 Restoring original README..."; \
		$(POETRY) run python scripts/prepare_pypi_readme.py --restore; \
		echo ""; \
		echo "✅ Published v$$VERSION to PyPI"; \
		echo ""; \
		echo "📢 Creating GitHub release..."; \
		if [ -f CHANGELOG.md ]; then \
			gh release create "v$$VERSION" \
				--title "Release v$$VERSION" \
				--notes-file CHANGELOG.md \
				--latest; \
		else \
			gh release create "v$$VERSION" \
				--title "Release v$$VERSION" \
				--notes "See CHANGELOG.md for details." \
				--latest; \
		fi; \
		echo "✅ Created GitHub release v$$VERSION"; \
		echo ""; \
		REMOTE_URL=$$(git remote get-url origin 2>/dev/null || true); \
		GITHUB_REPO=$$(REMOTE_URL="$$REMOTE_URL" python - <<'PY'\
	import os\
	import re\
	\
	remote = os.environ.get("REMOTE_URL", "")\
	match = re.search(r'github\\.com[:/](?P<repo>[^/]+/[^/]+)(?:\\.git)?$$', remote)\
	if match:\
	    print(match.group("repo"))\
	PY\
	); \
		echo "🎉 Release complete!"; \
		echo "   PyPI: https://pypi.org/project/tnh-scholar/"; \
		if [ -n "$$GITHUB_REPO" ]; then \
			echo "   GitHub: https://github.com/$$GITHUB_REPO/releases/tag/v$$VERSION"; \
		else \
			echo "   GitHub release URL not shown (origin remote not recognized as GitHub)."; \
		fi; \
	fi

release-full: release-commit release-tag release-publish
	@VERSION=$$($(POETRY) version -s); \
	echo ""; \
	echo "🎉 Full release workflow complete for v$$VERSION!"
