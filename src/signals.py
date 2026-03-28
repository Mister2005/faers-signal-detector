import numpy as np
import pandas as pd
from scipy import stats
from src.db import get_engine, run_sql, query_df
from src.config import (
    PRR_THRESHOLD, CHI2_THRESHOLD, MIN_CASE_COUNT, ROR_CI_LOWER_THRESHOLD
)


def compute_contingency(a: int, b: int, c: int, d: int) -> dict:
    """
    Core signal detection math for a single drug-event pair.

    Contingency table:
                    Event Y    All other events
    Drug X             a            b
    All other drugs    c            d

    Returns dict with PRR, Chi2, ROR, ROR 95% CI, and signal flag.
    Returns None if computation is invalid (zero denominators).
    """
    if (a + b) == 0 or (c + d) == 0 or b == 0 or c == 0:
        return None

    # PRR
    prr = (a / (a + b)) / (c / (c + d))

    # Chi-squared (Yates-corrected for small counts)
    n = a + b + c + d
    expected_a = ((a + b) * (a + c)) / n
    chi2 = ((abs(a - expected_a) - 0.5) ** 2) / expected_a if expected_a > 0 else 0

    # ROR and 95% CI
    if b == 0 or c == 0:
        ror = np.inf
        ror_ci_lower = np.inf
        ror_ci_upper = np.inf
    else:
        ror = (a * d) / (b * c)
        log_ror = np.log(ror) if ror > 0 else -np.inf
        se_log_ror = np.sqrt(1/a + 1/b + 1/c + 1/d)
        ror_ci_lower = np.exp(log_ror - 1.96 * se_log_ror)
        ror_ci_upper = np.exp(log_ror + 1.96 * se_log_ror)

    is_signal = bool(
        a >= MIN_CASE_COUNT and
        prr >= PRR_THRESHOLD and
        chi2 >= CHI2_THRESHOLD and
        ror_ci_lower > ROR_CI_LOWER_THRESHOLD
    )

    return {
        "prr": round(prr, 4),
        "chi2": round(chi2, 4),
        "ror": round(ror, 4),
        "ror_ci_lower": round(ror_ci_lower, 4),
        "ror_ci_upper": round(ror_ci_upper, 4),
        "is_signal": is_signal,
    }


