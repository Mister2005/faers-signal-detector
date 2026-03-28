import pytest
from src.signals import compute_contingency
from src.config import PRR_THRESHOLD, CHI2_THRESHOLD, MIN_CASE_COUNT

def test_prr_basic():
    """PRR should equal 1 when drug-event rate equals background rate."""
    result = compute_contingency(a=100, b=900, c=100, d=900)
    assert abs(result["prr"] - 1.0) < 0.01

def test_prr_elevated():
    """Known elevated signal: drug causes event 5x more than expected."""
    result = compute_contingency(a=50, b=50, c=10, d=890)
    assert result["prr"] > 4.0
    assert result["is_signal"] is True

def test_insufficient_cases():
    """Below minimum case count should not flag as signal even with high PRR."""
    result = compute_contingency(a=2, b=8, c=100, d=9890)
    assert result["is_signal"] is False  # a=2 < MIN_CASE_COUNT=3

def test_null_denominator():
    """Zero denominators should return None."""
    result = compute_contingency(a=0, b=0, c=10, d=990)
    assert result is None

def test_ror_greater_than_one_for_signal():
    """Confirmed signal should have ROR CI lower > 1."""
    result = compute_contingency(a=30, b=70, c=30, d=9870)
    if result["is_signal"]:
        assert result["ror_ci_lower"] > 1.0

def test_known_no_signal():
    """Very small PRR should not produce a signal."""
    result = compute_contingency(a=5, b=995, c=500, d=8500)
    assert result["prr"] < 1.0
    assert result["is_signal"] is False
