import fcntl
import hashlib
import os
import re
from contextlib import contextmanager, suppress
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, NewType, Optional, Tuple, Union

import yaml
from dotenv import load_dotenv
from git import Actor, Commit, Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from jinja2 import Environment, StrictUndefined, TemplateError
from jinja2.meta import find_undeclared_variables

from tnh_scholar import TNH_DEFAULT_PATTERN_DIR
from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import read_str_from_file, write_str_to_file

# Custom type for markdown content
MarkdownStr = NewType("MarkdownStr", str)

logger = get_child_logger(__name__)

MANAGER_UPDATE_MESSAGE = "PromptManager Update:"

class Prompt:
    """
    Base Prompt class for version-controlled template prompts.

    Prompts contain:
    - Instructions: The main prompt instructions as a Jinja2 template.
       Note: Instructions are intended to be saved in markdown format in a .md file.
    - Template fields: Default values for template variables
    - Metadata: Name and identifier information

    Version control is handled externally through Git, not in the prompt itself.
    Prompt identity is determined by the combination of identifiers.

    Attributes:
        name (str): The name of the prompt
        instructions (str): The Jinja2 template string for this prompt
        default_template_fields (Dict[str, str]): Default values for template variables
        _allow_empty_vars (bool): Whether to allow undefined template variables
        _env (Environment): Configured Jinja2 environment instance
    """

    @staticmethod
    def _normalize_name(value: str) -> str:
        """Canonicalize prompt names for case-insensitive handling.
        
        Currently: strip() + lower(). If future rules are needed (e.g.,
        removing punctuation, limiting length), implement them here.
        """
        return value.strip().lower()

    def __init__(
        self,
        name: str,
        instructions: MarkdownStr,
        path: Optional[Path] = None,
        default_template_fields: Optional[Dict[str, str]] = None,
        allow_empty_vars: bool = False,        
    ) -> None:
        """
        Initialize a new Prompt instance.

        Args:
            name: Unique name identifying the prompt
            instructions: Jinja2 template string containing the prompt
            default_template_fields: Optional default values for template variables
            allow_empty_vars: Whether to allow undefined template variables

        Raises:
            ValueError: If name or instructions are empty
            TemplateError: If template syntax is invalid
        """
        if not name or not instructions:
            raise ValueError("Name and instructions must not be empty")

        # Normalize prompt name to lowercase for case-insensitive handling
        name = Prompt._normalize_name(name)

        self.name = name
        self.instructions = instructions
        self.path = path
        self.default_template_fields = default_template_fields or {}
        self._allow_empty_vars = allow_empty_vars
        self._env = self._create_environment()

        # Validate template syntax on initialization
        self._validate_template()

    @staticmethod
    def _create_environment() -> Environment:
        """
        Create and configure a Jinja2 environment with optimal settings.

        Returns:
            Environment: Configured Jinja2 environment 
            with security and formatting options
        """
        return Environment(
            undefined=StrictUndefined,  # Raise errors for undefined variables
            trim_blocks=True,  # Remove first newline after a block
            lstrip_blocks=True,  # Strip tabs and spaces from the start of lines
            autoescape=True,  # Enable autoescaping for security
        )

    def _validate_template(self) -> None:
        """
        Validate the template syntax without rendering.

        Raises:
            TemplateError: If template syntax is invalid
        """
        try:
            self._env.parse(self.instructions)
        except TemplateError as e:
            raise TemplateError(
                f"Invalid template syntax in prompt '{self.name}': {str(e)}"
            ) from e

    def apply_template(self, field_values: Optional[Dict[str, str]] = None) -> str:
        """
        Apply template values to prompt instructions using Jinja2.

        Values precedence (highest to lowest):
        1. field_values (explicitly passed)
        2. frontmatter values (from prompt file)
        3. default_template_fields (prompt defaults)

        Args:
            field_values: Values to substitute into the template.
                        If None, uses frontmatter/defaults.

        Returns:
            str: Rendered instructions with template values applied.

        Raises:
            TemplateError: If template rendering fails
            ValueError: If required template variables are missing
        """
        # Get frontmatter values
        frontmatter = self.extract_frontmatter() or {}
        
        # Combine values with correct precedence using | operator
        template_values = self.default_template_fields | \
            frontmatter | (field_values or {})

        instructions = self.get_content_without_frontmatter()
        logger.debug(f"instructions without frontmatter:\n{instructions}")

        try:
            return self._render_template_with_values(instructions, template_values)
        except TemplateError as e:
            raise TemplateError(
                f"Template rendering failed for prompt '{self.name}': {str(e)}"
                ) from e

    def _render_template_with_values(
        self, 
        instructions: str, 
        template_values: dict
        ) -> str:
        """
        Validate and render template with provided values.
        
        Args:
            instructions: Template content without frontmatter
            template_values: Values to substitute into template
            
        Returns:
            Rendered template string
            
        Raises:
            ValueError: If required template variables are missing
        """
        # Parse for validation
        parsed_content = self._env.parse(instructions)
        required_vars = find_undeclared_variables(parsed_content)
        
        # Validate variables
        missing_vars = required_vars - set(template_values.keys())
        if missing_vars and not self._allow_empty_vars:
            raise ValueError(
                f"Missing required template variables in prompt '{self.name}': "
                f"{', '.join(sorted(missing_vars))}"
            )
        
        # Create and render template
        template = self._env.from_string(instructions)
        return template.render(**template_values)
    
    def extract_frontmatter(self) -> Optional[Dict[str, Any]]:
        """
        Extract and validate YAML frontmatter from markdown instructions.

        Returns:
            Optional[Dict]: Frontmatter data if found and valid, None otherwise

        Note:
            Frontmatter must be at the very start of the file and properly formatted.
        """

        prompt = r"\A---\s*\n(.*?)\n---\s*(?:\n|$)"
        if match := re.match(prompt, self.instructions, re.DOTALL):
            try:
                frontmatter = yaml.safe_load(match[1])
                if frontmatter is None:
                    return None
                if not isinstance(frontmatter, dict):
                    logger.warning(f"Frontmatter must be a YAML dictionary: "
                                   f"{frontmatter}")
                    return None
                return frontmatter
            except yaml.YAMLError as e:
                logger.warning(f"Invalid YAML in frontmatter: {e}")
                return None
        return None

    def get_content_without_frontmatter(self) -> str:
        """
        Get markdown content with frontmatter removed.

        Returns:
            str: Markdown content without frontmatter
        """
        prompt = r"\A---\s*\n.*?\n---\s*\n"
        return re.sub(prompt, "", self.instructions, flags=re.DOTALL)

    def update_frontmatter(self, new_data: Dict[str, Any]) -> None:
        """
        Update or add frontmatter to the markdown content.

        Args:
            new_data: Dictionary of frontmatter fields to update
        """

        current_frontmatter = self.extract_frontmatter() or {}
        updated_frontmatter = {**current_frontmatter, **new_data}

        # Create YAML string
        yaml_str = yaml.dump(
            updated_frontmatter, default_flow_style=False, allow_unicode=True
        )

        # Remove existing frontmatter if present
        content = self.get_content_without_frontmatter()

        # Combine new frontmatter with content
        self.instructions = f"---\n{yaml_str}---\n\n{content}"
        
        
    def source_bytes(self) -> bytes:
        """
        Best-effort raw bytes for prompt hashing.

        Prefers hashing exact on-disk bytes including front-matter.
        We therefore first try to read from `prompt_path`. If that fails, we fall back
        to hashing the concatenation of known templates. In V1, only
        the instructions (system template) are used for rendering.
        """
        # Preferred path: use on-disk bytes when available.
        if self.path is not None:
            return self.path.read_bytes()

        # Fallback: concatenate known templates deterministically
        sys_part = self.instructions or ""
        return sys_part.encode("utf-8")

    def content_hash(self) -> str:
        """
        Generate a SHA-256 hash of the prompt content.

        Useful for quick content comparison and change detection.

        Returns:
            str: Hexadecimal string of the SHA-256 hash
        """
        content = (
            f"{self.name}{self.instructions}"
            f"{sorted(self.default_template_fields.items())}"
            )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert prompt to dictionary for serialization.

        Returns:
            Dict containing all prompt data in serializable format
        """
        return {
            "name": self.name,
            "instructions": self.instructions,
            "default_template_fields": self.default_template_fields,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Prompt":
        """
        Create prompt instance from dictionary data.

        Args:
            data: Dictionary containing prompt data

        Returns:
            Prompt: New prompt instance

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = {"name", "instructions"}
        if missing_fields := required_fields - set(data.keys()):
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        return cls(
            name=Prompt._normalize_name(str(data["name"])),
            instructions=data["instructions"],
            path=None,
            default_template_fields=data.get("default_template_fields", {}),
        )

    def __eq__(self, other: object) -> bool:
        """Compare prompts based on their content."""
        if not isinstance(other, Prompt):
            return NotImplemented
        return self.content_hash() == other.content_hash()

    def __hash__(self) -> int:
        """Hash based on content hash for container operations."""
        return hash(self.content_hash())


