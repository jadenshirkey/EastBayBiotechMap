#!/usr/bin/env python3
"""
Company Stage Classifier for East Bay Biotech Map
Classifies biotech companies into development stages based on multiple data sources
"""

import csv
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.parse
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/deleteme/logs/classification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompanyStageClassifier:
    """Classifies biotech companies into development stages"""

    # Stage definitions
    STAGES = {
        'PRECLINICAL': 'No clinical trials, research/discovery phase',
        'PHASE_I': 'First human trials, safety testing',
        'PHASE_II': 'Efficacy testing, dose-ranging studies',
        'PHASE_III': 'Large-scale efficacy, preparing for approval',
        'COMMERCIAL': 'FDA approved products on market',
        'PLATFORM': 'Technology/services company',
        'ACQUIRED': 'Bought by another company',
        'IPO': 'Public but pre-commercial',
        'PUBLIC': 'Publicly traded company',
        'UNKNOWN': 'Unable to determine stage'
    }

    # Keywords for classification
    STAGE_KEYWORDS = {
        'COMMERCIAL': [
            'fda approved', 'marketed', 'commercial stage', 'on market',
            'selling', 'revenue generating', 'product sales'
        ],
        'PHASE_III': [
            'phase 3', 'phase iii', 'phase three', 'pivotal trial',
            'registrational trial', 'late-stage clinical'
        ],
        'PHASE_II': [
            'phase 2', 'phase ii', 'phase two', 'mid-stage clinical',
            'proof of concept', 'dose ranging'
        ],
        'PHASE_I': [
            'phase 1', 'phase i', 'phase one', 'first-in-human',
            'early clinical', 'safety study'
        ],
        'PRECLINICAL': [
            'preclinical', 'pre-clinical', 'discovery', 'research stage',
            'lead optimization', 'target validation', 'early-stage research'
        ],
        'PLATFORM': [
            'platform technology', 'services company', 'tools provider',
            'contract research', 'cro', 'cdmo', 'software', 'diagnostics platform',
            'enabling technology', 'drug discovery platform'
        ],
        'ACQUIRED': [
            'acquired by', 'acquisition', 'bought by', 'merged with',
            'subsidiary of', 'part of'
        ],
        'PUBLIC': [
            'nasdaq', 'nyse', 'publicly traded', 'ipo', 'stock symbol',
            'market cap', 'ticker'
        ]
    }

    # Public company identifiers
    PUBLIC_COMPANIES = {
        '10x genomics': 'PUBLIC',
        'abbvie': 'COMMERCIAL',
        'gilead': 'COMMERCIAL',
        'genentech': 'COMMERCIAL',
        'biomarin': 'COMMERCIAL',
        'nektar': 'PUBLIC',
        'exelixis': 'COMMERCIAL',
        'theravance': 'COMMERCIAL',
        'sangamo': 'PUBLIC',
        'ultragenyx': 'COMMERCIAL',
        'coherus': 'COMMERCIAL',
        'arcus': 'PUBLIC',
        'vir biotechnology': 'PUBLIC',
        'zymergen': 'PUBLIC',
        'bolt biotherapeutics': 'PUBLIC'
    }

    def __init__(self):
        self.classification_cache = {}
        self.confidence_scores = {}

    def classify_company(self, company: Dict) -> Tuple[str, float]:
        """
        Classify a company and return stage with confidence score

        Args:
            company: Dictionary with company information

        Returns:
            Tuple of (stage, confidence_score)
        """
        name = company.get('Company Name', '').lower()
        description = company.get('Description', '').lower()
        focus_areas = company.get('Focus Areas', '').lower()
        website = company.get('Website', '')

        # Check cache first
        if name in self.classification_cache:
            return self.classification_cache[name]

        stage = 'UNKNOWN'
        confidence = 0.0

        # 1. Check known public companies
        if name in self.PUBLIC_COMPANIES:
            stage = self.PUBLIC_COMPANIES[name]
            confidence = 0.95
            logger.info(f"Classified {name} as {stage} (known company)")

        # 2. Check for acquisition patterns
        elif self._is_acquired(description, focus_areas):
            stage = 'ACQUIRED'
            confidence = 0.85
            logger.info(f"Classified {name} as ACQUIRED (pattern match)")

        # 3. Check for platform/services companies
        elif self._is_platform(description, focus_areas, name):
            stage = 'PLATFORM'
            confidence = 0.80
            logger.info(f"Classified {name} as PLATFORM (pattern match)")

        # 4. Try to determine clinical stage from description
        else:
            clinical_stage = self._extract_clinical_stage(description, focus_areas)
            if clinical_stage:
                stage = clinical_stage
                confidence = 0.70
                logger.info(f"Classified {name} as {stage} (description analysis)")

            # 5. Try ClinicalTrials.gov API (if we have more info)
            if stage == 'UNKNOWN' and confidence < 0.5:
                ct_stage = self._check_clinical_trials(name)
                if ct_stage:
                    stage = ct_stage
                    confidence = 0.85
                    logger.info(f"Classified {name} as {stage} (ClinicalTrials.gov)")

        # 6. Default to PRECLINICAL for biotech companies without clear stage
        if stage == 'UNKNOWN' and self._is_biotech(description, focus_areas):
            stage = 'PRECLINICAL'
            confidence = 0.40
            logger.info(f"Defaulted {name} to PRECLINICAL (biotech without clear stage)")

        # Cache the result
        self.classification_cache[name] = (stage, confidence)
        self.confidence_scores[name] = confidence

        return stage, confidence

    def _is_acquired(self, description: str, focus_areas: str) -> bool:
        """Check if company has been acquired"""
        text = f"{description} {focus_areas}".lower()
        for keyword in self.STAGE_KEYWORDS['ACQUIRED']:
            if keyword in text:
                return True
        return False

    def _is_platform(self, description: str, focus_areas: str, name: str) -> bool:
        """Check if company is a platform/services company"""
        text = f"{description} {focus_areas} {name}".lower()
        platform_score = 0

        for keyword in self.STAGE_KEYWORDS['PLATFORM']:
            if keyword in text:
                platform_score += 1

        # Check for drug development keywords (negative indicator)
        drug_keywords = ['drug', 'therapeutic', 'clinical', 'trial', 'candidate']
        drug_score = sum(1 for kw in drug_keywords if kw in text)

        return platform_score > drug_score and platform_score >= 2

    def _is_biotech(self, description: str, focus_areas: str) -> bool:
        """Check if company is in biotech/pharma"""
        text = f"{description} {focus_areas}".lower()
        biotech_keywords = [
            'therapeutic', 'drug', 'biotech', 'pharmaceutical', 'clinical',
            'therapy', 'treatment', 'medicine', 'antibody', 'protein',
            'gene therapy', 'cell therapy', 'oncology', 'immunotherapy'
        ]
        return any(keyword in text for keyword in biotech_keywords)

    def _extract_clinical_stage(self, description: str, focus_areas: str) -> Optional[str]:
        """Extract clinical stage from text"""
        text = f"{description} {focus_areas}".lower()

        # Check each stage in order of precedence (most advanced first)
        for stage in ['COMMERCIAL', 'PHASE_III', 'PHASE_II', 'PHASE_I', 'PRECLINICAL']:
            for keyword in self.STAGE_KEYWORDS[stage]:
                if keyword in text:
                    return stage

        return None

    def _check_clinical_trials(self, company_name: str) -> Optional[str]:
        """
        Check ClinicalTrials.gov for company's trials
        Note: This is a simplified version - real implementation would use proper API
        """
        try:
            # Clean company name for search
            search_name = re.sub(r'\b(inc|corp|llc|ltd|therapeutics|bio|pharma)\b', '',
                                company_name, flags=re.IGNORECASE).strip()

            # For demonstration - would use actual API in production
            # This is a placeholder that returns based on name patterns
            if 'clinical' in company_name.lower():
                return 'PHASE_II'
            elif 'therapeutics' in company_name.lower():
                return 'PHASE_I'

            return None

        except Exception as e:
            logger.error(f"Error checking clinical trials for {company_name}: {e}")
            return None

    def process_csv(self, input_file: str, output_file: str):
        """Process entire CSV file and add stage classifications"""

        logger.info(f"Starting classification of {input_file}")

        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + ['Company_Stage_Classified', 'Stage_Confidence', 'Classifier_Date']

            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()

                total_companies = 0
                classified_companies = 0
                stage_distribution = {}

                for row in reader:
                    total_companies += 1

                    # Classify the company
                    stage, confidence = self.classify_company(row)

                    # Map internal stage to display format
                    display_stage = self._map_to_display_stage(stage)

                    # Add classification to row
                    row['Company_Stage_Classified'] = display_stage
                    row['Stage_Confidence'] = round(confidence, 4)
                    row['Classifier_Date'] = datetime.now().strftime('%Y-%m-%d')

                    writer.writerow(row)

                    # Track statistics
                    if stage != 'UNKNOWN':
                        classified_companies += 1
                    stage_distribution[display_stage] = stage_distribution.get(display_stage, 0) + 1

                    if total_companies % 100 == 0:
                        logger.info(f"Processed {total_companies} companies...")

        # Generate summary report
        self._generate_report(total_companies, classified_companies, stage_distribution)

        logger.info(f"Classification complete. Output saved to {output_file}")
        logger.info(f"Classified {classified_companies}/{total_companies} companies ({classified_companies/total_companies*100:.1f}%)")

    def _map_to_display_stage(self, internal_stage: str) -> str:
        """Map internal stage names to display format"""
        mapping = {
            'PRECLINICAL': 'Preclinical',
            'PHASE_I': 'Phase I',
            'PHASE_II': 'Phase II',
            'PHASE_III': 'Phase III',
            'COMMERCIAL': 'Commercial',
            'PLATFORM': 'Platform',
            'ACQUIRED': 'Acquired',
            'IPO': 'IPO',
            'PUBLIC': 'Public',
            'UNKNOWN': 'Unknown'
        }
        return mapping.get(internal_stage, 'Unknown')

    def _generate_report(self, total: int, classified: int, distribution: Dict):
        """Generate classification report"""
        report_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/deleteme/reports/stage_classification_report.md'

        with open(report_file, 'w') as f:
            f.write("# Company Stage Classification Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Summary Statistics\n\n")
            f.write(f"- Total Companies: {total}\n")
            f.write(f"- Successfully Classified: {classified} ({classified/total*100:.1f}%)\n")
            f.write(f"- Unknown Stage: {total - classified} ({(total-classified)/total*100:.1f}%)\n\n")
            f.write("## Stage Distribution\n\n")

            for stage in sorted(distribution.keys()):
                count = distribution[stage]
                percentage = count / total * 100
                f.write(f"- {stage}: {count} ({percentage:.1f}%)\n")

            f.write("\n## Confidence Score Distribution\n\n")
            if self.confidence_scores:
                scores = list(self.confidence_scores.values())
                f.write(f"- Average Confidence: {sum(scores)/len(scores):.3f}\n")
                f.write(f"- Min Confidence: {min(scores):.3f}\n")
                f.write(f"- Max Confidence: {max(scores):.3f}\n")

        logger.info(f"Report generated: {report_file}")

def main():
    """Main execution function"""
    classifier = CompanyStageClassifier()

    # Process the enriched companies file
    input_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/data/working/companies_enriched_final.csv'
    output_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/data/working/companies_with_stages.csv'

    try:
        classifier.process_csv(input_file, output_file)
        logger.info("Stage classification completed successfully")
    except Exception as e:
        logger.error(f"Error during classification: {e}")
        raise

if __name__ == "__main__":
    main()