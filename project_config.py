from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
CHARTS_DIR = PROJECT_ROOT / "charts"

CLEANED_DATA_FILENAME = "TTC_Subway_Delay_Data_Combined_Cleaned.csv"
ANALYSIS_REPORT_FILENAME = "analysis_results.txt"
METRICS_REPORT_FILENAME = "advanced_metrics_results.txt"
VALIDATION_REPORT_FILENAME = "validation_summary.txt"

PRIMARY_CODES_FILE = PROJECT_ROOT / "ttc-subway-delay-codes.xlsx"
SECONDARY_CODES_FILE = PROJECT_ROOT / "Code Descriptions.csv"

LEGACY_CLEANED_DATA_FILE = PROJECT_ROOT / CLEANED_DATA_FILENAME
CLEANED_DATA_FILE = PROCESSED_DATA_DIR / CLEANED_DATA_FILENAME
ANALYSIS_REPORT_FILE = REPORTS_DIR / ANALYSIS_REPORT_FILENAME
METRICS_REPORT_FILE = REPORTS_DIR / METRICS_REPORT_FILENAME
VALIDATION_REPORT_FILE = REPORTS_DIR / VALIDATION_REPORT_FILENAME

RAW_DATA_SEARCH_DIRS = (RAW_DATA_DIR, PROJECT_ROOT)
RAW_DATA_KEYWORDS = ("ttc", "subway", "delay", "data")
SUPPORTED_INPUT_SUFFIXES = {".csv", ".xlsx"}

LINE_MAPPING = {
    "YU": "Line 1 Yonge-University",
    "YUS": "Line 1 Yonge-University",
    "BD": "Line 2 Bloor-Danforth",
    "SHP": "Line 4 Sheppard",
    "SRT": "Line 3 Scarborough RT",
}

SUBWAY_LINES = (
    "Line 1 Yonge-University",
    "Line 2 Bloor-Danforth",
    "Line 4 Sheppard",
)

PEAK_WINDOWS = ((7, 9), (16, 19))
PEAK_WEIGHT = 1.5
OFF_PEAK_WEIGHT = 1.0

MIN_STATION_INCIDENT_THRESHOLD = 50
STATION_EXCLUDE_KEYWORDS = (
    "APPROACHING",
    " TO ",
    "BUILDING",
    "TRACK LEVEL",
    "CENTRE TRACK",
    "TAIL TRACK",
    "CROSSOVER",
    "YARD",
    "LOOP",
    "SIDING",
    "POCKET",
)

LINE_COLORS = {
    "Line 1 Yonge-University": "#FFCC00",
    "Line 2 Bloor-Danforth": "#00A859",
    "Line 4 Sheppard": "#A349A4",
}

