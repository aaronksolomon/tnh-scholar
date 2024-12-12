from pathlib import Path
import json
from typing import Dict, List

def load_jsonl_to_dict(file_path: Path) -> List[Dict]:
    """
    Load a JSONL file into a list of dictionaries.
    
    Args:
        file_path (Path): Path to the JSONL file.

    Returns:
        List[Dict]: A list of dictionaries, each representing a line in the JSONL file.
    
    Example:
        >>> from pathlib import Path
        >>> file_path = Path("data.jsonl")
        >>> data = load_jsonl_to_dict(file_path)
        >>> print(data)
        [{'key1': 'value1'}, {'key2': 'value2'}]
    """
    with file_path.open('r', encoding='utf-8') as file:
        return [json.loads(line.strip()) for line in file if line.strip()]