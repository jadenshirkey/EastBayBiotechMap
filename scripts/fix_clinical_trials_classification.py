#!/usr/bin/env python3
"""
Fix clinical trials classification - classify companies with trials but no classification
"""

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_clinical_trials_classifications(db_path: str = "data/bayarea_biotech_sources.db"):
    """Fix classification for companies with clinical trials but no classification"""

    # Validate database path
    from pathlib import Path
    import os

    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    if not os.access(db_path, os.R_OK | os.W_OK):
        raise PermissionError(f"Insufficient permissions for database: {db_path}")

    # Use row factory for safer data access
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Enable foreign key constraints for data integrity
    cursor.execute("PRAGMA foreign_keys = ON")

    try:
        # Get companies with trials but no classification
        cursor.execute("""
            SELECT
                c.company_id,
                c.company_name,
                COUNT(ct.trial_id) as trial_count,
                MAX(CASE
                    WHEN ct.phase IN ('PHASE3', 'PHASE4') THEN 3
                    WHEN ct.phase IN ('PHASE2', 'PHASE2_PHASE3') THEN 2
                    WHEN ct.phase IN ('PHASE1', 'PHASE1_PHASE2', 'EARLY_PHASE1') THEN 1
                    ELSE 0
                END) as max_phase_num,
                MAX(ct.phase) as max_phase
            FROM companies c
            JOIN clinical_trials ct ON c.company_id = ct.company_id
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE cc.company_stage IS NULL
            GROUP BY c.company_id, c.company_name
        """)

        companies_to_fix = cursor.fetchall()
        logger.info(f"Found {len(companies_to_fix)} companies with trials but no classification")

        fixed_count = 0
        for company_id, company_name, trial_count, max_phase_num, max_phase in companies_to_fix:
            # Determine classification based on trial count and phase
            if trial_count >= 5 or max_phase_num >= 2:
                # Multiple trials or Phase 2+ → Public/Late-Stage
                stage = 'Public/Late-Stage'
                confidence = 0.75
            else:
                # Few trials or early phase → Clinical Stage
                stage = 'Clinical Stage'
                confidence = 0.70

            logger.info(f"Classifying {company_name}: {trial_count} trials, max phase {max_phase} → {stage}")

            # Insert classification
            cursor.execute("""
                INSERT INTO company_classifications (
                    company_id, company_stage, classification_method,
                    classification_confidence, classification_source, is_current
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                company_id, stage, 'clinical_trials_fix',
                confidence, f'ClinicalTrials.gov ({trial_count} trials)', 1
            ))
            fixed_count += 1

        # Also check for companies with trials that have 'Unknown' classification
        cursor.execute("""
            SELECT
                c.company_id,
                c.company_name,
                COUNT(ct.trial_id) as trial_count,
                MAX(CASE
                    WHEN ct.phase IN ('PHASE3', 'PHASE4') THEN 3
                    WHEN ct.phase IN ('PHASE2', 'PHASE2_PHASE3') THEN 2
                    WHEN ct.phase IN ('PHASE1', 'PHASE1_PHASE2', 'EARLY_PHASE1') THEN 1
                    ELSE 0
                END) as max_phase_num
            FROM companies c
            JOIN clinical_trials ct ON c.company_id = ct.company_id
            JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE cc.company_stage = 'Unknown'
            GROUP BY c.company_id, c.company_name
        """)

        unknown_with_trials = cursor.fetchall()
        logger.info(f"\nFound {len(unknown_with_trials)} companies with trials classified as Unknown")

        for company_id, company_name, trial_count, max_phase_num in unknown_with_trials:
            # Mark old classification as not current
            cursor.execute("""
                UPDATE company_classifications
                SET is_current = 0
                WHERE company_id = ? AND is_current = 1
            """, (company_id,))

            # Determine new classification
            if trial_count >= 5 or max_phase_num >= 2:
                stage = 'Public/Late-Stage'
                confidence = 0.75
            else:
                stage = 'Clinical Stage'
                confidence = 0.70

            logger.info(f"Re-classifying {company_name}: {trial_count} trials → {stage}")

            # Insert new classification
            cursor.execute("""
                INSERT INTO company_classifications (
                    company_id, company_stage, classification_method,
                    classification_confidence, classification_source, is_current
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                company_id, stage, 'clinical_trials_fix',
                confidence, f'ClinicalTrials.gov ({trial_count} trials)', 1
            ))
            fixed_count += 1

        # Commit changes
        conn.commit()

        # Get statistics after fix
        cursor.execute("""
            SELECT COUNT(*)
            FROM companies c
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE cc.company_stage = 'Unknown' OR cc.company_stage IS NULL
        """)
        total_unknown = cursor.fetchone()[0]

        # Get breakdown of classifications
        cursor.execute("""
            SELECT company_stage, COUNT(*) as count
            FROM company_classifications
            WHERE is_current = 1
            GROUP BY company_stage
            ORDER BY count DESC
        """)

        # Get total companies for percentage calculations
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]

        logger.info("\n" + "="*60)
        logger.info("FIX RESULTS")
        logger.info("="*60)
        logger.info(f"Total companies fixed: {fixed_count}")
        logger.info(f"\nCurrent classification breakdown:")

        total = 0
        for stage, count in cursor.fetchall():
            total += count
            if total_companies > 0:
                logger.info(f"  {stage:25s}: {count:4d} ({count/total_companies*100:5.1f}%)")
            else:
                logger.info(f"  {stage:25s}: {count:4d}")

        logger.info(f"\nTotal Unknown companies remaining: {total_unknown}")
        if total_companies > 0:
            logger.info(f"Unknown percentage: {total_unknown / total_companies * 100:.1f}%")
            logger.info(f"Total classified: {total} ({total/total_companies*100:.1f}%)")
        else:
            logger.info("No companies found in database")

    except Exception as e:
        logger.error(f"Error fixing classifications: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_clinical_trials_classifications()