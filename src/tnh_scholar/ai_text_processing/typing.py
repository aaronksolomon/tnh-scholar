from typing import TypeVar, Union

from pydantic import BaseModel

ResponseFormat = TypeVar("ResponseFormat", bound=BaseModel)

# Define a type for processor results
ProcessorResult = Union[str, ResponseFormat]