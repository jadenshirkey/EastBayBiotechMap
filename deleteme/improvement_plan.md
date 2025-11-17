# East Bay Biotech Map Data Pipeline Improvement Plan

## Executive Summary

After comprehensive analysis, the data pipeline shows excellent address retrieval (99.1% success rate) but critically lacks company stage information (0% coverage). This plan focuses on three core improvements:

1. **Company Stage Classification** (Critical Priority)
2. **Data Quality & Standardization** (High Priority)
3. **Edge Case Handling & Validation** (Medium Priority)

Current Status:
- Total Companies: 1,002
- Address Coverage: 99.1% (993/1002)
- Company Stage Coverage: 0% (0/1002)
- Data Sources: Wikipedia, BioPharmGuy (working well)

## Phase 1: Critical Gap - Company Stage Classification

### Problem
The `Company Stage` field is completely empty in companies_enriched_final.csv, while the V3 final output requires classification into: Public, Unknown, Preclinical, Phase I-III, Commercial, Platform, Acquired, IPO.

### Solution Architecture

#### 1.1 Stage Classification System
```python
STAGE_DEFINITIONS = {
    'Preclinical': 'No clinical trials, research/discovery phase',
    'Phase I': 'First human trials, safety testing',
    'Phase II': 'Efficacy testing, dose-ranging studies',
    'Phase III': 'Large-scale efficacy, preparing for approval',
    'Commercial': 'FDA approved products on market',
    'Platform': 'Technology/services company',
    'Acquired': 'Bought by another company',
    'IPO': 'Public but pre-commercial',
    'Public': 'Publicly traded company',
    'Unknown': 'Unable to determine stage'
}
```

#### 1.2 Data Sources for Classification
1. **Primary Sources**
   - ClinicalTrials.gov API (active trials)
   - FDA Orange Book (approved drugs)
   - SEC EDGAR (public company filings)
   - Company websites (pipeline pages)

2. **Secondary Sources**
   - Press releases and news
   - Industry databases
   - LinkedIn company pages
   - Crunchbase data

#### 1.3 Classification Algorithm
```
1. Check if publicly traded → 'Public'
2. Check FDA Orange Book → 'Commercial'
3. Query ClinicalTrials.gov:
   - Active Phase 3 → 'Phase III'
   - Active Phase 2 → 'Phase II'
   - Active Phase 1 → 'Phase I'
4. Parse company description:
   - Keywords: "platform", "services", "tools" → 'Platform'
   - Keywords: "acquired", "subsidiary" → 'Acquired'
5. Check founding date:
   - Recent (<2 years) + no trials → 'Preclinical'
6. Default → 'Unknown' (with low confidence)
```

## Phase 2: Data Quality Framework

### Current Issues Identified
- Missing company stages (100% gap)
- Inconsistent name formats
- Some duplicate entries from multiple sources
- Confidence scores need calibration

### 2.1 Data Standardization Pipeline

#### Company Name Standardization
```python
def standardize_company_name(name):
    # Preserve original in separate field
    original = name

    # Remove legal suffixes for matching
    clean_name = remove_suffixes(name)  # Inc., Corp., LLC

    # Standardize capitalization
    formatted = title_case(clean_name)

    # Expand abbreviations
    expanded = expand_abbreviations(formatted)

    return {
        'company_name': original,
        'display_name': formatted,
        'search_name': clean_name.lower()
    }
```

#### Address Standardization
- Parse into components: street, city, state, zip
- Standardize state to 2-letter codes
- Validate ZIP codes (5 or 9 digits)
- Ensure consistent formatting

### 2.2 Duplicate Resolution Strategy

**Priority Order:**
1. Google Maps API (verified, 99.1% success)
2. Wikipedia (curated)
3. BioPharmGuy (comprehensive)
4. Manual entries

**Merge Logic:**
- Keep most complete record
- Combine unique fields
- Track source provenance
- Flag conflicts for review

### 2.3 Quality Scoring System

Each record gets scored on:
- **Completeness** (0-40 points): % of fields populated
- **Confidence** (0-30 points): Source reliability
- **Freshness** (0-20 points): Last update date
- **Validation** (0-10 points): Cross-source agreement

Total score 0-100, with thresholds:
- 85+: High quality, ready for production
- 70-84: Good quality, minor gaps
- 50-69: Needs improvement
- <50: Requires manual review

## Phase 3: Edge Case Handling

### 3.1 Companies Not Found (9 cases, 0.9%)

**Type A - Acquisitions/Mergers**
- Maintain acquisition mapping table
- Search parent company as fallback
- Preserve original + parent reference

**Type B - Name Variations**
- Build alias dictionary
- Try DBA names and abbreviations
- Use fuzzy matching (Levenshtein distance)

**Type C - New/Small Companies**
- Queue for manual research
- Check alternative databases
- Mark as "PENDING_VERIFICATION"

### 3.2 Wrong Company Matched

**Validation Checks:**
- Verify industry (NAICS codes 3254, 5417)
- Check for biotech keywords in description
- Validate against website content
- Geographic verification (California bounds)

