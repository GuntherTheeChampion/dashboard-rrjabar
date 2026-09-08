# app.py — GraPARI West Java Collection Monitoring Dashboard
# Streamlit UI: tabs, filters, KPI cards, data table
# Entry point: streamlit run app.py

import base64
import html as _html
import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from data_loader import BUCKET_URLS, clear_all_cache, fetch_workbook
from data_processor import (
    COL_BRANCH, COL_MSISDN, COL_STATUS, COL_FOLLOWUP, COL_FU_STATUS,
    compute_followup_kpis, extract_customer_records, extract_summary_kpis,
)

# Page config — must be the first Streamlit call
st.set_page_config(
    page_title="GraPARI Collection Monitoring | West Java",
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
    padding-top: 165px !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
  }

  /* Sticky page header */
  .sticky-header {
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 999;
    height: 140px;
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
  .sticky-header .hdr-logo {
    position: relative;
    flex-shrink: 0;
    width: 72px; height: 72px;
    border-radius: 50%;
    border: 3px solid rgba(255,255,255,0.85);
    background: rgba(255,255,255,0.12);
    overflow: hidden;
    display: flex; align-items: center; justify-content: center;
    z-index: 1;
  }
  .sticky-header .hdr-logo img {
    width: 100%; height: 100%;
    object-fit: contain;
    border-radius: 50%;
  }
  .sticky-header .hdr-logo .hdr-logo-fallback {
    display: flex; align-items: center; justify-content: center;
    width: 100%; height: 100%;
  }
  .sticky-header .hdr-text {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }
  .sticky-header .hdr-text h1 {
    font-size: 1.15rem; font-weight: 700;
    color: #ffffff; margin: 0;
    letter-spacing: -0.01em;
    line-height: 1.25;
    text-shadow: 0 1px 3px rgba(0,0,0,0.25);
  }
  .sticky-header .hdr-date {
    display: inline-block;
    font-size: 0.7rem; font-weight: 700;
    color: #fff;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 999px;
    padding: 0.1rem 0.6rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-top: 0.15rem;
    width: fit-content;
  }
  .sticky-header .hdr-text p {
    font-size: 0.8rem; font-weight: 400;
    color: rgba(255,255,255,0.8);
    margin: 0;
    line-height: 1.4;
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
        delta="Target 98.20%",
        delta_color="off",
    )


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
        "Bandung": "https://docs.google.com/spreadsheets/d/15PQ_1X2ExOr6TVTDTTkkjyAfM1qywLp_/edit?gid=345541408#gid=345541408",
        "Cirebon": "https://docs.google.com/spreadsheets/d/15PQ_1X2ExOr6TVTDTTkkjyAfM1qywLp_/edit?gid=1877488003#gid=1877488003",
        "Soreang": "https://docs.google.com/spreadsheets/d/15PQ_1X2ExOr6TVTDTTkkjyAfM1qywLp_/edit?gid=1979635845#gid=1979635845",
        "Tasik":   "https://docs.google.com/spreadsheets/d/15PQ_1X2ExOr6TVTDTTkkjyAfM1qywLp_/edit?gid=20802915#gid=20802915",
    },
    "60": {
        "Bandung": "https://docs.google.com/spreadsheets/d/1Ksm2NdALwhYFmI0bXbHnCCUA2QLQeLj3/edit?gid=2140506757#gid=2140506757",
        "Cirebon": "https://docs.google.com/spreadsheets/d/1Ksm2NdALwhYFmI0bXbHnCCUA2QLQeLj3/edit?gid=1797628141#gid=1797628141",
        "Soreang": "https://docs.google.com/spreadsheets/d/1Ksm2NdALwhYFmI0bXbHnCCUA2QLQeLj3/edit?gid=1639254421#gid=1639254421",
        "Tasik":   "https://docs.google.com/spreadsheets/d/1Ksm2NdALwhYFmI0bXbHnCCUA2QLQeLj3/edit?gid=2112723004#gid=2112723004",
    },
    "90": {
        "Bandung": "https://docs.google.com/spreadsheets/d/1xVEObliWzzX-D2n2ZZmWQIDSXPL1JW45/edit?gid=1906827724#gid=1906827724",
        "Cirebon": "https://docs.google.com/spreadsheets/d/1xVEObliWzzX-D2n2ZZmWQIDSXPL1JW45/edit?gid=1694707041#gid=1694707041",
        "Soreang": "https://docs.google.com/spreadsheets/d/1xVEObliWzzX-D2n2ZZmWQIDSXPL1JW45/edit?gid=1805663529#gid=1805663529",
        "Tasik":   "https://docs.google.com/spreadsheets/d/1xVEObliWzzX-D2n2ZZmWQIDSXPL1JW45/edit?gid=99814949#gid=99814949",
    },
}


