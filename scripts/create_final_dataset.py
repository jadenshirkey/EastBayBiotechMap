#!/usr/bin/env python3
"""
Create final comprehensive dataset by merging all enrichment sources.
Combines classification data, Google Maps enrichment, and other sources.
"""

import csv
from pathlib import Path

# File paths
COMPANIES_MERGED = Path("data/working/companies_merged.csv")
COMPANIES_CLASSIFIED = Path("data/working/companies_classified.csv")
COMPANIES_ENRICHED_FINAL = Path("data/working/companies_enriched_final.csv")
COMPANIES_FOCUSED = Path("data/working/companies_focused.csv")
POST_GOOGLE_REFERENCE = Path("data/working/Post-Google-API-Reference-List.csv")
OUTPUT_COMPLETE = Path("data/final/companies.csv")
OUTPUT_WORKING = Path("data/working/companies_complete.csv")

print("=" * 70)
print("Creating Comprehensive Final Dataset")
print("=" * 70)

# Step 1: Load all data sources
print("\n1. Loading data sources...")

# Load base companies
with open(COMPANIES_MERGED, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    base_companies = {row['Company Name']: row for row in reader}
print(f"  ✓ Base companies: {len(base_companies)}")

# Load classifications (if exists)
classified_data = {}
if COMPANIES_CLASSIFIED.exists():
    with open(COMPANIES_CLASSIFIED, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Company Name', '')
            if name:
                classified_data[name] = {
                    'Company_Stage_Classified': row.get('Company_Stage', 'Unknown'),
                    'Classifier_Date': row.get('Classifier_Date', ''),
                    'Focus_Areas_Enhanced': row.get('Focus_Areas', '')
                }
    print(f"  ✓ Classifications: {len(classified_data)}")

# Load Google Maps enrichment
google_enriched = {}
if COMPANIES_ENRICHED_FINAL.exists():
    with open(COMPANIES_ENRICHED_FINAL, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Company Name', '')
            if name:
                google_enriched[name] = {
                    'Google_Address': row.get('Google_Address', ''),
                    'Google_Name': row.get('Google_Name', ''),
                    'Google_Website': row.get('Google_Website', ''),
                    'Confidence_Score': row.get('Confidence_Score', ''),
                    'Latitude': row.get('Latitude', ''),
                    'Longitude': row.get('Longitude', '')
                }
    print(f"  ✓ Google Maps enriched: {len(google_enriched)}")

# Load focused companies (if exists - has enhanced descriptions)
focused_data = {}
if COMPANIES_FOCUSED.exists():
    with open(COMPANIES_FOCUSED, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Company Name', '')
            if name:
                # Get enhanced description if available
                description = row.get('Description', '')
                if description and description != base_companies.get(name, {}).get('Description', ''):
                    focused_data[name] = {
                        'Description_Enhanced': description
                    }
    print(f"  ✓ Enhanced descriptions: {len(focused_data)}")

# Step 2: Merge all data
print("\n2. Merging data...")
final_companies = []
stats = {
    'total': 0,
    'has_classification': 0,
    'has_google_maps': 0,
    'has_coordinates': 0,
    'has_enhanced_desc': 0,
    'stage_distribution': {}
}

for company_name, base_data in base_companies.items():
    # Start with base data
    merged = base_data.copy()

    # Add classification data
    if company_name in classified_data:
        merged.update(classified_data[company_name])
        stats['has_classification'] += 1
        stage = classified_data[company_name].get('Company_Stage_Classified', 'Unknown')
        stats['stage_distribution'][stage] = stats['stage_distribution'].get(stage, 0) + 1
    else:
        merged['Company_Stage_Classified'] = 'Unknown'
        merged['Classifier_Date'] = ''
        merged['Focus_Areas_Enhanced'] = merged.get('Focus Areas', '')
        stats['stage_distribution']['Unknown'] = stats['stage_distribution'].get('Unknown', 0) + 1

    # Add Google Maps data
    if company_name in google_enriched:
        merged.update(google_enriched[company_name])
        stats['has_google_maps'] += 1
        if google_enriched[company_name].get('Latitude') and google_enriched[company_name].get('Longitude'):
            stats['has_coordinates'] += 1
    else:
        merged.update({
            'Google_Address': '',
            'Google_Name': '',
            'Google_Website': '',
            'Confidence_Score': '',
            'Latitude': '',
            'Longitude': ''
        })

    # Add enhanced description (if available)
    if company_name in focused_data:
        merged.update(focused_data[company_name])
        stats['has_enhanced_desc'] += 1
    else:
        merged['Description_Enhanced'] = merged.get('Description', '')

    # Copy Google_Address to Address column if original is empty
    if not merged.get('Address') and merged.get('Google_Address'):
        merged['Address'] = merged['Google_Address']

    stats['total'] += 1
    final_companies.append(merged)

# Step 3: Sort companies by name
print("\n3. Sorting companies...")
final_companies.sort(key=lambda x: x.get('Company Name', ''))

# Step 4: Write output files
print("\n4. Writing output files...")

# Define field order
fieldnames = [
    # Core fields
    'Company Name',
    'Website',
    'City',
    'Address',

    # Classification
    'Company Stage',  # Original (usually empty)
    'Company_Stage_Classified',  # From classifier

    # Focus areas
    'Focus Areas',  # Original
    'Focus_Areas_Enhanced',  # From classifier

    # Descriptions
    'Description',  # Original
    'Description_Enhanced',  # From focused.csv

    # Google Maps enrichment
    'Google_Name',
    'Google_Address',
    'Google_Website',
    'Latitude',
    'Longitude',
    'Confidence_Score',

    # Metadata
    'Validation_Source',
    'Classifier_Date'
]

# Add any remaining fields that aren't in our list
for company in final_companies:
    for key in company.keys():
        if key not in fieldnames:
            fieldnames.append(key)

# Write to working directory
with open(OUTPUT_WORKING, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(final_companies)
print(f"  ✓ Saved to working: {OUTPUT_WORKING}")

# Write to final directory
OUTPUT_COMPLETE.parent.mkdir(exist_ok=True)
with open(OUTPUT_COMPLETE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(final_companies)
print(f"  ✓ Saved to final: {OUTPUT_COMPLETE}")

# Step 5: Display statistics
print("\n" + "=" * 70)
print("FINAL STATISTICS")
print("=" * 70)
print(f"Total companies: {stats['total']}")
print(f"With classification: {stats['has_classification']} ({stats['has_classification']/stats['total']*100:.1f}%)")
print(f"With Google Maps data: {stats['has_google_maps']} ({stats['has_google_maps']/stats['total']*100:.1f}%)")
print(f"With coordinates: {stats['has_coordinates']} ({stats['has_coordinates']/stats['total']*100:.1f}%)")
print(f"With enhanced descriptions: {stats['has_enhanced_desc']} ({stats['has_enhanced_desc']/stats['total']*100:.1f}%)")

print("\nCompany Stage Distribution:")
for stage in sorted(stats['stage_distribution'].keys()):
    count = stats['stage_distribution'][stage]
    pct = count / stats['total'] * 100
    print(f"  {stage}: {count} ({pct:.1f}%)")

print("=" * 70)
print("\n✓ Final comprehensive dataset created successfully!")
print(f"  Output: {OUTPUT_COMPLETE}")
print(f"  Total fields: {len(fieldnames)}")