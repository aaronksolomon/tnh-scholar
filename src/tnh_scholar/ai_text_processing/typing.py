from typing import TypeVar

from pydantic import BaseModel

ResponseFormat = TypeVar("ResponseFormat", bound=BaseModel)
