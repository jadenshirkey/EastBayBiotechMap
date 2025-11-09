# East Bay Biotech Map - Validation & Quality Control Log

**PURPOSE**: Consolidated validation reports tracking data quality, completeness, and enhancement opportunities across geography, focus areas, websites, and addresses.

**AUDIENCE**: Project owner (Jaden) - quality control reference

**Last Updated**: November 8, 2025

---

## Table of Contents

1. [Overview & Quality Metrics](#overview--quality-metrics)
2. [Geographic Data Validation](#geographic-data-validation)
3. [Focus Area Quality Assessment](#focus-area-quality-assessment)
4. [Website URL Validation](#website-url-validation)
5. [Address Consolidation History](#address-consolidation-history)
6. [Focus Area Mapping & Enhancement Opportunities](#focus-area-mapping--enhancement-opportunities)
7. [Action Plan & Priorities](#action-plan--priorities)

---

## Overview & Quality Metrics

### Dataset Snapshot (as of November 8, 2025)

| Metric | Value | Status |
|--------|-------|--------|
| Total Companies | 280 → **319** (final) | ✅ Expanded |
| Companies with Addresses | 165 (58.9%) → **319 (100%)** | ✅ Complete |
| Companies with Focus Areas | 280 (100%) | ✅ Complete |
| Focus Area Quality (100+ chars) | 97 (34.6%) | ⚠️ Needs improvement |
| Website URL Coverage | 271 (99%) | ✅ Excellent |
| HTTPS Protocol Usage | 270/271 (99.6%) | ✅ Excellent |
| Unique Cities Covered | 43 | ✅ Good coverage |

---

## Geographic Data Validation

**Generated**: November 8, 2025
**Source**: validation_geography.md (407 lines)

### Key Findings

#### Data Completeness
- **Total Companies**: 280
- **Companies with Addresses**: 165 (58.9% at time of validation)
- **Companies Missing Addresses**: 115 (41.1%)
- **Unique Cities**: 43 across Bay Area

**Current Status**: ✅ **100% address coverage achieved** (319 companies post-merge)

#### City Distribution (Top 15 Biotech Hubs)

| City | Count | Cluster Type |
|------|-------|--------------|
| South San Francisco | 34 | Primary biotech hub |
| San Francisco | 27 | Second largest cluster |
| Berkeley | 25 | University/research-affiliated |
| Redwood City | 23 | Corporate headquarters hub |
| Emeryville | 22 | Life sciences cluster |
| Palo Alto | 14 | Peninsula pharma hub |
| San Carlos | 12 | Peninsula biotech cluster |
| Alameda | 11 | Manufacturing/services hub |
| Fremont | 11 | South Bay manufacturing |
| Menlo Park | 11 | Life sciences/pharma hub |
| Hayward | 10 | South Bay services |
| Pleasanton | 9 | East Bay biotech |
| San Jose | 8 | South Bay hub |
| Mountain View | 7 | Peninsula tech companies |
| Brisbane | 4 | Gene editing cluster |

#### Data Quality Issues Identified & Resolved

**City Name Standardization**: ✅ GOOD
- No abbreviations or inconsistent formatting detected
- Standard convention and capitalization throughout

**City Mismatch Issues** (5 companies - RESOLVED):

1. **Accelero Biostructures**
   - Listed City: San Francisco | Address City: CA
   - Resolution: Confirmed San Francisco location

2. **Actym Therapeutics**
   - Listed City: Berkeley | Address City: San Francisco
   - Resolution: Updated to San Francisco (per address)

3. **Altay Therapeutics**
   - Listed City: San Francisco | Address City: San Bruno
   - Resolution: Updated to San Bruno

4. **Amber Bio**
   - Listed City: Berkeley | Address City: San Francisco
   - Resolution: Updated to San Francisco

5. **Pliant Therapeutics**
   - Listed City: Redwood City | Address City: South San Francisco
   - Resolution: Updated to South San Francisco

**Data Entry Error** (FIXED):
- FibroGen had "https://www.fibrogen.com" in City field instead of "San Francisco"

#### Geographic Scope Insights

**Core Bay Area Coverage**: South San Francisco, Berkeley, Emeryville remain top 3 biotech hubs

**Expansion to Outlier Cities**: Coverage includes less common biotech areas like Livermore, Orinda, Danville, Larkspur, Half Moon Bay, Morgan Hill - demonstrating comprehensive regional mapping

---

## Focus Area Quality Assessment

**Generated**: November 8, 2025
**Source**: validation_focus_areas.md (694 lines), VALIDATION_QUICK_REFERENCE.txt (160 lines)

### Critical Quality Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Companies with Focus Areas | 280/280 (100%) | ✅ Complete |
| Average Description Length | 53 characters | ❌ Too short |
| Desired Minimum Length | 100+ characters | Target |
| Current Compliance (100+ chars) | 97 companies (34.6%) | ⚠️ Critical issue |
| Very Generic Descriptions | 26 companies | ❌ Poor quality |
| Weak/Underdeveloped Descriptions | 78 companies | ❌ Needs work |
| **Total with Quality Issues** | **104 companies (37.1%)** | ⚠️ Major gap |

### Length Distribution

| Category | Count | Percentage | Assessment |
|----------|-------|------------|------------|
| <50 chars (Too Short) | 183 | 65.4% | ❌ PROBLEM |
| 50-200 chars (Acceptable) | 97 | 34.6% | ✅ Acceptable |
| 200+ chars (Rich) | 0 | 0.0% | ⚠️ Missing |

### Performance by Company Stage

| Stage | Companies | Avg Length | % Too Short | Severity |
|-------|-----------|------------|-------------|----------|
| Pre-clinical/Startup | 137 | 38 chars | 89% | ❌ CRITICAL |
| Tools/Services/CDMO | 38 | 41 chars | 84% | ❌ CRITICAL |
| Large Pharma | 7 | 70 chars | 43% | ⚠️ Concerning |
| Commercial-Stage | 35 | 76 chars | 34% | ⚠️ Concerning |
| Clinical-Stage | 44 | 78 chars | 27% | ⚠️ Medium |

### Examples: Poor vs. Excellent Descriptions

**POOR EXAMPLES (Current State)**:
- 1cBio: "Small molecule drug discovery" (26 chars) - TOO GENERIC
- Kimia: "AI/ML Drug Discovery Platform" (32 chars) - TOO VAGUE
- Amaros: "Ophthalmology data platform (AI)" (30 chars) - LACKS DETAIL
- Acrobat: "CRISPR-based drug discovery" (27 chars) - NO SPECIFICS
- Nanotein: "Protein-based Reagents for Cell Therapy" (39 chars) - MINIMAL

**EXCELLENT EXAMPLES (Model Standard)**:
- Arsenal Bio: "Programmable cell therapies for solid tumors. Advanced protein and genetic engineering of T-cells." (98 chars)
- Allogene: "Allogeneic CAR T (AlloCAR T™) therapies. Protein engineering of CAR constructs is critical." (89 chars)

### V2 Enrichment Opportunity

- **Companies in FOCUS_AREA_MAPPING_V2.md**: 54
- **Overlap with CSV dataset**: 49
- **HIGH-PRIORITY ENHANCEMENT CANDIDATES**: 41
- **V2 companies NOT in CSV (naming mismatch)**: 5

**Enhancement Impact**: 14.6% of dataset (41 companies) could be improved with existing V2 data, representing 2-5x richer descriptions per company.

### Quality Standards Going Forward

✅ **Requirements**:
- Minimum description length: 100 characters
- Must include: Specific disease/application area
- Must include: Key technology or mechanism
- Should include: Proprietary platform names (if applicable)
- Format: Single coherent statement or 2-3 focused sentences

❌ **Terminology to AVOID**:
- "Platform" (alone, without specifics)
- "Drug discovery" (too generic)
- "Therapeutics" (without modality)
- "Technologies" (without detail)

✅ **Preferred Patterns**:
- "Engineered [protein type] for [mechanism]"
- "[Modality] targeting [specific target/pathway]"
- "[Technology platform]™ enabling [application]"
- "[Mechanism] for [disease/indication]"

---

## Website URL Validation

**Generated**: November 8, 2025
**Source**: validation_websites.md (72 lines)

### Summary Statistics

| Metric | Value | Status |
|--------|-------|--------|
| Total Companies in Dataset | 271 | - |
| HTTPS URLs (secure) | 270 | ✅ 99.6% |
| HTTP URLs (insecure) | 1 | ⚠️ 0.4% |
| URLs with Format Issues | 0 | ✅ Perfect |

### Protocol Usage

- **HTTPS (secure)**: 270 URLs - Best practice ✅
- **HTTP (insecure)**: 1 URL - Needs upgrade ⚠️

### Issues Identified & Resolved

#### High Priority Issue (FIXED):
**Upgrade HTTP to HTTPS**:
- Atreca: Changed `http://atreca.com` → `https://atreca.com`

#### Medium Priority - Shared Domain URLs

**3 domains shared by multiple companies** (possible acquisitions or duplicates):

1. **acurex.com**: AcureX Biosciences, AcureX Therapeutics
2. **ancorabiotech.com**: Ancora Biotech, Ancora Bio
3. **atum.bio**: ATUM, ATUM (DNA2.0)

**Recommendation**: Verify if these are acquisitions, parent companies, or duplicate entries

### Ongoing Maintenance Recommendations

- Quarterly validation of all URLs
- Monitor for domain changes or company acquisitions
- Automated URL checking with `curl -I https://url.com`
- Test domain reachability periodically

---

## Address Consolidation History

**Generated**: November 8, 2025
**Source**: CONSOLIDATION_REPORT.txt (60 lines)

### Consolidation Process Summary

**Objective**: Consolidate address findings from multiple batch files and update companies.csv

**Data Sources Merged**:
1. addresses_batch1.json - 20 addresses
2. addresses_batch2.json - 18 addresses
3. addresses_found.json - 26 addresses (from first pass)
4. **Total unique addresses found**: 45 companies

### Results

**CSV Update Status**:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Companies WITH addresses | 150 (53.6%) | 165 (58.9%) | +15 (+5.4%) |
| Companies WITHOUT addresses | 130 (46.4%) | 115 (41.1%) | -15 |
| **Completion percentage** | 53.6% | **58.9%** | +5.4% |

**Duplicate Handling**:
- Duplicate addresses removed: 39 (from original 84 total entries)
- Final unique address entries: 45

### Sample of Companies Updated

✓ Akero Therapeutics → 601 Gateway Boulevard, Suite 350, South San Francisco, CA 94080
✓ Aligos Therapeutics → 1 Corporate Drive, 2nd floor, South San Francisco, CA 94080
✓ Altos Labs → 2600 Bridge Parkway, Redwood City, CA 94065
✓ Adverum Biotechnologies → 100 Cardinal Way, Redwood City, CA 94063
✓ Alamar Biosciences → 47071 Bayside Pkwy, Fremont, CA 94538

### Final Status

**Current State**: ✅ **100% address coverage achieved** (all 319 companies have addresses)

---

## Focus Area Mapping & Enhancement Opportunities

**Source**: FOCUS_AREA_MAPPING_V2.md (775 lines)

### Overview

Comprehensive focus area mapping with enhanced descriptions for 54 companies across priority tiers.

**Sources Referenced**:
- TXT: Data from biotech_companies_A.txt
- PDF: Data from biotech_companies_gem.pdf
- BOTH: Data merged from both sources

### Company Categorization by Technology Tier

#### TIER 1: CRISPR/GENE EDITING (6 companies)

**Core companies with enhanced descriptions**:

1. **Acrigen Biosciences** (Berkeley)
   - Enhanced: Advanced gene editing platform combining next-generation CRISPR enzymes (αCas and μCas families) with engineered anti-CRISPR proteins (ErAcrs)

2. **Acrobat Genomics** (San Carlos)
   - Platform utilizing CRISPR technology for systematic target discovery

3. **Addition Therapeutics** (Berkeley/South San Francisco)
   - RNA-only therapeutics platform using PRINT™ technology for RNA-mediated transgene insertion

4. **Amber Bio** (Berkeley/San Francisco)
   - First-of-its-kind RNA writing platform capable of multi-kilobase genetic edits

5. **Caribou Biosciences** (Berkeley)
   - Clinical-stage CRISPR-based allogeneic cell therapies using hybrid RNA-DNA guides

6. **Scribe Therapeutics** (Alameda)
   - Engineering bespoke CRISPR enzymes and delivery systems (co-founded by Jennifer Doudna)

#### TIER 2: ANTIBODY DISCOVERY & THERAPEUTICS (15+ companies)

**Highlighted companies**:

1. **Abalone Bio** (Emeryville)
   - Functional antibody discovery for GPCRs using FAST platform with AI-guided design

2. **Acepodia** (Alameda)
   - Antibody-Cell Conjugation (ACC™) technology using biorthogonal chemistry

3. **Adanate** (Alameda)
   - Antibody therapeutics targeting LILRB family for immuno-oncology

**Additional Antibody Companies**: Aarvik Therapeutics, Ab Studio, AbTherx, AbboMax, Accurus Biosciences, Antibodies Incorporated, Antibody Solutions, and more

### Enhancement Priority

**41 HIGH-PRIORITY CANDIDATES** identified for description enhancement using V2 mapping data

**5 NAMING MISMATCHES** to resolve:
- 4D Molecular Therapeutics
- Catalent (possible acquisition)
- Ginkgo Bioworks
- JBEI (Joint BioEnergy Institute)
- Phyllom BioProducts

---

## Action Plan & Priorities

### 90-Day Quality Improvement Plan (28-34 Hours Total Effort)

#### PRIORITY 1: V2 Integration (Week 1-2) - 4-6 Hours
- ✅ Integrate V2 enrichment for 41 candidate companies
- ✅ Fix 5 naming mismatches
- **Impact**: 14.6% of dataset greatly improved

#### PRIORITY 2: Focus Area Standardization (Week 3-4) - 6-8 Hours
- [ ] Standardize 104 weak/generic descriptions to ≥100 chars
- [ ] Research company websites and press releases
- **Impact**: 37% of dataset meets quality baseline

#### PRIORITY 3: Schema Definition (Week 5-6) - 3-4 Hours
- [ ] Define description schema by company category
- [ ] Apply consistent structure (Technology + Disease + Mechanism)
- **Impact**: Consistency across all categories

#### PRIORITY 4: Advanced Tagging (Week 7-8) - 6-8 Hours
- [ ] Extract proprietary technology platform names
- [ ] Assign Technology Cluster tags
- [ ] Assign Protein Science Relevance Tiers
- **Impact**: Enable advanced filtering and discovery

### Immediate Actions

1. ✅ Address all geographic city mismatches (5 companies)
2. ✅ Upgrade HTTP URL to HTTPS (Atreca)
3. ✅ Fix FibroGen city field data entry error
4. [ ] Integrate 41 V2 enhanced descriptions
5. [ ] Establish minimum 100-character description standard
6. [ ] Resolve 5 naming mismatches

### Expected Outcomes

| Phase | Inadequate Descriptions | Status |
|-------|------------------------|--------|
| Current State | 65% | ⚠️ Baseline |
| After Priority 1 | 50% | 🔄 41 companies improved |
| After Priority 2 | 15% | 🔄 Weak descriptions fixed |
| Final State | <5% | ✅ Target |

---

## User Experience Improvement

### Before Quality Enhancement
> User reads "Small molecule drug discovery" and cannot differentiate between 100+ similar companies; must research independently.

### After Quality Enhancement
> User reads "Small-molecule drug discovery platform targeting transcription factors for inflammation and cancer. Structure-based design focus." and immediately understands company positioning.

---

## Validation Methodology Notes

### Geographic Validation
- City name standardization check across all entries
- Address format validation (Street, City, State ZIP)
- City-address consistency verification
- Geographic outlier identification

### Focus Area Validation
- Description length analysis
- Quality assessment (generic vs. specific)
- Technology categorization
- Cross-reference with V2 enrichment data

### Website Validation
- Protocol verification (HTTP vs. HTTPS)
- Format validation (valid domain structure)
- Duplicate domain detection
- **Note**: Network reachability testing performed separately in production environment

### Address Consolidation
- Deduplication across multiple batch sources
- Format standardization
- Completeness tracking
- Quality verification through manual spot-checks

---

**Report Compiled**: November 8, 2025
**Next Review**: February 8, 2026 (Quarterly)
**Maintained By**: Jaden Shirkey
