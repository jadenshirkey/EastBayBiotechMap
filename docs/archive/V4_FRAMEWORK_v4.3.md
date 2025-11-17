
# V4.3 Framework — BioPharmGuy‑First Hybrid (Implementation‑Ready)

**Project:** Bay Area Biotech Map  
**Version:** 4.3  
**Date:** 2025-11-15  
**Status:** Canonical framework (architecture + implementation guide)  
**Scope:** Replaces V4.2 by incorporating Claude’s review into an implementation‑ready plan

---

## Executive Summary

V4.3 keeps the **BioPharmGuy‑first** architecture and makes it implementation‑ready:

- **Primary ground truth:** BioPharmGuy (BPG) **California‑wide** directory — `https://biopharmguy.com/links/state-ca-all-geo.php`. Extract **all** CA rows including external **Website** links; geofence later during merge/enrichment.  
- **Two‑path enrichment:**  
  - **Path A (Ground‑truth website present, preferred):** Pure Python + Google Places to obtain a formatted address and cross‑validate the website/domain, with strict geofencing and business‑type gates. Current `enrich_with_google_maps.py` takes “first result wins”; V4.3 replaces this with gated, cross‑validated logic. 【61†source】  
  - **Path B (No website):** Anthropic **Structured Outputs** + tool use to jointly discover website/address under a strict JSON Schema; explicit acceptance thresholds. V4.1 pioneered this; V4.3 keeps it but limits to the minority of rows. 【66†source】  
- **Deduplication & safety:** eTLD+1 + normalized‑name dedupe; **domain‑reuse** report blocks promotion until resolved. Current merge script already treats BPG Website as missing and filters early by city; V4.3 fixes both. 【63†source】【64†source】  
- **Unified geofence:** One 9‑county definition + city whitelist module, consistent with your methodology (60‑mile backstop optional). 【60†source】  
- **Costs:** Use **Google Maps setup** pricing as baseline (Text Search + Details ≈ **$0.049/company**) with $200 monthly credit; earlier $/company claims in V4.0 were inconsistent. Measure Anthropic cost empirically. 【62†source】【66†source】

---

## What Changed from V4.2 (at a glance)

- **BPG extractor:** switch source to **state‑ca‑all‑geo**; capture external `Website`; drop early Bay Area filter (geofence later). 【64†source】  
- **Path A details:** precise **website cross‑check** logic, **multi‑tenant threshold**, **deterministic confidence** scoring, and **Places API fields** spelled out (legacy Python client semantics). 【61†source】  
- **Path B details:** complete **prompt template**, **tool definitions**, and a **controller loop** using Anthropic’s **structured outputs** + tools with `max_tokens` and `temperature=0`. (Keep `response_format` with JSON schema; it’s how structured outputs are configured.)
- **Error handling:** retries, exponential backoff, rate limiting, fallbacks, cache policy.  
- **Testing plan:** unit, integration, validation tests beyond red‑team set.  
- **Cost analysis:** reconcile with Maps pricing doc; provide scenario table. 【62†source】  
- **Success metrics & timeline:** explicit tier targets, QC gates, and hour estimates.  
- **Methodology & README updates:** file‑specific edits for consistency (fields, counts). 【58†source】【60†source】

---

## Scope & Definitions (unchanged intent, unified implementation)

- **Geofence (canonical):** 9‑county Bay Area (Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma) + **city whitelist** module; optional **60‑mile** radius backstop from SF. Aligns with methodology text and fixes prior inconsistencies between scripts and docs. 【60†source】  
- **Production schema:** `Company Name, Website, City, Address, Company Stage, Focus Areas`. (Keep **Focus Areas**, not “Notes”.) README currently uses both; consolidate. 【58†source】  
- **Working fields (not necessarily shipped):** `Confidence, Confidence_Det, Validation_Source, Validation_JSON, Place_ID, Last_Verified`.

---

## Pipeline Overview (A→F)

