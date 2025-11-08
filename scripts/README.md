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

## Future Scripts (Planned)

See `PROJECT_PLAN.md` for upcoming scripts:
- `geocode_addresses.py` - Add latitude/longitude coordinates
- `fetch_descriptions.py` - Scrape company descriptions from websites
- `fetch_company_size.py` - Gather employee count data
- `find_careers_pages.py` - Locate careers/jobs page URLs
- `merge_csv_files.py` - Consolidate multiple CSV versions

---

**Last Updated**: January 2025
**Maintainer**: Jaden Shirkey
