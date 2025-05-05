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
    Check if yt-dlp needs updating and log appropriate messages.

    This function checks the installed version of yt-dlp against the latest version
    on PyPI and logs informational or error messages as appropriate. It handles
    network errors, missing packages, and version parsing issues gracefully.

    The function does not raise exceptions but logs them using the application's
    logging system.
    """
    checker = YTDVersionChecker()
    try:
        needs_update, current, latest = checker.check_version()
        if needs_update:
            logger.info(f"Update available: {current} -> {latest}")
            logger.info("Please run the appropriate upgrade in your environment.")
            logger.info("   For example: pip install --upgrade yt-dlp ")
            return False
        else:
            logger.info(f"yt-dlp is up to date (version {current})")

    except ImportError as e:
        logger.error(f"In yt-dlp version check: Package error: {e}")
    except requests.RequestException as e:
        logger.error(f"In yt-dlp version check: Network error: {e}")
    except InvalidVersion as e:
        logger.error(f"In yt-dlp version check: Version parsing error: {e}")
    except Exception as e:
        logger.error(f"In yt-dlp version check: Unexpected error: {e}")
        
    return True
