"""Main version checker implementation."""

from typing import Optional

from packaging.version import Version

from .cache import VersionCache
from .config import VersionCheckerConfig, VersionStrategy
from .models import PackageInfo, Result
from .providers import StandardVersionProvider, VersionProvider
from .strategies import (
    check_exact_version,
    check_minimum_version,
    check_version_diff,
)


class PackageVersionChecker:
    """Main class for checking package versions against requirements."""

    def __init__(
        self,
        provider: Optional[VersionProvider] = None,
        cache: Optional[VersionCache] = None,
    ):
        self.provider = provider or StandardVersionProvider()
        self.cache = cache or VersionCache()

    def _get_warning_level(self, diff_details: Optional[dict[str, int]]) -> Optional[str]:
        """Map diff details to a warning severity."""
        if not diff_details:
            return None
        if diff_details.get("major", 0) > 0:
            return "MAJOR"
        if diff_details.get("minor", 0) > 0:
            return "MINOR"
        if diff_details.get("micro", 0) > 0:
            return "MICRO"
        return None

    def _evaluate_version_diff(
        self,
        installed: Version,
        latest: Version,
        config: VersionCheckerConfig,
    ) -> tuple[bool, Optional[str], Optional[dict[str, int]]]:
        """Evaluate version difference thresholds."""
        is_compatible = True
        warning_level = None
        diff_details = None

        if config.vdiff_warn_matrix:
            warn_within_limits, diff_details = check_version_diff(
                installed,
                latest,
                config.vdiff_warn_matrix,
            )
            if not warn_within_limits:
                warning_level = self._get_warning_level(diff_details)

        if config.vdiff_fail_matrix:
            is_compatible, diff_details = check_version_diff(
                installed,
                latest,
                config.vdiff_fail_matrix,
            )

        return is_compatible, warning_level, diff_details

    def _determine_compatibility(
        self,
        installed: Version,
        latest: Version,
        config: VersionCheckerConfig,
    ) -> tuple[bool, Optional[str], Optional[dict[str, int]]]:
        """Determine compatibility for the configured strategy."""
        required_version = config.get_required_version()
        if config.strategy == VersionStrategy.MINIMUM:
            return (
                check_minimum_version(installed, required_version),
                None,
                None,
            )
        if config.strategy == VersionStrategy.EXACT:
            return (
                check_exact_version(installed, required_version),
                None,
                None,
            )
        if config.strategy == VersionStrategy.VERSION_DIFF:
            return self._evaluate_version_diff(installed, latest, config)
        return True, None, None

    def _build_package_info(
        self,
        package_name: str,
        installed: Version,
        latest: Version,
        config: VersionCheckerConfig,
    ) -> PackageInfo:
        """Build the package info payload for the result."""
        return PackageInfo(
            name=package_name,
            installed_version=str(installed),
            latest_version=str(latest),
            required_version=str(config.get_required_version())
            if config.requirement
            else None,
        )

    def check_version(
        self,
        package_name: str,
        config: Optional[VersionCheckerConfig] = None,
    ) -> Result:
        """Check if package meets version requirements based on config."""
        config = config or VersionCheckerConfig()

        try:
            installed = self.provider.get_installed_version(package_name)
            latest = self.provider.get_latest_version(package_name)
            needs_update = installed < latest
            is_compatible, warning_level, diff_details = self._determine_compatibility(
                installed,
                latest,
                config,
            )
            package_info = self._build_package_info(
                package_name,
                installed,
                latest,
                config,
            )

            return Result(
                is_compatible=is_compatible,
                needs_update=needs_update,
                package_info=package_info,
                warning_level=warning_level,
                diff_details=diff_details,
            )

        except Exception as e:
            if config.fail_on_error:
                raise
            return Result(
                is_compatible=False,
                needs_update=False,
                package_info=PackageInfo(name=package_name),
                error=str(e),
            )
