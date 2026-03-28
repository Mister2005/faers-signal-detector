import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go

PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "src").exists() and (p / "dashboard").exists()),
    Path(__file__).resolve().parent,
)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.styles import apply_plotly_theme
from dashboard.ui import (
    inject_global_styles,
    render_kpi,
    render_page_hero,
    render_panel,
    render_sidebar,
)
from src.db import query_df

st.set_page_config(
    page_title="FAERS Signal Detector",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_global_styles()

render_page_hero(
    title="FDA FAERS Pharmacovigilance Signal Detector",
    subtitle="Detecting drug safety signals from real-world adverse event reports using PRR, ROR, and Chi-square.",
    kicker="Clinical Signal Monitoring Terminal",
)

render_panel(
    title="Signal Criteria (Evans et al. 2001)",
    body="PRR >= 2.0, Chi-square >= 4.0, case count >= 3, and lower 95% ROR confidence bound > 1.0.",
)

@st.cache_data(ttl=300)
def get_home_metrics() -> tuple[int, int, int, int, int]:
    total_reports = query_df("SELECT COUNT(DISTINCT primaryid) AS n FROM clean_demo").iloc[0, 0]
    unique_drugs = query_df("SELECT COUNT(DISTINCT drug_name_clean) AS n FROM clean_drug").iloc[0, 0]
    unique_reactions = query_df("SELECT COUNT(DISTINCT reaction_pt) AS n FROM clean_reac").iloc[0, 0]
    confirmed_signals = query_df(
        "SELECT COUNT(*) AS n FROM signal_results WHERE is_signal = TRUE AND quarter_cutoff = 'ALL'"
    ).iloc[0, 0]
    death_associated = query_df(
        """
        SELECT COUNT(*) AS n
        FROM signal_results s
        WHERE s.quarter_cutoff = 'ALL'
          AND s.is_signal = TRUE
          AND EXISTS (
              SELECT 1
              FROM clean_reac r
              JOIN clean_outc o ON r.primaryid = o.primaryid
              WHERE r.reaction_pt = s.reaction_pt
                AND o.outc_cod = 'DE'
          )
        """
    ).iloc[0, 0]
    return int(total_reports), int(unique_drugs), int(unique_reactions), int(confirmed_signals), int(death_associated)


@st.cache_data(ttl=300)
def get_quarter_window() -> str:
    row = query_df(
        "SELECT MIN(quarter_cutoff) AS min_q, MAX(quarter_cutoff) AS max_q FROM signal_results WHERE quarter_cutoff != 'ALL'"
    ).iloc[0]
    if row["min_q"] and row["max_q"]:
        return f"{row['min_q']} - {row['max_q']}"
    return "N/A"


@st.cache_data(ttl=300)
def get_soc_signal_breakdown():
    return query_df(
        """
        WITH death_reactions AS (
            SELECT DISTINCT r.reaction_pt
            FROM clean_reac r
            JOIN clean_outc o ON r.primaryid = o.primaryid
            WHERE o.outc_cod = 'DE'
        )
        SELECT cr.soc_name,
               COUNT(*) AS signal_count,
               SUM(CASE WHEN s.reaction_pt IN (SELECT reaction_pt FROM death_reactions) THEN 1 ELSE 0 END) AS death_signal_count
        FROM signal_results s
        LEFT JOIN (
            SELECT DISTINCT reaction_pt, soc_name
            FROM clean_reac
            WHERE soc_name IS NOT NULL
        ) cr ON s.reaction_pt = cr.reaction_pt
        WHERE s.quarter_cutoff = 'ALL' AND s.is_signal = TRUE
        GROUP BY cr.soc_name
        ORDER BY signal_count DESC
        LIMIT 10
        """
    )


try:
    total_reports, unique_drugs, unique_reactions, confirmed_signals, death_associated = get_home_metrics()
    quarter_window = get_quarter_window()
    soc_df = get_soc_signal_breakdown()
except Exception as exc:
    st.error(
        "Unable to query dashboard metrics. Verify DB credentials in .env and rerun the data pipeline.")
    st.exception(exc)
    st.stop()

render_sidebar(
    current_route=Path(__file__).stem,
    total_reports=total_reports,
    unique_drugs=unique_drugs,
    unique_reactions=unique_reactions,
    confirmed_signals=confirmed_signals,
    quarter_window=quarter_window,
    updated_at="Mar 28 2026",
)

col1, col2, col3, col4 = st.columns(4, gap="small")

with col1:
    render_kpi("Total Reports", f"{total_reports:,}")

with col2:
    render_kpi("Unique Drugs", f"{unique_drugs:,}")

with col3:
    render_kpi("Confirmed Signals", f"{confirmed_signals:,}")

with col4:
    render_kpi("Death-Associated", f"{death_associated:,}")

st.markdown("<div class='section-title'>Confirmed Signals by Body System</div>", unsafe_allow_html=True)
if not soc_df.empty:
    highlight_soc = soc_df.sort_values("death_signal_count", ascending=False).iloc[0]["soc_name"]
    colors = ["#FF3B47" if s == highlight_soc else "#3B82F6" for s in soc_df["soc_name"]]
    fig_soc = go.Figure(
        go.Bar(
            x=soc_df["signal_count"],
            y=soc_df["soc_name"],
            orientation="h",
            marker=dict(color=colors),
            hovertemplate="<b>%{y}</b><br>Signals: %{x}<extra></extra>",
        )
    )
    fig_soc.update_layout(
        title="Confirmed Signals by Body System",
        xaxis_title="Confirmed Signal Count",
        yaxis_title="SOC",
        yaxis=dict(autorange="reversed"),
        height=360,
    )
    fig_soc.update_xaxes(showgrid=True, griddash="dash", gridcolor="#1E2D4A")
    apply_plotly_theme(fig_soc)
    st.plotly_chart(fig_soc, use_container_width=True)

st.markdown("<div class='section-title'>How to Use This Dashboard</div>", unsafe_allow_html=True)
st.markdown(
    "1. Use **Drug Explorer** to search a drug and inspect strongest adverse-event associations.\n"
    "2. Use **Signal Trends** to track PRR/ROR movement over cumulative quarters.\n"
    "3. Use **Severity Filter** to prioritize high-impact outcomes like death and life-threatening reports."
)
