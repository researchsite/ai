from __future__ import annotations
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from app.api.models import parse_blacklist

# Bundled minimal sample so the demo always works even without data/abuse.json
SAMPLE_BLACKLIST = {
    "meta": {"generatedAt": "2026-06-02T05:46:42+00:00"},
    "data": [
        {"ipAddress": "35.169.206.177",  "countryCode": "US", "abuseConfidenceScore": 100, "lastReportedAt": "2026-06-02T05:17:02+00:00"},
        {"ipAddress": "122.180.21.11",   "countryCode": "IN", "abuseConfidenceScore": 100, "lastReportedAt": "2026-06-02T05:17:02+00:00"},
        {"ipAddress": "43.157.181.189",  "countryCode": "BR", "abuseConfidenceScore": 100, "lastReportedAt": "2026-06-02T05:17:02+00:00"},
        {"ipAddress": "66.132.172.254",  "countryCode": "US", "abuseConfidenceScore": 100, "lastReportedAt": "2026-06-02T05:17:02+00:00"},
        {"ipAddress": "158.94.208.66",   "countryCode": "DE", "abuseConfidenceScore": 100, "lastReportedAt": "2026-06-02T05:17:02+00:00"},
        {"ipAddress": "79.124.62.134",   "countryCode": "BG", "abuseConfidenceScore": 100, "lastReportedAt": "2026-06-02T04:58:30+00:00"},
        {"ipAddress": "170.238.160.191", "countryCode": "BR", "abuseConfidenceScore": 100, "lastReportedAt": "2026-06-02T04:58:30+00:00"},
        {"ipAddress": "14.194.62.218",   "countryCode": "IN", "abuseConfidenceScore": 100, "lastReportedAt": "2026-06-02T04:58:30+00:00"},
        {"ipAddress": "185.220.101.47",  "countryCode": "DE", "abuseConfidenceScore": 100, "lastReportedAt": "2026-06-02T04:45:11+00:00"},
        {"ipAddress": "103.174.103.64",  "countryCode": "IN", "abuseConfidenceScore":  99, "lastReportedAt": "2026-06-02T04:40:00+00:00"},
        {"ipAddress": "91.92.243.232",   "countryCode": "NL", "abuseConfidenceScore":  98, "lastReportedAt": "2026-06-02T04:30:00+00:00"},
        {"ipAddress": "5.188.87.54",     "countryCode": "RU", "abuseConfidenceScore":  97, "lastReportedAt": "2026-06-02T04:20:00+00:00"},
        {"ipAddress": "192.241.220.145", "countryCode": "US", "abuseConfidenceScore":  95, "lastReportedAt": "2026-06-02T04:10:00+00:00"},
        {"ipAddress": "45.142.212.100",  "countryCode": "NL", "abuseConfidenceScore":  94, "lastReportedAt": "2026-06-02T04:00:00+00:00"},
        {"ipAddress": "194.165.16.11",   "countryCode": "LT", "abuseConfidenceScore":  93, "lastReportedAt": "2026-06-02T03:50:00+00:00"},
        {"ipAddress": "45.227.255.220",  "countryCode": "BR", "abuseConfidenceScore":  92, "lastReportedAt": "2026-06-02T03:40:00+00:00"},
        {"ipAddress": "218.92.0.112",    "countryCode": "CN", "abuseConfidenceScore":  91, "lastReportedAt": "2026-06-02T03:30:00+00:00"},
        {"ipAddress": "62.233.50.245",   "countryCode": "RU", "abuseConfidenceScore":  90, "lastReportedAt": "2026-06-02T03:20:00+00:00"},
        {"ipAddress": "141.98.10.56",    "countryCode": "PA", "abuseConfidenceScore":  89, "lastReportedAt": "2026-06-02T03:10:00+00:00"},
        {"ipAddress": "80.66.88.206",    "countryCode": "NL", "abuseConfidenceScore":  88, "lastReportedAt": "2026-06-02T03:00:00+00:00"},
    ],
}

