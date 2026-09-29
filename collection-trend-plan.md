# Collection Rate Trend Visualization — Plan

## Top-Level Overview

**Goal**: Add a new "📈 Trend" tab to the existing GraPARI Collection Monitoring Dashboard that displays an interactive line chart of monthly collection rates (60-H and/or 90-H) for 2026 (Jan–Aug), filterable by branch and bucket(s), sourced from the local Excel file `Performansi Collection Rate CTP 2026.xlsx`.

**Scope**:
- Add a new data loader/parser for the Excel file (local read, no Google Sheets involved)
- Add a "📈 Trend" tab as a 4th tab in `app.py`, alongside the existing 30H, 60H, 90H tabs
- Render a single Plotly line chart where each selected bucket is a separate colored line, each with its own dashed KPI target line
- Add two filters: Branch (single-select dropdown) and Bucket (multi-select: 30H / 60H / 90H)
- When 30H is selected but no data exists yet, show a friendly "data not yet available" message
- Style to match the existing Telkomsel dashboard design (red accent, CSS variables)

**Non-goals**:
- No changes to the existing 30H, 60H, 90H operational tabs
- No multi-year support yet (extensible later)
- No Google Sheets upload required — file stays local

**Data source**: `Performansi Collection Rate CTP 2026.xlsx` (Sheet1), already in the project root.

---

## Visualization Design

### Single bucket selected (e.g. only 60H):
- One line (Telkomsel red `#E30613`) for the actual monthly rate
- One dashed gray line for the KPI target (98.20%)
- X-axis: months Jan → Agu
- Y-axis: percentage, range ~96%–101% for clarity

### Multiple buckets selected (e.g. 60H + 90H):
- One line per bucket, each a different color:
  - 60-H → Telkomsel red `#E30613`
  - 90-H → blue `#2563EB`
  - 30-H → green `#16a34a` (ready for when data arrives)
- One dashed KPI line per bucket, same color but dashed
- All on a single chart — easy to compare trends

### Branch filter: single-select dropdown (Bandung, Cirebon, Soreang, Tasikmalaya, Jawa Barat)
### Bucket filter: multi-select checkboxes or multiselect widget (30H, 60H, 90H)

---

## Sub-Tasks

---

### Sub-Task 1 — Parse the Excel file into a clean DataFrame

**Intent**: Create a dedicated loader function that reads the local Excel file and returns a tidy, analysis-ready DataFrame. Isolates all parsing logic and makes it easy to add 30H or future years later.

**Expected Outcomes**:
- A function `load_trend_data()` in a new file `trend_loader.py`
- Returns a DataFrame with columns: `Branch`, `Bucket` (60-H / 90-H), `Month`, `Rate` (float, e.g. 0.9847), `KPI` (float, e.g. 0.9820)
- Covers all 5 entities: Bandung, Cirebon, Soreang, Tasikmalaya, Jawa Barat
- Months: Jan, Feb, Mar, Apr, Mei, Jun, Jul, Agu (as ordered categorical, Indonesian abbreviations)
- Decorated with `@st.cache_data` so the file is only parsed once per session

**Todo List**:
- [ ] Create `trend_loader.py` in the project root
- [ ] Use `pandas.read_excel(..., header=None)` to read Sheet1
- [ ] Hard-code the confirmed cell ranges:
  - Bandung 60-H actuals: row index 6, cols 2–9 (0-indexed)
  - Bandung 90-H actuals: row index 8, cols 2–9
  - Cirebon 60-H: row index 6, cols 12–19; 90-H: row index 8, cols 12–19
  - Soreang 60-H: row index 22, cols 2–9; 90-H: row index 24, cols 2–9
  - Tasikmalaya 60-H: row index 22, cols 12–19; 90-H: row index 24, cols 12–19
  - Jawa Barat 60-H: row index 38, cols 2–9; 90-H: row index 40, cols 2–9
- [ ] Read KPI targets dynamically: 60-H = cell (0, 1), 90-H = cell (1, 1)
- [ ] Build tidy long-format DataFrame and return it
- [ ] Add `@st.cache_data` decorator

**Relevant Context**:
- `data_loader.py` and `data_processor.py` show existing loading patterns
- `openpyxl` and `pandas` already in `requirements.txt`
- Excel layout confirmed from reading `Performansi Collection Rate CTP 2026.xlsx`

**Status**: `[x] done`

---

### Sub-Task 2 — Add Plotly as a dependency

**Intent**: The existing dashboard uses no charting library. Plotly Express is the right fit for interactive multi-line charts in Streamlit with minimal code.