class GitBackedRepository:
    """
    Manages versioned storage of prompts using Git.

    Provides basic Git operations while hiding complexity:
    - Automatic versioning of changes
    - Basic conflict resolution
    - History tracking
    """

    def __init__(self, repo_path: Path):
        """
        Initialize or connect to Git repository.

        Args:
            repo_path: Path to repository directory

        Raises:
            GitCommandError: If Git operations fail
        """
        self.repo_path = repo_path

        try:
            # Try to connect to existing repository
            self.repo = Repo(repo_path)
            logger.debug(f"Connected to existing Git repository at {repo_path}")

        except InvalidGitRepositoryError:
            # Initialize new repository if none exists
            logger.info(f"Initializing new Git repository at {repo_path}")
            self.repo = Repo.init(repo_path)

            # Create initial commit if repo is empty
            if not self.repo.head.is_valid():
                # Create and commit .gitignore
                gitignore = repo_path / ".gitignore"
                gitignore.write_text("*.lock\n.DS_Store\n")
                self.repo.index.add([".gitignore"])
                self.repo.index.commit("Initial repository setup")

    def update_file(self, file_path: Path) -> str:
        """
        Stage and commit changes to a file in the Git repository.

        Args:
            file_path: Absolute or relative path to the file.

        Returns:
            str: Commit hash if changes were made.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is outside the repository.
            GitCommandError: If Git operations fail.
        """
        file_path = file_path.resolve()

        # Ensure the file is within the repository
        try:
            rel_path = file_path.relative_to(self.repo_path)
        except ValueError as e:
            raise ValueError(
                f"File {file_path} is not under the repository root {self.repo_path}"
            ) from e

        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        try:
            return self._commit_file_update(rel_path, file_path)
        except GitCommandError as e:
            logger.error(f"Git operation failed: {e}")
            raise

    def _commit_file_update(self, rel_path, file_path):
        if self._is_file_clean(rel_path):
            # Return the current commit hash if no changes
            return self.repo.head.commit.hexsha

        logger.info(f"Detected changes in {rel_path}, updating version control.")
        self.repo.index.add([str(rel_path)])
        commit = self.repo.index.commit(
            f"{MANAGER_UPDATE_MESSAGE} {rel_path.stem}",
            author=Actor("PromptManager", ""),
        )
        logger.info(f"Committed changes to {file_path}: {commit.hexsha}")
        return commit.hexsha

    def _get_file_revisions(self, file_path: Path) -> List[Commit]:
        """
        Get ordered list of commits that modified a file, most recent first.

        Args:
            file_path: Path to file relative to repository root

        Returns:
            List of Commit objects affecting this file

        Raises:
            GitCommandError: If Git operations fail
        """
        rel_path = file_path.relative_to(self.repo_path)
        try:
            return list(self.repo.iter_commits(paths=str(rel_path)))
        except GitCommandError as e:
            logger.error(f"Failed to get commits for {rel_path}: {e}")
            return []

    def _get_commit_diff(
        self, commit: Commit, file_path: Path, prev_commit: Optional[Commit] = None
    ) -> Tuple[str, str]:
        """
        Get both stat and detailed diff for a commit.

        Args:
            commit: Commit to diff
            file_path: Path relative to repository root
            prev_commit: Previous commit for diff, defaults to commit's parent

        Returns:
            Tuple of (stat_diff, detailed_diff) where:
                stat_diff: Summary of changes (files changed, insertions/deletions)
                detailed_diff: Colored word-level diff with context

        Raises:
            GitCommandError: If Git operations fail
        """
        prev_hash = prev_commit.hexsha if prev_commit else f"{commit.hexsha}^"
        rel_path = file_path.relative_to(self.repo_path)

        try:
            # Get stats diff
            stat = self.repo.git.diff(prev_hash, commit.hexsha, rel_path, stat=True)

            # Get detailed diff
            diff = self.repo.git.diff(
                prev_hash,
                commit.hexsha,
                rel_path,
                unified=2,
                word_diff="plain",
                color="always",
                ignore_space_change=True,
            )

            return stat, diff
        except GitCommandError as e:
            logger.error(f"Failed to get diff for {commit.hexsha}: {e}")
            return "", ""

    def display_history(self, file_path: Path, max_versions: int = 0) -> None:
        """
        Display history of changes for a file with diffs between versions.

        Shows most recent changes first, limited to max_versions entries.
        For each change shows:
        - Commit info and date
        - Stats summary of changes
        - Detailed color diff with 2 lines of context

        Args:
            file_path: Path to file in repository
            max_versions: Maximum number of versions to show; zero shows all revisions.

        Example:
            >>> repo.display_history(Path("prompts/format_dharma_talk.yaml"))
            Commit abc123def (2024-12-28 14:30:22):
            1 file changed, 5 insertions(+), 2 deletions(-)

            diff --git a/prompts/format_dharma_talk.yaml ...
            ...
        """

        try:
            # Get commit history
            commits = self._get_file_revisions(file_path)
            if not commits:
                print(f"No history found for {file_path}")
                return

            if max_versions == 0:
                max_versions = len(commits)  # look at all commits.

            # Display limited history with diffs
            for i, commit in enumerate(commits[:max_versions]):
                # Print commit header
                date_str = commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                print(f"\nCommit {commit.hexsha[:8]} ({date_str}):")
                print(f"Message: {commit.message.strip()}")

                # Get and display diffs
                prev_commit = commits[i + 1] if i + 1 < len(commits) else None
                stat_diff, detailed_diff = self._get_commit_diff(
                    commit, file_path, prev_commit
                )

                if stat_diff:
                    print("\nChanges:")
                    print(stat_diff)
                if detailed_diff:
                    print("\nDetailed diff:")
                    print(detailed_diff)

                print("\033[0m", end="")
                print("-" * 80)  # Visual separator between commits

        except Exception as e:
            logger.error(f"Failed to display history for {file_path}: {e}")
            print(f"Error displaying history: {e}")
            raise

    def _is_file_clean(self, rel_path: Path) -> bool:
        """
        Check if file has uncommitted changes.

        Args:
            rel_path: Path relative to repository root

        Returns:
            bool: True if file has no changes
        """
        return str(rel_path) not in (
            [item.a_path for item in self.repo.index.diff(None)]
            + self.repo.untracked_files
        )


