# Google My Maps Import Notes

## Export Verification Results

### File Information
- **File**: `data/final/companies.csv`
- **Total Companies**: 978
- **File Size**: 173.6 KB (CSV format)

### Data Quality
- ✅ All 978 companies have complete addresses
- ✅ All 978 companies have valid latitude/longitude coordinates
- ✅ All required Google My Maps columns present

### Company Stage Distribution
- Private with SEC Filings: 313 (32.0%)
- Private: 241 (24.6%)
- Defunct: 176 (18.0%)
- Clinical Stage: 134 (13.7%)
- Public: 114 (11.7%)

### Important Notes

1. **Multi-location Companies**: 10 companies have California cities but non-California addresses. These are companies with California presence but headquarters elsewhere:
   - Alimentiv (San Diego city, Canada address)
   - Allucent (San Diego city, North Carolina address)
   - Apellis Pharmaceuticals (San Francisco city, Massachusetts address)
   - Eicos Sciences (San Mateo city, Maryland address)
   - Eliquent Life Sciences (San Francisco city, DC address)
   - And 5 others

   These should be manually reviewed after import to ensure proper California office locations.

2. **Google My Maps Import Steps**:
   1. Go to [Google My Maps](https://www.google.com/maps/d/)
   2. Click "Create a New Map"
   3. Click "Import"
   4. Upload `data/final/companies.csv`
   5. Select "Company Name" as the title column
   6. Select "Address" OR use Latitude/Longitude for positioning
   7. Style markers by "Company Stage" for visual differentiation

3. **Column Mapping**:
   - Title: Company Name
   - Location: Address (or use Latitude/Longitude)
   - Categories: Company Stage
   - Additional info: Website, Focus Areas, Clinical Trials, SEC Filings

4. **Layer Suggestions**:
   - Consider creating separate layers for each Company Stage
   - Or create layers by geographic region (SF Bay Area, San Diego, LA, etc.)

## Data Currency
- Database last updated: November 16, 2025
- Clinical trials data: Current as of enrichment run
- SEC filings data: Current as of enrichment run

## Export Command
To regenerate the export:
```bash
venv/bin/python3 scripts/export_california_companies.py
```

To export with different filters or limits:
```bash
venv/bin/python3 scripts/export_california_companies.py --limit 100  # For testing
```