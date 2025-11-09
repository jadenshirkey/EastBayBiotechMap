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
| **Tags** | Keywords | 1-3 controlled keywords (comma-separated) | "CRISPR, gene-therapy" or "antibody, oncology" | Recommended |
| **Notes** | Text | Brief description (1-2 sentences) | "CRISPR editors with in vivo delivery for oncology" | Optional |
| **Hiring** | Text | Hiring status or careers link | "Check Website", URL to careers page | Optional |

### Tags - Controlled Vocabulary

Use 1-3 keywords from this list (comma-separated):

**Therapeutics Modalities**:
- `antibody` - Antibodies, ADCs, bispecifics, Fc engineering
- `CRISPR` - CRISPR/Cas, base editors, prime editors
- `gene-therapy` - AAV, lentiviral, or other viral vectors
- `cell-therapy` - CAR-T, TCR-T, NK cells, stem cells
- `RNA` - mRNA, siRNA, ASO, RNA editing
- `small-molecule` - Traditional small molecule drugs
- `protein-engineering` - Protein design, engineering, enzymes
- `TPD` - Targeted protein degradation, PROTACs, molecular glue

**Disease Areas**:
- `oncology` - Cancer therapeutics
- `neurology` - Neurological/neurodegenerative diseases
- `rare-disease` - Orphan/rare diseases
- `autoimmune` - Autoimmune and inflammatory diseases

**Tools/Services**:
- `CDMO` - Contract development & manufacturing
- `CRO` - Contract research organization
- `diagnostics` - Diagnostic tests, companion diagnostics
- `platform` - Technology platform/tools for drug discovery
- `synthetic-biology` - Engineered organisms, metabolic engineering
- `AI-ML` - AI/ML for drug discovery or biotech

**Other**:
- `GMP-CMC` - Manufacturing, process development, quality

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

1. **Add Tags column** - Controlled keywords for filtering (2-3 hours for 171 companies)
2. **Enhance Hiring column** - Direct careers URLs (2-3 hours for top 100 companies)
3. **Simplify Company Stage** - Use proxy signals, mark Unknown if unclear (1 hour)
4. **Run QC checklist** - Validate data quality (30 min)

### Tags Strategy (NEW - High Value)

Add a "Tags" column with 1-3 controlled keywords per company:
- Scan website homepage and existing Notes
- Pick 1-3 tags from controlled vocabulary (see above)
- If unclear after 30 seconds, leave blank and move on
- **Don't overthink it** - 80% coverage is good enough

**Example**:
- "CRISPR gene therapy company" → `CRISPR, gene-therapy, oncology`
- "Antibody discovery platform" → `antibody, platform`
- "Contract manufacturer" → `CDMO, GMP-CMC`

### Hiring Enhancement Strategy (SIMPLIFIED)

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
- [ ] 80%+ companies have at least 1 tag
- [ ] Company Stage is filled (use "Unknown" if unclear)
- [ ] Addresses contain city name and CA
- [ ] Top 50 companies have careers links

**Deduplication (Simple Rules)**:
- [ ] Same domain = duplicate (keep one, merge data)
- [ ] Same address = duplicate (investigate, merge if same company)

**Spot Checks (Sample 10-20 companies)**:
- [ ] Website loads (not 404)
- [ ] Tags make sense for company focus
- [ ] Address is in correct city
- [ ] Not obviously closed/moved

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
