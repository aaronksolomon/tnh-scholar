PYTHON_VERSION = 3.12.4
POETRY        = poetry

.PHONY: setup setup-dev test lint format kernel

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