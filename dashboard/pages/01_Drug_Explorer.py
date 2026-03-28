import streamlit as st
import sys
from pathlib import Path
import plotly.express as px

PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "src").exists() and (p / "dashboard").exists()),
    Path(__file__).resolve().parent,
)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.styles import apply_plotly_theme
from dashboard.ui import inject_global_styles, render_page_hero, render_panel, render_sidebar
from src.db import query_df
from src.trends import get_top_signals
from dashboard.components.signal_table import render_signal_table

st.set_page_config(page_title="Drug Explorer", layout="wide")
inject_global_styles()

render_page_hero(
    title="Drug Explorer",
    subtitle="Search generic or brand names and inspect ranked adverse-event signals for fast triage.",
    kicker="Discovery",
)
render_panel(
    title="How This View Helps",
    body="Filter by case burden, inspect PRR intensity, and prioritize severe outcomes with color-coded signal states.",
)


@st.cache_data(ttl=300)
def get_common_sidebar_stats() -> tuple[int, int, int, int, str]:
    total_reports = int(query_df("SELECT COUNT(DISTINCT primaryid) AS n FROM clean_demo").iloc[0, 0])
    unique_drugs = int(query_df("SELECT COUNT(DISTINCT drug_name_clean) AS n FROM clean_drug").iloc[0, 0])
    unique_reactions = int(query_df("SELECT COUNT(DISTINCT reaction_pt) AS n FROM clean_reac").iloc[0, 0])
    confirmed_signals = int(query_df("SELECT COUNT(*) AS n FROM signal_results WHERE quarter_cutoff='ALL' AND is_signal=TRUE").iloc[0, 0])
    quarter_window = query_df(
        "SELECT MIN(quarter_cutoff) AS min_q, MAX(quarter_cutoff) AS max_q FROM signal_results WHERE quarter_cutoff != 'ALL'"
    ).iloc[0]
    window = f"{quarter_window['min_q']} - {quarter_window['max_q']}" if quarter_window['min_q'] else "N/A"
    return total_reports, unique_drugs, unique_reactions, confirmed_signals, window


_reports, _drugs, _reactions, _signals, _window = get_common_sidebar_stats()
render_sidebar(Path(__file__).stem, _reports, _drugs, _reactions, _signals, _window, "Mar 28 2026")

# --- Search box
drug_input = st.text_input(
    "Enter drug name (generic or brand):",
    placeholder="e.g. ATORVASTATIN, LIPITOR, METFORMIN"
).upper().strip()

col1, col2 = st.columns([2, 1])
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
        st.info(
            f"Found **{len(df)}** adverse event associations for **{df['drug_name'].iloc[0]}**. "
            f"Confirmed signals: **{signal_count}** (min cases: {min_cases})."
        )

        profile = df.iloc[0]
        death_assoc = query_df(
            """
            SELECT COUNT(*) AS n
            FROM clean_reac r
            JOIN clean_outc o ON r.primaryid = o.primaryid
            WHERE r.reaction_pt IN (
                SELECT DISTINCT reaction_pt FROM signal_results WHERE drug_name = :drug AND quarter_cutoff='ALL'
            ) AND o.outc_cod='DE'
            """,
            {"drug": profile["drug_name"]},
        ).iloc[0, 0]
        st.markdown(
            f"""
            <div style='background:linear-gradient(135deg,#0F1629,#111827);border:1px solid #1E2D4A;border-left:4px solid #3B82F6;border-radius:10px;padding:14px;margin-bottom:10px;'>
                <div style='font-size:22px;font-weight:700;color:#E8EDF5;'>{profile['drug_name']}</div>
                <div style='font-size:12px;color:#4A5A7A;margin-top:2px;'>Focused drug profile and signal summary.</div>
                <div style='margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;'>
                    <span style='background:#1E2D4A;color:#A8C4F0;padding:4px 8px;border-radius:12px;font-size:12px;'>Total Associations: {len(df):,}</span>
                    <span style='background:#2A200A;color:#F5C518;padding:4px 8px;border-radius:12px;font-size:12px;'>Signals: {int(signal_count):,}</span>
                    <span style='background:#3D0A0F;color:#FF8A8F;padding:4px 8px;border-radius:12px;font-size:12px;'>Death-assoc: {int(death_assoc):,}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # SOC breakdown pie chart
        if "soc_name" in df.columns and not df["soc_name"].isna().all():
            soc_counts = df.groupby("soc_name").size().reset_index(name="count")
            fig = px.pie(
                soc_counts.sort_values("count", ascending=False).head(10),
                names="soc_name",
                values="count",
                hole=0.6,
                title="Signal Distribution by SOC",
                color_discrete_sequence=["#3B82F6", "#14B8A6", "#F5C518", "#8B5CF6", "#FF8C00", "#EC4899", "#10B981", "#F43F5E"],
            )
            fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} signals (%{percent})<extra></extra>")
            fig.update_layout(legend=dict(orientation="h", y=-0.2), margin=dict(t=60, b=40, l=20, r=20))
            apply_plotly_theme(fig, height=360)
            st.plotly_chart(fig, use_container_width=True)

        render_signal_table(df, title=f"Signals for {df['drug_name'].iloc[0]}")

else:
    st.markdown("### Top 50 Confirmed Signals")
    df_top = get_top_signals(n=50, min_cases=5)
    render_signal_table(df_top, title="Top Signals by PRR")
