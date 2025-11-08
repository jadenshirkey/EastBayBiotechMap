# East Bay Biotech Map - GitHub Pages Setup Guide

## Project Overview
This project is an interactive web map of 73 biotech companies in the East Bay area of California. The goal is to create a publicly accessible GitHub Pages site that visualizes these companies on an interactive map, with filtering and search capabilities.

**Target User**: Job seekers in biotechnology, particularly those with backgrounds in protein engineering, structural biology, and computational biology.

---

## Current Project State

### ✅ COMPLETED (by Claude Code CLI)
- Git repository initialized
- `.gitignore` created (excludes personal files, resumes, old CSV versions)

### 📊 DATA FILES AVAILABLE
**Primary Working File**: `east_bay_biotech_with_addresses.csv`
- **73 companies** total
- **Columns**: Company Name, Website, City, Address, Relevance to Profile, Company Stage, Notes, Hiring
- **Address Status**: 72/73 have addresses (98.6% complete)
  - 1 company completely missing address (Intellia Therapeutics - Brisbane)
  - 16 companies have partial addresses (city only, need full street address)

**Other files** (excluded from git via .gitignore):
- Multiple legacy CSV versions
- Python scripts used for data cleaning
- Personal resumes and career documents
- Internal project notes (CLAUDE.md)

---

## TODO LIST FOR ONLINE CLAUDE

### Phase 1: Complete Address Data (CRITICAL)
**Goal**: Get complete street addresses for all 73 companies so they can be accurately geocoded.

#### 1.1 Find Missing Address
Use WebSearch to find the complete address for:
- **Intellia Therapeutics** (Brisbane, CA)

Update the Address column in `east_bay_biotech_with_addresses.csv`.

#### 1.2 Complete Partial Addresses
The following 16 companies currently only have "City, CA" format. Find their full street addresses:

**Berkeley companies (10)**:
- Addition Therapeutics
- Amber Bio
- Indee Labs
- Kimia Therapeutics
- Prellis Biologics
- Profluent (may have moved/check current location)
- Regel Therapeutics
- Sampling Human
- Santa Ana Bio (actually in Alameda despite name)
- Valitor

**Emeryville companies (3)**:
- OmniAb
- Profluent
- Prolific Machines

**Alameda companies (2)**:
- CellFE
- GeneFab
- Ohmic Biosciences

**Oakland companies (1)**:
- Phyllom BioProducts

**Search Strategy**:
```
WebSearch: "[Company Name]" "[City]" CA address headquarters
```

Look for official addresses in format: "123 Street Name, City, CA 12345"

Update `east_bay_biotech_with_addresses.csv` with the complete addresses.

---

### Phase 2: Geocode All Addresses
**Goal**: Add latitude/longitude coordinates for accurate map placement.

#### 2.1 Add Geocoding Columns
Add two new columns to `east_bay_biotech_with_addresses.csv`:
- `Latitude`
- `Longitude`

#### 2.2 Geocode Addresses
**Option A - Use Python geocoding** (if available):
```python
import pandas as pd
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="eastbay_biotech_map")

df = pd.read_csv('east_bay_biotech_with_addresses.csv')

for index, row in df.iterrows():
    try:
        location = geolocator.geocode(row['Address'])
        if location:
            df.at[index, 'Latitude'] = location.latitude
            df.at[index, 'Longitude'] = location.longitude
    except:
        print(f"Could not geocode: {row['Company Name']}")

df.to_csv('east_bay_biotech_with_addresses.csv', index=False)
```

**Option B - Manual/Batch geocoding**:
- Use a free batch geocoding service like geocod.io or Texas A&M Geocoding
- Export addresses, upload, download with lat/long
- Merge back into CSV

#### 2.3 Create Clean Public Data File
Copy `east_bay_biotech_with_addresses.csv` to `data/companies.csv` (create `data/` folder first).

This will be the public-facing data file loaded by the map.

---

### Phase 3: Build Interactive Map Website

#### 3.1 Create Project Structure
```
EastBayBiotechMap/
├── index.html
├── css/
│   └── style.css
├── js/
│   └── map.js
├── data/
│   └── companies.csv
└── README.md
```

#### 3.2 Create index.html
**Requirements**:
- Use Leaflet.js for mapping (free, open-source, no API key required)
- Load companies.csv data
- Create map centered on East Bay (approx: lat 37.8, lng -122.3)
- Include filter controls for:
  - City (dropdown or checkboxes)
  - Company Stage (dropdown)
  - Relevance to Profile (Tier 1/2/3)
- Search box to filter by company name
- Legend explaining marker colors
- Mobile-responsive design

**Map Marker Color Coding**:
Based on "Relevance to Profile" column:
- **Red markers**: Contains "Tier 1" or "High" → Most relevant (protein engineering, structural biology)
- **Orange markers**: Contains "Tier 2" or "Medium" → Medium relevance
- **Blue markers**: Contains "Tier 3" or "Low" → Lower relevance
- **Gray markers**: Academic/Government facilities

**Popup Content** (when clicking marker):
- Company Name (bold, larger font)
- Company Stage
- City
- Notes (from CSV)
- Website link (clickable)
- Hiring status (if available)

#### 3.3 Create css/style.css
**Design Requirements**:
- Clean, professional appearance
- Mobile-responsive (media queries for <768px)
- Filter controls should be collapsible on mobile
- Map should take up majority of screen
- Use professional color scheme (blues/grays, not too colorful)

