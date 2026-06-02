from __future__ import annotations
import json
import io
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.api.client import fetch_check, post_bulk_report
from app.api.models import CheckResponse, parse_check, parse_blacklist, detect_response_type
from app.components.gauge import render_abuse_gauge
from app.components.tables import decode_categories, render_kv_table, usage_type_badge

BULK_CSV_TEMPLATE = "IP,Categories,ReportDate,Comment\n1.2.3.4,18,2024-01-01T00:00:00+00:00,Brute force attempt\n"


def _render_check_result(result: CheckResponse, key: str = "main") -> None:
    """Render all visualizations and expanders for a /check response."""
    st.markdown(f"### Analysis: `{result.ipAddress}`")
    st.divider()

    # ── Row 1: Gauge + Country + IP meta ─────────────────────────────────────
    col_gauge, col_meta = st.columns([1, 1])

    with col_gauge:
        render_abuse_gauge(result.abuseConfidenceScore, key=f"{key}_gauge")

    with col_meta:
        st.markdown("**IP Intelligence Summary**")
        ip_version_label = f"IPv{result.ipVersion}"
        tor_label = "Yes" if result.isTor else "No"
        public_label = "Yes" if result.isPublic else "No"
        wl_label = "Yes" if result.isWhitelisted else "No"

        st.metric("Total Reports", result.totalReports)
        st.metric("Distinct Reporters", result.numDistinctUsers)
        cols = st.columns(2)
        cols[0].markdown(f"**IP Version:** {ip_version_label}")
        cols[1].markdown(f"**Public IP:** {public_label}")
        cols[0].markdown(f"**Tor Exit Node:** {tor_label}")
        cols[1].markdown(f"**Whitelisted:** {wl_label}")

    st.markdown("---")

    # ── Row 2: Country + Usage Type + Network ────────────────────────────────
    col_country, col_usage, col_net = st.columns(3)

    with col_country:
        st.markdown("**Country of Origin**")
        flag = _country_flag(result.countryCode)
        country_display = result.countryName or result.countryCode or "Unknown"
        st.markdown(
            f"<div style='font-size:2.5rem;text-align:center'>{flag}</div>"
            f"<div style='text-align:center;font-weight:bold'>{country_display}</div>"
            f"<div style='text-align:center;color:#7f8c8d'>{result.countryCode or ''}</div>",
            unsafe_allow_html=True,
        )

    with col_usage:
        st.markdown("**Network Usage Type**")
        usage_type_badge(result.usageType)
        st.markdown("")
        st.markdown(f"**ISP:** {result.isp or '—'}")
        st.markdown(f"**Domain:** {result.domain or '—'}")

    with col_net:
        st.markdown("**Last Reported**")
        if result.lastReportedAt:
            try:
                dt = datetime.fromisoformat(result.lastReportedAt.replace("Z", "+00:00"))
                st.markdown(f"**{dt.strftime('%Y-%m-%d')}**")
                st.caption(dt.strftime("%H:%M UTC"))
            except ValueError:
                st.markdown(result.lastReportedAt)
        else:
            st.markdown("Never reported")

        if result.hostnames:
            st.markdown("**Hostnames:**")
            for h in result.hostnames[:5]:
                st.code(h, language=None)

    st.markdown("---")

    # ── Reports Timeline ──────────────────────────────────────────────────────
    if result.reports:
        st.markdown("**Report Activity Timeline**")
        report_dates = []
        for r in result.reports:
            try:
                dt = datetime.fromisoformat(r.reportedAt.replace("Z", "+00:00"))
                report_dates.append(dt.date())
            except ValueError:
                pass

        if report_dates:
            date_series = pd.Series(report_dates).value_counts().sort_index()
            date_df = date_series.reset_index()
            date_df.columns = ["Date", "Reports"]

            fig = go.Figure(go.Bar(
                x=date_df["Date"].astype(str),
                y=date_df["Reports"],
                marker_color="#e74c3c",
                hovertemplate="%{x}: %{y} report(s)<extra></extra>",
            ))
            fig.update_layout(
                height=220,
                margin={"t": 10, "b": 40, "l": 40, "r": 10},
                xaxis_title="Date",
                yaxis_title="Reports",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis={"showgrid": False},
                yaxis={"showgrid": True, "gridcolor": "#ecf0f1"},
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{key}_timeline")

    # ── Raw Intelligence Expander ─────────────────────────────────────────────
    with st.expander("View Raw Intelligence Data", expanded=False):
        st.markdown("**Core Fields**")
        core_fields = {
            "ipAddress": result.ipAddress,
            "isPublic": result.isPublic,
            "ipVersion": result.ipVersion,
            "isWhitelisted": result.isWhitelisted,
            "abuseConfidenceScore": result.abuseConfidenceScore,
            "countryCode": result.countryCode,
            "countryName": result.countryName,
            "usageType": result.usageType,
            "isp": result.isp,
            "domain": result.domain,
            "hostnames": result.hostnames,
            "isTor": result.isTor,
            "totalReports": result.totalReports,
            "numDistinctUsers": result.numDistinctUsers,
            "lastReportedAt": result.lastReportedAt,
        }
        render_kv_table(core_fields)

        if result.reports:
            st.markdown("**Reports Array**")
            reports_df = pd.DataFrame([
                {
                    "Reported At": r.reportedAt,
                    "Categories": decode_categories(r.categories),
                    "Comment": r.comment or "—",
                    "Reporter Country": r.reporterCountryName or r.reporterCountryCode or "—",
                }
                for r in result.reports
            ])
            st.dataframe(reports_df, use_container_width=True, hide_index=True)


def _country_flag(country_code: str | None) -> str:
    if not country_code or len(country_code) != 2:
        return "🌐"
    # Convert ISO 3166-1 alpha-2 to regional indicator emoji
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in country_code.upper())


