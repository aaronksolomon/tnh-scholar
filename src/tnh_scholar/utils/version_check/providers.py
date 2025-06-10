"""Version provider implementations for retrieving package versions."""

import importlib.metadata
from abc import ABC, abstractmethod
from typing import Optional

import requests
from packaging.version import InvalidVersion, Version

from .cache import VersionCache


class VersionProvider(ABC):
    """Interface for retrieving package version information."""
    
    @abstractmethod
    def get_installed_version(self, package_name: str) -> Version:
        """Get installed package version."""
        pass
        
    @abstractmethod
    def get_latest_version(self, package_name: str) -> Version:
        """Get latest available package version."""
        pass


class StandardVersionProvider(VersionProvider):
    """Standard implementation of version provider using importlib and PyPI."""
    
    def __init__(self, cache: Optional[VersionCache] = None, timeout: int = 5):
        self.cache = cache or VersionCache()
        self.timeout = timeout
        self.pypi_url_template = "https://pypi.org/pypi/{package}/json"
        
    def get_installed_version(self, package_name: str) -> Version:
        """Get installed package version."""
        try:
            if version_str := str(importlib.metadata.version(package_name)):
                return Version(version_str)
            else:
                raise InvalidVersion(f"{package_name} version string is empty")
        except importlib.metadata.PackageNotFoundError as e:
            raise ImportError(f"{package_name} is not installed") from e
        except InvalidVersion as e:
            raise InvalidVersion(f"Invalid version for {package_name}: {e}") from e
            
    def get_latest_version(self, package_name: str) -> Version:
        """Get latest available package version from PyPI."""
        # Check cache first
        if cached_version := self.cache.get(f"{package_name}_latest"):
            return cached_version

        # Fetch from PyPI
        url = self.pypi_url_template.format(package=package_name)
        try:
            return self._send_url_request(url, package_name)
        except requests.RequestException as e:
            raise requests.RequestException(
                f"Failed to fetch {package_name} version from PyPI: {e}"
            ) from e

    def _send_url_request(self, url, package_name):
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        version_str = response.json()["info"]["version"]
        version = Version(version_str)

        # Cache the result
        self.cache.set(f"{package_name}_latest", version)

        return version