#### 3.4 Create js/map.js
**Functionality Required**:
- Load CSV using PapaParse or similar library
- Initialize Leaflet map
- Create markers from CSV data with appropriate colors
- Bind popups to markers
- Implement filtering logic:
  - Show/hide markers based on selected filters
  - Update visible markers when search text changes
- Add marker clustering for better UX (use Leaflet.markercluster)
- Fit map bounds to visible markers after filtering

**Example Leaflet Setup**:
```javascript
var map = L.map('map').setView([37.8, -122.3], 10);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Load CSV and create markers
// (implementation details to be filled in)
```

---

### Phase 4: Create Documentation

#### 4.1 Create README.md
**Contents**:
```markdown
# East Bay Biotech Map

An interactive map of biotechnology companies in the San Francisco East Bay Area.

## About
This map visualizes 73+ biotech companies across Emeryville, Berkeley, Alameda, and surrounding cities. Companies are color-coded by their relevance to protein engineering and structural biology roles.

### Features
- Interactive map with searchable/filterable company data
- Color-coded markers by company focus area
- Detailed company information in popups
- Filter by city, company stage, or relevance tier

### Data Sources
- Company information compiled from public sources (January 2025)
- Addresses verified via company websites and business registries

### Legend
- 🔴 Red: Tier 1 - Protein engineering, structural biology, CRISPR focus
- 🟠 Orange: Tier 2 - Cell therapy, antibodies, computational biology
- 🔵 Blue: Tier 3 - Tools/services, diagnostics, instruments
- ⚪ Gray: Academic/government research facilities

## Usage
Visit the live map at: [URL will be generated after GitHub Pages setup]

## Contributing
To suggest updates or corrections, please open an issue.

## Last Updated
[Date will be filled in]
```

---

### Phase 5: Deploy to GitHub

#### 5.1 Set Default Branch Name
```bash
git branch -M main
```

#### 5.2 Commit All Files
```bash
git add .
git commit -m "Initial commit: East Bay Biotech interactive map

- Add geocoded company data (73 companies)
- Create interactive Leaflet.js map with filters
- Add README and documentation
- Configure GitHub Pages deployment"
```

#### 5.3 Create GitHub Repository
1. Go to github.com and create new repository
2. Name: `EastBayBiotechMap` (or `east-bay-biotech-map`)
3. Description: "Interactive map of East Bay biotech companies for job seekers"
4. **Public** repository (required for free GitHub Pages)
5. Do NOT initialize with README (we already have one)

#### 5.4 Push to GitHub
```bash
git remote add origin https://github.com/[YOUR_USERNAME]/EastBayBiotechMap.git
git push -u origin main
```

#### 5.5 Enable GitHub Pages
1. Go to repository Settings → Pages (left sidebar)
2. Under "Source", select branch: `main`
3. Folder: `/ (root)`
4. Click Save
5. Wait 1-2 minutes for build

Your site will be live at:
```
https://[YOUR_USERNAME].github.io/EastBayBiotechMap/
```

---

### Phase 6: Test and Polish

#### 6.1 Test Live Site
- Verify map loads and centers correctly
- Test all filters (city, stage, tier)
- Test search functionality
- Click several markers to verify popups
- Test on mobile device or browser DevTools mobile view

#### 6.2 Common Issues & Fixes
**Map doesn't load**:
- Check browser console for errors
- Verify companies.csv path is correct
- Check Leaflet.js and PapaParse CDN links

**Markers not showing**:
- Verify latitude/longitude values are present and valid
- Check that CSV is properly parsed
- Look for JavaScript errors in console

**Filters not working**:
- Verify filter values match CSV column values exactly
- Check case sensitivity

#### 6.3 Optional Enhancements
Consider adding (can do in follow-up):
- Export filtered results to CSV
- Link to company job boards/careers pages
- Add "Hiring" status indicators
- Heatmap view option
- Directions link to Google Maps
- Share/bookmark specific filter views

---

## Technical Stack

**Frontend**:
- HTML5
- CSS3 (with Flexbox/Grid for layout)
- Vanilla JavaScript (ES6+)

**Libraries** (loaded via CDN):
- Leaflet.js v1.9+ (mapping)
- Leaflet.markercluster (optional - better UX with many markers)
- PapaParse (CSV parsing)

**Hosting**: GitHub Pages (free, static site hosting)

**No backend required** - fully client-side application

---

## Data Privacy Notes

The following files are **excluded** from the public repository via `.gitignore`:
- Personal resumes and CVs
- Professional summary document
- Internal project management files (CLAUDE.md)
- Python data processing scripts
- Legacy/intermediate CSV versions

Only the final cleaned company data is published, containing publicly available information:
- Company names
- Websites
- Addresses (all publicly listed business addresses)
- Company stage/focus (public information)

---

## Next Steps Summary

1. ✅ Git repo initialized
2. ✅ .gitignore created
3. ⏳ Complete missing/partial addresses (17 companies)
4. ⏳ Geocode all addresses → add lat/long columns
5. ⏳ Build HTML/CSS/JS map interface with Leaflet.js
6. ⏳ Create README.md
7. ⏳ Commit and push to GitHub
8. ⏳ Enable GitHub Pages
9. ⏳ Test and polish

**Estimated time**: 2-3 hours total

**Critical first step**: Complete the address data (Phase 1) before building the map interface.

Good luck! The data is in excellent shape and ready for a beautiful interactive map.
