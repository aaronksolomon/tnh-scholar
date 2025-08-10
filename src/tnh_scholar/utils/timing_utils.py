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
    

    # def __sub__(self, other: "TimeMs | int | float") -> "TimeMs":
    #     """
    #     Subtract another TimeMs, int, or float (interpreted as milliseconds).
    #     Raises TypeError for unsupported types.
    #     """
    #     if isinstance(other, TimeMs):
    #         return TimeMs(self._ms - other._ms)
    #     elif isinstance(other, (int, float)):
    #         return TimeMs(self._ms - round(other))
    #     else:
    #         raise TypeError(f"Unsupported operand type(s) for +: 'TimeMs' and '{type(other).__name__}'")
    #     return TimeMs(self._ms - other._ms)

    # def __int__(self) -> int:           # allows int(TimeMs(...))
    #     return self._ms

    # def __float__(self) -> float:       # allows float(TimeMs(...))
    #     return float(self._ms)

    def __repr__(self) -> str:
        return f"TimeMs({self.to_seconds():.3f}s)"

    # # ------------------------------------------------------------------ #
    # # Numeric protocol helpers and standard operator overloads
    # # ------------------------------------------------------------------ #
    # def _coerce_ms(self, other: "TimeMs | int | float") -> int | None:
    #     """Return *other* converted to integer‑milliseconds, or None if unsupported."""
    #     if isinstance(other, TimeMs):
    #         return other._ms
    #     if isinstance(other, (int, float)) and math.isfinite(other):
    #         return round(other)
    #     return None

    # # Comparison operators
    # def __eq__(self, other: object) -> bool:  # type: ignore[override]
    #     coerced = self._coerce_ms(other) # type: ignore[arg-type]
    #     return coerced is not None and self._ms == coerced  # noqa: E701

    # def __lt__(self, other: "TimeMs | int | float") -> bool:  # type: ignore[override]
    #     coerced = self._coerce_ms(other)
    #     return NotImplemented if coerced is None else self._ms < coerced

    # def __le__(self, other: "TimeMs | int | float") -> bool:  # type: ignore[override]
    #     coerced = self._coerce_ms(other)
    #     return NotImplemented if coerced is None else self._ms <= coerced

    # def __gt__(self, other: "TimeMs | int | float") -> bool:  # type: ignore[override]
    #     coerced = self._coerce_ms(other)
    #     return NotImplemented if coerced is None else self._ms > coerced

    # def __ge__(self, other: "TimeMs | int | float") -> bool:  # type: ignore[override]
    #     coerced = self._coerce_ms(other)
    #     return NotImplemented if coerced is None else self._ms >= coerced

    # def __hash__(self) -> int:  # allows use in dict/set keys
    #     return hash(self._ms)

    # # Arithmetic operators (beyond + and - implemented above)
    # def __radd__(self, other: "TimeMs | int | float") -> "TimeMs":
    #     return self + other  # __add__ already handles coercion

    # def __rsub__(self, other: "TimeMs | int | float") -> "TimeMs":
    #     # reverse subtraction: other - self
    #     if isinstance(other, TimeMs):
    #         return TimeMs(other._ms - self._ms)
    #     elif isinstance(other, (int, float)):
    #         return TimeMs(round(other) - self._ms)
    #     return NotImplemented  # type: ignore[return-value]

    # def __mul__(self, other: int | float) -> "TimeMs":  # scale by scalar
    #     if isinstance(other, (int, float)):
    #         return TimeMs(self._ms * other)
    #     raise TypeError("Can only multiply TimeMs by a number")

    # __rmul__ = __mul__  # commutative

    # def __truediv__(self, other: "TimeMs | int | float") -> "TimeMs | float":
    #     if isinstance(other, TimeMs):
    #         return self._ms / other._ms  # dimensionless ratio
    #     elif isinstance(other, (int, float)):
    #         return TimeMs(self._ms / other)
    #     raise TypeError("Unsupported operand for division with TimeMs")

    # def __rtruediv__(self, other: int | float) -> float:  # number / TimeMs -> ratio
    #     return other / self._ms if isinstance(other, (int, float)) else NotImplemented

    # def __floordiv__(self, other: "TimeMs | int | float") -> "TimeMs | int":
    #     if isinstance(other, TimeMs):
    #         return self._ms // other._ms
    #     elif isinstance(other, (int, float)):
    #         return TimeMs(self._ms // other)
    #     raise TypeError("Unsupported operand for floor division with TimeMs")

    # def __rfloordiv__(self, other: int | float) -> int:
    #     if isinstance(other, (int, float)):
    #         return int(other // self._ms)
    #     return NotImplemented  # type: ignore[return-value]

    # def __mod__(self, other: "TimeMs | int | float") -> "TimeMs":
    #     coerced = self._coerce_ms(other)
    #     if coerced is None:
    #         raise TypeError("Unsupported operand for % with TimeMs")
    #     return TimeMs(self._ms % coerced)

    # def __rmod__(self, other: int | float) -> "TimeMs":
    #     if isinstance(other, (int, float)):
    #         return TimeMs(round(other) % self._ms)
    #     return NotImplemented  # type: ignore[return-value]

    # def __divmod__(self, other: "TimeMs | int | float") -> tuple["TimeMs | int", "TimeMs"]:
    #     coerced = self._coerce_ms(other)
    #     if coerced is None:
    #         raise TypeError("Unsupported operand for divmod with TimeMs")
    #     q, r = divmod(self._ms, coerced)
    #     return (q if isinstance(other, TimeMs) else TimeMs(q), TimeMs(r))

    # def __rdivmod__(self, other: int | float) -> tuple[int, "TimeMs"]:
    #     if isinstance(other, (int, float)):
    #         q, r = divmod(round(other), self._ms)
    #         return q, TimeMs(r)
    #     return NotImplemented  # type: ignore[return-value]

    # # Unary operators
    # def __neg__(self) -> "TimeMs":
    #     return TimeMs(-self._ms)

    # def __pos__(self) -> "TimeMs":
    #     return TimeMs(+self._ms)

    # def __abs__(self) -> "TimeMs":
    #     return TimeMs(abs(self._ms))

    # # Pydantic support
    # @classmethod
    # def __get_validators__(cls):
    #     yield cls.validate

    # @classmethod
    # def validate(cls, v):
    #     if isinstance(v, cls):
    #         return v
    #     if isinstance(v, (int, float)):
    #         return cls(v)
    #     raise TypeError("Invalid type for TimeMs")
    

def convert_sec_to_ms(val: float) -> int:
    """ 
    Convert seconds to milliseconds, rounding to the nearest integer.
    """
    return round(val * 1000)

def convert_ms_to_sec(ms: int) -> float:
    """Convert time from milliseconds (int) to seconds (float)."""
    return float(ms / 1000)

