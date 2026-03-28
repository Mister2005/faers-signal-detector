from __future__ import annotations

import plotly.graph_objects as go


def inject_styles(st) -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(ANIMATION_CSS, unsafe_allow_html=True)


def apply_plotly_theme(fig: go.Figure, height: int | None = None) -> go.Figure:
    fig.update_layout(**FAERS_THEME)
    if height is not None:
        fig.update_layout(height=height)
    return fig


FAERS_THEME = {
    "paper_bgcolor": "#0B1220",
    "plot_bgcolor": "#111A2E",
    "font": {"family": "Inter, sans-serif", "color": "#AFC5E6", "size": 11},
    "colorway": [
        "#4D9EFF", "#22D3EE", "#FFB347", "#C084FC",
        "#34D399", "#FF6B6B", "#F472B6", "#FACC15",
    ],
    "xaxis": {
        "gridcolor": "#233457",
        "linecolor": "#233457",
        "zerolinecolor": "#233457",
        "tickfont": {"color": "#9FB2D4", "size": 10, "family": "JetBrains Mono, monospace"},
    },
    "yaxis": {
        "gridcolor": "#233457",
        "linecolor": "#233457",
        "zerolinecolor": "#233457",
        "tickfont": {"color": "#9FB2D4", "size": 10, "family": "JetBrains Mono, monospace"},
    },
    "legend": {
        "bgcolor": "rgba(12,20,36,0.9)",
        "bordercolor": "#2A3D63",
        "borderwidth": 1,
        "font": {"color": "#AFC5E6", "size": 10},
    },
    "hoverlabel": {
        "bgcolor": "#1B2A47",
        "bordercolor": "#4D9EFF",
        "font": {"color": "#EAF2FF", "size": 12},
    },
    "margin": {"l": 48, "r": 22, "t": 42, "b": 48},
}


GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg-primary: #0B1220;
  --bg-secondary: #111A2E;
  --bg-tertiary: #182540;
  --bg-card: rgba(17, 26, 46, 0.92);
  --bg-sidebar: #0C1527;
  --border-subtle: #233457;
  --border-active: #4D9EFF;
  --text-primary: #EAF2FF;
  --text-secondary: #AFC5E6;
  --text-muted: #6E84A8;
  --text-accent: #C8DAF7;
  --signal-critical: #FF5A5F;
  --signal-high: #FFB347;
  --signal-confirmed: #FFE066;
  --signal-borderline: #7FDBFF;
  --signal-none: #667085;
  --accent-blue: #4D9EFF;
  --accent-cyan: #22D3EE;
  --accent-violet: #C084FC;
  --accent-emerald: #34D399;
  --accent-rose: #FB7185;
}

.stApp {
  background:
    radial-gradient(1100px 600px at 8% -10%, rgba(77,158,255,0.16), transparent),
    radial-gradient(900px 450px at 100% -5%, rgba(192,132,252,0.14), transparent),
    radial-gradient(1000px 460px at 55% 100%, rgba(52,211,153,0.10), transparent),
    linear-gradient(180deg, #090F1C 0%, #0B1220 45%, #0A1326 100%);
}


/* Streamlit native top chrome: keep functionality, match premium theme */
[data-testid="stDecoration"] {
  background: linear-gradient(90deg, rgba(77,158,255,0.45), rgba(34,211,238,0.35), rgba(192,132,252,0.4)) !important;
  height: 2px !important;
}

[data-testid="stHeader"] {
  background: linear-gradient(180deg, rgba(10,20,38,0.9), rgba(10,20,38,0.68)) !important;
  border-bottom: 1px solid rgba(42,61,99,0.8);
  box-shadow: inset 0 -1px 0 rgba(77,158,255,0.15);
  backdrop-filter: blur(10px);
}

[data-testid="stToolbar"] {
  right: 0.75rem;
}

[data-testid="stToolbar"] button {
  border-radius: 8px !important;
  border: 1px solid rgba(52,78,124,0.9) !important;
  background: linear-gradient(180deg, rgba(24,40,69,0.88), rgba(20,33,58,0.88)) !important;
  color: #DCE8FF !important;
}

[data-testid="stToolbar"] button:hover {
  border-color: rgba(77,158,255,0.72) !important;
  box-shadow: 0 0 12px rgba(77,158,255,0.24);
  background: linear-gradient(180deg, rgba(33,53,89,0.94), rgba(24,39,68,0.94)) !important;
}

[data-testid="stStatusWidget"] {
  color: #9FB2D4 !important;
}

[data-testid="stToolbar"] [data-testid="stBaseButton-headerNoPadding"] {
  border: 1px solid rgba(52,78,124,0.9) !important;
  background: linear-gradient(180deg, rgba(24,40,69,0.88), rgba(20,33,58,0.88)) !important;
}



.main .block-container {
  padding-top: 1rem;
  padding-bottom: 2rem;
  max-width: 1320px;
}

body, p, li, td, th, label {
  font-family: 'Inter', sans-serif;
  color: var(--text-primary);
}

.hero {
  background:
    linear-gradient(135deg, rgba(22,34,58,0.96), rgba(17,30,54,0.96));
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 24px 28px;
  margin-bottom: 12px;
  box-shadow: 0 12px 26px rgba(0,0,0,0.35);
  position: relative;
  overflow: hidden;
}

.hero::after {
  content: "";
  position: absolute;
  right: -80px;
  top: -90px;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(77,158,255,0.2), rgba(77,158,255,0));
}

