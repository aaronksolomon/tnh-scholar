PYTHON_VERSION = 3.12.4
POETRY        = poetry
LYCHEE        = lychee

.PHONY: setup setup-dev test lint format kernel docs docs-validate docs-generate docs-build docs-drift docs-verify codespell link-check docs-quickcheck type-check release-check changelog-draft release-patch release-minor release-major release-commit release-tag release-publish release-full

setup:
	pyenv install -s $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION)
	$(POETRY) env use python
	$(POETRY) install

setup-dev:
	pyenv install -s $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION)
	$(POETRY) env use python
	$(POETRY) install --with dev
	$(POETRY) run python -m ipykernel install --user --name tnh-scholar --display-name "Python (tnh-scholar)"

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
	@echo "Validating markdown documentation..."
	@$(POETRY) run python scripts/validate_markdown.py || echo "⚠️  Validation warnings found (non-fatal)"

docs-generate: docs-validate
	@echo "Generating documentation artifacts..."
	$(POETRY) run python scripts/sync_root_docs.py
	$(POETRY) run python scripts/generate_index_md.py
	$(POETRY) run python scripts/generate_doc_index.py
	$(POETRY) run python scripts/generate_cli_docs.py

docs-build: docs-generate
	@echo "Building MkDocs site..."
	$(POETRY) run mkdocs build --strict

docs-drift:
	@echo "Checking README ↔ docs/index.md drift..."
	$(POETRY) run python scripts/check_readme_docs_drift.py

link-check:
	@echo "Running link check with lychee..."
	@command -v $(LYCHEE) >/dev/null 2>&1 || { echo >&2 "lychee not found. Install from https://github.com/lycheeverse/lychee/releases or set LYCHEE=<path>."; exit 1; }
	$(LYCHEE) --config .lychee.toml README.md docs

codespell:
	@echo "Running codespell..."
	$(POETRY) run codespell -q 3 -I .codespell-ignore.txt README.md docs

docs-verify: docs-drift docs-build link-check codespell
	@echo "Verifying documentation..."
	$(POETRY) run python scripts/sync_readme.py

docs: docs-verify
	@echo "Documentation build complete: site/"

docs-quickcheck: docs-generate
	@echo "Running docs quickcheck (strict build, links, spelling)..."
	$(POETRY) run mkdocs build --strict
	$(MAKE) link-check
	$(MAKE) codespell

# Type checking
type-check:
	@echo "Running type checks..."
	$(POETRY) run mypy src/

# Release management targets
release-check: test type-check lint docs-verify
	@echo "✅ All quality checks passed - ready to release"

changelog-draft:
	@echo "📝 Generating CHANGELOG entry from git history..."
	@$(POETRY) run python scripts/generate_changelog_entry.py || echo "\n⚠️  Could not generate changelog (no previous tag?)\n   You'll need to write it manually."
	@echo "\n👆 Copy this to CHANGELOG.md and edit as needed"

release-patch:
	@echo "🚀 Bumping patch version (0.x.Y -> 0.x.Y+1)..."
	$(POETRY) version patch
	@$(MAKE) _release-update-files

release-minor:
	@echo "🚀 Bumping minor version (0.X.y -> 0.X+1.0)..."
	$(POETRY) version minor
	@$(MAKE) _release-update-files

release-major:
	@echo "🚀 Bumping major version (X.y.z -> X+1.0.0)..."
	$(POETRY) version major
	@$(MAKE) _release-update-files

_release-update-files:
	@VERSION=$$($(POETRY) version -s); \
	echo "📝 Updating version to $$VERSION in TODO.md..."; \
	if grep -q "> \*\*Version\*\*:" TODO.md; then \
		sed -i.bak "s/> \*\*Version\*\*:.*/> **Version**: $$VERSION (Alpha)/" TODO.md && rm -f TODO.md.bak; \
	else \
		echo "⚠️  Version marker not found in TODO.md"; \
	fi; \
	echo "✅ Version updated to $$VERSION"; \
	echo ""; \
	echo "Next steps:"; \
	echo "  1. Run 'make changelog-draft' to generate CHANGELOG entry"; \
	echo "  2. Edit CHANGELOG.md with the generated content"; \
	echo "  3. Run 'make release-commit' to commit changes"; \
	echo "  4. Run 'make release-tag' to tag and push"; \
	echo "  5. Run 'make release-publish' to publish to PyPI"

release-commit:
	@VERSION=$$($(POETRY) version -s); \
	echo "📝 Committing version $$VERSION..."; \
	git add pyproject.toml TODO.md CHANGELOG.md poetry.lock; \
	git commit -m "chore: Bump version to $$VERSION" \
		-m "" \
		-m "- Update version in pyproject.toml" \
		-m "- Update TODO.md version header" \
		-m "- Add $$VERSION release notes to CHANGELOG.md" \
		-m "" \
		-m "🤖 Generated with Claude Code" \
		-m "" \
		-m "Co-Authored-By: Claude <noreply@anthropic.com>"; \
	echo "✅ Release committed"; \
	echo ""; \
	echo "Next: Run 'make release-tag' to tag and push"

release-tag:
	@VERSION=$$($(POETRY) version -s); \
	BRANCH=$$(git branch --show-current); \
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
	echo "Next: Run 'make release-publish' to publish to PyPI"

release-publish:
	@VERSION=$$($(POETRY) version -s); \
	echo "📦 Building package..."; \
	$(POETRY) build; \
	echo "📤 Publishing to PyPI..."; \
	$(POETRY) publish; \
	echo "✅ Published v$$VERSION to PyPI"; \
	echo ""; \
	echo "🎉 Release complete! Check https://pypi.org/project/tnh-scholar/"

release-full: release-commit release-tag release-publish
	@VERSION=$$($(POETRY) version -s); \
	echo ""; \
	echo "🎉 Full release workflow complete for v$$VERSION!"
