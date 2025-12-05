PYTHON_VERSION = 3.12.4
POETRY        = poetry
LYCHEE        = lychee

.PHONY: setup setup-dev test lint format kernel docs docs-validate docs-generate docs-build docs-drift docs-verify codespell link-check docs-quickcheck

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
