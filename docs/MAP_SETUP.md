# Google My Maps Setup & Update Guide

**Purpose**: Instructions for creating and maintaining the Bay Area Biotech Map using Google My Maps

**Current Version**: v1.0 (171 companies)

---

## Initial Setup (Do Once)

### Step 1: Import Data to Google My Maps

1. **Go to Google My Maps**: https://www.google.com/mymaps
2. **Click "Create a new map"**
3. **Click "Import"** (under "Untitled layer")
4. **Upload**: `data/final/companies.csv`
5. **Choose columns for markers**:
   - Position markers: **Address** column
   - Title: **Company Name**
6. **Click "Finish"**

### Step 2: Configure Map Display

**Marker Style by Company Stage**:
1. Click on the layer → **Style by** → **Uniform style**
2. Choose: **Company_Stage** column
3. Assign colors (8 categories per V4.3 classification):
   - 🟢 Green: **Public** (publicly traded companies)
   - 🟠 Orange: **Private** (venture-funded startups)
   - ⚫ Black: **Acquired** (acquired by larger companies)
   - 🔴 Red: **Clinical** (companies with drugs in clinical trials)
   - 🟣 Purple: **Research** (pre-clinical research stage)
   - 🟡 Yellow: **Incubator** (biotech accelerators/incubators)
   - 🔵 Blue: **Service** (CROs, CDMOs, service providers)
   - ⚪ Gray: **Unknown** (classification pending)

**Info Window Content**:
1. Click on any marker → Edit
2. Under title, add these fields (Google My Maps does this automatically from CSV):
   - Company Name (bold)
   - City
   - Address
   - Website (clickable link)
   - Company_Stage
   - Focus_Areas
   - Validation_Source

### Step 3: Name and Share the Map

1. **Click "Untitled map"** → Rename to: **Bay Area Biotech Companies**
2. **Add description**: "171 biotech companies across the SF Bay Area - for job seekers and researchers"
3. **Click "Share"** → Change to **Public** or **Anyone with the link**
4. **Copy the shareable link** (looks like: `https://www.google.com/maps/d/...`)

### Step 4: Get Embed Code (Optional)

For embedding on a website:
1. Click ⋮ (three dots) next to map title
2. Click **Embed on my site**
3. Copy the `<iframe>` code
4. Paste into your website HTML

---

## Updating the Map (When Data Changes)

### Option A: Re-import CSV (Recommended - Cleanest)

**When to use**: When you've updated many companies at once

**Steps**:
1. Update `data/final/companies.csv` with new data
2. Go to your Google My Maps
3. **Delete the old layer** (click ⋮ on layer → Delete layer)
4. **Import** the updated CSV (same as Step 1 in Initial Setup)
5. **Re-configure colors** by Company Stage
6. Done! Map is updated

**Pros**: Clean, complete refresh of all data
**Cons**: Resets any manual edits made in Google My Maps

---

### Option B: Manual Updates in Google My Maps

**When to use**: Small changes (1-10 companies)

**Adding a new company**:
1. Click **Add marker** (pin icon)
2. Click on the map where the company is located
3. Fill in: Company Name, Address, City, Website, Notes, Company Stage, Hiring
4. Save

**Editing existing company**:
1. Click on the marker
2. Click **Edit** (pencil icon)
3. Update fields
4. Save

**Deleting a company**:
1. Click on the marker
2. Click **Delete** (trash icon)

**Pros**: Quick for small changes
**Cons**: Can get out of sync with CSV file

---

### Option C: Hybrid (Best for Iteration)

**Workflow for iterative updates**:

1. **Make changes in CSV**: `data/final/companies.csv`
2. **Test with sample**: Import to a new test map first
3. **Validate**: Check that addresses geocode correctly
4. **Update production map**: Use Option A (re-import)
5. **Export from Google My Maps** (for backup):
   - Click ⋮ → **Export to KML/KMZ**
   - Save locally as backup

**This keeps CSV and map in sync!**

---

## Keeping Data in Sync

### Production Data File: `data/final/companies.csv`

**This is the source of truth**. Always update this file, then push to Google My Maps.

**Update workflow**:
```
1. Edit data/final/companies.csv
2. Commit to git: "Update company data - added X companies"
3. Re-import to Google My Maps
4. Verify map looks correct
5. Done!
```

### Exporting from Google My Maps

If you make edits directly in Google My Maps and want to save them back to CSV:

