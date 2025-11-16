
# V4.2 Framework — BioPharmGuy‑First Hybrid Enrichment
**Project:** Bay Area Biotech Map  
**Version:** 4.2  
**Date:** 2025-11-15  
**Authors:** BayAreaBiotechMap project maintainers

---

## Executive Summary

V4.2 adopts a **BioPharmGuy‑first** architecture with **conditional AI**:
- **Primary source of truth:** BioPharmGuy (BPG) *California‑wide* directory — `https://biopharmguy.com/links/state-ca-all-geo.php` (extract all rows, then geofence later).
- **Ground‑truth path (≈ majority of rows):** If BPG provides a website, we treat it as canonical for the domain/brand and use **pure Python + Google Places** to fetch a standardized address and perform cross‑validation.
- **Discovery path (≈ minority of rows):** If BPG lacks a website, use **structured outputs** (Claude function‑calling) to search, validate, and return a strictly‑typed enrichment record.
- **Quality strategy:** Prefer **nulls over wrong data**, with multi‑layer validation (geofence, brand↔domain match, business‑type filter, incubator handling), deterministic scoring, and auditable reasoning for any AI‑assisted decisions.
- **Reproducibility:** Staging→promotion file flow, deterministic runs (`temperature=0`), caching, and pre‑commit validators.

**What changed vs. V4.1**
1) BPG moves from “bonus validation” to **primary ground truth** for domains/websites.  
2) **No early Bay Area filter in the extractor**: we scrape **all California** first and apply geofencing later.  
3) Enrichment **branches**:
   - **Path A (Ground‑truth website present):** Python‑first; 1–2 Google Places calls to get a formatted address and confirm the website matches the BPG domain.
   - **Path B (No website):** Structured outputs (Claude + Google Places tools) with schema enforcement and explicit acceptance thresholds.
4) **Costs and risks** decrease because AI is only used for “gap” companies.

---

## Scope & Definitions

### Geographic Scope (canonical, enforced later)
Adopt a unified **9‑county Bay Area** geofence used consistently across all scripts:
- **Counties:** Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, **Solano**, Sonoma.
- **City whitelist:** managed in code via `config/geography.py` and referenced by both merge and enrichment.  
- **Distance backstop:** 60-mile radius from San Francisco (97 km) as an optional secondary guard.

> **Important:** We scrape **all California** and filter to Bay Area during merge/enrichment. This avoids dropping valid companies during extraction and lets us centralize scope logic in one module.

### Final Dataset Schema (production)
```csv
Company Name,Website,City,Address,Company Stage,Focus Areas
```
**Additional tracking fields in working/enriched files (not necessarily shipped to production):**
```
Confidence, Confidence_Det, Validation_Source, Validation_JSON, Place_ID, Last_Verified
```

---

## Data Sources

- **Primary:** BioPharmGuy California directory — `state-ca-all-geo.php`  
  Purpose: authoritative **company→website** mapping; approximate city/region text.
- **Secondary:** Wikipedia (names, occasional city), incubator portfolios, LinkedIn search (names only).  
- **Tertiary:** Google Places API (authoritative **address** + formatting + business context).

> **Terms & Etiquette:** Respect robots.txt/ToS, identify a research UA, rate‑limit requests, cache HTML, and avoid unnecessary re‑fetches.

---

## Pipeline Overview

```
Stage A — Extract (CA-wide)
  BPG CA page ──► bpg_ca_raw.csv (Company Name, Website, City?, Focus Area, Source URL, Notes)

Stage B — Merge & Geofence (deterministic Python)
  bpg_ca_raw.csv + wikipedia_companies.csv + existing companies.csv
    └─ dedupe by eTLD+1 + normalized name
    └─ apply Bay Area geofence (counties + city whitelist + distance backstop)
    └─ domain-reuse report (flag multi-company domains)
  ──► companies_merged.csv (Bay Area only)

Stage C — Enrichment (two-path strategy)
  Path A (Ground-truth website present, preferred)
     └─ Google Places Text Search ► Place Details
     └─ verify details.website eTLD+1 == BPG eTLD+1
     └─ geofence + business-type gates
  Path B (No website)
     └─ Claude structured outputs + Google Places tools
     └─ schema-enforced result + acceptance threshold

  ──► companies_enriched.csv (working; includes Confidence, Place_ID, Validation_JSON)

Stage D — Classification (separate step)
  ──► add Company Stage using methodology decision tree

Stage E — Focus Areas (short factual phrases)

Stage F — QC + Promotion
  └─ validators pass + manual review for flagged rows
  ──► data/final/companies.csv (production)
```

