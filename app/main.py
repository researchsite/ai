from __future__ import annotations
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `app.*` imports work regardless
# of how Streamlit resolves the script directory.
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from app.tabs import blacklist, ip_analysis


def _auth_gate() -> str | None:
    """Render the API key input and return the key if set, else None."""
    if "api_key" not in st.session_state:
        st.session_state["api_key"] = ""

    if st.session_state["api_key"]:
        return st.session_state["api_key"]

    st.markdown("---")
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("### Enter Your AbuseIPDB API Key")
        st.caption(
            "Your key is stored only in this browser session and never transmitted "
            "except directly to the AbuseIPDB API."
        )
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

    # ── Header ────────────────────────────────────────────────────────────────
    header_col, key_col = st.columns([4, 1])
    with header_col:
        st.title(":material/shield: ThreatScope Analytics")
        st.caption("Powered by AbuseIPDB v2 API")
    with key_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.get("api_key"):
            if st.button("Clear API Key", icon=":material/logout:", use_container_width=True):
                st.session_state["api_key"] = ""
                st.rerun()

    # ── Auth gate ─────────────────────────────────────────────────────────────
    api_key = _auth_gate()
    if not api_key:
        return

    # ── Main tabs ─────────────────────────────────────────────────────────────
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
