# Data Dictionary

Documentation for the Bay Area Biotech Map dataset.

## Current Files

### Production Data
- **Location**: `/data/working/companies_merged.csv`
- **Status**: Base file ready for enrichment
- **Companies**: 171 biotech companies across the Bay Area
- **Last Updated**: January 2025

### Archive Data
- **Location**: `/data/archive/`
- **Purpose**: Historical versions and source files for reference

---

## Column Definitions

### Current Columns (as of Phase 1)

| Column | Type | Description | Example | Required |
|--------|------|-------------|---------|----------|
| **Company Name** | Text | Official company name | "Ginkgo Bioworks" | Yes |
| **Website** | URL | Company website | "https://www.ginkgobioworks.com" | Yes |
| **City** | Text | City where company is located | "Emeryville" | Yes |
| **Address** | Text | Full street address | "5 Tower Place, Suite 100, Emeryville, CA 94608" | Recommended |
| **Company Stage** | Category | Development/commercial stage | "Clinical-Stage Biotech", "Commercial-Stage Biotech" | Yes |
| **Notes** | Text | Technology focus and brief description | "AAV gene therapy; capsid engineering" or "Synthetic biology platform" | Yes |
| **Hiring** | Text | Hiring status or careers link | "Check Website", URL to careers page | Optional |

**Note**: The Notes column already contains technology focus information (CRISPR, antibody, gene therapy, etc.), making it searchable and filterable without needing separate tags

### Company Stage Values

Use proxy signals for quick classification (don't spend time verifying):

- **Commercial-Stage Biotech**: "FDA-approved" or "marketed product" on website
- **Clinical-Stage Biotech**: "Phase 1/2/3" anywhere on website or ClinicalTrials.gov
- **Pre-clinical/Startup**: Developing therapeutics but no clinical trials yet
- **Tools/Services/CDMO**: Provides services, tools, instruments, or manufacturing
- **Large Pharma**: Fortune 500 scale with multiple Bay Area sites
- **Academic/Gov't**: Research institutions, government labs
- **Acquired**: Acquired by larger entity (note in Notes column)
- **Unknown**: If unclear, mark as Unknown and move on

---

## Phase 2 Enhancement (In Progress)

**Goal**: 70% quality with ~10% effort - add high-value, easy-to-collect data

### Enhancements (Priority Order)

1. **Enhance Hiring column** - Direct careers URLs (2-3 hours for top 100 companies)
2. **Simplify Company Stage** - Use proxy signals, mark Unknown if unclear (1 hour)
3. **Run QC checklist** - Validate data quality (30 min)

**Total Estimated Time**: 3.5-4.5 hours

### Hiring Enhancement Strategy

Focus on top 100 companies first (by size/stage):
1. Search `site:greenhouse.io "[Company Name]"` or `site:lever.co "[Company Name]"`
2. If found: Add URL
3. If not found: Search `"[Company Name]" careers`
4. If nothing clear in 1 minute: Leave as "Check Website"

**Don't waste time on**:
- Broken links (validate later if needed)
- Companies with no clear careers page
- Startups with <10 employees

### What We're NOT Adding

- ❌ **Latitude/Longitude**: Addresses auto-geocode in mapping tools
- ❌ **Company Size**: Overlaps with Stage; hard to verify
- ❌ **Founded Year**: Low utility for job seekers
- ❌ **Funding Status**: Goes stale quickly; requires paid data

---

## Data Quality Notes

### Address Completeness
- **Current**: 171/171 companies have addresses (100%)
- Some addresses may be incomplete (city-only format)
- Full geocoding will require complete street addresses

### Geographic Scope
The dataset includes companies across the San Francisco Bay Area:
- **East Bay**: Emeryville, Berkeley, Oakland, Alameda, Fremont, etc.
- **Peninsula**: Palo Alto, Redwood City, San Carlos, South San Francisco
- **San Francisco**: SF proper
- **North Bay**: San Rafael, Novato
- **Tri-Valley**: Pleasanton

### Data Sources
All information is from publicly available sources:
- Company websites
- Crunchbase
- LinkedIn
- Press releases
- Business registries

---

## Data Processing Pipeline

### Phase 1: Consolidation (Completed)
1. Started with `east_bay_biotech_v2.csv` (172 companies, full Bay Area)
2. Cross-referenced with `east_bay_biotech_with_addresses.csv` (74 East Bay companies)
3. Merged address data where with_addresses had more complete information
4. Removed personal ranking column ("Relevance to Profile")
5. Output: `data/working/companies_merged.csv`

### Phase 2: Enhancement (In Progress)
1. Enhance "Hiring" column with direct careers page URLs
2. Search ATS platforms (Greenhouse, Lever, Workday, SmartRecruiters)
3. Search company careers pages
4. Validate URLs are accessible
5. Output: `data/final/companies.csv`

### Phase 3: QC Checklist (Quick Validation)

Run these simple checks before finalizing:

**Required Fields (MUST HAVE)**:
- [ ] All companies have: Name, Website, City, Address
- [ ] Website URLs start with `http://` or `https://`
- [ ] No duplicate company names (check sorted list)

**Quality Checks (SHOULD HAVE)**:
- [ ] Company Stage is filled (use "Unknown" if unclear)
- [ ] Addresses contain city name and CA
- [ ] Top 50 companies have careers links
- [ ] Notes field has technology focus info

**Deduplication (Simple Rules)**:
- [ ] Same domain = duplicate (keep one, merge data)
- [ ] Same address = duplicate (investigate, merge if same company)

**Spot Checks (Sample 10-20 companies)**:
- [ ] Website loads (not 404)
- [ ] Notes describe company focus accurately
- [ ] Address is in correct city
- [ ] Not obviously closed/moved

---

## Usage Guidelines

### For Map Visualization
- Use **Latitude** and **Longitude** for marker placement (auto-geocode from Address)
- Color-code markers by **Company Stage** or **City**
- Display **Notes**, **Website**, **Careers Link** in popup windows

### For Filtering
Primary filter dimensions:
- **City** (dropdown or checkboxes)
- **Company Stage** (dropdown)
- **Text search** in Notes field for technology keywords (CRISPR, antibody, etc.)

### For Analysis
This dataset can be used to:
- Analyze geographic clustering of biotech companies
- Understand stage distribution in the ecosystem
- Identify technology focus areas in the region
- Track funding trends (once funding data added)

---

## Changelog

### Version 1.0 (January 2025)
- Initial dataset created
- 171 companies across Bay Area
- Merged from multiple source files
- Personal rankings removed for universal utility

### Planned Updates
- v1.1: Add geocoding (lat/long)
- v1.2: Add company descriptions and size
- v1.3: Add funding and technology focus data
- v2.0: Full enrichment complete, production ready

---

## Contact & Contributions

To suggest corrections or additions:
- Open an issue on GitHub
- Provide: Company name, website, location, and data source
- For address corrections, please include full street address

**Maintainer**: Jaden Shirkey
**Last Updated**: January 8, 2025