def compute_signals_for_quarter(quarter_cutoff: str | None = None) -> pd.DataFrame:
    """
    Compute PRR/ROR for all drug-event pairs.
    If quarter_cutoff is given (e.g. '2023Q2'), only use reports up to that quarter.
    If None, use all available data.

    Returns a DataFrame with one row per drug-event pair.
    """
    # Build quarter filter clause
    if quarter_cutoff:
        drug_quarter_filter = f"AND d.quarter <= '{quarter_cutoff}'"
        reac_quarter_filter = f"AND r.quarter <= '{quarter_cutoff}'"
        clean_drug_quarter_filter = f"AND quarter <= '{quarter_cutoff}'"
        clean_reac_quarter_filter = f"AND quarter <= '{quarter_cutoff}'"
    else:
        drug_quarter_filter = ""
        reac_quarter_filter = ""
        clean_drug_quarter_filter = ""
        clean_reac_quarter_filter = ""

    # Step 1: Get drug-event co-occurrence counts (= a)
    print("  Computing drug-event co-occurrence counts...")
    co_occurrence_sql = f"""
        SELECT
            d.drug_name_clean AS drug_name,
            r.reaction_pt,
            COUNT(DISTINCT d.primaryid) AS case_count
        FROM clean_drug d
        INNER JOIN clean_reac r ON d.primaryid = r.primaryid
        WHERE d.drug_name_clean != 'UNKNOWN'
          AND r.reaction_pt IS NOT NULL
                    {drug_quarter_filter}
                    {reac_quarter_filter}
        GROUP BY d.drug_name_clean, r.reaction_pt
        HAVING COUNT(DISTINCT d.primaryid) >= {MIN_CASE_COUNT}
    """
    df_co = query_df(co_occurrence_sql)
    print(f"    Found {len(df_co):,} drug-event pairs with >= {MIN_CASE_COUNT} cases")

    # Step 2: Drug totals (= a + b, reports mentioning drug X at all)
    print("  Computing drug totals...")
    drug_totals_sql = f"""
        SELECT drug_name_clean AS drug_name, COUNT(DISTINCT primaryid) AS drug_total
        FROM clean_drug
        WHERE drug_name_clean != 'UNKNOWN' {clean_drug_quarter_filter}
        GROUP BY drug_name_clean
    """
    drug_totals = query_df(drug_totals_sql).set_index("drug_name")["drug_total"]

    # Step 3: Event totals (= a + c, reports mentioning reaction Y at all)
    print("  Computing event totals...")
    event_totals_sql = f"""
        SELECT reaction_pt, COUNT(DISTINCT primaryid) AS event_total
        FROM clean_reac
        WHERE 1=1 {clean_reac_quarter_filter}
        GROUP BY reaction_pt
    """
    event_totals = query_df(event_totals_sql).set_index("reaction_pt")["event_total"]

    # Step 4: Total unique reports in database (= N)
    total_sql = f"SELECT COUNT(DISTINCT primaryid) AS n FROM clean_demo"
    if quarter_cutoff:
        total_sql = f"SELECT COUNT(DISTINCT primaryid) AS n FROM clean_demo WHERE quarter <= '{quarter_cutoff}'"
    N = query_df(total_sql).iloc[0, 0]
    print(f"    Total reports (N): {N:,}")

    # Step 5: Compute signal metrics for each pair
    print("  Computing PRR / ROR for all pairs...")
    results = []
    for _, row in df_co.iterrows():
        drug = row["drug_name"]
        event = row["reaction_pt"]
        a = int(row["case_count"])

        a_plus_b = int(drug_totals.get(drug, 0))
        a_plus_c = int(event_totals.get(event, 0))

        b = a_plus_b - a
        c = a_plus_c - a
        d = int(N) - a - b - c

        if d < 0:
            continue

        metrics = compute_contingency(a, b, c, d)
        if metrics is None:
            continue

        results.append({
            "drug_name": drug,
            "reaction_pt": event,
            "quarter_cutoff": quarter_cutoff or "ALL",
            "case_count": a,
            "drug_total": a_plus_b,
            "event_total": a_plus_c,
            "total_reports": int(N),
            **metrics
        })

    return pd.DataFrame(results)


def save_signals(df: pd.DataFrame):
    """Write signal results to PostgreSQL, replacing existing rows for same quarter."""
    if df.empty:
        print("  No signals to save.")
        return

    engine = get_engine()
    quarter = df["quarter_cutoff"].iloc[0]

    # Delete existing rows for this quarter cutoff before inserting
    run_sql(f"DELETE FROM signal_results WHERE quarter_cutoff = '{quarter}'")

    df.to_sql(
        "signal_results", engine,
        if_exists="append", index=False,
        method="multi", chunksize=2000
    )
    signals_count = df["is_signal"].sum()
    print(f"  Saved {len(df):,} pairs ({signals_count} confirmed signals) for {quarter}")


def compute_and_save_all_quarters(quarters: list[str]):
    """
    Compute signals cumulatively for each quarter.
    '2023Q1' uses only Q1 data, '2023Q2' uses Q1+Q2, etc.
    This enables trend analysis on the dashboard.
    """
    for i, q in enumerate(sorted(quarters)):
        print(f"\n[SIGNALS] Computing for cumulative data up to {q}...")
        df = compute_signals_for_quarter(quarter_cutoff=q)
        save_signals(df)

    # Also compute for all data combined
    print(f"\n[SIGNALS] Computing for ALL data...")
    df_all = compute_signals_for_quarter(quarter_cutoff=None)
    save_signals(df_all)
