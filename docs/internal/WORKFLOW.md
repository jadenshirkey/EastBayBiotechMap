# Data Collection Workflow - SIMPLIFIED (70/10 Approach)

**Purpose**: Enhance the Bay Area Biotech Map with high-value, easy-to-collect data

**Current Phase**: Phase 2 - Enhance Careers Links & Company Stage

**Philosophy**: 70% quality with ~10% effort. Ship it, don't perfect it.

---

## Overview

We have **171 companies** in `data/working/companies_merged.csv`. Our goal is to:

1. **Enhance Hiring column** - Direct careers URLs (for top 100 companies)
2. **Simplify Company Stage** - Use proxy signals, don't over-verify
3. **Run QC checks** - Quick validation before shipping

**Total Estimated Time**: 3.5-4.5 hours for 171 companies

**Why no Tags?** The existing Notes column already contains technology focus keywords (CRISPR, antibody, gene therapy, etc.), making them searchable without duplication.

---

## Task 1: Enhance Hiring Column (2-3 hours)

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

## Task 2: Simplify Company Stage (1 hour)

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

## Task 3: QC Checklist (30 minutes)

Run these quick checks before finalizing:

### Required Fields
- [ ] All companies have: Name, Website, City, Address
- [ ] No duplicate company names (sort by name, scan for dupes)
- [ ] Website URLs start with `http://` or `https://`

### Quality Targets (70% is good!)
- [ ] Top 50 companies have careers links
- [ ] Company Stage is filled (use "Unknown" if unclear)
- [ ] Notes field has technology focus information

### Deduplication (Simple)
- [ ] Same domain = duplicate → keep one, merge data
- [ ] Same address = duplicate → investigate

### Spot Check (Pick 10 random companies)
- [ ] Website loads
- [ ] Notes accurately describe company
- [ ] Address is in correct city

---

## Simplified Execution Plan

### Total Time: 3.5-4.5 hours

**Session 1: Add Careers Links (2-3 hours)**
- Sort CSV by Company Stage (Commercial → Clinical → Pre-clinical)
- Focus on top 100 companies
- Google search ATS platforms + careers pages
- Max 1 min per company
- Save progress every 25 companies

**Session 2: Simplify Company Stage (1 hour)**
- Scan websites for proxy signals
- Update stage classifications
- Mark "Unknown" if unclear and move on

**Session 3: QC Check (30 min)**
- Run through QC checklist
- Spot check 10-20 companies
- Fix obvious errors
- Ship it!

### Working Tips

**Batch work**:
- Work in batches of 25 companies
- Take breaks every hour
- Save CSV after each batch

**Tools**:
- Use Excel or Google Sheets (easier than text editor for CSV)
- Keep browser tabs organized (company website + Google search)
- Use keyboard shortcuts (Ctrl+C, Ctrl+V for URLs)

**When to stop**:
- Hit your time limit (stick to 70/10!)
- Coverage is 70-80% for top companies
- You're getting diminishing returns

---

## Quick Examples

**Example 1: Finding careers link (ATS)**
- Company: Ginkgo Bioworks
- Google: `site:greenhouse.io "Ginkgo"`
- Result: `https://boards.greenhouse.io/ginkgobioworks`
- Time: 30 seconds

**Example 2: Finding careers link (company page)**
- Company: Small startup
- Google: `"[Company Name]" careers`
- Find: `https://company.com/careers`
- Time: 45 seconds

**Example 3: Simplifying stage**
- Website mentions: "Phase 2 clinical trial"
- Classification: Clinical-Stage Biotech
- Time: 20 seconds

**Example 4: Unclear stage**
- Company: Website down or vague
- Stage: Mark as "Unknown"
- Time: 10 seconds (don't waste time!)

---

## Success Metrics (70/10 Goal)

**Target outcomes**:
- Top 100 companies have careers links
- All companies have a stage classification (or "Unknown")
- Notes field already has technology focus (no duplicate work!)
- Total time: 3.5-4.5 hours

**Quality over quantity**:
- ✅ Good enough is perfect
- ✅ Ship it and iterate
- ❌ Don't chase 100% perfection
- ❌ Don't get stuck on edge cases

---

**Last Updated**: January 2025
**Philosophy**: 70% coverage, ~10% effort
**Status**: Ready to execute
