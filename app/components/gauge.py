from __future__ import annotations
import plotly.graph_objects as go
import streamlit as st


def render_abuse_gauge(score: int, key: str = "gauge") -> None:
    """Render a Plotly gauge for abuseConfidenceScore (0–100)."""
    if score <= 25:
        bar_color = "#2ecc71"   # green
    elif score <= 60:
        bar_color = "#f39c12"   # orange
    else:
        bar_color = "#e74c3c"   # red

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={"text": "Abuse Confidence Score", "font": {"size": 18}},
        delta={"reference": 50, "increasing": {"color": "#e74c3c"}, "decreasing": {"color": "#2ecc71"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#7f8c8d"},
            "bar": {"color": bar_color},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "#bdc3c7",
            "steps": [
                {"range": [0, 25], "color": "#d5f5e3"},
                {"range": [25, 60], "color": "#fef9e7"},
                {"range": [60, 100], "color": "#fadbd8"},
            ],
            "threshold": {
                "line": {"color": "#2c3e50", "width": 4},
                "thickness": 0.75,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        height=280,
        margin={"t": 60, "b": 20, "l": 30, "r": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#2c3e50"},
    )
    st.plotly_chart(fig, use_container_width=True, key=key)
