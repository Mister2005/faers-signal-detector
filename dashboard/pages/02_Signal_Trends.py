import streamlit as st
from src.db import query_df
from src.trends import get_prr_trend, get_available_quarters
from dashboard.components.trend_chart import render_trend_chart

st.set_page_config(page_title="Signal Trends", layout="wide")
st.title("📈 Signal Trend Viewer")
st.markdown(
    "Track how a drug-event signal evolved across quarters. "
    "A rising PRR over time suggests a strengthening safety signal."
)

# Get all available confirmed signal pairs for dropdowns
signal_pairs = query_df(
    "SELECT DISTINCT drug_name, reaction_pt FROM signal_results "
    "WHERE is_signal = TRUE AND quarter_cutoff = 'ALL' ORDER BY drug_name LIMIT 500"
)

if signal_pairs.empty:
    st.warning("No signal data found. Run the pipeline first.")
    st.stop()

drug_options = sorted(signal_pairs["drug_name"].unique().tolist())
selected_drug = st.selectbox("Select Drug", drug_options)

reaction_options = sorted(
    signal_pairs[signal_pairs["drug_name"] == selected_drug]["reaction_pt"].tolist()
)
selected_reaction = st.selectbox("Select Adverse Event", reaction_options)

if selected_drug and selected_reaction:
    df_trend = get_prr_trend(selected_drug, selected_reaction)
    render_trend_chart(df_trend, selected_drug, selected_reaction)

    # Show raw trend table
    with st.expander("View raw trend data"):
        st.dataframe(df_trend, use_container_width=True)