def render_tab(bucket_key: str) -> None:
    url = BUCKET_URLS[bucket_key]

    with st.spinner("Memuat data..."):
        sheets = fetch_workbook(url)

    if not sheets:
        st.warning("Data tidak dapat dimuat. Periksa koneksi atau URL Google Sheets.")
        return

    summary_kpis  = extract_summary_kpis(sheets, bucket_key)
    customer_df   = extract_customer_records(sheets)

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
st.markdown("""
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

  <!-- Logo circle -->
  <div class="hdr-logo">
    <img src="data:image/jpeg;base64,/9j/4QAYRXhpZgAASUkqAAgAAAAAAAAAAAAAAP/sABFEdWNreQABAAQAAAA8AAD/4QMraHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLwA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/PiA8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJBZG9iZSBYTVAgQ29yZSA1LjMtYzAxMSA2Ni4xNDU2NjEsIDIwMTIvMDIvMDYtMTQ6NTY6MjcgICAgICAgICI+IDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+IDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VSZWYjIiB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCBDUzYgKFdpbmRvd3MpIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOjFGQzdDMjU1ODI4NjExRURBOUZGREYwQUY2NzRBRDg0IiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOjFGQzdDMjU2ODI4NjExRURBOUZGREYwQUY2NzRBRDg0Ij4gPHhtcE1NOkRlcml2ZWRGcm9tIHN0UmVmOmluc3RhbmNlSUQ9InhtcC5paWQ6MUZDN0MyNTM4Mjg2MTFFREE5RkZERjBBRjY3NEFEODQiIHN0UmVmOmRvY3VtZW50SUQ9InhtcC5kaWQ6MUZDN0MyNTQ4Mjg2MTFFREE5RkZERjBBRjY3NEFEODQiLz4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7/7gAOQWRvYmUAZMAAAAAB/9sAhAAGBAQEBQQGBQUGCQYFBgkLCAYGCAsMCgoLCgoMEAwMDAwMDBAMDg8QDw4MExMUFBMTHBsbGxwfHx8fHx8fHx8fAQcHBw0MDRgQEBgaFREVGh8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx//wAARCAFiAo4DAREAAhEBAxEB/8QAxgABAAICAwEAAAAAAAAAAAAAAAcIBQYCAwQBAQEAAQUBAQAAAAAAAAAAAAAABQIDBAYHAQgQAAEDAgMEAwkKCAoLAQAAAAABAgMEBREGByExQRJREwhhcYGRIjKzFHShsUJScpKyIzU2YtJTg5MVNxjBgjNDc8PTlFUW0aJjJDRUZCVlVhcmEQEAAgECAgUJBwIFBAIDAAAAAQIDEQQFBiExUXESQWGxwSIychMzgZHR4VIUNKEjQpIVNRbwYlNzgiSissL/2gAMAwEAAhEDEQA/ALUgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABqc2pWX6XOz8oXDnoa90cctHPPypDUdYi+SxyLsdimGDsMeBanNWLeGUjXhmW23+fX2q66Tp1w2wuo4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAVf7T3VLnqi5FTrG0EfWYb8etfykZvfeh0XlGuu2tr1eL1Q92k+v1RbOpsmbpXVFv2R011di6WHgjZuL2fhb044puqwbvTosx+N8s665MEdPlr+Cx1PU09TBHUU8jZoJWo6OVio5rmruVFTeSMS0O1ZrOk9EuwPAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOMsscUT5ZXIyKNque9y4I1qJiqqq8ED2ImZ0hS3VDNLc052uV2icrqNz0holXZ9REnKxU+Vtd4SEzZPHaZdg4Nsf222rSfe6575amrcS2kZhIOl2sV7yVUMo5+euy892M1Eq+VFjvfAq+avFW7l7m8yMG5mnRPTDXuMcBx7qPFX2cvb2961mXMzWTMlqiulnqm1VJL8JvnNdxY9u9rk4opK0vFo1hzXc7bJgvNLxpaGTKlgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFftfNVlmdPlCyy/VNXku9SxfOX/AJdqpwT4fi6SN3e4/wANftdA5V4D1bnLHwR//X4fegZyYmBq3yYcVae6rc1cFaFuatgyVnrMOTbolfaJsGvwSqpH4rDMxF817fecm1C7jy2pPQjOI8Kxbqml46fJPlhbHT3UzL2drf11A/qK+JE9bt0ip1sa9KfGZjucnuEtizReOhzDiXCsu0vpePZ8k+SW3F1GgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACLNbNU25boHWS1SY32tZ5cjV/4aF2zn+W74Pj7+Hu9x4I0jrltnLPAf3d/mZI/tV//ACns7u1V96KrlcqqquXFVXaqqpEw6t4IjohwVoeaOKtPYUTVwVoW5q4q09UTV6bTdrnZ7jDcbZUvpK2BeaKeNcHIvvKi8UXYpXS81nWGLudrjy1ml41rK0GlOuFszUyK1XlWUOYURGtRV5YalU3rEq7nceTxYklg3UX6J6Jc14zy/k2szentYv6x3/ilQy2uAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANP1M1CocmWNah3LLdKnFlupMdrnpve78BmOK+LiWM+eMca+VNcD4PffZvDHRSPensj8ZVJudxrrpX1FwrpXT1lU9ZZ5XbVVzv4OCJwQg7WmZ1l2nbbamHHGOkaVrGjy4Hmq9o4Kh7qtzD5goU6OCtUKJq+KilSiauCtULdquGL2uR7VVrmqitcmxUVNqKioVQs2pExpKetJ+0C6JILHnKZXR+ZTXl29qbmtqf7T53SZ+33fkt97RONcsz05NvHfX8PwWCjkjljbJG5HxvRHMe1UVqou1FRU3oSDSJiYnSXIPAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAxOasz2vLNkqLtcpOSCFMGM+FJIvmxsTi5xbyZIpXWWZsNjk3WWMWONbT/TzyqHnDNl1zVfZ7tcX+VIvLBCi+RFEi+TG3vceldpBZcs3nWXcOFcLx7LDGOn2z2z2sJgWkjo+YHql8Vp68mpyjVT4XBzRCmYcVQqUaODkGq1aHBWoerc1dbkVCqFm1Ul6V613bKEkVtuXPXZdVcOpxxlp8V86FV+D0s3dGBlYNzNOieprHGeX6bnW+P2cv9J7/wAVprLe7Ve7bDcrXUsqqKdMY5o1xTuoqb0VOKKSdbRaNYc3z4L4rTS8aWh7SpaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOmtraWho5qyrlbDS07HSTSvXBrWNTFVU8mdI1lXjx2vaK1jW09EKn6oaiVWc72r2K6Kz0iq23067Nm5ZXp8Z/uJs6SE3G4nJPmdp5d4HXY4enpy296fVHc0vlMeWxvitPNHjiqHmpoYHrzQwDx85T154XFUGqiYdatPdVuauCtPVq0ODmlS1arqdsQ91WLQ27TTUu75HvCVEHNUWuociXC34+S9u7nZjsbI1Ny8dyl7DmmkoXi/CKbvH2ZI6p9XcuLZrxbrza6a6W6ZJ6KrYkkMreKLwXoVF2KnSTFbRMaw5Xmw2xXmlo0tD2Hq0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAVURMV2Im9QK262apfr6rfl6zy42alfhUzsXZUytXhhvjYu7pXb0ETutz4vZjqdW5S5e+RWNxlj+5b3Y/TH4yidNhgt40b7pRplLnS4yyVUjqezUStSqlZhzve7akTFXcuG1V4GRttv8yfNDWOZeYI2NIrTpy26uyI7ZWApNJtOaaBkLLDSyNYmHPK3rXr3XPequUlI2mKP8MOZZOYt9aZmct+nsnR3f/L9PP/XqH9C09/bY/wBMKP8AXt9/5r/e4SaV6dSMVi5fo0RyYKrY0avgVuCoJ2uP9MFeP76J1+bf72g5n0DoaGeO8ZVibVOpXpLJYa5VkhnY1cVja9y8yYpwcq98xcmyiJ1r90tk2POGTJWcO4nwxbo+ZXotXz6fgzuRrNpXm21OqoMtUdNW0z1huFvlhb1kEyb2riiYp0Lh7uKFzDjw5I1isI3iu54js8nhtmvato1raJ6LR2tj/wDlunX/AK7Q/oWl79tj/TCL/wBc3v8A5b/e+f8AyzTr/wBdof0LR+2x/pg/1ze/+W/3or7QmTcq2PLdsqbPa6egnkrerkkgYjFczqnu5Vw7qIYm8xUpWNI06W18o8Qz5894yXtaIrr0z54QI5CPb9MOtzSqFm0OtcD1Zsmvs25/fQXiTKVdL/uVxV0tu5l2MqUTFzE6EkamPyk7pnbTLpPhaVzVw3xUjPWPar73d+SypItCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAhjXPVL1CKXKtlmwrZW4XOpYv8lG5P5Fq/HenndCd1SP3m509mOtvnKPL3zbRuM0exHux2z290K+bCKdTALJ9m1rUyNWORPKdcZcV6cIYiW4f7k97kXPP82P/AFx6ZSuZ7TQAAAi28Qx5W1mtFfS/V0ebI5KWviRcGLPEicj8N2KqrU8fSYN48GaJjqt0S23bXnd8LyUt0228xavwz1wlIzmpAEN9p77p2lOP6w/qJDA3/ux3t15H/k3+D1wrcqEY6ZaHW5CpZtDqchVCzaHbQVtRQV1NXUzlZU0krJ4XpwfG5HN91CqJ0nVjbjFGSk0nqtGi9diutPd7LQ3WnXGCugjqI+9I1Hfwk3W2sauMZ8U472pPXWdHuPVoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANE1c1B/ylYUZRq1b1cOaOiau3q2p58yp+BimHd8JibvcfLr0e9LYeXOC/vc3tfSp02/D7fQqvUOmmmkmme6WaVyvkkevM5znLirnKu9VUgZt0u0Yq1pWK1jSIdKpgVwvavh6NzydqvmrKVrkttpbTLTSTOqHdfG57udzWtXBUe3ZgxC/i3VscaQ17inLW23uX5mSbeLTTon8md/eJ1D/J0H6B/9oXP9RydkI3/g2y7cn3x+B+8TqH+St/6CT+1H+o5OyHn/AAfZduT74/BLujud73m+w1tfd2wtngq1gjSnYrG8iRsftRzn7cXKZ+0z2yVmZ7Wj8zcJxbHPWmPXSa69PfLfTLa4hbtKzSwUeXp4XLHPDUyPikbsc1zWtVFRe4qEdxGdIr3t85EpF8uWto1rNOn72k0vaE1Dgpo4XOo6hzERqzSwO6x2HF3I9jce8hjRv8nmbFk5I2NrTMeOPNE/k7P3jNQfydv/AEEn9qe/6hk8yieRtl25Pvj8GoZ11AzLnCaGS8TMWOnRUgpoW8kTFd5zkbi5VcuG9VLGXPbJ1pnhfBNvsazGKJ1t1zPW1VyFMJC0ODkKoWbOlxVCxLgVLEre6A10lXpbaesXmdTungx/BZM/lTwNVCV2060hyrmLHFd5fTy6T/RIZfQgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA+Pc1jVe5cGtRVcq8EQPYjVUvUDMkuZ801lz51dS83VULF3Ngj2Nw+VtcvfNX3W58eSZ8jtfA9hG021aae11275/Dqaw6F3QWYumYu63w9wqi65F3V1Dugq8arxw5JC7oPPE8m8OSQr0DxPPG5JCeeJ54lheze3lyndE/8g70ERNcMn2J73LOeZ13VP8A1+uUtEk0pCvaZTG22L+nm+ghGcS92ve37kL62T4Y9KAVbtIqJdQcHFT1wcewos4KhXCzZ1OKlizpcXIY1nWo0WplbHs4tcmmFMq7nVVSqd7nw/gJTa+45dzN/Mt3R6EnmQ18AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAatqfdX23I11mjXCaaL1aLp5p1SPHwI5VMPf5fBhtP/XSl+Bbf5u8x1nqidfu6VYlpUTYibENSi7sMZHB1MvQVeNVGR1OplVdxVGRXGRx9VXoKvG9+Yeqr0Hvjg+YerL0Hnjg+Y+LT4cB41XjT32dWq3K1zT/AMgvoIjYOFz/AG573Medp13VPg9cpWJNpqF+0v8AZli9ol9GRnE/djvb7yH9bJ8MelAbkImJdPiXU5CpU63FSiXB24rhbs6XlULFnU8uQxrOpRKzK5ujlmfaNNbHSyIrZZIPWZGrvRal6zYL3kfgS+CulIci41n+bu72jq10+7obmXUWAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAI81uVy5XpIkXBJK1nMnTyxyKnuoQ3HJ0wx8TZuVYj9zM9lJ9MIRWldjgan8x0WMritIpVF1XzXxaPpQq8b35rgtJ3B8x7GQWkXoHzD5ritJ3Cr5ir5rqfTb9h741UZE3aAM5Mt3NOmuX0ERtHB5/tT3ud85TruKfB65SgSzUEM9pREW22L2ib0ZF8Un2Y7298ifWyfDHpQI9MCIiXTol0vQrhXEulxXA4O3FcLVnU7cVQsWdLyuGNdnMg5VnzRm63WaNqrFNKj6p3xaePypV+amCd1S5Sk2tEIni28jbbe1/Lp0d8rvRsZHG2NicrGIjWonBE2ITLj8zq+h4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANG1gpHz5agkamLYKtjn95zHs99yEHx+J+RrHks2DlvJ4dxMfqrPqlDyUq4Gl+NvvzIFpFKoyvfmPnqqj5j35j56qp58w+Y+eqKPmPfmOD6bA9i72MjyTQb9heiy9W6YtCm8uXbin/Wr6GM2/gk64p7/U0Tm+ddxT4PXKSSZamhvtIpjbrF7RN6MiuK+7He3rkX6uT4Y9KBZE2kRV02rzvQrhdh0u3lcDg5CuFFodTiuGPaHS5OHErhj36Fo9A9NpMtWR96ucKx3q6tTCN/nQU29jO45/nO8CcCT22HwxrPXLlfMvFv3OXwUn+3T+s9qVzKa0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGJzXbEueXq2kRMXuj54/lxrzt91DB4lt/m7e9fN6OlmcPz/ACs1bedCSU+zccv8boMXfFpu4e+OVfzHz1fuDxyfMfPVu4e+I+ZItOicD2LvYvLplgToLlbLlby8E8OzcZNZZNbJX0TbhYbin/Wr6GM3LgE/2Z+L1Q0nmr69fg9cpEJxq6G+0f8AZ9j/AKeb0aEVxX3a97eeRvrZPhj0oGlIerpsPNJsLkL0OpybSuHujg5CqFNodTkK1i0Jm0I0mS5VMWbL3Djb4HY2umemyaRq/wAs5PiMXzeldu5NuftMGvtS5/zVxzwa7fFPtf4p7PN+KxpJOdgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARVmyxLbbrIjGYU06rJAqbkRV2t/iqcx47sp22edI9i/TH4fY3Lhm7+bjjX3q9EsL1GJC+JJeNxWnKou9i7gsB74lXidb4iqJVRZ5po9heovVljqhplUllUlKOjKYWO4e2L6GM3Xl/6M/F6oaZzRP8Afr8HrlIJPNZQ52j/ALOsi/7eb0ZFcV92O9vPI31snw+tAsikPV06sPNIpchdh1KpXCtxcmKFSizfdI9L5c43ZamtR0dgonItW9MUWV+9IGL3fhLwTuqZe2wfMnp6mp8y8djZ4/BT61urzR2/gtbBBDTwxwQMSOGJqMjjamDWtamCIidwmIjRyG1ptMzPTMuZ6pAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAx19s0N1olgfg2VvlQyfFd/oXiRvFeHV3eGaT0W8k9ksrabmcN/FHV5UbVVBNSzvgnYrJI1wci++ncOSbnBkwZJpkjS0Nqx563jWJ63Q6FC34l+LOt0JXFlcWeeWNELtZXK2eKdmwyKSyKSxdUiIhk0ZlElaMzwrbLlTo761lS2RzePK+NGovjYpvHL1o+VaPO1Hmik/NpbyeH1pENgauiPtHU0jsv2mqRPIhrFY9ejrInYY+FpGcTrrSO9uvI94jc3r209cK+SrghDRDqdXlc7EuxC7Dieqmw5FyVc8332K2USckSYPrKpU8mGJF2u+Uu5qcVL2HFOS2kIbjPF8exwze3vf4Y7Z/661urBYbZYbRT2q2RJDR0zeVjU3qq7XOcvFzl2qpO0pFY0jqcR3e6ybjJOTJOtrMgVscAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAx15slNc4sHeRO1Pq5k3p3F6UIji3B8e8ppPReOq3Z+TJ226tino6uxodxtlTQTrDUM5Xb2uTa1ydKKct4hw/NtMngyR3T5J7mybfc1yxrDwvYYdbMqLPLMzeX6SvUl4KhuwyaSyqSxFW1DMozcUuWXc01mWrqldTN62NydXU06rgj48ccMeDk4KTfDt5bBbWOqetTxDh1d1i8E9E+SeyUr0GrmRamFHzV/qUmGLoqlrmKi9HMiK1fApt+LiWG8a66d7Sc3Lm8pOkU8XnjparqjqRp5dsp19njrHVtVOxFpvV43KjZmLzRuV7ka3BHJtwXHAo3O6xWpNddUzy/wAD32Lc0y+HwVienWfJ5fOrvI7pIiHVqw6CuFx7bNZrlerpT2u2wrPW1TkZExN3dc5eDWptVSqtJtOkdbF3u8x7fFOTJOlarcafZFt+TrDHb6fCWqkwkrqvDBZZcNvea3c1CewYYx10hxDjPFsm+zzkt0V/wx2R/wBdbZi8iQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA6K6hpa2BYKhiPYu7pRelFMXebLFuaTTJGsLmLLak61aJe7DPbZMdr6Zy+RL0dx3Qpy7jPA8mztrHtYp6p9Utj2m9rljsswk0exSHrKRpZjapmwyscsqlmHrG7FM/GkMTBVnEkKJHEwlXhtM3HKRxsPUb1M2rPox8pkVZNXyOOSSRsUbFfI9UaxjUVXOc5cERETeqqXIL3isTMzpELRaP6YRZUtn6wuEbXX+tanXO39RGu1IWr7r1TeveJna7fwRrPvS43zNx+d7l8FJ/s06vPP6p9SRjLauAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABxkjjljdHI1HscmDmqmKKhRfHW8TW0axL2JmJ1hpOYsqy0yOqaJHSUybXxb3M73Shz3jPLNsMzkwR4qeWPLHd2wn9jxGLezfontabVt3ms06E/SWErU2KSGKUliYCt3OJHHCTwsDVrv6DOx9CSxwxNRvUzas2kPDIXolk1TzoXpb6syLNt6iVKiROa1Ur08xjk/l3IvwnJ5nQm3jsmNnttPbt1+RzLm7mH5kztsU+xHvT2z2d0eVNpItAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGpZnyWyqZJVW1EZUri58G5r148vQvuGq8X5crl1yYfZv5Y8k/hKa2HFJpMVydNe3sRTdGSRPfFK1Y5WKqPY5MHIqcFRTUIx2pbw2jSYbrtrRaNY6Ya1Xv2O2klijoS+GGBqXopnUhJ0hip344mXVmVhI2jGmC5jr23y7Rf9jo3/VQvTZUyt4f0bF87pXZ0kpstt458U+61HmrmD9tT5GKf7tuuf0x+MrKoiIiIiYImxEJpygAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGt5vyVQ5gp1c1UprgxPqqlE3/gyJxT3iM3/DMe4jXqv2/ileGcVvtbfqp2fgr7mm13OzV0lFcoXQzsxwx2te347HfCapq2Ta2xW8NuiXTuG7nHuKRfHOsejzS1SomTaZNKpylXuyTlmbNOa6KzNVWRSuV9TInwYI/KkVO7hsTuqZ23w/MvFWLxjiEbPbWy+XqjvnqW7t9vo7dRQUNFE2Ckp2JHDExMEa1qYIhslaxEaQ4dmy2yWm9p1tPW9B6tgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYbNOU7NmW3OorlCjti9TO3ZLE74zHfwblLOfb0yxpaGdw/iOXaZPHjn7PJPerHqFp/fcn1ypVMWotkrsKW4MTyHfgvT4D+54iCz7S2Ke2HXeB8bw76vRPhyR11/Dtht/Zrp4pcy3aqcmMkFIxka9CSyYu+ghl8Nr7Uz5kHz5eYw46+SbT/AEj81hiYcwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPNcrbQXOiloa+BlTSTt5ZYZE5muQ8tWJjSV3DnvivF6TNbR1TDQck6Vz5OzrWV9sqWyZfraZ0awSKvXxSI9rmNxwwe3ztuOPvmLh23y7zMdUti4rzB++2taZI/vUt1x1TGn9JSOZbWAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAjTPGuViyzdJLVBSyXKtg2VPI5I443b+RXKjsXdOCGNl3MUnTrbXwjlLPvMfzJmKUnq165a1+83T/4A/8AvCfiFr99HZKX/wCA5P8Ayx/l/N7LX2lbFNUtjuNqnpIXLgs8b2zI1OlzcGL4iqN5Xyxox9xyJuK11petp7Opkc062y2F8E7bMlfZ61Ffb7pT1KLFM1N6L5GLHt+E1dpcybjw+TWGFw7ladzrX5ngy096k16Y/r0x52C/ebp/8Af/AHhPxCz++jslKf8AAcn/AJa/cy+Ude4cxZkobK2zup1rXqxJ1mRyNwarseXkTHzS5j3UWtpoweJcn32uC2ackT4fJolkymmAAABHGted7/lO1W2ps0kcctTUOjlWSNJEVqM5kwRd20x9zlmkaw2jlbhGHe5b1y66Vrr0Tp5Wl6f6+XupvtNbcyMhlpq2RsMdXEzq3RPeuDeZqLyuaqrgvQWcW6mZ0sn+Ncm4seGcm3mdaxrMT06wnO4zSQW+pmj2SRRPexV2pi1qqhmy55irFrxE+WYVkTX7UjD/AIqm/u7CN/d38zrcclbDst/mS9otnW/Zrstwq7zJHJNT1SQxLGxI05Ora7aib9qmZt8k3jWWjc0cKw7LPWmLXSa69PT5Uil9rIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAatqbf7lYMl191tr2srKfq+rc9qPanNI1q+SvcUtZ7zWkzCX4Fsse53dMWT3ba+hC1j7Q+cKavjfd2QV1Aqok0bI0ikRvFWOauGKdCoYVd5bXp6m/wC85H21sc/Jm1b+TWdYWLoaynraOCsp3c9PURtlif0seiOaviUkYnVyzJjmlprbrrOjvPVAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFJswSulv1zkkdzPfVzq5y71VZHEJPXPfL6B4fERt8cR+ivoY/FOkpZhieje9Peuvdlv+UZUWdktI+42yPaqx1lNgvkf0jfJXDeX8OtqzX7mrcdiNtnxbuOiYtFLeetu3uaQtPUIqo6J6KmxUVqoqL4ix4Z7GyfPxzHvR97ctHaSqfqRZXNherY5HvevKuDWpE7avQhe29Z8cdCA5ozU/YZPajp08vnhbMlnFgAAAhrtM/YNl9rk9EYe992O9vnIX8jJ8HrQTZPtu3+0w+kaYFJ6Y73SN79C/w29C6F4+ya72eX6Ck1PU4Dt/qV749KkKbiDfQ9epYjs0fdm7+3J6FhJbP3Z73Kue/wCVT4PXKYTLaOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGi63fs1u35n0zDH3X05bFyp/uGP7fRKqCrvIp2xcjTxVXIthx/5GD6CEzh9yO5wPjH8vL8dvS2EuI0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwLYLG5yudbqVXOVVcqwxqqqu1VXYeaL8brLH+O33yf5fsX+G0v6CP8UaH7vN+u33yqvrBBBBqNeIoI2xRNfHyxsajWp9UzcibCK3P1Jdm5WtNthjmZ1np9Msx2fEx1Ej7lJOv0ULmz99gc7T/wDR/wDnCziwwquKxtVV3rghJOReKe15rhXWu00kldWyxUdLEmMs8ioxqJ3/AOA8mdOtdxYsma0UpE2tPkhGF77R2VqSd0Nroqi5cuKdfsgjVe5zYuX5pi23lY6ult+z5H3WSNclq4/N1yxdN2mqVZMKqwyNj6Yp2ud4nNb75T+9jsZl+Qcmns5Y17ki5P1Nylmv6u21XJWonM6hnTq5kRN+CY4OT5KqZGPNW/U1biXAtzs+nJX2f1R0w2ouodDXaZ+wbL7XJ6Iw977sd7fOQv5GT4PWgiyfbVv9qh9I0wKe9He6PvfoX+G3oXRvH2TXezy/QUmp6nAtv9SvfHpUhTcQb6Hr1LEdmj7s3f25PQsJLZ+7Pe5Vz3/Kp8HrlMDnIiKqrgibVVTLaOie89ovLVBdKiip6Coroqd6xpVxOY2N6t2KrebbhjxMW27rE6N02nJO5y44vNq08Ua6TrrDvy1rtS5ivNPabbYat9TUO2uWSPlYxPOkevBrUPce5i06RErXEOUb7TDOXJlp4Y7+meyEpY4JiuwyWoNAzVrbkmwSyUzZnXKtj2OgpERzWqnB0qqjE8CqWL7ilZ08rZOHcq7zcxFvD4KT5bfh1tNk7TcPWfVWFyx8FdUIjvcYWP3sdifjkG+nTlj/AC/mzdh7ROUK+ZIblTz2pzlRElfhLFt6XM8pPmlym7pPX0I3e8k7vFGuOa5I83RP9UoUVbR1tLHVUczKimlTmjmicjmORehUMmJ1ajkx2paa2jS0eSXceqEWZk19s1iv9bZ57VUzSUMqwvmY+NEcqIi4oirjxMa+6rWdJht+w5PzbnBXLW9Yi0a6Tq3LLmfcs3+xy3qiq2spKZF9cSbCN0ComKpIirs2cdyl6mSto1jqQW+4TuNtm+VevtT1adOvc0C+9pDL1LUvhtNvmuLGLh6y9yQxuX8FFRzlTvohjW3lYnojVs2z5G3GSsTktWnm65dFr7S1mlnay5WielicuDpoZGzcvdVqoxfEeRvY8sSubjkPPWNcd62ns6ks2W+Wq926K42upZVUc3mSsXim9qpvRU4opmVtExrDStztcmC80yR4bQ0vOGt2UMuVMlFGr7ncI15ZIKbDkYqb0fIvk49xMSxl3NadHXKe4Xyru93EW08FJ8tvVDUGdpuDrfLsD0i6W1Cc3uswLP72OyU7PIN9Pqxr8P5t9yVq3lLNcjaWlldSXJyY+o1KI17sN/VuRVa/wLj3DIxZ636mtcU5d3WyjxXjxU/VHV9vY3QvIJ56+4UVvpJaytnZTUsLeaWaVyNa1E6VU8mdOlcxYrZLRWkTa0+SEW3ztG5Vo5nQ2ujqLly4os2yGNVT4vNi5U/imLbeVjq6W4bTkjdZI1yWrj83XLERdpuHn+usD0Z0sqEVfdYhT+9jslnW5Bvp0ZY/y/m3HK2t+Sb9NHSulfba6VUayGrRGtc5dzWyNVWY9/Au03NLdHUgeI8q7zaxNtPHSPLX8OtIBkNbcZJY4o3SSORkbEVz3uVEaiJtVVVQ9iJmdI60aZk1/wAmWqV1PQtlu87FVHOp8Gwoqf7R2/8Aiopi33dI6ultex5N3mePFbTHH/d1/c1pnabi6zy7A7q8eFQnNh4WYFv99HZKXnkG+nRljX4fzbplHWrJuY5o6TrXW6vkXBlNV4NRzuhkiKrFXubFL+Pc0t5pa/xPlfd7SPFMeOkeWv4N+QvtcaLrd+zW7fmfTMMfdfTlsXKn+4Y/t9EqoLxIqXbFyNPPuNYfYYPoITOH3I7nA+Mfy8vx29LYS4jQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACpes/7Sr18uP0LCJ3P1Jdr5U/2/H9vplmOzy3HUJV6KGdf9ZiFzZ+/Pcj+eJ/+lHxx61lq6tpqGjnrKqRIqanY6WaR25rGJiqkjM6OT4sdslorWNbWnSFS9RdQ7pnG7vlke6K1QOVKCix8lrd3O9OL3cV4bkInNmm8+Z2zgPAsexxR0a5Z963qjzOORtNMx5wle63sbBQwu5Zq6bFI0dv5W4Ji93cQ9xYLXe8Y5g2+x6L+1ef8Mdf29jbr32c8z0VC+pt9fBcpo05lpUa6J7sN/Iqq5FXuLgXb7OYjonVB7TnrBe8VyUmlZ8vX96K4Zauhq2ywvfTVdM/Fr24skY9q+NFRTE6Ylul6Uy00nS1LR9kwtRpFn92b8uq6rVEu1AqQ1qJs58U8iVE4c6Jt7pK4Mvjrq4xzJwf9luNK/Tv01/D7Gqdpn7Bsvtcnoi1vfdjvTfIX8jJ8HrQRZPtq3+1Q+kaYFPejvdI330L/AA29C6F4+ya72eX6Ck1PU4Dt/qV+KPSpFwIN9Dx1LEdmj7s3f25PQsJHZ+7Pe5Vz3/Kp8Hrl0666m+owSZVs82FZO3C5zsXbFG5P5JFT4T087oTvjdZtI8Mda5yhwD5to3OWPYr7sds9vdHpQFT089RPHT08bpZ5XIyKJiYuc5y4IiJ3SPiJ1dOyZK0rNrTpWFqdJ9OIcoWbrKlrX3utajq6VNvIm9IWL0N49KkrgxeCPO4vzFxy2+zez0Yq+7HrlHmuGqlW+tnytZJ1ipoPIudTGuDpH8YWuTc1vwuldhj7nPPuw2flLl2vhjc5o1mfdif/ANvwQvFG+RzY42q97l5WMaiqqqu5ERDBiOx0K9orGs9EQ26m0h1HqadKiOyTNY5OZqSOjjfh8lzkcXo21+xBZOaNhW3hnJH2RMtautnutoq3UdzpJaOpbtWKZqtXDpTHendQotSa9aX228xZ6+LHaLV8zatMtSrjk+6sa97prHO5EraTHFGov87GnBzfdLmHPNJ/7UJzBwCm+x6xGmavVPb5pWupamCqpoqmB6SQTMbJFI3c5jkxaqd9CW1cXvSa2ms9EwqNqn+0a/8AtbveQh9x9SXb+W/4GL4WvwXSup6GqoYZ3R0lb1frUTV8l/VKrmY95VKItMRMeSUrk2uO965LRramuk9mvWz9p0vz7dqJtbQ2eZ9LInNHI9Wx86dLUerVVC5XBeenRF7nmPY4b+C+SPF5unT7mAulpuVqrZKG5U0lJVxefDK3lcmO5e6i9KFu1ZrOkpTbbrHnp48dotWfLDJ5ezrmLL9vuVDa6lYYLnGkcyJji1fjs+K7lxbiVUyWrExHlYW/4Pg3V6XyV1nHP3+afM+5VyLmjNU0jbNSLM2Jfrqh7kZE1V24K93Fejee0xWt1POI8Z22yiPm20meqI6/uerNemecMr07aq7UaJSOVG+swvbLGjl3I5U2tx7qHuTDasays8N5h2u8t4Mdva7J6PuazDNNBMyaB7oponI+ORiq1zXNXFFRU3KhajVM5Mdb1mto1rK3WmGbJcz5NorlUf8AGNxp6xU4yxbFd/GTBxL4cnjrEuGcf4dGz3Vsce71x3ShbX3OdZcszPy/FIrbba+VHxN2JJUOajnOd08qLgnhMPdZNbeHsb/yZwqmPB+4mPbydXmr+bQ8r5UvmZ7mlutEHXVHKr3ucvKxjE2cz3LuTaY9KTadIbPxHiWHZ4/mZZ0j+s9zfp+znndlOj46qhllw2wpJI1fnKzAv/s7+ZrFOetrNumt4j7PxapXZDzXlu8UC3i3SQwrUxIlS3CSFV6xP5xuLU8JZnDato1jypjHxva7vFf5V4m3hno6p6uxb4mHEFa9adT6q93SewWyZWWWjesc7mLh6xK1cHYqnwGrsROO8jd1m8U+GOp1flTl6uHHGfLGuW3TH/bH4tFyrlG+ZpuSW+zwdbI1OeaVy8scTN3M93D31MfHjm06Q2XiXFMOyx+PLPdHlnuSTP2aswMpFkhu9LLVImKQqx7GKvQj9v0TK/ZT2tRpz7im2k47RXt1jX7kUXe03G0XGe3XGF1NW0zuWWJ29F3oqKm9F3oqGHekxOkt22m6x7jHGSk+Klk9aD6kVV2hflq7TLLW0kfPQVD1xfJC3Y5jlXe5nBejvEjtc02jSetzTnDgVdvaNxijSlp9qOyfzbRrd+zS7fmfTMK919OURyp/uGP7fRKqC8SKl2xcjTz7jWH2GD6CEzh9yO5wPjH8vL8dvS2EuI0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAqXrP8AtKvXy4/QsInc/Ul2vlT/AG/H9vplnOzq3HPsrvi0MvuvYXNn789yN56/h1+OPRKSu0Je5LfkZKKJytfdKhkD1T8k1Fkenh5UQyd3bSne1PkzaRl3sWnqx11+3qhWXEi3YJWKyrrDpdl/L1DaKaWpRlLE1r3JTu8qRUxe9e652KknTcY6xEauTb/lriW5zWy2rGtp/VH2Mr+8Dpz+Xqv7u4q/dY+1if8ADeIfpj/NCBdR7pYrvnCvuljVy0NYrZfLYsapKrU6zyV6XbSPz2ibax1Ol8A22fBtK483v11jt6PI2Xs/XWSjz+ykR2EVxp5Ynt4K6NOtb9FS7s59rvRPO22i+y8flpaP69Dee0z9g2X2uT0Rf3vux3td5C/kZPg9aCLJ9tW/2mH0jTAp70d7pG9+hf4LehdC8fZNd7PL9BSanqcB2/1K/FHpUiQg30NCUdPdQ4MnaeXdYVa+81tarKCFduH1LEWVyfFb7qmZizRTHPa0vjXBLb7iFInoxVp7U/bPR9qM6ipnqaiWpqZHS1EzlfLK9cXOc5cVVV7pia9rcceOuOsVrGlY6k+6G6XPoI2ZpvUKtrpW/wDbaaRMFijd/Ouau57k83oTvkhtcOntT1uY83cwfOn9vhn2I96e2ezuhKeaLt+p8uXO58aOmlmb8prVVvumVadImWnbHb/Oz0x/qtEKWyzSzSvmlcr5ZXK+Ry7VVzlxVfGQsz0voHHSKVisdUJ27O2TKJ1DUZpqo0kqXSup6BXJikbWYdY9MfhKq4Y9wz9njjTxeVzTnfit/mRtqzpWI1t55nqhN6Ga5+1HVDJdFmjK1VC+Nv6wpY3zW+fDymyMTHlx+K/DBULObFF66JrgPFL7Pc1tE+xadLR2x+Sou3jsUiHc1nez/fpblkZKOZyuktUzqZqrv6pUR7E8HMqErtba07nHecdnGHezaOrJHi+3qlBmqf7Rr/7W73kMDP8AUl0flv8AgYvhejSTLlNfs+W+jq2pJSxc1VPGu5zYU5kavcV2GJ7t6eK61zPv7bbZ2tXotb2Y+38ltmtRqIiJgibERNyISziWuqFe0xbKb9W2a6I1EqmzvpXORNro3sV6Iq/gqzZ3zB3sdET52/8AIWe3zcmP/DNfF9sTp60BLsTEwHTlwtNrDT2TJNpo4mI17oGT1CpvdLM1HvVfHgTOKvhrEOD8b3ltxu8l5/VMR3R1PXnahp63KF5pp280T6OZVTutYrmr4FTE9yRrWVjhma2Pc47V64vHpUxRdm0hY6nf1kezeq/5KrEXcldJh+jYSWy9z7XJeef5kfBHplEmstpqbdqJdlmaqMrXpVQOXc5kjU3d5yKhibmul587d+U9zXJsaRHXTol4tPs/XDJl3krqWFlTDUMSKqp3ry8zUXFFa5PNcinmHL4J1ZPHOC03+KKWnwzWdYlO9h18yHcmsbWSy2qd2xzKliqxF/pGcyYd/Az67qk+ZzXecn73DrNYjJX/ALfwb/TVVsulGktPLDW0cqbHMVssbuPDFC/ExLW748mK2lomto+yWH1DvT7Jkq73GNeWWKnc2Ff9pJ5DPdcUZbeGsyzeD7X9xu8eOeqbdPpU4IZ3uI0TZpTqRp3lHK7aWrkn/WlS90te5kDnJzYqjGo7ijW+7iZ+DNjpXTXpc65j4Hv97uZvWsfLr0V9qG6fvBac/l6r+7uL37vH2oD/AIbxD9Mf5oRHrNm3KmabrQ3KxukdO2J0Naskax4o12Ma7d+9yGJub1vpNW8cqcN3Wzx3x5o0rrrXp172s5Du0lpzlZq9i4dVVRtf3WSLyPT5rlLOKdLxKY43toz7TJSf0z/TphZHW79mt2/M+mYSW6+nLk/Kn+4Y/t9EqoLxImXbVyNPPuNYfYYPoITOH3I7nA+Mfy8vx29LYS4jQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACpes/7Sr18uP0LCJ3P1Jdr5U/2/H9vplsPZxbjneqd8Whk92RhXs/fnuRfPU//Ur8fqltnaZY79SWR6ea2plaq91Y0VPeL+8johCchWiM+SP+2PSgCKNZJWRoqNV7kajnbETFcMVI6HT720iZ7Elp2etQHIitdRKi7UVJ1wVPmGXO0v5moTzvso8l/u/M/d51B6aL9M78Q8/aX8x/zjZdl/u/M/d51B6aL9Mv4gjZW7YP+b7Lsv8Ad+baNNNGM15fzlRXi6LTeqUiSrhFKrnK90asbs5U+MXsO2mttZQvH+atvutrbFji3itp1x59Xu7TH2DZfa5PRHu992O9Z5C/kZPg9aCLJ9tW/wBqh9I0j6e9He6RvfoX+G3oXQvH2TXezy/QUm56nAdv9SvxR6VIiDfQ8dTLQ5Zuk+WpswwR9bQUtR6rVcu10aq1HNe78FebDHpK/lzNfF5EffiWOu5jb26L2r4o8/m73oyjmSmy/c2V01ppro6NyOY2q5/IVOLMF5ce65qnuO3hnXTVb4pw+26xzSuS2OJ/Tp09/lWuybnC05sskd0tzsEXyaincqdZDIm9j8PcXihLY8kWjWHFuJ8Ny7PLOPJHdPkmO2Hj1Qgkn09v8caYvWjkciJxRnlL7iFOWPYnuXuA3iu9xTP64U/Id3haLQOrhn05pY48OennnjlTjzK/nTxo5CU2vuQ4zzhjmu/tM/4oiY+5I5ktWee4VMNLQVNTMqNhhifJIq7ka1qqp5M6dK7ipNrxWOuZUhlej5HvRMEc5XIncVcSEfQ2KvhrEdkJ87MsMqWm+TLj1T6iFjejmaxVX6SGfsuqe9zLn60fOxx5fDPpRVqn+0a/+1u95DFz/UlunLf8DF8LaOzttz7Kq70oZcPnsLmz9+e5Ec8/w6/HHolZck3JUQdpb7q2r2/+peYe99z7W88h/wAq/wD6/XCuzvNUjpdUlduyfY1B7ND9BCbr1Q+eNz9W3xT6XTmj7tXb2Ko9E4W6pV7L69Pjr6VKU3IQcdT6FWR7N33Lrfbn+jYSez9z7XJeef5lfgj0y3HPWn9jzjb201wasdTDitJWx4dZEq79/nNXi1S9kxReOlAcJ4xm2OTxY+qeuJ6pQJmPQbPNqke+ihZdqRu1slOqJJh3YnKi4/JxMC+1vHV0ulbHnLZ5oiMkzjt5+r72gVtBXUM609bTyUs7d8UzHMd4nIhYtWY64bTh3GPLGtLRaPNOrKZTzlfsrXFlbaqhzExTr6ZVVYpW8Wvbu8O9D3HktSdYYXE+E4N5j8GSOnyT5YT7qRfIMy6K1F4omqkVSyCVzN6sVszUe1fkuRUJHLbxYpmOxzHge1tteLVxX662mP6TorMRbsCQrLofnS8WmlulE+jdS1kaSwq6ZUXldwVOXehk12trRrGjVd1zftcGS2O8X8VZ0noe393nUHpov0zvxCr9nfzLH/ONl2X+78z93nUHpov0zvxB+zv5j/nGy7L/AHfm9Nq7PueIbpRy1TqRKaOeN86smVXIxr0V2Ccu/BD2u0tExPQsbrnTaXxWrWL+KazEdH5pW1t/ZpdvzPpmGTufpy0zlT/cMf2+iVUV4kVLti5Gnn3GsPsMH0EJnD7kdzgfGP5eX47elsJcRoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABUvWf9pV6+XH6FhE7n6ku18qf7fj+30y2Ts3pjnGuXooXekYXNn789yK58/i0+P1SlrWDK8uYsjVlPTsWStpFbV0rUTFXOix5mp8piuQzNxTxUmIaPy1xCNrvK2tOlbezP2/mqZwwXwoRHW7fHTCfdMddLS2109nzRK6mqaZrYobiqK6ORjUwb1mGKtcibMdykhh3UaaWcw4/wAoZYyTl28eKtunw+WJ83bCTmZ8yU+PrG32hVnT18ae+plfMr2tQtwndROk4r6/DLXMx64ZDs8Tkp6tbpVInkwUiczcfwpFwYnjUt33FI86W2PKe9zz01+XXtt+HWyOl2cq7N+X57vVwx06+tywwwx4qjY2NYrUVy+cvlLip7hyeOurE49wuuxzxirPi9mJmfPLSu0z9g2X2uT0RZ3vux3ti5C/kZPg9aCLJsvVv9ph9I0j69cd7pG9+hf4LehdC8fZNd7PL9BSbnqcB2/1K/FHpUiQg30NHUsH2c6anqsn3umqY2zU81YscsT0xa5roGIqKhI7OPZ+1y7njJam8x2rOlop0ffKONVtNqjJ9262mR0ljrHKtHMu1Y3b1hevSnwV4oY+4w+DpjqbZy1x6N7i8Np/vV6/P549bFZAz3csn3xtfTYy0kuDK6jxwbLHjw6Ht3tUt4cs0nVm8b4Nj32Hwz0Xj3bdk/gtbb7lZ8z5fbVUciVFtuMLm48eV6K1zXJwcm5UJaJi0eZxXNhy7XN4bR4b0lUPNeXKvLmYK2z1TVR9NIqRuX4cS7Y3p3HNIfJSazpLufC9/TdYK5a+WOnzT5YbHpbqXPku4ysnjdU2esVPWoGL5bHN2JLHjsxTcqcULuDN4O5Fcx8Ajf0iaz4cteqe3zSnul1h04qKZKj9dRRJhisUqPZInc5VTHHvGfG4p2uaZOWd/S3h+Vae7phGOq+ttFeLZLYct87qao8msr3orOZmO2ONq+Vg7i5TGz7mJjSrbuXOVMmHJGbcdE192vn7ZQy1iuVGtRXOVcEam1VVdyIYMOgzMRGs9S2+lGVJcs5Lo6Koby10+NTWN4pJLgvKvyWojSXwU8FIhw7mHiMbvd2vX3Y6I7oVw1T/AGjX/wBrd7yEduPqS6vy3/AxfC2js6/fyb2GX6bC5s/fnuQ/PP8ADr8ceiVlyTclRB2lvuravb/6l5h733I7288h/wAq/wD6/XCuq+YpHS6pK7lk+xqD2eL6CE3Xqh877j6lvin0unM/3au3sVR6Jwt1SubL61Pjr6VKU3IQcdT6FWR7N/3Lrfbn+jYSey9z7XJeef5kfBHplkKvWS12bPFxy5fm+rUsLo/U7gxFc1EfG1ytmRNqbV2OTwlc7iK3mssPHyzlz7Sm4w+1M6617p8n4N9oLta7jCk1BVw1UTkxR8MjXp/qqpfiexrmbb5MU6XrNZ88NY1UblFco17swthXlhf6pz8vXddy/V9T8Lm5sN3hLWfw+HpS3L87mNzSMGvXGvZp5dVSCIdyWV0qsDrroytqqk5Y7i2rbGruCPe5GO8DkxJTBXXFp2uQ8xbz5PFvm1/wTX+kdKuVwoKu3V9RQVkaxVVLI6KaNd6OYuCkZMTE6S6xts9M2OMlJ1raNYSjpFrDT5bpf1HfUe61cyvpapiK90CvXFzXN3qxV27Nxl7fceHot1NM5m5Xtub/AD8H1PLXt8/em+k1DyNVxJLDfaJWrt8qZjF8LXKioZ0ZKz1TDnmXhG7pOlsV/uY296wafWiNXSXWOqlTdBSfXvX5vkp4VKLZ6V65Ze05b3ueejHNY7bdEMfptqfUZ2vF2YykSkt1EyJaZqrzSuV7nIrnqmxN25CnFn8cz0dTJ47wCOH4sczbxXvrr2eTqenW39ml2/M+mYNz9OVHKv8AuGP7fRKqC8SKl2xcjTz7jWH2GD6CEzh9yO5wPjH8vL8dvS2EuI0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAArLr9lmuoM5SXhYnLb7myNzJ0TyUlY1GPYq8F8lFQjN1SYt4vJLrXJfEKZNr8nX26TPR5p6dXi0KvkNr1Apo53oyK4xPpMV3c7sHR+NzcPCebW8RfvZPOO0nLspmOukxb7PKtOSjjiDdU9Damoq5r3lWNrnSqslXa0waqvXar4cdm3i3xGFn22s61dC5e5ujHWMO5nojqv6p/FCFbQ1tDUOpq2nkpahi4OimarHIqdxyIYExMdbo2DcY8seKlotE9jz7CnWF7R7rVZbvdp209sopqyZy4IyFjn+NU2J4SqtZnqhi7ne4cFfFktWseeVotG8rXjLWTkoLvG2GrkqJKjqmuR/K17WoiOVNmPk8CV29JrXSetxzmfiGLd7ucmKda+GI+5jNfctV95yfHUUMTpprZP6w+JiYuWJWq16onHlxRSndUm1OjyMvk/iFNvu9LzpXJXTXz+RWWGV0M0czFwfE5Ht77VxQi9XXr1i9ZjyTC5cF1gu+T/1nTuSSKsoVlaqbdrolxTwLsJvXWNXAr4Jw7n5c9db6f1U0SCbD+Td81SE0d8rlrp1wsN2a2Oblm7I5qtX15N6YfzLCS2fu/a5bz1aJ3VNP0euUn5gsNsv1oqLVcokmpKlvK5OLV+C9q8HNXaimTaImNJajtN3k2+SMmOdLVVUztptmPKtylhmppKm3q5Vpa+NiujezhzcuPK7pRSKy4LUnzOz8I5g2+8xxPiiuTy1n1dsMnpTqLXZPunUVbJZbFWOT1uJGuVYnbuuYnSnwk4oV4M3gnp6mDzLwTHvcfipMfOr1T2+afUnDUDTuy59tENVBM2K4Mj5rfcWJzNcxycyNfh5zF8aGdlxRkhz3gvG83DssxMa0mfar+HnVzzNp/m3Lc7o7nb5EiRfJq4kWSBydKPbu7y4KRl8VqdcOrcP47td1GtLxr2T0S1tVTHeWtUvrD32mw3u8TthtdDPWSuXBEhY5yeF3mp4VK60tbqhibrf4MEa5L1rHenjS3RD9T1MV7zIjJrhFg+loWqj44XcHvXc56cMNiGfg23h6Z63NuYebP3EThwaxj8tvLP4QmIzGjKh6pRSrqLf1RjlRat2C4L0IRG4+pLt/LeSsbDF0x7rZuztHI3PkyuY5E9Rl2qip8Nhc2fvz3Ijni8Ts40n/HHolZYk3J0P9pdUTKtq9v8A6l5h733I7288h/yr/wDr9cK7K5vKu0jZl1SZXcsn2NQezxfQQna9UPnjcfVt8U+l05nT/wDNXbD/AJOo2fmnHluqVez+tT46+lSzqJ8E+rd81SDjqfQPza9sLH9nFr25LrUc1Wr68/YqYfzbOkk9n0U+1yfni0TvI0/RHplputGm2bZs0VuYaKjdXW6q5F/3fF8kfJGjV5408r4O9MSzucFpt4o6k9yrx7a029cF7eC9devqnp7UTKtZRSq1espZk2KnlRu/gUxNJhu/9vLGvs2j7JcXzT1UidY988m5vM5Xu8GOKniqtKUjoiKx9zd8jaQZozLVxSVFNJbrQios1ZO1WOc3ikTHYK5V6dxkYtvN56eiGucY5p2+1rMUmMmXyRHrlaO122jtlvp7fRRpFSUsbYoY04NamCEpERHQ49nzXy3m951tadZRzqvo/FmlVu1oVlPfWNRJGv8AJjqGtTYjl+C9NyO8Zj59v4+mOttHLnM1tl/aye1hn7693m8yu95sF6slS6lu1FLRzNXDCVqoi/Jd5rk7ykbelq9cOq7Tf4NxXxYrxaGO2FHQzHbSUdVWTJBSQPqJnbo4mq9y+BqKpVWuvUtZc1Mca3mKx550WF0FyRmXL7blW3il9TZXMibTwvVOt8hXKquamPLv47SR2uK1YmZ8rlnOXF9vuppTFbxeDXWfJ0t71Fy/UX/Jd0tVNtqpouanauzGSNyPa3wq3Av5qeKsw13g28rtt3TLb3Ynp7p6FPZ4J6eeSCojdFPE5WSxPRWua5N6Ki7iGnsnrd3x5K3rFqzrWVsdHL1TXTT61LFIj5aKP1Spbxa+LZgvfbgpL7e0TSHEuZdrOHfZInqtPij7W6l5AgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHTV0dJWQOp6uFlRA/wA+KVqPYvfa7FBMK8eS1J8VZmJ8zHUGT8q2+br6G0UlPMi4pLHCxHIvcXDFCnwR2MnLxHcZI0vkvMd8suVMMA8tdabXcGIyvpIatqbkmjbJh3uZFPJiJ613DnyY51paa906MU3T/JDZOsbYqFH4449Qz/QU/Lr2MyeLbuY0nLf/ADSzNJRUdHEkNJBHTxJujia1jfE1EK4jRg5MlrzraZmfO7goAMLNkrKE9UtXNZqN9Sq4rK6CNVVeldhT4I7GbXiW5rXwxkvEfFLLxQQxRNiiY2OJqYNjaiNaidCImwqYdrTM6z1viU8H5NvzUGj3xz2uTY2M2NajUXoTAPJmZcg8FTEDrWng/Jt+ah5oq8c9rm1qNREamCJuRD1SK1FRUVMUXegHhfYLE93O+3Ur3rtVzoY1XHv8p5oyK7vNEaRe33y9cNPBBGkcEbYo03MYiNangQ9WLWmZ1mdXYHgBwWCFVVXMaqrvVUQPYtMeV9bFE1cWsRq9KIiDQm0y5BS6Kygoa1jWVlPFUsavM1szGvRF3YojkU8mNV3HlvSdazNe6dHl/wAtZd/wuk/QRfinngjsXv32f9d/80sg1qNajWojWtTBETYiIhUxZFTFMOAHD1eH8m35qDRV4p7XJrGtTBqI1OhEwCmZmXLAPNHmqbbbqpUWqpYahU3LLG1/0kU8mF2ma9PdmY7pcKey2emkSSnoaeGRNz44mMXxoiCIhVfc5bdFrWn7ZezA9WQAB01VHSVcSw1UEdREu+OVqPb4nIqHmiumS1J1rMxPmYWTT/JD5OsdYqJX9PUM/wBB54K9jNji27iNIy3/AM0srQWi1W5isoKOGkau9IY2x49/lRD2IiOpi5dxkyTre02751es9WTADE3LKeWbpOk9xtdLVzp/OyxMc7Z0uVMVKZrHYy8O/wA+KNKXtWPNMvfRUFDQwpBRU8dNCm6OFjWN8TUQ9iIhYyZbXnW0zafP0u89WwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/9k=" alt="Telkomsel" style="display:block"/>
  </div>

  <!-- Text content -->
  <div class="hdr-text">
    <h1>Telkomsel Region West Java &mdash; GraPARI Collection Monitoring Dashboard</h1>
    <span class="hdr-date">Periode 31 Agustus 2026</span>
    <p>Mobile Collection Operations &nbsp;|&nbsp; Follow-up status monitoring across all GraPARI branches &mdash; 30H / 60H / 90H</p>
  </div>
</div>
""", unsafe_allow_html=True)

# Refresh button
rcol1, rcol2 = st.columns([9, 1])
with rcol2:
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
    if st.button("Refresh Data", type="secondary",
                 help="Loading ulang untuk update data terbaru"):
        clear_all_cache()
        st.rerun()

# Tabs
tab30, tab60, tab90 = st.tabs(["Cek 30 Hari", "Cek 60 Hari", "Cek 90 Hari"])

with tab30:
    render_tab("30")

with tab60:
    render_tab("60")

with tab90:
    render_tab("90")