---

## Stage A — Extraction (BioPharmGuy, CA‑wide)

**Key decisions**
- **Scrape the entire California index** and **do not** filter by Bay Area in the extractor.
- Capture **both** the **canonical company name** *and* the **external website URL** (the second link in most BPG rows).
- Capture approximate **location text** if present (sometimes “CA – City/Region”) and a short **focus/description** when available.
- Save: `Company Name`, `Website`, `City` *(optional)*, `Focus Area`, `Source URL`, `Notes` → `data/working/bpg_ca_raw.csv`.

**Robust parsing pattern (page-agnostic):**
```python
# constants
BIOPHARMGUY_URL = "https://biopharmguy.com/links/state-ca-all-geo.php"

# extraction sketch
soup = fetch_html(BIOPHARMGUY_URL)
rows = soup.find_all('tr')

for row in rows:
    company_td = row.find('td', class_='company') or row.find('td', string=lambda s: s and 'http' in s)
    location_td = row.find('td', class_='location')
    desc_td = row.find('td', class_='description') or row.find('td', class_='desc')

    if not company_td: 
        continue

    links = company_td.find_all('a')
    name_a, site_a = None, None
    for a in links:
        href = (a.get('href') or '').strip()
        if href.startswith('http'):
            site_a = a
        elif 'company' in href and href.endswith('.php'):
            name_a = a

    company_name = (name_a.get_text(strip=True) if name_a else (links[0].get_text(strip=True) if links else None))
    company_website = (site_a.get('href').strip() if site_a else '')

    # location (best-effort; refined later during geofence)
    city_guess = parse_city_from_text(location_td.get_text(strip=True) if location_td else '')

    focus = (desc_td.get_text(strip=True) if desc_td else '')

    write_row(company_name, company_website, city_guess, focus, BIOPHARMGUY_URL, "From BPG CA directory")
```

**Notes**
- Add a **persistent on-disk cache** (HTML snapshot) to avoid re-downloading between runs.
- Log extraction counts; compute `% with non‑empty Website` to quantify coverage.

---

## Stage B — Merge & Geofence (deterministic, centralized)

**Inputs**
- `data/working/bpg_ca_raw.csv`
- `data/working/wikipedia_companies.csv`
- `data/final/companies.csv` (existing production; read‑only for merge step)

**Process**
1. **Normalize names** (lowercase + strip suffixes + remove punctuation) for fuzzy equality.  
2. **Extract eTLD+1** from all `Website` values (use `tldextract`), e.g., `https://www.gene.com` → `gene.com`.
3. **Deduplicate** by (`eTLD+1`, normalized name). Favor the record with the **most complete** fields.
4. **Apply geofence** (counties + city whitelist + optional distance backstop). Assign/standardize `City` if possible.
5. **Domain‑reuse report**: flag any **eTLD+1** claimed by >1 company (except allow‑listed multi‑brand cases). Emit a human‑readable report and **block promotion** if unresolved duplicates remain.
6. **Output**: `data/working/companies_merged.csv` (Bay Area only; do **not** write to `final` here).

**Aggregator / parking domains (denylist)**
```
linkedin.com, crunchbase.com, facebook.com, yelp.com,
wixsite.com, squarespace.com, godaddysites.com, about.me, linktr.ee,
sites.google.com
```
If the website domain is on this list, reset `Website = ''` and route to **Path B** in Stage C.

