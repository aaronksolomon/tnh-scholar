"""Version comparison strategies for package version checking."""

from typing import Dict, Optional, Tuple

from packaging.version import Version


def check_minimum_version(installed: Version, required: Optional[Version]) -> bool:
    """Check if installed version meets minimum requirement."""
    return True if required is None else installed >= required

def check_exact_version(installed: Version, required: Optional[Version]) -> bool:
    """Check if installed version exactly matches requirement."""
    return True if required is None else installed == required

def check_version_diff(
    installed: Version,
    reference: Version,
    vdiff_matrix: str
) -> Tuple[bool, Dict[str, int]]:
    """Check if version difference is within specified limits."""
    # Calculate actual differences
    major_diff = abs(reference.major - installed.major)
    minor_diff = abs(reference.minor - installed.minor) if reference.major == installed.major else 0
    micro_diff = abs(reference.micro - installed.micro) if (reference.major == installed.major and 
                                                          reference.minor == installed.minor) else 0
    
    diff_details = {
        "major": major_diff,
        "minor": minor_diff,
        "micro": micro_diff
    }
    
    # If no matrix provided, differences are acceptable
    if not vdiff_matrix:
        return True, diff_details
        
    # Parse matrix
    major_limit, minor_limit, micro_limit = parse_vdiff_matrix(vdiff_matrix)
    
    # Check limits (None means no limit)
    if major_limit is not None and major_diff > major_limit:
        return False, diff_details
        
    if minor_limit is not None and minor_diff > minor_limit:
        return False, diff_details
        
    if micro_limit is not None and micro_diff > micro_limit:
        return False, diff_details
        
    return True, diff_details

def parse_vdiff_matrix(matrix_str: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """Parse a version difference matrix string."""
    parts = matrix_str.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version difference matrix: {matrix_str}")

    limits = []
    for part in parts:
        if part == "*":
            limits.append(None)  # No limit
        else:
            try:
                limits.append(int(part))
            except ValueError as e:
                raise ValueError(f"Invalid version component: {part}") from e

    return tuple(limits)  # Tuple[Optional[int], Optional[int], Optional[int]]