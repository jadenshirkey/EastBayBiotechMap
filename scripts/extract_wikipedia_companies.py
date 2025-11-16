#!/usr/bin/env python3
"""
Extract biotech/pharma company names from Wikipedia sources.

This script implements Phase 1 of the East Bay Biotech Map methodology:
automated extraction from Wikipedia's biotechnology and pharmaceutical company lists.

Usage:
    python3 extract_wikipedia_companies.py

Output:
    data/working/wikipedia_companies.csv

Author: Jaden Shirkey
Date: January 2025
"""

import requests
from bs4 import BeautifulSoup
import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

# Path constants (script-relative paths)
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
DATA_WORKING = REPO_ROOT / 'data' / 'working'
DATA_FINAL = REPO_ROOT / 'data' / 'final'

# Add parent directory to path for imports
sys.path.insert(0, str(REPO_ROOT))
from utils.helpers import is_aggregator

# Wikipedia sources per methodology
WIKIPEDIA_SOURCES = [
    {
        'name': 'Biotech Companies List',
        'url': 'https://en.wikipedia.org/wiki/List_of_biotechnology_companies',
        'type': 'table'
    },
    {
        'name': 'Pharma Companies Category',
        'url': 'https://en.wikipedia.org/wiki/Category:Pharmaceutical_companies_of_the_United_States',
        'type': 'category'
    },
    {
        'name': 'Bay Area Companies Category',
        'url': 'https://en.wikipedia.org/wiki/Category:Companies_based_in_the_San_Francisco_Bay_Area',
        'type': 'category'
    }
]

# Bay Area cities whitelist (from METHODOLOGY.md Appendix A)
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
    'Petaluma', 'Santa Rosa',
    # Napa County
    'Napa'
}


