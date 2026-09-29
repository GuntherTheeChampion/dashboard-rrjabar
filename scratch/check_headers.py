import pandas as pd
from data_loader import fetch_workbook

def check(name, url):
    print(f"\n--- Fetching {name} ---")
    sheets = fetch_workbook(url)
    sheet_list = list(sheets.values())
    
    for idx in range(1, len(sheet_list)):
        raw = sheet_list[idx]
        print(f"  Branch {idx} shape: {raw.shape}")
        
        for r_idx in range(min(15, len(raw))):
            row_vals = [str(x).strip().lower() for x in raw.iloc[r_idx]]
            if "msisdn" in row_vals or "no. handphone" in row_vals:
                print(f"    Header row found at {r_idx}")
                # print columns from 25 to 35
                for c_idx in range(max(0, 25), min(len(row_vals), 36)):
                    print(f"      Col {c_idx}: {row_vals[c_idx]}")
                break

urls = {
    "30": "https://docs.google.com/spreadsheets/d/1gLF5O7sVJUD2S7UZKGPj7yiu2zTiqmHb/edit",
    "60": "https://docs.google.com/spreadsheets/d/1uyybjOx8rKrgI6uoWePxEnvA3hwROhkI/edit",
    "90": "https://docs.google.com/spreadsheets/d/1kOeGP9XLx1G3k4QWb7zkqcO3N3KgLSx1/edit"
}

check("30", urls["30"])
check("60", urls["60"])
check("90", urls["90"])
