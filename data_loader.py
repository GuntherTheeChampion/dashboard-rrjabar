# data_loader.py — GraPARI West Java Collection Monitoring Dashboard
# Handles HTTP fetching from Google Sheets with anti-cache headers.
#
# NOTE: Google's /export?format=xlsx CDN takes 5-15 minutes to reflect
# sheet edits. No client-side header can bypass this — it is Google's
# own server-side cache. The app adds zero extra delay on top of that.
#
# To add a new bucket: add its URL to BUCKET_URLS below.

import io
import time

import pandas as pd
import requests
import streamlit as st

# Live Google Sheets source URLs (can be /edit or /export form)
BUCKET_URLS: dict[str, str] = {
    "30": "https://docs.google.com/spreadsheets/d/15PQ_1X2ExOr6TVTDTTkkjyAfM1qywLp_/edit",
    "60": "https://docs.google.com/spreadsheets/d/1Ksm2NdALwhYFmI0bXbHnCCUA2QLQeLj3/edit",
    "90": "https://docs.google.com/spreadsheets/d/1xVEObliWzzX-D2n2ZZmWQIDSXPL1JW45/edit",
}

# Sheet index → canonical branch label (index 0 = summary, skipped)
BRANCH_BY_INDEX: dict[int, str] = {
    1: "Bandung",
    2: "Cirebon",
    3: "Soreang",
    4: "Tasik",
}

# Anti-cache headers sent with every request
_ANTI_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


def _build_export_url(url: str) -> str:
    base = url.split("/edit")[0].split("/export")[0].rstrip("/")
    return f"{base}/export?format=xlsx&nocache={int(time.time() * 1000)}"


def fetch_workbook(url: str) -> dict[str, pd.DataFrame]:
    # No @st.cache_data — every call makes a real HTTP request to Google Sheets
    export_url = _build_export_url(url)
    try:
        response = requests.get(export_url, headers=_ANTI_CACHE_HEADERS, timeout=30)
        response.raise_for_status()
        return pd.read_excel(
            io.BytesIO(response.content),
            sheet_name=None,
            engine="openpyxl",
            header=None,
        )
    except Exception as exc:
        st.error(f"Failed to load workbook.\n\nURL: {export_url}\n\nError: {exc}")
        return {}


def clear_all_cache() -> None:
    # No-op — kept so the Refresh button in app.py doesn't break
    # st.rerun() alone is sufficient since there is no Streamlit cache
    pass
