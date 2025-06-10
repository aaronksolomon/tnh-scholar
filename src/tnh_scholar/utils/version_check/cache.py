"""Simple caching mechanism for version information."""

import time
from typing import Dict, Optional

from packaging.version import Version


# TODO have this persist in a cache file?
class VersionCache:
    """Simple time-based cache for version information."""
    
    def __init__(self, cache_duration: int = 3600):
        """Initialize cache with specified expiration time in seconds."""
        self.cache: Dict[str, Version] = {}
        self.timestamps: Dict[str, float] = {}
        self.cache_duration = cache_duration
        
    def get(self, key: str) -> Optional[Version]:
        """Get cached version if still valid."""
        return self.cache.get(key) if self.is_valid(key) else None
        
    def set(self, key: str, value: Version) -> None:
        """Cache version with current timestamp."""
        self.cache[key] = value
        self.timestamps[key] = time.time()
        
    def is_valid(self, key: str) -> bool:
        """Check if cached value is still valid."""
        if key not in self.timestamps:
            return False
        age = time.time() - self.timestamps[key]
        return age < self.cache_duration