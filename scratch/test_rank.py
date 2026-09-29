from data_loader import fetch_workbook
from data_processor import extract_rankings
sheets = fetch_workbook("https://docs.google.com/spreadsheets/d/16qXh1as-6QgI3JrE8xvPA41-LESAVyVT/edit")
res = extract_rankings(sheets, "30")
for item in res['bottom']:
    print(item)
print("TOP")
for item in res['top']:
    print(item)
