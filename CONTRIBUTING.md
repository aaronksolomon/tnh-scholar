---
title: "TNH Scholar CONTRIBUTING"
description: "TNH Scholar is rapidly evolving, but we strive for a predictable, reproducible development workflow."
owner: ""
author: ""
status: processing
created: "2024-10-21"
---
# TNH Scholar CONTRIBUTING

Guidance on contributing to the TNH Scholar Project. TNH Scholar is rapidly evolving, but we strive for a predictable, reproducible development workflow.  This document summarizes how to get set up, what tools we use, and what we expect in pull requests.

## 1. Development environment

TNH Scholar uses **pyenv** for Python version pinning and **Poetry** for dependency management.  
Follow [DEV_SETUP.md](DEV_SETUP.md) for detailed instructions. The essentials are:

1. Install `pyenv` and `Python 3.12.4` (`pyenv install 3.12.4 --skip-existing`).
2. Install Poetry and enable in-project environments: `poetry config virtualenvs.in-project true`.
3. Clone the repo and run one of the Make targets:

   ```bash
   make setup        # runtime dependencies only
   make setup-dev    # runtime + dev dependencies (recommended for contributors)
   ```

The Makefile mirrors our CI configuration, so using it locally guarantees parity.

## 2. Day-to-day workflow

- Create a feature branch from `main` (or the branch requested in your issue).
- Keep changes focused; open separate PRs for unrelated fixes.
- Use Poetry to run tools so the correct virtualenv is used:

  ```bash
  make lint         # poetry run ruff check .
  make format       # poetry run ruff format .
  poetry run mypy src/
  make test         # poetry run pytest
  ```

- Update documentation (README, DEV_SETUP, etc.) whenever behavior or commands change.

## 3. Pull request checklist

- [ ] All tests pass locally (`make test`).
- [ ] Linting and formatting pass (`make lint`, `make format`, `poetry run mypy src/`).
- [ ] New functionality includes tests and, when relevant, documentation updates.
- [ ] Commit messages and PR descriptions explain the motivation and approach.
- [ ] CI is green — it runs the same Poetry-based workflow described above.

## 4. Reporting issues & proposing ideas

Use [GitHub Issues](https://github.com/aaronksolomon/tnh-scholar/issues) to report bugs or request features.  
Please include:

- Steps to reproduce (commands, inputs, expected vs. actual behavior).
- Environment details (OS, Python version, whether you're using the Poetry env).
- Relevant logs or stack traces.

For design discussions, open an issue and tag it with `discussion` so we can keep the history public.

## 5. Need help?

If you get stuck during setup, consult [DEV_SETUP.md](DEV_SETUP.md) first — it is the canonical source for environment instructions.  
If that doesn’t answer your question, open an issue describing the problem and what you have tried.

Thanks for helping make TNH Scholar better!