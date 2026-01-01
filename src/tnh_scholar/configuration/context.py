"""Runtime context discovery and path resolution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from importlib import resources
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from platformdirs import user_config_dir

from tnh_scholar.exceptions import ConfigurationError


class RegistryCategory(StrEnum):
    """Registry category for path resolution."""

    PROVIDERS = "providers"
    OVERRIDES = "overrides"


@dataclass(frozen=True)
class WorkspaceDiscoveryPolicy:
    """Policy for workspace discovery."""

    markers: tuple[str, ...]
    stop_dir: Path

    @classmethod
    def default(cls) -> "WorkspaceDiscoveryPolicy":
        return cls(markers=(".tnh-scholar", ".git"), stop_dir=Path.home())


class WorkspaceLocator:
    """Locates a workspace root by walking upward."""

    def __init__(self, policy: WorkspaceDiscoveryPolicy) -> None:
        self._policy = policy

    def find(self, start_path: Path) -> Path | None:
        current = start_path.resolve()
        for candidate in self._walk_up(current):
            if self._has_marker(candidate):
                return candidate
            if candidate == self._policy.stop_dir:
                return None
        return None

    def _walk_up(self, start: Path) -> Iterable[Path]:
        current = start
        while True:
            yield current
            if current.parent == current:
                break
            current = current.parent

    def _has_marker(self, path: Path) -> bool:
        return any((path / marker).exists() for marker in self._policy.markers)


class BuiltinRootLocator:
    """Resolves the built-in runtime_assets root."""

    def resolve(self) -> Path:
        package_root = Path(str(resources.files("tnh_scholar")))
        runtime_assets = package_root / "runtime_assets"
        if not runtime_assets.exists():
            raise ConfigurationError("runtime_assets directory not found in package")
        return runtime_assets


class UserRootLocator:
    """Resolves the user configuration root."""

    def resolve(self) -> Path:
        return Path(user_config_dir("tnh-scholar"))


class ContextIdFactory:
    """Generates correlation and session identifiers."""

    def build(self, correlation_id: str | None, session_id: str | None) -> tuple[str, str]:
        return (
            correlation_id or str(uuid4()),
            session_id or str(uuid4()),
        )


@dataclass(frozen=True)
class TNHContext:
    """Resolved runtime context for TNH Scholar."""

    builtin_root: Path
    workspace_root: Path | None
    user_root: Path
    correlation_id: str
    session_id: str

    @classmethod
    def discover(
        cls,
        *,
        workspace_root: Path | None = None,
        user_root: Path | None = None,
        correlation_id: str | None = None,
        session_id: str | None = None,
        start_path: Path | None = None,
    ) -> "TNHContext":
        workspace = workspace_root or cls._discover_workspace(start_path)
        builtin_root = BuiltinRootLocator().resolve()
        user_root = user_root or UserRootLocator().resolve()
        correlation_id, session_id = ContextIdFactory().build(correlation_id, session_id)
        return cls(
            builtin_root=builtin_root,
            workspace_root=workspace,
            user_root=user_root,
            correlation_id=correlation_id,
            session_id=session_id,
        )

    def get_registry_search_paths(self, registry_type: str) -> list[Path]:
        category = RegistryCategory(registry_type)
        return RegistryPathBuilder(self).build(category)

    @classmethod
    def _discover_workspace(cls, start_path: Path | None) -> Path | None:
        start = start_path or Path.cwd()
        policy = WorkspaceDiscoveryPolicy.default()
        return WorkspaceLocator(policy).find(start)


class RegistryPathBuilder:
    """Builds registry search paths for a context."""

    def __init__(self, context: TNHContext) -> None:
        self._context = context

    def build(self, category: RegistryCategory) -> list[Path]:
        paths = []
        if self._context.workspace_root:
            paths.append(self._workspace_path(category))
        paths.extend((self._user_path(category), self._builtin_path(category)))
        return paths

    def _workspace_path(self, category: RegistryCategory) -> Path:
        return self._context.workspace_root / "registries" / category.value

    def _user_path(self, category: RegistryCategory) -> Path:
        return self._context.user_root / "registries" / category.value

    def _builtin_path(self, category: RegistryCategory) -> Path:
        return self._context.builtin_root / "registries" / category.value
