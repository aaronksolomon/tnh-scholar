"""Main version checker implementation."""

from typing import Optional

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
    
    def __init__(self, 
                 provider: Optional[VersionProvider] = None,
                 cache: Optional[VersionCache] = None):
        self.provider = provider or StandardVersionProvider()
        self.cache = cache or VersionCache()
    
    # TODO make this method more modular and extract out complexity  
    # also check why parse_vdiff is not being used.
    def check_version(self, 
                      package_name: str, 
                      config: Optional[VersionCheckerConfig] = None) -> Result:
        """Check if package meets version requirements based on config."""
        config = config or VersionCheckerConfig()
        
        try:
            # Get versions
            installed = self.provider.get_installed_version(package_name)
            latest = self.provider.get_latest_version(package_name)
            
            # Default values
            is_compatible = True
            needs_update = installed < latest
            warning_level = None
            diff_details = None
            
            # Check based on strategy
            if config.strategy == VersionStrategy.MINIMUM:
                is_compatible = check_minimum_version(installed, config.get_required_version())
                
            elif config.strategy == VersionStrategy.EXACT:
                is_compatible = check_exact_version(installed, config.get_required_version())
                
            elif config.strategy == VersionStrategy.VERSION_DIFF:
                # Check warning threshold
                if config.vdiff_warn_matrix:
                    warn_within_limits, diff_details = check_version_diff(
                        installed, latest, config.vdiff_warn_matrix)
                    if not warn_within_limits:
                        # Determine warning level based on which component exceeded threshold
                        if diff_details and "major" in diff_details and diff_details["major"] > 0:
                            warning_level = "MAJOR"
                        elif diff_details and "minor" in diff_details and diff_details["minor"] > 0:
                            warning_level = "MINOR"
                        else:
                            warning_level = "MICRO"
                
                # Check failure threshold
                if config.vdiff_fail_matrix:
                    fail_within_limits, diff_details = check_version_diff(
                        installed, latest, config.vdiff_fail_matrix)
                    is_compatible = fail_within_limits
            
            # Create package info
            package_info = PackageInfo(
                name=package_name,
                installed_version=str(installed),
                latest_version=str(latest),
                required_version=str(config.get_required_version()) if config.requirement else None
            )
            
            # Create and return result
            return Result(
                is_compatible=is_compatible,
                needs_update=needs_update,
                package_info=package_info,
                warning_level=warning_level,
                diff_details=diff_details
            )
            
        except Exception as e:
            # Handle errors based on configuration
            if config.fail_on_error:
                raise
            return Result(
                is_compatible=False,
                needs_update=False,
                package_info=PackageInfo(name=package_name),
                error=str(e)
            )