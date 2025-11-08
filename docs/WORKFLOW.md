# Data Collection Workflow

**Purpose**: Step-by-step procedures for enhancing the Bay Area Biotech Map dataset

**Current Phase**: Phase 2 - Enhance Careers Links

---

## Overview

We have **171 companies** in `data/working/companies_merged.csv`. The "Hiring" column currently contains placeholder text like "Check Website" or blank entries. Our goal is to replace these with **direct URLs to careers pages**.

**Target**: Fill the "Hiring" column with working URLs for all 171 companies

---

## Why Careers URLs Matter

For job seekers using this map:
- ✅ **One-click access** to job postings (no hunting through company websites)
- ✅ **Direct link** to application pages (saves time)
- ✅ **Standardized** across all companies (consistent user experience)

---

## Careers URL Search Strategy

### Priority Order

For each company, search in this order until you find a careers page:

1. **Applicant Tracking Systems (ATS)** - Most companies use these platforms
2. **Company-hosted careers page** - Custom /careers or /jobs page on company site
3. **Company website** - Fallback to main website if nothing else found

---

## Method 1: Automated Search with Python + WebSearch

### Prerequisites
- Python 3.6+
- Access to WebSearch tool (or web scraping capabilities)
- `data/working/companies_merged.csv`

### Script: `scripts/fetch_careers_urls.py`

**Location**: `/scripts/fetch_careers_urls.py` (to be created)

**What it does**:
1. Reads `companies_merged.csv`
2. For each company:
   - Searches ATS platforms (Greenhouse, Lever, Workday, SmartRecruiters)
   - Searches for company careers page
   - Extracts direct URL from search results
   - Updates "Hiring" column
3. Saves progress incrementally (every 25 companies)
4. Outputs final CSV with careers URLs

**Usage**:
```bash
cd scripts
python3 fetch_careers_urls.py
```

**Output**: `data/working/companies_with_careers.csv`

### Detailed Search Procedure (Per Company)

#### Step 1: Search Greenhouse.io
**Query**: `site:greenhouse.io "[Company Name]"`

**Look for**:
- URL pattern: `https://boards.greenhouse.io/[company-slug]`
- Example: `https://boards.greenhouse.io/ginkgobioworks`

**Extract**:
- If found: Copy the full URL
- If not found: Proceed to Step 2

#### Step 2: Search Lever.co
**Query**: `site:lever.co "[Company Name]"`

**Look for**:
- URL pattern: `https://jobs.lever.co/[company-name]`
- Example: `https://jobs.lever.co/cariboubio`

**Extract**:
- If found: Copy the full URL
- If not found: Proceed to Step 3

#### Step 3: Search Workday
**Query**: `site:myworkdayjobs.com "[Company Name]"`

**Look for**:
- URL pattern: `https://[company].wd1.myworkdayjobs.com/[careers-page]`
- Example: `https://genentech.wd1.myworkdayjobs.com/Careers`

**Extract**:
- If found: Copy the full URL
- If not found: Proceed to Step 4

#### Step 4: Search SmartRecruiters
**Query**: `site:smartrecruiters.com "[Company Name]"`

**Look for**:
- URL pattern: `https://jobs.smartrecruiters.com/[CompanyName]`
- Example: `https://jobs.smartrecruiters.com/Ginkgo`

**Extract**:
- If found: Copy the full URL
- If not found: Proceed to Step 5

#### Step 5: Search Company Careers Page
**Query**: `"[Company Name]" careers jobs apply`

**Look for**:
- Company's main careers page (usually on their domain)
- Common patterns:
  - `https://[company].com/careers`
  - `https://[company].com/jobs`
  - `https://[company].com/join-us`
  - `https://[company].com/about/careers`

**Extract**:
- If found: Copy the URL that leads to job listings
- Verify it's not just a "about us" page with no actual jobs
- If not found or unclear: Proceed to Step 6

#### Step 6: Fallback to Company Website
**Action**: Use the company's main website from the "Website" column

**Mark as**: Keep "Check Website" (indicates manual check needed)

---

## Method 2: Manual Research (If Automated Fails)

For companies where automated search doesn't find clear results:

### Manual Search Procedure

1. **Google Search**: `[Company Name] careers`
2. **Check Company Website**: Navigate to [Website column] and look for:
   - Footer links (often "Careers" or "Jobs")
   - Header navigation menu
   - "About Us" → "Careers" submenu