class ConcurrentAccessManager:
    """
    Manages concurrent access to prompt files.

    Provides:
    - File-level locking
    - Safe concurrent access prompts
    - Lock cleanup
    """

    def __init__(self, lock_dir: Path):
        """
        Initialize access manager.

        Args:
            lock_dir: Directory for lock files
        """
        self.lock_dir = Path(lock_dir)
        self._ensure_lock_dir()
        self._cleanup_stale_locks()

    def _ensure_lock_dir(self) -> None:
        """Create lock directory if it doesn't exist."""
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def _cleanup_stale_locks(self, max_age: timedelta = timedelta(hours=1)) -> None:
        """
        Remove stale lock files.

        Args:
            max_age: Maximum age for lock files before considered stale
        """
        current_time = datetime.now()
        for lock_file in self.lock_dir.glob("*.lock"):
            try:
                mtime = datetime.fromtimestamp(lock_file.stat().st_mtime)
                if current_time - mtime > max_age:
                    lock_file.unlink()
                    logger.warning(f"Removed stale lock file: {lock_file}")
            except FileNotFoundError:
                # Lock was removed by another process
                pass
            except Exception as e:
                logger.error(f"Error cleaning up lock file {lock_file}: {e}")

    @contextmanager
    def file_lock(self, file_path: Path) -> Iterator[None]:
        """
        Context manager for safely accessing files.

        Args:
            file_path: Path to file to lock

        Yields:
            None when lock is acquired

        Raises:
            RuntimeError: If file is already locked
            OSError: If lock file operations fail
        """
        file_path = Path(file_path)
        lock_file_path = self.lock_dir / f"{file_path.stem}.lock"
        lock_fd = None

        try:
            # Open or create lock file
            lock_fd = os.open(str(lock_file_path), os.O_WRONLY | os.O_CREAT)

            try:
                # Attempt to acquire lock
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

                # Write process info to lock file
                pid = os.getpid()
                timestamp = datetime.now().isoformat()
                os.write(lock_fd, f"{pid} {timestamp}\n".encode())

                logger.debug(f"Acquired lock for {file_path}")
                yield

            except BlockingIOError as e:
                raise RuntimeError(
                    f"File {file_path} is locked by another process"
                ) from e

        except OSError as e:
            logger.error(f"Lock operation failed for {file_path}: {e}")
            raise

        finally:
            if lock_fd is not None:
                try:
                    # Release lock and close file descriptor
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)

                    # Remove lock file
                    lock_file_path.unlink(missing_ok=True)
                    logger.debug(f"Released lock for {file_path}")

                except Exception as e:
                    logger.error(f"Error cleaning up lock for {file_path}: {e}")

    def is_locked(self, file_path: Path) -> bool:
        """
        Check if a file is currently locked.

        Args:
            file_path: Path to file to check

        Returns:
            bool: True if file is locked
        """
        lock_file_path = self.lock_dir / f"{file_path.stem}.lock"

        if not lock_file_path.exists():
            return False

        try:
            with open(lock_file_path, "r") as f:
                # Try to acquire and immediately release lock
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(f, fcntl.LOCK_UN)
                return False
        except BlockingIOError:
            return True
        except Exception:
            return False


