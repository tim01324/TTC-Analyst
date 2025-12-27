import pandas as pd
import os
import sys

# File Path
data_dir = r"c:\Users\tim01\Desktop\TTC"
cleaned_file = os.path.join(data_dir, "TTC_Subway_Delay_Data_Combined_Cleaned.csv")

def get_answers():
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        df = pd.read_csv(cleaned_file, encoding='utf-8')
    except:
        df = pd.read_csv(cleaned_file, encoding='cp1252')
        
    df['Date'] = pd.to_datetime(df['Date'])
    df['Min Delay'] = pd.to_numeric(df['Min Delay'], errors='coerce').fillna(0)

    # Write to file
    with open(r'c:\Users\tim01\Desktop\TTC\answers.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        
        print("--- ANSWERS START ---")
        
        # 1. Monthly
        df['Month'] = df['Date'].dt.to_period('M')
        top_month = df.groupby('Month')['Min Delay'].sum().idxmax()
        print(f"Top Month: {top_month}")

        # 2. Daily
        df['DayOfWeek'] = df['Date'].dt.day_name()
        top_day = df.groupby('DayOfWeek')['Min Delay'].sum().idxmax()
        print(f"Top Day: {top_day}")

        # 3. Peak/OffPeak
        def is_peak(row):
            day = row['DayOfWeek']
            if day in ['Saturday', 'Sunday']: return 'Off-Peak'
            try:
                h = int(str(row['Time']).split(':')[0])
                if (6 <= h < 9) or (15 <= h < 19): return 'Peak'
            except: pass
            return 'Off-Peak'

        df['Period'] = df.apply(is_peak, axis=1)
        period_stats = df.groupby('Period')['Min Delay'].sum()
        print(f"Peak Delay: {period_stats.get('Peak', 0)}")
        print(f"Off-Peak Delay: {period_stats.get('Off-Peak', 0)}")

        # 4. Line
        top_line = df.groupby('Line')['Min Delay'].sum().idxmax()
        print(f"Top Line: {top_line}")

        # 5. Top 10 Causes
        top_causes = df.groupby('Code Description')['Min Delay'].sum().sort_values(ascending=False).head(10)
        print("Top 10 Causes by Duration:")
        for c, val in top_causes.items():
            safe_c = str(c).replace('\n', ' ').strip()
            print(f"CAUSE: {safe_c} || MINS: {val}")

        print("--- ANSWERS END ---")
        sys.stdout = sys.__stdout__
        print("Answers saved to answers.txt")

if __name__ == "__main__":
    get_answers()
