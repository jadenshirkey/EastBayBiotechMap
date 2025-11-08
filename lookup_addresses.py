#!/usr/bin/env python3
"""
Lookup and update addresses for biotech companies.

This script reads the addresses JSON file and updates the CSV
with addresses that have been found via web search.
"""

import csv
import json
from pathlib import Path

# File paths
BASE_DIR = Path("/home/user/EastBayBiotechMap")
OUTPUT_CSV = BASE_DIR / "data/final/companies.csv"
ADDRESSES_FOUND = BASE_DIR / "addresses_found.json"

def read_csv(filepath):
    """Read CSV file and return list of dictionaries."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_csv(filepath, data, fieldnames):
    """Write data to CSV file."""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def update_addresses(csv_file, addresses_dict):
    """Update the CSV file with found addresses."""
    # Read current data
    companies = read_csv(csv_file)

    # Update addresses
    updated_count = 0
    for company in companies:
        company_name = company['Company Name']
        if company_name in addresses_dict and not company['Address']:
            company['Address'] = addresses_dict[company_name]
            updated_count += 1
            print(f"  Updated: {company_name}")

    # Write back to CSV
    fieldnames = ['Company Name', 'Website', 'City', 'Address', 'Company Stage', 'Focus Areas']
    write_csv(csv_file, companies, fieldnames)

    return updated_count

def main():
    # Check if addresses_found.json exists
    if not ADDRESSES_FOUND.exists():
        print(f"No addresses file found at: {ADDRESSES_FOUND}")
        print("Please create addresses_found.json with the format:")
        print('{"Company Name": "Full Address", ...}')
        return

    # Load found addresses
    with open(ADDRESSES_FOUND, 'r') as f:
        addresses = json.load(f)

    print(f"Loaded {len(addresses)} addresses from {ADDRESSES_FOUND}")
    print()

    # Update CSV
    print("Updating addresses in CSV...")
    updated = update_addresses(OUTPUT_CSV, addresses)

    print()
    print(f"Successfully updated {updated} company addresses")
    print(f"Output saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
