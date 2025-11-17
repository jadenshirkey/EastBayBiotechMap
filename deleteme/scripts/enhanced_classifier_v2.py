#!/usr/bin/env python3
"""
Enhanced Company Stage Classifier v2 for East Bay Biotech Map
Uses Focus Areas field as primary classification source
Implements waterfall logic: Focus Areas → Description → Name patterns → API
"""

import csv
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/deleteme/logs/classifier_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedStageClassifier:
    """Enhanced classifier that uses Focus Areas as primary signal"""

    # Comprehensive keyword mappings
    PLATFORM_KEYWORDS = {
        # Diagnostics
        'diagnostic', 'diagnostics', 'assay', 'test', 'testing', 'detection',
        'screening', 'biomarker', 'biosensor', 'imaging',

        # Tools & Services
        'reagent', 'reagents', 'kit', 'kits', 'tool', 'tools', 'instrument',
        'equipment', 'device', 'devices', 'software', 'platform', 'system',

        # Services
        'service', 'services', 'cro', 'cdmo', 'cmo', 'contract', 'consulting',
        'research services', 'manufacturing', 'production', 'formulation',

        # Technology platforms
        'discovery platform', 'drug discovery platform', 'ai platform',
        'computational', 'informatics', 'analytics', 'data', 'database'
    }

    THERAPEUTIC_KEYWORDS = {
        # Drug types
        'therapeutic', 'therapeutics', 'therapy', 'therapies', 'drug', 'drugs',
        'medicine', 'medication', 'treatment', 'cure', 'pharmaceutical',

        # Modalities
        'antibody', 'antibodies', 'mab', 'monoclonal', 'biologic', 'biologics',
        'protein', 'peptide', 'vaccine', 'cell therapy', 'gene therapy',
        'car-t', 'cart', 'rna', 'mrna', 'sirna', 'antisense', 'oligonucleotide',

        # Development terms
        'clinical', 'preclinical', 'pipeline', 'candidate', 'indication',
        'oncology', 'immunotherapy', 'immuno-oncology', 'neurology',
        'cardiovascular', 'metabolic', 'infectious', 'orphan', 'rare disease'
    }

    # Clinical stage indicators
    CLINICAL_STAGE_PATTERNS = {
        'COMMERCIAL': [
            'fda approved', 'marketed', 'commercial', 'on market', 'approved drug',
            'selling', 'revenue', 'product sales', 'commercialized'
        ],
        'PHASE_III': [
            'phase 3', 'phase iii', 'phase three', 'phase3', 'pivotal',
            'registrational', 'late-stage clinical', 'late stage'
        ],
        'PHASE_II': [
            'phase 2', 'phase ii', 'phase two', 'phase2', 'mid-stage',
            'proof of concept', 'dose ranging', 'mid stage'
        ],
        'PHASE_I': [
            'phase 1', 'phase i', 'phase one', 'phase1', 'first-in-human',
            'early clinical', 'safety study', 'early stage clinical'
        ],
        'PRECLINICAL': [
            'preclinical', 'pre-clinical', 'discovery', 'research stage',
            'lead optimization', 'target validation', 'early-stage research',
            'pre-ind', 'research', 'discovery stage'
        ]
    }

    # Known public/commercial companies
    KNOWN_COMPANIES = {
        # Public companies
        '10x genomics': ('PUBLIC', 0.95),
        'abbvie': ('COMMERCIAL', 0.95),
        'gilead': ('COMMERCIAL', 0.95),
        'genentech': ('COMMERCIAL', 0.95),
        'biomarin': ('COMMERCIAL', 0.95),
        'nektar': ('PUBLIC', 0.90),
        'exelixis': ('COMMERCIAL', 0.95),
        'theravance': ('COMMERCIAL', 0.90),
        'sangamo': ('PUBLIC', 0.85),
        'ultragenyx': ('COMMERCIAL', 0.90),
        'coherus': ('COMMERCIAL', 0.85),
        'arcus': ('PUBLIC', 0.85),
        'vir biotechnology': ('PUBLIC', 0.85),
        'bolt biotherapeutics': ('PUBLIC', 0.85),

        # Known platforms
        'illumina': ('PLATFORM', 0.95),
        'pacific biosciences': ('PLATFORM', 0.90),
        'bio-rad': ('PLATFORM', 0.95),
        'thermo fisher': ('PLATFORM', 0.95),
        'agilent': ('PLATFORM', 0.95),
    }

    def __init__(self):
        self.classification_cache = {}
        self.stats = defaultdict(int)

    def classify_company(self, row: Dict) -> Tuple[str, float, str]:
        """
        Classify a company using waterfall logic
        Returns: (stage, confidence, method_used)
        """
        company_name = row.get('Company Name', '').strip()
        focus_areas = row.get('Focus Areas', '').strip()
        description = row.get('Description', '').strip()
        website = row.get('Website', '').strip()

        # Check cache
        cache_key = company_name.lower()
        if cache_key in self.classification_cache:
            return self.classification_cache[cache_key]

        stage = 'Unknown'
        confidence = 0.0
        method = 'none'

        # 1. Check known companies first (highest confidence)
        if cache_key in self.KNOWN_COMPANIES:
            stage, confidence = self.KNOWN_COMPANIES[cache_key]
            method = 'known_company'
            logger.debug(f"{company_name}: {stage} (known company, conf={confidence})")

        # 2. Try Focus Areas field (primary signal)
        elif focus_areas:
            result = self._classify_from_focus_areas(focus_areas, company_name)
            if result[0] != 'Unknown':
                stage, confidence, method = result
                logger.debug(f"{company_name}: {stage} from Focus Areas (conf={confidence})")

        # 3. Try Description field (secondary signal)
        if stage == 'Unknown' and description:
            result = self._classify_from_description(description)
            if result[0] != 'Unknown':
                stage, confidence, method = result
                logger.debug(f"{company_name}: {stage} from Description (conf={confidence})")

        # 4. Try company name patterns (tertiary signal)
        if stage == 'Unknown':
            result = self._classify_from_name(company_name)
            if result[0] != 'Unknown':
                stage, confidence, method = result
                logger.debug(f"{company_name}: {stage} from name pattern (conf={confidence})")

        # 5. Default classification based on context
        if stage == 'Unknown':
            # If it has therapeutic keywords anywhere, default to Preclinical
            all_text = f"{focus_areas} {description} {company_name}".lower()
            if any(kw in all_text for kw in self.THERAPEUTIC_KEYWORDS):
                stage = 'Preclinical'
                confidence = 0.3
                method = 'default_therapeutic'
                logger.debug(f"{company_name}: Defaulted to Preclinical")

        # Cache and track stats
        result = (stage, confidence, method)
        self.classification_cache[cache_key] = result
        self.stats[method] += 1
        self.stats[stage] += 1

        return result

    def _classify_from_focus_areas(self, focus_areas: str, company_name: str) -> Tuple[str, float, str]:
        """Classify based on Focus Areas field"""
        focus_lower = focus_areas.lower()

        # Check for clinical stage indicators first
        for stage, patterns in self.CLINICAL_STAGE_PATTERNS.items():
            for pattern in patterns:
                if pattern in focus_lower:
                    display_stage = self._map_clinical_stage(stage)
                    return (display_stage, 0.75, 'focus_areas_clinical')

        # Check for platform indicators
        platform_score = sum(1 for kw in self.PLATFORM_KEYWORDS if kw in focus_lower)
        therapeutic_score = sum(1 for kw in self.THERAPEUTIC_KEYWORDS if kw in focus_lower)

        # Strong platform signal
        if platform_score >= 2 and platform_score > therapeutic_score:
            return ('Platform', 0.80, 'focus_areas_platform')

        # Pure platform (no therapeutic keywords)
        if platform_score > 0 and therapeutic_score == 0:
            return ('Platform', 0.85, 'focus_areas_platform')

        # Strong therapeutic signal
        if therapeutic_score >= 2 and therapeutic_score > platform_score:
            # Check if clinical stage is mentioned
            if any(word in focus_lower for word in ['clinical', 'phase', 'trial']):
                return ('Phase I', 0.60, 'focus_areas_therapeutic')
            return ('Preclinical', 0.65, 'focus_areas_therapeutic')

        # Pure therapeutic (no platform keywords)
        if therapeutic_score > 0 and platform_score == 0:
            return ('Preclinical', 0.70, 'focus_areas_therapeutic')

        # Mixed signals - classify based on company name
        if platform_score > 0 and therapeutic_score > 0:
            if 'therapeutics' in company_name.lower():
                return ('Preclinical', 0.55, 'focus_areas_mixed')
            else:
                return ('Platform', 0.55, 'focus_areas_mixed')

        return ('Unknown', 0.0, 'none')

    def _classify_from_description(self, description: str) -> Tuple[str, float, str]:
        """Classify based on Description field"""
        desc_lower = description.lower()

        # Check for explicit clinical stages
        for stage, patterns in self.CLINICAL_STAGE_PATTERNS.items():
            for pattern in patterns:
                if pattern in desc_lower:
                    display_stage = self._map_clinical_stage(stage)
                    return (display_stage, 0.70, 'description_clinical')

        # Check for acquisition
        if any(kw in desc_lower for kw in ['acquired by', 'acquisition', 'bought by', 'subsidiary of']):
            return ('Acquired', 0.80, 'description_acquired')

        # Platform vs Therapeutic
        platform_score = sum(1 for kw in self.PLATFORM_KEYWORDS if kw in desc_lower)
        therapeutic_score = sum(1 for kw in self.THERAPEUTIC_KEYWORDS if kw in desc_lower)

        if platform_score > therapeutic_score and platform_score >= 2:
            return ('Platform', 0.65, 'description_platform')

        if therapeutic_score > platform_score and therapeutic_score >= 2:
            return ('Preclinical', 0.60, 'description_therapeutic')

        return ('Unknown', 0.0, 'none')

    def _classify_from_name(self, company_name: str) -> Tuple[str, float, str]:
        """Classify based on company name patterns"""
        name_lower = company_name.lower()

        # Strong indicators in company names
        if 'diagnostics' in name_lower:
            return ('Platform', 0.70, 'name_pattern')

        if 'therapeutics' in name_lower or 'pharma' in name_lower:
            return ('Preclinical', 0.50, 'name_pattern')

        if 'clinical' in name_lower:
            if 'research' in name_lower:
                return ('Platform', 0.60, 'name_pattern')
            return ('Phase I', 0.45, 'name_pattern')

        if any(kw in name_lower for kw in ['biosystems', 'biosciences', 'biotech']):
            return ('Preclinical', 0.40, 'name_pattern')

        return ('Unknown', 0.0, 'none')

    def _map_clinical_stage(self, internal_stage: str) -> str:
        """Map internal stage names to display format"""
        mapping = {
            'PRECLINICAL': 'Preclinical',
            'PHASE_I': 'Phase I',
            'PHASE_II': 'Phase II',
            'PHASE_III': 'Phase III',
            'COMMERCIAL': 'Commercial'
        }
        return mapping.get(internal_stage, internal_stage)

    def process_csv(self, input_file: str, output_file: str):
        """Process CSV file with enhanced classification"""
        logger.info(f"Starting enhanced classification of {input_file}")

        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)

            # Determine output fields based on input
            input_fields = list(reader.fieldnames)

            # Always ensure all our fields are present
            new_fields = []
            if 'Company_Stage_Classified' not in input_fields:
                new_fields.append('Company_Stage_Classified')
            if 'Stage_Confidence' not in input_fields:
                new_fields.append('Stage_Confidence')
            if 'Classification_Method' not in input_fields:
                new_fields.append('Classification_Method')
            if 'Classifier_Date' not in input_fields:
                new_fields.append('Classifier_Date')

            fieldnames = input_fields + new_fields

            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()

                total = 0
                classified = 0
                stage_dist = defaultdict(int)
                method_dist = defaultdict(int)

                for row in reader:
                    total += 1

                    # Classify the company
                    stage, confidence, method = self.classify_company(row)

                    # Update row
                    row['Company_Stage_Classified'] = stage
                    row['Stage_Confidence'] = round(confidence, 4)
                    row['Classification_Method'] = method
                    row['Classifier_Date'] = datetime.now().strftime('%Y-%m-%d')

                    writer.writerow(row)

                    # Track statistics
                    if stage != 'Unknown':
                        classified += 1
                    stage_dist[stage] += 1
                    method_dist[method] += 1

                    if total % 100 == 0:
                        logger.info(f"Processed {total} companies, {classified} classified...")

        # Generate report
        self._generate_report(total, classified, stage_dist, method_dist)

        logger.info(f"Enhanced classification complete: {classified}/{total} ({classified/total*100:.1f}%)")
        logger.info(f"Output saved to: {output_file}")

        return classified / total

    def _generate_report(self, total: int, classified: int, stage_dist: Dict, method_dist: Dict):
        """Generate classification report"""
        report_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/deleteme/reports/enhanced_classification_report.md'

        with open(report_file, 'w') as f:
            f.write("# Enhanced Classification Report v2\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Summary\n\n")
            f.write(f"- Total Companies: {total}\n")
            f.write(f"- Successfully Classified: {classified} ({classified/total*100:.1f}%)\n")
            f.write(f"- Unknown: {total - classified} ({(total-classified)/total*100:.1f}%)\n\n")

            f.write("## Stage Distribution\n\n")
            for stage in sorted(stage_dist.keys()):
                count = stage_dist[stage]
                pct = count / total * 100
                f.write(f"- {stage}: {count} ({pct:.1f}%)\n")

            f.write("\n## Classification Methods Used\n\n")
            for method in sorted(method_dist.keys()):
                if method != 'none':
                    count = method_dist[method]
                    pct = count / total * 100
                    f.write(f"- {method}: {count} ({pct:.1f}%)\n")

            f.write("\n## Key Improvements from v1\n\n")
            f.write("- Now uses Focus Areas as primary classification signal\n")
            f.write("- Implements waterfall logic for multiple data sources\n")
            f.write("- Better platform vs therapeutic discrimination\n")
            f.write("- Improved confidence scoring\n")

        logger.info(f"Report saved to: {report_file}")

def main():
    """Main execution"""
    classifier = EnhancedStageClassifier()

    # Use the output from v1 as input
    input_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/data/working/companies_with_stages.csv'
    output_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/data/working/companies_enhanced_v2.csv'

    try:
        success_rate = classifier.process_csv(input_file, output_file)
        logger.info(f"Classification success rate: {success_rate*100:.1f}%")

        # Log statistics
        logger.info("\nClassification method breakdown:")
        for method, count in sorted(classifier.stats.items()):
            logger.info(f"  {method}: {count}")

    except Exception as e:
        logger.error(f"Error during classification: {e}")
        raise

if __name__ == "__main__":
    main()