def fetch_wikipedia_page(url):
    """Fetch Wikipedia page content."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; EastBayBiotechMap/1.0; Educational Research)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_from_table(soup, source_name='Wikipedia table'):
    """Extract companies from Wikipedia table format."""
    companies = []
    tables = soup.find_all('table', class_='wikitable')

    for table in tables:
        rows = table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue

            # First cell usually contains company name
            first_cell = cells[0]
            link = first_cell.find('a')
            if link and link.get('href'):
                company_name = link.get_text(strip=True)
                wiki_url = 'https://en.wikipedia.org' + link['href']

                # Try to extract city/location from row
                city = ''
                for cell in cells:
                    text = cell.get_text(strip=True)
                    for bay_city in BAY_AREA_CITIES:
                        if bay_city in text:
                            city = bay_city
                            break
                    if city:
                        break

                companies.append({
                    'company_name': company_name,
                    'website': '',  # Will be extracted later with API call
                    'source_url': wiki_url,
                    'city': city,
                    'notes': f'From {source_name}'
                })

    return companies


def extract_from_category(soup, source_name='Wikipedia category'):
    """Extract companies from Wikipedia category page."""
    companies = []

    # Category pages have two sections: Subcategories and Pages
    # We want only the "Pages" section (id="mw-pages")
    pages_section = soup.find('div', id='mw-pages')

    if pages_section:
        # Find the mw-category div within mw-pages
        category_div = pages_section.find('div', class_='mw-category')

        if category_div:
            links = category_div.find_all('a')
            for link in links:
                href = link.get('href', '')

                # Skip if not a wiki page or if it's a category page
                if not href.startswith('/wiki/'):
                    continue
                if '/wiki/Category:' in href:
                    continue

                company_name = link.get_text(strip=True)
                wiki_url = 'https://en.wikipedia.org' + href

                companies.append({
                    'company_name': company_name,
                    'website': '',  # Will be extracted later with API call
                    'source_url': wiki_url,
                    'city': '',  # Categories don't usually include location
                    'notes': f'From {source_name}'
                })

    return companies


def is_bay_area_company(company_name, city):
    """Check if company appears to be Bay Area based."""
    # If we found a Bay Area city in the data, it's valid
    if city and city in BAY_AREA_CITIES:
        return True

    # Check if company name mentions Bay Area location
    name_lower = company_name.lower()
    for city_name in BAY_AREA_CITIES:
        if city_name.lower() in name_lower:
            return True

    # Default to including it (manual filtering later)
    return True


def deduplicate_companies(companies):
    """Remove duplicate companies by name."""
    seen = {}
    deduplicated = []

    for company in companies:
        name = company['company_name'].strip()
        if name not in seen:
            seen[name] = True
            deduplicated.append(company)

    return deduplicated


def extract_core_company_name(company_name):
    """
    Extract the core company name by removing common suffixes.
    This helps match company names to their domains.
    """
    import re

    # Common suffixes to remove (order matters - longer first)
    suffixes = [
        'Pharmaceuticals', 'Pharmaceutical', 'Pharma',
        'Therapeutics', 'Therapeutic',
        'Laboratories', 'Laboratory', 'Labs', 'Lab',
        'International', 'Intl',
        'Technologies', 'Technology', 'Tech',
        'Biopharmaceuticals', 'Biopharmaceutical', 'Biopharma',
        'Biotechnology', 'Biotech', 'Bio',
        'Manufacturing', 'Mfg',
        'Corporation', 'Corp',
        'Incorporated', 'Inc',
        'Company', 'Co',
        'Limited', 'Ltd',
        'Medicines', 'Medicine', 'Med',
        'Sciences', 'Science',
        'Holdings', 'Holding',
        'Group', 'Grp',
        'Systems', 'System',
        'Solutions', 'Solution',
        'Industries', 'Industry',
        'Enterprises', 'Enterprise',
        'Associates', 'Associate', 'Assoc',
        'Partners', 'Partner',
        'Ventures', 'Venture'
    ]

    # Remove parenthetical content first
    core_name = re.sub(r'\([^)]*\)', '', company_name).strip()

    # Remove suffixes (case-insensitive)
    for suffix in suffixes:
        # Match suffix at word boundary with optional punctuation
        pattern = r'\b' + re.escape(suffix) + r'\.?\b'
        core_name = re.sub(pattern, '', core_name, flags=re.IGNORECASE).strip()

    # Remove any trailing punctuation and extra spaces
    core_name = re.sub(r'[,.\-]+$', '', core_name).strip()
    core_name = ' '.join(core_name.split())

    return core_name.lower()


def score_url_for_company(url, core_name):
    """
    Score how likely a URL is to be the official website for a company.
    Higher score = more likely to be the official site.
    """
    import re
    from urllib.parse import urlparse

    # Parse the URL
    parsed = urlparse(url.lower())
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.rstrip('/')

    # Immediately reject document files
    if any(ext in path.lower() for ext in ['.pdf', '.doc', '.xls', '.ppt', '.txt']):
        return -1000

    score = 0

    # Extract just the main domain part (before .com, .org, etc.)
    domain_parts = domain.split('.')
    if len(domain_parts) >= 2:
        # Get the part right before the TLD (e.g., "fibrogen" from "fibrogen.com")
        # but "gcs-web" from "fibrogen.gcs-web.com" (subdomain)
        if len(domain_parts) >= 3:
            # Has subdomain - check both subdomain and main domain
            subdomain = domain_parts[0]
            main_domain = domain_parts[-2]  # e.g., "gcs-web" from "fibrogen.gcs-web.com"
        else:
            subdomain = ''
            main_domain = domain_parts[0]  # e.g., "fibrogen" from "fibrogen.com"
    else:
        subdomain = ''
        main_domain = domain

    # Remove spaces and special chars from core name for matching
    core_name_clean = re.sub(r'[^a-z0-9]', '', core_name)

    # HIGHEST PRIORITY: Exact match of core name as the main domain
    if core_name_clean and main_domain == core_name_clean:
        score += 200  # Highest score for exact domain match
    # Good: Core name in subdomain (like fibrogen.gcs-web.com)
    elif subdomain and core_name_clean and core_name_clean == subdomain:
        score += 100  # Still good but not as good as main domain
    # OK: Core name appears somewhere in domain
    elif core_name_clean and core_name_clean in domain:
        score += 50

    # Check if individual words from core name appear in domain
    if core_name and score < 50:  # Only if we haven't found a good match
        core_words = core_name.split()
        for word in core_words:
            if len(word) > 3 and word in domain:  # Skip very short words
                score += 20

    # Prefer root domains over deep links
    if path == '' or path in ['/home', '/index.html', '/index.php']:
        score += 20
    elif path in ['/about', '/about-us', '/company']:
        score += 10

    # Prefer .com domains
    if domain.endswith('.com'):
        score += 5

    # Heavy penalties for news and investor relations sites
    news_patterns = [
        'news', 'media', 'press', 'journal', 'times', 'post',
        'reuters', 'bloomberg', 'forbes', 'fortune', 'wsj',
        'cnn', 'bbc', 'npr', 'ap', 'upi',
        'fierce', 'stat', 'endpoints', 'biospace',
        'businesswire', 'prnewswire', 'marketwatch',
        'seekingalpha', 'fool', 'investor', 'ir.',
        'gcs-web', 'q4cdn', 'edgar', 'sec.gov',
        'citeline', 'evaluate', 'genengnews', 'sdbj'
    ]

    for pattern in news_patterns:
        if pattern in domain:
            score -= 100  # Heavy penalty for news/IR sites

    # Penalize overly long URLs (likely news articles, deep links)
    url_length = len(url)
    if core_name:
        core_length = len(core_name)
        if core_length > 0:
            length_ratio = url_length / core_length

            # Ideal ratio is 2-6x company name length
            if length_ratio > 15:  # e.g., 80+ chars for 5-char name
                score -= 50  # Heavy penalty for very long URLs
            elif length_ratio > 10:  # e.g., 50+ chars for 5-char name
                score -= 30  # Moderate penalty
            elif length_ratio > 8:
                score -= 15  # Light penalty
            elif 2 <= length_ratio <= 6:
                score += 10  # Bonus for ideal length range

    # Penalize deep paths (likely not homepage)
    path_segments = [p for p in path.split('/') if p]  # Non-empty segments
    if len(path_segments) >= 4:  # e.g., /page/content/detail/id/
        score -= 40
    elif len(path_segments) >= 3:
        score -= 20
    elif len(path_segments) >= 2:
        score -= 10

    # Penalize URLs with many query parameters (often news, databases)
    if '?' in url:
        query_params = parsed.query
        param_count = len(query_params.split('&')) if query_params else 0

        if param_count >= 5:  # Many params (e.g., SEC filings)
            score -= 50
        elif param_count >= 3:
            score -= 30
        elif param_count >= 1:
            score -= 10

    # Penalize excessive punctuation (%, &, =, etc.)
    # Good sites: www.gene.com (mostly alphanumeric)
    # Bad sites: many %, &, = (query strings)
    special_chars = len(re.findall(r'[%&=?#]', url))
    if special_chars >= 10:
        score -= 30
    elif special_chars >= 5:
        score -= 15

    return score


def extract_official_website_from_html(page_title):
    """
    Extract the official website by parsing the External Links section HTML.
    This is more reliable than scoring all external links.

    Returns the official website URL or empty string if not found.
    """
    try:
        # Extract page name from full Wikipedia URL if needed
        if 'wikipedia.org/wiki/' in page_title:
            page_title = page_title.split('/wiki/')[-1]

        # Wikipedia API endpoint
        api_url = "https://en.wikipedia.org/w/api.php"
        headers = {
            'User-Agent': 'EastBayBiotechMap/1.0 (Educational Research; https://github.com/jadenshirkey/EastBayBiotechMap)'
        }

        # First, get section numbers to find "External links" section
        sections_params = {
            'action': 'parse',
            'page': unquote(page_title),
            'prop': 'sections',
            'format': 'json',
            'formatversion': 2
        }

        sections_response = requests.get(api_url, params=sections_params, headers=headers, timeout=10)
        sections_data = sections_response.json()

        if 'error' in sections_data or 'parse' not in sections_data:
            return ''

        # Find the section index for "External links"
        external_links_section = None
        for section in sections_data.get('parse', {}).get('sections', []):
            section_title = section.get('line', '').lower()
            if 'external link' in section_title:  # Matches "External links" or "External link"
                external_links_section = section['index']
                break

        if not external_links_section:
            return ''  # No external links section found

        # Get the HTML for just that section
        text_params = {
            'action': 'parse',
            'page': unquote(page_title),
            'prop': 'text',
            'section': external_links_section,
            'format': 'json',
            'formatversion': 2
        }

        text_response = requests.get(api_url, params=text_params, headers=headers, timeout=10)
        text_data = text_response.json()

        if 'error' in text_data or 'parse' not in text_data:
            return ''

        html = text_data.get('parse', {}).get('text', '')
        if not html:
            return ''

        # Parse HTML with BeautifulSoup to find "Official website"
        soup = BeautifulSoup(html, 'html.parser')

        # Strategy 1: Look for links with text containing "official website"
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True).lower()
            if 'official' in link_text and 'website' in link_text:
                href = link.get('href', '')
                # Ensure it's a full URL
                if href.startswith('http'):
                    return href

        # Strategy 2: Look for span with class "official-website"
        official_span = soup.find('span', class_='official-website')
        if official_span:
            link = official_span.find('a', href=True)
            if link:
                href = link.get('href', '')
                if href.startswith('http'):
                    return href

        # Strategy 3: First external link in a list item (often the official site)
        ul_element = soup.find('ul')
        if ul_element:
            first_li = ul_element.find('li')
            if first_li:
                link = first_li.find('a', href=True)
                if link:
                    # Check if it's likely an official site (not aggregator, not news)
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True).lower()
                    if href.startswith('http') and not is_aggregator(href):
                        # If text suggests it's official, return it
                        if any(word in link_text for word in ['official', 'company', 'homepage', 'corporate']):
                            return href

        return ''  # No official website found

    except Exception:
        # Silently handle errors
        return ''


def extract_website_from_wikipedia_api(page_title):
    """
    Extract official website from Wikipedia page.
    First tries to find "Official website" link from HTML,
    then falls back to scoring all external links.

    Returns the most likely official website URL, or empty string if not found.
    """
    try:
        # PRIORITY 1: Try to extract "Official website" from HTML
        official_website = extract_official_website_from_html(page_title)
        if official_website:
            return official_website

        # FALLBACK: Use original scoring method
        # Extract page name from full Wikipedia URL if needed
        if 'wikipedia.org/wiki/' in page_title:
            page_title = page_title.split('/wiki/')[-1]

        # Extract core company name from page title
        # Remove underscores and decode URL encoding
        company_name = unquote(page_title).replace('_', ' ')
        core_name = extract_core_company_name(company_name)

        # Wikipedia API endpoint
        api_url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'parse',
            'page': unquote(page_title),  # Decode URL-encoded titles
            'prop': 'externallinks',
            'format': 'json',
            'formatversion': 2
        }

        # Include User-Agent header (required by Wikipedia API)
        headers = {
            'User-Agent': 'EastBayBiotechMap/1.0 (Educational Research; https://github.com/jadenshirkey/EastBayBiotechMap)'
        }

        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'error' in data:
            return ''

        if 'parse' not in data:
            return ''

        external_links = data['parse'].get('externallinks', [])

        # Additional patterns to exclude (beyond what is_aggregator handles)
        exclude_patterns = [
            'archive.org', 'web.archive.org',  # Archive sites (handled separately in fallback)
            'doi.org', 'pubmed', 'ncbi.nlm',  # Scientific references
            'sec.gov', 'edgar',  # SEC filings
            'reuters.com', 'bloomberg.com', 'forbes.com', 'fortune.com',  # News sites
            'nytimes.com', 'wsj.com', 'washingtonpost.com',
            'semanticscholar.org', 'scholar.google',  # Academic
            'github.com', 'gitlab.com',  # Code repositories (usually not company sites)
            '.pdf', '.doc', '.xls',  # Direct file downloads
            'geohack.toolforge.org',  # Geographic coordinates tool
            '/media/', '/news/', '/press/',  # Skip deep links to news sections
            'marketwatch.com', 'yahoo.com',  # Financial news
            'biotickr.com',  # Generic biotech ticker site
            'businesswire.com', 'prnewswire.com',  # Press release sites
            'drugs.com', 'drugbank.ca',  # Drug databases
            'bizjournals.com', 'fiercebiotech.com',  # Industry news
            'pharmaintelligence.informa.com',  # Industry database
            'google.com/search', 'jstor.org',  # Search engines
            # Additional generalizable exclusions
            'answers.com',  # Q&A sites
            'biospace.com/article',  # Biotech news articles
            'genengnews.com',  # Genetic engineering news
            '.edu/',  # University sites (columbia.edu, etc.)
            'isin.toolforge.org',  # Stock identifier tools
            'indexes.', 'index.',  # Index/ranking sites (indexes.nasdaqomx.com)
            '/article/', '/releases/',  # Article/press release URLs
            '/news-posts/', '/news/',  # News paths
            'awards.com', 'rankings.',  # Award/ranking sites
            'oxfordjournals.org',  # Academic journals
            'startribune.com', 'chicagotribune.com',  # Local news
            'pharmaceutical-technology.com',  # Industry news sites
            'abcnews.go.com', 'newsweek.com',  # Major news outlets
            'connvoters.com',  # Voter registration (edge case)
            'springeducationgroup.com',  # Unrelated companies
            'auspostalhistory.com',  # Historical archives
            'translateals.com',  # Research sites (not company)
            'therapeuticsaccelerator.org',  # Non-profit initiatives
            'sandp500changes',  # Stock tracking sites
            'cmoleadershipawards',  # Award sites
            'geekwire.com',  # Tech news
            # New exclusions from data analysis
            'heraldstaronline.com', 'localtechwire.com',  # Found in data
            'specialtypharmacycontinuum.com', 'accessrx.com',  # Found in data
            'secfilings.', 'nasdaq.com/edgar',  # SEC filing variants
            '/story/', '/blog/',  # Generic article paths
            'FilingID=', 'FormType=', 'CoName=',  # Query params for filings
            'bostonglobe.com', 'latimes.com', 'sfgate.com',  # More news
            'statnews.com', 'endpts.com',  # Biotech news
            'wikinvest.com', 'seekingalpha.com',  # Financial sites
            '/filingFrameset.asp', '/content.detail/',  # Filing/CMS paths
            'pharmaceutical-journal.com', 'pharmatimes.com'  # More pharma news
        ]

        # Collect and score all potentially valid websites
        scored_websites = []
        for link in external_links:
            url = link if isinstance(link, str) else link.get('url', '')

            # Skip if empty
            if not url:
                continue

            # Skip aggregators using our helper
            if is_aggregator(url):
                continue

            # Skip excluded patterns
            if any(pattern in url.lower() for pattern in exclude_patterns):
                continue

            # Score this URL based on company name matching
            score = score_url_for_company(url, core_name)
            scored_websites.append((score, url))

        # Sort by score (highest first)
        scored_websites.sort(key=lambda x: x[0], reverse=True)

        # Return the highest scoring URL if it has a reasonable score
        # Even a score of 0 might be OK if it's the only option
        if scored_websites:
            best_score, best_url = scored_websites[0]
            # Accept if score is positive OR if it's the only non-negative option
            if best_score > -50:  # Allow slightly negative scores but not terrible ones
                return best_url

        # Fallback: Check for archived company websites (defunct companies)
        # Extract original URL from archive.org links
        import re
        for link in external_links:
            if 'archive.org/web/' in link:
                # Extract original URL from archive link
                # Format: https://web.archive.org/web/[timestamp]/[original_url]
                match = re.search(r'archive\.org/web/\d+/(.+)', link)
                if match:
                    original_url = match.group(1)
                    # Ensure it has http:// or https://
                    if not original_url.startswith(('http://', 'https://')):
                        original_url = 'http://' + original_url
                    # Ensure it's not another aggregator or excluded site
                    if not is_aggregator(original_url):
                        if not any(pattern in original_url.lower() for pattern in exclude_patterns):
                            # Return the original URL (note: site may be defunct)
                            return original_url

        return ''

    except Exception as e:
        # Silently handle errors - we'll just not have a website for this company
        return ''


def main():
    """Main extraction workflow."""
    print("="*70)
    print("Wikipedia Company Extraction")
    print("="*70)
    print()

    all_companies = []

    # Extract from each source
    for source in WIKIPEDIA_SOURCES:
        print(f"Fetching: {source['name']}")
        print(f"URL: {source['url']}")

        soup = fetch_wikipedia_page(source['url'])
        if not soup:
            print(f"  ⚠️  Failed to fetch page\n")
            continue

        # Extract based on page type
        if source['type'] == 'table':
            companies = extract_from_table(soup, source_name=source['name'])
        else:  # category
            companies = extract_from_category(soup, source_name=source['name'])

        print(f"  ✓ Extracted {len(companies)} companies\n")
        all_companies.extend(companies)

    print(f"Total companies extracted: {len(all_companies)}")

    # Deduplicate
    deduplicated = deduplicate_companies(all_companies)
    print(f"After deduplication: {len(deduplicated)} companies")

    # Filter for Bay Area (loose filter - keep most for manual review)
    bay_area = [c for c in deduplicated if is_bay_area_company(c['company_name'], c['city'])]
    print(f"Bay Area candidates: {len(bay_area)} companies")

    # Extract websites from Wikipedia pages
    print("\nExtracting websites from Wikipedia pages...")
    print("(This may take a minute due to rate limiting)")
    websites_found = 0
    for i, company in enumerate(bay_area):
        # Extract website using Wikipedia API
        website = extract_website_from_wikipedia_api(company['source_url'])
        if website:
            company['website'] = website
            websites_found += 1

        # Progress indicator every 25 companies
        if (i + 1) % 25 == 0:
            print(f"  Processed {i + 1}/{len(bay_area)} companies...")

        # Rate limiting: 0.1 second delay between API calls
        time.sleep(0.1)

    print(f"  ✓ Found websites for {websites_found}/{len(bay_area)} companies ({100*websites_found/len(bay_area):.1f}%)")
    print()

    # Sort by company name
    bay_area.sort(key=lambda x: x['company_name'])

    # Write to CSV
    output_dir = DATA_WORKING
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'wikipedia_companies.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Company Name', 'Website', 'Source URL', 'City', 'Notes'])
        writer.writeheader()

        for company in bay_area:
            writer.writerow({
                'Company Name': company['company_name'],
                'Website': company.get('website', ''),
                'Source URL': company['source_url'],
                'City': company['city'],
                'Notes': company['notes']
            })

    print()
    print(f"✓ Saved to: {output_file}")
    print()
    print("Next steps:")
    print("1. Review the CSV and remove non-biotech companies")
    print("2. Merge with BioPharmGuy data using merge_company_sources.py")
    print("3. Companies with websites can use Path A enrichment (automated)")
    print("4. Companies without websites will use Path B enrichment (AI-assisted)")
    print()


if __name__ == '__main__':
    main()
