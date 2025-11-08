# Data Processing Scripts

This folder contains Python scripts used to build and maintain the Bay Area Biotech Map dataset.

## Scripts Overview

### 1. `add_addresses.py`
**Purpose**: Initialize the address collection process

**What it does**:
- Reads the base CSV file (`east_bay_biotech_combined_notes.csv`)
- Adds an empty `Address` column after the `City` column
- Creates a new file ready for address population
- Outputs: `east_bay_biotech_with_addresses.csv`

**Usage**:
```bash
python3 add_addresses.py
```

---

### 2. `company_addresses.py`
**Purpose**: Hardcoded address dictionary and update functionality

**What it does**:
- Contains a dictionary mapping company names to street addresses
- Reads the base CSV and inserts addresses where available
- Tracks progress (addresses filled vs. remaining)
- Shows which companies still need addresses

**Contains addresses for**:
- 10x Genomics
- 4D Molecular Therapeutics
- Caribou Biosciences
- _(Many others marked "To be searched")_

**Usage**:
```bash
python3 company_addresses.py
```

**Output**: `east_bay_biotech_with_addresses.csv` with addresses filled in

---

### 3. `add_pasted_addresses.py`
**Purpose**: Update CSV with manually found addresses

**What it does**:
- Provides a template for manually adding addresses that were found through web search
- Inserts Address column after City
- Useful when addresses were found manually and need to be batch-imported

**Usage**:
```bash
python3 add_pasted_addresses.py
```

---

### 4. `create_addresses_csv.py`
**Purpose**: Generate a fresh CSV structure with address column

**What it does**:
- Similar to `add_addresses.py`
- Creates the initial CSV structure with Address field
- Sets up the file for subsequent address population

**Usage**:
```bash
python3 create_addresses_csv.py
```

---

### 5. `update_addresses.py`
**Purpose**: General-purpose address updater

**What it does**:
- Updates existing CSV files with new address data
- Validates and formats address fields
- Maintains data consistency across updates

**Usage**:
```bash
python3 update_addresses.py
```

---

## Workflow

The typical workflow for address collection was:

1. **Initialize**: Run `add_addresses.py` to create the structure
2. **Manual Research**: Find company addresses via web search (Google, company websites)
3. **Update**: Use `company_addresses.py` or `update_addresses.py` to add found addresses
4. **Verify**: Check output CSV for completeness

## Dependencies

All scripts require:
- Python 3.6+
- pandas library (`pip install pandas`)
- csv module (built-in)

## Data Files Used

**Input files** (in `/data/archive/`):
- `east_bay_biotech_combined_notes.csv` - Original company list without addresses

**Output files**:
- `east_bay_biotech_with_addresses.csv` - Company list with addresses added

---

### 6. `analyze_csv_differences.py`
**Purpose**: Analyze differences between multiple CSV versions

**What it does**:
- Compares v2.csv, with_addresses.csv, and pseudofinal.csv
- Reports on file sizes, column differences, geographic coverage
- Identifies company overlap and unique entries
- Provides merge recommendations

**Usage**:
```bash
python3 analyze_csv_differences.py
```

**Output**: Console analysis report with merge strategy recommendations

---

### 7. `merge_csv_files.py`
**Purpose**: Merge multiple CSV files into single dataset

**What it does**:
- Uses east_bay_biotech_v2.csv as base (171 companies)
- Merges better address data from with_addresses.csv
- Removes personal "Relevance to Profile" column
- Creates clean, consolidated dataset

**Usage**:
```bash
python3 merge_csv_files.py
```

**Output**: `data/working/companies_merged.csv` (171 companies, all Bay Area)

---

### 8. `fetch_careers_urls.py` ⭐ **PHASE 2 SCRIPT**
**Purpose**: Find careers page URLs for all companies

**What it does**:
- Searches Applicant Tracking Systems (Greenhouse, Lever, Workday, SmartRecruiters)
- Searches company career pages
- Updates "Hiring" column with direct URLs
- Saves progress incrementally (every 25 companies)
- Generates detailed search log

**Usage**:
```bash
python3 fetch_careers_urls.py
```

**Output**:
- `data/working/companies_with_careers.csv` (updated CSV)
- `data/working/careers_search_log.txt` (progress log)

**Note**: This is a TEMPLATE script. You'll need to implement WebSearch logic or conduct manual research for each company. See `docs/WORKFLOW.md` for detailed procedures.

---

### 9. `validate_urls.py` ⭐ **PHASE 2 SCRIPT**
**Purpose**: Validate all careers URLs are accessible

**What it does**:
- Tests each URL in the "Hiring" column
- Makes HTTP requests to check accessibility
- Reports: Valid (200), Redirects (3xx), Broken (4xx/5xx)
- Generates detailed validation report

**Prerequisites**:
```bash
pip install requests
```

**Usage**:
```bash
python3 validate_urls.py
```

**Output**:
- `data/working/url_validation_report.txt` (detailed report)
- Console summary of broken/working URLs

---

## Current Phase Scripts

**Phase 1 (Data Consolidation)**: ✅ Complete
- `analyze_csv_differences.py`
- `merge_csv_files.py`

**Phase 2 (Careers URL Enhancement)**: 🔄 In Progress
- `fetch_careers_urls.py` - Template created, needs implementation
- `validate_urls.py` - Template created, needs implementation

---

## Workflow

For the complete workflow and step-by-step procedures, see:
- **`docs/WORKFLOW.md`** - Detailed data collection procedures
- **`PROJECT_PLAN.md`** - Overall project roadmap
- **`docs/DATA_DICTIONARY.md`** - Data structure and column definitions

---

**Last Updated**: January 2025
**Maintainer**: Jaden Shirkey
