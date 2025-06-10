"""Data models for version checking results."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PackageInfo:
    """Information about a package and its versions."""
    
    name: str
    installed_version: Optional[str] = None
    latest_version: Optional[str] = None
    required_version: Optional[str] = None

@dataclass
class Result:
    """Result of a version check operation."""
    
    is_compatible: bool
    needs_update: bool
    package_info: PackageInfo
    error: Optional[str] = None
    warning_level: Optional[str] = None
    diff_details: Optional[Dict[str, int]] = None
    
    def get_upgrade_command(self) -> str:
        """Return pip command to upgrade package."""
        if not self.package_info or not self.package_info.name:
            return ""
        
        if self.package_info.latest_version:
            return f"pip install --upgrade {self.package_info.name}=={self.package_info.latest_version}"
        else:
            return f"pip install --upgrade {self.package_info.name}"