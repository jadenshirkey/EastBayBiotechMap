# Bay Area Biotech Map - Project Plan

## Project Vision

Create a comprehensive, publicly accessible map of biotechnology companies across the entire San Francisco Bay Area to help:
- **Job seekers** explore biotech opportunities
- **Researchers** understand the regional ecosystem
- **Entrepreneurs** identify potential partners or competitors
- **Investors** track the biotech landscape

**Key Principles**:
- Universal utility (not personal rankings)
- Rich company data (size, funding, focus areas)
- Interactive and filterable
- Well-documented and maintainable

---

## Current State (As of January 2025)

### Data Files We Have

1. **east_bay_biotech_v2.csv** (172 companies)
   - Broader Bay Area coverage (Palo Alto, SF, Redwood City, etc.)
   - Most comprehensive list
   - **This will be our BASE FILE**

2. **east_bay_biotech_with_addresses.csv** (74 companies)
   - East Bay focused
   - Uses "Tier 1/2/3" format (personal rankings)
   - More complete addresses for East Bay companies

3. **east_bay_biotech_pseudofinal.csv** (73 companies)
   - East Bay focused
   - Numeric relevance rankings (1, 2, 3)
   - Used in Google My Maps v1

### Python Scripts We Have

Located in `/scripts/` (to showcase computational skills):
- `add_addresses.py` - Add addresses to company list
- `add_pasted_addresses.py` - Import manually found addresses
- `company_addresses.py` - Address lookup/validation
- `create_addresses_csv.py` - Generate CSV with address column
- `update_addresses.py` - Update existing address data

### What's On Google My Maps v1

Currently visualizing: `east_bay_biotech_pseudofinal.csv` and/or `east_bay_biotech_v2.csv`
- 73-172 companies depending on which data was imported
- Basic markers with company info
- Link: https://www.google.com/maps/d/u/0/edit?mid=1ilB4lPNTYk8O5bgUxavsIbZw_yPN4pU&usp=sharing

---

## Target Data Structure

### Final CSV: `data/companies.csv`

**Core Fields** (already have):
- Company Name
- Website
- City
- Address (street address for geocoding)
- Latitude (to be added via geocoding)
- Longitude (to be added via geocoding)

**New Fields to Add**:

| Field | Description | Example Values | Source |
|-------|-------------|----------------|--------|
| **Description** | 1-2 sentence company overview | "Develops CRISPR-based gene therapies for rare diseases" | Company website, Google snippet |
| **Company Size** | Employee count category | Startup (<20), Small (20-100), Medium (100-500), Large (500+) | LinkedIn, Crunchbase |
| **Founded** | Year founded | 2015 | Crunchbase, company website |
| **Funding Status** | Notable funding or status | "Series B ($50M)", "Bootstrapped", "Acquired by X" | Crunchbase, press releases |
| **Technology Focus** | Primary technology area(s) | "Gene Therapy", "Antibody Discovery", "Diagnostics" | Company website, categorization |
| **Stage** | Development stage | Startup, Preclinical, Clinical, Commercial | Company website, pipeline info |
| **Careers Link** | Direct link to jobs page | https://company.com/careers | Company website |

**Notes**:
- Remove personal "Relevance to Profile" / "Tier" columns (not universal)
- Keep "Notes" field for additional context if needed
- All data should be publicly available information

---

## Project Phases

### ✅ Phase 0: Foundation (CURRENT)
- [x] Initialize git repository
- [x] Create README and LICENSE
- [ ] **Create organized folder structure**
  - [ ] `/data/` - All CSV files
    - [ ] `/data/final/` - Production data file
    - [ ] `/data/archive/` - Old versions for reference
  - [ ] `/scripts/` - Python data processing scripts
  - [ ] `/docs/` - Documentation
- [ ] **Update .gitignore** to showcase scripts but hide personal files
- [ ] **Document this plan** (this file!)

---

### 📊 Phase 1: Data Consolidation & Cleaning

**Goal**: Create single, clean CSV with all 172+ Bay Area companies

#### Step 1.1: Merge and Deduplicate
- [ ] Start with `east_bay_biotech_v2.csv` (172 companies) as base
- [ ] Cross-reference with `with_addresses.csv` for better East Bay addresses
- [ ] Remove duplicate entries
- [ ] Standardize column names and formats
- [ ] Remove personal ranking columns (Tier/Relevance)
- [ ] **Output**: `data/working/companies_merged.csv`

#### Step 1.2: Address Completion
- [ ] Identify companies with missing/incomplete addresses
- [ ] Research and fill in complete addresses (street, city, state, zip)
- [ ] Validate address formats
- [ ] **Tool**: Python script or manual lookup

#### Step 1.3: Geocoding
- [ ] Add Latitude and Longitude columns
- [ ] Use geocoding service (geopy, Google Maps API, or batch service)
- [ ] Validate coordinates are in Bay Area
- [ ] **Script**: `scripts/geocode_addresses.py` (to be created)

**Deliverable**: Clean CSV with name, website, city, full address, lat/lon for 172+ companies

