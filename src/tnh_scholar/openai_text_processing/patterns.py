from pathlib import Path
from typing import Optional, Dict, List, Any, Union, NamedTuple, Tuple
from datetime import datetime
import yaml
from git import Repo, Actor, Commit
from git.exc import GitCommandError, InvalidGitRepositoryError
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import fcntl
from datetime import datetime, timedelta
import os
import re 
from difflib import unified_diff
from jinja2 import Template, Environment, meta, TemplateError
from tnh_scholar.text_processing import write_text_to_file, get_text_from_file

from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)
        
SYSTEM_UPDATE_MESSAGE = "PatternManager System Update:"

@dataclass
class Pattern:
    """
    Base Pattern class for version-controlled patterns.
    
    Patterns contain:
    - Instructions: The main pattern instructions
    - Metadata: Optional structured data about the pattern
    - Identifiers: Type and classification information
    
    Version control is handled externally through Git, not in the pattern itself.
    pattern identity is determined by the combination of identifiers.
    """
    
    name: str # the name of the pattern
    instructions: str # The markdown string for this pattern
    template_fields: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert pattern to dictionary for YAML serialization.
        
        Returns:
            Dict containing all pattern data in serializable format
        """
        return {
            "name": self.name,
            "instructions": self.instructions,
            "template_fields": self.template_fields,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pattern':
        """
        Create pattern instance from dictionary data.
        
        Args:
            data: Dictionary containing pattern data
            
        Returns:
            New pattern instance
        """
        # Create a copy to avoid modifying input
        data = data.copy()
                    
        return cls(**data)

    def content_hash(self) -> str:
        """
        Generate a hash of the pattern content.
        Useful for quick content comparison and change detection.
        
        Returns:
            str: SHA-256 hash of the pattern content
        """
        instructions_str = str(self.instructions)
        return hashlib.sha256(instructions_str.encode('utf-8')).hexdigest()

    def apply_template(self, field_values: Optional[Dict[str, str]] = None) -> str:
        """
        Apply template values to pattern instructions using Jinja2.

        Args:
            field_values: Dictionary of values to pass into Jinja2.

        Returns:
            str: Rendered instructions with template values applied.

        Raises:
            TemplateError: If template rendering fails.
        """
        if field_values is None:
            field_values = {}

        try:
            # Create a Jinja2 environment
            env = Environment()

            # Parse the instructions to identify required variables
            parsed_content = env.parse(self.instructions)
            required_vars = meta.find_undeclared_variables(parsed_content)

            # Set missing values to empty strings
            for var in required_vars:
                if var not in field_values:
                    field_values[var] = ""

            # Render with provided values
            template = env.from_string(self.instructions)
            return template.render(**field_values)

        except TemplateError as e:
            raise TemplateError(f"Failed to render template: {e}")

class GitBackedRepository:
    """
    Manages versioned storage of patterns using Git.
    
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
                gitignore = repo_path / '.gitignore'
                gitignore.write_text('*.lock\n.DS_Store\n')
                self.repo.index.add(['.gitignore'])
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
            # Check for uncommitted changes
            if not self._is_file_clean(rel_path):
                logger.info(f"Detected changes in {rel_path}, updating version control.")
                self.repo.index.add([str(rel_path)])
                commit = self.repo.index.commit(
                    f"{SYSTEM_UPDATE_MESSAGE} {rel_path.stem}",
                    author=Actor("PatternManager", ""),
                )
                logger.info(f"Committed changes to {file_path}: {commit.hexsha}")
                return commit.hexsha
            else:
                # Return the current commit hash if no changes
                return self.repo.head.commit.hexsha

        except GitCommandError as e:
            logger.error(f"Git operation failed: {e}")
            raise
    
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

    def _get_commit_diff(self, 
                        commit: Commit, 
                        file_path: Path, 
                        prev_commit: Optional[Commit] = None) -> Tuple[str, str]:
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
            stat = self.repo.git.diff(
                prev_hash,
                commit.hexsha,
                rel_path,
                stat=True
            )
            
            # Get detailed diff
            diff = self.repo.git.diff(
                prev_hash,
                commit.hexsha,
                rel_path,
                unified=2,
                word_diff='plain',
                color='always',
                ignore_space_change=True
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
            max_versions: Maximum number of versions to show, if zero, shows all revisions.
            
        Example:
            >>> repo.display_history(Path("patterns/format_dharma_talk.yaml"))
            Commit abc123def (2024-12-28 14:30:22):
            1 file changed, 5 insertions(+), 2 deletions(-)
            
            diff --git a/patterns/format_dharma_talk.yaml ...
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
                    commit, 
                    file_path, 
                    prev_commit
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
            [item.a_path for item in self.repo.index.diff(None)] +
            self.repo.untracked_files
        )

