from __future__ import annotations

import streamlit as st

from interactive_charts import (
    chart_hourly_heatmap,
    chart_line_comparison,
    chart_monthly_trend,
    chart_station_reliability,
)
from pipeline_utils import calculate_station_reliability, load_cleaned_data


st.set_page_config(
    page_title="TTC Analyst Demo",
    page_icon="🚇",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top right, rgba(243, 156, 18, 0.18), transparent 30%),
            linear-gradient(180deg, #f8f5ef 0%, #eef3f7 55%, #ffffff 100%);
        font-family: "Avenir Next", "Segoe UI", sans-serif;
    }
    .hero {
        padding: 1.2rem 1.4rem;
        border-radius: 22px;
        background: linear-gradient(135deg, rgba(29, 53, 87, 0.96), rgba(67, 97, 122, 0.92));
        color: #f8fafc;
        margin-bottom: 1rem;
        box-shadow: 0 18px 40px rgba(29, 53, 87, 0.18);
    }
    .insight-card {
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid rgba(29, 53, 87, 0.08);
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        min-height: 150px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_app() -> None:
    try:
        df = load_cleaned_data()
    except FileNotFoundError:
        st.error("Cleaned data not found. Run `python run_pipeline.py` first.")
        return

    station_scores = calculate_station_reliability(df)
    if station_scores.empty:
        st.error("Station reliability output is empty. Check the cleaned dataset and filters.")
        return

    worst_station = station_scores.sort_values("reliability_score").iloc[0]
    top_line = (
        df.groupby("Line")["Min Delay"].sum().sort_values(ascending=False).index[0]
    )
    peak_share = df["Is Peak Hour"].mean() * 100

    st.markdown(
        """
        <div class="hero">
            <h1 style="margin-bottom:0.2rem;">TTC Delay Reliability Story</h1>
            <p style="font-size:1.05rem; margin-bottom:0;">
                A compact BI demo that shows where delay risk concentrates, how peak-hour pain changes the picture,
                and which stations deserve deeper operational attention.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
    kpi_1.metric("Incidents", f"{len(df):,}")
    kpi_2.metric("Total Delay", f"{df['Min Delay'].sum():,.0f} min")
    kpi_3.metric("Peak-Hour Share", f"{peak_share:.1f}%")
    kpi_4.metric("Lowest Reliability Station", worst_station["Station"])

    insight_1, insight_2, insight_3 = st.columns(3)
    insight_1.markdown(
        f"""
        <div class="insight-card">
            <h4>System Burden</h4>
            <p><strong>{top_line}</strong> carries the largest total delay load in the analytical dataset.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    insight_2.markdown(
        f"""
        <div class="insight-card">
            <h4>Peak-Hour Risk</h4>
            <p><strong>{peak_share:.1f}%</strong> of incidents happen during weighted peak windows, amplifying rider impact.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    insight_3.markdown(
        f"""
        <div class="insight-card">
            <h4>Reliability Signal</h4>
            <p><strong>{worst_station['Station']}</strong> ranks as the weakest filtered station on the weighted reliability score.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_summary, tab_evidence, tab_method = st.tabs(
        ["Executive Summary", "Evidence Charts", "Method"]
    )

    with tab_summary:
        st.subheader("What to say in 60-90 seconds")
        st.write(
            "I used TTC subway delay logs to build a reproducible analyst workflow, not just a one-off notebook. "
            "The key move was to weight incidents that hit riders during peak commuting windows, which gives a more business-relevant view of reliability. "
            "The result shows where delay pain is concentrated by line, time of day, and station, and it gives operations or planning teams a clearer shortlist for action."
        )
        st.plotly_chart(chart_line_comparison(df), use_container_width=True)

    with tab_evidence:
        left, right = st.columns(2)
        left.plotly_chart(chart_hourly_heatmap(df), use_container_width=True)
        right.plotly_chart(chart_station_reliability(df), use_container_width=True)
        st.plotly_chart(chart_monthly_trend(df), use_container_width=True)

    with tab_method:
        st.write("Shared business rules keep the outputs consistent across cleaning, metrics, charts, and the Streamlit demo.")
        st.code(
            "\n".join(
                [
                    "Peak windows: 07:00-09:00 and 16:00-19:00",
                    "Peak-hour weight: 1.5x",
                    "Subway scope: Line 1, Line 2, Line 4",
                    "Station reliability filter: >= 50 incidents and no yard / track-area records",
                ]
            )
        )


if __name__ == "__main__":
    render_app()
