#!/usr/bin/env python3
"""
Data Quality Analysis Script for East Bay Biotech Map
Analyzes the companies.csv dataset for quality issues, completeness, and accuracy.
"""

import csv
import re
from collections import Counter, defaultdict
from urllib.parse import urlparse

# Bay Area cities (comprehensive list based on 9-county definition)
BAY_AREA_CITIES = {
    # Alameda County
    'alameda', 'albany', 'berkeley', 'dublin', 'emeryville', 'fremont', 'hayward',
    'livermore', 'newark', 'oakland', 'piedmont', 'pleasanton', 'san leandro',
    'union city',
    # Contra Costa County
    'antioch', 'brentwood', 'clayton', 'concord', 'danville', 'el cerrito',
    'hercules', 'lafayette', 'martinez', 'oakley', 'orinda', 'pinole',
    'pittsburg', 'pleasant hill', 'richmond', 'san pablo', 'san ramon', 'walnut creek',
    # Marin County
    'belvedere', 'corte madera', 'fairfax', 'larkspur', 'mill valley', 'novato',
    'ross', 'san anselmo', 'san rafael', 'sausalito', 'tiburon',
    # Napa County
    'american canyon', 'calistoga', 'napa', 'st. helena', 'yountville',
    # San Francisco County
    'san francisco',
    # San Mateo County
    'atherton', 'belmont', 'brisbane', 'burlingame', 'colma', 'daly city',
    'east palo alto', 'foster city', 'half moon bay', 'hillsborough', 'menlo park',
    'millbrae', 'pacifica', 'portola valley', 'redwood city', 'san bruno',
    'san carlos', 'san mateo', 'south san francisco', 'woodside',
    # Santa Clara County
    'campbell', 'cupertino', 'gilroy', 'los altos', 'los altos hills', 'los gatos',
    'milpitas', 'monte sereno', 'morgan hill', 'mountain view', 'palo alto',
    'san jose', 'santa clara', 'saratoga', 'sunnyvale',
    # Solano County
    'benicia', 'dixon', 'fairfield', 'rio vista', 'suisun city', 'vacaville', 'vallejo',
    # Sonoma County
    'cloverdale', 'cotati', 'healdsburg', 'petaluma', 'rohnert park', 'santa rosa',
    'sebastopol', 'sonoma', 'windsor'
}

def normalize_city(city):
    """Normalize city name for comparison."""
    if not city:
        return ''
    return city.lower().strip()

