from pathlib import Path
import subprocess
import sys

ignore_list = ['__pycache__', '*.pyc', '*.pyo', '*.pyd', '.git*', '.pytest_cache', '*.egg-info', 'dist', 'build', 'data', 'processed_data', 'sandbox', 'patterns', '.vscode', 'tmp', 'site']

ignore_str = "|".join(ignore_list)
def generate_tree(root_dir='.', output_file='project_directory_tree.txt'):
    root = Path(root_dir)
    output = Path(output_file)
    
    try:
        # Try using tree command first
        subprocess.run(["tree", "-I", 
            ignore_str,
            "-o", str(output)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to pathlib implementation
        with open(output, "w") as f:
            f.write(".\n")
            for path in sorted(root.rglob("*")):
                if any(p.startswith(".") for p in path.parts):
                    continue
                if path.name in {"__pycache__", "*.pyc", "*.pyo", "*.pyd"}:
                    continue
                rel_path = path.relative_to(root)
                f.write(f"{'    ' * (len(path.parts)-1)}├── {path.name}\n")

if __name__ == "__main__":
    root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'project_directory_tree.txt'
    generate_tree(root_dir, output_file)