import re
from collections.abc import MutableMapping
from typing import Dict, Iterator, Mapping, Optional, Union

import yaml

from tnh_scholar.logging_config import get_child_logger

JsonValue = Union[str, int, float, bool, list, dict, None]

logger = get_child_logger(__name__)

class Metadata(MutableMapping):
    """
    Flexible metadata container that behaves like a dict while ensuring
    JSON serializability. Designed for AI processing pipelines where schema
    flexibility is prioritized over structure.
    """
    def __init__(
        self, 
        data: Optional[Union[Dict[str, JsonValue], 'Metadata']] = None
        ) -> None:
        self._data: Dict[str, JsonValue] = {}
        if data is not None:
            self.update(data._data if isinstance(data, Metadata) else data)

    # Core dict interface
    def __getitem__(self, key: str) -> JsonValue:
        return self._data[key]
    
    def __setitem__(self, key: str, value: JsonValue) -> None:
        self._data[key] = value
        
    def __delitem__(self, key: str) -> None:
        del self._data[key]
    
    def __iter__(self) -> Iterator[str]:
        return iter(self._data)
    
    def __len__(self) -> int:
        return len(self._data)

    # Dict union operations (|, |=)
    def __or__(self, other: Union[Mapping[str, JsonValue], 'Metadata']) -> 'Metadata':
        if isinstance(other, (Metadata, Mapping)):
            other_dict = other._data if isinstance(other, Metadata) else other
            return Metadata(self._data | other_dict) # type: ignore
        return NotImplemented

    def __ror__(self, other: Mapping[str, JsonValue]) -> 'Metadata':
        if isinstance(other, Mapping):
            return Metadata(other | self._data) # type: ignore
        return NotImplemented

    def __ior__(self, other: Union[Mapping[str, JsonValue], 'Metadata']) -> 'Metadata':
        if isinstance(other, (Metadata, Mapping)):
            self._data |= (other._data if isinstance(other, Metadata) else other)
            return self
        return NotImplemented

    # JSON serialization
    def to_dict(self) -> Dict[str, JsonValue]:
        """Convert to plain dict for JSON serialization."""
        return self._data.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, JsonValue]) -> 'Metadata':
        """Create from a plain dict."""
        return cls(data)

    def __repr__(self) -> str:
        return f"Metadata({self._data})"
    
    @classmethod
    def from_fields(cls, data: dict, fields: list[str]) -> "Metadata":
        """Create a Metadata object by extracting specified fields from a dictionary.
        
        Args:
            data: Source dictionary
            fields: List of field names to extract
            
        Returns:
            New Metadata instance with only specified fields
        """
        filtered = {k: data.get(k) for k in fields if k in data}
        return cls(filtered)
    
    def text_embed(self, content: str):
        return Frontmatter.embed(self, content)
 
class Frontmatter:
    """Handles YAML frontmatter embedding and extraction."""
    
    @staticmethod
    def extract(content: str) -> tuple[Metadata, str]:
        """Extract frontmatter and content from text.
        
        Args:
            content: Text with optional YAML frontmatter
            
        Returns:
            Tuple of (metadata object, remaining content)
        """
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        if match := re.match(pattern, content, re.DOTALL):
            try:
                yaml_data = yaml.safe_load(match[1])
                return Metadata(yaml_data or {}), match[2]
            except yaml.YAMLError:
                logger.warning("YAML Error in Frontmatter extraction.")
                return Metadata(), content
        return Metadata(), content

    @staticmethod
    def embed(metadata: Metadata, content: str) -> str:
        """Embed metadata as YAML frontmatter.
        
        Args:
            metadata: Dictionary of metadata
            content: Content text
            
        Returns:
            Text with embedded frontmatter
        """
        if not metadata:
            return content
            
        # Create YAML string
        yaml_str = yaml.dump(
            metadata.to_dict(),
            default_flow_style=False,
            allow_unicode=True
        )
        
        # Combine with content
        return (
            f"---\n"
            f"{yaml_str}---\n\n"
            f"{content.strip()}"
        )