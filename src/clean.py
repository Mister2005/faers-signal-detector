import re
from pathlib import Path
import pandas as pd
import numpy as np
from rapidfuzz import process, fuzz
from src.db import get_engine, run_sql, query_df
from src.config import (
    REFERENCE_DIR, DOSAGE_PATTERN, FUZZY_MATCH_THRESHOLD,
    REFERENCE_BRAND_GENERIC_FILE, REFERENCE_MEDDRA_SOC_FILE,
    KAGGLE_REFERENCE_DIR
)


# Drug Name Standardization

def load_brand_to_generic() -> dict:
    """Load brand->generic mapping from a Kaggle-sourced CSV."""
    candidate_files = []
    if REFERENCE_BRAND_GENERIC_FILE:
        candidate_files.append(Path(REFERENCE_BRAND_GENERIC_FILE))
    candidate_files.extend(Path(KAGGLE_REFERENCE_DIR).glob("*.csv"))
    candidate_files.extend(Path(REFERENCE_DIR).glob("*.csv"))

    selected = None
    for f in candidate_files:
        if not f.exists():
            continue
        try:
            cols = [c.strip().lower() for c in pd.read_csv(f, nrows=0).columns]
        except Exception:
            continue
        if {"brand", "generic"}.issubset(set(cols)):
            selected = f
            break

    if selected is None:
        raise FileNotFoundError(
            "Brand/generic reference file not found. Add a Kaggle CSV with columns "
            "'brand,generic' in data/reference/kaggle/ or set REFERENCE_BRAND_GENERIC_FILE."
        )

    df = pd.read_csv(selected)
    return dict(zip(df["brand"].str.upper(), df["generic"].str.upper()))


def load_meddra_soc() -> dict:
    """Load MedDRA SOC mapping from a Kaggle-sourced CSV."""
    candidate_files = []
    if REFERENCE_MEDDRA_SOC_FILE:
        candidate_files.append(Path(REFERENCE_MEDDRA_SOC_FILE))
    candidate_files.extend(Path(KAGGLE_REFERENCE_DIR).glob("*.csv"))
    candidate_files.extend(Path(REFERENCE_DIR).glob("*.csv"))

    selected = None
    for f in candidate_files:
        if not f.exists():
            continue
        try:
            cols = [c.strip().lower() for c in pd.read_csv(f, nrows=0).columns]
        except Exception:
            continue
        if {"reaction", "soc_name"}.issubset(set(cols)):
            selected = f
            break

    if selected is None:
        raise FileNotFoundError(
            "MedDRA SOC reference file not found. Add a Kaggle CSV with columns "
            "'reaction,soc_name' in data/reference/kaggle/ or set REFERENCE_MEDDRA_SOC_FILE."
        )

    df = pd.read_csv(selected)
    return dict(zip(df["reaction"].str.upper(), df["soc_name"]))