class PromptCatalog:
    """
    Main interface for prompt management system.

    Provides high-level operations:
    - Prompt creation and loading
    - Automatic versioning
    - Safe concurrent access
    - Basic history tracking
    - Case-insensitive prompt names (stored as lowercase)
    """

    def __init__(self, base_path: Path):
        """
        Initialize prompt management system.

        Args:
            base_path: Base directory for prompt storage
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Initialize subsystems
        self.repo = GitBackedRepository(self.base_path)
        self.access_manager = ConcurrentAccessManager(self.base_path / ".locks")

        logger.info(f"Initialized prompt management system at {base_path}")

    def _normalize_path(self, path: Union[str, Path]) -> Path:
        """
        Normalize a path to be absolute under the repository base path.

        Handles these cases to same result:
        - "my_file" -> <base_path>/my_file
        - "<base_path>/my_file" -> <base_path>/my_file

        Args:
            path: Input path as string or Path

        Returns:
            Path: Absolute path under base_path

        Raises:
            ValueError: If path would resolve outside repository
        """
        path = Path(path)  # ensure we have a path

        # Join with base_path as needed: always interpret relative
        # paths as relative to the repository base path. This avoids
        # incorrectly handling nested relative paths like "a/b"
        # which may not have the same parent as self.base_path.
        if not path.is_absolute():
            path = self.base_path / path

        # Safety check after resolution
        resolved = path.resolve()
        try:
            resolved.relative_to(self.base_path)
        except ValueError as e:
            raise ValueError(
                f"Path {path} resolves outside repository: {self.base_path}"
            ) from e

        return resolved

    def get_path(self, prompt_name: str) -> Optional[Path]:
        """
        Recursively search for a prompt file with the given name (case-insensitive)
        in base_path and all subdirectories.

        Args:
            prompt_name: prompt name (without extension) to search for

        Returns:
            Optional[Path]: Full path to the found prompt file, or None if not found
        """
        target = Prompt._normalize_name(prompt_name)
        with suppress(StopIteration):
            for path in self.base_path.rglob("*.md"):
                if path.is_file() and path.stem.lower() == target:
                    logger.debug(
                        f"Found prompt file for name {prompt_name} at: {path}"
                    )
                    return self._normalize_path(path)
        logger.debug(f"No prompt file found with name: {prompt_name}")
        return None

    def save(self, prompt: Prompt, subdir: Optional[Path] = None) -> Path:
        prompt_name = Prompt._normalize_name(prompt.name)
        instructions = prompt.instructions

        if subdir is None:
            path = self.base_path / f"{prompt_name}.md"
        else:
            path = self.base_path / subdir / f"{prompt_name}.md"

        path = self._normalize_path(path)

        # Check for existing prompt by case-insensitive match
        existing_path = self.get_path(prompt_name)

        try:
            # Lock on the destination path name (lowercase) to avoid races
            with self.access_manager.file_lock(path):
                # If an existing file is present but at a different case/path, rename it
                if existing_path is not None and existing_path != path:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(
                        f"Renaming existing prompt file from {existing_path} to {path} "
                        "to enforce lowercase naming."
                    )
                    existing_path.rename(path)

                write_str_to_file(path, instructions, overwrite=True)
                self.repo.update_file(path)
                logger.info(f"Prompt saved at {path}")
                return path.relative_to(self.base_path)

        except Exception as e:
            logger.error(f"Failed to save prompt {prompt_name}: {e}")
            raise

    def load(self, prompt_name: str) -> Prompt:
        """
        Load the .md prompt file by name, extract placeholders, and
        return a fully constructed Prompt object.

        Args:
            prompt_name: Name of the prompt (without .md extension).

        Returns:
            A new Prompt object whose 'instructions' is the file's text
            and whose 'template_fields' are inferred from placeholders in
            those instructions.
        """
        prompt_name = Prompt._normalize_name(prompt_name)
        # Locate the .md file; raise if missing
        path = self.get_path(prompt_name)
        if not path:
            raise FileNotFoundError(f"No prompt file named {prompt_name}.md found in prompt catalog:\n"
                                    f"{self.base_path}"
                                    )

        # Acquire lock before reading
        with self.access_manager.file_lock(path):
            instructions = read_str_from_file(path)

        instructions = MarkdownStr(instructions)

        # Create the prompt from the raw .md text (name is already lowercase)
        prompt = Prompt(name=prompt_name, instructions=instructions, path=path)

        # Check for local uncommitted changes, updating file:
        self.repo.update_file(path)

        return prompt

    def show_history(self, prompt_name: str) -> None:
        if path := self.get_path(prompt_name):
            self.repo.display_history(path)
        else:
            logger.error(f"Path to {prompt_name} not found.")
            return

    # def get_prompt_history_from_path(self, path: Path) -> List[Dict[str, Any]]:
    #     """
    #     Get version history for a prompt.

    #     Args:
    #         path: Path to prompt file

    #     Returns:
    #         List of version information
    #     """
    #     path = self._normalize_path(path)

    #     return self.repo.get_history(path)

    @classmethod
    def verify_repository(cls, base_path: Path) -> bool:
        """
        Verify repository integrity and uniqueness of prompt names.

        Performs the following checks:
        1. Validates Git repository structure.
        2. Ensures no duplicate prompt names exist.

        Args:
            base_path: Repository path to verify.

        Returns:
            bool: True if the repository is valid 
            and contains no duplicate prompt files.
        """
        try:
            # Check if it's a valid Git repository
            repo = Repo(base_path)

            # Verify basic repository structure
            basic_valid = (
                repo.head.is_valid()
                and not repo.bare
                and (base_path / ".git").is_dir()
                and (base_path / ".locks").is_dir()
            )

            if not basic_valid:
                return False

            prompt_files = list(base_path.rglob("*.md"))
            seen_names: Dict[str, Path] = {}

            for prompt_file in prompt_files:
                # Skip files in .git directory
                if ".git" in prompt_file.parts:
                    continue

                # Case-insensitive key
                key = Prompt._normalize_name(prompt_file.stem)

                if key in seen_names:
                    logger.error(
                        f"Duplicate prompt file detected (case-insensitive):\n"
                        f"  First occurrence: {seen_names[key]}\n"
                        f"  Second occurrence: {prompt_file}"
                    )
                    return False

                seen_names[key] = prompt_file

            return True

        except (InvalidGitRepositoryError, Exception) as e:
            logger.error(f"Repository verification failed: {e}")
            return False
        
