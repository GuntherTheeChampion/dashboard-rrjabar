# app.py — GraPARI West Java Collection Monitoring Dashboard
# Streamlit UI: tabs, filters, KPI cards, data table
# Entry point: streamlit run app.py

import base64
import html as _html
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from data_loader import clear_all_cache, fetch_workbook
from snapshot_manager import load_snapshots, save_snapshot, delete_snapshot
from data_processor import (
    COL_BRANCH, COL_MSISDN, COL_STATUS, COL_FOLLOWUP, COL_FU_STATUS,
    compute_followup_kpis, extract_customer_records, extract_rankings, extract_summary_kpis,
)
from trend_loader import MONTHS, load_trend_data

# Page config — must be the first Streamlit call
st.set_page_config(
    page_title="Collection Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Global CSS
st.markdown("""
<style>
  :root {
    --bg-page:        #F4F5F7;
    --bg-surface:     #FFFFFF;
    --bg-surface-alt: #F9FAFB;
    --border:         #D1D5DB;
    --text-primary:   #111827;
    --text-secondary: #4B5563;
    --text-muted:     #6B7280;
    --accent:         #E30613;
    --input-bg:       #FFFFFF;
    --input-text:     #111827;
    --input-border:   #D1D5DB;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg-page:        #0E1117;
      --bg-surface:     #1A1D27;
      --bg-surface-alt: #262B38;
      --border:         #374151;
      --text-primary:   #F3F4F6;
      --text-secondary: #D1D5DB;
      --text-muted:     #9CA3AF;
      --accent:         #FF2D3B;
      --input-bg:       #1A1D27;
      --input-text:     #F3F4F6;
      --input-border:   #4B5563;
    }
  }

  #MainMenu { visibility: hidden; }
  footer     { visibility: hidden; }
  header     { visibility: hidden; }

  html, body, [class*="css"] {
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif !important;
  }
  .block-container {
    padding-top: 130px !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
  }

  /* Sticky page header */
  .sticky-header {
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 999;
    height: 108px;
    padding: 0 2.5rem;
    background: #C8102E;
    display: flex;
    align-items: center;
    gap: 1.25rem;
    overflow: hidden;
  }
  .sticky-header .hdr-svg {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    width: 100%; height: 100%;
    pointer-events: none;
  }
  .sticky-header .hdr-text {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    gap: 0.05rem;
  }
  .sticky-header .hdr-text h1 {
    font-size: 1.25rem; font-weight: 700;
    color: #ffffff; margin: 0;
    letter-spacing: -0.01em;
    line-height: 1.2;
    text-shadow: 0 1px 3px rgba(0,0,0,0.25);
  }
  .sticky-header .hdr-date {
    display: inline-block;
    font-size: 0.62rem; font-weight: 700;
    color: #fff;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 999px;
    padding: 0.08rem 0.5rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-top: 0.04rem;
    width: fit-content;
  }
  .sticky-header .hdr-text p {
    font-size: 0.72rem; font-weight: 400;
    color: rgba(255,255,255,0.8);
    margin: 0;
    line-height: 1.3;
  }

  /* Mobile: compact header ≤640px */
  @media (max-width: 640px) {
    .block-container {
      padding-top: 90px !important;
    }
    .sticky-header {
      height: auto !important;
      min-height: 64px;
      padding: 0.65rem 1rem;
      gap: 0.75rem;
      align-items: center;
    }
    .sticky-header .hdr-text h1 {
      font-size: 0.9rem !important;
      line-height: 1.2 !important;
    }
    .sticky-header .hdr-date {
      font-size: 0.55rem !important;
      padding: 0.06rem 0.4rem !important;
      margin-top: 0.08rem !important;
    }
    .sticky-header .hdr-text p {
      font-size: 0.6rem !important;
      line-height: 1.3 !important;
    }
  }

  /* Section labels */
  .section-label {
    font-size: 0.72rem !important; font-weight: 700 !important;
    color: var(--text-secondary) !important; letter-spacing: 0.09em;
    text-transform: uppercase; margin-bottom: 0.5rem;
  }

  /* KPI cards */
  [data-testid="metric-container"] {
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    padding: 1rem 1.25rem !important;
  }
  [data-testid="metric-container"] label,
  [data-testid="metric-container"] [data-testid="stMetricLabel"] p,
  [data-testid="metric-container"] > div:first-child {
    font-size: 0.75rem !important; font-weight: 700 !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important; letter-spacing: 0.07em !important;
  }
  [data-testid="stMetricValue"] > div,
  [data-testid="stMetricValue"] {
    font-size: 1.75rem !important; font-weight: 700 !important;
    color: var(--text-primary) !important;
  }
  [data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
    color: var(--text-muted) !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border);
    border-radius: 6px 6px 0 0;
    padding: 0 0.5rem; gap: 0;
  }
  .stTabs [data-baseweb="tab"] {
    font-size: 0.875rem !important; font-weight: 600 !important;
    color: var(--text-secondary) !important;
    padding: 0.75rem 1.25rem !important; background: transparent !important;
  }
  .stTabs [aria-selected="true"] {
    color: var(--text-primary) !important;
    border-bottom: 3px solid var(--accent) !important;
    background: transparent !important;
  }
  .stTabs [data-baseweb="tab-panel"] {
    background-color: var(--bg-page) !important; padding-top: 1.25rem;
  }

  /* Selectbox */
  [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background-color: var(--input-bg) !important;
    border-color: var(--input-border) !important;
  }
  [data-testid="stSelectbox"] div[data-baseweb="select"] span,
  [data-testid="stSelectbox"] div[data-baseweb="select"] div {
    color: var(--input-text) !important;
  }
  [data-baseweb="popover"] [role="option"],
  [data-baseweb="menu"] li {
    background-color: var(--input-bg) !important; color: var(--input-text) !important;
  }
  [data-baseweb="popover"] [role="option"]:hover,
  [data-baseweb="menu"] li:hover {
    background-color: var(--bg-surface-alt) !important;
  }
  [data-testid="stSelectbox"] label p {
    font-size: 0.75rem !important; font-weight: 700 !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important; letter-spacing: 0.07em !important;
  }

  /* Divider */
  hr { border: none; border-top: 1px solid var(--border); margin: 1.25rem 0; }

  /* Caption */
  [data-testid="stCaptionContainer"] p {
    color: var(--text-muted) !important; font-size: 0.78rem !important;
  }
</style>
""", unsafe_allow_html=True)



import datetime

ID_MONTHS = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def format_id_date(iso_str):
    try:
        dt = datetime.datetime.strptime(iso_str, "%Y-%m-%d")
        return f"{dt.day} {ID_MONTHS[dt.month]} {dt.year}"
    except:
        return iso_str

snapshots = load_snapshots()
if not snapshots:
    snapshots = [{"id": "default", "name": "None", "date": "None", "urls": {"30": "", "60": "", "90": ""}}]

date_map = {s.get("date", s["name"]): s for s in snapshots}

if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

if st.session_state.current_page == "admin":
    st.header("🗂️ Manajemen Periode Data")
    if st.button("⬅️ Kembali ke Dashboard"):
        st.session_state.current_page = "dashboard"
        st.rerun()
        
    st.markdown("---")
    st.subheader("➕ Tambah / Update Data (Kalender)")
    new_date_obj = st.date_input("Pilih Tanggal:", value=datetime.date.today())
    new_date_str = new_date_obj.isoformat()
    
    existing = date_map.get(new_date_str, {})
    pre_30 = existing.get("urls", {}).get("30", "")
    pre_60 = existing.get("urls", {}).get("60", "")
    pre_90 = existing.get("urls", {}).get("90", "")
    
    new_30 = st.text_input("Link Spreadsheet 30H", value=pre_30, key="new_30")
    new_60 = st.text_input("Link Spreadsheet 60H", value=pre_60, key="new_60")
    new_90 = st.text_input("Link Spreadsheet 90H", value=pre_90, key="new_90")
    if st.button("Simpan Data untuk Tanggal Ini"):
        if date_map.get(new_date_str):
            st.warning("Data for this date already exists. Please delete it first before re‑upload.")
        else:
            save_snapshot(new_date_str, new_30, new_60, new_90)
            st.success("Data saved successfully.")
            st.balloons()
            st.rerun()

    st.markdown("---")
    st.subheader("🗑️ Hapus Data Periode")
    delete_display = [format_id_date(s.get("date", s["name"])) for s in snapshots]
    delete_selected = st.selectbox("**Pilih Periode untuk Dihapus:**", delete_display, key="del_select")
    del_idx = delete_display.index(delete_selected)
    del_date = snapshots[del_idx].get("date", snapshots[del_idx].get("name"))
    
    if st.button("Hapus Data untuk Periode Ini"):
        delete_snapshot(del_date)
        st.success("Data dihapus.")
        st.rerun()
        
    st.stop()

# --- DASHBOARD VIEW ---
st.markdown("""
<style>
div[data-testid="stButton"] button {
    background-color: #16a34a !important;
    border-color: #16a34a !important;
    color: #ffffff !important;
}
div[data-testid="stButton"] button:hover {
    background-color: #15803d !important;
    border-color: #15803d !important;
    color: #ffffff !important;
}
div[data-testid="stButton"] button:focus:not(:active) {
    border-color: #15803d !important;
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

display_names = [format_id_date(s.get("date", s["name"])) for s in snapshots]

col_sel, col_btn1, col_btn2 = st.columns([6, 2, 2])
with col_sel:
    selected_display = st.selectbox("**PILIH PERIODE AKTIF:**", display_names)
    selected_idx = display_names.index(selected_display)
    selected_snapshot = snapshots[selected_idx]

with col_btn1:
    st.markdown("<div style='margin-top: 1.75rem'></div>", unsafe_allow_html=True)
    if st.button("⚙️ Kelola Data Periode", use_container_width=True):
        st.session_state.current_page = "admin"
        st.rerun()

with col_btn2:
    st.markdown("<div style='margin-top: 1.75rem'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Data", type="secondary", help="Loading ulang untuk update data terbaru", use_container_width=True):
        clear_all_cache()
        st.rerun()

# Helpers
def _fmt_rp(val) -> str:
    # Format integer as Indonesian Rupiah: Rp 4.502.119
    if val is None:
        return "—"
    return "Rp " + f"{int(val):,}".replace(",", ".")


def _fmt_int(val) -> str:
    if val is None:
        return "—"
    return f"{int(val):,}"


def _fmt_pct(val) -> str:
    if val is None:
        return "—"
    return f"{val * 100:.2f}%"


# KPI cards — 4 cards from the Perform sheet
def render_kpi_cards(summary: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)

    tagihan_msisdn  = summary.get("tagihan_msisdn")
    tagihan_rp      = summary.get("tagihan_rp")
    tunggakan_msisdn= summary.get("tunggakan_msisdn")
    tunggakan_rp    = summary.get("tunggakan_rp")
    bayar_msisdn    = summary.get("bayar_msisdn")
    bayar_rp        = summary.get("bayar_rp")
    pct             = summary.get("pct_collection")
    pct_target      = summary.get("pct_target")

    target_label = f"Target {_fmt_pct(pct_target)}" if pct_target is not None else "Target —"

    c1.metric(
        "Total Target Tagihan",
        _fmt_rp(tagihan_rp),
        delta=f"{_fmt_int(tagihan_msisdn)} Accounts",
        delta_color="off",
    )
    c2.metric(
        "Sudah Terbayar",
        _fmt_rp(bayar_rp),
        delta=f"{_fmt_int(bayar_msisdn)} Accounts",
        delta_color="off",
    )
    c3.metric(
        "Sisa Tunggakan",
        _fmt_rp(tunggakan_rp),
        delta=f"{_fmt_int(tunggakan_msisdn)} Accounts",
        delta_color="off",
    )
    c4.metric(
        "% Collection",
        _fmt_pct(pct),
        delta=target_label,
        delta_color="off",
    )


# GraPARI ranking section — top & bottom performers
def render_rankings(rankings: dict, bucket_key: str) -> None:
    bottom = rankings.get("bottom", [])
    top    = rankings.get("top", [])
    if not bottom and not top:
        return

    st.markdown(
        f'<p class="section-label">Peringkat GraPARI &nbsp;&middot;&nbsp; {bucket_key}H</p>',
        unsafe_allow_html=True,
    )

    col_bot, col_top = st.columns(2)

    def _row_html(item: dict, is_bottom: bool) -> str:
        rank       = item["rank"]
        name       = item["name"].replace("GraPARI ", "")
        pct        = item["pct"]
        pencapaian = item["pencapaian"]

        if is_bottom:
            rank_color = "#dc2626"   # red-600
            bg_color   = "rgba(220,38,38,0.07)"
            border_col = "rgba(220,38,38,0.18)"
        else:
            rank_color = "#16a34a"   # green-600
            bg_color   = "rgba(22,163,74,0.07)"
            border_col = "rgba(22,163,74,0.18)"

        pct_str = f"{pct * 100:.2f}%" if pct is not None else f"{pencapaian * 100:.2f}%"

        return (
            f'<div style="display:flex;align-items:center;gap:.65rem;padding:.45rem .6rem;'
            f'margin-bottom:.3rem;border-radius:5px;background:{bg_color};border:1px solid {border_col}">'
            f'<span style="font-size:.78rem;font-weight:700;color:{rank_color};min-width:1.4rem;'
            f'text-align:center">{rank}</span>'
            f'<span style="font-size:.82rem;color:var(--text-primary);flex:1;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="GraPARI {name}">'
            f'{name}</span>'
            f'<span style="font-size:.8rem;font-weight:600;color:{rank_color};'
            f'white-space:nowrap">{pct_str}</span>'
            f'</div>'
        )

    with col_bot:
        st.markdown(
            '<div style="font-size:.72rem;font-weight:700;color:#dc2626;text-transform:uppercase;'
            'letter-spacing:.07em;margin-bottom:.5rem">Perlu Perhatian</div>',
            unsafe_allow_html=True,
        )
        rows_html = "".join(_row_html(item, is_bottom=True) for item in bottom)
        st.markdown(f'<div>{rows_html}</div>', unsafe_allow_html=True)

    with col_top:
        st.markdown(
            '<div style="font-size:.72rem;font-weight:700;color:#16a34a;text-transform:uppercase;'
            'letter-spacing:.07em;margin-bottom:.5rem">Pencapaian Tertinggi</div>',
            unsafe_allow_html=True,
        )
        rows_html = "".join(_row_html(item, is_bottom=False) for item in top)
        st.markdown(f'<div>{rows_html}</div>', unsafe_allow_html=True)


# Follow-up status cards — 2 inline cards with conditional colouring
def render_followup_cards(fu_kpis: dict) -> None:
    followed   = fu_kpis['followed_up']
    nofollowed = fu_kpis['no_followup']

    # followed_up: green when > 0; no_followup: red ONLY when exactly 0
    fu_color  = "#16a34a" if followed   > 0 else "var(--text-primary)"
    nfu_color = "#E30613" if nofollowed == 0 else "var(--text-primary)"

    ca, cb = st.columns(2)
    with ca:
        st.markdown(
            f'<div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;'
            f'padding:1rem 1.25rem">'
            f'<div style="font-size:.75rem;font-weight:700;color:var(--text-secondary);'
            f'text-transform:uppercase;letter-spacing:.07em;margin-bottom:.35rem">Followed Up</div>'
            f'<div style="font-size:1.75rem;font-weight:700;color:{fu_color}">{followed:,}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with cb:
        st.markdown(
            f'<div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;'
            f'padding:1rem 1.25rem">'
            f'<div style="font-size:.75rem;font-weight:700;color:var(--text-secondary);'
            f'text-transform:uppercase;letter-spacing:.07em;margin-bottom:.35rem">No Follow Up Yet</div>'
            f'<div style="font-size:1.75rem;font-weight:700;color:{nfu_color}">{nofollowed:,}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# HTML table with MSISDN filter + FU-status dropdown + row colour coding
def render_table_with_find(df: pd.DataFrame,
                           key: str,
                           csv_b64: str = "",
                           csv_fname: str = "data.csv") -> None:
    if df.empty:
        st.caption("No records to display.")
        return

    n_rows = len(df)
    cols   = df.columns.tolist()
    rows_data = []
    for _, row in df.iterrows():
        rows_data.append(["" if pd.isna(row[c]) else str(row[c]) for c in cols])

    cols_json    = json.dumps(cols)
    rows_json    = json.dumps(rows_data)
    csv_data_uri = f"data:text/csv;base64,{csv_b64}" if csv_b64 else ""

    # column indices for JS colouring (0-based, after the row-num column)
    idx_hasifu  = cols.index("Hasil Follow Up")    if "Hasil Follow Up"   in cols else -1
    idx_statusfu = cols.index("Status Follow Up")  if "Status Follow Up"  in cols else -1

    html_src = f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  :root {{
    --text:#E5E7EB; --text-muted:#9CA3AF; --border:#4B5563;
    --border-table:#374151; --bg-input:#262B38; --bg-thead:#1A1D27;
    --bg-row-hover:rgba(255,255,255,0.04); --row-divider:#262B38; --accent:#E30613;
    --green:#16a34a; --red:#E30613;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --text:#111827; --text-muted:#6B7280; --border:#9CA3AF;
      --border-table:#D1D5DB; --bg-input:#FFFFFF; --bg-thead:#F9FAFB;
      --bg-row-hover:rgba(0,0,0,0.02); --row-divider:#E5E7EB; --accent:#E30613;
      --green:#15803d; --red:#E30613;
    }}
  }}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:"Segoe UI",system-ui,-apple-system,sans-serif;font-size:13px;background:transparent;color:var(--text);}}
  #toolbar{{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px;flex-wrap:wrap;}}
  #filter-bar{{display:flex;align-items:center;gap:8px;flex:1 1 auto;flex-wrap:wrap;}}
  .filter-group{{display:flex;flex-direction:column;gap:3px;}}
  .filter-label{{font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;}}
  .filter-input{{padding:5px 10px;font-size:12px;font-family:inherit;
    border:1px solid var(--border);border-radius:4px;background:var(--bg-input);color:var(--text);outline:none;}}
  .filter-input::placeholder{{color:var(--text-muted);opacity:1;}}
  .filter-input:focus{{border-color:var(--accent);}}
  select.filter-input{{cursor:pointer;padding-right:24px;}}
  #btn-clear-all{{padding:5px 10px;font-size:11px;font-family:inherit;font-weight:600;
    border:1px solid var(--border);border-radius:4px;background:var(--bg-input);color:var(--text-muted);
    cursor:pointer;white-space:nowrap;align-self:flex-end;transition:border-color .12s,color .12s;}}
  #btn-clear-all:hover{{border-color:var(--accent);color:var(--accent);}}
  #action-btns{{display:flex;align-items:center;gap:4px;flex-shrink:0;}}
  .icon-btn{{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;
    border:1px solid var(--border);border-radius:4px;background:var(--bg-input);color:var(--text);
    cursor:pointer;text-decoration:none;transition:border-color .12s,color .12s;flex-shrink:0;}}
  .icon-btn:hover,.icon-btn.active{{border-color:var(--accent);color:var(--accent);}}
  #status-bar{{font-size:11px;color:var(--text-muted);margin-bottom:6px;min-height:16px;}}
  #table-wrap{{width:100%;overflow-x:auto;overflow-y:auto;max-height:440px;
    border:1px solid var(--border-table);border-radius:4px;}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px;table-layout:fixed;}}
  thead th{{position:sticky;top:0;background:var(--bg-thead);color:var(--text-muted);
    font-weight:600;text-align:left;padding:8px 12px;border-bottom:2px solid var(--border-table);
    border-right:1px solid var(--border-table);font-size:11px;text-transform:uppercase;
    letter-spacing:.06em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;z-index:2;}}
  thead th:last-child{{border-right:none;}}
  tbody tr{{border-bottom:1px solid var(--row-divider);transition:background .1s;}}
  tbody tr:hover{{background:var(--bg-row-hover);}}
  tbody td{{padding:7px 12px;color:var(--text);vertical-align:top;
    border-right:1px solid var(--row-divider);overflow:hidden;word-break:break-word;}}
  tbody td:last-child{{border-right:none;}}
  col.col-num{{width:46px;}} col.col-branch{{width:90px;}} col.col-msisdn{{width:145px;}}
  col.col-status{{width:110px;}} col.col-hasifu{{width:auto;}} col.col-statusfu{{width:140px;}}
  td.row-num,th.row-num{{width:46px;text-align:right;color:var(--text-muted);
    font-size:11px;padding-right:12px;white-space:nowrap;user-select:none;}}
  .fu-done{{color:var(--green) !important;font-weight:600;}}
  .fu-none{{color:var(--red) !important;font-style:italic;}}
</style>
</head>
<body>
<div id="toolbar">
  <div id="filter-bar">
    <div class="filter-group">
      <span class="filter-label">Cari MSISDN</span>
      <input id="msisdn-input" class="filter-input" type="text" placeholder="Ketik nomor HP..." autocomplete="off" style="width:180px"/>
    </div>
    <div class="filter-group">
      <span class="filter-label">Status Follow Up</span>
      <select id="fu-select" class="filter-input" style="width:180px">
        <option value="">Semua Status</option>
        <option value="Followed Up">Followed Up</option>
        <option value="No Follow Up Yet">No Follow Up Yet</option>
      </select>
    </div>
    <button id="btn-clear-all" title="Reset semua filter">&#10005; Reset</button>
  </div>
  <div id="action-btns">
    <button class="icon-btn" id="btn-compact" title="Toggle ringkas/penuh">
      <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 5h18M1 10h18M1 15h18"/></svg>
    </button>
    <a id="btn-download" class="icon-btn" href="{csv_data_uri}" download="{csv_fname}" title="Unduh CSV">
      <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3v10M6 9l4 4 4-4"/><rect x="3" y="15" width="14" height="2" rx="1"/></svg>
    </a>
    <button class="icon-btn" id="btn-copy" title="Salin ke clipboard">
      <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="3" width="10" height="13" rx="1"/><path d="M3 7v11a1 1 0 001 1h10"/></svg>
    </button>
  </div>
</div>
<div id="status-bar">Showing {n_rows:,} records</div>
<div id="table-wrap">
  <table id="data-table">
    <colgroup id="t-cols"></colgroup>
    <thead id="t-head"></thead>
    <tbody id="t-body"></tbody>
  </table>
</div>
<script>
(function(){{
  const COLS={cols_json};
  const ROWS={rows_json};
  const IDX_HASIFU={idx_hasifu};
  const IDX_STATUSFU={idx_statusfu};
  const COL_CLASS_MAP={{
    "Branch":"col-branch","MSISDN":"col-msisdn","Status":"col-status",
    "Hasil Follow Up":"col-hasifu","Status Follow Up":"col-statusfu"
  }};

  // Build colgroup
  const colgroup=document.getElementById("t-cols");
  const cn=document.createElement("col"); cn.className="col-num"; colgroup.appendChild(cn);
  COLS.forEach(c=>{{const col=document.createElement("col");if(COL_CLASS_MAP[c])col.className=COL_CLASS_MAP[c];colgroup.appendChild(col);}});

  // Build header
  const thead=document.getElementById("t-head");
  const tbody=document.getElementById("t-body");
  const hrow=document.createElement("tr");
  const thN=document.createElement("th"); thN.textContent="#"; thN.className="row-num"; hrow.appendChild(thN);
  COLS.forEach(c=>{{const th=document.createElement("th");th.textContent=c;hrow.appendChild(th);}});
  thead.appendChild(hrow);

  // Build rows with colour coding
  const allRows=[];
  ROWS.forEach((row,ri)=>{{
    const tr=document.createElement("tr");
    tr.dataset.ri=ri;
    const tdN=document.createElement("td"); tdN.className="row-num"; tdN.textContent=ri+1; tr.appendChild(tdN);
    row.forEach((val,ci)=>{{
      const td=document.createElement("td");
      td.dataset.orig=val;
      td.textContent=val;
      // Hasil Follow Up: green if has content, red if empty
      if(ci===IDX_HASIFU){{
        td.classList.add(val.trim()===""?"fu-none":"fu-done");
        if(val.trim()==="") td.textContent="—";
      }}
      // Status Follow Up: green for Followed Up, red for No Follow Up Yet
      if(ci===IDX_STATUSFU){{
        if(val==="Followed Up") td.classList.add("fu-done");
        else if(val==="No Follow Up Yet") td.classList.add("fu-none");
      }}
      tr.appendChild(td);
    }});
    tbody.appendChild(tr);
    allRows.push(tr);
  }});

  const statusBar=document.getElementById("status-bar");
  const msisdnInput=document.getElementById("msisdn-input");
  const fuSelect=document.getElementById("fu-select");
  let visibleCount={n_rows};

  function applyFilters(){{
    const msisdnQ=msisdnInput.value.replace(/[\u00A0\u200B\u200C\u200D\uFEFF]/g,"").trim().toLowerCase();
    const fuQ=fuSelect.value;
    let shown=0, dispNum=1;
    allRows.forEach(tr=>{{
      const cells=[...tr.querySelectorAll("td[data-orig]")];
      // MSISDN is col index 1 in COLS (after row-num td which has no data-orig)
      const msisdnIdx=COLS.indexOf("MSISDN");
      const msisdnVal=msisdnIdx>=0&&cells[msisdnIdx]?cells[msisdnIdx].dataset.orig.toLowerCase():"";
      const statusVal=IDX_STATUSFU>=0&&cells[IDX_STATUSFU]?cells[IDX_STATUSFU].dataset.orig:"";
      const matchMsisdn=msisdnQ===""||msisdnVal.includes(msisdnQ);
      const matchFu=fuQ===""||statusVal===fuQ;
      if(matchMsisdn&&matchFu){{
        tr.style.display="";
        tr.querySelector("td.row-num").textContent=dispNum++;
        shown++;
      }}else{{
        tr.style.display="none";
      }}
    }});
    visibleCount=shown;
    if(msisdnQ===""&&fuQ===""){{
      statusBar.textContent="Showing {n_rows:,} records";
    }}else{{
      statusBar.textContent=shown+" record ditampilkan dari {n_rows:,}";
    }}
  }}

  msisdnInput.addEventListener("input",applyFilters);
  fuSelect.addEventListener("change",applyFilters);
  document.getElementById("btn-clear-all").addEventListener("click",()=>{{
    msisdnInput.value=""; fuSelect.value=""; applyFilters();
  }});

  const btnCompact=document.getElementById("btn-compact"); let compact=false;
  btnCompact.addEventListener("click",()=>{{
    compact=!compact;
    document.querySelectorAll("#t-body td").forEach(td=>{{td.style.padding=compact?"3px 12px":"";}});
    btnCompact.classList.toggle("active",compact);
  }});

  const btnCopyAll=document.getElementById("btn-copy");
  btnCopyAll.addEventListener("click",()=>{{
    const visRows=[...document.querySelectorAll("#t-body tr")].filter(r=>r.style.display!=="none");
    const tsv=COLS.join("\\t")+"\\n"+visRows.map(tr=>[...tr.querySelectorAll("td[data-orig]")].map(td=>td.dataset.orig).join("\\t")).join("\\n");
    navigator.clipboard.writeText(tsv).then(()=>{{btnCopyAll.classList.add("active");setTimeout(()=>btnCopyAll.classList.remove("active"),1200);}}).catch(()=>{{}});
  }});
}})();
</script>
</body></html>"""

    component_height = min(46 + 33 * n_rows + 110, 660)
    components.html(html_src, height=component_height, scrolling=False)


# Tab renderer
DEEP_LINKS = {
    "30": {
        "Bandung": "https://docs.google.com/spreadsheets/d/16qXh1as-6QgI3JrE8xvPA41-LESAVyVT/edit?gid=1120671799#gid=1120671799",
        "Cirebon": "https://docs.google.com/spreadsheets/d/16qXh1as-6QgI3JrE8xvPA41-LESAVyVT/edit?gid=948339330#gid=948339330",
        "Soreang": "https://docs.google.com/spreadsheets/d/16qXh1as-6QgI3JrE8xvPA41-LESAVyVT/edit?gid=2036483408#gid=2036483408",
        "Tasik":   "https://docs.google.com/spreadsheets/d/16qXh1as-6QgI3JrE8xvPA41-LESAVyVT/edit?gid=2103088493#gid=2103088493",
    },
    "60": {
        "Bandung": "https://docs.google.com/spreadsheets/d/1S-yXXidmDb6qwsudYe4yXgzG4Xw0WCUC/edit?gid=227052033#gid=227052033",
        "Cirebon": "https://docs.google.com/spreadsheets/d/1S-yXXidmDb6qwsudYe4yXgzG4Xw0WCUC/edit?gid=1817837638#gid=1817837638",
        "Soreang": "https://docs.google.com/spreadsheets/d/1S-yXXidmDb6qwsudYe4yXgzG4Xw0WCUC/edit?gid=526873559#gid=526873559",
        "Tasik":   "https://docs.google.com/spreadsheets/d/1S-yXXidmDb6qwsudYe4yXgzG4Xw0WCUC/edit?gid=1701189022#gid=1701189022",
    },
    "90": {
        "Bandung": "https://docs.google.com/spreadsheets/d/14-TFIE2tIMup2BP0VZvgwCsqTiYdFVgO/edit?gid=87501463#gid=87501463",
        "Cirebon": "https://docs.google.com/spreadsheets/d/14-TFIE2tIMup2BP0VZvgwCsqTiYdFVgO/edit?gid=1439401178#gid=1439401178",
        "Soreang": "https://docs.google.com/spreadsheets/d/14-TFIE2tIMup2BP0VZvgwCsqTiYdFVgO/edit?gid=488080914#gid=488080914",
        "Tasik":   "https://docs.google.com/spreadsheets/d/14-TFIE2tIMup2BP0VZvgwCsqTiYdFVgO/edit?gid=907616748#gid=907616748",
    },
}


def render_tab(bucket_key: str, urls_dict: dict) -> None:
    url = urls_dict.get(bucket_key, "")

    if not url or url.strip() == "":
        st.info(f"Data belum diinput untuk {bucket_key} Hari.")
        return

    with st.spinner("Memuat data..."):
        sheets = fetch_workbook(url)

    if not sheets:
        st.warning("Data tidak dapat dimuat. Periksa koneksi atau URL Google Sheets.")
        return

    summary_kpis  = extract_summary_kpis(sheets, bucket_key)
    customer_df   = extract_customer_records(sheets, bucket_key)

    # Filters
    st.markdown('<p class="section-label">Filters</p>', unsafe_allow_html=True)
    branch_options  = ["Semua Branch", "Bandung", "Cirebon", "Soreang", "Tasik"]
    status_options  = ["Semua Status", "Followed Up", "No Follow Up Yet"]

    fcol1, fcol2, fcol3 = st.columns([2, 2, 5])
    with fcol1:
        branch_filter = st.selectbox("Branch", branch_options, key=f"branch_{bucket_key}")
    with fcol2:
        status_filter = st.selectbox("Status Follow Up", status_options, key=f"status_{bucket_key}")
    with fcol3:
        bucket_links = DEEP_LINKS.get(bucket_key, {})
        if branch_filter != "Semua Branch" and branch_filter in bucket_links:
            deep_url   = bucket_links[branch_filter]
            link_label = f"Buka Sheet: {branch_filter} &rarr;"
        else:
            first_link = next(iter(bucket_links.values()), "")
            deep_url   = first_link.split("?gid=")[0] if first_link else ""
            link_label = "Buka Google Sheet &rarr;"
        if deep_url:
            st.markdown(
                f'<div style="display:flex;flex-direction:column;justify-content:flex-end;height:100%;padding-bottom:.45rem">'
                f'<span style="font-size:.75rem;font-weight:700;color:var(--text-secondary);text-transform:uppercase;'
                f'letter-spacing:.07em;display:block;margin-bottom:.4rem">Sumber Data</span>'
                f'<a href="{deep_url}" target="_blank" rel="noopener noreferrer" '
                f'style="display:inline-flex;align-items:center;gap:.35rem;width:fit-content;font-size:.78rem;'
                f'font-weight:600;color:var(--text-secondary);text-decoration:none;background:var(--bg-surface-alt);'
                f'border:1px solid var(--border);border-radius:4px;padding:.35rem .65rem;white-space:nowrap">'
                f'{link_label}</a></div>',
                unsafe_allow_html=True,
            )

    # KPI section 1 — summary figures from Perform sheet
    summary_key = branch_filter if branch_filter != "Semua Branch" else "Total"
    branch_summary = summary_kpis.get(summary_key, {})

    scope_parts = []
    if branch_filter != "Semua Branch":
        scope_parts.append(branch_filter)
    if status_filter != "Semua Status":
        scope_parts.append(status_filter)
    scope_label = " — ".join(scope_parts) if scope_parts else "Semua Branch"

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        f'<p class="section-label">Performance Summary &nbsp;&middot;&nbsp; {scope_label}</p>',
        unsafe_allow_html=True,
    )
    render_kpi_cards(branch_summary)

    # Ranking section — always shows region-wide top/bottom regardless of branch filter
    rankings = extract_rankings(sheets, bucket_key)
    st.markdown("<hr>", unsafe_allow_html=True)
    render_rankings(rankings, bucket_key)

    # Apply customer record filters
    filtered = customer_df.copy()
    if branch_filter != "Semua Branch":
        filtered = filtered[filtered[COL_BRANCH] == branch_filter]
    if status_filter != "Semua Status":
        filtered = filtered[filtered[COL_FU_STATUS] == status_filter]

    # KPI section 2 — follow-up status from customer records
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        f'<p class="section-label">Follow-Up Status &nbsp;&middot;&nbsp; {scope_label}</p>',
        unsafe_allow_html=True,
    )
    fu_kpis = compute_followup_kpis(filtered)
    render_followup_cards(fu_kpis)

    # Customer records table
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Customer Records</p>', unsafe_allow_html=True)

    display_cols = [c for c in [COL_BRANCH, COL_MSISDN, COL_STATUS, COL_FOLLOWUP, COL_FU_STATUS]
                    if c in filtered.columns]
    table_df = filtered[display_cols].reset_index(drop=True)

    csv_bytes = table_df.to_csv(index=False).encode("utf-8")
    csv_b64   = base64.b64encode(csv_bytes).decode()
    csv_fname = f"collection_{bucket_key}hari_{branch_filter.lower().replace(' ', '_')}.csv"

    render_table_with_find(table_df, key=f"find_{bucket_key}",
                           csv_b64=csv_b64, csv_fname=csv_fname)


