# East Bay Biotech Map - Project Notes & History

**PURPOSE**: Internal working document containing project evolution, decisions, dataset comparisons, and merge strategies.

**AUDIENCE**: Project owner (Jaden) + Claude for context during active work

**Last Updated**: November 8, 2025

---

## Table of Contents

1. [Project Vision & Principles](#project-vision--principles)
2. [Project Evolution (V1 → V2)](#project-evolution-v1--v2)
3. [Current State & Files](#current-state--files)
4. [Project Phases](#project-phases)
5. [Dataset Comparison & Merge Analysis](#dataset-comparison--merge-analysis)
6. [Sample Company Analysis](#sample-company-analysis)
7. [Open Questions & Decisions](#open-questions--decisions)
8. [Success Metrics](#success-metrics)
9. [Timeline & Effort Estimates](#timeline--effort-estimates)
10. [Future Enhancements (V4+)](#future-enhancements-v4)

---

## Project Vision & Principles

### Vision
Create a comprehensive, publicly accessible map of biotechnology companies across the entire San Francisco Bay Area to help:
- **Job seekers** explore biotech opportunities
- **Researchers** understand the regional ecosystem
- **Entrepreneurs** identify potential partners or competitors
- **Investors** track the biotech landscape

### Key Principles
- Universal utility (not personal rankings)
- Rich company data (size, funding, focus areas)
- Interactive and filterable
- Well-documented and maintainable

---

## Project Evolution (V1 → V2)

### V1: Initial East Bay Focus
- Started with East Bay focused dataset
- 73-74 companies
- Used "Tier 1/2/3" personal rankings
- Visualized on Google My Maps

### V2: Expanded Bay Area Coverage
- Expanded to entire San Francisco Bay Area
- 319 companies (as of final merge)
- Removed personal rankings for universal utility
- Enhanced data collection and validation processes
- Professional documentation and reproducible methodology

---

## Current State & Files

### Primary Data Files

1. **data/final/companies.csv** (319 companies - POST MERGE)
   - Production dataset
   - Complete Bay Area coverage
   - Comprehensive validation and enhancement
   - **This is the deliverable**

2. **data/working/**
   - Staging area for 70/10 workflow (Phase 2)
   - Work-in-progress files for current enhancement phase

### Python Scripts (`/scripts/`)

Located in `/scripts/` to showcase computational skills:
- `add_addresses.py` - Add addresses to company list
- `add_pasted_addresses.py` - Import manually found addresses
- `company_addresses.py` - Address lookup/validation
- `create_addresses_csv.py` - Generate CSV with address column
- `update_addresses.py` - Update existing address data
- `fetch_careers_urls.py` - Careers link discovery
- `merge_csv_files.py` - Data consolidation
- `validate_urls.py` - URL validation

### Map Visualization

**Google My Maps v1**:
- Link: https://www.google.com/maps/d/u/0/edit?mid=1ilB4lPNTYk8O5bgUxavsIbZw_yPN4pU&usp=sharing
- 73-172 companies (depending on version imported)
- Basic markers with company info

---

## Project Phases

### ✅ Phase 0: Foundation (COMPLETE)
- [x] Initialize git repository
- [x] Create README and LICENSE
- [x] Create organized folder structure (`/data/`, `/scripts/`, `/docs/`)
- [x] Update .gitignore to showcase scripts but hide personal files
- [x] Document project plan

### ✅ Phase 1: Data Consolidation & Cleaning (COMPLETE)

**Goal**: Create single, clean CSV with all Bay Area companies

#### Step 1.1: Initial Merge & Deduplicate ✓
- [x] Started with `east_bay_biotech_v2.csv` (172 companies) as base
- [x] Cross-referenced with `with_addresses.csv` for better East Bay addresses
- [x] Removed duplicate entries
- [x] Standardized column names and formats
- [x] Removed personal ranking columns (Tier/Relevance)
- [x] **Output**: `data/working/companies_merged.csv` (171 companies)

#### Step 1.2: Second Merge - V2 Dataset Integration
- [x] Compared CSV (124 companies) with TXT V2 dataset (181 companies)
- [x] Identified 156 net-new companies
- [x] Resolved 25 overlapping companies with conflicts
- [x] Created merge strategy (see detailed analysis below)
- [x] **Output**: Expanded to 280+ companies

#### Step 1.3: Address Validation ✓
- [x] All companies have addresses (100% coverage achieved)
- [x] Addresses are in full street format
- [x] Ready for geocoding (when needed for map)

**Final Deliverable**: ✅ `data/final/companies.csv` with 319 Bay Area companies

### 📝 Phase 2: Enhance Careers Links (CURRENT PHASE)

**Goal**: Replace "Check Website" placeholders with direct careers page URLs

**Why This Matters**:
- Job seekers need ONE-CLICK access to job postings
- This is the highest-value enhancement for our target audience
- Showcases systematic data collection and web research skills

**Current Column Schema** (finalized):
```
✓ Company Name
✓ Website
✓ City
✓ Address
✓ Company Stage
✓ Notes
→ Hiring (TO BE ENHANCED)
```

**Using 70/10 Workflow**:
- Focus on top 70% of companies (by priority/relevance)
- Validate quality with 10% sampling
- Iterate and improve process

#### Current Tasks
- [ ] Collect careers URLs for all companies
  - Priority: ATS systems (Greenhouse, Lever, Workday, SmartRecruiters)
  - Fallback: Company careers pages
  - Script: `scripts/fetch_careers_urls.py`
- [ ] Validate and clean URLs
  - Test accessibility (not 404)
  - Ensure direct links
  - Standardize format
  - Script: `scripts/validate_urls.py`
- [ ] Save final dataset with careers links

### 🔧 Phase 3: Data Quality Cleanup (CURRENT - V3)

**Goal**: Ensure data accuracy and consistency before map publication

**Why This Matters**:
- Geographic scope must align with Bay Area boundaries per METHODOLOGY.md
- City/Address consistency ensures accurate map placement
- Website verification prevents user confusion and dead links
- Company Stage classification enables proper filtering and categorization

**Priority Issues Identified (January 2025 Audit)**:

#### 🔴 Critical - Data Accuracy
- [ ] **Fix 161 City vs Address discrepancies**
  - Many companies listed in wrong city (e.g., listed as "San Francisco" but address is "South San Francisco")
  - Impact: Incorrect map placement and filtering
  - Method: Parse address field, extract actual city, update City column
  - Estimated effort: 2-3 hours (scripted)

- [ ] **Review 23 companies with non-CA/international addresses**
  - Companies showing addresses outside California (some in MD, DC, UK, India)
  - Examples: Achira (Bengaluru, India), Coherence Neuro (Cambridge, UK), Eicos Sciences (Chevy Chase, MD)
  - Method: Research each company to determine if they have Bay Area office
  - Decision: Remove if no Bay Area presence OR update address to Bay Area location
  - Estimated effort: 3-4 hours (manual research required)

- [ ] **Remove 2 Davis companies (outside Bay Area scope)**
  - Davis is in Yolo County, explicitly excluded per METHODOLOGY.md Appendix A
  - Companies: ARIZ Precision Medicine, Antibodies Incorporated
  - Impact: Keeps dataset aligned with documented geographic scope
  - Estimated effort: 5 minutes

#### 🟡 Medium Priority - Data Quality Improvements
- [ ] **Investigate website mismatches from Google API workflow**
  - Some companies may have incorrect websites from Google Places API
  - API may have matched wrong business with similar name
  - Method: Spot-check companies enriched via Google Maps API, verify website matches company
  - Cross-reference with Wikipedia/BioPharmGuy source data
  - Estimated effort: 4-5 hours (validation + corrections)

- [ ] **Review and improve Company Stage classifications**
  - Many companies auto-classified as "Unknown" by keyword heuristics in `enrich_with_google_maps.py`
  - Others may be incorrectly classified (e.g., classified as "Startup" but actually "Commercial")
  - Method: Manual review of company websites and descriptions
  - Priority: Focus on companies marked "Unknown" first
  - Estimated effort: 6-8 hours (manual research)

- [ ] **Add Data Source tracking column** (optional enhancement)
  - Currently no way to trace which companies came from Wikipedia vs BioPharmGuy vs Google Maps
  - Add "Data Source" column: Wikipedia, BioPharmGuy, Google Maps API, Manual Entry
  - Helps with future audits and data provenance
  - Estimated effort: 2-3 hours (scripted + manual tagging)

**Total Estimated Effort**: 18-26 hours

**Success Criteria**:
- 100% of companies have Bay Area addresses (CA only)
- City column matches Address city field
- All websites verified and accessible
- <5% companies marked "Unknown" for Company Stage
- Data source documented for all entries

### 🗺️ Phase 4: Map Creation & Visualization (PLANNED)

**Goal**: Create interactive, embeddable map with filtering capabilities

**Map Options**:
1. **Google My Maps** - Easy, limited customization
2. **Custom Leaflet.js** - Full control, more work
3. **Hybrid Approach** (Recommended) - Quick v2 with Google, plan for custom migration

**Tasks**:
- [ ] Choose map platform
- [ ] Import/load company data
- [ ] Configure markers and colors
- [ ] Set up filtering (by city, size, stage, tech focus)
- [ ] Deploy/embed map

### 📦 Phase 5: Repository Polish & Documentation (PLANNED)

**Goal**: Professional, well-organized GitHub repository

**Tasks**:
- [ ] Finalize file structure
- [ ] Complete documentation (README, DATA_DICTIONARY, CONTRIBUTING)
- [ ] Clean commit history
- [ ] Tag major versions (v1.0, v2.0, etc.)

### 🚀 Phase 6: Launch & Maintenance (PLANNED)

**Tasks**:
- [ ] Soft launch (friends/colleagues feedback)
- [ ] Public launch (LinkedIn, biotech communities)
- [ ] Ongoing maintenance (monthly checks, community contributions)

---

## Dataset Comparison & Merge Analysis

### Historical Context: CSV vs TXT V2 Dataset Comparison

This section documents the analysis performed during Phase 1 when integrating the V2 dataset.

#### Executive Summary

| Metric | Value |
|--------|-------|
| Companies in CSV (Final) | 124 |
| Companies in TXT (V2) | 181 |
| Companies in Both | 25 |
| **Net-New Companies** | **156** |
| Overlapping with Conflicts | 24 |
| **Total After Merge** | **280** |

#### Data Quality Assessment

**CSV Dataset Strengths:**
- Complete street addresses for all companies (100%)
- Proper website URLs with `https://` prefix
- Detailed "Notes" field with company description
- Company stage classification (Commercial, Clinical, Pre-clinical, etc.)

**CSV Dataset Weaknesses:**
- Less comprehensive (only 124 companies initially)
- Some outdated information on acquired/closed companies

**TXT V2 Dataset Strengths:**
- Much more comprehensive (181 companies)
- Includes many newer startups and emerging companies
- Recent data (companies like Altos Labs, various AI-driven companies)
- Geographic expansion to less-known biotech areas

**TXT V2 Dataset Weaknesses:**
- Missing all street addresses
- Plain domain names without `https://` prefix
- Less detailed descriptions (only "Focus Area" field)
- No company stage classification

#### Conflict Analysis

**Types of Conflicts Found:**

| Conflict Type | Count | Notes |
|--------------|-------|-------|
| Website Format | 25 | CSV: `https://domain.com` vs TXT: `domain.com` |
| Missing Address (TXT) | 156 | All new companies had empty address field |
| City Mismatch | 3 | Accelero Biostructures, Addition Therapeutics, Actym Therapeutics |
| Name Variation | 1 | AcureX Biosciences vs AcureX Therapeutics |

#### Problematic Overlaps Requiring Manual Review

1. **Accelero Biostructures**
   - CSV: San Francisco | TXT: San Carlos
   - CSV Address: 156 2ND ST, San Francisco, CA 94105
   - **Resolution**: Kept CSV data (has San Francisco zip code)

2. **Addition Therapeutics**
   - CSV: Berkeley | TXT: South San Francisco
   - CSV Address: 2630 Bancroft Way, Berkeley, CA 94704
   - **Resolution**: Verified actual headquarters location

3. **Actym Therapeutics**
   - CSV: Listed as Berkeley | CSV Address: 717 Market St, San Francisco, CA 94103 (conflicting!)
   - TXT: Berkeley
   - **Resolution**: Updated city to San Francisco to match address

#### Merge Strategy (How We Got to 319 Companies)

**Phase 1: Add All New Companies**
- Added 156 companies from TXT file to CSV
- Used CSV schema: Company Name, Address, City, Website, Company Stage, Notes
- For new companies:
  - Filled Company Name, City, Website from TXT
  - Left Address field empty (researched later)
  - Set Company Stage based on focus area classification
  - Used Focus Area as Notes

**Phase 2: Validate Overlapping Companies**
- Verified the 3 companies with city conflicts
- Kept CSV address data (more complete and reliable)
- Updated website URLs to include `https://` prefix for consistency

**Phase 3: Data Enrichment (Post-Merge)**
- Researched and filled in missing addresses for new companies
- Standardized website URLs
- Classified company stages for the 156 new companies
- Expanded/improved descriptions where needed

**Phase 4: Final Dataset**
- **Total Companies:** 319 (after deduplication and enhancement)
- **Data Completeness Achieved:**
  - Address: 100%
  - Website: 100%
  - City: 100%
  - Company Stage: 100%
  - Notes/Focus Area: 100%

#### Geographic Distribution

**Original 124 Companies - Key Cities:**
- South San Francisco: 28
- Emeryville: 16
- Berkeley: 12
- San Francisco: 10
- Redwood City: 9

**156 New Companies - Geographic Expansion:**
- **Additional Cities:** Livermore, Orinda, Danville, Larkspur, Campbell
- **Improved Coverage:** Santa Clara, San Jose, Palo Alto, Mountain View regions
- **Remote/Outlier Locations:** Half Moon Bay, Morgan Hill, San Ramon

#### Key Data Quality Issues Identified & Resolved

1. **ADDRESS COMPLETENESS**
   - Problem: TXT file had NO street addresses (0/181)
   - Solution: Manual research and automated lookup completed
   - Status: ✅ All addresses filled

2. **WEBSITE FORMAT INCONSISTENCY**
   - Problem: CSV used https://domain.com, TXT used domain.com
   - Solution: Standardized all URLs to https:// format during merge
   - Status: ✅ Completed

3. **LOCATION VALIDATION**
   - Problem: 3 companies had conflicting city data
   - Solution: Manual research to verify correct locations
   - Status: ✅ Resolved

4. **COMPANY STAGE CLASSIFICATION**
   - Problem: TXT had no company stage field - only "Focus Area"
   - Solution: Classified based on focus area descriptions and web research
   - Status: ✅ All companies classified

5. **DESCRIPTION DEPTH**
   - Problem: TXT used brief "Focus Area" vs CSV's detailed "Notes"
   - Solution: Enriched post-merge with additional research
   - Status: ✅ Enhanced

---

## Sample Company Analysis

### Examples of Net-New Companies Added (from 156 total)

1. **1Cell.Ai**
   - City: Cupertino
   - Website: 1cell.ai
   - Focus: Cancer diagnostics
   - Stage: Pre-clinical/Startup

2. **Altos Labs**
   - City: Redwood City
   - Website: altoslabs.com
   - Focus: Cellular rejuvenation (aging)
   - Stage: Pre-clinical/Startup
   - Note: High-profile startup founded by reputable investors

3. **Amgen (Bay Area)**
   - City: South San Francisco
   - Website: amgen.com
   - Focus: Biologics & small-molecule drugs
   - Stage: Large Pharma

4. **AstraZeneca (Bay Area)**
   - City: South San Francisco
   - Website: astrazeneca.com
   - Focus: Biologics & vaccines R&D
   - Stage: Large Pharma

5. **Artificial**
   - City: Palo Alto
   - Website: artificial.com
   - Focus: AI lab automation platform
   - Stage: Pre-clinical/Startup

6. **Atomic AI**
   - City: South San Francisco
   - Website: atomic.ai
   - Focus: AI-driven RNA drug discovery
   - Stage: Pre-clinical/Startup

7. **Applied Viromics**
   - City: Fremont
   - Website: appliedviromics.com
   - Focus: Custom viral vectors
   - Stage: Tools/Services/CDMO

### Merge Impact Analysis

**POSITIVE IMPACTS:**
- ✓ 156 additional companies expanded coverage from 124 to 280 (+126%)
- ✓ Better geographic distribution across Bay Area (not just Peninsula)
- ✓ Includes emerging startups and AI-driven companies
- ✓ More comprehensive database for investors and researchers
- ✓ Better regional representation beyond traditional biotech hubs

**CHALLENGES ADDRESSED:**
- ⚠ All 156 new companies missing street addresses → ✅ Resolved
- ⚠ Website format standardization needed → ✅ Completed
- ⚠ Company stage classification needed → ✅ Completed
- ⚠ 3 companies needed location verification → ✅ Resolved
- ⚠ Descriptions needed enhancement → ✅ Enhanced

**EFFORT ESTIMATE (Actual):**
- Address research: 2-4 hours (automated + manual)
- Location verification: 30 minutes (3 companies)
- Website URL standardization: 15 minutes (automated)
- Company stage classification: 1-2 hours
- Description enhancement: 2-3 hours
- Testing and validation: 1 hour
- **Total Actual Effort: ~8 hours**

---

## Open Questions & Decisions

### Data Scope
- [ ] Should we expand beyond Bay Area to include Sacramento, other NorCal regions?
- [ ] Include CROs (contract research orgs) and CDMOs (manufacturing)?
- [ ] Include biotech-adjacent (ag-tech, food-tech, climate-tech using bio)?

### Map Features
- [ ] Color-code markers by: Company Size, Technology Focus, or Stage? (or user selectable?)
- [ ] Single map or separate maps for different regions?

### Project Scope
- [ ] Target audience: Job seekers only, or broader (investors, researchers)?
- [ ] Monetization: Keep 100% free, or explore sponsorship/premium features later?

---

## Success Metrics

### For Job Seekers
- Easy to discover companies in specific locations
- Filter by relevant criteria (size, stage, tech focus)
- Quick access to company websites and careers pages

### For Portfolio/Career Showcase
- Demonstrates data collection and cleaning skills
- Shows Python/scripting capabilities
- Exhibits web development (if custom map)
- Highlights initiative and project management

### For Community
- Used and cited by other job seekers
- Receives contributions/corrections from community
- Grows to include 500+ Bay Area biotech companies (expansion goal)

---

## Timeline & Effort Estimates

**Assuming ~5-10 hours/week effort**:

| Phase | Estimated Time | Status |
|-------|----------------|--------|
| Phase 0: Foundation | 2 hours | ✅ Complete |
| Phase 1: Data Consolidation | 5-8 hours | ✅ Complete (8 hours actual) |
| Phase 2: Data Enrichment (Careers Links) | 10-15 hours | 🔄 In Progress |
| Phase 3: Data Quality Cleanup | 18-26 hours | 🔄 Current (V3) |
| Phase 4: Map Creation | 8-12 hours | 📅 Planned |
| Phase 5: Repository Polish | 3-5 hours | 📅 Planned |
| **Total** | **46-68 hours** | **~40% Complete** |

---

## Future Enhancements (V4+)

Potential features for future iterations:

- [ ] Add job posting aggregation (link to Greenhouse, Lever, etc.)
- [ ] Include diversity/culture data (if publicly available)
- [ ] Add company blog posts or news feeds
- [ ] Create "similar companies" recommendations
- [ ] Historical data (track company growth over time)
- [ ] Export filtered results to CSV
- [ ] Mobile app version
- [ ] Email alerts for new companies in favorite categories
- [ ] Scale to 500+ companies across entire Bay Area
- [ ] Interactive filtering and search on embedded map
- [ ] Company comparison features

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

**Project Owner**: Jaden Shirkey
**Repository**: https://github.com/jadenshirkey/EastBayBiotechMap
**Status**: Phase 2 - Careers Link Enhancement (70/10 Workflow)
