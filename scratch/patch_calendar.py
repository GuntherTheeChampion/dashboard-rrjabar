import os

app_path = r"c:\Users\Guntur Ananta\Downloads\dashboard-rrjabar\dashboard-rrjabar-50dc2c5872b3f0c770a77d26e269922e3fae93e9\app.py"
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

old_ui = """snapshots = load_snapshots()
if not snapshots:
    snapshots = [{"id": "default", "name": "16 September 2026", "urls": {"30": "", "60": "", "90": ""}}]

# Place it in a neat expander at the top of the page
with st.expander("🗂️ Manajemen Periode Data", expanded=False):
    colA, colB = st.columns([1, 1])
    with colA:
        st.markdown("**Pilih Periode Aktif:**")
        selected_snapshot_name = st.selectbox("Periode", [s["name"] for s in snapshots], label_visibility="collapsed")
        selected_snapshot = next(s for s in snapshots if s["name"] == selected_snapshot_name)
    with colB:
        st.markdown("**➕ Tambah Periode Baru:**")
        new_name = st.text_input("Nama Periode (e.g., 1 Oktober 2026)", key="new_name")
        new_30 = st.text_input("Link Spreadsheet 30H", key="new_30")
        new_60 = st.text_input("Link Spreadsheet 60H", key="new_60")
        new_90 = st.text_input("Link Spreadsheet 90H", key="new_90")
        if st.button("Simpan & Update"):
            if new_name:
                save_snapshot(new_name, new_30, new_60, new_90)
                st.rerun()
            else:
                st.error("Nama Periode harus diisi!")"""

new_ui = """import datetime
snapshots = load_snapshots()
if not snapshots:
    snapshots = [{"id": "default", "name": "16 September 2026", "urls": {"30": "", "60": "", "90": ""}}]

# Helper to format dates nicely for Indonesian locale if needed, but ISO is fine for internal
# Let's map dates to snapshots
date_map = {s.get("date", s["name"]): s for s in snapshots}

with st.expander("🗂️ Manajemen Periode Data", expanded=False):
    colA, colB = st.columns([1, 1])
    with colA:
        st.markdown("**Pilih Periode Aktif (Calendar):**")
        # Try to parse the first snapshot's date to set as default
        default_date = datetime.date.today()
        first_date_str = snapshots[0].get("date", snapshots[0]["name"])
        try:
            default_date = datetime.datetime.strptime(first_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass # keep today as fallback if it's the old "16 September 2026" string
            
        selected_date_obj = st.date_input("Pilih Tanggal", value=default_date, label_visibility="collapsed")
        selected_date_str = selected_date_obj.isoformat()
        
        # Look up in our snapshots
        selected_snapshot = date_map.get(selected_date_str)
        if not selected_snapshot:
            # Fallback to the old name format just in case, or show empty
            selected_snapshot = date_map.get(selected_date_obj.strftime("%d %B %Y"))
            
        if not selected_snapshot:
            st.warning(f"Belum ada data untuk tanggal {selected_date_str}. Silakan tambahkan di sebelah kanan.")
            # Provide an empty snapshot so the rest of the app doesn't crash
            selected_snapshot = {"name": selected_date_str, "urls": {"30": "", "60": "", "90": ""}}
            
    with colB:
        st.markdown("**➕ Update / Tambah Data untuk Tanggal Terpilih:**")
        # Pre-fill links if data exists for this date so they can edit it
        pre_30 = selected_snapshot["urls"].get("30", "")
        pre_60 = selected_snapshot["urls"].get("60", "")
        pre_90 = selected_snapshot["urls"].get("90", "")
        
        new_30 = st.text_input("Link Spreadsheet 30H", value=pre_30, key="new_30")
        new_60 = st.text_input("Link Spreadsheet 60H", value=pre_60, key="new_60")
        new_90 = st.text_input("Link Spreadsheet 90H", value=pre_90, key="new_90")
        if st.button("Simpan Data untuk Tanggal Ini"):
            # Save using the exact date string
            save_snapshot(selected_date_str, new_30, new_60, new_90)
            st.rerun()"""

content = content.replace(old_ui, new_ui)

# We also need to fix the header injection to use selected_snapshot['name'] correctly since it might be a date now.
# Actually selected_snapshot['name'] is fine because we set it to selected_date_str.
with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("app.py patched with calendar UI")
