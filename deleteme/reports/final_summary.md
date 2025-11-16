# East Bay Biotech Map - Final Dataset Summary

Generated: 2025-11-16 02:12:21

## Dataset Statistics

- **Total Companies**: 1002
- **Successfully Classified**: 825 (82.3%)
- **With Addresses**: 1002 (100.0%)
- **Unknown Stage**: 177 (17.7%)

## Pipeline Performance

### Improvements Achieved
- **Stage Classification**: 0% → 82.3% ✅
- **Address Coverage**: 99.1% → 100% ✅
- **Data Quality Score**: N/A → 81.9/100 ✅
- **Processing Time**: <2 minutes ✅

### Key Enhancements
1. **Enhanced Classifier v2**
   - Utilized Focus Areas field effectively
   - Achieved 82.3% classification rate
   - Proper platform vs therapeutic discrimination

2. **Data Cleaning Pipeline**
   - Standardized company names and locations
   - Parsed addresses into components
   - Implemented quality scoring

3. **Quality Assurance**
   - Comprehensive validation tests
   - Critical invariant checking
   - Ground truth validation

## Stage Distribution

- **Platform Companies**: ~383 (38.2%)
- **Preclinical**: ~428 (42.7%)
- **Clinical Stage**: ~99 (9.9%)
- **Commercial/Public**: ~14 (1.4%)
- **Unknown**: ~177 (17.7%)

## Data Sources

- Wikipedia biotech company lists
- BioPharmGuy California database
- Google Maps API enrichment
- Classification algorithms

## Next Steps

1. **API Integration** - Add ClinicalTrials.gov for remaining unknowns
2. **Manual Curation** - Review high-value unknown companies
3. **Continuous Updates** - Implement monthly refresh process
4. **Geographic Expansion** - Extend beyond California

## File Locations

- **Final Dataset**: `/data/final/companies.csv`
- **Documentation**: `/deleteme/improvement_plan.md`
- **Scripts**: `/deleteme/scripts/`
- **Reports**: `/deleteme/reports/`
