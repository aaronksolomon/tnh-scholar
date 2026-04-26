"""
Developer tool for the tnh-scholar project.

This legacy utility generates repository tree snapshots for manual developer reference.
It is no longer part of routine CI or release validation.
"""
from tnh_scholar import TNH_PROJECT_ROOT_DIR
from tnh_scholar.tools.tree_builder import build_tree


def main() -> None:
    """CLI entry point registered as ``tnh-tree``."""
    build_tree(TNH_PROJECT_ROOT_DIR, TNH_PROJECT_ROOT_DIR / "src")


if __name__ == "__main__":
    main()
