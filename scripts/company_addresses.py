#!/usr/bin/env python3
import csv

# Dictionary with company addresses found via search
# Format: "Company Name": "Street Address, City, CA ZIP"
company_addresses = {
    "10x Genomics": "6230 Stoneridge Mall Road, Pleasanton, CA 94588",
    "4D Molecular Therapeutics": "5858 Horton Street, Suite 455, Emeryville, CA 94608",
    "Abalone Bio": "",  # To be searched
    "Advanced Biofuels and Bioproducts Process Development Unit": "",  # To be searched
    "Acepodia": "",  # To be searched
    "Acrigen Biosciences": "",  # To be searched
    "Actym Therapeutics": "",  # To be searched
    "Adanate": "",  # To be searched
    "Addition Therapeutics": "",  # To be searched
    "AllCells": "",  # To be searched
    "Amber Bio": "",  # To be searched
    "Ansa Biotechnologies": "",  # To be searched
    "Apertor Pharmaceuticals": "",  # To be searched
    "Arcadia Science": "",  # To be searched
    "Ardelyx": "",  # To be searched
    "ATUM": "",  # To be searched
    "Bayer": "",  # To be searched
    "Bio-Rad Laboratories": "",  # To be searched
    "Bolt Threads": "",  # To be searched
    "Caribou Biosciences": "2929 7th Street, Suite 105, Berkeley, CA 94710",
    "Catalent": "",  # To be searched
    "Catena Biosciences": "",  # To be searched
    "CellFE": "",  # To be searched
    "Cerus Corporation": "",  # To be searched
    "Joint Genome Institute": "",  # To be searched
    "Dynavax Technologies": "",  # To be searched
    "Eikon Therapeutics": "",  # To be searched
    "Eureka Therapeutics": "",  # To be searched
    "Exelixis": "",  # To be searched
    "GeneFab": "",  # To be searched
    "Ginkgo Bioworks": "",  # To be searched
    "Glyphic Biotechnologies": "",  # To be searched
    "Gritstone bio": "",  # To be searched
    "Indee Labs": "",  # To be searched
    "Innovative Genomics Institute": "",  # To be searched
    "Joint BioEnergy Institute": "",  # To be searched
    "Kimia Therapeutics": "",  # To be searched
    "Kyverna Therapeutics": "",  # To be searched
    "Advanced Light Source": "",  # To be searched
    "Lonza": "",  # To be searched
    "Lygos": "",  # To be searched
    "Nanotein": "",  # To be searched
    "Novartis": "",  # To be searched
    "Nutcracker Therapeutics": "",  # To be searched
    "Ohmic Biosciences": "",  # To be searched
    "OmniAb": "",  # To be searched
    "Phyllom BioProducts": "",  # To be searched
    "Pivot Bio": "",  # To be searched
    "Prellis Biologics": "",  # To be searched
    "Profluent": "",  # To be searched
    "Prolific Machines": "",  # To be searched
    "Ray Therapeutics": "",  # To be searched
    "Regel Therapeutics": "",  # To be searched
    "ResVita Bio": "",  # To be searched
    "Sampling Human": "",  # To be searched
    "Santa Ana Bio": "",  # To be searched
    "Santen": "",  # To be searched
    "Scribe Therapeutics": "",  # To be searched
    "Unchained Labs": "",  # To be searched
    "UCSF Benioff Children's Hospital Oakland": "",  # To be searched
    "USDA Western Regional Research Center": "",  # To be searched
    "Valitor": "",  # To be searched
    "XOMA Corporation": "",  # To be searched
    "Zymergen": "",  # To be searched
    "Metagenomi": "",  # To be searched
    "Mammoth Biosciences": "",  # To be searched
    "Sangamo Therapeutics": "",  # To be searched
    "Intellia Therapeutics": "",  # To be searched
    "BioMarin Pharmaceutical": "",  # To be searched
    "Ultragenyx Pharmaceutical": "",  # To be searched
    "Freenome": "",  # To be searched
    "IGM Biosciences": "",  # To be searched
    "Calico Life Sciences": "",  # To be searched
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
            rows.append(new_row)

    # Write the new CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Count how many addresses we have
    filled = sum(1 for addr in company_addresses.values() if addr)
    total = len(company_addresses)

    print(f"Updated {output_file}")
    print(f"Addresses filled: {filled}/{total}")
    print(f"Remaining to search: {total - filled}")

    # Show which companies still need addresses
    missing = [name for name, addr in company_addresses.items() if not addr]
    if missing and len(missing) <= 10:
        print("\nCompanies still needing addresses:")
        for name in missing[:10]:
            print(f"  - {name}")

if __name__ == "__main__":
    update_csv_with_addresses()