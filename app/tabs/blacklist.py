from __future__ import annotations
import pandas as pd
import streamlit as st

from app.api.client import fetch_blacklist, is_rate_limited
from app.api.models import parse_blacklist


# Cache blacklist for 4 hours to protect the 5/day quota
@st.cache_data(ttl=4 * 3600, show_spinner=False)
def _cached_blacklist(api_key: str) -> dict | None:
    return fetch_blacklist(api_key)


def render(api_key: str) -> None:
    st.subheader("Global Blacklist Feed", divider="red")
    st.caption(
        "Displays IPs with an abuse confidence score >= 75. "
        "Cached for 4 hours to protect your daily API quota."
    )

    col_refresh, col_status = st.columns([1, 4])

    with col_refresh:
        rate_limited = is_rate_limited()
        refresh_clicked = st.button(
            "Refresh",
            disabled=rate_limited,
            type="primary",
            icon=":material/refresh:",
            help="Clears the cache and re-fetches from AbuseIPDB" if not rate_limited
                 else "Rate limit active — refresh unavailable until daily reset.",
        )

    if refresh_clicked and not rate_limited:
        _cached_blacklist.clear()
        st.toast("Cache cleared — fetching fresh data...", icon="🔄")

    if rate_limited:
        with col_status:
            st.warning("Rate limit active. Displaying cached data.", icon="⚠️")

    with st.spinner("Loading blacklist..."):
        raw = _cached_blacklist(api_key)

    if raw is None:
        st.error("No data available. Check your API key or network connection.")
        return

    bl = parse_blacklist(raw)

    # Freshness indicator from meta block
    if bl.meta.generatedAt:
        st.info(f"Blacklist generated at: **{bl.meta.generatedAt}**  |  "
                f"Total IPs: **{bl.meta.count:,}**", icon="ℹ️")

    if not bl.data:
        st.warning("Blacklist returned no entries.")
        return

    # Build DataFrame
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

    # Primary table: required columns
    primary_cols = ["IP Address", "Abuse Score", "Last Reported"]
    st.dataframe(
        df[primary_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Abuse Score": st.column_config.ProgressColumn(
                "Abuse Score",
                min_value=0,
                max_value=100,
                format="%d",
            ),
            "Last Reported": st.column_config.DatetimeColumn(
                "Last Reported",
                format="YYYY-MM-DD HH:mm",
            ),
        },
    )

    # Extra data in expander — nothing wasted
    with st.expander("View Full Blacklist Data (All Fields)"):
        st.caption("All fields returned by the API are shown below.")
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Distribution chart
    st.markdown("---")
    st.markdown("**Score Distribution**")
    bins = pd.cut(df["Abuse Score"], bins=[74, 85, 95, 100], labels=["75–85", "86–95", "96–100"])
    dist = bins.value_counts().sort_index().reset_index()
    dist.columns = ["Score Range", "Count"]
    st.bar_chart(dist.set_index("Score Range"))
