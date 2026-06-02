from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BlacklistEntry:
    ipAddress: str
    abuseConfidenceScore: int
    lastReportedAt: str | None = None
    countryCode: str | None = None
    usageType: str | None = None
    isp: str | None = None
    domain: str | None = None
    totalReports: int = 0
    numDistinctUsers: int = 0


@dataclass
class BlacklistMeta:
    generatedAt: str
    page: int = 1
    count: int = 0
    total: int = 0


@dataclass
class BlacklistResponse:
    meta: BlacklistMeta
    data: list[BlacklistEntry]


@dataclass
class Report:
    reportedAt: str
    comment: str
    categories: list[int]
    reporterCountryCode: str
    reporterCountryName: str


@dataclass
class CheckResponse:
    ipAddress: str
    isPublic: bool
    ipVersion: int
    isWhitelisted: bool | None
    abuseConfidenceScore: int
    countryCode: str | None
    usageType: str | None
    isp: str | None
    domain: str | None
    hostnames: list[str]
    isTor: bool
    totalReports: int
    numDistinctUsers: int
    lastReportedAt: str | None
    countryName: str | None = None
    reports: list[Report] = field(default_factory=list)


def parse_blacklist(raw: dict[str, Any]) -> BlacklistResponse:
    meta_raw = raw.get("meta", {})
    meta = BlacklistMeta(
        generatedAt=meta_raw.get("generatedAt", ""),
        page=meta_raw.get("page", 1),
        count=meta_raw.get("count", 0),
        total=meta_raw.get("total", 0),
    )
    entries = [
        BlacklistEntry(
            ipAddress=e.get("ipAddress", ""),
            abuseConfidenceScore=e.get("abuseConfidenceScore", 0),
            lastReportedAt=e.get("lastReportedAt"),
            countryCode=e.get("countryCode"),
            usageType=e.get("usageType"),
            isp=e.get("isp"),
            domain=e.get("domain"),
            totalReports=e.get("totalReports", 0),
            numDistinctUsers=e.get("numDistinctUsers", 0),
        )
        for e in raw.get("data", [])
    ]
    return BlacklistResponse(meta=meta, data=entries)


def detect_response_type(raw: dict[str, Any]) -> str:
    """Return 'check', 'blacklist', or 'unknown' based on JSON structure."""
    data = raw.get("data")
    if isinstance(data, list):
        return "blacklist"
    if isinstance(data, dict) and "ipAddress" in data:
        return "check"
    if isinstance(raw, dict) and "ipAddress" in raw:
        return "check"
    return "unknown"


def parse_check(raw: dict[str, Any]) -> CheckResponse:
    d = raw.get("data", raw)
    if isinstance(d, list):
        raise ValueError(
            "This JSON is a blacklist response, not a /check response. "
            "Use the Blacklist tab or upload a single-IP check result."
        )
    reports = [
        Report(
            reportedAt=r.get("reportedAt", ""),
            comment=r.get("comment", ""),
            categories=r.get("categories", []),
            reporterCountryCode=r.get("reporterCountryCode", ""),
            reporterCountryName=r.get("reporterCountryName", ""),
        )
        for r in d.get("reports", [])
    ]
    return CheckResponse(
        ipAddress=d.get("ipAddress", ""),
        isPublic=d.get("isPublic", True),
        ipVersion=d.get("ipVersion", 4),
        isWhitelisted=d.get("isWhitelisted"),
        abuseConfidenceScore=d.get("abuseConfidenceScore", 0),
        countryCode=d.get("countryCode"),
        countryName=d.get("countryName"),
        usageType=d.get("usageType"),
        isp=d.get("isp"),
        domain=d.get("domain"),
        hostnames=d.get("hostnames", []),
        isTor=d.get("isTor", False),
        totalReports=d.get("totalReports", 0),
        numDistinctUsers=d.get("numDistinctUsers", 0),
        lastReportedAt=d.get("lastReportedAt"),
        reports=reports,
    )