# Page header — sticky, full-width, red with diagonal pill shapes
st.markdown(f"""
<div class="sticky-header">
  <!-- SVG decorative layer: diagonal rounded pills + halftone dots -->
  <svg class="hdr-svg" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
    <defs>
      <!-- Reusable pill shape: 260x90 rounded rectangle -->
      <rect id="pill-xl" width="260" height="90" rx="45" ry="45"/>
      <rect id="pill-lg" width="200" height="70" rx="35" ry="35"/>
      <rect id="pill-md" width="150" height="55" rx="27" ry="27"/>
      <rect id="pill-sm" width="110" height="42" rx="21" ry="21"/>
    </defs>
    <!-- Pills: dark crimson, rotated -35deg, scattered across header -->
    <g fill="#A00020" opacity="0.55">
      <use href="#pill-xl" transform="translate(-60, 10) rotate(-35, 130, 45)"/>
      <use href="#pill-xl" transform="translate(180, -20) rotate(-35, 130, 45)"/>
      <use href="#pill-lg" transform="translate(420, 5) rotate(-35, 100, 35)"/>
      <use href="#pill-lg" transform="translate(620, -15) rotate(-35, 100, 35)"/>
      <use href="#pill-md" transform="translate(800, 20) rotate(-35, 75, 27)"/>
      <use href="#pill-md" transform="translate(950, -10) rotate(-35, 75, 27)"/>
      <use href="#pill-sm" transform="translate(1100, 30) rotate(-35, 55, 21)"/>
      <use href="#pill-xl" transform="translate(1150, -5) rotate(-35, 130, 45)"/>
      <use href="#pill-sm" transform="translate(1350, 15) rotate(-35, 55, 21)"/>
      <use href="#pill-lg" transform="translate(1480, -20) rotate(-35, 100, 35)"/>
    </g>
    <!-- Halftone dot cluster: bottom-right quadrant -->
    <g fill="#ffffff" opacity="0.18">
      <circle cx="1300" cy="70" r="3"/><circle cx="1314" cy="70" r="3"/><circle cx="1328" cy="70" r="3"/>
      <circle cx="1342" cy="70" r="3"/><circle cx="1356" cy="70" r="3"/><circle cx="1370" cy="70" r="3"/>
      <circle cx="1300" cy="84" r="3"/><circle cx="1314" cy="84" r="3"/><circle cx="1328" cy="84" r="3"/>
      <circle cx="1342" cy="84" r="3"/><circle cx="1356" cy="84" r="3"/><circle cx="1370" cy="84" r="3"/>
      <circle cx="1307" cy="77" r="3"/><circle cx="1321" cy="77" r="3"/><circle cx="1335" cy="77" r="3"/>
      <circle cx="1349" cy="77" r="3"/><circle cx="1363" cy="77" r="3"/><circle cx="1377" cy="77" r="3"/>
      <circle cx="1307" cy="91" r="3"/><circle cx="1321" cy="91" r="3"/><circle cx="1335" cy="91" r="3"/>
      <circle cx="1349" cy="91" r="3"/><circle cx="1363" cy="91" r="3"/><circle cx="1377" cy="91" r="3"/>
      <circle cx="1300" cy="98" r="3"/><circle cx="1314" cy="98" r="3"/><circle cx="1328" cy="98" r="3"/>
      <circle cx="1342" cy="98" r="3"/><circle cx="1356" cy="98" r="3"/><circle cx="1370" cy="98" r="3"/>
      <circle cx="1390" cy="70" r="3"/><circle cx="1404" cy="70" r="3"/><circle cx="1418" cy="70" r="3"/>
      <circle cx="1432" cy="70" r="3"/><circle cx="1446" cy="70" r="3"/><circle cx="1460" cy="70" r="3"/>
      <circle cx="1390" cy="84" r="3"/><circle cx="1404" cy="84" r="3"/><circle cx="1418" cy="84" r="3"/>
      <circle cx="1432" cy="84" r="3"/><circle cx="1446" cy="84" r="3"/><circle cx="1460" cy="84" r="3"/>
      <circle cx="1397" cy="91" r="3"/><circle cx="1411" cy="91" r="3"/><circle cx="1425" cy="91" r="3"/>
      <circle cx="1439" cy="91" r="3"/><circle cx="1453" cy="91" r="3"/><circle cx="1467" cy="91" r="3"/>
      <circle cx="1390" cy="98" r="3"/><circle cx="1404" cy="98" r="3"/><circle cx="1418" cy="98" r="3"/>
      <circle cx="1432" cy="98" r="3"/><circle cx="1446" cy="98" r="3"/><circle cx="1460" cy="98" r="3"/>
    </g>
  </svg>

  <!-- Text content -->
  <div class="hdr-text">
    <h1>Collection Monitoring Dashboard</h1>
    <span class="hdr-date">Periode {format_id_date(selected_snapshot.get("date", selected_snapshot["name"]))}</span>
    <p>Mobile Collection Operations | Follow-up status monitoring across all GraPARI branches | 30H / 60H / 90H</p>
  </div>
</div>
""", unsafe_allow_html=True)