def render(api_key: str) -> None:
    st.subheader("Targeted IP Analysis & Reporting", divider="blue")

    # ── Input mode tabs ───────────────────────────────────────────────────────
    mode_single, mode_bulk, mode_json = st.tabs([
        "Single IP Check", "Bulk CSV Report", "Load JSON Response"
    ])

    # ── Single IP ─────────────────────────────────────────────────────────────
    with mode_single:
        with st.expander("How to use this tab", icon=":material/help:"):
            st.markdown(
                "Enter any IPv4 or IPv6 address to pull a full threat intelligence report "
                "from AbuseIPDB. This is useful when you spot a suspicious IP in your server "
                "logs, firewall alerts, or an intrusion detection system and want to know "
                "whether it's a known bad actor before deciding how to respond.\n\n"
                "The query looks back **90 days** and uses **verbose mode**, which means "
                "you get individual reporter comments — not just a summary score. This lets "
                "you see exactly what behaviour was reported (brute force, port scan, spam, "
                "etc.) and from which countries the reports came.\n\n"
                "**IPv6 is supported** — paste the address as-is (e.g. `2001:db8::1`) and "
                "ThreatScope handles the URL encoding automatically.\n\n"
                "Each query counts against your daily API limit (1,000 checks/day on the "
                "free plan), so avoid running the same IP repeatedly."
            )
        ip_input = st.text_input(
            "IP Address",
            placeholder="e.g. 1.2.3.4 or 2001:db8::1",
            label_visibility="collapsed",
        )
        if st.button("Analyze IP", type="primary", icon=":material/search:"):
            if not ip_input.strip():
                st.warning("Please enter an IP address.")
            else:
                with st.spinner(f"Querying AbuseIPDB for {ip_input.strip()}..."):
                    raw = fetch_check(api_key, ip_input.strip())
                if raw:
                    result = parse_check(raw)
                    _render_check_result(result)

    # ── Bulk CSV ──────────────────────────────────────────────────────────────
    with mode_bulk:
        with st.expander("How to use this tab", icon=":material/help:"):
            st.markdown(
                "Use this tab when you have a batch of malicious IPs you want to report "
                "to the AbuseIPDB community. This helps other users — and automated systems "
                "around the world — block those IPs faster.\n\n"
                "**Required CSV columns:**\n"
                "| Column | Description |\n"
                "|---|---|\n"
                "| `IP` | The IP address to report (IPv4 or IPv6) |\n"
                "| `Categories` | Comma-separated category numbers (see below) |\n"
                "| `ReportDate` | When the abuse occurred, in ISO 8601 format: `2024-01-15T08:30:00+00:00` |\n"
                "| `Comment` | A brief description of what the IP did |\n\n"
                "**Common category numbers:**\n"
                "4 = DDoS Attack · 9 = Open Proxy · 11 = Email Spam · 14 = Port Scan · "
                "15 = Hacking · 16 = SQL Injection · 18 = Brute-Force · 19 = Bad Web Bot · "
                "21 = Web App Attack · 22 = SSH Attack\n\n"
                "Download the template below to see the exact format, then fill in your own "
                "data. The preview shown after upload lets you double-check before submitting."
            )
        st.markdown(
            "Upload a CSV file to bulk-report multiple IPs. "
            "Required columns: `IP`, `Categories`, `ReportDate`, `Comment`."
        )

        col_dl, _ = st.columns([1, 3])
        with col_dl:
            st.download_button(
                label="Download CSV Template",
                data=BULK_CSV_TEMPLATE,
                file_name="bulk_report_template.csv",
                mime="text/csv",
                icon=":material/download:",
            )

        uploaded_csv = st.file_uploader(
            "Upload Bulk Report CSV",
            type=["csv"],
            help="Max file size determined by your Streamlit config.",
        )

        if uploaded_csv is not None:
            raw_bytes = uploaded_csv.read()
            uploaded_csv.seek(0)
            for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
                try:
                    preview_df = pd.read_csv(io.BytesIO(raw_bytes), encoding=enc)
                    break
                except (UnicodeDecodeError, Exception):
                    continue
            else:
                st.error("Could not decode the CSV file. Please save it as UTF-8 and try again.")
                st.stop()
            st.markdown("**Preview (first 10 rows):**")
            st.dataframe(preview_df.head(10), use_container_width=True, hide_index=True)

            if st.button("Submit Bulk Report", type="primary", icon=":material/send:"):
                with st.spinner("Submitting bulk report..."):
                    raw = post_bulk_report(api_key, uploaded_csv.read(), uploaded_csv.name)
                if raw:
                    st.success("Bulk report submitted successfully!")
                    with st.expander("Submission Response"):
                        st.json(raw)

    # ── JSON Upload ───────────────────────────────────────────────────────────
    with mode_json:
        with st.expander("How to use this tab", icon=":material/help:"):
            st.markdown(
                "If you already have a saved AbuseIPDB JSON response, upload it here to "
                "visualise it with all the same charts and tables as a live query — without "
                "spending any API quota.\n\n"
                "**When is this useful?**\n"
                "- You've hit your daily API limit and want to re-examine a response you "
                "fetched earlier.\n"
                "- You're sharing findings with a colleague who doesn't have an API key.\n"
                "- You fetched data programmatically (e.g. via `curl` or a script) and "
                "saved the raw JSON for later review.\n\n"
                "**Accepted formats:**\n"
                "- A `/check` response — single IP analysis. The `data` field is a dict "
                "containing `ipAddress`, `abuseConfidenceScore`, `reports`, etc.\n"
                "- A `/blacklist` response — the `data` field is an array of IP entries.\n\n"
                "ThreatScope detects the format automatically. Just upload and it figures "
                "out which view to render."
            )
        st.markdown(
            "Upload a pre-existing AbuseIPDB JSON response (`/check` or `/blacklist`) "
            "to inspect it without making a live API call."
        )
        uploaded_json = st.file_uploader(
            "Upload JSON Response File",
            type=["json"],
            help="Accepts AbuseIPDB /check or /blacklist response JSON.",
        )

        if uploaded_json is not None:
            try:
                raw = json.load(uploaded_json)
            except json.JSONDecodeError as exc:
                st.error(f"Invalid JSON file: {exc}")
                return

            response_type = detect_response_type(raw)

            if response_type == "check":
                try:
                    result = parse_check(raw)
                    st.success("Detected: `/check` response — displaying IP analysis below.")
                    _render_check_result(result)
                except (KeyError, ValueError) as exc:
                    st.error(f"Failed to parse check response: {exc}")

            elif response_type == "blacklist":
                try:
                    bl = parse_blacklist(raw)
                    ip_count = bl.meta.count or len(bl.data)
                    st.success(
                        f"Detected: `/blacklist` response — "
                        f"**{ip_count:,} IPs** generated at `{bl.meta.generatedAt}`."
                    )
                    df = pd.DataFrame([
                        {
                            "IP Address": e.ipAddress,
                            "Abuse Score": e.abuseConfidenceScore,
                            "Last Reported": e.lastReportedAt or "—",
                            "Country": e.countryCode or "—",
                            "Usage Type": e.usageType or "—",
                            "ISP": e.isp or "—",
                            "Domain": e.domain or "—",
                            "Total Reports": e.totalReports,
                            "Distinct Users": e.numDistinctUsers,
                        }
                        for e in bl.data
                    ])
                    df = df.sort_values(
                        by=["Abuse Score", "Last Reported"],
                        ascending=[False, False],
                    ).reset_index(drop=True)
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Abuse Score": st.column_config.ProgressColumn(
                                "Abuse Score", min_value=0, max_value=100, format="%d"
                            ),
                        },
                    )
                except (KeyError, ValueError) as exc:
                    st.error(f"Failed to parse blacklist response: {exc}")

            else:
                st.error(
                    "Could not identify this JSON as a known AbuseIPDB response. "
                    "Expected a `/check` (data is a dict with ipAddress) or "
                    "`/blacklist` (data is a list) response."
                )
