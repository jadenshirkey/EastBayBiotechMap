#!/usr/bin/env python3
"""Resume enrichment for remaining unenriched companies."""

import csv
import json
from pathlib import Path

NUM_WORKERS = 16
REFERENCE_LIST = Path("data/working/Post-Google-API-Reference-List.csv")
COMPANIES_MERGED = Path("data/working/companies_merged.csv")
CHUNK_DIR = Path("data/working/chunks")

# Load reference list to see what's already enriched
with open(REFERENCE_LIST, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    reference_data = {row['Original_Company_Name']: row for row in reader}

# Load all companies
with open(COMPANIES_MERGED, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    all_companies = list(reader)

# Filter to unenriched companies with websites
unenriched = []
for idx, company in enumerate(all_companies):
    name = company.get('Company Name', '')
    website = company.get('Website', '')
    ref = reference_data.get(name, {})

    if website and ref.get('Enriched') == 'No':
        company['original_index'] = idx
        unenriched.append(company)

print(f"Total companies: {len(all_companies)}")
print(f"Unenriched companies with websites: {len(unenriched)}")

if len(unenriched) == 0:
    print("All companies already enriched!")
    exit(0)

# Create chunk directory
CHUNK_DIR.mkdir(exist_ok=True)

# Split into chunks
chunk_size = (len(unenriched) + NUM_WORKERS - 1) // NUM_WORKERS
chunks = []

for i in range(NUM_WORKERS):
    start_idx = i * chunk_size
    end_idx = min((i + 1) * chunk_size, len(unenriched))

    if start_idx >= len(unenriched):
        break

    chunk_companies = unenriched[start_idx:end_idx]
    chunk_file = CHUNK_DIR / f"chunk_{i}.csv"

    # Write chunk to CSV
    if chunk_companies:
        with open(chunk_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=chunk_companies[0].keys())
            writer.writeheader()
            writer.writerows(chunk_companies)

        chunks.append({
            'worker_id': i,
            'chunk_file': str(chunk_file),
            'start_index': int(chunk_companies[0]['original_index']),
            'end_index': int(chunk_companies[-1]['original_index']),
            'size': len(chunk_companies)
        })

        print(f"Worker {i}: {len(chunk_companies)} companies (indices {chunks[-1]['start_index']}-{chunks[-1]['end_index']})")

# Write worker config
config_file = CHUNK_DIR / "worker_config.json"
with open(config_file, 'w') as f:
    json.dump(chunks, f, indent=2)

print(f"\nCreated {len(chunks)} chunks")
print(f"Config saved to: {config_file}")
print(f"\nReady to launch {len(chunks)} workers!")
