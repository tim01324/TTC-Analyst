from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pipeline_utils import (
    calculate_station_reliability,
    get_line_color,
    load_cleaned_data,
)
from project_config import CHARTS_DIR


def write_chart(fig: go.Figure, filename: str) -> None:
    html_path = CHARTS_DIR / f"{filename}.html"
    png_path = CHARTS_DIR / f"{filename}.png"

    fig.write_html(html_path)
    try:
        fig.write_image(png_path, scale=2)
    except Exception as exc:  # pragma: no cover - depends on local image engine
        print(f"Skipped PNG export for {filename}: {exc}")

    print(f"Saved {html_path}")


def create_dashboard(df: pd.DataFrame) -> go.Figure:
    total_incidents = len(df)
    total_delay = df["Min Delay"].sum()
    avg_delay = df["Min Delay"].mean()
    peak_incidents = int(df["Is Peak Hour"].sum())

    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}],
            [{"type": "indicator"}, {"type": "indicator"}],
        ],
        subplot_titles=(
            "Total Incidents",
            "Total Delay Time",
            "Average Delay",
            "Peak-Hour Incidents",
        ),
    )

    fig.add_trace(
        go.Indicator(
            mode="number",
            value=total_incidents,
            number={"font": {"size": 60, "color": "#243B53"}},
            title={"text": "Incidents", "font": {"size": 18}},
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=total_delay,
            number={"font": {"size": 60, "color": "#C05621"}, "suffix": " min"},
            title={"text": "Total Delay", "font": {"size": 18}},
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=avg_delay,
            number={"font": {"size": 60, "color": "#2B6CB0"}, "suffix": " min"},
            title={"text": "Avg Delay / Incident", "font": {"size": 18}},
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=peak_incidents,
            number={"font": {"size": 60, "color": "#D69E2E"}},
            title={
                "text": f"{peak_incidents / total_incidents * 100:.1f}% of incidents",
                "font": {"size": 18},
            },
        ),
        row=2,
        col=2,
    )

    fig.update_layout(
        title_text="TTC Subway Delay Overview",
        title_font_size=28,
        template="plotly_white",
        height=520,
    )
    return fig


