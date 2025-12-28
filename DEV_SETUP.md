---
title: "TNH-Scholar DEV_SETUP"
description: "This document outlines the standard development environment for TNH‑Scholar."
owner: ""
author: ""
status: processing
created: "2025-11-19"
---
# TNH-Scholar DEV_SETUP

This document outlines the standard development environment for TNH‑Scholar.  
The goals are: clarity, reproducibility, stability, and low onboarding friction.

The project uses **pyenv** to manage Python versions and **Poetry** to manage dependencies and virtual environments.

---

## 1. Install pyenv (Python version manager)

Follow official instructions for your platform:  
<https://github.com/pyenv/pyenv>

Recommended macOS setup (Homebrew):

```shell
brew install pyenv
```

After installation, ensure your shell is configured:

```shell
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
```

Reload your shell:

```shell
source ~/.zshrc
```

---

## 2. Install the required Python version

TNH‑Scholar currently targets: `Python 3.12.4`

Install it with pyenv:

```shell
pyenv install 3.12.4 --skip-existing
```

Then set the local version inside the project root:

```shell
cd tnh-scholar
pyenv local 3.12.4
```

This ensures all commands inside this directory use that exact Python interpreter.

---

## 3. Install Poetry (dependency + project manager)

Installation (official method):

```shell
curl -sSL https://install.python-poetry.org | python3 -
```

Ensure Poetry is added to your PATH (the installer will tell you where to place this):

```shell
export PATH="$HOME/.local/bin:$PATH"
```

Verify installation:

```shell
poetry --version
```

---

## 4. Configure Poetry for in‑project virtual environments

This keeps the `.venv/` folder inside the repository, making environment resolution easier for IDEs, Jupyter, and tooling.

```shell
poetry config virtualenvs.in-project true
```

---

## 5. Create the virtual environment & install project dependencies

Inside the project root, the recommended way to create the environment is via the `Makefile` (see below):

```shell
make setup
```

This will:

- Ensure the correct Python version via pyenv.
- Create or reuse the Poetry-managed virtualenv.
- Install all **core (non-dev)** dependencies from `pyproject.toml`.

For development work (tests, linting, docs, Jupyter, etc.), use:

```shell
make setup-dev
```

This will:

- Do everything `make setup` does **plus**:
- Install all **dev dependencies** (pytest, ruff, ipykernel, etc.).
- Register the `tnh-scholar` Jupyter kernel.

If you prefer to do it manually without `make`:

```shell
poetry env use python
poetry install  # Installs all dependencies including dev group (as of Dec 2025)
poetry run python -m ipykernel install --user --name tnh-scholar --display-name "Python (tnh-scholar)"
```

**Note**: As of December 2025, `poetry install` automatically includes dev dependencies (pytest, mkdocs, mypy, etc.) since the dev group is no longer marked as optional. No need for `--with dev` flag.

---

## 6. Common development commands

### Run the test suite

```shell
poetry run pytest
```

### Lint & format

```shell
poetry run ruff check .
poetry run ruff format .
```

### Run any script or tool

```shell
poetry run <command>
```

Example:

```shell
poetry run python scripts/some_tool.py
```

---

## 7. Makefile

The repository includes a `Makefile` at the project root:

```make
PYTHON_VERSION = 3.12.4
POETRY        = poetry

.PHONY: setup setup-dev test lint format kernel

setup:
 pyenv install -s $(PYTHON_VERSION)
 pyenv local $(PYTHON_VERSION)
 $(POETRY) env use python
 $(POETRY) install  # Includes dev dependencies automatically

setup-dev:
 pyenv install -s $(PYTHON_VERSION)
 pyenv local $(PYTHON_VERSION)
 $(POETRY) env use python
 $(POETRY) install  # Dev dependencies included by default (dev group not optional)
 $(POETRY) run python -m ipykernel install --user --name tnh-scholar --display-name "Python (tnh-scholar)"

test:
 $(POETRY) run pytest

lint:
 $(POETRY) run ruff check .

format:
 $(POETRY) run ruff format .

kernel:
 $(POETRY) run python -m ipykernel install --user --name tnh-scholar --display-name "Python (tnh-scholar)"
```

Standard onboarding:

```shell
# minimal (no dev tools)
make setup

# full development environment (recommended)
make setup-dev
```

---

## 8. Optional: Jupyter kernel registration

The recommended way to register the Jupyter kernel is via:

```shell
make setup-dev
```

which automatically installs dev dependencies and registers the kernel.

If you need to re-register the kernel manually:

```shell
make kernel
```

After that, VS Code or Jupyter will show a kernel named `Python (tnh-scholar)`.

---

## 9. CI and production recommendations

- Commit both `pyproject.toml` and `poetry.lock` to version control.
- In CI, always install using the lockfile:

```shell
poetry install --no-root --no-interaction --no-ansi
```

- When updating dependencies, update intentionally:

```shell
poetry add <package>
poetry update <package>
```

- Avoid global packages. Use Poetry environments or `pipx` for global tools.

---

## 10. Summary

Your workflow should look like this:

1. pyenv selects the Python version  
2. Poetry manages the environment + dependencies  
3. `.venv/` stays local to the project  
4. All tools run through `poetry run`  
5. Lockfile ensures reproducible builds  

This combination is stable, clean, and well‑understood—ideal for TNH‑Scholar’s long‑term architecture and multi‑year development cycle.