# Data Quality Issues in V3: Problems, Causes, and Solutions

**Purpose**: Document fundamental data quality issues identified across multiple investigations of the companies.csv dataset, focusing on qualitative understanding and strategic solutions with concrete technical implementations.

**Investigations Referenced**:
- claude/incomplete-request (geographic quality)
- claude/incomplete-b (deep data quality)
- claude/pull-from-v3 (name/website mismatches)
- claude/review-executive-summary (comprehensive review)
- ChatGPT technical audit (November 2025)

**Date**: November 2025
**Status**: V3 dataset contains systematic data quality issues requiring strategic cleanup with specific technical fixes

---

## Executive Summary

The V3 companies.csv dataset suffers from **systematic data quality issues** stemming primarily from over-reliance on automated Google Places API enrichment without sufficient validation. The core problem is that **automated enrichment introduced plausible-looking but fundamentally wrong data** that is difficult to detect and has propagated to external databases.

**Key Insight**: The dataset exhibits a tension between **completeness** (automated enrichment filled in missing data) and **accuracy** (that filled-in data is often wrong). Better to acknowledge gaps than publish incorrect information.

**Strategic Challenge**: Some errors are obvious (URLs in wrong fields), but many are subtle and plausible (wrong address that exists and looks legitimate). Systematic cleanup requires understanding error patterns, not just fixing individual rows.

**Technical Reality**: The current enrichment script's "first result wins" approach from Google Places Text Search, combined with no validation gates, causes ~20-25% of the dataset to have suspicious data quality issues (based on technical audit showing domain reuse patterns and name/website mismatches).

---

## Issue 1: Google API Contamination

### **Problem Description**

The Google Places API enrichment process introduced **systematic address and website errors** when it couldn't find companies. Instead of returning "not found," it returned the **nearest physical match** - often a completely different company at a nearby address.

**Nature of the problem**:
- Errors look plausible (valid addresses, legitimate companies)
- Wrong data is internally consistent (address + website + phone all match... the wrong company)
- Difficult to detect without manual verification
- Creates "ghost companies" (real address, wrong company name)

### **Root Cause**

**Google Places API "nearest match" behavior + "first result wins" acceptance**:

1. Search query: "BacStitch DNA biotech Burlingame CA"
2. Google doesn't find BacStitch DNA (small/new company, no Google listing)
3. Google returns: "Oh, you probably meant this biotech in Burlingame: Genentech"
4. **Script accepts FIRST result without validation**: BacStitch DNA now has Genentech's address, website, phone
5. No geofence check, no name similarity check, no brand-domain validation

**Specific code issues in `enrich_with_google_maps.py`**:
- Uses basic `gmaps.places(query)` and takes first result
- No location bias toward Bay Area (query is global)
- No candidate ranking or scoring
- No validation that returned name matches searched name
- No check that website domain relates to company name
- No geofence to ensure US/CA/Bay Area
- No handling of multi-tenant addresses (incubators)

**Why this happened**:
- API designed for fuzzy matching (helping users find what they want)
- No confidence score or "not found" option in basic Places API
- Script assumed first result = correct result
- No validation gates at all

### **Effect on Dataset**

