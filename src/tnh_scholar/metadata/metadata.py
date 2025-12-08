import re
from collections.abc import MutableMapping
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Union

import yaml
from pydantic_core import core_schema
from yaml.scanner import ScannerError

from tnh_scholar import TNH_METADATA_PROCESS_FIELD
from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import path_as_str, read_str_from_file

# TODO fix all bug warnings from Sourcery in this file.

JsonValue = Union[str, int, float, bool, list, dict, None]

logger = get_child_logger(__name__)

def safe_yaml_load(yaml_str: str, *, context: str = "unknown") -> dict:
    try:
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            logger.warning(
                "YAML in [%s] is not a dict. Returning empty metadata.", context
                )
            return {}
        return data
    except ScannerError as e:
        snippet = yaml_str.replace("\n", "\\n")
        logger.error("YAML ScannerError in [%s]: %s\nSnippet:\n%s", context, e, snippet)
    except yaml.YAMLError as e:
        logger.error("General YAML error in [%s]: %s", context, e)
    return {}

class Metadata(MutableMapping):
    """
    Flexible metadata container that behaves like a dict while ensuring
    JSON serializability. Designed for AI processing pipelines where schema
    flexibility is prioritized over structure.
    """
    # Type processors at class level
    _type_processors = {
        Path: lambda p: path_as_str(p),
        datetime: lambda d: d.isoformat(),
    }

    def __init__(
        self, 
        data: Optional[Union[Dict[str, Any], 'Metadata']] = None
        ) -> None:
        self._data: Dict[str, JsonValue] = {}
        if data is not None:
            raw_data = data._data if isinstance(data, Metadata) else data
            processed_data = {
                k: self._process_value(v) for k, v in raw_data.items()
            }
            self.update(processed_data)

    def _process_value(self, value: Any) -> JsonValue:
        """Convert input values to JSON-serializable format."""
        if isinstance(value, tuple(self._type_processors.keys())):
            for type_, processor in self._type_processors.items():
                if isinstance(value, type_):
                    return processor(value)
        if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
            raise ValueError(
                f"Value {value} of type {type(value)} has no conversion to JsonValue.")
        return value

    # Core dict interface
    def __getitem__(self, key: str) -> JsonValue:
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Process and set value, ensuring JSON serializability."""
        self._data[key] = self._process_value(value)
        
    def __delitem__(self, key: str) -> None:
        del self._data[key]
    
    def __iter__(self) -> Iterator[str]:
        return iter(self._data)
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __str__(self) -> str:
        return self.to_yaml()

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
    
    def __repr__(self) -> str:
        return f"Metadata({self._data})"
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        """Defines the Pydantic core schema for the `Metadata` class.

        This method allows Pydantic to validate `Metadata` objects as dictionaries.
        It handles both direct `Metadata` instances and dictionaries during validation,
        providing flexibility for data input.

        Args:
            source_type: The source type being validated.
            handler: A callable to handle schema generation for other types.

        Returns:
            A Pydantic core schema that validates either a Metadata instance
            (by converting it to a dictionary) or a standard dictionary.
        """
        return core_schema.union_schema(
            choices=[
                # Handle Metadata instances with serialization
                core_schema.is_instance_schema(
                    cls,
                    serialization=core_schema.plain_serializer_function_ser_schema(
                        lambda x: x.to_dict()  # Use our to_dict method
                    )
                ),
                # Handle dictionary input
                handler(dict),
            ],
        )
    
    # JSON serialization
    def to_dict(self) -> Dict[str, JsonValue]:
        """Convert to plain dict for JSON serialization."""
        return self._data.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, JsonValue]) -> 'Metadata':
        """Create from a plain dict."""
        return cls(data)

    def copy(self) -> 'Metadata':
        """Create a deep copy of the metadata object."""
        return Metadata(deepcopy(self._data))
    
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
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'Metadata':
        """Create Metadata instance from YAML string.
        
        Args:
            yaml_str: YAML formatted string
            
        Returns:
            New Metadata instance
            
        Raises:
            yaml.YAMLError: If YAML parsing fails
        """
        if not yaml_str.strip():
            return cls()

        data = safe_yaml_load(yaml_str, context="Metadata.from_yaml()")
        return cls(data) if isinstance(data, dict) else cls()
    
    def text_embed(self, content: str):
        return Frontmatter.embed(self, content)
    
    def add_process_info(self, process_metadata: 'ProcessMetadata') -> None:
        """Add process metadata to history."""
        history = self.get(TNH_METADATA_PROCESS_FIELD, [])
        if not isinstance(history, list):
            history = []
        history.append(process_metadata.to_dict())  # Store as dict for serialization
        self[TNH_METADATA_PROCESS_FIELD] = history
    
    @property
    def process_history(self) -> List[Dict[str, Any]]:
        """Access process history with proper typing."""
        return self.get(TNH_METADATA_PROCESS_FIELD, [])
    
    def to_yaml(self) -> str:
        """Return metadata as YAML formatted string"""
        return yaml.dump(
            self._data,
            default_flow_style=False,
            allow_unicode=True
        )

class ProcessMetadata(Metadata):
    """Records information about a specific processing operation."""
    def __init__(
        self,
        step: str,
        processor: str, 
        tool: Optional[str] = None,
        **additional_params
    ):
        # Initialize base Metadata with our process data structure
        super().__init__({
            "step": step,
            "timestamp": datetime.now(),
            "processor": processor,
            "tool": tool,
        })
            
        # Add any additional parameters at top level
        self.update(additional_params)
    
class Frontmatter:
    """Handles YAML frontmatter embedding and extraction.

    Note: `extract` is pure (no I/O). `extract_from_file` performs I/O and should be
    treated as adapter-level convenience, not domain-level parsing.
    """
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
                yaml_data = safe_yaml_load(match[1], context="Frontmatter.extract")
                return Metadata(yaml_data or {}), match[2]
            except yaml.YAMLError:
                logger.warning("YAML Error in Frontmatter extraction.")
                return Metadata(), content
        return Metadata(), content
    
    @classmethod
    def extract_from_file(cls, file: Path) -> tuple[Metadata, str]:
        """Adapter-level convenience wrapper that reads from disk then parses."""
        text_str = read_str_from_file(file)
        return cls.extract(text_str)

    @classmethod
    def embed(cls, metadata: Metadata, content: str) -> str:
        """Embed metadata as YAML frontmatter.
        
        Args:
            metadata: Dictionary of metadata
            content: Content text
            
        Returns:
            Text with embedded frontmatter
        """

        # Combine with content
        return (
            f"{cls.generate(metadata)}"
            f"{content.strip()}"
        )
        
    @staticmethod
    def generate(metadata: Metadata) -> str:
        if not metadata:
            return ""
    
        yaml_str = metadata.to_yaml() 
        return (
            f"---\n"
            f"{yaml_str}---\n\n"
        )
