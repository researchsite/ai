from __future__ import annotations
import json

import pandas as pd
import streamlit as st

from app.api.models import parse_blacklist, parse_check, detect_response_type

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


def _render_result(raw: dict) -> None:
    """Detect response type and render the appropriate view."""
    response_type = detect_response_type(raw)

    if response_type == "check":
        result = parse_check(raw)
        st.success(f"Detected a `/check` response for `{result.ipAddress}` — rendering analysis below.")
        from app.tabs.ip_analysis import _render_check_result
        _render_check_result(result)

    elif response_type == "blacklist":
        bl = parse_blacklist(raw)
        ip_count = bl.meta.count or len(bl.data)
        st.success(f"Detected a `/blacklist` response — **{ip_count:,} IPs**, generated at `{bl.meta.generatedAt}`.")
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
        if len(df) >= 3:
            st.markdown("**Score Distribution**")
            bins = pd.cut(df["Abuse Score"], bins=[74, 85, 95, 100], labels=["75–85", "86–95", "96–100"])
            dist = bins.value_counts().sort_index().reset_index()
            dist.columns = ["Score Range", "Count"]
            st.bar_chart(dist.set_index("Score Range"))

    else:
        st.error(
            "This file doesn't match any known AbuseIPDB response format. "
            "Expected either a `/check` response (where `data` is a dict with an `ipAddress` field) "
            "or a `/blacklist` response (where `data` is an array of IP entries)."
        )


def render() -> None:
    st.subheader("Try Demo", divider="gray")
    st.markdown(
        "Upload any AbuseIPDB JSON response you already have to explore the full dashboard "
        "without an API key. Don't have a file yet? Load the built-in sample below to "
        "see what ThreatScope looks like with real threat data."
    )

    # ── File uploader ─────────────────────────────────────────────────────────
    with st.expander("What files can I upload?", icon=":material/help:"):
        st.markdown(
            "**Accepted formats:**\n"
            "- A `/check` response — single IP analysis. Save the JSON from a previous "
            "query and load it here to re-examine it without spending quota.\n"
            "- A `/blacklist` response — the `data` field is an array of IP entries.\n\n"
            "ThreatScope auto-detects which type you uploaded and renders the right view."
        )

    uploaded = st.file_uploader(
        "Upload your AbuseIPDB JSON file",
        type=["json"],
        label_visibility="collapsed",
        help="Accepts /check (single IP) or /blacklist response JSON from AbuseIPDB.",
    )

    if uploaded is not None:
        # Clear sample state when user uploads their own file
        st.session_state.pop("demo_show_sample", None)
        try:
            raw = json.load(uploaded)
            _render_result(raw)
        except json.JSONDecodeError as exc:
            st.error(f"That file doesn't look like valid JSON: {exc}")
        return

    # ── No file uploaded — show empty state + sample option ──────────────────
    st.markdown(
        "<div style='text-align:center;padding:1.5rem 0 0.5rem;color:#95a5a6;font-size:0.95rem;'>"
        "No file uploaded yet."
        "</div>",
        unsafe_allow_html=True,
    )

    col_l, col_btn, col_r = st.columns([2, 1, 2])
    with col_btn:
        if st.button(
            "Load sample data",
            use_container_width=True,
            icon=":material/dataset:",
            help="Loads a bundled snapshot of real AbuseIPDB data so you can explore the UI.",
        ):
            st.session_state["demo_show_sample"] = True

    if st.session_state.get("demo_show_sample"):
        st.markdown("---")
        sample_bl, sample_ip = st.tabs(["Blacklist Snapshot", "IP Analysis Example"])

        with sample_bl:
            st.caption("20 real IPs from a recent AbuseIPDB blacklist snapshot.")
            _render_result(SAMPLE_BLACKLIST)

        with sample_ip:
            st.caption(
                "Full analysis for `185.220.101.47` — a known Tor exit node "
                "with 312 reports from 87 distinct reporters."
            )
            _render_result(SAMPLE_CHECK)
