#!/usr/bin/env python3
"""
Clean and standardize focus areas to be concise 4-5 word descriptions
Moves verbose descriptions to the description field
"""

import sqlite3
import re
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Mapping of verbose focus areas to concise categories
FOCUS_AREA_MAPPINGS = {
    # Gene and Cell Therapy
    r'.*gene therap.*': 'Gene Therapy',
    r'.*cell therap.*': 'Cell Therapy',
    r'.*CAR-T.*': 'CAR-T Therapy',
    r'.*TCR.*therap.*': 'TCR Therapies',
    r'.*stem cell.*': 'Stem Cell Therapy',

    # Diagnostics
    r'.*molecular diagnos.*': 'Molecular Diagnostics',
    r'.*cancer diagnos.*': 'Cancer Diagnostics',
    r'.*liquid biops.*': 'Liquid Biopsy',
    r'.*diagnos.*': 'Diagnostics',

    # Drug Development
    r'.*small molecule.*': 'Small Molecules',
    r'.*antibod.*': 'Antibody Development',
    r'.*biologic.*': 'Biologics',
    r'.*vaccine.*': 'Vaccine Development',
    r'.*immuno.*oncolog.*': 'Immuno-Oncology',
    r'.*immunotherap.*': 'Immunotherapy',

    # Services
    r'.*contract manufactur.*': 'Contract Manufacturing',
    r'.*CDMO.*': 'CDMO Services',
    r'.*CRO.*': 'CRO Services',
    r'.*clinical.*service.*': 'Clinical Services',
    r'.*bioanalytic.*': 'Bioanalytical Services',

    # Platforms
    r'.*genomics platform.*': 'Genomics Platform',
    r'.*proteomics.*': 'Proteomics Platform',
    r'.*AI.*drug.*': 'AI Drug Discovery',
    r'.*computational.*': 'Computational Biology',
    r'.*synthetic biolog.*': 'Synthetic Biology',

    # Specific Disease Areas
    r'.*oncolog.*': 'Oncology',
    r'.*neurodegen.*': 'Neurodegeneration',
    r'.*metabolic disease.*': 'Metabolic Diseases',
    r'.*rare disease.*': 'Rare Diseases',
    r'.*liver.*': 'Liver Treatments',
    r'.*cardiovascular.*': 'Cardiovascular',

    # Other
    r'.*medical device.*': 'Medical Devices',
    r'.*research tool.*': 'Research Tools',
    r'.*bioprocess.*': 'Bioprocessing',
    r'.*formulation.*': 'Drug Formulation',
}

def clean_focus_area(focus_area):
    """
    Clean a single focus area to be concise
    Returns tuple of (concise_focus, verbose_description)
    """
    if not focus_area or focus_area.strip() == '':
        return None, None

    focus_area = focus_area.strip()

    # Check if it's already concise (< 30 characters)
    if len(focus_area) <= 30:
        return focus_area, None

    # Try to match against known patterns
    lower_focus = focus_area.lower()
    for pattern, concise in FOCUS_AREA_MAPPINGS.items():
        if re.match(pattern, lower_focus):
            return concise, focus_area  # Return concise version and keep original as description

    # If no match, try to extract key terms
    # Remove company names and excessive details
    if '(' in focus_area:
        # Remove parenthetical content
        focus_area = re.sub(r'\([^)]*\)', '', focus_area).strip()

    # If still too long, take first 4-5 words
    words = focus_area.split()
    if len(words) > 5:
        concise = ' '.join(words[:5])
        return concise, focus_area

    return focus_area, None

def clean_all_focus_areas(db_path='data/bayarea_biotech_sources.db', dry_run=True):
    """
    Clean all focus areas in the database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("=" * 70)
    logger.info("FOCUS AREAS CLEANUP")
    logger.info("=" * 70)

    # Get all focus areas
    cursor.execute("""
        SELECT focus_id, company_id, focus_area
        FROM company_focus_areas
        WHERE focus_area IS NOT NULL AND focus_area != ''
        ORDER BY LENGTH(focus_area) DESC
    """)

    focus_areas = cursor.fetchall()
    logger.info(f"Found {len(focus_areas)} focus areas to process")

    updates = []
    verbose_count = 0

    for focus_id, company_id, original in focus_areas:
        concise, description = clean_focus_area(original)

        if concise and concise != original:
            verbose_count += 1
            updates.append((concise, focus_id))

            # Log verbose ones
            if len(original) > 50:
                logger.info(f"\nVerbose focus area found:")
                logger.info(f"  Original: {original[:100]}...")
                logger.info(f"  Concise:  {concise}")

    logger.info(f"\nFound {verbose_count} verbose focus areas to clean")

    if not dry_run and updates:
        logger.info(f"Updating {len(updates)} focus areas...")
        cursor.executemany(
            "UPDATE company_focus_areas SET focus_area = ? WHERE focus_id = ?",
            updates
        )
        conn.commit()
        logger.info("✓ Focus areas updated successfully")
    elif dry_run:
        logger.info("\n*** DRY RUN MODE - No changes made ***")
        logger.info(f"Would update {len(updates)} focus areas")

    # Show statistics
    cursor.execute("""
        SELECT
            AVG(LENGTH(focus_area)) as avg_length,
            MAX(LENGTH(focus_area)) as max_length,
            MIN(LENGTH(focus_area)) as min_length
        FROM company_focus_areas
        WHERE focus_area IS NOT NULL
    """)

    stats = cursor.fetchone()
    logger.info("\nFocus Area Statistics:")
    logger.info(f"  Average length: {stats[0]:.1f} characters")
    logger.info(f"  Max length: {stats[1]} characters")
    logger.info(f"  Min length: {stats[2]} characters")

    conn.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Clean and standardize focus areas')
    parser.add_argument('--db', default='data/bayarea_biotech_sources.db', help='Database path')
    parser.add_argument('--execute', action='store_true', help='Execute changes (default is dry-run)')

    args = parser.parse_args()

    clean_all_focus_areas(
        db_path=args.db,
        dry_run=not args.execute
    )

if __name__ == "__main__":
    main()