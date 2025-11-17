#!/usr/bin/env python3
"""
Run exhaustive enrichment on ALL companies using both SEC EDGAR and ClinicalTrials APIs
Tracks progress and generates final report
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, List
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enrichment.sec_edgar_client import SECEdgarEnricher
from enrichment.clinicaltrials_client import ClinicalTrialsEnricher
from db.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/exhaustive_enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExhaustiveEnrichmentRunner:
    """Run exhaustive enrichment on all companies"""

    def __init__(self, db_path: str = "data/bayarea_biotech_sources.db"):
        self.db = DatabaseManager(db_path)
        self.sec_enricher = SECEdgarEnricher(db_path)
        self.ct_enricher = ClinicalTrialsEnricher(db_path)

        self.start_time = None
        self.stats = {
            'total_companies': 0,
            'sec_processed': 0,
            'ct_processed': 0,
            'sec_found': 0,
            'ct_found': 0,
            'sec_classified': 0,
            'ct_classified': 0,
            'errors': 0
        }

    def get_initial_classification_stats(self) -> Dict:
        """Get classification statistics before enrichment"""
        logger.info("Getting initial classification statistics...")

        cursor = self.db.connection.cursor()

        # Total companies
        cursor.execute("SELECT COUNT(*) FROM companies")
        total = cursor.fetchone()[0]

        # Count companies with classifications (using is_current flag)
        cursor.execute("""
            SELECT company_stage, COUNT(DISTINCT company_id) as count
            FROM company_classifications
            WHERE is_current = 1
            GROUP BY company_stage
        """)

        classifications = {}
        classified_count = 0
        for row in cursor.fetchall():
            stage = row[0] if row[0] else 'Unknown'
            count = row[1]
            classifications[stage] = count
            if stage != 'Unknown':
                classified_count += count

        # Count companies WITHOUT any current classification
        cursor.execute("""
            SELECT COUNT(*)
            FROM companies c
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE cc.company_id IS NULL
        """)
        unclassified_count = cursor.fetchone()[0]

        return {
            'total_companies': total,
            'classifications': classifications,
            'classified_count': classified_count,
            'unclassified_count': unclassified_count,
            'unclassified_percent': (unclassified_count / total * 100) if total > 0 else 0
        }

    def run_sec_enrichment(self):
        """Run SEC EDGAR enrichment"""
        logger.info("="*80)
        logger.info("STARTING SEC EDGAR ENRICHMENT")
        logger.info("="*80)

        # Get companies that need SEC enrichment
        companies = self.db.get_companies_for_enrichment('sec_edgar')
        total = len(companies)

        logger.info(f"Processing {total} companies through SEC EDGAR API")

        # Run enrichment
        try:
            self.sec_enricher.run_enrichment()
            self.stats['sec_processed'] = self.sec_enricher.stats['total_processed']
            self.stats['sec_found'] = self.sec_enricher.stats['filings_found']
            self.stats['sec_classified'] = self.sec_enricher.stats['public_companies']
        except Exception as e:
            logger.error(f"SEC enrichment failed: {e}")
            self.stats['errors'] += 1

    def run_clinicaltrials_enrichment(self):
        """Run ClinicalTrials enrichment"""
        logger.info("="*80)
        logger.info("STARTING CLINICALTRIALS ENRICHMENT")
        logger.info("="*80)

        # Get companies that need ClinicalTrials enrichment
        companies = self.db.get_companies_for_enrichment('clinical_trials')
        total = len(companies)

        logger.info(f"Processing {total} companies through ClinicalTrials.gov API")

        # Run enrichment
        try:
            self.ct_enricher.run_enrichment()
            self.stats['ct_processed'] = self.ct_enricher.stats['total_processed']
            self.stats['ct_found'] = self.ct_enricher.stats['trials_found']
            self.stats['ct_classified'] = self.ct_enricher.stats['clinical_stage']
        except Exception as e:
            logger.error(f"ClinicalTrials enrichment failed: {e}")
            self.stats['errors'] += 1

    def generate_final_report(self, initial_stats: Dict, final_stats: Dict):
        """Generate comprehensive final report"""
        logger.info("\n" + "="*80)
        logger.info("EXHAUSTIVE ENRICHMENT FINAL REPORT")
        logger.info("="*80)

        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)

        logger.info(f"\nExecution Time: {hours}h {minutes}m {seconds}s")

        logger.info("\n" + "-"*80)
        logger.info("PROCESSING STATISTICS")
        logger.info("-"*80)
        logger.info(f"Total companies in database: {self.stats['total_companies']}")
        logger.info(f"SEC EDGAR processed: {self.stats['sec_processed']}")
        logger.info(f"  - Filings found: {self.stats['sec_found']}")
        logger.info(f"  - Public companies identified: {self.stats['sec_classified']}")
        logger.info(f"ClinicalTrials processed: {self.stats['ct_processed']}")
        logger.info(f"  - Trials found: {self.stats['ct_found']}")
        logger.info(f"  - Clinical stage identified: {self.stats['ct_classified']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")

        logger.info("\n" + "-"*80)
        logger.info("CLASSIFICATION IMPROVEMENT")
        logger.info("-"*80)

        logger.info("\nBEFORE ENRICHMENT:")
        for classification, count in sorted(initial_stats['classifications'].items()):
            pct = (count / initial_stats['total_companies'] * 100)
            logger.info(f"  {classification:25s}: {count:4d} ({pct:5.1f}%)")
        logger.info(f"  {'Unclassified':25s}: {initial_stats['unclassified_count']:4d} ({initial_stats['unclassified_percent']:5.1f}%)")

        logger.info("\nAFTER ENRICHMENT:")
        for classification, count in sorted(final_stats['classifications'].items()):
            pct = (count / final_stats['total_companies'] * 100)
            logger.info(f"  {classification:25s}: {count:4d} ({pct:5.1f}%)")
        logger.info(f"  {'Unclassified':25s}: {final_stats['unclassified_count']:4d} ({final_stats['unclassified_percent']:5.1f}%)")

        logger.info("\nIMPROVEMENT:")
        reduction = initial_stats['unclassified_count'] - final_stats['unclassified_count']
        reduction_pct = (reduction / initial_stats['unclassified_count'] * 100) if initial_stats['unclassified_count'] > 0 else 0
        newly_classified = final_stats['classified_count'] - initial_stats['classified_count']
        logger.info(f"  Companies newly classified: {newly_classified}")
        logger.info(f"  Unclassified companies reduced by: {reduction} ({reduction_pct:.1f}%)")
        logger.info(f"  Unclassified percentage reduced from {initial_stats['unclassified_percent']:.1f}% to {final_stats['unclassified_percent']:.1f}%")

        # Save report to file
        report_path = f"logs/enrichment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write("EXHAUSTIVE ENRICHMENT FINAL REPORT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Execution Time: {hours}h {minutes}m {seconds}s\n\n")
            f.write("-"*80 + "\n")
            f.write("PROCESSING STATISTICS\n")
            f.write("-"*80 + "\n")
            f.write(f"Total companies: {self.stats['total_companies']}\n")
            f.write(f"SEC EDGAR processed: {self.stats['sec_processed']}\n")
            f.write(f"  - Filings found: {self.stats['sec_found']}\n")
            f.write(f"  - Public companies: {self.stats['sec_classified']}\n")
            f.write(f"ClinicalTrials processed: {self.stats['ct_processed']}\n")
            f.write(f"  - Trials found: {self.stats['ct_found']}\n")
            f.write(f"  - Clinical stage: {self.stats['ct_classified']}\n")
            f.write(f"Errors: {self.stats['errors']}\n\n")

            f.write("-"*80 + "\n")
            f.write("CLASSIFICATION STATISTICS\n")
            f.write("-"*80 + "\n\n")
            f.write("BEFORE:\n")
            for classification, count in sorted(initial_stats['classifications'].items()):
                pct = (count / initial_stats['total_companies'] * 100)
                f.write(f"  {classification:20s}: {count:4d} ({pct:5.1f}%)\n")
            f.write(f"\nAFTER:\n")
            for classification, count in sorted(final_stats['classifications'].items()):
                pct = (count / final_stats['total_companies'] * 100)
                f.write(f"  {classification:20s}: {count:4d} ({pct:5.1f}%)\n")
            f.write(f"\nUnknown reduced by: {reduction} ({reduction_pct:.1f}%)\n")

        logger.info(f"\nReport saved to: {report_path}")

        logger.info("\n" + "="*80)
        logger.info("EXHAUSTIVE ENRICHMENT COMPLETE")
        logger.info("="*80)

    def run(self, sec_only: bool = False, ct_only: bool = False):
        """Run exhaustive enrichment"""
        self.start_time = time.time()

        # Get total companies
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM companies")
        self.stats['total_companies'] = cursor.fetchone()[0]

        logger.info("="*80)
        logger.info("EXHAUSTIVE ENRICHMENT STARTED")
        logger.info("="*80)
        logger.info(f"Total companies: {self.stats['total_companies']}")
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Get initial statistics
        initial_stats = self.get_initial_classification_stats()

        # Run enrichments
        if not ct_only:
            self.run_sec_enrichment()

        if not sec_only:
            self.run_clinicaltrials_enrichment()

        # Get final statistics
        final_stats = self.get_initial_classification_stats()

        # Generate report
        self.generate_final_report(initial_stats, final_stats)

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Run exhaustive enrichment on all companies')
    parser.add_argument('--sec-only', action='store_true', help='Run only SEC EDGAR enrichment')
    parser.add_argument('--ct-only', action='store_true', help='Run only ClinicalTrials enrichment')
    args = parser.parse_args()

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    runner = ExhaustiveEnrichmentRunner()
    runner.run(sec_only=args.sec_only, ct_only=args.ct_only)

if __name__ == "__main__":
    main()