def chart_line_comparison(df: pd.DataFrame) -> go.Figure:
    line_stats = (
        df.groupby("Line")
        .agg(
            total_delay=("Min Delay", "sum"),
            incident_count=("Min Delay", "count"),
            avg_delay=("Min Delay", "mean"),
            weighted_penalty=("Weighted Delay", "sum"),
        )
        .reset_index()
    )

    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "bar"}, {"type": "pie"}]],
        subplot_titles=("Total Delay Minutes", "Incident Distribution"),
    )
    fig.add_trace(
        go.Bar(
            x=line_stats["Line"],
            y=line_stats["total_delay"],
            marker_color=[get_line_color(line) for line in line_stats["Line"]],
            text=line_stats["total_delay"].apply(lambda value: f"{value:,.0f}"),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Total delay: %{y:,.0f} min<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Pie(
            labels=line_stats["Line"],
            values=line_stats["incident_count"],
            marker_colors=[get_line_color(line) for line in line_stats["Line"]],
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Incidents: %{value}<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.update_layout(
        title_text="Delay by Line",
        template="plotly_white",
        showlegend=False,
        height=500,
    )
    return fig


def chart_monthly_trend(df: pd.DataFrame) -> go.Figure:
    monthly = (
        df.groupby(["Month", "Line"])
        .agg(total_delay=("Min Delay", "sum"), incident_count=("Date", "count"))
        .reset_index()
    )

    fig = px.line(
        monthly,
        x="Month",
        y="total_delay",
        color="Line",
        color_discrete_map={
            line_name: get_line_color(line_name) for line_name in monthly["Line"].unique()
        },
        markers=True,
        title="Monthly Delay Trend",
        labels={"total_delay": "Total Delay (min)", "Month": "Month"},
    )
    fig.update_layout(template="plotly_white", hovermode="x unified", height=500)
    return fig


def chart_hourly_heatmap(df: pd.DataFrame) -> go.Figure:
    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    hourly = df.groupby(["DayOfWeek", "Hour"])["Min Delay"].sum().reset_index()
    pivot = hourly.pivot(index="DayOfWeek", columns="Hour", values="Min Delay").fillna(0)
    pivot = pivot.reindex(day_order)

    fig = px.imshow(
        pivot,
        labels={"x": "Hour", "y": "Day", "color": "Delay (min)"},
        x=[f"{hour:02d}:00" for hour in pivot.columns],
        y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        color_continuous_scale="YlOrRd",
        title="Delay Heatmap by Day and Hour",
    )
    fig.update_layout(template="plotly_white", height=420)
    return fig


def chart_station_reliability(df: pd.DataFrame) -> go.Figure:
    station_stats = calculate_station_reliability(df)
    worst = station_stats.nsmallest(15, "reliability_score")
    best = station_stats.nlargest(15, "reliability_score")

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("15 Least Reliable Stations", "15 Most Reliable Stations"),
        horizontal_spacing=0.18,
    )
    fig.add_trace(
        go.Bar(
            y=worst["Station"],
            x=worst["reliability_score"],
            orientation="h",
            marker_color="#C53030",
            text=worst["reliability_score"].apply(lambda value: f"{value:.1f}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Reliability: %{x:.1f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            y=best["Station"],
            x=best["reliability_score"],
            orientation="h",
            marker_color="#2F855A",
            text=best["reliability_score"].apply(lambda value: f"{value:.1f}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Reliability: %{x:.1f}<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.update_layout(
        title_text="Station Reliability Ranking",
        template="plotly_white",
        showlegend=False,
        height=650,
    )
    fig.update_xaxes(range=[0, 100])
    return fig


def chart_peak_comparison(df: pd.DataFrame) -> go.Figure:
    peak_stats = (
        df.groupby("Is Peak Hour")
        .agg(
            total_delay=("Min Delay", "sum"),
            incident_count=("Min Delay", "count"),
            avg_delay=("Min Delay", "mean"),
        )
        .reset_index()
    )
    peak_stats["Period"] = peak_stats["Is Peak Hour"].map(
        {True: "Peak (07-09, 16-19)", False: "Off-Peak"}
    )

    colors = ["#E76F51", "#2A9D8F"]
    fig = make_subplots(
        rows=1,
        cols=3,
        specs=[[{"type": "pie"}, {"type": "bar"}, {"type": "bar"}]],
        subplot_titles=("Incident Share", "Total Delay", "Average Delay"),
    )
    fig.add_trace(
        go.Pie(
            labels=peak_stats["Period"],
            values=peak_stats["incident_count"],
            marker_colors=colors,
            textinfo="percent+label",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=peak_stats["Period"],
            y=peak_stats["total_delay"],
            marker_color=colors,
            text=peak_stats["total_delay"].apply(lambda value: f"{value:,.0f}"),
            textposition="outside",
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Bar(
            x=peak_stats["Period"],
            y=peak_stats["avg_delay"],
            marker_color=colors,
            text=peak_stats["avg_delay"].apply(lambda value: f"{value:.1f}"),
            textposition="outside",
        ),
        row=1,
        col=3,
    )
    fig.update_layout(
        title_text="Peak vs Off-Peak Comparison",
        template="plotly_white",
        showlegend=False,
        height=430,
    )
    return fig


def chart_delay_causes(df: pd.DataFrame) -> go.Figure:
    cause_stats = (
        df.groupby("Code Description")
        .agg(total_delay=("Min Delay", "sum"), incident_count=("Min Delay", "count"))
        .reset_index()
        .nlargest(15, "total_delay")
        .rename(columns={"Code Description": "Cause"})
    )

    fig = px.sunburst(
        cause_stats,
        path=["Cause"],
        values="total_delay",
        color="total_delay",
        color_continuous_scale="Reds",
        title="Top 15 Delay Causes by Total Duration",
    )
    fig.update_layout(template="plotly_white", height=620)
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Total delay: %{value:,.0f} min<extra></extra>"
    )
    return fig


def build_all_charts(df: pd.DataFrame) -> list[tuple[str, go.Figure]]:
    return [
        ("00_dashboard", create_dashboard(df)),
        ("01_line_comparison", chart_line_comparison(df)),
        ("02_monthly_trend", chart_monthly_trend(df)),
        ("03_hourly_heatmap", chart_hourly_heatmap(df)),
        ("04_station_reliability", chart_station_reliability(df)),
        ("05_peak_comparison", chart_peak_comparison(df)),
        ("06_delay_causes", chart_delay_causes(df)),
    ]


def main() -> Path:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_cleaned_data()

    for filename, figure in build_all_charts(df):
        write_chart(figure, filename)

    print(f"All charts saved to {CHARTS_DIR}")
    return CHARTS_DIR


if __name__ == "__main__":
    main()
