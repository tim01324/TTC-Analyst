import pandas as pd
import os
import numpy as np
import glob

# Define file paths
data_dir = r"c:\Users\tim01\Desktop\TTC"
codes_excel = os.path.join(data_dir, "ttc-subway-delay-codes.xlsx")
codes_csv = os.path.join(data_dir, "Code Descriptions.csv")
output_file = os.path.join(data_dir, "TTC_Subway_Delay_Data_Combined_Cleaned.csv")


def load_codes():
    print("Loading codes maps...")
    code_map = {}

    # 1. Load Secondary (CSV) first - will be overwritten by Primary if duplicates exist
    # Or load Primary first, then fill missing from Secondary.
    # User said: "Check first code file, if not found, check second".
    # So Primary takes precedence.

    # Load Secondary (CSV)
    try:
        df_csv = pd.read_csv(codes_csv)
        # CSV format: _id, CODE, DESCRIPTION
        # Clean col names if needed
        df_csv.columns = df_csv.columns.str.strip().str.upper()
        if "CODE" in df_csv.columns and "DESCRIPTION" in df_csv.columns:
            df_csv["CODE"] = df_csv["CODE"].astype(str).str.strip()
            # Add to map
            secondary_map = dict(zip(df_csv["CODE"], df_csv["DESCRIPTION"]))
            print(f"Loaded {len(secondary_map)} codes from CSV (Secondary).")
            code_map.update(secondary_map)
        else:
            print("Warning: unexpected columns in CSV codes file.")
    except Exception as e:
        print(f"Error loading CSV codes: {e}")

    # Load Primary (Excel) - Overwrite CSV entries if conflict
    try:
        # Based on previous inspection structure
        df_ex = pd.read_excel(codes_excel, header=None)

        # Subway: Col 2 & 3 (indices 2,3), skip header rows
        sub = df_ex.iloc[2:, [2, 3]].dropna()
        sub.columns = ["Code", "Description"]

        # SRT: Col 6 & 7 (indices 6,7)
        srt = df_ex.iloc[2:, [6, 7]].dropna()
        srt.columns = ["Code", "Description"]

        combined = pd.concat([sub, srt])
        combined["Code"] = combined["Code"].astype(str).str.strip()

        primary_map = dict(zip(combined["Code"], combined["Description"]))
        print(f"Loaded {len(primary_map)} codes from Excel (Primary).")

        # Update map (Excel overrides CSV)
        code_map.update(primary_map)

    except Exception as e:
        print(f"Error loading Excel codes: {e}")

    # Manual Corrections (if any remain)
    manual_updates = {
        "XXXXX": "General/Unknown Error",
        # MUNCA, TUNCA etc are in CSV, so they should be covered now
    }
    code_map.update(manual_updates)

    print(f"Total unique codes loaded: {len(code_map)}")
    return code_map


def get_code_desc(code, mapping):
    if pd.isna(code) or code == "nan" or code == "":
        return "Unknown Code"
    code = str(code).strip()

    if code in mapping:
        return mapping[code]

    # Heuristic Fallback
    prefix = code[:2]
    prefix_map = {
        "MU": "Miscellaneous / Transportation",
        "TU": "Track / Signal",
        "PU": "Plant / Equipment",
        "EU": "Equipment",
        "SU": "Subway Service",
        "ER": "SRT Equipment",
    }
    if prefix in prefix_map:
        return f"{prefix_map[prefix]} - Unknown Subcode"

    return "Unknown Code"


def find_data_files():
    # Find files matching "ttc subway delay data" (case insensitive)
    # This matches user requirement: "判斷 檔案 名稱為 ttc subway delay data"
    all_files = glob.glob(os.path.join(data_dir, "*"))
    data_files = []

    print("Scanning for data files...")
    for f in all_files:
        fname = os.path.basename(f).lower()
        # Simple heuristic or specific keywords
        if (
            "ttc" in fname
            and "subway" in fname
            and "delay" in fname
            and "data" in fname
        ):
            if f.endswith(".csv") or f.endswith(".xlsx"):
                # Exclude the output file itself if it exists
                if "cleaned" in fname:
                    continue
                print(f"Found data file: {os.path.basename(f)}")
                data_files.append(f)
    return data_files


