from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pipeline_utils import ensure_project_directories, find_raw_data_files, save_text_report
from project_config import (
    CLEANED_DATA_FILE,
    LINE_MAPPING,
    PRIMARY_CODES_FILE,
    PROJECT_ROOT,
    SECONDARY_CODES_FILE,
    SUBWAY_LINES,
    VALIDATION_REPORT_FILE,
)


def load_codes() -> dict[str, str]:
    print("Loading code descriptions...")
    code_map: dict[str, str] = {}

    if SECONDARY_CODES_FILE.exists():
        df_csv = pd.read_csv(SECONDARY_CODES_FILE)
        df_csv.columns = df_csv.columns.str.strip().str.upper()
        if {"CODE", "DESCRIPTION"}.issubset(df_csv.columns):
            df_csv["CODE"] = df_csv["CODE"].astype(str).str.strip()
            secondary_map = dict(zip(df_csv["CODE"], df_csv["DESCRIPTION"]))
            code_map.update(secondary_map)
            print(f"Loaded {len(secondary_map)} codes from {SECONDARY_CODES_FILE.name}.")

    if PRIMARY_CODES_FILE.exists():
        df_excel = pd.read_excel(PRIMARY_CODES_FILE, header=None)

        subway_codes = df_excel.iloc[2:, [2, 3]].dropna()
        subway_codes.columns = ["Code", "Description"]

        srt_codes = df_excel.iloc[2:, [6, 7]].dropna()
        srt_codes.columns = ["Code", "Description"]

        primary_codes = pd.concat([subway_codes, srt_codes], ignore_index=True)
        primary_codes["Code"] = primary_codes["Code"].astype(str).str.strip()

        primary_map = dict(zip(primary_codes["Code"], primary_codes["Description"]))
        code_map.update(primary_map)
        print(f"Loaded {len(primary_map)} codes from {PRIMARY_CODES_FILE.name}.")

    code_map["XXXXX"] = "General/Unknown Error"
    print(f"Total unique codes available: {len(code_map)}")
    return code_map


def get_code_description(code: object, mapping: dict[str, str]) -> str:
    if pd.isna(code) or str(code).strip() in {"", "nan"}:
        return "Unknown Code"

    normalized_code = str(code).strip()
    if normalized_code in mapping:
        return mapping[normalized_code]

    prefix_map = {
        "MU": "Miscellaneous / Transportation",
        "TU": "Track / Signal",
        "PU": "Plant / Equipment",
        "EU": "Equipment",
        "SU": "Subway Service",
        "ER": "SRT Equipment",
    }
    prefix = normalized_code[:2]
    if prefix in prefix_map:
        return f"{prefix_map[prefix]} - Unknown Subcode"

    return "Unknown Code"


def load_raw_data(files: list[Path]) -> pd.DataFrame:
    dataframes: list[pd.DataFrame] = []

    for file_path in files:
        print(f"Reading {file_path.name}...")
        if file_path.suffix.lower() == ".xlsx":
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)

        if "_id" in df.columns:
            df = df.drop(columns=["_id"])

        dataframes.append(df)

    if not dataframes:
        raise ValueError("No raw delay files could be loaded.")

    return pd.concat(dataframes, ignore_index=True)


def standardize_strings(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    categorical_columns = ["Station", "Code", "Bound", "Line", "Vehicle"]

    for column in categorical_columns:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].astype(str).str.strip().str.upper()
            cleaned[column] = cleaned[column].replace(["NAN", "NONE", ""], np.nan)

    if "Station" in cleaned.columns:
        cleaned["Station"] = cleaned["Station"].str.replace(
            r"\s+STATION$", "", regex=True
        )

    if "Date" in cleaned.columns:
        cleaned["Date"] = pd.to_datetime(cleaned["Date"]).dt.date

    return cleaned


def build_validation_lines(
    total_original_rows: int,
    subway_rows_before_delay_filter: int,
    non_subway_rows_removed: int,
    count_dropped: int,
    count_kept: int,
    df_kept: pd.DataFrame,
) -> list[str]:
    verification_passed = count_kept + count_dropped == subway_rows_before_delay_filter

    lines = [
        "--- Clean Data Verification ---",
        f"Original Rows (all files): {total_original_rows}",
        f"After Subway Line Filter: {subway_rows_before_delay_filter}",
        f"Non-Subway Rows Removed: {non_subway_rows_removed}",
        f"Rows with Min Delay=0 (Dropped): {count_dropped}",
        f"Final Saved Rows: {count_kept}",
        f"Verification: {'PASSED' if verification_passed else 'FAILED'}",
        "",
        "--- Line Distribution ---",
        df_kept["Line"].value_counts().to_string(),
        "",
        "--- Peak Hour Distribution ---",
        f"Peak Hour incidents: {int(df_kept['Is Peak Hour'].sum())}",
        f"Off-Peak incidents: {int((~df_kept['Is Peak Hour']).sum())}",
        "",
        f"Rows with Unknown Codes (in final data): {len(df_kept[df_kept['Code Description'].str.contains('Unknown Code')])}",
        "",
        "Sample Data:",
        df_kept.head().to_string(),
    ]
    return lines


def clean_and_merge() -> Path:
    ensure_project_directories()

    raw_files = find_raw_data_files()
    if not raw_files:
        raise FileNotFoundError(
            "No raw delay data files found. Add TTC delay files to the project root or `data/raw/`."
        )

    print("Raw data files discovered:")
    for file_path in raw_files:
        try:
            display_path = file_path.relative_to(PROJECT_ROOT)
        except ValueError:
            display_path = file_path
        print(f"- {display_path}")

    combined = load_raw_data(raw_files)
    total_original_rows = len(combined)
    print(f"Total rows loaded: {total_original_rows}")

    combined = standardize_strings(combined)

    if "Line" in combined.columns:
        print("Applying line mapping...")
        combined["Line"] = combined["Line"].replace(LINE_MAPPING)

    subway_rows_before_line_filter = len(combined)
    combined = combined[combined["Line"].isin(SUBWAY_LINES)].copy()
    subway_rows_after_line_filter = len(combined)
    non_subway_rows_removed = (
        subway_rows_before_line_filter - subway_rows_after_line_filter
    )

    if "Time" in combined.columns:
        from pipeline_utils import is_peak_hour

        combined["Is Peak Hour"] = combined["Time"].apply(is_peak_hour)

    code_map = load_codes()
    if "Code" in combined.columns:
        combined["Code Description"] = combined["Code"].apply(
            lambda code: get_code_description(code, code_map)
        )

    combined["Min Delay"] = pd.to_numeric(
        combined["Min Delay"], errors="coerce"
    ).fillna(0)

    df_kept = combined[combined["Min Delay"] != 0].copy()
    df_dropped = combined[combined["Min Delay"] == 0].copy()

    CLEANED_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_kept.to_csv(CLEANED_DATA_FILE, index=False)

    report_lines = build_validation_lines(
        total_original_rows=total_original_rows,
        subway_rows_before_delay_filter=len(combined),
        non_subway_rows_removed=non_subway_rows_removed,
        count_dropped=len(df_dropped),
        count_kept=len(df_kept),
        df_kept=df_kept,
    )
    save_text_report(VALIDATION_REPORT_FILE, report_lines)

    print(f"Saved cleaned dataset to {CLEANED_DATA_FILE}")
    print(f"Saved validation report to {VALIDATION_REPORT_FILE}")
    return CLEANED_DATA_FILE


if __name__ == "__main__":
    clean_and_merge()
