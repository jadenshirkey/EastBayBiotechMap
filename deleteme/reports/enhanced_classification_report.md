# Enhanced Classification Report v2

Generated: 2025-11-16 02:04:08

## Summary

- Total Companies: 1002
- Successfully Classified: 825 (82.3%)
- Unknown: 177 (17.7%)

## Stage Distribution

- Acquired: 2 (0.2%)
- COMMERCIAL: 3 (0.3%)
- Commercial: 3 (0.3%)
- PLATFORM: 3 (0.3%)
- PUBLIC: 2 (0.2%)
- Phase I: 1 (0.1%)
- Platform: 383 (38.2%)
- Preclinical: 428 (42.7%)
- Unknown: 177 (17.7%)

## Classification Methods Used

- default_therapeutic: 15 (1.5%)
- description_acquired: 2 (0.2%)
- description_clinical: 8 (0.8%)
- description_platform: 6 (0.6%)
- description_therapeutic: 13 (1.3%)
- focus_areas_clinical: 79 (7.9%)
- focus_areas_mixed: 49 (4.9%)
- focus_areas_platform: 330 (32.9%)
- focus_areas_therapeutic: 251 (25.0%)
- known_company: 8 (0.8%)
- name_pattern: 64 (6.4%)

## Key Improvements from v1

- Now uses Focus Areas as primary classification signal
- Implements waterfall logic for multiple data sources
- Better platform vs therapeutic discrimination
- Improved confidence scoring
