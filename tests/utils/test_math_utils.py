import pytest

from tnh_scholar.utils.math_utils import fraction_to_percent


@pytest.mark.parametrize(
    "numerator, denominator, expected",
    [
        (0, 0, 0.0),
        (0, 10, 0.0),
        (1, 4, 25.0),
        (3, 4, 75.0),
    ],
)
def test_fraction_to_percent(numerator, denominator, expected):
    assert fraction_to_percent(numerator, denominator) == expected
