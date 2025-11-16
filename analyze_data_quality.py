#!/usr/bin/env python3
"""
Comprehensive data quality analysis for California biotech dataset
"""

import csv
import sys
from collections import defaultdict, Counter

def analyze_quality(csv_file):
    """Analyze data quality metrics"""

    stats = {
        'total': 0,
        'with_lat_long': 0,
        'with_website': 0,
        'with_address': 0,
        'with_google_address': 0,
        'with_city': 0,
        'with_stage': 0,
        'with_focus': 0,
        'with_description': 0,
        'confidence_scores': [],
        'validation_sources': Counter(),
        'cities': Counter(),
        'stages': Counter(),
        'missing_validation': []
    }

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats['total'] += 1
            company_name = row['Company Name']

            # Check critical fields
            if row['Latitude'] and row['Longitude']:
                stats['with_lat_long'] += 1
            else:
                stats['missing_validation'].append(company_name)

            if row['Website']:
                stats['with_website'] += 1

            if row['Address']:
                stats['with_address'] += 1

            if row['Google_Address']:
                stats['with_google_address'] += 1

            if row['City']:
                stats['with_city'] += 1
                stats['cities'][row['City']] += 1

            if row['Company_Stage_Classified']:
                stats['with_stage'] += 1
                stats['stages'][row['Company_Stage_Classified']] += 1

            if row['Focus_Areas_Enhanced'] or row['Focus Areas']:
                stats['with_focus'] += 1

            if row['Description_Enhanced'] or row['Description']:
                stats['with_description'] += 1

            if row['Confidence_Score']:
                try:
                    stats['confidence_scores'].append(float(row['Confidence_Score']))
                except ValueError:
                    pass

            if row['Validation_Source']:
                stats['validation_sources'][row['Validation_Source']] += 1

    # Calculate percentages
    total = stats['total']

    print("=" * 70)
    print("CALIFORNIA BIOTECH DATASET - QUALITY ANALYSIS")
    print("=" * 70)
    print(f"\nTOTAL COMPANIES: {total}")
    print(f"TARGET: 2000 companies")
    print(f"GAP: {2000 - total} companies needed")

    print("\n" + "-" * 70)
    print("VALIDATION METRICS (Critical for Google My Maps)")
    print("-" * 70)
    print(f"Companies with Lat/Long: {stats['with_lat_long']:4d} ({stats['with_lat_long']/total*100:5.1f}%)")
    print(f"Companies missing coords: {total - stats['with_lat_long']:4d} ({(total-stats['with_lat_long'])/total*100:5.1f}%)")

    if stats['confidence_scores']:
        avg_conf = sum(stats['confidence_scores']) / len(stats['confidence_scores'])
        print(f"Average confidence score: {avg_conf:.2f}")

    print("\n" + "-" * 70)
    print("DATA COMPLETENESS")
    print("-" * 70)
    print(f"Website:           {stats['with_website']:4d} ({stats['with_website']/total*100:5.1f}%)")
    print(f"Address (input):   {stats['with_address']:4d} ({stats['with_address']/total*100:5.1f}%)")
    print(f"Google Address:    {stats['with_google_address']:4d} ({stats['with_google_address']/total*100:5.1f}%)")
    print(f"City:              {stats['with_city']:4d} ({stats['with_city']/total*100:5.1f}%)")
    print(f"Company Stage:     {stats['with_stage']:4d} ({stats['with_stage']/total*100:5.1f}%)")
    print(f"Focus Areas:       {stats['with_focus']:4d} ({stats['with_focus']/total*100:5.1f}%)")
    print(f"Description:       {stats['with_description']:4d} ({stats['with_description']/total*100:5.1f}%)")

    print("\n" + "-" * 70)
    print("VALIDATION SOURCES")
    print("-" * 70)
    for source, count in stats['validation_sources'].most_common():
        print(f"{source:20s}: {count:4d} ({count/total*100:5.1f}%)")

    print("\n" + "-" * 70)
    print("COMPANY STAGES")
    print("-" * 70)
    for stage, count in stats['stages'].most_common():
        print(f"{stage:20s}: {count:4d} ({count/total*100:5.1f}%)")

    print("\n" + "-" * 70)
    print("TOP 15 CITIES")
    print("-" * 70)
    for city, count in stats['cities'].most_common(15):
        print(f"{city:25s}: {count:4d}")

    print("\n" + "-" * 70)
    print("SAMPLE COMPANIES MISSING VALIDATION")
    print("-" * 70)
    for company in stats['missing_validation'][:20]:
        print(f"  - {company}")
    if len(stats['missing_validation']) > 20:
        print(f"  ... and {len(stats['missing_validation']) - 20} more")

    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    validation_rate = stats['with_lat_long'] / total * 100

    if validation_rate < 50:
        print("CRITICAL: Validation rate is below 50%")
        print("Actions needed:")
        print("  1. Retry Google Maps API with 'Company Name + City' fallback")
        print("  2. Extract addresses from company websites")
        print("  3. Manual validation for top companies")
    elif validation_rate < 75:
        print("WARNING: Validation rate is below target (75%)")
        print("Actions needed:")
        print("  1. Implement improved geocoding strategies")
        print("  2. Web scraping for missing addresses")
    elif validation_rate < 95:
        print("GOOD: Validation rate is acceptable but can improve")
        print("Actions needed:")
        print("  1. Focus on dataset expansion")
        print("  2. Quality enhancement for validated companies")
    else:
        print("EXCELLENT: Validation rate meets target (>95%)")

    print(f"\nDataset expansion needed: {2000 - total} companies")
    print("Recommended sources:")
    print("  - California Life Sciences Association (CLSA)")
    print("  - Biocom California member directory")
    print("  - UC tech transfer portfolios")
    print("  - VC portfolio companies")

    return stats

if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'data/final/companies.csv'
    analyze_quality(csv_file)
