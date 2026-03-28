import pandas as pd
from src.db import query_df
from src.config import START_YEAR, END_YEAR, QUARTERS


def get_available_quarters() -> list[str]:
    """Return all quarter labels present in signal_results table."""
    df = query_df(
        "SELECT DISTINCT quarter_cutoff FROM signal_results "
        "WHERE quarter_cutoff != 'ALL' ORDER BY quarter_cutoff"
    )
    return df["quarter_cutoff"].tolist()


def get_prr_trend(drug_name: str, reaction_pt: str) -> pd.DataFrame:
    """
    Return PRR, ROR, and case count over time for a drug-event pair.
    One row per quarter, ordered chronologically.
    """
    df = query_df(
        """
        SELECT quarter_cutoff, case_count, prr, ror, ror_ci_lower, ror_ci_upper,
               chi2, is_signal
        FROM signal_results
        WHERE drug_name = :drug
          AND reaction_pt = :reaction
          AND quarter_cutoff != 'ALL'
        ORDER BY quarter_cutoff
        """,
        {"drug": drug_name.upper(), "reaction": reaction_pt.upper()}
    )
    return df


def get_top_signals(
    n: int = 50,
    min_cases: int = 5,
    soc_filter: str = None,
    serious_only: bool = False
) -> pd.DataFrame:
    """
    Return the top N confirmed signals from the latest cumulative quarter,
    ranked by PRR descending.
    """
    soc_clause = ""
    params = {"n": n, "min_cases": min_cases}

    latest_quarter = query_df(
        "SELECT MAX(quarter_cutoff) AS q FROM signal_results WHERE quarter_cutoff != 'ALL'"
    ).iloc[0, 0]

    base_sql = f"""
        SELECT s.drug_name, s.reaction_pt, s.case_count, s.prr, s.ror,
               s.ror_ci_lower, s.ror_ci_upper, s.chi2, s.is_signal,
               r.soc_name
        FROM signal_results s
        LEFT JOIN (
            SELECT DISTINCT reaction_pt, soc_name FROM clean_reac
        ) r ON s.reaction_pt = r.reaction_pt
        WHERE s.quarter_cutoff = '{latest_quarter}'
          AND s.is_signal = TRUE
          AND s.case_count >= :min_cases
        {f"AND r.soc_name = :soc" if soc_filter else ""}
        ORDER BY s.prr DESC
        LIMIT :n
    """
    if soc_filter:
        params["soc"] = soc_filter

    return query_df(base_sql, params)
