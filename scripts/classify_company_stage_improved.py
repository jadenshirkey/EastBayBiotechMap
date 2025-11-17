#!/usr/bin/env python3
"""
Improved Company Stage Classification Script
Uses database integration to properly classify companies based on SEC data

New classification categories:
- Public: Has active stock ticker (verified via SEC)
- Private with SEC Filings: Has SEC data but no active ticker
- Clinical Stage: Has clinical trials data
- Private: Default for companies without public data
- Unknown: Only when truly no information available

Author: Bay Area Biotech Map V5
Date: 2025-11-16
"""

import sqlite3
import logging
import sys
import argparse
from datetime import datetime
from typing import Dict, Tuple, Optional
# from scripts.db.db_manager import DatabaseManager  # Commented for standalone testing

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovedCompanyClassifier:
    """Improved classifier that uses database for accurate classification"""

    def __init__(self, db_path: str = "data/bayarea_biotech_sources.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.dry_run = False
        self.limit = None
        self.stats = {
            'total': 0,
            'Public': 0,
            'Private with SEC Filings': 0,
            'Clinical Stage': 0,
            'Private': 0,
            'Unknown': 0,
            'updated': 0,
            'skipped': 0
        }

    def classify_company(self, company_id: int) -> Tuple[str, float, str]:
        """
        Classify a company based on SEC and clinical trials data

        Returns:
            Tuple of (classification, confidence, source)
        """
        # Get SEC data
        self.cursor.execute("""
            SELECT ticker, company_status, filing_count, latest_filing_date
            FROM sec_edgar_data
            WHERE company_id = ?
        """, (company_id,))
        sec_data = self.cursor.fetchone()

        # Get clinical trials data
        self.cursor.execute("""
            SELECT COUNT(*) as trial_count,
                   MAX(phase) as max_phase
            FROM clinical_trials
            WHERE company_id = ?
        """, (company_id,))
        trials_data = self.cursor.fetchone()

        # Get company basic info
        self.cursor.execute("""
            SELECT company_name, website
            FROM companies
            WHERE company_id = ?
        """, (company_id,))
        company_info = self.cursor.fetchone()

        if not company_info:
            return ('Unknown', 0.1, 'No company data')

        company_name = company_info[0]

        # Classification logic with new categories

        # Priority 1: Public companies (have active ticker)
        if sec_data:
            ticker, company_status, filing_count, latest_filing = sec_data

            if ticker and company_status == 'public':
                logger.debug(f"  {company_name}: Public (ticker: {ticker})")
                return ('Public', 0.95, f'SEC EDGAR (ticker: {ticker})')

            # Priority 2: Private with SEC Filings (has SEC data but no active ticker)
            if filing_count and filing_count > 0:
                if company_status == 'formerly_public':
                    logger.debug(f"  {company_name}: Private with SEC Filings (formerly public)")
                    return ('Private with SEC Filings', 0.85, 'SEC EDGAR (formerly public)')
                elif company_status == 'acquired':
                    logger.debug(f"  {company_name}: Private with SEC Filings (acquired)")
                    return ('Private with SEC Filings', 0.90, 'SEC EDGAR (acquired)')
                elif company_status == 'subsidiary':
                    logger.debug(f"  {company_name}: Private with SEC Filings (subsidiary)")
                    return ('Private with SEC Filings', 0.80, 'SEC EDGAR (subsidiary)')
                else:
                    # Has filings but unclear status - still classify as Private with SEC
                    logger.debug(f"  {company_name}: Private with SEC Filings (has filings)")
                    return ('Private with SEC Filings', 0.75, f'SEC EDGAR ({filing_count} filings)')

        # Priority 3: Clinical Stage (has clinical trials but no SEC data)
        if trials_data:
            trial_count, max_phase = trials_data
            if trial_count and trial_count > 0:
                # Determine if late-stage based on trial count and phase
                if trial_count >= 5:
                    logger.debug(f"  {company_name}: Clinical Stage ({trial_count} trials)")
                    return ('Clinical Stage', 0.80, f'ClinicalTrials.gov ({trial_count} trials)')
                else:
                    logger.debug(f"  {company_name}: Clinical Stage ({trial_count} trials)")
                    return ('Clinical Stage', 0.70, f'ClinicalTrials.gov ({trial_count} trials)')

        # Priority 4: Check focus areas for classification hints
        self.cursor.execute("""
            SELECT GROUP_CONCAT(focus_area, ', ') as focus_areas
            FROM company_focus_areas
            WHERE company_id = ?
        """, (company_id,))
        focus_data = self.cursor.fetchone()

        if focus_data and focus_data[0]:
            focus_areas = focus_data[0].lower()

            # Service provider indicators
            service_keywords = ['cro', 'contract research', 'cdmo', 'contract manufacturing',
                              'consulting', 'laboratory services', 'testing']
            if any(kw in focus_areas for kw in service_keywords):
                logger.debug(f"  {company_name}: Private (service provider)")
                return ('Private', 0.65, 'Focus area analysis (service provider)')

            # Research indicators
            research_keywords = ['research', 'discovery', 'platform', 'preclinical', 'early-stage']
            if any(kw in focus_areas for kw in research_keywords):
                logger.debug(f"  {company_name}: Private (research-stage)")
                return ('Private', 0.60, 'Focus area analysis (research)')

        # Priority 5: Default to Private for companies with some data
        if company_info[1]:  # Has website
            logger.debug(f"  {company_name}: Private (default with website)")
            return ('Private', 0.55, 'Default classification')

        # Final: Unknown only when truly no information
        logger.debug(f"  {company_name}: Unknown (no classification signals)")
        return ('Unknown', 0.30, 'No classification signals')

    def update_all_classifications(self):
        """Update classifications for all companies in the database"""

        logger.info("Starting comprehensive classification update...")

        # Get all companies (with limit if specified)
        query = "SELECT company_id FROM companies ORDER BY company_name"
        if self.limit:
            query += f" LIMIT {self.limit}"

        self.cursor.execute(query)
        companies = self.cursor.fetchall()

        total = len(companies)
        logger.info(f"Processing {total} companies...")

        if self.dry_run:
            logger.info("DRY RUN: Simulating changes only")

        for i, (company_id,) in enumerate(companies):
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{total} ({i/total*100:.1f}%)")

            self.stats['total'] += 1

            # Get new classification
            new_stage, confidence, source = self.classify_company(company_id)

            # Check existing classification
            self.cursor.execute("""
                SELECT company_stage, classification_source
                FROM company_classifications
                WHERE company_id = ? AND is_current = 1
            """, (company_id,))
            existing = self.cursor.fetchone()

            # Update or insert classification
            if existing:
                existing_stage, existing_source = existing

                # Only update if different or improved confidence
                if new_stage != existing_stage or 'improved' in source.lower():
                    if not self.dry_run:
                        # Mark old as not current
                        self.cursor.execute("""
                            UPDATE company_classifications
                            SET is_current = 0
                            WHERE company_id = ? AND is_current = 1
                        """, (company_id,))

                        # Insert new classification
                        self.cursor.execute("""
                            INSERT INTO company_classifications (
                                company_id, company_stage, classification_method,
                                classification_confidence, classification_source, is_current
                            ) VALUES (?, ?, ?, ?, ?, 1)
                        """, (company_id, new_stage, 'improved_classifier', confidence, source))

                    self.stats['updated'] += 1
                    logger.debug(f"{'[DRY RUN] ' if self.dry_run else ''}Updated: {company_id} from {existing_stage} to {new_stage}")
                else:
                    self.stats['skipped'] += 1
            else:
                # Insert new classification
                if not self.dry_run:
                    self.cursor.execute("""
                        INSERT INTO company_classifications (
                            company_id, company_stage, classification_method,
                            classification_confidence, classification_source, is_current
                        ) VALUES (?, ?, ?, ?, ?, 1)
                    """, (company_id, new_stage, 'improved_classifier', confidence, source))

                self.stats['updated'] += 1
                logger.debug(f"{'[DRY RUN] ' if self.dry_run else ''}Classified: {company_id} as {new_stage}")

            # Update statistics
            self.stats[new_stage] += 1

        # Commit all changes
        if not self.dry_run:
            self.conn.commit()

    def add_defunct_detection(self):
        """Add defunct company detection based on SEC filing signals

        NOTE: This method is very conservative about marking companies as defunct.
        Many companies that deregister or stop filing are still active private companies.
        Only mark as defunct if there's strong evidence the company no longer exists.
        """

        logger.info("Detecting truly defunct companies from SEC filings...")

        # Only look for companies with very strong defunct signals
        # We're being VERY conservative here - false positives are worse than false negatives
        self.cursor.execute("""
            SELECT
                c.company_id,
                c.company_name,
                s.latest_filing_date,
                s.latest_filing_type,
                s.company_status,
                c.website,
                JULIANDAY('now') - JULIANDAY(s.latest_filing_date) as days_since_filing
            FROM companies c
            JOIN sec_edgar_data s ON c.company_id = s.company_id
            WHERE
                -- Only consider if filing explicitly mentions liquidation/dissolution
                (s.latest_filing_type IN ('15-12B', '15-12G', '25')
                 AND s.latest_filing_date < date('now', '-5 years'))  -- And it's been 5+ years
                OR s.latest_filing_type = 'REVOKED'  -- SEC revoked registration
        """)

        defunct_candidates = self.cursor.fetchall()

        logger.info(f"Found {len(defunct_candidates)} potential defunct companies (being very conservative)")

        defunct_count = 0
        reclassified_count = 0

        for company_id, name, last_filing, filing_type, status, website, days_since in defunct_candidates:
            # Check if company has recent clinical trials (strong signal they're still active)
            self.cursor.execute("""
                SELECT COUNT(*) FROM clinical_trials
                WHERE company_id = ?
                AND start_date > date('now', '-3 years')
            """, (company_id,))
            recent_trials = self.cursor.fetchone()[0]

            if recent_trials > 0:
                logger.debug(f"  {name}: Has recent trials, NOT marking as defunct")
                continue

            # Companies that filed deregistration forms should be "Private with SEC Filings"
            # unless there's strong evidence they're actually defunct
            if filing_type in ['15-12B', '15-12G', '25']:
                # These are deregistration forms - company went private
                # Only mark as defunct if it's been MANY years and no website
                if days_since and days_since > 1825 and not website:  # 5+ years, no website
                    # This might be defunct
                    classification = 'Defunct'
                    confidence = 0.70
                    reason = f"Deregistration {int(days_since/365)} years ago, no website"
                else:
                    # Company deregistered but likely still active as private
                    classification = 'Private with SEC Filings'
                    confidence = 0.85
                    reason = f"Deregistered (Form {filing_type})"
                    reclassified_count += 1

            elif filing_type == 'REVOKED':
                # SEC revoked - this is stronger signal but still might be active private
                if not website:
                    classification = 'Defunct'
                    confidence = 0.80
                    reason = "SEC registration revoked, no website"
                else:
                    classification = 'Private with SEC Filings'
                    confidence = 0.75
                    reason = "SEC registration revoked but has website"
                    reclassified_count += 1
            else:
                # Skip this company
                continue

            # Update classification
            if not self.dry_run:
                self.cursor.execute("""
                    UPDATE company_classifications
                    SET is_current = 0
                    WHERE company_id = ? AND is_current = 1
                """, (company_id,))

                self.cursor.execute("""
                    INSERT INTO company_classifications (
                        company_id, company_stage, classification_method,
                        classification_confidence, classification_source, is_current
                    ) VALUES (?, ?, ?, ?, ?, 1)
                """, (company_id, classification, 'sec_filing_analysis', confidence, reason))

            if classification == 'Defunct':
                defunct_count += 1
                logger.debug(f"{'[DRY RUN] ' if self.dry_run else ''}Marked as defunct: {name} ({reason})")
            else:
                logger.debug(f"{'[DRY RUN] ' if self.dry_run else ''}Reclassified as {classification}: {name} ({reason})")

        if not self.dry_run:
            self.conn.commit()
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Marked {defunct_count} companies as truly defunct")
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Reclassified {reclassified_count} companies as Private with SEC Filings")

    def print_statistics(self):
        """Print classification statistics"""

        # Get final statistics from database
        self.cursor.execute("""
            SELECT company_stage, COUNT(*) as count
            FROM company_classifications
            WHERE is_current = 1
            GROUP BY company_stage
            ORDER BY count DESC
        """)

        classifications = self.cursor.fetchall()

        # Get total companies
        self.cursor.execute("SELECT COUNT(*) FROM companies")
        total = self.cursor.fetchone()[0]

        # Get companies without classification
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM companies c
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE cc.company_id IS NULL
        """)
        unclassified = self.cursor.fetchone()[0]

        logger.info("\n" + "="*60)
        logger.info("CLASSIFICATION RESULTS")
        logger.info("="*60)
        logger.info(f"Total companies: {total}")
        logger.info(f"Processing stats:")
        logger.info(f"  Updated: {self.stats['updated']}")
        logger.info(f"  Skipped: {self.stats['skipped']}")
        logger.info(f"\nClassification breakdown:")

        for stage, count in classifications:
            pct = count / total * 100
            logger.info(f"  {stage:30s}: {count:4d} ({pct:5.1f}%)")

        if unclassified > 0:
            logger.info(f"  {'Unclassified':30s}: {unclassified:4d} ({unclassified/total*100:5.1f}%)")

        # Calculate Unknown percentage
        unknown_count = next((count for stage, count in classifications if stage == 'Unknown'), 0)
        unknown_pct = (unknown_count + unclassified) / total * 100

        logger.info(f"\nTotal Unknown/Unclassified: {unknown_count + unclassified} ({unknown_pct:.1f}%)")
        logger.info("="*60)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main entry point with safety flags"""
    parser = argparse.ArgumentParser(
        description="Classify biotech companies with safety features"
    )
    parser.add_argument(
        '--db',
        default='data/bayarea_biotech_sources.db',
        help='Database path (default: production database)'
    )
    parser.add_argument(
        '--test-db',
        action='store_true',
        help='Use test database (data/test_biotech.db)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying database'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of companies to process'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine database path
    db_path = args.db
    if args.test_db:
        db_path = 'data/test_biotech.db'
        logger.info("Using TEST database")

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be saved")

    if args.limit:
        logger.info(f"Processing limited to {args.limit} companies")

    logger.info("Starting Improved Company Classification")
    logger.info("New categories: Public / Private with SEC Filings / Clinical Stage / Private / Unknown")
    logger.info(f"Database: {db_path}")
    logger.info("")

    try:
        classifier = ImprovedCompanyClassifier(db_path=db_path)

        # Set dry run and limit in classifier
        classifier.dry_run = args.dry_run
        classifier.limit = args.limit

        # Run classification update
        classifier.update_all_classifications()

        # Add defunct detection
        classifier.add_defunct_detection()

        # Print statistics
        classifier.print_statistics()

        classifier.close()

        if args.dry_run:
            logger.info("\n✓ DRY RUN complete (no changes saved)")
        else:
            logger.info("\n✓ Classification complete!")
        return 0

    except Exception as e:
        logger.error(f"Classification failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())