# Expansion Strategy: Simple & Efficient Approach (80/20 Rule)

**Status**: Future roadmap (Phase 3+)
**Current State**: 171 companies (manually curated)
**Goal**: Efficient expansion using subagents - 20% effort for 80% results

---

## Philosophy: Keep It Simple

**What we're NOT doing**:
- ❌ Building complex API integrations
- ❌ Writing elaborate web scrapers
- ❌ Running expensive Google Places queries
- ❌ Maintaining complicated automation

**What we ARE doing**:
- ✅ Using subagents to do focused research tasks
- ✅ Leveraging free/existing resources (Wikipedia, directories)
- ✅ Adding only high-value companies (quality over quantity)
- ✅ Keeping maintenance burden low

---

## The 80/20 Approach: 3 Simple Expansions

### Expansion 1: Mine Existing Directories (Subagent Task)
**Effort**: 30 minutes | **Gain**: +50-100 companies

**Task for subagent**:
> "Search BioPharmGuy California directory and Wikipedia 'Companies based in SF Bay Area' for biotech companies. Extract: company name, city, website. Focus on companies we don't already have in our 171-company list. Return as CSV format."

**Why this works**: These directories already exist, subagent can scrape/extract quickly

**Expected output**: 50-100 new companies with basic info

---

### Expansion 2: Keyword Enrichment for Existing Companies (Subagent Batch Tasks)
**Effort**: 1-2 hours | **Gain**: Technology focus tags for all 171 companies

**Controlled Vocabulary** (from ChatGPT methodology - the good part!):

| Tag | Keywords to Look For |
|-----|---------------------|
| Antibody | antibody, bispecific, ADC, monoclonal |
| CRISPR | CRISPR, Cas, Cas9, base editor, gene editing |
| Gene Therapy | AAV, lentiviral, viral vector, gene therapy |
| Cell Therapy | CAR-T, cell therapy, iPSC, stem cell |
| Protein Engineering | protein engineering, directed evolution, AlphaFold |
| Diagnostics | diagnostic, liquid biopsy, IVD, CLIA |
| CDMO/CRO | CDMO, CRO, contract manufacturing |
| Synthetic Biology | synthetic biology, metabolic engineering |

**Task for subagent** (run in batches of 10-20 companies):
> "Visit the websites for these 10 companies: [list]. For each, read their homepage/about page and tag them with relevant keywords from this list: [taxonomy]. Return company name and comma-separated tags."

**Why this works**: Subagents can read websites and extract keywords quickly

**Expected output**: Each company tagged with 2-4 relevant keywords

---

### Expansion 3: Fill Known Gaps (Targeted Subagent Research)
**Effort**: 1 hour | **Gain**: +20-30 high-value companies

**Known gaps** in our current list:
- South Bay (San Jose, Sunnyvale) - underrepresented
- Diagnostics companies - fewer than expected
- CROs/CDMOs - service providers
- Newer startups (founded 2020+)

**Task for subagent**:
> "Find 20-30 biotech companies in [San Jose, Sunnyvale, Mountain View] that we don't already have. Focus on diagnostics, genomics, and contract services. For each, provide: name, address, website, brief description."

**Why this works**: Targeted search, high-value additions, subagent can do research

**Expected output**: 20-30 quality additions in underrepresented areas

---

## Using Subagents Effectively (The Key!)

### Pattern: Launch Multiple Subagents in Parallel

Instead of writing complex Python scripts, **use the Task tool with multiple subagents**:

**Example - Keyword Tagging (Run 5-10 in parallel)**:
```
Task 1: Tag companies 1-20 with keywords
Task 2: Tag companies 21-40 with keywords
Task 3: Tag companies 41-60 with keywords
... (etc)
```

**Each task runs independently**, completes in 5-10 minutes, returns structured data

### Pattern: Focused Research Tasks

**Instead of**: "Find all biotech companies in Bay Area"
**Do**: "Find 20 diagnostics companies in South Bay we don't have"