**Fundamental data integrity issue**:
- Companies have **wrong addresses** (different company's location)
- Companies have **wrong websites** (different company's domain)
- Companies have **wrong phone numbers** (different company's contact)
- Original company data is **lost** (overwritten with wrong data)

**Cascading problems**:
- Users looking for Company A find address for Company B
- Mapping visualization shows companies in wrong locations
- Contact information leads to wrong companies
- **Circular reference**: Wrong data exported to Crunchbase/LinkedIn, now can't use those for validation

**Trust impact**:
- Dataset appears complete and professional
- But contains systematic, hidden errors
- Once discovered, undermines confidence in entire dataset
- Can't easily determine which companies are affected

### **Concrete Technical Solution (MVP - Ship This First)**

**Philosophy**: Keep scope small, fix top failure modes with deterministic validation gates. Goal is ≥90% confidence retention, set aside rest for later pass. This aligns with the 70/10 methodology rule.

#### **A. Change How You Query Places**

**Current (broken)**:
```python
query = f"{company_name} {city} CA biotech"
results = gmaps.places(query)
# Takes first result, no validation
```

**Fixed (with validation)**:
```python
# Use Text Search (New) with Bay Area location bias
BAY_CENTER = (37.7749, -122.4194)  # SF coordinates
BAY_RADIUS_M = 80000  # ~50 miles

query = f"{company_name} {city} CA biotech"
results = gmaps.places(
    query,
    location=BAY_CENTER,
    radius=BAY_RADIUS_M
)

# Pull top N candidates (e.g., 5), not just first
candidates = results.get('results', [])[:5]

# Fetch Place Details for each to evaluate
for candidate in candidates:
    details = gmaps.place(
        candidate['place_id'],
        fields=['name', 'formatted_address', 'address_components',
                'website', 'types', 'geometry', 'business_status']
    )
    # Score and validate (see below)
```

**Key change**: Request location bias + pull multiple candidates + fetch full details with `address_components` for validation.

#### **B. Hard Validation Gates (No Exceptions)**

**Geofence** (CRITICAL):
```python
def is_bay_area(address_components):
    """
    Validate address is US + CA + Bay Area city.
    Only accept if ALL checks pass.
    """
    country = next((c['short_name'] for c in address_components
                    if 'country' in c['types']), '')
    state = next((c['short_name'] for c in address_components
                  if 'administrative_area_level_1' in c['types']), '')
    city = next((c['long_name'] for c in address_components
                 if 'locality' in c['types']), '')

    # HARD GATE: Reject if not US + CA
    if country != 'US' or state != 'CA':
        return False, city

    # HARD GATE: Reject if city not in Bay Area whitelist
    if city not in BAY_AREA_CITIES:
        return False, city

    return True, city

# BAY_AREA_CITIES from methodology appendix (comprehensive 9-county list)
BAY_AREA_CITIES = {
    # Alameda County
    'Alameda', 'Albany', 'Berkeley', 'Dublin', 'Emeryville', 'Fremont',
    'Hayward', 'Livermore', 'Newark', 'Oakland', 'Pleasanton', 'San Leandro',
    'Union City',
    # ... (full 9-county list from methodology)
}
```

**Type Filter** (avoid building-level listings):
```python
def is_business_type(types):
    """
    Down-rank or reject generic building types.
    Helps avoid landlord/building websites.
    """
    REJECT_TYPES = {'real_estate_agency', 'lodging'}
    GENERIC_TYPES = {'premise', 'point_of_interest'}

    if any(t in types for t in REJECT_TYPES):
        return False  # Reject real estate agencies

    # If ONLY generic types (no business category), down-rank
    if set(types) <= GENERIC_TYPES:
        return False

    return True
```

**Brand-Domain Check** (CRITICAL for preventing wrong URLs):
```python
GENERIC_TOKENS = {'bio','biosciences','biotech','therapeutics','inc',
                  'corp','llc','company','pharma','pharmaceuticals'}

def normalize(s):
    """Remove generic tokens and special chars for comparison."""
    s = re.sub(r'\([^)]*\)', '', s or '')  # Remove parentheticals
    s = re.sub(r'[^a-z0-9 ]', '', s.lower())  # Only alphanumeric
    return ' '.join(w for w in s.split() if w not in GENERIC_TOKENS)

def brand_from_domain(url):
    """Extract brand from domain (leftmost label)."""
    m = re.search(r'^(?:https?://)?(?:www\.)?([^/]+)', url or '', re.I)
    if not m:
        return ''
    left = m.group(1).split('.')[0]
    return re.sub('[^a-z0-9]', '', left)

def brand_matches(company_name, candidate_name, website):
    """
    Check if website domain brand appears in normalized company or candidate name.
    Prevents "Delve Bio" from getting "distributedbio.com".
    """
    if not website:
        return False  # No website = no brand match

    # Blocklist aggregator domains (never valid company websites)
    AGGREGATORS = {'linkedin.com', 'yelp.com', 'facebook.com',
                   'crunchbase.com', 'mbcbiolabs.com'}
    if any(agg in website.lower() for agg in AGGREGATORS):
        return False

    domain_brand = brand_from_domain(website)
    if not domain_brand:
        return False

    # Check if brand appears in normalized company or candidate name
    norm_company = normalize(company_name).replace(' ', '')
    norm_candidate = normalize(candidate_name).replace(' ', '')

    return (domain_brand in norm_company) or (domain_brand in norm_candidate)
```

**Multi-Tenant Address Handling**:
```python
# Known incubator/co-working addresses (keep this list small and precise)
MULTITENANT_ADDRESSES = {
    "201 Gateway Blvd, South San Francisco, CA 94080, USA",
    "544b Bryant St, San Francisco, CA 94107, USA",
    # MBC BioLabs locations
    "Oyster Point Blvd, South San Francisco",  # Can use substring matching
    # QB3 locations
    # JLABS locations
    # Add more as discovered
}

def is_multitenant_address(formatted_address):
    """Check if address is known shared/incubator location."""
    return any(known in formatted_address for known in MULTITENANT_ADDRESSES)
```

#### **C. Scoring & Acceptance Rule (Deterministic)**

```python
def score_candidate(company_name, expected_city, details):
    """
    Score candidate from 0-1. Accept if >= 0.75 and all gates pass.

    Returns: (score, validation_dict, accept_decision)
    """
    address_components = details.get('address_components', [])

    # GATE 1: Geofence
    in_bay, city = is_bay_area(address_components)
    if not in_bay:
        return 0.0, {
            'geofence_ok': False,
            'city_in_whitelist': False,
            'brand_match': False,
            'notes': [f'Out of Bay Area: {city}']
        }, False

    # GATE 2: Business type
    types = set(details.get('types', []))
    if not is_business_type(types):
        return 0.0, {
            'geofence_ok': True,
            'city_in_whitelist': True,
            'brand_match': False,
            'notes': ['Rejected: building/real estate type']
        }, False

    # GATE 3: Brand match
    website = details.get('website', '')
    candidate_name = details.get('name', '')
    brand_ok = brand_matches(company_name, candidate_name, website)

    # GATE 4: Multi-tenant special handling
    formatted_addr = details.get('formatted_address', '')
    is_multitenant = is_multitenant_address(formatted_addr)
    if is_multitenant and not brand_ok:
        return 0.0, {
            'geofence_ok': True,
            'city_in_whitelist': True,
            'brand_match': False,
            'notes': ['Multi-tenant address without brand match - rejected']
        }, False

    # SCORING (if all gates passed)
    # Name similarity (token overlap)
    def name_similarity(a, b):
        A, B = set(normalize(a).split()), set(normalize(b).split())
        if not A or not B:
            return 0.0
        return len(A & B) / len(A | B)

    sim = name_similarity(company_name, candidate_name)
    city_match = 1.0 if city == expected_city else 0.0
    brand_score = 1.0 if brand_ok else 0.0

    # Type penalty for overly generic
    type_penalty = 0.1 if {'real_estate_agency', 'premise'} & types else 0.0

    score = (0.5 * sim) + (0.2 * city_match) + (0.2 * brand_score) - type_penalty

    # Multi-tenant without brand match: reduce score
    if is_multitenant and not brand_ok:
        score -= 0.4

    notes = []
    if is_multitenant and not brand_ok:
        notes.append('Multi-tenant address without brand match')
    if website and not brand_ok:
        notes.append('Website brand mismatch')
    if sim < 0.3:
        notes.append(f'Low name similarity: {sim:.2f}')

    validation = {
        'geofence_ok': True,
        'city_in_whitelist': city in BAY_AREA_CITIES,
        'brand_match': brand_ok,
        'notes': notes
    }

    # ACCEPT if score >= 0.75
    accept = score >= 0.75

    return score, validation, accept
```

#### **D. Prefer Blanks to Bad Data**

```python
def enrich_company(company_name, city):
    """
    Enrich company with validation gates.
    Returns enriched data OR blanks if confidence < threshold.
    """
    candidates = fetch_candidates(company_name, city)

    best_score = 0.0
    best_candidate = None
    best_validation = None

    for candidate in candidates:
        details = fetch_place_details(candidate['place_id'])
        score, validation, accept = score_candidate(company_name, city, details)

        if accept and score > best_score:
            best_score = score
            best_candidate = details
            best_validation = validation

    if best_candidate:
        # Accept high-confidence result
        return {
            'address': best_candidate.get('formatted_address', ''),
            'website': best_candidate.get('website', ''),
            'confidence': best_score,
            'validation': best_validation,
            'status': 'match'
        }
    else:
        # No confident match - return BLANKS (not wrong data!)
        return {
            'address': '',  # Empty, not wrong
            'website': '',  # Empty, not wrong
            'confidence': 0.0,
            'validation': {'notes': ['No confident match found']},
            'status': 'ambiguous'
        }
```

**Key principle**: Your map is more useful with NO website than with WRONG website. If confidence < threshold, leave blank and add `validation_flag` column.

#### **E. Implementation Estimate**

**Time to implement**: 1-2 days
- Update `enrich_with_google_maps.py` with validation gates: 6-8 hours
- Test on sample of 50 companies: 2-3 hours
- Run on full dataset with validation reporting: 2-3 hours

**Impact**: Prevents ~20-25% of dataset from getting contaminated with wrong data

---

## Issue 2: Circular Reference Problem

### **Problem Description**

Wrong data from the V3 dataset has **propagated to external databases** (Crunchbase, PitchBook, LinkedIn, other biotech directories), creating a **circular reference problem** where wrong data validates itself.

**The vicious cycle**:
1. V3 dataset enriched with wrong Google data
2. Other researchers/databases copy data from V3
3. Wrong data now appears in Crunchbase, LinkedIn, etc.
4. Try to validate V3 using Crunchbase → finds same wrong data
5. "Validation" confirms wrong data (circular reference)

### **Root Cause**

**Automated data sharing without provenance tracking**:
- Biotech community shares company lists
- Databases scrape each other for completeness
- No tracking of "original source" vs "copied data"
- Wrong data multiplies across ecosystem

**Why this is insidious**:
- Can't tell which database is "ground truth"
- Multiple sources saying same wrong thing ≠ validation
- Correcting one source doesn't fix others
- Wrong data becomes "accepted fact"

### **Effect on Dataset**

**Loss of external validation capability**:
- Can't use Crunchbase to verify addresses (might be copied from V3)
- Can't use LinkedIn to verify companies (might be copied from V3)
- Can't use other biotech directories (might be copied from V3)
- Only true source: **company's own website** (if it exists)

**Reputational risk**:
- If V3 is "source of wrong data" → damages credibility
- Other databases may blame V3 for their errors
- Correction responsibility falls on V3 maintainer

**Technical debt**:
- Must track data provenance going forward
- Can't rely on "multiple sources agree" heuristic
- Increases verification burden

### **Potential Solutions**

**Short-term (Source Identification)**:
1. **Company website as ground truth**: Only trust data from company's own website
2. **Primary source verification**: For critical companies, go to source (not aggregators)
3. **Contact companies directly**: Email/call to verify address (for high-priority companies)
4. **Flag uncertain data**: Explicitly mark fields with unknown/unverified data

**Medium-term (Provenance Tracking)**:
1. **Add "source" column**: Track where each field's data came from
2. **Confidence scoring**: Rate data quality (verified, likely, uncertain, unknown)
3. **Last verified date**: Track when data was last confirmed from primary source
4. **Version control**: Track data changes over time to identify degradation

**Long-term (Ecosystem Correction)**:
1. **Publish corrections**: If V3 is source of wrong data, publish correction list
2. **Contact downstream databases**: Notify Crunchbase/LinkedIn of errors
3. **Community coordination**: Work with biotech community on data quality standards
4. **Primary source culture**: Advocate for original source verification

**Implementation Complexity**: MEDIUM
- Can start with company website verification (doable)
- Provenance tracking requires schema changes
- Ecosystem correction is long-term cultural work

---

## Issue 3: Shared Address Confusion

### **Problem Description**

Many biotech companies operate from **incubators, co-working spaces, and shared office buildings**, creating confusion when the same physical address hosts multiple companies. This causes **URL/company associations to cross-contaminate** during automated enrichment.

**The problem**:
- 10 companies at "201 Gateway Blvd" (incubator)
- Google search for any of them returns same address
- But which company's website should be associated?
- Script may assign wrong website to right address
- Or multiple companies get same website (distributedbio.com example: assigned to 11 companies at same address!)

### **Root Cause**

**Physical address ≠ company identity**:
- Incubators: QB3, JLABS, SkyDeck, MBC BioLabs, BioCenter, etc.
- Co-working: WeWork, Regus, shared lab spaces
- Office buildings: Multi-tenant commercial buildings

**Why this causes errors**:
1. Google Maps shows building, not specific company
2. Building may have landlord website (not tenant company)
3. First tenant in Google results gets associated with all tenants
4. Website-to-address mapping becomes many-to-one (wrong)

**Compounding factors**:
- Startups move frequently (address changes)
- Acquisitions (company name changes but address stays)
- Incubators rebrand (QB3 → QBI → specific accelerator)
- Virtual offices (company address but no physical presence)

### **Effect on Dataset**

**Identity confusion**:
- Company A at shared address gets Company B's website
- Can't tell which companies are truly at that address
- Duplicate detection fails (legitimate shared address vs error)
- Map visualization shows cluster but wrong company info

**User experience problems**:
- Click company → taken to wrong website
- See 10 companies at same address → think it's error (but might be legitimate)
- Can't distinguish incubator tenants from address errors

**Validation challenges**:
- How to confirm a company is at shared address?
- When is duplicate address legitimate vs error?
- How to handle companies that moved?

### **Concrete Technical Solution**

#### **Multi-Tenant Address Handling (Already Shown in Issue 1)**

**Rule**: At known shared addresses, REQUIRE brand match or leave website blank.

```python
# Maintain small, high-precision list
MULTITENANT_ADDRESSES = {
    "201 Gateway Blvd, South San Francisco, CA 94080, USA",
    "544b Bryant St, San Francisco, CA 94107, USA",
    "149 Commonwealth Dr, Menlo Park, CA 94025, USA",  # MBC BioLabs
    # ... add more as discovered
}

# In scoring function:
if is_multitenant_address(formatted_addr) and not brand_ok:
    # REJECT: Don't assign first tenant's website to all tenants
    return 0.0, validation, False
```

**This prevents**: distributedbio.com being assigned to 11 different companies at 201 Gateway Blvd.

#### **Domain Reuse Detection**

Add to `merge_company_sources.py`:

```python
def detect_domain_reuse(companies):
    """
    Flag domains assigned to multiple companies.
    Helps identify shared address contamination.
    """
    from collections import defaultdict

    domain_to_companies = defaultdict(list)

    for idx, company in enumerate(companies):
        website = company.get('Website', '').strip()
        if website:
            domain = brand_from_domain(website)
            if domain:
                domain_to_companies[domain].append({
                    'index': idx,
                    'name': company.get('Company Name', ''),
                    'address': company.get('Address', '')
                })

    # Flag domains with >1 company (except allowlist)
    ALLOWED_MULTI_BRAND = {'gene.com'}  # Genentech legitimately has sub-brands

    duplicates = {}
    for domain, company_list in domain_to_companies.items():
        if len(company_list) > 1 and domain not in ALLOWED_MULTI_BRAND:
            duplicates[domain] = company_list

    # Report
    if duplicates:
        print(f"\n⚠️  Found {len(duplicates)} domains assigned to multiple companies:")
        for domain, companies in list(duplicates.items())[:10]:
            print(f"\n  {domain}:")
            for c in companies[:5]:
                print(f"    - {c['name']} (row {c['index']})")

    return duplicates
```

**Run this BEFORE enrichment** to catch existing issues, and AFTER enrichment to verify no new contamination.

### **Potential Solutions**

**Short-term (Manual Disambiguation)**:
1. **Website as canonical identifier**: Use domain name as primary key, address as secondary
2. **Incubator mapping**: Create whitelist of known shared addresses (implemented above)
3. **Manual verification of shared addresses**: Visit each company's website to confirm location
4. **Flag incubator addresses**: Add metadata indicating "shared location"

**Medium-term (Improved Data Model)**:
1. **Many-to-many relationship**: Allow multiple companies per address, multiple addresses per company
2. **Building vs suite distinction**: Capture suite number, not just street address
3. **Primary vs secondary addresses**: Company may list headquarters vs actual lab space
4. **Location verification date**: Track when address was last confirmed

**Long-term (Smart Deduplication)**:
1. **Address clustering algorithm**: Group companies at shared addresses, require manual review
2. **Website-based identity**: Treat website domain as ground truth, address as supporting info
3. **Company lifecycle tracking**: Track moves, acquisitions, closures over time
4. **Incubator partnerships**: Work with QB3, JLABS etc. for tenant lists

**Implementation Complexity**: MEDIUM
- Multi-tenant list: 30 minutes (add addresses as discovered)
- Domain reuse detection: 1-2 hours
- Manual verification needed for flagged cases
- Ongoing maintenance as companies move

---

## Issue 4: Company Stage Classification Failure

### **Problem Description**

The automated company stage classification produces **too many "Unknown" classifications**, reducing the dataset's utility for filtering and categorization. The keyword-based algorithm is **too simplistic** to accurately classify diverse company types.

**The problem**:
- Half of companies classified as "Unknown"
- Classification reduces dataset searchability
- Users can't filter by development stage
- Defeats purpose of having "Company Stage" field

### **Root Cause**

**Oversimplified classification algorithm**:
```python
# Current simplistic approach
if "FDA approved" in text → Commercial
elif "Phase 2" in text → Clinical
elif "therapeutic" in text → Pre-clinical
else → Unknown
```

**Why this fails**:
- **Insufficient keywords**: Many companies don't use standard terms
- **Keyword conflicts**: "FDA approved drug in Phase 2 trial" → which stage?
- **No priority ordering**: First match wins (arbitrary)
- **No external validation**: Doesn't check FDA database, ClinicalTrials.gov
- **Binary matching**: Keyword present/absent, no fuzzy matching
- **Static keywords**: Doesn't learn from patterns

**Complexity of reality**:
- Companies have multiple product stages simultaneously
- Acquired companies: classification frozen in time or updated?
- Tools/Services vs Therapeutics: different stage definitions
- Startups pre-funding vs post-Series A: both "pre-clinical"?

### **Effect on Dataset**

**Reduced utility**:
- Can't filter for clinical-stage companies
- Can't analyze stage distribution across region
- "Unknown" stage is uninformative
- Users must manually research stage anyway

**Missed opportunity**:
- Company stage is **highly valuable** for users
- Job seekers want clinical-stage (more stable)
- Investors want pre-clinical (higher upside)
- But field is unreliable, so users ignore it

**User trust**:
- Half the data marked "Unknown" signals incompleteness
- Undermines perception of dataset quality
- Better to omit field than have 50% Unknown

### **Potential Solutions**

**Short-term (Improved Keywords)**:
1. **Expand keyword lists**: Add more variations, synonyms
2. **Priority ordering**: Explicit rules for keyword conflicts
3. **Domain-specific keywords**: Different keywords for Tools vs Therapeutics
4. **Fuzzy matching**: "Phase II" vs "Phase 2" vs "phase two"

**Medium-term (External Validation)**:
1. **FDA database lookup**: Check approved drugs
2. **ClinicalTrials.gov API**: Check active trials
3. **Crunchbase funding stage**: Correlate funding with development stage
4. **SEC filings**: Public companies disclose pipeline stages
5. **Acquisition status**: Check if company was acquired (from press releases)

**Long-term (Manual Curation + ML)**:
1. **Manual classification of top N companies**: Build training dataset
2. **Machine learning classifier**: Train on manually curated examples
3. **Confidence scoring**: Return probability distribution over stages
4. **Active learning**: Flag uncertain cases for manual review
5. **Ongoing updates**: Re-classify as companies progress

**Pragmatic approach**:
1. **Accept "Unknown" for ambiguous cases**: Better than wrong classification
2. **Manual curation threshold**: Top 200 companies manually classified, rest accept gaps
3. **User-contributed updates**: Allow community to suggest stage corrections
4. **Staged rollout**: Improve coverage over time, don't try to solve all at once

**Implementation Complexity**: MEDIUM
- Keyword expansion is quick (days)
- External validation requires API integration (weeks)
- Manual curation is time-intensive but high-value (hours per company)
- ML approach requires expertise and training data (months)

**NOTE**: Classification is LOWER priority than fixing Google API contamination. Don't expand scope here until enrichment is validated.

---

## Issue 5: Name/Website/Address Triangulation Failures

### **Problem Description**

The three primary company identifiers—**company name, website domain, and physical address**—often don't align, creating confusion about which company is which. This is the **"identity crisis"** problem where we have partial information that doesn't consistently point to one company.

**Examples of misalignment**:
- Company name: "ATUM" vs "ATUM (DNA 2.0)" → same company, different names
- Website: atum.bio → which name is canonical?
- Address: Same address, but company moved/renamed
- Company name says "X" but website domain is "Y.com"

**The fundamental question**: When these three don't agree, which is the "true" identifier?

### **Root Cause**

**No canonical identifier strategy**:
- Treated all three as equally important
- Didn't establish "ground truth" preference
- Assumed they'd always align (they don't)

**Why they diverge**:
1. **Name changes**: Company rebrand but keeps website/address
2. **Acquisitions**: Acquired company keeps old domain but new name
3. **Doing business as (DBA)**: Legal name ≠ marketing name
4. **Typos/variations**: "BioMarin" vs "BioMarin Pharmaceutical" vs "BioMarin Inc."
5. **Domain availability**: Company wants X.com but settles for X-bio.com
6. **Company moves**: Address changes but name/website stay
7. **Shared addresses**: Right address, wrong company association

**Google API amplified the problem**:
- Searched by name
- Returned address + website
- But returned data might be for different company entirely
- Now have: searched name + wrong address + wrong website

### **Effect on Dataset**

**Identity ambiguity**:
- Is "ATUM" same as "ATUM (DNA 2.0)"? (Yes, but looks like duplicate)
- Is "AbTherx" same company as "Wield Therapeutics"? (They share abtherx.com - one is wrong)
- Multiple entries for same company under different names
- Or single entry with conflicting identifiers

**Deduplication fails**:
- Name-based deduplication misses renamed companies
- Domain-based deduplication catches some, misses others
- Address-based deduplication false positives at shared addresses

**User confusion**:
- Which field should user trust for identity?
- If name says X but website is Y, which is correct?
- How to contact the company?

### **Concrete Technical Solution: Brand-Domain Extraction**

**Already implemented in Issue 1**, but here's the full logic:

```python
def brand_from_domain(url):
    """
    Extract brand from domain (leftmost label minus www).
    Examples:
      - "https://www.distributedbio.com/about" → "distributedbio"
      - "biomarin.com" → "biomarin"
      - "atum.bio" → "atum"
    """
    m = re.search(r'^(?:https?://)?(?:www\.)?([^/]+)', url or '', re.I)
    if not m:
        return ''
    domain = m.group(1)
    left_label = domain.split('.')[0]
    # Normalize: only alphanumeric
    return re.sub('[^a-z0-9]', '', left_label.lower())

# Usage in validation:
domain_brand = brand_from_domain("https://atum.bio")  # "atum"
company_normalized = normalize("ATUM (DNA 2.0)")  # "atum"
# Check if "atum" in "atum" → True, brand matches!
```

**This enables**:
- Catch when "Delve Bio" tries to get "distributedbio.com" (brand mismatch)
- Confirm "ATUM" → "atum.bio" (brand matches)
- Reject aggregator domains (linkedin.com, yelp.com)

### **Potential Solutions**

**Short-term (Establish Canonical ID)**:
1. **Website domain as primary key**: Most stable identifier
   - Companies rarely change domain (high switching cost)
   - Domain is globally unique
   - Easy to verify (visit website)
   - Drawback: Not all companies have websites
2. **Name as secondary**: Use for display, but domain for deduplication
3. **Address as tertiary**: Supporting info, not identifier
4. **Explicit merge rules**: When domain matches, merge names as variations

**Medium-term (Identity Resolution)**:
1. **Create "aliases" table**: Track name variations for same domain
   - ATUM = ATUM (DNA 2.0) = ATUM Bio
   - All point to atum.bio as canonical identifier
2. **Cross-reference table**: Link domain → legal name → DBA names
3. **Verification status per identifier**:
   - Domain: verified by website visit
   - Name: verified by website header/title
   - Address: verified by website "contact" page
4. **Conflict resolution workflow**: Flag when identifiers don't align, require manual review

**Long-term (Identity Graph)**:
1. **Company entity graph**: Track relationships
   - Acquisitions: Company A acquired by Company B
   - Rebrands: Company A renamed to Company B
   - Spinoffs: Company B spun out from Company A
   - Shared resources: Companies A, B, C all at incubator X
2. **Temporal tracking**: Track identifier changes over time
3. **Provenance**: Where did each identifier come from?
4. **Confidence scoring**: How sure are we of each identifier?

**Decision needed**: Which identifier is "ground truth"?
- **Recommendation**: Website domain (when available)
- **Rationale**: Most stable, verifiable, unique
- **Fallback**: For companies without websites, use name + address combo

**Implementation Complexity**: MEDIUM
- Brand-domain extraction: Already implemented (Issue 1 solution)
- Canonical ID strategy: Decision + update merge script (1-2 hours)
- Alias table requires schema design (medium effort)
- Identity graph is long-term infrastructure (high effort)

---

## Issue 6: Documentation Drift

### **Problem Description**

Documentation (README, DATA_DICTIONARY) contains **contradictory company counts** that don't match the actual dataset. This is a **credibility issue** - if we can't get the basic count right, how can users trust the data?

**The contradiction**:
- README line 12: "1,210 companies"
- README line 61: "169 companies"
- DATA_DICTIONARY: "171 companies"
- Actual CSV: 1,172 companies

**None of these match**, and there's no explanation for the discrepancies.

### **Root Cause**

**Documentation not updated as dataset evolved**:
- Dataset started at 169-171 companies
- Grew through multiple enrichment rounds
- README updated in some places (1,210) but not others (169)
- DATA_DICTIONARY never updated
- No single source of truth
- No automated consistency checking

**Why this happened**:
- Documentation is manual (easy to forget)
- Count is hardcoded in multiple places (should be computed)
- No CI/CD to catch inconsistencies
- Dataset changed faster than docs updated

### **Effect on Dataset**

**Credibility damage**:
- Users notice contradictions → question data quality
- Suggests lack of attention to detail
- Undermines trust in everything else
- Professional datasets don't have these errors

**User confusion**:
- Which count is correct?
- Is dataset incomplete (171 vs 1,172)?
- Did I download the wrong file?

**Maintenance burden**:
- Must remember to update docs when data changes
- Multiple places to update (error-prone)
- Version synchronization problem

### **Potential Solutions**

**Short-term (Manual Fix)**:
1. **Update all documentation** to current count (1,172)
2. **Add "last updated" date** to each document
3. **Version tag**: "v3.1" with explicit version in all docs

**Medium-term (Automation)**:
1. **Computed counts**: Don't hardcode numbers, compute from data
   ```markdown
   Companies: {{company_count}} <!-- generated from CSV -->
   ```
2. **Documentation generation**: Script that updates docs from data
3. **Pre-commit hook**: Verify docs match data before commit
4. **CI/CD check**: Fail build if docs out of sync with data

**Long-term (Single Source of Truth)**:
1. **Metadata file**: `metadata.json` with canonical counts, dates
2. **All docs pull from metadata**: Documentation references metadata
3. **Automated updates**: When CSV changes, metadata auto-updates
4. **Version control**: Track metadata changes over time

**Schema naming fix**:
- Documentation says "Notes" column
- Actual CSV has "Focus Areas" column
- Simple rename: pick one and standardize

**Implementation Complexity**: LOW
- Manual update is quick (30 minutes - 1 hour)
- Automation is straightforward (1 day)
- Full infrastructure is medium effort (1 week)

---

## Issue 7: BioPharmGuy Data Loss (Quick Win!)

### **Problem Description**

The BioPharmGuy extraction script **parses company website links from HTML but doesn't write them to the output CSV**. This loses a high-value validation anchor that could be used to verify Google Places results.

**What's happening**:
```python
# In extract_biopharmguy_companies.py
# Second link is the company website (valuable!)
# But only "Source URL" is written to CSV, not the company website
```

**The loss**:
- BioPharmGuy provides company websites directly from directory
- These are "primary source" data (from the company listing)
- Could use to validate Google results: does Google URL match BioPharmGuy URL?
- Currently this data is parsed but discarded

### **Root Cause**

**Script design oversight**:
- Script identifies and extracts the company website link
- But output CSV schema doesn't include Website column
- Data is available during extraction but not persisted

### **Effect on Dataset**

**Missed validation opportunity**:
- Lose ~200+ company websites from BioPharmGuy (already extracted, just not saved!)
- Can't cross-validate Google Places results against BioPharmGuy
- Can't use as "ground truth" seed before Google enrichment
- Forced to rely 100% on Google (which we know is unreliable)

**Compounding error**:
- Without BioPharmGuy website, have no external validation
- Google returns wrong website → accepted without challenge
- If had BioPharmGuy URL, could compare and catch mismatch

### **Potential Solution (ONE-LINE FIX!)**

```python
# In extract_biopharmguy_companies.py

# BEFORE (current):
writer.writerow({
    'Company Name': company_name,
    'City': city,
    'Focus Area': focus_area,
    'Source URL': source_url  # This is BioPharmGuy page, not company website!
})

# AFTER (fixed):
writer.writerow({
    'Company Name': company_name,
    'Website': company_website,  # ADD THIS (you already parse this!)
    'City': city,
    'Focus Area': focus_area,
    'Source URL': source_url
})
```

**Then in merge script**:
- BioPharmGuy Website becomes "ground truth"
- During Google enrichment: if BioPharmGuy has Website, DON'T overwrite
- Or: compare Google URL to BioPharmGuy URL, flag if mismatch

**Implementation Complexity**: TRIVIAL
- **Time**: 30 minutes
- **Impact**: HIGH (adds 200+ validated websites as seeds)
- **Risk**: ZERO (additive change, doesn't break anything)

**Priority**: CRITICAL - do this FIRST before re-running enrichment

---

## Anthropic Structured Outputs Integration (Recommended Approach)

### **What It Is**

Anthropic now supports **structured outputs** (JSON schema-validated) and **strict tool use** (agent can ONLY use your specified tools). This is perfect for enrichment validation because:

1. **No hallucinated URLs**: Agent can't invent websites, must use your Google API wrapper
2. **Schema enforcement**: Output MUST conform to your JSON schema (validation flags, confidence scores)
3. **Auditable decisions**: Every enrichment decision is logged with reasoning
4. **Validation server-side**: Apply all gates BEFORE data reaches the agent

### **Why Use This**

**Current problem**: Your Python script makes all enrichment decisions with hard-coded logic.

**With structured outputs**:
- Agent evaluates candidates using your validation tools
- Must return typed JSON (can't skip confidence or validation fields)
- Can only call `places_text_search` and `place_details` (no other data sources)
- Server enforces all validation gates before returning data to agent

**Benefits**:
- **Flexibility**: Can adjust validation logic without rewriting scoring code
- **Transparency**: Every decision includes reasoning (notes field)
- **Testability**: Mock the tools, test the schema
- **Evolution**: As Google API changes, agent adapts within constraints

### **How It Works**

#### **1. Define Two Tools (Google API Wrappers)**

```python
tools = [
    {
        "name": "places_text_search",
        "description": "Search Google Places for companies in Bay Area",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "location": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 2
                },
                "radius_m": {"type": "integer"},
                "max_results": {"type": "integer"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "place_details",
        "description": "Get detailed info for a place_id",
        "input_schema": {
            "type": "object",
            "properties": {
                "place_id": {"type": "string"}
            },
            "required": ["place_id"]
        }
    }
]
```

**Server-side implementation** (you control this):
```python
def handle_tool_call(tool_name, tool_input):
    if tool_name == "places_text_search":
        # Call Google API
        results = gmaps.places(
            tool_input['query'],
            location=tool_input.get('location', BAY_CENTER),
            radius=tool_input.get('radius_m', BAY_RADIUS_M)
        )
        # Return top N candidates
        return {"candidates": results['results'][:5]}

    elif tool_name == "place_details":
        # Call Google Place Details
        details = gmaps.place(
            tool_input['place_id'],
            fields=['name', 'formatted_address', 'address_components',
                    'website', 'types', 'geometry', 'business_status']
        )

        # ⭐ APPLY VALIDATION GATES HERE (server-side)
        result = details['result']
        score, validation, accept = score_candidate(
            company_name,  # From context
            expected_city,  # From context
            result
        )

        # Enrich with validation metadata
        result['validation'] = validation
        result['confidence'] = score
        result['accept'] = accept

        return result
```

#### **2. Define Strict Output Schema**

```python
output_schema = {
    "type": "object",
    "additionalProperties": False,  # No extra fields allowed
    "required": ["company_name", "status", "confidence", "address",
                 "website", "place_id", "validation"],
    "properties": {
        "company_name": {"type": "string"},
        "status": {
            "type": "string",
            "enum": ["match", "ambiguous", "no_match", "out_of_area"]
        },
        "place_id": {"type": "string"},
        "matched_name": {"type": "string"},
        "address": {"type": "string"},
        "website": {"type": "string"},
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
        },
        "validation": {
            "type": "object",
            "required": ["geofence_ok", "city_in_whitelist",
                        "brand_match", "notes"],
            "properties": {
                "geofence_ok": {"type": "boolean"},
                "city_in_whitelist": {"type": "boolean"},
                "brand_match": {"type": "boolean"},
                "notes": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    }
}
```

**Schema enforcement**: Agent CANNOT return data that doesn't validate. Must include all required fields.

#### **3. Call Anthropic API**

```python
from anthropic import Anthropic

client = Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-5",
    system="""You enrich Bay Area biotech companies.

    Rules:
    1. ONLY use provided tools (places_text_search, place_details)
    2. Search with Bay Area location bias
    3. Evaluate ALL candidates, pick best scoring
    4. Apply geofence: US + CA + Bay Area city whitelist
    5. Check brand match: website domain should relate to company name
    6. At multi-tenant addresses, require brand match
    7. If no confident match (confidence < 0.75), return status=ambiguous
    8. Never hallucinate data - only use tool results
    """,
    tools=tools,
    tool_choice={"type": "any"},  # Must use tools

    # ⭐ ENFORCE STRUCTURED OUTPUT
    output_format={
        "type": "json_schema",
        "json_schema": {
            "name": "CompanyEnrichment",
            "schema": output_schema
        }
    },

    # ⭐ STRICT TOOL USE (can only use provided tools)
    strict=True,

    messages=[{
        "role": "user",
        "content": f"""Enrich this company:
        Name: {company_name}
        City: {city}, California

        Find the best match using Google Places. Return enriched data with validation.
        """
    }]
)
```

**What happens**:
1. Agent MUST call `places_text_search` (can't skip, strict mode)
2. Agent gets candidates, MUST call `place_details` for evaluation
3. Server returns candidates WITH validation metadata (score, gates, notes)
4. Agent picks best candidate based on server-provided scores
5. Agent MUST return JSON matching schema (can't skip validation field)
6. You get structured, validated output with confidence + reasoning

#### **4. Benefits Over Pure Python**

| Aspect | Pure Python Script | Anthropic Structured Outputs |
|--------|-------------------|------------------------------|
| **Flexibility** | Hard-coded scoring logic | Can adjust prompt, logic adapts |
| **Transparency** | Print statements | Structured reasoning in notes |
| **Validation** | Manual checks | Schema-enforced, can't skip fields |
| **Auditability** | Logs | Full decision trace with confidence |
| **Evolution** | Rewrite code | Update prompt or tools |
| **Hallucination risk** | N/A (no LLM) | Zero (strict tools + schema) |

**When to use**:
- If you're already using Claude Code for enrichment
- If you want auditable, explainable enrichment decisions
- If validation logic may evolve over time
- If you need confidence scores and provenance tracking

**When NOT to use**:
- If simple Python script works fine (don't over-engineer)
- If you don't need auditability (just want clean data)
- If you're not familiar with Anthropic API

### **Implementation Estimate**

**Time**: 2-3 days
- Set up Anthropic API client: 2-3 hours
- Define tools + schema: 2-3 hours
- Implement server-side validation: 4-6 hours (reuse scoring logic from Issue 1)
- Test on sample companies: 2-3 hours
- Integration with pipeline: 2-3 hours

**Complexity**: MEDIUM (requires API integration, but logic is same as Issue 1)

**Recommendation**: Implement Issue 1 validation in pure Python FIRST. Then optionally migrate to Anthropic structured outputs if you want the additional benefits.

---

## Root Cause Analysis: Systemic Issues

The individual issues above stem from **deeper systemic problems** in the data collection and validation process:

### **1. Over-Reliance on Automation**

**Problem**: Assumed automated enrichment (Google API) would produce accurate results
**Reality**: Automation is fast and complete, but accuracy requires validation
**Lesson**: Automation should **augment** human judgment, not replace it
**Fix**: Add validation gates (Issue 1 solution)

### **2. Absence of Validation at Collection Time**

**Problem**: No checks when data entered the dataset
**Reality**: Errors compound over time; early detection is easier than late correction
**Lesson**: Validate early and often; reject bad data at the source
**Fix**: Scoring + acceptance threshold (Issue 1 solution)

### **3. No Feedback Loop for Error Detection**

**Problem**: No way to discover errors once in dataset
**Reality**: Users find errors but can't report them; errors persist indefinitely
**Lesson**: Need error reporting mechanism and continuous improvement
**Fix**: Validation reporting + user feedback (Phase 4)

### **4. Assumption That External Sources = Ground Truth**

**Problem**: Trusted Google, Crunchbase, LinkedIn as authoritative
**Reality**: These sources have errors too; circular reference problem
**Lesson**: Only **primary sources** (company's own website) are truly authoritative
**Fix**: Company website as ground truth, BioPharmGuy as seed (Issue 7)

### **5. Lack of Canonical Identifier Strategy**

**Problem**: Treated name, website, address as equally important
**Reality**: These can diverge; need to pick one as "ground truth"
**Lesson**: Establish **identity resolution strategy** before collecting data
**Fix**: Website domain as primary key (Issue 5 solution)

### **6. Completeness Prioritized Over Accuracy**

**Problem**: Wanted 100% complete dataset (all fields filled)
**Reality**: Better to acknowledge gaps than publish wrong information
**Lesson**: **Accuracy > Completeness**; empty field better than wrong field
**Fix**: Prefer blanks to bad data (Issue 1, section D)

### **7. No Testing or Quality Metrics**

**Problem**: No automated tests to catch errors
**Reality**: Can't improve what you don't measure
**Lesson**: Need **data quality metrics** and **regression tests**
**Fix**: Validation reporting, domain reuse detection (Issue 3 solution)

### **8. "First Result Wins" Without Scoring**

**Problem**: Accepted first Google result without evaluation
**Reality**: First result often wrong (nearest match, not best match)
**Lesson**: Evaluate multiple candidates, score each, pick best above threshold
**Fix**: Pull top N, score all, accept if >= 0.75 (Issue 1, section C)

---

## Solution Framework: Strategic Approaches

Rather than fixing issues one-by-one, we need **strategic approaches** that address root causes:

### **Strategy 1: Manual Cleanup (Accuracy First)**

**Approach**: Accept that some data requires human verification

**Actions**:
- Manually verify high-value companies (top 200 by importance)
- Remove data that can't be verified (better gap than wrong)
- Flag uncertain data explicitly
- Build "verified" subset of dataset

**Trade-offs**:
- Time-intensive (hours per company)
- Doesn't scale to full dataset
- But: High accuracy for important companies

**When to use**: Critical companies, obvious errors, high-impact fields

### **Strategy 2: Multi-Source Verification (Trust But Verify)**

**Approach**: Require multiple independent sources to confirm data

**Actions**:
- Company website (primary source)
- BioPharmGuy (if available - Issue 7 fix adds this!)
- Google Maps (secondary, with validation)
- Only accept if 2+ sources agree OR single source with high confidence

**Concrete implementation**:
```python
def multi_source_verification(company_name, city):
    sources = {}

    # Source 1: BioPharmGuy (if available)
    biopharmguy_website = get_from_biopharmguy(company_name)
    if biopharmguy_website:
        sources['biopharmguy'] = {
            'website': biopharmguy_website,
            'confidence': 0.9  # High confidence (primary source)
        }

    # Source 2: Google Places (with validation)
    google_result = enrich_with_google(company_name, city)
    if google_result['status'] == 'match':
        sources['google'] = {
            'website': google_result['website'],
            'address': google_result['address'],
            'confidence': google_result['confidence']
        }

    # If 2+ sources, check agreement
    if len(sources) >= 2:
        websites = [s['website'] for s in sources.values()]
        if len(set(websites)) == 1:
            # Agreement! High confidence
            return sources['google']  # Has address too
        else:
            # Disagreement - flag for manual review
            return {'status': 'ambiguous', 'reason': 'source disagreement'}

    # Single source: accept if high confidence
    if sources and max(s['confidence'] for s in sources.values()) >= 0.75:
        return next(s for s in sources.values() if s['confidence'] >= 0.75)

    # No confident match
    return {'status': 'ambiguous'}
```

**Trade-offs**:
- Reduces errors but also reduces completeness
- Requires API integrations
- Some companies have poor online presence

**When to use**: Automated enrichment, batch updates

### **Strategy 3: Canonical Identifier (Identity Resolution)**

**Approach**: Use website domain as ground truth, derive other fields from it

**Actions**:
- Visit company website
- Extract name from website (not Google)
- Extract address from "Contact" page
- Use domain as primary key for deduplication

**Trade-offs**:
- Requires company has website
- Websites can be outdated
- But: Most stable identifier over time

**When to use**: Deduplication, identity conflicts

### **Strategy 4: Validation Rules (Automated Quality Checks)**

**Approach**: Define business rules that catch common errors

**Concrete rules** (from Issue 1 solution):
```python
VALIDATION_RULES = {
    'geofence': 'country=US AND state=CA AND city IN bay_area_whitelist',
    'brand_match': 'domain_brand IN normalized_company_name',
    'type_filter': 'REJECT IF types CONTAINS real_estate_agency',
    'multi_tenant': 'IF address IN known_incubators REQUIRE brand_match',
    'url_format': 'website MATCHES https?://[^/]+',
    'no_aggregators': 'website NOT IN (linkedin.com, yelp.com, facebook.com)',
    'no_duplicate_domains': 'domain appears only once in dataset',
    'company_stage': 'stage IN allowed_stages OR stage = Unknown'
}
```

**Implementation**:
- Pre-enrichment: Run on input data
- During enrichment: Apply as gates (Issue 1)
- Post-enrichment: Run as validation report
- Pre-commit: Run as git hook

**Trade-offs**:
- Rules can be too strict (false positives)
- Can't catch subtle errors
- But: Catches obvious errors automatically

**When to use**: Pre-commit hooks, CI/CD, batch validation

### **Strategy 5: Confidence Scoring (Know What We Don't Know)**

**Approach**: Track data quality per field, acknowledge uncertainty

**Actions**:
- Add "confidence" metadata (0.0-1.0 score)
- Add "source" metadata (company website, Google, BioPharmGuy, manual)
- Add "last_verified" date
- Expose confidence to users (let them decide trust level)

**Schema changes**:
```csv
Company Name,Website,Website_Source,Website_Confidence,Address,Address_Source,Address_Confidence,Last_Verified
Genentech,gene.com,manual,1.0,"1 DNA Way, SSF",google,0.95,2025-01-15
ATUM,atum.bio,biopharmguy,0.9,"37950 Central Ct, Newark",google,0.82,2025-01-15
```

**Trade-offs**:
- Schema becomes more complex
- Requires provenance tracking
- But: Transparency builds trust

**When to use**: All data collection, ongoing maintenance

### **Strategy 6: Feedback Loop (Continuous Improvement)**

**Approach**: Users report errors, we fix and learn

**Actions**:
- Add error reporting form to website
- Track common error patterns
- Update validation rules based on errors
- Publish corrections log

**Trade-offs**:
- Requires community engagement
- Ongoing maintenance burden
- But: Crowd-sourced validation scales

**When to use**: Post-publication, ongoing dataset maintenance

---

## Minimal Code Patches (Drop-In Ready)

These are the **exact code changes** to implement the core fixes. Copy-paste ready.

### **Patch 1: BioPharmGuy Website Extraction (30 minutes)**

**File**: `scripts/extract_biopharmguy_companies.py`

**Find this section** (around line that writes CSV row):
```python
writer.writerow({
    'Company Name': company_name,
    'City': city,
    'Focus Area': focus_area,
    'Source URL': source_url
})
```

**Replace with**:
```python
# Parse company website (second link in listing)
company_website = ''
if len(links) >= 2:
    company_website = links[1].get('href', '')

writer.writerow({
    'Company Name': company_name,
    'Website': company_website,  # ⭐ ADD THIS LINE
    'City': city,
    'Focus Area': focus_area,
    'Source URL': source_url
})
```

**Update CSV header** (top of file):
```python
# OLD:
writer = csv.DictWriter(f, fieldnames=['Company Name', 'City', 'Focus Area', 'Source URL'])

# NEW:
writer = csv.DictWriter(f, fieldnames=['Company Name', 'Website', 'City', 'Focus Area', 'Source URL'])
```

### **Patch 2: Domain Reuse Detection (1-2 hours)**

**File**: `scripts/merge_company_sources.py`

**Add at top of file** (after imports):
```python
def brand_from_domain(url):
    """Extract brand from domain (leftmost label)."""
    import re
    m = re.search(r'^(?:https?://)?(?:www\.)?([^/]+)', url or '', re.I)
    if not m:
        return ''
    left = m.group(1).split('.')[0]
    return re.sub('[^a-z0-9]', '', left.lower())

def detect_domain_reuse(companies):
    """Flag domains assigned to multiple companies."""
    from collections import defaultdict

    domain_to_companies = defaultdict(list)

    for idx, company in enumerate(companies):
        website = company.get('Website', '').strip()
        if website:
            domain = brand_from_domain(website)
            if domain:
                domain_to_companies[domain].append({
                    'index': idx,
                    'name': company.get('Company Name', ''),
                    'address': company.get('Address', '')
                })

    # Allowlist for legitimate multi-brand domains
    ALLOWED_MULTI_BRAND = {'gene.com'}

    duplicates = {}
    for domain, company_list in domain_to_companies.items():
        if len(company_list) > 1 and domain not in ALLOWED_MULTI_BRAND:
            duplicates[domain] = company_list

    # Report
    if duplicates:
        print(f"\n⚠️  WARNING: Found {len(duplicates)} domains assigned to multiple companies:")
        print("   This indicates potential data quality issues (shared address contamination)")
        for domain, companies in list(duplicates.items())[:10]:
            print(f"\n  {domain} ({len(companies)} companies):")
            for c in companies[:5]:
                print(f"    - Row {c['index']}: {c['name']}")
            if len(companies) > 5:
                print(f"    ... and {len(companies) - 5} more")
        print()

    return duplicates
```

**Add before final save** (in `main()` function):
```python
def main():
    # ... existing code ...

    # After merging, before saving
    merged_companies = merge_and_deduplicate(existing, wikipedia, biopharmguy)

    # ⭐ ADD THIS: Detect domain reuse
    duplicates = detect_domain_reuse(merged_companies)
    if duplicates:
        print(f"💡 TIP: Review duplicate domains before enrichment")
        print(f"   Run manual verification on these companies")

    # Save
    save_companies(merged_companies, output_path)
```

### **Patch 3: Enrichment Validation Gates (1 day)**

**File**: `scripts/enrich_with_google_maps.py`

**Add at top** (after imports, before functions):
```python
# Bay Area configuration
BAY_CENTER = (37.7749, -122.4194)  # San Francisco
BAY_RADIUS_M = 80000  # ~50 miles

# Bay Area cities whitelist (from methodology appendix)
BAY_AREA_CITIES = {
    # Alameda County
    'Alameda', 'Albany', 'Berkeley', 'Dublin', 'Emeryville', 'Fremont',
    'Hayward', 'Livermore', 'Newark', 'Oakland', 'Pleasanton', 'San Leandro',
    'Union City',
    # Contra Costa County
    'Antioch', 'Concord', 'Richmond', 'San Ramon', 'Walnut Creek',
    # Marin County
    'Novato', 'San Rafael',
    # San Francisco County
    'San Francisco',
    # San Mateo County
    'Belmont', 'Burlingame', 'Foster City', 'Menlo Park', 'Redwood City',
    'San Carlos', 'San Mateo', 'South San Francisco',
    # Santa Clara County
    'Campbell', 'Cupertino', 'Milpitas', 'Mountain View', 'Palo Alto',
    'San Jose', 'Santa Clara', 'Sunnyvale',
    # Solano County
    'Benicia', 'Fairfield', 'Vallejo',
    # Sonoma County
    'Petaluma', 'Santa Rosa'
}

# Multi-tenant addresses (known incubators)
MULTITENANT_ADDRESSES = {
    "201 Gateway Blvd, South San Francisco, CA 94080, USA",
    "544b Bryant St, San Francisco, CA 94107, USA",
}

# Aggregator domains (never valid company websites)
AGGREGATOR_DOMAINS = {'linkedin.com', 'yelp.com', 'facebook.com',
                      'crunchbase.com', 'mbcbiolabs.com'}

GENERIC_TOKENS = {'bio','biosciences','biotech','therapeutics','inc',
                  'corp','llc','company','pharma','pharmaceuticals'}

def normalize(s):
    """Remove generic tokens and special chars."""
    s = re.sub(r'\([^)]*\)', '', s or '')
    s = re.sub(r'[^a-z0-9 ]', '', s.lower())
    return ' '.join(w for w in s.split() if w not in GENERIC_TOKENS)

def brand_from_domain(url):
    """Extract brand from domain."""
    m = re.search(r'^(?:https?://)?(?:www\.)?([^/]+)', url or '', re.I)
    if not m:
        return ''
    left = m.group(1).split('.')[0]
    return re.sub('[^a-z0-9]', '', left.lower())

def is_bay_area(address_components):
    """Validate address is US + CA + Bay Area."""
    country = next((c['short_name'] for c in address_components
                    if 'country' in c['types']), '')
    state = next((c['short_name'] for c in address_components
                  if 'administrative_area_level_1' in c['types']), '')
    city = next((c['long_name'] for c in address_components
                 if 'locality' in c['types']), '')

    if country != 'US' or state != 'CA':
        return False, city

    if city not in BAY_AREA_CITIES:
        return False, city

    return True, city

def is_business_type(types):
    """Filter out building-level listings."""
    REJECT_TYPES = {'real_estate_agency', 'lodging'}
    if any(t in types for t in REJECT_TYPES):
        return False
    return True

def brand_matches(company_name, candidate_name, website):
    """Check if website domain relates to company name."""
    if not website:
        return False

    if any(agg in website.lower() for agg in AGGREGATOR_DOMAINS):
        return False

    domain_brand = brand_from_domain(website)
    if not domain_brand:
        return False

    norm_company = normalize(company_name).replace(' ', '')
    norm_candidate = normalize(candidate_name).replace(' ', '')

    return (domain_brand in norm_company) or (domain_brand in norm_candidate)

def is_multitenant_address(formatted_address):
    """Check if address is known shared location."""
    return any(known in formatted_address for known in MULTITENANT_ADDRESSES)

def score_candidate(company_name, expected_city, details):
    """
    Score candidate from 0-1.
    Returns: (score, validation_dict, accept_decision)
    """
    address_components = details.get('address_components', [])

    # GATE 1: Geofence
    in_bay, city = is_bay_area(address_components)
    if not in_bay:
        return 0.0, {
            'geofence_ok': False,
            'city_in_whitelist': False,
            'brand_match': False,
            'notes': [f'Out of Bay Area: {city}']
        }, False

    # GATE 2: Business type
    types = set(details.get('types', []))
    if not is_business_type(types):
        return 0.0, {
            'geofence_ok': True,
            'city_in_whitelist': True,
            'brand_match': False,
            'notes': ['Rejected: building/real estate type']
        }, False

    # GATE 3: Brand match
    website = details.get('website', '')
    candidate_name = details.get('name', '')
    brand_ok = brand_matches(company_name, candidate_name, website)

    # GATE 4: Multi-tenant handling
    formatted_addr = details.get('formatted_address', '')
    is_multitenant = is_multitenant_address(formatted_addr)
    if is_multitenant and not brand_ok:
        return 0.0, {
            'geofence_ok': True,
            'city_in_whitelist': True,
            'brand_match': False,
            'notes': ['Multi-tenant address without brand match']
        }, False

    # SCORING
    def name_similarity(a, b):
        A, B = set(normalize(a).split()), set(normalize(b).split())
        if not A or not B:
            return 0.0
        return len(A & B) / len(A | B)

    sim = name_similarity(company_name, candidate_name)
    city_match = 1.0 if city == expected_city else 0.0
    brand_score = 1.0 if brand_ok else 0.0
    type_penalty = 0.1 if {'real_estate_agency', 'premise'} & types else 0.0

    score = (0.5 * sim) + (0.2 * city_match) + (0.2 * brand_score) - type_penalty

    if is_multitenant and not brand_ok:
        score -= 0.4

    notes = []
    if is_multitenant:
        notes.append('Multi-tenant address')
    if website and not brand_ok:
        notes.append('Website brand mismatch')
    if sim < 0.3:
        notes.append(f'Low name similarity: {sim:.2f}')

    validation = {
        'geofence_ok': True,
        'city_in_whitelist': city in BAY_AREA_CITIES,
        'brand_match': brand_ok,
        'notes': notes
    }

    accept = score >= 0.75

    return score, validation, accept
```

**Replace `search_place()` function**:
```python
def search_place(gmaps, company_name, city):
    """
    Search for company using Google Places with validation.
    Returns enriched data OR None if no confident match.
    """
    try:
        # Text Search with Bay Area bias
        query = f"{company_name} {city} CA biotech"
        results = gmaps.places(query, location=BAY_CENTER, radius=BAY_RADIUS_M)

        if results['status'] != 'OK' or not results.get('results'):
            return None

        # Get top N candidates
        candidates = results['results'][:5]

        best_score = 0.0
        best_match = None
        best_validation = None

        # Evaluate each candidate
        for candidate in candidates:
            place_id = candidate['place_id']

            # Fetch details
            details_response = gmaps.place(
                place_id,
                fields=['name', 'formatted_address', 'address_components',
                       'website', 'types', 'geometry', 'business_status']
            )

            if details_response['status'] != 'OK':
                continue

            details = details_response['result']

            # Score candidate
            score, validation, accept = score_candidate(company_name, city, details)

            if accept and score > best_score:
                best_score = score
                best_match = details
                best_validation = validation

        if best_match:
            return {
                'name': best_match.get('name', ''),
                'address': best_match.get('formatted_address', ''),
                'website': best_match.get('website', ''),
                'lat': best_match.get('geometry', {}).get('location', {}).get('lat', ''),
                'lng': best_match.get('geometry', {}).get('location', {}).get('lng', ''),
                'confidence': best_score,
                'validation': best_validation
            }
        else:
            # No confident match - return None (will leave fields empty)
            return None

    except Exception as e:
        print(f"  Error searching for {company_name}: {e}")
        return None
```

**Add validation reporting** (in `main()` function, after enrichment loop):
```python
def main():
    # ... existing code ...

    # After enrichment loop
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    total = len(companies)
    enriched = sum(1 for c in companies if c.get('Address'))
    ambiguous = total - enriched

    print(f"Total companies: {total}")
    print(f"Successfully enriched: {enriched} ({(enriched/total)*100:.1f}%)")
    print(f"Ambiguous/no match: {ambiguous} ({(ambiguous/total)*100:.1f}%)")
    print("\n💡 Ambiguous companies have blank address/website (better than wrong data)")
    print("   Review these manually or accept data gaps")
    print()
```

---

## Prioritized Action Plan (Updated with Technical Fixes)

Organize work by **strategic goal**, now with **specific code patches**:

### **Phase 1: Stop the Bleeding (1-2 weeks)**

**Goal**: Fix obvious errors, prevent new errors with validation gates

**Actions**:
1. ✅ **Patch BioPharmGuy extractor** (30 min - Patch 1 above)
   - Add Website column to output
   - Re-run extraction to get ~200 validated websites

2. ✅ **Add domain reuse detection** (1-2 hours - Patch 2 above)
   - Add to merge script
   - Run to identify current duplicates
   - Manual review flagged cases

3. ✅ **Implement validation gates in enrichment** (1 day - Patch 3 above)
   - Geofence (US + CA + Bay Area)
   - Brand-domain check
   - Multi-tenant address handling
   - Scoring with 0.75 threshold
   - Prefer blanks to bad data

4. ✅ Fix data entry errors (URLs in wrong fields, schema violations) - 1 hour

5. ✅ Update documentation to accurate counts - 30 min

6. ✅ Remove companies outside geographic scope (if strict boundary) - 1 hour

7. ✅ Add basic validation tests (schema, required fields, allowed values) - 2-3 hours

8. ✅ Establish canonical identifier rule (website domain) - decision + update merge script

**Success criteria**:
- No more obvious errors
- Docs match reality
- Validation gates prevent contamination
- ~90% enriched with confidence >= 0.75
- ~10% ambiguous (blank fields, not wrong data)

**Time estimate**: 3-5 days (including testing)

### **Phase 2: Establish Ground Truth (1 month)**

**Goal**: Build high-confidence subset of dataset

**Actions**:
1. ✅ Manually verify top 200 companies (by importance/size)
   - Visit website, extract name, address, stage
   - Mark as "verified" with verification date
   - Compare to enriched data, fix discrepancies

2. ✅ Deduplicate using domain-based strategy
   - Merge companies with same domain
   - Track name variations as aliases
   - Use domain reuse detection (Patch 2) to find cases

3. ✅ Remove/flag companies with conflicting identifiers
   - If name/website/address don't align, flag for review
   - Use brand_from_domain() to check consistency

4. ✅ Accept data gaps for unverifiable companies
   - Remove wrong data, leave fields empty
   - Add confidence scores

5. ✅ **(Optional) Set up Anthropic structured outputs** (2-3 days)
   - If you want auditable, explainable enrichment
   - Reuse validation logic from Patch 3
   - Add schema enforcement

**Success criteria**: 200 high-confidence companies, clear verification status, domain-based deduplication working

**Time estimate**: 20-30 hours over 4 weeks

### **Phase 3: Systematic Cleanup (2-3 months)**

**Goal**: Address error categories systematically

**Actions**:
1. ✅ **Google API contamination**: Re-enrich with validation
   - Use website as ground truth (BioPharmGuy + manual)
   - Only fill gaps, don't overwrite verified data
   - Require name matching + domain verification (Patch 3)

2. ✅ **Shared address disambiguation**: Manual review of incubators
   - Create comprehensive whitelist of known shared addresses
   - Verify each tenant manually
   - Use multi-tenant handling (Patch 3)

3. ✅ **Company stage improvement**: External validation
   - FDA database lookup
   - ClinicalTrials.gov check
   - Manual curation for top 200
   - Accept Unknown for rest (don't force classification)

4. ✅ **Documentation schema alignment**: Standardize naming
   - Pick "Focus Areas" vs "Notes"
   - Update all docs

**Success criteria**: Each error category addressed, <30% Unknown stage, <5% flagged for review

**Time estimate**: 40-60 hours over 2-3 months

### **Phase 4: Infrastructure (3-6 months)**

**Goal**: Build sustainable data quality pipeline

**Actions**:
1. ✅ **Automated validation**: CI/CD with quality checks
   - Run validation script on every commit
   - Fail if domain reuse detected
   - Fail if docs out of sync

2. ✅ **Provenance tracking**: Source + confidence per field
   - Add columns: Website_Source, Website_Confidence, Last_Verified
   - Track where data came from

3. ✅ **Feedback mechanism**: User error reporting
   - Add form to website
   - Track corrections

4. ✅ **Versioning**: Clear dataset versions with changelogs
   - Tag releases (v3.1, v3.2, etc.)
   - Document changes

5. ✅ **Documentation generation**: Auto-update from data
   - Compute company count from CSV
   - Generate stats automatically

**Success criteria**: New data validated before entry, users can report errors, clear data provenance

**Time estimate**: 60-80 hours over 3-6 months

---

## Open Questions & Decisions Needed

Strategic decisions required before proceeding:

### **Q1: Accuracy vs Completeness Trade-off**

**Question**: Is it better to have 1,172 companies with ~20% having quality issues, or ~900 high-confidence companies with gaps in the rest?

**Options**:
- **A**: Keep all companies, flag confidence level (transparency approach)
- **B**: Remove unverifiable companies (quality over quantity)
- **C**: Two-tier dataset: "verified" vs "unverified" subsets

**Technical implementation** (if Option C):
```csv
company_id,tier,Company Name,Website,...
1,verified,Genentech,gene.com,...
2,verified,BioMarin,biomarin.com,...
...
800,unverified,SmallCo Inc,,...  (blank fields OK)
```

**Implications**: Affects user expectations and dataset positioning

**Recommendation**: Option C (two-tier) - best of both worlds. Ship verified subset immediately, improve unverified over time.

---

### **Q2: Geographic Boundary Definition**

**Question**: Should Davis, CA companies be included? (80 miles from Bay Area, Central Valley)

**Options**:
- **A**: Strict 9-county Bay Area only (remove Davis)
- **B**: Flexible "Greater Bay Area" including Central Valley biotech (keep Davis)
- **C**: Document both, let users filter

**Technical implementation** (if Option A):
- Geofence already rejects Davis (Patch 3)
- Remove 2 Davis companies from current dataset
- Document exclusion in METHODOLOGY.md

**Implications**: Affects dataset scope and user expectations

**Recommendation**: Option A (strict boundary) with documentation of exclusion rationale. Geofence is already implemented.

---

### **Q3: Acquired Company Handling**

**Question**: How to handle acquired companies (e.g., ARMO BioSciences acquired by Eli Lilly)?

**Options**:
- **A**: Remove acquired companies (focus on active companies)
- **B**: Keep with "Acquired" stage, note acquiring company
- **C**: Keep with link to parent company

**Implications**: Historical value vs current-state snapshot

**Recommendation**: Option B - valuable for understanding ecosystem history. Update Focus Areas to note "Acquired by [Parent] in [Year]".

---

### **Q4: Manual Curation Level**

**Question**: How many companies should be manually verified?

**Options**:
- **A**: All 1,172 companies (comprehensive but time-intensive)
- **B**: Top 200 by importance (high-value subset)
- **C**: Staged approach: verify as needed, prioritize user requests

**Time estimates**:
- Option A: 1,172 companies × 15 min/company = 293 hours (7+ weeks full-time)
- Option B: 200 companies × 15 min/company = 50 hours (1-2 weeks)
- Option C: 50-100 hours spread over months

**Implications**: Time investment vs dataset quality

**Recommendation**: Option B → C - start with top 200 (Phase 2), then ongoing curation (Phase 3-4). Use validation gates (Patch 3) to catch errors automatically for the rest.

---

### **Q5: Empty Fields Policy**

**Question**: When we can't verify data, should we leave it empty or mark "Unknown"?

**Options**:
- **A**: Empty field (NULL) - explicit absence of data
- **B**: "Unknown" text - explicitly states uncertainty
- **C**: Remove row entirely - only include complete records

**Implications**: User experience and data interpretation

**Recommendation**:
- **Company Stage**: Use "Unknown" (categorical field, "Unknown" is valid category)
- **Address/Website**: Leave empty (better than wrong - already implemented in Patch 3!)
- **Focus Areas**: Leave empty if can't verify
- **Don't remove rows** (Option C) - 1,172 companies is better than 900, as long as blanks are intentional

---

## Conclusion: Path Forward

The V3 dataset faces **systematic data quality challenges** stemming from over-reliance on automated enrichment without sufficient validation. The good news: **these problems are fixable** with a strategic, phased approach **and we now have specific code patches ready to implement**.

### **Key Principles for Data Quality**

1. **Accuracy > Completeness**: Better to acknowledge gaps than publish wrong information
2. **Primary Sources > Aggregators**: Only company websites are truly authoritative
3. **Manual Verification > Automation**: For critical data, human judgment is essential
4. **Transparency > Perfection**: Acknowledge limitations, expose confidence levels
5. **Validation > Collection**: Catch errors early; validate before accepting data
6. **Continuous Improvement > One-Time Fix**: Build feedback loop for ongoing quality
7. **Blanks > Wrong Data**: Empty field is better than incorrect field (implemented in Patch 3!)
8. **Evaluate Multiple Candidates**: Pull top N, score all, pick best (implemented in Patch 3!)

### **Realistic Expectations**

- **Quick fixes** (1 week): BioPharmGuy patch + validation gates + domain detection = prevent 20-25% contamination
- **High-quality subset** (1 month): 200 verified companies + ~70% confidence for rest with validation
- **Systematic cleanup** (3 months): Each error category addressed, <30% Unknown, domain-based deduplication
- **Sustainable pipeline** (6 months): Validation infrastructure, provenance tracking, CI/CD

### **Success Metrics**

- **Enrichment confidence**: % of companies with enrichment confidence >= 0.75
- **Verification status**: % of companies with verified data (manual or multi-source)
- **Confidence distribution**: High/Medium/Low confidence breakdown
- **Error rate**: % of records with known errors (from validation flags)
- **Documentation accuracy**: Docs match data (automated check)
- **User trust**: Can users rely on the dataset?
- **Domain reuse**: 0 duplicate domains (from Patch 2 detection)

### **Immediate Next Steps**

1. **This week**:
   - Apply Patch 1 (BioPharmGuy Website - 30 min)
   - Apply Patch 2 (Domain reuse detection - 1-2 hours)
   - Review flagged duplicates manually

2. **Next week**:
   - Apply Patch 3 (Validation gates - 1 day)
   - Test on sample of 50 companies
   - Run full enrichment with validation
   - Review ambiguous cases (confidence < 0.75)

3. **Month 1**:
   - Manual verification of top 200 companies
   - Domain-based deduplication
   - Update documentation

4. **Months 2-3**:
   - Systematic cleanup of error categories
   - Company stage manual curation
   - CI/CD pipeline setup

The dataset has **great bones** (excellent address coverage, comprehensive scope), but needs **strategic data quality work with specific technical implementation** to reach its potential. The issues are known, the solutions are clear and coded, and the path forward is achievable.

---

**Next Steps**:
1. Review this document and code patches
2. Make strategic decisions (Open Questions)
3. Apply Patch 1, 2, 3 in sequence
4. Test on sample data
5. Proceed with Phase 1 full implementation
