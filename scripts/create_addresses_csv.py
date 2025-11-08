#!/usr/bin/env python3
import csv
from datetime import datetime

# Read the original CSV
input_file = 'east_bay_biotech_combined_notes.csv'
output_file = 'east_bay_biotech_with_addresses.csv'

# Dictionary to store addresses as we find them (will be populated via searches)
company_addresses = {
    # Format: "Company Name": "Full Address"
    # Will be filled in as we search
}

with open(input_file, 'r', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    original_fieldnames = reader.fieldnames

    # Create new fieldnames list with Address after City
    fieldnames = []
    for field in original_fieldnames:
        fieldnames.append(field)
        if field == 'City':
            fieldnames.append('Address')

    # Read all rows
    rows = []
    for row in reader:
        # Insert Address field after City
        new_row = {}
        for field in original_fieldnames:
            new_row[field] = row[field]
            if field == 'City':
                # Look up address if we have it
                company_name = row['Company Name']
                address = company_addresses.get(company_name, '')
                new_row['Address'] = address
        rows.append(new_row)

# Write the new CSV
with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Created {output_file} with {len(rows)} companies")
print(f"Address column added after City column")
print(f"Columns: {', '.join(fieldnames)}")