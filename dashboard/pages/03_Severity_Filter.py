import streamlit as st
from src.db import query_df
from dashboard.components.signal_table import render_signal_table

st.set_page_config(page_title="Severity Filter", layout="wide")
st.title("🚨 High-Severity Signal Monitor")
st.markdown(
    "Filter confirmed signals by outcome severity. "
    "'Death' and 'Life-Threatening' signals are the highest priority for pharmacovigilance review."
)

OUTCOME_LABELS = {
    "DE": "💀 Death",
    "LT": "⚠️ Life-Threatening",
    "HO": "🏥 Hospitalization",
    "DS": "♿ Disability",
    "CA": "👶 Congenital Anomaly",
    "RI": "🔧 Required Intervention",
    "OT": "📋 Other Serious",
}

selected_outcomes = st.multiselect(
    "Select outcome severity:",
    options=list(OUTCOME_LABELS.keys()),
    format_func=lambda x: OUTCOME_LABELS[x],
    default=["DE", "LT"]
)

soc_options = query_df(
    "SELECT DISTINCT soc_name FROM clean_reac WHERE soc_name IS NOT NULL ORDER BY soc_name"
)["soc_name"].tolist()
selected_soc = st.selectbox("Filter by System Organ Class (optional)", ["All"] + soc_options)

min_cases = st.slider("Minimum case count", 1, 100, 10)
top_n = st.slider("Number of results", 10, 200, 50)

if selected_outcomes:
    outcome_list = ", ".join([f"'{o}'" for o in selected_outcomes])
    soc_clause = f"AND r.soc_name = '{selected_soc}'" if selected_soc != "All" else ""

    query = f"""
        SELECT DISTINCT s.drug_name, s.reaction_pt, s.case_count, s.prr,
                        s.chi2, s.ror, s.ror_ci_lower, s.ror_ci_upper,
                        s.is_signal, r.soc_name
        FROM signal_results s
        INNER JOIN clean_reac r ON s.reaction_pt = r.reaction_pt
        INNER JOIN clean_outc o ON r.primaryid = o.primaryid
        WHERE s.quarter_cutoff = 'ALL'
          AND s.is_signal = TRUE
          AND s.case_count >= {min_cases}
          AND o.outc_cod IN ({outcome_list})
          {soc_clause}
        ORDER BY s.prr DESC
        LIMIT {top_n}
    """
    df = query_df(query)
    outcome_str = ", ".join([OUTCOME_LABELS[o] for o in selected_outcomes])
    render_signal_table(df, title=f"Signals with Outcome: {outcome_str}")
