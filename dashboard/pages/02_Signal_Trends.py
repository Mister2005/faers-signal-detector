import streamlit as st
import sys
from pathlib import Path

PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "src").exists() and (p / "dashboard").exists()),
    Path(__file__).resolve().parent,
)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.ui import inject_global_styles, render_page_hero, render_panel
from src.db import query_df
from src.trends import get_prr_trend, get_available_quarters
from dashboard.components.trend_chart import render_trend_chart
from dashboard.ui import render_sidebar

st.set_page_config(page_title="Signal Trends", layout="wide")
inject_global_styles()

render_page_hero(
    title="Signal Trend Viewer",
    subtitle="Track quarter-wise momentum for a specific drug-event pair and monitor confidence movement over time.",
    kicker="Temporal Analysis",
)
render_panel(
    title="Interpretation Tip",
    body="A persistent PRR above 2.0 with increasing case counts and ROR confidence bounds above 1.0 indicates a stronger safety signal.",
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

# Get all available confirmed signal pairs for dropdowns
@st.cache_data(ttl=300)
def get_signal_pairs():
    return query_df(
        "SELECT DISTINCT drug_name, reaction_pt FROM signal_results "
        "WHERE is_signal = TRUE AND quarter_cutoff = 'ALL' ORDER BY drug_name LIMIT 2000"
    )


signal_pairs = get_signal_pairs()

if signal_pairs.empty:
    st.warning("No signal data found. Run the pipeline first.")
    st.stop()

left_col, right_col = st.columns([2, 3], gap="large")

with left_col:
    drug_options = sorted(signal_pairs["drug_name"].unique().tolist())
    selected_drug = st.selectbox("Select Drug", drug_options)

    reaction_options = sorted(
        signal_pairs[signal_pairs["drug_name"] == selected_drug]["reaction_pt"].tolist()
    )
    selected_reaction = st.selectbox("Select Adverse Event", reaction_options)

if selected_drug and selected_reaction:
    df_trend = get_prr_trend(selected_drug, selected_reaction)
    if not df_trend.empty:
        latest = df_trend.iloc[-1]
        first_signal = df_trend[df_trend["is_signal"] == True]
        first_q = first_signal.iloc[0]["quarter_cutoff"] if not first_signal.empty else "Not reached"
        status = "CONFIRMED" if bool(latest["is_signal"]) else "WATCH"
        status_color = "#F5C518" if bool(latest["is_signal"]) else "#4FC3F7"

        with left_col:
            st.markdown(
                f"""
                <div style='background:linear-gradient(135deg,#111827,#0F1629);border:1px solid #1E2D4A;border-left:4px solid #F5C518;border-radius:10px;padding:16px;margin-top:16px;'>
                    <div style='color:#8B9DC3;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px;'>Signal Summary</div>
                    <div style='display:flex;justify-content:space-between;border-bottom:1px solid #1E2D4A;padding:6px 0;'><span style='color:#4A5A7A;font-size:12px;'>Status</span><span style='color:{status_color};font-weight:600;font-size:12px;'>{status}</span></div>
                    <div style='display:flex;justify-content:space-between;border-bottom:1px solid #1E2D4A;padding:6px 0;'><span style='color:#4A5A7A;font-size:12px;'>First detected</span><span style='color:#A8C4F0;font-size:12px;'>{first_q}</span></div>
                    <div style='display:flex;justify-content:space-between;border-bottom:1px solid #1E2D4A;padding:6px 0;'><span style='color:#4A5A7A;font-size:12px;'>PRR (latest)</span><span style='color:#14B8A6;font-size:12px;'>{latest['prr']:.2f}</span></div>
                    <div style='display:flex;justify-content:space-between;border-bottom:1px solid #1E2D4A;padding:6px 0;'><span style='color:#4A5A7A;font-size:12px;'>ROR (latest)</span><span style='color:#8B5CF6;font-size:12px;'>{latest['ror']:.2f}</span></div>
                    <div style='display:flex;justify-content:space-between;padding:6px 0;'><span style='color:#4A5A7A;font-size:12px;'>Total cases</span><span style='color:#A8C4F0;font-size:12px;'>{int(latest['case_count']):,}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right_col:
            render_trend_chart(df_trend, selected_drug, selected_reaction)
            with st.expander("View raw trend data"):
                st.dataframe(df_trend, use_container_width=True)