.hero-kicker {
  color: #9ED0FF;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .12em;
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 8px;
}

.hero h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.hero p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  max-width: 820px;
}

.info-panel {
  background: linear-gradient(90deg, rgba(27,41,68,0.9), rgba(23,35,58,0.9));
  border: 1px solid #2A3D63;
  border-left: 3px solid #4D9EFF;
  border-radius: 10px;
  padding: 11px 14px;
  margin-bottom: 11px;
}

.info-panel-title {
  margin: 0;
  font-size: 11px;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: #C8DAF7;
  font-weight: 600;
}

.info-panel-copy {
  margin: 4px 0 0;
  color: #AFC5E6;
  font-size: 13px;
}

.section-title {
  color: #C8DAF7;
  font-size: 18px;
  font-weight: 600;
  margin: 14px 0 8px;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0A1426 0%, #0C1A30 100%);
  border-right: 1px solid #24385D;
}

[data-testid="stSidebarNav"] {
  display: none;
}

.sidebar-brand-wrap {
  background: rgba(21,34,58,0.8);
  border: 1px solid #2A3D63;
  border-radius: 10px;
  padding: 10px;
  margin-bottom: 10px;
}

.sidebar-brand-title {
  color: #EAF2FF;
  font-weight: 700;
  font-size: 16px;
}

.sidebar-brand-subtitle {
  color: #8FAAD1;
  font-size: 11px;
}

.sidebar-live {
  margin-top: 8px;
  color: #74F0C5;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: 'JetBrains Mono', monospace;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #34D399;
  display: inline-block;
  animation: pulse 2s infinite;
}

.sidebar-section-title {
  margin: 10px 0 6px;
  color: #8FAAD1;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .1em;
}

.sidebar-nav-item {
  display: block;
  padding: 7px 10px;
  margin-bottom: 4px;
  color: #AFC5E6 !important;
  text-decoration: none;
  border-radius: 7px;
  border: 1px solid transparent;
  transition: all .15s ease;
}

[data-testid="stSidebar"] .stButton {
  margin-bottom: 4px;
}

[data-testid="stSidebar"] .stButton > button {
  width: 100%;
  text-align: center;
  background: linear-gradient(180deg, rgba(24,40,69,0.92), rgba(20,33,58,0.92));
  color: #DCE8FF;
  border: 1px solid #2F4673;
  border-radius: 7px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.18);
  font-weight: 500;
  min-height: 42px;
  padding: 8px 10px;
  box-sizing: border-box;
  transform: none !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
  background: linear-gradient(180deg, rgba(33,53,89,0.96), rgba(24,39,68,0.96));
  border-color: rgba(77,158,255,0.55);
  color: #EAF2FF;
  box-shadow: 0 0 12px rgba(77,158,255,0.22);
  transform: none !important;
}

[data-testid="stSidebar"] .stButton > button:focus,
[data-testid="stSidebar"] .stButton > button:active {
  transform: none !important;
  outline: none;
  box-shadow: 0 0 12px rgba(77,158,255,0.22);
}

[data-testid="stSidebar"] .stButton > button:disabled {
  opacity: 1;
  cursor: default;
  background: linear-gradient(90deg, rgba(77,158,255,0.22) 0%, rgba(192,132,252,0.18) 100%);
  border-color: rgba(77,158,255,0.65);
  color: #EAF2FF;
  box-shadow: inset 3px 0 0 #4D9EFF, 0 2px 10px rgba(0,0,0,0.18);
}

.sidebar-nav-item:hover {
  background: rgba(77,158,255,0.12);
  border-color: rgba(77,158,255,0.35);
}

.sidebar-nav-item-active {
  background: linear-gradient(90deg, rgba(77,158,255,0.2) 0%, rgba(192,132,252,0.16) 100%);
  border-color: rgba(77,158,255,0.55);
  color: #EAF2FF !important;
  box-shadow: inset 2px 0 0 #4D9EFF;
}

.sidebar-stat {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px solid rgba(42,61,99,0.7);
}

.sidebar-stat-label {
  color: #6E84A8;
  font-size: 12px;
}

.sidebar-stat-value {
  color: #C8DAF7;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
}

.sidebar-meta {
  color: #9FB2D4;
  font-size: 12px;
}

.sidebar-criteria {
  color: #9FB2D4;
  font-size: 12px;
  line-height: 1.5;
}

.sidebar-footnote {
  color: #6E84A8;
  font-size: 11px;
  margin-top: 4px;
}

.metric-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 16px 16px;
  box-shadow: 0 8px 22px rgba(0,0,0,.35);
  position: relative;
  overflow: hidden;
}

.metric-card-premium {
  border-image: linear-gradient(135deg, rgba(77,158,255,.45), rgba(192,132,252,.4), rgba(52,211,153,.4)) 1;
}

