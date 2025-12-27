import pandas as pd
import os
import sys

# File Path
data_dir = r"c:\Users\tim01\Desktop\TTC"
cleaned_file = os.path.join(data_dir, "TTC_Subway_Delay_Data_Combined_Cleaned.csv")
output_file = os.path.join(data_dir, "advanced_metrics_results.txt")

def calculate_metrics():
    """
    計算進階指標報告
    
    使用 相對損害評分 (Relative Impact Score) 來計算可靠性分數
    
    計算邏輯：
    - 頻率扣分 (Frequency Penalty)：計算每個車站/線路在一段時間內的事故總次數
    - 時長扣分 (Duration Penalty)：加總所有 Min Delay
    - 時段乘數 (Time Multiplier)：尖峰時段 (07:00-09:00 或 16:00-19:00) 權重 x 1.5
    - 標準化 (Normalization)：將所有車站的總扣分映射到 0-100
    
    公式：
    Station Penalty = Σ(Min Delay × Peak Hour Weight)
    Reliability Score = 100 - (Station Penalty / Max Penalty in System × 100)
    """
    
    # Load Data
    try:
        df = pd.read_csv(cleaned_file, encoding='utf-8')
    except:
        df = pd.read_csv(cleaned_file, encoding='cp1252')
        
    df['Min Delay'] = pd.to_numeric(df['Min Delay'], errors='coerce').fillna(0)
    
    # 確保有 Is Peak Hour 欄位
    if 'Is Peak Hour' not in df.columns:
        def is_peak_hour(time_str):
            try:
                h = int(str(time_str).split(':')[0])
                if (7 <= h < 9) or (16 <= h < 19):
                    return True
            except:
                pass
            return False
        df['Is Peak Hour'] = df['Time'].apply(is_peak_hour)
    
    # 計算加權延遲 (Peak Hour Weight = 1.5, Off-Peak = 1.0)
    df['Peak Weight'] = df['Is Peak Hour'].apply(lambda x: 1.5 if x else 1.0)
    df['Weighted Delay'] = df['Min Delay'] * df['Peak Weight']
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Redirect stdout
        sys.stdout = f
        
        print("=" * 60)
        print("        ADVANCED METRICS REPORT (相對損害評分)")
        print("=" * 60)
        print("\n計算方法說明:")
        print("  - 尖峰時段 (07:00-09:00, 16:00-19:00) 權重: 1.5x")
        print("  - 非尖峰時段權重: 1.0x")
        print("  - 可靠性分數 = 100 - (加權扣分 / 系統最大扣分 × 100)")
        print("-" * 60)
        
        # 1. Average Delay per Incident
        total_delay = df['Min Delay'].sum()
        total_weighted_delay = df['Weighted Delay'].sum()
        total_incidents = len(df)
        avg_delay_global = total_delay / total_incidents if total_incidents > 0 else 0
        avg_weighted_delay = total_weighted_delay / total_incidents if total_incidents > 0 else 0
        
        print(f"\n[全系統統計]")
        print(f"總事故次數: {total_incidents}")
        print(f"總延遲分鐘數: {total_delay:.0f}")
        print(f"加權總延遲: {total_weighted_delay:.0f}")
        print(f"平均每次事故延遲: {avg_delay_global:.2f} 分鐘")
        print(f"加權平均延遲: {avg_weighted_delay:.2f}")
        
        print("\n" + "=" * 60)
        
        # 2. Line Reliability (使用新公式)
        print("\n[路線可靠性分數 - Line Reliability Score]")
        print("-" * 40)
        
        line_stats = df.groupby('Line').agg({
            'Min Delay': ['sum', 'count'],
            'Weighted Delay': 'sum'
        }).reset_index()
        line_stats.columns = ['Line', 'Total Delay', 'Incident Count', 'Weighted Penalty']
        
        # 計算可靠性分數
        max_line_penalty = line_stats['Weighted Penalty'].max()
        line_stats['Reliability Score'] = 100 - ((line_stats['Weighted Penalty'] / max_line_penalty) * 100)
        line_stats['Avg Delay per Incident'] = line_stats['Total Delay'] / line_stats['Incident Count']
        
        # 按可靠性分數排序
        line_stats = line_stats.sort_values('Reliability Score', ascending=False)
        
        for _, row in line_stats.iterrows():
            print(f"\n{row['Line']}")
            print(f"  可靠性分數: {row['Reliability Score']:.1f}/100")
            print(f"  事故次數: {row['Incident Count']}")
            print(f"  總延遲: {row['Total Delay']:.0f} 分鐘")
            print(f"  加權扣分: {row['Weighted Penalty']:.0f}")
            print(f"  平均每次延遲: {row['Avg Delay per Incident']:.1f} 分鐘")
        
        print("\n" + "=" * 60)

        # 3. Station Reliability (使用新公式)
        print("\n[車站可靠性分數 - Station Reliability Score]")
        print("-" * 40)
        
        station_stats = df.groupby('Station').agg({
            'Min Delay': ['sum', 'count'],
            'Weighted Delay': 'sum'
        }).reset_index()
        station_stats.columns = ['Station', 'Total Delay', 'Incident Count', 'Weighted Penalty']
        
        # ========== 數據清洗：過濾無效車站記錄 ==========
        # 設定門檻：只分析事故次數 > 50 的車站
        MIN_INCIDENT_THRESHOLD = 50
        
        # 過濾關鍵字：剔除非正式車站記錄
        EXCLUDE_KEYWORDS = [
            'APPROACHING', ' TO ', 'BUILDING', 'TRACK LEVEL', 
            'CENTRE TRACK', 'TAIL TRACK', 'CROSSOVER',
            'YARD', 'LOOP', 'SIDING', 'POCKET'
        ]
        
        # 應用過濾條件
        def is_valid_station(station_name):
            """檢查是否為有效車站名稱"""
            station_upper = str(station_name).upper()
            for keyword in EXCLUDE_KEYWORDS:
                if keyword in station_upper:
                    return False
            return True
        
        station_stats['Is Valid Station'] = station_stats['Station'].apply(is_valid_station)
        
        # 過濾後的車站統計
        valid_stations = station_stats[
            (station_stats['Incident Count'] >= MIN_INCIDENT_THRESHOLD) & 
            (station_stats['Is Valid Station'])
        ].copy()
        
        print(f"\n數據清洗條件:")
        print(f"  - 事故次數門檻: >= {MIN_INCIDENT_THRESHOLD}")
        print(f"  - 排除關鍵字: {', '.join(EXCLUDE_KEYWORDS[:5])}...")
        print(f"  - 原始車站數: {len(station_stats)}")
        print(f"  - 過濾後車站數: {len(valid_stations)}")
        
        # 計算可靠性分數 (使用過濾後的數據)
        max_station_penalty = valid_stations['Weighted Penalty'].max()
        valid_stations['Reliability Score'] = 100 - ((valid_stations['Weighted Penalty'] / max_station_penalty) * 100)
        valid_stations['Avg Delay'] = valid_stations['Total Delay'] / valid_stations['Incident Count']
        
        # Worst 10 (Lowest Score)
        print("\n>> 最不可靠的 10 個車站 (Top 10 LEAST Reliable):")
        worst_stations = valid_stations.sort_values('Reliability Score', ascending=True).head(10)
        for i, (_, row) in enumerate(worst_stations.iterrows(), 1):
            print(f"  {i}. {row['Station']}")
            print(f"     分數: {row['Reliability Score']:.1f} | 事故: {row['Incident Count']} | 加權扣分: {row['Weighted Penalty']:.0f}")
        
        # Best 10 (Highest Score)
        print("\n>> 最可靠的 10 個車站 (Top 10 MOST Reliable):")
        best_stations = valid_stations.sort_values('Reliability Score', ascending=False).head(10)
        for i, (_, row) in enumerate(best_stations.iterrows(), 1):
            print(f"  {i}. {row['Station']}")
            print(f"     分數: {row['Reliability Score']:.1f} | 事故: {row['Incident Count']} | 加權扣分: {row['Weighted Penalty']:.0f}")
        
        print("\n" + "=" * 60)
        
        # 4. Peak Hour Analysis
        print("\n[尖峰時段 vs 非尖峰時段分析]")
        print("-" * 40)
        
        peak_stats = df.groupby('Is Peak Hour').agg({
            'Min Delay': ['sum', 'count', 'mean']
        }).reset_index()
        peak_stats.columns = ['Is Peak Hour', 'Total Delay', 'Incident Count', 'Avg Delay']
        
        for _, row in peak_stats.iterrows():
            print(f"  平均延遲: {row['Avg Delay']:.1f} 分鐘")

        # 5. Trend Analysis (2024 vs 2025)
        print("\n" + "=" * 60)
        print("\n[年度趨勢分析 (2024 vs 2025)]")
        print("-" * 40)
        
        df['Year'] = pd.to_datetime(df['Date']).dt.year
        valid_years = [2024, 2025]
        df_trends = df[df['Year'].isin(valid_years)].copy()
        
        yearly_stats = df_trends.groupby('Year').agg({
            'Min Delay': ['sum', 'count'],
            'Weighted Delay': 'sum'
        }).reset_index()
        yearly_stats.columns = ['Year', 'Total Delay', 'Incident Count', 'Weighted Penalty']
        
        if len(yearly_stats) >= 2:
            y24 = yearly_stats[yearly_stats['Year'] == 2024].iloc[0]
            y25 = yearly_stats[yearly_stats['Year'] == 2025].iloc[0]
            
            inc_change = ((y25['Incident Count'] - y24['Incident Count']) / y24['Incident Count']) * 100
            delay_change = ((y25['Total Delay'] - y24['Total Delay']) / y24['Total Delay']) * 100
            
            print(f"2024 事故總數: {y24['Incident Count']:.0f}")
            print(f"2025 事故總數: {y25['Incident Count']:.0f}")
            print(f"事故數量變化: {inc_change:+.1f}%")
            
            print(f"\n2024 總延遲分鐘: {y24['Total Delay']:.0f}")
            print(f"2025 總延遲分鐘: {y25['Total Delay']:.0f}")
            print(f"延遲時長變化: {delay_change:+.1f}%")
            
            # 衡量 2025 是否比 2024 更「痛苦」 (加權平均)
            y24_avg_w = y24['Weighted Penalty'] / y24['Incident Count']
            y25_avg_w = y25['Weighted Penalty'] / y25['Incident Count']
            impact_change = ((y25_avg_w - y24_avg_w) / y24_avg_w) * 100
            
            print(f"\n平均事故損害指數 (加權):")
            print(f"  2024: {y24_avg_w:.2f}")
            print(f"  2025: {y25_avg_w:.2f}")
            print(f"  變化: {impact_change:+.1f}% (正值表示單次事故影響變大)")
        else:
            print("數據不足，無法進行年度對比（需要 2024 與 2025 的完整數據）")

    # Reset stdout
    sys.stdout = sys.__stdout__
    print(f"Metrics saved to {output_file}")

if __name__ == "__main__":
    calculate_metrics()