```
A. Extract (CA‑wide)  → data/working/bpg_ca_raw.csv
B. Merge & Geofence   → data/working/companies_merged.csv (Bay Area only)
C. Enrichment         → data/working/companies_enriched.csv (Path A / Path B)
D. Classification     → separate pass using methodology tree
E. Focus Areas        → short factual phrases
F. QC & Promotion     → data/final/companies.csv (after validators & spot‑checks)
```

**Why:** Current extractor filters early by Bay Area and current merge sets `Website` blank for BPG; both limit the value of BPG’s websites. V4.3 corrects the order of operations and preserves canonical websites. 【64†source】【63†source】

---

## A. Extraction — BioPharmGuy (CA‑wide)

**Source:** `https://biopharmguy.com/links/state-ca-all-geo.php` (scrape **all** CA companies; don’t geofence yet).  
**Capture:** `Company Name`, **`Website` (external link)**, optional `City` guess, `Focus Area`/description (if present), `Source URL`, `Notes`.  
**Why:** The Northern California page omitted many Bay Area rows; the CA‑wide page plus later geofencing maximizes coverage without contamination. Current extractor targets “Northern California by name” and drops the external website field entirely; V4.3 fixes that. 【64†source】

**Implementation notes**  
- Persist page HTML (disk cache) and respectful UA; throttle requests.  
- Robust link capture: choose the **external** website href if present; fall back gracefully.  
- No city filtering here; city is refined by Stage B and C.  
- Output: `data/working/bpg_ca_raw.csv`.

---

## B. Merge & Geofence — deterministic, centralized

**Inputs:** BPG CA raw, Wikipedia extractions (names), existing production `companies.csv`. Wikipedia is minimal (names, occasional cities). 【65†source】  
**Process:**  
1) Normalize company names (lowercase, strip suffixes, remove punctuation).  
2) Extract **eTLD+1** from each `Website` (use `tldextract`); dedupe by (`eTLD+1`, normalized name) and prefer most complete rows.  
3) Apply **geofence** (counties + city whitelist; optional 60‑mile backstop). One shared module to avoid drift across scripts. 【60†source】  
4) **Domain‑reuse report:** flag any eTLD+1 claimed by >1 company (allowlist rare cases like `gene.com`). Block promotion until resolved.  
5) **Aggregator/parking denylist:** `linkedin.com, crunchbase.com, facebook.com, yelp.com, wixsite.com, squarespace.com, godaddysites.com, about.me, linktr.ee, sites.google.com`. If matched, set `Website=''` and route to Path B.  
6) Output: `data/working/companies_merged.csv` (Bay Area only, still staging).

**Why now:** Current merge script sets `Website=''` for BPG and filters by Bay Area cities inline, which discards useful ground truth and spreads geofence logic across files; centralizing fixes this. 【63†source】

---

## C. Enrichment — two‑path strategy

### Path A (preferred): ground‑truth website present → **pure Python**

**Goal:** obtain a formatted **Address** and cross‑validate the website/domain via Google Places **without** AI.  
**Current state:** `enrich_with_google_maps.py` does a Places query and accepts the first result; V4.3 replaces this with gated validation. 【61†source】

**Algorithm (legacy Google Maps Python client semantics):**  
1) Build a biasable query: `"{brand_token} {City} CA biotech"`; derive `brand_token` from the eTLD+1 (e.g., `gene` from `gene.com`) with a small alias table for tricky brands.  
2) **Text Search** → collect top 3–5 candidates.  
3) For each candidate, call **Place Details** with fields: `['name','formatted_address','website','types','geometry','business_status']`.  
4) Apply **hard gates**:  
   - **Geofence** must pass.  
   - **Business type** must exclude `real_estate_agency`, `lodging`, `premise`‑only, etc.  
   - **Multi‑tenant**: if the address is a known incubator/lab building, require stronger evidence (see below).
