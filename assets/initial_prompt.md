# ThreatScope Analytics — The Initial Prompt

This is the exact prompt used to start the project. Every requirement, constraint, and design decision was specified here before a single line of code was written. This is what "understand first, then orchestrate" looks like in practice.

---

```
Role: You are a Senior Python Developer specializing in building secure,
interactive Streamlit applications that interface with external APIs.

Task: Build a server-side security dashboard named "ThreatScope Analytics"
using Streamlit and the AbuseIPDB APIv2. The app must have a clean UI with
two primary tabs. Ensure that absolutely zero data from the JSON responses
is wasted; any extra JSON data not graphed must be accessible via Streamlit
expanders or tooltips.

Technical & API Requirements:

Authentication: The app must ask the user for their AbuseIPDB API key via
st.text_input (with type="password") and store it securely in st.session_state.

Headers & Security: Pass the key securely via the HTTP header as Key: <API_KEY>
for all requests.get() or requests.post() calls. Do not pass it in the query
string. All requests must also include Accept: application/json.

URL Encoding: Ensure all IP addresses passed to the API are URL-encoded
(using urllib.parse.quote), which is required because IPv6 addresses contain
colons.

Global Error Handling (Crucial):
  HTTP 429 (Rate Limiting): If any API call returns an HTTP 429 status code,
  gracefully catch it and display an st.error message: "Token limit exceeded.
  Please try again after some time." Do not crash the app.
  JSON Errors: The API conforms to the JSON API spec for errors. If an error
  occurs, parse the JSON for the status and detail members and display them
  to the user.

Feature Requirements:

1. Tab 1: Global Blacklist Feed (Default Tab)
   Endpoint: GET https://api.abuseipdb.com/api/v2/blacklist
   Server-Side Caching & Rate Limit Protection: The standard API limit for
   this endpoint is only 5 requests per day. Use Streamlit's
   @st.cache_data(ttl=...) to cache this response server-side. Set the TTL
   to at least a few hours to protect the quota.
   Refresh Logic: Provide a manual "Refresh" button. However, if a 429 error
   was recently encountered, prevent the refresh button from making an
   immediate API call until the daily data limit is reset, and fall back to
   displaying the cached data if available.
   Display:
     Create an st.dataframe or table displaying the top malicious IPs.
     Columns: ipAddress, abuseConfidenceScore, and lastReportedAt. Order by
     abuseConfidenceScore (descending), then lastReportedAt (most recent).
   Freshness Indicator: Read the generatedAt property from the JSON meta block
   (or X-Generated-At header) and display an st.info badge showing exactly
   when the Blacklist was generated.

2. Tab 2: Targeted IP Analysis & Input
   Inputs: Provide an st.text_input for a single IPv4/IPv6 address, and an
   st.file_uploader to accept a CSV of IPs for bulk reporting
   (POST /api/v2/bulk-report).
   Additionally, allow the user to manually upload a JSON file containing
   pre-existing API responses for direct display and review (bypassing the
   live API check).
   Endpoint (Single IP Analysis): GET https://api.abuseipdb.com/api/v2/check
   ?ipAddress=[IP]&maxAgeInDays=90&verbose=true.
   Visualizations (Based on the CHECK response):
     Use Streamlit native charts or Plotly to build visualizations:
     Abuse Confidence Gauge: A visual gauge or progress bar for
     abuseConfidenceScore.
     Country Origin: Display the countryCode/country name data.
     Usage Type: Categorize the usageType string.
   No Wasted Data (Expanders):
     For all other data (e.g., isWhitelisted, isp, domain, totalReports, and
     the raw reports array containing user comments), place this inside an
     st.expander("View Raw Intelligence Data") at the bottom of the tab.
     Display it as a cleanly formatted table or JSON dictionary so the user
     can inspect 100% of the returned data.

Create a UV project and use Streamlit for the app.
First, brainstorm with me about the project structure, design, and how you
plan to build it. Do not code unless I confirm.
```

---

## What happened next

The AI (Claude Code) responded with a full design proposal — module structure, API client design, caching strategy, tab layout, and chart choices — and asked four clarifying questions before writing a single line of code.

After confirmation, it built the entire application in one session running in auto-accept edit mode, with active monitoring throughout.

Seven bugs hit along the way. All documented in the [full build story](https://rawweights.com/guide/threatscope.html).

**Live app:** https://ipthreatscope.streamlit.app  
**Source:** https://github.com/researchsite/ai