---

### 📝 Phase 2: Data Enrichment

**Goal**: Add company descriptions, size, funding, and focus areas

#### Approach Options:

**Option A: Automated (faster, less accurate)**
- Write Python scripts to scrape data from:
  - Company websites (description, careers link)
  - Crunchbase API (funding, size, founded year)
  - LinkedIn Company Pages (size, description)
- Requires API keys or web scraping
- May have gaps/errors

**Option B: Manual Curation (slower, more accurate)**
- Create spreadsheet template with new columns
- Research top ~50 most important companies first
- Fill in data from company websites, Crunchbase, LinkedIn
- Expand to full list over time

**Option C: Hybrid (recommended)**
- Use automated scripts to gather what's available
- Manually verify and fill gaps for major companies
- Community contribution for long tail

#### Step 2.1: Add Description Field
- [ ] Extract 1-2 sentence descriptions from company websites
- [ ] Store in Description column
- [ ] **Script idea**: `scripts/fetch_descriptions.py`

#### Step 2.2: Add Company Size
- [ ] Categorize as: Startup (<20), Small (20-100), Medium (100-500), Large (500+)
- [ ] Source: LinkedIn, Crunchbase, company websites
- [ ] **Script idea**: `scripts/fetch_company_size.py`

#### Step 2.3: Add Funding Information
- [ ] Research funding stage and notable amounts
- [ ] Format: "Series B ($50M)", "Bootstrapped", "IPO (NASDAQ: TICK)"
- [ ] Source: Crunchbase, press releases, company announcements

#### Step 2.4: Add Technology Focus & Stage
- [ ] Categorize technology areas (can be multiple)
- [ ] Determine development stage
- [ ] May require manual curation/validation

#### Step 2.5: Add Careers Links
- [ ] Find direct careers/jobs page URLs
- [ ] Test that links work
- [ ] **Script idea**: `scripts/find_careers_pages.py`

**Deliverable**: `data/final/companies.csv` with all enriched fields

---

### 🗺️ Phase 3: Map Creation & Visualization

**Goal**: Create interactive, embeddable map with filtering capabilities

#### Map Options:

##### Option 1: Google My Maps (Easiest, Limited Customization)
**Pros**:
- Easy to create and update
- Free
- Embeddable via iframe
- Export as .kml/.kmz

**Cons**:
- Limited styling options
- Max 2,000 markers per map
- Limited filtering capabilities
- Requires Google account

**Implementation**:
1. Import `data/final/companies.csv` to Google My Maps
2. Configure marker colors by category (size, stage, or tech focus)
3. Add info windows with company details
4. Export .kml file for backup
5. Get embed code for website integration

##### Option 2: Custom Leaflet.js Web Map (More Control, More Work)
**Pros**:
- Full customization of filters, colors, popups
- Host on GitHub Pages (free)
- No external dependencies
- Professional appearance
- Advanced features (search, multi-filter, clustering)

**Cons**:
- Requires HTML/CSS/JavaScript development
- Need to maintain code
- More complex setup

**Implementation**:
1. Create `index.html`, `css/style.css`, `js/map.js`
2. Use Leaflet.js for map rendering
3. Load CSV data with PapaParse
4. Create marker layers by category
5. Build filter UI (checkboxes, dropdowns)
6. Deploy to GitHub Pages

##### Option 3: Hybrid Approach (Recommended)
- Use Google My Maps for quick v2
- Document export format (.kml/.kmz)
- Plan for eventual custom Leaflet.js migration
- Keep map data in CSV for portability

#### Step 3.1: Choose Map Platform
- [ ] Decide: Google My Maps v2, Custom Leaflet.js, or Hybrid
- [ ] Document decision and rationale

#### Step 3.2: Create Map
- [ ] Import/load company data
- [ ] Configure markers and colors
- [ ] Set up info popups/windows
- [ ] Test on different devices

#### Step 3.3: Add Filtering
- [ ] By City
- [ ] By Company Size
- [ ] By Technology Focus
- [ ] By Stage
- [ ] By Funding Status (optional)

#### Step 3.4: Embed/Deploy
- [ ] If Google My Maps: Get embed code, add to README
- [ ] If custom: Deploy to GitHub Pages
- [ ] Test embedded map functionality

**Deliverable**: Live, interactive map accessible via public URL

---

### 📦 Phase 4: Repository Polish & Documentation

**Goal**: Professional, well-organized GitHub repository

#### Step 4.1: Organize File Structure
```
BayAreaBiotechMap/
├── README.md                          # Project overview, map link
├── PROJECT_PLAN.md                    # This file
├── LICENSE                            # MIT License
├── .gitignore                         # Hide personal files
├── data/
│   ├── final/
│   │   └── companies.csv              # Production dataset
│   └── archive/
│       ├── east_bay_biotech_v2.csv
│       ├── east_bay_biotech_with_addresses.csv
│       └── east_bay_biotech_pseudofinal.csv
├── scripts/
│   ├── README.md                      # Script documentation
│   ├── geocode_addresses.py
│   ├── fetch_descriptions.py
│   ├── fetch_company_size.py
│   └── ... (other data processing scripts)
├── docs/
│   ├── DATA_DICTIONARY.md             # Column definitions
│   └── CONTRIBUTING.md                # How others can help
└── index.html (if custom map)
```

