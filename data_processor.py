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
# Branch sheet column layout (0-indexed) — varies by bucket and branch:
#   Row 0  = header row
#   col 2  = MSISDN (all buckets, all branches)
#
#   Status column:
#     30H all branches  → col 12 (M)
#     60H all branches  → col 12 (M)
#     90H Bandung       → col 13 (N)
#     90H Crb/Sor/Tsk   → col 12 (M)
#
#   Hasil Follow Up GraPARI column:
#     30H Bandung       → col 30 (AE)
#     30H Crb/Sor/Tsk   → col 31 (AF)
#     60H all branches  → col 31 (AF)
#     90H Bandung       → col 32 (AG)
#     90H Crb/Sor/Tsk   → col 31 (AF)

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
_CI_PCT_COLLECTION   = 8   # col I — MSISDN-based collection %
_CI_PCT_TARGET       = 9   # col J — Rp-based collection % (actual KPI target)

# Branch sheet — fixed columns (all buckets/branches)
_BI_MSISDN = 2

# Per-bucket, per-branch-index status column (0-indexed)
# sheet index 1=Bandung, 2=Cirebon, 3=Soreang, 4=Tasik
_BI_STATUS: dict[str, dict[int, int]] = {
    "30": {1: 12, 2: 12, 3: 12, 4: 12},
    "60": {1: 12, 2: 12, 3: 12, 4: 12},
    "90": {1: 13, 2: 12, 3: 12, 4: 12},
}

# Per-bucket, per-branch-index Hasil Follow Up column (0-indexed)
_BI_FOLLOWUP: dict[str, dict[int, int]] = {
    "30": {1: 30, 2: 31, 3: 31, 4: 31},
    "60": {1: 31, 2: 31, 3: 31, 4: 31},
    "90": {1: 32, 2: 31, 3: 31, 4: 31},
}

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
        "pct_target": None,
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
                "pct_target":       _to_float(row.iloc[_CI_PCT_TARGET]),
            }
        except Exception:
            result[label] = dict(empty)

    return result


# Customer records extraction from branch sheets (indices 1-4)
def extract_customer_records(sheets: dict[str, pd.DataFrame], bucket_key: str) -> pd.DataFrame:
    # Uses sheet INDEX only — never sheet name (names differ between buckets)
    # bucket_key drives per-branch column lookups for Status and Hasil Follow Up
    sheet_list = list(sheets.values())
    frames = []

    status_map  = _BI_STATUS.get(bucket_key, _BI_STATUS["30"])
    followup_map = _BI_FOLLOWUP.get(bucket_key, _BI_FOLLOWUP["30"])

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
        status_col  = status_map.get(idx, 12)
        followup_col = followup_map.get(idx, 31)

        def _col(col_idx: int) -> pd.Series:
            if col_idx < len(data_rows.columns):
                return data_rows.iloc[:, col_idx].reset_index(drop=True)
            return pd.Series([""] * n)

        msisdn_series = _col(_BI_MSISDN).apply(_clean_msisdn)
        status_series = _col(status_col).apply(
            lambda x: str(x).strip() if pd.notna(x) and str(x).strip().lower() not in ("nan", "") else ""
        )
        fu_series = _col(followup_col).apply(
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


# GraPARI ranking extraction from the ranked Bottom/Top tables in the Perform sheet.
#
# All periods: col 0 = rank (or NaN if no rank), col 1 = name, col 2 = pencapaian, col 4 = %
#   30H/60H: rank numbers present in col 0
#   90H:     col 0 is NaN — auto-assign rank 1-10
#
# Row ranges (0-indexed):
#   30H/60H: Bottom 86-95, Top 99-108
#   90H:     Bottom 89-98, Top 102-111
_RANK_ROWS: dict[str, dict] = {
    "30": {"bottom_start": 86, "bottom_end": 96, "top_start": 99,  "top_end": 109},
    "60": {"bottom_start": 86, "bottom_end": 96, "top_start": 99,  "top_end": 109},
    "90": {"bottom_start": 89, "bottom_end": 99, "top_start": 102, "top_end": 112},
}


def extract_rankings(sheets: dict[str, pd.DataFrame], bucket_key: str) -> dict:
    """Return top and bottom GraPARI rankings from the Perform sheet.

    Returns:
        {
          "bottom": [{"rank": int, "name": str, "pencapaian": float, "pct": float}, ...],
          "top":    [{"rank": int, "name": str, "pencapaian": float, "pct": float}, ...],
        }
    """
    empty = {"bottom": [], "top": []}
    sheet_list = list(sheets.values())
    if not sheet_list:
        return empty

    df = sheet_list[0]
    cfg = _RANK_ROWS.get(bucket_key, _RANK_ROWS["30"])

    def _parse_rows(start: int, end: int) -> list:
        records = []
        auto_rank = 1
        for i in range(start, min(end, len(df))):
            # col 1 = name, col 2 = pencapaian, col 4 = % — consistent across all periods
            name_raw       = df.iloc[i, 1]
            pencapaian_raw = df.iloc[i, 2]
            pct_raw        = df.iloc[i, 4] if df.shape[1] > 4 else None

            # col 0 = rank number if present, else fall back to auto-increment
            rank_raw = df.iloc[i, 0]
            try:
                rank = int(float(str(rank_raw).strip()))
            except (ValueError, TypeError):
                rank = auto_rank

            name = str(name_raw).strip()
            if not name or name.lower() in ("nan", "grapari"):
                continue
            pencapaian = _to_float(pencapaian_raw)
            pct = _to_float(pct_raw)
            if pencapaian is None:
                continue
            records.append({"rank": rank, "name": name, "pencapaian": pencapaian, "pct": pct})
            auto_rank += 1
        return records

    return {
        "bottom": _parse_rows(cfg["bottom_start"], cfg["bottom_end"]),
        "top":    _parse_rows(cfg["top_start"],    cfg["top_end"]),
    }
