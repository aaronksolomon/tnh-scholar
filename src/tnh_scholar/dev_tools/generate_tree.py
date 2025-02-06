from pathlib import Path
import subprocess
import sys

from tnh_scholar import TNH_PROJECT_ROOT_DIR

default_root_path = TNH_PROJECT_ROOT_DIR
default_output_path = TNH_PROJECT_ROOT_DIR / "project_directory_tree.txt"


def generate_tree(root_dir: Path = default_root_path, output_path: Path = default_output_path):
    subprocess.run(["tree", "--gitignore", root_dir,
            "-o", str(output_path)], check=True)
    
if __name__ == "__main__":
    root_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default_root_path
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else default_output_path
    generate_tree(root_dir, output_file)