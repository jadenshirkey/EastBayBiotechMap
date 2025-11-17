#!/usr/bin/env python3
"""
Fix SEC classification bug - properly classify companies with formerly_public and acquired status
"""

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_sec_classifications(db_path: str = "data/bayarea_biotech_sources.db"):
    """Fix classification for companies with SEC data but incorrect/missing classification"""

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
        # First, get statistics before fix
        cursor.execute("""
            SELECT COUNT(*)
            FROM companies c
            JOIN sec_edgar_data s ON c.company_id = s.company_id
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE cc.company_stage = 'Unknown' OR cc.company_stage IS NULL
        """)
        before_count = cursor.fetchone()[0]

        logger.info(f"Companies with SEC data but Unknown/NULL classification: {before_count}")

        # Get breakdown by status
        cursor.execute("""
            SELECT s.company_status, COUNT(*) as count
            FROM companies c
            JOIN sec_edgar_data s ON c.company_id = s.company_id
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE cc.company_stage = 'Unknown' OR cc.company_stage IS NULL
            GROUP BY s.company_status
        """)

        logger.info("\nBreakdown by SEC status:")
        status_counts = {}
        for status, count in cursor.fetchall():
            status_counts[status] = count
            logger.info(f"  {status}: {count} companies")

        # Fix 1: Mark existing classifications as not current for companies we're updating
        logger.info("\nUpdating existing classifications...")
        cursor.execute("""
            UPDATE company_classifications
            SET is_current = 0
            WHERE company_id IN (
                SELECT c.company_id
                FROM companies c
                JOIN sec_edgar_data s ON c.company_id = s.company_id
                LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
                WHERE (cc.company_stage = 'Unknown' OR cc.company_stage IS NULL)
                AND s.company_status IN ('formerly_public', 'acquired', 'public')
            )
        """)

        # Fix 2: Add proper classifications for formerly_public companies
        logger.info("Adding classifications for formerly_public companies...")
        cursor.execute("""
            INSERT INTO company_classifications (
                company_id, company_stage, classification_method,
                classification_confidence, classification_source, is_current
            )
            SELECT
                c.company_id,
                'Public/Late-Stage',
                'sec_edgar_fix',
                0.85,
                'SEC EDGAR (formerly public)',
                1
            FROM companies c
            JOIN sec_edgar_data s ON c.company_id = s.company_id
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE (cc.company_stage = 'Unknown' OR cc.company_stage IS NULL)
            AND s.company_status = 'formerly_public'
        """)
        formerly_public_fixed = cursor.rowcount
        logger.info(f"  Fixed {formerly_public_fixed} formerly_public companies")

        # Fix 3: Add proper classifications for acquired companies
        logger.info("Adding classifications for acquired companies...")
        cursor.execute("""
            INSERT INTO company_classifications (
                company_id, company_stage, classification_method,
                classification_confidence, classification_source, is_current
            )
            SELECT
                c.company_id,
                'Public/Late-Stage',
                'sec_edgar_fix',
                0.90,
                'SEC EDGAR (acquired)',
                1
            FROM companies c
            JOIN sec_edgar_data s ON c.company_id = s.company_id
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE (cc.company_stage = 'Unknown' OR cc.company_stage IS NULL)
            AND s.company_status = 'acquired'
        """)
        acquired_fixed = cursor.rowcount
        logger.info(f"  Fixed {acquired_fixed} acquired companies")

        # Fix 4: Also fix any public companies that somehow got missed
        logger.info("Checking for any missed public companies...")
        cursor.execute("""
            INSERT INTO company_classifications (
                company_id, company_stage, classification_method,
                classification_confidence, classification_source, is_current
            )
            SELECT
                c.company_id,
                'Public',
                'sec_edgar_fix',
                0.95,
                'SEC EDGAR (public)',
                1
            FROM companies c
            JOIN sec_edgar_data s ON c.company_id = s.company_id
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE (cc.company_stage = 'Unknown' OR cc.company_stage IS NULL)
            AND s.company_status = 'public'
        """)
        public_fixed = cursor.rowcount
        logger.info(f"  Fixed {public_fixed} public companies")

        # Commit changes
        conn.commit()

        # Get statistics after fix
        cursor.execute("""
            SELECT COUNT(*)
            FROM companies c
            JOIN sec_edgar_data s ON c.company_id = s.company_id
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE cc.company_stage = 'Unknown' OR cc.company_stage IS NULL
        """)
        after_count = cursor.fetchone()[0]

        # Get overall Unknown count
        cursor.execute("""
            SELECT COUNT(*)
            FROM companies c
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE cc.company_stage = 'Unknown' OR cc.company_stage IS NULL
        """)
        total_unknown = cursor.fetchone()[0]

        logger.info("\n" + "="*60)
        logger.info("FIX RESULTS")
        logger.info("="*60)
        logger.info(f"Companies with SEC data but Unknown (before): {before_count}")
        logger.info(f"Companies with SEC data but Unknown (after):  {after_count}")
        logger.info(f"Total fixed: {before_count - after_count}")
        logger.info(f"  - Formerly public: {formerly_public_fixed}")
        logger.info(f"  - Acquired: {acquired_fixed}")
        logger.info(f"  - Public: {public_fixed}")

        # Get total companies for percentage calculations
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]

        logger.info(f"\nTotal Unknown companies remaining: {total_unknown}")
        if total_companies > 0:
            logger.info(f"Unknown percentage: {total_unknown / total_companies * 100:.1f}%")
        else:
            logger.info("No companies found in database")

    except Exception as e:
        logger.error(f"Error fixing classifications: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_sec_classifications()