#!/usr/bin/env python3
"""
Autonomous Dataset Expansion and Quality Improvement
Orchestrates all data improvement activities
"""

import os
import sys
import csv
import json
from typing import List, Dict
import subprocess
import time
from datetime import datetime

class AutonomousDatasetManager:
    def __init__(self, base_dir: str = '.'):
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, 'data')
        self.final_dir = os.path.join(self.data_dir, 'final')
        self.working_dir = os.path.join(self.data_dir, 'working')
        self.current_csv = os.path.join(self.final_dir, 'companies.csv')

        # Ensure directories exist
        os.makedirs(self.working_dir, exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def run_quality_analysis(self) -> Dict:
        """Run initial quality analysis"""
        self.log("Running quality analysis...")

        try:
            result = subprocess.run(
                ['python3', 'analyze_data_quality.py', self.current_csv],
                capture_output=True,
                text=True,
                timeout=60
            )

            print(result.stdout)
            if result.stderr:
                print("Warnings:", result.stderr)

            return {'success': True}

        except Exception as e:
            self.log(f"Error in quality analysis: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}

    def expand_from_apis(self) -> int:
        """Expand dataset using public APIs"""
        self.log("Expanding dataset from public APIs...")

        try:
            result = subprocess.run(
                ['python3', 'expand_dataset_api.py'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            print(result.stdout)

            # Count companies in output file
            api_file = os.path.join(self.working_dir, 'api_companies.csv')
            if os.path.exists(api_file):
                with open(api_file, 'r', encoding='utf-8') as f:
                    count = sum(1 for _ in f) - 1  # Subtract header
                    self.log(f"Found {count} new companies from APIs")
                    return count

        except subprocess.TimeoutExpired:
            self.log("API expansion timed out", "WARNING")
        except Exception as e:
            self.log(f"Error in API expansion: {str(e)}", "ERROR")

        return 0

    def merge_new_companies(self, source_file: str) -> int:
        """Merge new companies into main dataset"""
        self.log(f"Merging companies from {source_file}...")

        if not os.path.exists(source_file):
            self.log(f"Source file not found: {source_file}", "WARNING")
            return 0

        # Load existing companies
        existing = []
        with open(self.current_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing = list(reader)
            existing_fieldnames = reader.fieldnames

        # Load new companies
        new_companies = []
        with open(source_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            new_companies = list(reader)

        self.log(f"Loaded {len(existing)} existing, {len(new_companies)} new companies")

        # Merge - add required fields to new companies
        merged_count = 0
        for company in new_companies:
            # Fill in missing fields with defaults
            merged_company = {field: '' for field in existing_fieldnames}

            # Copy available fields
            for key, value in company.items():
                if key in merged_company:
                    merged_company[key] = value

            # Set defaults for specific fields
            merged_company['Company_Stage_Classified'] = company.get('Company Stage', 'Unknown')
            merged_company['Validation_Source'] = company.get('Source', 'API')
            merged_company['Classifier_Date'] = datetime.now().strftime('%Y-%m-%d')

            existing.append(merged_company)
            merged_count += 1

        # Save merged dataset
        backup_file = os.path.join(self.working_dir, f'companies_backup_{int(time.time())}.csv')
        os.rename(self.current_csv, backup_file)
        self.log(f"Backed up existing data to {backup_file}")

        with open(self.current_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=existing_fieldnames)
            writer.writeheader()
            writer.writerows(existing)

        self.log(f"Merged {merged_count} new companies")
        return merged_count

    def geocode_missing(self) -> int:
        """Geocode companies missing coordinates"""
        self.log("Geocoding companies with missing coordinates...")

        try:
            # Check if we have Google API key
            api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
            if not api_key:
                self.log("No Google Maps API key found - skipping geocoding", "WARNING")
                return 0

            result = subprocess.run(
                ['python3', 'improved_geocoder.py',
                 self.current_csv,
                 os.path.join(self.working_dir, 'companies_geocoded.csv')],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )

            print(result.stdout)

            # Replace current file with geocoded version
            geocoded_file = os.path.join(self.working_dir, 'companies_geocoded.csv')
            if os.path.exists(geocoded_file):
                os.replace(geocoded_file, self.current_csv)
                self.log("Geocoding complete - updated main dataset")
                return 1

        except subprocess.TimeoutExpired:
            self.log("Geocoding timed out", "WARNING")
        except Exception as e:
            self.log(f"Error in geocoding: {str(e)}", "ERROR")

        return 0

    def generate_manual_expansion_list(self, target: int = 500) -> str:
        """Generate list of high-priority companies to add manually"""
        self.log(f"Generating list of {target} high-priority companies to research...")

        manual_list = []

        # California biotech hubs and known companies
        priority_companies = [
            # San Francisco Bay Area
            {"name": "Ginkgo Bioworks", "city": "Boston/CA presence"},
            {"name": "Zymergen", "city": "Emeryville"},
            {"name": "Twist Bioscience", "city": "South San Francisco"},
            {"name": "Mammoth Biosciences", "city": "Brisbane"},
            {"name": "Synthego", "city": "Redwood City"},
            {"name": "Scribe Therapeutics", "city": "Alameda"},
            {"name": "Encoded Therapeutics", "city": "South San Francisco"},
            {"name": "Vir Biotechnology", "city": "San Francisco"},
            {"name": "Verve Therapeutics", "city": "San Francisco"},
            {"name": "Century Therapeutics", "city": "Emeryville"},

            # San Diego
            {"name": "Fate Therapeutics", "city": "San Diego"},
            {"name": "Arena Pharmaceuticals", "city": "San Diego"},
            {"name": "Cidara Therapeutics", "city": "San Diego"},
            {"name": "Gossamer Bio", "city": "San Diego"},
            {"name": "Turning Point Therapeutics", "city": "San Diego"},
            {"name": "Beam Therapeutics", "city": "San Diego presence"},
            {"name": "Mirum Pharmaceuticals", "city": "Foster City"},

            # LA/Orange County
            {"name": "Kite Pharma", "city": "Santa Monica"},
            {"name": "Amgen", "city": "Thousand Oaks"},
            {"name": "Edwards Lifesciences", "city": "Irvine"},
            {"name": "Masimo", "city": "Irvine"},

            # Add research institutions' spinouts
            {"name": "Stanford Spinouts", "city": "Palo Alto", "note": "Research top Stanford biotech spinouts"},
            {"name": "UC Berkeley Spinouts", "city": "Berkeley", "note": "Research UC Berkeley biotech spinouts"},
            {"name": "UCSF Spinouts", "city": "San Francisco", "note": "Research UCSF biotech spinouts"},
            {"name": "Caltech Spinouts", "city": "Pasadena", "note": "Research Caltech biotech spinouts"},
        ]

        output_file = os.path.join(self.working_dir, 'manual_expansion_targets.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("MANUAL DATASET EXPANSION - PRIORITY TARGETS\n")
            f.write("="*70 + "\n\n")

            f.write("High-priority companies to research and add:\n\n")

            for idx, company in enumerate(priority_companies, 1):
                f.write(f"{idx}. {company['name']} ({company['city']})\n")
                if 'note' in company:
                    f.write(f"   Note: {company['note']}\n")
                f.write("\n")

            f.write("\n" + "="*70 + "\n")
            f.write("RESEARCH CATEGORIES FOR ADDITIONAL COMPANIES:\n")
            f.write("="*70 + "\n\n")

            categories = [
                "1. CRISPR/Gene Editing Companies in California",
                "2. Cell Therapy Companies in California",
                "3. Synthetic Biology Startups",
                "4. Precision Medicine/Diagnostics",
                "5. Agricultural Biotech (AgTech)",
                "6. Biotech Manufacturing/CRO/CDMO",
                "7. Bioinformatics/Computational Biology",
                "8. Medical Device Companies",
                "9. Recently funded biotech startups (2022-2025)",
                "10. University spinouts (Stanford, Berkeley, UCSF, UCLA, UCSD, Caltech)",
            ]

            for category in categories:
                f.write(category + "\n")

            f.write("\n" + "="*70 + "\n")
            f.write("DATA SOURCES TO CHECK:\n")
            f.write("="*70 + "\n\n")

            sources = [
                "- California Life Sciences Association (CLSA) member directory",
                "- Biocom California member directory",
                "- Golden Ticket Awards nominees (SF/Bay Area biotech)",
                "- JPM Healthcare Conference attendees (California companies)",
                "- BIO International Convention exhibitors",
                "- Y Combinator biotech startups",
                "- IndieBio accelerator portfolio",
                "- Berkeley SkyDeck biotech companies",
                "- UCSF QB3 incubator companies",
                "- Illumina Accelerator portfolio",
                "- Johnson & Johnson Innovation JLABS residents",
                "- Recent FDA approvals (California sponsors)",
                "- NIH SBIR/STTR awardees (California)",
            ]

            for source in sources:
                f.write(source + "\n")

        self.log(f"Generated manual expansion list: {output_file}")
        return output_file

    def enhance_descriptions(self) -> int:
        """Enhance company descriptions using web scraping"""
        self.log("Enhancing company descriptions...")

        # Count companies missing descriptions
        companies = []
        with open(self.current_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            companies = list(reader)

        missing_desc = [c for c in companies
                       if not c.get('Description_Enhanced') and not c.get('Description')]

        self.log(f"Found {len(missing_desc)} companies missing descriptions")

        # This would implement web scraping of company websites
        # For now, we'll note it as a manual task

        return len(missing_desc)

    def generate_final_report(self):
        """Generate final quality report"""
        self.log("Generating final report...")

        report_file = os.path.join(self.working_dir, 'final_report.txt')

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("CALIFORNIA BIOTECH DATASET - FINAL REPORT\n")
            f.write("="*70 + "\n")
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Run quality analysis and append to report
        subprocess.run(
            ['python3', 'analyze_data_quality.py', self.current_csv],
            stdout=open(report_file, 'a'),
            stderr=subprocess.STDOUT
        )

        self.log(f"Final report saved to: {report_file}")
        return report_file


def main():
    """Main autonomous execution"""
    print("\n" + "="*70)
    print("AUTONOMOUS CALIFORNIA BIOTECH DATASET EXPANSION")
    print("="*70)
    print()

    manager = AutonomousDatasetManager()

    # Phase 1: Initial Analysis
    print("\n### PHASE 1: QUALITY ANALYSIS ###\n")
    manager.run_quality_analysis()

    # Phase 2: Expand from APIs
    print("\n### PHASE 2: API-BASED EXPANSION ###\n")
    api_count = manager.expand_from_apis()

    # Phase 3: Merge new companies
    if api_count > 0:
        print("\n### PHASE 3: MERGING NEW COMPANIES ###\n")
        api_file = os.path.join(manager.working_dir, 'api_companies.csv')
        merged = manager.merge_new_companies(api_file)
        print(f"Merged {merged} new companies")

    # Phase 4: Geocode missing
    print("\n### PHASE 4: GEOCODING ###\n")
    if os.environ.get('GOOGLE_MAPS_API_KEY'):
        manager.geocode_missing()
    else:
        print("Skipping geocoding - no API key available")

    # Phase 5: Generate manual expansion targets
    print("\n### PHASE 5: MANUAL EXPANSION GUIDANCE ###\n")
    manager.generate_manual_expansion_list()

    # Phase 6: Final Report
    print("\n### PHASE 6: FINAL REPORT ###\n")
    report = manager.generate_final_report()

    print("\n" + "="*70)
    print("AUTONOMOUS EXPANSION COMPLETE")
    print("="*70)
    print(f"\nFinal report: {report}")
    print("\nNext steps:")
    print("1. Review data/working/manual_expansion_targets.txt")
    print("2. Manually research and add high-priority companies")
    print("3. Run validation on new entries")
    print("4. Continue until reaching 2000 companies")


if __name__ == '__main__':
    main()
