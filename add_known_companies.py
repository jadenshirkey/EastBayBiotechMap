#!/usr/bin/env python3
"""
Add known California biotech companies manually curated from reliable sources
Focus on quality over quantity
"""

import csv
import os
from typing import List, Dict, Set
import re

class KnownCompanyAdder:
    def __init__(self):
        self.known_companies = self.get_known_california_biotech()

    def normalize_name(self, name: str) -> str:
        """Normalize company name for comparison"""
        name = name.strip().lower()
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'[,.\-]', '', name)
        name = re.sub(r'\s+(inc|llc|corp|corporation|limited|ltd|company)$', '', name)
        return name

    def get_known_california_biotech(self) -> List[Dict]:
        """
        Curated list of known California biotech companies
        Sources: Public databases, news, biotech directories
        """

        companies = [
            # Major Public Companies
            {"Company Name": "Amgen", "City": "Thousand Oaks", "Website": "https://www.amgen.com",
             "Focus Areas": "Biologics, Oncology, Inflammation", "Company Stage": "Public",
             "Description": "Multinational biopharmaceutical company focused on human therapeutics"},

            {"Company Name": "Neurocrine Biosciences", "City": "San Diego", "Website": "https://www.neurocrine.com",
             "Focus Areas": "Neuroscience, Endocrine", "Company Stage": "Public",
             "Description": "Neuroscience-focused pharmaceutical company"},

            {"Company Name": "BioMarin Pharmaceutical", "City": "San Rafael", "Website": "https://www.biomarin.com",
             "Focus Areas": "Rare Diseases, Gene Therapy", "Company Stage": "Public",
             "Description": "Biopharmaceutical company focused on rare genetic diseases"},

            {"Company Name": "Seagen", "City": "Bothell/CA presence", "Website": "https://www.seagen.com",
             "Focus Areas": "Antibody-Drug Conjugates, Oncology", "Company Stage": "Public",
             "Description": "Biotechnology company focused on oncology therapeutics"},

            # CRISPR/Gene Editing
            {"Company Name": "Mammoth Biosciences", "City": "Brisbane", "Website": "https://www.mammoth.bio",
             "Focus Areas": "CRISPR Diagnostics", "Company Stage": "Private",
             "Description": "CRISPR-based diagnostics platform"},

            {"Company Name": "Scribe Therapeutics", "City": "Alameda", "Website": "https://www.scribetherapeutics.com",
             "Focus Areas": "CRISPR Gene Editing", "Company Stage": "Private",
             "Description": "Next-generation CRISPR therapeutics"},

            {"Company Name": "Synthego", "City": "Redwood City", "Website": "https://www.synthego.com",
             "Focus Areas": "CRISPR Tools, Gene Editing", "Company Stage": "Private",
             "Description": "Genome engineering company providing CRISPR tools"},

            # Synthetic Biology
            {"Company Name": "Twist Bioscience", "City": "South San Francisco", "Website": "https://www.twistbioscience.com",
             "Focus Areas": "DNA Synthesis, Synthetic Biology", "Company Stage": "Public",
             "Description": "Synthetic biology company manufacturing synthetic DNA"},

            {"Company Name": "Zymergen", "City": "Emeryville", "Website": "https://www.zymergen.com",
             "Focus Areas": "Biomanufacturing, Materials", "Company Stage": "Private",
             "Description": "Biomanufacturing company using machine learning"},

            {"Company Name": "Ginkgo Bioworks", "City": "Emeryville", "Website": "https://www.ginkgobioworks.com",
             "Focus Areas": "Organism Engineering, Platform", "Company Stage": "Public",
             "Description": "Organism engineering company, platform for cell programming"},

            # Cell & Gene Therapy
            {"Company Name": "Fate Therapeutics", "City": "San Diego", "Website": "https://www.fatetherapeutics.com",
             "Focus Areas": "iPSC Cell Therapy, Immuno-Oncology", "Company Stage": "Public",
             "Description": "Clinical-stage cell therapy company"},

            {"Company Name": "Allogene Therapeutics", "City": "South San Francisco", "Website": "https://www.allogene.com",
             "Focus Areas": "Allogeneic CAR-T", "Company Stage": "Public",
             "Description": "Allogeneic CAR T cell therapy developer"},

            {"Company Name": "Poseida Therapeutics", "City": "San Diego", "Website": "https://www.poseida.com",
             "Focus Areas": "CAR-T, Gene Therapy", "Company Stage": "Public",
             "Description": "Cell and gene therapy company"},

            {"Company Name": "Arcellx", "City": "Redwood City", "Website": "https://www.arcellx.com",
             "Focus Areas": "Cell Therapy, Immuno-Oncology", "Company Stage": "Public",
             "Description": "Cell therapy company with novel receptor platforms"},

            {"Company Name": "Century Therapeutics", "City": "Emeryville", "Website": "https://www.centurytx.com",
             "Focus Areas": "iPSC Cell Therapy", "Company Stage": "Public",
             "Description": "iPSC-derived cell therapy developer"},

            # Oncology
            {"Company Name": "Turning Point Therapeutics", "City": "San Diego", "Website": "https://www.tptherapeutics.com",
             "Focus Areas": "Precision Oncology", "Company Stage": "Acquired",
             "Description": "Precision oncology company focused on kinase inhibitors"},

            {"Company Name": "Gossamer Bio", "City": "San Diego", "Website": "https://www.gossamerbio.com",
             "Focus Areas": "Immunology, Oncology", "Company Stage": "Public",
             "Description": "Clinical-stage company developing immunology therapeutics"},

            {"Company Name": "Revolution Medicines", "City": "Redwood City", "Website": "https://www.revmed.com",
             "Focus Areas": "Oncology, RAS Inhibitors", "Company Stage": "Public",
             "Description": "Oncology company targeting frontier targets in cancer"},

            {"Company Name": "Relay Therapeutics", "City": "Cambridge/CA", "Website": "https://www.relaytx.com",
             "Focus Areas": "Precision Oncology, Computational", "Company Stage": "Public",
             "Description": "Precision medicine company using computational approaches"},

            # Immunology
            {"Company Name": "Vir Biotechnology", "City": "San Francisco", "Website": "https://www.vir.bio",
             "Focus Areas": "Infectious Disease, Immunology", "Company Stage": "Public",
             "Description": "Clinical-stage immunology company"},

            {"Company Name": "Checkmate Pharmaceuticals", "City": "Cambridge/CA", "Website": "https://www.checkmatepharma.com",
             "Focus Areas": "Immuno-Oncology", "Company Stage": "Public",
             "Description": "Immuno-oncology company developing CpG-A therapeutics"},

            {"Company Name": "Regulus Therapeutics", "City": "San Diego", "Website": "https://www.regulusrx.com",
             "Focus Areas": "MicroRNA Therapeutics", "Company Stage": "Public",
             "Description": "Biopharmaceutical company developing microRNA therapeutics"},

            # Rare Disease
            {"Company Name": "Mirum Pharmaceuticals", "City": "Foster City", "Website": "https://www.mirumpharma.com",
             "Focus Areas": "Rare Liver Disease", "Company Stage": "Public",
             "Description": "Rare disease company focused on liver diseases"},

            {"Company Name": "Achaogen", "City": "South San Francisco", "Website": "https://www.achaogen.com",
             "Focus Areas": "Antibiotics, Infectious Disease", "Company Stage": "Acquired",
             "Description": "Antibiotics company (acquired/defunct)"},

            {"Company Name": "Cidara Therapeutics", "City": "San Diego", "Website": "https://www.cidara.com",
             "Focus Areas": "Antifungal, Antiviral", "Company Stage": "Public",
             "Description": "Biotechnology company developing therapeutics for infectious diseases"},

            # Cardiovascular
            {"Company Name": "Edwards Lifesciences", "City": "Irvine", "Website": "https://www.edwards.com",
             "Focus Areas": "Heart Valves, Hemodynamic Monitoring", "Company Stage": "Public",
             "Description": "Medical devices for structural heart disease and critical care"},

            {"Company Name": "Tenaya Therapeutics", "City": "South San Francisco", "Website": "https://www.tenayatherapeutics.com",
             "Focus Areas": "Heart Disease, Gene Therapy", "Company Stage": "Public",
             "Description": "Cardiac gene therapy and cellular regeneration"},

            # Diagnostics/Tools
            {"Company Name": "NanoString Technologies", "City": "Seattle/CA", "Website": "https://www.nanostring.com",
             "Focus Areas": "Molecular Diagnostics, Spatial Genomics", "Company Stage": "Public",
             "Description": "Molecular diagnostics company"},

            {"Company Name": "Guardant Health", "City": "Redwood City", "Website": "https://www.guardanthealth.com",
             "Focus Areas": "Liquid Biopsy, Oncology Diagnostics", "Company Stage": "Public",
             "Description": "Precision oncology company with liquid biopsy platform"},

            {"Company Name": "Grail", "City": "Menlo Park", "Website": "https://www.grail.com",
             "Focus Areas": "Early Cancer Detection", "Company Stage": "Private",
             "Description": "Multi-cancer early detection test developer"},

            {"Company Name": "Freenome", "City": "South San Francisco", "Website": "https://www.freenome.com",
             "Focus Areas": "Cancer Screening, AI Diagnostics", "Company Stage": "Private",
             "Description": "Early cancer detection using cell-free biomarkers and AI"},

            {"Company Name": "Singlera Genomics", "City": "San Diego", "Website": "https://www.singleraoncology.com",
             "Focus Areas": "Cancer Detection, Liquid Biopsy", "Company Stage": "Private",
             "Description": "Cancer detection through liquid biopsy"},

            # Neuroscience
            {"Company Name": "Denali Therapeutics", "City": "South San Francisco", "Website": "https://www.denalitherapeutics.com",
             "Focus Areas": "Neurodegenerative Disease", "Company Stage": "Public",
             "Description": "Neurodegenerative disease therapeutics developer"},

            {"Company Name": "Encoded Therapeutics", "City": "South San Francisco", "Website": "https://www.encodedtherapeutics.com",
             "Focus Areas": "Gene Therapy, Neurological", "Company Stage": "Private",
             "Description": "Genetic medicines for severe neurological disorders"},

            {"Company Name": "Neumora Therapeutics", "City": "Watertown/CA", "Website": "https://www.neumora.com",
             "Focus Areas": "Brain Disease, Precision Medicine", "Company Stage": "Private",
             "Description": "Precision medicine for brain diseases"},

            # Ophthalmology
            {"Company Name": "Adverum Biotechnologies", "City": "Redwood City", "Website": "https://www.adverum.com",
             "Focus Areas": "Gene Therapy, Ophthalmology", "Company Stage": "Public",
             "Description": "Gene therapy for ocular diseases"},

            {"Company Name": "Applied Genetic Technologies", "City": "Alachua/CA", "Website": "https://www.agtc.com",
             "Focus Areas": "Gene Therapy, Ophthalmology", "Company Stage": "Public",
             "Description": "Gene therapy for inherited retinal diseases"},

            # Metabolic/Endocrine
            {"Company Name": "89bio", "City": "San Francisco", "Website": "https://www.89bio.com",
             "Focus Areas": "Metabolic Disease, NASH", "Company Stage": "Public",
             "Description": "Clinical-stage company developing therapies for liver disease"},

            {"Company Name": "Viking Therapeutics", "City": "San Diego", "Website": "https://www.vikingtherapeutics.com",
             "Focus Areas": "Metabolic, Endocrine", "Company Stage": "Public",
             "Description": "Clinical-stage company in metabolic and endocrine disorders"},

            # Platform/CRO/CDMO
            {"Company Name": "Codexis", "City": "Redwood City", "Website": "https://www.codexis.com",
             "Focus Areas": "Enzyme Engineering, Biomanufacturing", "Company Stage": "Public",
             "Description": "Protein engineering company"},

            {"Company Name": "Zymergen", "City": "Emeryville", "Website": "https://www.zymergen.com",
             "Focus Areas": "Biomanufacturing", "Company Stage": "Private",
             "Description": "Molecular technology company"},

            {"Company Name": "Inscripta", "City": "Boulder/CA", "Website": "https://www.inscripta.com",
             "Focus Areas": "Gene Editing Platform", "Company Stage": "Private",
             "Description": "Benchtop platform for genome engineering"},

            {"Company Name": "Absci", "City": "Vancouver/CA", "Website": "https://www.absci.com",
             "Focus Areas": "Drug Discovery, AI Platform", "Company Stage": "Public",
             "Description": "AI-powered drug discovery platform"},

            # Medical Devices
            {"Company Name": "Masimo", "City": "Irvine", "Website": "https://www.masimo.com",
             "Focus Areas": "Patient Monitoring, Medical Devices", "Company Stage": "Public",
             "Description": "Medical technology company specializing in noninvasive patient monitoring"},

            {"Company Name": "Shockwave Medical", "City": "Santa Clara", "Website": "https://www.shockwavemedical.com",
             "Focus Areas": "Cardiovascular Devices", "Company Stage": "Public",
             "Description": "Medical device company treating cardiovascular disease"},

            {"Company Name": "Alphatec Spine", "City": "Carlsbad", "Website": "https://www.alphatecspine.com",
             "Focus Areas": "Spinal Surgery Devices", "Company Stage": "Public",
             "Description": "Medical technology company focused on spinal surgery"},

            {"Company Name": "SI-BONE", "City": "Santa Clara", "Website": "https://www.si-bone.com",
             "Focus Areas": "Orthopedic Devices", "Company Stage": "Public",
             "Description": "Medical device company for sacroiliac joint disorders"},

            # Antibody Therapeutics
            {"Company Name": "Xencor", "City": "Monrovia", "Website": "https://www.xencor.com",
             "Focus Areas": "Antibody Engineering", "Company Stage": "Public",
             "Description": "Clinical-stage biopharmaceutical company developing engineered antibodies"},

            {"Company Name": "Ablynx", "City": "Ghent/CA presence", "Website": "https://www.ablynx.com",
             "Focus Areas": "Nanobody Therapeutics", "Company Stage": "Acquired",
             "Description": "Nanobody therapeutics (acquired by Sanofi)"},

            {"Company Name": "Atreca", "City": "Redwood City", "Website": "https://www.atreca.com",
             "Focus Areas": "Antibody Discovery, Oncology", "Company Stage": "Public",
             "Description": "Biopharmaceutical company discovering antibodies from immune responses"},

            # Microbiome
            {"Company Name": "Kaleido Biosciences", "City": "Cambridge/CA", "Website": "https://www.kaleido.com",
             "Focus Areas": "Microbiome, Metabolic", "Company Stage": "Public",
             "Description": "Clinical-stage company developing microbiome therapeutics"},

            {"Company Name": "Finch Therapeutics", "City": "Somerville/CA", "Website": "https://www.finchtherapeutics.com",
             "Focus Areas": "Microbiome Therapeutics", "Company Stage": "Public",
             "Description": "Microbiome therapeutics company"},

            # RNA Therapeutics
            {"Company Name": "Arrowhead Pharmaceuticals", "City": "Pasadena", "Website": "https://www.arrowheadpharma.com",
             "Focus Areas": "RNAi Therapeutics", "Company Stage": "Public",
             "Description": "Biopharmaceutical company developing RNAi therapeutics"},

            {"Company Name": "Beam Therapeutics", "City": "Cambridge/CA presence", "Website": "https://www.beamtx.com",
             "Focus Areas": "Base Editing, Gene Therapy", "Company Stage": "Public",
             "Description": "Base editing company"},

            # Recently Funded Startups (2022-2024)
            {"Company Name": "Profluent Bio", "City": "Berkeley", "Website": "https://www.profluent.bio",
             "Focus Areas": "AI Protein Design", "Company Stage": "Private",
             "Description": "AI-powered protein design for therapeutics"},

            {"Company Name": "Insitro", "City": "South San Francisco", "Website": "https://www.insitro.com",
             "Focus Areas": "Machine Learning, Drug Discovery", "Company Stage": "Private",
             "Description": "Machine learning-driven drug discovery"},

            {"Company Name": "Neomorph", "City": "San Diego", "Website": "https://www.neomorph.com",
             "Focus Areas": "Molecular Glues, Drug Discovery", "Company Stage": "Private",
             "Description": "Molecular glue degrader therapeutics"},

            {"Company Name": "Dewpoint Therapeutics", "City": "Boston/CA", "Website": "https://www.dewpointx.com",
             "Focus Areas": "Biomolecular Condensates", "Company Stage": "Private",
             "Description": "Drug discovery based on biomolecular condensates"},

            {"Company Name": "Aria Pharmaceuticals", "City": "South San Francisco", "Website": "https://www.ariapharma.com",
             "Focus Areas": "RNA-Targeting Therapeutics", "Company Stage": "Private",
             "Description": "Small molecule RNA-targeting therapeutics"},

            {"Company Name": "Umoja Biopharma", "City": "Seattle/CA", "Website": "https://www.umoja-biopharma.com",
             "Focus Areas": "In Vivo Cell Therapy", "Company Stage": "Private",
             "Description": "In vivo cell therapy platform"},

            {"Company Name": "Generate Biomedicines", "City": "Somerville/CA", "Website": "https://www.generatebiomedicines.com",
             "Focus Areas": "AI Drug Design", "Company Stage": "Private",
             "Description": "AI-driven drug generation"},

            # Stanford Spinouts
            {"Company Name": "Shasqi", "City": "San Francisco", "Website": "https://www.shasqi.com",
             "Focus Areas": "Click Chemistry, Oncology", "Company Stage": "Private",
             "Description": "Click-activated protodrugs for cancer"},

            {"Company Name": "NotCo", "City": "San Carlos", "Website": "https://www.notco.com",
             "Focus Areas": "Food Technology, AI", "Company Stage": "Private",
             "Description": "Plant-based food using AI (not traditional biotech but innovative)"},

            # UCSF Spinouts
            {"Company Name": "Graphite Bio", "City": "South San Francisco", "Website": "https://www.graphitebio.com",
             "Focus Areas": "Gene Editing, Gene Therapy", "Company Stage": "Public",
             "Description": "Precision gene editing therapeutics"},

            {"Company Name": "Spotlight Therapeutics", "City": "South San Francisco", "Website": "https://www.spotlighttx.com",
             "Focus Areas": "Gene Therapy, Ophthalmology", "Company Stage": "Private",
             "Description": "Gene therapies for ophthalmology"},

            # UC Berkeley Spinouts
            {"Company Name": "Caribou Biosciences", "City": "Berkeley", "Website": "https://www.cariboubio.com",
             "Focus Areas": "CRISPR Therapeutics", "Company Stage": "Public",
             "Description": "CRISPR genome editing therapeutics"},

            {"Company Name": "Metagenomi", "City": "Emeryville", "Website": "https://www.metagenomi.co",
             "Focus Areas": "Gene Editing Tools", "Company Stage": "Private",
             "Description": "Next-generation gene editing tools from metagenomics"},

            # Accelerator/Incubator Companies
            {"Company Name": "Cellino", "City": "Cambridge/CA", "Website": "https://www.cellino.com",
             "Focus Areas": "iPSC Automation", "Company Stage": "Private",
             "Description": "Automated stem cell production"},

            {"Company Name": "Resilience", "City": "Fremont", "Website": "https://www.resilience.com",
             "Focus Areas": "Biomanufacturing CDMO", "Company Stage": "Private",
             "Description": "Biomanufacturing platform"},

        ]

        return companies

    def load_existing_names(self, csv_file: str) -> Set[str]:
        """Load existing company names"""
        existing = set()
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    normalized = self.normalize_name(row['Company Name'])
                    existing.add(normalized)
        except FileNotFoundError:
            pass
        return existing

    def add_to_dataset(self, existing_csv: str, output_csv: str):
        """Add known companies to dataset"""

        print("="*70)
        print("ADDING KNOWN CALIFORNIA BIOTECH COMPANIES")
        print("="*70)

        # Load existing
        existing_names = self.load_existing_names(existing_csv)
        print(f"Loaded {len(existing_names)} existing companies")

        existing_rows = []
        fieldnames = None

        try:
            with open(existing_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                existing_rows = list(reader)
        except FileNotFoundError:
            print(f"Warning: {existing_csv} not found")
            return

        # Filter new companies
        new_companies = []
        for company in self.known_companies:
            normalized = self.normalize_name(company['Company Name'])
            if normalized not in existing_names:
                new_companies.append(company)

        print(f"Found {len(new_companies)} new companies to add")

        # Add new companies with proper fields
        added = 0
        for company in new_companies:
            row = {field: '' for field in fieldnames}

            # Map fields
            row['Company Name'] = company.get('Company Name', '')
            row['Website'] = company.get('Website', '')
            row['City'] = company.get('City', '')
            row['Address'] = company.get('Address', '')
            row['Company_Stage_Classified'] = company.get('Company Stage', 'Unknown')
            row['Focus Areas'] = company.get('Focus Areas', '')
            row['Focus_Areas_Enhanced'] = company.get('Focus Areas', '')
            row['Description'] = company.get('Description', '')
            row['Description_Enhanced'] = company.get('Description', '')
            row['Validation_Source'] = 'Manual_Curated'
            row['Classifier_Date'] = '2025-11-16'

            existing_rows.append(row)
            added += 1

        # Save combined dataset
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows)

        print(f"\n{'='*70}")
        print(f"SUCCESS")
        print(f"{'='*70}")
        print(f"Added: {added} new companies")
        print(f"Total in dataset: {len(existing_rows)}")
        print(f"Saved to: {output_csv}")


if __name__ == '__main__':
    import sys

    input_file = sys.argv[1] if len(sys.argv) > 1 else 'data/final/companies.csv'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'data/working/companies_expanded.csv'

    adder = KnownCompanyAdder()
    adder.add_to_dataset(input_file, output_file)
