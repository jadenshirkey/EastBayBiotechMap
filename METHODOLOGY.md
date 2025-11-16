# East Bay Biotech Map - Methodology

**Version:** 4.3
**Last Updated:** 2025-11-16
**Philosophy:** Systematic validation with automated QC gates - prioritizing data quality and reproducibility

---

## Overview

This document describes the reproducible process for discovering, validating, and cataloging biotechnology companies in the San Francisco Bay Area using the V4.3 framework.

The V4.3 framework introduces:
- **BPG-first extraction** with CA-wide coverage
- **Two-path enrichment** (Path A for companies with websites, Path B for those without)
- **Deterministic validation** with confidence scoring
- **Automated QC gates** with manual review for edge cases
- **Staging → Promotion flow** ensuring only validated data reaches production

---

## Geographic Scope

### Included Counties (9-County Bay Area)
- **Core:** Alameda, Contra Costa, Marin, San Francisco, San Mateo, Santa Clara
- **Extended:** Napa, Solano, Sonoma

All 9 counties are treated equally in the V4.3 geofence.

### Excluded Areas
- **Davis, CA** (Yolo County - outside Bay Area)
- **Sacramento metro** (Sacramento County)
- **Central Valley** cities
- Any location >60 miles from San Francisco (backstop radius check)

### City Whitelist
Companies must be located in recognized Bay Area cities (~60 cities across 9 counties). See `config/geography.py` for the canonical whitelist.

**Geofence Logic:** Accept if **City in whitelist** OR **Coordinates within 60-mile radius of SF**.

---

## Validation Strategy (V4.3)

### Path A: Deterministic Validation (Companies with BPG Website)

**Input:** Companies with Website field from BioPharmGuy

**Process:**
1. Extract brand token from eTLD+1 domain (e.g., gene.com → "gene")
2. Build biasable query: "{brand_token} {City} CA biotech"
3. Call Google Maps Text Search → get top 3-5 candidates
4. For each candidate, call Place Details
5. Apply hard gates:
   - **Geofence**: Address must be in Bay Area (9-county + city whitelist)
   - **Business type**: Exclude real_estate_agency, lodging, premise-only
   - **Multi-tenant**: If incubator address, require strong brand match (name similarity ≥0.85 OR website eTLD+1 match)
6. **Website cross-check**: Score += 0.3 if Google website eTLD+1 == BPG eTLD+1
7. **Accept if confidence ≥ 0.75**

**Output:** Address, Place_ID, Confidence_Det, Validation_Reason

### Path B: AI Validation (Companies without BPG Website)

**Input:** Companies without Website field (routed to Path B queue)

**Process:**
1. Use Anthropic Claude Sonnet 4.5 with structured outputs
2. Provide tools: `search_places`, `get_place_details` (Google Maps API wrappers)
3. Prompt includes:
   - Geographic hard gate (9-county Bay Area only)
   - Brand-domain validation (reject aggregators)
   - Business-type validation (exclude lodging, real estate, premise)
   - Multi-tenant handling (incubator addresses need strong brand evidence)
   - Acceptance threshold ≥0.75
   - **Prefer nulls over wrong data**
4. Temperature = 0 (deterministic)
5. JSON schema enforced for output

**Output:** Address, Website (if found), Confidence, Validation JSON

### Confidence Tiers

Companies are categorized into 4 tiers based on confidence scores:

| Tier | Confidence Range | Description | QC Process |
|------|-----------------|-------------|------------|
| **Tier 1** | ≥ 0.95 | BPG + Google confirm same eTLD+1 | 10 random spot-checks |
| **Tier 2** | 0.90-0.95 | BPG ground truth, Google mismatch/missing | 10 random spot-checks |
| **Tier 3** | 0.75-0.90 | AI validated (Path B) | Automated validators only |
| **Tier 4** | < 0.75 | Flagged for manual review | **All companies reviewed** |

**Target Distribution:**
- Tier 1: ≥70%
- Tier 2: ≥10%
- Tier 3: ≤10%
- Tier 4: 0% (all resolved before promotion)

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

**Definition:** Major pharmaceutical corporations with global operations and either annual revenue >$5B OR public market cap >$50B.

**Quantified Thresholds:**
- Annual revenue: **>$5 billion**
- OR Public market cap: **>$50 billion**
- AND Global operations (presence on multiple continents)

**How to verify (step-by-step):**

