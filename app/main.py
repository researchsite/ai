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
