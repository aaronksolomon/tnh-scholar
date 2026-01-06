import importlib.metadata
from typing import Tuple

import requests
from packaging.version import InvalidVersion, Version

from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)


class YTDVersionChecker:
    """
    Simple version checker for yt-dlp with robust version comparison.

    This is a prototype implementation may need expansion in these areas:
    - Caching to prevent frequent PyPI calls
    - More comprehensive error handling for:
        - Missing/uninstalled packages
        - Network timeouts
        - JSON parsing errors
        - Invalid version strings
    - Environment detection (virtualenv, conda, system Python)
    - Configuration options for version pinning
    - Proxy support for network requests
    """

    PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"
    NETWORK_TIMEOUT = 5  # seconds

    def _get_installed_version(self) -> Version:
        """
        Get installed yt-dlp version.

        Returns:
            Version object representing installed version

        Raises:
            ImportError: If yt-dlp is not installed
            InvalidVersion: If installed version string is invalid
        """
        try:
            if version_str := str(importlib.metadata.version("yt-dlp")):
                return Version(version_str)
            else:
                raise InvalidVersion("yt-dlp version string is empty")
        except importlib.metadata.PackageNotFoundError as e:
            raise ImportError("yt-dlp is not installed") from e
        except InvalidVersion:
            raise

    def _get_latest_version(self) -> Version:
        """
        Get latest version from PyPI.

        Returns:
            Version object representing latest available version

        Raises:
            requests.RequestException: For any network-related errors
            InvalidVersion: If PyPI version string is invalid
            KeyError: If PyPI response JSON is malformed
        """
        try:
            response = requests.get(self.PYPI_URL, timeout=self.NETWORK_TIMEOUT)
            response.raise_for_status()
            version_str = response.json()["info"]["version"]
            return Version(version_str)
        except requests.RequestException as e:
            raise requests.RequestException(
                "Failed to fetch version from PyPI. Check network connection."
            ) from e

    def check_version(self) -> Tuple[bool, Version, Version]:
        """
        Check if yt-dlp needs updating.

        Returns:
            Tuple of (needs_update, installed_version, latest_version)

        Raises:
            ImportError: If yt-dlp is not installed
            requests.RequestException: For network-related errors
            InvalidVersion: If version strings are invalid
        """
        installed_version = self._get_installed_version()
        latest_version = self._get_latest_version()

        needs_update = installed_version < latest_version
        return needs_update, installed_version, latest_version


def check_ytd_version() -> bool:
    """
    Check if yt-dlp is up to date and available.

    This function checks the installed version of yt-dlp against the latest version
    on PyPI. Since YouTube changes frequently break older yt-dlp versions, this
    check is strict and requires the latest version.

    Returns:
        bool: True if yt-dlp is installed and up to date, False otherwise.

    Note:
        This is a strict check. Outdated versions return False to prevent
        wasting time on long-running jobs that will likely fail due to
        YouTube API changes.
    """
    checker = YTDVersionChecker()
    try:
        needs_update, current, latest = checker.check_version()
        if needs_update:
            logger.error(f"yt-dlp is outdated: {current} (latest: {latest})")
            logger.error("YouTube downloads require the latest yt-dlp version.")
            logger.error("Update with: poetry update yt-dlp")
            logger.error("Or run: make build-all")
            return False  # Fail fast - don't waste time on outdated version
        else:
            logger.info(f"yt-dlp is up to date (version {current})")
            return True

    except ImportError as e:
        logger.error(f"yt-dlp is not installed: {e}")
        logger.error("Install with: poetry install")
        return False  # Cannot proceed without yt-dlp
    except requests.RequestException as e:
        logger.error(f"Could not check yt-dlp version (network error): {e}")
        logger.error("Cannot verify yt-dlp is up to date. Refusing to proceed.")
        return False  # Fail safe - don't run without version confirmation
    except InvalidVersion as e:
        logger.error(f"Could not parse yt-dlp version: {e}")
        logger.error("Cannot verify yt-dlp is up to date. Refusing to proceed.")
        return False  # Fail safe
    except Exception as e:
        logger.error(f"Unexpected error checking yt-dlp version: {e}")
        logger.error("Cannot verify yt-dlp is up to date. Refusing to proceed.")
        return False  # Fail safe
