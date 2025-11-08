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
| **Notes** | Text | Technology platform or focus areas | "Synthetic biology platform for organism engineering" | Yes |
| **Hiring** | Text | Hiring status or careers link | "Check Website", URL to careers page | Optional |

### Company Stage Values

- **Startup** / **Pre-clinical/Startup**: Early-stage companies in R&D
- **Clinical-Stage Biotech**: Companies with therapies in clinical trials
- **Commercial-Stage Biotech**: Companies with marketed products
- **Tools/Services/CDMO**: Service providers, contract manufacturers, tool/instrument makers
- **Academic/Gov't**: Research institutions, government labs
- **Acquired**: Companies that have been acquired by larger entities

---

## Phase 2 Enhancement (In Progress)

**Focus**: Enhancing the "Hiring" column with direct careers page URLs

| Enhancement | Type | Description | Example Values | Source |
|-------------|------|-------------|----------------|--------|
| **Hiring** (enhanced) | URL | Direct link to jobs/careers page | "https://boards.greenhouse.io/ginkgo" or "https://company.com/careers" | ATS platforms, company websites |

**Why We're Not Adding Other Columns**:
- ❌ **Latitude/Longitude**: Addresses auto-geocode in Google My Maps or Leaflet.js (no manual work needed)
- ❌ **Description**: Already have "Notes" field with excellent descriptions
- ❌ **Technology Focus**: Redundant with "Notes" field; hard to standardize
- ❌ **Company Size**: Overlaps with "Company Stage"; requires LinkedIn/Crunchbase access
- ❌ **Founded Year**: Low utility for job seekers
- ❌ **Funding Status**: Requires paid Crunchbase subscription; data goes stale quickly

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

### Phase 3: Validation (Planned)
1. Validate all URLs (check for 404s)
2. Verify address formats
3. Check for duplicates
4. Validate coordinates are in Bay Area
5. Manual QA check on major companies

---

## Usage Guidelines

### For Map Visualization
- Use **Latitude** and **Longitude** for marker placement
- Color-code markers by **Company Size**, **Technology Focus**, or **Company Stage**
- Display **Description**, **Website**, **Careers Link** in popup windows

### For Filtering
Primary filter dimensions:
- **City** (dropdown or checkboxes)
- **Company Stage** (dropdown)
- **Company Size** (once added)
- **Technology Focus** (once added, may be multi-select)

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
