"""Per-invocation sink selection and path validation."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RunStatusConfig(BaseModel):
    """Configuration resolved once, independently of service configuration."""

    model_config = ConfigDict(frozen=True)
    status_file: Path | None = None
    interactive: bool = False
    no_color: bool = False
    heartbeat_seconds: float = Field(default=4.0, gt=0, allow_inf_nan=False)

    @classmethod
    def resolve(
        cls, *, status_file: Path | None, api: bool, quiet: bool, is_tty: bool, no_color: bool
    ) -> "RunStatusConfig":
        """Preserve explicit machine artifacts in quiet/API mode."""
        return cls(status_file=status_file, interactive=is_tty and not api and not quiet, no_color=no_color)

    def validate_paths(self, protected_paths: tuple[Path | None, ...]) -> None:
        """Reject aliases before creating a status file or invoking the service."""
        if self.status_file is None:
            return
        destination = self.status_file.resolve()
        if any(path is not None and path.resolve() == destination for path in protected_paths):
            raise ValueError("Status file must differ from input, config, and output paths")
        if self.status_file.exists() or self.status_file.is_symlink():
            raise ValueError("Status file already exists; choose a fresh path")
        if not self.status_file.parent.is_dir():
            raise ValueError("Status file parent directory must already exist")
