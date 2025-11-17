#!/usr/bin/env python3
"""
Fix incorrect city data for companies that are not actually in California
These companies have California city names but addresses in other states/countries
"""

import sqlite3
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Companies with incorrect California cities (but non-CA addresses)
# Using exact names from database
CITY_CORRECTIONS = [
    # company_name, correct_city, correct_state/country
    ("Alimentiv", "London", "ON, Canada"),
    ("Allucent", "Cary", "NC"),
    ("Apellis Pharmaceuticals", "Waltham", "MA"),
    ("Eliquent Life Sciences", "Washington", "DC"),
    ("HAYA Therapeutics", "Epalinges", "Switzerland"),
    ("Level Zero Health", "London", "UK"),
    ("Oncolytics Biotech", "Calgary", "AB, Canada"),
]

def fix_cities(db_path='data/bayarea_biotech_sources.db', dry_run=False):
    """
    Fix incorrect city data for non-California companies
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("=" * 70)
    logger.info("FIXING NON-CALIFORNIA COMPANY CITIES")
    logger.info("=" * 70)

    fixed_count = 0

    for company_name, correct_city, location in CITY_CORRECTIONS:
        # Find the company
        cursor.execute("""
            SELECT company_id, company_name, city, google_address
            FROM companies
            WHERE company_name = ?
        """, (company_name,))

        result = cursor.fetchone()

        if result:
            company_id, name, old_city, address = result
            logger.info(f"\nCompany: {name}")
            logger.info(f"  Old city: {old_city}")
            logger.info(f"  New city: {correct_city} ({location})")
            logger.info(f"  Address: {address[:80]}...")

            if not dry_run:
                cursor.execute("""
                    UPDATE companies
                    SET city = ?
                    WHERE company_id = ?
                """, (correct_city, company_id))
                fixed_count += 1
        else:
            logger.warning(f"Company not found: {company_name}")

    if not dry_run and fixed_count > 0:
        conn.commit()
        logger.info(f"\n✓ Fixed {fixed_count} company cities")
    elif dry_run:
        logger.info("\n*** DRY RUN MODE - No changes made ***")
        logger.info(f"Would fix {len(CITY_CORRECTIONS)} companies")

    conn.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix incorrect city data')
    parser.add_argument('--db', default='data/bayarea_biotech_sources.db', help='Database path')
    parser.add_argument('--execute', action='store_true', help='Execute changes (default is dry-run)')

    args = parser.parse_args()

    fix_cities(
        db_path=args.db,
        dry_run=not args.execute
    )

if __name__ == "__main__":
    main()