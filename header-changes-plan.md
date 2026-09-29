# Header Changes Plan — Collection Monitoring Dashboard

## Overview
Remove the Telkomsel logo from the sticky header, rename the dashboard title to
"Collection Monitoring Dashboard", make the title text bigger, anchor it to the
top-left corner where the logo was, and strip every visible "Telkomsel" label
from the UI. All changes are in `app.py` only.

---

## Sub-Tasks

### 1. Update `page_title`
**Intent:** Remove brand ownership signal from browser tab / page metadata.  
**Expected Outcome:** `st.set_page_config` uses `"Collection Monitoring Dashboard"`.  
**Todo:**
- [ ] Change `page_title` value on line 23.
**Relevant Context:** `app.py` line 23.  
**Status:** [ ] pending

---

### 2. Remove logo CSS rules
**Intent:** Delete the now-unused `.hdr-logo` CSS blocks to keep the stylesheet clean.  
**Expected Outcome:** No `.hdr-logo` selectors remain.  
**Todo:**
- [ ] Delete `.sticky-header .hdr-logo`, `.sticky-header .hdr-logo img`,
  `.sticky-header .hdr-logo .hdr-logo-fallback` blocks (lines 92–111).
- [ ] Delete the mobile `@media` `.sticky-header .hdr-logo` override (lines 158–163).
**Relevant Context:** `app.py` lines 92–111 and 158–163.  
**Status:** [ ] pending

---

### 3. Adjust header layout and title font size
**Intent:** Make the title visually prominent and left-aligned at the top of the
header now that the logo circle is gone.  
**Expected Outcome:** `.sticky-header` uses `align-items: flex-start` with top
padding, and `h1` font size is at least `1.6rem`.  
**Todo:**
- [ ] Change `.sticky-header` `align-items: center` → `align-items: flex-start` and add `padding-top: 1.5rem`.
- [ ] Increase `.sticky-header .hdr-text h1` `font-size` from `1.15rem` → `1.65rem`.
- [ ] Update mobile `h1` font-size override from `0.8rem` → `1rem`.
**Relevant Context:** `app.py` lines 74–85 and 119–125.  
**Status:** [ ] pending

---

### 4. Remove the logo HTML block
**Intent:** Remove the `<div class="hdr-logo">…</div>` element (and its
multi-KB base64 image) from the sticky-header markdown string.  
**Expected Outcome:** No `hdr-logo` div in the rendered HTML; no base64 JPEG string.  
**Todo:**
- [ ] Delete lines 822–824 (the entire `<!-- Logo circle -->` div including the `<img>` tag).
**Relevant Context:** `app.py` lines 821–824.  
**Status:** [ ] pending

---

### 5. Update `<h1>` text and remove "Telkomsel" from description
**Intent:** Replace the branded title with the new generic title.  
**Expected Outcome:** `<h1>` reads `Collection Monitoring Dashboard`. No "Telkomsel"
appears anywhere in the rendered page.  
**Todo:**
- [ ] Replace `Telkomsel Region West Java: GraPARI Collection Monitoring Dashboard`
  → `Collection Monitoring Dashboard` in the `<h1>` on line 828.
- [ ] Update the `<p>` subtitle if it contains "Telkomsel" (confirmed it does not).
**Relevant Context:** `app.py` line 828.  
**Status:** [ ] pending
