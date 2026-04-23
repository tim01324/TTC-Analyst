from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline_utils import load_cleaned_data, save_text_report
from project_config import ANALYSIS_REPORT_FILE


def build_analysis_report(df: pd.DataFrame) -> list[str]:
    monthly = (
        df.groupby("Month")["Min Delay"]
        .agg(total_delay="sum", incident_count="count")
        .sort_values("total_delay", ascending=False)
    )
    daily = (
        df.groupby("DayOfWeek")["Min Delay"]
        .agg(total_delay="sum", incident_count="count")
        .sort_values("total_delay", ascending=False)
    )
    peak_stats = df.groupby("Is Peak Hour")["Min Delay"].agg(
        total_delay="sum", incident_count="count", avg_delay="mean"
    )
    line_stats = (
        df.groupby("Line")["Min Delay"]
        .agg(total_delay="sum", incident_count="count")
        .sort_values("total_delay", ascending=False)
    )
    top_frequency = df["Code Description"].value_counts().head(10)
    top_duration = (
        df.groupby("Code Description")["Min Delay"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    lines = [
        "TTC SUBWAY DELAY ANALYSIS REPORT",
        "=" * 40,
        f"Rows analyzed: {len(df):,}",
        f"Total delay minutes: {df['Min Delay'].sum():,.0f}",
        "",
        "1. Time Dimension",
        "-" * 40,
        "",
        "Worst months by total delay minutes:",
        monthly.head(5).to_string(),
        "",
        "Worst days of week by total delay minutes:",
        daily.to_string(),
        "",
        "Peak vs off-peak summary:",
        peak_stats.rename(index={False: "Off-Peak", True: "Peak"}).to_string(),
        "",
        "2. Spatial Dimension",
        "-" * 40,
        "",
        "Delay by subway line:",
        line_stats.to_string(),
        "",
        "3. Cause Analysis",
        "-" * 40,
        "",
        "Top 10 causes by frequency:",
        top_frequency.to_string(),
        "",
        "Top 10 causes by total delay minutes:",
        top_duration.to_string(),
    ]
    return lines


def analyze() -> Path:
    df = load_cleaned_data()
    report_path = save_text_report(ANALYSIS_REPORT_FILE, build_analysis_report(df))
    print(f"Analysis saved to {report_path}")
    return report_path


if __name__ == "__main__":
    analyze()