**Instead of**: "Scrape all websites for keywords"
**Do**: "Tag these 15 companies with keywords from this taxonomy"

---

## Practical Implementation (Phases 3a, 3b, 3c)

### Phase 3a: Add Existing Directory Companies (30 min effort)
**Goal**: +50-100 companies from existing sources

**Steps**:
1. Launch subagent: "Extract Bay Area biotech from BioPharmGuy directory"
2. Launch subagent: "Extract biotech from Wikipedia SF Bay Area companies"
3. Merge results, dedupe against our 171 companies
4. Add new companies to CSV (name, website, city, address if available)

**Output**: `companies_v2.csv` with ~220-270 companies

---

### Phase 3b: Keyword Enrichment (1-2 hours effort)
**Goal**: Tag all companies with technology focus

**Steps**:
1. Create batches of 10-20 companies
2. Launch 5-10 subagents in parallel (one batch each)
3. Each subagent: Visit websites, apply controlled vocabulary, return tags
4. Merge results into new "Keywords" column

**Output**: All companies have 2-4 technology tags

---

### Phase 3c: Fill Targeted Gaps (1 hour effort)
**Goal**: +20-30 high-value additions in underrepresented areas

**Steps**:
1. Identify gaps: South Bay, diagnostics, newer startups
2. Launch 2-3 subagents with focused searches
3. Manual review of additions (quick skim)
4. Add to final CSV

**Output**: `companies_v3.csv` with ~240-300 companies, keyword-tagged

---

## Total Effort vs. Gain

| Phase | Effort | Gain | Method |
|-------|--------|------|--------|
| **3a: Directory Mining** | 30 min | +50-100 companies | Subagent extraction |
| **3b: Keyword Tagging** | 1-2 hours | Tags for all companies | Parallel subagents |
| **3c: Targeted Gaps** | 1 hour | +20-30 quality adds | Focused subagent research |
| **TOTAL** | **2.5-3.5 hours** | **+70-130 companies + full keyword enrichment** | **Subagents do the work!** |

**That's the 80/20 principle**: Minimal manual effort, maximum value through smart use of subagents.

---

## Key Simplifications (vs. Complex Approach)

**Complex approach** (original ChatGPT plan):
- Google Places API ($30-50 cost)
- OpenCorporates integration
- TF-IDF analysis
- Custom Python scrapers
- Ongoing maintenance automation

**Simple approach** (our 80/20 version):
- ✅ Use existing directories (free)
- ✅ Subagents for research (built-in capability)
- ✅ Controlled vocabulary (simple keyword matching)
- ✅ One-time enrichment (no automation needed)
- ✅ Manual spot-checks (acceptable for this scale)

---

## When to Use This (After Phase 2)

**Current Priority**: Phase 2 (careers URLs for 171 companies)

**Then decide**:
- Option A: Build map with 171 companies → Phase 3 expansion later
- Option B: Do Phase 3a-c first (add 70-130 companies) → then build map with ~240-300
- Option C: Skip expansion, keep it lean at 171 (quality over quantity)

**Recommendation**: Do Phase 2 first (careers URLs are highest value for job seekers), then reassess based on feedback.

---

## Controlled Vocabulary Reference (Keep It Simple)

