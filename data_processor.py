# data_processor.py — GraPARI West Java Collection Monitoring Dashboard
# Handles all sheet parsing, data cleaning, and KPI extraction.
#
# Sheet index order (same across all 3 bucket files):
#   Index 0 = Perform / Summary sheet
#   Index 1 = Bandung branch
#   Index 2 = Cirebon branch
#   Index 3 = Soreang branch
#   Index 4 = Tasikmalaya branch
#
# Summary sheet column layout (0-indexed):
#   col 1 = Branch label
#   col 2 = Tagihan Msisdn (Total Target)
#   col 3 = Tagihan Rp
#   col 4 = Tunggakan Msisdn
#   col 5 = Tunggakan Rp
#   col 6 = Bayar Msisdn (Terbayar)
#   col 7 = Bayar Rp
#   col 8 = % Collection rate (float 0-1)
#
# Summary branch row indices (0-indexed):
#   30H and 60H: Bandung=53, Cirebon=54, Soreang=55, Tasik=56, Total=57
#   90H:         Bandung=56, Cirebon=57, Soreang=58, Tasik=59, Total=60
#
# Branch sheet column layout (0-indexed):
#   Row 0  = header row
#   col 2  = MSISDN
#   col 12 = Status (BLOCKED 1, BLOCKED 2, UNBLOCKED, CANCELLED)
#   col 28 = Hasil Follow Up GraPARI

import pandas as pd
from data_loader import BRANCH_BY_INDEX

# Summary sheet row config (0-indexed)
SUMMARY_ROWS: dict[str, dict] = {
    "30": {"Bandung": 53, "Cirebon": 54, "Soreang": 55, "Tasik": 56, "Total": 57},
    "60": {"Bandung": 53, "Cirebon": 54, "Soreang": 55, "Tasik": 56, "Total": 57},
    "90": {"Bandung": 56, "Cirebon": 57, "Soreang": 58, "Tasik": 59, "Total": 60},
}

# Summary column indices (0-indexed)
_CI_TAGIHAN_MSISDN   = 2
_CI_TAGIHAN_RP       = 3
_CI_TUNGGAKAN_MSISDN = 4
_CI_TUNGGAKAN_RP     = 5
_CI_BAYAR_MSISDN     = 6
_CI_BAYAR_RP         = 7
_CI_PCT_COLLECTION   = 8

# Branch sheet column indices (0-indexed)
_BI_MSISDN   = 2
_BI_STATUS   = 12
_BI_FOLLOWUP = 28

# Canonical internal column names
COL_BRANCH    = "Branch"
COL_MSISDN    = "MSISDN"
COL_STATUS    = "Status"
COL_FOLLOWUP  = "Hasil Follow Up"
COL_FU_STATUS = "Status Follow Up"


# Helpers
def _to_int(val) -> int | None:
    try:
        f = float(val)
        return int(f) if not pd.isna(f) else None
    except (TypeError, ValueError):
        return None


def _to_float(val) -> float | None:
    try:
        f = float(val)
        return f if not pd.isna(f) else None
    except (TypeError, ValueError):
        return None


def _clean_msisdn(val) -> str:
    # Convert MSISDN to clean string, remove trailing '.0' from float reads
    s = str(val).strip()
    if s.lower() in ("nan", "none", ""):
        return ""
    if s.endswith(".0"):
        s = s[:-2]
    return s


# KPI extraction from the summary (Perform) sheet
def extract_summary_kpis(sheets: dict[str, pd.DataFrame], bucket_key: str) -> dict:
    # Returns dict keyed by branch name + "Total", each value has tagihan/tunggakan/bayar/pct
    empty = {
        "tagihan_msisdn": None, "tagihan_rp": None,
        "tunggakan_msisdn": None, "tunggakan_rp": None,
        "bayar_msisdn": None, "bayar_rp": None,
        "pct_collection": None,
    }

    sheet_list = list(sheets.values())
    if not sheet_list:
        return {k: dict(empty) for k in ["Bandung", "Cirebon", "Soreang", "Tasik", "Total"]}

    summary_df = sheet_list[0]
    row_map = SUMMARY_ROWS.get(bucket_key, SUMMARY_ROWS["30"])

    result = {}
    for label, row_idx in row_map.items():
        if row_idx >= len(summary_df):
            result[label] = dict(empty)
            continue
        row = summary_df.iloc[row_idx]
        try:
            result[label] = {
                "tagihan_msisdn":   _to_int(row.iloc[_CI_TAGIHAN_MSISDN]),
                "tagihan_rp":       _to_int(row.iloc[_CI_TAGIHAN_RP]),
                "tunggakan_msisdn": _to_int(row.iloc[_CI_TUNGGAKAN_MSISDN]),
                "tunggakan_rp":     _to_int(row.iloc[_CI_TUNGGAKAN_RP]),
                "bayar_msisdn":     _to_int(row.iloc[_CI_BAYAR_MSISDN]),
                "bayar_rp":         _to_int(row.iloc[_CI_BAYAR_RP]),
                "pct_collection":   _to_float(row.iloc[_CI_PCT_COLLECTION]),
            }
        except Exception:
            result[label] = dict(empty)

    return result


# Customer records extraction from branch sheets (indices 1-4)
def extract_customer_records(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    # Uses sheet INDEX only — never sheet name (names differ between buckets)
    sheet_list = list(sheets.values())
    frames = []

    for idx in range(1, 5):
        if idx >= len(sheet_list):
            continue

        raw = sheet_list[idx].copy()
        branch_label = BRANCH_BY_INDEX.get(idx, f"Branch_{idx}")

        if len(raw) < 2:
            continue

        data_rows = raw.iloc[1:].copy()
        data_rows.columns = range(len(data_rows.columns))

        n = len(data_rows)

        def _col(col_idx: int) -> pd.Series:
            if col_idx < len(data_rows.columns):
                return data_rows.iloc[:, col_idx].reset_index(drop=True)
            return pd.Series([""] * n)

        msisdn_series = _col(_BI_MSISDN).apply(_clean_msisdn)
        status_series = _col(_BI_STATUS).apply(
            lambda x: str(x).strip() if pd.notna(x) and str(x).strip().lower() not in ("nan", "") else ""
        )
        fu_series = _col(_BI_FOLLOWUP).apply(
            lambda x: str(x).strip() if pd.notna(x) and str(x).strip().lower() not in ("nan", "") else ""
        )
        fu_status_series = fu_series.apply(
            lambda x: "Followed Up" if x.strip() != "" else "No Follow Up Yet"
        )

        df = pd.DataFrame({
            COL_BRANCH:    branch_label,
            COL_MSISDN:    msisdn_series,
            COL_STATUS:    status_series,
            COL_FOLLOWUP:  fu_series,
            COL_FU_STATUS: fu_status_series,
        })

        df = df[df[COL_MSISDN].str.strip() != ""].reset_index(drop=True)
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=[COL_BRANCH, COL_MSISDN, COL_STATUS, COL_FOLLOWUP, COL_FU_STATUS])

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values([COL_BRANCH, COL_STATUS]).reset_index(drop=True)
    return combined


# KPI aggregation over filtered customer records (for follow-up cards)
def compute_followup_kpis(df: pd.DataFrame) -> dict:
    total = len(df)
    followed     = int((df[COL_FU_STATUS] == "Followed Up").sum())     if total else 0
    not_followed = int((df[COL_FU_STATUS] == "No Follow Up Yet").sum()) if total else 0
    return {"followed_up": followed, "no_followup": not_followed, "total_records": total}
