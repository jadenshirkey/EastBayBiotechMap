# Data Extraction Scripts - V3

This folder contains automated scripts for extracting biotech/pharma company data according to the methodology documented in `/METHODOLOGY.md`.

## Philosophy

Following the **70% coverage with 10% effort** principle:
- Automated extraction from high-quality sources
- Simple, focused scripts that do one thing well
- Manual enrichment for fields requiring judgment

## Scripts

### `extract_wikipedia_companies.py`

**Purpose**: Automated extraction of company names from Wikipedia sources

**What it does**:
- Fetches 3 Wikipedia pages:
  - List of biotechnology companies
  - Pharmaceutical companies of the United States (category)
  - Companies based in San Francisco Bay Area (category)
- Extracts company names and Wikipedia URLs
- Filters for Bay Area cities (using methodology whitelist)
- Auto-deduplicates by company name
- Outputs to `data/working/wikipedia_companies.csv`

**Output columns**:
- Company Name
- Source URL (Wikipedia page)
- City (if detected)
- Notes

**Usage**:
```bash
# Install dependencies
pip install -r requirements.txt

# Run extraction
cd scripts
python3 extract_wikipedia_companies.py
```

**Output location**: `data/working/wikipedia_companies.csv`

**Next steps after running**:
1. Review CSV and remove non-biotech companies
2. Manually enrich with: Website, Address, Company Stage, Focus Areas
3. Merge with existing `data/final/companies.csv`

---

### `extract_biopharmguy_companies.py`

**Purpose**: Automated extraction of company names from BioPharmGuy Northern California directory

**What it does**:
- Fetches BioPharmGuy Northern California companies page
- Parses HTML table structure (company, location, description)
- Filters for Bay Area cities only
- Auto-deduplicates by company name
- Outputs to `data/working/biopharmguy_companies.csv`

**Output columns**:
- Company Name
- Source URL
- City
- Focus Area (from description field)
- Notes

**Usage**:
```bash
cd scripts
python3 extract_biopharmguy_companies.py
```

**Output location**: `data/working/biopharmguy_companies.csv`

**Expected yield**: ~1,100 Bay Area biotech/pharma companies

**Advantages**:
- Pre-filtered to Northern California
- Includes focus area descriptions
- City names in consistent format
- Higher volume than Wikipedia

---

### `merge_company_sources.py`

**Purpose**: Merge and deduplicate companies from multiple sources

**What it does**:
- Combines Wikipedia, BioPharmGuy, and existing company data
- Deduplicates by normalized company name (removes Inc., LLC, etc.)
- Preserves complete data from existing dataset (priority: existing > BioPharmGuy > Wikipedia)
- Creates timestamped backup before merging
- Filters for Bay Area cities only

**Output columns**:
- Company Name
- Website
- City
- Address
- Company Stage
- Focus Areas

**Usage**:
```bash
cd scripts
python3 merge_company_sources.py
```

**Input files**:
- `../data/final/companies.csv` (existing dataset - highest priority)
- `../data/working/wikipedia_companies.csv`
- `../data/working/biopharmguy_companies.csv`

**Output**: Updated `../data/final/companies.csv` + backup created

**What gets merged**:
- Existing companies: preserved with all data
- New from BioPharmGuy: added with city + focus areas
- New from Wikipedia: added only if Bay Area city confirmed

---

### `enrich_with_google_maps.py`

**Purpose**: Enrich company data using Google Maps Places API

**What it does**:
- Searches Google Maps for companies missing addresses/websites
- Retrieves verified addresses, websites, phone numbers, and coordinates
- Auto-classifies company stage using keyword heuristics
- Saves progress every 50 companies (safe for interruption)
- Generates detailed enrichment report

**Output columns enriched**:
- Address (formatted street address)
- Website (verified URL)
- Company Stage (if not already set)
- Coordinates (latitude/longitude for mapping)

**Usage**:
```bash
# Set your Google Maps API key
export GOOGLE_MAPS_API_KEY="your-api-key-here"

# Run enrichment
cd scripts
python3 enrich_with_google_maps.py
```

**Requirements**:
- Google Cloud Platform account
- Places API enabled
- Billing enabled (Places API is not free)
- API key with Places API access

**Output**:
- Updated `../data/final/companies.csv`
- `../data/working/enrichment_report.txt` (statistics and companies not found)

**Rate limiting**: 0.1 second delay between API calls to respect limits

**Cost estimate**: ~$0.032 per company lookup (Places API pricing)

---

## Installation

```bash
pip install -r requirements.txt
```

## Complete Workflow

This implements the full data pipeline from discovery to enrichment:

```
Step 1: Extract from Sources
─────────────────────────────────────────────────
Wikipedia Sources              BioPharmGuy Directory
(3 pages, automated)           (Northern CA, automated)
        ↓                              ↓
extract_wikipedia_companies.py   extract_biopharmguy_companies.py
        ↓                              ↓
wikipedia_companies.csv           biopharmguy_companies.csv
(~200 companies)                  (~1,100 companies)

Step 2: Merge & Deduplicate
─────────────────────────────────────────────────
        └──────────┬───────────────────┘
                   ↓
         merge_company_sources.py
         (existing + new sources)
                   ↓
          Deduplication by normalized name
          Backup created automatically
                   ↓
          data/final/companies.csv
              (merged dataset)

Step 3: Enrich Missing Data
─────────────────────────────────────────────────
      enrich_with_google_maps.py
    (Google Places API - requires key)
                   ↓
    Finds addresses, websites, coordinates
    Auto-classifies company stages
                   ↓
          data/final/companies.csv
         (complete, verified data)
               1,210 companies
```

**Run in sequence**:
```bash
# 1. Extract new companies
python3 extract_wikipedia_companies.py
python3 extract_biopharmguy_companies.py

# 2. Merge with existing data
python3 merge_company_sources.py

# 3. Enrich missing fields
export GOOGLE_MAPS_API_KEY="your-key"
python3 enrich_with_google_maps.py
```

## Future Enhancements

Potential future scripts:
- `extract_linkedin.py` - LinkedIn company search automation
- `validate_data.py` - Automated data quality checks
- `cleanup_backups.py` - Remove old backup files

## Dependencies

- Python 3.9+
- requests >= 2.31.0 - HTTP library for fetching web pages
- beautifulsoup4 >= 4.12.0 - HTML parsing
- googlemaps >= 4.10.0 - Google Maps Places API client (for enrichment script only)

See `requirements.txt` for complete list.

## Troubleshooting

**Error: "No module named 'requests'"**
- Run: `pip install -r requirements.txt`

**Error: "Failed to fetch page"**
- Check internet connection
- Wikipedia may be temporarily unavailable
- Try again in a few minutes

**Too many/few companies extracted**
- Script uses loose filtering (includes most candidates)
- Manual review is expected per methodology
- Adjust `BAY_AREA_CITIES` set in script if needed

**Google Maps API errors**
- Verify API key is set: `echo $GOOGLE_MAPS_API_KEY`
- Check Places API is enabled in Google Cloud Console
- Verify billing is enabled (Places API requires it)
- Check API quotas and limits

**Merge script creates duplicate backups**
- Backup files are timestamped: `companies_backup_YYYYMMDD_HHMMSS.csv`
- Safe to delete old backups, keep most recent
- Located in `data/final/`

## Documentation

- `/METHODOLOGY.md` - Complete data collection methodology
- `/docs/DATA_DICTIONARY.md` - Field definitions and validation rules
- `/docs/WORKFLOW.md` - Step-by-step procedures

---

**Last Updated**: January 2025
**Version**: V3
