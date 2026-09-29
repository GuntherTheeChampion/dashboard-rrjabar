import os
import re

app_path = r"c:\Users\Guntur Ananta\Downloads\dashboard-rrjabar\dashboard-rrjabar-50dc2c5872b3f0c770a77d26e269922e3fae93e9\app.py"
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# We want to replace everything from `import datetime` to `st.rerun()"""` (which was our previous logic)
# Let's find the boundaries.
start_str = "import datetime"
end_str = "st.rerun()"

# Wait, we know the exact previous UI string since we wrote it. Let's just use regex or find to replace the block.
start_idx = content.find("import datetime\nsnapshots = load_snapshots()")
end_idx = content.find("st.rerun()", start_idx)
if start_idx != -1 and end_idx != -1:
    old_block = content[start_idx:end_idx + len("st.rerun()")]
    
    new_ui = """import datetime

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
    snapshots = [{"id": "default", "name": "16 September 2026", "date": "2026-09-16", "urls": {"30": "", "60": "", "90": ""}}]

date_map = {s.get("date", s["name"]): s for s in snapshots}

with st.expander("🗂️ Manajemen Periode Data", expanded=False):
    colA, colB = st.columns([1, 1])
    with colA:
        st.markdown("**Pilih Periode Aktif:**")
        # DROPDOWN UNTUK PAST DATA
        display_names = [format_id_date(s.get("date", s["name"])) for s in snapshots]
        selected_display = st.selectbox("Periode", display_names, label_visibility="collapsed")
        selected_idx = display_names.index(selected_display)
        selected_snapshot = snapshots[selected_idx]
        
    with colB:
        st.markdown("**➕ Tambah / Update Data (Kalender):**")
        # CALENDAR UNTUK INPUT DATA
        new_date_obj = st.date_input("Pilih Tanggal Laporan", value=datetime.date.today())
        new_date_str = new_date_obj.isoformat()
        
        # Pre-fill jika tanggal tersebut sudah ada di database
        existing = date_map.get(new_date_str, {})
        pre_30 = existing.get("urls", {}).get("30", "")
        pre_60 = existing.get("urls", {}).get("60", "")
        pre_90 = existing.get("urls", {}).get("90", "")
        
        new_30 = st.text_input("Link Spreadsheet 30H", value=pre_30, key="new_30")
        new_60 = st.text_input("Link Spreadsheet 60H", value=pre_60, key="new_60")
        new_90 = st.text_input("Link Spreadsheet 90H", value=pre_90, key="new_90")
        if st.button("Simpan Data untuk Tanggal Ini"):
            save_snapshot(new_date_str, new_30, new_60, new_90)
            st.rerun()"""
    
    content = content.replace(old_block, new_ui)

# Now fix the header display. The header currently has:
# <span class="hdr-date">Periode {selected_snapshot['name']}</span>
# or something similar. We want to replace it with:
# <span class="hdr-date">Periode {format_id_date(selected_snapshot.get('date', selected_snapshot['name']))}</span>

content = content.replace(
    '<span class="hdr-date">Periode {selected_snapshot[\'name\']}</span>',
    '<span class="hdr-date">Periode {format_id_date(selected_snapshot.get("date", selected_snapshot["name"]))}</span>'
)
content = content.replace(
    '<span class="hdr-date">Periode {selected_snapshot.get(\'name\')}</span>', # in case it was written differently
    '<span class="hdr-date">Periode {format_id_date(selected_snapshot.get("date", selected_snapshot["name"]))}</span>'
)


with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("app.py patched for dropdown and calendar format")
