from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline_utils import (
    calculate_station_reliability,
    load_cleaned_data,
    save_text_report,
)
from project_config import (
    METRICS_REPORT_FILE,
    MIN_STATION_INCIDENT_THRESHOLD,
    PEAK_WEIGHT,
    STATION_EXCLUDE_KEYWORDS,
)


def build_metrics_report(df: pd.DataFrame) -> list[str]:
    total_delay = df["Min Delay"].sum()
    total_weighted_delay = df["Weighted Delay"].sum()
    total_incidents = len(df)
    avg_delay_global = total_delay / total_incidents if total_incidents else 0
    avg_weighted_delay = (
        total_weighted_delay / total_incidents if total_incidents else 0
    )

    line_stats = (
        df.groupby("Line")
        .agg(
            total_delay=("Min Delay", "sum"),
            incident_count=("Min Delay", "count"),
            weighted_penalty=("Weighted Delay", "sum"),
        )
        .reset_index()
    )
    max_line_penalty = line_stats["weighted_penalty"].max()
    line_stats["reliability_score"] = 100 - (
        line_stats["weighted_penalty"] / max_line_penalty * 100
    )
    line_stats["avg_delay_per_incident"] = (
        line_stats["total_delay"] / line_stats["incident_count"]
    )
    line_stats = line_stats.sort_values("reliability_score", ascending=False)

    station_stats = calculate_station_reliability(df)
    worst_stations = station_stats.sort_values("reliability_score").head(10)
    best_stations = station_stats.sort_values("reliability_score", ascending=False).head(10)

    peak_stats = (
        df.groupby("Is Peak Hour")
        .agg(
            total_delay=("Min Delay", "sum"),
            incident_count=("Min Delay", "count"),
            avg_delay=("Min Delay", "mean"),
        )
        .rename(index={False: "Off-Peak", True: "Peak"})
    )

    yearly_stats = (
        df[df["Year"].isin([2024, 2025])]
        .groupby("Year")
        .agg(
            total_delay=("Min Delay", "sum"),
            incident_count=("Min Delay", "count"),
            weighted_penalty=("Weighted Delay", "sum"),
        )
        .reset_index()
    )

    lines = [
        "ADVANCED METRICS REPORT",
        "=" * 60,
        "Methodology",
        f"- Peak windows: 07:00-09:00 and 16:00-19:00",
        f"- Peak-hour weight: {PEAK_WEIGHT:.1f}x",
        "- Reliability Score = 100 - (weighted penalty / worst penalty in group x 100)",
        "",
        "System Summary",
        "-" * 60,
        f"Total incidents: {total_incidents:,}",
        f"Total delay minutes: {total_delay:,.0f}",
        f"Total weighted delay: {total_weighted_delay:,.0f}",
        f"Average delay per incident: {avg_delay_global:.2f} minutes",
        f"Average weighted delay per incident: {avg_weighted_delay:.2f}",
        "",
        "Line Reliability Score",
        "-" * 60,
        line_stats.to_string(index=False),
        "",
        "Station Reliability Score",
        "-" * 60,
        f"Station filter: incidents >= {MIN_STATION_INCIDENT_THRESHOLD}",
        f"Excluded keywords: {', '.join(STATION_EXCLUDE_KEYWORDS)}",
        f"Stations included after filtering: {len(station_stats)}",
        "",
        "10 least reliable stations:",
        worst_stations[["Station", "incident_count", "weighted_penalty", "reliability_score"]].to_string(index=False),
        "",
        "10 most reliable stations:",
        best_stations[["Station", "incident_count", "weighted_penalty", "reliability_score"]].to_string(index=False),
        "",
        "Peak vs Off-Peak",
        "-" * 60,
        peak_stats.to_string(),
        "",
        "Year-over-Year Trend (2024 vs 2025)",
        "-" * 60,
    ]

    if len(yearly_stats) >= 2:
        y2024 = yearly_stats[yearly_stats["Year"] == 2024].iloc[0]
        y2025 = yearly_stats[yearly_stats["Year"] == 2025].iloc[0]

        incident_change = (
            (y2025["incident_count"] - y2024["incident_count"])
            / y2024["incident_count"]
            * 100
        )
        delay_change = (
            (y2025["total_delay"] - y2024["total_delay"]) / y2024["total_delay"] * 100
        )
        impact_2024 = y2024["weighted_penalty"] / y2024["incident_count"]
        impact_2025 = y2025["weighted_penalty"] / y2025["incident_count"]
        impact_change = ((impact_2025 - impact_2024) / impact_2024) * 100

        lines.extend(
            [
                yearly_stats.to_string(index=False),
                "",
                f"Incident count change: {incident_change:+.1f}%",
                f"Total delay change: {delay_change:+.1f}%",
                f"Weighted impact per incident change: {impact_change:+.1f}%",
            ]
        )
    else:
        lines.append("Not enough data for a 2024 vs 2025 comparison.")

    return lines


def calculate_metrics() -> Path:
    df = load_cleaned_data()
    report_path = save_text_report(METRICS_REPORT_FILE, build_metrics_report(df))
    print(f"Metrics saved to {report_path}")
    return report_path


if __name__ == "__main__":
    calculate_metrics()