5) **Website cross‑check logic (explicit):**
```
details_etld1 = etld1(details.website) if details.website else ""
bpg_etld1     = etld1(bpg_website)

score = 0.0
if name_similarity(details.name, company_name) >= 0.8:        score += 0.4
if details_etld1 and details_etld1 == bpg_etld1:              score += 0.3   # strong match
elif not details_etld1:                                       score += 0.1   # absent, not contradictory
else:                                                         score -= 0.2   # contradiction

if geofence_ok(details.formatted_address):                    score += 0.2
if business_type_ok(details.types) and is_operational(details.business_status): score += 0.1

accept = (score >= 0.75)
```
6) **Multi‑tenant threshold:** When `is_multi_tenant(address)` is true, **require** `name_similarity≥0.9 OR (details_etld1 == bpg_etld1)`; otherwise **don’t accept**.  
7) If accepted, keep `Website` from BPG (canonical), add `Address`, `Place_ID`, `Confidence_Det=score`, and a short `Validation_Reason` string.  
8) If none accepted, leave fields null and route to manual queue (or Path B, if you wish).

**Why:** Prevents wrong addresses/websites while fully leveraging BPG ground truth.

### Path B: no website → **Anthropic Structured Outputs + tools**

**Goal:** jointly discover `website + address` with a strict JSON Schema and auditable reasoning; **accept only if high confidence**. Built on the V4.1 concept, but limited to the rows that need it. 【66†source】

**JSON Schema (unchanged in spirit):**
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
        "required": ["in_bay_area","brand_matches","is_business","reasoning"],
        "additionalProperties": false
      }
    },
    "required": ["company_name","confidence","validation"],
    "additionalProperties": false
  }
}
```

**Complete prompt template (multi‑paragraph):**  
```
System / Validation Rules
You are enriching data for the Bay Area Biotech Map, a curated directory of biotechnology companies.
Follow these rules strictly. Prefer leaving fields null over guessing.

Geographic Scope (HARD GATE)
- Only accept addresses in the 9-county San Francisco Bay Area: Alameda, Contra Costa, Marin,
  Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma.
- Reject Davis, Sacramento, or anything outside California.
- If unsure, return nulls and lower confidence.

Brand-Domain Validation
- The website domain brand must plausibly relate to the company name.
- Reject aggregator/parking domains: linkedin.com, crunchbase.com, facebook.com, yelp.com,
  wixsite.com, squarespace.com, godaddysites.com, about.me, linktr.ee, sites.google.com.

Business-Type Validation
- Must be an actual business location, not only a building, real-estate listing, or lodging.
- Reject types: real_estate_agency, lodging, premise-only.

Multi-Tenant Handling
- If the address is a known incubator/lab building, accept only with strong brand evidence:
  exact/same-name OR website eTLD+1 match.

Acceptance Thresholds
- confidence ≥ 0.75 and all hard gates passed → accept.
- else return nulls and a clear explanation in `validation.reasoning`.

Task
Given the company: "{company_name}" and expected city hint: "{city}", find a valid website and Bay Area address.

Procedure
1) Use `search_places` with a query like "{company_name} {city} CA biotech".
2) For up to 5 candidates, call `get_place_details` to retrieve name, address, website, types, status.
3) Validate using the rules above.
4) Score confidence on [0,1].
5) Return a single JSON object that conforms exactly to the schema.
```

**Tool definitions (Python wrappers around googlemaps client):**  
```python
SEARCH_PLACES_TOOL = {
  "name": "search_places",
  "description": "Search Google Places for candidates.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "location_bias": {"type": "object", "properties": {"lat":{"type":"number"}, "lng":{"type":"number"}}}
    },
    "required": ["query"]
  }
}

