# Data Collection Workflow - SIMPLIFIED (70/10 Approach)

**Purpose**: Enhance the Bay Area Biotech Map with high-value, easy-to-collect data

**Current Phase**: Phase 2 - Add Tags & Enhance Careers Links

**Philosophy**: 70% quality with ~10% effort. Ship it, don't perfect it.

---

## Overview

We have **171 companies** in `data/working/companies_merged.csv`. Our goal is to add:

1. **Tags** - Controlled keywords for filtering (NEW - highest value!)
2. **Hiring links** - Direct careers URLs (for top 100 companies)
3. **Simplified Company Stage** - Use proxy signals, don't verify

**Total Estimated Time**: 5-7 hours for 171 companies

---

## Task 1: Add Tags Column (2-3 hours) ⭐ HIGHEST VALUE

**Why**: Makes map filterable, helps job seekers find relevant companies fast.

### Quick Process (30 seconds per company)

For each company:
1. Open company website (already in CSV)
2. Scan homepage + existing Notes column
3. Pick 1-3 tags from controlled vocabulary (see DATA_DICTIONARY.md)
4. Add to new "Tags" column (comma-separated)
5. **If unclear after 30 seconds: leave blank and move on**

### Examples

| Company | Notes | Tags |
|---------|-------|------|
| Ginkgo Bioworks | Synthetic biology platform | `synthetic-biology, platform` |
| 4D Molecular Therapeutics | AAV gene therapy; capsid engineering | `gene-therapy, protein-engineering` |
| ATUM | Gene & protein design/synthesis | `CDMO, protein-engineering` |
| Acrigen | Precision CRISPR gene editing | `CRISPR, platform` |
| 89bio | Engineered FGF21 analog for liver disease | `protein-engineering, rare-disease` |

### Controlled Vocabulary (see DATA_DICTIONARY.md for full list)

**Common tags**: `antibody`, `CRISPR`, `gene-therapy`, `cell-therapy`, `RNA`, `protein-engineering`, `CDMO`, `CRO`, `diagnostics`, `platform`, `oncology`, `synthetic-biology`, `AI-ML`

### Pro Tips
- ✅ Tag what you see on homepage, not deep research
- ✅ Use Notes column to speed it up (already has good info)
- ✅ 80% coverage is plenty - don't tag everything
- ❌ Don't spend >30 sec per company
- ❌ Don't overthink it

---

## Task 2: Enhance Hiring Column (2-3 hours)

**Focus on top 100 companies** (Commercial-Stage, Clinical-Stage, Large Pharma first)

### Fast Search Process (1 minute per company max)

For each company in priority order (Commercial → Clinical → Pre-clinical):

**Step 1: Try common ATS platforms** (30 seconds)
- Google: `site:greenhouse.io "[Company Name]"`
- Google: `site:lever.co "[Company Name]"`
- If found: Copy URL, move to next company

**Step 2: Search careers page** (30 seconds)
- Google: `"[Company Name]" careers`
- Look for: `/careers`, `/jobs`, `/join-us` on company domain
- If found: Copy URL, move to next company

**Step 3: Give up** (immediately)
- If nothing clear in 1 minute: Leave as "Check Website"
- **Don't waste time** - move to next company

### Common ATS Patterns

- Greenhouse: `https://boards.greenhouse.io/[company-slug]`
- Lever: `https://jobs.lever.co/[company-name]`
- Workday: `https://[company].wd1.myworkdayjobs.com/Careers`
- SmartRecruiters: `https://jobs.smartrecruiters.com/[CompanyName]`

### What to SKIP

❌ Don't validate URLs (do later if needed)
❌ Don't check if jobs are posted
❌ Don't research acquired companies deeply
❌ Don't spend >1 min per company

---

## Task 3: Simplify Company Stage (1 hour)

**Use proxy signals - don't verify everything**

### Quick Classification Rules

