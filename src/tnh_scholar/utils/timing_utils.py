def convert_sec_to_ms(val: float) -> int:
    """ 
    Convert seconds to milliseconds, rounding to the nearest integer.
    """
    return round(val * 1000)

def convert_ms_to_sec(seconds: int) -> float:
    """Convert time from milliseconds (int) to seconds (float)."""
    return float(seconds / 1000)