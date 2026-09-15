import io
import time

import pandas as pd
import requests
import streamlit as st

TREND_URL = "https://docs.google.com/spreadsheets/d/1Q0_olojU_ee_GN70KYAjL3u5ECTtK-gK/edit"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu"]

# Each entry: (branch_name, bucket, row_index, col_start, col_end)
# col_end is exclusive (pandas iloc slicing), all 0-indexed
_LAYOUT = [
    ("Bandung",      "60-H",  6, 2, 10),
    ("Bandung",      "90-H",  8, 2, 10),
    ("Cirebon",      "60-H",  6, 12, 20),
    ("Cirebon",      "90-H",  8, 12, 20),
    ("Soreang",      "60-H", 22, 2, 10),
    ("Soreang",      "90-H", 24, 2, 10),
    ("Tasikmalaya",  "60-H", 22, 12, 20),
    ("Tasikmalaya",  "90-H", 24, 12, 20),
    ("Jawa Barat",   "60-H", 38, 2, 10),
    ("Jawa Barat",   "90-H", 40, 2, 10),
]

# KPI target row/col indices (0-indexed)
_KPI_ROW = {"60-H": 0, "90-H": 1}
_KPI_COL = 1

_ANTI_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


def _build_export_url(url: str) -> str:
    base = url.split("/edit")[0].split("/export")[0].rstrip("/")
    return f"{base}/export?format=xlsx&nocache={int(time.time() * 1000)}"


@st.cache_data(ttl=900)
def load_trend_data() -> pd.DataFrame:
    """Fetch the CTP trend Excel from Google Sheets and return a tidy long-format DataFrame.

    Columns:
        Branch  : str   — e.g. "Bandung"
        Bucket  : str   — "60-H" or "90-H"
        Month   : str   — Indonesian month abbreviation, e.g. "Jan"
        Rate    : float — actual collection rate, e.g. 0.9847
        KPI     : float — KPI target for that bucket, e.g. 0.9820
    """
    export_url = _build_export_url(TREND_URL)
    try:
        response = requests.get(export_url, headers=_ANTI_CACHE_HEADERS, timeout=30)
        response.raise_for_status()
        raw = pd.read_excel(
            io.BytesIO(response.content),
            sheet_name="Sheet1",
            header=None,
            engine="openpyxl",
        )
    except Exception as exc:
        st.error(f"Gagal memuat data tren.\n\nError: {exc}")
        return pd.DataFrame(columns=["Branch", "Bucket", "Month", "Rate", "KPI"])

    # Read KPI targets dynamically
    kpi = {
        "60-H": float(raw.iloc[_KPI_ROW["60-H"], _KPI_COL]),
        "90-H": float(raw.iloc[_KPI_ROW["90-H"], _KPI_COL]),
    }

    rows = []
    for branch, bucket, row_idx, col_start, col_end in _LAYOUT:
        values = raw.iloc[row_idx, col_start:col_end].tolist()
        for month, rate in zip(MONTHS, values):
            rows.append({
                "Branch": branch,
                "Bucket": bucket,
                "Month":  month,
                "Rate":   float(rate) if rate is not None else None,
                "KPI":    kpi[bucket],
            })

    df = pd.DataFrame(rows)
    df["Month"] = pd.Categorical(df["Month"], categories=MONTHS, ordered=True)
    return df
