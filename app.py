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
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
  }

  /* Page header */
  .page-header {
    padding: 1.25rem 1.5rem;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 4px;
    margin-bottom: 1.5rem;
  }
  .page-header h1 {
    font-size: 1.35rem; font-weight: 700;
    color: var(--text-primary); margin: 0 0 0.25rem 0;
    letter-spacing: -0.01em;
  }
  .page-header p {
    font-size: 0.85rem; color: var(--text-secondary); margin: 0;
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


# Follow-up status cards — 2 inline cards from filtered customer records
def render_followup_cards(fu_kpis: dict) -> None:
    ca, cb = st.columns(2)
    ca.metric("Followed Up",       f"{fu_kpis['followed_up']:,}")
    cb.metric("No Follow Up Yet",  f"{fu_kpis['no_followup']:,}")


# HTML table with find bar
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

    html_src = f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  :root {{
    --text:#E5E7EB; --text-muted:#9CA3AF; --border:#4B5563;
    --border-table:#374151; --bg-input:#262B38; --bg-thead:#1A1D27;
    --bg-row-hover:rgba(255,255,255,0.04); --row-divider:#262B38; --accent:#E30613;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --text:#111827; --text-muted:#6B7280; --border:#9CA3AF;
      --border-table:#D1D5DB; --bg-input:#FFFFFF; --bg-thead:#F9FAFB;
      --bg-row-hover:rgba(0,0,0,0.02); --row-divider:#E5E7EB; --accent:#E30613;
    }}
  }}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:"Segoe UI",system-ui,-apple-system,sans-serif;font-size:13px;background:transparent;color:var(--text);}}
  #toolbar{{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px;flex-wrap:wrap;}}
  #find-bar{{display:flex;align-items:center;gap:6px;flex:1 1 auto;}}
  #action-btns{{display:flex;align-items:center;gap:4px;flex-shrink:0;}}
  .icon-btn{{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;
    border:1px solid var(--border);border-radius:4px;background:var(--bg-input);color:var(--text);
    cursor:pointer;text-decoration:none;transition:border-color .12s,color .12s;flex-shrink:0;}}
  .icon-btn:hover,.icon-btn.active{{border-color:var(--accent);color:var(--accent);}}
  #find-input{{flex:0 0 220px;padding:5px 10px;font-size:12px;font-family:inherit;
    border:1px solid var(--border);border-radius:4px;background:var(--bg-input);color:var(--text);outline:none;}}
  #find-input::placeholder{{color:var(--text-muted);opacity:1;}}
  #find-input:focus{{border-color:var(--accent);}}
  #find-counter{{font-size:11px;color:var(--text-muted);min-width:52px;text-align:center;}}
  .find-btn{{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;
    border:1px solid var(--border);border-radius:4px;background:var(--bg-input);color:var(--text);
    cursor:pointer;font-size:13px;line-height:1;transition:border-color .12s,color .12s;}}
  .find-btn:hover{{border-color:var(--accent);color:var(--accent);}}
  .find-btn:disabled{{opacity:.35;cursor:default;}}
  #btn-clear{{font-size:15px;font-weight:600;}}
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
  col.col-status{{width:110px;}} col.col-hasifu{{width:auto;}} col.col-statusfu{{width:130px;}}
  td.row-num,th.row-num{{width:46px;text-align:right;color:var(--text-muted);
    font-size:11px;padding-right:12px;white-space:nowrap;user-select:none;}}
  mark{{background:#FDE68A;color:#1A1A2E;border-radius:2px;padding:0 1px;}}
  mark.active-match{{background:#F59E0B;color:#1A1A2E;outline:2px solid #D97706;border-radius:2px;}}
</style>
</head>
<body>
<div id="toolbar">
  <div id="find-bar">
    <input id="find-input" type="text" placeholder="Cari di tabel..." autocomplete="off"/>
    <span id="find-counter"></span>
    <button class="find-btn" id="btn-prev" title="Sebelumnya (Shift+Enter)" disabled>&#8593;</button>
    <button class="find-btn" id="btn-next" title="Berikutnya (Enter)" disabled>&#8595;</button>
    <button class="find-btn" id="btn-clear" title="Hapus" style="display:none">&#215;</button>
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
  const COL_CLASS_MAP={{
    "Branch":"col-branch","MSISDN":"col-msisdn","Status":"col-status",
    "Hasil Follow Up":"col-hasifu","Status Follow Up":"col-statusfu"
  }};
  const colgroup=document.getElementById("t-cols");
  const cn=document.createElement("col"); cn.className="col-num"; colgroup.appendChild(cn);
  COLS.forEach(c=>{{const col=document.createElement("col");if(COL_CLASS_MAP[c])col.className=COL_CLASS_MAP[c];colgroup.appendChild(col);}});
  const thead=document.getElementById("t-head");
  const tbody=document.getElementById("t-body");
  const hrow=document.createElement("tr");
  const thN=document.createElement("th"); thN.textContent="#"; thN.className="row-num"; hrow.appendChild(thN);
  COLS.forEach(c=>{{const th=document.createElement("th");th.textContent=c;hrow.appendChild(th);}});
  thead.appendChild(hrow);
  ROWS.forEach((row,ri)=>{{
    const tr=document.createElement("tr");
    const tdN=document.createElement("td"); tdN.className="row-num"; tdN.textContent=ri+1; tr.appendChild(tdN);
    row.forEach(val=>{{const td=document.createElement("td");td.dataset.orig=val;td.textContent=val;tr.appendChild(td);}});
    tbody.appendChild(tr);
  }});
  const input=document.getElementById("find-input");
  const counter=document.getElementById("find-counter");
  const statusBar=document.getElementById("status-bar");
  const btnPrev=document.getElementById("btn-prev");
  const btnNext=document.getElementById("btn-next");
  const btnClear=document.getElementById("btn-clear");
  let matches=[],cursor=-1;
  function escRe(s){{return s.replace(/[.*+?^${{}}()|[\\]\\\\]/g,"\\\\$&");}}
  function escHtml(s){{return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}}
  function clearHL(){{document.querySelectorAll("#t-body td").forEach(td=>{{td.textContent=td.dataset.orig;}});matches=[];cursor=-1;}}
  function applySearch(q){{
    clearHL();
    if(!q){{counter.textContent="";btnPrev.disabled=btnNext.disabled=true;btnClear.style.display="none";statusBar.textContent="Showing {n_rows:,} records";return;}}
    btnClear.style.display="";
    const re=new RegExp(escRe(q),"gi");
    document.querySelectorAll("#t-body td").forEach(td=>{{
      const orig=td.dataset.orig; if(!orig)return;
      const mArr=[...orig.matchAll(re)]; if(!mArr.length)return;
      let html="",last=0;
      mArr.forEach(m=>{{html+=escHtml(orig.slice(last,m.index))+"<mark>"+escHtml(m[0])+"</mark>";last=m.index+m[0].length;matches.push(td);}});
      html+=escHtml(orig.slice(last)); td.innerHTML=html;
    }});
    if(!matches.length){{counter.textContent="0 hasil";btnPrev.disabled=btnNext.disabled=true;statusBar.textContent='Tidak ada hasil untuk "'+q+'"';return;}}
    cursor=0; activateCursor();
  }}
  function activateCursor(){{
    document.querySelectorAll("mark.active-match").forEach(m=>m.classList.remove("active-match"));
    if(!matches.length)return;
    const allMarks=[...document.querySelectorAll("#t-body mark")];
    if(cursor<0)cursor=allMarks.length-1; if(cursor>=allMarks.length)cursor=0;
    const el=allMarks[cursor];
    if(el){{el.classList.add("active-match");el.scrollIntoView({{block:"nearest",behavior:"smooth"}});}}
    counter.textContent=(cursor+1)+" / "+allMarks.length;
    btnPrev.disabled=btnNext.disabled=allMarks.length<=1;
    statusBar.textContent=allMarks.length+" kecocokan ditemukan";
  }}
  function normQ(s){{return s.replace(/[\u00A0\u200B\u200C\u200D\uFEFF]/g,"").trim();}}
  input.addEventListener("input",()=>applySearch(normQ(input.value)));
  btnNext.addEventListener("click",()=>{{cursor++;activateCursor();}});
  btnPrev.addEventListener("click",()=>{{cursor--;activateCursor();}});
  btnClear.addEventListener("click",()=>{{input.value="";applySearch("");}});
  input.addEventListener("keydown",e=>{{if(e.key==="Enter"){{e.preventDefault();if(e.shiftKey)cursor--;else cursor++;activateCursor();}}}});
  const btnCompact=document.getElementById("btn-compact"); let compact=false;
  btnCompact.addEventListener("click",()=>{{compact=!compact;document.querySelectorAll("#t-body td").forEach(td=>{{td.style.padding=compact?"3px 12px":"";}});btnCompact.classList.toggle("active",compact);statusBar.textContent=compact?"Tampilan ringkas aktif":"Showing {n_rows:,} records";}});
  const btnCopyAll=document.getElementById("btn-copy");
  btnCopyAll.addEventListener("click",()=>{{
    const tsv=COLS.join("\\t")+"\\n"+[...document.querySelectorAll("#t-body tr")].map(tr=>[...tr.querySelectorAll("td[data-orig]")].map(td=>td.dataset.orig).join("\\t")).join("\\n");
    navigator.clipboard.writeText(tsv).then(()=>{{btnCopyAll.classList.add("active");setTimeout(()=>btnCopyAll.classList.remove("active"),1200);}}).catch(()=>{{}});
  }});
}})();
</script>
</body></html>"""

    component_height = min(46 + 33 * n_rows + 90, 640)
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


# Page header
st.markdown("""
<div class="page-header">
    <h1>Telkomsel Region West Java &mdash; GraPARI Collection Monitoring Dashboard</h1>
    <p style="margin-top:0.25rem;font-size:0.78rem;color:var(--text-muted);letter-spacing:0.03em">Periode 31 Agustus 2026</p>
    <p style="margin-top:0.5rem">Mobile Collection Operations &nbsp;|&nbsp; Follow-up status monitoring across all GraPARI branches &mdash; 30H / 60H / 90H</p>
</div>
""", unsafe_allow_html=True)

# Refresh button
rcol1, rcol2 = st.columns([9, 1])
with rcol2:
    if st.button("Refresh Data", type="secondary",
                 help="Ambil data terbaru dari Google Sheets. Tunggu ~1-2 menit setelah mengedit sheet."):
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