---

## Stage C — Enrichment (two‑path strategy)

### Path A — Ground‑truth website present (preferred, pure Python)

**Goal:** obtain a **formatted street address** and **cross‑validate website** from Google Places.

**Algorithm**
1. Build a biasable search query: `"{brand_token} {City} CA biotech"` where `brand_token` is derived from eTLD+1 (e.g., `gene` from `gene.com`) with an alias table for tricky brands.
2. **Places Text Search** (optionally with `location` + `radius=80km`) → take top 3–5 candidates.
3. For each candidate, call **Place Details** (`fields=['name','formatted_address','website','types','geometry','business_status']`).
4. **Validation gates** (hard):
   - **Geofence**: address must resolve inside the Bay Area.  
   - **Business type**: exclude `real_estate_agency`, `lodging`, `premise`, etc.  
   - **Multi‑tenant**: if address is a known incubator/lab building, require strong brand evidence (name match or details.website match).
5. **Website cross‑check**: accept if `details.website` eTLD+1 == BPG eTLD+1.  
   - If absent but all other gates pass, accept with **lower Confidence_Det** and add `Validation_Reason` (e.g., “website absent in Place Details; accepted by name/geofence/type”).  
6. **Output**: Address (formatted), optional Place_ID, Confidence_Det ∈ [0,1], Validation_Reason; keep `Website` from BPG.

**Deterministic confidence (example)**
```
+0.4 name exact/similar (Levenshtein ≤ 2)
+0.3 website eTLD+1 matches (strict)
+0.2 geofence passed
+0.1 business-type acceptable + operational
>=0.75 accept; else route to manual queue
```

### Path B — No website (structured outputs; Claude + tool use)

**Goal:** jointly discover **website + address** with strict schema and explainability.

**Contract (JSON schema)**  
Return fields: `company_name`, `address|null`, `city|null`, `website|null (uri)`, `confidence (0..1)`, `validation` with booleans (`in_bay_area`, `brand_matches`, `is_business`) and a free‑text `reasoning`.

**Prompt essentials**
- Enforce 9‑county **HARD GATE**.
- Enforce **brand↔domain** relation; reject aggregator domains.
- Enforce **business type**.  
- Prefer **nulls** to wrong data.

**Tool‑use loop (controller sketch)**
```python
resp = client.messages.create(..., tools=[search_places, get_place_details], response_format=ENRICHMENT_SCHEMA)
while has_tool_calls(resp):
    results = []
    for call in tool_calls(resp):
        out = TOOL_REGISTRY[call.name](**call.input)  # call Python wrapper to Google Places
        results.append({"type":"tool_result","tool_use_id":call.id,"content":out})
    resp = client.messages.create(..., messages = messages + [{"role":"assistant","content":resp.content}] + [{"role":"user","content":results}], response_format=ENRICHMENT_SCHEMA, temperature=0, top_p=0)
# final content matches schema; parse and record
```

**Acceptance**
- Accept when `confidence ≥ 0.75` **and** `in_bay_area=True` **and** `is_business=True` and **no** aggregator website.
- Persist `Validation_JSON` for auditability.

---

## Stage D — Classification (separate concern)

Apply your methodology’s eight categories using a **separate pass** (avoid mixing classification with address/website enrichment). Record classifier provenance and date. Leave “Unknown” if ambiguous; avoid hallucinating.  

---

## Stage E — Focus Areas

Extract 1–3 factual sentences from the website’s “About/Technology” pages; de‑marketing; ≤200 characters ideal; include key platform keywords.

---

## Stage F — Quality Control & Promotion

**Automated validators (must pass before promotion):**
- Valid HTTPS URLs or blank; aggregator domains rejected.
- City in whitelist; address in Bay Area (geofence check).
- **Zero duplicate eTLD+1** outside allow‑list.
- If `Address` present → `Place_ID` present (for Path A/B).

**Manual checks (sampled and flagged):**
- Tier 1/2 spot‑checks (10 random) confirm address on the company website.
- All Tier 4 entries manually reviewed or removed.