class LocalPromptManager:
    """
    A simple singleton implementation of PromptManager that ensures only one instance
    is created and reused throughout the application lifecycle.

    This class wraps the PromptManager to provide efficient prompt loading by
    maintaining a single reusable instance.

    Attributes:
        _instance (Optional[SingletonPromptManager]): The singleton instance
        _prompt_manager (Optional[PromptManager]): The wrapped PromptManager instance
    """

    _instance: Optional["LocalPromptManager"] = None

    def __new__(cls) -> "LocalPromptManager":
        """
        Create or return the singleton instance.

        Returns:
            SingletonPromptManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._prompt_manager = None
        return cls._instance

    @property
    def prompt_manager(self) -> "PromptCatalog":
        """
        Lazy initialization of the PromptManager instance.

        Returns:
            PromptManager: The wrapped PromptManager instance

        Raises:
            RuntimeError: If PATTERN_REPO is not properly configured
        """
        if self._prompt_manager is None:  # type: ignore
            try:
                load_dotenv()
                if prompt_path_name := os.getenv("TNH_PATTERN_DIR"):
                    prompt_dir = Path(prompt_path_name)
                    logger.debug(f"prompt dir: {prompt_path_name}")
                else:
                    prompt_dir = TNH_DEFAULT_PATTERN_DIR
                self._prompt_manager = PromptCatalog(prompt_dir)
            except ImportError as err:
                raise RuntimeError(
                    "Failed to initialize PromptManager. Ensure prompt_manager "
                    f"module and PATTERN_REPO are properly configured: {err}"
                ) from err
        return self._prompt_manager

    def get_prompt(self, name: str) -> Prompt:
        """Get a prompt by name."""
        return self.prompt_manager.load(Prompt._normalize_name(name))
    
    
