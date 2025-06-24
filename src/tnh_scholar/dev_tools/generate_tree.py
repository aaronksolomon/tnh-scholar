"""
Developer tool for the tnh-scholar project.

This script generates a directory tree for the entire project and for the src directory,
saving the results to 'project_directory_tree.txt' and 'src_directory_tree.txt' respectively.

Exposed as a script via pyproject.toml under the name 'tnh-tree'.
"""
import subprocess

from tnh_scholar import TNH_PROJECT_ROOT_DIR


def generate_tree():
    project_tree_output = TNH_PROJECT_ROOT_DIR / "project_directory_tree.txt"
    src_tree_output = TNH_PROJECT_ROOT_DIR / "src_directory_tree.txt"
    src_dir = TNH_PROJECT_ROOT_DIR / "src"

    subprocess.run(["tree", "--gitignore", TNH_PROJECT_ROOT_DIR, "-o", str(project_tree_output)], check=True)
    subprocess.run(["tree", "--gitignore", src_dir, "-o", str(src_tree_output)], check=True)

if __name__ == "__main__":
    generate_tree()