**Promotion flow**
- Write working outputs to `data/working/companies_enriched.csv`.  
- Only after all validators pass + manual spot‑checks, **promote** to `data/final/companies.csv`.

---

## Confidence Tiers (V4.2)

- **Tier 1 — Ground Truth Confirmed**: BPG website present **AND** Google Places confirms same eTLD+1 (and passes all gates). `Confidence ≥ 0.95`.
- **Tier 2 — Ground Truth Only**: BPG website present; Google mismatch/missing but passes other gates. `Confidence ~ 0.90–0.95`.
- **Tier 3 — AI Validated**: No BPG website; structured outputs found and validated a plausible match. `Confidence ~ 0.75–0.90`.
- **Tier 4 — Flagged**: Low confidence or conflicts; manual review required.

---

## Costs & Performance

- **Google Places**: Text Search + Details ≈ **$0.049 per company** in the **worst case** (1 Text Search + 1 Details). Use caching and accept‑on‑first‑valid candidate to minimize calls.  
- **Structured outputs (Claude)**: invoked only for the “no‑website” minority. Configure `temperature=0`. Track token usage empirically; store logs to estimate ongoing cost.

**Optimization levers**
- Query shaping (brand token + city) reduces extraneous candidates.
- Cache Place Details by `place_id` during the run.
- Skip Details if Text Search already includes a website and geofence passes (verify in your client library).

---

## Migration Plan (from current repo)

1) **Extractor**
   - Switch source to `state-ca-all-geo.php`.  
   - **Do not** filter to Bay Area in the extractor.  
   - Save `Website` (external link), not just `Source URL`.  
   - Add disk cache and UA; write to `data/working/bpg_ca_raw.csv`.

2) **Merge**
   - Import `config/geography.py` for counties/cities.  
   - Deduplicate by **eTLD+1 + normalized name**.  
   - Emit **domain‑reuse report**; block promotion on unresolved duplicates.  
   - Output `data/working/companies_merged.csv` (Bay Area only).

3) **Enrichment**
   - Implement **Path A** first (pure Python).  
   - Implement **Path B** with a proper **tool‑use loop** + strict JSON schema.  
   - Persist `Confidence`, `Confidence_Det`, `Place_ID`, `Validation_JSON`, `Validation_Source`.

4) **Classification & Focus Areas**
   - Separate script(s); leave “Unknown” where ambiguous.

5) **QC & Promotion**
   - Add a pre‑commit validator (URL format, geofence, duplicates, aggregator denylist).  
   - Promote only after validators pass + spot‑checks.

---

## Red‑Team Test Set (before full run)

Build a 30‑company set:
- Clear wins: Genentech (SSF), Gilead (Foster City), BioMarin (San Rafael), etc.
- Incubator tenants (require brand evidence)
- Alias brands / unusual domains
- City edge cases (e.g., “South SF” vs “South San Francisco”)
- Known aggregator‑only web presence
- Out‑of‑scope distractors (Davis/Sacramento)

Success: ≥90% Tier 1–3; 0 obvious errors; 0 duplicate eTLD+1.

---

## Appendices

### A. Minimal `config/geography.py`
```python
BAY_COUNTIES = [
  "Alameda","Contra Costa","Marin","Napa","San Francisco","San Mateo","Santa Clara","Solano","Sonoma"
]

CITY_WHITELIST = [
  # Alameda
  "Alameda","Albany","Berkeley","Dublin","Emeryville","Fremont","Hayward",
  "Livermore","Newark","Oakland","Pleasanton","San Leandro","Union City",
  # Contra Costa
  "Antioch","Concord","Richmond","San Ramon","Walnut Creek","Danville","Martinez","Pleasant Hill",
  # Marin
  "Novato","San Rafael","Mill Valley","Larkspur","Corte Madera","Tiburon","Sausalito",
  # San Francisco
  "San Francisco",
  # San Mateo
  "Belmont","Brisbane","Burlingame","Daly City","Foster City","Half Moon Bay","Menlo Park",
  "Redwood City","San Bruno","San Carlos","San Mateo","South San Francisco","Millbrae",
  # Santa Clara
  "Campbell","Cupertino","Los Altos","Los Gatos","Milpitas","Mountain View","Palo Alto",
  "San Jose","Santa Clara","Saratoga","Sunnyvale","Morgan Hill",
  # Solano
  "Benicia","Fairfield","Vallejo",
  # Sonoma
  "Petaluma","Santa Rosa"
]
SF_LATLNG = (37.7749, -122.4194)
BAY_RADIUS_M = 97000  # 60 miles
```