3. **Check LinkedIn**: Company LinkedIn page often has "Jobs" tab
4. **Last resort**: Email company or mark as "No careers page found"

### Recording Manual Results

When recording manually found URLs:
```csv
Company Name,Hiring
Ginkgo Bioworks,https://www.ginkgobioworks.com/careers/
Caribou Biosciences,https://jobs.lever.co/cariboubio
Acme Biotech,Check Website
```

---

## URL Validation & Quality Control

After collecting URLs, validate them:

### Validation Checklist

For each URL in the "Hiring" column:

- [ ] **URL is accessible** (doesn't return 404 error)
- [ ] **URL is direct** (goes to jobs page, not generic "About" page)
- [ ] **URL shows job listings** (or says "No current openings" - both OK)
- [ ] **URL is properly formatted** (starts with `https://`)

### Validation Script: `scripts/validate_urls.py`

**What it does**:
1. Reads CSV with careers URLs
2. Tests each URL (HTTP GET request)
3. Reports:
   - ✅ Working URLs (200 OK)
   - ⚠️ Redirects (3xx status)
   - ❌ Broken URLs (404, 5xx)
4. Outputs validation report

**Usage**:
```bash
cd scripts
python3 validate_urls.py
```

**Output**: `data/working/url_validation_report.txt`

---

## Data Quality Standards

### What Counts as a Valid Careers URL

✅ **GOOD**:
- Direct ATS links (Greenhouse, Lever, Workday, SmartRecruiters)
- Company /careers page showing job listings
- Company /jobs page with application links
- Page that says "No current openings" (proves it's the careers page)

❌ **NOT GOOD**:
- Generic company homepage
- "About Us" page mentioning careers but no jobs
- Broken/404 links
- PDF job descriptions (prefer online application pages)

### Special Cases

**Acquired Companies**:
- If company was acquired, link to parent company careers page
- Note in Comments: "Acquired by [Parent Company]"

**Defunct Companies**:
- Leave "Hiring" blank
- Update "Company Stage" to "Defunct" or "Closed"

**No Careers Page**:
- Leave as "Check Website"
- Consider removing from final map (not hiring = not useful for job seekers)

---

## Workflow Timeline & Effort Estimate

### Option A: Fully Automated
**Time**: 2-3 hours
**Pros**: Minimal manual work, reproducible
**Cons**: May miss some URLs, requires script development
**Best for**: Quick first pass, then manual cleanup

### Option B: Fully Manual
**Time**: 8-10 hours (171 companies × ~3 min each)
**Pros**: Most accurate, catch edge cases
**Cons**: Time-consuming, not easily reproducible
**Best for**: Small datasets or high-accuracy requirements

### Option C: Hybrid (Recommended)
**Phase 1**: Automated search for ATS platforms (30 min)
**Phase 2**: Manual research for missing entries (3-4 hours)
**Phase 3**: Validation and cleanup (1 hour)
**Total**: 4-5 hours

---

## Step-by-Step Execution Plan

### Week 1: Automated Collection

**Day 1: Setup**
- [ ] Review `data/working/companies_merged.csv`
- [ ] Create `scripts/fetch_careers_urls.py` script
- [ ] Test on 5-10 companies first

**Day 2: Run Automated Collection**
- [ ] Run script on all 171 companies
- [ ] Save progress to `data/working/companies_with_careers.csv`
- [ ] Generate report: how many found vs. not found

**Day 3: Review Results**
- [ ] Check automated results for accuracy
- [ ] Identify companies needing manual research
- [ ] Prioritize companies (larger/well-known companies first)

### Week 2: Manual Cleanup

**Day 4-5: Manual Research**
- [ ] Research companies where automated search found nothing
- [ ] Focus on top 50 companies first
- [ ] Update CSV with manually found URLs

**Day 6: Validation**
- [ ] Run URL validation script
- [ ] Fix broken links
- [ ] Test sample of URLs manually

**Day 7: Finalization**
- [ ] Copy to `data/final/companies.csv`
- [ ] Update DATA_DICTIONARY.md
- [ ] Commit and tag as v1.0

---

## Example Company Workflows

### Example 1: Ginkgo Bioworks (Large Company, Uses Greenhouse)

**Automated Search**:
1. Query: `site:greenhouse.io "Ginkgo Bioworks"`
2. Result: `https://boards.greenhouse.io/ginkgobioworks`
3. Validation: Visit URL → Shows job listings ✅
4. Update CSV: `Ginkgo Bioworks,https://boards.greenhouse.io/ginkgobioworks`

**Time**: <1 minute (automated)

---

### Example 2: Small Startup (Custom Careers Page)

**Automated Search**:
1. Query: `site:greenhouse.io "Acme Biotech"` → No results
2. Query: `site:lever.co "Acme Biotech"` → No results
3. Query: `"Acme Biotech" careers` → Find `https://acmebiotech.com/join-our-team`
4. Validation: Visit URL → Shows 3 job listings ✅
5. Update CSV: `Acme Biotech,https://acmebiotech.com/join-our-team`

**Time**: 2-3 minutes (semi-automated)

---

### Example 3: Acquired Company

**Manual Research**:
1. Google: "Acme Biotech careers" → News article says "Acquired by BigPharma in 2023"
2. Visit: `https://www.bigpharma.com/careers`
3. Update CSV: `Acme Biotech,https://www.bigpharma.com/careers`
4. Add note in "Notes" column: "Acquired by BigPharma (2023)"

**Time**: 5 minutes (manual)

---

## Tools & Resources

### Required Tools
- Python 3 with csv module (built-in)
- WebSearch capability or internet access for manual searches
- Text editor or Excel for CSV editing

### Helpful Resources
- **Greenhouse**: https://boards.greenhouse.io/
- **Lever**: https://jobs.lever.co/
- **Workday**: https://[company].wd1.myworkdayjobs.com/
- **SmartRecruiters**: https://jobs.smartrecruiters.com/

### ATS Platform Detection Tips

**How to identify if a company uses an ATS**:
1. Google: "[Company Name] careers"
2. Click the careers link
3. Look at the URL:
   - Contains "greenhouse.io" → Greenhouse
   - Contains "lever.co" → Lever
   - Contains "myworkdayjobs.com" → Workday
   - Contains "smartrecruiters.com" → SmartRecruiters
   - Company's own domain → Custom page

---

## Troubleshooting

### Problem: Company has multiple careers pages
**Solution**: Choose the most general/comprehensive one
- Prefer: All jobs page
- Avoid: Specific department pages (e.g., /engineering-jobs)

### Problem: Careers page requires login
**Solution**: Check if there's a public job board
- Some companies have both public and employee-only portals
- Link to the public-facing one

### Problem: URL redirects to a different page
**Solution**: Use the final destination URL
- Follow the redirect chain
- Record the final URL where jobs are displayed

### Problem: Company is hiring but no careers page found
**Solution**:
- Check LinkedIn Jobs tab
- Check Indeed or ZipRecruiter (may post there)
- Worst case: Leave as "Check Website"

---

## Progress Tracking

Use this checklist to track progress:

### Phase 2 Progress Tracker

**Automated Collection**:
- [ ] Script created and tested
- [ ] Run on all 171 companies
- [ ] Results saved to CSV
- [ ] Report generated (X% found, Y% manual needed)

**Manual Research**:
- [ ] Top 50 companies researched
- [ ] All remaining companies researched
- [ ] Edge cases handled (acquired, defunct, etc.)

**Validation**:
- [ ] URL validation script created
- [ ] All URLs tested for accessibility
- [ ] Broken links fixed
- [ ] Final QA check completed

**Finalization**:
- [ ] Final CSV saved to `data/final/companies.csv`
- [ ] Documentation updated
- [ ] Changes committed to git
- [ ] Version tagged (v1.0)

---

## Success Metrics

**Target**: 80%+ of companies have direct careers links

**Quality metrics**:
- ✅ URL is accessible (not 404)
- ✅ URL shows actual jobs or "no openings" message
- ✅ URL is direct (no need for additional navigation)

**Expected results**:
- ~120-140 companies: Direct ATS or careers page URL
- ~20-30 companies: "Check Website" (no clear careers page)
- ~10-20 companies: Acquired/defunct (special handling)

---

**Last Updated**: January 8, 2025
**Phase**: 2 (Careers URL Enhancement)
**Status**: Ready to execute
