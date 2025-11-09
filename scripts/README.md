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

## Installation

```bash
pip install -r requirements.txt
```

## Workflow

This implements **Phase 1: Company Discovery** from the methodology:

```
Wikipedia Sources (automated)
    ↓
extract_wikipedia_companies.py
    ↓
data/working/wikipedia_companies.csv
    ↓
Manual enrichment (Phases 2-4)
    ↓
data/final/companies.csv
```

## Future Enhancements

Following scripts may be added:
- `extract_biopharmguy.py` - BioPharmGuy directory extraction
- `extract_linkedin.py` - LinkedIn company search
- `merge_sources.py` - Combine multiple extraction sources

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