def strip_dosage(name: str) -> str:
    """Remove dosage information from drug name string."""
    cleaned = re.sub(DOSAGE_PATTERN, "", name, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(tablet|cap|capsule)s?\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def normalize_drug_name(name: str, brand_map: dict, generic_list: list) -> str:
    """
    Full drug name normalization pipeline:
    1. Uppercase and strip whitespace
    2. Remove dosage patterns
    3. Direct lookup in brand->generic map
    4. Fuzzy match against known generics list
    5. Return cleaned name (or original if no match found)
    """
    if not name or pd.isna(name):
        return "UNKNOWN"

    name = str(name).upper().strip()
    name = strip_dosage(name)

    # Remove trailing punctuation and parenthetical suffixes
    name = re.sub(r'\s*\(.*?\)', '', name)
    name = name.strip(".,;:-/ ")

    # Direct brand->generic lookup
    if name in brand_map:
        return brand_map[name]

    # Check if name starts with a known brand (for compound names)
    for brand, generic in brand_map.items():
        if name.startswith(brand):
            return generic

    # Fuzzy match against the full generic list
    if generic_list:
        match, score, _ = process.extractOne(
            name, generic_list, scorer=fuzz.token_sort_ratio
        )
        if score >= FUZZY_MATCH_THRESHOLD:
            return match

    return name


# Age Normalization

AGE_UNIT_TO_YEARS = {
    "YR": 1.0,
    "MON": 1/12,
    "WK": 1/52,
    "DY": 1/365,
    "HR": 1/8760,
    "DEC": 10.0,
}

def normalize_age(age_str, age_cod_str) -> float | None:
    """Convert age + age_cod to decimal years. Returns None if invalid."""
    try:
        age = float(age_str)
        cod = str(age_cod_str).strip().upper()
        multiplier = AGE_UNIT_TO_YEARS.get(cod, 1.0)
        result = age * multiplier
        # Sanity check: discard clearly invalid ages
        if result < 0 or result > 120:
            return None
        return round(result, 2)
    except (ValueError, TypeError):
        return None


# Deduplication

DEDUPLICATE_SQL = """
    SELECT DISTINCT ON (caseid)
        primaryid::BIGINT,
        caseid::BIGINT,
        quarter,
        age,
        age_cod,
        sex,
        reporter_country,
        occp_cod
    FROM raw_demo
    WHERE primaryid IS NOT NULL AND caseid IS NOT NULL
    ORDER BY caseid, fda_dt DESC NULLS LAST, caseversion DESC NULLS LAST
"""

def build_clean_demo():
    """
    Deduplicate raw_demo (keep most recent report per case) and
    write to clean_demo with normalized age and seriousness flag.
    """
    engine = get_engine()
    print("[CLEAN] Deduplicating demographics...")
    df = query_df(DEDUPLICATE_SQL)
    print(f"  Raw reports: {query_df('SELECT COUNT(*) AS n FROM raw_demo').iloc[0,0]:,}")
    print(f"  Deduplicated: {len(df):,}")

    # Normalize age (vectorized for large FAERS volumes)
    age_num = pd.to_numeric(df["age"], errors="coerce")
    age_cod = df["age_cod"].astype(str).str.strip().str.upper()
    multiplier = age_cod.map(AGE_UNIT_TO_YEARS).fillna(1.0)
    age_years = (age_num * multiplier).round(2)
    age_years[(age_years < 0) | (age_years > 120)] = np.nan
    df["age_years"] = age_years
    df["sex"] = df["sex"].str.upper().str.strip().replace({"M": "Male", "F": "Female"})

    # Determine if any serious outcome (death, hospitalization, life-threatening)
    serious_ids = set(query_df(
        "SELECT DISTINCT caseid FROM raw_outc WHERE outc_cod IN ('DE','LT','HO','DS')"
    )["caseid"].dropna().astype("Int64").astype(str).tolist())
    df["serious"] = df["caseid"].astype("Int64").astype(str).isin(serious_ids)

    clean = df[[
        "primaryid", "caseid", "quarter",
        "age_years", "sex", "reporter_country", "occp_cod", "serious"
    ]]

    run_sql("TRUNCATE TABLE clean_demo")
    clean.to_sql("clean_demo", engine, if_exists="append", index=False,
                 method="multi", chunksize=5000)
    print(f"  Written {len(clean):,} rows to clean_demo")


def build_clean_drug():
    """
    Standardize drug names for all primary-suspect drugs.
    Only process PS (primary suspect) and SS (secondary suspect) roles.
    """
    engine = get_engine()
    print("[CLEAN] Standardizing drug names...")

    brand_map = load_brand_to_generic()
    generic_list = list(set(brand_map.values()))

    # Load only suspect drugs (role_cod PS or SS)
    df = query_df(
        "SELECT primaryid, drug_seq, role_cod, drugname, prod_ai, route, quarter "
        "FROM raw_drug WHERE role_cod IN ('PS', 'SS')"
    )
    print(f"  Loaded {len(df):,} suspect drug records")

    # Use prod_ai (active ingredient) if drugname is missing
    df["drug_name_raw"] = df["drugname"].fillna(df["prod_ai"]).fillna("UNKNOWN")

    print("  Running name normalization...")
    # Normalize unique raw names once to avoid O(rows x fuzzy_match) behavior.
    unique_raw = df["drug_name_raw"].astype(str).dropna().unique().tolist()
    name_map = {}
    for name in unique_raw:
        name_map[name] = normalize_drug_name(name, brand_map, generic_list)
    df["drug_name_clean"] = df["drug_name_raw"].astype(str).map(name_map).fillna("UNKNOWN")

    clean = df[[
        "primaryid", "drug_seq", "role_cod",
        "drug_name_raw", "drug_name_clean", "route", "quarter"
    ]]

    # raw_drug can contain repeated rows for the same (primaryid, drug_seq)
    # which violates clean_drug PK; keep a single representative row.
    before = len(clean)
    clean = clean.drop_duplicates(subset=["primaryid", "drug_seq"], keep="first")
    removed = before - len(clean)
    if removed:
        print(f"  [INFO] Removed {removed:,} duplicate (primaryid, drug_seq) rows before insert")

    run_sql("TRUNCATE TABLE clean_drug")
    clean.to_sql("clean_drug", engine, if_exists="append", index=False,
                 method="multi", chunksize=5000)
    print(f"  Written {len(clean):,} rows to clean_drug")


def build_clean_reac():
    """
    Clean reactions: uppercase, deduplicate per report, join SOC names.
    """
    engine = get_engine()
    print("[CLEAN] Processing reactions...")

    df = query_df("SELECT primaryid, caseid, pt, quarter FROM raw_reac WHERE pt IS NOT NULL")
    df["reaction_pt"] = df["pt"].str.upper().str.strip()

    # Load SOC reference
    soc_map = load_meddra_soc()
    df["soc_name"] = df["reaction_pt"].map(soc_map).fillna("Other")

    # Deduplicate (one row per primaryid-reaction pair)
    clean = df[["primaryid", "reaction_pt", "soc_name", "quarter"]].drop_duplicates(
        subset=["primaryid", "reaction_pt"]
    )

    run_sql("TRUNCATE TABLE clean_reac")
    clean.to_sql("clean_reac", engine, if_exists="append", index=False,
                 method="multi", chunksize=5000)
    print(f"  Written {len(clean):,} rows to clean_reac")


def build_clean_outc():
    """Copy outcomes for deduplicated reports only."""
    engine = get_engine()
    print("[CLEAN] Processing outcomes...")

    df = query_df(
        "SELECT o.primaryid, o.outc_cod, o.quarter FROM raw_outc o "
        "INNER JOIN clean_demo d ON o.primaryid::BIGINT = d.primaryid"
    )
    clean = df.drop_duplicates(subset=["primaryid", "outc_cod"])

    run_sql("TRUNCATE TABLE clean_outc")
    clean.to_sql("clean_outc", engine, if_exists="append", index=False,
                 method="multi", chunksize=5000)
    print(f"  Written {len(clean):,} rows to clean_outc")


def run_all_cleaning():
    build_clean_demo()
    build_clean_drug()
    build_clean_reac()
    build_clean_outc()
