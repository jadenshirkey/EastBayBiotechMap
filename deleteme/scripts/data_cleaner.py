#!/usr/bin/env python3
"""
Data Cleaning Pipeline for East Bay Biotech Map
Standardizes, deduplicates, and validates company data
Implements quality scoring and prepares for final output
"""

import csv
import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/deleteme/logs/data_cleaner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataCleaner:
    """Comprehensive data cleaning and standardization pipeline"""

    # Legal suffixes to handle
    LEGAL_SUFFIXES = [
        'Inc.', 'Inc', 'Incorporated',
        'Corp.', 'Corp', 'Corporation',
        'LLC', 'L.L.C.', 'Limited Liability Company',
        'Ltd.', 'Ltd', 'Limited',
        'LP', 'L.P.', 'Limited Partnership',
        'LLP', 'L.L.P.',
        'Co.', 'Co', 'Company'
    ]

    # Common abbreviations to expand
    ABBREVIATIONS = {
        'Rx': 'Therapeutics',
        'Bio': 'Biosciences',
        'Pharma': 'Pharmaceuticals',
        'Tech': 'Technologies',
        'Lab': 'Laboratories',
        'Intl': 'International',
        'Natl': 'National',
        'Assoc': 'Associates',
        'Svcs': 'Services',
        'Mfg': 'Manufacturing'
    }

    # City name standardization
    CITY_MAPPING = {
        'SF': 'San Francisco',
        'S.F.': 'San Francisco',
        'South SF': 'South San Francisco',
        'S. San Francisco': 'South San Francisco',
        'SSF': 'South San Francisco',
        'LA': 'Los Angeles',
        'L.A.': 'Los Angeles',
        'SD': 'San Diego',
        'Berkeley': 'Berkeley',
        'Bezerkeley': 'Berkeley',  # Common misspelling
        'Foster': 'Foster City',
        'Menlo': 'Menlo Park',
        'Mtn View': 'Mountain View',
        'Mt View': 'Mountain View',
        'Mt. View': 'Mountain View'
    }

    # State standardization
    STATE_MAPPING = {
        'California': 'CA',
        'Calif.': 'CA',
        'Calif': 'CA',
        'Cal': 'CA'
    }

    def __init__(self):
        self.duplicate_groups = []
        self.quality_scores = {}
        self.cleaning_stats = defaultdict(int)

    def clean_company_data(self, row: Dict) -> Dict:
        """Clean and standardize all fields in a company record"""
        cleaned = row.copy()

        # Clean company name
        cleaned['Company Name'] = self._clean_company_name(row.get('Company Name', ''))
        cleaned['Display_Name'] = self._create_display_name(cleaned['Company Name'])

        # Clean location fields
        cleaned['City'] = self._standardize_city(row.get('City', ''))
        # Only add State field if it exists in input
        if 'State' in row:
            cleaned['State'] = self._standardize_state(row.get('State', 'CA'))

        # Clean and parse address
        if row.get('Google_Address'):
            parsed = self._parse_address(row['Google_Address'])
            cleaned.update(parsed)

        # Clean website
        cleaned['Website'] = self._clean_website(row.get('Website', ''))

        # Ensure consistent stage naming
        if 'Company_Stage_Classified' in cleaned:
            cleaned['Company_Stage_Classified'] = self._standardize_stage(
                cleaned['Company_Stage_Classified']
            )

        # Calculate quality score
        quality_score = self._calculate_quality_score(cleaned)
        cleaned['Quality_Score'] = quality_score
        self.quality_scores[cleaned['Company Name']] = quality_score

        return cleaned

    def _clean_company_name(self, name: str) -> str:
        """Clean and standardize company name"""
        if not name:
            return ''

        # Remove extra whitespace
        name = ' '.join(name.split())

        # Preserve original case for proper nouns
        # but standardize legal suffixes
        for suffix in self.LEGAL_SUFFIXES:
            pattern = r'\b' + re.escape(suffix) + r'\.?$'
            if re.search(pattern, name, re.IGNORECASE):
                name = re.sub(pattern, '', name, flags=re.IGNORECASE).strip()
                # Store legal suffix separately if needed
                break

        self.cleaning_stats['names_cleaned'] += 1
        return name

    def _create_display_name(self, name: str) -> str:
        """Create a clean display name for UI"""
        if not name:
            return ''

        # Expand common abbreviations
        display = name
        for abbr, full in self.ABBREVIATIONS.items():
            pattern = r'\b' + re.escape(abbr) + r'\b'
            display = re.sub(pattern, full, display, flags=re.IGNORECASE)

        return display

    def _standardize_city(self, city: str) -> str:
        """Standardize city names"""
        if not city:
            return ''

        city = city.strip()

        # Check mapping first
        for variant, standard in self.CITY_MAPPING.items():
            if city.lower() == variant.lower():
                self.cleaning_stats['cities_standardized'] += 1
                return standard

        # Title case for unmapped cities
        return city.title()

    def _standardize_state(self, state: str) -> str:
        """Standardize state to 2-letter code"""
        if not state:
            return 'CA'  # Default to California

        state = state.strip()

        # Check mapping
        for variant, standard in self.STATE_MAPPING.items():
            if state.lower() == variant.lower():
                return standard

        # Already 2-letter code?
        if len(state) == 2 and state.upper() == 'CA':
            return 'CA'

        return state.upper()[:2]

    def _parse_address(self, address: str) -> Dict:
        """Parse address into components"""
        parsed = {}

        if not address:
            return parsed

        # Common Google Maps address format: "street, city, state zip, country"
        parts = address.split(',')

        if len(parts) >= 3:
            parsed['Street_Address'] = parts[0].strip()
            parsed['City_Parsed'] = parts[1].strip()

            # Parse state and zip from third part
            state_zip = parts[2].strip()
            match = re.match(r'([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', state_zip)
            if match:
                parsed['State_Parsed'] = match.group(1)
                parsed['Zip_Code'] = match.group(2)
            else:
                parsed['State_Parsed'] = 'CA'

        self.cleaning_stats['addresses_parsed'] += 1
        return parsed

    def _clean_website(self, website: str) -> str:
        """Clean and standardize website URLs"""
        if not website:
            return ''

        website = website.strip()

        # Ensure protocol
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website

        # Remove trailing slashes
        website = website.rstrip('/')

        # Basic validation
        if '.' not in website:
            return ''

        self.cleaning_stats['websites_cleaned'] += 1
        return website

    def _standardize_stage(self, stage: str) -> str:
        """Ensure consistent stage naming"""
        stage_mapping = {
            'preclinical': 'Preclinical',
            'phase i': 'Phase I',
            'phase 1': 'Phase I',
            'phase ii': 'Phase II',
            'phase 2': 'Phase II',
            'phase iii': 'Phase III',
            'phase 3': 'Phase III',
            'commercial': 'Commercial',
            'platform': 'Platform',
            'public': 'Public',
            'ipo': 'IPO',
            'acquired': 'Acquired',
            'unknown': 'Unknown'
        }

        stage_lower = stage.lower().strip()
        return stage_mapping.get(stage_lower, stage)

    def _calculate_quality_score(self, row: Dict) -> float:
        """Calculate data quality score (0-100)"""
        score = 0.0
        weights = {
            'name': 10,
            'city': 10,
            'address': 15,
            'website': 10,
            'stage': 20,
            'description': 10,
            'focus_areas': 10,
            'confidence': 10,
            'coordinates': 5
        }

        # Check required fields
        if row.get('Company Name'):
            score += weights['name']

        if row.get('City'):
            score += weights['city']

        if row.get('Google_Address') or row.get('Address'):
            score += weights['address']

        if row.get('Website'):
            score += weights['website']

        if row.get('Company_Stage_Classified') and row.get('Company_Stage_Classified') != 'Unknown':
            score += weights['stage']

        if row.get('Description'):
            score += weights['description']

        if row.get('Focus Areas'):
            score += weights['focus_areas']

        # Confidence score contribution
        if row.get('Stage_Confidence'):
            try:
                conf = float(row['Stage_Confidence'])
                score += weights['confidence'] * conf
            except:
                pass

        # Coordinates present
        if row.get('Latitude') and row.get('Longitude'):
            score += weights['coordinates']

        return round(score, 2)

    def detect_duplicates(self, companies: List[Dict]) -> List[List[int]]:
        """Detect duplicate companies"""
        duplicate_groups = []
        seen = {}

        for idx, company in enumerate(companies):
            # Create signature for matching
            name_key = self._normalize_for_matching(company.get('Company Name', ''))

            if name_key in seen:
                # Found duplicate
                group_idx = seen[name_key]
                duplicate_groups[group_idx].append(idx)
                self.cleaning_stats['duplicates_found'] += 1
            else:
                # New company
                seen[name_key] = len(duplicate_groups)
                duplicate_groups.append([idx])

        # Filter out single-company groups
        self.duplicate_groups = [g for g in duplicate_groups if len(g) > 1]
        return self.duplicate_groups

    def _normalize_for_matching(self, name: str) -> str:
        """Normalize company name for duplicate detection"""
        if not name:
            return ''

        # Remove legal suffixes and punctuation
        normalized = name.lower()
        for suffix in self.LEGAL_SUFFIXES:
            normalized = normalized.replace(suffix.lower(), '')

        # Remove non-alphanumeric
        normalized = re.sub(r'[^a-z0-9]', '', normalized)

        return normalized

    def merge_duplicates(self, companies: List[Dict]) -> List[Dict]:
        """Merge duplicate company records"""
        if not self.duplicate_groups:
            return companies

        merged = []
        processed_indices = set()

        for group in self.duplicate_groups:
            # Merge records in this group
            merged_record = self._merge_company_group(
                [companies[i] for i in group]
            )
            merged.append(merged_record)
            processed_indices.update(group)
            self.cleaning_stats['companies_merged'] += len(group) - 1

        # Add non-duplicate companies
        for idx, company in enumerate(companies):
            if idx not in processed_indices:
                merged.append(company)

        logger.info(f"Merged {len(companies)} records into {len(merged)}")
        return merged

    def _merge_company_group(self, group: List[Dict]) -> Dict:
        """Merge a group of duplicate companies"""
        # Start with the record with highest quality score
        group.sort(key=lambda x: self.quality_scores.get(x.get('Company Name', ''), 0), reverse=True)
        merged = group[0].copy()

        # Merge fields from other records
        for record in group[1:]:
            for field, value in record.items():
                # Skip if field already has value
                if merged.get(field):
                    continue
                # Add missing fields
                if value and value != 'Unknown':
                    merged[field] = value

        # Recalculate quality score
        merged['Quality_Score'] = self._calculate_quality_score(merged)
        merged['Data_Sources'] = len(group)  # Track merge count

        return merged

    def process_csv(self, input_file: str, output_file: str):
        """Process CSV with full cleaning pipeline"""
        logger.info(f"Starting data cleaning pipeline for {input_file}")

        # Read all companies
        companies = []
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

            for row in reader:
                cleaned = self.clean_company_data(row)
                companies.append(cleaned)

        logger.info(f"Cleaned {len(companies)} company records")

        # Detect and merge duplicates
        self.detect_duplicates(companies)
        if self.duplicate_groups:
            logger.info(f"Found {len(self.duplicate_groups)} duplicate groups")
            companies = self.merge_duplicates(companies)

        # Sort by quality score (highest first)
        companies.sort(key=lambda x: x.get('Quality_Score', 0), reverse=True)

        # Add additional fields for output
        output_fields = list(fieldnames)
        new_fields = ['Display_Name', 'Quality_Score', 'Data_Sources',
                     'Street_Address', 'City_Parsed', 'State_Parsed', 'Zip_Code']

        for field in new_fields:
            if field not in output_fields:
                output_fields.append(field)

        # Write cleaned data
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_fields)
            writer.writeheader()

            for company in companies:
                writer.writerow(company)

        # Generate cleaning report
        self._generate_report(len(companies))

        logger.info(f"Data cleaning complete. Output saved to {output_file}")

    def _generate_report(self, total_companies: int):
        """Generate data cleaning report"""
        report_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/deleteme/reports/cleaning_report.md'

        # Calculate quality score statistics
        scores = list(self.quality_scores.values())
        avg_score = sum(scores) / len(scores) if scores else 0
        high_quality = len([s for s in scores if s >= 85])
        medium_quality = len([s for s in scores if 50 <= s < 85])
        low_quality = len([s for s in scores if s < 50])

        with open(report_file, 'w') as f:
            f.write("# Data Cleaning Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Summary\n\n")
            f.write(f"- Companies Processed: {total_companies}\n")
            f.write(f"- Duplicates Found: {self.cleaning_stats['duplicates_found']}\n")
            f.write(f"- Companies Merged: {self.cleaning_stats['companies_merged']}\n")
            f.write(f"- Final Count: {total_companies}\n\n")

            f.write("## Cleaning Operations\n\n")
            f.write(f"- Names Cleaned: {self.cleaning_stats['names_cleaned']}\n")
            f.write(f"- Cities Standardized: {self.cleaning_stats['cities_standardized']}\n")
            f.write(f"- Addresses Parsed: {self.cleaning_stats['addresses_parsed']}\n")
            f.write(f"- Websites Cleaned: {self.cleaning_stats['websites_cleaned']}\n\n")

            f.write("## Quality Score Distribution\n\n")
            f.write(f"- Average Score: {avg_score:.1f}/100\n")
            f.write(f"- High Quality (85+): {high_quality} ({high_quality/total_companies*100:.1f}%)\n")
            f.write(f"- Medium Quality (50-84): {medium_quality} ({medium_quality/total_companies*100:.1f}%)\n")
            f.write(f"- Low Quality (<50): {low_quality} ({low_quality/total_companies*100:.1f}%)\n\n")

            f.write("## Data Improvements\n\n")
            f.write("- Standardized city names for consistency\n")
            f.write("- Parsed addresses into components\n")
            f.write("- Cleaned and validated websites\n")
            f.write("- Merged duplicate entries\n")
            f.write("- Added quality scoring for prioritization\n")

        logger.info(f"Cleaning report saved to {report_file}")

def main():
    """Main execution"""
    cleaner = DataCleaner()

    # Use enhanced classified data as input
    input_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/data/working/companies_enhanced_v2.csv'
    output_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/data/working/companies_cleaned.csv'

    try:
        cleaner.process_csv(input_file, output_file)

        # Log summary statistics
        logger.info("\nCleaning Statistics:")
        for stat, count in cleaner.cleaning_stats.items():
            logger.info(f"  {stat}: {count}")

    except Exception as e:
        logger.error(f"Error during data cleaning: {e}")
        raise

if __name__ == "__main__":
    main()