PYTHON_VERSION = 3.12.4
POETRY        = poetry

.PHONY: setup setup-dev test lint format kernel docs docs-generate docs-build docs-drift docs-verify

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
docs-generate:
	@echo "Generating documentation artifacts..."
	$(POETRY) run python scripts/generate_index_md.py
	$(POETRY) run python scripts/generate_doc_index.py
	$(POETRY) run python scripts/generate_cli_docs.py

docs-build: docs-generate
	@echo "Building MkDocs site..."
	$(POETRY) run mkdocs build

docs-drift:
	@echo "Checking README ↔ docs/index.md drift..."
	$(POETRY) run python scripts/check_readme_docs_drift.py

docs-verify: docs-drift docs-build
	@echo "Verifying documentation..."
	$(POETRY) run python scripts/sync_readme.py

docs: docs-verify
	@echo "Documentation build complete: site/"