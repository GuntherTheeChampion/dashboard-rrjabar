import os

app_path = r"c:\Users\Guntur Ananta\Downloads\dashboard-rrjabar\dashboard-rrjabar-50dc2c5872b3f0c770a77d26e269922e3fae93e9\app.py"
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# The UI logic currently looks like:
# st.sidebar.markdown("### 🗂️ Manajemen Periode Data")
# selected_snapshot_name = st.sidebar.selectbox("Pilih Periode", [s["name"] for s in snapshots])
# ...
# with st.sidebar.expander("➕ Tambah Periode Baru"):

# We will replace `st.sidebar.` with `st.` to put it in the main page.
# However, we want it to look nice, maybe put it inside an expander or a container.
# Let's put it right after the CSS and header.
# Actually, the current patch added it right before # Helpers.

# Let's completely replace the UI logic block.
old_ui = """snapshots = load_snapshots()
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
            st.error("Semua field harus diisi!")"""

new_ui = """snapshots = load_snapshots()
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
            if new_name and new_30 and new_60 and new_90:
                save_snapshot(new_name, new_30, new_60, new_90)
                st.rerun()
            else:
                st.error("Semua field harus diisi!")
"""

content = content.replace(old_ui, new_ui)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("app.py patched successfully to move UI")