.metric-label {
  color: #9FB2D4;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .09em;
  margin-bottom: 8px;
}

.metric-value {
  color: #EAF2FF;
  font-size: 33px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1;
}

.metric-delta {
  margin-top: 6px;
  font-size: 11px;
  color: #8FE3C0;
}

.metric-accent {
  position: absolute;
  right: -24px;
  bottom: -24px;
  width: 84px;
  height: 84px;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent) 35%, transparent), transparent);
  opacity: .45;
}

.stTextInput > div > div > input {
  background-color: #1A2844 !important;
  border: 1px solid #2A3D63 !important;
  color: #EAF2FF !important;
  border-radius: 7px !important;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
}

.stTextInput > div > div > input:focus {
  border-color: #4D9EFF !important;
  box-shadow: 0 0 0 3px rgba(77,158,255,0.18) !important;
}

.stSelectbox > div > div,
[data-baseweb="select"] > div,
[data-baseweb="input"] {
  background-color: #1A2844 !important;
  border: 1px solid #2A3D63 !important;
  color: #EAF2FF !important;
}

.stSlider [data-baseweb="slider"] div[role="slider"] { background-color: #4D9EFF !important; }
.stSlider [data-baseweb="track"] div:first-child { background-color: #4D9EFF !important; }

.stButton > button,
.stDownloadButton > button {
  background: linear-gradient(90deg, #4D9EFF 0%, #22D3EE 45%, #34D399 100%);
  color: #081226;
  border: none;
  border-radius: 7px;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 13px;
  transition: all .15s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
  filter: brightness(1.06);
  box-shadow: 0 0 16px rgba(77,158,255,0.35);
  transform: translateY(-1px);
}

[data-testid="stDataFrame"] {
  border: 1px solid #2A3D63;
  border-radius: 10px;
  overflow: hidden;
}

[data-testid="stDataFrame"] th {
  background-color: #121F38 !important;
  color: #8FAAD1 !important;
  font-size: 11px !important;
  text-transform: uppercase;
  letter-spacing: .06em;
  border-bottom: 1px solid #2A3D63 !important;
}

[data-testid="stDataFrame"] td {
  color: #EAF2FF !important;
  font-size: 12px !important;
  border-bottom: 1px solid #1D2E4D !important;
}

[data-testid="stDataFrame"] tr:hover td { background-color: #1A2844 !important; }

.streamlit-expanderHeader {
  background-color: #111A2E !important;
  color: #AFC5E6 !important;
  border: 1px solid #2A3D63 !important;
  border-radius: 7px !important;
  font-size: 13px !important;
}

.stInfo {
  background-color: rgba(31,49,83,0.65) !important;
  border-left: 3px solid #7FDBFF !important;
}

.stWarning {
  background-color: rgba(53,35,16,0.68) !important;
  border-left: 3px solid #FFB347 !important;
}

.stError {
  background-color: rgba(60,19,24,0.75) !important;
  border-left: 3px solid #FF5A5F !important;
}

.stSuccess {
  background-color: rgba(20,53,44,0.7) !important;
  border-left: 3px solid #34D399 !important;
}

.signal-pill {
  padding: 2px 8px;
  border-radius: 11px;
  font-size: 10px;
  font-weight: 600;
}
.signal-pill-critical { background:#3D1318; color:#FF8C90; border:1px solid rgba(255,90,95,0.45); }
.signal-pill-high { background:#3A2A14; color:#FFB347; border:1px solid rgba(255,179,71,0.45); }
.signal-pill-confirmed { background:#3A351A; color:#FFE066; border:1px solid rgba(255,224,102,0.45); }
.signal-pill-watch { background:#132A3A; color:#7FDBFF; border:1px solid rgba(127,219,255,0.45); }
.signal-pill-none { background:#1D2E4D; color:#8FAAD1; border:1px solid rgba(143,170,209,0.35); }

.ticker-wrap {
  margin-top: 10px;
  background: linear-gradient(90deg, rgba(24,37,64,0.95), rgba(20,32,57,0.95));
  border-top: 1px solid #FF5A5F;
  border-bottom: 1px solid #2A3D63;
  padding: 8px 0;
  overflow: hidden;
  white-space: nowrap;
  border-radius: 8px;
}

.ticker-content {
  display: inline-block;
  animation: ticker 38s linear infinite;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #AFC5E6;
}

.ticker-sep {
  color: #FF5A5F;
  margin: 0 18px;
  font-weight: 700;
}

@media (max-width: 1024px) {
  .sidebar-stat { display: none; }
}

@media (max-width: 768px) {
  .hero h1 { font-size: 23px; }
  .hero { padding: 18px 16px; }
}
</style>
"""


ANIMATION_CSS = """
<style>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0%,100% { opacity: 1; }
  50% { opacity: 0.35; }
}

@keyframes ticker {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}

[data-testid="stAppViewContainer"] {
  animation: fadeIn 0.3s ease-in;
}

[data-testid="stDataFrame"] tr {
  transition: background-color .12s ease;
}
</style>
"""