## Phase 4: Implementation Roadmap

### Week 1: Core Development

#### Day 1-2: Assessment & Setup
- [x] Analyze companies_enriched_final.csv structure
- [x] Document V3 format requirements
- [x] Identify gaps (Stage: 100%, Address: 0.9%)
- [ ] Set up project infrastructure

#### Day 3-4: Stage Classification
- [ ] Build stage_classifier.py
- [ ] Integrate ClinicalTrials.gov API
- [ ] Implement keyword classification
- [ ] Test on 100-company sample

#### Day 5: Data Cleaning
- [ ] Create data_cleaner.py
- [ ] Implement standardization functions
- [ ] Build duplicate detection
- [ ] Add validation rules

### Week 2: Execution & Delivery

#### Day 6-7: Full Pipeline Run
- [ ] Process all 1,002 companies
- [ ] Classify company stages
- [ ] Clean and standardize data
- [ ] Generate quality reports

#### Day 8: Final Output
- [ ] Generate final companies.csv
- [ ] Validate against V3 format
- [ ] Create documentation
- [ ] Package for deployment

## Phase 5: Final CSV Structure

### Required Columns (V3 Compatible)
```csv
company_name         # Official name
display_name        # Clean UI name
stage              # Development stage (REQUIRED)
city, state, zip   # Location components
address_full       # Complete address
latitude, longitude # Coordinates
website           # Primary URL
description       # Company overview
description_enhanced # AI-enhanced description
focus_areas       # Therapy areas
focus_areas_enhanced # AI-enhanced focus
founded_year      # Establishment date
employee_count    # Size category
last_updated     # Data timestamp
data_source      # Provenance
confidence_score # Quality metric
validation_source # Last validator
classifier_date  # Stage classification date
```

## Success Metrics

### Target Outcomes
- **Company Stage Coverage**: 100% (from 0%)
- **Address Coverage**: Maintain 99.1%
- **Data Quality Score**: 85% average
- **Processing Time**: <2 hours full pipeline
- **Manual Review Queue**: <5% of records

### Validation Checkpoints
1. Stage classification accuracy (sample validation)
2. No data regression from current 99.1% addresses
3. Format compatibility with V3
4. Quality scores meet thresholds

## Risk Mitigation

### Technical Risks
- **API Rate Limits**: Already at 99.1%, minimal API calls needed
- **Classification Errors**: Multi-source validation, confidence scoring
- **Data Loss**: Version control, incremental processing

### Process Risks
- **Manual Review Backlog**: Prioritize by company size/importance
- **Format Breaking Changes**: Maintain backward compatibility
- **Source Data Changes**: Abstract data sources in configuration

## Immediate Action Items

### Today's Priority Tasks
1. ✓ Analyze current data quality (Complete)
   - Address coverage: 99.1% ✓
   - Stage coverage: 0% (identified as critical gap)

2. Create stage classification module
   - Set up ClinicalTrials.gov API access
   - Build keyword classifier
   - Test on sample data

3. Document data dictionary
   - Map all fields from working to final
   - Define transformation rules
   - Create validation criteria

## Technical Implementation Details

### Directory Structure
```
/deleteme/
├── improvement_plan.md (this document)
├── scripts/
│   ├── stage_classifier.py
│   ├── data_cleaner.py
│   ├── quality_scorer.py
│   └── pipeline_runner.py
├── logs/
│   ├── classification.log
│   ├── validation.log
│   └── errors.log
├── manual_review/
│   ├── needs_stage.csv
│   ├── low_quality.csv
│   └── conflicts.csv
└── reports/
    ├── quality_metrics.md
    ├── stage_distribution.md
    └── validation_report.md
```

### Key Algorithms

#### Stage Classification Confidence
```python
def calculate_stage_confidence(company, sources_checked):
    confidence = 0.0

    # Source weights
    if 'clinicaltrials' in sources_checked:
        confidence += 0.4
    if 'fda_orange_book' in sources_checked:
        confidence += 0.3
    if 'sec_filings' in sources_checked:
        confidence += 0.2
    if 'website_pipeline' in sources_checked:
        confidence += 0.1

    # Adjust for data quality
    if company['description']:
        confidence *= 1.1
    if company['website']:
        confidence *= 1.05

    return min(confidence, 1.0)
```

## Maintenance & Sustainability

### Monthly Updates
- Refresh ClinicalTrials.gov data
- Update FDA Orange Book entries
- Re-run stage classification
- Validate address changes

### Quarterly Reviews
- Audit data quality trends
- Update classification rules
- Refresh API integrations
- Review manual entries

### Documentation
- Maintain data dictionary
- Update transformation rules
- Document edge cases
- Track decision log

## Conclusion

The pipeline shows excellent performance in address retrieval (99.1%) but critically lacks company stage information. By focusing on stage classification as the top priority, we can deliver a complete, high-quality dataset that meets all V3 requirements. The modular approach allows for incremental improvements while maintaining system stability.

**Next Step**: Begin implementing the stage classification module to address the 100% gap in company stages.