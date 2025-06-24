# --------------------------------------------------------------------------- #
# Simple Time abstraction to keep milliseconds/seconds handling explicit.
# For now it only stores an integer number of milliseconds and exposes a few
# helpers.  Down‑stream code can adopt it incrementally without breaking the
# current int‑ms API.
# --------------------------------------------------------------------------- #
import math


class TimeMs:
    """
    Lightweight representation of a time interval or timestamp.
    Allows negative values.

    Internally everything is stored in **milliseconds** 
    The class exposes helpers to create from / convert to seconds.
    Helps avoid conversion errors.
    """

    __slots__ = ("_ms",)

    def __init__(self, ms: int | float):
        if not isinstance(ms, (int, float)):
            raise TypeError(f"ms must be a number, got {type(ms).__name__}")
        if not math.isfinite(ms):
            raise ValueError("ms must be a finite number")
        self._ms = round(ms)

    @classmethod
    def from_seconds(cls, seconds: int | float) -> "TimeMs":
        return cls(round(seconds * 1000))

    def to_ms(self) -> int:
        return self._ms

    def to_seconds(self) -> float:
        return float(self._ms / 1000)

    def __add__(self, other: "TimeMs | int | float") -> "TimeMs":
        """
        Add another TimeMs, int, or float (interpreted as milliseconds).
        Raises TypeError for unsupported types.
        """
        if isinstance(other, TimeMs):
            return TimeMs(self._ms + other._ms)
        elif isinstance(other, (int, float)):
            return TimeMs(self._ms + round(other))
        else:
            raise TypeError(f"Unsupported operand type(s) for +: 'TimeMs' and '{type(other).__name__}'")

    def __sub__(self, other: "TimeMs | int | float") -> "TimeMs":
        """
        Subtract another TimeMs, int, or float (interpreted as milliseconds).
        Raises TypeError for unsupported types.
        """
        if isinstance(other, TimeMs):
            return TimeMs(self._ms - other._ms)
        elif isinstance(other, (int, float)):
            return TimeMs(self._ms - round(other))
        else:
            raise TypeError(f"Unsupported operand type(s) for +: 'TimeMs' and '{type(other).__name__}'")
        return TimeMs(self._ms - other._ms)

    def __int__(self) -> int:           # allows int(TimeMs(...))
        return self._ms

    def __float__(self) -> float:       # allows float(TimeMs(...))
        return float(self._ms)

    def __repr__(self) -> str:
        return f"TimeMs({self.to_seconds():.3f}s)"
    
    # Pydantic support
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v
        if isinstance(v, (int, float)):
            return cls(v)
        raise TypeError("Invalid type for TimeMs")
    

def convert_sec_to_ms(val: float) -> int:
    """ 
    Convert seconds to milliseconds, rounding to the nearest integer.
    """
    return round(val * 1000)

def convert_ms_to_sec(ms: int) -> float:
    """Convert time from milliseconds (int) to seconds (float)."""
    return float(ms / 1000)

