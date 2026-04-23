from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from project_config import (
    CHARTS_DIR,
    CLEANED_DATA_FILE,
    LEGACY_CLEANED_DATA_FILE,
    LINE_COLORS,
    MIN_STATION_INCIDENT_THRESHOLD,
    OFF_PEAK_WEIGHT,
    PEAK_WEIGHT,
    PEAK_WINDOWS,
    PRIMARY_CODES_FILE,
    PROCESSED_DATA_DIR,
    RAW_DATA_KEYWORDS,
    RAW_DATA_SEARCH_DIRS,
    REPORTS_DIR,
    SECONDARY_CODES_FILE,
    STATION_EXCLUDE_KEYWORDS,
    SUPPORTED_INPUT_SUFFIXES,
)


def ensure_project_directories() -> None:
    for directory in (PROCESSED_DATA_DIR, REPORTS_DIR, CHARTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def read_csv_with_fallback(path: Path, **kwargs) -> pd.DataFrame:
    encodings = ("utf-8", "cp1252")
    last_error = None

    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding, **kwargs)
        except UnicodeDecodeError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    return pd.read_csv(path, **kwargs)


def get_cleaned_data_path() -> Path:
    if CLEANED_DATA_FILE.exists():
        return CLEANED_DATA_FILE
    return LEGACY_CLEANED_DATA_FILE


def load_cleaned_data() -> pd.DataFrame:
    cleaned_path = get_cleaned_data_path()
    if not cleaned_path.exists():
        raise FileNotFoundError(
            "Cleaned dataset not found. Run `python run_pipeline.py` first."
        )

    df = read_csv_with_fallback(cleaned_path)
    return enrich_delay_data(df)


def find_raw_data_files() -> list[Path]:
    discovered: list[Path] = []
    seen: set[Path] = set()

    for directory in RAW_DATA_SEARCH_DIRS:
        if not directory.exists():
            continue

        for path in sorted(directory.iterdir()):
            if not path.is_file():
                continue

            lowered_name = path.name.lower()
            if "cleaned" in lowered_name:
                continue
            if path.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
                continue
            if not all(keyword in lowered_name for keyword in RAW_DATA_KEYWORDS):
                continue
            if path in {PRIMARY_CODES_FILE, SECONDARY_CODES_FILE}:
                continue
            if path in seen:
                continue

            discovered.append(path)
            seen.add(path)

    return discovered


def is_peak_hour(time_value: object) -> bool:
    try:
        hour = int(str(time_value).split(":")[0])
    except (TypeError, ValueError, AttributeError, IndexError):
        return False

    return any(start <= hour < end for start, end in PEAK_WINDOWS)


def enrich_delay_data(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()

    if "Date" in enriched.columns:
        enriched["Date"] = pd.to_datetime(enriched["Date"])
        enriched["Month"] = enriched["Date"].dt.to_period("M").astype(str)
        enriched["Year"] = enriched["Date"].dt.year
        enriched["DayOfWeek"] = enriched["Date"].dt.day_name()

    if "Time" in enriched.columns:
        enriched["Hour"] = enriched["Time"].apply(parse_hour)
        enriched["Is Peak Hour"] = enriched["Time"].apply(is_peak_hour)
    else:
        enriched["Hour"] = 0
        enriched["Is Peak Hour"] = False

    if "Min Delay" in enriched.columns:
        enriched["Min Delay"] = pd.to_numeric(
            enriched["Min Delay"], errors="coerce"
        ).fillna(0)

    enriched["Peak Weight"] = enriched["Is Peak Hour"].map(
        lambda is_peak: PEAK_WEIGHT if is_peak else OFF_PEAK_WEIGHT
    )
    enriched["Weighted Delay"] = enriched["Min Delay"] * enriched["Peak Weight"]

    return enriched


def parse_hour(time_value: object) -> int:
    try:
        return int(str(time_value).split(":")[0])
    except (TypeError, ValueError, AttributeError, IndexError):
        return 0


def format_distribution(series: pd.Series) -> str:
    if series.empty:
        return "No records found."
    return series.to_string()


def is_valid_station_name(station_name: object) -> bool:
    station_upper = str(station_name).upper()
    return not any(keyword in station_upper for keyword in STATION_EXCLUDE_KEYWORDS)


def calculate_station_reliability(df: pd.DataFrame) -> pd.DataFrame:
    station_stats = (
        df.groupby("Station")
        .agg(
            total_delay=("Min Delay", "sum"),
            incident_count=("Min Delay", "count"),
            weighted_penalty=("Weighted Delay", "sum"),
        )
        .reset_index()
    )

    filtered = station_stats[
        (station_stats["incident_count"] >= MIN_STATION_INCIDENT_THRESHOLD)
        & (station_stats["Station"].apply(is_valid_station_name))
    ].copy()

    if filtered.empty:
        filtered["reliability_score"] = pd.Series(dtype=float)
        filtered["avg_delay"] = pd.Series(dtype=float)
        return filtered

    max_penalty = filtered["weighted_penalty"].max()
    filtered["reliability_score"] = 100 - (
        filtered["weighted_penalty"] / max_penalty * 100
    )
    filtered["avg_delay"] = filtered["total_delay"] / filtered["incident_count"]
    return filtered


def save_text_report(path: Path, lines: Iterable[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        file.write("\n".join(lines).rstrip() + "\n")
    return path


def get_line_color(line_name: str) -> str:
    return LINE_COLORS.get(line_name, "#7F8C8D")

