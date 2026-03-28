import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "src").exists() and (p / "dashboard").exists()),
    Path(__file__).resolve().parent,
)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.styles import apply_plotly_theme
from dashboard.ui import inject_global_styles, render_page_hero, render_panel, render_sidebar
from src.db import query_df
from dashboard.components.signal_table import render_signal_table


def _sparkline(values: list[float]) -> str:
    if not values:
        return "----"
    bars = "▁▂▃▄▅▆▇█"
    min_v, max_v = min(values), max(values)
    if max_v == min_v:
        return bars[3] * len(values)
    out = []
    for v in values:
        idx = int((v - min_v) / (max_v - min_v) * (len(bars) - 1))
        out.append(bars[idx])
    return "".join(out)


def _get_trend_sparklines(df):
    pairs = df[["drug_name", "reaction_pt"]].drop_duplicates().reset_index(drop=True)
    if pairs.empty:
        return {}

    values_sql = []
    params = {}
    for i, row in pairs.iterrows():
        values_sql.append(f"(:d{i}, :r{i})")
        params[f"d{i}"] = row["drug_name"]
        params[f"r{i}"] = row["reaction_pt"]

    trend_query = f"""
        WITH pairs(drug_name, reaction_pt) AS (
            VALUES {', '.join(values_sql)}
        ), ranked AS (
            SELECT s.drug_name, s.reaction_pt, s.prr,
                   ROW_NUMBER() OVER (
                       PARTITION BY s.drug_name, s.reaction_pt
                       ORDER BY s.quarter_cutoff DESC
                   ) AS rn
            FROM signal_results s
            JOIN pairs p
              ON s.drug_name = p.drug_name AND s.reaction_pt = p.reaction_pt
            WHERE s.quarter_cutoff != 'ALL'
        )
        SELECT drug_name, reaction_pt, prr, rn
        FROM ranked
        WHERE rn <= 4
        ORDER BY drug_name, reaction_pt, rn DESC
    """
    tdf = query_df(trend_query, params)
    if tdf.empty:
        return {}

    grouped = {}
    for _, row in tdf.iterrows():
        key = (row["drug_name"], row["reaction_pt"])
        grouped.setdefault(key, []).append(float(row["prr"]))

    return {k: _sparkline(v[-4:]) for k, v in grouped.items()}

st.set_page_config(page_title="Severity Filter", layout="wide")
inject_global_styles()

