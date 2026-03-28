import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render_signal_table(df: pd.DataFrame, title: str = "Signal Results"):
    """
    Render a formatted signal results table with color coding.
    Confirmed signals (is_signal=True) shown with red background,
    borderline cases (PRR >= 1.5 but < 2) shown with yellow.
    """
    if df.empty:
        st.warning("No results found for the selected filters.")
        return

    st.subheader(title)
    st.caption(f"Showing {len(df):,} drug-event pairs")

    def highlight_signal(row):
        if row.get("is_signal", False):
            return ["background-color: #ffcccc"] * len(row)
        elif row.get("prr", 0) >= 1.5:
            return ["background-color: #fff3cd"] * len(row)
        return [""] * len(row)

    display_cols = {
        "drug_name": "Drug",
        "reaction_pt": "Adverse Event",
        "case_count": "Cases (a)",
        "prr": "PRR",
        "chi2": "Chi²",
        "ror": "ROR",
        "ror_ci_lower": "ROR CI Lower",
        "ror_ci_upper": "ROR CI Upper",
        "is_signal": "Signal?",
    }

    # Only include columns that exist in df
    cols = [c for c in display_cols if c in df.columns]
    display_df = df[cols].rename(columns=display_cols)

    # Format numerics
    for col in ["PRR", "Chi²", "ROR", "ROR CI Lower", "ROR CI Upper"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda x: f"{x:.3f}" if pd.notna(x) and x != float("inf") else "∞"
            )

    styled = display_df.style.apply(highlight_signal, axis=1)
    st.dataframe(styled, use_container_width=True, height=500)

    # Download button
    csv = df[cols].to_csv(index=False)
    st.download_button(
        "📥 Download as CSV",
        data=csv,
        file_name="faers_signals.csv",
        mime="text/csv"
    )