Scan company website for these keywords:

| If website mentions... | Classification |
|------------------------|----------------|
| "FDA-approved" or "marketed product" | Commercial-Stage Biotech |
| "Phase 1/2/3" or "clinical trial" | Clinical-Stage Biotech |
| "Platform" or "technology" (but no products) | Pre-clinical/Startup |
| "Contract" or "CDMO" or "services" | Tools/Services/CDMO |
| "Acquired by..." | Acquired |
| Unclear or website down | Unknown |

### Don't Waste Time On

❌ Verifying FDA approvals
❌ Checking ClinicalTrials.gov
❌ Researching company history
❌ Reading press releases

**Just mark it and move on.** You can refine later if needed.

---

## Task 4: QC Checklist (30 minutes)

Run these quick checks before finalizing:

### Required Fields
- [ ] All companies have: Name, Website, City, Address
- [ ] No duplicate company names (sort by name, scan for dupes)
- [ ] Website URLs start with `http://` or `https://`

### Quality Targets (70% is good!)
- [ ] 80%+ companies have at least 1 tag
- [ ] Top 50 companies have careers links
- [ ] Company Stage is filled (use "Unknown" if unclear)

### Deduplication (Simple)
- [ ] Same domain = duplicate → keep one, merge tags
- [ ] Same address = duplicate → investigate

### Spot Check (Pick 10 random companies)
- [ ] Website loads
- [ ] Tags make sense
- [ ] Address is in correct city

---

## Simplified Execution Plan

### Total Time: 5-7 hours

**Session 1: Add Tags (2-3 hours)**
- Open CSV in Excel/Sheets
- Add "Tags" column
- Work through companies, adding 1-3 tags each
- Save every 25 companies
- Target: 80%+ coverage

**Session 2: Add Careers Links (2-3 hours)**
- Sort by Company Stage (Commercial → Clinical → Pre-clinical)
- Focus on top 100 companies
- Google search ATS + careers pages
- Max 1 min per company
- Save progress frequently

**Session 3: Simplify Company Stage (1 hour)**
- Scan websites for proxy signals
- Update stage classifications
- Mark "Unknown" if unclear

**Session 4: QC Check (30 min)**
- Run through QC checklist
- Spot check 10-20 companies
- Fix obvious errors
- Done!

### Working Tips

**Batch work**:
- Do tags in batches of 25 companies
- Take breaks every hour
- Save CSV after each batch

**Tools**:
- Use Excel or Google Sheets (easier than text editor)
- Keep browser tabs organized (website + Google search)
- Use keyboard shortcuts (Ctrl+C, Ctrl+V, Ctrl+F)

**When to stop**:
- Hit your time limit (stick to 70/10!)
- Coverage is 70-80%
- You're getting diminishing returns

---

## Quick Examples

**Example 1: Tagging a CRISPR company**
- Company: Acrigen Biosciences
- Website scan: "Precision CRISPR Gene Editing"
- Tags: `CRISPR, platform`
- Time: 20 seconds

**Example 2: Finding careers link**
- Company: Ginkgo Bioworks
- Google: `site:greenhouse.io "Ginkgo"`
- Result: `https://boards.greenhouse.io/ginkgobioworks`
- Time: 30 seconds

**Example 3: Unclear stage**
- Company: Website down or unclear
- Stage: Mark as "Unknown"
- Time: 10 seconds (don't waste time!)

---

## Success Metrics (70/10 Goal)

**Target outcomes**:
- 70-80% companies have tags
- Top 100 companies have careers links
- All companies have a stage classification
- Total time: 5-7 hours

**Quality over quantity**:
- ✅ Good enough is perfect
- ✅ Ship it and iterate
- ❌ Don't chase 100% perfection
- ❌ Don't get stuck on edge cases

---

**Last Updated**: January 2025
**Philosophy**: 70% coverage, ~10% effort
**Status**: Ready to execute
