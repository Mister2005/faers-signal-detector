import pytest
from src.clean import normalize_drug_name, strip_dosage, normalize_age

BRAND_MAP = {
    "TYLENOL": "ACETAMINOPHEN",
    "ADVIL": "IBUPROFEN",
    "LIPITOR": "ATORVASTATIN"
}
GENERIC_LIST = list(BRAND_MAP.values())

def test_brand_lookup():
    assert normalize_drug_name("TYLENOL", BRAND_MAP, GENERIC_LIST) == "ACETAMINOPHEN"

def test_case_insensitive():
    assert normalize_drug_name("tylenol", BRAND_MAP, GENERIC_LIST) == "ACETAMINOPHEN"

def test_strip_dosage():
    assert strip_dosage("ASPIRIN 500MG") == "ASPIRIN"
    assert strip_dosage("IBUPROFEN 200 mg tablet") == "IBUPROFEN"

def test_dosage_stripping_before_lookup():
    assert normalize_drug_name("LIPITOR 20MG", BRAND_MAP, GENERIC_LIST) == "ATORVASTATIN"

def test_unknown_drug():
    result = normalize_drug_name("XYZZYDRUGNOTREAL123", BRAND_MAP, GENERIC_LIST)
    assert isinstance(result, str)  # Should return something, not crash

def test_age_years():
    assert normalize_age("25", "YR") == 25.0

def test_age_months():
    assert abs(normalize_age("18", "MON") - 1.5) < 0.01

def test_age_invalid():
    assert normalize_age("abc", "YR") is None

def test_age_out_of_range():
    assert normalize_age("999", "YR") is None
