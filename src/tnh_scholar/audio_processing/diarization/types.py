from typing import TypedDict


class PyannoteEntry(TypedDict):
    speaker: str
    start: float  # seconds
    end: float    # seconds