1. Go to your map
2. Click ⋮ (three dots) → **Export to KML/KMZ**
3. Choose **KML** format (not KMZ)
4. Download the file
5. **Convert KML to CSV**:
   - Open in Google Earth Pro
   - File → Save → Save as CSV
   - Or use an online KML-to-CSV converter

**Then** update `data/final/companies.csv` with the exported data

---

## Common Update Scenarios

### Scenario 1: Added Careers URLs for 50 companies

**Steps**:
1. Update `data/final/companies.csv` (fill in Hiring column)
2. Commit to git
3. Re-import to Google My Maps (Option A)
4. Done!

**Time**: 5 minutes

---

### Scenario 2: Added 20 new companies

**Steps**:
1. Add 20 rows to `data/final/companies.csv`
2. Commit to git
3. Re-import to Google My Maps (Option A)
4. Verify new pins appear
5. Done!

**Time**: 5 minutes

---

### Scenario 3: Updated Notes/Descriptions for all companies

**Steps**:
1. Update Notes column in `data/final/companies.csv`
2. Commit to git
3. Re-import to Google My Maps (Option A)
4. Click a few markers to verify Notes updated
5. Done!

**Time**: 5 minutes

---

## Pro Tips

### Geocoding Issues

If some addresses don't geocode correctly:

1. **Check address format**: Should be "Street, City, State ZIP"
2. **Be specific**: "123 Main St" is better than "Main Street"
3. **Fix in CSV first**, then re-import
4. **Manual placement**: In Google My Maps, drag pin to correct location

### Testing Before Production Update

**Always test with a new map first**:
1. Create → Import updated CSV
2. Check a sample of companies
3. If looks good → Update production map
4. If issues → Fix CSV and retry

### Backup Your Map

**Regularly export** your Google My Maps data:
- Click ⋮ → Export to KML
- Save to `/data/backups/map_backup_YYYY-MM-DD.kml`
- Commit to git (if not too large)

This gives you a restore point if something goes wrong.

---

## Map Sharing & Embedding

### Shareable Link

After creating the map, get the public link:
- Format: `https://www.google.com/maps/d/edit?mid=XXXXXX&usp=sharing`
- Change `edit` to `viewer` for view-only: `https://www.google.com/maps/d/viewer?mid=XXXXXX`

**Use this link**:
- In your README.md
- On LinkedIn/resume
- Share with friends/colleagues

### Embed on Website

If you build a custom website later:
```html
<iframe
  src="https://www.google.com/maps/d/embed?mid=XXXXXX"
  width="100%"
  height="600"
  frameborder="0"
  style="border:0"
></iframe>
```

Paste this in your `index.html`

---

## Limitations of Google My Maps

**Good for**:
- Quick visual map
- No coding required
- Easy sharing
- Automatic geocoding

**Limitations**:
- Max 2,000 markers per map (we're at 171, plenty of room)
- Limited filter/search options
- Can't customize popups much
- No advanced interactivity

**If you outgrow Google My Maps**, consider:
- Custom Leaflet.js map (see PROJECT_PLAN.md Phase 3)
- Mapbox
- ArcGIS Online

For v1.0, Google My Maps is perfect!

---

## Troubleshooting

### Problem: CSV import fails

**Solution**: Check CSV format
- Must be UTF-8 encoded
- No special characters in headers
- Address column must exist
- Try opening in Excel, save as CSV (UTF-8)

### Problem: Addresses don't geocode

**Solution**:
- Add full address: "Street, City, State ZIP"
- Use Google Maps to verify address exists
- Fix typos in CSV

### Problem: Map link doesn't work

**Solution**:
- Make sure map is set to **Public** or **Anyone with link**
- Click "Share" → Check visibility settings

### Problem: Lost changes made in Google My Maps

**Solution**:
- Export to KML regularly
- Update CSV from exports before re-importing
- Or use CSV as source of truth (don't edit in map)

---

## Next Steps After Launch

Once your map is live:

1. **Share it**:
   - LinkedIn post
   - Reddit (r/biotech, r/sanfrancisco)
   - BioSpace forums
   - Career advisors

2. **Iterate**:
   - Add careers URLs (Phase 2)
   - Add more companies (Phase 3)
   - Get feedback from users

3. **Track usage** (if you want):
   - Google My Maps doesn't have built-in analytics
   - Share via bit.ly for click tracking
   - Ask people to comment/suggest additions

---

**Current Status**: Ready for v1.0 launch with 171 companies!

**Last Updated**: January 8, 2025
