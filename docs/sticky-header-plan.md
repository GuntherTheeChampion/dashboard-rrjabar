# Sticky Red Header with Telkomsel Logo — Plan

## Top-Level Overview

Replace the current `page-header` block in `app.py` with a full-width, sticky (fixed to top) header bar. The new header:

- Spans 100% of the viewport width, hugs the very top of the browser window (no gap above it)
- Has a deep-red background with a CSS-generated dynamic decoration: diagonal rounded pill/stadium shapes at varied angles, plus a halftone dot cluster — all rendered with inline SVG inside the header element (no external image needed for the pattern)
- Shows a circular logo placeholder in the top-left corner; once the user drops `static/telkomsel-logo.png` in place, the circle fills with the real logo
- Retains all existing text content:
  - Title: "Telkomsel Region West Java — GraPARI Collection Monitoring Dashboard"
  - Date pill: "Periode 31 Agustus 2026"
  - Subtitle: "Mobile Collection Operations | Follow-up status monitoring across all GraPARI branches — 30H / 60H / 90H"
- Pushes the rest of the page content down by the exact height of the header so nothing is hidden underneath

The change is isolated to `app.py` only: the CSS block (`.page-header` rule replacement + new sticky header rules) and the HTML markdown block that renders the header.

---

## Sub-Tasks

### Sub-Task 1 — Add sticky header CSS rules

**Intent**  
Inject the CSS that makes the new header fixed to the top of the viewport and reserves space below it so page content is not obscured.

**Expected Outcomes**
- A `position: fixed; top: 0; left: 0; width: 100%; z-index: 999` rule on `.sticky-header`
- A corresponding `padding-top` added to `.block-container` equal to the header height (~110px) so Streamlit content starts below the header
- Streamlit's own `header { visibility: hidden }` rule kept so the default Streamlit toolbar doesn't overlap

**Todo List**
1. Inside the existing `st.markdown("""<style>…</style>""")` block in `app.py`, remove the old `.page-header` CSS rule (lines 71–87)
2. Add the new `.sticky-header` CSS rule set:
   - `position: fixed; top: 0; left: 0; right: 0; z-index: 999`
   - `height: 110px; padding: 0 2.5rem`
   - `background: #C8102E` (Telkomsel red, dark tone)
   - `display: flex; align-items: center; gap: 1.25rem; overflow: hidden`
3. Update `.block-container` `padding-top` from `2rem` to `130px` so body content clears the header

**Relevant Context**
- [`app.py`](app.py:65-69) — `.block-container` rule (current `padding-top: 2rem`)
- [`app.py`](app.py:71-87) — old `.page-header` rule to be replaced
- [`app.py`](app.py:58-60) — `header { visibility: hidden }` must stay

**Status:** `[ ] pending`

---

### Sub-Task 2 — Build the header HTML with dynamic shapes and logo circle

**Intent**  
Replace the old `<div class="page-header">` markdown block with a new `<div class="sticky-header">` that contains:
1. An SVG layer (absolutely positioned, full cover) with the diagonal pill shapes + halftone dot cluster
2. A circular logo zone on the left (CSS circle with a white ring; shows `static/telkomsel-logo.png` if present, otherwise a tasteful placeholder icon via an inline SVG monogram)
3. A text block (title, date badge, subtitle) to the right of the logo

**Expected Outcomes**
- Header visually matches reference image 1 (bold geometric rounded pills at ~-35° angle, halftone dot cluster bottom-right)
- Logo circle is 72×72px, white border ring, circular crop
- Text is white; date shown as a small pill badge; subtitle is lighter-weight below the title
- All existing text content is preserved word-for-word

**Todo List**
1. Remove the old `st.markdown("""<div class="page-header">…</div>""")` block (lines 543–550)
2. Use `st.markdown(…, unsafe_allow_html=True)` to inject the new `<div class="sticky-header">` HTML
3. Inside the header HTML:
   - Place the SVG decorative layer as an absolutely-positioned child: 3–4 pill shapes in dark-red (`#A00020`) at ~-35°, varying sizes (large 260×90px, medium 180×65px, small 130×50px), spread across the header; halftone dots cluster as a grid of small circles (r=3, spacing 14px) in bottom-right quadrant at opacity 0.25
   - Logo zone: `<div class="hdr-logo">` — a 72×72px circle; use `<img src="./static/telkomsel-logo.png" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">` followed by a fallback inline SVG (white "T" monogram on transparent background), so both states look intentional
   - Text zone: `<div class="hdr-text">` — `<h1>` title, `<span class="hdr-date">` date badge, `<p>` subtitle

**Relevant Context**
- [`app.py`](app.py:543-550) — old header block to replace
- [`app.py`](app.py:71-87) — old `.page-header` CSS (being removed in Sub-Task 1)
- Reference: Style 1 (diagonal rounded pills + halftone dots)
- Logo file will be placed at: `static/telkomsel-logo.png`

**Status:** `[ ] pending`

---

### Sub-Task 3 — Guide user to add the Telkomsel logo file

**Intent**  
Tell the user exactly where to place the logo file, what dimensions and format to use, and how Streamlit serves static files — since this is a manual step, not a code step.

**Expected Outcomes**
- User knows the exact path: `static/telkomsel-logo.png` (relative to `app.py`)
- User knows the Streamlit config needed to serve static files: add `[server] enableStaticServing = true` to `.streamlit/config.toml`
- User knows recommended logo dimensions: **200×200px minimum, square aspect ratio, PNG with transparent background preferred** (will be rendered at 72×72px inside the circle)
- User understands the fallback: if the logo file is missing, a white "T" monogram placeholder circle appears automatically

**Todo List**
1. Create the `.streamlit/` directory and `config.toml` with `[server]\nenableStaticServing = true`
2. Write instructions for user: download official Telkomsel logo → save as `static/telkomsel-logo.png`
3. Confirm the `onerror` fallback in the HTML (already coded in Sub-Task 2) covers the absent-file scenario

**Relevant Context**
- Streamlit static file serving: requires `enableStaticServing = true` in `.streamlit/config.toml` and files placed in `static/` folder at the project root
- Logo circle CSS: `border-radius: 50%; width: 72px; height: 72px; object-fit: contain`

**Status:** `[ ] pending`

---

## File Change Summary

| File | Change |
|------|--------|
| `app.py` | Replace `.page-header` CSS + old header HTML with sticky header CSS + new header HTML |
| `.streamlit/config.toml` | Create new file: enable static file serving |
| `static/telkomsel-logo.png` | **Manual step** — user places the logo here |
