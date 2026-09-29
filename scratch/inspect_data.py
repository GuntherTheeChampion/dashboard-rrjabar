import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
from data_loader import fetch_workbook, BUCKET_URLS

sheets = fetch_workbook(BUCKET_URLS["30"])
print("Sheets:", list(sheets.keys()))
sheet_list = list(sheets.values())
for i in range(1, 5):
    if i < len(sheet_list):
        df = sheet_list[i]
        print(f"Sheet {i} columns (first 3 rows):")
        for row in range(3):
            print(f"Row {row}:", df.iloc[row].to_dict())
        break
