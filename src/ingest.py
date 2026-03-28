import os
import glob
import pandas as pd
from sqlalchemy import text
from src.db import get_engine
from src.config import DATA_RAW_DIR

# Column name mappings - FAERS uses inconsistent casing across quarters
# These are the canonical lowercase column names we normalize to
DEMO_COLS = [
    "primaryid", "caseid", "caseversion", "i_f_code", "event_dt", "mfr_dt",
    "init_fda_dt", "fda_dt", "rept_cod", "auth_num", "mfr_num", "mfr_sndr",
    "lit_ref", "age", "age_cod", "age_grp", "sex", "e_sub", "wt", "wt_cod",
    "rept_dt", "to_mfr", "occp_cod", "reporter_country", "occr_country"
]

DRUG_COLS = [
    "primaryid", "caseid", "drug_seq", "role_cod", "drugname", "prod_ai",
    "val_vbm", "route", "dose_vbm", "cum_dose_chr", "cum_dose_unit",
    "dechal", "rechal", "lot_num", "exp_dt", "nda_num", "dose_amt",
    "dose_unit", "dose_freq"
]

REAC_COLS = ["primaryid", "caseid", "pt", "drug_rec_act"]
OUTC_COLS = ["primaryid", "caseid", "outc_cod"]
INDI_COLS = ["primaryid", "caseid", "drug_seq", "indi_drug_seq", "indi_pt"]

FILE_CONFIG = {
    "DEMO": ("raw_demo", DEMO_COLS),
    "DRUG": ("raw_drug", DRUG_COLS),
    "REAC": ("raw_reac", REAC_COLS),
    "OUTC": ("raw_outc", OUTC_COLS),
    "INDI": ("raw_indi", INDI_COLS),
}

INT_COLS_BY_TABLE = {
    "raw_demo": ["primaryid", "caseid", "caseversion"],
    "raw_drug": ["primaryid", "caseid", "drug_seq", "val_vbm"],
    "raw_reac": ["primaryid", "caseid"],
    "raw_outc": ["primaryid", "caseid"],
    "raw_indi": ["primaryid", "caseid", "drug_seq", "indi_drug_seq"],
}

FLOAT_COLS_BY_TABLE = {
    "raw_demo": ["age", "wt"],
}


def get_varchar_limits(engine, table_name: str) -> dict[str, int]:
    """Return VARCHAR/CHAR length limits for the target table."""
    query = text(
        """
        SELECT column_name, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = :table_name
          AND data_type IN ('character varying', 'character')
          AND character_maximum_length IS NOT NULL
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"table_name": table_name}).fetchall()
    return {row[0]: int(row[1]) for row in rows}


def sanitize_numeric_columns(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Coerce numeric columns to nullable pandas numeric dtypes."""
    for col in INT_COLS_BY_TABLE.get(table_name, []):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in FLOAT_COLS_BY_TABLE.get(table_name, []):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def sanitize_varchar_columns(df: pd.DataFrame, table_name: str, limits: dict[str, int]) -> pd.DataFrame:
    """Trim values that exceed DB VARCHAR limits to avoid insert failures."""
    for col, max_len in limits.items():
        if col not in df.columns:
            continue

        string_series = df[col].astype(str)
        too_long = df[col].notna() & (string_series.str.len() > max_len)
        trimmed_count = int(too_long.sum())
        if trimmed_count:
            print(f"    [WARN] Trimming {trimmed_count:,} values in {table_name}.{col} to {max_len} chars")
            df.loc[too_long, col] = string_series.loc[too_long].str.slice(0, max_len)

    return df


def find_file(directory: str, prefix: str) -> str | None:
    """Find a FAERS ASCII file by prefix (case-insensitive)."""
    for f in os.listdir(directory):
        if f.upper().startswith(prefix.upper()) and f.upper().endswith(".TXT"):
            return os.path.join(directory, f)
    return None


def read_faers_file(filepath: str, expected_cols: list) -> pd.DataFrame:
    """
    Read a FAERS ASCII pipe-delimited file with robust error handling.
    FAERS files use '$' as delimiter in older quarters, '|' in newer ones.
    """
    for sep in ["$", "|", "\t"]:
        try:
            df = pd.read_csv(
                filepath,
                sep=sep,
                encoding="latin-1",
                dtype=str,
                on_bad_lines="skip",
                low_memory=False
            )
            df.columns = [c.strip().lower() for c in df.columns]

            # Keep only expected columns that exist, fill missing ones with None
            available = [c for c in expected_cols if c in df.columns]
            df = df[available].copy()
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = None
            return df[expected_cols]
        except Exception:
            continue
    raise ValueError(f"Could not parse {filepath} with any known delimiter")


def ingest_quarter(quarter_label: str, extract_dir: str):
    """
    Ingest all 5 FAERS files for one quarter into PostgreSQL.
    Appends to existing tables - does not truncate.
    """
    engine = get_engine()
    varchar_limits_cache: dict[str, dict[str, int]] = {}

    # Walk into subdirectory if FAERS ZIP extracted into a subfolder
    ascii_dir = extract_dir
    for root, dirs, files in os.walk(extract_dir):
        txt_files = [f for f in files if f.upper().endswith(".TXT")]
        if len(txt_files) >= 3:
            ascii_dir = root
            break

    for prefix, (table_name, expected_cols) in FILE_CONFIG.items():
        filepath = find_file(ascii_dir, prefix)
        if filepath is None:
            print(f"  [WARN] {prefix} file not found in {ascii_dir}")
            continue

        print(f"  [INGEST] {prefix} -> {table_name}")
        df = read_faers_file(filepath, expected_cols)
        df["quarter"] = quarter_label

        if table_name not in varchar_limits_cache:
            varchar_limits_cache[table_name] = get_varchar_limits(engine, table_name)

        df = sanitize_numeric_columns(df, table_name)
        df = sanitize_varchar_columns(df, table_name, varchar_limits_cache[table_name])

        # Append to PostgreSQL table
        df.to_sql(
            table_name,
            engine,
            if_exists="append",
            index=False,
            chunksize=5000
        )
        print(f"    Loaded {len(df):,} rows")


def ingest_all_quarters(quarter_dirs: list[tuple[str, str]]):
    """
    Ingest all quarters. quarter_dirs is a list of (label, path) tuples.
    Example: [('2023Q1', 'data/raw/2023Q1'), ...]
    """
    for quarter_label, extract_dir in quarter_dirs:
        print(f"\n[INGEST {quarter_label}]")
        ingest_quarter(quarter_label, extract_dir)