def is_valid_url(url):
    """Check if URL is valid."""
    if not url or url.strip() == '':
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def analyze_dataset(csv_path):
    """Perform comprehensive data quality analysis."""

    print("=" * 80)
    print("EAST BAY BIOTECH MAP - DATA QUALITY ANALYSIS REPORT")
    print("=" * 80)
    print()

    companies = []
    issues = []

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        print(f"📊 DATASET OVERVIEW")
        print(f"-" * 80)
        print(f"CSV Schema: {headers}")
        print()

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
            companies.append(row)

    total_companies = len(companies)
    print(f"Total Companies: {total_companies}")
    print()

    # ========================================================================
    # ANALYSIS 1: Schema Validation
    # ========================================================================
    print("=" * 80)
    print("1. SCHEMA VALIDATION")
    print("=" * 80)

    expected_columns = ['Company Name', 'Website', 'City', 'Address', 'Company Stage', 'Focus Areas']
    actual_columns = headers

    print(f"Expected columns: {expected_columns}")
    print(f"Actual columns:   {actual_columns}")

    if list(actual_columns) != expected_columns:
        print("❌ SCHEMA MISMATCH DETECTED")
        missing = set(expected_columns) - set(actual_columns)
        extra = set(actual_columns) - set(expected_columns)
        if missing:
            print(f"   Missing columns: {missing}")
            issues.append(f"Schema: Missing columns {missing}")
        if extra:
            print(f"   Extra columns: {extra}")
            issues.append(f"Schema: Extra columns {extra}")
    else:
        print("✅ Schema matches expected structure")
    print()

    # ========================================================================
    # ANALYSIS 2: Completeness Check
    # ========================================================================
    print("=" * 80)
    print("2. DATA COMPLETENESS ANALYSIS")
    print("=" * 80)

    completeness = {}
    for col in headers:
        empty_count = sum(1 for company in companies if not company.get(col, '').strip())
        completeness[col] = {
            'empty': empty_count,
            'filled': total_companies - empty_count,
            'pct': ((total_companies - empty_count) / total_companies) * 100
        }

        status = "✅" if empty_count == 0 else ("⚠️" if empty_count < total_companies * 0.1 else "❌")
        print(f"{status} {col:20s}: {completeness[col]['filled']:4d}/{total_companies} ({completeness[col]['pct']:5.1f}%) complete")

        if empty_count > 0:
            issues.append(f"Completeness: {col} has {empty_count} empty values ({(empty_count/total_companies)*100:.1f}%)")

    print()

    # ========================================================================
    # ANALYSIS 3: Geographic Validation
    # ========================================================================
    print("=" * 80)
    print("3. GEOGRAPHIC VALIDATION")
    print("=" * 80)

    cities = Counter()
    outside_bay_area = []

    for idx, company in enumerate(companies, start=2):
        city = normalize_city(company.get('City', ''))
        cities[city] += 1

        if city and city not in BAY_AREA_CITIES:
            outside_bay_area.append({
                'row': idx,
                'company': company.get('Company Name', ''),
                'city': company.get('City', ''),
                'address': company.get('Address', '')
            })

    print(f"Unique cities: {len(cities)}")
    print(f"Companies outside Bay Area: {len(outside_bay_area)}")
    print()

    if outside_bay_area:
        print("❌ COMPANIES OUTSIDE BAY AREA BOUNDARIES:")
        print(f"{'Row':<6} {'Company':<40} {'City':<20}")
        print("-" * 80)
        for item in outside_bay_area[:20]:  # Show first 20
            print(f"{item['row']:<6} {item['company']:<40} {item['city']:<20}")
            issues.append(f"Geography: Row {item['row']} - {item['company']} in {item['city']} (not Bay Area)")

        if len(outside_bay_area) > 20:
            print(f"... and {len(outside_bay_area) - 20} more")
        print()
    else:
        print("✅ All companies are within Bay Area boundaries")
        print()

    print("Top 15 Cities by Company Count:")
    for city, count in cities.most_common(15):
        in_bay = "✅" if city in BAY_AREA_CITIES else "❌"
        print(f"  {in_bay} {city:30s}: {count:4d} companies")
    print()

    # ========================================================================
    # ANALYSIS 4: URL Validation
    # ========================================================================
    print("=" * 80)
    print("4. URL VALIDATION")
    print("=" * 80)

    valid_urls = 0
    invalid_urls = []

    for idx, company in enumerate(companies, start=2):
        url = company.get('Website', '').strip()
        if is_valid_url(url):
            valid_urls += 1
        else:
            invalid_urls.append({
                'row': idx,
                'company': company.get('Company Name', ''),
                'url': url
            })

    print(f"Valid URLs: {valid_urls}/{total_companies} ({(valid_urls/total_companies)*100:.1f}%)")
    print(f"Invalid URLs: {len(invalid_urls)}")

    if invalid_urls:
        print("\n❌ INVALID WEBSITE URLs:")
        print(f"{'Row':<6} {'Company':<40} {'URL':<30}")
        print("-" * 80)
        for item in invalid_urls[:10]:
            print(f"{item['row']:<6} {item['company']:<40} {item['url']:<30}")
            issues.append(f"URL: Row {item['row']} - {item['company']} has invalid URL: '{item['url']}'")

        if len(invalid_urls) > 10:
            print(f"... and {len(invalid_urls) - 10} more")
    else:
        print("✅ All website URLs are valid")
    print()

    # ========================================================================
    # ANALYSIS 5: Company Stage Distribution
    # ========================================================================
    print("=" * 80)
    print("5. COMPANY STAGE DISTRIBUTION")
    print("=" * 80)

    stages = Counter()
    for company in companies:
        stage = company.get('Company Stage', '').strip()
        stages[stage] += 1

    print(f"{'Company Stage':<30} {'Count':<8} {'Percentage'}")
    print("-" * 80)
    for stage, count in stages.most_common():
        pct = (count / total_companies) * 100
        print(f"{stage:<30} {count:<8} {pct:5.1f}%")
    print()

    # ========================================================================
    # ANALYSIS 6: Duplicate Detection
    # ========================================================================
    print("=" * 80)
    print("6. DUPLICATE DETECTION")
    print("=" * 80)

    # Check by company name
    name_counts = Counter()
    for company in companies:
        name = company.get('Company Name', '').strip().lower()
        name_counts[name] += 1

    duplicates_by_name = [(name, count) for name, count in name_counts.items() if count > 1]

    if duplicates_by_name:
        print(f"❌ Found {len(duplicates_by_name)} duplicate company names:")
        for name, count in duplicates_by_name[:10]:
            print(f"  - '{name}' appears {count} times")
            issues.append(f"Duplicate: Company name '{name}' appears {count} times")
        if len(duplicates_by_name) > 10:
            print(f"  ... and {len(duplicates_by_name) - 10} more")
    else:
        print("✅ No duplicate company names found")
    print()

    # Check by website domain
    domain_counts = defaultdict(list)
    for idx, company in enumerate(companies, start=2):
        url = company.get('Website', '').strip()
        if is_valid_url(url):
            domain = urlparse(url).netloc.lower()
            # Remove www. prefix for comparison
            domain = domain.replace('www.', '')
            domain_counts[domain].append({
                'row': idx,
                'company': company.get('Company Name', '')
            })

    duplicate_domains = {domain: companies for domain, companies in domain_counts.items() if len(companies) > 1}

    if duplicate_domains:
        print(f"❌ Found {len(duplicate_domains)} duplicate website domains:")
        for domain, company_list in list(duplicate_domains.items())[:10]:
            print(f"  - {domain}:")
            for item in company_list:
                print(f"    Row {item['row']}: {item['company']}")
            issues.append(f"Duplicate domain: {domain} used by {len(company_list)} companies")
        if len(duplicate_domains) > 10:
            print(f"  ... and {len(duplicate_domains) - 10} more")
    else:
        print("✅ No duplicate website domains found")
    print()

    # ========================================================================
    # ANALYSIS 7: Address Quality
    # ========================================================================
    print("=" * 80)
    print("7. ADDRESS QUALITY ANALYSIS")
    print("=" * 80)

    addresses_with_street = 0
    addresses_city_only = 0
    addresses_missing = 0
    addresses_without_zip = 0

    for company in companies:
        address = company.get('Address', '').strip()
        if not address:
            addresses_missing += 1
        elif ',' in address and any(char.isdigit() for char in address):
            addresses_with_street += 1
            # Check for ZIP code (5 digits)
            if not re.search(r'\b\d{5}\b', address):
                addresses_without_zip += 1
        else:
            addresses_city_only += 1

    print(f"Full street addresses: {addresses_with_street}/{total_companies} ({(addresses_with_street/total_companies)*100:.1f}%)")
    print(f"City-only addresses:   {addresses_city_only}/{total_companies} ({(addresses_city_only/total_companies)*100:.1f}%)")
    print(f"Missing addresses:     {addresses_missing}/{total_companies} ({(addresses_missing/total_companies)*100:.1f}%)")
    print(f"Addresses without ZIP: {addresses_without_zip}/{total_companies} ({(addresses_without_zip/total_companies)*100:.1f}%)")

    if addresses_city_only > 0:
        issues.append(f"Address Quality: {addresses_city_only} addresses are city-only format")
    if addresses_without_zip > 0:
        issues.append(f"Address Quality: {addresses_without_zip} addresses missing ZIP codes")
    if addresses_missing > 0:
        issues.append(f"Address Quality: {addresses_missing} addresses are completely missing")

    print()

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 80)
    print("SUMMARY OF ISSUES")
    print("=" * 80)
    print(f"Total issues found: {len(issues)}")
    print()

    if issues:
        # Group issues by category
        issue_categories = defaultdict(list)
        for issue in issues:
            category = issue.split(':')[0]
            issue_categories[category].append(issue)

        for category, category_issues in issue_categories.items():
            print(f"\n{category} ({len(category_issues)} issues):")
            for issue in category_issues[:5]:  # Show first 5 per category
                print(f"  - {issue}")
            if len(category_issues) > 5:
                print(f"  ... and {len(category_issues) - 5} more")
    else:
        print("✅ No data quality issues detected!")

    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    csv_path = os.path.join(repo_root, 'data', 'final', 'companies.csv')
    analyze_dataset(csv_path)