GET_PLACE_DETAILS_TOOL = {
  "name": "get_place_details",
  "description": "Get Place Details by place_id (name, formatted_address, website, types, business_status, geometry).",
  "input_schema": {
    "type": "object",
    "properties": {"place_id": {"type": "string"}},
    "required": ["place_id"]
  }
}
```

**Controller loop (messages API with structured outputs + tools):**  
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

tools = [SEARCH_PLACES_TOOL, GET_PLACE_DETAILS_TOOL]

def run_structured_enrichment(company_name, city):
    system = VALIDATION_PROMPT_TEXT  # full multi-paragraph template above
    user_msg = f'Enrich this company: "{company_name}" (hint city: "{city}")'

    messages = [{"role": "user", "content": user_msg}]

    for _ in range(8):
        resp = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            temperature=0,
            max_tokens=1200,
            system=system,
            tools=tools,
            messages=messages,
            response_format={
              "type": "json_schema",
              "json_schema": COMPANY_ENRICHMENT_SCHEMA  # dict as shown above
            }
        )

        # If the assistant wants to call tools, execute them and append tool_result blocks
        tool_uses = [b for b in resp.content if getattr(b, "type", "") == "tool_use"]
        if tool_uses:
            tool_results = []
            for call in tool_uses:
                if call.name == "search_places":
                    out = search_places_tool(**call.input)           # your Python wrapper
                elif call.name == "get_place_details":
                    out = get_place_details_tool(**call.input)       # your Python wrapper
                else:
                    out = {"error": f"unknown tool {call.name}"}
                tool_results.append({"type": "tool_result", "tool_use_id": call.id, "content": out})

            messages = messages + [{"role": "assistant", "content": resp.content}] + [{"role": "user", "content": tool_results}]
            continue

        # No tool calls; expect a final JSON object conforming to the schema.
        # Depending on SDK version, the JSON may arrive as a dedicated JSON block or as text.
        # Parse the first JSON-looking block safely:
        for block in resp.content:
            if hasattr(block, "text"):
                try:
                    return json.loads(block.text)
                except Exception:
                    pass
            if getattr(block, "type", None) in ("output_json", "json"):
                return block  # already a parsed dict in some SDKs

        raise RuntimeError("No structured JSON found")

    raise RuntimeError("Exceeded max tool loop steps")
```

> **Notes:**  
> • `max_tokens` is required; `temperature=0` for determinism.  
> • `response_format` with `type: "json_schema"` is the Anthropic‑supported way to require schema‑conforming output for structured outputs.  
> • If your SDK returns the final object inside a JSON‑typed block instead of `.text`, handle both cases as shown.  
> • Keep the tool wrappers thin; they should call `googlemaps.Client(...).places()` and `.place(fields=[...])` in line with your current script. 【61†source】

---

## D. Classification (separate pass)

Use your methodology’s eight categories and verifiable rules; avoid mixing with enrichment. If ambiguous, leave “Unknown” rather than guessing. 【60†source】

---

## E. Focus Areas (short, factual)

Extract 1–3 plain sentences (≤200 chars ideally) from homepage/About/Technology pages; avoid marketing fluff; include platform keywords.

---

## F. QC & Promotion (gates you must pass)

**Automated validators:**  
- URLs valid HTTPS or blank; **denylist** aggregators reset to blank.  
- City ∈ whitelist; Address geofences to 9 counties (and radius backstop if enabled).  
- **Zero duplicate eTLD+1** outside allow‑list.  
- If `Address` present → `Place_ID` present.  
- Flag if Path A contradiction (`details.website` eTLD+1 ≠ BPG eTLD+1).

**Manual checks:**  
- Spot‑check 10 random Tier‑1/2 entries (address matches website).  
- Review all Tier‑4 (flagged) cases.

**Promotion policy:**  
- Only promote from `data/working/companies_enriched.csv` to `data/final/companies.csv` after validators **and** spot‑checks pass. Current scripts write directly to `final`; stop doing that. 【61†source】

---

## Costs (reconciled) & Scenarios

**Authoritative baseline for Google Places:** Text Search $0.032 + Details $0.017 ≈ **$0.049/company** (see your setup guide). $200/month free credit typically covers the run. 【62†source】

Because Path A often accepts the first valid candidate and caches details, you will usually make fewer calls than the worst‑case pair. Provide two scenario ranges and **measure actuals** in logs:

