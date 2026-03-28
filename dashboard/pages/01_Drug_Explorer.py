import streamlit as st
from src.db import query_df
from src.trends import get_top_signals
from dashboard.components.signal_table import render_signal_table

st.set_page_config(page_title="Drug Explorer", layout="wide")
st.title("🔍 Drug Explorer")
st.markdown("Search any drug and see its top adverse event signals ranked by PRR.")

# --- Search box
drug_input = st.text_input(
    "Enter drug name (generic or brand):",
    placeholder="e.g. ATORVASTATIN, LIPITOR, METFORMIN"
).upper().strip()

col1, col2 = st.columns([1, 1])
with col1:
    min_cases = st.slider("Minimum case count", 1, 50, 3)
with col2:
    show_all = st.checkbox("Show non-signals too (PRR < threshold)", value=False)

if drug_input:
    query = """
        SELECT s.drug_name, s.reaction_pt, s.case_count, s.prr, s.chi2,
               s.ror, s.ror_ci_lower, s.ror_ci_upper, s.is_signal, r.soc_name
        FROM signal_results s
        LEFT JOIN (SELECT DISTINCT reaction_pt, soc_name FROM clean_reac) r
               ON s.reaction_pt = r.reaction_pt
        WHERE s.quarter_cutoff = 'ALL'
          AND s.drug_name ILIKE :drug
          AND s.case_count >= :min_cases
          {signal_clause}
        ORDER BY s.prr DESC
        LIMIT 100
    """.format(signal_clause="" if show_all else "AND s.is_signal = TRUE")

    df = query_df(query, {"drug": f"%{drug_input}%", "min_cases": min_cases})

    if df.empty:
        st.info(f"No {'signals' if not show_all else 'results'} found for '{drug_input}'. "
                f"Try a different name or lower the minimum case count.")
    else:
        # Summary banner
        signal_count = df["is_signal"].sum()
        st.success(
            f"Found **{len(df)}** adverse event associations for **{df['drug_name'].iloc[0]}** "
            f"- **{signal_count}** confirmed signals (PRR >= 2, Chi² >= 4, cases >= {min_cases})"
        )

        # SOC breakdown pie chart
        if "soc_name" in df.columns and not df["soc_name"].isna().all():
            import plotly.express as px
            soc_counts = df.groupby("soc_name").size().reset_index(name="count")
            fig = px.pie(soc_counts, names="soc_name", values="count",
                         title="Signals by System Organ Class")
            st.plotly_chart(fig, use_container_width=True)

        render_signal_table(df, title=f"Signals for {df['drug_name'].iloc[0]}")

else:
    st.markdown("### Top 50 Confirmed Signals (All Data)")
    df_top = get_top_signals(n=50, min_cases=5)
    render_signal_table(df_top, title="Top Signals by PRR")
