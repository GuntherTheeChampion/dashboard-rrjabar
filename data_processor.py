import pandas as pd
from data_loader import BRANCH_BY_INDEX

# Canonical internal column names
COL_BRANCH    = "Branch"
COL_MSISDN    = "MSISDN"
COL_STATUS    = "Status"
COL_FOLLOWUP  = "Hasil Follow Up"
COL_FU_STATUS = "Status Follow Up"

# Summary column indices (0-indexed)
_CI_TAGIHAN_MSISDN   = 2 # Kolom C
_CI_TAGIHAN_RP       = 3 # Kolom D
_CI_TUNGGAKAN_MSISDN = 4 # Kolom E
_CI_TUNGGAKAN_RP     = 5 # Kolom F
_CI_BAYAR_MSISDN     = 6 # Kolom G
_CI_BAYAR_RP         = 7 # Kolom H
_CI_PCT_COLLECTION   = 8 # Kolom I
_CI_PCT_TARGET       = 9 # Kolom J

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
    s = str(val).strip()
    if s.lower() in ("nan", "none", ""):
        return ""
    if s.endswith(".0"):
        s = s[:-2]
    return s

def extract_summary_kpis(sheets: dict[str, pd.DataFrame], bucket_key: str) -> dict:
    empty_kpi = {
        "tagihan_msisdn": None, "tagihan_rp": None,
        "tunggakan_msisdn": None, "tunggakan_rp": None,
        "bayar_msisdn": None, "bayar_rp": None,
        "pct_collection": None,
        "pct_target": None,
    }
    labels = ["Bandung", "Cirebon", "Soreang", "Tasik", "Total"]
    result = {k: dict(empty_kpi) for k in labels}
    
    if not sheets:
        return result
        
    summary_df = list(sheets.values())[0]
    
    # Base row: Row 54 (index 53) untuk 30H/60H. Row 57 (index 56) untuk 90H.
    base_row = 56 if bucket_key == "90" else 53
    
    # Offset baris berurutan ke bawah
    row_map = {
        "Bandung": base_row,
        "Cirebon": base_row + 1,
        "Soreang": base_row + 2,
        "Tasik": base_row + 3,
        "Total": base_row + 4
    }
    
    for branch, r_idx in row_map.items():
        if r_idx < len(summary_df):
            row = summary_df.iloc[r_idx]
            try:
                result[branch] = {
                    "tagihan_msisdn":   _to_int(row.iloc[2]), # Kolom C
                    "tagihan_rp":       _to_int(row.iloc[3]), # Kolom D
                    "tunggakan_msisdn": _to_int(row.iloc[4]), # Kolom E
                    "tunggakan_rp":     _to_int(row.iloc[5]), # Kolom F
                    "bayar_msisdn":     _to_int(row.iloc[6]), # Kolom G
                    "bayar_rp":         _to_int(row.iloc[7]), # Kolom H
                    "pct_collection":   _to_float(row.iloc[8]), # Kolom I
                    "pct_target":       _to_float(row.iloc[9]), # Kolom J
                }
            except Exception:
                pass
                
    return result


def extract_customer_records(sheets: dict[str, pd.DataFrame], bucket_key: str) -> pd.DataFrame:
    sheet_list = list(sheets.values())
    frames = []

    # Static indices based on explicit instructions:
    msisdn_col = 2   # Kolom C
    status_col = 12  # Kolom M
    followup_col = 30 # Kolom AE

    for idx in range(1, 5):
        if idx >= len(sheet_list):
            continue

        raw = sheet_list[idx].copy()
        
        # Use mapped branch label (Bandung/Cirebon/etc) for dashboard filters compatibility
        branch_label = BRANCH_BY_INDEX.get(idx, f"Branch_{idx}")

        if len(raw) < 2:
            continue
            
        # Data starts from Row 2 (index 1)
        data_rows = raw.iloc[1:].copy()
        data_rows.columns = range(len(data_rows.columns))
        n = len(data_rows)

        def _col(col_idx: int) -> pd.Series:
            if col_idx < len(data_rows.columns):
                return data_rows.iloc[:, col_idx].reset_index(drop=True)
            return pd.Series([""] * n)

        msisdn_series = _col(msisdn_col).apply(_clean_msisdn)
        
        # Fallback for Status in Kolom N (13) if Kolom M is simply "1"
        status_series_m = _col(status_col)
        status_series_n = _col(13)
        
        def _get_status(val_m, val_n):
            vm = str(val_m).strip()
            vn = str(val_n).strip()
            if vm == "1" and vn in ("BLOCKED 2", "CANCELLED", "ACTIVE", "SUSPEND"):
                return vn
            return vm if pd.notna(val_m) and vm.lower() not in ("nan", "") else ""
            
        status_series = pd.Series([_get_status(m, n) for m, n in zip(status_series_m, status_series_n)])

        # Hasil follow up
        fu_series = _col(followup_col).apply(
            lambda x: str(x).strip() if pd.notna(x) and str(x).strip().lower() not in ("nan", "") else ""
        )
        
        # Logic: if empty -> No Follow Up Yet, if filled -> Followed Up
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


def compute_followup_kpis(df: pd.DataFrame) -> dict:
    total = len(df)
    followed     = int((df[COL_FU_STATUS] == "Followed Up").sum())     if total else 0
    not_followed = int((df[COL_FU_STATUS] == "No Follow Up Yet").sum()) if total else 0
    return {"followed_up": followed, "no_followup": not_followed, "total_records": total}


def extract_rankings(sheets: dict[str, pd.DataFrame], bucket_key: str) -> dict:
    empty = {"bottom": [], "top": []}
    sheet_list = list(sheets.values())
    if not sheet_list:
        return empty

    df = sheet_list[0]
    
    # Base offsets for 30H/60H. Add 3 for 90H.
    offset = 3 if bucket_key == "90" else 0
    
    # Bottom 10 starts at row 87 (index 86)
    bottom_start = 86 + offset
    # Top 10 starts at row 100 (index 99)
    top_start = 99 + offset
    
    bottom = []
    top = []
    
    def _clean_rank_name(raw_name: str) -> str:
        s = str(raw_name).strip()
        parts = s.split(" ", 1)
        if len(parts) == 2 and parts[0].isdigit():
            s = parts[1]
        s = s.replace("GraPARI ", "").replace("GRAPARI ", "")
        return s.strip()

    # Extract Bottom 10
    for i in range(10):
        row_idx = bottom_start + i
        if row_idx < len(df):
            raw_name = str(df.iloc[row_idx, 1]).strip() # Kolom B
            if not raw_name or raw_name.lower() in ("nan", "none", ""):
                continue
                
            name = _clean_rank_name(raw_name)
            pencapaian = _to_float(df.iloc[row_idx, 2]) # Kolom C
            
            if pencapaian is not None:
                bottom.append({
                    "rank": i + 1,
                    "name": name,
                    "pct": pencapaian,
                    "pencapaian": pencapaian
                })

    # Extract Top 10
    for i in range(10):
        row_idx = top_start + i
        if row_idx < len(df):
            raw_name = str(df.iloc[row_idx, 1]).strip() # Kolom B
            if not raw_name or raw_name.lower() in ("nan", "none", ""):
                continue
                
            name = _clean_rank_name(raw_name)
            pencapaian = _to_float(df.iloc[row_idx, 2]) # Kolom C
            
            if pencapaian is not None:
                top.append({
                    "rank": i + 1,
                    "name": name,
                    "pct": pencapaian,
                    "pencapaian": pencapaian
                })

    return {"bottom": bottom, "top": top}
