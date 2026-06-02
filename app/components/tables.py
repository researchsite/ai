from __future__ import annotations
import pandas as pd
import streamlit as st

CATEGORY_MAP = {
    1: "DNS Compromise", 2: "DNS Poisoning", 3: "Fraud Orders",
    4: "DDoS Attack", 5: "FTP Brute-Force", 6: "Ping of Death",
    7: "Phishing", 8: "Fraud VoIP", 9: "Open Proxy",
    10: "Web Spam", 11: "Email Spam", 12: "Blog Spam",
    13: "VPN IP", 14: "Port Scan", 15: "Hacking",
    16: "SQL Injection", 17: "Spoofing", 18: "Brute-Force",
    19: "Bad Web Bot", 20: "Exploited Host", 21: "Web App Attack",
    22: "SSH", 23: "IoT Targeted",
}

USAGE_TYPE_COLORS = {
    "Data Center/Web Hosting/Transit": "#e74c3c",
    "Commercial": "#e67e22",
    "Organization": "#f1c40f",
    "Government": "#3498db",
    "Military": "#2ecc71",
    "Library": "#9b59b6",
    "University/College/School": "#1abc9c",
    "Fixed Line ISP": "#95a5a6",
    "Mobile ISP": "#95a5a6",
    "Content Delivery Network": "#e74c3c",
    "Fixed Line ISP | Mobile ISP": "#95a5a6",
}


def render_kv_table(data: dict, title: str | None = None) -> None:
    """Render a key-value dict as a two-column Streamlit table."""
    if title:
        st.markdown(f"**{title}**")
    rows = [{"Field": k, "Value": str(v)} for k, v in data.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def decode_categories(cat_ids: list[int]) -> str:
    return ", ".join(CATEGORY_MAP.get(c, f"Category {c}") for c in cat_ids) or "—"


def usage_type_badge(usage_type: str | None) -> None:
    if not usage_type:
        st.markdown("**Usage Type:** `Unknown`")
        return
    color = USAGE_TYPE_COLORS.get(usage_type, "#7f8c8d")
    st.markdown(
        f'**Usage Type:** <span style="background:{color};color:white;'
        f'padding:2px 10px;border-radius:12px;font-size:0.85em">{usage_type}</span>',
        unsafe_allow_html=True,
    )
