import sys
import os

# Ensure the parent directory is in the path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_loader import fetch_workbook, BUCKET_URLS
import pandas as pd

def main():
    bucket_key = "60" # We can check 60-H as an example
    url = BUCKET_URLS[bucket_key]
    print(f"Fetching workbook for bucket {bucket_key}...")
    sheets = fetch_workbook(url)
    
    if not sheets:
        print("Failed to fetch sheets.")
        return

    sheet_list = list(sheets.values())
    summary_df = sheet_list[0]
    
    print("\n--- Grand Total Extraction ---")
    total_row_idx = 3 if bucket_key in ["30", "60"] else 6
    print(f"Looking at Row Index {total_row_idx} (Excel Row {total_row_idx + 1}):")
    try:
        print(summary_df.iloc[total_row_idx].to_dict())
    except Exception as e:
        print(f"Error accessing row {total_row_idx}: {e}")

    print("\n--- GraPARI Branch Data Extraction ---")
    start_row = 11 if bucket_key in ["30", "60"] else 14
    print(f"Iterating starting from Row Index {start_row} (Excel Row {start_row + 1}):")
    
    for i in range(start_row, min(start_row + 20, len(summary_df))):
        grapari_name = str(summary_df.iloc[i, 1]).strip()
        print(f"Row {i} (Excel Row {i+1}): Col B (Index 1) = '{grapari_name}'")
        
        # Also print the specific columns it tries to read
        try:
            tagihan_m = summary_df.iloc[i, 2]
            bayar_m = summary_df.iloc[i, 6]
            print(f"   -> Tagihan MSISDN (Col C, Idx 2): {tagihan_m}")
            print(f"   -> Bayar MSISDN (Col G, Idx 6): {bayar_m}")
        except Exception as e:
            print(f"   -> Error reading data columns: {e}")

if __name__ == "__main__":
    main()
