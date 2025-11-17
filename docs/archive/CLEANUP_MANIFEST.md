# Cleanup Manifest - V5 Branch

## Files Removed During Cleanup

### Test Data Files
- `data/test_biotech.db` - 50-company test subset database
- `data/test_export.csv` - Test export with 10 companies

### Helper/Debug Scripts (One-time use)
- `check_misclassified.py` - Used to investigate misclassified companies
- `check_private_with_sec.py` - Used to verify Private with SEC Filings
- `check_schema.py` - Used to inspect database schema
- `check_test_db.py` - Used to verify test database contents
- `create_test_subset.py` - Script to create test subset (functionality incorporated into main workflow)
- `test_fixes.py` - Initial testing of security fixes
- `test_sample_output.py` - Sample output testing

## Files Kept

### Core Scripts
- All scripts in `scripts/` directory
- `query_db.py` - Database query utility
- `visualize_db.py` - Database visualization utility
- `setup.py` - Package setup

### Documentation
- All `.md` files documenting methodology and improvements
- Configuration templates (.env.template)

### Data
- `data/bayarea_biotech_sources.db` - Main production database
- `data/final/companies.csv` - Final California-only export for Google My Maps
- All backup files in `data/backups/`

## Cleanup Date
November 16, 2025