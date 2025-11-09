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

## Installation

```bash
pip install -r requirements.txt
```

## Workflow

This implements **Phase 1: Company Discovery** from the methodology:

```
Wikipedia Sources              BioPharmGuy Directory
(3 pages, automated)           (Northern CA, automated)
        ↓                              ↓
extract_wikipedia_companies.py   extract_biopharmguy_companies.py
        ↓                              ↓
wikipedia_companies.csv           biopharmguy_companies.csv
(~201 companies)                  (~1,116 companies)
        ↓                              ↓
        └──────────┬───────────────────┘
                   ↓
         Manual deduplication
                   ↓
         Manual enrichment (Phases 2-4)
      (Website, Address, Company Stage)
                   ↓
          data/final/companies.csv
```

## Future Enhancements

Following scripts may be added:
- `extract_linkedin.py` - LinkedIn company search automation
- `merge_sources.py` - Automated deduplication across sources
- `enrich_addresses.py` - Geocoding and address standardization

## Dependencies

- Python 3.7+
- requests - HTTP library for fetching web pages
- beautifulsoup4 - HTML parsing

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

## Documentation

- `/METHODOLOGY.md` - Complete data collection methodology
- `/docs/DATA_DICTIONARY.md` - Field definitions and validation rules
- `/docs/WORKFLOW.md` - Step-by-step procedures

---

**Last Updated**: January 2025
**Version**: V3