| Scenario | Path A size | Calls / co. | Google cost | Path B size | Calls / co. | Google cost | Anthropic cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Conservative** | 900 | 1 Text + 1 Details | 900×0.049 ≈ **$44.1** | 300 | 1 Text + 1 Details | 300×0.049 ≈ **$14.7** | **I don’t know** — instrument and compute |
| **Optimized** | 900 | 1 Text + 0.5 Details | 900×0.040 ≈ **$36.0** | 300 | 1 Text + 0.5 Details | 300×0.040 ≈ **$12.0** | **I don’t know** — instrument and compute |

> **Anthropic cost:** your V4.0 file estimated totals, but it conflicts with the Maps pricing doc. Without reliable per‑token pricing + prompt sizes, **I don’t know** the exact cost. Log token usage per call and multiply by your current rate plan to compute true cost; store this report alongside `enrichment_report.txt`. 【66†source】【62†source】

---

## Success Metrics (targets)

- **Tier distribution after QC:** ≥ **70–80% Tier‑1**, ≥ **10–20% Tier‑2**, ≤ **10% Tier‑3**, **0% Tier‑4** after manual review.  
- **Zero Davis/Sacramento companies**; all addresses geofence‑validated. 【60†source】  
- **0 duplicate eTLD+1** except allow‑list.  
- **No aggregator websites** shipped.  
- **Reproducibility:** rerun variance ≤ 5% on Path B outcomes (with same seeds and caches).

---

## Timeline (estimates)

- **Phase A: Extract CA‑wide BPG** — 2 h  
- **Phase B: Merge & geofence** — 3 h  
- **Phase C‑A: Path A enrichment** — 4 h (batched)  
- **Phase C‑B: Path B implementation & run** — 6 h (incl. tool loop controller)  
- **Phase D–E: Classify + Focus Areas** — 3 h  
- **Phase F: QC & Promotion** — 2 h  
- **Total (one pass):** ~ **20 h**

---

## File‑by‑File Change List (actionable)

1) **`scripts/extract_biopharmguy_companies.py`**  
   - **Source:** change to `state-ca-all-geo.php` (CA‑wide).  
   - **Do not** filter to Bay Area here.  
   - **Write `Website` column** (external URL) in output CSV; keep `Source URL`.  
   - Add disk cache + UA + retry with backoff; throttle.  
   - **Output:** `data/working/bpg_ca_raw.csv`.  
   _Rationale:_ Current extractor uses Northern California page and omits Website, and filters by Bay Area at extraction. 【64†source】

2) **`scripts/merge_company_sources.py`**  
   - Import shared geofence module.  
   - Dedupe by (`eTLD+1`, normalized name).  
   - Emit **domain‑reuse** report (block promotion until resolved).  
   - Apply **denylist**; if matched, reset Website to blank to force Path B.  
   - **Output:** `data/working/companies_merged.csv` (do not write to `final`).  
   _Rationale:_ Current merge sets `Website:''` for BPG and filters by city inline. 【63†source】

3) **`scripts/enrich_with_google_maps.py`**  
   - **Replace “first result wins”** with Path‑A gating & scoring; add `Place_ID`, `Confidence_Det`, `Validation_Reason`. 【61†source】  
   - Add **Path B** entry point that calls the Anthropic controller loop when `Website==''`.  
   - Persist a JSONL of Path‑B `validation.reasoning`.  
   - **Output:** `data/working/companies_enriched.csv`; never write to `final` in this script.

4) **`METHODOLOGY.md`**  
   - Add a **Validation Strategy** section: geofence hard gate, brand/domain check, business type, multi‑tenant threshold; Path‑A/P‑B split; acceptance ≥0.75; prefer nulls to wrong data. 【60†source】  
   - Add **Confidence Tiers** and **QC checklist** consistent with this doc.

