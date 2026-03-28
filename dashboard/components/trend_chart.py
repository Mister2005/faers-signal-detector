import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def render_trend_chart(df: pd.DataFrame, drug_name: str, reaction_pt: str):
    """
    Render a PRR-over-time line chart with confidence band for ROR,
    and a bar chart of case counts per quarter.
    """
    if df.empty:
        st.warning(f"No trend data found for {drug_name} / {reaction_pt}.")
        return

    fig = go.Figure()

    # PRR line
    fig.add_trace(go.Scatter(
        x=df["quarter_cutoff"],
        y=df["prr"],
        mode="lines+markers",
        name="PRR",
        line=dict(color="#1f77b4", width=2),
        marker=dict(size=8)
    ))

    # PRR threshold line
    fig.add_hline(
        y=2.0,
        line_dash="dash",
        line_color="red",
        annotation_text="PRR threshold (2.0)",
        annotation_position="bottom right"
    )

    # ROR with CI band
    fig.add_trace(go.Scatter(
        x=pd.concat([df["quarter_cutoff"], df["quarter_cutoff"][::-1]]).tolist(),
        y=pd.concat([df["ror_ci_upper"], df["ror_ci_lower"][::-1]]).tolist(),
        fill="toself",
        fillcolor="rgba(255, 165, 0, 0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="ROR 95% CI"
    ))

    fig.add_trace(go.Scatter(
        x=df["quarter_cutoff"],
        y=df["ror"],
        mode="lines",
        name="ROR",
        line=dict(color="orange", width=1.5, dash="dot")
    ))

    fig.update_layout(
        title=f"Signal Trend: {drug_name} -> {reaction_pt}",
        xaxis_title="Quarter (Cumulative)",
        yaxis_title="PRR / ROR",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    # Case count bar chart
    fig2 = go.Figure(go.Bar(
        x=df["quarter_cutoff"],
        y=df["case_count"],
        marker_color="#1f77b4",
        name="Case Count"
    ))
    fig2.update_layout(
        title="Cumulative Case Count Over Time",
        xaxis_title="Quarter",
        yaxis_title="Cases",
        height=250
    )
    st.plotly_chart(fig2, use_container_width=True)
