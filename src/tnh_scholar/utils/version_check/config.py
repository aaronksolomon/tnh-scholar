"""Configuration classes for version checking."""

from enum import Enum
from typing import Optional

from packaging.version import Version


class VersionStrategy(Enum):
    """Enumeration of version checking strategies."""
    MINIMUM = "minimum"    # Package version must be >= requirement
    EXACT = "exact"        # Package version must be == requirement
    LATEST = "latest"      # Package version should be the latest available
    RANGE = "range"        # Package version must be within a specified range
    VERSION_DIFF = "vdiff" # Check version difference against thresholds

class VersionCheckerConfig:
    """Configuration for version checking behavior."""
    
    def __init__(self,
                 strategy: VersionStrategy = VersionStrategy.MINIMUM,
                 requirement: str = "",
                 fail_on_error: bool = False,
                 cache_duration: int = 3600,  # 1 hour
                 network_timeout: int = 5,    # seconds
                 vdiff_warn_matrix: Optional[str] = None,
                 vdiff_fail_matrix: Optional[str] = None):
        """Initialize version checker configuration."""
        self.strategy = strategy
        self.requirement = requirement
        self.fail_on_error = fail_on_error
        self.cache_duration = cache_duration
        self.network_timeout = network_timeout
        self.vdiff_warn_matrix = vdiff_warn_matrix
        self.vdiff_fail_matrix = vdiff_fail_matrix
    
    def get_required_version(self) -> Optional[Version]:
        """Get required version as a Version object."""
        return Version(self.requirement) if self.requirement else None