# ── Trend chart — main page (above tabs) ──────────────────────────────────────
st.markdown("---")
st.markdown("#### Tren Collection Rate 2026")

_BUCKET_COLORS = {
    "60-H": "#E30613",
    "90-H": "#2563EB",
}
_ALL_BRANCHES = ["Bandung", "Cirebon", "Soreang", "Tasikmalaya", "Jawa Barat"]
_ALL_BUCKETS  = ["60-H", "90-H"]

col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    selected_branch = st.selectbox("Branch", _ALL_BRANCHES, key="trend_branch")
with col_f2:
    selected_buckets = st.multiselect(
        "Bucket", _ALL_BUCKETS, default=["60-H", "90-H"], key="trend_bucket"
    )

if not selected_buckets:
    st.warning("Pilih minimal satu bucket untuk menampilkan grafik.")
else:
    df_trend = load_trend_data()
    df_filtered = df_trend[
        (df_trend["Branch"] == selected_branch) &
        (df_trend["Bucket"].isin(selected_buckets))
    ].copy()
    df_filtered = df_filtered.sort_values("Month")

    fig = go.Figure()

    for bucket in selected_buckets:
        color = _BUCKET_COLORS[bucket]
        df_b = df_filtered[df_filtered["Bucket"] == bucket]
        kpi_val = df_b["KPI"].iloc[0] if not df_b.empty else None

        fig.add_trace(go.Scatter(
            x=df_b["Month"].tolist(),
            y=df_b["Rate"].tolist(),
            mode="lines+markers",
            name=bucket,
            line=dict(color=color, width=2.5),
            marker=dict(size=7),
            hovertemplate="%{x}: %{y:.2%}<extra>" + bucket + "</extra>",
        ))

        if kpi_val is not None:
            fig.add_trace(go.Scatter(
                x=MONTHS,
                y=[kpi_val] * len(MONTHS),
                mode="lines",
                name=f"KPI {bucket} ({kpi_val:.2%})",
                line=dict(color=color, width=1.5, dash="dash"),
                opacity=0.55,
                hovertemplate=f"Target {bucket}: {kpi_val:.2%}<extra></extra>",
            ))

        fig.update_layout(
            title=dict(
                text=f"Collection Rate — {selected_branch}",
                font=dict(size=15, color="#1f2328"),
            ),
            xaxis=dict(
                title="Bulan",
                categoryorder="array",
                categoryarray=MONTHS,
                showgrid=False,
                tickfont=dict(size=12),
            ),
            yaxis=dict(
                title="Collection Rate (%)",
                tickformat=".2%",
                range=[0.95, 1.005],
                showgrid=True,
                gridcolor="#e5e7eb",
                gridwidth=1,
                tickfont=dict(size=12),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(size=12),
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60, b=40, l=10, r=10),
            hovermode="x unified",
            font=dict(family="-apple-system, 'Segoe UI', system-ui, sans-serif"),
        )

        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Tabs
tab30, tab60, tab90 = st.tabs(["Cek 30 Hari", "Cek 60 Hari", "Cek 90 Hari"])

with tab30:
    render_tab("30", selected_snapshot["urls"])

with tab60:
    render_tab("60", selected_snapshot["urls"])

with tab90:
    render_tab("90", selected_snapshot["urls"])
