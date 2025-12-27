import pandas as pd
import os
import sys

# File Path
data_dir = r"c:\Users\tim01\Desktop\TTC"
cleaned_file = os.path.join(data_dir, "TTC_Subway_Delay_Data_Combined_Cleaned.csv")

def analyze():
    # Write directly to file to avoid encoding issues with shell redirection
    output_path = os.path.join(data_dir, "analysis_results.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        # Redirect stdout to this file
        sys.stdout = f

        print("Loading data...")
        if not os.path.exists(cleaned_file):
            print("Cleaned file not found!")
            return

        try:
            df = pd.read_csv(cleaned_file, encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback if file was somehow saved with default encoding
            df = pd.read_csv(cleaned_file, encoding='cp1252')
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Ensure Min Delay is numeric
        df['Min Delay'] = pd.to_numeric(df['Min Delay'], errors='coerce').fillna(0)

        print(f"\nData Loaded. Total Rows: {len(df)}")
        print(f"Total Delay Minutes: {df['Min Delay'].sum()}")

        # ==========================================
        # 1. Time Dimension
        # ==========================================
        print("\n" + "="*40)
        print("1. TIME DIMENSION ANALYSIS")
        print("="*40)

        # A. Monthly
        df['Month'] = df['Date'].dt.to_period('M')
        monthly = df.groupby('Month')['Min Delay'].agg(['sum', 'count']).sort_values('sum', ascending=False)
        print("\n[Worst Months by Total Delay Minutes]")
        print(monthly.head(5))

        # B. Daily (Day of Week)
        # Ensure Day column is consistent or re-derive
        df['DayOfWeek'] = df['Date'].dt.day_name()
        daily = df.groupby('DayOfWeek')['Min Delay'].agg(['sum', 'count']).sort_values('sum', ascending=False)
        print("\n[Worst Days of Week by Total Delay Minutes]")
        print(daily)

        # C. Peak vs Off-Peak
        # Peak: Mon-Fri, 06:00-09:00 & 15:00-19:00
        # Parse Time
        def is_peak(row):
            day = row['DayOfWeek']
            if day in ['Saturday', 'Sunday']:
                return 'Off-Peak'
            
            try:
                # Time format HH:MM
                h = int(str(row['Time']).split(':')[0])
                if (6 <= h < 9) or (15 <= h < 19):
                    return 'Peak'
            except:
                pass # Invalid time parsing
                
            return 'Off-Peak'

        df['Period'] = df.apply(is_peak, axis=1)
        peak_stats = df.groupby('Period')['Min Delay'].agg(['sum', 'count', 'mean'])
        print("\n[Peak vs Off-Peak Stats]")
        print(peak_stats)


        # ==========================================
        # 2. Spatial Dimension
        # ==========================================
        print("\n" + "="*40)
        print("2. SPATIAL DIMENSION ANALYSIS")
        print("="*40)

        # Group by Line
        line_stats = df.groupby('Line')['Min Delay'].agg(['sum', 'count']).sort_values('sum', ascending=False)
        print("\n[Delays by Subway Line]")
        print(line_stats)


        # ==========================================
        # 3. Cause Analysis
        # ==========================================
        print("\n" + "="*40)
        print("3. CAUSE ANALYSIS")
        print("="*40)

        # Top 10 by Frequency
        print("\n[Top 10 Causes by FREQUENCY (Count)]")
        top_freq = df['Code Description'].value_counts().head(10)
        print(top_freq)

        # Top 10 by Duration
        print("\n[Top 10 Causes by DURATION (Total Minutes)]")
        top_dur = df.groupby('Code Description')['Min Delay'].sum().sort_values(ascending=False).head(10)
        print(top_dur)
    
    # Reset stdout
    sys.stdout = sys.__stdout__
    print(f"Analysis saved to {output_path}")

if __name__ == "__main__":
    analyze()