render_page_hero(
    title="High-Severity Signal Monitor",
    subtitle="Prioritize critical outcomes to surface safety signals that need urgent pharmacovigilance review.",
    kicker="Risk Prioritization",
)
render_panel(
    title="Triage Strategy",
    body="Start with Death and Life-Threatening outcomes, then expand to Hospitalization and Disability to widen clinical coverage.",
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

OUTCOME_LABELS = {
    "DE": "Death",
    "LT": "Life-Threatening",
    "HO": "Hospitalization",
    "DS": "Disability",
    "CA": "Congenital Anomaly",
    "RI": "Required Intervention",
    "OT": "Other Serious",
}

selected_outcomes = st.multiselect(
    "Select outcome severity:",
    options=list(OUTCOME_LABELS.keys()),
    format_func=lambda x: OUTCOME_LABELS[x],
    default=["DE", "LT"],
)


@st.cache_data(ttl=300)
def get_soc_options():
    return query_df(
        "SELECT DISTINCT soc_name FROM clean_reac WHERE soc_name IS NOT NULL ORDER BY soc_name"
    )["soc_name"].tolist()


soc_options = get_soc_options()
selected_soc = st.selectbox("Filter by System Organ Class (optional)", ["All"] + soc_options)

left, right = st.columns(2)
with left:
    min_cases = st.slider("Minimum case count", 1, 100, 10)
with right:
    top_n = st.slider("Number of results", 10, 200, 50)

if selected_outcomes:
    if "DE" in selected_outcomes or "LT" in selected_outcomes:
        st.markdown(
            """
            <div style='background:linear-gradient(90deg, #3D0A0F 0%, #1A0508 100%);border:1px solid #FF3B47;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;gap:12px;'>
                <span style='font-size:11px;color:#FF8A8F;letter-spacing:.12em;text-transform:uppercase;'>Alert</span>
                <div>
                    <div style='color:#FF3B47;font-weight:700;font-size:13px;'>HIGH SEVERITY SIGNALS - REVIEW REQUIRED</div>
                    <div style='color:#FF8A8F;font-size:11px;margin-top:2px;'>Showing signals associated with death or life-threatening outcomes.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    outcome_list = ", ".join([f":o{i}" for i in range(len(selected_outcomes))])
    params = {
        "min_cases": min_cases,
        "top_n": top_n,
    }
    params.update({f"o{i}": outcome for i, outcome in enumerate(selected_outcomes)})

    soc_clause = ""
    if selected_soc != "All":
        soc_clause = "AND r.soc_name = :soc"
        params["soc"] = selected_soc

    query = f"""
        SELECT DISTINCT s.drug_name, s.reaction_pt, s.case_count, s.prr,
                        s.chi2, s.ror, s.ror_ci_lower, s.ror_ci_upper,
                        s.is_signal, r.soc_name
        FROM signal_results s
        INNER JOIN clean_reac r ON s.reaction_pt = r.reaction_pt
        INNER JOIN clean_outc o ON r.primaryid = o.primaryid
        WHERE s.quarter_cutoff = 'ALL'
          AND s.is_signal = TRUE
          AND s.case_count >= :min_cases
          AND o.outc_cod IN ({outcome_list})
          {soc_clause}
        ORDER BY s.prr DESC
        LIMIT :top_n
    """

    df = query_df(query, params)
    if not df.empty:
        trend_map = _get_trend_sparklines(df)
        df["trend_last4"] = [
            trend_map.get((r["drug_name"], r["reaction_pt"]), "----")
            for _, r in df.iterrows()
        ]
    outcome_str = ", ".join([OUTCOME_LABELS[o] for o in selected_outcomes])
    render_signal_table(df, title=f"Signals with Outcome: {outcome_str}")

    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            fig_hist = go.Figure(
                go.Histogram(
                    x=df["prr"],
                    nbinsx=20,
                    marker=dict(color="#3B82F6", line=dict(color="#1E2D4A", width=1)),
                    opacity=0.92,
                )
            )
            fig_hist.add_vline(x=2.0, line_dash="dash", line_color="#F5C518", annotation_text="Threshold")
            fig_hist.update_layout(title="PRR Distribution - Filtered Signals", xaxis_title="PRR Value", yaxis_title="Signal Count")
            apply_plotly_theme(fig_hist, height=320)
            st.plotly_chart(fig_hist, use_container_width=True)

        with c2:
            outc_df = query_df(
                f"""
                SELECT o.outc_cod, COUNT(*) AS n
                FROM clean_outc o
                WHERE o.outc_cod IN ({outcome_list})
                GROUP BY o.outc_cod
                ORDER BY n DESC
                """,
                {f"o{i}": outcome for i, outcome in enumerate(selected_outcomes)},
            )
            if not outc_df.empty:
                mapping = {
                    "DE": "Death",
                    "LT": "Life-Threatening",
                    "HO": "Hospitalization",
                    "DS": "Disability",
                    "CA": "Congenital",
                    "RI": "Intervention",
                    "OT": "Other",
                }
                outc_df["label"] = outc_df["outc_cod"].map(mapping).fillna(outc_df["outc_cod"])
                fig_donut = px.pie(
                    outc_df,
                    names="label",
                    values="n",
                    hole=0.55,
                    title="Case Distribution by Outcome",
                    color="label",
                    color_discrete_map={
                        "Death": "#FF3B47",
                        "Life-Threatening": "#FF8C00",
                        "Hospitalization": "#3B82F6",
                        "Disability": "#8B5CF6",
                        "Congenital": "#10B981",
                        "Intervention": "#14B8A6",
                        "Other": "#374151",
                    },
                )
                fig_donut.update_traces(textinfo="percent+label")
                apply_plotly_theme(fig_donut, height=320)
                st.plotly_chart(fig_donut, use_container_width=True)
else:
    st.warning("Select at least one outcome severity to view results.")