**Use these 8 core tags** (don't overcomplicate):

1. **Antibody** - Antibody therapeutics, bispecifics, ADCs
2. **CRISPR** - Gene editing, Cas9, base editing
3. **Gene Therapy** - AAV, viral vectors, gene delivery
4. **Cell Therapy** - CAR-T, iPSC, stem cells
5. **Protein Engineering** - Computational design, directed evolution
6. **Diagnostics** - IVD, liquid biopsy, molecular diagnostics
7. **CDMO/CRO** - Contract services, manufacturing
8. **Synthetic Biology** - Metabolic engineering, biomanufacturing

**How to apply**: Subagent reads homepage → identifies 2-4 matching tags → returns list

---

## Summary: Simple, Subagent-Driven Expansion

**Instead of complex infrastructure**:
- Launch 10-15 focused subagent tasks
- Let them do the research/extraction/tagging
- Manual review only for final additions
- Total time: 2.5-3.5 hours for 80% of the value

**Result**: 240-300 well-tagged companies ready for mapping

**Philosophy**: Use AI to do AI things. Keep human effort minimal and high-value (review, decisions, not manual data entry).

---

**Last Updated**: January 8, 2025
**Status**: Streamlined approach - ready when Phase 2 complete
**Effort**: 2.5-3.5 hours total
**Cost**: $0 (using free resources + subagents)

---

## Why Expand? (Phase 3+ Rationale)

**Current approach (Phase 1-2)**: Manual curation
- ✅ High quality, verified data
- ✅ 171 companies across Bay Area
- ❌ Limited coverage (estimated 40-50% of total ecosystem)
- ❌ Manual updates required
- ❌ May miss newer/smaller companies

**Expanded approach (Phase 3+)**: Programmatic discovery + verification
- ✅ Near-complete coverage (300-500+ companies)
- ✅ Automated discovery of new companies
- ✅ Systematic keyword tagging
- ✅ Regular automated updates possible
- ⚠️ Requires API keys, more complex infrastructure
- ⚠️ Higher maintenance burden

---

## 1. Geographic Definition (Ground Truth)

### Bay Area Counties (Official Boundaries)

Instead of fuzzy "Bay Area" concept, use **10 counties** as ground truth:

**Core East Bay**:
- Alameda County
- Contra Costa County

**Peninsula & SF**:
- San Francisco County
- San Mateo County

**South Bay**:
- Santa Clara County

**North Bay**:
- Marin County
- Napa County
- Sonoma County
- Solano County

**Optional** (sometimes included):
- Santa Cruz County
- San Benito County

**Why this matters**:
- Precise geocoding validation (coordinates must fall within county boundaries)
- Systematic city-by-city search (exhaustive coverage)
- Clear inclusion/exclusion criteria

---

## 2. Data Sources (Authoritative & Programmatic)

### A. Seed Sources (Human-Curated Lists)

**Wikipedia** - "Companies based in San Francisco Bay Area" (biotech subset)
- **Purpose**: High-level seed entities, well-known companies
- **URL**: https://en.wikipedia.org/wiki/Category:Companies_based_in_the_San_Francisco_Bay_Area
- **Coverage**: ~50-100 major biotech companies
- **Accuracy**: High (but limited to notable companies)

**BioPharmGuy California Directory**
- **Purpose**: Wide life-science directory with locations
- **URL**: http://www.biopharmguy.com/links/state-ca.php
- **Coverage**: Broad (CROs, CDMOs, diagnostics, tools, etc.)
- **Use**: Recall-focused (verify each entry)

**OpenCorporates** - Legal entity database
- **Purpose**: Verify company legal status, registered addresses
- **URL**: https://opencorporates.com/
- **Query**: Filter by jurisdiction (California) + industry keywords
- **Use**: Deduplication, verification, backup addresses

### B. Programmatic Discovery (APIs)

**Google Places API - Text Search + Place Details**
- **Purpose**: Systematic discovery by city + keyword
- **Coverage**: Best for currently operating businesses with physical locations
- **Cost**: ~$17 per 1000 requests (Text Search), $17 per 1000 (Place Details)
- **Docs**: https://developers.google.com/maps/documentation/places/web-service/text-search

**Method**:
```python
# Iterate through:
cities = ["Berkeley, CA", "Emeryville, CA", "Oakland, CA", ...]
keywords = ["biotechnology", "biopharma", "CRISPR", "gene therapy", ...]

for city in cities:
    for keyword in keywords:
        results = google_places_text_search(f"{keyword} in {city}")
        # Returns: place_id, name, address, lat/lon, website
```

**OpenStreetMap Overpass API**
- **Purpose**: Cross-check, incremental recall
- **Coverage**: Sparse for biotech, but free and useful for validation
- **Query**: Features tagged with biotech-related tags within Bay Area bounding boxes
- **Docs**: https://wiki.openstreetmap.org/wiki/Overpass_API

---

## 3. NAICS Industry Codes (Classification)

### Relevant NAICS Codes for Biotechnology

**Primary**:
- **541714**: Research and Development in Biotechnology (except Nanobiotechnology)

**Secondary**:
- **541715**: Research and Development in the Physical, Engineering, and Life Sciences (except Nanotechnology and Biotechnology)
- **325414**: Biological Product (except Diagnostic) Manufacturing
- **325413**: In-Vitro Diagnostic Substance Manufacturing
- **541380**: Testing Laboratories (for diagnostics/analytical services)

**Use Cases**:
1. **Discovery**: Query business registries by NAICS code
2. **Validation**: Verify companies are actually biotech (not misclassified)
3. **Categorization**: Distinguish R&D vs. manufacturing vs. services

**Resources**:
- Official NAICS: https://www.census.gov/naics/
- NAICS Association: https://www.naics.com/six-digit-naics/

---

## 4. Normalization, Deduplication & Verification

### A. Normalization Rules

**Company Name Canonicalization**:
```python
def normalize_name(name):
    # Lowercase
    name = name.lower()

    # Remove common suffixes
    suffixes = ["inc", "inc.", "corp", "corp.", "llc", "ltd", "limited",
                "therapeutics", "biosciences", "technologies", "corporation"]
    for suffix in suffixes:
        name = re.sub(rf'\b{suffix}\b', '', name)

    # Strip punctuation, extra spaces
    name = re.sub(r'[^\w\s]', '', name)
    name = ' '.join(name.split())

    return name
```

**Website Domain Canonicalization**:
```python
import tldextract

def canon_domain(url):
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}"  # e.g., "ginkgobioworks.com"
```

### B. Deduplication Strategy

**Multi-level deduplication** (in order):

1. **Exact domain match**: Same website domain → same company
2. **Fuzzy name match** (within same city):
   ```python
   from rapidfuzz import fuzz
   if fuzz.ratio(name1, name2) >= 90:  # 90% similarity threshold
       # Likely duplicate
   ```
3. **Proximity deduplication**: Same lat/lon within 50-100 meters + similar name → likely duplicate

### C. Verification Chain (Confidence Scoring)

Build a confidence score for each company:

| Source | Points | Notes |
|--------|--------|-------|
| Google Places verified | +3 | High confidence (currently operating) |
| Company website 200 OK | +2 | Website is live and accessible |
| OpenCorporates legal record | +2 | Registered business entity |
| In seed directory (Wikipedia/BioPharmGuy) | +1 | Known company |
| NAICS code matches | +1 | Industry classification confirmed |

**Threshold**: Keep companies with score ≥ 4 for high-quality dataset

---

## 5. Keyword Enrichment (Controlled Vocabulary)

### A. Technology Focus Taxonomy

Based on ChatGPT methodology, create a controlled vocabulary of biotech domains:

#### Therapeutic Modalities
- **antibody**: antibody, bispecific, ADC, Fc, monoclonal, IgG
- **CRISPR**: CRISPR, Cas, Cas9, Cas12, base editor, prime editor, guide RNA, genome editing
- **gene therapy**: AAV, adeno-associated virus, lentiviral, viral vector, capsid, gene therapy, gene delivery
- **cell therapy**: CAR-T, cell therapy, T cell, NK cell, iPSC, stem cell, allogeneic, autologous
- **RNA therapeutics**: mRNA, siRNA, antisense, RNA, lipid nanoparticle, LNP
- **protein therapeutics**: fusion protein, cytokine, enzyme replacement, recombinant protein

#### Technology Platforms
- **protein engineering**: protein engineering, directed evolution, enzyme, computational design, AlphaFold, RosettaFold
- **synthetic biology**: synthetic biology, metabolic engineering, pathway engineering, biomanufacturing
- **protein degradation**: degrader, PROTAC, molecular glue, E3 ligase, ubiquitin, TPD

#### Diagnostics & Tools
- **diagnostics**: diagnostic, IVD, in vitro diagnostic, liquid biopsy, assay, CLIA, biomarker, companion diagnostic
- **genomics**: sequencing, NGS, genomics, single-cell, spatial transcriptomics
- **proteomics**: mass spectrometry, proteomics, protein analysis

#### Services
- **CDMO/CRO**: CDMO, CRO, contract development, contract manufacturing, process development, scale-up
- **biologics/GMP**: biologics, CMC, GMP, downstream processing, upstream processing, bioprocessing

### B. Keyword Extraction Method

**Controlled Vocabulary Matching** (high precision):
```python
labels = {
    "antibody": ["antibody", "bispecific", "adc", "fc"],
    "CRISPR": ["crispr", "cas", "base editor", "prime editor", "guide rna"],
    # ... (full taxonomy above)
}

def tag_keywords(text):
    text_lower = text.lower()
    tags = []
    for label, keywords in labels.items():
        if any(keyword in text_lower for keyword in keywords):
            tags.append(label)
    return ",".join(sorted(set(tags)))
```

**TF-IDF Enhancement** (better recall):
```python
from sklearn.feature_extraction.text import TfidfVectorizer

vec = TfidfVectorizer(max_features=10000, ngram_range=(1,2), stop_words="english")
X = vec.fit_transform(website_texts)
top_terms = vec.get_feature_names_out()

# Inspect per-company top TF-IDF features
# Map high-scoring novel terms back to taxonomy
```

**Data Source**: Scrape company homepage, About page, Technology/Platform page

---

## 6. Reproducible Pipeline (Python Implementation)

### Overview Architecture

```
[Seed Lists] ──┐
               ├──> [Discovery] ──> [Normalization] ──> [Deduplication] ──> [Verification] ──> [Enrichment] ──> [CSV Export]
[Google API] ──┤                                                                                    ↓
[OSM]        ──┘                                                                            [Keyword Tagging]
```

### Step-by-Step Runbook

#### Step 1: Google Places Discovery
```python
import requests, time, pandas as pd

API_KEY = "YOUR_GOOGLE_PLACES_KEY"

# Systematic city coverage
cities = [
    # East Bay (Alameda County)
    "Berkeley, CA", "Emeryville, CA", "Oakland, CA", "Alameda, CA",
    "Albany, CA", "Hayward, CA", "Fremont, CA", "Newark, CA",
    "Union City, CA", "Pleasanton, CA", "Livermore, CA",

    # Peninsula (San Mateo County)
    "South San Francisco, CA", "San Mateo, CA", "Redwood City, CA",
    "Menlo Park, CA", "Foster City, CA", "Burlingame, CA",

    # San Francisco
    "San Francisco, CA",

    # South Bay (Santa Clara County)
    "Palo Alto, CA", "Mountain View, CA", "Sunnyvale, CA",
    "Santa Clara, CA", "San Jose, CA", "Cupertino, CA",

    # Contra Costa County
    "Richmond, CA", "Hercules, CA", "Concord, CA", "Walnut Creek, CA",

    # North Bay
    "San Rafael, CA", "Novato, CA", "Petaluma, CA", "Napa, CA"
]

# Systematic keyword coverage
keywords = [
    # Broad
    "biotechnology company", "biopharma", "biopharmaceutical", "life sciences",

    # Modalities
    "gene therapy", "cell therapy", "CRISPR", "antibody", "biologics",

    # Platforms
    "protein engineering", "synthetic biology", "genomics", "diagnostics",

    # Services
    "CDMO", "CRO", "contract manufacturing", "bioprocessing"
]

def text_search(query, api_key):
    url = "https://places.googleapis.com/v1/places:searchText"
    payload = {"textQuery": query}
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.websiteUri"
    }
    r = requests.post(url, headers=headers, json=payload, timeout=20)
    r.raise_for_status()
    return r.json().get("places", [])

# Discovery loop
all_places = []
for city in cities:
    for keyword in keywords:
        query = f"{keyword} in {city}"
        print(f"Searching: {query}")
        places = text_search(query, API_KEY)
        all_places.extend(places)
        time.sleep(0.5)  # Rate limiting

# Convert to DataFrame
df = pd.DataFrame([{
    "place_id": p.get("id"),
    "company_name": p.get("displayName", {}).get("text"),
    "address": p.get("formattedAddress"),
    "lat": p.get("location", {}).get("latitude"),
    "lon": p.get("location", {}).get("longitude"),
    "website": p.get("websiteUri"),
    "source": "google_places"
} for p in all_places])
```

#### Step 2: Normalize & Dedupe
```python
# (See Section 4.A normalization code above)

# Dedupe by domain first
df = df.sort_values("website").drop_duplicates(subset=["website"], keep="first")

# Fuzzy name dedupe
from rapidfuzz import fuzz

deduped = []
seen_names = []
for _, row in df.iterrows():
    name = normalize_name(row["company_name"] or "")
    if any(fuzz.ratio(name, seen) >= 90 for seen in seen_names):
        continue  # Skip duplicate
    seen_names.append(name)
    deduped.append(row)

df = pd.DataFrame(deduped)
```

#### Step 3: Keyword Enrichment
```python
import requests, bs4

# (Use labels dict from Section 5.A)

def scrape_website(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        # Remove scripts, styles
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        return " ".join(soup.get_text(" ").split())
    except:
        return ""

df["website_text"] = df["website"].fillna("").apply(scrape_website)
df["keywords"] = df["website_text"].apply(tag_keywords)  # Function from 5.B
```

#### Step 4: Export Enhanced CSV
```python
output = df[[
    "company_name", "address", "city", "state", "zip",
    "lat", "lon", "website", "keywords", "source"
]]

output.to_csv("bay_area_biotech_expanded.csv", index=False)
```

---

## 7. Cost & Resource Estimates

### API Costs (Google Places)

**Text Search**: $17 per 1,000 requests
**Place Details**: $17 per 1,000 requests (if needed for additional fields)

**Estimated queries**:
- 30 cities × 10 keywords = 300 Text Search requests
- ~500-1000 unique places found = 500-1000 Place Details requests (if used)

**Total estimated cost**: $5-15 for initial discovery + $8-17 for details = **$13-32 total**

### Time Estimates

**Automated discovery (Steps 1-2)**: 1-2 hours (mostly API calls)
**Website scraping & keyword enrichment (Step 3)**: 3-4 hours (500 websites × 20-30 sec each)
**Manual verification/cleanup (Step 4)**: 4-6 hours
**Total**: ~10-12 hours for 300-500 company dataset

---

## 8. Integration with Current Dataset

### Approach: Merge, Don't Replace

**Current dataset** (`data/working/companies_merged.csv`): 171 companies, manually curated, high quality

**Expanded dataset** (from this methodology): 300-500 companies, programmatically discovered

**Integration strategy**:
1. Run discovery pipeline to generate `bay_area_biotech_expanded.csv`
2. Match against existing 171 companies by domain
3. **For matches**: Enrich existing entries with keywords, verify data
4. **For new companies**: Add to dataset with automated data + manual review flag
5. **Output**: `data/final/companies_v2.csv` with ~300-500 companies

**Column additions**:
- `keywords` (comma-separated technology focus areas)
- `naics` (NAICS codes, comma-separated if multiple)
- `confidence_score` (1-10, based on verification chain)
- `discovery_method` (manual, google_places, opencorporates, etc.)

---

## 9. Ongoing Maintenance Strategy

### Quarterly Update Workflow

**Every 3 months**:
1. Re-run Google Places queries (captures new companies, relocated companies)
2. Validate all URLs (detect closures, acquisitions)
3. Re-scrape websites for keyword changes
4. Manual review of new discoveries (top 50 by confidence score)
5. Update final CSV

**Automation potential**:
- GitHub Actions to run discovery script monthly
- Automated pull request with new companies for manual review
- Automated URL validation (flag broken links)

---

## 10. Limitations & Caveats

### What This Approach Doesn't Capture

**Virtual/Remote companies**: No physical Bay Area presence (Google Places won't find them)
**Stealth startups**: Pre-launch, no website, not in registries
**Academic labs**: Unless they have commercial arms
**Recent moves**: Company relocated but old address still indexed

### Data Quality Trade-offs

**Automated discovery**:
- ✅ Comprehensive coverage
- ✅ Scalable, reproducible
- ❌ Lower precision (false positives)
- ❌ Requires more validation effort

**Manual curation** (current approach):
- ✅ High precision
- ✅ Known to be relevant
- ❌ Limited coverage
- ❌ Labor-intensive to scale

**Hybrid approach** (recommended):
- Use automation for discovery
- Manual verification for final inclusion
- Best of both worlds

---

## 11. Implementation Roadmap

### Phase 3a: Proof of Concept (1 week)
- [ ] Set up Google Places API key
- [ ] Test discovery script on 3-5 cities
- [ ] Scrape 20-30 websites for keyword extraction
- [ ] Validate approach, refine keyword taxonomy
- [ ] Decision point: Proceed or adjust

### Phase 3b: Full Discovery (2 weeks)
- [ ] Run discovery across all Bay Area cities
- [ ] Deduplicate and merge with existing dataset
- [ ] Keyword enrichment for all companies
- [ ] Generate `companies_v2.csv` with ~300-500 entries

### Phase 3c: Verification & Cleanup (1 week)
- [ ] Manual review of new companies (top 100 by confidence)
- [ ] URL validation for all entries
- [ ] Final QA and data quality checks
- [ ] Release v2.0 of dataset

### Phase 4: Automation & Maintenance (ongoing)
- [ ] Set up quarterly update workflow
- [ ] Create GitHub Actions for automated discovery
- [ ] Document maintenance procedures
- [ ] Community contribution process

---

## 12. Resources & References

### APIs & Services
- **Google Places API**: https://developers.google.com/maps/documentation/places
- **OpenCorporates API**: https://api.opencorporates.com/
- **OpenStreetMap Overpass**: https://wiki.openstreetmap.org/wiki/Overpass_API

### Python Libraries
```bash
pip install requests beautifulsoup4 pandas tldextract rapidfuzz scikit-learn
```

### Documentation
- NAICS Codes: https://www.census.gov/naics/
- BioPharmGuy Directory: http://www.biopharmguy.com/
- Wikipedia Biotech: https://en.wikipedia.org/wiki/Biotechnology

---

## Summary: Why This Matters

**Current state**: 171 manually-curated companies (excellent quality, limited scope)

**Future state**: 300-500+ programmatically-discovered companies (comprehensive coverage, validated quality)

**Value proposition**:
- Job seekers see the **complete** Bay Area ecosystem, not just well-known companies
- Discover hidden gems: smaller startups, newer entrants
- Automated updates keep dataset fresh
- Showcases advanced data engineering skills (APIs, NLP, deduplication)

**Next steps**: Wait until Phase 2 (careers URLs) is complete, then decide whether to pursue Phase 3 expansion.

---

**Last Updated**: January 8, 2025
**Status**: Planning document for future implementation
**Estimated Effort**: 4-5 weeks part-time
**Estimated Cost**: $30-50 (API fees)
