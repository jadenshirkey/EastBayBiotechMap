# East Bay Biotech Map - Methodology

**Version:** 3.0
**Last Updated:** 2025-11-08
**Philosophy:** 70% coverage with 10% effort - prioritizing practical execution over exhaustive completeness

---

## Overview

This document describes the reproducible process for discovering, validating, and cataloging biotechnology companies in the San Francisco Bay Area.

---

## Geographic Scope

### Included Counties
- **Core:** San Francisco, San Mateo, Alameda, Contra Costa, Santa Clara
- **Extended:** Marin, Napa, Sonoma (on case-by-case basis)

### Excluded Areas
- **Davis, CA** (Yolo County - outside Bay Area)
- **Sacramento metro**
- Any location >60 miles from San Francisco

### City Whitelist
Companies must be located in recognized Bay Area cities. [See full list in appendix]

---

## Phase 1: Company Discovery

### Primary Sources (Simple & Fast)

#### 1. Wikipedia Lists (~30 min)
- [List of biotechnology companies](https://en.wikipedia.org/wiki/List_of_biotechnology_companies)
- [Pharmaceutical companies of the United States](https://en.wikipedia.org/wiki/Category:Pharmaceutical_companies_of_the_United_States)
- [Companies based in the San Francisco Bay Area](https://en.wikipedia.org/wiki/Category:Companies_based_in_the_San_Francisco_Bay_Area)
- **Action:** Extract company names → validate location → add to staging list

#### 2. BioPharmGuy Directory (~30 min)
- Visit [BioPharmGuy California listings](http://www.biopharmguy.com)
- Filter by Bay Area counties
- **Action:** Copy table → filter by city → deduplicate

#### 3. LinkedIn Company Search (~30 min)
- **Search:** Industry filter = "Biotechnology" OR "Pharmaceuticals" + Location filters (San Francisco Bay Area)
- **Action:** Extract company names → verify website via Google → add if valid Bay Area location

### Secondary Sources (Lower Priority)
- Industry conference attendee lists
- Bay Area biotech incubator portfolios (QB3, JLABS, etc.)
- Crunchbase (if accessible)
- Scientific publication author affiliations

---

## Phase 2: Data Standardization

### CSV Schema

Required fields:
```csv
Company Name, Website, City, Address, Company Stage, Focus Areas
```

### Field Validation Rules

| Field | Rule | Example |
|-------|------|---------|
| **Company Name** | Official legal or DBA name | `Genentech` |
| **Website** | Valid HTTPS URL | `https://www.gene.com` |
| **City** | Must be in Bay Area whitelist | `South San Francisco` |
| **Address** | Full street address with ZIP | `1 DNA Way, South San Francisco, CA 94080` |
| **Company Stage** | One of 8 defined categories | `Large Pharma` |
| **Focus Areas** | 1-3 sentences from company website | See examples below |

### Address Validation Process
1. Copy address from source
2. Paste into Google Maps
3. Verify it resolves to a Bay Area location
4. Use Google's standardized address format
5. Confirm city matches our whitelist

---

## Phase 3: Company Classification

### Company Stage Categories

The following 8 categories are mutually exclusive and easily verifiable using the criteria below.

---

#### 1. Large Pharma

**Definition:** Major pharmaceutical corporations with global operations and multi-billion dollar revenue.

**Verification Criteria (check in order):**
1. **Public market cap** >$50B (check Google Finance, Yahoo Finance)
2. **OR** Annual revenue >$5B (check latest 10-K, annual report, or Wikipedia)
3. **AND** Global presence (operations in multiple continents)

**How to verify:**
- Search: `[Company name] revenue` → Check financial reports
- Check Wikipedia infobox for revenue/market cap
- Look for "Locations" or "Global" page on website

**Examples:** Genentech, Amgen, AbbVie, Novartis, Bayer

---

#### 2. Commercial Biotech

**Definition:** Biotechnology companies with ≥1 FDA-approved product generating revenue, but smaller than Large Pharma.

**Verification Criteria:**
1. Website mentions "FDA approved" product OR "commercial" product
2. **OR** Check FDA.gov Drugs@FDA database for approved products
3. **AND** Revenue <$5B (not Large Pharma threshold)

**How to verify:**
- Visit company website → Look for "Products" or "Pipeline" page
- Search: `[Company name] FDA approval`
- Check [FDA Drugs@FDA](https://www.accessdata.fda.gov/scripts/cder/daf/)

**Examples:** BioMarin, Exelixis, Dynavax, Codexis

---

#### 3. Clinical-Stage Biotech

**Definition:** Companies with ≥1 therapeutic asset in Phase I, II, or III clinical trials, but no approved products yet.

**Verification Criteria:**
1. Website mentions "clinical trial" or "Phase I/II/III"
2. **OR** Check [ClinicalTrials.gov](https://clinicaltrials.gov/) for active/recruiting trials
3. **AND** No FDA-approved products

**How to verify:**
- Visit company website → Check "Pipeline" or "Programs" page
- Search ClinicalTrials.gov for company name
- Look for press releases about trial initiation/results

**Examples:** Alector, Arsenal Biosciences, Caribou Biosciences

---

#### 4. Preclinical Biotech

**Definition:** Companies developing therapeutics in discovery or preclinical stage, with no active clinical trials.

**Verification Criteria:**
1. Website describes therapeutic pipeline OR drug discovery platform
2. **AND** No mention of clinical trials or FDA approvals
3. **AND** Not primarily a tools/services provider

**How to verify:**
- Check website "Technology" or "Pipeline" page
- Look for terms: "preclinical," "discovery," "research stage," "platform"
- Verify NO clinical trials on ClinicalTrials.gov

**Examples:** Profluent, Scribe Therapeutics, Metagenomi

---

#### 5. Platform/Tools

**Definition:** Companies whose primary business is providing tools, services, instruments, or contract services (CDMO/CRO), not developing their own therapeutics.

**Verification Criteria:**
1. Website emphasizes "services," "tools," "platform," "CDMO," or "CRO"
2. Business model is B2B (selling to other biotech/pharma companies)
3. May have technology but not developing own drugs

**How to verify:**
- Check website → Look for "Services," "Products," or "Solutions"
- Look for customer testimonials or case studies
- Check if they offer contract services, instruments, or reagents

**Examples:** ATUM, Catalent, Unchained Labs, Bio-Rad

---

#### 6. Academic

**Definition:** University-affiliated research organizations or academic institutes.

**Verification Criteria:**
1. Website domain is `.edu`
2. **OR** Explicitly states university affiliation (e.g., "UC Berkeley," "Stanford")
3. Primary mission is research and education

**How to verify:**
- Check website domain
- Look for "About" page mentioning university affiliation
- Check for academic publications, faculty listings

**Examples:** Innovative Genomics Institute (IGI), QB3 institutes

---

#### 7. Government

**Definition:** Federal, state, or local government research labs and facilities.

**Verification Criteria:**
1. Website domain is `.gov`
2. **OR** Explicitly run by government agency (DOE, NIH, USDA, etc.)
3. Funded by government appropriations

**How to verify:**
- Check website domain
- Look for "About" page mentioning DOE, NIH, USDA, etc.
- Check for government logos/seals

**Examples:** Joint BioEnergy Institute (DOE), USDA Western Regional Research Center, Lawrence Berkeley National Lab facilities

---

#### 8. Nonprofit

**Definition:** Non-profit research organizations that are neither academic nor government.

**Verification Criteria:**
1. Website states "non-profit," "501(c)(3)," or "foundation"
2. **OR** Domain is `.org` AND explicitly non-commercial mission
3. Not affiliated with university or government

**How to verify:**
- Check website "About" page for nonprofit status
- Look for 501(c)(3) designation or "non-profit" statement
- Check funding sources (grants, donations vs. commercial revenue)

**Examples:** Gladstone Institutes, Arcadia Science

---

### Classification Decision Tree

Use this flowchart to classify companies:

```
1. Check domain:
   - .edu → Academic
   - .gov → Government

2. Check website "About" page:
   - States "non-profit" or "501(c)(3)" → Nonprofit
   - University affiliation → Academic
   - Government agency → Government

3. Check business model:
   - Primary business is services/tools/CDMO → Platform/Tools

4. Check revenue/market cap:
   - Revenue >$5B OR market cap >$50B → Large Pharma

5. Check products:
   - Has FDA-approved product → Commercial Biotech

6. Check clinical trials:
   - Active clinical trials (ClinicalTrials.gov) → Clinical-Stage Biotech

7. Check pipeline:
   - Therapeutic pipeline but no trials → Preclinical Biotech

8. If still unclear → Default to Preclinical Biotech or Platform/Tools
```

### Special Cases

**Acquired Companies:**
- Classify by original business category
- Add "(Acquired by [Parent Company])" to Focus Areas
- If operations ceased entirely, consider excluding from list

**Pivoted Companies:**
- Use current business model for classification
- Note pivot in Focus Areas if significant

**Multi-Business Companies:**
- Classify by primary/majority business
- If 50/50 split, use higher stage (e.g., Clinical over Preclinical)

**Uncertain Cases:**
- Default to most conservative category
- Platform/Tools if business model unclear
- Preclinical if development stage unclear

---

## Phase 4: Focus Areas Capture

### Information Sources (in priority order)
1. Company website homepage hero text
2. "About" page first 2 paragraphs
3. "Technology" or "Platform" page summary
4. LinkedIn company description

### Format Guidelines
- **Length:** 1-3 sentences (max 200 characters preferred)
- **Content:** Technology platform, therapeutic areas, key innovations
- **Tone:** Factual, not marketing fluff
- **Keywords:** Include relevant terms (antibody, CRISPR, AAV, etc.)

### Good Examples
```
"CRISPR-based diagnostics and in vivo gene editing"

"Engineered IgM antibodies. Novel antibody engineering platform"

"Cell-free protein synthesis platform (XpressCF™) for ADCs and cytokine-based therapeutics."
```

### Poor Examples (avoid)
```
"Leading the future of medicine" (too vague)
"Innovative solutions for patients worldwide" (marketing speak)
"Founded in 2018 by..." (wrong focus)
```

---

## Phase 5: Deduplication

### Simple Deduplication Rules

**Check for duplicates when:**
1. Company names are identical
2. Website domains match (e.g., gene.com = www.gene.com)
3. Addresses are identical

### Merge Priority
When duplicates found, keep entry with:
1. Most complete Focus Areas description
2. Most recent/accurate address
3. Better source attribution

### Tool: Google Sheets
1. Sort by Company Name (A→Z)
2. Use conditional formatting to highlight potential duplicates
3. Manual review and merge

---

## Phase 6: Quality Control Checklist

Before adding company to master CSV, verify:

- [ ] Website is live (loads without errors)
- [ ] Company is still operating (not "ceased operations" or acquired/dissolved)
- [ ] Address is in Bay Area (city in whitelist)
- [ ] Actually biotech-related (not IT services, generic staffing, etc.)
- [ ] Company Stage is appropriate
- [ ] Focus Areas is informative and factual
- [ ] No duplicate entry exists

---

## Incremental Updates

### Adding New Companies
1. Follow discovery process (Phase 1)
2. Validate and standardize data (Phase 2-4)
3. Check for duplicates (Phase 5)
4. Run QC checklist (Phase 6)
5. Add to staging CSV
6. Review staging batch (recommend 10-20 companies at a time)
7. Merge into master companies.csv

### Removing Companies
Remove when:
- Acquired and operations ceased
- Moved outside Bay Area
- Pivoted away from biotech
- Website permanently down / company dissolved

**Process:** Move to `removed_companies.csv` with removal date and reason

---

## Appendix: Bay Area City Whitelist

### San Francisco County
San Francisco

### San Mateo County
South San Francisco, San Mateo, Redwood City, Menlo Park, Brisbane, Burlingame, Foster City, San Carlos, Belmont, Millbrae, Daly City, Half Moon Bay

### Alameda County
Oakland, Berkeley, Emeryville, Alameda, Hayward, Fremont, Newark, Union City, Pleasanton, Dublin, Livermore, Albany, San Leandro

### Santa Clara County
San Jose, Palo Alto, Mountain View, Sunnyvale, Santa Clara, Cupertino, Milpitas, Campbell, Los Gatos, Saratoga, Morgan Hill, Los Altos

### Contra Costa County
Richmond, Concord, Walnut Creek, San Ramon, Danville, Pleasant Hill, Martinez

### Marin County
San Rafael, Novato, Mill Valley, Larkspur, Corte Madera, Tiburon, Sausalito

### Sonoma County
(Case-by-case basis - generally excluded unless major biotech presence)

### Napa County
(Case-by-case basis - generally excluded unless major biotech presence)

---

## Tools & Resources

### Recommended Tools
- **Google Sheets** - CSV management and deduplication
- **Google Maps** - Address validation
- **Bulk URL Checker** - Verify website status
- **OpenRefine** (optional) - Advanced deduplication

### Useful Links
- [BioPharmGuy Directory](http://www.biopharmguy.com)
- [Wikipedia Biotech Lists](https://en.wikipedia.org/wiki/List_of_biotechnology_companies)
- [Bay Area Biotech Incubators](https://qb3.org/)

---

## Version History

**V3.0 (2025-11-08)**
- Initial methodology document
- Ultra-simplified discovery process (70/10 rule)
- Primary sources: Wikipedia (3 lists), BioPharmGuy, LinkedIn only
- Defined 8 company stage categories with verification criteria
- Separated Academic, Government, and Nonprofit categories
- Added step-by-step verification process for each category
- Established QC checklist

**V2.0** - Manual curation, basic CSV
**V1.0** - Initial East Bay focus

---

## Contributing

To propose methodology improvements:
1. Open an issue describing the change
2. Explain how it improves coverage OR reduces effort
3. Maintain the 70/10 philosophy

---

## License

This methodology is released under CC BY 4.0 - free to use and adapt with attribution.