class ConcurrentAccessManager:
    """
    Manages concurrent access to pattern files.
    
    Provides:
    - File-level locking
    - Safe concurrent access patterns
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
    def file_lock(self, file_path: Path):
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
                
            except BlockingIOError:
                raise RuntimeError(f"File {file_path} is locked by another process")
                
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
            with open(lock_file_path, 'r') as f:
                # Try to acquire and immediately release lock
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(f, fcntl.LOCK_UN)
                return False
        except BlockingIOError:
            return True
        except Exception:
            return False

class PatternManager:
    """
    Main interface for pattern management system.
    
    Provides high-level operations:
    - Pattern creation and loading
    - Automatic versioning
    - Safe concurrent access
    - Basic history tracking
    """
        
    def __init__(self, base_path: Path):
        """
        Initialize pattern management system.

        Args:
            base_path: Base directory for pattern storage
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize subsystems
        self.repo = GitBackedRepository(self.base_path)
        self.access_manager = ConcurrentAccessManager(self.base_path / '.locks')
        
        logger.info(f"Initialized pattern management system at {base_path}")
        
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
        
        if not path.is_absolute():
            if path.parent == self.base_path:
                # Path already has base_path as parent
                path = path
            else:
                # Join with base_path
                path = self.base_path / path
                
        # Safety check after resolution
        resolved = path.resolve()
        if not resolved.is_relative_to(self.base_path):
            raise ValueError(f"Path {path} resolves outside repository: {self.base_path}")
            
        return resolved
        
    def get_pattern_path(self, pattern_name: str) -> Optional[Path]:
        """
        Recursively search for a pattern file with the given name in base_path and all subdirectories.
        
        Args:
            ptrn_id: pattern identifier to search for
            
        Returns:
            Optional[Path]: Full path to the found pattern file, or None if not found
        """
        pattern = f"{pattern_name}.md"
        
        try:
            pattern_path = next(
                path for path in self.base_path.rglob(pattern)
                if path.is_file()
            )
            logger.debug(f"Found pattern file for ID {pattern_name} at: {pattern_path}")
            return self._normalize_path(pattern_path)
            
        except StopIteration:
            logger.debug(f"No pattern file found with ID: {pattern_name}")
            return None

    def save_pattern(self, pattern: Pattern, subdir: Optional[Path] = None):
        
        pattern_name = pattern.name 
        instructions = pattern.instructions
        
        if subdir is None:
            path = self.base_path / f"{pattern_name}.md"
        else:
            path = self.base_path / subdir / f"{pattern_name}.md"
            
        path = self._normalize_path(path)
        
        # Check for existing pattern with same ID
        existing_path = self.get_pattern_path(pattern_name)
            
        if existing_path is not None:
            if path != existing_path:
                error_msg = (
                    f"Existing pattern - {pattern_name} already exists at "
                    f"{existing_path.relative_to(self.base_path)}. "
                    f"Attempted to accecss at location: {path.relative_to(self.base_path)}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
                path = existing_path
                
        try:
            with self.access_manager.file_lock(path):
                write_text_to_file(path, instructions, overwrite=True)
                self.repo.update_file(path)
                logger.info(f"Pattern saved at {path}")
                return path.relative_to(self.base_path)
                    
        except Exception as e:
            logger.error(f"Failed to save pattern {pattern.name}: {e}")
            raise     
    
    def load_pattern(self, pattern_name: str) -> Pattern:
        """
        Load the .md pattern file by name, extract placeholders, and 
        return a fully constructed Pattern object.
        
        Args:
            pattern_name: Name of the pattern (without .md extension).
        
        Returns:
            A new Pattern object whose 'instructions' is the file's text
            and whose 'template_fields' are inferred from placeholders in
            those instructions.
        """
        # Locate the .md file; raise if missing
        path = self.get_pattern_path(pattern_name)
        if not path:
            raise FileNotFoundError(f"No pattern file named {pattern_name}.md found.")

        # Acquire lock before reading
        with self.access_manager.file_lock(path):
            instructions = get_text_from_file(path)

        # Create the pattern from the raw .md text
        pattern = Pattern(name=pattern_name, instructions=instructions)

        # Check for local uncommitted changes, updating file:
        self.repo.update_file(path)

        return pattern
    
    def show_pattern_history(self, pattern_name: str):
        path = self.get_pattern_path(pattern_name)
        
        self.repo.display_history(path)
    
    # def get_pattern_history_from_path(self, path: Path) -> List[Dict[str, Any]]:
    #     """
    #     Get version history for a pattern.
        
    #     Args:
    #         path: Path to pattern file
            
    #     Returns:
    #         List of version information
    #     """
    #     path = self._normalize_path(path)
            
    #     return self.repo.get_history(path)

    @classmethod
    def verify_repository(cls, base_path: Path) -> bool:
        """
        Verify repository integrity and uniqueness of pattern names.

        Performs the following checks:
        1. Validates Git repository structure.
        2. Ensures no duplicate pattern names exist.

        Args:
            base_path: Repository path to verify.

        Returns:
            bool: True if the repository is valid and contains no duplicate pattern files.
        """
        try:
            # Check if it's a valid Git repository
            repo = Repo(base_path)

            # Verify basic repository structure
            basic_valid = (
                repo.head.is_valid() and
                not repo.bare and
                (base_path / '.git').is_dir() and
                (base_path / '.locks').is_dir()
            )

            if not basic_valid:
                return False

            # Check for duplicate pattern names
            pattern_files = list(base_path.rglob('*.md'))
            seen_names = {}

            for pattern_file in pattern_files:
                # Skip files in .git directory
                if '.git' in pattern_file.parts:
                    continue

                # Get pattern name from the filename (without extension)
                pattern_name = pattern_file.stem

                if pattern_name in seen_names:
                    logger.error(
                        f"Duplicate pattern file detected:\n"
                        f"  First occurrence: {seen_names[pattern_name]}\n"
                        f"  Second occurrence: {pattern_file}"
                    )
                    return False

                seen_names[pattern_name] = pattern_file

            return True

        except (InvalidGitRepositoryError, Exception) as e:
            logger.error(f"Repository verification failed: {e}")
            return False
        
# old / reference code
# def _get_file_content_at_commit(self, rel_path: Path, commit_hash: str) -> Optional[Dict]:
#         """
#         Get the file content at a specific commit.
        
#         Args:
#             rel_path: File path relative to repository root
#             commit_hash: Commit hash to retrieve content from
            
#         Returns:
#             Dict containing the file content if successful, None otherwise
#         """
#         try:
#             # Use relative path for git show command
#             content = self.repo.git.show(f"{commit_hash}:{rel_path}")
#             return yaml.safe_load(content)
#         except Exception as e:
#             logger.debug(f"Could not get content at {commit_hash}: {e}")
#             return None
        
#     def _calculate_meaningful_diff(self, prev_content: Dict, current_content: Dict) -> CommitDiff:
#         """
#         Calculate a meaningful diff between two pattern versions.
        
#         Args:
#             prev_content: Previous version content
#             current_content: Current version content
            
#         Returns:
#             CommitDiff containing structured difference information
#         """
#         additions = []
#         deletions = []
#         modified = []
        
#         # Compare top-level fields
#         all_keys = set(prev_content.keys()) | set(current_content.keys())
        
#         for key in all_keys:
#             prev_val = prev_content.get(key)
#             curr_val = current_content.get(key)
            
#             if key not in prev_content:
#                 additions.append(f"{key}: {curr_val}")
#             elif key not in current_content:
#                 deletions.append(f"{key}: {prev_val}")
#             elif prev_val != curr_val:
#                 # # Special handling for nested structures
#                 # if isinstance(prev_val, dict) and isinstance(curr_val, dict):
#                 #     modified.append(f"{key}: dictionary modified")
#                 # elif isinstance(prev_val, list) and isinstance(curr_val, list):
#                 #     modified.append(f"{key}: list modified")
#                 # else:
#                 modified.append(f"{key}: {prev_val} → {curr_val}")
        
#         return CommitDiff(additions=additions, deletions=deletions, modified=modified)

# def save_pattern(self, pattern: Pattern, dir: Optional[Path] = None) -> Path:
    #     """
    #     Save and version a pattern. Prevents duplicate pattern IDs across repository.
        
    #     Args:
    #         pattern: Pattern to save
    #         path: Optional specific path to save to
                
    #     Returns:
    #         Path: Relative path where pattern was saved (relative to base_path)
                
    #     Raises:
    #         RuntimeError: If file is locked
    #         GitCommandError: If versioning fails
    #         ValueError: If attempting to save pattern with duplicate ID at different location
    #     """
        
    #     if dir is None:
    #         path = self.base_path / f"{pattern.ptrn_id}.yaml"
    #     else:
    #         path = self.base_path / dir / f"{pattern.ptrn_id}.yaml"
                
    #     # Check for existing pattern with same ID
    #     existing_path = self.get_pattern_path(pattern.ptrn_id)
        
    #     if existing_path is not None:
    #         if path != existing_path:
    #             error_msg = (
    #                 f"Existing pattern - ID {pattern.ptrn_id} already exists at "
    #                 f"{existing_path.relative_to(self.base_path)}. "
    #                 f"Attempted to accecss at location: {path.relative_to(self.base_path)}"
    #             )
    #             logger.error(error_msg)
    #             raise ValueError(error_msg)
    #             path = existing_path

    #     try:
    #         with self.access_manager.file_lock(path):
    #             self.repo.track_pattern(pattern, path)
    #             logger.info(f"Pattern saved at {path}")
    #             return path.relative_to(self.base_path)
                    
    #     except Exception as e:
    #         logger.error(f"Failed to save pattern {pattern.ptrn_id}: {e}")
    #         raise
    
        # def track_file(self, file_path: Path):
    #     """
    #     Track changes to a file in the Git repository.

    #     Args:
    #         file_path: Absolute or relative path to the file.

    #     Returns:
    #         str: Commit hash if changes were made.

    #     Raises:
    #         FileNotFoundError: If the file does not exist.
    #         ValueError: If the file is outside the repository.
    #         GitCommandError: If Git operations fail.
    #     """
    #     file_path = Path(file_path).resolve()  # Ensure we are working with absolute paths

    #     # Ensure file is within the repository
    #     try:
    #         rel_path = file_path.relative_to(self.repo_path)  # Relative path within repo
    #     except ValueError:
    #         logger.error(f"File {file_path} is outside the repository root {self.repo_path}")
    #         raise ValueError(f"File {file_path} is not under the repository root {self.repo_path}")

    #     if not file_path.exists():
    #         logger.error(f"File to track not found: {file_path}")
    #         raise FileNotFoundError(f"File does not exist: {file_path}")

    #     try:
    #         # Check if file has uncommitted changes
    #         if not self._is_file_clean(rel_path):
    #             # Stage and commit changes
    #             self.repo.index.add([str(rel_path)])
    #             commit = self.repo.index.commit(
    #                 f"Update pattern {rel_path.stem}",
    #                 author=Actor("patternManager", "patternManager@example.com")
    #             )
    #             logger.info(f"Committed changes to {file_path}: {commit.hexsha}")
    #             return commit.hexsha

    #         # Return the current commit hash if no changes
    #         return self.repo.head.commit.hexsha

    #     except GitCommandError as e:
    #         logger.error(f"Git operation failed: {e}")
    #         raise