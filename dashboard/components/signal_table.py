import streamlit as st
import pandas as pd


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
        signal_col = "Signal?"
        prr_col = "PRR"

        if row.get(signal_col, "") == "Yes":
            if row.get(prr_col, 0) >= 5.0:
                return ["background-color: #3D0A0F; color: #FF8A8F; border-left:3px solid #FF3B47"] * len(row)
            return ["background-color: #2A200A; color: #F5C518; border-left:3px solid #F5C518"] * len(row)
        elif row.get(prr_col, 0) >= 1.5:
            return ["background-color: #071A2E; color: #4FC3F7; border-left:3px solid #4FC3F7"] * len(row)
        return [""] * len(row)

    def prr_color(v):
        try:
            val = float(v)
        except Exception:
            return "color:#4A5A7A"
        if val >= 5.0:
            return "color:#FF3B47;font-weight:700"
        if val >= 3.0:
            return "color:#FF8C00;font-weight:600"
        if val >= 2.0:
            return "color:#F5C518;font-weight:600"
        if val >= 1.5:
            return "color:#4FC3F7"
        return "color:#4A5A7A"

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
        "trend_last4": "PRR Trend (4Q)",
    }

    # Only include columns that exist in df
    cols = [c for c in display_cols if c in df.columns]
    display_df = df[cols].rename(columns=display_cols)

    # Format numerics
    for col in ["PRR", "Chi²", "ROR", "ROR CI Lower", "ROR CI Upper"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda x: float(x) if pd.notna(x) and x != float("inf") else None
            )

    if "Signal?" in display_df.columns:
        display_df["Signal?"] = display_df["Signal?"].map(lambda v: "Yes" if bool(v) else "No")

    if "Cases (a)" in display_df.columns:
        display_df["Cases (a)"] = display_df["Cases (a)"].map(lambda v: f"{int(v):,}" if pd.notna(v) else "")

    styled = display_df.style.apply(highlight_signal, axis=1)
    if "PRR" in display_df.columns:
        styled = styled.map(prr_color, subset=["PRR"]).format({"PRR": "{:.3f}", "Chi²": "{:.3f}", "ROR": "{:.3f}", "ROR CI Lower": "{:.3f}", "ROR CI Upper": "{:.3f}"}, na_rep="∞")
    else:
        styled = styled.format({"Chi²": "{:.3f}", "ROR": "{:.3f}", "ROR CI Lower": "{:.3f}", "ROR CI Upper": "{:.3f}"}, na_rep="∞")
    st.dataframe(styled, use_container_width=True, height=500)

    # Download button
    csv = df[cols].to_csv(index=False)
    st.download_button(
        "Download as CSV",
        data=csv,
        file_name="faers_signals.csv",
        mime="text/csv"
    )
