import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
from data_loader import fetch_workbook, BUCKET_URLS

sheets = fetch_workbook(BUCKET_URLS["30"])
df = list(sheets.values())[0]
print("Summary Sheet 30H")
print("Rows 10 to 30:")
for i in range(10, min(30, len(df))):
    print(f"Row {i}:", df.iloc[i, :10].to_dict())

sheets90 = fetch_workbook(BUCKET_URLS["90"])
df90 = list(sheets90.values())[0]
print("Summary Sheet 90H")
print("Rows 13 to 30:")
for i in range(13, min(30, len(df90))):
    print(f"Row {i}:", df90.iloc[i, :10].to_dict())
