from __future__ import annotations
import time
from urllib.parse import quote
from typing import Any

import requests
import streamlit as st

BASE_URL = "https://api.abuseipdb.com/api/v2"
RATE_LIMIT_COOLDOWN = 86400  # 24 hours in seconds


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Key": api_key,
        "Accept": "application/json",
    }


def _handle_error_response(resp: requests.Response) -> None:
    """Parse JSON API error spec and surface via st.error."""
    if resp.status_code == 429:
        st.session_state["rate_limited_at"] = time.time()
        st.error("Token limit exceeded. Please try again after some time.")
        return

    try:
        body = resp.json()
        errors = body.get("errors", [])
        if errors:
            for err in errors:
                status = err.get("status", resp.status_code)
                detail = err.get("detail", "Unknown error")
                st.error(f"API Error {status}: {detail}")
        else:
            st.error(f"Unexpected response ({resp.status_code}): {resp.text[:300]}")
    except Exception:
        st.error(f"HTTP {resp.status_code}: {resp.text[:300]}")


def is_rate_limited() -> bool:
    ts = st.session_state.get("rate_limited_at")
    if ts is None:
        return False
    return (time.time() - ts) < RATE_LIMIT_COOLDOWN


def fetch_blacklist(api_key: str, limit: int = 10000) -> dict[str, Any] | None:
    """GET /blacklist — returns raw JSON dict or None on error."""
    try:
        resp = requests.get(
            f"{BASE_URL}/blacklist",
            headers=_headers(api_key),
            params={"limit": limit, "confidenceMinimum": 75},
            timeout=30,
        )
    except requests.RequestException as exc:
        st.error(f"Network error: {exc}")
        return None

    if resp.status_code == 200:
        return resp.json()

    _handle_error_response(resp)
    return None


def fetch_check(api_key: str, ip: str) -> dict[str, Any] | None:
    """GET /check — returns raw JSON dict or None on error."""
    encoded_ip = quote(ip.strip(), safe="")
    try:
        resp = requests.get(
            f"{BASE_URL}/check",
            headers=_headers(api_key),
            params={"ipAddress": encoded_ip, "maxAgeInDays": 90, "verbose": "true"},
            timeout=15,
        )
    except requests.RequestException as exc:
        st.error(f"Network error: {exc}")
        return None

    if resp.status_code == 200:
        return resp.json()

    _handle_error_response(resp)
    return None


def post_bulk_report(api_key: str, csv_bytes: bytes, filename: str) -> dict[str, Any] | None:
    """POST /bulk-report — returns raw JSON dict or None on error."""
    try:
        resp = requests.post(
            f"{BASE_URL}/bulk-report",
            headers=_headers(api_key),
            files={"csv": (filename, csv_bytes, "text/csv")},
            timeout=60,
        )
    except requests.RequestException as exc:
        st.error(f"Network error: {exc}")
        return None

    if resp.status_code == 200:
        return resp.json()

    _handle_error_response(resp)
    return None