SAMPLE_CHECK = {
    "data": {
        "ipAddress": "185.220.101.47",
        "isPublic": True,
        "ipVersion": 4,
        "isWhitelisted": False,
        "abuseConfidenceScore": 100,
        "countryCode": "DE",
        "countryName": "Germany",
        "usageType": "Data Center/Web Hosting/Transit",
        "isp": "Frantech Solutions",
        "domain": "frantech.ca",
        "hostnames": ["tor-exit.example.net"],
        "isTor": True,
        "totalReports": 312,
        "numDistinctUsers": 87,
        "lastReportedAt": "2026-06-02T04:45:11+00:00",
        "reports": [
            {"reportedAt": "2026-06-02T04:45:11+00:00", "comment": "SSH brute force from this Tor exit node", "categories": [22, 18], "reporterCountryCode": "US", "reporterCountryName": "United States"},
            {"reportedAt": "2026-06-01T18:30:00+00:00", "comment": "Port scanning and credential stuffing", "categories": [14, 18], "reporterCountryCode": "GB", "reporterCountryName": "United Kingdom"},
            {"reportedAt": "2026-06-01T09:15:00+00:00", "comment": "Automated login attempts on admin panel", "categories": [21, 18], "reporterCountryCode": "DE", "reporterCountryName": "Germany"},
            {"reportedAt": "2026-05-31T22:00:00+00:00", "comment": "Web application attack — SQLi probes", "categories": [16, 21], "reporterCountryCode": "FR", "reporterCountryName": "France"},
            {"reportedAt": "2026-05-31T14:20:00+00:00", "comment": "Known Tor exit — flagged for policy", "categories": [9], "reporterCountryCode": "NL", "reporterCountryName": "Netherlands"},
        ],
    }
}


def _load_local_blacklist() -> dict:
    """Use local abuse.json if present, fall back to bundled sample."""
    local = Path(__file__).parent.parent.parent / "data" / "abuse.json"
    if local.exists():
        try:
            with open(local) as f:
                return json.load(f)
        except Exception:
            pass
    return SAMPLE_BLACKLIST


def render() -> None:
    st.subheader("Demo — Sample Threat Data", divider="gray")
    st.info(
        "This tab uses pre-loaded sample data so you can explore the dashboard "
        "without an API key. Enter your key in the **Connect** tab to query live data.",
        icon="ℹ️",
    )

    demo_bl, demo_ip = st.tabs(["Blacklist Preview", "IP Analysis Preview"])

    # ── Blacklist preview ─────────────────────────────────────────────────────
    with demo_bl:
        raw = _load_local_blacklist()
        bl = parse_blacklist(raw)
        ip_count = bl.meta.count or len(bl.data)

        st.info(
            f"Blacklist snapshot — **{ip_count:,} IPs** — "
            f"generated at **{bl.meta.generatedAt}**",
            icon="ℹ️",
        )

        df = pd.DataFrame([
            {
                "IP Address": e.ipAddress,
                "Abuse Score": e.abuseConfidenceScore,
                "Last Reported": e.lastReportedAt or "—",
                "Country": e.countryCode or "—",
            }
            for e in bl.data
        ]).sort_values(by=["Abuse Score", "Last Reported"], ascending=[False, False]).reset_index(drop=True)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Abuse Score": st.column_config.ProgressColumn(
                    "Abuse Score", min_value=0, max_value=100, format="%d"
                ),
                "Last Reported": st.column_config.DatetimeColumn(
                    "Last Reported", format="YYYY-MM-DD HH:mm"
                ),
            },
        )

        st.markdown("**Score Distribution**")
        bins = pd.cut(df["Abuse Score"], bins=[74, 85, 95, 100], labels=["75–85", "86–95", "96–100"])
        dist = bins.value_counts().sort_index().reset_index()
        dist.columns = ["Score Range", "Count"]
        st.bar_chart(dist.set_index("Score Range"))

    # ── IP analysis preview ───────────────────────────────────────────────────
    with demo_ip:
        from app.api.models import parse_check
        from app.tabs.ip_analysis import _render_check_result
        result = parse_check(SAMPLE_CHECK)
        st.caption("Sample analysis for a known Tor exit node (185.220.101.47)")
        _render_check_result(result)
