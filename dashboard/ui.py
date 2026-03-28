from __future__ import annotations

import hashlib
import re
from urllib.parse import quote_plus

import streamlit as st
import streamlit.components.v1 as components

from dashboard.styles import inject_styles


def inject_global_styles() -> None:
    inject_styles(st)


def render_page_hero(title: str, subtitle: str, kicker: str = "FAERS Intelligence") -> None:
    st.markdown(
        f"""
        <section class="hero">
            <div class="hero-kicker">{kicker}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_panel(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="info-panel">
            <p class="info-panel-title">{title}</p>
            <p class="info-panel-copy">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _normalize_route(current_route: str) -> str:
    route = (current_route or "").strip()
    route = route.replace(".py", "")
    route = route.split("/")[-1].split("\\")[-1]
    return route


def render_sidebar(
    current_route: str,
    total_reports: int,
    unique_drugs: int,
    unique_reactions: int,
    confirmed_signals: int,
    quarter_window: str,
    updated_at: str,
) -> None:
    route = _normalize_route(current_route)

    nav = [
        ("app", "Home", "app.py"),
        ("01_Drug_Explorer", "Drug Explorer", "pages/01_Drug_Explorer.py"),
        ("02_Signal_Trends", "Signal Trends", "pages/02_Signal_Trends.py"),
        ("03_Severity_Filter", "Severity Monitor", "pages/03_Severity_Filter.py"),
    ]

    with st.sidebar:
        st.markdown("""
            <div class="sidebar-brand-wrap">
                <div class="sidebar-brand-title">FAERS</div>
                <div class="sidebar-brand-subtitle">Signal Detector</div>
                <div class="sidebar-live"><span class="live-dot"></span>LIVE <span class="sidebar-live-window"></span></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(
            f"""
            <script>
                const liveWindow = window.parent.document.querySelector('.sidebar-live-window');
                if (liveWindow) liveWindow.textContent = {quarter_window!r};
            </script>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='sidebar-section-title'>Navigation</div>", unsafe_allow_html=True)
        for route_key, label, page_path in nav:
            is_active = route == route_key
            if st.button(
                label,
                key=f"nav_btn_{route_key}",
                use_container_width=True,
                disabled=is_active,
            ):
                st.switch_page(page_path)

        st.markdown("<div class='sidebar-section-title'>Database Stats</div>", unsafe_allow_html=True)
        stats = [
            ("Reports", total_reports),
            ("Drugs", unique_drugs),
            ("Reactions", unique_reactions),
            ("Signals", confirmed_signals),
        ]
        for label, value in stats:
            st.markdown(
                f"<div class='sidebar-stat'><span class='sidebar-stat-label'>{label}</span><span class='sidebar-stat-value'>{value:,}</span></div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='sidebar-section-title'>Last Updated</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sidebar-meta'>{updated_at}</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-section-title'>Signal Criteria</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='sidebar-criteria'>
                <div>PRR >= 2.0</div>
                <div>Chi-square >= 4.0</div>
                <div>Cases >= 3</div>
                <div>ROR CI lower > 1.0</div>
                <div class='sidebar-footnote'>Evans et al. 2001</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _extract_number(value: str | int | float) -> int | None:
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        return None
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else None


def render_kpi(label: str, value: str | int | float, delta: str = "", accent: str = "#7CFFB2") -> None:
    numeric_target = _extract_number(value)
    shown_value = f"{int(value):,}" if isinstance(value, int) else str(value)
    dom_id = "kpi_" + hashlib.md5(f"{label}-{shown_value}".encode("utf-8")).hexdigest()[:10]

    delta_html = ""
    if delta:
        delta_html = f"<div class='metric-delta'>{delta}</div>"

    html = f"""
    <style>
        .metric-card {{
            background: rgba(17, 26, 46, 0.95);
            border: 1px solid #2A3D63;
            border-radius: 12px;
            padding: 16px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 8px 22px rgba(0,0,0,.32);
            font-family: Inter, Segoe UI, sans-serif;
        }}
        .metric-label {{
            color: #9FB2D4;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: .09em;
            margin-bottom: 8px;
        }}
        .metric-value {{
            color: #EAF2FF;
            font-size: 33px;
            font-weight: 700;
            font-family: "JetBrains Mono", Consolas, monospace;
            line-height: 1;
        }}
        .metric-delta {{
            margin-top: 6px;
            font-size: 11px;
            color: #8FE3C0;
        }}
        .metric-accent {{
            position: absolute;
            right: -24px;
            bottom: -24px;
            width: 84px;
            height: 84px;
            border-radius: 50%;
            background: radial-gradient(circle, var(--accent), rgba(0,0,0,0));
            opacity: .22;
        }}
    </style>
    <div class="metric-card metric-card-premium">
      <div class="metric-label">{label}</div>
      <div id="{dom_id}" class="metric-value">{shown_value}</div>
      {delta_html}
      <div class="metric-accent" style="--accent:{accent};"></div>
    </div>
    <script>
      (function() {{
        const el = document.getElementById('{dom_id}');
        if (!el) return;
        const target = {numeric_target if numeric_target is not None else 'null'};
        if (target === null) return;
        const start = performance.now();
        const duration = 1200;
        const easeOut = (t) => 1 - Math.pow(1 - t, 3);
        function frame(now) {{
          const t = Math.min((now - start) / duration, 1);
          const val = Math.floor(easeOut(t) * target);
          el.textContent = val.toLocaleString();
          if (t < 1) requestAnimationFrame(frame);
        }}
        requestAnimationFrame(frame);
      }})();
    </script>
    """

    components.html(html, height=142)


def signal_badge(is_signal: bool, prr: float) -> str:
    if is_signal and prr >= 5:
        return '<span class="signal-pill signal-pill-critical">HIGH</span>'
    if is_signal and prr >= 3:
        return '<span class="signal-pill signal-pill-high">SIGNAL</span>'
    if is_signal:
        return '<span class="signal-pill signal-pill-confirmed">SIGNAL</span>'
    if prr >= 1.5:
        return '<span class="signal-pill signal-pill-watch">WATCH</span>'
    return '<span class="signal-pill signal-pill-none">NONE</span>'


def prr_bar(prr: float, max_prr: float = 10.0) -> str:
    pct = min((prr / max_prr) * 100, 100)
    if prr >= 5:
        color = "#FF5A5F"
    elif prr >= 3:
        color = "#FFB347"
    elif prr >= 2:
        color = "#FFE066"
    elif prr >= 1.5:
        color = "#7FDBFF"
    else:
        color = "#667085"

    return (
        f"<div style='display:flex;align-items:center;gap:6px;'>"
        f"<div style='font-family:JetBrains Mono,monospace;font-size:12px;color:{color};font-weight:500;min-width:38px;'>{prr:.2f}</div>"
        f"<div style='flex:1;background:#233457;height:4px;border-radius:2px;'>"
        f"<div style='width:{pct:.1f}%;background:{color};height:100%;border-radius:2px;'></div></div></div>"
    )


def render_ticker(items: list[str]) -> None:
    if not items:
        return
    formatted = "<span class='ticker-sep'> • </span>".join(quote_plus(item).replace("+", " ") for item in items)
    st.markdown(
        f"""
        <div class="ticker-wrap">
            <div class="ticker-content">{formatted}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
