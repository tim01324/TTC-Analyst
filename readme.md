# TTC Subway Delay Data Analysis (2024-2025) 🚇

## 📊 Project Overview
This project provides a comprehensive analysis and cleaning of subway delay data from the Toronto Transit Commission (TTC) for the years 2024 and 2025. By implementing a **Relative Impact Score** model, we move beyond simple delay counts to reflect the actual "pain level" experienced by commuters, especially during peak hours.

---

## 📈 Visual Analytics (English)

### 0. System Dashboard
![Dashboard](charts/00_dashboard.png)
> High-level overview of total incidents, accumulated delay minutes, and average impact per incident.

### 1. Line Performance Comparison
![Line Comparison](charts/01_line_comparison.png)
> **Insight**: Line 1 (YU) handles the highest volume of incidents, while Line 4 (Sheppard) remains the most reliable line in the system.

### 2. Monthly Delay Trend
![Monthly Trend](charts/02_monthly_trend.png)
> Tracking seasonal fluctuations and monthly performance across all lines.

### 3. Hourly Delay Heatmap
![Hourly Heatmap](charts/03_hourly_heatmap.png)
> **Insight**: Deep red areas clearly identify morning and evening rush hours (Mon-Fri) as the high-risk periods for delays.

### 4. Station Reliability Rankings
![Station Reliability](charts/04_station_reliability.png)
> Identification of the "Most Reliable" vs. "Least Reliable" stations. Stations like `EGLINTON` and `KIPLING` currently show the lowest reliability scores.

### 5. Peak vs. Off-Peak Analysis
![Peak Comparison](charts/05_peak_comparison.png)

### 6. Principal Delay Causes
![Delay Causes](charts/06_delay_causes.png)
> Root cause analysis using a sunburst distribution to visualize the impact of different delay codes.

---

## 🔍 Advanced Reporting & Methodology
We utilize a weighted Scoring model to evaluate system performance:
- **Peak Hour Weighting (07:00-09:00, 16:00-19:00)**: Assigned a **1.5x multiplier** to reflect the higher social cost of delays during rush hour.
- **Reliability Score**: Normalized from 0 to 100, where 0 represents the system's worst-performing entity and 100 represents theoretical perfection.

### 2024 vs. 2025 Comparative Trends
- **Incident Frequency**: 2025 has seen a **21.0% decrease** in total incidents compared to 2024.
- **Total Delay Duration**: Decreased by **21.7%**.
- **Average Impact Index**: Decreased slightly by **1.9%**, suggesting that while frequency is down, the severity of individual incidents remains consistent.

---

## 🛠️ Data Pipeline
1. **Consolidation**: Merged multi-format data (Excel/CSV) from 2024 and 2025.
2. **Standardization**:
    - Normalized station names (e.g., merging `WARDEN STATION` and `WARDEN`).
    - Standardized abbreviations (e.g., `VMC` -> `VAUGHAN METROPOLITAN CENTRE`).
3. **Refinement**: Filtered out non-revenue incidents (`Min Delay = 0`) and maintenance areas (`YARD`, `TAIL TRACK`).
4. **Visualization**: Automated English-language reporting using Python & Plotly.

---

## 🚀 Interactive Access
The interactive HTML versions of these charts are available in the `charts/` directory. You can open them in any browser for full zoom and hover capabilities:
- [Open Master Dashboard](charts/00_dashboard.html)
- [Open Hourly Heatmap](charts/03_hourly_heatmap.html)

---
*Last Updated: 2025-12-26*