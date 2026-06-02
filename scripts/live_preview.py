"""Bypass auth gate for local screenshot capture — not for production use."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import streamlit as st
from app.tabs import blacklist, ip_analysis

st.set_page_config(page_title="ThreatScope – Live Preview", layout="wide")
api_key = os.environ.get("ABUSEIPDB_KEY", "")
if not api_key:
    st.error("Set ABUSEIPDB_KEY environment variable to run this preview.")
    st.stop()

st.title("ThreatScope Analytics – Live Preview")
tab_bl, tab_ip = st.tabs(["Global Blacklist Feed", "IP Analysis"])
with tab_bl:
    blacklist.render(api_key)
with tab_ip:
    ip_analysis.render(api_key)
