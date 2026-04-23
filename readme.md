# TTC Analyst Portfolio Project

This project turns raw TTC subway delay logs into a reproducible analyst workflow with three deliverables:

- a cleaned dataset for downstream analysis
- text reports that explain the system and reliability metrics
- interactive visuals and a lightweight Streamlit demo for interviews

The target audience is a hiring manager or interviewer reviewing a Data Analyst / BI portfolio in 3 to 5 minutes.

## Live Demo

Streamlit app: https://ttc-analyst-fd7ka9hbucujfv2ptgupjz.streamlit.app/

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py
streamlit run app.py
```

If you want to keep raw input files outside the repo root, place them in `data/raw/`.

## What The Pipeline Produces

- Cleaned data: `data/processed/TTC_Subway_Delay_Data_Combined_Cleaned.csv`
- Validation summary: `reports/validation_summary.txt`
- Analysis report: `reports/analysis_results.txt`
- Advanced metrics report: `reports/advanced_metrics_results.txt`
- Interactive charts: `charts/00_dashboard.html` to `charts/06_delay_causes.html`

## Interview Flow

### 1. Business Question
Where is the TTC subway system least reliable, when do delays hurt riders the most, and which causes create the biggest operational pain?

### 2. Analytical Approach
- Consolidate raw TTC delay files from CSV and Excel sources.
- Standardize line names and station labels.
- Remove zero-minute incidents from the final analytical dataset.
- Apply a shared peak-hour rule across cleaning, metrics, and charts.
- Score reliability with a weighted penalty model instead of raw counts alone.

### 3. Shared Business Rules
- Peak windows: `07:00-09:00` and `16:00-19:00`
- Peak-hour weight: `1.5x`
- Subway scope: `Line 1`, `Line 2`, and `Line 4`
- Station reliability filter: at least `50` incidents and no yard / track-area records

These rules now live in shared configuration so every script uses the same definitions.

## Key Insights

- Line 1 carries the largest total delay burden and the highest incident volume.
- Delay risk clusters around weekday commute windows, which is why the heatmap is a core evidence chart.
- Reliability looks different when peak-hour pain is weighted: the ranking is not just about frequency, but rider impact.

## Evidence To Show In Interviews

- Live app: https://ttc-analyst-fd7ka9hbucujfv2ptgupjz.streamlit.app/
- Main overview: [charts/00_dashboard.html](/Users/tim/Desktop/TTC-Analyst/charts/00_dashboard.html)
- Peak risk evidence: [charts/03_hourly_heatmap.html](/Users/tim/Desktop/TTC-Analyst/charts/03_hourly_heatmap.html)
- Reliability ranking: [charts/04_station_reliability.html](/Users/tim/Desktop/TTC-Analyst/charts/04_station_reliability.html)
- Metrics report: [reports/advanced_metrics_results.txt](/Users/tim/Desktop/TTC-Analyst/reports/advanced_metrics_results.txt)
- Interview talk track: [interview_talk_track.md](/Users/tim/Desktop/TTC-Analyst/interview_talk_track.md)

## Validation Baseline

The versioned baseline reference is [validation_summary.txt](/Users/tim/Desktop/TTC-Analyst/validation_summary.txt). A fresh rerun should match these core figures:

- Original rows loaded: `47,730`
- Subway rows after line filter: `46,951`
- Zero-delay rows dropped: `30,142`
- Final saved rows: `16,809`
- Peak-hour incidents: `4,872`
- Unknown codes in final dataset: `0`

Your new run writes the comparable output to [reports/validation_summary.txt](/Users/tim/Desktop/TTC-Analyst/reports/validation_summary.txt).

## Project Structure

```text
.
|-- app.py
|-- run_pipeline.py
|-- clean_data.py
|-- analyze_delays.py
|-- advanced_metrics.py
|-- interactive_charts.py
|-- project_config.py
|-- pipeline_utils.py
|-- data/
|   |-- raw/
|   `-- processed/
|-- reports/
`-- charts/
```

## Demo Notes

The Streamlit app is intentionally lightweight:

- KPI summary for fast scanning
- evidence charts for line performance, time-of-day risk, and station reliability
- short narrative blocks you can use as speaking prompts

That keeps the portfolio focused on analyst storytelling instead of app complexity.