#### Step 4.2: Write Documentation
- [ ] **README.md**: Project overview, map link, features, how to contribute
- [ ] **DATA_DICTIONARY.md**: Explain each column in companies.csv
- [ ] **scripts/README.md**: Explain what each script does
- [ ] **CONTRIBUTING.md**: How to suggest additions/corrections

#### Step 4.3: Update .gitignore
- [ ] Keep Python scripts visible (showcase computational work)
- [ ] Hide personal files (resumes, notes)
- [ ] Hide legacy/intermediate CSV files (keep in archive/ only)
- [ ] Hide API keys or secrets

#### Step 4.4: Clean Commit History
- [ ] Ensure no sensitive data in git history
- [ ] Create clear commit messages
- [ ] Tag major versions (v1.0, v2.0, etc.)

**Deliverable**: Professional GitHub repository ready for public showcase

---

### 🚀 Phase 5: Launch & Maintenance

#### Step 5.1: Soft Launch
- [ ] Share with friends/colleagues for feedback
- [ ] Fix any issues or bugs
- [ ] Gather suggestions for improvements

#### Step 5.2: Public Launch
- [ ] Post on LinkedIn (showcase to potential employers)
- [ ] Share in biotech communities (Reddit, forums)
- [ ] Submit to relevant directories/lists
- [ ] Add to portfolio/resume

#### Step 5.3: Ongoing Maintenance
- [ ] Set up issue templates for corrections/additions
- [ ] Monthly check for new companies
- [ ] Update funding/stage information periodically
- [ ] Respond to community contributions

---

## Open Questions & Decisions Needed

### Data
- [ ] Should we expand beyond Bay Area to include Sacramento, other NorCal regions?
- [ ] Include CROs (contract research orgs) and CDMOs (manufacturing)?
- [ ] Include biotech-adjacent (ag-tech, food-tech, climate-tech using bio)?

### Map
- [ ] Color-code markers by: Company Size, Technology Focus, or Stage? (or user selectable?)
- [ ] Single map or separate maps for different regions?

### Scope
- [ ] Target audience: Job seekers only, or broader (investors, researchers)?
- [ ] Monetization: Keep 100% free, or explore sponsorship/premium features later?

---

## Success Metrics

### For Job Seekers:
- Easy to discover companies in specific locations
- Filter by relevant criteria (size, stage, tech focus)
- Quick access to company websites and careers pages

### For Portfolio/Career Showcase:
- Demonstrates data collection and cleaning skills
- Shows Python/scripting capabilities
- Exhibits web development (if custom map)
- Highlights initiative and project management

### For Community:
- Used and cited by other job seekers
- Receives contributions/corrections from community
- Grows to include 200+ Bay Area biotech companies

---

## Timeline Estimate

**Assuming ~5-10 hours/week effort**:

| Phase | Estimated Time | Target Completion |
|-------|----------------|-------------------|
| Phase 0: Foundation | 2 hours | Week 1 |
| Phase 1: Data Consolidation | 5-8 hours | Week 2 |
| Phase 2: Data Enrichment | 10-15 hours | Weeks 3-4 |
| Phase 3: Map Creation | 8-12 hours | Week 5 |
| Phase 4: Repository Polish | 3-5 hours | Week 6 |
| **Total** | **28-42 hours** | **6 weeks** |

**Fast track options**:
- Phase 2 can be done incrementally (top 50 companies first)
- Phase 3 can use Google My Maps for quick launch
- Community contributions can speed up data enrichment

---

## Notes & Resources

### Geocoding Services
- **Free**: geopy with Nominatim (rate-limited)
- **Paid**: Google Maps Geocoding API (~$5/1000 requests)
- **Batch**: Texas A&M Geocoding Service (free for academic use)

### Company Data Sources
- **Crunchbase**: Best for funding, size, founded date (API or manual)
- **LinkedIn**: Company pages have size, description, employee count
- **PitchBook**: Venture capital/PE database (requires subscription)
- **Company websites**: Most accurate for description and careers links

### Map Libraries
- **Leaflet.js**: Most popular open-source mapping library
- **Mapbox**: Beautiful maps but requires API key (free tier available)
- **Google Maps**: Familiar but requires API key and billing

---

## Future Enhancements (v3+)

- [ ] Add job posting aggregation (link to Greenhouse, Lever, etc.)
- [ ] Include diversity/culture data (if publicly available)
- [ ] Add company blog posts or news feeds
- [ ] Create "similar companies" recommendations
- [ ] Historical data (track company growth over time)
- [ ] Export filtered results to CSV
- [ ] Mobile app version
- [ ] Email alerts for new companies in favorite categories

---

**Last Updated**: January 8, 2025
**Project Owner**: Jaden Shirkey
**Status**: Phase 0 - Planning & Foundation
