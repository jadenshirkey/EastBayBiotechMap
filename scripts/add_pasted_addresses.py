#!/usr/bin/env python3
import csv

# Addresses from user's paste
pasted_addresses = {
    "Acrigen Biosciences": "626 Bancroft Way, Berkeley, CA 94702",
    "Actym Therapeutics": "Berkeley, CA",
    "Addition Therapeutics": "Berkeley, CA",
    "Amber Bio": "Berkeley, CA",
    "Bayer": "800 Dwight Way, Berkeley, CA 94710",
    "Caribou Biosciences": "2929 7th St, Suite 105, Berkeley, CA 94710",
    "Glyphic Biotechnologies": "3100 San Pablo Avenue, Suite 201, Berkeley, CA 94702",
    "Indee Labs": "Berkeley, CA",
    "Innovative Genomics Institute": "2151 Berkeley Way, Berkeley, CA 94720",
    "Kimia Therapeutics": "Berkeley, CA",
    "Advanced Light Source": "1 Cyclotron Rd, Berkeley, CA 94720",
    "Nanotein": "2950 San Pablo Ave, Berkeley, CA 94702",
    "Pivot Bio": "2910 7th St, Berkeley, CA 94710",
    "Prellis Biologics": "Berkeley, CA",
    "Ray Therapeutics": "2607 7th Street, Suite B, Berkeley, CA 94710",
    "Regel Therapeutics": "Berkeley, CA",
    "ResVita Bio": "2625 Durant Avenue, Berkeley, CA 94720",
    "Sampling Human": "Berkeley, CA",
    "Valitor": "Berkeley, CA",
    "4D Molecular Therapeutics": "Emeryville, CA",
    "Abalone Bio": "Emeryville, CA",
    "Ansa Biotechnologies": "1198 65th St, Suite 250, Emeryville, CA 94608",
    "Arcadia Science": "6401 Hollis St, Suite 100, Emeryville, CA 94608",
    "Catalent": "5959 Horton St, Suite 400, Emeryville, CA 94608",
    "Dynavax Technologies": "2100 Powell St, Suite 720, Emeryville, CA 94608",
    "Eureka Therapeutics": "5858 Horton St, Suite 370, Emeryville, CA 94608",
    "Ginkgo Bioworks": "1440 Stanford Ave, Emeryville, CA 94608",
    "Gritstone bio": "5959 Horton St, Suite 300, Emeryville, CA 94608",
    "Joint BioEnergy Institute": "5885 Hollis St, Emeryville, CA 94608",
    "Advanced Biofuels and Bioproducts Process Development Unit": "5885 Hollis St, Emeryville, CA 94608",
    "OmniAb": "Emeryville, CA",
    "Prolific Machines": "Emeryville, CA",
    "Profluent": "Emeryville, CA",
    "Phyllom BioProducts": "Oakland, CA",
    "UCSF Benioff Children's Hospital Oakland": "5700 Martin Luther King Jr Way, Oakland, CA 94609",
    "USDA Western Regional Research Center": "800 Buchanan St, Albany, CA 94710",
    "Acepodia": "Alameda, CA",
    "Adanate": "1010 Atlantic Avenue, Suite 102, Alameda, CA 94501",
    "AllCells": "1301 Harbor Bay Pkwy, Suite 200, Alameda, CA 94502",
    "Apertor Pharmaceuticals": "1640 South Loop Road, Suite 200, Alameda, CA 94502",
    "CellFE": "Alameda, CA",
    "Exelixis": "1851 Harbor Bay Pkwy, Alameda, CA 94502",
    "GeneFab": "Alameda, CA",
    "Ohmic Biosciences": "Alameda, CA",
    "Santa Ana Bio": "Alameda, CA",
    "Scribe Therapeutics": "1150 Marina Village Pkwy, Alameda, CA 94501",
}

# Read existing CSV
with open('east_bay_biotech_with_addresses.csv', 'r', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames
    rows = list(reader)

# Update addresses
updated_count = 0
for row in rows:
    company_name = row['Company Name']
    if company_name in pasted_addresses:
        if not row['Address'] or row['Address'] == '':
            row['Address'] = pasted_addresses[company_name]
            updated_count += 1
            print(f"Updated: {company_name} -> {pasted_addresses[company_name]}")

# Write updated CSV
with open('east_bay_biotech_with_addresses.csv', 'w', encoding='utf-8', newline='') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nTotal addresses updated: {updated_count}")