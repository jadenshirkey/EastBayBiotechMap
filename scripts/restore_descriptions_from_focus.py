#!/usr/bin/env python3
"""
Restore descriptions from original verbose focus areas
Uses the original database to populate empty description fields
"""

import sqlite3
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def restore_descriptions(
    current_db='data/bayarea_biotech_sources.db',
    original_db='data/bayarea_biotech_sources_original.db',
    dry_run=True
):
    """
    Restore descriptions from original verbose focus areas
    """
    # Connect to both databases
    current_conn = sqlite3.connect(current_db)
    current_cursor = current_conn.cursor()

    original_conn = sqlite3.connect(original_db)
    original_cursor = original_conn.cursor()

    logger.info("=" * 70)
    logger.info("RESTORING DESCRIPTIONS FROM ORIGINAL FOCUS AREAS")
    logger.info("=" * 70)

    # Get companies without descriptions
    current_cursor.execute("""
        SELECT company_id, company_name, description
        FROM companies
        WHERE description IS NULL OR description = ''
    """)

    companies_without_desc = current_cursor.fetchall()
    logger.info(f"Found {len(companies_without_desc)} companies without descriptions")

    updates = []

    for company_id, company_name, _ in companies_without_desc:
        # Get original verbose focus areas for this company
        original_cursor.execute("""
            SELECT focus_area
            FROM company_focus_areas
            WHERE company_id = ?
            AND LENGTH(focus_area) > 30
            ORDER BY LENGTH(focus_area) DESC
        """, (company_id,))

        verbose_focus_areas = original_cursor.fetchall()

        if verbose_focus_areas:
            # Use the longest (most descriptive) focus area as description
            description = verbose_focus_areas[0][0]

            # If multiple verbose focus areas, combine them
            if len(verbose_focus_areas) > 1:
                all_verbose = [fa[0] for fa in verbose_focus_areas[:3]]  # Max 3
                description = ". ".join(all_verbose)

            updates.append((description, company_id))

            if len(updates) <= 5:  # Show first 5 examples
                logger.info(f"\nCompany: {company_name}")
                logger.info(f"  New description: {description[:100]}...")

    logger.info(f"\nWill update {len(updates)} company descriptions")

    if not dry_run and updates:
        logger.info("Updating descriptions...")
        current_cursor.executemany(
            "UPDATE companies SET description = ? WHERE company_id = ?",
            updates
        )
        current_conn.commit()
        logger.info("✓ Descriptions updated successfully")

        # Verify the update
        current_cursor.execute("""
            SELECT COUNT(*)
            FROM companies
            WHERE description IS NOT NULL AND description != ''
        """)
        total_with_desc = current_cursor.fetchone()[0]
        logger.info(f"Total companies with descriptions now: {total_with_desc}")

    elif dry_run:
        logger.info("\n*** DRY RUN MODE - No changes made ***")
        logger.info(f"Would update {len(updates)} descriptions")

    current_conn.close()
    original_conn.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Restore descriptions from original focus areas')
    parser.add_argument('--current-db', default='data/bayarea_biotech_sources.db',
                        help='Current database path')
    parser.add_argument('--original-db', default='data/bayarea_biotech_sources_original.db',
                        help='Original database path with verbose focus areas')
    parser.add_argument('--execute', action='store_true',
                        help='Execute changes (default is dry-run)')

    args = parser.parse_args()

    restore_descriptions(
        current_db=args.current_db,
        original_db=args.original_db,
        dry_run=not args.execute
    )

if __name__ == "__main__":
    main()