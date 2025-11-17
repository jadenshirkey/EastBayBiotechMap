#!/usr/bin/env python3
"""
Comprehensive Test Validator for East Bay Biotech Map Pipeline
Implements critical invariants and quality checks
Based on subagent recommendations for robust testing
"""

import csv
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/deleteme/logs/validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PipelineValidator:
    """Validates pipeline output against critical invariants"""

    # Critical invariants that must hold
    CRITICAL_INVARIANTS = {
        'address_coverage': {
            'check': lambda old, new: new >= old * 0.99,  # Allow 1% variance
            'message': 'Address coverage must not degrade more than 1%'
        },
        'total_companies': {
            'check': lambda old, new: new >= old * 0.95,  # Max 5% loss
            'message': 'Cannot lose more than 5% of companies'
        },
        'classification_rate': {
            'check': lambda rate: rate >= 0.75,  # Min 75%
            'message': 'Classification rate must be at least 75%'
        },
        'quality_average': {
            'check': lambda score: score >= 70,  # Min quality
            'message': 'Average quality score must be at least 70'
        }
    }

    # Known company ground truth for validation
    GROUND_TRUTH = {
        '10x genomics': 'Public',
        'genentech': 'Commercial',
        'gilead': 'Commercial',
        'biomarin': 'Commercial',
        'illumina': 'Platform',
        'bio-rad': 'Platform'
    }

    # Data integrity rules
    DATA_INTEGRITY_RULES = {
        'unique_companies': 'Company names must be unique',
        'required_fields': 'All required fields must be present',
        'valid_coordinates': 'Coordinates must be valid lat/long',
        'valid_confidence': 'Confidence scores must be 0-1',
        'source_attribution': 'Classified companies must have source',
        'stage_consistency': 'Stage values must be from allowed set'
    }

    # Allowed stage values
    ALLOWED_STAGES = {
        'Preclinical', 'Phase I', 'Phase II', 'Phase III',
        'Commercial', 'Platform', 'Public', 'IPO',
        'Acquired', 'Unknown'
    }

    def __init__(self):
        self.validation_results = {}
        self.test_stats = defaultdict(int)

    def validate_pipeline_output(self,
                                input_file: str,
                                output_file: str,
                                baseline_file: Optional[str] = None) -> bool:
        """
        Comprehensive validation of pipeline output

        Args:
            input_file: Original input data
            output_file: Pipeline output to validate
            baseline_file: Optional baseline for regression testing

        Returns:
            bool: True if all validations pass
        """
        logger.info(f"Starting validation of {output_file}")

        all_passed = True

        # 1. Data Integrity Tests
        integrity_passed = self._validate_data_integrity(output_file)
        all_passed &= integrity_passed

        # 2. Critical Invariants Tests
        invariants_passed = self._validate_invariants(input_file, output_file)
        all_passed &= invariants_passed

        # 3. Ground Truth Tests
        ground_truth_passed = self._validate_ground_truth(output_file)
        all_passed &= ground_truth_passed

        # 4. Quality Metrics Tests
        quality_passed = self._validate_quality_metrics(output_file)
        all_passed &= quality_passed

        # 5. Regression Tests (if baseline provided)
        if baseline_file:
            regression_passed = self._validate_regression(baseline_file, output_file)
            all_passed &= regression_passed

        # 6. Edge Cases Tests
        edge_cases_passed = self._validate_edge_cases(output_file)
        all_passed &= edge_cases_passed

        # Generate validation report
        self._generate_validation_report(all_passed)

        return all_passed

    def _validate_data_integrity(self, file_path: str) -> bool:
        """Validate data integrity rules"""
        logger.info("Validating data integrity...")
        passed = True

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Check unique companies
        company_names = [r.get('Company Name', '') for r in rows]
        if len(company_names) != len(set(company_names)):
            logger.error("FAILED: Duplicate company names found")
            self.test_stats['duplicate_companies'] = len(company_names) - len(set(company_names))
            passed = False
        else:
            logger.info("PASSED: All company names are unique")

        # Check required fields
        required_fields = ['Company Name', 'City', 'Company_Stage_Classified']
        for row in rows:
            for field in required_fields:
                if not row.get(field):
                    self.test_stats['missing_required_fields'] += 1
                    passed = False

        if self.test_stats['missing_required_fields'] > 0:
            logger.error(f"FAILED: {self.test_stats['missing_required_fields']} missing required fields")
        else:
            logger.info("PASSED: All required fields present")

        # Validate coordinates
        invalid_coords = 0
        for row in rows:
            lat = row.get('Latitude')
            lon = row.get('Longitude')
            if lat and lon:
                try:
                    lat_f = float(lat)
                    lon_f = float(lon)
                    if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
                        invalid_coords += 1
                except:
                    invalid_coords += 1

        if invalid_coords > 0:
            logger.error(f"FAILED: {invalid_coords} invalid coordinates")
            passed = False
        else:
            logger.info("PASSED: All coordinates valid")

        # Validate confidence scores
        invalid_confidence = 0
        for row in rows:
            conf = row.get('Stage_Confidence')
            if conf:
                try:
                    conf_f = float(conf)
                    if not (0 <= conf_f <= 1):
                        invalid_confidence += 1
                except:
                    invalid_confidence += 1

        if invalid_confidence > 0:
            logger.error(f"FAILED: {invalid_confidence} invalid confidence scores")
            passed = False
        else:
            logger.info("PASSED: All confidence scores valid")

        # Validate stage consistency
        invalid_stages = 0
        for row in rows:
            stage = row.get('Company_Stage_Classified')
            if stage and stage not in self.ALLOWED_STAGES:
                invalid_stages += 1
                logger.warning(f"Invalid stage: {stage}")

        if invalid_stages > 0:
            logger.error(f"FAILED: {invalid_stages} invalid stage values")
            passed = False
        else:
            logger.info("PASSED: All stage values valid")

        self.validation_results['data_integrity'] = passed
        return passed

    def _validate_invariants(self, input_file: str, output_file: str) -> bool:
        """Validate critical invariants"""
        logger.info("Validating critical invariants...")
        passed = True

        # Load input data
        with open(input_file, 'r', encoding='utf-8') as f:
            input_rows = list(csv.DictReader(f))

        # Load output data
        with open(output_file, 'r', encoding='utf-8') as f:
            output_rows = list(csv.DictReader(f))

        # Check total companies invariant
        input_count = len(input_rows)
        output_count = len(output_rows)

        if not self.CRITICAL_INVARIANTS['total_companies']['check'](input_count, output_count):
            logger.error(f"FAILED: {self.CRITICAL_INVARIANTS['total_companies']['message']}")
            logger.error(f"  Input: {input_count}, Output: {output_count}")
            passed = False
        else:
            logger.info(f"PASSED: Company count preserved ({output_count}/{input_count})")

        # Check address coverage invariant
        input_addresses = sum(1 for r in input_rows if r.get('Google_Address'))
        output_addresses = sum(1 for r in output_rows if r.get('Google_Address'))

        input_coverage = input_addresses / input_count if input_count > 0 else 0
        output_coverage = output_addresses / output_count if output_count > 0 else 0

        if not self.CRITICAL_INVARIANTS['address_coverage']['check'](input_coverage, output_coverage):
            logger.error(f"FAILED: {self.CRITICAL_INVARIANTS['address_coverage']['message']}")
            logger.error(f"  Input: {input_coverage:.1%}, Output: {output_coverage:.1%}")
            passed = False
        else:
            logger.info(f"PASSED: Address coverage maintained ({output_coverage:.1%})")

        # Check classification rate
        classified = sum(1 for r in output_rows
                        if r.get('Company_Stage_Classified') and
                        r.get('Company_Stage_Classified') != 'Unknown')
        classification_rate = classified / output_count if output_count > 0 else 0

        if not self.CRITICAL_INVARIANTS['classification_rate']['check'](classification_rate):
            logger.error(f"FAILED: {self.CRITICAL_INVARIANTS['classification_rate']['message']}")
            logger.error(f"  Rate: {classification_rate:.1%}")
            passed = False
        else:
            logger.info(f"PASSED: Classification rate sufficient ({classification_rate:.1%})")

        # Check quality average
        quality_scores = []
        for row in output_rows:
            if row.get('Quality_Score'):
                try:
                    quality_scores.append(float(row['Quality_Score']))
                except:
                    pass

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        if not self.CRITICAL_INVARIANTS['quality_average']['check'](avg_quality):
            logger.error(f"FAILED: {self.CRITICAL_INVARIANTS['quality_average']['message']}")
            logger.error(f"  Average: {avg_quality:.1f}")
            passed = False
        else:
            logger.info(f"PASSED: Quality score average acceptable ({avg_quality:.1f})")

        self.validation_results['invariants'] = passed
        return passed

    def _validate_ground_truth(self, file_path: str) -> bool:
        """Validate known companies against ground truth"""
        logger.info("Validating ground truth companies...")
        passed = True

        with open(file_path, 'r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

        # Check each ground truth company
        mismatches = []
        for company_name, expected_stage in self.GROUND_TRUTH.items():
            found = False
            for row in rows:
                if company_name in row.get('Company Name', '').lower():
                    actual_stage = row.get('Company_Stage_Classified', '')
                    if actual_stage != expected_stage:
                        mismatches.append(f"{company_name}: expected {expected_stage}, got {actual_stage}")
                    found = True
                    break

            if not found:
                mismatches.append(f"{company_name}: not found in output")

        if mismatches:
            logger.error(f"FAILED: {len(mismatches)} ground truth mismatches")
            for mismatch in mismatches:
                logger.error(f"  {mismatch}")
            passed = False
        else:
            logger.info("PASSED: All ground truth companies correctly classified")

        self.validation_results['ground_truth'] = passed
        return passed

    def _validate_quality_metrics(self, file_path: str) -> bool:
        """Validate quality metrics calculation"""
        logger.info("Validating quality metrics...")
        passed = True

        with open(file_path, 'r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

        # Analyze quality score distribution
        quality_distribution = {
            'high': 0,    # 85+
            'medium': 0,  # 50-84
            'low': 0      # <50
        }

        for row in rows:
            if row.get('Quality_Score'):
                try:
                    score = float(row['Quality_Score'])
                    if score >= 85:
                        quality_distribution['high'] += 1
                    elif score >= 50:
                        quality_distribution['medium'] += 1
                    else:
                        quality_distribution['low'] += 1
                except:
                    pass

        total_scored = sum(quality_distribution.values())

        # Check that most companies have medium or high quality
        good_quality = quality_distribution['high'] + quality_distribution['medium']
        good_quality_pct = good_quality / total_scored if total_scored > 0 else 0

        if good_quality_pct < 0.70:
            logger.error(f"FAILED: Only {good_quality_pct:.1%} have good quality scores")
            passed = False
        else:
            logger.info(f"PASSED: {good_quality_pct:.1%} have good quality scores")

        logger.info(f"  High quality: {quality_distribution['high']}")
        logger.info(f"  Medium quality: {quality_distribution['medium']}")
        logger.info(f"  Low quality: {quality_distribution['low']}")

        self.validation_results['quality_metrics'] = passed
        return passed

    def _validate_regression(self, baseline_file: str, output_file: str) -> bool:
        """Validate against baseline for regression detection"""
        logger.info("Running regression tests...")
        passed = True

        # Load baseline
        with open(baseline_file, 'r', encoding='utf-8') as f:
            baseline_rows = list(csv.DictReader(f))

        # Load output
        with open(output_file, 'r', encoding='utf-8') as f:
            output_rows = list(csv.DictReader(f))

        # Compare key metrics
        baseline_classified = sum(1 for r in baseline_rows
                                 if r.get('Company_Stage_Classified') != 'Unknown')
        output_classified = sum(1 for r in output_rows
                               if r.get('Company_Stage_Classified') != 'Unknown')

        if output_classified < baseline_classified * 0.95:
            logger.error(f"REGRESSION: Classification count degraded")
            logger.error(f"  Baseline: {baseline_classified}, Output: {output_classified}")
            passed = False
        else:
            logger.info(f"PASSED: No classification regression detected")

        self.validation_results['regression'] = passed
        return passed

    def _validate_edge_cases(self, file_path: str) -> bool:
        """Validate edge case handling"""
        logger.info("Validating edge case handling...")
        passed = True

        with open(file_path, 'r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

        # Check companies with no address
        no_address_companies = [r for r in rows if not r.get('Google_Address')]

        # They should still have classification
        unclassified_no_address = sum(1 for r in no_address_companies
                                     if r.get('Company_Stage_Classified') == 'Unknown')

        if unclassified_no_address > len(no_address_companies) * 0.5:
            logger.warning(f"WARNING: {unclassified_no_address} companies with no address are unclassified")

        # Check for proper handling of special characters
        special_char_companies = [r for r in rows
                                 if any(c in r.get('Company Name', '')
                                       for c in ['&', '-', '(', ')', '/'])]

        logger.info(f"  Companies with special characters: {len(special_char_companies)}")

        # Check for international companies (non-CA)
        non_ca_companies = [r for r in rows
                           if r.get('State_Parsed') and r.get('State_Parsed') != 'CA']

        if non_ca_companies:
            logger.info(f"  Non-California companies: {len(non_ca_companies)}")

        self.validation_results['edge_cases'] = passed
        return passed

    def _generate_validation_report(self, all_passed: bool):
        """Generate comprehensive validation report"""
        report_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/deleteme/reports/validation_report.md'

        with open(report_file, 'w') as f:
            f.write("# Pipeline Validation Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            status = "✅ PASSED" if all_passed else "❌ FAILED"
            f.write(f"## Overall Status: {status}\n\n")

            f.write("## Test Results\n\n")
            for test_name, result in self.validation_results.items():
                status = "✅" if result else "❌"
                f.write(f"- {test_name}: {status}\n")

            f.write("\n## Test Statistics\n\n")
            for stat, value in self.test_stats.items():
                f.write(f"- {stat}: {value}\n")

            f.write("\n## Recommendations\n\n")
            if not all_passed:
                f.write("- Review failed tests and fix issues\n")
                f.write("- Re-run pipeline after fixes\n")
                f.write("- Ensure all invariants are satisfied\n")
            else:
                f.write("- Pipeline output meets all quality criteria\n")
                f.write("- Ready for production deployment\n")
                f.write("- Consider setting current output as new baseline\n")

        logger.info(f"Validation report saved to {report_file}")

def main():
    """Run validation tests"""
    validator = PipelineValidator()

    # Define file paths
    input_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/data/working/companies_enriched_final.csv'
    output_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/data/working/companies_cleaned.csv'
    baseline_file = '/mnt/c/Users/shirk/Documents/Adulting/EastBayBiotechMap/data/working/companies_with_stages.csv'

    # Run validation
    all_passed = validator.validate_pipeline_output(input_file, output_file, baseline_file)

    if all_passed:
        logger.info("✅ All validation tests PASSED")
        return 0
    else:
        logger.error("❌ Some validation tests FAILED")
        return 1

if __name__ == "__main__":
    exit(main())