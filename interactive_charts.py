"""
TTC 地鐵延遲數據 - 互動式圖表生成器
使用 Plotly 產生互動式 HTML 圖表
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# 檔案路徑
data_dir = r"c:\Users\tim01\Desktop\TTC"
cleaned_file = os.path.join(data_dir, "TTC_Subway_Delay_Data_Combined_Cleaned.csv")
output_dir = os.path.join(data_dir, "charts")

# 建立輸出資料夾
os.makedirs(output_dir, exist_ok=True)

# 顏色主題
COLORS = {
    "Line 1 Yonge-University": "#FFCC00",  # 黃色
    "Line 2 Bloor-Danforth": "#00A859",    # 綠色
    "Line 4 Sheppard": "#A349A4",          # 紫色
}

def load_data():
    """載入並預處理數據"""
    try:
        df = pd.read_csv(cleaned_file, encoding="utf-8")
    except:
        df = pd.read_csv(cleaned_file, encoding="cp1252")
    
    df["Date"] = pd.to_datetime(df["Date"])
    df["Min Delay"] = pd.to_numeric(df["Min Delay"], errors="coerce").fillna(0)
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    df["DayOfWeek"] = df["Date"].dt.day_name()
    df["Hour"] = df["Time"].apply(lambda x: int(str(x).split(":")[0]) if pd.notna(x) else 0)
    
    # 尖峰時段加權
    if "Is Peak Hour" not in df.columns:
        df["Is Peak Hour"] = df["Hour"].apply(lambda h: (7 <= h < 9) or (16 <= h < 19))
    
    df["Peak Weight"] = df["Is Peak Hour"].apply(lambda x: 1.5 if x else 1.0)
    df["Weighted Delay"] = df["Min Delay"] * df["Peak Weight"]
    
    return df


def chart_line_comparison(df):
    """圖表 1: 路線延遲比較 (柱狀圖 + 餅圖)"""
    
    line_stats = df.groupby("Line").agg({
        "Min Delay": ["sum", "count", "mean"],
        "Weighted Delay": "sum"
    }).reset_index()
    line_stats.columns = ["Line", "Total Delay", "Incident Count", "Avg Delay", "Weighted Penalty"]
    
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "bar"}, {"type": "pie"}]],
        subplot_titles=("總延遲分鐘數", "事故比例分佈")
    )
    
    # 柱狀圖
    fig.add_trace(
        go.Bar(
            x=line_stats["Line"],
            y=line_stats["Total Delay"],
            marker_color=[COLORS.get(line, "#888") for line in line_stats["Line"]],
            text=line_stats["Total Delay"].apply(lambda x: f"{x:,.0f}"),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>總延遲: %{y:,.0f} 分鐘<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 餅圖
    fig.add_trace(
        go.Pie(
            labels=line_stats["Line"],
            values=line_stats["Incident Count"],
            marker_colors=[COLORS.get(line, "#888") for line in line_stats["Line"]],
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>事故次數: %{value}<br>佔比: %{percent}<extra></extra>"
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title_text="🚇 TTC 地鐵路線延遲分析",
        title_font_size=24,
        showlegend=False,
        height=500
    )
    
    fig.write_html(os.path.join(output_dir, "01_line_comparison.html"))
    print("[OK] Chart 1: Line Comparison generated")


def chart_monthly_trend(df):
    """圖表 2: 月度趨勢圖"""
    
    monthly = df.groupby(["Month", "Line"]).agg({
        "Min Delay": "sum",
        "Date": "count"
    }).reset_index()
    monthly.columns = ["Month", "Line", "Total Delay", "Incident Count"]
    
    fig = px.line(
        monthly,
        x="Month",
        y="Total Delay",
        color="Line",
        color_discrete_map=COLORS,
        markers=True,
        title="📈 月度延遲趨勢",
        labels={"Total Delay": "總延遲 (分鐘)", "Month": "月份"}
    )
    
    fig.update_layout(
        hovermode="x unified",
        legend_title_text="路線",
        height=500
    )
    
    fig.write_html(os.path.join(output_dir, "02_monthly_trend.html"))
    print("[OK] Chart 2: Monthly Trend generated")


def chart_hourly_heatmap(df):
    """圖表 3: 時段熱力圖"""
    
    # 星期排序
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    hourly = df.groupby(["DayOfWeek", "Hour"])["Min Delay"].sum().reset_index()
    hourly_pivot = hourly.pivot(index="DayOfWeek", columns="Hour", values="Min Delay").fillna(0)
    
    # 按星期排序
    hourly_pivot = hourly_pivot.reindex(day_order)
    
    fig = px.imshow(
        hourly_pivot,
        labels=dict(x="小時", y="星期", color="延遲分鐘"),
        x=[f"{h:02d}:00" for h in hourly_pivot.columns],
        y=["週一", "週二", "週三", "週四", "週五", "週六", "週日"],
        color_continuous_scale="YlOrRd",
        title="🔥 延遲熱力圖 (按星期 × 時段)"
    )
    
    fig.update_layout(height=400)
    
    fig.write_html(os.path.join(output_dir, "03_hourly_heatmap.html"))
    print("[OK] Chart 3: Hourly Heatmap generated")


def chart_station_reliability(df):
    """圖表 4: 車站可靠性排名 (水平柱狀圖)"""
    
    # 過濾條件
    MIN_INCIDENTS = 50
    EXCLUDE_KEYWORDS = ["APPROACHING", " TO ", "BUILDING", "TRACK LEVEL", "CENTRE TRACK"]
    
    station_stats = df.groupby("Station").agg({
        "Weighted Delay": "sum",
        "Min Delay": "count"
    }).reset_index()
    station_stats.columns = ["Station", "Weighted Penalty", "Incident Count"]
    
    # 過濾
    def is_valid(name):
        for kw in EXCLUDE_KEYWORDS:
            if kw in str(name).upper():
                return False
        return True
    
    station_stats = station_stats[
        (station_stats["Incident Count"] >= MIN_INCIDENTS) &
        (station_stats["Station"].apply(is_valid))
    ]
    
    max_penalty = station_stats["Weighted Penalty"].max()
    station_stats["Reliability Score"] = 100 - (station_stats["Weighted Penalty"] / max_penalty * 100)
    
    # Top 15 最差 + Top 15 最好
    worst = station_stats.nsmallest(15, "Reliability Score")
    best = station_stats.nlargest(15, "Reliability Score")
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("⚠️ 最不可靠的 15 個車站", "✅ 最可靠的 15 個車站"),
        horizontal_spacing=0.15
    )
    
    # 最差
    fig.add_trace(
        go.Bar(
            y=worst["Station"],
            x=worst["Reliability Score"],
            orientation="h",
            marker_color="crimson",
            text=worst["Reliability Score"].apply(lambda x: f"{x:.1f}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>可靠性: %{x:.1f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 最好
    fig.add_trace(
        go.Bar(
            y=best["Station"],
            x=best["Reliability Score"],
            orientation="h",
            marker_color="seagreen",
            text=best["Reliability Score"].apply(lambda x: f"{x:.1f}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>可靠性: %{x:.1f}<extra></extra>"
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title_text="🏆 車站可靠性排名 (過濾後)",
        height=600,
        showlegend=False
    )
    
    fig.update_xaxes(range=[0, 100])
    
    fig.write_html(os.path.join(output_dir, "04_station_reliability.html"))
    print("[OK] Chart 4: Station Reliability generated")


def chart_peak_comparison(df):
    """圖表 5: 尖峰 vs 離峰比較"""
    
    peak_stats = df.groupby("Is Peak Hour").agg({
        "Min Delay": ["sum", "count", "mean"]
    }).reset_index()
    peak_stats.columns = ["Is Peak Hour", "Total Delay", "Incident Count", "Avg Delay"]
    peak_stats["Period"] = peak_stats["Is Peak Hour"].apply(
        lambda x: "尖峰時段 (07-09, 16-19)" if x else "離峰時段"
    )
    
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{"type": "pie"}, {"type": "bar"}, {"type": "bar"}]],
        subplot_titles=("事故分佈", "總延遲", "平均延遲/次")
    )
    
    colors = ["#FF6B6B", "#4ECDC4"]
    
    fig.add_trace(
        go.Pie(
            labels=peak_stats["Period"],
            values=peak_stats["Incident Count"],
            marker_colors=colors,
            textinfo="percent+label"
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=peak_stats["Period"],
            y=peak_stats["Total Delay"],
            marker_color=colors,
            text=peak_stats["Total Delay"].apply(lambda x: f"{x:,.0f}"),
            textposition="outside"
        ),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(
            x=peak_stats["Period"],
            y=peak_stats["Avg Delay"],
            marker_color=colors,
            text=peak_stats["Avg Delay"].apply(lambda x: f"{x:.1f}"),
            textposition="outside"
        ),
        row=1, col=3
    )
    
    fig.update_layout(
        title_text="⏰ 尖峰 vs 離峰時段分析",
        height=400,
        showlegend=False
    )
    
    fig.write_html(os.path.join(output_dir, "05_peak_comparison.html"))
    print("[OK] Chart 5: Peak Comparison generated")


def chart_delay_causes(df):
    """圖表 6: 延遲原因分析 (Sunburst)"""
    
    cause_stats = df.groupby("Code Description").agg({
        "Min Delay": ["sum", "count"]
    }).reset_index()
    cause_stats.columns = ["Cause", "Total Delay", "Count"]
    cause_stats = cause_stats.nlargest(15, "Total Delay")
    
    fig = px.sunburst(
        cause_stats,
        path=["Cause"],
        values="Total Delay",
        color="Total Delay",
        color_continuous_scale="Reds",
        title="🔍 Top 15 延遲原因 (按總延遲時間)"
    )
    
    fig.update_layout(height=600)
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>總延遲: %{value:,.0f} 分鐘<extra></extra>"
    )
    
    fig.write_html(os.path.join(output_dir, "06_delay_causes.html"))
    print("[OK] Chart 6: Delay Causes generated")


def create_dashboard(df):
    """圖表 7: 綜合儀表板"""
    
    # 統計數據
    total_incidents = len(df)
    total_delay = df["Min Delay"].sum()
    avg_delay = df["Min Delay"].mean()
    peak_incidents = df["Is Peak Hour"].sum()
    
    fig = make_subplots(
        rows=2, cols=2,
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}],
            [{"type": "indicator"}, {"type": "indicator"}]
        ],
        subplot_titles=("總事故次數", "總延遲時間", "平均延遲", "尖峰時段事故")
    )
    
    # 指標卡
    fig.add_trace(go.Indicator(
        mode="number",
        value=total_incidents,
        number={"font": {"size": 60, "color": "#2C3E50"}},
        title={"text": "次", "font": {"size": 20}}
    ), row=1, col=1)
    
    fig.add_trace(go.Indicator(
        mode="number",
        value=total_delay,
        number={"font": {"size": 60, "color": "#E74C3C"}, "suffix": " 分鐘"},
        title={"text": "", "font": {"size": 20}}
    ), row=1, col=2)
    
    fig.add_trace(go.Indicator(
        mode="number",
        value=avg_delay,
        number={"font": {"size": 60, "color": "#3498DB"}, "suffix": " 分鐘/次"},
        title={"text": "", "font": {"size": 20}}
    ), row=2, col=1)
    
    fig.add_trace(go.Indicator(
        mode="number",
        value=peak_incidents,
        number={"font": {"size": 60, "color": "#F39C12"}},
        title={"text": f"({peak_incidents/total_incidents*100:.1f}%)", "font": {"size": 20}}
    ), row=2, col=2)
    
    fig.update_layout(
        title_text="📊 TTC 地鐵延遲數據總覽",
        title_font_size=28,
        height=500
    )
    
    fig.write_html(os.path.join(output_dir, "00_dashboard.html"))
    print("[OK] Chart 0: Dashboard generated")


def main():
    print("=" * 50)
    print("  TTC 互動式圖表生成器")
    print("=" * 50)
    
    print("\n載入數據...")
    df = load_data()
    print(f"已載入 {len(df)} 筆資料\n")
    
    print("生成圖表中...\n")
    
    create_dashboard(df)
    chart_line_comparison(df)
    chart_monthly_trend(df)
    chart_hourly_heatmap(df)
    chart_station_reliability(df)
    chart_peak_comparison(df)
    chart_delay_causes(df)
    
    print("\n" + "=" * 50)
    print(f"All charts saved to: {output_dir}")
    print("=" * 50)
    print("\nOpen HTML files in browser to view interactive charts!")


if __name__ == "__main__":
    main()