### B. Deterministic helpers
```python
import tldextract, re

def etld1(url: str) -> str:
    if not url: return ""
    ext = tldextract.extract(url)
    return ".".join([ext.domain, ext.suffix]) if ext.domain and ext.suffix else ""

def brand_token_from_etld1(domain: str) -> str:
    # gene.com -> gene ; biorad.com -> biorad ; dna20.com -> dna20
    return re.sub(r"[^a-z0-9]", "", domain.split(".")[0].lower()) if domain else ""

AGGREGATOR_ETLD1 = {
  "linkedin.com","crunchbase.com","facebook.com","yelp.com",
  "wixsite.com","squarespace.com","godaddysites.com","about.me","linktr.ee","google.com"
}

def is_aggregator(url: str) -> bool:
    return etld1(url) in AGGREGATOR_ETLD1
```

### C. Structured outputs (schema + prompt skeleton)
```json
{
  "name": "company_enrichment_result",
  "strict": true,
  "schema": {
    "type": "object",
    "properties": {
      "company_name": {"type": "string"},
      "address": {"type": ["string","null"]},
      "city": {"type": ["string","null"]},
      "website": {"type": ["string","null"], "format": "uri"},
      "confidence": {"type": "number", "minimum": 0, "maximum": 1},
      "validation": {
        "type": "object",
        "properties": {
          "in_bay_area": {"type": "boolean"},
          "brand_matches": {"type": "boolean"},
          "is_business": {"type": "boolean"},
          "reasoning": {"type": "string"}
        },
        "required": ["in_bay_area","brand_matches","is_business","reasoning"]
      }
    },
    "required": ["company_name","confidence","validation"],
    "additionalProperties": false
  }
}
```

Prompt essentials:
```
- HARD GATE: 9-county Bay Area only; reject Davis/Sacramento/out-of-state.
- Brand-domain check; denylist aggregator domains.
- Business-type filter; require strong brand at incubators.
- Prefer nulls over wrong data; acceptance threshold ≥0.75.
- Return JSON strictly matching the schema.
```

### D. Known incubator / multi-tenant examples (extend in code)
```
201 Gateway Blvd, South San Francisco, CA 94080, USA
149 Commonwealth Dr, Menlo Park, CA 94025, USA
544B Bryant St, San Francisco, CA 94107, USA
```

### E. Promotion policy
```
- Only promote from data/working/... to data/final/companies.csv when:
  • validators pass,
  • domain-reuse conflicts resolved,
  • spot-checks completed (Tier 1/2),
  • flagged items dispositioned.
```

---

## Checklist (V4.2 readiness)

- [ ] Extractor switched to **state-ca-all-geo.php** and **saves Website** for every row with an external link.
- [ ] Merge dedupes by **eTLD+1 + normalized name**; emits **domain‑reuse** report.
- [ ] Geofence logic centralized; city whitelist consistent across scripts.
- [ ] Enrichment Path A implemented; crosses `details.website` vs BPG eTLD+1.
- [ ] Enrichment Path B implemented with a **tool‑use loop** and strict schema.
- [ ] Pre‑commit validator checks URLs, geofence, duplicates, aggregators.
- [ ] Staging→promotion flow enforced; no script writes to `final` mid‑run.
- [ ] README & Methodology updated to match scope and field names.
