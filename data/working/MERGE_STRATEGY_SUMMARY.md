# Biotech Companies Dataset Merge Strategy

## Overview
This document summarizes the comparison between the current final dataset (`companies.csv`) and the V2 dataset (`biotech_companies_A.txt`).

## Key Metrics

| Metric | Value |
|--------|-------|
| Companies in CSV (Final) | 124 |
| Companies in TXT (V2) | 181 |
| Companies in Both | 25 |
| **Net-New Companies** | **156** |
| Overlapping with Conflicts | 24 |

## Analysis Summary

### 1. Data Quality Assessment

#### CSV Dataset
- **Strengths:**
  - Complete street addresses for all 124 companies (100%)
  - Proper website URLs with `https://` prefix
  - Detailed "Notes" field with company description
  - Company stage classification (Commercial, Clinical, Pre-clinical, etc.)
  
- **Weaknesses:**
  - Less comprehensive (only 124 companies)
  - Some outdated information on acquired/closed companies

#### TXT Dataset (V2)
- **Strengths:**
  - Much more comprehensive (181 companies)
  - Includes many newer startups and emerging companies
  - Recent data (companies like Altos Labs, various AI-driven companies)
  - Geographic expansion to less-known biotech areas
  
- **Weaknesses:**
  - Missing all street addresses
  - Plain domain names without `https://` prefix
  - Less detailed descriptions (only "Focus Area" field)
  - No company stage classification

### 2. Conflict Analysis

**Types of Conflicts Found:**

| Conflict Type | Count | Notes |
|--------------|-------|-------|
| Website Format | 25 | CSV: `https://domain.com` vs TXT: `domain.com` |
| Missing Address (TXT) | 156 | All new companies have empty address field |
| City Mismatch | 3 | Accelero Biostructures, Addition Therapeutics, Actym Therapeutics |
| Name Variation | 1 | AcureX Biosciences vs AcureX Therapeutics |

### 3. Problematic Overlaps Requiring Manual Review

These companies have city/location discrepancies:

1. **Accelero Biostructures**
   - CSV: San Francisco
   - TXT: San Carlos
   - CSV Address: 156 2ND ST, San Francisco, CA 94105
   - **Action:** Keep CSV data (has San Francisco zip code)

2. **Addition Therapeutics**
   - CSV: Berkeley
   - TXT: South San Francisco
   - CSV Address: 2630 Bancroft Way, Berkeley, CA 94704
   - **Action:** Verify actual headquarters location

3. **Actym Therapeutics**
   - CSV: Listed as Berkeley
   - CSV Address: 717 Market St, San Francisco, CA 94103 (conflicting!)
   - TXT: Berkeley
   - **Action:** Address is in SF, not Berkeley - update city to match address

## Recommended Merge Strategy

### Phase 1: Add All New Companies
- Add 156 companies from TXT file to CSV
- Use CSV schema: Company Name, Address, City, Website, Company Stage, Notes
- For new companies:
  - Fill Company Name, City, Website from TXT
  - Leave Address field empty (can be researched later)
  - Set Company Stage to "Unknown" (can be classified later)
  - Use Focus Area as Notes

### Phase 2: Validate Overlapping Companies
- Verify the 3 companies with city conflicts
- Keep CSV address data (more complete and reliable)
- Update website URLs to include `https://` prefix for consistency

### Phase 3: Data Enrichment (Post-Merge)
- Research and fill in missing addresses for new companies
- Standardize website URLs
- Classify company stages for the 156 new companies
- Expand/improve descriptions where needed

### Phase 4: Final Dataset
- **Total Companies:** 280 (124 original + 156 new)
- **Data Completeness Goals:**
  - Address: 100%
  - Website: 100%
  - City: 100%
  - Company Stage: 100%
  - Notes/Focus Area: 100%

## Files Generated

1. **COMPARISON_REPORT.txt** - Detailed analysis with all company listings
2. **NEW_COMPANIES_TO_ADD.csv** - Ready-to-import CSV with 156 new companies
3. **MERGE_STRATEGY_SUMMARY.md** - This file

## Implementation Steps

```
1. Backup current companies.csv
2. Add 156 new companies from NEW_COMPANIES_TO_ADD.csv
3. Manually verify 3 companies with location conflicts
4. Update website URLs to standardized format
5. Classify company stages for new entries
6. Research and fill in missing addresses
7. Validate and test final merged dataset
```

## Geographic Distribution

### Original 124 Companies - Key Cities
- South San Francisco: 28
- Emeryville: 16
- Berkeley: 12
- San Francisco: 10
- Redwood City: 9

### 156 New Companies - Geographic Expansion
- **Additional Cities:** Livermore, Orinda, Danville, Larkspur, Campbell
- **Improved Coverage:** Santa Clara, San Jose, Palo Alto, Mountain View regions
- **Remote/Outlier Locations:** Half Moon Bay, Morgan Hill, San Ramon

## Notes

- Website format differences are cosmetic and can be easily standardized
- Address field is critical - TXT dataset should be enhanced with this data
- Company stage classification needed for new companies (based on focus area descriptions)
- Consider maintaining separate "Source" field to track which dataset each company came from

---

Generated: 2025-11-08
