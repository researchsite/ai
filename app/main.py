from __future__ import annotations
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `app.*` imports work regardless
# of how Streamlit resolves the script directory.
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from app.tabs import blacklist, ip_analysis, demo


def _render_connect_tab() -> str | None:
    """Render the API key input form. Returns the key once connected."""
    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("### Enter Your AbuseIPDB API Key")
        st.caption(
            "Your key is stored only in this browser session and never transmitted "
            "except directly to the AbuseIPDB API."
        )
        st.markdown(
            "Don't have a key? Get one free at "
            "[abuseipdb.com](https://www.abuseipdb.com/) — takes 30 seconds to sign up."
        )
        st.markdown("")
        key_input = st.text_input(
            "API Key",
            type="password",
            placeholder="Paste your AbuseIPDB v2 API key here",
        )
        if st.button("Connect", type="primary", use_container_width=True):
            if key_input.strip():
                st.session_state["api_key"] = key_input.strip()
                st.rerun()
            else:
                st.error("API key cannot be empty.")
    return None


def main() -> None:
    st.set_page_config(
        page_title="ThreatScope Analytics",
        page_icon=":material/shield:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    if "api_key" not in st.session_state:
        st.session_state["api_key"] = ""

    # ── Header ────────────────────────────────────────────────────────────────
    header_col, key_col = st.columns([4, 1])
    with header_col:
        st.title(":material/shield: ThreatScope Analytics")
        st.caption("Powered by AbuseIPDB v2 API")
    with key_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state["api_key"]:
            if st.button("Clear API Key", icon=":material/logout:", use_container_width=True):
                st.session_state["api_key"] = ""
                st.rerun()

    api_key = st.session_state["api_key"]

    # ── Hero — shown only before auth ─────────────────────────────────────────
    if not api_key:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                border-radius: 12px;
                padding: 2.5rem 3rem;
                margin-bottom: 1.5rem;
                border: 1px solid #e74c3c33;
            ">
                <h2 style="color:#ffffff;margin:0 0 0.5rem 0;font-size:1.6rem;">
                    Real-time IP Threat Intelligence — in your browser
                </h2>
                <p style="color:#bdc3c7;font-size:1rem;line-height:1.7;margin:0 0 1.5rem 0;max-width:780px;">
                    ThreatScope Analytics connects to the <strong style="color:#e74c3c;">AbuseIPDB</strong>
                    community database to help security engineers, sysadmins, and analysts answer
                    one question fast: <em>is this IP address a known threat?</em>
                    No scripts, no terminal — just paste an IP and get a full picture in seconds.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem;">
                <div style="background:#1e2a3a;border-radius:8px;padding:1.2rem;border-left:3px solid #e74c3c;box-sizing:border-box;">
                    <div style="font-size:1.4rem;">🛡️</div>
                    <div style="color:#ecf0f1;font-weight:600;margin:0.4rem 0 0.3rem;">Global Blacklist</div>
                    <div style="color:#95a5a6;font-size:0.85rem;line-height:1.5;">Live feed of the world's most abusive IPs, updated daily and cached to protect your quota.</div>
                </div>
                <div style="background:#1e2a3a;border-radius:8px;padding:1.2rem;border-left:3px solid #3498db;box-sizing:border-box;">
                    <div style="font-size:1.4rem;">🔍</div>
                    <div style="color:#ecf0f1;font-weight:600;margin:0.4rem 0 0.3rem;">IP Deep Dive</div>
                    <div style="color:#95a5a6;font-size:0.85rem;line-height:1.5;">Score gauge, country, ISP, usage type, and 90 days of individual reporter comments for any IP.</div>
                </div>
                <div style="background:#1e2a3a;border-radius:8px;padding:1.2rem;border-left:3px solid #2ecc71;box-sizing:border-box;">
                    <div style="font-size:1.4rem;">📋</div>
                    <div style="color:#ecf0f1;font-weight:600;margin:0.4rem 0 0.3rem;">Bulk Reporting</div>
                    <div style="color:#95a5a6;font-size:0.85rem;line-height:1.5;">Upload a CSV to report multiple malicious IPs to the community in a single action.</div>
                </div>
                <div style="background:#1e2a3a;border-radius:8px;padding:1.2rem;border-left:3px solid #f39c12;box-sizing:border-box;">
                    <div style="font-size:1.4rem;">📂</div>
                    <div style="color:#ecf0f1;font-weight:600;margin:0.4rem 0 0.3rem;">Offline Review</div>
                    <div style="color:#95a5a6;font-size:0.85rem;line-height:1.5;">Load a saved AbuseIPDB JSON response and explore it visually without spending API quota.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

    # ── Pre-auth: Demo + Connect tabs ─────────────────────────────────────────
    if not api_key:
        tab_demo, tab_connect = st.tabs([
            ":material/play_circle: Try Demo",
            ":material/key: Connect API Key",
        ])
        with tab_demo:
            demo.render()
        with tab_connect:
            _render_connect_tab()
        return

    # ── Post-auth: full dashboard ─────────────────────────────────────────────
    tab_bl, tab_ip = st.tabs([
        ":material/list: Global Blacklist Feed",
        ":material/manage_search: IP Analysis",
    ])

    with tab_bl:
        blacklist.render(api_key)

    with tab_ip:
        ip_analysis.render(api_key)


if __name__ == "__main__":
    main()
