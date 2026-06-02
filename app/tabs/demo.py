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


def _render_blacklist_preview(raw: dict) -> None:
    bl = parse_blacklist(raw)
    ip_count = bl.meta.count or len(bl.data)
    st.info(
        f"Blacklist snapshot — **{ip_count:,} IPs** — generated at **{bl.meta.generatedAt}**",
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
    if len(df) >= 3:
        st.markdown("**Score Distribution**")
        bins = pd.cut(df["Abuse Score"], bins=[74, 85, 95, 100], labels=["75–85", "86–95", "96–100"])
        dist = bins.value_counts().sort_index().reset_index()
        dist.columns = ["Score Range", "Count"]
        st.bar_chart(dist.set_index("Score Range"))


def render() -> None:
    st.subheader("Try Demo", divider="gray")

    st.markdown(
        "Explore the full dashboard without an API key. "
        "The **Sample Data** tab shows what ThreatScope looks like with real-world threat data. "
        "The **Upload Your File** tab lets you load any AbuseIPDB JSON response you already have — "
        "great for reviewing saved data or exploring without spending API quota."
    )

    tab_sample, tab_upload = st.tabs([
        ":material/dataset: Sample Data",
        ":material/upload_file: Upload Your File",
    ])

    # ── Sample Data ───────────────────────────────────────────────────────────
    with tab_sample:
        st.caption(
            "These are real IPs from a recent AbuseIPDB blacklist snapshot, bundled here "
            "so you can explore the interface. Connect your API key for live, up-to-date data."
        )

        sample_bl, sample_ip = st.tabs(["Blacklist Preview", "IP Analysis Preview"])

        with sample_bl:
            with st.expander("What am I looking at?", icon=":material/help:"):
                st.markdown(
                    "This is a preview of the **Global Blacklist Feed** — AbuseIPDB's daily "
                    "list of the most abusive IPs on the internet right now.\n\n"
                    "- **Abuse Score** is a community-sourced confidence score from 0–100. "
                    "100 means every reporter who checked this IP flagged it as malicious. "
                    "75+ is the threshold used here — anything below that is noise.\n"
                    "- **Last Reported** is the most recent time someone submitted an abuse "
                    "report for this IP.\n"
                    "- The **Score Distribution** chart at the bottom breaks the list into "
                    "bands so you can see how severe the current threat landscape is."
                )
            _render_blacklist_preview(SAMPLE_BLACKLIST)

        with sample_ip:
            with st.expander("What am I looking at?", icon=":material/help:"):
                st.markdown(
                    "This is a preview of the **IP Analysis** view for a single IP address. "
                    "The example below is `185.220.101.47`, a known Tor exit node that has "
                    "been reported 312 times by 87 different reporters.\n\n"
                    "- **Gauge** — the red/amber/green indicator shows the abuse confidence "
                    "score at a glance. Red (60–100) means high confidence of malicious activity.\n"
                    "- **Country & ISP** — helps you understand who operates the IP and where.\n"
                    "- **Usage Type** — categorises the IP as a data centre, ISP, CDN, etc. "
                    "Data centre IPs showing up in your logs are often bots or scrapers.\n"
                    "- **Timeline** — shows when abuse was reported over the last 90 days, "
                    "so you can see if it's an ongoing threat or a one-off incident.\n"
                    "- **Raw Intelligence** — expand it to see every single field the API "
                    "returned, including individual reporter comments."
                )
            from app.tabs.ip_analysis import _render_check_result
            result = parse_check(SAMPLE_CHECK)
            _render_check_result(result)

    # ── Upload Your File ──────────────────────────────────────────────────────
    with tab_upload:
        with st.expander("How does this work?", icon=":material/help:"):
            st.markdown(
                "If you've previously fetched data from the AbuseIPDB API and saved the "
                "JSON response, you can load it here to review it visually — without "
                "making a new API call or spending any of your daily quota.\n\n"
                "**Accepted file types:**\n"
                "- A `/check` response — the JSON you get when you query a single IP. "
                "The top-level `data` field will be a dict containing `ipAddress`.\n"
                "- A `/blacklist` response — the JSON from a blacklist query. "
                "The top-level `data` field will be an array of IP entries.\n\n"
                "ThreatScope automatically detects which type you uploaded and renders "
                "the appropriate view. You do not need to tell it which format it is."
            )

        uploaded = st.file_uploader(
            "Drop your AbuseIPDB JSON file here",
            type=["json"],
            help="Accepts /check (single IP) or /blacklist (array of IPs) response JSON.",
            label_visibility="collapsed",
        )

        if uploaded is None:
            st.markdown(
                "<div style='text-align:center;padding:2rem;color:#95a5a6'>"
                "Upload a JSON file above to visualise your data here."
                "</div>",
                unsafe_allow_html=True,
            )
            return

        try:
            raw = json.load(uploaded)
        except json.JSONDecodeError as exc:
            st.error(f"That file doesn't look like valid JSON: {exc}")
            return

        response_type = detect_response_type(raw)

        if response_type == "check":
            try:
                result = parse_check(raw)
                st.success(f"Detected a `/check` response for `{result.ipAddress}` — rendering analysis below.")
                from app.tabs.ip_analysis import _render_check_result
                _render_check_result(result)
            except (KeyError, ValueError) as exc:
                st.error(f"Couldn't parse the check response: {exc}")

        elif response_type == "blacklist":
            try:
                bl = parse_blacklist(raw)
                ip_count = bl.meta.count or len(bl.data)
                st.success(f"Detected a `/blacklist` response — **{ip_count:,} IPs**, generated at `{bl.meta.generatedAt}`.")
                _render_blacklist_preview(raw)
            except (KeyError, ValueError) as exc:
                st.error(f"Couldn't parse the blacklist response: {exc}")

        else:
            st.error(
                "This file doesn't match any known AbuseIPDB response format. "
                "Expected either a `/check` response (where `data` is a dict with an `ipAddress` field) "
                "or a `/blacklist` response (where `data` is an array of IP entries)."
            )
