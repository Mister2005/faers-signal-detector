import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from dashboard.styles import apply_plotly_theme


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
        line=dict(color="#14B8A6", width=2.5),
        marker=dict(size=7, color="#14B8A6", line=dict(color="#0A0E1A", width=2))
    ))

    # PRR threshold line
    fig.add_hline(
        y=2.0,
        line_dash="dash",
        line_color="#FF3B47",
        annotation_text="PRR threshold (2.0)",
        annotation_position="bottom right"
    )

    # ROR with CI band
    fig.add_trace(go.Scatter(
        x=pd.concat([df["quarter_cutoff"], df["quarter_cutoff"][::-1]]).tolist(),
        y=pd.concat([df["ror_ci_upper"], df["ror_ci_lower"][::-1]]).tolist(),
        fill="toself",
        fillcolor="rgba(139,92,246,0.08)",
        line=dict(color="rgba(255,255,255,0)"),
        name="ROR 95% CI"
    ))

    fig.add_trace(go.Scatter(
        x=df["quarter_cutoff"],
        y=df["ror"],
        mode="lines",
        name="ROR",
        line=dict(color="#8B5CF6", width=1.5, dash="dot")
    ))

    # annotate first detected quarter
    signal_rows = df[df["is_signal"] == True]
    if not signal_rows.empty:
        first = signal_rows.iloc[0]
        fig.add_annotation(
            x=first["quarter_cutoff"],
            y=first["prr"],
            text="First detected",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#F5C518",
            font=dict(color="#F5C518", size=10),
            bgcolor="#2A200A",
            bordercolor="#F5C518",
            borderwidth=1,
            borderpad=4,
        )

    fig.update_layout(
        title=f"Signal Trend: {drug_name} -> {reaction_pt}",
        xaxis_title="Quarter (Cumulative)",
        yaxis_title="PRR / ROR",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
        height=340,
    )
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    # Case count bar chart
    fig2 = go.Figure(go.Bar(
        x=df["quarter_cutoff"],
        y=df["case_count"],
        marker=dict(
            color=df["case_count"],
            colorscale=[[0, "#1E2D4A"], [0.5, "#3B82F6"], [1.0, "#14B8A6"]],
            line=dict(color="rgba(0,0,0,0)", width=0),
        ),
        hovertemplate="<b>%{x}</b><br>Cumulative cases: %{y}<extra></extra>",
        name="Case Count"
    ))
    fig2.update_layout(
        title="Cumulative Case Count Over Time",
        xaxis_title="Quarter",
        yaxis_title="Cases",
        height=220,
    )
    apply_plotly_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)
