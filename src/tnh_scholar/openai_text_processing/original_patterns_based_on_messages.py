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

from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)

class ContentType(Enum):
    """Enumeration of content types for pattern classification."""
    DHARMA_TALK = "dharma_talk"
    CHAPTER = "chapter"
    BOOK = "book"
    NEWSLETTER = "newsletter"
    LINE_TRANSLATION = "line_translation"
    LINE_TRANSCRIPTION = "line_transcription"
    ARTICLE = "article"
    DEFAULT = "default"
    
class TaskType(Enum):
    """Enumeration of task types for pattern processing."""
    TRANSLATE = "translate"
    SECTION = "section" 
    SUMMARIZE = "summarize"
    FORMAT = "format"
    ANALYZE = "analyze"
    GENERATE = "generate"
    PROCESS = "process"
    DEFAULT = "default"

# structures for commit info and history
class CommitDiff(NamedTuple):
        """Structured format for commit differences."""
        additions: List[str]
        deletions: List[str]
        modified: List[str]

class HistoryEntry(NamedTuple):
        """Structured format for a single history entry."""
        hash: str
        date: datetime
        pattern: str
        diff: Optional[CommitDiff] = None
        
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
    task_type: TaskType
    content_type: ContentType
    instructions: str
    input_language: str = "multi"
    keyword: str = "default"
    template_fields: Dict[str, str] = field(default_factory=dict)
    
    def _validate_template_fields(self):
        # Validate template fields
        actual_fields = set(re.findall(r'{{(\w+)}}', self.instructions))
        declared_fields = set(self.template_fields.keys())
        if actual_fields != declared_fields:
            raise ValueError(
                f"Template fields mismatch:\n"
                f"Extra declared fields: {declared_fields - actual_fields}\n"
                f"Undeclared used fields: {actual_fields - declared_fields}"
            )

    def __post_init__(self):
        """Validate and process fields after initialization."""
        # Ensure enums are properly set
        if isinstance(self.task_type, str):
            self.task_type = TaskType(self.task_type)
        if isinstance(self.content_type, str):
            self.content_type = ContentType(self.content_type)
        
        # Validate template fields:
        self._validate_template_fields()
    
    @staticmethod    
    def ptrn_id_from_dict(dict):
        ptrn_id = f"{dict.get('task_type')}_{dict.get('content_type')}_{dict.get('input_language')}_{dict.get('keyword')}"
        return ptrn_id
        
    @property
    def ptrn_id(self) -> str:
        """
        Generate a unique identifier for the pattern based on its key attributes.
        Format: {task_type}_{content_type}_{input_language}_{keyword}
        """
        return f"{self.task_type.value}_{self.content_type.value}_{self.input_language}_{self.keyword}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert pattern to dictionary for YAML serialization.
        
        Returns:
            Dict containing all pattern data in serializable format
        """
        return {
            "task_type": self.task_type.value,
            "content_type": self.content_type.value,
            "instructions": self.instructions,
            "input_language": self.input_language,
            "keyword": self.keyword,
            "template_fields": self.template_fields,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'pattern':
        """
        Create pattern instance from dictionary data.
        
        Args:
            data: Dictionary containing pattern data
            
        Returns:
            New pattern instance
        """
        # Create a copy to avoid modifying input
        data = data.copy()
        
        # Convert string representations to enums if needed
        if isinstance(data.get('task_type'), str):
            data['task_type'] = TaskType(data['task_type'])
        if isinstance(data.get('content_type'), str):
            data['content_type'] = ContentType(data['content_type'])
            
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
            field_values: Optional dictionary of field values to override defaults

        Returns:
            str: Rendered instructions with template values applied

        Raises:
            TemplateError: If template rendering fails
            ValueError: If required template variables are missing
        """
        # Start with default template values
        values = self.template_fields.copy()
        
        # Override with provided values if any
        if field_values:
            values.update(field_values)

        try:
            # Create template from instructions
            template = Template(self.instructions)
            
            # Get required variables from template
            required_vars = meta.find_undeclared_variables(template.environment.parse(self.instructions))
            
            # Check for missing required variables
            missing_vars = required_vars - set(values.keys())
            if missing_vars:
                raise ValueError(f"Missing required template variables: {missing_vars}")
                
            # Render template with values
            return template.render(**values)
            
        except TemplateError as e:
            raise TemplateError(f"Failed to render template: {str(e)}")


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
                
    def track_file(self, file_path: Path):
        """
        Track changes to a file
        
        Args:
            file_path: Path to the file.
            
        Returns:
            str: Commit hash if changes were made
            
        Raises:
            GitCommandError: If Git operations fail
        """
        file_path = Path(file_path)
        
        rel_path = file_path.relative_to(self.repo_path).resolve()
        
        if not rel_path.exists():
            raise FileNotFoundError()
        
        try:
            # Check if file has changed
            if not self._is_file_clean(rel_path):
                # Stage and commit changes
                self.repo.index.add([str(rel_path)])
                commit = self.repo.index.commit(
                    f"Update pattern {pattern.ptrn_id}",
                    author=Actor("patternManager", "")
                )
                logger.info(f"Committed changes to {rel_path}: {commit.hexsha}")
                return commit.hexsha
            
            # Return current commit hash if no changes
            return self.repo.head.commit.hexsha
            
        except GitCommandError as e:
            logger.error(f"Git operation failed: {e}")
            raise

    def track_pattern(self, pattern: Pattern, file_path: Path) -> str:
        """
        Track changes to a pattern file.
        
        Args:
            pattern: pattern to track
            file_path: Path where pattern is stored
            
        Returns:
            str: Commit hash if changes were made
            
        Raises:
            GitCommandError: If Git operations fail
        """
        file_path = Path(file_path)
        rel_path = file_path.relative_to(self.repo_path)
        
        # Write pattern to file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            yaml.safe_dump(pattern.to_dict(), f)
            
        try:
            # Check if file has changed
            if not self._is_file_clean(rel_path):
                # Stage and commit changes
                self.repo.index.add([str(rel_path)])
                commit = self.repo.index.commit(
                    f"Update pattern {pattern.ptrn_id}",
                    author=Actor("patternManager", "")
                )
                logger.info(f"Committed changes to {rel_path}: {commit.hexsha}")
                return commit.hexsha
            
            # Return current commit hash if no changes
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

    def display_history(self, file_path: Path, max_versions: int = 3) -> None:
        """
        Display history of changes for a file with diffs between versions.
        
        Shows most recent changes first, limited to max_versions entries.
        For each change shows:
        - Commit info and date
        - Stats summary of changes
        - Detailed color diff with 2 lines of context
        
        Args:
            file_path: Path to file in repository
            max_versions: Maximum number of versions to show, defaults to 3
            
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
                
            # Display limited history with diffs
            for i, commit in enumerate(commits[:max_versions]):
                # Print commit header
                date_str = commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                print(f"\nCommit {commit.hexsha[:8]} ({date_str}):")
                print(f"pattern: {commit.pattern.strip()}")
                
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
                
                print("-" * 80)  # Visual separator between commits
                
        except Exception as e:
            logger.error(f"Failed to display history for {file_path}: {e}")
            print(f"Error displaying history: {e}")
            
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
        
    def get_pattern_path(self, ptrn_id: str) -> Optional[Path]:
        """
        Recursively search for a pattern file with the given ID in base_path and all subdirectories.
        
        Args:
            ptrn_id: pattern identifier to search for
            
        Returns:
            Optional[Path]: Full path to the found pattern file, or None if not found
        """
        pattern = f"{ptrn_id}.yaml"
        
        try:
            pattern_path = next(
                path for path in self.base_path.rglob(pattern)
                if path.is_file()
            )
            logger.debug(f"Found pattern file for ID {ptrn_id} at: {pattern_path}")
            return self._normalize_path(pattern_path)
            
        except StopIteration:
            logger.debug(f"No pattern file found with ID: {ptrn_id}")
            return None

    def save_pattern_md(self, ptrn_id, instructions: str, dir: Optional[Path] = None):
        if dir is None:
            path = self.base_path / f"{pattern.ptrn_id}.md"
        else:
            path = self.base_path / dir / f"{pattern.ptrn_id}.md"
            
        
    def save_pattern(self, pattern: Pattern, dir: Optional[Path] = None) -> Path:
        """
        Save and version a pattern. Prevents duplicate pattern IDs across repository.
        
        Args:
            pattern: Pattern to save
            path: Optional specific path to save to
                
        Returns:
            Path: Relative path where pattern was saved (relative to base_path)
                
        Raises:
            RuntimeError: If file is locked
            GitCommandError: If versioning fails
            ValueError: If attempting to save pattern with duplicate ID at different location
        """
        
        if dir is None:
            path = self.base_path / f"{pattern.ptrn_id}.yaml"
        else:
            path = self.base_path / dir / f"{pattern.ptrn_id}.yaml"
                
        # Check for existing pattern with same ID
        existing_path = self.get_pattern_path(pattern.ptrn_id)
        
        if existing_path is not None:
            if path != existing_path:
                error_msg = (
                    f"Existing pattern - ID {pattern.ptrn_id} already exists at "
                    f"{existing_path.relative_to(self.base_path)}. "
                    f"Attempted to accecss at location: {path.relative_to(self.base_path)}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
                path = existing_path

        try:
            with self.access_manager.file_lock(path):
                self.repo.track_pattern(pattern, path)
                logger.info(f"Pattern saved at {path}")
                return path.relative_to(self.base_path)
                    
        except Exception as e:
            logger.error(f"Failed to save pattern {pattern.ptrn_id}: {e}")
            raise
    
    def load_pattern(self, ptrn_id: str) -> Pattern:
        """
        Load a pattern by its pattern ID.
        
        This method searches for a pattern file matching the provided pattern ID 
        within the base directory. The method assumes pattern files follow the 
        naming convention: {ptrn_id}.yaml
        
        Args:
            ptrn_id: The pattern ID to search for
                Format: {task_type}_{content_type}_{input_language}_{keyword}
                
        Returns:
            pattern: The loaded pattern object
            
        Raises:
            FileNotFoundError: If no matching pattern file is found
            RuntimeError: If file access is locked
            yaml.YAMLError: If the pattern file is invalid YAML
            ValueError: If multiple matching files are found (should not occur in normal operation)
            
        Example:
            >>> manager = PatternManager(Path("./patterns"))
            >>> msg = manager.load_pattern_by_id("translate_article_vi_default")
        """
        path = self.get_pattern_path(ptrn_id)
            
        # Load the single matching file
        return self.load_pattern_from_path(path)
    
    def load_pattern_md_from_path(self, path) -> Str:
        pass
    
    def load_pattern_from_path(self, path: Path) -> Pattern:
        """
        Load a pattern from file and ensure version control is up to date.
        
        Args:
            path: Path to pattern file
            
        Returns:
            Loaded pattern
            
        Raises:
            FileNotFoundError: If pattern file doesn't exist
            RuntimeError: If file is locked
            yaml.YAMLError: If file is invalid
        """
        try:
            path = self._normalize_path(path)
            with self.access_manager.file_lock(path):
                # First load the pattern from disk
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                pattern = Pattern.from_dict(data)
                
                # Check if file has changes relative to Git
                if not self.repo._is_file_clean(path.relative_to(self.base_path)):
                    logger.info(f"Detected changes in {path}, updating version control")
                    # Track changes in Git
                    commit_hash = self.repo.track_pattern(pattern, path)
                    logger.info(f"Updated version control for {path}, new commit: {commit_hash}")
                
                return pattern
                    
        except FileNotFoundError:
            logger.error(f"Pattern file not found: {path}")
            raise
        except Exception as e:
            logger.error(f"Failed to load pattern from {path}: {e}")
            raise
    
    def get_pattern_history(self, ptrn_id: str):
        path = self.get_pattern_path(ptrn_id)
        
        return self.get_pattern_history_from_path(path)
        
    def get_pattern_history_from_path(self, path: Path) -> List[Dict[str, Any]]:
        """
        Get version history for a pattern.
        
        Args:
            path: Path to pattern file
            
        Returns:
            List of version information
        """
        path = self._normalize_path(path)
            
        return self.repo.get_history(path)

    @classmethod
    def verify_repository(cls, base_path: Path) -> bool:
        """
        Verify repository integrity and pattern uniqueness.
        
        Performs the following checks:
        1. Validates Git repository structure
        2. Ensures no duplicate pattern IDs exist across different directories
        3. Ensures that all pattern yaml file names (based on the unique pattern id) match the info stored in the file. 
        
        Args:
            base_path: Repository path to verify
                
        Returns:
            bool: True if repository is valid and contains no duplicate pattern IDs
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
                
            # Check for duplicate pattern IDs and filename consistency
            ptrn_ids = {}  # Dict to store {ptrn_id: file_path}
            
            # Recursively find all YAML files
            for yaml_file in base_path.rglob('*.yaml'):
                try:
                    # Skip files in .git directory
                    if '.git' in yaml_file.parts:
                        continue
                        
                    # Load pattern to get its ID
                    with open(yaml_file, 'r') as f:
                        data = yaml.safe_load(f)
                        if not data:
                            logger.warning(f"Empty or invalid YAML file: {yaml_file}")
                            continue
                            
                        # Reconstruct pattern ID from data
                        ptrn_id = Pattern.ptrn_id_from_dict(data)
                        
                        # Check that filename matches pattern ID
                        expected_filename = f"{ptrn_id}.yaml"
                        if yaml_file.name != expected_filename:
                            logger.error(
                                f"Filename does not match pattern ID in {yaml_file}:\n"
                                f"  Expected: {expected_filename}\n"
                                f"  Found: {yaml_file.name}"
                            )
                            return False
                        
                        # Check for duplicate
                        if ptrn_id in ptrn_ids:
                            logger.error(
                                f"Duplicate pattern ID '{ptrn_id}' found:\n"
                                f"  First occurrence: {ptrn_ids[ptrn_id]}\n"
                                f"  Second occurrence: {yaml_file}"
                            )
                            return False
                            
                        ptrn_ids[ptrn_id] = yaml_file
                        
                except (yaml.YAMLError, KeyError) as e:
                    logger.error(f"Error processing {yaml_file}: {e}")
                    return False
                    
            return True
            
        except (InvalidGitRepositoryError, Exception) as e:
            logger.error(f"Repository verification failed: {e}")
            return False
        
        
# reference code
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