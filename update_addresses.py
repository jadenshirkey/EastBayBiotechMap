#!/usr/bin/env python3
import csv
from datetime import datetime

# Dictionary with company addresses found via search
# Format: "Company Name": "Street Address, City, CA ZIP"
company_addresses = {
    "10x Genomics": "6230 Stoneridge Mall Road, Pleasanton, CA 94588",
    "4D Molecular Therapeutics": "5858 Horton Street, Suite 455, Emeryville, CA 94608",
    "Abalone Bio": "",
    "Advanced Biofuels and Bioproducts Process Development Unit": "",
    "Acepodia": "",
    "Acrigen Biosciences": "",
    "Actym Therapeutics": "",
    "Adanate": "",
    "Addition Therapeutics": "",
    "AllCells": "",
    "Amber Bio": "",
    "Ansa Biotechnologies": "1198 65th Street, Suite 250, Emeryville, CA 94608",
    "Apertor Pharmaceuticals": "",
    "Arcadia Science": "",
    "Ardelyx": "",
    "ATUM": "",
    "Bayer": "",
    "Bio-Rad Laboratories": "",
    "Bolt Threads": "",
    "Caribou Biosciences": "2929 7th Street, Suite 105, Berkeley, CA 94710",
    "Catalent": "",
    "Catena Biosciences": "",
    "CellFE": "",
    "Cerus Corporation": "",
    "Joint Genome Institute": "",
    "Dynavax Technologies": "",
    "Eikon Therapeutics": "",
    "Eureka Therapeutics": "",
    "Exelixis": "1851 Harbor Bay Parkway, Alameda, CA 94502",
    "GeneFab": "",
    "Ginkgo Bioworks": "5858 Horton Street, Suite 400, Emeryville, CA 94608",
    "Glyphic Biotechnologies": "",
    "Gritstone bio": "",
    "Indee Labs": "",
    "Innovative Genomics Institute": "",
    "Joint BioEnergy Institute": "",
    "Kimia Therapeutics": "",
    "Kyverna Therapeutics": "",
    "Advanced Light Source": "",
    "Lonza": "",
    "Lygos": "",
    "Nanotein": "",
    "Novartis": "",
    "Nutcracker Therapeutics": "",
    "Ohmic Biosciences": "",
    "OmniAb": "",
    "Phyllom BioProducts": "",
    "Pivot Bio": "",
    "Prellis Biologics": "",
    "Profluent": "",
    "Prolific Machines": "",
    "Ray Therapeutics": "",
    "Regel Therapeutics": "",
    "ResVita Bio": "",
    "Sampling Human": "",
    "Santa Ana Bio": "",
    "Santen": "",
    "Scribe Therapeutics": "1150 Marina Village Parkway, Suite 100, Alameda, CA 94501",
    "Unchained Labs": "",
    "UCSF Benioff Children's Hospital Oakland": "",
    "USDA Western Regional Research Center": "",
    "Valitor": "",
    "XOMA Corporation": "",
    "Zymergen": "",
    "Metagenomi": "",
    "Mammoth Biosciences": "",
    "Sangamo Therapeutics": "",
    "Intellia Therapeutics": "",
    "BioMarin Pharmaceutical": "",
    "Ultragenyx Pharmaceutical": "",
    "Freenome": "",
    "IGM Biosciences": "",
    "Calico Life Sciences": "",
}

def update_csv_with_addresses():
    """Update the CSV file with addresses"""
    input_file = 'east_bay_biotech_combined_notes.csv'
    output_file = 'east_bay_biotech_with_addresses.csv'

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
        companies_found = []
        companies_not_found = []

        for row in reader:
            # Insert Address field after City
            new_row = {}
            for field in original_fieldnames:
                new_row[field] = row[field]
                if field == 'City':
                    # Look up address
                    company_name = row['Company Name']
                    address = company_addresses.get(company_name, '')
                    new_row['Address'] = address

                    if address:
                        companies_found.append(company_name)
                    else:
                        companies_not_found.append(company_name)
            rows.append(new_row)

    # Write the new CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Statistics
    filled = len(companies_found)
    total = len(rows)

    print(f"Updated {output_file}")
    print(f"Addresses filled: {filled}/{total}")
    print(f"Remaining to search: {total - filled}")
    print(f"\nCompanies WITH addresses:")
    for name in companies_found:
        print(f"  ✓ {name}")

    print(f"\nNext batch to search (first 10):")
    for name in companies_not_found[:10]:
        print(f"  - {name}")

if __name__ == "__main__":
    update_csv_with_addresses()