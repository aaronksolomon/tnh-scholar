"""
Developer tool for the tnh-scholar project.

This script generates a directory tree for the entire project and for the src directory,
saving the results to 'project_directory_tree.txt' and 'src_directory_tree.txt' respectively.

Uses the generic module generate_tree which has a basic function build_tree that executes tree building.

Exposed as a script via pyproject.toml under the name 'tnh-tree'.
"""
from tnh_scholar import TNH_PROJECT_ROOT_DIR
from tnh_scholar.tools.tree_builder import build_tree


def main() -> None:
    """CLI entry point registered as ``tnh-tree``."""
    build_tree(TNH_PROJECT_ROOT_DIR, TNH_PROJECT_ROOT_DIR / "src")


if __name__ == "__main__":
    main()
