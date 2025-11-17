#!/usr/bin/env python3
"""Fix data quality issues in the source database"""

import sqlite3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_database_issues():
    """Fix known data quality issues in the database"""

    logger.info("Connecting to database...")
    conn = sqlite3.connect("data/bayarea_biotech_sources.db")
    cursor = conn.cursor()

    # Fix 1: Intuitive Surgical address
    logger.info("Fixing Intuitive Surgical address...")
    cursor.execute("""
        UPDATE companies
        SET google_address = '1020 Kifer Rd, Sunnyvale, CA 94086, USA'
        WHERE company_name = 'Intuitive Surgical'
        AND google_address = '21627043, Sunnyvale, CA 94086, USA'
    """)
    intuitive_rows = cursor.rowcount
    logger.info(f"  Updated {intuitive_rows} row(s) for Intuitive Surgical")

    # Fix 2: GE HealthCare missing city
    logger.info("Fixing GE HealthCare city field...")
    cursor.execute("""
        UPDATE companies
        SET city = 'Sunnyvale'
        WHERE company_name = 'GE HealthCare'
        AND (city IS NULL OR city = '')
        AND google_address LIKE '%Sunnyvale%'
    """)
    ge_rows = cursor.rowcount
    logger.info(f"  Updated {ge_rows} row(s) for GE HealthCare")

    # Commit changes
    conn.commit()

    # Verify fixes
    logger.info("\nVerifying fixes...")
    cursor.execute("""
        SELECT company_name, google_address, city
        FROM companies
        WHERE company_name IN ('Intuitive Surgical', 'GE HealthCare')
        ORDER BY company_name
    """)

    for row in cursor.fetchall():
        logger.info(f"  {row[0]}: {row[1]} | City: {row[2]}")

    conn.close()
    logger.info("\n✓ Database fixes completed!")

    return intuitive_rows + ge_rows

if __name__ == "__main__":
    fixed_count = fix_database_issues()
    print(f"\nTotal rows fixed: {fixed_count}")