#!/usr/bin/env python3
"""Finalize enrichment by combining all results and creating reference list."""

import csv
from pathlib import Path

# File paths
ORIGINAL_ENRICHED = Path("data/working/companies_enriched_path_a.csv")  # First 1650 companies
PARALLEL_ENRICHED = Path("data/working/companies_enriched_parallel.csv")  # New 407 companies
COMPANIES_MERGED = Path("data/working/companies_merged.csv")
FINAL_OUTPUT = Path("data/working/companies_enriched_final.csv")
REFERENCE_LIST = Path("data/working/Post-Google-API-Reference-List.csv")

print("=" * 70)
print("Finalizing Google Maps Enrichment")
print("=" * 70)

# Load original enriched data (if exists)
original_enriched = []
if ORIGINAL_ENRICHED.exists():
    with open(ORIGINAL_ENRICHED, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        original_enriched = list(reader)
    print(f"✓ Loaded {len(original_enriched)} companies from original enrichment")

# Load parallel enriched data
with open(PARALLEL_ENRICHED, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    parallel_enriched = list(reader)
print(f"✓ Loaded {len(parallel_enriched)} companies from parallel enrichment")

# Combine all enriched data
all_enriched = original_enriched + parallel_enriched
print(f"✓ Total enriched companies: {len(all_enriched)}")

# Write final combined output
if all_enriched:
    with open(FINAL_OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_enriched[0].keys())
        writer.writeheader()
        writer.writerows(all_enriched)
    print(f"✓ Saved final enriched output: {FINAL_OUTPUT}")

# Create reference list comparing original vs Google data
print("\nCreating Post-Google-API-Reference-List.csv...")

# Load original companies
with open(COMPANIES_MERGED, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    all_companies = {row['Company Name']: row for row in reader}

# Build enriched lookup
enriched_lookup = {row['Company Name']: row for row in all_enriched}

# Create reference list
reference_data = []
for company_name, original in all_companies.items():
    enriched = enriched_lookup.get(company_name, {})

    reference_data.append({
        'Original_Company_Name': company_name,
        'Original_Website': original.get('Website', ''),
        'Original_City': original.get('City', ''),
        'Google_Company_Name': enriched.get('Google_Name', ''),
        'Google_Address': enriched.get('Google_Address', ''),
        'Google_Website': enriched.get('Google_Website', ''),
        'Latitude': enriched.get('Latitude', ''),
        'Longitude': enriched.get('Longitude', ''),
        'Match_Score': enriched.get('Confidence_Score', ''),
        'Enriched': 'Yes' if company_name in enriched_lookup else 'No'
    })

with open(REFERENCE_LIST, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=reference_data[0].keys())
    writer.writeheader()
    writer.writerows(reference_data)

print(f"✓ Saved reference list: {REFERENCE_LIST}")

# Final statistics
total_companies = len(all_companies)
enriched_count = len(all_enriched)
failed_count = total_companies - enriched_count

print("\n" + "=" * 70)
print("FINAL STATISTICS")
print("=" * 70)
print(f"Total companies in dataset: {total_companies}")
print(f"Successfully enriched: {enriched_count} ({enriched_count/total_companies*100:.1f}%)")
print(f"Failed to enrich: {failed_count} ({failed_count/total_companies*100:.1f}%)")
print("=" * 70)