**Expected Outcomes**:
- `plotly` added to `requirements.txt`
- `import plotly.express as px` works in the app

**Todo List**:
- [ ] Add `plotly` to `requirements.txt`

**Relevant Context**:
- `requirements.txt` currently lists: `streamlit`, `pandas`, `openpyxl`, `requests`
- Streamlit renders Plotly figures natively via `st.plotly_chart()`

**Status**: `[x] done`

---

### Sub-Task 3 — Build the Trend tab UI in app.py

**Intent**: Add a 4th "📈 Trend" tab to the existing tab navigation and render two filters (branch + bucket) plus a single multi-line Plotly chart inside it.

**Expected Outcomes**:
- A new "📈 Trend" tab appears alongside the existing three tabs
- Two filters rendered using existing selectbox/multiselect CSS patterns:
  - **Branch** dropdown: Bandung, Cirebon, Soreang, Tasikmalaya, Jawa Barat
  - **Bucket** multiselect: 30H, 60H, 90H (30H shows "no data yet" if selected alone)
- A single `st.plotly_chart()` figure with:
  - One solid colored line per selected bucket (60-H = red, 90-H = blue, 30-H = green)
  - One dashed line per selected bucket for its KPI target (same color, dashed)
  - X-axis: months Jan → Agu in correct order
  - Y-axis: percentage format, range ~96%–101%
  - Legend showing bucket names
  - Chart title showing the selected branch name
- If 30H is the only selection, a friendly `st.info()` message: "Data 30H belum tersedia untuk periode ini"
- Styled to match dashboard theme (background, font, gridlines)

**Todo List**:
- [ ] Import `trend_loader` and `plotly.graph_objects as go` at the top of `app.py`
- [ ] Extend `st.tabs()` call from 3 to 4 tabs, adding "📈 Trend"
- [ ] Inside the new tab block:
  - [ ] Load data via `load_trend_data()`
  - [ ] Render branch `st.selectbox()` (reuses existing CSS automatically)
  - [ ] Render bucket `st.multiselect()` with default = `["60-H", "90-H"]`
  - [ ] Filter DataFrame by selected branch and selected buckets
  - [ ] If only 30H selected and no data, show `st.info()` message
  - [ ] Build Plotly figure using `go.Figure()` — add one `go.Scatter()` trace per bucket (actual line) + one `go.Scatter()` trace per bucket (KPI dashed line)
  - [ ] Apply chart layout: transparent background, Telkomsel font/colors, gridlines
  - [ ] Render with `st.plotly_chart(fig, use_container_width=True)`

**Relevant Context**:
- Tab navigation is at lines 789–798 of `app.py`
- Existing selectbox CSS already defined and will apply automatically
- Colors: 60-H = `#E30613`, 90-H = `#2563EB`, 30-H = `#16a34a`
- KPI dashed lines: same color per bucket, `dash="dash"`, reduced opacity

**Status**: `[x] done`

---

## Data File Layout Reference

```
Excel Sheet1 layout (0-indexed rows and cols for pandas):
  Row 0, Col 1: 0.9820  ← 60-H KPI target
  Row 1, Col 1: 0.9850  ← 90-H KPI target

  BANDUNG:
    Row 6, Cols 2–9:  60-H actuals (Jan–Agu)
    Row 8, Cols 2–9:  90-H actuals (Jan–Agu)

  CIREBON:
    Row 6, Cols 12–19: 60-H actuals
    Row 8, Cols 12–19: 90-H actuals

  SOREANG:
    Row 22, Cols 2–9:  60-H actuals
    Row 24, Cols 2–9:  90-H actuals

  TASIKMALAYA:
    Row 22, Cols 12–19: 60-H actuals
    Row 24, Cols 12–19: 90-H actuals

  JAWA BARAT (Total):
    Row 38, Cols 2–9:  60-H actuals
    Row 40, Cols 2–9:  90-H actuals
```

---

## Notes for Implementation

- Excel file path: `"Performansi Collection Rate CTP 2026.xlsx"` — project root, alongside `app.py`
- Use `pd.read_excel(..., header=None)` to avoid header-row confusion
- Month labels use Indonesian abbreviations (`Mei`, `Agu`) — keep as-is for consistency
- `@st.cache_data` on `load_trend_data()` prevents re-reading on every Streamlit rerun
- 30H bucket entry is prepared in the loader with empty data so the filter works gracefully from day one
- When more years of data are available, only `trend_loader.py` needs updating — `app.py` stays unchanged
