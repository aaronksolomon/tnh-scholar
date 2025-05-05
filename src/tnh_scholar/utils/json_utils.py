import json
from pathlib import Path
from typing import Dict, List, Union

from pydantic import BaseModel, ValidationError


def write_data_to_json_file(
    file: Path, data: Union[dict, list], indent: int = 4, ensure_ascii: bool = False
) -> None:
    """
    Writes a dictionary or list as a JSON string to a file, 
    ensuring the parent directory exists,
    and supports formatting with indentation and ASCII control.

    Args:
        file (Path): Path to the JSON file where the data will be written.
        data (Union[dict, list]): The data to write to the file. Typically a dict or list.
        indent (int): Number of spaces for JSON indentation. Defaults to 4.
        ensure_ascii (bool): Whether to escape non-ASCII characters. Defaults to False.

    Raises:
        ValueError: If the data cannot be serialized to JSON.
        IOError: If there is an issue writing to the file.

    Example:
        >>> from pathlib import Path
        >>> data = {"key": "value"}
        >>> write_json_str_to_file(Path("output.json"), data, indent=2, ensure_ascii=True)
    """
    try:
        # Convert the data to a formatted JSON string
        json_str = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    except TypeError as e:
        raise ValueError(f"Error serializing data to JSON: {e}") from e

    try:
        # Ensure the parent directory exists
        file.parent.mkdir(parents=True, exist_ok=True)

        # Write the JSON string to the file
        with file.open("w", encoding="utf-8") as f:
            f.write(json_str)
    except IOError as e:
        raise IOError(f"Error writing JSON string to file '{file}': {e}") from e


def save_model_to_json(
    file: Path, model: BaseModel, indent: int = 4, ensure_ascii: bool = False
) -> None:
    """
    Saves a Pydantic model to a JSON file, formatted with indentation for readability.

    Args:
        file (Path): Path to the JSON file where the model will be saved.
        model (BaseModel): The Pydantic model instance to save.
        indent (int): Number of spaces for JSON indentation. Defaults to 4.
        ensure_ascii (bool): Whether to escape non-ASCII characters. Defaults to False.

    Raises:
        ValueError: If the model cannot be serialized to JSON.
        IOError: If there is an issue writing to the file.

    Example:
        class ExampleModel(BaseModel):
            name: str
            age: int

        if __name__ == "__main__":
            model_instance = ExampleModel(name="John", age=30)
            json_file = Path("example.json")
            try:
                save_model_to_json(json_file, model_instance)
                print(f"Model saved to {json_file}")
            except (ValueError, IOError) as e:
                print(e)
    """
    try:
        # Serialize model to JSON string
        model_dict = model.model_dump()
    except TypeError as e:
        raise ValueError(f"Error serializing model to JSON: {e}") from e

    # Write the JSON string to the file
    write_data_to_json_file(file, model_dict, indent=indent, ensure_ascii=ensure_ascii)


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
    with file_path.open("r", encoding="utf-8") as file:
        return [json.loads(line.strip()) for line in file if line.strip()]


def load_json_into_model(file: Path, model: type[BaseModel]) -> BaseModel:
    """
    Loads a JSON file and validates it against a Pydantic model.

    Args:
        file (Path): Path to the JSON file.
        model (type[BaseModel]): The Pydantic model to validate against.

    Returns:
        BaseModel: An instance of the validated Pydantic model.

    Raises:
        ValueError: If the file content is invalid JSON or does not match the model.
    Example:
        class ExampleModel(BaseModel):
        name: str
        age: int
        city: str

        if __name__ == "__main__":
            json_file = Path("example.json")
            try:
                data = load_json_into_model(json_file, ExampleModel)
                print(data)
            except ValueError as e:
                print(e)
    """
    try:
        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return model(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Error loading or validating JSON file '{file}': {e}") from e


def format_json(file: Path) -> None:
    """
    Formats a JSON file with line breaks and indentation for readability.

    Args:
        file (Path): Path to the JSON file to be formatted.

    Example:
        format_json(Path("data.json"))
    """
    with file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    with file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
