def fraction_to_percent(numerator: float, denominator: float) -> float:
    """Convert a fraction to a percentage (0.0 if denominator is zero)."""
    if denominator == 0:
        return 0.0
    return (numerator / denominator) * 100.0