def is_peak_hour(time_str):
    """判斷是否為尖峰時段 (07:00-09:00 或 16:00-19:00)"""
    try:
        h = int(str(time_str).split(":")[0])
        if (7 <= h < 9) or (16 <= h < 19):
            return True
    except:
        pass
    return False


def clean_and_merge():
    # 1. Identify Files
    files = find_data_files()
    if not files:
        print("No data files found!")
        return

    # 2. Load Data
    dfs = []
    for f in files:
        try:
            if f.endswith(".xlsx"):
                d = pd.read_excel(f)
            else:
                d = pd.read_csv(f)

            # Standardize columns? 2025 has _id
            if "_id" in d.columns:
                d.drop(columns=["_id"], inplace=True)

            dfs.append(d)
        except Exception as e:
            print(f"Error reading {f}: {e}")

    # 3. Merge
    if not dfs:
        return

    df_combined = pd.concat(dfs, ignore_index=True)
    total_original_rows = len(df_combined)
    print(f"\n--- Total Rows Loaded: {total_original_rows} ---")

    # 4. Standardize / Trim Strings
    print("Trimming string columns...")
    cat_cols = ["Station", "Code", "Bound", "Line", "Vehicle"]
    # Check if columns exist before processing
    for col in cat_cols:
        if col in df_combined.columns:
            # Convert to string, trim whitespace, upper case for consistency
            df_combined[col] = df_combined[col].astype(str).str.strip().str.upper()
            # Replace 'NAN', 'NONE' strings with real NaN
            df_combined[col] = df_combined[col].replace(["NAN", "NONE", ""], np.nan)
        
        # Specific Normalization for Station Name
        if "Station" in df_combined.columns:
            # Remove " STATION" suffix if exists
            df_combined["Station"] = df_combined["Station"].str.replace(r"\s+STATION$", "", regex=True)
            # Standardize common variations
            station_map = {
                "ST GEORGE": "ST. GEORGE",
                "ST CLAIR": "ST. CLAIR",
                "ST ANDREW": "ST. ANDREW",
                "ST PATRICK": "ST. PATRICK",
                "BLOOR-YONGE": "BLOOR", # Often referred as Bloor Station
                "KENNEDY BD": "KENNEDY",
                "VMC": "VAUGHAN METROPOLITAN CENTRE",
            }
            # Optional: More aggressive cleaning
            # df_combined["Station"] = df_combined["Station"].replace(station_map)

    # Date Standardize
    if "Date" in df_combined.columns:
        df_combined["Date"] = pd.to_datetime(df_combined["Date"]).dt.date

    # 5. 路線名稱標準化 (Line Rename)
    # Line 1: Yonge-University - 地鐵 (Subway) - 營運中
    # Line 2: Bloor-Danforth - 地鐵 (Subway) - 營運中
    # Line 3: Scarborough RT - 輕軌 (LRT) - 已永久關閉 (2023 年退役)
    # Line 4: Sheppard - 地鐵 (Subway) - 營運中
    # Line 5: Eglinton Crosstown - 輕軌 (LRT) - 尚未開通
    # Line 6: Finch West - 輕軌 (LRT) - 營運中 (2025 年 12 月 7 日開通)
    print("\n--- Renaming Lines ---")
    line_mapping = {
        "YU": "Line 1 Yonge-University",
        "YUS": "Line 1 Yonge-University",
        "BD": "Line 2 Bloor-Danforth",
        "SHP": "Line 4 Sheppard",
        "SRT": "Line 3 Scarborough RT",  # 已關閉，會被過濾掉
    }

    if "Line" in df_combined.columns:
        # 記錄原始的 Line 分佈
        print("Original Line Distribution:")
        print(df_combined["Line"].value_counts())

        # 應用映射
        df_combined["Line"] = df_combined["Line"].replace(line_mapping)

        print("\nAfter Renaming:")
        print(df_combined["Line"].value_counts())

    # 6. 只保留地鐵資料 (Filter Subway Only - Lines 1, 2, 4)
    subway_lines = [
        "Line 1 Yonge-University",
        "Line 2 Bloor-Danforth",
        "Line 4 Sheppard",
    ]

    print("\n--- Filtering Subway Lines Only ---")
    rows_before_filter = len(df_combined)
    df_combined = df_combined[df_combined["Line"].isin(subway_lines)].copy()
    rows_after_filter = len(df_combined)

    print(f"Rows before subway filter: {rows_before_filter}")
    print(f"Rows after subway filter: {rows_after_filter}")
    print(f"Rows removed (non-subway): {rows_before_filter - rows_after_filter}")

    print("\nFinal Line Distribution (Subway Only):")
    print(df_combined["Line"].value_counts())

    # 7. 新增尖峰時段欄位 (Add Peak Hour Column)
    print("\n--- Adding Peak Hour Column ---")
    if "Time" in df_combined.columns:
        df_combined["Is Peak Hour"] = df_combined["Time"].apply(is_peak_hour)
        peak_count = df_combined["Is Peak Hour"].sum()
        offpeak_count = len(df_combined) - peak_count
        print(f"Peak Hour incidents: {peak_count}")
        print(f"Off-Peak incidents: {offpeak_count}")

    # 8. Map Codes
    code_map = load_codes()
    if "Code" in df_combined.columns:
        df_combined["Code Description"] = df_combined["Code"].apply(
            lambda c: get_code_desc(c, code_map)
        )

    # 9. Filter Verification Logic
    # User Request: "delay = 0 刪除後的檔案數量" & "判斷加起來的line 數量應該是一樣的"

    print("\n--- Filtering Data (Remove Min Delay = 0) ---")
    # Cast Min Delay to number just in case
    df_combined["Min Delay"] = pd.to_numeric(
        df_combined["Min Delay"], errors="coerce"
    ).fillna(0)

    subway_rows_before_delay_filter = len(df_combined)

    # Split Data
    df_kept = df_combined[df_combined["Min Delay"] != 0].copy()
    df_dropped = df_combined[df_combined["Min Delay"] == 0].copy()

    count_kept = len(df_kept)
    count_dropped = len(df_dropped)

    print(f"Subway Rows (before delay filter): {subway_rows_before_delay_filter}")
    print(f"Filtered (Kept) Count: {count_kept}")
    print(f"Dropped (Delay=0) Count: {count_dropped}")

    # Verification
    if count_kept + count_dropped == subway_rows_before_delay_filter:
        print("VERIFICATION PASSED: Kept + Dropped = Subway Total")
    else:
        print(
            f"VERIFICATION FAILED: {count_kept} + {count_dropped} != {subway_rows_before_delay_filter}"
        )

    # 10. Save
    print(f"\nSaving to {output_file}...")
    df_kept.to_csv(output_file, index=False)

    # Validation Summary File
    with open("validation_summary.txt", "w", encoding="utf-8") as f:
        f.write("--- Clean Data Verification ---\n")
        f.write(f"Original Rows (all files): {total_original_rows}\n")
        f.write(f"After Subway Line Filter: {subway_rows_before_delay_filter}\n")
        f.write(f"Non-Subway Rows Removed: {rows_before_filter - rows_after_filter}\n")
        f.write(f"Rows with Min Delay=0 (Dropped): {count_dropped}\n")
        f.write(f"Final Saved Rows: {count_kept}\n")
        f.write(
            f"Verification: {'PASSED' if (count_kept + count_dropped == subway_rows_before_delay_filter) else 'FAILED'}\n\n"
        )

        f.write("--- Line Distribution ---\n")
        f.write(df_kept["Line"].value_counts().to_string() + "\n\n")

        f.write("--- Peak Hour Distribution ---\n")
        if "Is Peak Hour" in df_kept.columns:
            f.write(f"Peak Hour incidents: {df_kept['Is Peak Hour'].sum()}\n")
            f.write(f"Off-Peak incidents: {(~df_kept['Is Peak Hour']).sum()}\n\n")

        # Check for unknown codes in the FINAL set
        unknowns = df_kept[df_kept["Code Description"].str.contains("Unknown Code")]
        f.write(f"Rows with Unknown Codes (in final data): {len(unknowns)}\n")
        if len(unknowns) > 0:
            f.write(f"Unique Unknowns: {unknowns['Code'].unique()}\n")

        f.write("\nSample Data:\n")
        f.write(df_kept.head().to_string())

    print("Done. Check validation_summary.txt.")


if __name__ == "__main__":
    clean_and_merge()