1. **Check if publicly traded:**
   - Search: `[Company name] stock` or `[Company name] ticker symbol`
   - If traded on NYSE/NASDAQ → Get market cap from [Google Finance](https://www.google.com/finance) or [Yahoo Finance](https://finance.yahoo.com)
   - If market cap >$50B → **Large Pharma**

2. **If not public or market cap <$50B, check revenue:**
   - Search: `[Company name] revenue` or `[Company name] annual report`
   - Sources (in priority order):
     a. Wikipedia infobox (look for "Revenue" field)
     b. Company's "Investors" or "About" page
     c. Latest financial report (10-K for US public companies)
   - If revenue >$5B → Check global presence (step 3)
   - If revenue <$5B → **Not Large Pharma** (likely Commercial Biotech)

3. **Check global presence:**
   - Visit company website → "Locations" or "Global Operations" page
   - Must have operations in ≥2 continents (not just sales offices)
   - If global AND (market cap >$50B OR revenue >$5B) → **Large Pharma**

**Data not available?**
- If revenue/market cap data unavailable after checking all sources → Default to **Commercial Biotech** if they have approved products

**Examples:**
- Genentech (revenue ~$15B, owned by Roche)
- Amgen (market cap ~$150B, revenue ~$28B)
- AbbVie (market cap ~$330B, revenue ~$54B)
- Novartis (market cap ~$200B, revenue ~$50B)

---

#### 2. Commercial Biotech

**Definition:** Biotechnology companies with ≥1 FDA-approved product generating revenue, with annual revenue ≤$5B AND market cap ≤$50B.

**Quantified Thresholds:**
- Has ≥1 FDA-approved product (drugs, biologics, devices, diagnostics)
- AND Annual revenue: **≤$5 billion**
- AND Public market cap: **≤$50 billion** (if publicly traded)

**How to verify (step-by-step):**

1. **Check for FDA-approved products:**
   - Visit company website → "Products" or "Pipeline" page
   - Look for terms: "FDA approved," "marketed," "commercial product"
   - **OR** Search [FDA Drugs@FDA database](https://www.accessdata.fda.gov/scripts/cder/daf/)
   - **OR** Search: `[Company name] FDA approval`
   - If NO approved products → Skip to Clinical-Stage or Preclinical

2. **If has approved product(s), verify size:**
   - Search: `[Company name] revenue` or `[Company name] market cap`
   - Sources (in priority order):
     a. Wikipedia infobox (Revenue/Market cap fields)
     b. Google Finance / Yahoo Finance (for market cap)
     c. Company "Investors" or "About" page
     d. Latest 10-K or annual report

3. **Apply thresholds:**
   - If revenue >$5B OR market cap >$50B → **Large Pharma** (not Commercial)
   - If revenue ≤$5B AND market cap ≤$50B → **Commercial Biotech**
   - If financial data unavailable → Default to **Commercial Biotech** (has approved product but clearly not Big Pharma scale)

**Data not available?**
- If revenue/market cap not found after checking sources → Assume **Commercial Biotech** if company has approved product and doesn't appear to be Big Pharma

**Examples:**
- BioMarin (market cap ~$18B, revenue ~$2B)
- Exelixis (market cap ~$8B, revenue ~$1.7B)
- Dynavax (market cap ~$1.5B, revenue ~$300M)
- Codexis (market cap ~$800M, revenue ~$150M)

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

Use this flowchart to classify companies systematically:

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

4. Check if has FDA-approved products:
   - Visit website "Products" page OR search FDA.gov Drugs@FDA
   - If NO approved products → Skip to step 6

5. If has approved product(s), check company size:
   - Get revenue from: Wikipedia OR Google search "[Company] revenue"
   - Get market cap from: Google Finance OR Yahoo Finance

   Decision:
   - If revenue >$5B OR market cap >$50B → Large Pharma
   - If revenue ≤$5B AND market cap ≤$50B → Commercial Biotech
   - If data not available → Commercial Biotech (has product, not Big Pharma)

6. Check clinical trials (for companies without approved products):
   - Search ClinicalTrials.gov for company name
   - If active clinical trials → Clinical-Stage Biotech

7. Check pipeline (for companies with no products or trials):
   - Website mentions therapeutic pipeline/drug discovery → Preclinical Biotech

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

### Format Guidelines (V4.3)
- **Length:** 1-3 sentences (≤200 characters enforced)
- **Content:** Technology platform, therapeutic areas, key innovations
- **Tone:** Factual, not marketing fluff (de-marketed)
- **Keywords:** Platform, technology, therapeutic area, modality
- **Extraction:** Automated from About/Technology pages (see `scripts/extract_focus_areas.py`)

**Note:** V4.3 uses automated extraction with HTML caching and rate limiting. Manual review focuses on accuracy, not extraction.

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

## V4.3 QC Checklist

Before promotion to `data/final/`, all companies must pass:

### Automated Validators (6 Gates)

**All validators must return PASS before promotion proceeds.**

1. **URL Validation**
   - All Website fields are valid HTTPS/HTTP or blank
   - No malformed URLs

2. **Geofence Validation**
   - All City values in city whitelist
   - All Address values within Bay Area (9-county or 60-mile radius)

3. **Duplicate Domain Check**
   - Zero duplicate eTLD+1 domains (except allowlist: gene.com for multi-brand)
   - Each domain maps to exactly one company

4. **Aggregator Check**
   - Zero aggregator domains (LinkedIn, Crunchbase, Facebook, Yelp, etc.)
   - Aggregators reset to blank during merge

5. **Place ID Requirement**
   - If Address present, Place_ID must be present
   - Ensures Google Maps validated all addresses

6. **Out-of-Scope Check**
   - Zero Davis/Sacramento/Central Valley companies
   - No locations outside 9-county Bay Area

### Manual Review

**Tier 1/2 Spot-Checks (10 random samples)**
- Verify address matches company's actual location (check website)
- Confirm company is legitimate biotech/life sciences
- Validate city and focus areas accuracy

**Tier 4 Full Review (ALL flagged companies)**
- Investigate why confidence is low
- Options:
  - Fix data issues (incorrect website, address)
  - Remove from dataset if out of scope
  - Accept if data correct despite low confidence
- Document review in `data/working/reviewed_flags.csv`

**Blocking:** Promotion blocked if Tier 4 companies unreviewed.

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

## V3 Workflow: Batch Discovery & Enrichment

### Workflow Overview

This workflow is optimized for efficiency by **deduplicating early** to avoid wasting resources on companies already in the master list.

```
STAGE 1: Discovery (30 min)
┌─────────────────┐
│ Wikipedia Agent │──┐
└─────────────────┘  │
┌─────────────────┐  │
│BioPharmGuy Agent│──┤──→ [Merge & Dedupe] ──→ raw.csv
└─────────────────┘  │       (by name)
┌─────────────────┐  │
│ LinkedIn Agent  │──┘
└─────────────────┘

STAGE 1.5: Early Deduplication (10 min) ⚡ CRITICAL OPTIMIZATION
┌──────────────┐   ┌───────────────────────┐
│   raw.csv    │ + │ master companies.csv  │
└──────────────┘   └───────────────────────┘
         │                    │
         └────────┬───────────┘
                  ↓
      [Dedupe by website domain + company name]
                  ↓
         new_companies.csv
      (ONLY companies not in master)

STAGE 2: Address Acquisition (1-2 hr)
Process ONLY new_companies.csv
┌──────────────────────┐
│ Batch 1: Cos 1-50    │──┐
└──────────────────────┘  │
┌──────────────────────┐  │
│ Batch 2: Cos 51-100  │──┤──→ addresses_added.csv
└──────────────────────┘  │
┌──────────────────────┐  │
│ Batch 3: Cos 101-150 │──┘
└──────────────────────┘

STAGE 3: Classification (1-2 hr)
Each batch visits website once to determine stage
┌──────────────────────┐
│ Classifier Batch 1   │──┐
└──────────────────────┘  │
┌──────────────────────┐  │
│ Classifier Batch 2   │──┤──→ classified.csv
└──────────────────────┘  │
┌──────────────────────┐  │
│ Classifier Batch 3   │──┘
└──────────────────────┘

STAGE 4: Focus Areas Extraction (1-2 hr)
Each batch extracts focus areas from same website
┌──────────────────────┐
│ Extractor Batch 1    │──┐
└──────────────────────┘  │
┌──────────────────────┐  │
│ Extractor Batch 2    │──┤──→ enriched.csv
└──────────────────────┘  │
┌──────────────────────┐  │
│ Extractor Batch 3    │──┘
└──────────────────────┘

STAGE 5: Merge to Master (5 min)
┌──────────────────┐
│  enriched.csv    │──┐
└──────────────────┘  │
┌──────────────────┐  │──→ [Append] ──→ master companies.csv (UPDATED)
│ master companies │──┘
│      .csv        │
└──────────────────┘
```

### Why Early Deduplication Matters

**Without early deduplication:**
- 500 companies discovered in Stage 1
- 300 already in master list
- **Waste:** 300 × 3 stages = 900 redundant operations

**With early deduplication (Stage 1.5):**
- 500 companies discovered in Stage 1
- **Immediately filter to 200 new companies**
- Only process 200 × 3 stages = 600 operations
- **Savings:** 300 operations avoided + faster execution

### Stage Details

#### Stage 1: Discovery (Parallel)
- **Input:** None
- **Output:** `raw.csv` (columns: Company Name, Website)
- **Parallelization:** 3 agents run simultaneously
- **Agent 1:** Scrape Wikipedia lists
- **Agent 2:** Extract BioPharmGuy directory
- **Agent 3:** LinkedIn company search
- **Merge:** Combine all sources, dedupe by name/website

#### Stage 1.5: Early Deduplication
- **Input:** `raw.csv` + `master companies.csv`
- **Output:** `new_companies.csv`
- **Process:**
  1. Extract domains from raw.csv websites
  2. Extract domains from master companies.csv websites
  3. Remove any raw.csv companies where domain matches master
  4. Remove any raw.csv companies where name matches master (fuzzy match)
  5. Result = ONLY truly new companies

#### Stage 2: Address Acquisition (Batched)
- **Input:** `new_companies.csv`
- **Output:** `addresses_added.csv`
- **Batch size:** 50-100 companies per agent
- **Process:** Each agent visits company websites, extracts addresses, validates with Google Maps

#### Stage 3: Classification (Batched by Column)
- **Input:** `addresses_added.csv`
- **Output:** `classified.csv`
- **Batch size:** 50-100 companies per agent
- **Process:** Each agent determines Company Stage using decision tree from Phase 3

#### Stage 4: Focus Areas (Batched by Column)
- **Input:** `classified.csv`
- **Output:** `enriched.csv`
- **Batch size:** 50-100 companies per agent
- **Process:** Each agent extracts 1-3 sentence descriptions from websites

#### Stage 5: Merge to Master
- **Input:** `enriched.csv` + `master companies.csv`
- **Output:** Updated `master companies.csv`
- **Process:** Append new companies to master, sort by city/name

### Estimated Timeline

| Stage | Duration | Parallelization | Total Time |
|-------|----------|-----------------|------------|
| Stage 1: Discovery | 30 min | 3 agents | 30 min |
| Stage 1.5: Deduplication | 10 min | 1 process | 10 min |
| Stage 2: Addresses | 2 hr | 3 agents | 40 min |
| Stage 3: Classification | 2 hr | 3 agents | 40 min |
| Stage 4: Focus Areas | 2 hr | 3 agents | 40 min |
| Stage 5: Merge | 5 min | 1 process | 5 min |
| **TOTAL** | | | **~3 hours** |

### Success Metrics

After workflow completion:
- [ ] `raw.csv` has 200-500 companies
- [ ] `new_companies.csv` has <50% of raw.csv (good deduplication)
- [ ] `enriched.csv` has 100% complete data (all columns filled)
- [ ] `master companies.csv` increased by size of `new_companies.csv`
- [ ] All new companies pass QC checklist (Phase 6)

---

## Automated Pipeline Architecture

### Overview

The East Bay Biotech Map uses a five-stage automated Python pipeline that transforms web data into a validated, enriched database. This pipeline implements the 70/10 principle: achieving 70% data completeness with 10% of the effort through smart automation.

**Pipeline Philosophy:**
- **Multi-source discovery**: Cast a wide net, then filter intelligently
- **Progressive refinement**: Each stage improves data quality
- **Safety first**: Backups, progressive saving, non-destructive updates
- **Transparency**: Extensive logging at every stage

### Stage 1: Discovery - Web Scraping

The pipeline begins with two parallel extraction scripts that discover companies from complementary sources:

#### Wikipedia Extraction (`extract_wikipedia_companies.py`)
**Sources:**
- List of biotechnology companies (structured table)
- US pharmaceutical companies category page
- San Francisco Bay Area companies category page

**Algorithm:**
1. Fetches pages using requests library with polite User-Agent header
2. Parses HTML using BeautifulSoup with two strategies:
   - **Tables**: Extracts company names from wikitable links, scans for Bay Area cities
   - **Categories**: Filters out meta-pages, extracts company links from mw-category divs
3. Applies permissive Bay Area filtering (defaults to inclusion for manual review)
4. Outputs to `data/working/wikipedia_companies.csv`

**Yield**: ~200 companies requiring manual validation

#### BioPharmGuy Extraction (`extract_biopharmguy_companies.py`)
**Source:** BioPharmGuy Northern California directory (pre-filtered to region)

**Algorithm:**
1. Parses HTML table with company/location/description columns
2. Extracts company name from website link (second link in cell)
3. Parses location format "CA - City Name" with abbreviation mapping:
   - "South SF" → "South San Francisco"
   - "SF" → "San Francisco"
4. Applies strict Bay Area city validation (rejects non-Bay Area immediately)
5. Captures "Focus Area" descriptions for classification
6. Outputs to `data/working/biopharmguy_companies.csv`

**Yield**: ~1,117 high-quality companies with cities and focus areas

### Stage 2: Merge & Deduplication (`merge_company_sources.py`)

This critical stage intelligently combines data from multiple sources while eliminating duplicates.

**Input Priority Hierarchy:**
1. **Existing database** (highest - manually validated)
2. **BioPharmGuy** (medium - industry curated)
3. **Wikipedia** (lowest - general encyclopedia)

**Company Name Normalization:**
The key to deduplication is aggressive normalization that catches variations:
```
"BioMarin Pharmaceutical Inc." → "biomarin pharmaceutical"
"ATUM (DNA 2.0)" → "atum"
"Genentech, LLC" → "genentech"
```

**Process:**
1. Convert to lowercase
2. Remove legal suffixes (Inc., LLC, Corp., Ltd., etc.) via regex
3. Strip parenthetical notes
4. Remove special characters
5. Normalize whitespace

**Three-Phase Merge:**
1. **Preserve existing**: All existing companies added unconditionally
2. **Add BioPharmGuy**: New companies not matching existing normalized names
3. **Add Wikipedia**: Only if new AND has verified Bay Area city

**Safety**: Creates timestamped backup before overwriting

**Output**: Unified `data/final/companies.csv` (~1,130 deduplicated companies)

### Stage 3: Google Maps Enrichment (`enrich_with_google_maps.py`)

Fills missing addresses and websites using Google's authoritative Places API.

**Two-Tier Search Strategy:**
1. **Primary**: `"[Company] [City] CA biotech"` - qualifier helps disambiguate
2. **Fallback**: `"[Company] [City] CA"` - broader search if first fails

**API Usage:**
- Places Search API → Place Details API (two-step process)
- Fields retrieved: address, website, coordinates, phone
- Cost: ~$0.049 per company ($24.50 per 500 companies)

**Company Stage Classification:**
Keyword-based heuristic classifier with 8 categories (checked in priority order):
1. Acquired (keywords: "acquired by", "acquisition")
2. Academic/Gov't ("university", "institute", ".edu", ".gov")
3. Large Pharma ("fortune 500", "global pharmaceutical")
4. Commercial-Stage ("FDA approved", "marketed product")
5. Clinical-Stage ("phase 1/2/3", "clinical trial")
6. Tools/Services/CDMO ("CDMO", "CRO", "reagents", "kits")
7. Pre-clinical/Startup ("therapeutic", "drug", "therapy")
8. Unknown (no matching keywords)

**Safety Features:**
- **Progressive saving**: Every 50 companies (protects expensive API calls)
- **Rate limiting**: 0.1s delay between calls (10 req/sec max)
- **Non-destructive**: Only fills empty fields, preserves manual entries
- **Error resilience**: Individual failures don't crash entire run

**Output**: Updated `data/final/companies.csv` + enrichment report

### Stage 4: Data Quality Analysis (`data_quality_analysis.py`)

Comprehensive audit identifying issues before publication.

**Seven-Part Analysis:**

1. **Schema Validation**: Verifies correct columns and order
2. **Completeness Check**: Measures % filled per column (✅ >90%, ⚠️ 80-90%, ❌ <80%)
3. **Geographic Validation**: Identifies companies outside 80+ Bay Area cities
4. **URL Validation**: Checks proper URL format (scheme + netloc)
5. **Company Stage Distribution**: Shows breakdown by development stage
6. **Duplicate Detection**:
   - By normalized name (case-insensitive)
   - By domain (catches shared websites from acquisitions)
7. **Address Quality**:
   - Full street addresses (contains comma + digits)
   - City-only addresses (missing street)
   - Missing addresses (empty field)

**Output**: Console report with categorized issues and actionable recommendations

### Stage 5: Manual Review & Correction

While automated, the pipeline identifies items requiring human judgment:
- Companies outside Bay Area boundaries
- Invalid or missing URLs
- Duplicate entries requiring consolidation
- Companies not found in Google Maps

### Pipeline Performance

**Execution Times:**
- Wikipedia extraction: 10-30 seconds
- BioPharmGuy extraction: 5-15 seconds
- Merge & deduplication: <1 second
- Google Maps enrichment: 50-500 seconds (rate limited)
- Quality analysis: 1-2 seconds
- **Total**: 1-10 minutes depending on enrichment scope

**Data Volumes:**
- Raw discovery: ~1,300 companies
- After deduplication: ~1,130 companies
- Enrichment success rate: 85-95%
- Final completeness: >95% for all critical fields

### Running the Pipeline

**Prerequisites:**
```bash
# Install Python dependencies
pip install -r scripts/requirements.txt

# Set Google Maps API key (for enrichment)
export GOOGLE_MAPS_API_KEY="your-key-here"
```

**Execution:**
```bash
# Stage 1: Extract (run in parallel)
python3 scripts/extract_wikipedia_companies.py &
python3 scripts/extract_biopharmguy_companies.py &
wait

# Stage 2: Merge
python3 scripts/merge_company_sources.py

# Stage 3: Enrich (optional, requires API key)
python3 scripts/enrich_with_google_maps.py

# Stage 4: Analyze
python3 scripts/data_quality_analysis.py
```

For detailed script usage, see [scripts/README.md](scripts/README.md).

### Key Design Patterns

1. **Path Independence**: Scripts use `Path(__file__).parent` for reliability
2. **Normalization Intelligence**: Aggressive name matching catches subtle duplicates
3. **Source Prioritization**: Clear data quality hierarchy
4. **Progressive Refinement**: Each stage adds value
5. **API Respect**: Rate limiting, polite headers, timeout handling
6. **Safety Mechanisms**: Backups, checkpoints, non-destructive updates

The pipeline embodies the 70/10 principle: automate the tedious parts while preserving room for human expertise where it matters most.

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

## V4.3 Pipeline Stages

The V4.3 framework implements a complete A→F staged pipeline:

**Stage A: Extraction**
- BioPharmGuy CA-wide extraction (state-ca-all-geo.php)
- Website field capture (external link preservation)
- HTML caching with 7-day expiration
- Output: `data/working/bpg_ca_raw.csv`

**Stage B: Merge & Geofence**
- eTLD+1 deduplication with domain-reuse detection
- Late geofencing (after deduplication)
- Aggregator denylist filtering
- Output: `data/working/companies_merged.csv`

**Stage C: Enrichment**
- **Path A**: Companies with Website → Google Maps validation
- **Path B**: Companies without Website → Anthropic structured outputs
- Merge Path A + Path B outputs
- Output: `data/working/companies_enriched.csv`

**Stage D: Classification**
- Apply methodology decision tree (8 categories)
- Default to "Unknown" if ambiguous
- Output: `data/working/companies_classified.csv`

**Stage E: Focus Extraction**
- Fetch company websites (About/Technology pages)
- Extract 1-3 factual sentences (≤200 chars)
- HTML caching, rate limiting (1 req/sec)
- Output: `data/working/companies_focused.csv`

**Stage F: QC & Promotion**
- Run 6 automated validators
- Generate review queues (spot-checks + Tier 4)
- Manual review process
- Promotion to `data/final/companies.csv` (ONLY after QC passes)

**Key Scripts:**
- `scripts/classify_company_stage.py` - Stage D
- `scripts/extract_focus_areas.py` - Stage E
- `scripts/validate_for_promotion.py` - Stage F validators
- `scripts/generate_review_queues.py` - Stage F review queues
- `scripts/promote_to_final.py` - Stage F promotion

---

## Version History

**V4.3 (2025-11-16)**
- Complete A→F staged pipeline implementation
- Two-path enrichment (Path A deterministic, Path B AI)
- 6 automated validators with hard gates
- Confidence tiering system (Tier 1-4)
- Manual review process for QC
- Staging → Promotion flow (no direct writes to final/)
- BPG-first with CA-wide extraction
- eTLD+1 deduplication with domain-reuse detection

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
