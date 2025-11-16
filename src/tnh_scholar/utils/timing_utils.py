# --------------------------------------------------------------------------- #
# Simple Time abstraction to keep milliseconds/seconds handling explicit.
# For now it only stores an integer number of milliseconds and exposes a few
# helpers.  Down‑stream code can adopt it incrementally without breaking the
# current int‑ms API.
# --------------------------------------------------------------------------- #
import math
from typing import Union

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class TimeMs(int):
    """
    Lightweight representation of a time interval or timestamp in milliseconds.
    Allows negative values.
    """

    def __new__(cls, ms: Union[int, float, "TimeMs"]):
        if isinstance(ms, TimeMs):
            value = int(ms)
        elif isinstance(ms, (int, float)):
            if not math.isfinite(ms):
                raise ValueError("ms must be a finite number")
            value = round(ms)
        else:
            raise TypeError(f"ms must be a number or TimeMs, got {type(ms).__name__}")
        return int.__new__(cls, value)

    @classmethod
    def from_seconds(cls, seconds: int | float) -> "TimeMs":
        return cls(round(seconds * 1000))

    def to_ms(self) -> int:
        return int(self)

    def to_seconds(self) -> float:
        return float(self) / 1000

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        return core_schema.with_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(lambda v: int(v)),
        )
        
    @classmethod
    def _validate(cls, value, info):
        """
        Pydantic core validator for TimeMs.

        Args:
            value: The value to validate.
            info: Pydantic core schema info (unused).

        Returns:
            TimeMs: Validated TimeMs instance.
        """
        return cls(value)

    def __add__(self, other):
        return TimeMs(int(self) + int(other))
    
    def __radd__(self, other):
        return TimeMs(int(other) + int(self))
    
    def __sub__(self, other):
        return TimeMs(int(self) - int(other))
    
    def __rsub__(self, other):
        return TimeMs(int(self) - int(other))

    def __repr__(self) -> str:
        return f"TimeMs({self.to_seconds():.3f}s)"

def convert_sec_to_ms(val: float) -> int:
    """ 
    Convert seconds to milliseconds, rounding to the nearest integer.
    """
    return round(val * 1000)

def convert_ms_to_sec(ms: int) -> float:
    """Convert time from milliseconds (int) to seconds (float)."""
    return float(ms / 1000)

