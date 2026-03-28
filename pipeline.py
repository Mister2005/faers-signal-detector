"""
Master pipeline script. Runs all steps in order.
Usage:
    python pipeline.py --all            # Full run: download, ingest, clean, signals
    python pipeline.py --skip-download  # Skip download (re-use existing ZIPs)
    python pipeline.py --signals-only   # Re-run signal computation only
"""
import argparse
import sys
from src.config import START_YEAR, END_YEAR, QUARTERS
from src.db import get_engine, run_sql
from src.download import download_all_quarters, get_all_quarters
from src.ingest import ingest_all_quarters
from src.clean import run_all_cleaning
from src.signals import compute_signals_for_quarter, save_signals, compute_and_save_all_quarters


def setup_database():
    """Create all tables if they don't exist."""
    print("[SETUP] Creating database tables...")
    with open("sql/create_tables.sql", "r") as f:
        sql = f.read()
    # Execute each statement separately
    for statement in sql.split(";"):
        stmt = statement.strip()
        if stmt:
            run_sql(stmt)

    # Backward-compatible migration for existing DBs created with VARCHAR(2).
    run_sql("ALTER TABLE raw_demo ALTER COLUMN sex TYPE VARCHAR(10)")
    print("  Tables ready.")


def get_quarter_labels() -> list[str]:
    return [f"{year}Q{q}" for year, q in get_all_quarters()]


def main():
    parser = argparse.ArgumentParser(description="FAERS Signal Detection Pipeline")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--skip-download", action="store_true", help="Skip data download")
    parser.add_argument("--signals-only", action="store_true", help="Recompute signals only")
    args = parser.parse_args()

    print("=" * 60)
    print(" FAERS Signal Detection Pipeline")
    print("=" * 60)

    setup_database()

    if args.signals_only:
        quarters = get_quarter_labels()
        compute_and_save_all_quarters(quarters)
        return

    # Step 1: Download
    if not args.skip_download:
        print("\n[STEP 1] Downloading FAERS data...")
        quarter_dirs = download_all_quarters()
    else:
        print("\n[STEP 1] Skipping download.")
        import os
        quarter_dirs = []
        for year, q in get_all_quarters():
            label = f"{year}Q{q}"
            path = f"data/raw/{label}"
            if os.path.exists(path):
                quarter_dirs.append((label, path))
            else:
                print(f"  [WARN] Expected directory not found: {path}")

    # Step 2: Ingest
    print("\n[STEP 2] Ingesting raw data into PostgreSQL...")
    ingest_all_quarters(quarter_dirs)

    # Step 3: Clean
    print("\n[STEP 3] Cleaning and standardizing data...")
    run_all_cleaning()

    # Step 4: Compute signals
    print("\n[STEP 4] Computing pharmacovigilance signals...")
    quarters = get_quarter_labels()
    compute_and_save_all_quarters(quarters)

    print("\n" + "=" * 60)
    print(" Pipeline complete. Run dashboard with:")
    print("   streamlit run dashboard/app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
