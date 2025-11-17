#!/usr/bin/env python3
"""Merge enriched chunks into final output file."""

import csv
from pathlib import Path

CHUNKS_DIR = Path("data/working/chunks")
OUTPUT_FILE = Path("data/working/companies_enriched_parallel.csv")

# Collect all enriched chunks
chunk_files = sorted(CHUNKS_DIR.glob("chunk_*_enriched.csv"))
print(f"Found {len(chunk_files)} enriched chunks")

# Read all enriched companies
all_enriched = []
headers = None

for chunk_file in chunk_files:
    with open(chunk_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if headers is None:
            headers = reader.fieldnames
        chunk_data = list(reader)
        all_enriched.extend(chunk_data)
        print(f"{chunk_file.name}: {len(chunk_data)} companies")

print(f"\nTotal enriched: {len(all_enriched)} companies")

# Write merged output
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(all_enriched)

print(f"✓ Merged output saved to: {OUTPUT_FILE}")
