#!/usr/bin/env python3
"""
Export California-only companies to CSV for Google My Maps
Reads from SQL database and applies California filter
"""

import sqlite3
import pandas as pd
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def export_california_companies(
    db_path: str = "data/bayarea_biotech_sources.db",
    output_path: str = "data/final/companies.csv",
    limit: int = None,
    validate: bool = True
):
    """
    Export California companies from database to CSV

    Args:
        db_path: Path to SQLite database
        output_path: Path for output CSV file
        limit: Optional limit for testing
        validate: Whether to validate data quality
    """

    logger.info("=" * 70)
    logger.info("EXPORTING CALIFORNIA BIOTECH COMPANIES")
    logger.info("=" * 70)

    # Connect to database
    conn = sqlite3.connect(db_path)

    # Build query for California companies
    query = """
    SELECT DISTINCT
        c.company_id,
        c.company_name,
        COALESCE(c.google_address, c.address) as address,
        c.city,
        c.website,
        c.description,
        c.latitude,
        c.longitude,
        cc.company_stage,
        cc.classification_confidence,
        cc.classification_source,
        -- Count of clinical trials
        (SELECT COUNT(*) FROM clinical_trials WHERE company_id = c.company_id) as clinical_trial_count,
        -- Count of SEC filings
        (SELECT filing_count FROM sec_edgar_data WHERE company_id = c.company_id LIMIT 1) as sec_filing_count,
        -- Focus areas (concatenated)
        (SELECT GROUP_CONCAT(focus_area, '; ')
         FROM company_focus_areas
         WHERE company_id = c.company_id) as focus_areas
    FROM companies c
    LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
    WHERE
        -- California filter - ONLY check if address contains CA (more reliable than city field)
        (c.google_address LIKE '%, CA %'
         OR c.google_address LIKE '%, CA,USA%'
         OR c.google_address LIKE '%, California %'
         OR c.google_address LIKE '%, CA, USA%')
        -- Must have an address for Google My Maps
        AND (c.google_address IS NOT NULL OR c.address IS NOT NULL)
        AND (c.google_address != '' OR c.address != '')
    """

    if limit:
        query += f" LIMIT {limit}"

    # Load data
    logger.info("Loading companies from database...")
    df = pd.read_sql_query(query, conn)
    logger.info(f"Found {len(df)} California companies with addresses")

    # Data validation
    if validate:
        logger.info("\nValidating data quality...")

        # Check for missing critical fields
        missing_stage = df['company_stage'].isna().sum()
        missing_address = df['address'].isna().sum()

        # Check stage distribution
        stage_counts = df['company_stage'].value_counts()

        logger.info(f"  Missing company stage: {missing_stage}")
        logger.info(f"  Missing address: {missing_address} (should be 0)")
        logger.info("\n  Stage distribution:")
        for stage, count in stage_counts.items():
            pct = count / len(df) * 100
            logger.info(f"    {stage:30s}: {count:4d} ({pct:5.1f}%)")

        # Check for non-CA companies that slipped through
        # Since we're filtering by CA addresses, this should be 0
        non_ca_count = df[~df['address'].str.contains(', CA ', na=False)].shape[0]
        if non_ca_count > 0:
            logger.error(f"  ERROR: Found {non_ca_count} companies without ', CA ' in address!")
            logger.error("  Export aborted to prevent non-California companies in output.")
            logger.error("  Please check the database for incorrect city/address data.")
            # Show examples of problematic companies
            non_ca = df[~df['address'].str.contains(', CA ', na=False)]
            for _, row in non_ca.head(5).iterrows():
                logger.error(f"    - {row['company_name']}: {row['address']}")
            conn.close()
            raise ValueError(f"Data validation failed: {non_ca_count} non-California companies detected")

    # Clean up data for export
    logger.info("\nPreparing data for export...")

    # Rename columns for Google My Maps
    export_df = df.rename(columns={
        'company_name': 'Company Name',
        'address': 'Address',
        'city': 'City',
        'website': 'Website',
        'description': 'Description',
        'company_stage': 'Company Stage',
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        'focus_areas': 'Focus Areas',
        'clinical_trial_count': 'Clinical Trials',
        'sec_filing_count': 'SEC Filings'
    })

    # Select and order columns for export
    export_columns = [
        'Company Name',
        'Address',
        'City',
        'Company Stage',
        'Website',
        'Focus Areas',
        'Description',
        'Clinical Trials',
        'SEC Filings'
        # Removed Latitude and Longitude for privacy/security
    ]

    # Filter to only columns that exist
    export_columns = [col for col in export_columns if col in export_df.columns]
    export_df = export_df[export_columns]

    # Fill NaN values
    export_df = export_df.fillna('')

    # Sort by company name
    export_df = export_df.sort_values('Company Name')

    # Write to CSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    export_df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"\n✓ Exported {len(export_df)} companies to {output_path}")

    # Final statistics
    logger.info("\n" + "=" * 70)
    logger.info("EXPORT SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total companies exported: {len(export_df)}")
    logger.info(f"Output file: {output_path}")
    logger.info(f"File size: {output_path.stat().st_size / 1024:.1f} KB")

    conn.close()
    return export_df

def main():
    parser = argparse.ArgumentParser(
        description="Export California biotech companies to CSV"
    )
    parser.add_argument(
        '--db',
        default='data/bayarea_biotech_sources.db',
        help='Database path'
    )
    parser.add_argument(
        '--output',
        default='data/final/companies.csv',
        help='Output CSV path'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of companies (for testing)'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip validation checks'
    )
    parser.add_argument(
        '--filter-california',
        action='store_true',
        default=True,
        help='Filter to California companies only (default: True)'
    )

    args = parser.parse_args()

    export_california_companies(
        db_path=args.db,
        output_path=args.output,
        limit=args.limit,
        validate=not args.no_validate
    )

if __name__ == "__main__":
    main()