5) **`README.md`**  
   - Reconcile counts/coverage claims and field names (use **Focus Areas**; ensure the 1,210/100% address claims and dates are accurate). 【58†source】  
   - Add a short **Data Quality** section describing tiers and gates.

---

## Error Handling & Fallbacks

- **HTTP / API errors:** retry 3× with exponential backoff (e.g., 0.5s, 1s, 2s).  
- **429 / quota:** back off to 60s; resume where left off (checkpoint every N rows).  
- **Network timeouts:** retry; if repeated, skip and log to manual queue.  
- **Tool loop safety:** cap to 8 tool‑rounds; on exceed, flag low confidence.  
- **Cache policy:** store BPG HTML snapshots; store Google Place Details keyed by `place_id`. Invalidate if older than 30 days.  
- **Fallbacks:** (a) keep nulls; (b) send to manual queue; (c) Path B attempt for stubborn Path A misses.

---

## Testing Strategy

- **Unit tests:**  
  - `etld1()`, `brand_token_from_etld1()`, `is_aggregator()`, `name_similarity()`, geofence checks.  
  - Multi‑tenant helper: `is_multi_tenant()`, `validate_multi_tenant_match()`.
- **Integration tests:**  
  - Path A on known companies (Genentech, BioMarin, Gilead) should accept with high `Confidence_Det`.  
  - Path A against incubator addresses should **reject** without strong brand evidence.  
  - Path B on “no‑website” rows returns schema‑conforming JSON and respects hard gates.  
- **Validation tests:**  
  - Denylist enforcement; duplicate eTLD+1 blocking; Davis/Sacramento rejection. 【60†source】  
- **Red‑team set (30 companies):** cover alias brands, incubators, aggregator‑only, geofence edges.

---

## Helper Snippets

**Multi‑tenant:**  
```python
INCUBATOR_ADDRESSES = {
  "201 Gateway Blvd, South San Francisco, CA 94080, USA",
  "149 Commonwealth Dr, Menlo Park, CA 94025, USA",
  "544B Bryant St, San Francisco, CA 94107, USA",
}

def is_multi_tenant(address: str) -> bool:
    return any(addr.lower() in (address or "").lower() for addr in INCUBATOR_ADDRESSES)

def validate_multi_tenant_match(company_name, details_name, details_website, bpg_website) -> bool:
    nm = normalize_name(company_name) == normalize_name(details_name)
    wm = etld1(details_website) == etld1(bpg_website) if details_website and bpg_website else False
    return nm or wm
```

**Name similarity (simple):**  
```python
def name_similarity(a, b):
    # Jaro-Winkler or Levenshtein; placeholder 0..1
    import textdistance as td
    return td.jaro_winkler.normalized_similarity((a or "").lower(), (b or "").lower())
```

---

## Changelog

- **V4.3 (this file):** Adds complete prompt, tool loop, Path‑A thresholds, error handling, tests, reconciled costs, metrics, timeline, and file‑by‑file diffs.  
- **V4.2:** Introduced BPG‑first architecture and two‑path strategy (kept here), but lacked several implementation sections now provided.  
- **V4.0:** Structured outputs for 100% of companies; cost figures conflicted with Maps pricing doc (superseded by this plan). 【66†source】【62†source】

---

## Citations to current repo (evidence)

- Current **enrichment** script uses “first result wins”: `gmaps.places(...)` then first candidate → details (no gates). 【61†source】  
- **Merge** reads BPG CSV but sets Website `''` and filters for Bay Area early. 【63†source】  
- **BPG extractor** targets Northern California page and **does not** write Website; filters to Bay Area at extraction. 【64†source】  
- **Wikipedia extractor** provides names with minimal metadata. 【65†source】  
- **Methodology** defines Bay Area scope; use as canonical and centralize. 【60†source】  
- **README** contains inconsistent counts/coverage and field naming (e.g., “Notes” vs “Focus Areas”); update alongside this framework. 【58†source】  
- **Google Maps pricing** and free‑tier credit are documented in your setup guide (use these, not older estimates). 【62†source】
