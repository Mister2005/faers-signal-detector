import streamlit as st

st.set_page_config(
    page_title="FAERS Signal Detector",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("💊 FDA FAERS Pharmacovigilance Signal Detector")
st.markdown(
    """
    This tool detects drug safety signals from the **FDA Adverse Event Reporting System (FAERS)**
    using industry-standard pharmacovigilance methods: **Proportional Reporting Ratio (PRR)**
    and **Reporting Odds Ratio (ROR)**.

    Use the sidebar to navigate between views.
    """
)

st.info(
    "**Signal criteria (Evans et al. 2001):** PRR >= 2.0, Chi² >= 4.0, "
    "case count >= 3, ROR lower 95% CI > 1.0",
    icon="ℹ️"
)

# Summary metrics on home page
from src.db import query_df

col1, col2, col3, col4 = st.columns(4)

with col1:
    n = query_df("SELECT COUNT(DISTINCT primaryid) AS n FROM clean_demo").iloc[0, 0]
    st.metric("Total Reports", f"{n:,}")

with col2:
    n_drugs = query_df("SELECT COUNT(DISTINCT drug_name_clean) AS n FROM clean_drug").iloc[0, 0]
    st.metric("Unique Drugs", f"{n_drugs:,}")

with col3:
    n_reac = query_df("SELECT COUNT(DISTINCT reaction_pt) AS n FROM clean_reac").iloc[0, 0]
    st.metric("Unique Reactions", f"{n_reac:,}")

with col4:
    n_signals = query_df(
        "SELECT COUNT(*) AS n FROM signal_results WHERE is_signal = TRUE AND quarter_cutoff = 'ALL'"
    ).iloc[0, 0]
    st.metric("Confirmed Signals", f"{n_signals:,}")
