#!/usr/bin/env python3
"""
Restore descriptions from V4 verbose focus areas
Uses the V4 companies.csv to populate empty description fields
"""

import sqlite3
import pandas as pd
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def restore_descriptions(
    db_path='data/bayarea_biotech_sources.db',
    v4_csv='data/v4_companies.csv',
    dry_run=True
):
    """
    Restore descriptions from V4 verbose focus areas
    """
    # Load V4 data
    logger.info("Loading V4 companies data...")
    v4_df = pd.read_csv(v4_csv)
    logger.info(f"Loaded {len(v4_df)} companies from V4")

    # Filter to verbose focus areas (> 50 chars) that could be good descriptions
    verbose_v4 = v4_df[v4_df['Focus Areas'].str.len() > 50].copy()
    logger.info(f"Found {len(verbose_v4)} companies with verbose focus areas (>50 chars)")

    # Connect to current database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("=" * 70)
    logger.info("RESTORING DESCRIPTIONS FROM V4 FOCUS AREAS")
    logger.info("=" * 70)

    # Get companies without descriptions
    cursor.execute("""
        SELECT company_id, company_name, description
        FROM companies
        WHERE description IS NULL OR description = ''
    """)

    companies_without_desc = cursor.fetchall()
    logger.info(f"Found {len(companies_without_desc)} companies without descriptions")

    updates = []
    matched = 0
    not_matched = []

    for company_id, company_name, _ in companies_without_desc:
        # Try to match by company name (case insensitive)
        v4_match = verbose_v4[verbose_v4['Company Name'].str.lower() == company_name.lower()]

        if len(v4_match) > 0:
            matched += 1
            # Use the verbose focus area as description
            description = v4_match.iloc[0]['Focus Areas']
            updates.append((description, company_id))

            if matched <= 5:  # Show first 5 examples
                logger.info(f"\nMatched: {company_name}")
                logger.info(f"  Description: {description[:100]}...")
        else:
            # Try fuzzy matching by removing common suffixes
            clean_name = company_name.replace(' Inc', '').replace(' Inc.', '').replace(' LLC', '').replace(' Corp', '').strip()
            v4_match = verbose_v4[verbose_v4['Company Name'].str.contains(clean_name, case=False, na=False)]

            if len(v4_match) > 0:
                matched += 1
                description = v4_match.iloc[0]['Focus Areas']
                updates.append((description, company_id))

                if matched <= 5:
                    logger.info(f"\nFuzzy matched: {company_name}")
                    logger.info(f"  Description: {description[:100]}...")
            else:
                not_matched.append(company_name)

    logger.info(f"\nMatched {matched} companies with V4 verbose focus areas")
    logger.info(f"Will update {len(updates)} company descriptions")

    if len(not_matched) > 0 and len(not_matched) < 20:
        logger.info(f"\nNot matched ({len(not_matched)}): {', '.join(not_matched[:10])}")

    if not dry_run and updates:
        logger.info("\nUpdating descriptions...")
        cursor.executemany(
            "UPDATE companies SET description = ? WHERE company_id = ?",
            updates
        )
        conn.commit()
        logger.info("✓ Descriptions updated successfully")

        # Verify the update
        cursor.execute("""
            SELECT COUNT(*)
            FROM companies
            WHERE description IS NOT NULL AND description != ''
        """)
        total_with_desc = cursor.fetchone()[0]
        logger.info(f"Total companies with descriptions now: {total_with_desc}")

        # Check California companies specifically
        cursor.execute("""
            SELECT COUNT(*)
            FROM companies
            WHERE (description IS NOT NULL AND description != '')
            AND google_address LIKE '%, CA %'
        """)
        ca_with_desc = cursor.fetchone()[0]
        logger.info(f"California companies with descriptions: {ca_with_desc}")

    elif dry_run:
        logger.info("\n*** DRY RUN MODE - No changes made ***")
        logger.info(f"Would update {len(updates)} descriptions")

    conn.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Restore descriptions from V4 focus areas')
    parser.add_argument('--db', default='data/bayarea_biotech_sources.db',
                        help='Database path')
    parser.add_argument('--v4-csv', default='data/v4_companies.csv',
                        help='V4 companies CSV path')
    parser.add_argument('--execute', action='store_true',
                        help='Execute changes (default is dry-run)')

    args = parser.parse_args()

    restore_descriptions(
        db_path=args.db,
        v4_csv=args.v4_csv,
        dry_run=not args.execute
    )

if __name__ == "__main__":
    main()