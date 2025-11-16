#!/usr/bin/env python3
"""
Stage-F (QC Part 2): Manual Review Queue Generation

Generates two review queues for manual QC:
1. spot_check_sample.csv - 10 random Tier 1/2 companies (high confidence)
2. tier_4_review.csv - ALL Tier 4 companies (flagged for review)

Tiers based on Confidence score:
- Tier 1: Confidence ≥ 0.95 (BPG + Google confirm same eTLD+1)
- Tier 2: Confidence 0.90-0.95 (BPG ground truth, Google mismatch/missing)
- Tier 3: Confidence 0.75-0.90 (AI validated via Path B)
- Tier 4: Confidence < 0.75 (flagged for manual review)

Usage:
    python scripts/generate_review_queues.py

Input:  data/working/companies_focused.csv
Output: data/working/spot_check_sample.csv
        data/working/tier_4_review.csv

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import csv
import sys
import logging
import random
from pathlib import Path
from typing import List, Dict, Tuple

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

INPUT_FILE = Path("data/working/companies_focused.csv")
SPOT_CHECK_FILE = Path("data/working/spot_check_sample.csv")
TIER_4_FILE = Path("data/working/tier_4_review.csv")

# Tier thresholds
TIER_1_THRESHOLD = 0.95
TIER_2_THRESHOLD = 0.90
TIER_3_THRESHOLD = 0.75

# Spot check sample size
SPOT_CHECK_SIZE = 10

# Random seed for reproducible sampling
RANDOM_SEED = 42


# ============================================================================
# Tier Calculation
# ============================================================================

def calculate_tier(confidence: float) -> int:
    """
    Calculate tier based on confidence score.

    Args:
        confidence: Confidence score (0.0 to 1.0)

    Returns:
        Tier number (1, 2, 3, or 4)
    """
    if confidence >= TIER_1_THRESHOLD:
        return 1
    elif confidence >= TIER_2_THRESHOLD:
        return 2
    elif confidence >= TIER_3_THRESHOLD:
        return 3
    else:
        return 4


def get_confidence_from_row(row: Dict) -> float:
    """
    Extract confidence score from a row.

    Tries multiple fields for compatibility:
    - Confidence (from Path B)
    - Confidence_Det (from Path A)

    Args:
        row: Company data row

    Returns:
        Confidence score, or 0.0 if not found
    """
    # Try "Confidence" first (Path B)
    confidence_str = row.get("Confidence", "").strip()

    # Fall back to "Confidence_Det" (Path A)
    if not confidence_str:
        confidence_str = row.get("Confidence_Det", "").strip()

    # Parse as float
    try:
        return float(confidence_str)
    except (ValueError, TypeError):
        # If no valid confidence score, treat as Tier 4 (lowest confidence)
        return 0.0


# ============================================================================
# Review Queue Generation
# ============================================================================

def generate_review_queues(input_path: Path,
                           spot_check_path: Path,
                           tier_4_path: Path) -> Dict[str, int]:
    """
    Generate manual review queues.

    Args:
        input_path: Path to companies_focused.csv
        spot_check_path: Path to output spot_check_sample.csv
        tier_4_path: Path to output tier_4_review.csv

    Returns:
        Dictionary with statistics
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("This script expects companies_focused.csv from Stage E (focus extraction).")
        return {}

    # Load data and categorize by tier
    logger.info(f"Loading data from: {input_path}")

    tier_1_companies = []
    tier_2_companies = []
    tier_3_companies = []
    tier_4_companies = []

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            confidence = get_confidence_from_row(row)
            tier = calculate_tier(confidence)

            # Add tier to row for output
            row_with_tier = row.copy()
            row_with_tier["Tier"] = str(tier)
            row_with_tier["Confidence_Score"] = f"{confidence:.3f}"

            if tier == 1:
                tier_1_companies.append(row_with_tier)
            elif tier == 2:
                tier_2_companies.append(row_with_tier)
            elif tier == 3:
                tier_3_companies.append(row_with_tier)
            else:  # tier == 4
                tier_4_companies.append(row_with_tier)

    # Statistics
    stats = {
        "total": len(tier_1_companies) + len(tier_2_companies) + len(tier_3_companies) + len(tier_4_companies),
        "tier_1": len(tier_1_companies),
        "tier_2": len(tier_2_companies),
        "tier_3": len(tier_3_companies),
        "tier_4": len(tier_4_companies),
    }

    logger.info(f"Loaded {stats['total']} companies")
    logger.info(f"  Tier 1 (≥0.95): {stats['tier_1']}")
    logger.info(f"  Tier 2 (0.90-0.95): {stats['tier_2']}")
    logger.info(f"  Tier 3 (0.75-0.90): {stats['tier_3']}")
    logger.info(f"  Tier 4 (<0.75): {stats['tier_4']}")
    logger.info("")

    # Prepare output fieldnames (add Tier and Confidence_Score)
    output_fieldnames = list(fieldnames) + ["Tier", "Confidence_Score"]

    # Generate spot check sample (10 random from Tier 1/2)
    tier_1_2_companies = tier_1_companies + tier_2_companies

    if len(tier_1_2_companies) > 0:
        # Set random seed for reproducibility
        random.seed(RANDOM_SEED)

        # Sample up to SPOT_CHECK_SIZE companies
        sample_size = min(SPOT_CHECK_SIZE, len(tier_1_2_companies))
        spot_check_sample = random.sample(tier_1_2_companies, sample_size)

        logger.info(f"Generating spot check sample ({sample_size} companies)...")

        with open(spot_check_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(spot_check_sample)

        logger.info(f"  ✓ Spot check sample written to: {spot_check_path}")

        stats["spot_check_size"] = sample_size
    else:
        logger.warning("No Tier 1/2 companies found - cannot generate spot check sample")
        stats["spot_check_size"] = 0

    # Generate Tier 4 review queue (ALL Tier 4 companies)
    if len(tier_4_companies) > 0:
        logger.info(f"Generating Tier 4 review queue ({len(tier_4_companies)} companies)...")

        with open(tier_4_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(tier_4_companies)

        logger.info(f"  ✓ Tier 4 review queue written to: {tier_4_path}")
    else:
        logger.info("No Tier 4 companies found - no manual review needed!")

        # Write empty file to indicate completion
        with open(tier_4_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()

    return stats


def print_statistics(stats: Dict[str, int]) -> None:
    """Print review queue statistics."""
    if not stats:
        return

    total = stats["total"]

    logger.info("")
    logger.info("=" * 60)
    logger.info("REVIEW QUEUE STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total companies: {total}")
    logger.info("")

    for tier in [1, 2, 3, 4]:
        count = stats[f"tier_{tier}"]
        pct = (count / total * 100) if total > 0 else 0
        logger.info(f"  Tier {tier}: {count:4d} ({pct:5.1f}%)")

    logger.info("")
    logger.info(f"Spot check sample size: {stats.get('spot_check_size', 0)}")
    logger.info("")

    # Quality check: warn about tier distribution
    tier_1_pct = (stats["tier_1"] / total * 100) if total > 0 else 0
    tier_4_pct = (stats["tier_4"] / total * 100) if total > 0 else 0

    if tier_1_pct < 70:
        logger.warning(f"Tier 1 percentage ({tier_1_pct:.1f}%) is below target (70%)")

    if tier_4_pct > 0:
        logger.warning(f"Tier 4 companies ({stats['tier_4']}) require manual review before promotion")

    logger.info("=" * 60)


def print_manual_review_instructions() -> None:
    """Print instructions for manual review."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("MANUAL REVIEW INSTRUCTIONS")
    logger.info("=" * 60)
    logger.info("")
    logger.info("1. SPOT CHECK (Tier 1/2 - 10 random samples):")
    logger.info("   - Open spot_check_sample.csv")
    logger.info("   - For each company, verify:")
    logger.info("     * Address matches the company's actual location (check website)")
    logger.info("     * Company is a legitimate biotech/life sciences company")
    logger.info("     * City and focus areas are accurate")
    logger.info("")
    logger.info("2. TIER 4 REVIEW (ALL flagged companies):")
    logger.info("   - Open tier_4_review.csv")
    logger.info("   - For each company, investigate why confidence is low")
    logger.info("   - Options:")
    logger.info("     * Fix data issues (incorrect website, address, etc.)")
    logger.info("     * Remove from dataset if not in scope")
    logger.info("     * Accept if data is correct despite low confidence")
    logger.info("")
    logger.info("3. After review, create data/working/reviewed_flags.csv with:")
    logger.info("   - Company Name")
    logger.info("   - Reviewed (Yes/No)")
    logger.info("   - Action (Keep/Remove/Fix)")
    logger.info("   - Notes")
    logger.info("")
    logger.info("The promotion script will check that all Tier 4 companies are reviewed.")
    logger.info("=" * 60)


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    """Main entry point."""
    logger.info("Starting Review Queue Generation (Stage F - Part 2)")
    logger.info("V4.3 Framework - Issue #23")
    logger.info("")

    try:
        # Create output directory if it doesn't exist
        SPOT_CHECK_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Generate review queues
        stats = generate_review_queues(INPUT_FILE, SPOT_CHECK_FILE, TIER_4_FILE)

        if not stats:
            logger.error("Review queue generation failed - no statistics generated")
            return 1

        # Print statistics
        print_statistics(stats)

        # Print manual review instructions
        print_manual_review_instructions()

        logger.info("")
        logger.info("✓ Review queues generated successfully!")
        logger.info(f"✓ Spot check: {SPOT_CHECK_FILE}")
        logger.info(f"✓ Tier 4 review: {TIER_4_FILE}")

        return 0

    except Exception as e:
        logger.error(f"Review queue generation failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
