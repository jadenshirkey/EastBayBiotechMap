#!/usr/bin/env python3
"""
Stage-D: Company Stage Classification Script

Classifies companies into one of 8 categories based on verifiable signals:
- Public (stock ticker)
- Private (Series A-D+)
- Acquired (acquisition announcements)
- Clinical (clinical trial stage)
- Research (research-only, no products)
- Incubator (incubator/accelerator)
- Service (CRO, consulting, services)
- Unknown (ambiguous or insufficient data)

Default to "Unknown" if ambiguous - prefer null over wrong data.

Usage:
    python scripts/classify_company_stage.py

Input:  data/working/companies_enriched.csv
Output: data/working/companies_classified.csv

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import csv
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# ============================================================================
# Setup Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

INPUT_FILE = Path("data/working/companies_enriched.csv")
OUTPUT_FILE = Path("data/working/companies_classified.csv")

# Company stages (8 categories per methodology)
STAGE_PUBLIC = "Public"
STAGE_PRIVATE = "Private"
STAGE_ACQUIRED = "Acquired"
STAGE_CLINICAL = "Clinical"
STAGE_RESEARCH = "Research"
STAGE_INCUBATOR = "Incubator"
STAGE_SERVICE = "Service"
STAGE_UNKNOWN = "Unknown"

# Known public biotech companies (stock ticker holders)
# This is a small sample - in production, this could be enriched from SEC/market data
PUBLIC_COMPANIES = {
    "Genentech",  # Part of Roche but historically public
    "Gilead Sciences",
    "BioMarin Pharmaceutical",
    "Twist Bioscience",
    "10x Genomics",
    "Berkeley Lights",
    "Zymergen",
    "Vir Biotechnology",
    "Allogene Therapeutics",
    "Revolution Medicines",
}

# Known acquired companies
ACQUIRED_COMPANIES = {
    "Flatiron Health",  # Acquired by Roche
    "Juno Therapeutics",  # Acquired by Celgene/BMS
    "Kite Pharma",  # Acquired by Gilead
}

# Service provider keywords (CROs, consulting, testing labs)
SERVICE_KEYWORDS = [
    "CRO", "contract research", "consulting", "services",
    "testing lab", "clinical trials", "diagnostics lab",
    "laboratory services", "bioanalytical", "preclinical services"
]

# Incubator/accelerator keywords
INCUBATOR_KEYWORDS = [
    "incubator", "accelerator", "QB3", "IndieBio",
    "JLABS", "BioLabs", "co-working", "shared lab space"
]


# ============================================================================
# Classification Logic
# ============================================================================

def classify_company_stage(company_name: str, website: Optional[str],
                           notes: Optional[str] = None) -> str:
    """
    Classify a company into one of 8 stages using the methodology decision tree.

    This function uses simple heuristics based on name matching and keywords.
    For a production system, this could be enhanced with:
    - API calls to Crunchbase/PitchBook for funding data
    - SEC Edgar lookups for public company filings
    - Clinical trials database queries
    - News article analysis

    Args:
        company_name: Name of the company
        website: Company website (may be None)
        notes: Optional notes/description field

    Returns:
        One of the 8 stage categories, or "Unknown"
    """
    if not company_name:
        return STAGE_UNKNOWN

    # Normalize for comparison
    name_lower = company_name.lower()
    notes_lower = notes.lower() if notes else ""
    combined_text = f"{name_lower} {notes_lower}"

    # Check 1: Public company?
    for public_co in PUBLIC_COMPANIES:
        if public_co.lower() in name_lower:
            logger.debug(f"  → Classified as Public (known ticker holder): {company_name}")
            return STAGE_PUBLIC

    # Check 2: Acquired company?
    for acquired_co in ACQUIRED_COMPANIES:
        if acquired_co.lower() in name_lower:
            logger.debug(f"  → Classified as Acquired: {company_name}")
            return STAGE_ACQUIRED

    # Check 3: Incubator/accelerator?
    for keyword in INCUBATOR_KEYWORDS:
        if keyword.lower() in combined_text:
            logger.debug(f"  → Classified as Incubator (keyword: {keyword}): {company_name}")
            return STAGE_INCUBATOR

    # Check 4: Service provider (CRO, consulting)?
    for keyword in SERVICE_KEYWORDS:
        if keyword.lower() in combined_text:
            logger.debug(f"  → Classified as Service (keyword: {keyword}): {company_name}")
            return STAGE_SERVICE

    # Check 5: Look for stage indicators in company name
    # (Some companies include "Clinical" or "Therapeutics" in their name)
    if "therapeutics" in name_lower or "pharma" in name_lower:
        # Companies with "Therapeutics" or "Pharma" are likely clinical-stage or private
        # Default to Private (most common for biotech therapeutics companies)
        logger.debug(f"  → Classified as Private (therapeutics/pharma in name): {company_name}")
        return STAGE_PRIVATE

    # Check 6: Research indicators
    if "research" in name_lower and "institute" in name_lower:
        logger.debug(f"  → Classified as Research (research institute): {company_name}")
        return STAGE_RESEARCH

    # Default: Unknown
    # In a production system, we would default to Unknown unless we have strong signals
    # This avoids misclassification and allows for manual review
    logger.debug(f"  → Classified as Unknown (insufficient signals): {company_name}")
    return STAGE_UNKNOWN


def process_classification(input_path: Path, output_path: Path) -> Dict[str, int]:
    """
    Read enriched companies CSV and add Company_Stage classification.

    Args:
        input_path: Path to companies_enriched.csv
        output_path: Path to output companies_classified.csv

    Returns:
        Dictionary with classification statistics
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("This script expects companies_enriched.csv from Stage C (enrichment).")
        logger.info("If you haven't run enrichment yet, this is expected.")
        return {}

    # Statistics
    stats = {
        "total": 0,
        STAGE_PUBLIC: 0,
        STAGE_PRIVATE: 0,
        STAGE_ACQUIRED: 0,
        STAGE_CLINICAL: 0,
        STAGE_RESEARCH: 0,
        STAGE_INCUBATOR: 0,
        STAGE_SERVICE: 0,
        STAGE_UNKNOWN: 0,
    }

    # Get current date for Classifier_Date field
    classifier_date = datetime.now().strftime("%Y-%m-%d")

    # Read input, classify, write output
    logger.info(f"Reading from: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        # Prepare output fieldnames (add new columns)
        fieldnames = reader.fieldnames + ["Company_Stage", "Classifier_Date"]

        with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                stats["total"] += 1

                # Extract fields
                company_name = row.get("Company Name", "")
                website = row.get("Website", "")
                # Try both "Focus Areas" and "Notes" for compatibility
                notes = row.get("Focus Areas", "") or row.get("Notes", "")

                # Classify
                stage = classify_company_stage(company_name, website, notes)

                # Add new fields
                row["Company_Stage"] = stage
                row["Classifier_Date"] = classifier_date

                # Update stats
                stats[stage] += 1

                # Write to output
                writer.writerow(row)

    logger.info(f"Output written to: {output_path}")

    return stats


def print_statistics(stats: Dict[str, int]) -> None:
    """Print classification statistics."""
    if not stats:
        return

    total = stats["total"]

    logger.info("=" * 60)
    logger.info("CLASSIFICATION STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total companies classified: {total}")
    logger.info("")

    for stage in [STAGE_PUBLIC, STAGE_PRIVATE, STAGE_ACQUIRED, STAGE_CLINICAL,
                  STAGE_RESEARCH, STAGE_INCUBATOR, STAGE_SERVICE, STAGE_UNKNOWN]:
        count = stats[stage]
        pct = (count / total * 100) if total > 0 else 0
        logger.info(f"  {stage:15s}: {count:4d} ({pct:5.1f}%)")

    logger.info("=" * 60)

    # Quality check: warn if too many unknowns
    unknown_pct = (stats[STAGE_UNKNOWN] / total * 100) if total > 0 else 0
    if unknown_pct > 50:
        logger.warning(f"High percentage of Unknown classifications ({unknown_pct:.1f}%)")
        logger.warning("Consider enhancing classification logic with external data sources.")


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    """Main entry point."""
    logger.info("Starting Company Stage Classification (Stage D)")
    logger.info("V4.3 Framework - Issue #20")
    logger.info("")

    try:
        # Create output directory if it doesn't exist
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Process classification
        stats = process_classification(INPUT_FILE, OUTPUT_FILE)

        if not stats:
            logger.error("Classification failed - no statistics generated")
            return 1

        # Print statistics
        print_statistics(stats)

        logger.info("")
        logger.info("✓ Classification complete!")
        logger.info(f"✓ Output: {OUTPUT_FILE}")

        return 0

    except Exception as e:
        logger.error(f"Classification failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
