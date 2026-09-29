import os

app_path = r"c:\Users\Guntur Ananta\Downloads\dashboard-rrjabar\dashboard-rrjabar-50dc2c5872b3f0c770a77d26e269922e3fae93e9\app.py"
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace 1: Imports
content = content.replace(
    "from data_loader import BUCKET_URLS, clear_all_cache, fetch_workbook",
    "from data_loader import clear_all_cache, fetch_workbook\nfrom snapshot_manager import load_snapshots, save_snapshot"
)

# Replace 2: UI for snapshot management (right before global CSS)
# Actually, better place is after global CSS, before render_kpi_cards
helper_idx = content.find("# Helpers")
ui_logic = """
snapshots = load_snapshots()
if not snapshots:
    snapshots = [{"id": "default", "name": "16 September 2026", "urls": {"30": "", "60": "", "90": ""}}]

st.sidebar.markdown("### 🗂️ Manajemen Periode Data")
selected_snapshot_name = st.sidebar.selectbox("Pilih Periode", [s["name"] for s in snapshots])
selected_snapshot = next(s for s in snapshots if s["name"] == selected_snapshot_name)

with st.sidebar.expander("➕ Tambah Periode Baru"):
    new_name = st.text_input("Nama Periode (e.g., 1 Oktober 2026)")
    new_30 = st.text_input("Link Spreadsheet 30H")
    new_60 = st.text_input("Link Spreadsheet 60H")
    new_90 = st.text_input("Link Spreadsheet 90H")
    if st.button("Simpan & Update"):
        if new_name and new_30 and new_60 and new_90:
            save_snapshot(new_name, new_30, new_60, new_90)
            st.rerun()
        else:
            st.error("Semua field harus diisi!")

"""
content = content[:helper_idx] + ui_logic + content[helper_idx:]

# Replace 3: render_tab signature
content = content.replace(
    "def render_tab(bucket_key: str) -> None:\n    url = BUCKET_URLS[bucket_key]",
    "def render_tab(bucket_key: str, urls_dict: dict) -> None:\n    url = urls_dict.get(bucket_key, \"\")"
)

# Replace 4: Header date injection
content = content.replace(
    "st.markdown(\"\"\"\n<div class=\"sticky-header\">",
    "st.markdown(f\"\"\"\n<div class=\"sticky-header\">"
)
content = content.replace(
    "<span class=\"hdr-date\">Periode 16 September 2026</span>",
    "<span class=\"hdr-date\">Periode {selected_snapshot['name']}</span>"
)

# Replace 5: render_tab calls at the bottom
content = content.replace(
    "with tab30:\n    render_tab(\"30\")",
    "with tab30:\n    render_tab(\"30\", selected_snapshot[\"urls\"])"
)
content = content.replace(
    "with tab60:\n    render_tab(\"60\")",
    "with tab60:\n    render_tab(\"60\", selected_snapshot[\"urls\"])"
)
content = content.replace(
    "with tab90:\n    render_tab(\"90\")",
    "with tab90:\n    render_tab(\"90\", selected_snapshot[\"urls\"])"
)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("app.py patched successfully")
