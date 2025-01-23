# Release Checklist

- [ ] Update version in pyproject.toml
- [ ] Update CHANGELOG.md
- [ ] Run full test suite: `pytest`
- [ ] Run type checks: `mypy`
- [ ] Run linting: `ruff check .`
- [ ] Build test
- [ ] TestPyPI upload & install test
- [ ] PyPI upload
- [ ] Tag release in git